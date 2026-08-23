"""Run metrics — pass@k / pass^k, cost ESTIMATES, and the noise-floor comparison.

pass@k answers "can it ever?" (capability); pass^k answers "does it, reliably?"
(regression). At N=1 trials they are equal. See skills/eval-harness STEP 6.

Costs are ESTIMATES: tokens ~= chars / 4, priced by the per-model rate table in
config.json. Good enough to see the trend; never billing-grade.
"""

from __future__ import annotations

CHARS_PER_TOKEN = 4


def suite_metrics(verdicts_per_case: list[list[bool]]) -> dict:
    """verdicts_per_case: one list of per-trial pass/fail booleans per case."""
    if not verdicts_per_case:
        raise ValueError("no verdicts: cannot compute metrics for an empty run")
    cases = len(verdicts_per_case)
    trials = sum(len(v) for v in verdicts_per_case)
    return {
        "pass_at_k": sum(any(v) for v in verdicts_per_case) / cases,
        "pass_pow_k": sum(all(v) for v in verdicts_per_case) / cases,
        "per_trial_accuracy": sum(sum(v) for v in verdicts_per_case) / trials,
    }


def estimate_tokens(text: str) -> int:
    """Rough token estimate: chars / 4. Labeled as an estimate everywhere."""
    return len(text) // CHARS_PER_TOKEN


def estimate_cost_usd(input_tokens: int, output_tokens: int, rates: dict) -> float:
    """rates: {"input": $/MTok, "output": $/MTok} for the model under test."""
    return (
        input_tokens / 1_000_000 * rates["input"]
        + output_tokens / 1_000_000 * rates["output"]
    )


def compare_to_baseline(
    current: float, baseline: float | None, noise_floor_pp: float
) -> dict:
    """Compare a pass rate to the last committed result, honoring the noise floor.

    A delta inside the floor is 'within noise, not a regression' and must not
    flip the gate.
    """
    if baseline is None:
        return {
            "delta_pp": None,
            "within_noise": False,
            "verdict": "no baseline result to compare against (first run?)",
        }
    delta_pp = (current - baseline) * 100
    within = abs(delta_pp) <= noise_floor_pp
    if within:
        verdict = (
            f"delta {delta_pp:+.1f}pp vs baseline is within the "
            f"{noise_floor_pp:.1f}pp noise floor: within noise, not a regression"
        )
    elif delta_pp < 0:
        verdict = (
            f"delta {delta_pp:+.1f}pp vs baseline exceeds the "
            f"{noise_floor_pp:.1f}pp noise floor: this is a regression"
        )
    else:
        verdict = (
            f"delta {delta_pp:+.1f}pp vs baseline exceeds the "
            f"{noise_floor_pp:.1f}pp noise floor: improvement"
        )
    return {"delta_pp": delta_pp, "within_noise": within, "verdict": verdict}
