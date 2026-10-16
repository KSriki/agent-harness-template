# Intent — the enterprise skill cut (grill-me, 2026-10-16)

**Originator:** repo owner. **Scope:** branch `harness/enterprise-ai-platform`.

## Problem (in the owner's words)

"I need a branch of my agent-harness-template with a reduced amount of skills"
for a Devin-based enterprise environment: GitLab, Kubernetes, Helm/helmfile,
podman, servers with no internet, Jira. The environment has no web access, takes
credentials from the terminal, is a shared repo where the agent must not open MRs
or touch GitLab settings, and tickets change acceptance criteria mid-flight.
Definite needs: `tdd`, architecture + diagrams matching an existing format,
splitting work into steps and committing small changes, a living ticket document.

## Proposed outcome

A branch whose skills are all offline-capable and all fire for this team's work:
12 skills dragged by hand into `.devin/skills/`, 3 maintainer-only skills kept on
the branch, product and cloud names absent from the repo, the serving-stack
specifics built inside the environment from a template.

## Decisions made (rounds 1–3)

- Skills loading: Devin reads `.devin/skills/`; the owner drags folders by hand. No installer changes.
- Jira is the spec of record → `write-a-prd` dropped; `ticket-docs` holds the living ticket (AC, plan = commits, changes log, Jira paste) **and** the splitting procedure (steps → commits; story → epic with child docs) → `prd-to-issues` dropped.
- Platform team owns the cluster, the mirror, and CI/releases → `azure-platform`, `air-gapped-delivery`, `ci-cd` dropped. The agent applies only to the testing namespace, from the testing env, after the human pulls the branch.
- The team uses models, does not evaluate them → `eval-harness` dropped.
- `architecture-patterns` dropped (overkill); `adr`, `write-design-doc`, `architecture-diagrams` kept. Pattern docs stay on disk as reference.
- `handoff` dropped (sessions not cut; ticket docs are the resumable state).
- `observability` kept (team owns monitoring via its own service).
- `tdd` + `run-tests` both kept (build-first vs run-the-gate).
- `secure-code-review`, `grill-me` (offline premise round), `review-pr` (small commits, `tickets/<KEY>.mr.md`, never opens the MR) kept.
- Product/cloud names scrubbed; generic tooling names kept; "no internet" posture kept. The serving-stack skill becomes `docs/templates/serving-stack-skill.md` with a grill-me question set, instantiated in the env.
- Git boundary: nothing reaches `origin` without the human approving that specific action (no push, remote branch/tag, fetch/pull unless asked). Humans cut releases.
- helmfile secret inputs: `vals` + `--state-values-set`; the owner fills the exact invocation in the env.

## Constraints

No internet in the agent env · shared GitLab, read-only to the agent · Jira written by the human · platform team owns cluster/mirror/CI · repo is private but keeps product specifics out.

## Kill criteria (this cut was a bad idea if…)

1. Within the first two tickets the agent needs a removed procedure more than once → restore that skill.
2. The agent keeps opening `kubernetes-ops` when `helm-charts` was meant, or vice versa → merge them.
3. The scrubbed skills read too generic to act on → specifics go into env-local copies, never back into the branch.

## Open questions

- Exact `.devin/skills/` loading semantics (does Devin read `AGENTS.md` at the repo root?) — owner to confirm in the env.
- Whether `orchestrator_engine/` should shrink to `models.py` (separate ADR).
