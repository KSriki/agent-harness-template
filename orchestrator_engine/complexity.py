"""assess_complexity — deterministic dispatch-shape heuristic.

Inputs are counts the orchestrator already knows after reading the tickets.
No model call: the same inputs always give the same answer.
"""

from __future__ import annotations


def assess_complexity(
    tickets: int = 1,
    boundaries: int = 1,
    max_chain_depth: int = 0,
    crosses_stack: bool = False,
) -> dict:
    """tickets: how many; boundaries: distinct file-ownership areas;
    max_chain_depth: longest blocked-by chain; crosses_stack: UI+server both touched."""
    score = tickets + 2 * boundaries + max_chain_depth + (2 if crosses_stack else 0)
    if tickets <= 1 and boundaries <= 1:
        level = "single-worker"
        advice = (
            "Do NOT orchestrate: dispatch one worker (or hand back to the main thread)."
        )
    elif boundaries <= 3:
        level = "small-fanout"
        advice = "Fan out 2-3 workers in parallel; contract first; merge-validate."
    else:
        level = "staged-pipeline"
        advice = (
            "Too wide for one wave: sequence by blocked-by chains, cap 2-3 concurrent, "
            "use the defect ledger, consider a stacked-PR chain for dependent slices."
        )
    return {"score": score, "level": level, "advice": advice}
