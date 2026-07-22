---
name: wayfinder
description: >
  Use to plan a body of work too big for one agent session — by charting it as a
  map of DECISION tickets on your issue tracker, then resolving those decisions one
  at a time until the route to a defined destination is clear. Triggers on "this is
  too big for one session", "we need to figure out the plan before building", "map
  out this initiative", "chart the work", "what do we need to decide first",
  "wayfinder". Produces decisions, not deliverables. Also the RE-ENTRY point
  mid-build: when you or an agent surfaces a new idea or workaround, chart it here
  instead of improvising it into the build.
  Do NOT use to cut build tickets from a settled plan (`prd-to-issues`), to BUILD
  them (`tdd` / `orchestrate-agents`), for a single expensive-to-reverse decision
  (`write-design-doc`), for the rung check (`new-service`), or to research one
  external question (`debug-research`).
---

# Wayfinder: chart the decisions before you build

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

Two moments, one skill:

- **Planning a new feature on an existing project** — the route isn't visible yet,
  too big for one session, full of open questions. Chart the decisions before the
  PRD/tickets get cut.
- **Mid-build re-entry** — you or an agent hits a new idea, a workaround, or a
  surprise. Don't improvise it into the build: chart it as a decision ticket and
  resolve it deliberately.

Wayfinder maps the **decisions** as tickets so the plan survives across many
stateless agent sessions, and so the *thinking* is done before the *building*.

**Not this skill if:** the plan is settled and needs build tickets → `prd-to-issues`.
It's one irreversible design call → `write-design-doc`. It's "should this be its own
service" → `new-service`.

## The core idea

> **You chart DECISIONS, not tasks.** A wayfinder ticket is a *question whose
> resolution is a decision* — not a slice of work to execute.

The urge to "just start building" is the signal you've hit the **edge of the map** —
what's past it isn't decided yet. Turn that urge into a ticket, don't act on it.

## Prerequisites

- An issue tracker to hold the map: 〈GitHub Issues · Linear · or local files in `docs/plans/`〉.

## Procedure

### Chart mode — map the frontier (decides nothing; that's correct)

1. **Name the destination.** Run a `grill-me` / domain pass until you can state, in
   a sentence, what "done" looks like. A map with no destination is a wander.
2. **Create the map issue** (label `wayfinder:map`) with sections:
   **Destination · Decisions-so-far · Not-yet-specified (the fog) · Out-of-scope.**
3. **Break the frontier into decision tickets** — one open question each, typed by
   label 〈`wayfinder:research` · `prototype` · `grilling` · `task`〉. Then a second
   pass wires **blocking** relationships (the tracker's native dependency links) so
   the unblocked frontier is visible at a glance.
4. **Fan out** `debug-research` subagents for the research tickets — in parallel.
5. **Stop.** Charting resolves nothing; resist finishing decisions here.

### Work mode — resolve one decision per session

6. Load the map, **claim the next unblocked frontier ticket** (assign it to
   yourself — assignment is the concurrency lock).
7. **Resolve exactly one decision** (research tickets excepted), post the resolution
   as a comment, close it, and append a **one-line gist to Decisions-so-far**.
8. **Graduate the fog:** questions newly made answerable become fresh tickets.
9. Repeat until the frontier is empty.

### Hand off to execution

When no undecided questions remain, the route is clear — hand the now-concrete plan
to `write-a-prd` (capture it) → `prd-to-issues` (cut the tickets) → `tdd` /
`orchestrate-agents` (build them).

## Conventions

- **Refer to issues by title, never bare id** — ids are meaningless across sessions.
- **Classify each ticket HITL vs AFK** so a human knows what needs them.
- The **map is the single source of truth** — if it's not on the map, it isn't decided.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Charting turned into building | Resolved decisions in chart mode | Chart maps the frontier; resolve in work mode, one at a time |
| Map went stale, nobody trusts it | Decisions made in-session, not recorded | Every resolution → a Decisions-so-far line + close the ticket |
| Everything's "blocked" | Blocking edges not wired, or fake dependencies | Second-pass the edges; only real blockers block |
| Endless planning, never ships | No named destination | Step 1 — you can't chart a route with no endpoint |

## Definition of done

- [ ] A `wayfinder:map` issue exists with a **named destination**
- [ ] Every open question is a **decision ticket**, blockers wired
- [ ] The frontier is **empty** — no undecided questions, no open tickets
- [ ] Each closed ticket has a recorded answer + a one-line map entry
- [ ] The clear plan is handed to `write-a-prd` → `prd-to-issues` → build
