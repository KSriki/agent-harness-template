---
name: helm-charts
description: >
  Use when creating, changing, reviewing, or versioning a Helm chart or a helmfile
  release: Chart.yaml, values.yaml and values.schema.json, templates and
  _helpers.tpl, subchart dependencies, umbrella charts, hooks, CRDs, helmfile.yaml
  environments and the secret values it needs. Triggers on "helm lint", "helm
  template", "helm unittest", "kubeconform", "helmfile diff/template/apply", "bump
  the chart version", "add a values flag", "the chart renders wrong", "Chart.lock",
  "helm rollback".
  Do NOT use for debugging a running workload or raw manifest semantics (probes,
  RBAC, GPU scheduling) — `kubernetes-ops`; for the Jira-facing plan of the change
  — `ticket-docs`; for the MR text — `review-pr`.
---

# Helm charts — author, validate, version; helmfile as the deploy manifest

## When to use this

You are editing files under a chart directory or `helmfile.yaml`, or deciding how
a chart should be shaped. The chart is the deployable unit here: a change nobody
can `helm template` and diff is a change nobody can review.

**Boundary:** validation and rendering happen on the dev machine. Applying happens
only in the testing environment against the testing namespace, after the human
pulls the branch there. The agent never applies from the dev machine, never to
production, never pushes charts to the registry unless your repo's flow says so
(§7 slot).

**Not this skill if:** the chart renders fine but pods misbehave → `kubernetes-ops`.

## Prerequisites

```bash
helm version --short                                   # 3.x
helm plugin list                                       # want: unittest, diff
command -v helmfile kubeconform vals 2>/dev/null || echo "missing tool — propose it (guardrail 3)"
```

Plugins and binaries are dependencies: **propose, don't install** (guardrail 3). In
the no-egress environment they come from the internal mirror.

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
  secret arrive via the secrets-store CSI driver or External Secrets Operator
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
helm lint . -f values.yaml -f values-test.yaml --strict
helm template rel . -f values-test.yaml > /tmp/rendered.yaml
kubeconform -strict -summary -kubernetes-version <cluster-version> \
  -schema-location default \
  -schema-location '<internal-crd-schema-dir>/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  /tmp/rendered.yaml
helm unittest .                                        # tests/*_test.yaml — write the failing case FIRST (tdd)
# in the testing environment only:
helm diff upgrade rel . -f values-test.yaml -n <testing-ns>
helm upgrade --install rel . -f values-test.yaml -n <testing-ns> --dry-run=server   # admission + API validation
```

What each catches: `lint` → syntax and missing required values; `template` +
`kubeconform` → wrong apiVersion/fields for the target cluster version (set it!);
`unittest` → your logic (flags, conditionals, helpers); `diff` → the actual change
reviewers must see; `--dry-run=server` → admission policies in the enterprise
cluster that reject what passes offline. **Paste the diff into `tickets/<KEY>.mr.md`.**

For CRDs that kubeconform does not know, point `-schema-location` at an internal
copy of the CRD schema catalog rather than skipping with `-ignore-missing-schemas`;
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

## §5 — helmfile: many releases, one declared state

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
    url: <internal-registry>/helm         # mirrored charts only
releases:
  - name: gateway
    namespace: <ns>
    chart: internal/gateway
    version: 1.4.2                        # PINNED
    values: [charts/gateway/values-{{ .Environment.Name }}.yaml]
  - name: model-a
    namespace: <ns>
    chart: ./charts/model-server          # local chart, used once per model
    values: [releases/model-a/values-{{ .Environment.Name }}.yaml]
    needs: [<ns>/gateway]                 # ordering only; not a runtime dependency
```

```bash
helmfile -e test lint
helmfile -e test template | kubeconform -strict -summary -kubernetes-version <ver> -schema-location <internal-schemas>
helmfile -e test diff                     # in the testing env — the review artifact, pasted into the MR file
helmfile -e test apply                    # in the testing env, testing namespace, when the human says so
helmfile -e prod -l name=gateway diff     # prod: the platform team's step; you may be asked to read the diff
```

**Secret inputs (your repo's flow — fill this slot in your environment):** this
team passes secret values at render time via `vals` references and/or
`--state-values-set <key>=<value>`. Rules regardless of mechanism:
- the value comes from the **shell environment** the human already set, never typed
  into a command line that lands in history, never in a file, never in a log or a
  commit; reference it as `"$VAR"` and let the shell substitute;
- `helmfile template` output that contains a resolved secret is **not** pasted into
  the MR file or the ticket doc — diff the rendered manifests with the secret
  redacted, or diff only the non-secret resources;
- `〈exact invocation this repo uses — e.g. helmfile -e test --state-values-set 〈key〉="$〈VAR〉" template〉`.

Also:
- Pin every `version:`; a floating release is an unreviewed deploy.
- Per-environment differences live in `envs/*.yaml` and `values-<env>.yaml`,
  never in `helmfile.yaml` conditionals that nobody can diff.
- `helmfile diff` needs the `helm-diff` plugin and cluster access; it runs in the
  testing environment, not on the laptop.

## §6 — Dependencies, umbrella charts, hooks, CRDs

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
  roll back as a unit (the gateway with its database and cache). **Separate
  releases** when lifecycles differ (each model server is its own release so one
  model can be rolled back alone). Record the choice as an ADR (`adr`).
- Subchart values are namespaced under the subchart name; `global:` is the only
  shared block. A value set at the wrong level silently does nothing — `helm
  template` and grep for it.
- **`crds/` are installed on `install` only.** `helm upgrade` never updates them.
  Ship CRDs in their own chart (e.g. `<thing>-crds`) and upgrade that first, or
  apply them with `kubectl apply --server-side` before the release (platform team
  if cluster-scoped).
- Hooks (`helm.sh/hook: pre-upgrade`) run Jobs outside the release's resource set;
  give them `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded` or they
  pile up and block the next run.
- `helm upgrade --install --atomic --timeout 10m --wait` → failed upgrades roll
  back automatically. Model servers take minutes to load weights: the timeout must
  exceed the startup probe window (`kubernetes-ops` §2) or every deploy "fails".
- Immutable fields (selector labels, PVC size on some storage classes, Job spec)
  make `upgrade` error with *field is immutable*. The fix is a new resource name,
  not `--force` (which deletes and recreates — downtime and data risk).

## §7 — Versioning, rollback, publishing

- `Chart.yaml` `version` is SemVer: MAJOR = values contract break, MINOR = new
  optional key or resource, PATCH = fix with no values change. Consumers pin it.
- Rollback is `helm rollback <release> <revision>` after `helm history <release>`;
  it reverts manifests, **not** data or CRDs. In the testing namespace you may run
  it; elsewhere you write the command into the MR file for the human.
- **Publishing (slot — your repo's flow):** charts reach the internal registry by
  〈the pipeline on merge | a human running `helm package` + `helm push oci://…`〉.
  The agent does not push charts unless that slot says it does; the same chart
  version is never pushed twice with different content.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `nil pointer evaluating interface {}.x` | Accessing a missing nested value | `with`/`default`, or `required`; add the key to the schema |
| `field is immutable` on upgrade | Selector labels / Job spec changed | New resource name; never `--force` outside the testing namespace |
| Rendered fine, cluster rejected it | Admission policy in the enterprise cluster | `--dry-run=server` in the testing env; fix the manifest, don't ask for an exemption |
| Subchart ignores my value | Set at top level instead of under `<subchart>:` | Move it; `helm template` and grep |
| Pods didn't restart after config change | No checksum annotation | Add `checksum/config` (§3) |
| `--atomic` rolls back every model deploy | Timeout shorter than weight-load time | Raise `--timeout`; align with startup probe |
| CRD change had no effect | CRDs live in `crds/` | Separate CRD chart or server-side apply first (§6) |
| Chart pulls a public registry in the no-egress cluster | No `global.imageRegistry` override | Add the override; ask the platform team to mirror the image |
| Secret appeared in a diff / MR file | Rendered with the secret resolved | Redact or diff non-secret resources only (§5); rotate if it was committed |

## Definition of done

- [ ] `Chart.yaml` `version` bumped; `Chart.lock` committed if dependencies changed
- [ ] `helm lint --strict` + `helm template | kubeconform` clean for the target cluster version
- [ ] `helm unittest` covers the new flag/conditional — written before the template change
- [ ] Diff (redacted if needed) pasted in `tickets/<KEY>.mr.md`; reviewer saw the actual change
- [ ] No secret in values, diffs, or logs; images overridable via `global.imageRegistry`
- [ ] Nothing applied outside the testing namespace; cluster-side needs written as requests
- [ ] Structural decision (umbrella vs separate, secrets mechanism) recorded via `adr` if new
