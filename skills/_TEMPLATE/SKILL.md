---
name: skill-name-in-kebab-case
description: >
  Use this skill when 〈CONCRETE TRIGGER CONDITIONS〉. Covers 〈what it does〉.
  Do NOT use for 〈the nearest thing it is NOT〉.
---

<!--
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  HOW SKILLS WORK — read once, then delete this block in real skills.     ║
  ╚══════════════════════════════════════════════════════════════════════════╝

  THE THREE TIERS OF CONTEXT (this is the whole reason skills exist):

    1. `description` above  → ALWAYS in context. ~1 line. Costs you every turn.
    2. This SKILL.md body   → Loads ONLY when the description matches the task.
    3. Files in this dir    → Load only if THIS body tells the agent to read them.

  So: the description is an *index entry*, not a summary. Its ONLY job is to make
  the model correctly decide "do I need to open this?" — everything else goes in
  the body, where it's free until it's needed.

  DESCRIPTION RULES (this is where skills succeed or fail):
    • Write TRIGGERS, not topics.  ✗ "Testing best practices."
                                   ✓ "Use when running, debugging, or adding
                                      tests, or when a CI quality gate fails."
    • Include the words the user will actually say (pytest, coverage, SonarQube).
    • Add an explicit NOT clause. Overlapping skills are the #1 failure mode —
      the model opens the wrong one and follows the wrong procedure.
    • Third person, imperative. It is read by a model deciding what to load.

  BODY RULES:
    • Procedure, not philosophy. The steering doc holds the philosophy.
    • Show the exact commands. An agent that guesses a command is a bug.
    • Keep it under ~500 lines. If it's longer, split it into reference files
      in this directory and point at them from here (see "Reference files").
    • Write for a competent engineer who has never seen THIS repo.

  WHEN TO CREATE A SKILL AT ALL:
    Create one when a procedure is (a) repeated, (b) non-obvious, and (c) you
    have corrected a model on it more than once. That third condition is the
    real trigger — a repeated correction IS the signal that a skill is missing.
    Do NOT create a skill for something needed on every turn (→ AGENTS.md) or
    for something done once (→ just say it in the thread).
-->

# 〈Skill Title〉

## When to use this

〈Restate the trigger, in a sentence. The model has already decided to load this,
 so this is a confirmation check — "am I in the right place?" — not a re-pitch.〉

**Not this skill if:** 〈nearest neighbor〉 → use `〈other-skill〉` instead.

## Prerequisites

- 〈Local stack running: `docker compose up -d`〉
- 〈Deps installed: `uv sync`〉

## Procedure

### 1. 〈First step〉

```bash
〈exact command〉
```

〈What to look for. What "good" looks like. What the common failure means.〉

### 2. 〈Next step〉

```bash
〈exact command〉
```

### 3. 〈Verify〉

〈How the agent proves to itself the task actually worked — not "it ran" but
 "it produced the right outcome." Every skill needs this step; without it the
 agent will report success on a no-op.〉

## Failure modes

<!-- The highest-value section in most skills. Write these from real incidents. -->

| Symptom | Cause | Fix |
|---|---|---|
| 〈hangs, no output〉 | 〈db not up〉 | 〈`docker compose up -d db`〉 |
| 〈`ModuleNotFoundError`〉 | 〈bare `python` used〉 | 〈use `uv run`〉 |

## Definition of done

- [ ] 〈concrete, checkable〉
- [ ] 〈tests added and passing, if code changed〉
- [ ] 〈docs/diagram updated, if behavior changed〉

## Reference files

<!-- Tier 3. Only list what exists. The agent reads these ONLY if pointed here. -->

- `〈reference.md〉` — 〈read when: 〈condition〉〉
- `〈scripts/helper.py〉` — 〈run when: 〈condition〉〉
