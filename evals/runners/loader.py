"""Load + validate the eval config and golden jsonl files.

Golden case contract (frozen, versioned): {id, input, expected, tags}.
Rubric-based cases are a named extension point (see scorers.py) — NOT loaded here.
"""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED_CASE_FIELDS = ("id", "input", "expected", "tags")
REQUIRED_SUITE_FIELDS = ("golden", "scorer", "case_cap", "pass_floor", "prompt")
KNOWN_SCORERS = ("exact", "regex")


def load_golden(path: str | Path) -> list[dict]:
    """Read a golden .jsonl file; validate every case; reject duplicates."""
    path = Path(path)
    cases: list[dict] = []
    seen_ids: set[str] = set()
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{path.name} line {lineno}: not valid JSON ({exc})"
            ) from exc
        for field in REQUIRED_CASE_FIELDS:
            if field not in case:
                raise ValueError(f"{path.name} line {lineno}: missing field '{field}'")
        if case["id"] in seen_ids:
            raise ValueError(f"{path.name} line {lineno}: duplicate id '{case['id']}'")
        seen_ids.add(case["id"])
        cases.append(case)
    return cases


def load_config(path: str | Path) -> dict:
    """Read evals/config.json; validate suites against the scorer registry."""
    path = Path(path)
    config = json.loads(path.read_text())
    for key in ("model", "trials", "noise_floor_pp", "cost_rates_per_mtok", "suites"):
        if key not in config:
            raise ValueError(f"{path.name}: missing top-level key '{key}'")
    for name, suite in config["suites"].items():
        for field in REQUIRED_SUITE_FIELDS:
            if field not in suite:
                raise ValueError(f"{path.name}: suite '{name}' missing field '{field}'")
        if suite["scorer"] not in KNOWN_SCORERS:
            raise ValueError(
                f"{path.name}: suite '{name}' has unknown scorer '{suite['scorer']}'"
                f" (known: {', '.join(KNOWN_SCORERS)})"
            )
    return config
