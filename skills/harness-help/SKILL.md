---
name: harness-help
description: >
  Use when the user asks how to customize the harness or where something goes:
  "how do I add a rule / gotcha / skill", "where do I change the gate", "what
  file controls X", "how do I make this repo's agents do Y", "what should I
  edit". Answers with the specific file + section, in place. Do NOT use to
  actually apply a harness change (that's `evolve-harness`, human-gated), to
  set up a project (`init-agent-harness`), or for machine install (SETUP.md §0).
---

# /harness-help — where does my change go?

Route the question with this table, open the target file, and answer with the
specific section. Propose diffs; **never self-apply** changes to guardrails,
the steering doc, skills, or subagent definitions (AGENTS.md guardrail 6).

| You want to… | Go to |
|---|---|
| Add a repo rule, gotcha, or command | `AGENTS.md` → *Repo-specific rules* / *Gotchas* / *Commands* — edit directly, no ceremony |
| Add business rules / domain terms | `domain-modeling` skill → `CONTEXT.md` glossary |
| Change what "done" means (lint/tests/coverage) | `.claude/gate.sh` (this repo's checks) · `gates/README.md` (how the layers work) |
| Make CI enforce the gate | copy `gates/github-actions-gate.yml` → `.github/workflows/gate.yml` + branch protection |
| Add / edit / prune a skill or subagent | `evolve-harness` (the gate) + `writing-for-agents` (the craft) |
| Change guardrails or the steering doc | human-only edit — draft via `evolve-harness`, never auto-applied |
| Set up a new project with the harness | `init-agent-harness` skill (in-Claude) or `python3 init.py` (fallback) |
| New machine install / symlinks / hooks | `SETUP.md` §0 · `HARNESS.md` "How to use it" |
| Understand why it's built this way | `ARCHITECTURE.md` |

If the question is really a repeated correction ("you keep getting X wrong"),
don't just answer — offer `evolve-harness` to make the fix durable.
