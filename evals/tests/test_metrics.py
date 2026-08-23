"""Metrics tests — pass@k, pass^k, per-trial accuracy, cost estimate, noise floor.

Expected values are worked examples computed by hand (independent of the code):
  3 cases x 2 trials, verdicts [[T,T],[T,F],[F,F]]:
    pass@k  = cases with ANY passing trial / cases = 2/3
    pass^k  = cases with ALL trials passing / cases = 1/3
    per-trial accuracy = passing trials / total trials = 3/6 = 0.5
"""

import unittest

from evals.runners.metrics import (
    compare_to_baseline,
    estimate_cost_usd,
    estimate_tokens,
    suite_metrics,
)

VERDICTS = [[True, True], [True, False], [False, False]]


class TestSuiteMetrics(unittest.TestCase):
    def test_worked_example(self):
        m = suite_metrics(VERDICTS)
        self.assertAlmostEqual(m["pass_at_k"], 2 / 3)
        self.assertAlmostEqual(m["pass_pow_k"], 1 / 3)
        self.assertAlmostEqual(m["per_trial_accuracy"], 0.5)

    def test_single_trial_pass_at_k_equals_pass_pow_k(self):
        m = suite_metrics([[True], [False], [True], [True]])
        self.assertAlmostEqual(m["pass_at_k"], 0.75)
        self.assertEqual(m["pass_at_k"], m["pass_pow_k"])
        self.assertEqual(m["pass_at_k"], m["per_trial_accuracy"])

    def test_all_pass(self):
        m = suite_metrics([[True, True, True]])
        self.assertEqual(m["pass_at_k"], 1.0)
        self.assertEqual(m["pass_pow_k"], 1.0)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            suite_metrics([])


class TestCostEstimate(unittest.TestCase):
    def test_token_estimate_is_chars_over_four(self):
        self.assertEqual(estimate_tokens("x" * 400), 100)

    def test_cost_uses_per_mtok_rates(self):
        # 1M input tokens at $1/MTok + 1M output tokens at $5/MTok = $6.
        rates = {"input": 1.0, "output": 5.0}
        self.assertAlmostEqual(estimate_cost_usd(1_000_000, 1_000_000, rates), 6.0)

    def test_small_run_worked_example(self):
        # 2000 input + 100 output tokens on haiku-style rates ($1/$5 per MTok):
        # 2000/1e6*1 + 100/1e6*5 = 0.0025
        rates = {"input": 1.0, "output": 5.0}
        self.assertAlmostEqual(estimate_cost_usd(2000, 100, rates), 0.0025)


class TestNoiseFloor(unittest.TestCase):
    def test_delta_within_floor_is_not_a_regression(self):
        r = compare_to_baseline(current=0.88, baseline=0.90, noise_floor_pp=3.0)
        self.assertAlmostEqual(r["delta_pp"], -2.0)
        self.assertTrue(r["within_noise"])
        self.assertIn("within noise, not a regression", r["verdict"])

    def test_delta_beyond_floor_is_a_regression(self):
        r = compare_to_baseline(current=0.80, baseline=0.90, noise_floor_pp=3.0)
        self.assertAlmostEqual(r["delta_pp"], -10.0)
        self.assertFalse(r["within_noise"])
        self.assertIn("regression", r["verdict"])
        self.assertNotIn("not a regression", r["verdict"])

    def test_improvement_beyond_floor_is_named(self):
        r = compare_to_baseline(current=0.98, baseline=0.90, noise_floor_pp=3.0)
        self.assertFalse(r["within_noise"])
        self.assertIn("improvement", r["verdict"])

    def test_no_baseline(self):
        r = compare_to_baseline(current=0.9, baseline=None, noise_floor_pp=3.0)
        self.assertIsNone(r["delta_pp"])
        self.assertIn("no baseline", r["verdict"])


if __name__ == "__main__":
    unittest.main()
