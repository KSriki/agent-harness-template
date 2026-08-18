---
name: writing-for-agents
description: >
  Use when creating or editing anything an AGENT reads — skills, AGENTS.md,
  CLAUDE.md, subagent definitions, steering rules, or docs reached by pointer.
  The craft reference: context pointers, information hierarchy, completion
  criteria, leading words, pruning. The goal is the agent taking the same PROCESS
  every run.
  Do NOT use for human-facing docs (steering §8), for the harness-change PROCESS
  (`evolve-harness` — that's the gate; this is the craft), or for the skill file
  scaffold itself (`skills/_TEMPLATE`).
---

# Writing for agents

> Adapted from `mattpocock/skills` (MIT), v1.2 (`writing-for-agents`, née
> `writing-great-skills`). The packaging differs — skill, AGENTS.md, agent file —
> **the writing does not.**

## What good looks like

An agent-facing document succeeds when the agent takes the **same process every
run** — not the same output. Every technique below serves that: predictable
reach, predictable execution, predictable stopping.

## 1. Context pointers

A pointer = an in-context reference naming out-of-context material **plus the
condition for reaching it**. A skill's `description`, a row in the AGENTS.md
skills table, a "see X when Y" line — same object.

- **The pointer's WORDING, not its target, decides whether it gets reached.** A
  weak pointer over a must-have target is a variance bug: **sharpen the wording
  first; inline the material only if sharpening fails.**
- Front-load the leading word. One trigger per branch — collapse synonyms.
- Cut identity the body already carries (the body doesn't need to re-say what it is).

## 2. The information hierarchy (and the two loads)

Two costs: **context load** (always-loaded material — paid in tokens and attention
every turn) and **cognitive load** on the human as index (not a cost to minimize —
it's the price of human agency).

The three-rung ladder for any piece of material:
1. **In-file step** — every run needs it.
2. **In-file reference** — every run *might* consult it.
3. **Disclosed reference behind a pointer** — only some branches reach it.

**Progressive disclosure** is the move down the ladder — framed as protecting the
hierarchy, not saving tokens. The cleanest test is **branching**: inline what every
branch needs; push behind a pointer what only some branches reach. **Co-locate** a
concept's definition, rules, and caveats under one heading; a doc can be **sprawl**
even when every line is live — split it.

## 3. Steps and completion criteria

Every step ends on a completion criterion with two properties:

- **Clarity** — a vague bound invites *premature completion*. Defense order:
  sharpen the bound first; only then hide later steps — and hiding only works
  across a **real context boundary** (a hand-off or a subagent dispatch), never
  within one context.
- **Demand** — the criterion must force the legwork. *"Every modified module
  accounted for"* demands; *"produce a change list"* doesn't. Demand binds flat
  reference too: *"every rule applied."*

Split a document **by sequence** when post-completion steps tempt rushing, or
**by invocation** when different triggers want different bodies (see rung 3).

## 4. Leading words

A **leading word** is a pretrained, compact concept the agent thinks with —
*tight*, *red*, *tracer bullets*, *frontier*. Repeat it as a token, never expand it
into a sentence; it anchors execution in the body and invocation in pointers.
("fast, deterministic, low-overhead" → *tight*. "a failing test you believe in" →
*red*.)

**The companion failure is negation:** *"don't think of an elephant"* — and the
elephant is all there is. Prompt the positive. A prohibition earns its place only
as a hard guardrail that can't be phrased positively — and even then, pair it with
the positive target.

## 5. Pruning

- **Single source of truth.** Duplication is how two copies drift (this repo's
  docs/README.md discipline — same rule, smaller scale).
- **The environment is a source of truth.** A doc restating `package.json` is a
  **cache** — cache only what the agent *cannot find by looking*.
- **Sediment:** lines that were once load-bearing and now aren't. Check relevance,
  not just truth.
- **The no-op test**, sentence by sentence, model-relative: would the agent behave
  differently without this sentence? *"Be thorough"* is a no-op — the fix is a
  stronger word (*relentless*), not more words. Settle disputes **by running the
  document, not by debate.** Delete whole sentences.

## Skill-file mechanics (this harness)

- Structure and description rules live in `skills/_TEMPLATE/SKILL.md` — triggers
  not topics, the NOT-clause, exact commands.
- **Model-invoked** skills keep a `description` (permanent context load; other
  skills can reach them). A `disable-model-invocation: true` skill costs zero
  context but **no other skill can ever invoke it** — shared reference between two
  such skills must live in a plain file both point at.
- Every change to an agent-facing doc is a behavior change → the `evolve-harness`
  gate and, for `docs/`, a CHANGELOG entry.

## Definition of done

- [ ] Pointers worded to be reached (leading word front-loaded, one trigger per branch)
- [ ] Material on the right rung; every-branch content inline, some-branch content disclosed
- [ ] Every step ends on a criterion with **clarity + demand**
- [ ] Positives prompted; prohibitions only as paired hard guardrails
- [ ] No-op test run sentence-by-sentence; caches and sediment deleted
- [ ] Verified by **running the document**, not by rereading it
