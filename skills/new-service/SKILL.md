---
name: new-service
description: >
  Use when adding a new service, module, worker, queue, cache, or any new
  deployable/infrastructure component — or when splitting an existing one.
  Enforces the complexity-rung check first, then scaffolds. Triggers on
  "add a service", "split this out", "we need a queue/cache/worker",
  "microservice", "should this be its own thing".
  Do NOT use for adding a function/class inside an existing module — that
  needs no ceremony, just write it.
---

# Adding a service or component

## When to use this

Something new is about to be **deployed, operated, and paged on**. That's the
bar. A new class is free; a new component costs forever.

**Not this skill if:** you're adding code *inside* an existing module. Just
write it — no gate, no ceremony.

---

## STEP 0 — The rung check (do not skip; do not scaffold before this passes)

> Each rung up roughly **doubles operational complexity**. The default answer to
> "should this be its own service?" is **no**, until a named failure says yes.

**Ladder:** `0` script → `1` monolith → `2` **modular monolith** → `3` a few
services → `4` microservices → `5` serverless.
**Most systems should stop at 2 or 3.** Stopping early is a win, not unfinished work.

Answer these **in writing**, in the PR or design doc. If you cannot, the answer
is "don't build it."

1. **What specifically fails if we DON'T add this?** Name the failure mode —
   an actual symptom (this box saturates at N rps; a Thumbnail crash takes down
   uploads; this workload is CPU-spiky and starves the API). "It's cleaner" and
   "it's more scalable" are not failure modes.
2. **Why doesn't the rung below solve it?** Could a module boundary, an index,
   a bigger box, or a background thread do this? If yes, do that instead.
3. **What's the tax?** Name what you're buying: a deploy target, a monitor, an
   on-call surface, a network hop (latency + partial failure), a versioned
   contract. Say it out loud so it's an intentional purchase.
4. **Is the seam real?** Split along genuine differences in **scaling shape** or
   **failure blast-radius** — not along nouns in the domain model. Auth vs.
   thumbnailing is a real seam (different scale, different criticality).
   `UserService` / `OrderService` split because they're different nouns is a
   **distributed monolith** — all the cost of services, none of the benefit.

**If step 0 fails:** say so plainly, propose the lower rung, and stop. That
outcome is a success of this skill, not a failure.

---

## STEP 1 — Choose the interaction style

| Question | If yes → |
|---|---|
| Does the caller need the result to return its own response? | **Sync** (HTTP/gRPC) |
| Can it be late without breaking the caller? | **Async** via broker |
| Might *other* components later care about this event? | **Async** — pub/sub fan-out |
| Would the caller break if this component is down? | **Async**, or add a circuit breaker |

**The pivotal question:** *what happens when this new component is down or slow?*
If the answer is "the critical path fails," you have coupled a non-critical
feature to a critical one — put a broker between them. Then a failure means the
feature is *late*, not that the system is *down*.

**If async:** the write-then-publish pair is a dual-write. Use the **Outbox
pattern** — write the row and the event in one transaction, relay after commit.
Do not hand-wave "and then we publish an event."
**Consequences to accept explicitly:** eventual consistency is now user-visible;
delivery is at-least-once, so **consumers must be idempotent**.

---

## STEP 2 — Scaffold

Only now. Match the repo's existing layout — consistency beats novelty.

```
〈src/services/<name>/
  api/         # thin transport layer, no business logic
  domain/      # logic — no I/O, unit-testable standalone
  adapters/    # DB, queue, S3, external clients (mockable + budgetable)
  config.py    # env-only; secrets never committed
tests/
  unit/<name>/         # fast, no I/O
  integration/<name>/  # real deps
infra/<name>/          # terraform
Dockerfile〉
```

Non-negotiables at creation time — build these *in*, not later:

- [ ] **Stateless** — no local state, or it can't scale horizontally
- [ ] **Health check endpoint** — the load balancer needs it to route away from a sick box
- [ ] **Structured logging** with a correlation/trace id threaded through
- [ ] **Audit trail** for state mutations; **no PII/secrets/tokens in logs**
- [ ] **Config from env** (`.env.example` is the contract)
- [ ] **Metrics + an alert path** — if it breaks at 3am, how do you find out?
- [ ] **Cost shape named** if it calls anything paid (rate limits, token budget)
- [ ] **Tests from commit one** — unit + integration
- [ ] **Autoscaling `min=2`** if it's a scaled service, so a deploy/crash always leaves a healthy target

## STEP 3 — Document

- [ ] Design doc updated (`write-design-doc` skill) with the **rejected rung** recorded
- [ ] **Mermaid** diagram updated — new component, its edges, sync vs async
- [ ] `AGENTS.md` updated **only if** a command or repo-rule changed

## Definition of done

- [ ] Step 0 answered in writing, with the named failure mode
- [ ] Sync/async chosen deliberately; Outbox + idempotency if async
- [ ] Scaffold checklist complete (stateless, health, logs, audit, config, metrics)
- [ ] Tests written and passing
- [ ] Diagram + design doc updated; rejected alternative recorded
