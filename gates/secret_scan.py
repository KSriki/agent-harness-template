#!/usr/bin/env python3
"""secret_scan.py — the gate's secret check. Stdlib only; no gitleaks dependency.

    secret_scan.py          scan files changed vs HEAD + untracked   (gate `fast`)
    secret_scan.py --all    scan every tracked file                  (gate `full` / CI)

Exit 1 with file:line findings on a hit, 0 when clean. High-confidence patterns
only — a noisy scanner gets allowlisted into uselessness. A genuine test fixture
opts out per line with the pragma `gate:allow-secret` (reviewable in the diff).
Upgrade path: gitleaks is stronger — adopting it is a dependency decision
(guardrail 3), so it's proposed, not installed.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "private key": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY",
    "AWS access key": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "GitHub token": r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b",
    "Anthropic key": r"\bsk-ant-[A-Za-z0-9_-]{20,}",
    "OpenAI key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,}",
    "Slack token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "Stripe live key": r"\b(?:sk|rk)_live_[0-9A-Za-z]{24,}",
    "credential in URL": r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s:/@]{6,}@[\w.-]+",
}
COMPILED = [(name, re.compile(rx)) for name, rx in PATTERNS.items()]
PRAGMA = "gate:allow-secret"
MAX_BYTES = 1_000_000


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line]


def candidate_files(all_files: bool) -> list[Path]:
    if all_files:
        names = _git("ls-files")
    else:
        names = _git("diff", "--name-only", "HEAD") + _git(
            "ls-files", "--others", "--exclude-standard"
        )
    return [p for p in map(Path, dict.fromkeys(names)) if p.is_file()]


def scan_text(text: str) -> list[tuple[int, str]]:
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if PRAGMA in line:
            continue
        for name, rx in COMPILED:
            if rx.search(line):
                hits.append((lineno, name))
    return hits


def scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        if path.stat().st_size > MAX_BYTES:
            return []
        data = path.read_bytes()
    except OSError:
        return []
    if b"\0" in data[:8192]:  # binary
        return []
    return scan_text(data.decode("utf-8", errors="replace"))


def main(argv: list[str]) -> int:
    findings = [
        f"{path}:{lineno}: possible {name}"
        for path in candidate_files("--all" in argv)
        for lineno, name in scan_file(path)
    ]
    if not findings:
        return 0
    print(
        "SECRET SCAN FAILED — never commit credentials; move them to env/secret store:",
        file=sys.stderr,
    )
    for f in findings:
        print(f"  {f}", file=sys.stderr)
    print(
        f"False positive in a test fixture? Add `{PRAGMA}` to that line.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
