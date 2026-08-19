---
doc: workflows
version: 1.0.0
updated: 2026-08-18
status: active
source: docs/agents/work-types.md (taxonomy) + agents/orchestration/orchestrator.md (the 12-step spine)
derivation: diagrams over the canonical files — pictures, not a second source of truth
load: on-trigger
triggers: [how does the workflow go, workflow diagram, what happens when I say, pipeline shape]
review_after: 2026-11-18
---

# Workflows — the common paths, drawn

> Diagrams of what actually happens for each kind of ask. The **taxonomy** lives
> in [`docs/agents/work-types.md`](./agents/work-types.md) and the **step
> sequence** in the orchestrator — this file only draws them. If a diagram and
> those files disagree, the files win.

## The orchestrator's 12-step spine (every managed run)

```mermaid
flowchart TB
    subgraph startup ["Startup (1–4)"]
        S1["1 Get the target"] --> S2["2 Classify — work-types.md"] --> S3["3 Assess scale<br/>(assess-complexity)"] --> S4["4 Init / resume state<br/>(bd ready = frontier)"]
    end
    subgraph loop ["Build loop (5–10)"]
        S5["5 Plan by ownership"] --> S6["6 Contract FIRST"] --> S7["7 Dispatch workers<br/>(worktrees, model ladder)"] --> S8["8 Arbitrate ledger"] --> S9["9 Review diffs<br/>(decorrelated)"] --> S10["10 Merge-validate<br/>(full gate, combined)"]
    end
    subgraph close ["Close (11–12)"]
        S11["11 Record<br/>(PRODUCT · REGISTRY · learnings)"] --> S12["12 Exit by class<br/>SUCCESS / ESCALATION / ABORT"]
    end
    S4 --> S5
    S10 --> S11
    S3 -. "single-verdict types<br/>(judge · research · eval · locate)" .-> S12
```

## Add a feature (Type A)

```mermaid
flowchart LR
    A["'Add 〈feature〉'"] --> G["grill-me<br/>(if scope fuzzy)"] --> P["PRD-lite<br/>(write-a-prd)"] --> T["prd-to-issues<br/>(tracer bullets + edges)"] --> B["build test-first<br/>(1–3 workers, tdd)"] --> R["review-pr"] --> M["merge-validate<br/>gate full"] --> SHIP["ship (ci-cd)"]
```

Small, well-understood feature? Skip straight from the ask to build — the
pipeline is for non-trivial work (the escape valve).

## Fix a bug (Type B) — and the hotfix variant

```mermaid
flowchart LR
    BUG["'Fix 〈bug〉'"] --> TRI["triage<br/>(reproduce, locate)"] --> RED["write the FAILING test<br/>(red — proves the bug)"] --> FIX["minimal fix<br/>(green)"] --> GATE["gate full"] --> SHIP["ship"]
    P1["'P1 / prod down'"] -. "hotfix: fix NOW,<br/>paperwork after" .-> FIX
    SHIP -. hotfix only .-> RETRO["retro ticket +<br/>decision-log line"]
```

One worker, always. The failing test comes *before* the fix — a bug fix without
a red test is a guess that compiles.

## Architecture decision — prepare, then escalate

```mermaid
flowchart LR
    Q["'Should we 〈split / pattern /<br/>storage / auth〉…'"] --> AP["architecture-patterns<br/>(+ FULL-KB at cited §)"] --> OPT["options + tradeoffs +<br/>recommendation<br/>(write-design-doc draft)"] --> RUNG["rung check (new-service)<br/>if it adds a component"] --> DR["design-reviewer judges<br/>the draft"] --> H{{"HUMAN decides"}}
    H --> REC["record: design doc / ADR<br/>(+ REGISTRY.md if repo strategy)"] --> BUILD["then build tickets"]
```

The fleet never decides expensive-to-reverse questions. The references outrank
model priors — that's what makes N agents give one answer.

## Testing & the gate (how "done" is proven, every path)

```mermaid
flowchart LR
    subgraph tdd ["Inside a slice (tdd)"]
        W["write failing test<br/>(red)"] --> C["minimal code<br/>(green)"] --> RF["refactor"] --> W
    end
    RF --> E["every edit →<br/>hook: gate fast (lint)"]
    E --> DONE["'I'm done' →<br/>hook: gate full<br/>lint · format · tests · coverage"]
    DONE -->|red| BLOCKED["turn BLOCKED —<br/>failures fed back"] --> C
    DONE -->|green| PR["PR → CI runs the<br/>SAME gate.sh full"] -->|green + branch protection| MERGE["merge"]
```

One script (`.claude/gate.sh`) is the definition of done at all three layers —
edit hook, stop hook, CI. Coverage is a floor set at honest reality and raised
by tickets, never gamed.

Changelog:
- 2026-08-18 — 1.0.0: initial — spine + the four most-asked paths (feature,
  bug/hotfix, architecture, testing).
