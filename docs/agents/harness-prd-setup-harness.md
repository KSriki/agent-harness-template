# PRD: `setup-harness` — the per-project first-pass, done as a skill

**Status:** ready-for-agent · **Owner:** human (Srikant) · **Source:** grill-me
session 2026-08-18 (Q1–Q14 confirmed) · **Supersedes:** `init-agent-harness` (rename + extension)

## Problem Statement

Setting up a project to work with the harness is today split across a CLI wizard
(`init.py`), a skill (`init-agent-harness`), and several manual steps (gate.sh
creation, CI workflow, tracker init). The manual steps get skipped — this very
repo shipped the gate mechanism while having no gate — and the recorded decisions
(tracker choice, repo shape, rules) either aren't captured at all or land in
scattered one-off files that rot as the project changes. A user starting a new
project cannot run one first pass that configures everything, and an agent
arriving in a half-configured repo has no defined way to finish the job.

## Solution

One skill, `setup-harness`, is the per-project first pass and the ongoing
update path. It applies a three-way rule: **interview once for decisions,
self-heal mechanics just-in-time, hard-stop for dependencies.** Decisions are
recorded in one living document per repo (`docs/agents/harness-config.md`,
filled from a template) that consumers read and self-heal against. Re-running
the skill enters **update mode**: it diffs recorded decisions against current
reality and proposes amendments — the single source of truth changes with the
project instead of rotting.

## User Stories

1. As a **developer on a new machine**, I want machine setup to stay a CLI
   (`init.py --link-global --install-hooks --global-claude`), so that the
   bootstrap works before any skill can load.
2. As a **developer starting a project**, I want `/setup-harness` to run one
   first pass — context files, commands, gate, CI, tracker — so that the repo is
   fully harnessed without me remembering the manual steps.
3. As a **developer whose project evolved**, I want re-running `/setup-harness`
   to detect drift between `harness-config.md` and reality and propose updates,
   so that the config stays the single source of truth.
4. As an **orchestrator or planning agent** in a half-configured repo, I want a
   self-heal clause — run the missing setup step (propose→confirm), then
   continue — so that setup is optional front-loading, never a blocking
   prerequisite.
5. As a **user of non-Claude tools** (Cursor, Copilot), I want the `init.py`
   per-project wizard kept as a documented fallback, so that the harness stays
   portable.
6. As a **repo owner**, I want gate-red findings during setup routed correctly —
   mechanical fixes applied inline with one confirm; substantive failures filed
   as tickets in the just-configured tracker — so that setup configures the
   workshop without doing the carpentry.
7. As a **harness maintainer**, I want additions to the always-on tier to
   require naming a demotion (the `evolve-harness` routing step), so that the
   steering doc stays a constitution and does not bloat.

## Implementation Decisions

- **Rename:** `init-agent-harness` → `setup-harness`; update references
  (SETUP.md, HARNESS.md, AGENTS.md skills table). No alias.
- **The three-way rule**, canonical in the skill body, restated in the config
  template header; steering doc **untouched** (Q13):
  - *Interviewed (decisions):* tracker choice, repo shape (mono/polyrepo), agent
    isolation (worktrees default vs Docker/devcontainer), business rules, tech
    limitations, coverage floor %.
  - *Automatic (mechanics, idempotent):* copy context files (never clobber
    filled ones), fill Commands (detect→propose→confirm, never fabricate),
    create `.claude/gate.sh` from the template and prove it green, copy
    `gates/github-actions-gate.yml` → `.github/workflows/gate.yml`, `bd init`
    when tracker=Beads, print the customization map (points at `harness-help`).
  - *Hard stop (dependencies):* any install (`brew install beads`, pytest-cov,
    …) is proposed, never run — guardrail 3.
- **Fix-routing during "prove the gate green"** (Q9): autofixable lint/format →
  propose + apply inline, one confirm. Failing tests / judgment-requiring
  errors → file as tickets in the tracker just configured, report the gate red,
  hand to the normal SDLC loop. Setup never fixes substance.
- **Living config doc** (Q10): new `docs/harness-config-template.md` in the
  harness (sibling of the design-doc template) → filled per repo as
  `docs/agents/harness-config.md`. Sections carry a one-line mini-changelog
  (existing provenance-header pattern). Supersedes `docs/agents/issue-tracker.md`;
  the two references (orchestrator agent, this skill) move to the config doc,
  with the tracker section as the compatible read path.
- **Update mode** (Q10): on a repo whose config doc exists, the skill diffs each
  recorded decision against detected reality, proposes amendments
  section-by-section, and never re-interviews from scratch. A consumer treats a
  *stale* section like a missing one.
- **Self-heal clause** (Q5): written once in `setup-harness` ("no config doc or
  missing/stale section → run that step: propose→confirm→record, then
  continue"); one pointer line each in `orchestrator.md` and `prd-to-issues`.
- **Group agent rules** (Q13): no import/build mechanism. Authoring-time
  conventions live in `agents/<group>/README.md` (applied by `evolve-harness`
  when editing member agents); runtime sharing stays in orchestrator dispatch
  prompts.
- **`evolve-harness` demotion rule** (Q13): one line added to its Step-1
  routing — adding to an always-on file requires naming what is removed or
  demoted to a lower tier. Human-gated diff.

## Testing Decisions

Highest seam, one seam: **run the skill's procedure against a fixture repo**
(fresh temp dir, `git init`, minimal stack markers) and assert external
behavior: expected files exist, gate.sh is executable and green, re-run is a
no-op (idempotence), update mode proposes — not applies — on injected drift.
Deterministic parts that land in code (any shared slot-filling in `init.py`)
get unit tests in the existing stdlib-unittest style. The skill prose itself is
verified by the fixture walkthrough, not mocked internals.

## Out of Scope

- Machine-level bootstrap changes (`--link-global`, hooks) — shipped this session.
- mypy adoption (separate dependency decision).
- Any steering-doc edit (Q13 resolved: none).
- An include/import system for agent definitions (rung not earned).
- Business-harness content (separate harness per memory).

## Further Notes

`harness-help`, the repo's own gate + CI, portable hooks, and honest coverage
floor shipped ahead of this PRD (commits a5ac353…03d53e1). The `cli.py` test
gap is ticketed separately and raises the floor 65→80 when closed.
