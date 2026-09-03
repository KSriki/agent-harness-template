# Evals

The test suite for non-deterministic components. See `skills/eval-harness/SKILL.md`
for the full procedure, and **`docs/evals.md` for the full human-facing manual**
(architecture, gate semantics, metrics, extension points).

```
golden/    # Frozen, versioned, APPEND-ONLY cases. Seed from REAL inputs/failures.
           #   {id, input, expected, tags}  →  golden/*.jsonl
prompts/   # Prompt templates per suite ({input} placeholder). Prompts are code.
runners/   # Execution + scoring (loader, scorers, metrics, the model seam).
results/   # Scored runs, timestamped. COMMIT THESE — the trend is the point.
config.json  # suites (golden file, scorer, case cap, pass floor), trials,
             # noise floor, model, cost-rate table
run.py     # python3 -m evals.run --suite smoke|full [--trials N] [--dry-run]
```

**Runner facts (hand-rolled, stdlib-only — portable to other projects):**
- Scorers implemented: `exact`, `regex` (whole-output match). Judge scoring is a
  named extension point in `runners/scorers.py` — deliberately not built yet.
- The ONLY model touchpoint is `runners/model.py::call_model` (shells out to
  `claude -p`). Tests mock this seam; they never call the real CLI.
- Missing/unauthenticated CLI → LOUD "EVALS SKIPPED … this is not a pass" and
  exit 0. Never silent, never fake-green, never red for absence of the tool.
- Gate: exit 1 when per-trial accuracy < the suite's `pass_floor`, unless the
  delta vs the last committed result is within `noise_floor_pp`.
- Costs in results are ESTIMATES (tokens ~= chars/4 x config rate table).
- Tests live in `evals/tests/` (stdlib unittest, pytest-discoverable).

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
