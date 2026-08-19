# Context Changelog

Every promotion into `docs/` gets one entry — and so does any behavior-changing
promotion to `skills/` or `agents/`. A PR that changes those without changing this
file is a promotion without a record — gate on it.

**Version semantics** — pinned to *agent behaviour*, not edit size:

- **MAJOR** — agent-breaking. A rule changed such that previously-correct behaviour is
  now wrong. Every entry carries a **Re-check:** line.
- **MINOR** — additive. New guidance; everything previously correct still is.
- **PATCH** — no behavioural change. Clarification, link fix, formatting.

The test for MAJOR: *if an agent had memorised the previous version and acted on it,
would it now be wrong?* If yes, major. If it would merely be missing something, minor.

---

## 2026-08-19

- `skills/init-agent-harness` → **`skills/setup-harness`** (MAJOR — agent-breaking rename, no alias; ticket agent-harness-template-6zd, PRD `harness-prd-setup-harness.md` fresh-repo slice)
  - The per-project first pass now also: creates `.claude/gate.sh` from the
    template and **proves it green** (autofixable findings → one propose+apply
    confirm; substantive findings → reported, gate left honestly red — full
    fix-routing is ticket 04), copies the CI workflow, runs `bd init` when
    tracker = Beads, writes `docs/agents/harness-config.md` from
    `docs/harness-config-template.md` (uninterviewed sections marked
    `TODO — ticket 03's interview`), and ends on the customization map.
    The three-way rule (interview decisions · self-heal mechanics ·
    hard-stop dependencies) is canonical in the skill body. Every mechanic
    is idempotent — re-running changes nothing, never clobbers.
  - `docs/agents/issue-tracker.md` is superseded: consumers (orchestrator
    step 4, the skill) now read the config doc's Tracker section, with
    `issue-tracker.md` accepted as a legacy fallback.
  - **Re-check:** anything that invokes `init-agent-harness` by name (it no
    longer exists), and any procedure that reads `docs/agents/issue-tracker.md`
    as the primary tracker record.

## 2026-08-18

- `skills/grill-me` — → **2.0.0** (MAJOR — agent-breaking; upstream mattpocock v1.2, firewall-reviewed)
  - One-question-at-a-time is GONE. The interview now works the **question
    frontier in rounds**: all currently-unblocked questions per round, numbered,
    each with a recommended answer; facts fetched by non-blocking subagents;
    exit = empty frontier + explicit confirmation.
  - **Re-check:** any procedure or habit that assumes one question per turn.
    Batched answers ("Q1 agree, Q2 change X…") are now the expected reply shape.
- `skills/writing-for-agents` — **new** (MINOR; upstream v1.2 adaptation)
  - The craft reference for anything an agent reads: context pointers,
    information hierarchy/progressive disclosure, completion criteria
    (clarity + demand), leading words vs negation, no-op-test pruning.
    `evolve-harness` STEP 3 now points at it.
- `skills/wait-what` — **new** (MINOR; upstream v1.2, user-invoked)
  - Three-line corrective: re-pitch the last answer in plain English +
    `CONTEXT.md` vocabulary. Zero context cost until invoked.
- `agents/orchestration/orchestrator` — work-type table gains a **Default
  dispatch** column + sprint-planning row (MINOR)
  - Each work type now sets the default dispatch shape (most = ONE worker);
    `assess-complexity` confirms or overrides; never escalate the shape without
    naming what forces it.

## 2026-08-17

- `multi-agent-orchestration` — → **2.0.0** (MAJOR — agent-breaking)
  - **Beads is now the tracker preset.** Frontier = `bd ready --json`; assignment =
    `bd update <id> --claim`. Membership in `bd ready` IS the ready-for-agent signal.
  - Added the **BOUNDARY**: Beads holds the work graph only. Never `bd remember`.
    Never `bd setup claude`.
  - Added §0 (operational roles vs. org-chart simulation), §3 (what actually caps
    worker count), §9 (why a fleet framework was not adopted).
  - Added abort-recording to the guardrails, and the review-only caveat.
  - **Re-check:** any orchestration procedure that dispatches without claiming, or
    that treats a hand-maintained list as the frontier. Double-dispatch is now
    preventable and therefore a defect.

- **All `docs/*.md` — provenance headers added** (PATCH, no behavioural change)
  - Every doc now carries `version`, `source`, `source_version`, `derivation`, and
    `review_after`. Before this there was no way to tell a current derived doc from a
    stale one by looking at it.
  - `derivation: compressed` docs also carry a one-line note under the title so an
    agent knows it is reading a derivation and should say so rather than infer detail
    the file doesn't carry.

- `architecture-patterns-FULL-KB` — read guard added (PATCH)
  - Header now states the file is opened **at a cited §**, never read whole. The
    policy already existed in `docs/README.md`; nothing enforced it, and one
    whole-file read spends the entire budget the tier system protects.

---

<!--
TEMPLATE — copy for the next entry:

## YYYY-MM-DD

- `<doc-name>` X.Y.Z → **A.B.C** (MAJOR|MINOR|PATCH — short reason)
  - What changed, in terms of what an agent would now do differently.
  - **Re-check:** <MAJOR only — what has to be revisited>
-->

## 2026-08-19 — isolation survey adoptions (P1/P2/P4/P5; human-approved)

- `orchestrate-agents` MINOR: worktrees = file isolation, NOT an OS boundary;
  Claude Code ≥ 2.1.163 floor (two 2026 worktree CVEs).
- `harness-config-template` MINOR: named container triggers (unattended /
  untrusted code / MCC-in-boundary) per Anthropic's isolation ladder.
- `secure-code-review` MINOR: §4 post-install diff of .claude/settings*.json,
  .mcp.json, .vscode/tasks.json (npm-worm hook persistence).
- `.claude/settings.json`: guardrail-6 ask-rules on governing paths (P2).
- `orchestrator` PATCH: Go recorded as the language IF the event-driven rung is
  ever earned; engine stays Python CLI until then.
- Deferred: P3 Bash-sandbox trial until Claude Code ≥ 2.1.221 (currently 2.1.197).
