"""Scorers — the cheap end of the ladder (skills/eval-harness STEP 2).

Implemented: exact-match and regex/schema. Chosen per-suite via config.json.

EXTENSION POINT — judge scoring: rubric-based cases ({id, input, rubric, tags})
would add a `score_judge` entry here that calls a judge model (judge model !=
producer model, reason-before-verdict, validated against human labels first).
Deliberately NOT built: no suite needs it yet, and judge machinery is the most
common eval-harness waste. A scorer is any callable
(output: str, expected: str) -> bool registered in SCORERS.
"""

from __future__ import annotations

import re


def score_exact(output: str, expected: str) -> bool:
    """Case- and whitespace-insensitive exact match. Empty output never passes."""
    return output.strip().lower() == expected.strip().lower() != ""


def score_regex(output: str, expected: str) -> bool:
    """Schema-style check: the WHOLE (stripped) output must match the pattern."""
    return re.fullmatch(expected, output.strip()) is not None


SCORERS = {"exact": score_exact, "regex": score_regex}


def get_scorer(name: str):
    """Resolve a config scorer name to its callable."""
    if name not in SCORERS:
        raise ValueError(
            f"unknown scorer '{name}' (known: {', '.join(SCORERS)}). "
            "Judge scoring is a documented extension point — see this module's "
            "docstring — not yet implemented."
        )
    return SCORERS[name]
