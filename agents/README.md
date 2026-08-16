# Subagents

## What a subagent is actually for

A subagent runs a task in its **own context window** and returns only a summary
to the caller. That is the entire point, and it is a *context* decision before
it is a task decision:

> **Delegate when the work would pollute the main thread with tokens the main
> thread doesn't need afterward.**

Reading 40 files to find one bug produces 40 files' worth of context and one
sentence of value. Do that inline and the main thread now carries 39 files of
dead weight for the rest of the session. Delegate it, and you get the sentence.

## When to delegate

**Delegate:**
- **Search / exploration** — "find where X is handled" (huge input, tiny output)
- **Bounded, well-specified subtasks** — "write the tests for this module"
- **Parallelizable work** — 〈N〉 independent things at once
- **Anything with a big read-to-conclusion ratio** — logs, corpora, large diffs

**Do NOT delegate:**
- Work needing the **full conversation history** — the subagent doesn't have it
- **Highly interactive** work — every round trip through a subagent is expensive
- **Trivial** tasks — the delegation overhead exceeds the task
- Anything where **you need to see each step** — you get the summary, not the path

## The tradeoff, stated honestly

You are trading **fidelity for context economy.** The subagent sees less than you
do and reports back compressed. That's a *good* trade for "find the file"; it's a
*bad* trade for "make the architectural call." Delegate the retrieval, keep the
judgment.

## Writing one

Each subagent is `agents/<name>.md` with frontmatter:

```markdown
---
name: <kebab-case>
description: When to invoke this. Concrete triggers — this is the routing key
  (the main agent auto-delegates on it, exactly like a skill description).
tools: Read, Grep, Glob        # canonical capitalized names, least privilege:
                               # a searcher gets no Write. Omit the line = inherit ALL.
model: haiku | sonnet | opus | inherit   # fast for mechanical, strong for judgment,
                                         # inherit to match the main session
---

<System prompt: the role, the procedure, and — critically — the OUTPUT CONTRACT.>
```

**The output contract is the most important part.** The whole value is the
summary, so specify it precisely: what fields, what shape, how long. An
unconstrained subagent returns a wall of text and you've saved nothing.

**Least privilege on `tools`.** A code-searcher does not need write access. A
test-writer does not need to deploy. Scope narrowly — it bounds the blast radius
and it makes the agent's job clearer.

**Match the model to the work.** Mechanical retrieval → fast/cheap model.
Judgment → strong model. Paying frontier prices to grep is a budget leak.
→ The full routing policy: **Model routing** below.

## Model routing (which model for which task)

The ladder, cheapest first. **Default DOWN a tier and escalate on observed
failure** — same rule as the eval-harness scorer ladder: the cheapest model that
works. "It might need the big model" is not evidence; a failed cheap attempt is.

| Tier | 〈Models〉 | Task shapes it owns |
|---|---|---|
| **Local SLM** | 〈Ollama/vLLM: `llama3.2:3b`, `qwen2.5:7b`〉 | High-volume mechanical work with a tight spec + schema: bulk classification/extraction/transforms, doc summarization at scale. Free + private; quality must be **spot-checked or eval-gated**, never assumed |
| **Fast API** | 〈haiku〉 | Search/retrieval across many files, mechanical summarization, format conversions — `code-searcher` lives here |
| **Mid** | 〈sonnet〉 | Day-to-day implementation, tests for existing code, well-specified bounded edits — `test-writer` lives here |
| **Frontier** | 〈opus〉 | Judgment: adversarial review, security, architecture, weighing ambiguous evidence — all three reviewers + both researchers live here |
| **inherit** | session model | Production-code workers (`implementer` + variants): the code ships, so it gets whatever tier you chose for the session |

**Five routing rules (in order):**
1. **Mechanical vs judgment** — can a competent junior do it with a checklist?
   Then it's mechanical: route down.
2. **Blast radius overrides cost** — anything irreversible, security-relevant, or
   contract-defining routes UP regardless of how mechanical it looks. A cheap
   model reviewing a migration is a false economy.
3. **Volume routes down + gates** — 1,000 small calls belong on a small model
   **with** a deterministic check or eval sampling on the output (`eval-harness`),
   not on a frontier model unsampled.
4. **Measure, don't vibe** — log cost/latency per agent run (steering §5). A
   model choice nobody measured is a guess; revisit the tier when the numbers say so.
5. **Decorrelate the checker from the doer** — where feasible, the agent
   verifying work (QA, review, judge) runs on a **different model** than the one
   that produced it. Shared model = shared blind spots; `eval-harness` applies the
   same rule to judges (self-judging inflates).

Static assignments live in each agent's `model:` frontmatter. When orchestrating
ad-hoc (`orchestrate-agents`, one-off subagent spawns), apply the same ladder in
the spawn — the orchestrator names the tier deliberately, not by default.

**Where model config actually lives (three control points, most→least specific):**
1. **Per-invocation** — the Agent tool's `model` parameter at spawn time (what the
   `orchestrator` uses to route per-slice).
2. **Per-agent** — the `model:` frontmatter in these files. **This is the versioned
   registry**: model choice is behavior, so it changes by PR like everything else.
3. **Fleet-wide** — `CLAUDE_CODE_SUBAGENT_MODEL` env overrides ALL subagents (e.g.
   force `haiku` for a cheap bulk run); `ANTHROPIC_DEFAULT_〈OPUS|SONNET|HAIKU〉_MODEL`
   re-points what each alias resolves to. Use for experiments, not as the default —
   an env override is invisible in git.

**Other frontmatter worth knowing:** `skills:` (preload a skill's full content —
how workers get `tdd` as law; keep to 1–2, it's paid on every spawn) · `Skill` in
`tools:` (dynamic skill invocation) · `effort:` · `maxTurns:` (cap runaway agents)
· `permissionMode:` — exists, but **`bypassPermissions` is never used in this
harness**; an agent that skips permission checks is outside the guardrail model.

## Provided

| Agent | Use for |
|---|---|
| `research/code-searcher.md` | Locating code/behavior across the repo without polluting main context |
| `qa/test-writer.md` | Writing tests for a specified module against the quality gates |
| `review/design-reviewer.md` | Reviewing a design/PR against the rung check + cross-cutting constraints |
| `research/debug-research.md` | External research (library bugs, API checks, lib evaluation) without dragging forum noise into main context |
| `review/security-reviewer.md` | Adversarial BLOCK/ALLOW review: egress, injection, supply chain, insecure patterns |
| `review/deploy-reviewer.md` | Adversarial BLOCK/ALLOW review of a **ship**: rollback, migration safety, blast radius, contract compat, data safety |
| `research/trend-scout.md` | Periodic ecosystem/harness-practice survey → ranked **proposals** for `evolve-harness`. Read-untrusted-only, **propose-never-apply** |
| `engineering/implementer.md` | Worktree-isolated worker: builds one owned slice in a parallel fan-out (`orchestrate-agents`), returns a branch + summary. **Never merges/deploys**. The DEFAULT for mixed/unclear slices |
| `engineering/frontend-implementer.md` | `implementer` specialized for UI slices: React+TS idiom, local-first state, behavior-through-the-rendered-interface tests, a11y as correctness |
| `engineering/backend-implementer.md` | `implementer` specialized for server slices: dependency-points-inward, parameterized SQL, backward-compatible migrations, idempotent consumers |
| `orchestration/orchestrator.md` | **The manager**: plans, contracts, dispatches workers (it CAN spawn subagents), arbitrates `DEFECTS.md`, merge-validates, exits by class (success/escalation/abort). **Writes no product code** |

## The rule that keeps this honest

> **Same complexity ladder as everything else:** do not add a subagent until you
> can name what fails without it. An unused subagent is a maintenance cost with
> no payoff — and a poorly-scoped one silently returns confident, lossy summaries,
> which is worse than no subagent at all.
