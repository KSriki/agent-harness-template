---
name: improve-codebase-architecture
description: >
  Use to audit an EXISTING codebase for "deepening opportunities" — refactors that
  turn shallow modules into deep ones for testability + AI-navigability — present them
  as a self-contained visual report, then grill through whichever one you pick.
  Triggers on "improve the architecture", "find refactoring opportunities", "this
  code is hard to navigate/test", "audit the codebase design", "where's the tech debt".
  Do NOT use to choose a NEW pattern for a new decision (`architecture-patterns`), to
  design one module's interface in isolation (`codebase-design`), or to review a
  specific PR/design (`review-pr` / the `design-reviewer` agent).
---

# Improve codebase architecture

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.
> Built on the `codebase-design` vocabulary — module · interface · depth · seam ·
> adapter · leverage · locality · the deletion test. Use those terms exactly.

## When to use this

Auditing code that already exists for structural improvement — not choosing a pattern
for something new. Domain names come from `CONTEXT.md`; ADRs in 〈`docs/adr/` / `docs/design/`〉
are respected, not re-litigated.

**Not this skill if:** it's a *new* pattern choice → `architecture-patterns`. It's one
module's interface → `codebase-design`. It's reviewing a specific change →
`review-pr` / `design-reviewer`.

## Procedure

### 1. Explore (scope before scanning — YAGNI)

- If the human named a direction, take it. Else walk `git log --oneline` for **hot
  spots** (recently/frequently changed files) and start there; widen only if scattered.
- Read the `CONTEXT.md` glossary + relevant ADRs **first**.
- Delegate the walk to the **`Explore` subagent** (Agent tool) — it reads broadly and
  reports friction without polluting main context. Have it note:
  - understanding a concept requires **bouncing between many small modules**;
  - **shallow** modules (interface ~ as complex as the implementation);
  - pure functions extracted *only* for testability, where real bugs hide in the call
    sites (no **locality**);
  - tightly-coupled modules **leaking across seams**;
  - untested / hard-to-test-through-the-interface areas.
- Apply the **deletion test**: would collapsing this *concentrate* complexity (signal)
  or just move it around (not yet)?

### 2. Present candidates as a SELF-CONTAINED report

Write a **single self-contained HTML file** to a scratch location 〈`$TMPDIR` /
`.scratch/`〉, `architecture-review-<label>.html`. **Inline all CSS/JS and embed any
diagram assets — no CDN / external hosts** (our artifact policy; do not load Tailwind
or Mermaid from a CDN — inline them or hand-draw SVG). Then **offer** to open it and
print the absolute path (don't auto-shell without asking).

Per-candidate card: **Files · Problem · Solution (plain English) · Benefits (in terms
of locality & leverage, and testability) · Before/After diagram · Recommendation
badge** (`Strong` / `Worth exploring` / `Speculative`). End with a **Top
recommendation**. Use `CONTEXT.md` vocabulary for the domain, `codebase-design`
vocabulary for the architecture. Surface an ADR conflict **only** when the friction
genuinely warrants reopening it, and mark it clearly (*"contradicts ADR-0007 — but
worth reopening because…"*). **Do not propose interfaces yet** — after writing the
file, ask *"Which of these would you like to explore?"*

### 3. Grill through the pick

Once a candidate is chosen, run **`grill-me`** to walk the decision tree (constraints,
dependencies, the shape of the deepened module, what sits behind the seam, which tests
survive). Record side effects inline via **`domain-modeling`**: a new concept →
add it to `CONTEXT.md`; a fuzzy term sharpened → update it; a candidate rejected for a
**load-bearing** reason → offer an ADR (only if a future explorer would need it). Want
alternative interfaces → **`codebase-design`** "design it twice."

## Definition of done

- [ ] Scanned hot-spots first (scoped, not the whole tree); `CONTEXT.md` + ADRs read
- [ ] Candidates found via the deletion test, described in `codebase-design` terms
- [ ] **Self-contained** report (no external hosts); auto-open only if the human agreed
- [ ] Interfaces NOT pre-proposed; human picked a candidate, then grilled
- [ ] Model side-effects (glossary/ADR) recorded via `domain-modeling`
