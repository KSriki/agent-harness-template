# Architecture Patterns — Agent Reference

> **Compressed operational version** of `docs/architecture-patterns-FULL-KB.md`
> (~1,800 lines). This file is **decision rules and triggers**, not exposition —
> it is written to be *acted on*, not read linearly.
>
> **§ numbers map to the full KB.** When a decision is expensive or irreversible,
> **open the full KB at the cited §** rather than working from this summary.
> This file tells you *what* and *when*; the KB tells you *why* and *how*.

---

## THE FIVE PILLARS (§0.5) — every decision trades against these

`Scalability` · `Availability` · `Maintainability` · `Performance` · `Cost`

**Security and Observability are NOT tradeable axes.** They are constraints. A
design that trades them away has a bug upstream. Design them in.

---

## THE LADDER (§0.7) — the single most-used rule here

| Rung | Architecture | Push up only when |
|---|---|---|
| 0 | Single script/process | Multiple users; uptime needed |
| 1 | Monolith | Build/test/deploy blocks the team; conflicting release cadences |
| 2 | **Modular Monolith** | Genuine need for *independent scaling or deploys* of specific modules |
| 3 | Service-Oriented (a few) | 2–5 components with genuinely different scaling/availability/ownership |
| 4 | Microservices | Many teams, many cadences, real polyglot + scaling heterogeneity |
| 5 | Serverless/FaaS | Spiky workloads, no-ops mandate, glue |

**Rules:**
- **Each rung up ~DOUBLES operational complexity.** Cost is not linear.
- **Rung 2 (modular monolith) is the rung most teams should pick and skip past.**
  Most evolvability of microservices at a fraction of the cost. Extract a service
  later when you actually need it.
- **"Microservices because Netflix" is not a reason.** "Two teams need independent
  deploys on incompatible cadences" *is* a reason.
- **Bottom rungs aren't shameful.** $10M+ ARR businesses run on Rung 1.
- **You can't skip rungs cheaply.** Monolith → microservices without passing
  through modular-monolith = learning boundary discipline *and* distributed ops
  simultaneously. That's where the regret stories come from.

**The test:** name the *specific failure mode* of the rung below. Can't? Stay put.

---

## DETERMINISM ↔ AUTONOMY (§0.9) — who authors the control flow

For anything with a model in it. **The most-skipped decision in agentic systems.**

`Hardcoded` → `Config-driven` → `Rules engine` → **`Workflow (LLM in steps)`** →
`Agent (LLM authors control flow)` → `Multi-agent`

- **The test (§0.9.4):** *Can you enumerate the steps in advance?*
  **Yes → workflow.** No → agent. Most "agents" are workflows wearing a costume.
- **Crossing into autonomy has an architectural payload (§0.9.5):** you now need
  decision-path observability, eval harnesses, cost/latency variance handling,
  and containment. You are buying all of it, not just "an LLM call."
- **Putting a model where rules belong is a DOWNGRADE (§0.9.6)** — slower, costlier,
  non-deterministic, harder to test. If it's routing/validating/parsing, that's code.
- **Push logic into deterministic code.** Every branch you move out of the model is
  a branch you unit-test for free, forever.

---

## PARADIGM (§0.8)

**Functional Core, Imperative Shell (§0.8.4)** — the default worth defaulting to.
Pure logic in the middle (no I/O, trivially testable), effects at the edges.
This *is* Hexagonal (§1.4) at the code level, and it's why `domain/` must not
import `adapters/`.

---

## STRUCTURE (§1, §1A)

| Pattern | Use when | §|
|---|---|---|
| **Layered (n-tier)** | Default for simple apps | 1.1 |
| **Hexagonal / Ports & Adapters** | You want the domain testable without I/O | 1.4 |
| **DDD + Hexagonal** | Complex domain, long-lived, multiple teams | 1A |
| MVC | UI apps | 1.3 |

**The dependency direction rule (§1A.2) — the one that matters:**
> **Dependencies point INWARD.** `domain/` imports nothing. `application/` imports
> `domain/`. `adapters/` import inward. **Never the reverse.**
> Enforce it mechanically (§1A.9), not by convention — conventions rot.

**Vertical slices over horizontal layers (§1A.8)** — organize by *feature*, not by
technical layer. `features/billing/{domain,api,adapters}` beats
`domain/…, api/…, adapters/…` split across the repo.

**DDD is OVERKILL when (§1A.11):** simple CRUD, short-lived, solo dev, thin domain.
Don't cargo-cult it.

---

## TESTABILITY (§1B)

- **Test pyramid (§1B.1):** many unit, fewer integration, fewest e2e.
- **Vocabulary (§1B.2):** *stub* = canned answers. *mock* = asserts interactions.
  *fake* = working lightweight impl. Use precisely; people conflate these constantly.
- **The anti-patterns that destroy testability (§1B.4):** I/O in the domain,
  static/global state, hidden time (`now()` inline), new-ing dependencies inside
  the thing under test. **If you need 4 mocks to unit-test something, the DESIGN is
  wrong — don't mock harder.**
- **TDD is design pressure (§1B.5)**, not a test discipline. Hard to test = badly designed.
- **Contract testing (§1B.7)** — the underused win for services. If you split, do this.
- **Property-based testing (§1B.8)** — the underused win for domain logic (Hypothesis).

---

## SCALING (§2A)

- **Vertical** = bigger box. Simple, hard ceiling, SPOF.
- **Horizontal** = more boxes + load balancer. **REQUIRES STATELESSNESS** — check
  this precondition before assuming you can scale out.
- **LB algorithms (§2A.2):** round-robin (default) · weighted · **sticky sessions
  (a smell if you're truly stateless)** · least-connections (uneven request cost).
- **Autoscale `min=2`, never 1** — always a healthy target during deploy/crash.
- **DB scaling (§2A.3):** read replicas → sharding. Sharding is a big step; be sure.
- **Elastic vs reserved (§2A.5)** — spiky → elastic; steady → reserved (cheaper).

---

## DATA (§3)

| Pattern | Use when | Cost | §|
|---|---|---|---|
| **Outbox** | You write a row AND publish an event | **Mandatory** if you do this — otherwise dual-write bug | 3.7 |
| Cache-Aside | Hot reads on small data | Invalidation | 7.2 |
| Read Replicas | Read-heavy | Replica lag | 7.4 |
| CQRS | Read and write models genuinely diverge | Two models to maintain | 3.1 |
| Event Sourcing | You need the full history as truth (ledgers, audit) | **High.** Replay, versioning, snapshots. | 3.2 |
| Saga | Multi-service transaction | Compensations are hard | 3.3 |
| Sharding | One DB can't hold it | Rebalancing, cross-shard queries | 3.4 |
| Materialized View | Expensive query, tolerable staleness | Refresh | 3.6 |

**CQRS and Event Sourcing are frequently over-applied.** They are not defaults.
Both are Rung-4-ish complexity. Have a named reason.

---

## COMMUNICATION (§4)

**The pivotal question:** *what happens when the callee is down or slow?*
If a non-critical feature can break a critical path → **you need async.**

- **Sync (request-reply, §4.2):** caller needs the result to answer.
- **Async (pub-sub, §4.1):** callee can be late; others may want the event too.
  Broker gives: HA, durability, redelivery, separation of concerns.
- **If async, you MUST accept:** eventual consistency is user-visible ·
  at-least-once delivery → **consumers must be idempotent** · dual-write →
  **use Outbox (§3.7)**.
- **API Gateway (§4.4):** single front door, path routing, auth at the edge.
- **BFF (§4.5):** one backend per frontend type. Only when clients genuinely diverge.

---

## SECURITY (§5A)

- **AuthN (§5A.1) vs AuthZ** — verify identity vs verify permission. Different.
- **JWT at the edge:** Auth signs with private key; **gateway verifies with public
  key, no network call per request**; injects trusted `X-User-Id`. Bad traffic dies
  at the edge. Trade-off: **revocation is hard** (a valid JWT is valid till expiry).
- **Signed/pre-signed URLs** with short expiry for blob serving — bytes go direct
  from storage, never through your compute.
- **Defense in depth (§5A.6):** layered, not nested.
- **Secrets (§5A.8):** env/vault only. Never in git, never in logs.
- **Agentic overlay (§5A.10):** prompt injection, tool-permission scoping, egress
  control. → see `secure-code-review` skill.

---

## RESILIENCE (§5)

Rate limiting (429) · circuit breaker · retry **with backoff + jitter** ·
bulkhead · timeout. **Retries without backoff are a self-DDoS.**

---

## OPTIMIZATION (§7) — the rule people get wrong

- **Small, hot, rarely-changing structured data → RAM cache (Redis).** Cache-Aside.
- **Large static blobs → CDN.** Edge PoPs.
- **DO NOT put a 20MB video in Redis.** Expensive RAM, wrong tool.
  **Matching the cache's shape to the data's shape IS the pattern.** Getting this
  backwards is the common, expensive mistake.

---

## MIGRATION (§6)

- **Strangler Fig (§6.1)** — the default for replacing a legacy system. Incremental.
- **Anti-Corruption Layer (§6.2)** — isolate the legacy model from the new one.
- **Branch by Abstraction (§6.3)** — swap an implementation behind an interface.
- **Parallel Run (§6.4)** — run both, compare outputs, then cut over. Highest confidence.

---

## DEPLOYMENT (§8)

Blue-Green (§8.1) · Canary (§8.2) · Feature Flags (§8.3) ·
Shadow traffic (§8.4 — test with prod load, no user risk).

---

## ANTI-PATTERNS (§10) — check the design against these

- **Distributed monolith** — services that must deploy together. All the cost of
  microservices, none of the benefit. **The #1 failure of premature splitting.**
- **Big ball of mud** — no boundaries.
- **Golden hammer** — one pattern for everything.
- **Premature optimization / premature distribution.**
- **Shared database across services** — couples them at the schema. Kills independence.
- **Chatty services** — N+1 over the network.

---

## PICKING A PATTERN (§11) — the workflow

1. **Name the actual problem** (not the pattern you want to use).
2. **Which pillar (§0.5) is under pressure?** Scalability? Cost? Maintainability?
3. **What's the lowest rung (§0.7) that solves it?**
4. **What's the penalty for being wrong?** Expensive/irreversible → design it.
   Cheap → just pick one and move.
5. **Name the tax.** Every pattern has one. Say it out loud.
6. **Record the rejected alternative.** → `write-design-doc`.

---

## DESIGN PATTERNS (§11A) — GoF, briefly

Creational (§11A.1) · Structural (§11A.2) · Behavioral (§11A.3) ·
Concurrency (§11A.4).

**§11A.5 — when design patterns become a smell:** a pattern applied for its own
sake, a `FactoryFactory`, an abstraction with one implementation. **Patterns are
vocabulary, not goals.**

---

## WHEN TO OPEN THE FULL KB

Open `docs/architecture-patterns-FULL-KB.md` at the cited § when:

- The decision is **expensive or irreversible** (storage engine, service boundary,
  auth model, sync-vs-async, event sourcing)
- You need the **trade-offs and failure modes**, not just the name
- You're about to **climb a rung** and want the real cost
- You need **real-world examples** or the source index (§12)

**This file is the index. The KB is the depth. Do not guess from the summary when
the penalty for being wrong is high.**
