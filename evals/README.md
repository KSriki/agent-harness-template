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
