# docs/ — the directional docs, and who reads them

## ⚠️ The thing to understand first: TWO consumers, TWO context systems

Your three directional docs have **two different audiences that read via completely
different mechanisms.** Confusing them is the #1 way this setup silently fails.

| Consumer | Reads via | Sees |
|---|---|---|
| **You, chatting** (Claude Project / claude.ai) | **Project knowledge** — RAG retrieval | Whatever you uploaded there |
| **The agent** (Claude Code, Cursor, CI) | **The filesystem** — `AGENTS.md`, skills, files on disk | **ONLY what's in the repo** |

> ### **Claude Code CANNOT see Claude Project knowledge.**
> They are separate systems. A doc uploaded *only* to Project knowledge is invisible
> to the agent running in your terminal. If the agent needs it, **it must be on disk.**

**So the docs live in both places, at two fidelities — same source, different form:**

- **Project knowledge** → the **full** docs. You're chatting, RAG handles retrieval,
  depth is free and useful.
- **This `docs/` dir** → the **agent-sized** versions. Every token is paid for on
  every turn, so compression is the whole point.

---

## What's here, and what tier it loads at

| File | Tier | Loads |
|---|---|---|
| `engineering-steering-doc.md` | **ALWAYS-ON** | Every turn. Imported by `AGENTS.md`. |
| `architecture-patterns.md` | **On-demand** | Via the `architecture-patterns` skill |
| `design-doc-template.md` | **On-demand** | Via the `write-design-doc` skill |
| `multi-agent-orchestration.md` | **On-demand** | Via the `orchestrate-agents` skill |
| `agents/work-types.md` | **On-demand** | Universal work classification — read by entry points (orchestrator step 2, main thread) at classify time |
| `workflows.md` | **On-demand** | Diagrams of the common paths (spine, feature, bug, architecture, testing) — pictures over the canonical files |
| `evals.md` | **On-demand** | Human manual for the eval runner (`evals/`) — agents route via the `eval-harness` skill |
| `architecture-patterns-FULL-KB.md` | **Reference-only** | Opened at a cited § — never read whole |
| `agentic-frameworks-knowledge-base.md` | **Reference-only** | Opened at a cited § (steering cites "Agentic KB §x") — never read whole |
| `CHANGELOG.md` | **Never loaded** | Human record of promotions |
| `design/*.md` | **On-demand** | The filled-in design docs for *this* system |

### Why the steering doc is always-on and the others are NOT

The steering doc is ~140 lines of **behavior** — how to work, what to default to,
when to stop. It applies to *every turn*, so it earns its place in the budget.

The architecture docs are **reference**. The full KB is ~1,800 lines and is
irrelevant to most turns. Loading it always-on would:

1. **Blow the context budget** on material you don't need this turn, and
2. **Dilute the rules that DO matter** — a model given 40 rules follows them worse
   than a model given 6.

That's not a compromise; it's the correct design. **The same complexity ladder from
your own docs applies to your harness: don't add a tier until the one below it
visibly fails.**

---

## The compression is lossy ON PURPOSE

`architecture-patterns.md` is a **distillation**, not a replacement. It carries the
*decision rules and triggers* — the parts that fire on a real decision. It drops the
exposition, the examples, and most of the nuance.

> **When the penalty for being wrong is high, open the FULL KB at the cited §.**
> The compressed file tells you *what* and *when*. The KB tells you *why*, and — more
> importantly — **the failure modes.**

Expensive/irreversible (→ open the KB): storage engine · service boundary · auth
model · sync-vs-async · event sourcing · sharding.
Cheap/reversible (→ the summary is fine): a library choice · a cache TTL · naming.

---

## Keeping the two copies from drifting

The honest risk of duplication: they diverge, and nobody notices.

- **The full docs are the content source.** Edit them first.
- **The repo is the durable record.** Git is where a change persists and is versioned.
  These are different axes, not a contradiction — content flows project → repo;
  durability lives in git.
- **The compressed version is derived.** When the source's *decision rules* change,
  regenerate it. When only prose or examples change, don't bother.
- **Never edit a derived file in place.** Fix the source and re-derive. Editing the
  copy gives it improvements the source doesn't have, and then neither one is right —
  this is exactly how the two forked last time.
- **The steering doc stays byte-identical** in both places (`derivation: verbatim`).

### How you can actually tell

Every file here carries a provenance header. The field that does the work is
`source_version`:

| Question | Answer |
|---|---|
| Is this copy current? | `source_version` == the source doc's current version |
| Is it a summary or the whole truth? | `derivation: compressed` vs `verbatim` |
| Has anyone confirmed it lately? | `last_verified` / `review_after` |

**Monthly, one question in the project:** *"what version is each doc at?"* — diff
against these headers. Manual by necessity: Claude Code can't read Project knowledge
and the project can't read the repo, so no automated check can span the gap. Pretending
otherwise produces a check that silently passes.

**Log every promotion** in [`CHANGELOG.md`](./CHANGELOG.md). A PR that changes `docs/`
without touching the changelog is a promotion with no record — that's how this
discipline quietly stops being followed in month three. Worth a gate.

- **Still worth keeping:** if an agent cites a § that doesn't exist, or gives advice
  the source contradicts, the compression has drifted. Fix it then.

---

## Setup checklist

- [ ] Full docs uploaded to **Claude Project knowledge** (for your own chat use)
- [ ] `engineering-steering-doc.md` copied **here**, imported by `AGENTS.md`
- [ ] `architecture-patterns.md` (compressed) **here**, routed by its skill
- [ ] `design-doc-template.md` **here**, routed by `write-design-doc`
- [ ] Full KB **on disk too** if the agent should be able to open it at a cited §
      — otherwise the skill's "open the full KB" instruction is a dead end
- [ ] `AGENTS.md` imports the steering doc **and nothing else from `docs/`**
