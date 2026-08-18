"""generate_deployment_plan — deterministic merge/ship ordering.

Topological sort (Kahn) over the branches' blocked-by edges. The blocking edges
the tickets already declared ARE the merge order; a cycle is a planning bug and
is reported, never silently broken.
"""

from __future__ import annotations


def generate_deployment_plan(
    branches: list[dict], gate_cmd: str = "./.claude/gate.sh full"
) -> dict:
    """branches: [{"name": str, "slice": str, "blocked_by": [names]}]"""
    names = {b["name"] for b in branches}
    deps = {
        b["name"]: [d for d in b.get("blocked_by", []) if d in names] for b in branches
    }
    indegree = {n: len(ds) for n, ds in deps.items()}
    ready = sorted([n for n, d in indegree.items() if d == 0])
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m, ds in deps.items():
            if n in ds:
                indegree[m] -= 1
                if indegree[m] == 0:
                    ready.append(m)
        ready.sort()
    if len(order) != len(branches):
        cycle = sorted(names - set(order))
        return {
            "ok": False,
            "error": "dependency cycle — fix the blocked_by edges",
            "in_cycle": cycle,
        }

    steps: list[str] = []
    for n in order:
        steps.append(f"git merge --no-ff {n}")
        steps.append(f"{gate_cmd}   # gate after {n} — red = stop, dispatch fix")
    steps.append(f"{gate_cmd}   # final full gate on the combined tree")
    steps.append("deploy-reviewer verdict (ALLOW required) before any push/ship")
    return {"ok": True, "merge_order": order, "steps": steps}
