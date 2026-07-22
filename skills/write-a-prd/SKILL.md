---
name: write-a-prd
description: >
  Use to turn the CURRENT conversation into a spec / PRD and publish it to the
  project's issue tracker — no interview, just synthesis of what's already been
  discussed. Triggers on "write a PRD", "write the spec", "turn this into a spec",
  "spec this out", "productise this discussion". Produces a product-level document
  (problem, solution, user stories, decisions), labeled ready-for-agent.
  Do NOT use to INTERROGATE the idea first (that's `grill-me`, run before this), to
  record a big irreversible technical decision (`write-design-doc`), or to break the
  spec into build tickets (`prd-to-issues`, run after this).
---

# Write a PRD (spec)

> Adapted from `mattpocock/skills` (MIT, `to-spec`) — reimplemented in this repo's style.

## When to use this

The idea has been discussed and grilled; now capture it. **No interview here** —
you *synthesize what's already known* into a spec and publish it. If the thinking
isn't done yet, stop and run `grill-me` first.

**Not this skill if:** you still have open questions → `grill-me`. It's a technical
design decision → `write-design-doc`. You're breaking it into buildable tickets →
`prd-to-issues`.

## Prerequisites

- The project's tracker + label vocabulary configured (via `init-agent-harness`):
  〈GitHub via `gh` · GitLab via `glab` · local files under `.scratch/`〉.

## Procedure

1. **Explore for current state** (if not already). Use the project's **domain
   glossary** vocabulary (`domain-modeling` / `CONTEXT.md`); respect existing ADRs in
   the area you touch.
2. **Sketch the test seams.** Prefer existing seams; use the **highest seam possible**;
   propose new seams high; **fewer seams is better — the ideal is one.** Check the
   seams match the human's expectations. (Vocabulary from `codebase-design`.)
3. **Write the spec from the template** (below), publish it to the tracker, and apply
   the **`ready-for-agent`** label — no further triage.

## Spec template (sections, in order)

- **## Problem Statement** — from the *user's* point of view.
- **## Solution** — from the *user's* point of view.
- **## User Stories** — a numbered list, format *"As an `<actor>`, I want a
  `<feature>`, so that `<benefit>`"*. Be extensive.
- **## Implementation Decisions** — modules built/modified, interfaces, technical
  clarifications, architectural decisions, schema changes, API contracts, interactions.
  **No file paths or code snippets** — *exception:* inline a snippet only if it
  encodes a decision more precisely than prose, trimmed to the decision-rich part.
- **## Testing Decisions** — what makes a good test here (external behavior, not
  implementation detail), which modules, prior art.
- **## Out of Scope**
- **## Further Notes**

## Definition of done

- [ ] Spec synthesized from the discussion — **no interview**, no invented requirements
- [ ] Domain-glossary vocabulary used; ADRs in the touched area respected
- [ ] Test seams sketched (highest, fewest — ideal one)
- [ ] Published to the tracker with the **ready-for-agent** label
