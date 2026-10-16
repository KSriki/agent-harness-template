---
name: kubernetes-ops
description: >
  Use when writing, reviewing, or debugging Kubernetes workload manifests and
  running pods: Deployments/StatefulSets/Jobs, probes, resource requests and
  limits, RBAC and ServiceAccounts, ConfigMaps and Secrets delivery, NetworkPolicy,
  PodDisruptionBudgets, HPA, GPU scheduling (node selectors, taints, nvidia.com/gpu),
  storage classes and PVCs, and kubectl triage of CrashLoopBackOff, OOMKilled,
  Pending, ImagePullBackOff. Triggers on "pod is Pending", "CrashLoopBackOff",
  "OOMKilled", "readiness failing", "RBAC forbidden", "which probe", "GPU not
  scheduled", "NetworkPolicy", "kubectl".
  Do NOT use for chart structure, templating, versioning, or publishing —
  `helm-charts`; for AKS node pools, identity, networking, and `az` commands —
  `azure-platform`; for vLLM/LiteLLM-specific sizing and config — `ai-serving-stack`.
metadata:
  origin: adapted from ECC `kubernetes-patterns` (MIT, affaan-m/ECC) — trimmed and extended for GPU, NetworkPolicy, no-egress clusters
---

# Kubernetes ops — manifests that survive production, and triage when they don't

## When to use this

The YAML is the question: what the workload should declare, or why the pods are not
doing what the YAML says. Everything here applies whether the manifest is raw or
rendered by Helm.

**Not this skill if:** the problem is in the chart's templating → `helm-charts`.
The node pool, identity, or private endpoint is wrong → `azure-platform`.

## §1 — The production Deployment baseline

Every Deployment reviewed here is checked against this shape:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels: {app.kubernetes.io/name: app, app.kubernetes.io/version: "1.4.2"}
spec:
  replicas: 2                               # ≥2 for anything user-facing
  selector: {matchLabels: {app.kubernetes.io/name: app}}   # IMMUTABLE after create
  strategy:
    type: RollingUpdate
    rollingUpdate: {maxSurge: 1, maxUnavailable: 0}        # GPU workloads: see §6
  template:
    metadata:
      labels: {app.kubernetes.io/name: app, app.kubernetes.io/version: "1.4.2"}
    spec:
      serviceAccountName: app                 # never `default`
      automountServiceAccountToken: false     # true only if the app calls the K8s API
      securityContext: {runAsNonRoot: true, runAsUser: 10001, fsGroup: 10001, seccompProfile: {type: RuntimeDefault}}
      terminationGracePeriodSeconds: 30
      containers:
        - name: app
          image: <internal-registry>/team/app@sha256:<digest>   # digest or immutable tag; never :latest
          ports: [{containerPort: 8080, name: http}]
          resources:
            requests: {cpu: "250m", memory: "256Mi"}
            limits:   {memory: "512Mi"}       # memory limit = yes; CPU limit = usually no (throttling)
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: ["ALL"]}
          startupProbe:  {httpGet: {path: /health, port: http}, periodSeconds: 5, failureThreshold: 30}   # 150s to start
          livenessProbe: {httpGet: {path: /health, port: http}, periodSeconds: 30, failureThreshold: 3}
          readinessProbe: {httpGet: {path: /ready, port: http}, periodSeconds: 10, failureThreshold: 2}
          envFrom: [{configMapRef: {name: app-config}}]
          env:
            - {name: DB_PASSWORD, valueFrom: {secretKeyRef: {name: app-secrets, key: db-password}}}
          volumeMounts: [{name: tmp, mountPath: /tmp}]
      volumes: [{name: tmp, emptyDir: {}}]
```

## §2 — Probes: which, and the arithmetic

| Probe | On failure | Use for |
|---|---|---|
| `startupProbe` | restarts after `failureThreshold × periodSeconds` | slow starts (JVM, model weight loading) — **replaces** `initialDelaySeconds` guesswork |
| `livenessProbe` | restart | deadlock / hung process only; must be cheap and dependency-free |
| `readinessProbe` | removed from Service endpoints | "can't serve right now" (warming, downstream down) |

- Startup window = `failureThreshold × periodSeconds`. For a model server that
  loads for 6 minutes: `periodSeconds: 10, failureThreshold: 60`.
- Liveness must **not** check dependencies — a DB outage would restart every pod
  and turn a degradation into an outage. Readiness checks dependencies.
- `/health` and `/ready` are different endpoints for this reason.

## §3 — Resources

- **Requests** place the pod; **limits** kill (memory) or throttle (CPU) it.
- Always set requests. Set a memory limit. CPU limits usually hurt latency-sensitive
  services (throttling) — omit unless a noisy neighbour forced it, and say so.
- HPA computes utilisation against **requests**; no requests → no autoscaling.
- `kubectl top pods -n <ns>` and `kubectl describe pod` → `Last State: OOMKilled`
  tell you the limit was real.

| Workload | CPU req | Mem req | Notes |
|---|---|---|---|
| Web/API | 100–250m | 128–512Mi | mem limit ≈ 2× request |
| Worker | 250–500m | 256Mi–1Gi | mem limit = request (predictable) |
| JVM | 500m–1 | 512Mi–2Gi | headroom over `-Xmx` |
| Model server | 2–8 | 16–64Gi + GPU | see `ai-serving-stack`; `nvidia.com/gpu` req = limit |

## §4 — Config and secrets delivery

- ConfigMap for non-secret config; `envFrom` for flat vars, a file mount for
  structured config. Change → pods must restart (checksum annotation, `helm-charts` §3).
- **A Kubernetes Secret is base64, not encryption.** In this environment secrets
  are *synced in*, never committed:
  - **Azure Key Vault Secrets Store CSI driver** — mounts secrets as files, can also
    sync to a K8s Secret; identity via Workload Identity (`azure-platform` §3).
  - **External Secrets Operator** — `ExternalSecret` → K8s Secret from Key Vault.
  Either way the chart accepts `existingSecret` and never renders values.
- RBAC: grant `get` on the specific secret by `resourceNames`, never `list secrets`
  namespace-wide.

## §5 — RBAC and ServiceAccounts

Most apps need **no** API access: dedicated SA + `automountServiceAccountToken: false`.
Operators/controllers get a `Role` (namespace) with the minimum verbs; `ClusterRole`
only for cluster-scoped resources; `cluster-admin` for an app is a finding.

```bash
kubectl auth can-i list secrets --as=system:serviceaccount:<ns>:<sa> -n <ns>   # prove the minimum
kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa> -n <ns>
```

Humans on AKS authenticate through Entra ID (`kubelogin`); their rights are Azure
RBAC roles, not in-cluster RoleBindings — `azure-platform` §2.

## §6 — GPU workloads

```yaml
spec:
  nodeSelector: {agentpool: gpu}                            # AKS node pool name label
  tolerations:
    - {key: "sku", operator: "Equal", value: "gpu", effect: "NoSchedule"}   # match the pool's taint
  containers:
    - name: vllm
      resources:
        limits: {nvidia.com/gpu: 1}                         # requests auto-set equal; fractional not allowed
      volumeMounts: [{name: shm, mountPath: /dev/shm}]
  volumes:
    - name: shm
      emptyDir: {medium: Memory, sizeLimit: 8Gi}           # NCCL/tensor-parallel needs real shm
```

- `nvidia.com/gpu` only exists once the **NVIDIA device plugin** (or GPU Operator) is
  running on the pool — `kubectl describe node <gpu-node> | grep nvidia.com/gpu`.
  Zero capacity = plugin missing, not quota.
- **Rolling updates need a spare GPU.** With one GPU per node and no spare node,
  `maxSurge: 1` waits forever. Use `strategy: Recreate` (brief downtime, honest) or
  `maxSurge: 0, maxUnavailable: 1`, or keep one spare GPU node for rollouts — a
  cost decision worth an `adr`.
- HPA on CPU is meaningless for GPU servers; scale on queue depth / custom metrics
  (KEDA or Prometheus adapter) or by hand, deliberately.
- GPU nodes are expensive: taint them so CPU workloads never land there; set a
  `PriorityClass` so model servers preempt batch jobs, not the reverse.

## §7 — Network: default-deny in a no-egress cluster

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: default-deny, namespace: ai}
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: allow-dns, namespace: ai}
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: kube-system}}}]
      ports: [{protocol: UDP, port: 53}, {protocol: TCP, port: 53}]
```

Then allow exactly the flows the design names (clients → LiteLLM; LiteLLM → vLLM;
LiteLLM → Postgres). Needs a CNI that enforces policy (Azure CNI with network
policy, Cilium) — verify, otherwise the YAML is decoration. A new egress rule is a
guardrail-2 hard stop: propose it, with the destination and reason.

## §8 — Availability and storage

- `PodDisruptionBudget` with `minAvailable: 1` (or `maxUnavailable: 1`) for anything
  with replicas; node drains during AKS upgrades otherwise take the service down.
- `topologySpreadConstraints` across zones for replicas ≥2.
- Storage: `ReadWriteOnce` (Azure Disk) for one pod; `ReadWriteMany` (Azure Files /
  NFS / Blob CSI) when several model servers share a weights cache. PVC size is
  often immutable per storage class — size for growth.
- Jobs: `restartPolicy: OnFailure|Never`, `backoffLimit`, `ttlSecondsAfterFinished`.
  CronJobs: `concurrencyPolicy: Forbid` unless overlap is proven safe.

## §9 — Triage cheatsheet

```bash
kubectl get pods -n <ns> -o wide                          # node placement, restarts
kubectl describe pod <pod> -n <ns>                        # Events: the answer is usually here
kubectl logs <pod> -n <ns> --previous                     # the crashed container's logs
kubectl logs <pod> -n <ns> -c <container> --since=10m
kubectl get events -n <ns> --sort-by=.lastTimestamp | tail -30
kubectl rollout status deploy/<name> -n <ns>; kubectl rollout history deploy/<name> -n <ns>
kubectl rollout undo deploy/<name> -n <ns>                # (Helm-managed? prefer helm rollback)
kubectl exec -it <pod> -n <ns> -- sh                      # readOnlyRootFilesystem may bite
kubectl debug -it <pod> -n <ns> --image=<internal-registry>/tools/netshoot --target=<container>
kubectl port-forward svc/<svc> 8080:80 -n <ns>
kubectl apply --dry-run=server -f manifest.yaml           # admission + schema, no change
```

| Symptom | Look at | Usual cause |
|---|---|---|
| `Pending` | `describe` → Events `FailedScheduling` | no node with the GPU/CPU/mem request; missing toleration; PVC unbound; quota |
| `ImagePullBackOff` | Events | image not mirrored to the internal registry; wrong `imagePullSecrets`; digest typo |
| `CrashLoopBackOff` | `logs --previous` | app error; config missing; `readOnlyRootFilesystem` with no writable `/tmp` |
| `OOMKilled` | `describe` → Last State | limit below real usage; model too big for RAM (CPU side) |
| Ready never true | readiness endpoint; `describe` | depends on an unreachable downstream (NetworkPolicy / private endpoint DNS) |
| `x509: certificate signed by unknown authority` | container logs | corporate CA not mounted (`air-gapped-delivery` §5) |
| `forbidden: User "system:serviceaccount…"` | logs; `kubectl auth can-i` | RBAC rule missing or wrong namespace |
| Service has no endpoints | `kubectl get endpoints` | selector/label mismatch; pods not Ready |

## Failure modes (reviewer's list)

| Finding | Why it matters |
|---|---|
| `image: …:latest` or mutable tag | unreproducible rollouts; rollback to "the same tag" changes nothing |
| No `resources.requests` | scheduler guesses; HPA inert; node overcommit |
| Liveness checks a dependency | cascading restarts during a downstream blip |
| `default` SA with token mounted | lateral movement path if the pod is compromised |
| Secret value in ConfigMap/values | leak with a diff |
| No PDB on a multi-replica service | AKS upgrade drains both replicas |
| `cluster-admin` binding for an app | god-mode for a web app |
| GPU Deployment with `maxSurge: 1` and no spare GPU | rollout hangs forever |

## Definition of done

- [ ] Baseline (§1) satisfied: digest/immutable image, requests, three probes, non-root, dedicated SA
- [ ] Secrets synced in (CSI / ESO), none rendered from values
- [ ] GPU workloads: toleration + selector + shm volume + honest rollout strategy
- [ ] NetworkPolicy allows exactly the designed flows; new egress proposed, not added
- [ ] `kubectl apply --dry-run=server` clean against the target cluster
- [ ] PDB present for replicas ≥2
