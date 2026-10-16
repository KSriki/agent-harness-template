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
  (`write-design-doc` / `adr`), or to cut the tickets (`prd-to-issues`).
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
You're cutting tickets from a settled plan → `prd-to-issues`.

## Round 0 — the premise round (before the tree opens)

The design tree has a root every later question silently assumes: **"should this
exist at all?"** Walking the tree without visiting the root is how a model helps
you build a bad idea well. So, before Round 1:

1. **Build the case against — offline.** This environment has no internet, so the
   outside view comes from what is on disk and in the room: existing ADRs
   (`docs/adr/`) and design docs that touched this area, the platform's own
   incident/retro notes, the steering doc's ladder (§0), and the user's knowledge
   of what the organisation tried before. Ask the user for the prior art they know
   of as part of Round 0 — that is a fact-finding question, not a decision.
2. **Present the verdict with the first round:** the strongest case against (with
   its source — "ADR-0007 rejected this in June", "nothing on disk argues
   against it"), the proposed kill criteria, and your PROCEED / RETHINK
   recommendation — same ❓/➡️ format as every other question. The user rules on
   the premise like any other decision.
3. **Kill criteria are mandatory output.** 2–4 falsifiable *"this was a bad idea
   if…"* conditions go into the intent doc. If neither you nor the user can name
   one, say so out loud — that is a finding about the premise, not a formality
   to skip.
4. **On RETHINK — warn, then let the human bet.** Present the evidence as
   *"here's what the record says — are you sure you want to continue?"* and
   **pause until the user explicitly rules**. Silence is not consent — but **an
   informed override is a fully legitimate outcome**: contrarian bets are how new
   things get built, and this round exists to make the bet *informed*, never to
   veto it. An override is recorded in the intent doc (the evidence overridden,
   the user's reasoning, kill criteria armed) and, if it changes architecture, as
   an `adr` — that record is what separates a bet from a blind spot.
5. **Skip condition (stated, never silent):** an internal-only, cheap-to-reverse
   change needs no outside view — skip Round 0 and say so in one line.

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
   non-blocking** (`code-searcher`; `helm template` / `kubectl explain` / `az` reads
   for platform facts): a running exploration is an
   unsettled prerequisite, so only its downstream questions wait — ask the rest of
   the frontier now. The *decisions* are the user's: put each to them and wait.
6. **Exit:** done when **the frontier is empty** — every branch visited, nothing
   left silently assumed. **Do not act until the user confirms** shared
   understanding is reached. The confirmation is the gate.
7. **Persist the intent.** On confirmation, write the settled understanding to
   `intent/<slug>.intent.md` in the originator's own words: problem, proposed
   outcome, affected users/systems, constraints, decisions made, open questions —
   plus, from Round 0: the **kill criteria** (falsifiable "this was a bad idea
   if…" conditions), the premise verdict, and any **override record** (evidence
   overridden + the user's reasoning).
   This is the first link of the artifact chain — `write-a-prd` reads it, and a
   fresh agent can resume from it without this transcript. Propose the commit;
   don't commit unasked (conservative profile).

> Prefer the old cadence? Say "ask one question at a time" — the rounds are a
> default, not a law.

## Definition of done

- [ ] **Round 0 ran** (or its skip was stated in one line): premise verdict presented,
      **kill criteria** captured; a RETHINK was ruled on by the human — override or
      retreat, but never silence
- [ ] The design tree walked to an **empty frontier** — no branch silently assumed
- [ ] Every question carried a **recommendation**; rounds respected dependencies
- [ ] Facts were **looked up (subagents, non-blocking)**, never asked
- [ ] The human **explicitly confirmed** shared understanding — only then does work start
- [ ] Confirmed understanding persisted as `intent/<slug>.intent.md` — an artifact, not just chat
