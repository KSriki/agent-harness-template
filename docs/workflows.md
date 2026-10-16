---
doc: workflows
version: 1.2.0
updated: 2026-10-16
status: active
source: docs/agents/work-types.md (taxonomy) + the skills each path names
derivation: diagrams over the canonical files — pictures, not a second source of truth
load: on-trigger
triggers: [how does the workflow go, workflow diagram, what happens when I say, pipeline shape]
review_after: 2026-11-18
---

# Workflows — the common paths, drawn

> Diagrams of what actually happens for each kind of ask. The **taxonomy** lives
> in [`docs/agents/work-types.md`](./agents/work-types.md) and the **procedures**
> in the skills each box names — this file only draws them. If a diagram and
> those files disagree, the files win.

## Ship a platform change (chart · manifest · pipeline) — the common path here

```mermaid
flowchart LR
    T["ticket"] --> D{"decision<br/>in it?"}
    D -- yes --> ADR["adr<br/>(human confirms)"] --> B
    D -- no --> B["build test-first<br/>(tdd · helm-charts · kubernetes-ops)"]
    B --> V["helm lint · kubeconform ·<br/>helm unittest · gate full"] --> MR["review-pr (MR)<br/>+ security-reviewer if external code"] --> DR["deploy-reviewer<br/>BLOCK / ALLOW"] --> H["human: pull branch into the<br/>testing env · helmfile apply · verify"]
```

## Add a feature (Type A)

```mermaid
flowchart LR
    A["'Add 〈feature〉'"] --> G["grill-me<br/>(premise gate; if scope fuzzy)"] --> T["ticket-docs<br/>(plan: steps = commits)"] --> B["build test-first<br/>(1–3 workers, tdd)"] --> R["review-pr"] --> M["merge-validate<br/>gate full"] --> SHIP["ship (human applies)"]
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
    Q["'Should we 〈split / pattern /<br/>storage / auth〉…'"] --> AP["ladder check (steering §0)<br/>+ existing ADRs"] --> OPT["options + tradeoffs +<br/>recommendation<br/>(write-design-doc draft)"] --> RUNG["ladder check (steering §0)<br/>if it adds a component"] --> DR["design-reviewer judges<br/>the draft"] --> H{{"HUMAN decides"}}
    H --> REC["record: adr<br/>(design doc if multi-page)"] --> BUILD["then build tickets"]
```

The agent never decides expensive-to-reverse questions. The references outrank
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
- 2026-10-16 — 1.2.0: second cut — ci-cd / prd-to-issues / architecture-patterns
  boxes replaced by ticket-docs, the ladder, and the human's testing-env apply.
- 2026-10-16 — 1.1.0: enterprise-ai-platform branch — orchestrator spine removed
  with the agent; added the platform-change path (adr → build → validate → MR →
  deploy-reviewer → ci-cd); architecture path records via `adr`.
- 2026-08-18 — 1.0.0: initial — spine + the four most-asked paths (feature,
  bug/hotfix, architecture, testing).
