---
name: handoff
description: >
  Use to compact the current session into a standalone handoff document so a FRESH
  agent (or you, later) can resume the work without the transcript. Triggers on
  "hand this off", "running out of context", "write a handoff", "continue this in a
  new session", "compact this for another agent", "pass this to the next agent".
  Optionally takes what the next session should focus on.
  Do NOT use to dump the full transcript, to write a design record (`write-design-doc`),
  a PR description (`review-pr`), or a PRD (`write-a-prd`) — a handoff REFERENCES
  those, it does not replace them.
---

# Handoff: compact the session for a fresh agent

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

You're ending a session, running low on context, or passing work to another agent,
and the next one starts with **none of this conversation**. A good handoff is what
lets them resume in one read instead of re-deriving everything.

**Not this skill if:** you're recording a decision → `write-design-doc`. Opening a
PR → `review-pr`. Writing a PRD → `write-a-prd`. A handoff points *at* those
artifacts; it doesn't duplicate them.

## What a handoff is (and isn't)

> **Reference, don't restate.** The handoff links to the spec, the ADR, the issue,
> the commits, the diff — by path or URL. It is **not** a transcript dump and not a
> second copy of artifacts that already exist.

## Procedure

### 1. Summarize for continuation, not for the record

Write it forward-looking: **the goal, current state, decisions already made (with a
one-line why), what's in flight, and the immediate next step.** Enough for a cold
agent to act, no more.

### 2. Reference existing artifacts by path/URL

Specs, design docs, issues, commits, diffs — link them, don't paste them. Restating
an artifact means two copies that drift.

### 3. Add a "suggested next skills" section

Name the skills the next agent should reach for (e.g. "work the next ticket with
`tdd`; verify via `run-tests`; ship via `ci-cd`"). This is what makes the handoff
*actionable* rather than just informative.

### 4. Redact sensitive data

**Strip API keys, tokens, passwords, and PII** before writing. A handoff is a
document that gets passed around — treat it as such (this is guardrail #2 in
practice: secrets don't leak into artifacts).

### 5. Tailor to the next focus, if given

If a next-session focus was specified, orient the doc around it — foreground what
that focus needs, background the rest.

### 6. Write it to scratch, not into the repo

Save to a scratch/temp location 〈your OS temp dir · or `docs/handoffs/` if you want
it tracked〉. Don't commit it into the codebase unless that's the intent.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Next agent still lost | Summarized the past, not the next step | Write it forward-looking (goal → state → next) |
| Two drifting copies of a spec | Restated an artifact instead of linking | Reference by path/URL only |
| Secret ended up in the handoff | No redaction pass | Step 4 — strip keys/tokens/PII |
| Handoff is a transcript wall | Dumped the conversation | Compact to decisions + state + next; link the rest |

## Definition of done

- [ ] A **standalone, forward-looking** handoff doc a cold agent can act on
- [ ] Existing artifacts **referenced by path/URL**, not duplicated
- [ ] A **suggested-next-skills** section
- [ ] **Redacted** — no keys, tokens, or PII
- [ ] Tailored to the stated next focus (if any); saved to scratch, not committed by default
