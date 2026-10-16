---
name: prd-to-issues
description: >
  Use to break a plan, spec/PRD, or the current conversation into a set of
  tracer-bullet tickets — each a narrow-but-complete vertical slice, declaring its
  blocking edges — written as ticket docs under `tickets/` for the human to create
  in Jira. Triggers on "break this into tickets", "turn the PRD into issues",
  "slice this into work", "what's the dependency order", "split this ticket".
  Do NOT use to write the product spec itself (`write-a-prd`, run before this), to
  resolve open DESIGN decisions first (`grill-me` / `write-design-doc`), to build
  a ticket (`tdd`, run after), or to maintain one ticket's doc over time
  (`ticket-docs`).
---

# PRD → tickets (tracer-bullet ticket docs)

> Adapted from `mattpocock/skills` (MIT, `to-tickets`) — reimplemented in this repo's style.

## When to use this

A settled plan/spec exists and you need **buildable tickets** in dependency order.
Each ticket is a **tracer bullet**: a thin, complete path through every layer
that's independently demoable — not a horizontal "do all the values files" slice.
The output is **files**, because the tracker is Jira and the agent does not write
to Jira (`ticket-docs` §4).

**Not this skill if:** the spec isn't written → `write-a-prd`. Open *decisions*
first → `grill-me` / `write-design-doc`. Building a ticket → `tdd`.

## Procedure

1. **Gather context.** Work from the conversation and the spec on disk
   (`intent/<slug>.spec.md`, a design doc, the ADRs it cites). If the human pastes
   a Jira epic, treat its text as the spec; its key becomes the `Blocks`/parent.
2. **Explore the repo (optional).** Existing charts, pipelines, namespaces, ADR
   vocabulary; look for **prefactoring** — *"make the change easy, then make the
   easy change"* (e.g. add the values schema before the feature that needs it).
3. **Draft vertical slices.** Tracer-bullet rules:
   - each slice cuts a **narrow but COMPLETE** path (chart · manifest · pipeline ·
     test · doc) — **vertical, not horizontal**;
   - independently **demoable / verifiable** (a `helm template` diff, a smoke call
     through the gateway, a green job);
   - sized to a **single fresh context window** and to one MR of ≤ ~400 lines;
   - prefactoring first;
   - each ticket **declares its blocking edges**; no-blocker tickets start now.
   - **Wide-refactor exception:** one mechanical change with large blast radius
     (rename a release, move every chart to the OCI mirror) → **expand → migrate
     (in batches, each blocked by expand) → contract**. Each batch stays green.
4. **Quiz the human.** Present the breakdown as a numbered list; per ticket show
   **Title · Blocked by · What it delivers · first failing test.** Ask:
   granularity right? edges correct? merge or split any? Iterate until approved.
5. **Write the ticket docs.** One file per slice from the `ticket-docs` template:

   ```bash
   mkdir -p tickets
   ls tickets/                                  # keep numbering after existing files
   # tickets/NN-<slug>.md per slice, NN in dependency order; tickets/README.md index row each
   ```

   Fill header (Blocked by / Blocks by NN until keys exist), Summary, observable
   acceptance criteria, and the Plan with the **first red test** named. Status `todo`.
6. **Hand to the human.** They create the Jira issues (copy the Summary + AC via
   the Jira-paste block), link blockers in Jira, then tell you the keys; you
   `git mv tickets/NN-slug.md tickets/<KEY>.md` and fill the key in the header and
   index. **Do not touch Jira yourself.**

   **Dependent chains ship as chained MRs** (each targets the branch below;
   `review-pr` §A1). The blocking edges you declared here ARE the chain order;
   **expand → migrate → contract maps 1:1 onto a chain.** Independent tickets are
   separate MRs.

## Ticket template

The `ticket-docs` §2 template. In short: `# NN — <Title>` · header with Blocked by /
Blocks · **Summary** (end-to-end behaviour, operator's POV — not a layer list) ·
**Acceptance criteria** as observable rows · **Plan** whose first step is the
failing test · Status `todo`. No file paths or code in Summary/AC.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Ticket "update all values files" | Horizontal slice | Re-cut vertically: one chart end-to-end, then the next |
| Ticket needs 3 MRs | Too big for one context window | Split; declare the edge |
| Edges wrong, work blocked mid-build | Breakdown not quizzed | Step 4 — the human approves edges explicitly |
| Agent created Jira issues | Ignored the no-Jira rule | `ticket-docs` §4; report and stop |
| Keys never recorded | Step 6 skipped | Rename files to keys; index row per ticket |

## Definition of done

- [ ] Slices are **vertical tracer bullets** — complete, demoable, context-window-sized
- [ ] **Blocking edges** declared; wide refactors sequenced expand → migrate → contract
- [ ] Human approved the breakdown (granularity + edges)
- [ ] `tickets/NN-*.md` written from the `ticket-docs` template with observable AC and a named first test; index updated
- [ ] Nothing written to Jira; human given the paste blocks and asked for the keys
