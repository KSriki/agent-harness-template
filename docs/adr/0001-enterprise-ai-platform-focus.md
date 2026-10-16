# ADR-0001: Cut the harness to an enterprise AI-platform focus (GitLab · AKS · Helm · no-egress · Jira)

- **Date:** 2026-10-16
- **Status:** proposed (becomes *accepted* when the human merges this branch)
- **Deciders:** Srikant Kalaputapu (repo owner); drafted by the agent on the branch `harness/enterprise-ai-platform`
- **Related:** `docs/CHANGELOG.md` 2026-10-16 · steering doc v1.1.0 · `docs/agents/work-types.md` 1.1.0

## Context

The template ships ~26 general-purpose skills and 12 agents tuned for a solo,
internet-connected, GitHub-and-Beads workflow with multi-agent fan-out. The
target now is a Devin-style agent in an **enterprise environment** with these
hard facts: no internet in the agent environment; GitLab CI on a shared instance
the agent must not administer or open MRs on; Kubernetes on Azure (AKS) with
Helm/helmfile and podman; servers with no egress; tickets in Jira that change
mid-flight; a culture of ADRs and architecture diagrams in an existing format;
and the job of deploying an AI serving stack (LiteLLM, vLLM, kagent, chat UIs).
The owner is new to Azure. Every skill description costs context on every turn,
so unused generic skills actively degrade routing.

## Decision

We maintain a **focused branch** of the template rather than a flag-driven
profile: nine generic skills and five agents are removed; seven platform skills
are added; four kept skills are rewritten for the environment; AGENTS.md and the
steering doc are pre-filled for the stack. One agent, one ticket, one worktree —
no fleet. The agent writes files the human pastes (MR text, Jira updates); it
never calls GitLab or Jira.

| Removed | Why |
|---|---|
| `orchestrate-agents`, `orchestrator` agent, `frontend-`/`backend-implementer`, `docs/multi-agent-orchestration.md` | Worktree fan-out is a Claude Code mechanism; the target runs one agent per ticket. Web-stack worker variants have no stack to serve. `orchestrator_engine/` stays as the model registry `harness_lint` checks |
| `debug-research` (skill + agent), `trend-scout`, `premise-reviewer` | All three fetch from the internet; the environment has none. grill-me's premise round now runs offline from ADRs and the human's knowledge |
| `codebase-design`, `improve-codebase-architecture`, `domain-modeling`, `new-service` | App-code module design; the ladder check lives in the steering doc; ADRs get their own skill |
| `graphify`, `wayfinder`, `wait-what`, `harness-help` | External CLI / decision-mapping / UX conveniences with no named failure here |

| Added | Owns |
|---|---|
| `adr` | one decision → `docs/adr/NNNN` (adapted from ECC, MIT) |
| `architecture-diagrams` | diagrams matching the repo's existing format; offline rendering |
| `helm-charts` | chart authoring, validation ladder, versioning, OCI publish, helmfile |
| `kubernetes-ops` | workload manifests, GPU scheduling, NetworkPolicy, triage (adapted from ECC, MIT) |
| `azure-platform` | Azure mental model for newcomers, identity, AKS, private networking |
| `air-gapped-delivery` | images/charts/models/wheels into the no-egress estate by digest |
| `ai-serving-stack` | vLLM sizing, LiteLLM gateway, kagent, chat UIs |
| `ticket-docs` | `tickets/<KEY>.md` mirror of the Jira ticket + paste block |

| Rewritten | Change |
|---|---|
| `ci-cd` | GitLab-native; agent edits YAML only, humans own Settings |
| `review-pr` | small commits from the ticket plan; writes `tickets/<KEY>.mr.md`; never opens an MR |
| `prd-to-issues` | emits ticket docs, not tracker issues |
| `grill-me` | offline premise round |

## Alternatives considered

### Keep one branch, add an "enterprise profile" flag to `init.py`
- Pros: one codebase, no drift between branches.
- Cons: every skill description still loads in every profile unless the installer
  deletes files, which is the same cut done at install time with more machinery.
- Why not: the owner asked for a branch; a profile is a later refactor if two
  variants need to coexist on one machine.

### Keep the research agents with a "no network" note
- Pros: nothing to delete.
- Cons: their whole procedure is fetching; descriptions that never fire dilute routing.
- Why not: dead skills are the #1 mis-routing cause (ARCHITECTURE.md).

### Add a GitLab-API skill with a hard confirmation gate
- Pros: the agent could open MRs.
- Cons: shared instance; the owner explicitly wants to open MRs manually.
- Why not: an owner constraint, recorded in AGENTS.md "Environment facts".

### Use Beads for tickets as the template does
- Why not: the team's tracker is Jira; the agent cannot write to it by default, so
  the design is a local ticket doc + paste block.

## Consequences

**Positive:** skill descriptions in always-on context drop from 26 to 24 while
every one of them is relevant; routing between Helm / k8s / Azure / delivery is
explicit via NOT-clauses; the shared-environment rules are stated once in
AGENTS.md and enforced by three skills.

**Negative / cost:** the branch will drift from `main`; merges of upstream
template improvements need a human eye on the removed files. `orchestrator_engine/`
carries dead code paths (`research.py` dispatch names) kept only so `harness_lint`
and the gate stay green. The evals under `evals/golden/premise-*` still describe
the removed premise-reviewer and are now historical.

**Risks and mitigations:** Azure/kagent/LiteLLM facts in the new skills were
written without internet and may lag the installed versions — every skill says
"verify against the installed version" where it matters; `evolve-harness` is the
path to correct them. Mitigate drift by re-running `python3 -m harness_lint .`
and the gate after every upstream merge.

**Follow-ups:** fill AGENTS.md slots in the first target repo via `setup-harness`;
remove or rewrite the premise-* eval suites; decide whether `orchestrator_engine/`
should be reduced to `models.py` (separate ADR).
