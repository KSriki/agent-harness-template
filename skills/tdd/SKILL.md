---
name: tdd
description: >
  Use to build a feature or fix a bug TEST-FIRST — the red→green loop that constrains
  the agent to write a failing test, then the minimal code to pass it, one vertical
  slice at a time. Triggers on "TDD", "red-green-refactor", "test-first", "write the
  test first", "build this test-driven". Covers what a good test is, where seams go,
  mocking, and the loop rules.
  Do NOT use for the full local quality-gate sequence or test-AFTER existing code
  (that's `run-tests` — tests assert, the gate runs) or for scoring non-deterministic
  LLM output (`eval-harness`).
---

# TDD: red before green

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

Building a slice test-first, so the test pins the behavior before the code exists.
This is the *discipline*; `run-tests` is the *gate* you run afterward.

**Not this skill if:** you're running the full lint/type/coverage gate, or writing
tests for code that already exists → `run-tests`. You're scoring model outputs →
`eval-harness`.

Read `CONTEXT.md` first (if present) so test names/vocabulary match the domain.

## What a good test is

Verifies behavior through the **public interface**, not implementation details; reads
like a specification; **survives refactors**; one logical assertion. (Interface
vocabulary from `codebase-design`.)

## Seams — where tests go

A **seam** is the public boundary you observe behavior at. **Test only at pre-agreed
seams** — write the seams down and **confirm with the human before writing any test**;
no test at an unconfirmed seam. Ask: *"What's the public interface, and which seams
should we test?"*

## The loop (rules)

1. **Red before green** — a failing test first, then the **minimal** code to pass it.
   No speculative features.
2. **One slice at a time** — one seam, one test, one minimal implementation per cycle
   (a vertical tracer bullet — never all-tests-then-all-code).
3. **Refactoring is NOT part of the loop** — it belongs to the review stage
   (`review-pr`). Green first; clean up under review.

## Anti-patterns (don't write these)

| Anti-pattern | Tell | Instead |
|---|---|---|
| **Implementation-coupled** | mocks internal collaborators · tests privates · asserts call counts; breaks on refactor with no behavior change | assert observable behavior through the public interface |
| **Bypassing the interface** | verifies via `SELECT * FROM …` / internal state | verify via the interface (`getUser(id)`) |
| **Tautological** | expected value recomputed the way the code does it | expected comes from an **independent** source — a literal, a worked example, the spec |
| **Horizontal slicing** | all tests, then all impl | vertical slices: one test → one impl → repeat |

## Mocking (only at system boundaries)

**Mock:** external APIs, sometimes the DB (prefer a test DB), time/randomness,
sometimes the filesystem. **Don't mock** your own modules/internal collaborators.
Design for it: **inject dependencies** (`processPayment(order, paymentClient)`), and
prefer **SDK-style interfaces** (`getUser`, `createOrder`) over one generic `fetch()`.

## Definition of done

- [ ] Seams confirmed with the human **before** any test written
- [ ] Every cycle: **red → minimal green**, one vertical slice
- [ ] Tests assert behavior through the interface — no implementation coupling, no tautology
- [ ] Mocks only at true boundaries; deps injected
- [ ] Refactor deferred to review (`review-pr`), not smuggled into the loop
