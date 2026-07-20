---
name: observability
description: >
  Use when instrumenting a service (structured logs, metrics, traces), defining
  SLOs or alerts, building a dashboard, or triaging a live production incident /
  on-call page. Triggers on "prod is down", "latency spiked", "error rate is up",
  "what do I even look at", "add logging/metrics/tracing", "OpenTelemetry",
  "define an SLO", "this alert is too noisy", "write the postmortem", "correlation id".
  Do NOT use for pre-merge test gates (`run-tests`) or for the CI pipeline and
  deploy mechanics themselves (`ci-cd`).
---

# Observability: instrument before, triage during

## When to use this

Two moments, one skill. **Before** shipping: make the service answer "is it
healthy, and if not, where does it hurt?" **During** an incident: find and stop
the bleeding, then learn from it.

**Not this skill if:** you're proving a change correct pre-merge → `run-tests`.
You're wiring the deploy/rollback → `ci-cd` (though incident response *uses*
`ci-cd` §6 to actually roll back).

---

## MODE A — Instrument (do this at build time, not after the first outage)

### The three signals — use each for its job, don't duplicate

| Signal | Answers | Cardinality | Don't |
|---|---|---|---|
| **Metrics** | "Is it healthy? how much? how fast?" — aggregate | low | put unbounded IDs in labels (cardinality explosion → cost + slow) |
| **Logs** | "What exactly happened in *this* request?" | high | log at INFO in a hot loop; log secrets/PII |
| **Traces** | "Where did the time go across services?" | per-request | trace 100% of prod traffic — sample it |

### Structured logging (non-negotiables)

- **Structured (JSON), not string-concatenated.** You cannot query prose.
- **A correlation/trace id threaded through every log line** of a request, across
  service hops. Without it you cannot reconstruct one request from the interleaved
  firehose of all of them.
- **Never log secrets, tokens, credentials, or PII.** This is guardrail #2 wearing
  a different hat — a token in a log is an exfiltrated token. Redact at the logger.
- Log **levels mean things:** ERROR = a human should look; WARN = degraded but
  handled; INFO = state transitions; DEBUG = off in prod. If everything is ERROR,
  nothing is.

### Metrics: the four golden signals

For every user-facing service, emit **Latency, Traffic, Errors, Saturation**
(request-driven: RED = Rate/Errors/Duration; resource-driven: USE =
Utilization/Saturation/Errors). Track **latency as percentiles (p50/p95/p99),
never averages** — an average hides the tail that's actually hurting users.

### SLOs & alerting — alert on symptoms, page on pain

- Define an **SLO** on user-facing behavior 〈99.9% of requests < 300ms over 30d〉.
  The **error budget** (the allowed 0.1%) is what tells you whether you can ship
  risk or must slow down.
- **Alert on symptoms (SLO burn rate), not causes.** "CPU is 80%" is not an
  incident; "checkout p99 is 4s and climbing" is. Paging on causes trains people
  to ignore pages.
- **A page must be human-actionable and user-affecting.** Everything else is a
  dashboard or a ticket. **A noisy alert is worse than no alert** — it manufactures
  the alert fatigue that makes the real page get missed.

---

## MODE B — Triage a live incident (runbook)

> **Order of operations: stop the bleeding, *then* diagnose. Mitigate before you
> understand.** Users don't care about root cause while they're down.

### 1. Stabilize (minutes, reversible-first)

- **Did a deploy just go out? Roll it back first, ask questions after** (`ci-cd`
  §6). Rollback is the fastest mitigation and it's reversible — reach for it before
  a clever forward fix.
- Can you **flip a feature flag** to disable the broken path? Do that.
- Declare the incident, assign one **incident commander**, start a timeline log.

### 2. Diagnose (follow the signals top-down)

1. **Dashboards first** — which golden signal moved, and *when*? The "when"
   usually names the cause (a deploy, a traffic spike, a dependency).
2. **Correlate to a change** — deploy, config change, migration, a spike in
   traffic, an upstream dependency's incident. Most incidents are a change you made.
3. **Traces** to find the slow/failing hop; **logs** (filtered by correlation id)
   to see the exact failure in that hop.
4. **Form one hypothesis, test it, keep a timeline.** Resist shotgun changes —
   they turn one incident into two.

### 3. Fix & verify

Apply the *minimal* mitigation, then **watch the signals return to baseline** —
"the alert cleared" is not "it's fixed"; the graph coming home is.

### 4. Learn — blameless postmortem

- **Blameless: the target is the system, not the person.** People act reasonably
  given what they knew; fix what let a reasonable action cause an outage.
- Capture: timeline, user impact, root cause, what detected it (and how late),
  and **action items with owners**. An action item nobody owns didn't happen.
- Feed it back: a missing alert, a missing test, or a repeated correction becomes a
  new gate — that's the maintenance loop the harness runs on.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| "It's slow" but no data | Averages, no percentiles, no tracing | Emit p95/p99 + traces; instrument *before* the next incident |
| Can't reconstruct a request | No correlation id threaded | Thread a trace id through every hop and log line |
| Metrics bill exploded | Unbounded label cardinality (user id, URL, uuid in labels) | Move high-cardinality data to logs/traces, not metric labels |
| Alert fatigue; real page missed | Alerting on causes, paging on non-user-facing noise | Page only on SLO burn that affects users; demote the rest |
| Secrets/PII in logs | Logging raw request/response objects | Redact at the logger; never log tokens or PII |
| Incident dragged on | Diagnosed before mitigating | Roll back / flag-off first, understand second |

## Definition of done

**Instrumenting:**
- [ ] Structured logs with a correlation id threaded through; **no secrets/PII**
- [ ] Golden signals emitted; latency as **percentiles**, not averages
- [ ] An SLO defined on user-facing behavior; alerts fire on **symptom/burn**, not cause
- [ ] Traces sampled, not 100%; metric labels bounded

**After an incident:**
- [ ] Mitigated reversibly first (rollback/flag), then root-caused
- [ ] Signals confirmed back to baseline before closing
- [ ] Blameless postmortem with owned action items; a new gate added if a rule was missing
