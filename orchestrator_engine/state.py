"""The state registry — per-project machine state for an orchestrated run.

<target-repo>/.orchestrator/state.json   run, workers, status, spend
<target-repo>/product-docs/PRODUCT.md    scaffolded once; the resume anchor
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

STATE_DIR = ".orchestrator"

PRODUCT_TEMPLATE = """# {goal}

**Started:** {date} · the RESUME ANCHOR: maintained by the orchestrator at the end
of every run; humans edit freely. "Continue this product" starts by reading this file.

## Product status

- Lifecycle: 〈DISCOVERY | BUILD | OPERATE〉
- Work type: {work_type}
- Repository strategy: 〈monorepo | polyrepo (N repos)〉 — components in REGISTRY.md
- Tracker: 〈GitHub Issues · JIRA key · .scratch/ local〉
- Dev image: 〈container:tag, if any〉

## Git workflow

- Branches: 〈main (prod-ready) ← develop (integration) ← feature/bugfix/chore〉
- Naming: 〈feature|bugfix|chore/TICKET-NNN-short-desc〉
- Commits: 〈TICKET-NNN: type(scope): message〉
- Flow: 〈branch → build → PR to develop → squash-merge → delete branch;
  never commit directly to develop〉
- Cross-repo rule (polyrepo): 〈every ticket gets a same-named branch in EACH
  affected repo〉

## Product description

(what it is and for whom — sharpened as it's learned)

## Pipeline state

- Current stage: 〈stage / ticket frontier〉
- Last completed: 〈…〉
- Completed this session: (orchestrator appends before exiting)

## Gate history

<!-- Human approval gates. Verdicts: approved · approved-with-changes · rejected. -->

| Gate | Stage | Date | Verdict | Conditions |
|---|---|---|---|---|
| 〈G1〉 | 〈vision〉 | 〈date〉 | 〈approved-with-changes〉 | 〈e.g. "arch must support both supervisor AND hierarchical routing, config-driven"〉 |

## Decision log

<!-- The dated INDEX of decisions, one line each — the full record lives in the
     design doc / ADR it links to (reference, don't restate). -->

1. 〈date〉 — 〈gate GN | feature | bugfix〉 — 〈verdict〉 — 〈one-line gist + link to ADR/design doc〉

## Next

-
"""

VISION_TEMPLATE = """# {goal} — Product Vision

**Version:** 0.1 · {date} · **Owner: the human.** The orchestrator and workers
read this; they never rewrite it.

## Vision statement

〈What this product IS and the bet it makes — a paragraph, not a feature list.〉

## Target users & personas

- 〈persona〉 — 〈what they do · what they need · a question they'd literally ask〉

## Architectural constraints (from the product owner)

- 〈constraints the design MUST honor — e.g. "orchestration pattern is
  config-selectable at runtime: supervisor AND hierarchical"〉

<!-- This anchors grill-me / write-a-prd; the constraints here bind every design
     doc downstream. -->
"""

REGISTRY_TEMPLATE = """# Component Registry

## Repository strategy

- **Type:** 〈monorepo | polyrepo (N repos)〉
- **Root:** {root}
- **Product docs:** {root}/product-docs

## Repositories

| Repo | Path | Remote | Stack | Deploy target |
|---|---|---|---|---|
| 〈name〉 | 〈path〉 | 〈git remote / local〉 | 〈Python/uv · Go · React+TS〉 | 〈where it ships〉 |

## Components

| Component | Type | Repo | Path | Status | Owner |
|---|---|---|---|---|---|
| 〈api-core〉 | 〈config, auth, DB, middleware〉 | 〈repo〉 | 〈api/core/〉 | 〈planned / building / complete〉 | 〈backend-implementer〉 |

<!-- The Components table IS the ownership-boundary map: Owner = the worker agent
     responsible for that path. Dispatch reads it; workers stay inside their row.
     The orchestrator updates Status as slices land. Humans edit freely — this is
     a catalog, not machine state (.orchestrator/state.json is the machine state). -->
"""


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class Registry:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self.path = self.root / STATE_DIR / "state.json"

    def load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {
            "run": None,
            "status": "idle",
            "workers": [],
            "spend_usd": 0.0,
            "updated": None,
        }

    def save(self, data: dict) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data["updated"] = _now()
        self.path.write_text(json.dumps(data, indent=2) + "\n")
        return data

    def init_run(
        self, goal: str, work_type: str, budget_usd: float | None = None
    ) -> dict:
        """Start (or restart) a run. Scaffolds product-docs/PRODUCT.md if absent."""
        data = self.load()
        data.update(
            {
                "run": {
                    "goal": goal,
                    "work_type": work_type,
                    "started": _now(),
                    "budget_usd": budget_usd,
                },
                "status": "running",
                "workers": [],
                "spend_usd": 0.0,
            }
        )
        docs = self.root / "product-docs"
        product = docs / "PRODUCT.md"
        if not product.exists():
            docs.mkdir(parents=True, exist_ok=True)
            product.write_text(
                PRODUCT_TEMPLATE.format(
                    goal=goal, date=_now()[:10], work_type=work_type
                )
            )
        registry_md = docs / "REGISTRY.md"
        if not registry_md.exists():
            docs.mkdir(parents=True, exist_ok=True)
            registry_md.write_text(
                REGISTRY_TEMPLATE.format(root=str(self.root.resolve()))
            )
        vision = docs / "docs" / "vision" / "product-vision.md"
        if not vision.exists():
            vision.parent.mkdir(parents=True, exist_ok=True)
            vision.write_text(VISION_TEMPLATE.format(goal=goal, date=_now()[:10]))
        (docs / "docs" / "sprints").mkdir(parents=True, exist_ok=True)
        return self.save(data)

    def upsert_worker(
        self,
        name: str,
        slice_: str,
        branch: str | None = None,
        status: str = "dispatched",
    ) -> dict:
        data = self.load()
        for w in data["workers"]:
            if w["name"] == name and w["slice"] == slice_:
                w.update(
                    {
                        "branch": branch or w.get("branch"),
                        "status": status,
                        "updated": _now(),
                    }
                )
                break
        else:
            data["workers"].append(
                {
                    "name": name,
                    "slice": slice_,
                    "branch": branch,
                    "status": status,
                    "updated": _now(),
                }
            )
        return self.save(data)

    def add_spend(self, usd: float) -> dict:
        data = self.load()
        data["spend_usd"] = round(data.get("spend_usd", 0.0) + usd, 4)
        return self.save(data)

    def set_status(self, status: str, reason: str | None = None) -> dict:
        data = self.load()
        data["status"] = status
        if reason:
            data["status_reason"] = reason
        return self.save(data)
