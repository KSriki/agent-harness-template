---
name: air-gapped-delivery
description: >
  Use when something has to get INTO the no-internet environment: container
  images, Helm charts, model weights, Python/npm packages, CA bundles, tool
  binaries — or when a workload inside it is trying to phone home. Covers
  mirroring (ACR import, skopeo), pinning by digest, offline model caches
  (HF_HUB_OFFLINE), internal package mirrors, corporate CA trust, provenance
  (checksums, cosign, SBOM), and the artifact manifest. Triggers on
  "ImagePullBackOff in prod but fine in dev", "x509 unknown authority", "pip
  can't reach PyPI", "the model tries to download", "mirror this image", "how do
  we get the weights onto the cluster", "disable telemetry".
  Do NOT use for Azure network design itself (private endpoints, firewall) —
  `azure-platform`; for chart authoring — `helm-charts`; for vLLM/LiteLLM config
  beyond offline flags — `ai-serving-stack`.
---

# Air-gapped delivery — nothing enters without a digest and a manifest

## When to use this

The cluster, its nodes, and its pods cannot reach the internet (no VPN, no proxy
exception). Anything they need must be **staged** from a connected side into
internal stores — registry, chart repo, package mirror, blob — by a reviewable,
repeatable step. "It pulled fine on my laptop" is the dev/prod gap this skill closes.

**Not this skill if:** the network path itself is the question → `azure-platform` §5.

## Prerequisites

- Know the two sides: the **connected side** (your workstation or a connected
  GitLab runner with internet + rights to push into internal stores) and the
  **disconnected side** (cluster, runners, nodes).
- Internal stores exist: ACR (images + Helm OCI), package mirror (Nexus /
  Artifactory / GitLab package registry + dependency proxy), Blob for weights.
- Mirroring tools are dependencies — **propose, don't install** (guardrail 3).

## §1 — Inventory: what does this deploy actually need?

```bash
helm template rel charts/<name> -f values-prod.yaml | grep -E '^\s*image:' | sort -u   # every image
grep -rE 'repository:|oci://' charts/*/Chart.yaml                                       # subcharts
grep -rE 'FROM ' Dockerfile*                                                           # base images
grep -rE 'model|revision' charts/<name>/values-prod.yaml                               # weights + revision
cat requirements*.txt pyproject.toml uv.lock 2>/dev/null | head                        # python deps
```

Write the result into `delivery/manifest.yaml` (or the repo's existing equivalent)
**before** mirroring: one entry per artifact with source, destination, version, and
digest/checksum. The manifest is the review artifact and the audit trail.

```yaml
images:
  - source: docker.io/vllm/vllm-openai:v0.X.Y
    dest: <acr>.azurecr.io/mirror/vllm/vllm-openai:v0.X.Y
    digest: sha256:<fill after import>
charts:
  - source: oci://ghcr.io/<org>/<chart>   # version pinned
    dest: oci://<acr>.azurecr.io/helm/<chart>
    version: 1.2.3
models:
  - repo: <org>/<model>
    revision: <commit sha>              # never "main"
    dest: https://<sa>.blob.core.windows.net/models/<org>/<model>/<sha>/
    sha256sums: delivery/models/<model>.sha256
```

## §2 — Images

**ACR import** (preferred when the pipeline can reach Azure but the cluster can't
reach the internet — ACR does the pull):

```bash
az acr import -n <acr> --source docker.io/vllm/vllm-openai:v0.X.Y --image mirror/vllm/vllm-openai:v0.X.Y
az acr repository show-manifests -n <acr> --repository mirror/vllm/vllm-openai --detail \
  --query "[?tags[?@=='v0.X.Y']].digest" -o tsv        # record the digest in the manifest
```

**skopeo / crane / podman** (when the connected side has registry creds but no
`az`, or the destination is not ACR — credentials come from the shell's existing
`podman login` / `docker login` state; the agent never logs in to a new registry):

```bash
skopeo copy --all docker://docker.io/library/postgres:16.4 docker://<registry>/mirror/postgres:16.4
crane copy ghcr.io/<org>/<img>:<tag> <registry>/mirror/<org>/<img>:<tag>
crane digest <registry>/mirror/<org>/<img>:<tag>
# podman, when that is what the workstation has (single-arch unless --all-platforms on pull):
podman pull docker.io/<org>/<img>:<tag> && podman tag docker.io/<org>/<img>:<tag> <registry>/mirror/<org>/<img>:<tag>
podman push <registry>/mirror/<org>/<img>:<tag> --digestfile /tmp/digest.txt
```

Rules: `--all` keeps multi-arch manifests; **deploy by digest** (`image@sha256:`)
on the disconnected side so a re-tag upstream cannot change what runs; the chart
gets `global.imageRegistry: <acr>.azurecr.io/mirror` (`helm-charts` §3). Never
mirror `latest`.

## §3 — Charts

```bash
helm pull oci://ghcr.io/<org>/<chart> --version 1.2.3 -d dist/     # connected side
helm registry login <acr>.azurecr.io -u 00000000-0000-0000-0000-000000000000 \
  --password-stdin <<< "$(az acr login -n <acr> --expose-token --query accessToken -o tsv)"
helm push dist/<chart>-1.2.3.tgz oci://<acr>.azurecr.io/helm
```

Subchart `repository:` fields in `Chart.yaml` point at the internal OCI path; or
vendor the `.tgz` into `charts/` and commit it (bigger diffs, zero runtime fetch).
Either way `Chart.lock` is committed and `helm dependency build` runs offline.

## §4 — Model weights

On the connected side, pin the **revision** (commit SHA on the Hub), download,
checksum, upload:

```bash
export HF_HUB_DISABLE_TELEMETRY=1
huggingface-cli download <org>/<model> --revision <sha> --local-dir ./stage/<model> \
  --exclude "*.msgpack" "*.h5" "*.ot"                       # only the format you serve (safetensors)
( cd stage && find <model> -type f -exec sha256sum {} \; | sort ) > delivery/models/<model>.sha256
azcopy copy ./stage/<model> "https://<sa>.blob.core.windows.net/models/<org>/<model>/<sha>/" --recursive
```

- Gated/licensed models: the token and the licence acceptance live on the connected
  side only; **record the licence** in the manifest — the deploy-reviewer asks.
- On the disconnected side the weights reach the pod via (a) a pre-warm `Job` that
  copies Blob → PVC and verifies the `.sha256`, or (b) a Blob CSI mount (read-only,
  slower first load). Serving pods then run with:
  ```yaml
  env:
    - {name: HF_HUB_OFFLINE, value: "1"}
    - {name: TRANSFORMERS_OFFLINE, value: "1"}
    - {name: HF_HUB_DISABLE_TELEMETRY, value: "1"}
    - {name: HF_HOME, value: /models/hf}
  ```
  and are given a **local path** (`--model /models/<org>/<model>`), never a Hub id —
  a Hub id makes the server try to resolve online even when the files exist.
- Verify before serving: the pre-warm Job's last step is `sha256sum -c`. A partial
  upload produces a model that loads and answers garbage.

## §5 — Packages, tools, and trust

- **Python:** point `uv`/`pip` at the internal index (`UV_INDEX_URL` /
  `PIP_INDEX_URL` = Nexus/Artifactory/GitLab PyPI proxy). For a fully offline build:
  `uv pip compile` on the connected side → `pip download -r requirements.txt -d wheelhouse/`
  → `uv pip install --no-index --find-links wheelhouse/`. Images are built on the
  connected side anyway; the cluster only *pulls*.
- **OS packages in Dockerfiles** (`apt-get`, `apk`) resolve against the internal
  mirror or the build fails in the disconnected runner — set the mirror in the
  base image or build on the connected side.
- **Tool binaries** (helm, kubeconform, skopeo) are mirrored as packages or baked
  into a pinned internal `tools` image used by the pipeline.
- **Corporate CA:** internal stores present certificates from the enterprise CA.
  Mount the bundle and tell every runtime about it:
  ```yaml
  env:
    - {name: SSL_CERT_FILE,       value: /etc/ssl/certs/corp-ca-bundle.crt}
    - {name: REQUESTS_CA_BUNDLE,  value: /etc/ssl/certs/corp-ca-bundle.crt}
    - {name: NODE_EXTRA_CA_CERTS, value: /etc/ssl/certs/corp-ca-bundle.crt}
  ```
  `x509: certificate signed by unknown authority` is always this, not a server bug.
  **Never** fix it with `verify=False` / `--insecure` (guardrail 4).

## §6 — Phone-home and telemetry: off, verified

Software assumes internet. Known switches to set in the serving stack:

| Component | Setting |
|---|---|
| vLLM | `VLLM_NO_USAGE_STATS=1`, `DO_NOT_TRACK=1` |
| Hugging Face libs | `HF_HUB_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1` |
| LiteLLM | `litellm_settings: telemetry: false` in `config.yaml` |
| Python tooling | `PIP_DISABLE_PIP_VERSION_CHECK=1`; `uv` has no telemetry |
| Anything else | read its docs for `TELEMETRY` / `ANALYTICS` env; confirm with `tcpdump`/NetworkPolicy drops |

Verify, don't trust: the namespace's **default-deny egress** NetworkPolicy
(`kubernetes-ops` §7) makes any attempt visible as a connection failure in logs,
and the firewall's deny log is the proof for the security review.

## §7 — Provenance (what the security reviewer asks for)

```bash
cosign verify --certificate-identity-regexp '<publisher>' --certificate-oidc-issuer '<issuer>' <source-image>   # if upstream signs
syft <registry>/mirror/<img>@sha256:<digest> -o spdx-json > delivery/sbom/<img>.spdx.json
sha256sum -c delivery/models/<model>.sha256
```

Commit the manifest, SBOMs, and checksum files. The MR that introduces a new
artifact gets `secure-code-review` (supply-chain section): who publishes it, is
the version pinned, what does it do at start-up.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `ImagePullBackOff` only in the no-egress cluster | Image not mirrored / chart still points at public registry | Import; set `global.imageRegistry`; deploy by digest |
| `x509: certificate signed by unknown authority` | Corporate CA not trusted by the runtime | Mount bundle + env vars (§5) |
| `pip`/`uv` hangs then times out | Index URL is PyPI | Internal index env; or wheelhouse build |
| Model server tries `huggingface.co` despite local files | Hub id given instead of path; offline env missing | `--model /path`; `HF_HUB_OFFLINE=1` |
| Model loads, outputs garbage | Partial/corrupt weights | `sha256sum -c` in the pre-warm Job; re-stage |
| Pod logs show connection refused to telemetry hosts | Phone-home not disabled | §6 switches; keep default-deny so it stays visible |
| "Works in dev" (dev has egress) | Dev cluster not representative | Give dev the same default-deny; mirror for dev too |
| Chart dependency fetch fails in runner | `repository:` is a public URL | Internal OCI path or vendored `.tgz` |

## Definition of done

- [ ] `delivery/manifest.yaml` lists every artifact with source, destination, version, **digest/checksum**
- [ ] Images deployed by digest from the internal registry; charts from internal OCI; weights verified by checksum
- [ ] Offline env vars set on serving pods; telemetry switches off; default-deny egress confirms it
- [ ] CA bundle mounted where TLS to internal stores is used; no `--insecure` anywhere
- [ ] New artifacts passed `secure-code-review` (supply chain); licences recorded for models
