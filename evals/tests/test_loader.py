"""Loader tests — stdlib unittest, no deps. Run:
python3 -m unittest discover -s evals/tests -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from evals.runners.loader import load_config, load_golden


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


class TestLoadGolden(unittest.TestCase):
    def test_loads_valid_cases(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(
                Path(d) / "g.jsonl",
                '{"id": "c1", "input": "Fix the login bug", "expected": "bug-fix",'
                ' "tags": ["type:bug-fix", "difficulty:easy"]}\n'
                '{"id": "c2", "input": "Add dark mode", "expected": "feature",'
                ' "tags": ["type:feature", "difficulty:easy"]}\n',
            )
            cases = load_golden(p)
            self.assertEqual(len(cases), 2)
            self.assertEqual(cases[0]["id"], "c1")
            self.assertEqual(cases[1]["expected"], "feature")

    def test_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(
                Path(d) / "g.jsonl",
                '{"id": "c1", "input": "x", "expected": "y", "tags": []}\n\n\n',
            )
            self.assertEqual(len(load_golden(p)), 1)

    def test_missing_required_field_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(Path(d) / "g.jsonl", '{"id": "c1", "input": "x"}\n')
            with self.assertRaises(ValueError) as ctx:
                load_golden(p)
            self.assertIn("expected", str(ctx.exception))
            self.assertIn("line 1", str(ctx.exception))

    def test_duplicate_id_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(
                Path(d) / "g.jsonl",
                '{"id": "c1", "input": "x", "expected": "y", "tags": []}\n'
                '{"id": "c1", "input": "z", "expected": "y", "tags": []}\n',
            )
            with self.assertRaises(ValueError) as ctx:
                load_golden(p)
            self.assertIn("duplicate", str(ctx.exception).lower())

    def test_malformed_json_raises_with_line_number(self):
        with tempfile.TemporaryDirectory() as d:
            p = _write(Path(d) / "g.jsonl", "not json\n")
            with self.assertRaises(ValueError) as ctx:
                load_golden(p)
            self.assertIn("line 1", str(ctx.exception))


class TestLoadConfig(unittest.TestCase):
    def _config(self, d, overrides=None):
        cfg = {
            "model": "claude-haiku-4-5",
            "trials": 1,
            "noise_floor_pp": 3.0,
            "cost_rates_per_mtok": {"claude-haiku-4-5": {"input": 1.0, "output": 5.0}},
            "suites": {
                "smoke": {
                    "golden": "golden/g.jsonl",
                    "scorer": "exact",
                    "case_cap": 12,
                    "pass_floor": 0.9,
                    "prompt": "prompts/p.txt",
                }
            },
        }
        cfg.update(overrides or {})
        p = Path(d) / "config.json"
        p.write_text(json.dumps(cfg))
        return p

    def test_loads_and_resolves_suite(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = load_config(self._config(d))
            self.assertEqual(cfg["model"], "claude-haiku-4-5")
            self.assertIn("smoke", cfg["suites"])
            self.assertEqual(cfg["suites"]["smoke"]["scorer"], "exact")

    def test_unknown_scorer_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._config(d)
            bad = json.loads(p.read_text())
            bad["suites"]["smoke"]["scorer"] = "vibes"
            p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError) as ctx:
                load_config(p)
            self.assertIn("vibes", str(ctx.exception))

    def test_missing_suite_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._config(d)
            bad = json.loads(p.read_text())
            del bad["suites"]["smoke"]["golden"]
            p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError) as ctx:
                load_config(p)
            self.assertIn("golden", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
