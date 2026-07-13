---
name: eval-harness
description: >
  Use when building, running, or debugging evaluations for LLM or agent
  components: golden sets, regression evals, LLM-as-judge, rubric scoring,
  human-in-the-loop review gates, or agent trajectory/decision-path evaluation.
  Triggers on "eval", "judge", "golden set", "the agent got worse", "how do we
  know the prompt change helped", "HITL", "score the outputs".
  Do NOT use for deterministic code — that's `run-tests`. Tests assert; evals score.
---

# Evals: the test suite for non-deterministic components

## When to use this

Any component whose output is **not deterministic** — an LLM call, an agent, an
SLM worker, a retrieval step, a CV model. You cannot `assertEqual` these, but you
absolutely can regression-test them. Evals **are** the tests here, and they get
the same rigor: written as you go, run in CI, block the merge.

**Not this skill if:** the thing under test is deterministic → `run-tests`.

---

## STEP 0 — Make it deterministic first

> **The cheapest eval is the one you don't need.** Before scoring model output,
> check whether the logic could be *in code* instead.

Push as much control flow as possible into deterministic code and reserve the
model for what genuinely needs judgment. Every branch you move out of the model
is a branch you can unit-test for free and never has to be scored again.

Ask: is the model *deciding*, or just *formatting*? If it's routing, validating,
or parsing — that's often code.

---

## STEP 1 — Build the golden set before you tune anything

Without a fixed eval set, "the prompt is better now" is a vibe. This is the
single highest-leverage artifact in the loop.

- **Seed it from reality.** Real inputs, real failures. Every production bug
  becomes a golden case — that's how the set earns its coverage.
- **Cover the edges deliberately:** the happy path, the ambiguous case, the
  adversarial/injection case, the empty/malformed input, the long input.
- **Freeze it and version it.** 〈`evals/golden/*.jsonl`〉, in git. If the set
  moves under you, your regressions are meaningless.
- **Size:** start at 〈20–50〉 cases. Small and honest beats large and synthetic.

```
〈evals/
  golden/           # frozen cases, versioned  {input, expected|rubric, tags}
  judges/           # judge prompts + rubrics
  runners/          # execution + scoring
  results/          # scored runs, timestamped, committed for trend
  run.py〉
```

---

## STEP 2 — Choose the scorer (cheapest that works)

Escalate only when the cheaper one can't express the criterion.

| Scorer | Use when | Notes |
|---|---|---|
| **Exact / regex / schema** | Structured output, valid JSON, required field | Free, instant, no drift — **always try first** |
| **Programmatic check** | Code compiles, SQL runs, tool call is well-formed, output validates | Deterministic and cheap. Prefer over a judge. |
| **Deterministic metric** | Retrieval (recall@k), CV (IoU, mAP), classification (P/R/F1) | Use the real metric, not a judge |
| **LLM-as-judge** | Genuine qualitative judgment — is it faithful, helpful, grounded? | Last resort. It is a *model*, so it has error too. |
| **Human (HITL)** | High-stakes, or you're validating the judge itself | Expensive. Spend it where it counts. |

**Do not reach for a judge when a schema check would do.** That's the most common
waste in eval harnesses.

---

## STEP 3 — LLM-as-judge, done properly

The judge is a component under test too. Treat it as one.

**Rules:**
- **Rubric, not vibes.** Concrete criteria with named levels. "Rate 1–5" without
  anchors produces noise.
- **Binary or low-cardinality beats a 1–10 scale.** Models are far more reliable
  at "is this grounded in the source: yes/no" than at "7 vs 8."
- **Ask for the reason before the score.** Reasoning-then-verdict is more
  reliable than verdict-then-justification.
- **Pairwise > absolute** when comparing two prompt/model versions — "which is
  better, A or B" is an easier judgment than scoring each alone.
- **Control position bias** — randomize A/B order; judges favor the first (or
  last) slot.
- **A different model than the one under test**, where feasible. Self-judging
  inflates.

**Validate the judge against humans — this is the step people skip.** Score
〈30–50〉 cases by hand, compare to the judge, measure agreement (κ or raw). If the
judge doesn't agree with you, it isn't measuring the thing you care about, and
every number downstream is decoration. Re-validate whenever the rubric changes.

---

## STEP 4 — Human-in-the-loop gates

Decide *deliberately* where a human sits in the loop, and write it down:

| Gate | Where | Blocking? |
|---|---|---|
| **Pre-deploy** | Judge-vs-human agreement on the golden set | Yes — blocks release |
| **Pre-action** | Before an irreversible/expensive agent action (write, send, spend, delete) | Yes |
| **Sampled review** | 〈N%〉 of production traffic, reviewed async | No — feeds the golden set |
| **Escalation** | Low model confidence, or a guardrail fires | Yes, for that request |

**Design rule:** a human gate belongs anywhere the action is **irreversible** —
same penalty-for-being-wrong filter as the design doc. Reversible action, high
confidence → let it run. Irreversible → gate it.

**Every human decision at a gate is a free golden case.** Capture it. That's the
flywheel: the loop generates its own test set.

---

## STEP 5 — Evaluate the trajectory, not just the output

For agents/subagents, a right answer reached by a wrong path is a latent bug.
Score the **decision path**:

- Did it call the right tools, in a sane order?
- How many steps? (Silent step-count creep = cost creep.)
- Did it recover from a tool error, or loop?
- Did it stop, or run away?

Log the decision path as a first-class artifact — **tool calls, arguments, and
the reason for each** — not just final I/O. You cannot debug an agent from its
output alone. This is the observability requirement, applied to the model tier.

---

## STEP 6 — Wire it into CI

```bash
〈uv run python -m evals.run --suite smoke〉      # fast, every PR
〈uv run python -m evals.run --suite full〉       # nightly / pre-release
```

- **Smoke suite on every PR** — small, fast, catches obvious regressions.
- **Full suite nightly + pre-release.**
- **A regression blocks the merge.** Same rule as tests: no merge on red.
- **Commit scored results** (`evals/results/`) so the trend is visible over time —
  you want to *see* the slow degradation, not discover it.
- **Track cost and latency per run**, not just quality. A prompt that's 2% better
  and 3× the tokens is usually a bad trade — and you can only see that if you
  measure it.

---

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Scores swing between identical runs | Temperature > 0; no seed; tiny eval set | Pin temp/seed for evals; grow the set |
| Judge agrees with everything | Rubric too vague; leading prompt | Concrete anchors; binary criteria; ask for reason first |
| Evals pass, production fails | Golden set is synthetic | Reseed from real traffic and real incidents |
| "It feels better" but numbers flat | You're measuring the wrong thing | Fix the rubric to match what you actually care about |
| Slow quality decay, nobody noticed | No trend tracking | Commit results; chart over time |
| Eval bill is huge | Judge used where a schema check would do | Escalate scorers only as needed (Step 2) |

## Definition of done

- [ ] Deterministic logic pushed into code first (Step 0)
- [ ] Golden set frozen, versioned, seeded from **real** cases
- [ ] Cheapest sufficient scorer chosen; judge only where it's earned
- [ ] **Judge validated against human labels**; agreement measured
- [ ] HITL gates placed on the irreversible actions
- [ ] Trajectory/decision path logged and scored, not just output
- [ ] Smoke suite in CI and **blocking**; results committed for trend
- [ ] Cost + latency tracked per run
