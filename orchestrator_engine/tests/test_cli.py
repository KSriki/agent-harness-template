"""CLI tests — every subcommand path through main(argv), JSON out. Run:
python3 -m unittest discover -s orchestrator_engine/tests -v
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from orchestrator_engine.cli import main


def run_cli(*argv, stdin=None):
    """Invoke main() with argv, return (exit_code, parsed-or-raw stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if stdin is not None:
            with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                code = main(list(argv))
        else:
            code = main(list(argv))
    out = buf.getvalue()
    try:
        return code, json.loads(out)
    except json.JSONDecodeError:
        return code, out


class TestStateCommands(unittest.TestCase):
    def test_state_init_scaffolds_and_reports(self):
        with tempfile.TemporaryDirectory() as d:
            code, data = run_cli(
                "--root",
                d,
                "state-init",
                "--goal",
                "test product",
                "--work-type",
                "feature",
                "--budget-usd",
                "25.0",
            )
            self.assertEqual(code, 0)
            self.assertEqual(data["status"], "running")
            self.assertEqual(data["run"]["budget_usd"], 25.0)
            self.assertTrue((Path(d) / "product-docs" / "PRODUCT.md").exists())

    def test_state_show_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            run_cli("--root", d, "state-init", "--goal", "g", "--work-type", "feature")
            code, data = run_cli("--root", d, "state-show")
            self.assertEqual(code, 0)
            self.assertEqual(data["status"], "running")
            self.assertEqual(data["run"]["goal"], "g")

    def test_worker_upsert(self):
        with tempfile.TemporaryDirectory() as d:
            run_cli("--root", d, "state-init", "--goal", "g", "--work-type", "feature")
            run_cli(
                "--root",
                d,
                "worker",
                "--name",
                "backend-implementer",
                "--slice",
                "api",
                "--branch",
                "feat/api",
            )
            code, data = run_cli(
                "--root",
                d,
                "worker",
                "--name",
                "backend-implementer",
                "--slice",
                "api",
                "--status",
                "done",
            )
            self.assertEqual(code, 0)
            workers = data["workers"]
            self.assertEqual(len(workers), 1)
            self.assertEqual(workers[0]["status"], "done")
            self.assertEqual(workers[0]["branch"], "feat/api")

    def test_spend_accumulates(self):
        with tempfile.TemporaryDirectory() as d:
            run_cli("--root", d, "state-init", "--goal", "g", "--work-type", "feature")
            run_cli("--root", d, "spend", "--usd", "1.25")
            code, data = run_cli("--root", d, "spend", "--usd", "0.75")
            self.assertEqual(code, 0)
            self.assertEqual(data["spend_usd"], 2.0)


class TestAssessComplexity(unittest.TestCase):
    def test_single_worker_default(self):
        code, data = run_cli("assess-complexity")
        self.assertEqual(code, 0)
        self.assertEqual(data["level"], "single-worker")

    def test_staged_pipeline_with_flags(self):
        code, data = run_cli(
            "assess-complexity",
            "--tickets",
            "8",
            "--boundaries",
            "5",
            "--chain-depth",
            "3",
            "--crosses-stack",
        )
        self.assertEqual(code, 0)
        self.assertEqual(data["level"], "staged-pipeline")


class TestCheckBudget(unittest.TestCase):
    def test_thresholds(self):
        code, data = run_cli("check-budget", "--spent", "5", "--cap", "25")
        self.assertEqual(code, 0)
        self.assertEqual(data["action"], "continue")
        _, data = run_cli("check-budget", "--spent", "25", "--cap", "25")
        self.assertEqual(data["action"], "abort")

    def test_no_cap(self):
        code, data = run_cli("check-budget", "--spent", "999")
        self.assertEqual(code, 0)
        self.assertEqual(data["action"], "continue")


class TestGetModel(unittest.TestCase):
    def test_default_and_override(self):
        code, data = run_cli("get-model", "--agent", "code-searcher")
        self.assertEqual(code, 0)
        self.assertEqual(data["model"], "haiku")
        with tempfile.TemporaryDirectory() as d:
            od = Path(d) / ".orchestrator"
            od.mkdir()
            (od / "models.json").write_text(json.dumps({"implementer": "sonnet"}))
            _, data = run_cli("--root", d, "get-model", "--agent", "implementer")
            self.assertEqual(data["model"], "sonnet")
            self.assertEqual(data["source"], "override")


class TestLedgerCommands(unittest.TestCase):
    def test_log_completion_and_summary(self):
        with tempfile.TemporaryDirectory() as d:
            code, _ = run_cli(
                "--root",
                d,
                "log-completion",
                "--agent",
                "implementer",
                "--model",
                "inherit",
                "--outcome",
                "success",
                "--turns",
                "12",
                "--cost-usd",
                "0.5",
                "--notes",
                "clean run",
            )
            self.assertEqual(code, 0)
            run_cli(
                "--root",
                d,
                "log-completion",
                "--agent",
                "implementer",
                "--model",
                "inherit",
                "--outcome",
                "failed",
            )
            code, summary = run_cli("--root", d, "ledger-summary")
            self.assertEqual(code, 0)
            self.assertEqual(summary["runs"], 2)
            self.assertEqual(
                summary["by_agent"]["implementer"]["outcomes"]["failed"], 1
            )

    def test_invalid_outcome_rejected(self):
        with self.assertRaises(SystemExit):
            run_cli(
                "log-completion", "--agent", "a", "--model", "m", "--outcome", "nope"
            )


class TestLearningsCommands(unittest.TestCase):
    def test_log_and_list_with_limit(self):
        with tempfile.TemporaryDirectory() as d:
            run_cli(
                "--root",
                d,
                "log-learning",
                "--agent",
                "orchestrator",
                "--learning",
                "compose is a standalone binary",
            )
            run_cli(
                "--root",
                d,
                "log-learning",
                "--agent",
                "backend-implementer",
                "--learning",
                "string without max_length bypasses validation",
            )
            code, got = run_cli("--root", d, "learnings")
            self.assertEqual(code, 0)
            self.assertEqual(got["count"], 2)
            _, limited = run_cli("--root", d, "learnings", "--limit", "1")
            self.assertEqual(limited["learnings"][0]["agent"], "backend-implementer")


class TestDeployPlan(unittest.TestCase):
    BRANCHES = [
        {"name": "feat/ui", "slice": "ui", "blocked_by": ["feat/api"]},
        {"name": "feat/api", "slice": "api", "blocked_by": []},
    ]

    def test_branches_json_flag(self):
        code, plan = run_cli(
            "deploy-plan", "--branches-json", json.dumps(self.BRANCHES)
        )
        self.assertEqual(code, 0)
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["merge_order"], ["feat/api", "feat/ui"])

    def test_branches_on_stdin(self):
        code, plan = run_cli("deploy-plan", stdin=json.dumps(self.BRANCHES))
        self.assertEqual(code, 0)
        self.assertEqual(plan["merge_order"], ["feat/api", "feat/ui"])


class TestAbort(unittest.TestCase):
    def test_abort_marks_state(self):
        with tempfile.TemporaryDirectory() as d:
            run_cli("--root", d, "state-init", "--goal", "g", "--work-type", "feature")
            run_cli(
                "--root",
                d,
                "worker",
                "--name",
                "implementer",
                "--slice",
                "core",
                "--branch",
                "feat/core",
            )
            code, result = run_cli("--root", d, "abort", "--reason", "budget cap hit")
            self.assertEqual(code, 0)
            self.assertEqual(result["exit_class"], "ABORT")
            self.assertIn("feat/core", result["preserve_branches"])
            _, state = run_cli("--root", d, "state-show")
            self.assertEqual(state["status"], "aborted")


class TestResearchCommands(unittest.TestCase):
    QUESTIONS = ["why does httpx timeout on streams"]

    def test_research_plan_flag_and_stdin(self):
        code, plan = run_cli(
            "research-plan", "--questions-json", json.dumps(self.QUESTIONS)
        )
        self.assertEqual(code, 0)
        self.assertEqual(plan["questions"][0]["agent"], "debug-research")
        _, plan = run_cli("research-plan", stdin=json.dumps(self.QUESTIONS))
        self.assertEqual(plan["questions"][0]["agent"], "debug-research")

    def test_format_research_markdown_out(self):
        findings = [
            {"question": "q1", "verdict": "yes", "confidence": "high", "sources": ["a"]}
        ]
        code, md = run_cli("format-research", "--findings-json", json.dumps(findings))
        self.assertEqual(code, 0)
        self.assertIsInstance(md, str)
        self.assertIn("| 1 | q1 | yes | high | a |", md)


class TestArgparseGuards(unittest.TestCase):
    def test_missing_subcommand_exits(self):
        with self.assertRaises(SystemExit):
            run_cli()

    def test_unknown_subcommand_exits(self):
        with self.assertRaises(SystemExit):
            run_cli("no-such-cmd")


if __name__ == "__main__":
    unittest.main()
