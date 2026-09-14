"""Scorer tests — exact-match and regex, the cheap end of the ladder."""

import unittest

from evals.runners.scorers import (
    get_scorer,
    score_exact,
    score_first_word,
    score_regex,
)


class TestExactScorer(unittest.TestCase):
    def test_exact_match_passes(self):
        self.assertTrue(score_exact("feature", "feature"))

    def test_mismatch_fails(self):
        self.assertFalse(score_exact("bug-fix", "feature"))

    def test_normalizes_case_and_whitespace(self):
        self.assertTrue(score_exact("  Feature \n", "feature"))

    def test_empty_output_fails(self):
        self.assertFalse(score_exact("", "feature"))


class TestRegexScorer(unittest.TestCase):
    def test_pattern_fullmatch_passes(self):
        self.assertTrue(score_regex("run-2026-08-23", r"run-\d{4}-\d{2}-\d{2}"))

    def test_partial_match_is_not_enough(self):
        # Schema-style check: the WHOLE output must conform, not a substring.
        self.assertFalse(
            score_regex("garbage run-2026-08-23", r"run-\d{4}-\d{2}-\d{2}")
        )

    def test_no_match_fails(self):
        self.assertFalse(score_regex("nope", r"\d+"))

    def test_output_whitespace_stripped(self):
        self.assertTrue(score_regex(" 42 \n", r"\d+"))


class TestScoreFirstWord(unittest.TestCase):
    """Regression (baseline run 2026-09-14): a correct single-word verdict
    followed by unrequested reasoning must still pass a single-label suite."""

    def test_bare_word_passes(self):
        self.assertTrue(score_first_word("rethink", "rethink"))

    def test_verdict_plus_reasoning_passes(self):
        self.assertTrue(
            score_first_word("rethink\n\n**Reason:** rule 2(b) applies.", "rethink")
        )

    def test_hyphenated_label_is_one_token(self):
        self.assertTrue(score_first_word("single-source because ...", "single-source"))

    def test_case_insensitive(self):
        self.assertTrue(score_first_word("Proceed.", "proceed") is False)
        self.assertTrue(score_first_word("Proceed", "proceed"))

    def test_wrong_first_word_fails(self):
        self.assertFalse(score_first_word("proceed rethink", "rethink"))

    def test_empty_output_never_passes(self):
        self.assertFalse(score_first_word("", "proceed"))
        self.assertFalse(score_first_word("   \n", "proceed"))


class TestScorerRegistry(unittest.TestCase):
    def test_lookup_by_config_name(self):
        self.assertIs(get_scorer("exact"), score_exact)
        self.assertIs(get_scorer("regex"), score_regex)
        self.assertIs(get_scorer("first-word"), score_first_word)

    def test_unknown_scorer_raises_and_names_judge_extension_point(self):
        with self.assertRaises(ValueError) as ctx:
            get_scorer("llm-judge")
        # Judge scoring is a documented extension point, not built machinery.
        self.assertIn("extension point", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
