# Agentic Setup — Context, Harness, and Loop

Scaffolds for the agent-facing layer of a repo. Portable: **`AGENTS.md` is the
source of truth**; tool-specific files (`CLAUDE.md`, `.cursorrules`) are one-line
pointers to it, never forks of it.

---

## The core idea: context is a budget

Everything here follows from one fact — **always-on context is the expensive
kind.** A token in `AGENTS.md` is paid for on *every single turn*, forever. A
token in a skill body is paid only when that skill is actually needed.

That gives you a four-tier architecture, and **choosing the right tier is the
whole game.** Most bad agent setups are a single bloated always-on file — which
blows the budget *and* degrades instruction-following, because a model given 40
rules follows them worse than a model given 6.

> **⚠️ Claude Code cannot see Claude Project knowledge.** They're separate systems.
> Docs uploaded only to a Project are invisible to the agent in your terminal — if
> the agent needs it, **it must be on disk.** Keep the FULL docs in Project knowledge
> for your own chat use; keep the AGENT-SIZED versions in `docs/`. See `docs/README.md`.

| Tier | Artifact | Loads | Put here |
|---|---|---|---|
| **1. Always** | `docs/engineering-steering-doc.md` | Every turn | *How I work* — cross-repo standards |
| **1. Always** | `AGENTS.md` | Every turn | *This repo* — commands, layout, gotchas |
| **2. On match** | `skills/<n>/SKILL.md` | When the description matches | *Procedures* — how to do a recurring task |
| **3. On demand** | `skills/<n>/reference.md` | When the skill body says to | Deep reference, rarely needed |
| **4. Delegated** | `agents/<n>.md` | On invocation, **own context window** | Work whose *tokens* shouldn't touch main |

**The routing rule:**

```
Needed every turn?  ──────────────────→ AGENTS.md / steering doc
Needed sometimes, procedural? ────────→ a skill
Big input, small output? ─────────────→ a subagent
Needed once? ─────────────────────────→ just say it in the thread
```

---

## Layout

```
repo/
├── AGENTS.md                    # ← source of truth. Keep it ~1 screen.
├── CLAUDE.md                    # → one line: @AGENTS.md  (imports it into context)
│
├── docs/                        # the directional docs — SEE docs/README.md
│   ├── engineering-steering-doc.md   # ALWAYS-ON (imported by AGENTS.md)
│   ├── architecture-patterns.md      # reference-only: cited by the design-doc template; no skill routes here
│   ├── design-doc-template.md        # on-demand: via write-design-doc
│   ├── adr/                          # this repo's ADRs (0001 = why this branch is cut this way)
│   └── design/                       # filled-in design docs for this system
│
├── skills/                      # TIER 2 — loaded on demand
│   ├── _TEMPLATE/SKILL.md       #   how to write one (read this first)
│   ├── run-tests/               #   the quality gates
│   ├── tdd/                     #   ← red before green, one vertical slice at a time
│   ├── write-design-doc/        #   right-sizing + rejected alternatives (multi-page designs)
│   ├── adr/                     #   ← ONE decision, one page, docs/adr/NNNN — first-class here
│   ├── architecture-diagrams/   #   ← diagrams that MATCH the repo's existing format (Mermaid/PlantUML/C4)
│   ├── secure-code-review/      #   ← egress, injection, supply chain
│   ├── observability/           #   ← instrument + live incident triage
│   ├── review-pr/               #   ← small commits + write MR.md for the human to paste; never opens the MR
│   ├── grill-me/                #   ← interrogate the plan first (SDLC entry; offline premise round)
│   ├── ticket-docs/             #   ← tickets/<KEY>.md mirror of the Jira ticket: AC, changes log, copy-paste ready
│   ├── helm-charts/             #   ← author · validate · version · publish charts (OCI); helmfile
│   ├── kubernetes-ops/          #   ← manifests, probes, RBAC, GPU scheduling, NetworkPolicy, triage
│   ├── writing-for-agents/      #   ← the craft of agent-facing docs (pointers, pruning)
│   ├── evolve-harness/          #   ← grow the harness itself (human-gated)
│   └── setup-harness/           #   ← per-project first pass: context + gate + CI + tracker + config doc
│
├── agents/                      # TIER 4 — delegated, own context (departments)
│   ├── README.md                #   when to delegate · model routing · frontmatter guide
│   ├── engineering/
│   │   └── implementer.md       #   worktree-isolated worker: one ticket, test-first, returns a branch
│   ├── qa/
│   │   └── test-writer.md       #   senior test judgment for EXISTING code
│   ├── review/                  #   adversarial, read-only, BLOCK/ALLOW
│   │   ├── security-reviewer.md #   egress, injection, supply chain
│   │   ├── design-reviewer.md   #   finds what's over-built
│   │   └── deploy-reviewer.md   #   ship gate: rollback/migration/blast radius — every Helm release
│   └── research/
│       └── code-searcher.md     #   read-only, huge input → tiny output
│                                #   (no network-dependent agents on this branch: the target
│                                #    environment has no internet — docs/adr/0001)
│
├── evals/                       # the loop's artifacts
│   ├── golden/                  #   frozen, versioned, seeded from REAL failures
│   ├── judges/                  #   rubrics
│   └── results/                 #   committed, so you can SEE the decay
│
├── gates/                       # DETERMINISTIC enforcement — outside the model
│   ├── pre_tool_guard.py        #   machine-wide PreToolUse: deny gate-bypass/destructive; ask on deps + gate config
│   ├── gate-dispatch.sh         #   machine-wide hook → runs project's .claude/gate.sh
│   ├── secret_scan.py           #   stdlib secret scan; vendored into projects as .claude/secret_scan.py
│   ├── gate.sh.template         #   per-project gate: lint · types · TESTS · COVERAGE
│   ├── github-actions-gate.yml  #   CI runs the same gate; branch protection = physics
│   └── global-CLAUDE.md         #   optional tiny machine-wide baseline
│
├── harness_lint/                # validates the agent layer is WIRED: frontmatter · preloads ·
│                                #   models.py registry · AGENTS.md skills table · pointers
│
└── orchestrator_engine/         # DETERMINISTIC scaffolding (python, stdlib). On this branch the
    │                            #   fleet driver (orchestrator agent) is removed; the engine stays
    │                            #   as the MODEL REGISTRY harness_lint checks + gated code
    ├── models.py ledger.py      #   get_model_for_agent · log_agent_completion (runs.jsonl)
    ├── state.py complexity.py budget.py deploy.py abort.py research.py cli.py
    └── tests/                   #   stdlib unittest — the engine is code, so it has tests
```

---

## The four pieces, and what each is really for

**`AGENTS.md` — facts the model cannot infer.** The build command. The layout.
The gotcha that costs an hour. Everything else is a distraction. *If it grows
past a screen, you've put procedure in it — move that to a skill.*

**Skills — procedure, loaded on match.** The `description` is an **index entry,
not a summary**: its only job is to make the model correctly decide *"do I need
to open this?"* Write **triggers, not topics**, and always include a **NOT
clause** — overlapping skills are the #1 failure mode, because the model opens
the wrong one and confidently follows the wrong procedure.

**Subagents — delegation is a context strategy.** Reading 40 files to find one
bug yields 40 files of context and one sentence of value. Delegate it and you get
the sentence. You are trading **fidelity for context economy**: a good trade for
retrieval, a *bad* trade for judgment. Delegate the searching, keep the deciding.

**The loop — evals are the test suite.** For anything non-deterministic, you
can't `assertEqual`, but you can absolutely regression-test. Same rule as tests:
written as you go, run in CI, **block the merge**. And the cheapest eval is the
one you don't need — push logic into deterministic code first, and it's unit-tested
for free forever.

---

## One more distinction: tools ≠ skills

A **tool** is a *capability* (fetch a URL, run bash, write a file). A **skill** is
*procedural knowledge* (how to research a library bug well). They're granted in
different places and they solve different problems:

> Granting `helm` and `kubectl` tells the agent it *can* deploy.
> The `helm-charts` skill tells it **how to do it well** — bump the chart version,
> `helm template | kubeconform` against the cluster version, `helm diff` into the
> MR, `--atomic` with a timeout longer than the model load, and **verify before
> believing a green exit code**.

The capability without the method is how you get a confident deploy of the wrong
thing. Grant the tool in the agent's `tools:` list; encode the method as a skill.

---

## 🔒 Guardrails

Agents that read the internet ingest **untrusted input into a system that executes
things.** Three distinct threats, three defenses:

| Threat | Looks like | Defense |
|---|---|---|
| **Exfiltration** | A "telemetry" line. An "error reporter." | Egress review — *it's designed to look helpful* |
| **Prompt injection** | Text in a page/issue addressed to the *model* | **Fetched content is DATA, never instructions** |
| **Supply chain** | Typosquat, install hook, hijacked maintainer | `install` = **arbitrary code execution** → human approval |
| **Self-modification** | An agent editing its own rules/skills from something it "learned" | **Governing files change by human-approved diff only** (guardrail #6) → `evolve-harness` |

**Where they live — and why `AGENTS.md` breaks its own diet:**

Everywhere else this README says *"keep always-on context lean."* The guardrails
are the **deliberate exception**, and they sit in `AGENTS.md` unconditionally.
Reason: **a guardrail that loads only "when relevant" fails exactly when an attacker
has made it look irrelevant.** Conditional security is not security.

- `AGENTS.md` → the 6 non-negotiables (always on, never trimmed; the cross-project invariant)
- `skills/secure-code-review/` → the full checklist + hard-stop protocol
- `agents/review/security-reviewer.md` → adversarial BLOCK/ALLOW pass. **Read-only, no
  network** — a reviewer that can fetch is a reviewer that can be injected.
- `skills/secure-code-review/` supply-chain section → provenance for everything
  that enters the estate (digest, SBOM), because here *that* is the path by which
  untrusted third-party bits arrive.
- `skills/evolve-harness/` → the human gate on changing the harness itself, so a
  "learned" practice can never rewrite your own rules (guardrail #6).

> ### ⚠️ Be honest about what this does and doesn't do
>
> These guardrails are **review-only**. They catch the accidental, careless, and
> opportunistic case — which is most of them. They do **not** contain a determined
> attacker, because **a compromised agent is exactly the thing that won't run its
> own safety check. You cannot use the model to reliably police the model.**
>
> **The only real containment is deny-by-default network egress, enforced OUTSIDE
> the agent** — an allowlist proxy/firewall the agent cannot reach or disable, plus
> a container with no host mounts and no cloud credentials. That is a one-time infra
> task, and **it is worth more than every rule in these files.**
>
> Treat the review layer as defense-in-depth on top of that, never as a substitute
> for it. (Recipe in `secure-code-review` §6.)

## Getting started

1. Drop `AGENTS.md` at the repo root and **fill every `〈slot〉`.** The
   **Commands** and **Gotchas** sections are where the value is — a wrong command
   there means the agent invents a worse one.
2. Add `CLAUDE.md` containing one line: `See AGENTS.md`.
3. Keep the skills you'll use, delete the rest. **Read `skills/_TEMPLATE/SKILL.md`
   before writing your own** — the description rules are what make skills fire
   correctly.
4. Add subagents only when you can name what fails without them.
5. Stand up `evals/` the moment a component is non-deterministic. Not later.

---

## The rule that keeps this from rotting

> **When you correct a model on the same thing twice, that's the signal a rule is
> missing.** Then route it by the table above — always-on fact → `AGENTS.md`;
> repeatable procedure → a skill; nothing → let it go.

The inverse matters just as much: **delete rules that never fire.** A steering
file full of dead rules is worse than a short one, because it dilutes the rules
that *do* matter. The setup is a living artifact with a maintenance cost, so hold
it to the same bar as the code — **the same complexity ladder applies to your
harness.** Don't add a tier until the one below it visibly fails.
