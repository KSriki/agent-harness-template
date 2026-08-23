"""Portable eval runner — stdlib only, config-driven.

Usage:
    python3 -m evals.run --suite smoke|full [--trials N] [--dry-run]
                         [--config PATH]

Reads evals/config.json (suites, scorer, trials, noise floor, model, rates),
runs each golden case through the model seam (runners/model.py), scores with
the suite's configured scorer, and writes the full result to
evals/results/<timestamp>-<suite>.json (commit it — the trend is the point).

Honest unavailability: if the model CLI is missing/unauthenticated, prints a
LOUD skip and exits 0 — never silent, never fake-green, never red for absence
of the tool.

Gate: red (exit 1) when per-trial accuracy is below the suite's pass_floor —
UNLESS the delta vs the last committed result is within the configured noise
floor ("within noise, not a regression").

This file is a TEMPLATE deliverable: project-agnostic; everything
suite-specific lives in config.json, golden/*.jsonl, and prompts/*.txt
(prompt templates use a literal {input} placeholder).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from evals.runners.loader import load_config, load_golden
from evals.runners.metrics import (
    compare_to_baseline,
    estimate_cost_usd,
    estimate_tokens,
    suite_metrics,
)
from evals.runners.model import call_model, check_cli_available
from evals.runners.scorers import get_scorer

SKIP_BANNER = "=" * 72


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _find_baseline(results_dir: Path, suite_name: str) -> float | None:
    """Per-trial accuracy of the newest committed result for this suite."""
    candidates = sorted(results_dir.glob(f"*-{suite_name}.json"))
    if not candidates:
        return None
    last = json.loads(candidates[-1].read_text())
    return last.get("metrics", {}).get("per_trial_accuracy")


def run_suite(
    suite_name: str,
    config: dict,
    base_dir: str | Path,
    model_fn=call_model,
    trials: int | None = None,
) -> dict:
    """Run one suite end-to-end; write and return the full result dict."""
    base_dir = Path(base_dir)
    suite = config["suites"][suite_name]
    cases = load_golden(base_dir / suite["golden"])[: suite["case_cap"]]
    prompt_template = (base_dir / suite["prompt"]).read_text()
    scorer = get_scorer(suite["scorer"])
    model = config["model"]
    n_trials = trials if trials is not None else config["trials"]

    started = time.monotonic()
    case_results: list[dict] = []
    verdicts: list[list[bool]] = []
    input_tokens = output_tokens = 0
    for case in cases:
        prompt = prompt_template.replace("{input}", case["input"])
        trial_results = []
        for _ in range(n_trials):
            output = model_fn(prompt, model)
            passed = scorer(output, case["expected"])
            trial_results.append({"output": output.strip(), "passed": passed})
            input_tokens += estimate_tokens(prompt)
            output_tokens += estimate_tokens(output)
        flags = [t["passed"] for t in trial_results]
        verdicts.append(flags)
        case_results.append(
            {
                "id": case["id"],
                "expected": case["expected"],
                "tags": case["tags"],
                "trials": trial_results,
                "passed_any": any(flags),
                "passed_all": all(flags),
            }
        )
    wall_time_s = round(time.monotonic() - started, 3)

    metrics = suite_metrics(verdicts)
    results_dir = base_dir / "results"
    baseline = compare_to_baseline(
        current=metrics["per_trial_accuracy"],
        baseline=_find_baseline(results_dir, suite_name)
        if results_dir.is_dir()
        else None,
        noise_floor_pp=config["noise_floor_pp"],
    )
    below_floor = metrics["per_trial_accuracy"] < suite["pass_floor"]
    red = below_floor and not baseline["within_noise"]
    rates = config["cost_rates_per_mtok"][model]
    result = {
        "suite": suite_name,
        "timestamp": _timestamp(),
        "model": model,
        "trials": n_trials,
        "scorer": suite["scorer"],
        "cases": case_results,
        "metrics": metrics,
        "wall_time_s": wall_time_s,
        "cost": {
            "input_tokens_est": input_tokens,
            "output_tokens_est": output_tokens,
            "usd_est": round(estimate_cost_usd(input_tokens, output_tokens, rates), 6),
            "note": "estimate only: tokens ~= chars/4, priced by config rate table",
        },
        "baseline": baseline,
        "gate": {
            "pass_floor": suite["pass_floor"],
            "below_floor": below_floor,
            "red": red,
        },
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"{result['timestamp']}-{suite_name}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    result["result_file"] = str(out_path)
    return result


def _print_summary(result: dict) -> None:
    m = result["metrics"]
    print(
        f"suite: {result['suite']}   model: {result['model']}   trials: {result['trials']}"
    )
    failed = [c for c in result["cases"] if not c["passed_all"]]
    for c in result["cases"]:
        mark = "PASS" if c["passed_all"] else ("flaky" if c["passed_any"] else "FAIL")
        print(f"  [{mark:>5}] {c['id']} (expected: {c['expected']})")
    print(
        f"pass@k: {m['pass_at_k']:.1%}   pass^k: {m['pass_pow_k']:.1%}   "
        f"per-trial accuracy: {m['per_trial_accuracy']:.1%}"
    )
    print(
        f"wall time: {result['wall_time_s']}s   est. cost: ${result['cost']['usd_est']} ({result['cost']['note']})"
    )
    print(f"baseline: {result['baseline']['verdict']}")
    gate = result["gate"]
    if gate["red"]:
        print(f"GATE RED: per-trial accuracy below floor {gate['pass_floor']:.0%}")
        for c in failed:
            outs = {t["output"] for t in c["trials"] if not t["passed"]}
            print(f"  failing: {c['id']} expected '{c['expected']}' got {sorted(outs)}")
    elif gate["below_floor"]:
        print(
            f"below floor {gate['pass_floor']:.0%} but within noise of baseline — not flipping the gate"
        )
    else:
        print("GATE GREEN")
    print(f"result written: {result['result_file']}")


def _dry_run(config: dict, base_dir: Path, suite_name: str) -> int:
    suite = config["suites"][suite_name]
    cases = load_golden(base_dir / suite["golden"])
    (base_dir / suite["prompt"]).read_text()
    print(
        f"dry-run OK: suite '{suite_name}' — config valid, "
        f"{len(cases)} golden cases valid, prompt template found. No model calls made."
    )
    return 0


def main(argv=None, model_fn=call_model, availability_check=check_cli_available) -> int:
    parser = argparse.ArgumentParser(prog="evals.run", description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--trials", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--config", default=str(Path(__file__).parent / "config.json"))
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    base_dir = config_path.parent
    try:
        config = load_config(config_path)
        if args.suite not in config["suites"]:
            print(
                f"unknown suite '{args.suite}' (known: {', '.join(config['suites'])})"
            )
            return 2
        if args.dry_run:
            return _dry_run(config, base_dir, args.suite)
    except (ValueError, OSError) as exc:
        print(f"config/golden validation failed: {exc}")
        return 2

    ok, reason = availability_check()
    if not ok:
        print(SKIP_BANNER)
        print(f"EVALS SKIPPED: {reason} — this is not a pass.")
        print("No model was called; no result was recorded. Fix the CLI and re-run.")
        print(SKIP_BANNER)
        return 0

    result = run_suite(
        args.suite, config, base_dir, model_fn=model_fn, trials=args.trials
    )
    _print_summary(result)
    return 1 if result["gate"]["red"] else 0


if __name__ == "__main__":
    sys.exit(main())
