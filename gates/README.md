# gates/ — deterministic enforcement (the layer prose can't provide)

> **Context guides; only things outside the model enforce.** Skills and steering
> docs shape behavior — but an agent can rationalize past any sentence. These gates
> run as shell commands and CI checks the model doesn't get a vote on.

## The three layers

| Layer | Lives | Enforces | Can be bypassed by |
|---|---|---|---|
| **1. Context** (steering §4.5, skills) | repo / `~/.claude` | process (red-before-green, the SDLC loop) | a rationalizing model |
| **2. Hooks** (this dir) | `~/.claude/settings.json` → every project on the machine | outcomes at the agent layer: lint · typecheck · **tests · coverage** | `--no-verify`-style local edits, a human |
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
- **The Stop hook blocks "I'm done" on a red gate** (exit 2 feeds the failures back
  and the agent keeps working). Loop guard: if the gate is still red on the *second*
  stop attempt of a turn, it allows the stop with a loud warning instead of looping
  forever — the red output stays in the transcript either way.
- **Fast vs full:** edit-time checks must be cheap (lint), or the feedback loop
  becomes unbearable. The expensive proof — **tests + coverage threshold** — runs at
  turn end and in CI.

## Files

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
