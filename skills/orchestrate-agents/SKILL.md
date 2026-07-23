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

Fan out with the **`implementer`** subagent (one per boundary) — it builds
**test-first** (`tdd`: failing test from the acceptance criteria, then minimal
code). Compose the fleet: `implementer` builds → `security-reviewer` /
`deploy-reviewer` gate → you merge (`test-writer` is for covering code that
*already exists*, not for the worker loop). Tickets from `prd-to-issues` map
naturally onto workers: each no-blocker frontier ticket is a slice, and **its
acceptance criteria become the worker's first failing tests.** **SLM workers:**
for a cheap, bounded, well-specified subtask, point an implementer at a local
model (Ollama/vLLM) — measure cost/latency vs. frontier.

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
- [ ] **Merged, then full gate re-run on the result** (merge-validation pass)
- [ ] Every diff reviewed before merge; **no auto-merge**; external code went through `secure-code-review`

## Reference files

- `../../docs/multi-agent-orchestration.md` — read for the diagram, exact worktree
  workflow, a full worked example, and how to invoke it in a Claude Code session.
