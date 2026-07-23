#!/usr/bin/env bash
# gate-dispatch.sh — global Claude Code hook target (installed once per machine).
# Delegates to the current project's .claude/gate.sh; silent no-op where absent.
#
#   gate-dispatch.sh fast   ← PostToolUse (Edit|Write): cheap checks, instant feedback
#   gate-dispatch.sh full   ← Stop: the whole gate — lint, typecheck, TESTS, COVERAGE
#
# Exit codes (Claude Code hook contract):
#   0 = pass/no-op · 2 = block + feed stderr back to the model
set -uo pipefail

MODE="${1:-full}"
INPUT="$(cat 2>/dev/null || true)"

json_field() {  # $1 = key; stdlib python only, no jq dependency
  printf '%s' "$INPUT" | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('$1',''))
except Exception: print('')" 2>/dev/null
}

CWD="$(json_field cwd)"
[ -z "$CWD" ] && CWD="$PWD"
GATE="$CWD/.claude/gate.sh"

# Opt-in per project: no gate script (or not executable) → nothing to enforce here.
[ -x "$GATE" ] || exit 0

OUT="$(cd "$CWD" && "$GATE" "$MODE" 2>&1)"
RC=$?
[ $RC -eq 0 ] && exit 0

if [ "$MODE" = "fast" ]; then
  { echo "FAST CHECKS FAILED (.claude/gate.sh fast) — fix before continuing:"
    echo "$OUT" | tail -20; } >&2
  exit 2
fi

# full mode (Stop hook): block the first "I'm done" on red; on the second attempt
# of the same turn (stop_hook_active), allow the stop with a loud warning instead
# of looping forever. The red output lands in the transcript either way.
ACTIVE="$(json_field stop_hook_active)"
if [ "$ACTIVE" = "True" ] || [ "$ACTIVE" = "true" ]; then
  { echo "GATE STILL RED after retry — allowing stop, but this is NOT done."
    echo "Do not merge. Failures:"
    echo "$OUT" | tail -30; } >&2
  exit 0
fi

{ echo "GATE FAILED (.claude/gate.sh full) — the turn is not done until this is green."
  echo "Fix these, re-run the gate, then finish:"
  echo "$OUT" | tail -40; } >&2
exit 2
