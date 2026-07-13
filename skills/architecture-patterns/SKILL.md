---
name: architecture-patterns
description: >
  Use when making an architectural or design decision: choosing between patterns,
  deciding sync vs async, picking a caching or data strategy, deciding whether to
  split a service, choosing a scaling approach, evaluating whether an agent or a
  workflow is right, or reviewing a design against known anti-patterns. Triggers
  on "should we use X or Y", "what's the right pattern for", "how should we
  structure", "is this over-engineered", CQRS/event-sourcing/saga/outbox/CDN/
  circuit-breaker questions, and any conversation about scaling or coupling.
  Do NOT use for writing the design doc itself — that's `write-design-doc`; and
  not for scaffolding a new component — that's `new-service`.
---

# Architecture pattern selection

## When to use this

You're choosing *how* to build something and the choice has consequences. This
skill routes you to the right pattern and the right depth of reading.

**Not this skill if:** you're *writing the doc* → `write-design-doc`. You're
*scaffolding a component* → `new-service` (which has the rung gate).

## The two-tier reference

1. **`docs/architecture-patterns.md`** — compressed agent reference. Decision rules
   and triggers. **Read this first.** It covers most decisions.
2. **The full KB** (`docs/architecture-patterns-FULL-KB.md`, ~1,800
   lines) — the depth. **Open it at the cited § when the penalty for being wrong is
   high.**

**Do not guess from the summary on an expensive decision.** The compressed file
tells you *what* and *when*; the KB tells you *why*, with the failure modes.

---

## Procedure

### 1. Name the problem, not the pattern

The most common failure is arriving with a pattern and looking for a justification.
State the *problem* first — "reads are slow and the same row is fetched 500×/day" —
and let the pattern fall out of it.

### 2. Which pillar is under pressure? (§0.5)

`Scalability` · `Availability` · `Maintainability` · `Performance` · `Cost`

**Security and Observability are not tradeable.** If a proposal trades them away,
something upstream is wrong.

### 3. What's the LOWEST rung that solves it? (§0.7)

> `0` script → `1` monolith → **`2` modular monolith** → `3` a few services →
> `4` microservices → `5` serverless

**Each rung ~doubles operational complexity.** Rung 2 is where most systems should
stop. **Name the specific failure mode of the rung below** — if you can't, stay put.

**If a model is involved (§0.9):** *can you enumerate the steps in advance?*
**Yes → workflow, not an agent.** Most "agents" are workflows in costume, and
crossing into autonomy has a real architectural payload (decision-path
observability, evals, cost variance, containment).

### 4. Look up the pattern

Open `docs/architecture-patterns.md`. Find the decision. Note the **§ reference**.

### 5. Penalty for being wrong?

| Expensive / irreversible → **open the full KB** | Cheap / reversible → **just pick one** |
|---|---|
| Storage engine, schema shape | A library version |
| Service boundary | Log format |
| Sync vs async coupling | Internal naming |
| Auth model | Folder layout |
| Event sourcing, CQRS, sharding | A config default |

### 6. Name the tax, record the rejected option

Every pattern costs something. Say it out loud so it's an intentional purchase.
Then record what you *didn't* pick and why → that's the part that gets reviewed.

---

## The decisions this comes up for most

| Question | Go to |
|---|---|
| Split this into a service? | §0.7 ladder + `new-service` gate. Default: **no.** |
| Sync or async? | §4. *What happens when the callee is down?* Non-critical breaking critical → **async.** |
| Publishing an event after a DB write? | **§3.7 Outbox. Mandatory.** Otherwise it's a dual-write bug. |
| Async — anything else I must do? | **Idempotent consumers** (at-least-once) + eventual consistency is user-visible. |
| Cache this? | §7. **Small/hot/structured → Redis. Large blobs → CDN. Never a 20MB video in Redis.** |
| Scale out? | §2A. **Requires statelessness** — verify that first. `min=2`. |
| CQRS / Event Sourcing? | §3.1/3.2. **Usually no.** High cost, frequently over-applied. Need a named reason. |
| Agent or workflow? | §0.9.4. **Can you enumerate the steps? → workflow.** |
| Replacing a legacy system? | §6.1 **Strangler Fig** — default. §6.4 Parallel Run for high confidence. |
| Is this design bad? | §10 anti-patterns. Check **distributed monolith** and **shared DB** first. |
| Need 4 mocks to test it? | §1B.4 — **the design is wrong.** Don't mock harder. I/O leaked into the domain. |

---

## Definition of done

- [ ] Problem named before the pattern
- [ ] Pillar under pressure identified
- [ ] **Lowest viable rung chosen**, with the failure mode of the rung below named
- [ ] Full KB opened if the decision is expensive/irreversible
- [ ] **Tax named**; rejected alternative recorded
- [ ] Checked against §10 anti-patterns
