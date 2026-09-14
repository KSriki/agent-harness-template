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

## 2026-09-14

- `evals/runners/model.py`, `.claude/gate.sh` — **model seam runs the CLI from
  a neutral cwd; live evals move to `gate.sh evals`** (PATCH for agents, bug
  fixes for the runner/gate; ticket agent-harness-template-yxr). Headless
  `claude -p` inheriting the repo cwd fired the repo's SessionStart hook
  (`bd prime` — dolt lock contention with the calling session) and the
  machine-wide Stop-hook gate, which re-ran the evals and spawned claude
  recursively (observed: 34 min for one haiku call vs 51 s neutral; a live
  cascade of 28+ stray processes). Fixes: seam passes
  `cwd=tempfile.gettempdir()` (regression test in `test_model_seam.py`);
  `gate.sh full` (the turn-end/CI path) is now deterministic-only, with all
  live-model suites behind the explicit `gate.sh evals` mode — with an authed
  CLI they cost minutes per run and would bust the Stop hook's timeout every
  turn; the gate also resolves a python that actually has pytest (hook
  environments can carry a minimal PATH).
- `evals/runners/scorers.py` (+ loader, tests), `evals/golden/source-provenance.jsonl`
  — **`first-word` scorer; two golden cases tightened** (baseline runs
  2026-09-14, both suites 85.7% vs 0.9 floor — all four failures were eval
  defects, not model errors). New deterministic scorer compares the first
  whitespace token so a correct single-word verdict followed by unrequested
  reasoning still passes; sp-004's common upstream became bylined+dated (an
  anonymous comment collided with the never-citable rule), sp-014 became two
  independent secondary reproductions (a maintainer-acknowledged tracker
  report is a primary artifact, so the model's "verified" was correct under
  the stated precedence rule).

- `evals/` (premise-verdict + source-provenance suites), `.claude/gate.sh`,
  `docs/engineering-steering-doc.md` §4.5 — **premise-gate eval coverage**
  (MINOR — additive; ticket agent-harness-template-fu1, follow-up to 63j;
  steering-doc line human-approved in session). The premise-reviewer's judgment
  is non-deterministic, so evals are its tests (steering §3): two frozen golden
  sets (14 cases each, exact scorer, pass floor 0.9) probe verdict discipline
  (RETHINK only on VERIFIED/CORROBORATED contradiction of a load-bearing
  assumption or an unfalsifiable premise; injection in the dossier resisted in
  both directions; circular citations counted as one source; superseded
  evidence; verified-but-not-load-bearing distractors) and source-provenance
  tiering (verified/corroborated/single-source/unverified, incl. common-
  upstream collapse, never-citable material, the negative-space test). Both
  suites run via `gate.sh evals` (the live-model mode) with the standard
  loud-skip semantics; the turn-end `full` path stays deterministic.

- `skills/grill-me` → **3.0.0**, `agents/review/premise-reviewer.md` — NEW,
  `agents/orchestration/orchestrator.md`, `skills/write-a-prd` — **premise gate**
  (MAJOR for grill-me — agent-breaking; MINOR elsewhere; ticket
  agent-harness-template-63j). Trigger: user-named failure mode — premise-level
  sycophancy: agents optimize *inside* a bad frame instead of challenging it,
  and existing adversarial review only starts at code/design/ship. grill-me now
  opens with **Round 0**: dispatch `premise-reviewer` (fresh context, premise
  summary only) for outside-view *disconfirming* research under strict
  source-provenance rules built against AI citogenesis (primary sources
  establish / secondary only locate; one-hop independence tracing before
  corroboration counts; never-citable list; negative-space test; tiered
  confidence — RETHINK rests only on VERIFIED/CORROBORATED; model recall is a
  lead, never a source). Output: PROCEED/RETHINK + **kill criteria**, persisted
  in `intent/<slug>.intent.md`, carried verbatim into the spec by write-a-prd,
  and armed through the build by the orchestrator (tripped criterion =
  ESCALATION + `bd human`). **By design, RETHINK warns, never vetoes** — an
  informed human override, recorded with its reasoning, is a first-class
  outcome (contrarian bets build new things; the record separates a bet from a
  blind spot). Rejected: devil's-advocate pass at every stage (guardrail
  sprawl — premise gate at ingress, human gate at egress, reviewers at merge is
  the band).
  **Re-check:** any memorized grill-me flow — the interview now opens with
  Round 0 (premise verdict + kill criteria) unless the skip is stated in one
  line; jumping straight to the design tree is now wrong.

## 2026-09-03

- `skills/write-design-doc`, `skills/codebase-design` — **concrete-anchor DoD
  lines** (MINOR — additive; ticket agent-harness-template-39i). Design docs
  must anchor every described component with a contract example, pseudo-code,
  or a `file:line` reference (implementations linked, never pasted);
  codebase-design must write the chosen interface down as a contract sketch.
  `write-a-prd`'s no-snippet rule is deliberately unchanged.
- `docs/evals.md` — NEW (MINOR — additive; ticket agent-harness-template-v9z).
  Human-facing manual for the `evals/` runner: run anatomy (Mermaid), golden-set
  contract, config reference, gate semantics incl. loud-skip and noise floor,
  pass@k vs pass^k, extension points (scorers, judge, model seam), porting.
  `evals/README.md` and the `docs/README.md` tier table now point to it.
- `skills/grill-me`, `skills/write-a-prd`, `skills/observability`, `AGENTS.md`
  layout — **intent.md artifact chain** adopted from Anthropic's AI-native SDLC
  playbook (MINOR — additive; ticket agent-harness-template-4ya, PR #1, merged
  earlier today — entry recorded late). grill-me persists confirmed
  understanding as `intent/<slug>.intent.md`; write-a-prd reads it as canonical
  and saves `intent/<slug>.spec.md` beside it; observability gains the
  tiered-autonomy maintenance loop (1σ log / 2σ read-only diagnose / ≥3σ
  propose-via-PR) whose diagnosis exits as an intent artifact.

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

## 2026-08-20 — Anthropic eval/caps survey adoptions (P1/P2/P3+P5 stance; human-approved)

- `eval-harness` MINOR: pass@k vs pass^k, declared noise floor (~3pp start),
  N-trials rule for agents; judge "Unknown" out + isolated judge per dimension;
  corrected the pin-temp/seed failure-mode row for stochastic agents.
- `evals/README` MINOR: mirrored trial/noise bullets + recorded framework
  stance (hand-rolled first; hosted eval platforms = guardrail-2 egress).
- `agents/README` MINOR: control point 4 — runtime subagent caps (depth /
  concurrency / max_budget_usd, ≥2.1.217); effort named the primary Opus 5
  cost dial (eval-driven sweep).
- `.claude/settings.json`: depth 3 / concurrent 8 pinned (arm on update).
- `orchestrator` PATCH: check-budget reframed as warn band inside the hard caps.
