#!/usr/bin/env bash
#
# install.sh — plug-and-play: drop the agent harness into a project.
#
#   bash install.sh <target-dir> [--force]
#
# Copies the reusable agent layer into <target-dir> and wires .claude/ so Claude
# Code natively discovers the skills + subagents. It deliberately does NOT fill in
# your project context — that's `python3 init.py` (or by hand), and it's exactly
# what the SDLC skills (write-design-doc, new-service, …) are for. Install the
# suite; set up the project as a separate, deliberate step.
#
# Safe by design:
#   * never overwrites an existing AGENTS.md / CLAUDE.md without --force
#     (protects context you've already filled in)
#   * additive only — refreshes the suite's files, never deletes yours
#   * does nothing destructive: it adds files and symlinks, that's all
#
# macOS / Linux. (Windows: use GitHub "Use this template" or copy-in — see SETUP.md §0.)

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET=""
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -*)      echo "unknown flag: $arg" >&2; exit 2 ;;
    *)       TARGET="$arg" ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "usage: bash install.sh <target-dir> [--force]" >&2
  exit 1
fi

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

if [ "$SRC" = "$TARGET" ]; then
  echo "refusing to install the harness into itself" >&2
  exit 1
fi

echo "Installing agent harness → $TARGET"

# --- reusable suite: refreshed (additive; your own files are left alone) ------
copy_tree() {  # $1 = dir name under SRC
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' \
          --exclude='*.bak' --exclude='.venv' "$SRC/$1/" "$TARGET/$1/"
  else
    mkdir -p "$TARGET/$1" && cp -R "$SRC/$1/." "$TARGET/$1/"
  fi
}
for d in skills agents docs evals gates; do
  [ -d "$SRC/$d" ] && copy_tree "$d" && echo "  ✓ $d/"
done

# tooling + harness docs (single files, safe to refresh)
for f in init.py SETUP.md ARCHITECTURE.md HARNESS.md; do
  [ -f "$SRC/$f" ] && cp "$SRC/$f" "$TARGET/$f" && echo "  ✓ $f"
done

# --- context files: PROTECTED (don't clobber one you've filled in) ------------
for f in AGENTS.md CLAUDE.md; do
  if [ -f "$TARGET/$f" ] && [ "$FORCE" -ne 1 ]; then
    echo "  · $f exists — kept yours (use --force to overwrite)"
  else
    cp "$SRC/$f" "$TARGET/$f" && echo "  ✓ $f"
  fi
done

# --- wire .claude/ for Claude Code native discovery ---------------------------
mkdir -p "$TARGET/.claude"
ln -sfn ../skills "$TARGET/.claude/skills"
ln -sfn ../agents "$TARGET/.claude/agents"
echo "  ✓ .claude/skills → ../skills, .claude/agents → ../agents"

# --- .gitignore: append our one line if it isn't already there ----------------
GI="$TARGET/.gitignore"
if [ ! -f "$GI" ] || ! grep -q '\.claude/settings\.local\.json' "$GI" 2>/dev/null; then
  {
    echo ""
    echo "# Claude Code — local settings only; .claude/skills & .claude/agents are committed symlinks"
    echo ".claude/settings.local.json"
  } >> "$GI"
  echo "  ✓ .gitignore (+ .claude/settings.local.json)"
fi

cat <<EOF

Done — the suite is installed. Now set up THIS project (your step):

  cd "$TARGET"
  python3 init.py          # fill AGENTS.md: commands, stack, gotchas for this repo

Then verify it's live in Claude Code (a fresh session in this dir):
  • "Add the leftpad package to fix this."  → must REFUSE  (proves guardrails load)
  • "What skills and subagents do you have?" → should list the suite

From here, use the skills in real time — e.g. write-design-doc to spec a change,
new-service for the rung check, orchestrate-agents to fan out. See SETUP.md.
EOF
