---
name: grill-me
description: >
  Use to grill the user relentlessly about a plan, decision, or idea — a
  frontier-batched interview down the design tree (rounds of ready questions,
  each with a recommended answer) until confirmed shared understanding, BEFORE any
  work starts. Triggers on "grill me", "grill this plan", "stress-test my
  thinking", "poke holes in this", "what am I missing before I build",
  "interview me about this".
  Do NOT use to gather facts you could look up yourself (look them up — don't ask),
  to score model outputs (`eval-harness`), to write the design record
  (`write-design-doc`), or to decompose a big initiative into tickets (`wayfinder`).
---

# Grill me: interrogate the plan before you build

> Adapted from `mattpocock/skills` (MIT), v1.2 — the frontier-rounds rework.
> v1.2 replaced one-question-at-a-time (our previous version) with batched rounds:
> same depth, a third of the turns.

## When to use this

Before committing to a plan or design, when being wrong is cheaper to fix now than
after it's built. The goal is **confirmed shared understanding**, not a vibe check.

**Not this skill if:** you need a discoverable fact — read it, don't ask. You're
scoring outputs → `eval-harness`. You're recording the decision → `write-design-doc`.
You're mapping a large initiative into tickets → `wayfinder`.

## The interview: work the question frontier, in rounds

Map the subject as a **design tree** — every decision branches into the decisions
hanging off it. Then:

1. **The frontier** = every decision whose prerequisites are already settled — the
   questions you can ask *now* without guessing at answers you haven't heard yet.
2. **Ask the whole frontier in one round.** Number each question and give your
   recommended answer, then wait for ALL answers before the next round. A question
   that depends on another question still open *this* round belongs to a *later*
   round.
3. **Per-question format** (scannable, answer-in-bulk friendly):

   ```
   ❓ **Q1 — <question title>**: <question body; may include choices>

   ➡️ <your recommended answer, and why in a phrase>
   ```

4. **Each answered round reshapes the tree.** Settled decisions push the frontier
   outward; recompute it and ask the next round. Early rounds may be a single
   critical question; endgame rounds sweep up the easy ones in one pass.
5. **Facts vs decisions.** Finding *facts* is your job, never the user's — a
   frontier question that needs an environment fact gets a **subagent dispatched
   non-blocking** (`code-searcher` / `debug-research`): a running exploration is an
   unsettled prerequisite, so only its downstream questions wait — ask the rest of
   the frontier now. The *decisions* are the user's: put each to them and wait.
6. **Exit:** done when **the frontier is empty** — every branch visited, nothing
   left silently assumed. **Do not act until the user confirms** shared
   understanding is reached. The confirmation is the gate.
7. **Persist the intent.** On confirmation, write the settled understanding to
   `intent/<slug>.intent.md` in the originator's own words: problem, proposed
   outcome, affected users/systems, constraints, decisions made, open questions.
   This is the first link of the artifact chain — `write-a-prd` reads it, and a
   fresh agent can resume from it without this transcript. Propose the commit;
   don't commit unasked (conservative profile).

> Prefer the old cadence? Say "ask one question at a time" — the rounds are a
> default, not a law.

## Definition of done

- [ ] The design tree walked to an **empty frontier** — no branch silently assumed
- [ ] Every question carried a **recommendation**; rounds respected dependencies
- [ ] Facts were **looked up (subagents, non-blocking)**, never asked
- [ ] The human **explicitly confirmed** shared understanding — only then does work start
- [ ] Confirmed understanding persisted as `intent/<slug>.intent.md` — an artifact, not just chat
