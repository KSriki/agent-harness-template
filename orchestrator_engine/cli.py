"""CLI — every command prints JSON (or markdown where noted). The orchestrator
agent shells out to these; deterministic in, deterministic out."""

from __future__ import annotations

import argparse
import json
import sys

from .abort import execute_abort
from .budget import check_budget
from .complexity import assess_complexity
from .deploy import generate_deployment_plan
from .learnings import list_learnings, log_learning
from .runs import log_agent_completion, summarize_runs
from .models import get_model_for_agent
from .research import create_research_plan, format_research_summary
from .state import Registry


def _out(obj) -> None:
    print(json.dumps(obj, indent=2) if not isinstance(obj, str) else obj)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="orchestrator_engine")
    p.add_argument("--root", default=".", help="target repo root (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("state-init", help="start a run; scaffolds product-docs/")
    s.add_argument("--goal", required=True)
    s.add_argument("--work-type", required=True)
    s.add_argument("--budget-usd", type=float, default=None)

    sub.add_parser("state-show", help="print the state registry")

    s = sub.add_parser("worker", help="upsert a worker's state")
    s.add_argument("--name", required=True)
    s.add_argument("--slice", required=True, dest="slice_")
    s.add_argument("--branch", default=None)
    s.add_argument("--status", default="dispatched")

    s = sub.add_parser("spend", help="add spend to the run")
    s.add_argument("--usd", type=float, required=True)

    s = sub.add_parser("assess-complexity")
    s.add_argument("--tickets", type=int, default=1)
    s.add_argument("--boundaries", type=int, default=1)
    s.add_argument("--chain-depth", type=int, default=0)
    s.add_argument("--crosses-stack", action="store_true")

    s = sub.add_parser("check-budget")
    s.add_argument("--spent", type=float, required=True)
    s.add_argument("--cap", type=float, default=None)

    s = sub.add_parser("get-model")
    s.add_argument("--agent", required=True)

    s = sub.add_parser("log-completion")
    s.add_argument("--agent", required=True)
    s.add_argument("--model", required=True)
    s.add_argument(
        "--outcome", required=True, choices=["success", "escalation", "abort", "failed"]
    )
    s.add_argument("--turns", type=int, default=None)
    s.add_argument("--cost-usd", type=float, default=None)
    s.add_argument("--notes", default=None)

    sub.add_parser("ledger-summary")

    s = sub.add_parser(
        "log-learning", help="append a product-scoped operational learning"
    )
    s.add_argument("--agent", required=True)
    s.add_argument("--learning", required=True)

    s = sub.add_parser("learnings", help="list recorded learnings")
    s.add_argument("--limit", type=int, default=None)

    s = sub.add_parser("deploy-plan", help="branches JSON on stdin or --branches-json")
    s.add_argument("--branches-json", default=None)

    s = sub.add_parser("abort")
    s.add_argument("--reason", required=True)

    s = sub.add_parser(
        "research-plan", help="questions JSON list on stdin or --questions-json"
    )
    s.add_argument("--questions-json", default=None)

    s = sub.add_parser(
        "format-research", help="findings JSON list on stdin or --findings-json"
    )
    s.add_argument("--findings-json", default=None)

    a = p.parse_args(argv)
    reg = Registry(a.root)

    if a.cmd == "state-init":
        _out(reg.init_run(a.goal, a.work_type, a.budget_usd))
    elif a.cmd == "state-show":
        _out(reg.load())
    elif a.cmd == "worker":
        _out(reg.upsert_worker(a.name, a.slice_, a.branch, a.status))
    elif a.cmd == "spend":
        _out(reg.add_spend(a.usd))
    elif a.cmd == "assess-complexity":
        _out(assess_complexity(a.tickets, a.boundaries, a.chain_depth, a.crosses_stack))
    elif a.cmd == "check-budget":
        _out(check_budget(a.spent, a.cap))
    elif a.cmd == "get-model":
        _out(get_model_for_agent(a.agent, a.root))
    elif a.cmd == "log-completion":
        _out(
            log_agent_completion(
                a.agent, a.model, a.outcome, a.turns, a.cost_usd, a.notes, a.root
            )
        )
    elif a.cmd == "ledger-summary":
        _out(summarize_runs(a.root))
    elif a.cmd == "log-learning":
        _out(log_learning(a.agent, a.learning, a.root))
    elif a.cmd == "learnings":
        _out(list_learnings(a.root, a.limit))
    elif a.cmd == "deploy-plan":
        branches = json.loads(a.branches_json or sys.stdin.read())
        _out(generate_deployment_plan(branches))
    elif a.cmd == "abort":
        _out(execute_abort(a.reason, a.root))
    elif a.cmd == "research-plan":
        questions = json.loads(a.questions_json or sys.stdin.read())
        _out(create_research_plan(questions))
    elif a.cmd == "format-research":
        findings = json.loads(a.findings_json or sys.stdin.read())
        _out(format_research_summary(findings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
