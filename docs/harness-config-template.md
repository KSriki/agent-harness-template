---
doc: harness-config-template
version: 1.0.0
updated: 2026-08-18
status: active
load: on-trigger
triggers: [setup-harness, harness config, per-repo decisions, update mode, self-heal]
review_after: 2026-11-18
---

# Harness Config — Template (the living per-repo decision record)

> **How to use this:** `setup-harness` copies this file into a target repo as
> `docs/agents/harness-config.md` and fills every `〈slot〉` — by interview for
> decisions, by detection (propose→confirm) for facts. Hand-filling works too.
> Delete the `> GUIDANCE` blocks once used; delete sections that don't apply.
>
> **The three-way rule this doc exists to serve:**
> **interview once for decisions · self-heal mechanics just-in-time · hard-stop
> for dependencies (guardrail 3).** This file records the *decisions* so nothing
> re-asks them; the mechanics (gate.sh, CI workflow, tracker init) are derived
> from it and self-heal when missing.
>
> **This is a LIVING doc.** Every section ends with a `Changelog:` line — append,
> never rewrite. Consumers (orchestrator, planning skills) treat a **stale
> section like a missing one**: each section's *Reality check* names what to
> diff against; drift → propose an amendment (update mode), never silently adopt.

## Repo shape

> GUIDANCE: the one answer that reshapes dispatch: polyrepo means every ticket
> may need a same-named branch in EACH affected repo.

- **Shape:** 〈monorepo | polyrepo (list sibling repos) | single service〉
- **Stack:** 〈Python 3.12 / uv · Go · React+TS · …〉
- **Architecture rung:** 〈modular monolith | …〉 — see `docs/design/`.
- *Reality check:* top-level layout + `git remote -v` still match the shape above.
- Changelog: 〈YYYY-MM-DD — initial (setup-harness)〉

## Tracker

> GUIDANCE: detect from `git remote -v`; agent-heavy/solo → Beads. The tracker
> is the WORK GRAPH only — learnings and run state stay in their own stores.

- **Tracker:** 〈Beads (`bd`) | GitHub (`gh`) | GitLab (`glab`) | `.scratch/` markdown〉
- **Labels:** `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` · `wontfix` 〈or the repo's mapped equivalents〉
- *Reality check:* the tracker above is initialized and reachable (`bd ready` / `gh issue list`).
- Changelog: 〈YYYY-MM-DD — initial (setup-harness)〉

## Gate & coverage

> GUIDANCE: the gate script is the single definition of done — hooks and CI run
> the same file. The floor is honest reality, raised by tickets, never gamed.

- **Gate:** `.claude/gate.sh` — fast: 〈lint cmd〉 · full: 〈format check · typecheck · tests〉
- **Coverage floor:** 〈N〉% 〈— target 〈M〉% when 〈ticket〉 closes〉
- **CI:** `.github/workflows/gate.yml` runs `gate.sh full`; branch protection 〈enabled | TODO〉.
- *Reality check:* the commands above match `.claude/gate.sh` verbatim, and the gate is green on main.
- Changelog: 〈YYYY-MM-DD — initial (setup-harness)〉

## Agent isolation

> GUIDANCE: worktrees are the default (cheap, git-native) — but they isolate
> FILE EDITS only, never the OS: workers share env, credentials, and network
> (two 2026 worktree CVEs; require Claude Code ≥ 2.1.163). OS-level controls are
> the sandbox settings' job. Docker/devcontainer is a rung up — the NAMED
> triggers, per Anthropic's isolation ladder: (a) you pass
> `--dangerously-skip-permissions` / run fully unattended, (b) a worker must
> execute untrusted third-party code or unreviewed deps, (c) you need MCP
> servers/hooks inside the boundary (the Bash sandbox structurally can't).

- **Isolation:** 〈git worktrees (default) | Docker/devcontainer: 〈image/config〉〉
- **Parallel dispatch:** 〈allowed | single-threaded only〉 · ownership boundaries per 〈component registry | AGENTS.md Layout〉
- *Reality check:* the mechanism above is what `orchestrate-agents` runs in this repo.
- Changelog: 〈YYYY-MM-DD — initial (setup-harness)〉

## Business rules

> GUIDANCE: rules the code cannot reveal — compliance, domain invariants, money
> handling, tenancy. NEVER fabricated: every line traces to a human answer.
> Domain *vocabulary* goes to `CONTEXT.md` (domain-modeling), not here.

- 〈e.g. "All money is integer cents — no floats, ever."〉
- 〈e.g. "PII never leaves the EU region; exports go through the redaction service."〉
- *Reality check:* rules still hold as stated; a contradicted rule is an amendment, not a silent edit.
- Changelog: 〈YYYY-MM-DD — initial (interviewed)〉

## Tech limitations

> GUIDANCE: hard constraints agents must not "fix" — pinned versions, forbidden
> dependencies, platform ceilings, external API budgets.

- 〈e.g. "Python pinned ≤3.11 until the vendored wheel supports 3.12."〉
- 〈e.g. "LLM spend: ≤ $X/day; all provider calls via adapters/clients/."〉
- *Reality check:* constraints match reality (pins, budgets, adapters) — a lifted limitation is an amendment.
- Changelog: 〈YYYY-MM-DD — initial (interviewed)〉

---

> **For consumers (orchestrator, planning skills):** no file, or any section
> missing/stale by its Reality check → run that `setup-harness` step
> (propose→confirm→record), then continue. Config is read at dispatch-wave
> boundaries: confirmed amendments reach the next wave; mid-flight workers keep
> their dispatched contract.
