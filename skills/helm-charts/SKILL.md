---
name: helm-charts
description: >
  Use when creating, changing, reviewing, versioning, or publishing a Helm chart:
  Chart.yaml, values.yaml and values.schema.json, templates and _helpers.tpl,
  subchart dependencies, umbrella charts, hooks, CRDs, OCI chart registries.
  Triggers on "helm lint", "helm template", "helm unittest", "kubeconform", "bump
  the chart version", "add a values flag", "the chart renders wrong", "publish the
  chart", "helm diff", "helm rollback", "Chart.lock".
  Do NOT use for debugging a running workload or raw manifest semantics (probes,
  RBAC, GPU scheduling) — `kubernetes-ops`; for the pipeline that runs these
  commands — `ci-cd`; for mirroring charts/images into a no-egress registry —
  `air-gapped-delivery`.
---

# Helm charts — author, validate, version, publish

## When to use this

You are editing files under a chart directory, or deciding how a chart should be
shaped. The chart is the deployable unit here: a change nobody can `helm template`
and diff is a change nobody can review.

**Not this skill if:** the chart renders fine but pods misbehave → `kubernetes-ops`.
You're wiring the validation jobs → `ci-cd`.

## Prerequisites

```bash
helm version --short                                   # 3.x
helm plugin list                                       # want: unittest, diff
command -v kubeconform || echo "kubeconform missing — propose it (guardrail 3)"
```

Plugins and binaries are dependencies: **propose, don't install** (guardrail 3). In
the no-egress environment they come from the internal mirror (`air-gapped-delivery`).

## §1 — Anatomy and the rules that keep a chart reviewable

```
charts/<name>/
├── Chart.yaml           # version (CHART semver) · appVersion (what it deploys) · dependencies
├── Chart.lock           # COMMITTED — pins subchart versions
├── values.yaml          # every knob, documented, safe default; NO secrets
├── values.schema.json   # types + required keys → helm refuses bad values
├── values-<env>.yaml    # per-environment overrides (dev · test · prod), small
├── templates/
│   ├── _helpers.tpl     # name/labels/selector helpers — the only place names are built
│   ├── deployment.yaml  # one resource per file, named after the kind
│   ├── NOTES.txt        # what to check after install
│   └── tests/           # helm test pods (optional)
├── crds/                # raw CRDs — installed once, NEVER upgraded by helm (see §6)
└── tests/               # helm-unittest specs: *_test.yaml
```

Rules:
- **Bump `version` on every change to the chart**, even values-only. Unbumped
  charts are the #1 cause of "the registry has a different chart with the same tag".
- **`appVersion` is informational** — the image tag comes from values, not from it.
- **No secret values in `values.yaml`** — accept `existingSecret: <name>` and let the
  secret arrive via the Key Vault CSI driver or External Secrets Operator
  (`kubernetes-ops` §4). A chart that templates a password is a leak with a diff.
- **Images are `registry/repository:tag` or `@sha256:` from values, with a
  `global.imageRegistry` override** so the no-egress environment can repoint every
  image to the internal registry in one line.
- **Selector labels never change after first install** (`matchLabels` is immutable).
  Keep `selectorLabels` minimal in `_helpers.tpl`; put versions in `labels`, not selectors.
- Labels: the `app.kubernetes.io/*` set via a helper; one source of truth.

## §2 — Validation ladder (cheapest first — same as any gate)

```bash
cd charts/<name>
helm dependency build                                  # honours Chart.lock; fails if drift
helm lint . -f values.yaml -f values-prod.yaml --strict
helm template rel . -f values-prod.yaml > /tmp/rendered.yaml
kubeconform -strict -summary -kubernetes-version <cluster-version> \
  -schema-location default \
  -schema-location '<internal-crd-schema-dir-or-url>/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  /tmp/rendered.yaml
helm unittest .                                        # tests/*_test.yaml
helm diff upgrade rel . -f values-prod.yaml -n <ns>    # against the live release (needs cluster)
helm upgrade --install rel . -f values-prod.yaml -n <ns> --dry-run=server   # admission + API validation
```

What each catches: `lint` → syntax and missing required values; `template` +
`kubeconform` → wrong apiVersion/fields for the target cluster version (set it!);
`unittest` → your logic (flags, conditionals, helpers); `diff` → the actual change
reviewers must see; `--dry-run=server` → admission policies (Azure Policy / Gatekeeper
in the enterprise cluster) that reject what passes offline. **Paste the `helm diff`
into the MR.**

For CRDs that kubeconform does not know, point `-schema-location` at an internal
copy of the CRD schema catalog (air-gapped) rather than skipping with `-ignore-missing-schemas`;
ignoring is the last resort and gets a comment saying why.

## §3 — Templates: idioms that avoid 80% of render bugs

```yaml
# Restart pods when their config changes
metadata:
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

```yaml
# Pass through scheduling knobs verbatim — GPU pools need these (kubernetes-ops §6)
{{- with .Values.nodeSelector }}
nodeSelector: {{- toYaml . | nindent 8 }}
{{- end }}
{{- with .Values.tolerations }}
tolerations: {{- toYaml . | nindent 8 }}
{{- end }}
```

```yaml
# Image reference with registry override and optional digest
{{- define "chart.image" -}}
{{- $reg := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- if .Values.image.digest -}}
{{ $reg }}/{{ .Values.image.repository }}@{{ .Values.image.digest }}
{{- else -}}
{{ $reg }}/{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
{{- end -}}
{{- end }}
```

- `required "message" .Values.x` for keys with no safe default; the message names
  the key and the values file to set it in.
- `tpl` renders strings from values that themselves contain templates (e.g. an
  ingress host like `{{ .Release.Name }}.internal`). Use it deliberately, not everywhere.
- `nindent` not `indent` after a newline-sensitive key; `toYaml` for structured passthrough.
- Whitespace: `{{-` eats the newline before; forgetting it leaves empty lines that
  break `kind:` boundaries in multi-doc output.
- Lookups (`lookup`) return empty on `helm template` — logic depending on them is
  untestable offline; avoid.

## §4 — Values design and the schema

`values.schema.json` makes bad input fail at `helm lint`, not at 3am:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image"],
  "properties": {
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": {"type": "string"},
        "tag": {"type": "string"},
        "digest": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"}
      }
    },
    "replicaCount": {"type": "integer", "minimum": 1},
    "resources": {"type": "object"}
  }
}
```

Document every key in `values.yaml` with a comment line above it. Prefer flat,
boring keys over clever nesting. Per-environment files hold only deltas.

## §4b — helmfile: many releases, one declared state

When the repo has a `helmfile.yaml`, it — not ad-hoc `helm upgrade` — is how
releases reach a cluster. Treat it as the deployment manifest:

```yaml
# helmfile.yaml (shape)
environments:
  test:  {values: [envs/test.yaml]}
  prod:  {values: [envs/prod.yaml]}
---
repositories:
  - name: internal
    oci: true
    url: <acr>.azurecr.io/helm            # mirrored charts only
releases:
  - name: litellm
    namespace: ai
    chart: internal/litellm
    version: 1.4.2                        # PINNED
    values: [charts/litellm/values-{{ .Environment.Name }}.yaml]
  - name: vllm-model-a
    namespace: ai
    chart: ./charts/vllm                  # local chart
    values: [releases/vllm-model-a/values-{{ .Environment.Name }}.yaml]
    needs: [ai/litellm]                   # ordering only; not a runtime dependency
```

```bash
helmfile -e test lint
helmfile -e test template | kubeconform -strict -summary -kubernetes-version <ver> -schema-location /schemas/...
helmfile -e test diff                     # the review artifact — paste into the MR file
helmfile -e test apply                    # CI job, or the human; --skip-deps when charts are vendored
helmfile -e prod -l name=litellm diff     # one release at a time for prod
```

- Pin every `version:`; a floating release is an unreviewed deploy.
- Per-environment differences live in `envs/*.yaml` and `values-<env>.yaml`,
  never in `helmfile.yaml` conditionals that nobody can diff.
- `helmfile diff` needs the `helm-diff` plugin and cluster access; in the no-egress
  estate it runs on the internal runner, not the laptop (`ci-cd`).
- Secrets: `helm-secrets`/SOPS is a dependency decision (guardrail 3); the default
  here is still `existingSecret` + Key Vault sync (`kubernetes-ops` §4).

## §5 — Dependencies and umbrella charts

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "15.x.x"
    repository: "oci://<internal-registry>/helm"      # mirrored; never a public URL in the no-egress env
    condition: postgresql.enabled
```

```bash
helm dependency update      # resolves + writes Chart.lock + downloads charts/*.tgz
git add Chart.lock          # the lock is the review artifact; charts/*.tgz is usually gitignored
```

- **Umbrella chart** (one release, many subcharts) when the components deploy and
  roll back as a unit (LiteLLM + its Postgres + Redis). **Separate releases** when
  lifecycles differ (each vLLM model server is its own release so one model can be
  rolled back alone). Record the choice as an ADR (`adr`).
- Subchart values are namespaced under the subchart name; `global:` is the only
  shared block. A value set at the wrong level silently does nothing — `helm
  template` and grep for it.

## §6 — Hooks, CRDs, and the upgrade traps

- **`crds/` are installed on `install` only.** `helm upgrade` never updates them.
  Ship CRDs in their own chart (e.g. `<thing>-crds`) and upgrade that first, or apply
  them with `kubectl apply --server-side` in the pipeline before the release.
- Hooks (`helm.sh/hook: pre-upgrade`) run Jobs outside the release's resource set;
  give them `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded` or they
  pile up and block the next run.
- `helm upgrade --install --atomic --timeout 10m --wait` → failed upgrades roll
  back automatically. Model servers take minutes to load weights: the timeout must
  exceed the startup probe window (`ai-serving-stack` §3) or every deploy "fails".
- Immutable fields (selector labels, PVC size on some storage classes, Job spec)
  make `upgrade` error with *field is immutable*. The fix is a new resource name,
  not `--force` (which deletes and recreates — downtime and data risk).

## §7 — Versioning and publishing (OCI)

```bash
# version bumped in Chart.yaml first (semver: MAJOR = values contract break)
helm package charts/<name> -d dist/
helm registry login <internal-registry> -u "$HELM_USER" --password-stdin <<< "$HELM_TOKEN"
helm push dist/<name>-<version>.tgz oci://<internal-registry>/helm
helm show chart oci://<internal-registry>/helm/<name> --version <version>   # prove it landed
```

- Same chart version must never be pushed twice with different content; CI should
  fail if the tag already exists.
- Consumers pin `--version`. A floating latest chart is an unreviewed deploy.
- Rollback is `helm rollback <release> <revision>` after `helm history <release>`;
  it reverts manifests, **not** data or CRDs.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `nil pointer evaluating interface {}.x` | Accessing a missing nested value | `with`/`default`, or `required`; add the key to the schema |
| `field is immutable` on upgrade | Selector labels / Job spec changed | New resource name; never `--force` in prod |
| Rendered fine, cluster rejected it | Admission policy (Azure Policy / Gatekeeper) | `--dry-run=server` in the pipeline; fix the manifest, don't exempt |
| Subchart ignores my value | Set at top level instead of under `<subchart>:` | Move it; `helm template` and grep |
| Pods didn't restart after config change | No checksum annotation | Add `checksum/config` (§3) |
| `--atomic` rolls back every model deploy | Timeout shorter than weight-load time | Raise `--timeout`; align with startup probe |
| CRD change had no effect | CRDs live in `crds/` | Separate CRD chart or server-side apply first (§6) |
| Chart pulls `docker.io` in the no-egress cluster | No `global.imageRegistry` override | Add the override; mirror the image (`air-gapped-delivery`) |

## Definition of done

- [ ] `Chart.yaml` `version` bumped; `Chart.lock` committed if dependencies changed
- [ ] `helm lint --strict` + `helm template | kubeconform` clean for the target cluster version
- [ ] `helm unittest` covers the new flag/conditional
- [ ] `helm diff` (or rendered diff) pasted in the MR; reviewer saw the actual change
- [ ] No secret in values; images overridable via `global.imageRegistry`
- [ ] Structural decision (umbrella vs separate, secrets mechanism) recorded via `adr` if new
