"""Runner tests — end-to-end through the public interface (run_suite / main)
with the model seam MOCKED. The real CLI is never called from tests."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from evals.run import main, run_suite
from evals.runners.loader import load_config
from evals.runners.model import ModelUnavailable

GOLDEN = (
    '{"id": "c1", "input": "Add dark mode", "expected": "feature",'
    ' "tags": ["type:feature", "difficulty:easy"]}\n'
    '{"id": "c2", "input": "Fix the login bug", "expected": "bug-fix",'
    ' "tags": ["type:bug-fix", "difficulty:easy"]}\n'
    '{"id": "c3", "input": "Pay down the test debt", "expected": "debt",'
    ' "tags": ["type:debt", "difficulty:easy"]}\n'
)


def _scaffold(d: Path, case_cap: int = 12, pass_floor: float = 0.9) -> Path:
    (d / "golden").mkdir()
    (d / "prompts").mkdir()
    (d / "golden" / "g.jsonl").write_text(GOLDEN)
    (d / "prompts" / "p.txt").write_text("Classify: {input}\nAnswer with the type.")
    config = {
        "model": "claude-haiku-4-5",
        "trials": 1,
        "noise_floor_pp": 3.0,
        "cost_rates_per_mtok": {"claude-haiku-4-5": {"input": 1.0, "output": 5.0}},
        "suites": {
            "smoke": {
                "golden": "golden/g.jsonl",
                "scorer": "exact",
                "case_cap": case_cap,
                "pass_floor": pass_floor,
                "prompt": "prompts/p.txt",
            }
        },
    }
    cfg = d / "config.json"
    cfg.write_text(json.dumps(config))
    return cfg


def _oracle(prompt: str, model: str) -> str:
    """Fake model: answers correctly for every case in GOLDEN."""
    for needle, answer in (
        ("dark mode", "feature"),
        ("login bug", "bug-fix"),
        ("test debt", "debt"),
    ):
        if needle in prompt:
            return answer + "\n"
    return "unknown"


def _wrong_on_c3(prompt: str, model: str) -> str:
    return "feature\n" if "test debt" in prompt else _oracle(prompt, model)


class TestRunSuite(unittest.TestCase):
    def test_verdicts_metrics_and_result_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d)
            result = run_suite("smoke", load_config(cfg), d, model_fn=_wrong_on_c3)
            by_id = {c["id"]: c for c in result["cases"]}
            self.assertTrue(by_id["c1"]["trials"][0]["passed"])
            self.assertFalse(by_id["c3"]["trials"][0]["passed"])
            self.assertAlmostEqual(result["metrics"]["per_trial_accuracy"], 2 / 3)
            self.assertAlmostEqual(result["metrics"]["pass_at_k"], 2 / 3)
            self.assertEqual(
                result["metrics"]["pass_at_k"], result["metrics"]["pass_pow_k"]
            )
            # Result JSON committed to results/<timestamp>-<suite>.json
            files = list((d / "results").glob("*-smoke.json"))
            self.assertEqual(len(files), 1)
            on_disk = json.loads(files[0].read_text())
            self.assertEqual(on_disk["suite"], "smoke")
            self.assertIn("wall_time_s", on_disk)
            self.assertIn("estimate", on_disk["cost"]["note"])
            self.assertGreater(on_disk["cost"]["usd_est"], 0)

    def test_case_cap_limits_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d, case_cap=2)
            result = run_suite("smoke", load_config(cfg), d, model_fn=_oracle)
            self.assertEqual(len(result["cases"]), 2)

    def test_trials_n_runs_each_case_n_times(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d)
            calls = []

            def counting(prompt, model):
                calls.append(prompt)
                return _oracle(prompt, model)

            result = run_suite(
                "smoke", load_config(cfg), d, model_fn=counting, trials=2
            )
            self.assertEqual(len(calls), 6)  # 3 cases x 2 trials
            self.assertEqual(len(result["cases"][0]["trials"]), 2)

    def test_gate_red_below_floor_without_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d)
            result = run_suite("smoke", load_config(cfg), d, model_fn=_wrong_on_c3)
            self.assertTrue(result["gate"]["red"])

    def test_gate_not_red_when_within_noise_of_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d, pass_floor=0.68)  # floor above 2/3 = 0.667
            (d / "results").mkdir()
            baseline = {
                "suite": "smoke",
                "metrics": {"per_trial_accuracy": 0.667},
            }
            (d / "results" / "20260101T000000Z-smoke.json").write_text(
                json.dumps(baseline)
            )
            result = run_suite("smoke", load_config(cfg), d, model_fn=_wrong_on_c3)
            # 66.7% < 68% floor, but delta vs baseline is ~0pp: within noise.
            self.assertFalse(result["gate"]["red"])
            self.assertIn(
                "within noise, not a regression", result["baseline"]["verdict"]
            )


class TestMainCli(unittest.TestCase):
    def _main(self, argv, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(argv, **kwargs)
        return code, out.getvalue()

    def test_skip_path_is_loud_and_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _scaffold(Path(tmp))
            code, out = self._main(
                ["--suite", "smoke", "--config", str(cfg)],
                availability_check=lambda: (False, "'claude' CLI not found on PATH"),
            )
            self.assertEqual(code, 0)
            self.assertIn("EVALS SKIPPED", out)
            self.assertIn("this is not a pass", out)
            self.assertIn("not found", out)

    def test_midrun_model_unavailable_is_loud_skip_not_traceback(self):
        # An UNAUTHENTICATED CLI passes the PATH pre-flight but fails at call
        # time — that must be the same loud skip, never a raw traceback.
        def raises(prompt, model):
            raise ModelUnavailable(
                "'claude' exited 1: Not logged in · Please run /login"
            )

        with tempfile.TemporaryDirectory() as tmp:
            cfg = _scaffold(Path(tmp))
            code, out = self._main(
                ["--suite", "smoke", "--config", str(cfg)],
                model_fn=raises,
                availability_check=lambda: (True, ""),
            )
            self.assertEqual(code, 0)
            self.assertIn("EVALS SKIPPED", out)
            self.assertIn("Not logged in", out)
            self.assertIn("this is not a pass", out)

    def test_dry_run_validates_without_model_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _scaffold(Path(tmp))

            def explode(prompt, model):
                raise AssertionError("model called during --dry-run")

            code, out = self._main(
                ["--suite", "smoke", "--config", str(cfg), "--dry-run"],
                model_fn=explode,
            )
            self.assertEqual(code, 0)
            self.assertIn("dry-run", out.lower())

    def test_dry_run_catches_bad_golden(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            cfg = _scaffold(d)
            (d / "golden" / "g.jsonl").write_text('{"id": "c1"}\n')
            code, out = self._main(
                ["--suite", "smoke", "--config", str(cfg), "--dry-run"]
            )
            self.assertNotEqual(code, 0)

    def test_red_run_exits_nonzero_and_green_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _scaffold(Path(tmp))
            code_red, out_red = self._main(
                ["--suite", "smoke", "--config", str(cfg)],
                availability_check=lambda: (True, ""),
                model_fn=_wrong_on_c3,
            )
            self.assertEqual(code_red, 1)
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _scaffold(Path(tmp))
            code_green, out_green = self._main(
                ["--suite", "smoke", "--config", str(cfg), "--trials", "2"],
                availability_check=lambda: (True, ""),
                model_fn=_oracle,
            )
            self.assertEqual(code_green, 0)
            self.assertIn("pass@k", out_green)
            self.assertIn("pass^k", out_green)


if __name__ == "__main__":
    unittest.main()
