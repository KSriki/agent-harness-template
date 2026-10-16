# Template: your environment's `serving-stack` skill

> **Why this is a template and not a skill.** The real skill names the products
> your team runs — model server, gateway, agent runtime, chat UI — and their exact
> flags, endpoints, and failure modes. Those belong in your environment, not in this
> repo. Build the skill **there**, on day one, by running `grill-me` against the
> questions in Part A and filling the skeleton in Part B. Save the result as
> `skills/serving-stack/SKILL.md` (or `.devin/skills/serving-stack/SKILL.md`) and
> keep it out of this repo.

---

## Part A — the grill-me question set

Run `grill-me` with this list as the design tree. Each answer becomes a line in
Part B. Answers you can't give yet are **Open questions** in the skill, not guesses.

**Round 0 — premise**
- Is a single gateway in front of every model server mandatory, or are direct
  calls allowed? (If allowed, name who and why — that is ADR material.)
- Kill criteria: what would make this stack the wrong choice (latency floor, GPU
  budget, licence, team skills)?

**Round 1 — components (names, versions, where they come from)**
- Model server: product + pinned version + image path in the internal registry.
  OpenAI-compatible API? Which endpoints exist for health / readiness / metrics?
- Gateway: product + version. Where is its config (ConfigMap? file? DB)? Does it
  need a database / cache? Where do per-team keys and budgets live?
- Agent runtime (if any): product + version; is it CRD-based? Which CRD points an
  agent at a model, and how does it reference a key?
- Chat UI (if any): product + version; which single base URL does it get?
- Weights: where do they live (object store? PVC? both)? How do they reach a pod?
  Which env flags keep the server from touching the internet?
- Which of these does the **platform team** operate vs your team? (Draw the line.)

**Round 2 — sizing and scheduling**
- GPU SKUs available, GPUs per node, quota per environment.
- For each model you serve: parameter count, precision/quantisation policy,
  context length cap, expected concurrency → GPUs per replica, tensor parallelism,
  memory-utilisation setting.
- Startup time per model (cold) → startup-probe window and helm `--timeout`.
- Rollout strategy with scarce GPUs: `Recreate`, spare node, or blue/green via
  the gateway's routing?

**Round 3 — gateway policy**
- Key hierarchy: per team / per app / per environment? Budget period and ceiling?
  What happens at exhaustion (429)? Who can raise a budget?
- Routing: one logical model name → which backends; fallbacks; retries.
- Auth between gateway and model servers (header? network policy only?).
- What is logged, and are prompts allowed in logs (data classification)?

**Round 4 — operations**
- Metrics: which endpoints are scraped, by what, into which dashboard? The three
  numbers that page someone (TTFT p95, queue depth, availability of the default
  model?).
- Smoke test after any deploy to the testing namespace: the exact `curl`s.
- Rollback: gateway config vs model server release — which rolls back how?
- Failure modes already seen in this estate (CUDA OOM at start, shm too small,
  pod Pending on GPU, 401s through the gateway, model-name mismatch…). Each one is
  a row in the skill's table with the real fix.

---

## Part B — the skill skeleton (fill every 〈slot〉)

```markdown
---
name: serving-stack
description: >
  Use when deploying, sizing, configuring, or debugging the AI serving layer on
  Kubernetes in THIS estate: the model server (〈product〉), the gateway
  (〈product〉), the agent runtime (〈product〉), and the chat UI (〈product〉).
  Triggers on "CUDA out of memory", "which GPU / how many", "tensor parallel",
  "the model takes minutes to start", "gateway 401/429", "model not found via the
  gateway", "per-team key", "point the UI at our models", "〈product〉 CRD".
  Do NOT use for generic pod semantics (probes math, RBAC, NetworkPolicy) —
  `kubernetes-ops`; for chart mechanics or helmfile — `helm-charts`; for
  recording the decision — `adr`.
---

# Serving stack — 〈model server〉 behind 〈gateway〉, 〈agents〉 and 〈UI〉 on top

## Architecture (record deviations as ADRs)
clients (〈UI〉 · 〈agent runtime〉 · apps) ──► 〈gateway〉 (keys · budgets · routing · logs)
                                              ├──► 〈model server〉 model-A (1 release per model, GPU pool 〈name〉)
                                              └──► 〈model server〉 model-B
**One gateway.** Nothing calls a model server directly except the gateway and the smoke test.

## §1 — Sizing before YAML
| Model | Params | Precision | Weights VRAM | Context cap | GPUs / TP | Cold start |
|---|---|---|---|---|---|---|
| 〈…〉 | | | | | | |
Rules: weights ≤ ~60–70 % of the GPU memory given to the server (KV cache needs the
rest); TP = GPUs in one pod on one node; quantisation is a quality decision → ADR.

## §2 — 〈model server〉 Deployment essentials
〈exact args · env flags (offline, no telemetry, API key var) · ports · resources
with nvidia.com/gpu · startupProbe window = cold start + margin · shm volume ·
weights mount · rollout strategy〉
Endpoints: health 〈path〉 · models 〈path〉 · metrics 〈path〉 (〈the 4–5 metric names that matter〉).

## §3 — 〈gateway〉 configuration
〈where the config lives · model_list shape · env references for secrets (never
literals) · routing/fallbacks · telemetry off · master key location · DB〉
Keys: 〈hierarchy · budget period · exhaustion behaviour · who raises〉.
Health: 〈liveness path〉 · 〈readiness path〉. Smoke:
    curl -fsS "$GW/v1/models" -H "Authorization: Bearer $SMOKE_KEY"
    curl -fsS "$GW/v1/chat/completions" -H "Authorization: Bearer $SMOKE_KEY" -d '{"model":"〈name〉","messages":[{"role":"user","content":"Reply with OK"}],"max_tokens":5}'

## §4 — 〈agent runtime〉
〈install (charts, CRDs first) · the CRD that binds an agent to a model via the
gateway + a key Secret · tool/MCP registration = new egress → secure-code-review ·
verify field names with `kubectl explain` on the installed version〉

## §5 — 〈chat UI〉
〈one base URL = the gateway · its own key · egress/update checks off · SSO〉

## §6 — Observability
〈scrape targets · dashboard · the paging numbers · spend per key〉 — `observability`.

## Failure modes
| Symptom | Cause | Fix |
|---|---|---|
| 〈CUDA OOM at start〉 | 〈…〉 | 〈…〉 |
| 〈Pending forever〉 | 〈…〉 | 〈…〉 |
| 〈gateway 401 / 429 / model not found〉 | 〈…〉 | 〈…〉 |

## Definition of done
- [ ] Sizing stated with headroom; quantisation changes recorded as ADR
- [ ] Server reads local weights; offline + no-telemetry flags set; shm; startup window ≥ cold start
- [ ] Only the gateway reaches model servers (NetworkPolicy); clients hold per-team keys
- [ ] Smoke test green through the gateway in the testing namespace after deploy
- [ ] Metrics scraped; paging numbers on a dashboard
```

---

## Part C — what stays generic in this repo

`kubernetes-ops` §6 (GPU scheduling), §2 (probe arithmetic), §7 (default-deny) and
`helm-charts` §5 (helmfile) already cover the parts of the serving stack that are
the same for every product. Your local skill should **point at them**, not repeat
them.
