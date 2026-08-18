"""Product-scoped operational learnings — append-only JSONL.

<target-repo>/product-docs/docs/learnings.jsonl — one line per learning:
{"ts": ..., "agent": "orchestrator", "learning": "pydantic String fields without
max_length silently bypass validation ..."}

These are facts about THIS product's environment and libraries — the machine
version of AGENTS.md "Gotchas". They live in product-docs (committed knowledge,
not gitignored machine state) because a learning nobody can read is a learning
twice paid for.

GUARDRAIL #6 BOUNDARY: learnings never auto-modify the harness. A learning that
keeps recurring graduates into an AGENTS.md gotcha or a skill via evolve-harness
— proposed by an agent, applied by a human.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path


def _path(root: str | Path) -> Path:
    return Path(root) / "product-docs" / "docs" / "learnings.jsonl"


def log_learning(agent: str, learning: str, root: str | Path = ".") -> dict:
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "agent": agent,
        "learning": learning,
    }
    p = _path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def list_learnings(root: str | Path = ".", limit: int | None = None) -> dict:
    p = _path(root)
    if not p.exists():
        return {"count": 0, "learnings": []}
    entries = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    if limit:
        entries = entries[-limit:]
    return {"count": len(entries), "learnings": entries}
