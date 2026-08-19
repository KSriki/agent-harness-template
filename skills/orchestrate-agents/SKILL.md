---
name: orchestrate-agents
description: >
  Use to ship a multi-part change by running several agents IN PARALLEL — fan-out
  across subagents, each isolated in its own git worktree, then verify-and-merge.
  Triggers on "orchestrate agents", "parallel agents", "run these in parallel",
  "split this across agents", "agent fleet", "multi-agent", "worktree", "spin up
  workers for X and Y". Covers when to parallelize, how to split by ownership, the
  worktree isolation mechanism, and the mandatory merged-validation pass.
  Do NOT use to delegate ONE search/research task (just spawn a `code-searcher` /
  `debug-research` subagent), for a single-threaded change (just do it), or to
  decide architecture (`architecture-patterns`). See `docs/multi-agent-orchestration.md`
  for the full worked example + diagram.
---

# Orchestrating parallel agents

## When to use this

A change that genuinely splits into **independent, parallel workstreams** you'll
ship faster by running at once — each in an isolated worktree so they can't corrupt
each other's file state. You are the orchestrator; the workers are subagents.

**Not this skill if:** it's one research/search task → spawn a single subagent. It's
one coherent edit → just make it. You're deciding *whether* to split a **service**
→ `new-service`. You're deciding a pattern → `architecture-patterns`.

## The decision: parallelize only when BOTH are true

1. **The work splits along genuine ownership boundaries** — different files/modules,
   not different nouns in the same file. Two agents editing the same file is a merge
   conflict machine; two agents owning `adapters/auth/` and `adapters/audit/` is clean.
2. **Your REVIEW capacity can keep up.** The bottleneck is not compute — it's *you
   verifying the output*. **Practical cap is ~2–3 parallel agents.** Ten agents you
   can't review is ten unreviewed diffs, which is worse than one you trust.

If either is false, stay sequential. Parallelism has a coordination tax; name what
it buys before you pay it.

## The pattern (plan → contract → split → isolate → test → merge-validate)

```
1. PLAN (you, main thread)      decompose; name each worker's file ownership
2. SHARED CONTRACT              the interface/types/API the workers agree on, FIRST
3. SPLIT by ownership           one worker per boundary; no overlapping files
4. ISOLATE in a worktree        each worker gets its own git worktree (see below)
5. TDD per worker               red before green (`tdd`), gate green in its own tree
6. MERGE-VALIDATE (you)         merge, then ONE full validation pass on the result
```

**Step 2 is the one people skip and regret.** If the workers don't agree on the
shared interface *before* they start, they build to different contracts and the
merge is a rewrite. Define the types/signatures/API first, in the main thread.

## The mechanism: worktree isolation

Each worker runs in its own git worktree — a separate working directory backed by
the one shared `.git`, so parallel edits never touch the same file state.

**Worktrees isolate FILE EDITS, not the operating system** — workers still share
the host's env, credentials, and network (Anthropic's own wording: worktrees "are
not operating-system sandboxes"). Two 2026 CVEs attacked exactly this mechanism
(CVE-2026-55607 sandbox escape via worktree path confusion, fixed in Claude Code
2.1.163; CVE-2026-40068 trust-dialog bypass via worktree spoofing, fixed 2.1.84)
— **run Claude Code ≥ 2.1.163**, and treat OS-level isolation as the sandbox
settings' job, not the worktree's.

Two ways:
- **Subagent frontmatter:** the `implementer` agent declares `isolation: worktree`,
  so each spawned instance gets a fresh worktree automatically.
- **Explicit:** create the trees yourself and point each worker at one.

```bash
git worktree add ../wt-auth   -b feat/auth
git worktree add ../wt-audit  -b feat/audit
# ... a worker runs in each; when done:
git worktree remove ../wt-auth
```

Fan out with the **`implementer`** subagent (one per boundary) — or its stack
variants **`frontend-implementer`** / **`backend-implementer`** when a slice is
clearly UI-only or server-only (same worker rules + stack conventions; the
generic worker remains the default for mixed slices). Every worker builds
**test-first** (`tdd`: failing test from the acceptance criteria, then minimal
code). Compose the fleet: `implementer` builds → `security-reviewer` /
`deploy-reviewer` gate → you merge (`test-writer` is for covering code that
*already exists*, not for the worker loop). Tickets from `prd-to-issues` map
naturally onto workers: each no-blocker frontier ticket is a slice, and **its
acceptance criteria become the worker's first failing tests.** **SLM workers:**
for a cheap, bounded, well-specified subtask, point an implementer at a local
model (Ollama/vLLM) — measure cost/latency vs. frontier. **Model choice per
worker follows the routing ladder in `agents/README.md` (Model routing):**
default down, escalate on failure; blast radius routes up; volume routes down
plus an output gate.

**Shipping the branches:** *independent* slices → separate PRs, as always.
*Dependent* slices (blocked-by chains) → a GitHub **PR stack** (public preview
2026-07): each PR targets the branch below, per-layer CI runs the same gate as if
targeting main, merge bottom-up, upper layers auto-rebase. Stacks are for chains —
never force parallel fan-out into one. The merge-validation pass still applies at
the top of the stack.

## Guardrails — parallelism multiplies the surface

- **No auto-merge. Ever.** Every worker's diff is reviewed before it lands — parallel
  agents multiply both the error surface and the injection surface. The merged result
  gets `review-pr` + (if it ships) `deploy-reviewer`.
- **The final merged-validation pass is non-negotiable.** Each worker's tests passing
  in isolation does NOT prove the *combination* works. Run the full gate on the merge.
- **External code / new deps** in any worker → `secure-code-review` still applies. A
  worker cannot install on its own authority (guardrail #3).
- Workers stay **inside their ownership boundary**. A worker editing outside its files
  is a finding, not a convenience.

## Two ways to drive this

**You orchestrate** (default): run the pattern yourself in the main thread — full
visibility, you review as workers return. **Or delegate the management**: spawn the
**`orchestrator`** subagent (it can spawn workers itself) for multi-ticket or
long/autonomous runs — it plans, contracts, dispatches, arbitrates the ledger, and
reports an explicit exit class (success / escalation / abort). Either way, the
human gate on merges and dependencies is unchanged.

## Long / autonomous runs: the defect ledger

For a fan-out that runs for hours (or overnight), coordination moves into a
**defect ledger** — `DEFECTS.md` at the repo root — with **asymmetric write rules**:

- **QA/testing agents OPEN defects** (severity, repro steps, expected vs actual,
  history) — they never fix code.
- **Workers FIX code** — they never edit the ledger.
- **Only the opener retests and CLOSES** a defect after the fix lands.
- **No victory with open defects:** the run's exit predicate is "all success
  criteria met AND every defect closed" — never "the model feels done."

One reviewable file, a complete audit trail, and it removes the worst failure mode
of long runs: declaring success over known breakage.

Two companion rules for long runs:
- **The orchestrator does not write product code.** It plans, defines contracts,
  dispatches, arbitrates the ledger, and validates — keeping its context clean for
  judgment (and its token spend a sliver of the total).
- **Decorrelate the checker:** where feasible, the QA/review agent runs on a
  **different model** than the workers it checks (`agents/README.md` Model
  routing, rule 5). Shared model = shared blind spots.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Merge is a rewrite | No shared contract defined first | Step 2 — agree the interface before splitting |
| Constant merge conflicts | Split by noun, not by file ownership | Re-split along real file boundaries |
| Unreviewed diffs pile up | More agents than you can review | Cap at ~2–3; review is the bottleneck |
| "Each passed but the whole is broken" | Skipped merge-validation | Always run the full gate on the merged result |
| Worker did something weird | Lossy summary; scope too vague | Tighter task + contract; read the diff, not just the summary |

## Definition of done

- [ ] Parallelized only because work split by **real ownership boundaries** + review capacity allowed it
- [ ] **Shared contract defined first**, in the main thread
- [ ] Each worker **isolated in its own worktree**; stayed in its lane
- [ ] Each worker's gate green in isolation
- [ ] Long runs: **defect ledger empty** — every opened defect retested and closed by its opener
- [ ] **Merged, then full gate re-run on the result** (merge-validation pass)
- [ ] Every diff reviewed before merge; **no auto-merge**; external code went through `secure-code-review`

## Reference files

- `../../docs/multi-agent-orchestration.md` — read for the diagram, exact worktree
  workflow, a full worked example, and how to invoke it in a Claude Code session.
