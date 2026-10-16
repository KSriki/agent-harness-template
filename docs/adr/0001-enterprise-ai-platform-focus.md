# ADR-0001: Cut the harness to an enterprise AI-platform focus (GitLab · Kubernetes · Helm · no-egress · Jira)

- **Date:** 2026-10-16 (second cut, same day, after a `grill-me` session — see `intent/enterprise-skill-cut.intent.md`)
- **Status:** proposed (becomes *accepted* when the human merges this branch)
- **Deciders:** Srikant Kalaputapu (repo owner); drafted by the agent on the branch `harness/enterprise-ai-platform`
- **Related:** `intent/enterprise-skill-cut.intent.md` · `docs/CHANGELOG.md` 2026-10-16 · steering doc v1.2.0 · `docs/agents/work-types.md` 1.2.0 · `docs/templates/serving-stack-skill.md`

## Context

The template ships ~26 general-purpose skills and 12 agents tuned for a solo,
internet-connected, GitHub-and-Beads workflow with multi-agent fan-out. The
target is a Devin-based agent in an **enterprise environment**: no internet in
the agent environment; a shared GitLab the agent must not administer or open MRs
on; a Kubernetes cluster, internal registry, CI, and releases all **owned by a
platform team** — the agent renders locally and applies only to a testing
namespace, from a testing environment, after the human pulls the branch; Helm with
helmfile and secret render inputs; tickets in Jira whose acceptance criteria
change mid-flight; a culture of ADRs and architecture diagrams in an existing
format. The repo is private but the owner wants product and vendor names kept out
of it. Every skill description costs context on every turn, so skills that never
fire degrade routing.

## Decision

We maintain a **focused branch**. Twelve skills ship (dragged by hand into the
environment's `.devin/skills/`), three stay maintainer-only, everything else is
removed. Product and cloud names are absent; the serving-stack specifics are
built inside the environment from a template plus a `grill-me` question set.
One agent, one ticket, one worktree. The agent writes files the human pastes (MR
text, Jira updates) and nothing reaches `origin` without the human approving that
specific action.

| Ships | Owns |
|---|---|
| `tdd`, `run-tests` | build test-first; the gate |
| `helm-charts` | chart authoring, validation ladder, versioning, helmfile + its secret inputs (slot) |
| `kubernetes-ops` | workload manifests, GPU scheduling, NetworkPolicy, triage in the testing namespace (adapted from ECC, MIT) |
| `review-pr` | small commits from the ticket plan; `tickets/<KEY>.mr.md`; local review notes; never touches `origin` |
| `ticket-docs` | `tickets/<KEY>.md` mirror of the Jira ticket; AC changes; splitting (steps → commits, story → epic); Jira paste |
| `grill-me` | offline premise round + frontier rounds; its intent doc feeds `ticket-docs` |
| `adr`, `write-design-doc`, `architecture-diagrams` | record · design · draw in the house format |
| `secure-code-review`, `observability` | trust boundaries; the team's own monitoring |

| Removed | Why |
|---|---|
| `orchestrate-agents`, `orchestrator`, `frontend-`/`backend-implementer` | one agent per ticket; worktree fan-out is a Claude Code mechanism |
| `debug-research` (skill + agent), `trend-scout`, `premise-reviewer` | they fetch from the internet; there is none |
| `ci-cd` | CI and releases are the platform team's; the owner does not cut releases |
| `air-gapped-delivery`, `azure-platform` | the platform team owns mirroring and the cloud; the owner needs no cloud skill |
| `ai-serving-stack` | names products; rebuilt in the env from `docs/templates/serving-stack-skill.md` |
| `write-a-prd`, `prd-to-issues` | Jira is the spec of record; splitting moved into `ticket-docs` |
| `eval-harness` | the team uses models, it does not evaluate them |
| `architecture-patterns` | app-architecture pattern KB — overkill; the ladder lives in the steering doc, docs stay as reference |
| `codebase-design`, `improve-codebase-architecture`, `domain-modeling`, `new-service` | app-code module design |
| `graphify`, `wayfinder`, `wait-what`, `harness-help`, `handoff` | no named failure here; ticket docs are the resumable state |

Maintainer-only (on the branch, not in the env): `setup-harness`, `evolve-harness`,
`writing-for-agents`, `_TEMPLATE`.

## Alternatives considered

### One branch with an install-profile flag
- Pros: no drift between branches.
- Why not: the owner drags folders by hand and asked for a branch; a profile is a
  later refactor if two variants must coexist on one machine.

### Keep the research agents with a "no network" note
- Why not: their whole procedure is fetching; descriptions that never fire are the
  #1 mis-routing cause.

### Keep `ci-cd` as "validation jobs only"
- Why not: the owner does not own CI or releases; the one thing it would say
  ("humans run the pipeline") now lives in AGENTS.md's environment facts.

### Ship the serving-stack skill with product names
- Why not: the owner wants the repo free of product specifics; the template plus
  grill-me rebuilds it in the env in one session.

### Beads / GitLab issues for tickets
- Why not: the tracker is Jira and the agent cannot write to it by default; the
  design is a local ticket doc + paste block.

## Consequences

**Positive:** every shipped description is relevant; the shared-environment rules
(no `origin` writes, no GitLab/Jira API, testing namespace only) are stated once
in AGENTS.md and enforced by `review-pr`, `ticket-docs`, `kubernetes-ops`,
`helm-charts`; the repo carries no product fingerprint.

**Negative / cost:** the branch drifts from `main`; upstream merges need a human
eye on the removed files. `orchestrator_engine/` carries dead dispatch names
(`research.py`) kept so `harness_lint` and the gate stay green. The
`evals/golden/premise-*` suites describe a removed agent and are historical. The
scrubbed skills are more generic than the first cut; the env-local serving-stack
skill carries the specifics.

**Risks and mitigations:** generic wording may be too thin to act on → kill
criterion 3 (specifics go into env-local copies). Helm/Kubernetes facts were
written without internet → every skill says "verify against the installed
version" where it matters.

**Follow-ups:** fill AGENTS.md slots in the first target repo; build
`serving-stack` in the env from the template; remove or rewrite the premise-*
eval suites; decide whether `orchestrator_engine/` shrinks to `models.py`
(separate ADR).
