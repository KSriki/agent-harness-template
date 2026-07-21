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

- **The full docs are the source of truth.** Edit them first.
- **The compressed version is derived.** When the KB's *decision rules* change,
  regenerate it. When only prose/examples change, don't bother.
- **The steering doc is short enough to keep byte-identical** in both places. Do that.
- **Cheap check:** if an agent ever cites a § that doesn't exist, or gives advice
  the KB contradicts, the compression has drifted. Fix it then.

---

## Setup checklist

- [ ] Full docs uploaded to **Claude Project knowledge** (for your own chat use)
- [ ] `engineering-steering-doc.md` copied **here**, imported by `AGENTS.md`
- [ ] `architecture-patterns.md` (compressed) **here**, routed by its skill
- [ ] `design-doc-template.md` **here**, routed by `write-design-doc`
- [ ] Full KB **on disk too** if the agent should be able to open it at a cited §
      — otherwise the skill's "open the full KB" instruction is a dead end
- [ ] `AGENTS.md` imports the steering doc **and nothing else from `docs/`**
