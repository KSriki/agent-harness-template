# Spec: 〈feature name〉

> Copy this per feature. Keep it short and **living** — update it as decisions change.
> Behavior, not implementation. Every acceptance criterion must map to a test.

**Status:** 〈draft | in-progress | shipped〉 · **Owner:** 〈you〉 · **Updated:** 〈date〉

## 1. Goal (why)

〈1–2 sentences. The problem and who it's for. If you can't state the problem, stop.〉

## 2. Non-goals

〈What this explicitly does NOT do. Bounds the agent — the most useful section.〉

## 3. Actors & inputs

〈Who/what calls this, and the inputs (shape, source, trust level).〉

## 4. Acceptance criteria (EARS — each line is a test)

<!-- When <trigger> · While <state> · If <cond> then · Where <feature> · (ubiquitous) The system shall … -->

- [ ] 〈When a submission PDF is uploaded, the system shall extract 〈fields〉 and return them as JSON.〉
- [ ] 〈If a required field is missing, then the system shall reject with 422 naming the field.〉
- [ ] 〈While a request is over 〈N〉 pages, the system shall 〈…〉.〉
- [ ] 〈The system shall never 〈log PII / call an un-allowlisted host / …〉.〉

## 5. Contracts / data

〈The interface other code (or parallel workers) depends on: types, signatures, API
 shape, DB changes. If this feeds `orchestrate-agents`, THIS is the shared contract —
 nail it before splitting work.〉

## 6. Constraints

〈Performance budget, cost/token budget, security rules, environments, backward-compat.〉

## 7. Increment plan

〈Slice into testable pieces. Each is independently verifiable; each could be an
 `orchestrate-agents` worker with a clear ownership boundary.〉

1. 〈Increment 1 — …〉 → verifies criteria: 〈#1〉
2. 〈Increment 2 — …〉 → verifies criteria: 〈#2, #3〉

## 8. Verification

〈How each criterion is tested (unit/integration/eval). For non-deterministic output,
 point at `eval-harness`, not `run-tests`.〉

## 9. Open questions

〈Unknowns that could change the spec. Resolve before/while building; don't let the
 agent guess an answer and bake it in silently.〉
