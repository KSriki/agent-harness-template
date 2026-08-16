"""orchestrator_engine — deterministic scaffolding for multi-agent runs.

The doctrine (steering §7 / Agentic KB §0.9.5): keep control flow in CODE and
reserve the model for judgment. The orchestrator AGENT decides; this engine
computes, records, and orders. Stdlib only. Called via:

    python3 -m orchestrator_engine <command> ...   (JSON out, always)

State lives in the TARGET repo: .orchestrator/ (machine state + run ledger) and
product-docs/PRODUCT.md (the human/agent-readable resume anchor).
"""

from .state import Registry
from .complexity import assess_complexity
from .budget import check_budget
from .models import get_model_for_agent
from .ledger import log_agent_completion, summarize_runs
from .learnings import log_learning, list_learnings
from .deploy import generate_deployment_plan
from .abort import execute_abort
from .research import create_research_plan, format_research_summary

__all__ = [
    "Registry",
    "assess_complexity",
    "check_budget",
    "get_model_for_agent",
    "log_agent_completion",
    "summarize_runs",
    "log_learning",
    "list_learnings",
    "generate_deployment_plan",
    "execute_abort",
    "create_research_plan",
    "format_research_summary",
]
