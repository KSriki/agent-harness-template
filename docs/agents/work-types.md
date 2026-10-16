---
doc: work-types
version: 1.2.0
updated: 2026-10-16
status: active
source: the former orchestrator routing table (extracted to single source; the orchestrator agent was removed on the enterprise-ai-platform branch — see docs/adr/0001)
derivation: moved-verbatim, then owned here; dispatch column simplified 2026-10-16
load: on-trigger
triggers: [classify the work, work type, what kind of ask, routing table, pipeline depth]
review_after: 2026-11-18
---

# Work Types — the universal classification

> **The single source of truth for "what kind of work is this?"** Every entry
> point classifies against THIS table before doing anything else; consumers
> (the main thread, planning skills) hold pointers, never copies. Workers do not
> read this file — the caller stamps `type + ticket` into each dispatch prompt
> instead (universally *readable* ≠ universally *loaded*).
>
> Resolve from any repo: `$(dirname "$(readlink ~/.claude/agents)")/docs/agents/work-types.md`

## The two governing rules

1. **The type sets the DEFAULT dispatch shape; `assess-complexity` confirms or
   overrides it.** Most asks are a single agent — never escalate the shape
   without naming what forces it.
2. **The checker never shares a model with the doer** (judge-type dispatches).
   A type that maps to a single subagent IS the dispatch — no pipeline ceremony
   around a one-verdict ask.

## The routing table

| The ask looks like | Type | Pipeline | Default dispatch | Done means |
|---|---|---|---|---|
| "Build 〈idea〉" | **D — New product** | full loop: grill → ticket docs (split) → build → ship | one `implementer` per ticket, in dependency order | all acceptance criteria + merged gate green + human gates passed |
| "Add 〈feature〉" | **A — Feature** | grill (if fuzzy) → ticket doc → build → ship | 1–3 workers, by real boundaries | tickets closed, merged gate green |
| "Fix 〈bug〉" | **B — Bug fix** | triage → failing test → fix → gate → ship | **ONE worker** | red test now green, gate green |
| "P1 / prod down" | **B — Hotfix** | fix now → gate → ship; paperwork after | main thread or ONE worker, immediately | prod restored; retro ticket filed |
| "Continue 〈product〉" | **Resume** | read state, work the ticket frontier | whatever the frontier admits | frontier advanced honestly |
| "Pay down debt" | **C — Debt** | audit (chart drift, unpinned images, missing probes/PDBs, stale ADRs) → pick → build | ONE worker per picked item | picked item landed, gate green |
| "Plan the sprint" | **Sprint planning** | compose next sprint from the work graph: 60% features · 20% bugs · 15% debt · 5% maintenance | no dispatch — planning only | sprint manifest written |
| "Review 〈diff / design / release〉" | **Judge** | no pipeline — a VERDICT | the matching read-only reviewer: `security-reviewer` / `design-reviewer` / `deploy-reviewer` | verdict delivered with reasons |
| "Research 〈question / library〉" | **Research** | offline: installed source, mirrored chart, `--help`, `kubectl explain`, `helm show` — else ask the human for the doc | main thread (no network here) | version-checked verdict, local sources named, unknowns marked |
| "Score / eval 〈outputs〉" | **Evaluation** | out of scope on this branch — the team uses models, it does not evaluate them; say so | main thread | the human decides where evaluation lives |
| "Where is / how does 〈X〉 reach 〈Y〉" | **Locate / trace** | answer only | `code-searcher` | the answer, with locations |
| "Should we 〈split / pattern / storage / auth / GPU SKU / gateway〉…" | **Architecture decision** | ladder check (steering §0) + existing ADRs → draft via `write-design-doc` (rejected alternatives recorded); ladder check (steering §0) if it adds a component | **PREPARE, then ESCALATE** — options + tradeoffs + a recommendation; `design-reviewer` judges the draft | the HUMAN decided; decision recorded via `adr` (or design doc) |

## Type notes (only what a row can't hold)

- **Architecture grounding:** the named skills route to the repo's references —
  `docs/design-doc-template.md` (which cites the pattern KB at § level for
  expensive decisions) and the existing ADRs — and `design-reviewer` judges
  against the same files. **The references outrank model priors**; that is what
  makes N agents give ONE answer to the same design question. Expensive-to-reverse
  ⇒ the human decides, never the agent.
- **New-product bootstrap decisions (Type D):** repo strategy (monorepo vs
  polyrepo) is an Architecture-decision-type ask — prepare options, the human
  decides, record in `REGISTRY.md` (cross-repo branch rule in `PRODUCT.md` if
  poly). Same for storage engine, auth model, service boundaries.
- **Hotfix:** bypasses sprint ceremony by design; the paperwork (retro ticket,
  decision-log line) is filed AFTER prod is restored, never skipped entirely.
- **Human-facing view:** the "you say → what fires" table in `HARNESS.md` is
  the human mirror of this file; if they drift, THIS file wins.

Changelog:
- 2026-10-16 — 1.2.0: second cut — evaluation out of scope; architecture row
  uses the ladder + ADRs; pipeline columns name ticket docs, not PRDs.
- 2026-10-16 — 1.1.0: enterprise-ai-platform branch — dispatch column no longer
  names a fleet/orchestrator; debt row describes platform debt; architecture row
  points at `adr`; `graphify` / `new-service` references removed with those skills.
- 2026-08-18 — 1.0.0: extracted verbatim from the orchestrator's routing table
  into the universal single source (example-harness `rules/work-types.md`
  pattern, adapted to this repo's doc tiers).
