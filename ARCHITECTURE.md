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
│   ├── architecture-patterns.md      # on-demand: COMPRESSED pattern reference
│   ├── design-doc-template.md        # on-demand: via write-design-doc
│   ├── multi-agent-orchestration.md  # on-demand: via orchestrate-agents skill
│   └── design/                       # filled-in design docs for this system
│
├── skills/                      # TIER 2 — loaded on demand
│   ├── _TEMPLATE/SKILL.md       #   how to write one (read this first)
│   ├── run-tests/               #   the quality gates
│   ├── new-service/             #   ← enforces the complexity-rung check
│   ├── write-design-doc/        #   right-sizing + rejected alternatives
│   ├── eval-harness/            #   the loop: evals, judges, HITL
│   ├── debug-research/          #   ← the bug is in THEIR code, not ours
│   ├── secure-code-review/      #   ← egress, injection, supply chain
│   ├── architecture-patterns/   #   ← routes to the pattern reference
│   ├── ci-cd/                   #   ← pipeline, deploy, release, rollback
│   ├── observability/           #   ← instrument + live incident triage
│   ├── review-pr/               #   ← open a PR / review one (not security)
│   ├── orchestrate-agents/      #   ← parallel agents in worktrees; fan-out + merge-validate
│   ├── grill-me/                #   ← interrogate the plan first (SDLC entry)
│   ├── wayfinder/               #   ← fuzzy scope → decision tickets; mid-build re-entry
│   ├── write-a-prd/             #   ← discussion → spec, ready-for-agent
│   ├── prd-to-issues/           #   ← spec → tracer-bullet tickets + blocking edges
│   ├── tdd/                     #   ← red before green, one vertical slice at a time
│   ├── codebase-design/         #   ← deep modules, seams, design-it-twice
│   ├── domain-modeling/         #   ← CONTEXT.md glossary + sparing ADRs
│   ├── improve-codebase-architecture/  # ← audit existing code for deepening
│   ├── handoff/                 #   ← compact session → resumable doc
│   ├── evolve-harness/          #   ← grow the harness itself (human-gated)
│   └── init-agent-harness/      #   ← scaffold per-project context + tracker/labels/glossary
│
├── agents/                      # TIER 4 — delegated, own context
│   ├── README.md                #   when to delegate (and when NOT to)
│   ├── code-searcher.md         #   read-only, huge input → tiny output
│   ├── test-writer.md           #   bounded diff
│   ├── design-reviewer.md       #   judgment — finds what's over-built
│   ├── debug-research.md        #   context firewall for external research
│   ├── security-reviewer.md     #   adversarial: BLOCK/ALLOW, read-only
│   ├── deploy-reviewer.md       #   adversarial ship gate: rollback/migration/blast radius
│   ├── trend-scout.md           #   periodic trend survey → proposals only (never applies)
│   └── implementer.md           #   worktree-isolated worker: builds one slice in a fan-out
│
└── evals/                       # the loop's artifacts
    ├── golden/                  #   frozen, versioned, seeded from REAL failures
    ├── judges/                  #   rubrics
    └── results/                 #   committed, so you can SEE the decay
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

> Granting a fetch tool tells the agent it *can* search the web.
> The `debug-research` skill tells it **how to search well** — pin the version
> first, read the installed source before the internet, distrust a 2019 Stack
> Overflow answer for a library now on v5, and **verify locally before believing
> anything**.

The capability without the method is how you get a confident answer sourced from a
stale blog post. Grant the tool in the agent's `tools:` list; encode the method as
a skill.

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
- `agents/security-reviewer.md` → adversarial BLOCK/ALLOW pass. **Read-only, no
  network** — a reviewer that can fetch is a reviewer that can be injected.
- `skills/debug-research/` §3.5 → mandatory security gate, because *that* skill is
  the one whose job is ingesting untrusted third-party text.
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
