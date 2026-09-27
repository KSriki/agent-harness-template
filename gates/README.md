# gates/ — deterministic enforcement (the layer prose can't provide)

> **Context guides; only things outside the model enforce.** Skills and steering
> docs shape behavior — but an agent can rationalize past any sentence. These gates
> run as shell commands and CI checks the model doesn't get a vote on.

## The three layers

| Layer | Lives | Enforces | Can be bypassed by |
|---|---|---|---|
| **1. Context** (steering §4.5, skills) | repo / `~/.claude` | process (red-before-green, the SDLC loop) | a rationalizing model |
| **2a. Guard** (`pre_tool_guard.py`) | `~/.claude/settings.json` → every project, **before** the tool runs | guardrails 3/4 as physics: no gate bypass, no destructive commands, a human on dep installs + gate-config edits | obfuscated shell (`$(printf …)`, `base64 \| sh`), a human |
| **2b. Hooks** (this dir) | `~/.claude/settings.json` → every project on the machine | outcomes at the agent layer: lint · **secrets** · typecheck · **tests · coverage** | local edits by a human (2a stops the agent doing it) |
| **3. CI + branch protection** | `.github/workflows/` + repo settings | the same gate, un-bypassably: **PRs do not merge on red** | nobody |

## How the hook layer works

```
Claude edits a file ──▶ PostToolUse hook ──▶ gate-dispatch.sh fast ──▶ .claude/gate.sh fast   (lint — instant feedback)
Claude tries to stop ─▶ Stop hook ────────▶ gate-dispatch.sh full ──▶ .claude/gate.sh full   (lint+types+TESTS+COVERAGE)
                                             │
                                             └─ no .claude/gate.sh in the project? → silent no-op (opt-in per project)
```

- **Global hook, per-project contract.** The hook is installed once per machine
  (`python3 init.py --install-hooks`) and fires in *every* project — but it only
  acts where the project has opted in by defining `.claude/gate.sh`. Different
  stacks, one convention.
- **No baked-in paths.** The hook command resolves the harness at fire time via
  the `~/.claude/skills` symlink (from `init.py --link-global`), so the same
  `settings.json` works on any machine — clone the harness anywhere, link once,
  done. No link (or no dispatch script) → silent no-op.
- **The Stop hook blocks "I'm done" on a red gate** (exit 2 feeds the failures back
  and the agent keeps working). Loop guard: if the gate is still red on the *second*
  stop attempt of a turn, it allows the stop with a loud warning instead of looping
  forever — the red output stays in the transcript either way.
- **Fast vs full:** edit-time checks must be cheap (lint), or the feedback loop
  becomes unbearable. The expensive proof — **tests + coverage threshold** — runs at
  turn end and in CI.

## The PreToolUse guard (`pre_tool_guard.py`)

Runs before every Bash / Edit / Write in **every** project (no opt-in — guardrails
are cross-project). Stdlib Python, <50ms, parses shell with `shlex` and recurses
into `bash -c` / `eval`.

| Decision | What | Why |
|---|---|---|
| **deny** | `--no-verify`, `commit -n`, any `core.hooksPath` redirect | skipping the hooks that ARE the gate is faking done |
| **deny** | force-push to `main`/`master`; `rm -r` of `/`, `~`, `$HOME`, `*`, `.`, `..` or the project root | irreversible; never an agent action |
| **ask** | new-package installs: `npm/pnpm/yarn/bun add\|i <pkg>`, `pip install <pkg>`, `uv add`, `poetry/cargo add`, `go get/install`, `gem/brew install`, `npx`/`uvx`/`dlx` | guardrail 3 — installing executes code before review. Lockfile restores (`npm ci`, bare `npm install`, `uv sync`, `pip install -r`) pass |
| **ask** | force-push to other branches, `git reset --hard`, `git clean -f`, remote ref delete, `rm -r` outside the project | destructive but sometimes legit — a human decides |
| **ask** | edits to an **existing** gate/lint/typecheck/test/CI config or dependency manifest (`.claude/gate.sh`, `.github/workflows/*`, `ruff.toml`, `tsconfig*.json`, eslint/prettier, `pyproject.toml`, `package.json`, `requirements*.txt`, …) | loosening the gate to pass is the cheapest fake-done; a manifest edit is the other door to guardrail 3. Creating a new config is allowed (scaffolding) |

**Fails open** on malformed input (a guard bug must not brick every session) and
logs to stderr. **Kill switch:** launch Claude Code with `HARNESS_GUARD=off` — an
inline `HARNESS_GUARD=off cmd` inside a Bash call does not reach the hook. This
is a seatbelt against honest mistakes and rationalization, not a sandbox against
an adversary — Layer 3 is still the wall.

## Secret scan (`secret_scan.py`)

`gate.sh fast` scans changed + untracked files; `full` (and CI) scans every tracked
file. High-confidence patterns only (private keys, AWS/GitHub/Anthropic/OpenAI/
Slack/Google/Stripe tokens, credentials in URLs) — a noisy scanner gets
allowlisted into uselessness. A real test fixture opts out per line with
`gate:allow-secret`. `setup-harness` vendors it to `.claude/secret_scan.py` so CI
(which has no harness clone) runs the same file. gitleaks is stronger; adopting it
is a dependency decision (guardrail 3).

## Files

- `pre_tool_guard.py` — the global PreToolUse guard (above). Tests: `gates/tests/`.
- `secret_scan.py` — the gate's secret check (above); copy to `<project>/.claude/`.
- `gate-dispatch.sh` — the global hook target. Reads the hook JSON, delegates to the
  project's `.claude/gate.sh`. No project file → exits 0 silently.
- `gate.sh.template` — copy to `<project>/.claude/gate.sh`, fill the 〈slots〉, `chmod +x`.
  **This one file is the single source of truth for "done"** — hooks and CI both run it.
- `settings-hooks.json` — the snippet `init.py --install-hooks` merges into
  `~/.claude/settings.json` (kept here as reviewable documentation).
- `github-actions-gate.yml` — Layer 3 template. Copy to
  `<project>/.github/workflows/gate.yml`, fill the setup slot. Then enable **branch
  protection** requiring the `gate` check — that's the step that makes red-means-no-merge physics.
- `global-CLAUDE.md` — optional tiny machine-wide baseline (`init.py --global-claude`),
  for sessions in projects that don't carry the harness context yet.

## Honest limits

Hooks verify **outcomes** (tests exist and pass, coverage holds), not **process**
(that the test was written before the code) — process lives in Layer 1 and in the
`implementer`'s mandatory `tdd` rule. And local layers can always be edited by a
human with the keyboard; **Layer 3 + branch protection is the only layer nothing
talks its way past.** Install all three.
