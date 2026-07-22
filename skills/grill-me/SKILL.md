---
name: grill-me
description: >
  Use to grill the user relentlessly about a plan, decision, or idea — a
  one-question-at-a-time interview down the decision tree to reach confirmed shared
  understanding BEFORE any work starts. Triggers on "grill me", "grill this plan",
  "stress-test my thinking", "poke holes in this", "what am I missing before I
  build", "interview me about this".
  Do NOT use to gather facts you could look up yourself (look them up — don't ask),
  to score model outputs (`eval-harness`), to write the design record
  (`write-design-doc`), or to decompose a big initiative into tickets (`wayfinder`).
---

# Grill me: interrogate the plan before you build

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

Before committing to a plan or design, when being wrong is cheaper to fix now than
after it's built. The goal is **confirmed shared understanding**, not a vibe check —
this is the discipline that separates a senior engineer from an eager one.

**Not this skill if:** you need a discoverable fact — read it, don't ask. You're
scoring outputs → `eval-harness`. You're recording the decision → `write-design-doc`.
You're mapping a large initiative into tickets → `wayfinder`.

## The interview

1. **Walk every branch of the decision tree**, resolving dependencies between
   decisions **one by one** — don't jump around.
2. **One question at a time. Never batch.** Multiple questions at once is bewildering
   and gets shallow, averaged answers. One sharp question keeps momentum.
3. **Lead with your recommended answer**, then ask. A question with no recommendation
   is lazy — you've thought about this, so say what you'd do and why, *then* ask.
4. **Facts vs. decisions.** Anything discoverable from the repo, the docs, the tools,
   or the environment — **look it up yourself.** Pestering the human for lookup-able
   facts burns trust. Reserve every question for a genuine **decision** only they can make.
5. **Do not act** on the plan until the human **confirms** shared understanding is
   reached. The confirmation is the gate.

## Definition of done

- [ ] Every open **decision** (not fact) surfaced and resolved, in dependency order
- [ ] Each asked **one at a time**, recommendation-first
- [ ] Facts were **looked up**, not asked
- [ ] The human **explicitly confirmed** shared understanding — only then does work start
