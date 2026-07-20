# Scheduled trend-research (Tier-3 reference)

> **Read when:** wiring the `trend-scout` agent to run on a schedule, or setting up
> the "keep up with trends" loop referenced in `evolve-harness`. This is depth — the
> skill body already covers the manual case.

## The loop, in one line

**Research on a timer; adopt on a human.** A scheduled `trend-scout` *drafts*
proposals; a person runs the approved ones through `evolve-harness` STEP 3–4. The
schedule is **never** wired to the apply step (guardrail #6).

## Flow

```
[cron: monthly / quarterly]
      │
      ▼
 trend-scout  ── reads AGENTS.md + steering doc + skills/ + lockfiles,
      │           surveys the ecosystem (version-dated), runs the security gate
      ▼
 proposals artifact  ── ranked candidate changes, PROPOSALS ONLY,
      │                 written to a review surface (a dated file / issue / draft PR)
      ▼
 human review  ── keep the few worth it, drop the rest
      │
      ▼
 evolve-harness STEP 3–4  ── draft the diff, human approves, commit
```

## Cadence — slower than you'd think

- **Monthly or quarterly.** Ecosystems and harness practice move in months, not
  days. A weekly pass produces **churn, not signal** — and churn degrades the
  harness, because oscillating/dead rules dilute the live ones.
- **Security advisories are the exception**, but they are *not* this scout's job:
  fast CVE alerting belongs to **automated SCA in CI, running OUTSIDE the agent**
  (`secure-code-review` §6). The scout is for *practice and version* drift.

## Activate it (in a real fork, with a real stack)

This template ships the **capability**, not a live job — a scheduled pass against
the placeholder `〈stack〉` would research nothing. In a filled-in fork:

1. Use the `schedule` skill (or your own scheduler / a CI cron) to run, e.g.
   monthly, with a prompt like:

   > "Run the `trend-scout` agent. Survey what changed for our stack (see
   > `AGENTS.md`) and in agent-harness practice since last cycle. Return ranked
   > proposals per its output contract, written to
   > `docs/harness-proposals/〈date〉.md`. **Do not edit any skill, agent, `AGENTS.md`,
   > or the steering doc — proposals only.**"

2. Point the output at a **review surface a human actually sees** — a dated file, a
   tracking issue, or a *draft* PR. Never a surface that merges itself.

3. On review day, run each accepted proposal through `evolve-harness` (STEP 3–4).

## Anti-patterns (each one breaks the safety model)

- ❌ Wiring the schedule to `evolve-harness`'s **apply** step. The human gate is the
  entire point; automating past it *is* guardrail #6's failure mode.
- ❌ A daily/weekly cadence → harness churn, not currency.
- ❌ Letting the scout **install, run, or edit** anything. It is
  read-untrusted-only and propose-only, precisely so an injected or compromised
  result cannot act.
- ❌ Proposals landing on an **auto-merge** branch. A proposal no human reads is a
  self-modification with extra steps.
