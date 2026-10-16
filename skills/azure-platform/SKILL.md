---
name: azure-platform
description: >
  Use when the task touches Azure itself: subscriptions and resource groups,
  Entra ID identities and RBAC role assignments, AKS clusters and node pools
  (including GPU pools and private clusters), Azure Container Registry, Key Vault,
  VNets, private endpoints and egress control, Blob/Files storage, Azure Monitor,
  quotas, or any `az` CLI / Bicep / Terraform azurerm change. Written for an
  engineer new to Azure: it maps concepts first, then gives the commands.
  Triggers on "az aks", "resource group", "managed identity", "workload identity",
  "private endpoint", "AcrPull", "Key Vault", "node pool", "GPU quota", "what is the
  Azure equivalent of".
  Do NOT use for the workload YAML inside the cluster — `kubernetes-ops`; for Helm
  charts — `helm-charts`; for copying images/charts/models into the no-egress
  environment — `air-gapped-delivery`.
---

# Azure platform — the mental model, then the commands

## When to use this

Something outside the cluster's YAML has to exist, be permitted, or be reachable:
an identity, a role, a registry, a vault secret, a private endpoint, a node pool.

**Not this skill if:** the cluster is fine and the pod is wrong → `kubernetes-ops`.

## §1 — The hierarchy (read once)

```
Entra ID tenant (identity: users, groups, service principals, managed identities)
└── Management group(s)
    └── Subscription            ← billing + quota boundary; most RBAC lives here or below
        └── Resource group      ← lifecycle unit: delete the RG, delete everything in it
            └── Resources       ← AKS cluster · ACR · Key Vault · VNet · Storage account · Log Analytics
```

- **Scope** is everything in Azure RBAC. A role assigned at the subscription
  applies to every RG beneath; assigned at an RG, only there. Assign at the
  **narrowest scope that works**.
- **Region** is chosen per resource; GPU SKUs and quotas are per region per
  subscription. "No capacity in region" is a real error you plan around.
- AKS creates a **second, managed RG** (`MC_<rg>_<cluster>_<region>`) holding the
  node VMs, disks, and load balancers. Don't hand-edit it; it is reconciled.

**Translation table for people arriving from AWS/GCP:**

| Concept | Azure |
|---|---|
| IAM users/roles | Entra ID (users, groups, service principals) + Azure RBAC role assignments |
| IAM role for a pod (IRSA) | **Workload Identity** (user-assigned managed identity + federated credential) |
| EKS / GKE | AKS |
| ECR / GCR | Azure Container Registry (ACR) — also hosts Helm OCI charts |
| S3 / GCS | Blob Storage (in a Storage account) |
| EFS | Azure Files (SMB/NFS) |
| EBS | Azure Disk |
| VPC / subnets / SG | VNet / subnets / Network Security Group (NSG) |
| PrivateLink | Private Endpoint + Private DNS zone |
| Secrets Manager / KMS | Key Vault (secrets, keys, certificates) |
| CloudWatch | Azure Monitor + Log Analytics workspace (Container Insights for AKS) |
| CloudFormation | Bicep (native) — or Terraform `azurerm` (this team's default, steering §5) |
| Service quotas | Subscription quotas (`az vm list-usage`) — GPU cores default to **0**; request first |

## §2 — Identity and access

Three identity kinds you will meet:

| Kind | Use for | Notes |
|---|---|---|
| User / group | humans | assign roles to **groups**, never individuals |
| Service principal (app registration) | CI from outside Azure (GitLab runners) | prefer **OIDC federation** from GitLab over a client secret |
| Managed identity (system- or user-assigned) | Azure resources and pods | no secret to rotate; **user-assigned** survives recreation and is reusable |

```bash
az login                                   # or: az login --identity (on a VM/runner with MI)
az account list -o table; az account set --subscription "<name-or-id>"
az ad group show --group "<team-group>" --query id -o tsv
az role assignment create --assignee-object-id <oid> --assignee-principal-type Group \
  --role "Azure Kubernetes Service Cluster User Role" --scope <aks-resource-id>
az role assignment list --scope <resource-id> -o table   # who can do what, here
```

Roles you will actually assign (built-in): `Reader` · `Contributor` (avoid for
humans in prod) · `AcrPull` / `AcrPush` · `Key Vault Secrets User` /
`Key Vault Secrets Officer` · `Azure Kubernetes Service Cluster User Role` (fetch
kubeconfig) · `Azure Kubernetes Service RBAC Reader/Writer/Admin` (in-cluster rights
via Azure RBAC) · `Storage Blob Data Reader/Contributor` · `Monitoring Reader`.
**`Owner` is for break-glass.** Every assignment is reviewable IaC, not a portal click.

Key Vault access: prefer **Azure RBAC authorisation** on the vault (roles above)
over legacy access policies; one or the other is in effect, not both.

## §3 — AKS: the parts that bite

```bash
az aks get-credentials -g <rg> -n <cluster> --overwrite-existing   # writes kubeconfig
kubelogin convert-kubeconfig -l azurecli                            # Entra-integrated cluster: token via az login
kubectl get nodes -L agentpool,kubernetes.azure.com/accelerator      # see pools and GPU labels
az aks nodepool list -g <rg> --cluster-name <cluster> -o table
```

- **System vs user node pools.** System pools run cluster add-ons; your workloads
  go on user pools. Taint the system pool (`CriticalAddonsOnly=true:NoSchedule`).
- **GPU pool:**
  ```bash
  az vm list-usage -l <region> -o table | grep -i NC        # quota first — default is often 0
  az aks nodepool add -g <rg> --cluster-name <cluster> -n gpu \
    --node-vm-size Standard_NC24ads_A100_v4 --node-count 1 --min-count 0 --max-count 2 \
    --enable-cluster-autoscaler --node-taints sku=gpu:NoSchedule --labels agentpool=gpu
  ```
  AKS installs the NVIDIA driver on GPU pools by default; the **NVIDIA device
  plugin** (DaemonSet, or the GPU Operator) still has to be deployed before
  `nvidia.com/gpu` appears — verify against the AKS docs for your cluster version,
  the default has changed over time. Scale-to-zero (`--min-count 0`) keeps idle
  GPU cost at zero; first pod then waits minutes for a node.
- **Private cluster** (`--enable-private-cluster`): the API server has a private
  endpoint; `kubectl` works only from inside the VNet (jump host, runner, VPN). This
  is the no-egress team's default.
- **Egress control:** `--outbound-type userDefinedRouting` routes node egress through
  your firewall (Azure Firewall / NVA). AKS still needs a documented set of FQDNs
  (MCR, Entra, Azure management, `*.hcp.<region>.azmk8s.io`) — take the list from the
  current Microsoft doc for your configuration, never from memory; it changes.
- **Attach ACR** so nodes can pull without secrets: `az aks update --attach-acr <acr>`
  (grants the kubelet identity `AcrPull`). No `imagePullSecrets` needed for that ACR.
- **Workload Identity** (pods calling Azure: Key Vault, Blob, OpenAI):
  ```bash
  az aks update -g <rg> -n <cluster> --enable-oidc-issuer --enable-workload-identity
  ISSUER=$(az aks show -g <rg> -n <cluster> --query oidcIssuerProfile.issuerUrl -o tsv)
  az identity create -g <rg> -n <app>-mi
  az identity federated-credential create --name <app>-fic --identity-name <app>-mi -g <rg> \
    --issuer "$ISSUER" --subject system:serviceaccount:<ns>:<sa> --audiences api://AzureADTokenExchange
  ```
  Then annotate the SA `azure.workload.identity/client-id: <mi-client-id>` and label the
  pod `azure.workload.identity/use: "true"`; assign the MI `Key Vault Secrets User` on
  the vault. No secret anywhere.
- **Upgrades** drain nodes: PDBs (`kubernetes-ops` §8) or you lose the service.
  Pin a maintenance window; check `az aks get-upgrades`.

## §4 — Registry, vault, storage, monitoring (the supporting cast)

```bash
az acr login -n <acr>                                              # docker/helm auth via Entra token
az acr repository list -n <acr> -o table
az acr import -n <acr> --source docker.io/vllm/vllm-openai:<tag> --image vllm/vllm-openai:<tag>   # mirror (air-gapped-delivery §2)
az keyvault secret set --vault-name <kv> -n <name> --value "<value>"   # from a trusted shell, never from a pipeline log
az storage container create --account-name <sa> -n models --auth-mode login
az monitor log-analytics query -w <workspace-id> --analytics-query 'ContainerLogV2 | where PodName startswith "vllm" | take 50'
```

- ACR: use **Premium** for private endpoints and geo-replication; enable
  content trust / quarantine if policy requires; `az acr import` is how upstream
  images enter a no-egress estate (ACR pulls, the cluster never reaches the internet).
- Key Vault: soft-delete + purge protection on; RBAC authorisation; one vault per
  environment is the usual boundary.
- Storage: model weights in Blob (hierarchical namespace optional); mount into AKS
  via the **Blob CSI** (read-mostly) or stage onto a PVC — `ai-serving-stack` §3.
- Monitoring: Container Insights ships pod logs/metrics to Log Analytics; Azure
  Monitor **managed Prometheus + Grafana** is the native way to scrape `/metrics`
  from vLLM and LiteLLM (`observability` for the SLOs).

## §5 — Private networking for a no-egress estate

Every PaaS the cluster needs (ACR, Key Vault, Storage, Postgres Flexible Server)
gets a **private endpoint** in the VNet plus a **Private DNS zone** linked to the
VNet so `<acr>.azurecr.io` resolves to a private IP. Symptoms when this is wrong:
`ImagePullBackOff` with timeouts, `dial tcp: lookup … no such host`, Key Vault 403s
that are really network denies.

```bash
az network private-endpoint list -g <rg> -o table
az network private-dns link vnet list -g <rg> -z privatelink.azurecr.io -o table
nslookup <acr>.azurecr.io            # from inside the VNet: must return 10.x, not a public IP
```

Public network access on those PaaS resources: **disabled**, with the firewall
exception list empty. A new egress destination is a guardrail-2 hard stop: propose.

## §6 — IaC and change discipline

- Everything above is Terraform (`azurerm`) or Bicep in a repo, applied by the
  pipeline (`ci-cd`), never by hand in the portal. Portal for **reading** is fine.
- `az` commands in this skill are for inspection and one-off verification; if one
  creates or changes a resource, it must be mirrored into IaC the same day or
  reverted.
- Record platform-shape decisions (private cluster, egress model, identity model,
  GPU SKU, registry topology) as ADRs (`adr`) — they are the expensive-to-reverse kind.
- Cost: GPU pools scale to zero when idle; **Spot** pools for dev/experiments only
  (evictable); reserved instances for steady prod GPU. Tag everything
  (`env`, `owner`, `cost-center`) — `az tag` — or finance cannot attribute spend.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `kubectl` hangs / `no route to host` | Private cluster, you're outside the VNet | Run from the jump host / runner inside the VNet |
| `nvidia.com/gpu: 0` on the GPU node | Device plugin not deployed | Deploy NVIDIA device plugin / GPU Operator (`kubernetes-ops` §6) |
| Node pool create fails: quota | Regional GPU quota is 0 | Request quota increase for the SKU family; wait |
| `ImagePullBackOff` from ACR | ACR not attached / private DNS missing / image not imported | `--attach-acr`; fix DNS zone link; `az acr import` |
| Pod gets 401/403 from Key Vault | Workload Identity not wired or role missing | Check SA annotation, pod label, federated subject, `Key Vault Secrets User` |
| `AADSTS…` on `kubectl` | Expired `az login` / wrong tenant | `az login --tenant <id>`; `kubelogin remove-tokens` |
| Portal change "disappeared" | Terraform reconciled it away | Make the change in IaC |
| Service unreachable after "nothing changed" | NSG / firewall rule, or PaaS public access toggled | Diff IaC state; check NSG flow logs |

## Definition of done

- [ ] Change exists in IaC (Terraform/Bicep) and was applied by the pipeline
- [ ] Role assignments at the narrowest scope, to groups or managed identities
- [ ] No client secrets created where a managed identity / OIDC federation would do
- [ ] Private endpoint + DNS zone verified from inside the VNet for any new PaaS
- [ ] Shape decisions recorded via `adr`
