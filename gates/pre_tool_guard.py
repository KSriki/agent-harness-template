#!/usr/bin/env python3
"""pre_tool_guard.py — global PreToolUse hook: guardrails 3/4 as physics, not prose.

    Bash            → deny destructive / gate-bypassing commands; ASK on dependency installs
    Edit|Write|...  → ASK before modifying an EXISTING gate/lint/typecheck/CI/dep-manifest file

Stdlib only. Reads the hook JSON on stdin; answers with the PreToolUse
`permissionDecision` contract (deny = refused + reason fed to the model;
ask = the human is prompted). Anything unrecognized → allow (exit 0, no output).

Honest limits: this parses shell with shlex, not a real shell. It catches the
honest-mistake and rationalization cases (`--no-verify` to get past a red gate,
`pip install` to make an import work), not a determined adversary — obfuscated
commands (`$(printf ...)`, base64 | sh) get through. Layer 3 (CI + branch
protection) is still the wall. Kill switch: HARNESS_GUARD=off in the environment
Claude Code was launched with (a command's own inline env does not reach the hook).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

SEPARATORS = {";", "&&", "||", "|", "&", "|&", "(", ")"}
WRAPPERS = {"sudo", "env", "command", "exec", "time", "nohup", "nice", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash"}
PROTECTED_BRANCHES = {"main", "master"}

# Tool config that decides whether the gate is green. Loosening one to pass is
# the cheapest way to fake "done" — so an EXISTING one needs a human.
PROTECTED_CONFIG = [
    r"(^|/)\.claude/gate\.sh$",
    r"(^|/)\.claude/settings(\.local)?\.json$",
    r"(^|/)\.github/workflows/[^/]+\.ya?ml$",
    r"(^|/)(ruff|\.ruff)\.toml$",
    r"(^|/)(setup\.cfg|\.flake8|mypy\.ini|\.mypy\.ini|pytest\.ini|\.coveragerc|tox\.ini)$",
    r"(^|/)\.golangci\.ya?ml$",
    r"(^|/)(\.eslintrc(\.\w+)?|eslint\.config\.\w+|\.prettierrc(\.\w+)?|prettier\.config\.\w+)$",
    r"(^|/)tsconfig(\.[\w-]+)?\.json$",
    r"(^|/)(jest|vitest)\.config\.\w+$",
    r"(^|/)\.pre-commit-config\.ya?ml$",
    # Dependency manifests: the other door to guardrail 3 (edit manifest → sync).
    r"(^|/)(pyproject\.toml|package\.json|go\.mod|Cargo\.toml|Gemfile)$",
    r"(^|/)requirements[\w.-]*\.txt$",
]


def deny(reason: str) -> dict:
    return _decision("deny", reason)


def ask(reason: str) -> dict:
    return _decision("ask", reason)


def _decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": f"[harness guard] {reason}",
        }
    }


# ── Bash ──────────────────────────────────────────────────────────────────────


def split_commands(command: str) -> list[list[str]]:
    """Command string → list of argv lists, split on ; && || | & and newlines."""
    out: list[list[str]] = []
    for line in command.splitlines() or [command]:
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        try:
            tokens = list(lex)
        except ValueError:  # unbalanced quotes → best effort on whitespace
            tokens = line.split()
        argv: list[str] = []
        for tok in tokens:
            if tok in SEPARATORS:
                if argv:
                    out.append(argv)
                argv = []
            else:
                argv.append(tok)
        if argv:
            out.append(argv)
    return out


def strip_wrappers(argv: list[str]) -> list[str]:
    """Drop leading VAR=val assignments and sudo/env/time-style wrappers."""
    i = 0
    while i < len(argv):
        tok = argv[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok) or tok in WRAPPERS:
            i += 1
        elif tok.startswith("-") and i > 0 and argv[i - 1] in WRAPPERS:
            i += 1  # wrapper's own flags, e.g. `sudo -u x`, `nice -n 5`
        else:
            break
    return argv[i:]


def check_bash(command: str, cwd: str) -> dict | None:
    for raw in split_commands(command):
        argv = strip_wrappers(raw)
        if not argv:
            continue
        prog = os.path.basename(argv[0])
        # Recurse into `bash -c '...'` and `eval '...'` — the classic wrapper dodge.
        if prog in SHELLS and "-c" in argv[1:]:
            idx = argv.index("-c")
            if idx + 1 < len(argv):
                verdict = check_bash(argv[idx + 1], cwd)
                if verdict:
                    return verdict
            continue
        if prog == "eval":
            verdict = check_bash(" ".join(argv[1:]), cwd)
            if verdict:
                return verdict
            continue
        for rule in (_git, _rm, _installs):
            verdict = rule(prog, argv[1:], cwd)
            if verdict:
                return verdict
    return None


def _git(prog: str, args: list[str], cwd: str) -> dict | None:
    if prog != "git":
        return None
    joined = " ".join(args)
    if re.search(r"core\.hooksPath", joined, re.I):
        return deny(
            "Redirecting core.hooksPath bypasses the repo's git hooks. Fix the failure instead."
        )
    # Skip git's global options to find the subcommand: -C <dir>, -c <k=v>, --flags.
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c") else 1
    sub, rest = (args[i], args[i + 1 :]) if i < len(args) else ("", [])

    if "--no-verify" in rest or (sub == "commit" and _has_short_flag(rest, "n")):
        return deny(
            "--no-verify skips the hooks that ARE the gate. The gate being red is the "
            "signal — fix what it reports, or escalate to the human."
        )
    if sub == "push":
        forced = any(
            a in ("--force", "-f", "--mirror") or a.startswith("--force-with-lease")
            for a in rest
        ) or _has_short_flag(rest, "f")
        forced = forced or any(a.startswith("+") for a in rest)
        if forced:
            refs = {
                re.split(r"[:+]", a.lstrip("+"))[-1]
                for a in rest
                if not a.startswith("-")
            }
            if refs & PROTECTED_BRANCHES:
                return deny(
                    "Force-push to main/master rewrites shared history. Not an agent action."
                )
            return ask(
                "Force-push rewrites remote history — confirm the branch is yours alone."
            )
        if "--delete" in rest or "-d" in rest or any(a.startswith(":") for a in rest):
            return ask("Deleting a remote ref — confirm.")
    if sub == "reset" and "--hard" in rest:
        return ask(
            "`git reset --hard` discards uncommitted work irrecoverably — confirm."
        )
    if sub == "clean" and any(re.match(r"^-[a-zA-Z]*f", a) for a in rest):
        return ask("`git clean -f` deletes untracked files irrecoverably — confirm.")
    return None


def _has_short_flag(args: list[str], flag: str) -> bool:
    return any(re.match(rf"^-[a-zA-Z]*{flag}[a-zA-Z]*$", a) for a in args)


def _rm(prog: str, args: list[str], cwd: str) -> dict | None:
    if prog != "rm":
        return None
    flags = "".join(
        a.lstrip("-") for a in args if a.startswith("-") and not a.startswith("--")
    )
    long = {a for a in args if a.startswith("--")}
    recursive = "r" in flags or "R" in flags or "--recursive" in long
    if not recursive:
        return None
    root = Path(cwd).resolve()
    home = Path.home().resolve()
    for target in (a for a in args if not a.startswith("-")):
        if target in ("*", ".", "..", "~", "/", "/*") or target.startswith(
            ("$HOME", "${HOME}", "~/")
        ):
            return deny(
                f"`rm -r {target}` targets a root/home/whole-project path. Name the exact paths."
            )
        path = (
            (root / target).resolve()
            if not target.startswith("/")
            else Path(target).resolve()
        )
        if path in (home, Path("/")) or root.is_relative_to(path):
            return deny(
                f"`rm -r {target}` would delete home, root, or the project itself."
            )
        if not path.is_relative_to(root):
            return ask(
                f"`rm -r {target}` reaches outside the project ({root}) — confirm."
            )
    return None


def _installs(prog: str, args: list[str], cwd: str) -> dict | None:
    sub = args[0] if args else ""
    positional = [a for a in args[1:] if not a.startswith("-")]
    reason = None
    if (
        prog in ("npm", "pnpm", "yarn", "bun")
        and sub in ("install", "i", "add")
        and positional
    ):
        reason = f"{prog} {sub} {' '.join(positional)}"
    elif prog in ("pip", "pip3") or (
        prog.startswith("python") and args[:2] == ["-m", "pip"]
    ):
        pip_args = args[2:] if prog.startswith("python") else args
        if pip_args[:1] == ["install"] and _pip_adds_package(pip_args[1:]):
            reason = f"pip {' '.join(pip_args)}"
    elif prog == "uv" and (sub == "add" or (sub == "pip" and args[1:2] == ["install"])):
        reason = f"uv {' '.join(args)}"
    elif prog in ("poetry", "cargo") and sub in ("add", "install") and positional:
        reason = f"{prog} {' '.join(args)}"
    elif prog == "go" and sub in ("get", "install") and positional:
        reason = f"go {' '.join(args)}"
    elif prog in ("gem", "brew") and sub == "install":
        reason = f"{prog} {' '.join(args)}"
    elif prog in ("npx", "bunx", "uvx") or (prog in ("pnpm", "yarn") and sub == "dlx"):
        reason = f"{prog} {' '.join(args)} (downloads + runs an unreviewed package)"
    if reason:
        return ask(
            f"Guardrail 3 — installing a dependency executes its code before review: `{reason}`. "
            "Approve only if the human asked for this package."
        )
    return None


def _pip_adds_package(args: list[str]) -> bool:
    """`pip install -r reqs.txt` / `-e .` restore what's declared; a bare name adds one."""
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a in ("-r", "--requirement", "-c", "--constraint", "-e", "--editable"):
            skip_next = True
            continue
        if not a.startswith("-") and a != ".":
            return True
    return False


# ── Edit / Write ──────────────────────────────────────────────────────────────


def check_edit(file_path: str, cwd: str) -> dict | None:
    if not file_path:
        return None
    path = Path(file_path) if os.path.isabs(file_path) else Path(cwd) / file_path
    if not path.exists():
        return None  # creating a new config is scaffolding, not loosening
    try:
        rel = path.resolve().relative_to(Path(cwd).resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    for pattern in PROTECTED_CONFIG:
        if re.search(pattern, rel):
            return ask(
                f"`{rel}` decides what 'green' means (lint/typecheck/test/CI/deps). "
                "Loosening it to pass is faking done — approve only if the human asked for this change."
            )
    return None


def decide(payload: dict) -> dict | None:
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool == "Bash":
        return check_bash(tool_input.get("command", ""), cwd)
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return check_edit(
            tool_input.get("file_path") or tool_input.get("notebook_path", ""), cwd
        )
    return None


def main() -> int:
    if os.environ.get("HARNESS_GUARD", "").lower() == "off":
        return 0
    try:
        payload = json.load(sys.stdin)
        verdict = decide(payload)
    except (
        Exception
    ) as exc:  # never break the session on a guard bug — fail open, loudly
        print(f"[harness guard] internal error, allowing: {exc}", file=sys.stderr)
        return 0
    if verdict:
        print(json.dumps(verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
