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
description: When to invoke this. Concrete triggers — this is the routing key.
tools: [<only what it needs>]   # least privilege: a searcher gets no write tools
model: <fast model for mechanical work; strong model for judgment>
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

## Provided

| Agent | Use for |
|---|---|
| `code-searcher.md` | Locating code/behavior across the repo without polluting main context |
| `test-writer.md` | Writing tests for a specified module against the quality gates |
| `design-reviewer.md` | Reviewing a design/PR against the rung check + cross-cutting constraints |
| `debug-research.md` | External research (library bugs, API checks, lib evaluation) without dragging forum noise into main context |
| `security-reviewer.md` | Adversarial BLOCK/ALLOW review: egress, injection, supply chain, insecure patterns |
| `deploy-reviewer.md` | Adversarial BLOCK/ALLOW review of a **ship**: rollback, migration safety, blast radius, contract compat, data safety |
| `trend-scout.md` | Periodic ecosystem/harness-practice survey → ranked **proposals** for `evolve-harness`. Read-untrusted-only, **propose-never-apply** |

## The rule that keeps this honest

> **Same complexity ladder as everything else:** do not add a subagent until you
> can name what fails without it. An unused subagent is a maintenance cost with
> no payoff — and a poorly-scoped one silently returns confident, lossy summaries,
> which is worse than no subagent at all.
