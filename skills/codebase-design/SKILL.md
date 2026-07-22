---
name: codebase-design
description: >
  Use to design or improve a single MODULE's interface — deciding where a seam
  goes, making code more testable / AI-navigable, or judging whether a module is
  too shallow. Provides the deep-module vocabulary other skills reuse. Triggers on
  "design this module", "where should the seam go", "make this testable", "is this
  interface too shallow", "ports and adapters", "design it twice", "deep module".
  Do NOT use for system-level pattern choices — sync vs async, caching, CQRS,
  scaling — that's `architecture-patterns`; for whether to add a whole component
  (`new-service`); or for writing the tests themselves (`tdd` / `run-tests`).
---

# Codebase design: deep modules, seams, design-it-twice

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

Designing the *interface* of a module so it hides complexity behind a small surface.
This is the shared vocabulary the architecture/refactor skills lean on — load it when
you're shaping a module boundary or another skill sends you here for the terms.

**Not this skill if:** it's a system-level pattern (sync/async, caching, CQRS,
scaling) → `architecture-patterns`. It's "should this be its own service" →
`new-service`. It's writing tests → `tdd`.

## The vocabulary (load-bearing — use these words precisely)

- **Module** — a scale-agnostic unit (function, class, package) with an interface and an implementation.
- **Interface** — the *complete* surface: signatures, invariants, constraints, error handling, config, performance expectations. (Not just the type signature.)
- **Depth** — behavior accessible per unit of interface learned. **Deep** modules hide complexity; **shallow** ones expose it.
- **Seam** — a place where you can alter behavior *without editing in that place* (Feathers). Distinct from the implementation behind it.
- **Adapter** — a concrete implementation satisfying an interface at a seam.
- **Leverage** — capability per unit of learning, for callers. **Locality** — concentrated change, for maintainers. Depth buys both.

## Design principles

- Depth lives in the **interface contract**, not the internal structure.
- **Test the interface the way callers use it.**
- Introduce a **seam only when variation actually exists** — not speculatively.
- **Accept dependencies; return results, not side effects.**
- Minimize method count and parameter complexity.

**Anti-patterns:** shallow modules that expose a near-complete implementation surface;
treating "interface" as just the type signature; confusing seams with DDD boundaries.

## Dependencies → where the seam goes (the deletion test)

Apply the **deletion test** to a candidate: would collapsing it *concentrate*
complexity (good) or just move it around (not yet)? Then classify each dependency:

| Dependency kind | Seam treatment |
|---|---|
| **In-process / pure** | deepen directly — no adapter |
| **Local-substitutable** (in-memory FS, PGLite…) | internal seam, test stand-in — no port |
| **Remote but owned** | **ports & adapters** — define a port at the seam, inject transport as an adapter, in-memory adapter for tests |
| **True external** (payment, email…) | inject as a port, **mock** adapter in tests |

> **Seam discipline:** *one adapter is a hypothetical seam; two adapters is a real
> one.* Don't add a port for a single adapter — that's just indirection.

## Design it twice (before committing to an interface)

Your first idea is rarely the best (Ousterhout). For a non-trivial interface:

1. **Frame the problem** — write the constraints, the dependency categories, a short
   illustrative sketch; show it to the human.
2. **Spawn 3+ implementer/`Explore` sub-agents in parallel** (the Agent tool — this is
   an `orchestrate-agents` fan-out), each producing a *radically different* interface
   under a different constraint: (a) minimize interface / max leverage, (b) maximize
   flexibility, (c) optimize the common caller, (d) ports-&-adapters for cross-seam
   deps. Each returns: interface + a usage example + what it hides behind the seam +
   its dependency strategy + trade-offs.
3. **Compare by depth, locality, and seam placement**, then give an opinionated
   recommendation (or a hybrid).

## Definition of done

- [ ] The interface hides complexity — deep, not shallow (behavior ≫ surface)
- [ ] Seams placed only where **real** variation exists (two-adapter rule)
- [ ] Dependencies classified; ports/mocks only at true boundaries
- [ ] For non-trivial interfaces, **designed twice** and compared before committing
