#!/usr/bin/env bash
# .claude/gate.sh — the harness repo's own quality gate (the repo that ships the
# gate mechanism is gated by it). Machine-wide hooks run this: fast on edits,
# full on turn end. CI should run `full` on every PR (gates/github-actions-gate.yml).
set -euo pipefail
MODE="${1:-full}"

# ── FAST — after every edit. Cheap only. ─────────────────────────────────────
ruff check .

[ "$MODE" = "fast" ] && exit 0

# ── FULL — turn end + CI. The whole proof. ───────────────────────────────────
ruff format --check .
python3 -m pytest orchestrator_engine/tests evals/tests -q \
    --cov=orchestrator_engine --cov=evals --cov-fail-under=80 --cov-report=term:skip-covered

# Eval smoke — the classifier golden set. Loud-skips (exit 0) where the claude
# CLI is absent/unauthed; a real run below the floor is a red gate, same as tests.
python3 -m evals.run --suite smoke

# Premise-gate evals — verdict discipline + source-provenance tiering for the
# premise-reviewer (ticket 63j/fu1). Same loud-skip / red-below-floor semantics.
python3 -m evals.run --suite premise-verdict
python3 -m evals.run --suite source-provenance

# TODO(needs-approval): mypy is not installed; adding it is a dependency
# decision (guardrail 3) — propose before installing.
