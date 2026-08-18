# Agent Harness Template

A base repo for **context, harness, and loop engineering** — the agent-facing layer
that sits alongside your code. Fork it, fill in the slots, delete what you don't need.

Portable by design: **`AGENTS.md` is the source of truth**; `CLAUDE.md` is a one-line
pointer. Works with Claude Code, Cursor, Copilot, or anything that reads repo context.

**→ Use everywhere (global toolkit):** `python3 init.py --link-global` — symlinks `skills/` + `agents/` into `~/.claude/` so they load in every project. Run once per machine; `git pull` to update all of them.
**→ Enforce the gates:** `python3 init.py --install-hooks` — machine-wide hooks run each project's `.claude/gate.sh` (lint · typecheck · **tests · coverage**) on edits and at turn end; CI runs the same script. See [`gates/README.md`](./gates/README.md).
**→ Install into one project:** `bash install.sh /path/to/project` — copies the suite in and wires Claude Code native discovery (`.claude/` symlinks + `CLAUDE.md` @import). Won't clobber a filled-in `AGENTS.md`.
**→ Fill a project's context:** `python3 init.py` — interactive wizard, detects your stack, fills `AGENTS.md`.
**→ Then read [`SETUP.md`](./SETUP.md).**
**→ Why it's built this way: [`ARCHITECTURE.md`](./ARCHITECTURE.md).**

---

## How to use it (the five-minute version)

**Once per machine:**

```bash
git clone <this repo> ~/agent-harness && cd ~/agent-harness
python3 init.py --link-global --install-hooks --global-claude
# restart Claude Code → every project on this machine now has the suite
```

**Once per project** — in the project, in Claude Code, say **"set up the agent
harness here"** (`init-agent-harness`). It scaffolds `AGENTS.md` (guardrails +
your commands), the quality gate, and the CI file. Fill the Commands table
honestly; add Gotchas as you learn them.

**Daily — just say what you want; the skill routing does the rest:**

| You say | What fires |
|---|---|
| "grill me about 〈idea〉" | `grill-me` — frontier rounds of questions until understanding is confirmed |
| "write the PRD" → "break it into tickets" | `write-a-prd` → `prd-to-issues` (Beads: `bd ready` = the frontier) |
| "build 〈one ticket〉" | one worker, test-first (`tdd`) — most asks need exactly one agent |
| "use the orchestrator: build 〈these tickets〉" | classify type → route → managed fleet (worktrees, ledger, gates) |
| "review this 〈diff / design / release〉" | the matching read-only reviewer, verdict only |
| "research 〈question / library〉" | `debug-research` — verdict with citations |
| "how does 〈X〉 reach 〈Y〉" | `code-searcher` / `graphify` |
| "/wait-what" | the last answer, re-pitched in plain English |
| "you keep getting 〈X〉 wrong" | `evolve-harness` — turn the correction into a rule (you approve it) |

**Done = the gate passes** (lint · typecheck · tests · coverage) — enforced by
hooks and CI, not by the model's opinion. **And the rule of scale:** the pipeline
is for non-trivial work; a typo fix goes straight to build, and most asks need
one agent, not a fleet.

Deeper: [`SETUP.md`](./SETUP.md) (install paths, verification) ·
[`agents/README.md`](./agents/README.md) (the fleet + model routing) ·
[`docs/README.md`](./docs/README.md) (the doc tiers).

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

**The budget, concretely:** always-on is ~**344 lines** (`AGENTS.md` + the imported
steering doc). Naively pasting every skill and doc into context would be ~**3,700
lines, every turn** — more than **10× the cost**, and *worse* instruction-following,
because a model given 40 rules follows them worse than one given 6. (That's before
the ~1,800-line full pattern KB, which is deliberately never pasted — opened only at
a cited § when a decision is expensive to reverse.)

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
| `orchestrate-agents` | Run **parallel agents** in worktrees to ship a multi-part change; fan-out + merge-validate |
| `grill-me` · `wayfinder` | Interrogate the plan; map fuzzy scope as decision tickets |
| `write-a-prd` · `prd-to-issues` | Discussion → spec → tracer-bullet tickets with blocking edges |
| `tdd` | Test-first build loop: red before green, one vertical slice at a time |
| `codebase-design` · `domain-modeling` | Deep-module vocabulary; the glossary + light ADRs |
| `improve-codebase-architecture` | Audit existing code for deepening/refactor opportunities |
| `handoff` | Compact a session for a fresh agent to resume |
| `graphify` | Query the repo as a knowledge graph — connections, blast radius, hubs (local-first) |
| `writing-for-agents` | The craft of agent-facing docs: pointers, hierarchy, completion criteria, pruning |
| `wait-what` | User-invoked: "re-pitch that in plain English" when an answer doesn't land |
| `evolve-harness` | Grow the harness itself — new skill/rule from a repeated correction, **human-gated** |
| `init-agent-harness` | Scaffold a project's context (AGENTS.md + CLAUDE.md + docs) from your global link — no installer script |

**Subagents** (own context window)
`orchestrator` (the manager — spawns the fleet, backed by the deterministic `orchestrator_engine/`) · `code-searcher` · `test-writer` · `design-reviewer` · `debug-research` · `security-reviewer` · `deploy-reviewer` · `trend-scout` · `implementer` (+ `frontend-` / `backend-` variants) — organized in `agents/` by department: orchestration · engineering · qa · review · research

**Docs** — steering doc (always-on) + architecture patterns (compressed 14% + full KB)

---

## 🔒 Guardrails — read the caveat

Agents that read the internet ingest **untrusted input into a system that executes
things.** Four threats: **exfiltration** (disguised as telemetry), **prompt
injection** (fetched content instructing the model), **supply chain** (`install` =
arbitrary code execution), and **self-modification** (an agent rewriting its own
rules/skills from something it read — the risk the `evolve-harness` loop is built to contain).

Defenses live in `AGENTS.md` (the **6** always-on non-negotiables, deliberately),
`skills/secure-code-review/`, `agents/review/security-reviewer.md`, and — for changes to the
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
