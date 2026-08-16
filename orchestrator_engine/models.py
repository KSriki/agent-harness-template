"""get_model_for_agent — the model registry, resolvable by code.

Defaults mirror the agents' frontmatter (the git-versioned registry). A target
repo may override per-agent via <repo>/.orchestrator/models.json, e.g.
{"implementer": "sonnet"} — reviewed like any config change.
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {
    "orchestrator": "opus",
    "code-searcher": "haiku",
    "test-writer": "sonnet",
    "implementer": "inherit",
    "frontend-implementer": "inherit",
    "backend-implementer": "inherit",
    "security-reviewer": "opus",
    "design-reviewer": "opus",
    "deploy-reviewer": "opus",
    "debug-research": "opus",
    "trend-scout": "opus",
}

VALID = {"haiku", "sonnet", "opus", "fable", "inherit"}


def get_model_for_agent(agent: str, root: str | Path = ".") -> dict:
    overrides_path = Path(root) / ".orchestrator" / "models.json"
    source = "default"
    model = DEFAULTS.get(agent)
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text())
        if agent in overrides:
            model, source = overrides[agent], "override"
    if model is None:
        return {"agent": agent, "model": "inherit", "source": "unknown-agent-fallback"}
    if model not in VALID:
        return {"agent": agent, "model": "inherit", "source": f"invalid-value({model})-fallback"}
    return {"agent": agent, "model": model, "source": source}
