---
name: spec-driven-development
description: >
  Use to build a feature the reliable way: write a short, testable SPEC first
  (behavior + acceptance criteria), then have an agent implement it in small
  verified increments — instead of "vibe coding" from a vague prompt and letting the
  result drift. Triggers on "write a spec", "spec-driven", "spec first", "acceptance
  criteria", "EARS", "turn this ticket into a spec", "the agent keeps building the
  wrong thing". Covers spec quality, EARS acceptance criteria, increments, and the
  spec→implement→verify loop.
  Do NOT use for a design decision that's expensive to reverse (schema, boundary,
  auth model) — that's a design doc, `write-design-doc`. Not for a trivial change
  (just do it). Not for running the tests themselves (`run-tests`).
---

# Spec-driven development

## When to use this

Any non-trivial feature you're about to hand (partly or wholly) to an agent. The
spec is the antidote to the #1 agentic failure mode: **confident, plausible code
that quietly solves the wrong problem** because nothing pinned down what "right"
means. Write the spec, and the agent has explicit goals, constraints, and a
finish line — and *you* have something to verify against.

**Not this skill if:** the decision is architectural and hard to reverse →
`write-design-doc` (that's an ADR; this is a build spec). It's a one-line change →
just do it. You're scoring the output → `run-tests` / `eval-harness`.

**Rule of thumb (current practice):** *vibe-code throwaway prototypes; spec-drive
anything that ships.*

## The loop

```
SPEC ──▶ PLAN ──▶ IMPLEMENT (one increment) ──▶ VERIFY vs acceptance criteria ──▶ (next increment)
 ▲                                                          │
 └──────────────── update the spec as decisions change ◀────┘   (the spec is a living doc)
```

## 1. Write the spec — what makes it good

A good spec is:
- **Behavior-focused** — *what* happens, not *how* it's coded.
- **Testable** — every requirement is verifiable; if you can't test it, it's a wish.
- **Unambiguous** — two readers reach the same interpretation.
- **Complete, not over-specified** — cover the essential cases; don't design the code.

Use the template: `spec-template.md` (copy it per feature).

## 2. Acceptance criteria in EARS

**EARS** (Easy Approach to Requirements Syntax) makes criteria unambiguous to both
humans and models, and each line maps almost 1:1 onto a test:

| Pattern | Shape |
|---|---|
| Ubiquitous | The system shall `<response>` |
| Event | **When** `<trigger>`, the system shall `<response>` |
| State | **While** `<state>`, the system shall `<response>` |
| Unwanted | **If** `<condition>`, **then** the system shall `<response>` |
| Optional | **Where** `<feature included>`, the system shall `<response>` |

> "When an uploaded submission is missing a required field, the system shall reject
> it with a 422 naming the field." → that's one criterion **and** one test.

## 3. Implement in small, verified increments

Do **not** hand over the whole spec and walk away. Slice it into increments that each
deliver one testable piece. After each: **verify against its acceptance criteria**
(the criterion *is* the test — see `run-tests`), then move on. This is what keeps the
agent from drifting over a long build, and it's what makes parallelizing safe (each
increment can become an `orchestrate-agents` worker with a clear contract).

## 4. Keep the spec alive

When you or the agent change the data model, cut a case, or discover a constraint —
**update the spec.** A stale spec is worse than none: it lies about ground truth.
The prompts you used are part of the artifact too; keep the good ones.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Agent built the wrong thing, confidently | No spec / vague spec | Write behavior + acceptance criteria first |
| Spec argued over, means different things | Prose, not EARS | Rewrite criteria in EARS; one interpretation |
| Huge diff, hard to verify | Whole spec handed over at once | Slice into increments; verify each |
| Spec no longer matches the code | Treated as write-once | Update it as decisions change — living doc |
| Over-built to the spec | Spec described *how*, not *what* | Keep it behavior-focused; leave the how to implementation |

## Definition of done

- [ ] Spec written: behavior-focused, **testable**, unambiguous, not over-specified
- [ ] Acceptance criteria in **EARS**, each mapping to a test
- [ ] Implemented in **increments**, each verified against its criteria before the next
- [ ] Tests exist for the acceptance criteria and are green (`run-tests`)
- [ ] Spec updated to match the final decisions (living doc)

## Reference files

- `spec-template.md` — copy per feature; the fill-in spec structure (EARS criteria + increment plan).
