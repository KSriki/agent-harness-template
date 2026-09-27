#!/usr/bin/env bash
# .claude/gate.sh — the harness repo's own quality gate (the repo that ships the
# gate mechanism is gated by it). Machine-wide hooks run this: fast on edits,
# full on turn end. CI should run `full` on every PR (gates/github-actions-gate.yml).
# `evals` runs the LIVE model suites (all of them) — manual/baseline/pre-release,
# NOT the turn-end path: with an authed claude CLI they cost minutes of wall
# time per run and would bust the Stop hook's timeout every turn (ticket yxr).
set -euo pipefail
MODE="${1:-full}"

# ── FAST — after every edit. Cheap only. ─────────────────────────────────────
ruff check .
python3 gates/secret_scan.py
python3 -m harness_lint .    # skills/agents/indexes wired correctly (stdlib, <1s)

[ "$MODE" = "fast" ] && exit 0

# Resolve a python that actually has pytest — hook environments (Stop/PostToolUse)
# can carry a minimal PATH where bare python3 is the CommandLineTools build.
PY=""
for c in python3 "$HOME/.pyenv/shims/python3.12" "$HOME/.pyenv/shims/python3" python3.12; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import pytest" >/dev/null 2>&1; then
        PY="$c"; break
    fi
done
[ -n "$PY" ] || { echo "GATE: no python with pytest found on PATH" >&2; exit 1; }

# ── FULL — turn end + CI. The whole deterministic proof. ─────────────────────
ruff format --check .
python3 gates/secret_scan.py --all
"$PY" -m pytest orchestrator_engine/tests evals/tests harness_lint/tests gates/tests -q \
    --cov=orchestrator_engine --cov=evals --cov=harness_lint --cov=gates \
    --cov-fail-under=80 --cov-report=term:skip-covered

[ "$MODE" = "full" ] && exit 0

# ── EVALS — live model suites. Run deliberately (`gate.sh evals`), never from
# the turn-end hook: each case is a real `claude -p` call (~30-60s). Loud-skips
# (exit 0) where the CLI is absent/unauthed; below-floor is red, same as tests.
"$PY" -m evals.run --suite smoke
"$PY" -m evals.run --suite premise-verdict
"$PY" -m evals.run --suite source-provenance

# TODO(needs-approval): mypy is not installed; adding it is a dependency
# decision (guardrail 3) — propose before installing.
