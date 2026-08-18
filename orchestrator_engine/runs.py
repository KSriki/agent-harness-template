"""log_agent_completion / summarize_runs — the RUN/TELEMETRY record.

Append-only JSONL at <repo>/.orchestrator/runs.jsonl. This is routing rule 4
("measure, don't vibe") made real: every agent completion is a data point, and
the summary is what re-tiers models on evidence.

Named runs.py, not ledger.py: "the ledger" in this harness means Beads (bd) —
the WORK ledger (tickets, dependencies, the frontier). This file is the
run/telemetry record. Two different jobs; don't merge them.
"""

from __future__ import annotations

import datetime
import json
from collections import defaultdict
from pathlib import Path


def _path(root: str | Path) -> Path:
    return Path(root) / ".orchestrator" / "runs.jsonl"


def log_agent_completion(
    agent: str,
    model: str,
    outcome: str,
    turns: int | None = None,
    cost_usd: float | None = None,
    notes: str | None = None,
    root: str | Path = ".",
) -> dict:
    """outcome: success | escalation | abort | failed"""
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "agent": agent,
        "model": model,
        "outcome": outcome,
        "turns": turns,
        "cost_usd": cost_usd,
        "notes": notes,
    }
    p = _path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def summarize_runs(root: str | Path = ".") -> dict:
    p = _path(root)
    if not p.exists():
        return {"runs": 0, "by_agent": {}, "note": "no ledger yet"}
    by_agent: dict = defaultdict(lambda: {"runs": 0, "outcomes": defaultdict(int), "cost_usd": 0.0, "models": defaultdict(int)})
    total = 0
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        total += 1
        a = by_agent[e["agent"]]
        a["runs"] += 1
        a["outcomes"][e.get("outcome", "?")] += 1
        a["models"][e.get("model", "?")] += 1
        if e.get("cost_usd"):
            a["cost_usd"] = round(a["cost_usd"] + e["cost_usd"], 4)
    return {
        "runs": total,
        "by_agent": {k: {**v, "outcomes": dict(v["outcomes"]), "models": dict(v["models"])} for k, v in by_agent.items()},
    }
