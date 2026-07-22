---
name: prd-to-issues
description: >
  Use to break a plan, spec/PRD, or the current conversation into a set of
  tracer-bullet tickets — each a narrow-but-complete vertical slice, declaring its
  blocking edges — published to the configured tracker. Triggers on "break this into
  issues/tickets", "turn the PRD into issues", "create the tickets", "slice this
  into work", "what's the dependency order".
  Do NOT use to write the product spec itself (`write-a-prd`, run before this), to
  map open DECISIONS for fuzzy work (`wayfinder`), or to run parallel agents on the
  tickets (`orchestrate-agents`, run after).
---

# PRD → issues (tracer-bullet tickets)

> Adapted from `mattpocock/skills` (MIT, `to-tickets`) — reimplemented in this repo's style.

## When to use this

A settled plan/spec exists and you need **buildable tickets** in dependency order.
Each ticket is a **tracer bullet**: a thin, complete path through every layer that's
independently demoable — not a horizontal "do all the schema" slice.

**Not this skill if:** the spec isn't written → `write-a-prd`. There are open
*decisions* to resolve first → `wayfinder`. You're executing the tickets in parallel
→ `orchestrate-agents`.

## Procedure

1. **Gather context.** Work from the conversation; if given a reference (spec path,
   issue #/URL), fetch and read its full body + comments.
2. **Explore the codebase (optional).** Use domain-glossary vocabulary; respect ADRs;
   look for **prefactoring** — *"make the change easy, then make the easy change."*
3. **Draft vertical slices.** Tracer-bullet rules:
   - each slice cuts a **narrow but COMPLETE** path through every layer (schema · API · UI · tests) — **vertical, not horizontal**;
   - independently **demoable / verifiable**;
   - sized to a **single fresh context window**;
   - prefactoring first.
   - Each ticket **declares its blocking edges** (tickets that must finish first); no-blocker tickets can start immediately.
   - **Wide-refactor exception:** one mechanical change with large blast radius → sequence as **expand → migrate (in batches, each blocked by expand) → contract** (delete the old form, blocked by every migrate). If batches can't each stay green, share an integration branch that all block a final integrate-and-verify ticket.
4. **Quiz the human.** Present the breakdown as a numbered list; per ticket show
   **Title · Blocked by · What it delivers.** Ask: granularity right? blocking edges
   correct? merge or split any? Iterate until approved.
5. **Publish to the tracker** 〈GitHub/GitLab via native blocking / sub-issue links ·
   or local files under `.scratch/<feature-slug>/issues/NN-slug.md`, numbered in
   dependency order〉. Apply **`ready-for-agent`** unless told otherwise. Work the
   **frontier** (any ticket whose blockers are all done). **Do NOT close or modify any
   parent issue.**

## Ticket template

`# <NN> — <Title>` · **What to build** (end-to-end behavior, user's POV — not a layer
list) · **Blocked by** (numbers/titles, or "None — can start immediately") ·
**Status: ready-for-agent** · checkbox acceptance criteria. Avoid file paths / code
(same decision-snippet exception as `write-a-prd`).

## Definition of done

- [ ] Slices are **vertical tracer bullets** — each complete + demoable, context-window-sized
- [ ] **Blocking edges** declared; wide refactors sequenced expand→migrate→contract
- [ ] Human approved the breakdown (granularity + edges)
- [ ] Published in dependency order, **ready-for-agent**; no parent issue touched
