---
name: ai-serving-stack
description: >
  Use when deploying, sizing, configuring, or debugging the AI serving layer on
  Kubernetes: vLLM model servers (GPU memory, tensor parallelism, max-model-len,
  startup time, OpenAI-compatible API), the LiteLLM proxy as the single gateway
  (model_list, virtual keys, budgets, fallbacks, Postgres), kagent agents and
  ModelConfigs, and chat front-ends pointed at the gateway. Triggers on "CUDA out
  of memory", "which GPU / how many", "tensor-parallel-size", "the model takes 10
  minutes to start", "LiteLLM 401", "model not found via the proxy", "virtual key",
  "spend per team", "kagent Agent CRD", "point the chat UI at our models".
  Do NOT use for generic pod semantics (probes math, RBAC, NetworkPolicy) —
  `kubernetes-ops`; for chart mechanics — `helm-charts`; for getting weights and
  images into the no-egress estate — `air-gapped-delivery`; for scoring model
  output quality — `eval-harness`.
---

# AI serving stack — vLLM behind LiteLLM, agents and UIs on top

## When to use this

You are standing up or operating the thing that answers `/v1/chat/completions`
inside the enterprise estate. The architecture this skill assumes (record
deviations as ADRs):

```
clients (chat UI · kagent agents · apps) ──► LiteLLM proxy (auth · keys · budgets · routing · logs)
                                                 ├──► vLLM  model-A  (1 Deployment per model, GPU pool)
                                                 ├──► vLLM  model-B
                                                 └──► (optional) Azure OpenAI / other providers via private endpoint
```

**One gateway.** Nothing calls a vLLM Service directly except LiteLLM and the
smoke test. That is where audit, cost, and kill-switch live.

**Not this skill if:** the pod is Pending for non-GPU reasons → `kubernetes-ops`.
The quality of answers regressed → `eval-harness`.

## §1 — Sizing before YAML

Weights VRAM ≈ parameters × bytes per parameter (bf16/fp16 = 2, int8 = 1,
4-bit ≈ 0.55 incl. overhead). Then **KV cache** needs the rest: more concurrent
requests × longer context = more KV. Rule of thumb: weights ≤ ~60–70 % of the
GPU memory you give vLLM, or throughput collapses.

| Model | bf16 weights | Fits on | Note |
|---|---|---|---|
| 7–8B | ~16 GB | 1× 24 GB (tight) · 1× 80 GB (comfortable) | int8/4-bit for 24 GB with long context |
| 30–34B | ~68 GB | 1× 80 GB (short ctx) · 2× 80 GB TP=2 | |
| 70B | ~140 GB | 2× 80 GB TP=2 (quantised) · 4× 80 GB TP=4 | |

- `--tensor-parallel-size N` = GPUs in **one pod on one node**; N must divide the
  attention-head count. Pipeline parallel across nodes is a last resort.
- `--max-model-len` caps context; set it to what the use case needs, not the model's
  max — it directly frees KV memory.
- `--gpu-memory-utilization 0.90` is the fraction vLLM may take; leave headroom if
  anything else shares the GPU (it shouldn't).
- Quantisation (AWQ/GPTQ/FP8) is a **quality decision**: run `eval-harness` before
  and after; record the policy as an ADR.
- Check quota and SKU on Azure first (`azure-platform` §3): NC A100/H100 families;
  one pod per GPU set; no fractional GPUs.

## §2 — vLLM Deployment essentials

```yaml
containers:
  - name: vllm
    image: <acr>/mirror/vllm/vllm-openai@sha256:<digest>
    args:
      - --model=/models/<org>/<model>          # LOCAL PATH (air-gapped-delivery §4)
      - --served-model-name=<public-name>      # what LiteLLM will reference
      - --tensor-parallel-size=2
      - --max-model-len=16384
      - --gpu-memory-utilization=0.90
      - --dtype=bfloat16
      - --port=8000
    env:
      - {name: VLLM_API_KEY, valueFrom: {secretKeyRef: {name: vllm-<model>, key: api-key}}}  # LiteLLM → vLLM auth
      - {name: HF_HUB_OFFLINE, value: "1"}
      - {name: VLLM_NO_USAGE_STATS, value: "1"}
      - {name: DO_NOT_TRACK, value: "1"}
    ports: [{containerPort: 8000, name: http}]
    resources:
      requests: {cpu: "4", memory: "32Gi", nvidia.com/gpu: 2}
      limits:   {memory: "64Gi", nvidia.com/gpu: 2}
    startupProbe:  {httpGet: {path: /health, port: http}, periodSeconds: 10, failureThreshold: 90}   # 15 min
    livenessProbe: {httpGet: {path: /health, port: http}, periodSeconds: 30, failureThreshold: 3}
    readinessProbe: {httpGet: {path: /health, port: http}, periodSeconds: 10, failureThreshold: 3}
    volumeMounts:
      - {name: models, mountPath: /models, readOnly: true}
      - {name: shm, mountPath: /dev/shm}
volumes:
  - {name: models, persistentVolumeClaim: {claimName: models-<model>}}
  - {name: shm, emptyDir: {medium: Memory, sizeLimit: 16Gi}}
```

Plus from `kubernetes-ops` §6: GPU node selector + toleration, `strategy: Recreate`
(or a spare GPU node), PDB only if replicas ≥2, `PriorityClass`. Endpoints:
`/health`, `/v1/models`, `/metrics` (Prometheus: `vllm:num_requests_running`,
`vllm:num_requests_waiting`, `vllm:gpu_cache_usage_perc`,
`vllm:time_to_first_token_seconds`, `vllm:e2e_request_latency_seconds`).

Startup = weights read from disk + CUDA graph capture; minutes, not seconds.
The **startup probe window and the Helm `--timeout` must both exceed it**
(`helm-charts` §6) or every deploy rolls back "healthy" code.

## §3 — LiteLLM proxy as the gateway

`config.yaml` (mounted from a ConfigMap; secrets via `os.environ/` references only):

```yaml
model_list:
  - model_name: chat-default                     # what clients ask for
    litellm_params:
      model: openai/<public-name>                # openai/ prefix = OpenAI-compatible backend
      api_base: http://vllm-<model>.ai.svc.cluster.local:8000/v1
      api_key: os.environ/VLLM_MODEL_A_KEY
  - model_name: chat-default                     # same name twice = load-balanced / fallback pool
    litellm_params:
      model: openai/<public-name-b>
      api_base: http://vllm-<model-b>.ai.svc.cluster.local:8000/v1
      api_key: os.environ/VLLM_MODEL_B_KEY
router_settings:
  routing_strategy: simple-shuffle
  num_retries: 2
  fallbacks: [{chat-default: [chat-small]}]
litellm_settings:
  telemetry: false
  drop_params: true                             # don't 400 on params a backend ignores
  set_verbose: false
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY     # admin only; never handed to clients
  database_url: os.environ/DATABASE_URL         # Postgres: virtual keys, teams, spend
```

- **Virtual keys per team/app** (`POST /key/generate` with the master key): set
  `max_budget`, `budget_duration`, `models`, `team_id`. Budget exhausted → 429; that is
  the cost kill-switch. Rotate by generating a new key and deleting the old.
- Health: `/health/liveliness`, `/health/readiness` (readiness checks the DB);
  `/health` probes every backend (slow — not for a probe). `/metrics` exposes
  Prometheus spend/latency metrics — availability depends on your LiteLLM version
  and licence tier; check the installed version's docs.
- Postgres (Azure Database for PostgreSQL Flexible Server via private endpoint, or
  in-cluster for dev) is **stateful**: back it up; it holds every key and the
  spend ledger. Redis is optional (shared rate limits across replicas).
- Logging: LiteLLM can forward spend/request logs to OTel or a callback. Keep
  prompts out of logs unless the data classification allows it (steering §9).
- Smoke test (pipeline post-deploy):
  ```bash
  curl -fsS "$LITELLM_URL/v1/models" -H "Authorization: Bearer $SMOKE_KEY" | jq '.data[].id'
  curl -fsS "$LITELLM_URL/v1/chat/completions" -H "Authorization: Bearer $SMOKE_KEY" \
    -H 'Content-Type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"Reply with OK"}],"max_tokens":5}'
  ```

## §4 — kagent (Kubernetes-native agents)

kagent runs agents as CRDs reconciled by a controller; install via its Helm charts
(CRDs chart first, then the controller — `helm-charts` §6), mirrored into the
internal OCI registry (`air-gapped-delivery` §3).

- **`ModelConfig`** points agents at a model. Use the **OpenAI-compatible provider
  with `baseUrl` = the LiteLLM proxy** and an API-key `Secret` holding a LiteLLM
  virtual key — so every agent call is metered and budgeted like any client.
- **`Agent`** = system prompt + ModelConfig + tools. **`ToolServer` / MCP server
  resources** register tools; each is a new capability with egress — review under
  `secure-code-review` (what can it reach, what can it write).
- kagent iterates fast: **confirm field names with `kubectl explain modelconfig.spec`
  and `kubectl explain agent.spec` against the installed version** rather than from
  memory; pin the chart version in the manifest.
- Agents are consequential actors: the steering doc's egress-gate rule applies —
  an agent with tools that mutate systems needs a HITL/approval stage, and its
  budget (virtual key) is finite by design.

## §5 — Chat front-end

Whatever UI the team adopts (Open WebUI is the common open-source choice; other
"OpenChat"-style UIs behave the same), configure it with **one** OpenAI-compatible
base URL — the LiteLLM proxy — and a per-UI virtual key. Do not give the UI vLLM
addresses or the master key. Check the UI's own egress (update checks, model
hub browsing, telemetry) and turn it off (`air-gapped-delivery` §6); SSO via
Entra ID (OIDC) rather than local accounts where supported.

## §6 — Observability and evals

- Scrape `/metrics` of vLLM and LiteLLM (Azure Monitor managed Prometheus or the
  in-cluster stack); dashboards: requests running/waiting, KV cache %, TTFT p95,
  tokens/s, 429/5xx by key. SLO candidates: TTFT p95, availability of
  `chat-default` — `observability`.
- Every model/quantisation/`max-model-len` change is a **behaviour** change: run
  the golden set through the gateway (`eval-harness`) in the pipeline before
  promotion. Latency numbers come from the metrics, not from feelings.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `CUDA out of memory` at start | `max-model-len` × batch too big; utilisation too high; wrong TP | Lower `--max-model-len`; `--gpu-memory-utilization 0.85`; add GPUs / TP; quantise |
| Pod Pending forever | no GPU node / taint / plugin missing | `kubernetes-ops` §6, `azure-platform` §3 |
| NCCL / "Bus error" with TP>1 | `/dev/shm` too small | Memory `emptyDir` on `/dev/shm`, 8–16Gi |
| Rollout never completes | startup probe or `helm --timeout` shorter than load | Raise both; align |
| Server tries to reach huggingface.co | Hub id instead of path; offline env unset | `--model /models/...`; `HF_HUB_OFFLINE=1` |
| LiteLLM 401 for a client | wrong/expired virtual key; model not allowed on key | `GET /key/info`; regenerate with `models` list |
| LiteLLM 400 "model not found" | `model_name` mismatch; `served-model-name` differs from `litellm_params.model` | Align the three names |
| LiteLLM 429 | key/team budget exhausted or rate limit | Intended; raise budget via `/key/update` with approval |
| Slow TTFT under load | many waiting requests; KV cache full | More replicas/GPUs; shorter `max-model-len`; enable prefix caching |
| Spend not recorded | no `database_url` | Configure Postgres; keys and spend need it |
| kagent agent silent | ModelConfig secret/baseUrl wrong | `kubectl describe agent`; test the baseUrl with the same key via curl |

## Definition of done

- [ ] Sizing stated (model, precision, GPUs, TP, `max-model-len`) with headroom; quantisation change eval-gated
- [ ] vLLM reads local weights by path; offline + no-telemetry env set; shm volume; startup window ≥ load time
- [ ] Only LiteLLM reaches vLLM (NetworkPolicy); clients hold virtual keys with budgets; master key in Key Vault only
- [ ] `/v1/models` + one completion smoke test green through the gateway post-deploy
- [ ] Metrics scraped; TTFT/availability on a dashboard; spend visible per key
- [ ] Architecture deviations (second gateway, direct vLLM access, per-tenant clusters) recorded via `adr`
