# Agent Harness Template

A base repo for **context, harness, and loop engineering** — the agent-facing layer
that sits alongside your code. Fork it, fill in the slots, delete what you don't need.

Portable by design: **`AGENTS.md` is the source of truth**; `CLAUDE.md` is a one-line
pointer. Works with Claude Code, Cursor, Copilot, or anything that reads repo context.

**→ Quick start:** `python3 init.py` — interactive wizard, detects your stack, fills `AGENTS.md`.
**→ Then read [`SETUP.md`](./SETUP.md).**
**→ Why it's built this way: [`ARCHITECTURE.md`](./ARCHITECTURE.md).**

---

## The idea in one table

**Context is a budget, and always-on context is the expensive kind.** A token in
`AGENTS.md` is paid on *every turn, forever*. A token in a skill is paid only when
that skill is actually needed. Four tiers, and picking the right one is most of the
skill:

| Tier | Where | Loads | Holds |
|---|---|---|---|
| **Always** | `AGENTS.md`, `docs/engineering-steering-doc.md` | Every turn | Facts + behavior needed always |
| **On match** | `skills/*/SKILL.md` | When the description matches | Procedures needed *sometimes* |
| **On demand** | `docs/architecture-patterns.md`, the full KB | When a skill points at it | Depth, rarely needed |
| **Delegated** | `agents/*.md` | On invocation — **own context window** | Work whose *tokens* shouldn't touch main |

```
Needed every turn?     → AGENTS.md / steering doc
Sometimes, procedural? → a skill
Big input, small output? → a subagent
Needed once?           → just say it in the thread
```

**The budget, concretely:** always-on is ~**324 lines**. Naively pasting every doc
into context would be ~**2,587 lines, every turn** — 8× the cost, and *worse*
instruction-following, because a model given 40 rules follows them worse than one
given 6.

---

## What's in here

**Skills** (loaded on demand)
| Skill | Fires when |
|---|---|
| `run-tests` | Running/writing tests; a CI gate fails |
| `secure-code-review` | **Before** accepting external code or ANY new dependency |
| `architecture-patterns` | Choosing a pattern; sync-vs-async; caching; scaling |
| `new-service` | Adding a component — **enforces the complexity-rung check** |
| `write-design-doc` | A decision that's expensive to reverse |
| `debug-research` | The bug is in a *library*, not your code |
| `eval-harness` | Evals, LLM-as-judge, HITL gates |
| `ci-cd` | Pipeline, deploy, promotion, release, and rollback |
| `observability` | Instrument logs/metrics/traces; SLOs; **triage a live incident** |
| `review-pr` | Preparing a PR, or reviewing one for correctness + blast radius |
| `evolve-harness` | Grow the harness itself — new skill/rule from a repeated correction, **human-gated** |

**Subagents** (own context window)
`code-searcher` · `test-writer` · `design-reviewer` · `debug-research` · `security-reviewer` · `deploy-reviewer` · `trend-scout`

**Docs** — steering doc (always-on) + architecture patterns (compressed 14% + full KB)

---

## 🔒 Guardrails — read the caveat

Agents that read the internet ingest **untrusted input into a system that executes
things.** Four threats: **exfiltration** (disguised as telemetry), **prompt
injection** (fetched content instructing the model), **supply chain** (`install` =
arbitrary code execution), and **self-modification** (an agent rewriting its own
rules/skills from something it read — the risk the `evolve-harness` loop is built to contain).

Defenses live in `AGENTS.md` (the **6** always-on non-negotiables, deliberately),
`skills/secure-code-review/`, `agents/security-reviewer.md`, and — for changes to the
harness itself — the human gate in `skills/evolve-harness/` (guardrail #6).

> **⚠️ These are REVIEW-ONLY.** They catch the accidental and careless case — most
> real incidents. They do **not** contain a determined attacker: a compromised agent
> is exactly the thing that won't run its own safety check. **You cannot use the
> model to police the model.**
>
> **Real containment = deny-by-default egress enforced OUTSIDE the agent**, plus a
> container with no host mounts and no cloud creds. One-time infra task. Worth more
> than every rule in this repo. (`secure-code-review` §6, `SETUP.md` §3.)

---

## Make it yours

`docs/engineering-steering-doc.md` encodes **one specific engineer's** standards
(Python/uv, Go, React+TS, rebase, Mermaid, KISS-over-cleverness). **Rewrite it**, or
your agent will optimize for someone else's preferences.

## Maintenance

> **Correct a model on the same thing twice → a rule is missing.** Route it by tier.
> **Delete rules that never fire** — dead rules dilute live ones.

The complexity ladder applies to the harness too: **don't add a tier until the one
below it visibly fails.**

## License

MIT — see [LICENSE](./LICENSE).
