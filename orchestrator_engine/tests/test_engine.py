"""Engine tests — stdlib unittest, no deps. Run:
python3 -m unittest discover -s orchestrator_engine/tests -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from orchestrator_engine import (
    Registry,
    assess_complexity,
    check_budget,
    create_research_plan,
    execute_abort,
    format_research_summary,
    generate_deployment_plan,
    get_model_for_agent,
    list_learnings,
    log_agent_completion,
    log_learning,
    summarize_runs,
)


class TestRegistry(unittest.TestCase):
    def test_init_scaffolds_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Registry(d)
            data = reg.init_run("test product", "feature", budget_usd=25.0)
            self.assertEqual(data["status"], "running")
            self.assertEqual(data["run"]["budget_usd"], 25.0)
            self.assertTrue((Path(d) / "product-docs" / "PRODUCT.md").exists())
            self.assertTrue((Path(d) / "product-docs" / "REGISTRY.md").exists())
            self.assertIn(
                "Component Registry",
                (Path(d) / "product-docs" / "REGISTRY.md").read_text(),
            )
            product = (Path(d) / "product-docs" / "PRODUCT.md").read_text()
            for section in (
                "Gate history",
                "Decision log",
                "Pipeline state",
                "Git workflow",
            ):
                self.assertIn(section, product)
            self.assertTrue(
                (
                    Path(d) / "product-docs" / "docs" / "vision" / "product-vision.md"
                ).exists()
            )
            self.assertTrue((Path(d) / "product-docs" / "docs" / "sprints").is_dir())

    def test_worker_upsert_updates_not_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Registry(d)
            reg.init_run("g", "feature")
            reg.upsert_worker("backend-implementer", "api", branch="feat/api")
            reg.upsert_worker("backend-implementer", "api", status="done")
            data = reg.load()
            self.assertEqual(len(data["workers"]), 1)
            self.assertEqual(data["workers"][0]["status"], "done")
            self.assertEqual(data["workers"][0]["branch"], "feat/api")

    def test_spend_accumulates(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Registry(d)
            reg.init_run("g", "feature")
            reg.add_spend(1.25)
            self.assertEqual(reg.add_spend(0.75)["spend_usd"], 2.0)


class TestComplexity(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(assess_complexity(1, 1)["level"], "single-worker")
        self.assertEqual(assess_complexity(4, 2, 1)["level"], "small-fanout")
        self.assertEqual(assess_complexity(8, 5, 3, True)["level"], "staged-pipeline")

    def test_deterministic(self):
        self.assertEqual(assess_complexity(3, 2, 1), assess_complexity(3, 2, 1))


class TestBudget(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(check_budget(5, 25)["action"], "continue")
        self.assertEqual(check_budget(20, 25)["action"], "warn")
        self.assertEqual(check_budget(25, 25)["action"], "abort")
        self.assertFalse(check_budget(30, 25)["ok"])

    def test_no_cap(self):
        self.assertEqual(check_budget(999, None)["action"], "continue")


class TestModels(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(get_model_for_agent("code-searcher")["model"], "haiku")
        self.assertEqual(get_model_for_agent("security-reviewer")["model"], "opus")
        self.assertEqual(get_model_for_agent("implementer")["model"], "inherit")

    def test_override_and_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            od = Path(d) / ".orchestrator"
            od.mkdir()
            (od / "models.json").write_text(
                json.dumps({"implementer": "sonnet", "test-writer": "gpt-9"})
            )
            self.assertEqual(
                get_model_for_agent("implementer", d)["source"], "override"
            )
            self.assertEqual(get_model_for_agent("implementer", d)["model"], "sonnet")
            # invalid value falls back safely
            self.assertEqual(get_model_for_agent("test-writer", d)["model"], "inherit")

    def test_unknown_agent(self):
        self.assertEqual(get_model_for_agent("nonexistent")["model"], "inherit")


class TestLedger(unittest.TestCase):
    def test_append_and_summarize(self):
        with tempfile.TemporaryDirectory() as d:
            log_agent_completion(
                "implementer", "inherit", "success", turns=12, cost_usd=0.5, root=d
            )
            log_agent_completion("implementer", "inherit", "failed", root=d)
            log_agent_completion(
                "security-reviewer", "opus", "success", cost_usd=0.2, root=d
            )
            s = summarize_runs(d)
            self.assertEqual(s["runs"], 3)
            self.assertEqual(s["by_agent"]["implementer"]["runs"], 2)
            self.assertEqual(s["by_agent"]["implementer"]["outcomes"]["failed"], 1)
            self.assertEqual(s["by_agent"]["security-reviewer"]["cost_usd"], 0.2)


class TestDeployPlan(unittest.TestCase):
    def test_topo_order_respects_edges(self):
        plan = generate_deployment_plan(
            [
                {"name": "feat/ui", "slice": "ui", "blocked_by": ["feat/api"]},
                {"name": "feat/api", "slice": "api", "blocked_by": ["feat/schema"]},
                {"name": "feat/schema", "slice": "schema", "blocked_by": []},
            ]
        )
        self.assertTrue(plan["ok"])
        self.assertEqual(plan["merge_order"], ["feat/schema", "feat/api", "feat/ui"])
        self.assertIn("final full gate", plan["steps"][-2])

    def test_cycle_detected(self):
        plan = generate_deployment_plan(
            [
                {"name": "a", "slice": "a", "blocked_by": ["b"]},
                {"name": "b", "slice": "b", "blocked_by": ["a"]},
            ]
        )
        self.assertFalse(plan["ok"])
        self.assertEqual(sorted(plan["in_cycle"]), ["a", "b"])


class TestAbort(unittest.TestCase):
    def test_abort_marks_state_and_plans_winddown(self):
        with tempfile.TemporaryDirectory() as d:
            reg = Registry(d)
            reg.init_run("g", "feature")
            reg.upsert_worker("implementer", "core", branch="feat/core")
            result = execute_abort("budget cap hit", root=d)
            self.assertEqual(result["exit_class"], "ABORT")
            self.assertIn("feat/core", result["preserve_branches"])
            self.assertEqual(reg.load()["status"], "aborted")
            self.assertEqual(reg.load()["status_reason"], "budget cap hit")


class TestLearnings(unittest.TestCase):
    def test_append_and_list(self):
        with tempfile.TemporaryDirectory() as d:
            log_learning(
                "orchestrator",
                "docker compose is the standalone binary at /usr/local/bin",
                root=d,
            )
            log_learning(
                "backend-implementer",
                "pydantic String without max_length bypasses validation",
                root=d,
            )
            got = list_learnings(d)
            self.assertEqual(got["count"], 2)
            self.assertEqual(got["learnings"][1]["agent"], "backend-implementer")
            self.assertEqual(
                list_learnings(d, limit=1)["learnings"][0]["agent"],
                "backend-implementer",
            )
            # lives in committed product-docs, not gitignored machine state
            self.assertTrue(
                (Path(d) / "product-docs" / "docs" / "learnings.jsonl").exists()
            )


class TestResearch(unittest.TestCase):
    def test_routing(self):
        plan = create_research_plan(
            ["why does httpx timeout on streams", "what changed in the React ecosystem"]
        )
        agents = [q["agent"] for q in plan["questions"]]
        self.assertEqual(agents, ["debug-research", "trend-scout"])

    def test_summary_format(self):
        md = format_research_summary(
            [
                {
                    "question": "q1",
                    "verdict": "yes",
                    "confidence": "high",
                    "sources": ["a", "b"],
                }
            ]
        )
        self.assertIn("| 1 | q1 | yes | high | a · b |", md)


if __name__ == "__main__":
    unittest.main()
