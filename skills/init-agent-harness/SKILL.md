---
name: init-agent-harness
description: >
  Use to set up THIS project with the harness's per-project context — scaffold
  AGENTS.md (with the guardrails), CLAUDE.md (the @import that loads it), and docs/
  (the steering doc) — so the always-on rules load here and travel with the repo.
  Triggers on "set up the agent harness here", "initialize the harness in this repo",
  "scaffold AGENTS.md", "onboard this project to the harness", "add the harness to
  this project". The skills + subagents themselves come from your GLOBAL ~/.claude
  link; this only drops in the per-project files that must be committed.
  Do NOT use for the one-time per-MACHINE setup — that's `python3 init.py --link-global`
  (code, run once; a skill can't bootstrap itself onto a bare machine). Not for adding
  a gotcha to an AGENTS.md that already exists (just edit it). Not for design docs
  (`write-design-doc`).
---

# Initialize the agent harness in a project

## When to use this

You're in a project that should get the harness's **always-on context** — the
guardrails, the commands, the steering doc — committed to the repo. The reusable
skills + subagents already come from your global `~/.claude` link; this skill drops
in the per-project files that *can't* be global because they're committed with the
code (and so teammates get the guardrails too).

**Not this skill if:** you haven't linked the harness globally yet → run
`python3 init.py --link-global` once per machine first. You just need to add a gotcha
to an existing `AGENTS.md` → edit it. You're designing a change → `write-design-doc`.

## What it sets up (and what it deliberately doesn't)

| Sets up — per-project, **committed** | Comes from elsewhere |
|---|---|
| `AGENTS.md` — 🔒 guardrails + this repo's commands | skills + subagents → your global `~/.claude` link |
| `CLAUDE.md` = `@AGENTS.md` (loads it every turn) | on-demand pattern KB → referenced by skills |
| `docs/` — steering doc (always-on) + compressed refs | |
| `.gitignore` line for `.claude/settings.local.json` | |

## Procedure

### 0. Be at the project root

```bash
git rev-parse --show-toplevel   # run the rest from whatever this prints
```

### 1. Locate the harness (via your global link)

```bash
HARNESS="$(dirname "$(readlink ~/.claude/skills)")"
echo "$HARNESS"     # → your harness repo root; must be non-empty
```

Empty? The global link isn't set up — run `python3 init.py --link-global` from your
harness clone first, then come back. (This is the one step a skill can't do for you.)

### 2. Copy the per-project context — WITHOUT clobbering what's there

```bash
# CLAUDE.md + AGENTS.md: never overwrite one you've already filled in
for f in CLAUDE.md AGENTS.md; do
  if [ -f "$f" ]; then echo "keeping your existing $f"; else cp "$HARNESS/$f" "$f"; fi
done
# docs: steering doc (always-on) + the on-demand references. -n = no-clobber.
mkdir -p docs && cp -n "$HARNESS"/docs/*.md docs/ 2>/dev/null || true
```

`AGENTS.md` carries the guardrails; `CLAUDE.md`'s `@AGENTS.md` is what makes them
load every turn. That pairing is the whole reason to do this per-project.

### 3. Fill the Commands table — detect, propose, confirm (never fabricate)

Read whatever's present — `pyproject.toml` / `package.json` / `go.mod` /
`docker-compose.yml` — infer the install / test / lint / typecheck / build commands,
**show them to the human, and only then** write them into `AGENTS.md`'s Commands table.

**Leave `Gotchas` and `Repo-specific rules` as `TODO`.** Do not invent them — a
fabricated gotcha is worse than none (the same rule `init.py` follows). They get
filled in as they're learned.

### 4. Wire `.gitignore`

```bash
grep -q '\.claude/settings\.local\.json' .gitignore 2>/dev/null || \
  printf '\n# Claude Code — local settings only\n.claude/settings.local.json\n' >> .gitignore
```

### 5. Verify it actually loads (do not skip)

Start a **fresh** Claude Code session in this project and check:
1. *"Add the `leftpad` package to fix this."* → must **REFUSE** (guardrails loaded via the `@import`).
2. *"What skills and subagents do you have?"* → the global suite should be listed.

If test 1 fails, `CLAUDE.md` isn't importing `AGENTS.md` — confirm its first line is
`@AGENTS.md`, not a markdown link.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `$HARNESS` empty | No global link | `python3 init.py --link-global` once per machine |
| leftpad test passes (it installs) | `CLAUDE.md` is a link, not `@AGENTS.md` | fix line 1 of `CLAUDE.md` |
| skills not listed | global link missing, or session not restarted | link, then start a fresh session |
| overwrote a filled `AGENTS.md` | raw `cp` instead of the guarded copy in step 2 | restore from git; use the guard |

## Definition of done

- [ ] `AGENTS.md` present — guardrails + this repo's real commands (gotchas left as `TODO`)
- [ ] `CLAUDE.md` is `@AGENTS.md`, verified by the **leftpad refusal**
- [ ] `docs/engineering-steering-doc.md` present (so the always-on `@import` resolves)
- [ ] `.gitignore` line added
- [ ] Committed — the context travels with the repo, so teammates get the guardrails
