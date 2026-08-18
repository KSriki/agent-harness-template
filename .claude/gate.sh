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
# Floor is honest reality (cli.py is untested — ticketed); raise to 80 when closed.
python3 -m pytest orchestrator_engine/tests -q \
    --cov=orchestrator_engine --cov-fail-under=65 --cov-report=term:skip-covered

# TODO(needs-approval): mypy is not installed; adding it is a dependency
# decision (guardrail 3) — propose before installing.
