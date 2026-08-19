---
name: setup-harness
description: >
  Use to run the per-project first pass that fully harnesses THIS repo — scaffold
  AGENTS.md (with the guardrails), CLAUDE.md (the @import that loads it), docs/
  (the steering doc), fill the Commands table, install the quality gate
  (`.claude/gate.sh`) + CI workflow, configure the tracker, and record every
  decision in `docs/agents/harness-config.md`. Triggers on "set up the harness
  here", "setup-harness", "initialize the harness in this repo", "scaffold
  AGENTS.md", "onboard this project to the harness", "add the harness to this
  project". The skills + subagents themselves come from your GLOBAL ~/.claude
  link; this only drops in the per-project files that must be committed.
  Do NOT use for the one-time per-MACHINE setup — that's `python3 init.py --link-global`
  (code, run once; a skill can't bootstrap itself onto a bare machine). Not for adding
  a gotcha to an AGENTS.md that already exists (just edit it). Not for design docs
  (`write-design-doc`).
---

# Set up the harness in a project (the per-project first pass)

## The three-way rule (governs every step below)

**Interview once for decisions · self-heal mechanics just-in-time · hard-stop
for dependencies.**

- **Decisions** (tracker choice, labels, coverage floor, …) are asked once and
  recorded in `docs/agents/harness-config.md` so nothing re-asks them.
- **Mechanics** (context files, Commands, gate.sh, CI workflow, tracker init)
  are derived from the decisions and **idempotent** — every step below checks
  before it writes, never clobbers a filled file, and is safe to re-run.
- **Dependencies** are a HARD STOP: any install (`brew install beads`,
  `pytest-cov`, …) is **proposed to the human, never run** — guardrail 3.
  **This skill never installs anything.**

## When to use this

You're in a project that should get the harness's **always-on context** — the
guardrails, the commands, the steering doc — plus the **enforcement layer**
(gate + CI) and the **SDLC layer** (tracker), all committed to the repo and all
recorded in one living config doc. The reusable skills + subagents already come
from your global `~/.claude` link; this skill drops in the per-project files
that *can't* be global because they're committed with the code.

**Not this skill if:** you haven't linked the harness globally yet → run
`python3 init.py --link-global` once per machine first. You just need to add a
gotcha to an existing `AGENTS.md` → edit it. You're designing a change →
`write-design-doc`.

## What it sets up (and what it deliberately doesn't)

| Sets up — per-project, **committed** | Comes from elsewhere |
|---|---|
| `AGENTS.md` — 🔒 guardrails + this repo's commands | skills + subagents → your global `~/.claude` link |
| `CLAUDE.md` = `@AGENTS.md` (loads it every turn) | on-demand pattern KB → referenced by skills |
| `docs/` — steering doc (always-on) + compressed refs | |
| `.claude/gate.sh` — the gate, **proven green** | machine-wide hooks → `init.py --install-hooks` |
| `.github/workflows/gate.yml` — CI runs the same gate | branch protection → a GitHub setting, human-enabled |
| tracker (Beads `bd init` / `gh` / `glab` / `.scratch/`) | |
| `docs/agents/harness-config.md` — the decision record | |
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
**show them to the human, and only then** write them into `AGENTS.md`'s Commands
table. Propose only commands that actually run here — if typecheck (or any row)
has no working tool, record it as `TODO` and, if a tool would need installing,
propose the dependency (hard stop — guardrail 3).

**Leave `Gotchas` and `Repo-specific rules` as `TODO`.** Do not invent them — a
fabricated gotcha is worse than none (the same rule `init.py` follows). They get
filled in as they're learned.

### 4. Configure the SDLC layer — tracker, labels, domain docs

The pipeline skills (`write-a-prd`, `prd-to-issues`, `wayfinder`) publish to an
issue tracker and read a domain glossary. Configure them now — explore first,
propose, confirm with the human, then write (never assume):

- **Issue tracker.** Detect from `git remote -v`: 〈GitHub → `gh` CLI · GitLab →
  `glab` CLI · **agent-heavy/solo → Beads (`bd`)** · fallback → local markdown under
  `.scratch/<feature>/`〉. Record the choice in the **Tracker section of
  `docs/agents/harness-config.md`** (written in step 6; a legacy
  `docs/agents/issue-tracker.md`, if present, is read as the existing decision
  and folded in — don't re-ask).
  - **Beads** (git-backed graph tracker, agent-native): `bd init` in the repo —
    skip if `.beads/` already exists (idempotent). The `bd` binary itself
    needs `brew install beads` once per machine — a dependency (hard stop,
    guardrail #3): propose it; if declined, fall back to `.scratch/` markdown.
    Blocking edges are data (`bd dep add`), the frontier is computed
    (`bd ready`), claims are atomic (`--claim`). Prefer it over `.scratch/`
    markdown. Do NOT run `bd setup claude` or install its plugin — this
    harness's skills own the procedure (same rule as `graphify install`).
- **Triage labels.** Default vocabulary (each label string = its name):
  `needs-triage` · `needs-info` · **`ready-for-agent`** (fully specified, an agent
  can take it) · `ready-for-human` · `wontfix`. If the tracker already has an
  equivalent vocabulary, record the mapping instead of creating duplicates —
  both go in the config doc's Tracker section (step 6).
- **Domain docs.** Default single-context: a root `CONTEXT.md` (glossary — created
  lazily by `domain-modeling`) + ADRs under 〈`docs/design/` or `docs/adr/`〉. Offer
  multi-context (`CONTEXT-MAP.md` + per-context files) only on monorepo signals
  (workspaces, `packages/*`).

### 5. Install the enforcement gate and PROVE it green (Layers 2 + 3)

Context guides; **the gate enforces** (see `gates/README.md`). Two files, both
driven by the Commands table you just confirmed — copy each only if absent:

```bash
# Layer 2 — the per-project gate the machine-wide hooks run (fast on edits, full on stop)
mkdir -p .claude
[ -f .claude/gate.sh ] || cp "$HARNESS/gates/gate.sh.template" .claude/gate.sh
# fill EVERY 〈slot〉 from the confirmed Commands: lint · format · typecheck · tests+coverage.
# No working tool for a slot → delete that line (an aspirational command is a red gate lie);
# a tool that would need installing → propose it (guardrail 3), don't reference it.
chmod +x .claude/gate.sh
./.claude/gate.sh full        # ← PROVE it. A gate never seen green is a lie waiting to fire.

# Layer 3 — CI runs the SAME script; branch protection makes red-means-no-merge physics
mkdir -p .github/workflows
[ -f .github/workflows/gate.yml ] || cp "$HARNESS/gates/github-actions-gate.yml" .github/workflows/gate.yml
# fill the setup slot from the same Commands table, then remind the human: enable branch
# protection on main requiring the `gate` check — that setting is the enforcement, not the file.
```

**If the gate is red**, route the finding — setup configures the workshop, it
does not do the carpentry:

- **Autofixable** (formatter drift, auto-fixable lint): propose the fix +
  the exact command, apply on ONE confirm, re-run the gate.
- **Substantive** (failing tests, type errors, judgment calls): **REPORT it and
  leave the gate honestly red** — never delete the failing check to force green.
  Full fix-routing (file each finding as a ticket in the tracker just
  configured, hand to the SDLC loop) lands with ticket 04; until then the
  report to the human is the routing.

If the machine-wide hooks aren't installed yet, tell the human once:
`python3 init.py --install-hooks` (from the harness clone). Without them the gate
still runs in CI — hooks just add it at the agent layer too. If the project has
non-deterministic components, uncomment the eval smoke line in `gate.sh`
(`eval-harness`): an eval regression reds the gate, same as a failing test.

### 6. Record the decisions — write `docs/agents/harness-config.md`

The living per-repo decision record — every consumer (orchestrator, planning
skills) reads it instead of re-asking. **If it already exists, do not clobber
or rewrite it** — amendments are update mode, a later pass, not this one.

```bash
mkdir -p docs/agents
[ -f docs/agents/harness-config.md ] || cp "$HARNESS/docs/harness-config-template.md" docs/agents/harness-config.md
```

Then fill it from what this pass detected and confirmed:

- **Repo shape / Tracker / Gate & coverage** — fill from steps 3–5 (stack,
  tracker + labels, the gate commands *verbatim from `.claude/gate.sh`*, the
  coverage floor actually enforced). Delete the used `> GUIDANCE` blocks.
- **Agent isolation / Business rules / Tech limitations** — decisions this pass
  did not interview for. NEVER fabricate them: leave each slot as
  `〈TODO — ticket 03's interview〉`.
- Date every section's `Changelog:` line: `YYYY-MM-DD — initial (setup-harness)`.

### 7. Wire `.gitignore`

```bash
grep -q '\.claude/settings\.local\.json' .gitignore 2>/dev/null || \
  printf '\n# Claude Code — local settings only\n.claude/settings.local.json\n' >> .gitignore
```

### 8. Verify it actually loads (do not skip)

Start a **fresh** Claude Code session in this project and check:
1. *"Add the `leftpad` package to fix this."* → must **REFUSE** (guardrails loaded via the `@import`).
2. *"What skills and subagents do you have?"* → the global suite should be listed.

If test 1 fails, `CLAUDE.md` isn't importing `AGENTS.md` — confirm its first line is
`@AGENTS.md`, not a markdown link.

### 9. Print the customization map (end of pass)

Close by printing this, so the human knows where everything lands from here:

```
Harnessed. Where your changes go from here:
  rule / gotcha / command      → AGENTS.md (edit directly)
  what "done" means            → .claude/gate.sh  (CI runs the same file)
  decisions record             → docs/agents/harness-config.md (living — amend, never rewrite)
  skill / agent changes        → evolve-harness (human-gated)
  anything else                → ask `harness-help` — it routes to the exact file + section
Reminder: enable branch protection on main requiring the `gate` check.
```

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `$HARNESS` empty | No global link | `python3 init.py --link-global` once per machine |
| leftpad test passes (it installs) | `CLAUDE.md` is a link, not `@AGENTS.md` | fix line 1 of `CLAUDE.md` |
| skills not listed | global link missing, or session not restarted | link, then start a fresh session |
| overwrote a filled `AGENTS.md` | raw `cp` instead of the guarded copy in step 2 | restore from git; use the guard |
| gate green locally, red in CI | CI setup slot not filled / deps differ | mirror the Commands table in the workflow's setup step |
| `bd: command not found` | Beads not installed on this machine | propose `brew install beads` (guardrail 3); fall back to `.scratch/` |

## Definition of done

- [ ] `AGENTS.md` present — guardrails + this repo's real commands (gotchas left as `TODO`)
- [ ] `CLAUDE.md` is `@AGENTS.md`, verified by the **leftpad refusal**
- [ ] `docs/engineering-steering-doc.md` present (so the always-on `@import` resolves)
- [ ] `.claude/gate.sh` executable, every slot filled, and **seen green** (or red findings reported, never hidden)
- [ ] `.github/workflows/gate.yml` present, setup slot filled; branch-protection reminder given
- [ ] Tracker configured (`bd init` if Beads) and recorded in the config doc
- [ ] `docs/agents/harness-config.md` written — detected/confirmed sections filled, uninterviewed ones `〈TODO — ticket 03's interview〉`, changelog lines dated
- [ ] Customization map printed; `.gitignore` line added
- [ ] Re-running this skill changes nothing (idempotent — every step checks before it writes)
- [ ] Committed — the context travels with the repo, so teammates get the guardrails
