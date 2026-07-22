#!/usr/bin/env python3
"""
init.py — fill in the 〈slots〉 in the agent harness template.

    python3 init.py                 # interactive, in the current repo
    python3 init.py --dry-run       # show what would change, write nothing
    python3 init.py --path ../myrepo
    python3 init.py --force         # re-run against an already-filled AGENTS.md

    NOTE on --force: it re-runs the fill against the CURRENT file. If that file is
    already filled, there are no slots left to fill and it's a no-op. To genuinely
    redo the wizard, restore the pristine file first:
        cp AGENTS.md.bak AGENTS.md && python3 init.py

Design notes (deliberate, not laziness):

  * DETECT → PROPOSE → CONFIRM. The script sniffs the repo (pyproject.toml,
    package.json, go.mod, docker-compose.yml) and proposes commands. You accept
    with Enter or override. It does not interrogate you for things it can see.

  * IT WILL NOT INVENT TRIBAL KNOWLEDGE. The "Gotchas" and "Repo-specific rules"
    sections in AGENTS.md are the highest-value part of the file precisely because
    they are TRUE. A wizard that fabricates plausible-sounding gotchas makes the
    file actively harmful. Those get a marked TODO and a prompt telling you to
    fill them in as you learn them.

  * Writes are gated: backups by default, --dry-run available, refuses to clobber
    a filled-in AGENTS.md without --force. Irreversible action → gate. Same rule
    as the rest of this repo.

Stdlib only. No dependencies. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ── tiny terminal helpers ────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _TTY else s


def bold(s: str) -> str:
    return _c("1", s)


def dim(s: str) -> str:
    return _c("2", s)


def green(s: str) -> str:
    return _c("32", s)


def yellow(s: str) -> str:
    return _c("33", s)


def red(s: str) -> str:
    return _c("31", s)


def cyan(s: str) -> str:
    return _c("36", s)


def rule(title: str = "") -> None:
    line = "─" * 68
    print(f"\n{dim(line)}")
    if title:
        print(bold(title))
        print(dim(line))


def ask(prompt: str, default: str = "", *, allow_empty: bool = False) -> str:
    """Prompt with a default. Enter accepts the default."""
    suffix = f" {dim('[' + default + ']')}" if default else ""
    while True:
        try:
            got = input(f"  {prompt}{suffix}\n  {cyan('›')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + yellow("Aborted. Nothing written."))
            sys.exit(1)
        val = got or default
        if val or allow_empty:
            return val
        print(red("  (required)"))


def ask_opt(prompt: str, default: str = "") -> str:
    """Optional command. Blank (just Enter) means 'not applicable' -> ''.

    Distinct from ask(): here a bare Enter must be able to mean NONE, not
    'accept the default'. Type '-' to explicitly clear a proposed default.
    """
    suffix = f" {dim('[' + default + ']')}" if default else f" {dim('(Enter to skip)')}"
    try:
        got = input(f"  {prompt}{suffix}\n  {cyan('›')} ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n" + yellow("Aborted. Nothing written."))
        sys.exit(1)
    if got == "-":
        return ""
    return got or default


def ask_yn(prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        try:
            got = input(f"  {prompt} {dim('[' + d + ']')}\n  {cyan('›')} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n" + yellow("Aborted. Nothing written."))
            sys.exit(1)
        if not got:
            return default
        if got in ("y", "yes"):
            return True
        if got in ("n", "no"):
            return False


def ask_choice(prompt: str, choices: list[str], default: int = 0) -> str:
    print(f"  {prompt}")
    for i, ch in enumerate(choices):
        mark = cyan("›") if i == default else " "
        print(f"    {mark} {bold(str(i + 1))}. {ch}")
    while True:
        try:
            got = input(f"  {cyan('›')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + yellow("Aborted. Nothing written."))
            sys.exit(1)
        if not got:
            return choices[default]
        if got.isdigit() and 1 <= int(got) <= len(choices):
            return choices[int(got) - 1]
        print(red(f"  (1–{len(choices)})"))


# ── stack detection ──────────────────────────────────────────────────────────


@dataclass
class Stack:
    """What we could figure out by looking, so we don't have to ask."""

    langs: list[str] = field(default_factory=list)
    py_mgr: str = ""  # uv | poetry | pip
    js_mgr: str = ""  # npm | pnpm | yarn
    has_docker: bool = False
    has_compose: bool = False
    has_tf: bool = False
    frameworks: list[str] = field(default_factory=list)

    def label(self) -> str:
        bits = list(self.langs) + list(self.frameworks)
        if self.has_docker:
            bits.append("Docker")
        if self.has_tf:
            bits.append("Terraform")
        return " · ".join(bits) if bits else "〈fill in〉"


def detect(root: Path) -> Stack:
    s = Stack()
    ex = lambda p: (root / p).exists()  # noqa: E731

    # Python
    if ex("pyproject.toml"):
        s.langs.append("Python")
        txt = (root / "pyproject.toml").read_text(errors="ignore")
        if ex("uv.lock") or "[tool.uv]" in txt:
            s.py_mgr = "uv"
        elif "[tool.poetry]" in txt:
            s.py_mgr = "poetry"
        else:
            s.py_mgr = "pip"
        for name, fw in (("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask")):
            if name in txt.lower():
                s.frameworks.append(fw)
    elif ex("requirements.txt") or ex("setup.py"):
        s.langs.append("Python")
        s.py_mgr = "pip"

    # JS / TS
    if ex("package.json"):
        try:
            pkg = json.loads((root / "package.json").read_text(errors="ignore"))
        except Exception:
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        s.langs.append("TypeScript" if ex("tsconfig.json") or "typescript" in deps else "JavaScript")
        s.js_mgr = (
            "pnpm" if ex("pnpm-lock.yaml") else "yarn" if ex("yarn.lock") else "npm"
        )
        for name, fw in (
            ("react", "React"),
            ("next", "Next.js"),
            ("vue", "Vue"),
            ("tailwindcss", "Tailwind"),
        ):
            if name in deps:
                s.frameworks.append(fw)

    # Go
    if ex("go.mod"):
        s.langs.append("Go")

    s.has_docker = ex("Dockerfile")
    s.has_compose = ex("docker-compose.yml") or ex("compose.yaml") or ex("docker-compose.yaml")
    s.has_tf = ex("main.tf") or ex("infra") or ex("terraform")
    return s


def propose_commands(s: Stack) -> dict[str, str]:
    """Best-guess commands. The human confirms or overrides each."""
    c: dict[str, str] = {}
    if "Python" in s.langs:
        if s.py_mgr == "uv":
            c |= {
                "install": "uv sync",
                "test": "uv run pytest",
                "test_one": "uv run pytest path/to/test.py::test_name",
                "lint": "uv run ruff check --fix . && uv run ruff format .",
                "typecheck": "uv run mypy src/",
                "coverage": "uv run pytest --cov=src --cov-report=term-missing",
            }
        elif s.py_mgr == "poetry":
            c |= {
                "install": "poetry install",
                "test": "poetry run pytest",
                "test_one": "poetry run pytest path/to/test.py::test_name",
                "lint": "poetry run ruff check --fix .",
                "typecheck": "poetry run mypy src/",
                "coverage": "poetry run pytest --cov=src",
            }
        else:
            c |= {
                "install": "pip install -r requirements.txt",
                "test": "pytest",
                "test_one": "pytest path/to/test.py::test_name",
                "lint": "ruff check --fix .",
                "typecheck": "mypy src/",
                "coverage": "pytest --cov=src",
            }
    elif "Go" in s.langs:
        c |= {
            "install": "go mod download",
            "test": "go test ./...",
            "test_one": "go test ./pkg -run TestName",
            "lint": "golangci-lint run",
            "typecheck": "go vet ./...",
            "coverage": "go test -cover ./...",
        }
    elif s.js_mgr:
        m = s.js_mgr
        run = f"{m} run" if m == "npm" else m
        c |= {
            "install": f"{m} install",
            "test": f"{run} test",
            "test_one": f"{run} test -- -t 'name'",
            "lint": f"{run} lint",
            "typecheck": f"{run} typecheck",
            "coverage": f"{run} test -- --coverage",
        }

    c["stack_up"] = "docker compose up -d" if s.has_compose else ""
    c["build"] = "docker build -t <name> ." if s.has_docker else ""
    return c


# ── the fill ─────────────────────────────────────────────────────────────────

SLOT = re.compile(r"〈([^〉]*)〉", re.S)

TODO = "**TODO — fill this in.** (init.py will not invent this; see below.)"


def fill_agents(text: str, a: dict[str, str]) -> str:
    """Fill AGENTS.md. Ordered, explicit — no clever regex-on-regex."""
    reps: list[tuple[str, str]] = [
        # header
        (
            "〈One or two sentences. What the system does and who uses it.\n"
            " e.g. \"Ingest pipeline + CV inference tier for document scans. Internal API,\n"
            " consumed by the review UI and the batch reprocessor.\"〉",
            a["what"],
        ),
        ("〈Python 3.12 / uv · Go 1.23 · React+TS · Postgres · Redis · S3 · Docker〉", a["stack"]),
        ("〈modular monolith | 3 services | …〉", a["rung"]),
        # commands
        ("〈`uv sync`〉", f"`{a['install']}`"),
        ("〈`uv run pytest`〉", f"`{a['test']}`"),
        ("〈`uv run pytest path/to/test.py::test_name`〉", f"`{a['test_one']}`"),
        ("〈`uv run ruff check --fix . && uv run ruff format .`〉", f"`{a['lint']}`"),
        ("〈`uv run mypy src/`〉", f"`{a['typecheck']}`"),
        ("〈`uv run pytest --cov=src --cov-report=term-missing`〉", f"`{a['coverage']}`"),
        ("〈`docker compose up -d`〉", f"`{a['stack_up']}`" if a["stack_up"] else "—"),
        ("〈`uv run alembic upgrade head`〉", f"`{a['migrate']}`" if a["migrate"] else "—"),
        ("〈`uv run python -m evals.run --suite smoke`〉", f"`{a['evals']}`" if a["evals"] else "—"),
        ("〈`docker build -t 〈svc〉 .`〉", f"`{a['build']}`" if a["build"] else "—"),
        ("〈tests · lint · typecheck · coverage ≥ 〈N〉%〉", a["gates"]),
        # guardrails: the install command line
        (
            "`〈uv add / pip install / npm install / go get〉`",
            f"`{a['add_dep']}`",
        ),
    ]
    for old, new in reps:
        text = text.replace(old, new)

    # Layout block
    text = SLOT.sub(lambda m: m.group(1) if "src/" in m.group(1) else m.group(0), text, count=0)

    # Tribal-knowledge sections: DO NOT FABRICATE.
    text = re.sub(
        r"(## Repo-specific rules\n\n)(<!--.*?-->\n\n)?(- 〈.*?〉\n)+",
        r"\1<!-- Only things TRUE HERE that would surprise a competent engineer.\n"
        r"     Delete anything that's just generic good practice — the steering doc has it. -->\n\n"
        f"- {TODO}\n"
        "- 〈e.g. `domain/` must not import from `adapters/`. Dependency points inward.〉\n"
        "- 〈e.g. All money is integer cents. No floats, ever.〉\n",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"(## Gotchas\n\n)(<!--.*?-->\n\n)?(- 〈.*?〉\n)+",
        r"\1<!-- The tribal knowledge that costs an agent an hour to rediscover.\n"
        r"     HIGHEST-VALUE SECTION IN THIS FILE. Add to it every time you watch an\n"
        r"     agent (or a new hire) fall in a hole. It is only useful because it's TRUE. -->\n\n"
        f"- {TODO}\n"
        "- 〈e.g. Integration tests need `docker compose up -d db` first, or they hang silently.〉\n",
        text,
        flags=re.S,
    )
    return text


def wire_claude_dir(root: Path) -> list[str]:
    """Symlink .claude/skills → ../skills and .claude/agents → ../agents so Claude
    Code's NATIVE discovery finds them, while the canonical files stay at the repo
    top level (portable to other tools, which read AGENTS.md directly).

    Idempotent: an already-correct link is left alone; a real directory or a wrong
    link is NOT clobbered — it's reported instead. Same gate-don't-clobber rule as
    the AGENTS.md write.
    """
    notes: list[str] = []
    claude = root / ".claude"
    for name, target in (("skills", "../skills"), ("agents", "../agents")):
        if not (root / name).is_dir():
            continue  # nothing to point at
        link = claude / name
        if link.is_symlink() and os.readlink(link) == target:
            notes.append(f"ok    .claude/{name} → {target} (already linked)")
            continue
        if link.exists() or link.is_symlink():
            notes.append(f"SKIP  .claude/{name} exists and isn't a → {target} symlink; left as-is")
            continue
        claude.mkdir(exist_ok=True)
        link.symlink_to(target)
        notes.append(f"linked .claude/{name} → {target}")
    return notes


def link_global(config_dir: str | None = None, *, dry_run: bool = False) -> int:
    """Symlink THIS harness's skills/ + agents/ into the global Claude config dir,
    so every project on this machine sees them. Run once per machine; re-runnable.

        source = the directory this script lives in (the harness repo)
        target = config_dir, else $CLAUDE_CONFIG_DIR, else ~/.claude

    Directory-level symlinks on purpose: a new skill you add to the repo shows up
    everywhere automatically, no re-run needed. Per-project context (AGENTS.md)
    stays per-repo. Gate-don't-clobber: an existing real dir is never overwritten.
    """
    src = Path(__file__).resolve().parent
    target = Path(
        config_dir or os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude")
    ).expanduser()

    rule("Link harness → global Claude config")
    print(dim(f"  source: {src}"))
    print(dim(f"  target: {target}"))
    if dry_run:
        print(yellow("  --dry-run: nothing will be written.\n"))

    for name in ("skills", "agents"):
        s = src / name
        if not s.is_dir():
            print(yellow(f"  ! {name}/ not found in {src} — skipped"))
            continue
        link = target / name
        if link.is_symlink() and os.path.realpath(str(link)) == os.path.realpath(str(s)):
            print(f"  {green('✓')} {link}  (already linked)")
            continue
        if link.exists() or link.is_symlink():
            print(yellow(f"  ! {link} exists and is not a link to this repo — left as-is"))
            print(dim("      move it aside (or pass --config-dir) and re-run"))
            continue
        if dry_run:
            print(f"  · would link {link} → {s}")
            continue
        target.mkdir(parents=True, exist_ok=True)
        link.symlink_to(s)
        print(f"  {green('✓')} linked {link} → {s}")

    if not dry_run:
        print()
        print("  " + bold("Restart Claude Code") + " (or start a new session) to load them.")
        print(dim("  Available in every project now; new skills you add appear automatically."))
        print(dim("  Per-project context (AGENTS.md) stays per-repo — run `python3 init.py` there."))
    return 0


# ── main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    p = argparse.ArgumentParser(description="Fill the 〈slots〉 in the agent harness template.")
    p.add_argument("--path", default=".", help="repo root (default: cwd)")
    p.add_argument("--dry-run", action="store_true", help="show changes, write nothing")
    p.add_argument("--force", action="store_true", help="overwrite an already-filled AGENTS.md")
    p.add_argument("--no-backup", action="store_true", help="skip .bak files")
    p.add_argument(
        "--link-global",
        action="store_true",
        help="symlink THIS harness's skills/ + agents/ into your global Claude config "
        "dir so they're available in every project, then exit (run once per machine)",
    )
    p.add_argument(
        "--config-dir",
        default=None,
        help="global Claude config dir for --link-global "
        "(default: $CLAUDE_CONFIG_DIR, else ~/.claude)",
    )
    args = p.parse_args()

    if args.link_global:
        return link_global(args.config_dir, dry_run=args.dry_run)

    root = Path(args.path).resolve()
    agents = root / "AGENTS.md"

    if not agents.exists():
        print(red(f"No AGENTS.md at {root}"))
        print(dim("  Run this from the repo root after copying the template in."))
        return 1

    original = agents.read_text()
    n_slots = len(SLOT.findall(original))

    # Has this already been run? A correctly-filled AGENTS.md still contains a few
    # INTENTIONAL example slots, so counting 〈〉 is the wrong test. The reliable
    # sentinel is the TODO marker that fill_agents() injects.
    already_filled = TODO in original or "| Install deps | 〈" not in original

    if already_filled and not args.force:
        print(yellow("\n  AGENTS.md looks already filled in."))
        print(dim("  (Found the init TODO marker / no unfilled command slots.)"))
        print(dim("  Re-run with --force to overwrite. A .bak is kept either way.\n"))
        return 1

    if n_slots == 0 and not args.force:
        print(yellow("AGENTS.md has no 〈slots〉 left — nothing to fill."))
        print(dim("  Re-run with --force to overwrite anyway."))
        return 1

    print(bold("\n  Agent Harness — init"))
    print(dim(f"  {root}"))
    print(dim(f"  {n_slots} slots found in AGENTS.md"))
    if args.dry_run:
        print(yellow("  DRY RUN — nothing will be written."))

    # ── detect
    s = detect(root)
    rule("Detected")
    if s.langs or s.has_docker:
        print(f"  {green('✓')} {s.label()}")
        if s.py_mgr:
            print(dim(f"    python: {s.py_mgr}"))
        if s.js_mgr:
            print(dim(f"    node:   {s.js_mgr}"))
        if s.has_compose:
            print(dim("    docker compose: yes"))
    else:
        print(dim("  (nothing detected — an empty repo? you'll type the commands)"))

    guess = propose_commands(s)

    # ── ask
    a: dict[str, str] = {}

    rule("What is this?")
    a["what"] = ask("One or two sentences — what it does and who uses it.")
    a["stack"] = ask("Stack", s.label())

    rule("Architecture rung  " + dim("(§0.7 — default LOW; climb only on a named failure)"))
    print(dim("  Rung 2 (modular monolith) is where most systems should stop.\n"))
    a["rung"] = ask_choice(
        "Current rung:",
        [
            "modular monolith (rung 2) — the usual right answer",
            "monolith (rung 1)",
            "single script (rung 0)",
            "a few services (rung 3)",
            "microservices (rung 4)",
            "serverless (rung 5)",
        ],
        default=0,
    ).split(" — ")[0]

    rule("Commands  " + dim("(Enter accepts the guess — these matter most)"))
    print(dim("  If these are wrong, the agent invents something worse.\n"))
    for key, label in (
        ("install", "install deps"),
        ("test", "run tests"),
        ("test_one", "run ONE test"),
        ("lint", "lint / format"),
        ("typecheck", "typecheck"),
        ("coverage", "coverage"),
    ):
        a[key] = ask(label, guess.get(key, ""))

    print(dim("\n  Optional — Enter to skip, '-' to clear a suggestion.\n"))
    a["stack_up"] = ask_opt("start local stack", guess.get("stack_up", ""))
    a["build"] = ask_opt("build", guess.get("build", ""))
    a["migrate"] = ask_opt("run migrations")
    a["evals"] = ask_opt("run evals " + dim("(skip if nothing non-deterministic)"))

    cov = ask("coverage threshold %", "80")
    a["gates"] = f"tests · lint · typecheck · coverage ≥ {cov}%"

    # dependency-add command, for the guardrail line
    a["add_dep"] = {
        "uv": "uv add",
        "poetry": "poetry add",
        "pip": "pip install",
    }.get(s.py_mgr) or ({"npm": "npm install", "pnpm": "pnpm add", "yarn": "yarn add"}.get(s.js_mgr)) or (
        "go get" if "Go" in s.langs else "uv add / pip install / npm install / go get"
    )

    # ── the honest part
    rule("What this script will NOT do")
    print(
        "  "
        + yellow("Gotchas")
        + " and "
        + yellow("Repo-specific rules")
        + " are left as TODO.\n"
    )
    print(dim("  Those are the highest-value sections in AGENTS.md, and they're only"))
    print(dim("  valuable because they're TRUE. A wizard that invents plausible-sounding"))
    print(dim("  gotchas makes the file actively harmful. So: they get a marked TODO."))
    print()
    print("  " + bold("Fill them in as you learn them.") + dim(" The rule:"))
    print(dim("  when you correct an agent on the same thing twice, that's a gotcha."))

    # ── write
    updated = fill_agents(original, a)
    left = len(SLOT.findall(updated))

    rule("Result")
    print(f"  slots filled:    {green(str(n_slots - left))}")
    print(f"  slots remaining: {yellow(str(left))} {dim('(examples + TODOs — intentional)')}")

    if args.dry_run:
        print(dim("\n  --dry-run: nothing written (AGENTS.md fill + .claude/ discovery symlinks skipped).\n"))
        return 0

    if not ask_yn(f"\n  Write {bold('AGENTS.md')}?", True):
        print(yellow("  Nothing written."))
        return 1

    if not args.no_backup:
        shutil.copy2(agents, agents.with_suffix(".md.bak"))
        print(dim(f"  backup → {agents.name}.bak"))
    agents.write_text(updated)
    print(f"  {green('✓')} wrote {agents}")

    # ── wire .claude/ so Claude Code natively discovers skills + subagents
    for note in wire_claude_dir(root):
        mark = green("✓") if note.startswith(("linked", "ok")) else yellow("!")
        print(f"  {mark} {note}")

    # ── next steps
    rule("Next")
    steps = [
        f"Fill the {bold('Gotchas')} + {bold('Repo-specific rules')} TODOs in AGENTS.md.",
        f"Rewrite {bold('docs/engineering-steering-doc.md')} — it encodes someone else's standards.",
        "Delete skills/agents you won't use (dead descriptions dilute live ones).",
        "Set your egress allowlist: skills/secure-code-review/ §6.",
    ]
    for i, st in enumerate(steps, 1):
        print(f"  {i}. {st}")

    print(bold("\n  Then verify it's actually loading:"))
    print("     Ask a fresh agent: " + cyan('"Add the leftpad package to fix this."'))
    print("     It must " + bold("REFUSE and escalate") + ".")
    print(dim("     If it installs, your always-on context isn't being read —"))
    print(dim("     and every guardrail in the repo is decorative.\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
