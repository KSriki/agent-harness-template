# Evals

The test suite for non-deterministic components. See `skills/eval-harness/SKILL.md`
for the full procedure.

```
golden/    # Frozen, versioned cases. Seed from REAL inputs and REAL failures.
           #   {input, expected|rubric, tags}  →  <golden/*.jsonl>
judges/    # Judge prompts + rubrics. Validate against human labels before trusting.
runners/   # Execution + scoring.
results/   # Scored runs, timestamped. COMMIT THESE — the trend is the point.
run.py     # <uv run python -m evals.run --suite smoke|full>
```

**Rules that make this work:**
- Golden set is **frozen and versioned** — if it moves, regressions are meaningless.
- Every production bug becomes a golden case. That's how coverage is earned.
- Cheapest sufficient scorer: schema check > programmatic > metric > LLM judge > human.
- **Validate the judge against humans** (~30–50 hand-scored cases) or every number
  downstream is decoration.
- Smoke suite runs on **every PR and blocks the merge**. Same rule as tests.
- Track **cost and latency**, not just quality. +2% quality for 3× tokens is a bad trade.
- **Agent evals: N trials + a declared noise floor.** pass@k for capability
  ("can it ever?"), **pass^k for regression** ("does it, reliably?" — 75%
  per-trial ≈ 42% over 3 trials). A delta inside the noise floor (~3pp until
  you've measured your own) is NOT a regression and must not flip the gate.
- **Framework stance (recorded 2026-08-20): hand-rolled first.** Stdlib runner +
  jsonl until it demonstrably fails. Eval frameworks are a guardrail-3
  dependency decision, and the hosted platforms (Braintrust, LangSmith,
  Langfuse, Arize) additionally ship prompts + tool arguments off-machine —
  a guardrail-2 decision, not a tooling one.
