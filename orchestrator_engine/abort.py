"""execute_abort — record the abort and emit the wind-down plan.

HONEST LIMIT: this cannot kill a running subagent. It marks the registry
aborted, preserves what exists, and produces the plan the ORCHESTRATOR then
executes (stop dispatching, park branches, report partial state). An abort
that isn't recorded becomes a success claim later — that's the failure this
prevents.
"""

from __future__ import annotations

from .state import Registry


def execute_abort(reason: str, root: str = ".") -> dict:
    reg = Registry(root)
    data = reg.set_status("aborted", reason)
    open_workers = [w for w in data.get("workers", []) if w.get("status") not in ("done", "merged")]
    branches = [w["branch"] for w in data.get("workers", []) if w.get("branch")]
    return {
        "exit_class": "ABORT",
        "reason": reason,
        "dispatch": "STOP — no new workers; let in-flight workers finish or discard their worktrees",
        "preserve_branches": branches,
        "open_workers": open_workers,
        "cleanup": [f"git worktree remove <path-of:{w['name']}:{w['slice']}> --force" for w in open_workers],
        "report": "Return partial state + branch names + what remains. Never dress an abort as success.",
    }
