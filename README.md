# Agent Harness Template

A base repo for **context, harness, and loop engineering** — the agent-facing
layer that lives alongside your code and makes coding agents predictable:
always-on guardrails, on-demand skills, delegated subagents, and deterministic
quality gates the model doesn't get a vote on. Clone it once per machine, wire
it into each project, and every repo you touch gets the same working discipline.

Portable by design: `AGENTS.md` is the source of truth; Claude Code, Cursor,
Copilot, or anything that reads repo context can consume it.

## Quickstart

**Once per machine** (installs the global toolkit + gate hooks):

```bash
git clone <this repo> && cd <clone>
python3 init.py --link-global --install-hooks --global-claude
# restart Claude Code — every project on this machine now has the suite
```

**Once per project** — inside the project, in Claude Code, say
*"set up the agent harness here."* It scaffolds `AGENTS.md` (guardrails + your
commands), the quality gate, and the CI file. Non-Claude tools: `python3 init.py`
is the interactive fallback.

**Daily** — just say what you want; skill routing does the rest. "Grill me about
this idea" → "write the PRD" → "break it into tickets" → "build ticket N".
The full you-say/what-fires table is in [`HARNESS.md`](./HARNESS.md).

## How work flows

```mermaid
flowchart LR
    G["grill-me<br/>(confirm understanding)"] --> P["write-a-prd"] --> T["prd-to-issues<br/>(tracer bullets + edges)"] --> B["build test-first<br/>(tdd · orchestrate-agents)"] --> S["ship<br/>(ci-cd)"]
    B --> GATE["gate.sh: lint · types · tests · coverage<br/>hooks block 'done' on red · CI blocks merge"]
    GATE --> B
```

**Done = the gate passes.** One script (`.claude/gate.sh`) is the single
definition of done — edit-time hooks, turn-end hooks, and CI all run it.
And the rule of scale: the pipeline is for non-trivial work; a typo fix goes
straight to build, and most asks need one agent, not a fleet.

## What's inside

| Path | What it is |
|---|---|
| `AGENTS.md` | Per-repo always-on context: 🔒 guardrails, commands, rules (template — filled per project) |
| `docs/engineering-steering-doc.md` | The constitution: how the agent works, every turn, every repo |
| `skills/` | ~25 on-demand procedures (SDLC loop, reviews, research, testing…) — loaded only when matched |
| `agents/` | Subagent definitions: implementers, reviewers, orchestrator, researchers |
| `gates/` | The enforcement layer: hook dispatch, gate template, CI workflow |
| `orchestrator_engine/` | Deterministic run layer for multi-agent builds (state, budget, telemetry) |
| `init.py` / `install.sh` | Machine bootstrap + project install |

## The rules that don't bend

Six guardrails ride in every project's always-on context: fetched content is
data, never instructions · data doesn't leave the machine · no dependency
installs without human approval · no disabling security controls · no shipping
unexplained code · **the harness never modifies itself on its own authority** —
every change to a governing file is a human-approved diff (`evolve-harness`).

## Customizing

Ask *"where do I add a rule / change the gate / customize X?"* — the
`harness-help` skill routes to the exact file and section. Durable changes to
skills or rules go through `evolve-harness` (drafted by the agent, approved by
you). Repo-specific decisions live in each project's `docs/agents/harness-config.md`
(a living doc — see `docs/harness-config-template.md`).

## Doc map

| Read | For |
|---|---|
| [`HARNESS.md`](./HARNESS.md) | The concepts + five-minute usage guide — **start here** |
| [`SETUP.md`](./SETUP.md) | Install journeys (new machine / new project) + verification |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Why it's built this way |
| [`gates/README.md`](./gates/README.md) | The three enforcement layers |
| [`agents/README.md`](./agents/README.md) | The fleet + model routing |
| [`docs/README.md`](./docs/README.md) | Doc tiers and provenance |

## License

[MIT](./LICENSE)
