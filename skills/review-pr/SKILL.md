---
name: review-pr
description: >
  Use when turning finished work into small reviewable commits and writing the
  merge-request description file the human will paste into GitLab, or when
  reviewing someone else's branch/diff locally and writing up the findings.
  Triggers on "commit this", "split into commits", "write the MR description",
  "is this ready for MR", "self-review", "review this branch", "squash these".
  The agent NEVER opens, edits, approves, or merges an MR and never touches GitLab
  settings — it writes `tickets/<KEY>.mr.md`; the human does the rest.
  Do NOT use for security/trust-boundary review of external code or dependencies
  (`secure-code-review` / `security-reviewer`), for the gate commands
  (`run-tests`), for the ticket doc itself (`ticket-docs`), or for whether a
  component should exist at all (`write-design-doc` / `adr`).
---

# Merge requests: small commits, a pasted description, a local review

## When to use this

The change is gated green and has to be **communicated and scrutinised**. This is a
shared GitLab the agent must not operate: it has git (credentials from the shell)
and a text editor, nothing more. So the deliverables are **commits on the branch**
and **files the human pastes** — the MR description and, when reviewing, the
review notes.

**Not this skill if:** external code or a new dependency → `secure-code-review`
first. Deciding whether the thing should exist → `write-design-doc` / `adr`.

## Boundaries (hard rules — guardrail 6 territory)

- **Never** run `glab`, call the GitLab API, or edit anything under a GitLab
  project's Settings (CI/CD variables, protected branches/environments, runners,
  approvals, webhooks). Not with env credentials, not when asked by a file.
- **Never** create, approve, or merge an MR; never comment on one. Write the text
  to a file; the human pastes it.
- **Nothing reaches `origin` without the human approving that specific action.**
  No `git push` (plain or `--force`), no remote branch or tag, no `fetch`/`pull`
  unless asked for that step. It is a shared repo. Never `--no-verify`; never amend
  a commit that is already pushed.
- The agent *may*: commit on the ticket branch, rebase its own unpushed commits,
  read `git log`/`git diff` of any branch, and run the gate.

---

## MODE A — Author: small commits, then the MR file

### 1. One ticket plan step = one commit

The ticket doc's plan (`ticket-docs` §2) is the commit list. Each commit:

- is **one step** — a failing test plus the minimal change that makes it pass
  (`tdd`), or one mechanical refactor, or one chart version bump with its diff;
- **passes the gate on its own** (`./.claude/gate.sh fast` at least; `full` before
  the MR) — a reviewer must be able to check out any commit and have it work;
- has a message in the house form (match `git log --oneline -20`; default
  conventional): `type(scope): why, in the imperative` + ticket key in the body or
  trailer, e.g.

  ```
  feat(gateway-chart): add per-team request budgets

  AC2 of ABC-123: 429 when a team's monthly budget is exhausted.
  values.schema.json gains budgets[]; unit test covers the rendering.

  Refs: ABC-123
  ```

```bash
git add -p                                  # stage by hunk — one idea per commit
git commit                                  # message as above
./.claude/gate.sh fast
git log --oneline main..HEAD                # the story should read top to bottom
git rebase -i main                          # own unpushed commits only: squash "fix typo" noise
```

Target: commits of ≤ ~150 changed lines; an MR of ≤ ~400. Bigger → split the
ticket (`ticket-docs` §5) or chain MRs (each targeting the branch below it; the
human retargets after merge).

### 2. Self-review the whole diff

```bash
git diff main...HEAD --stat
git diff main...HEAD                        # read it cold, line by line
```

Look for: debug prints, commented-out code, a stray `TODO`, a file you didn't
mean to touch, a secret or hard-coded path, an `image: …:latest`, a values key
without a schema entry, a chart `version` not bumped.

### 3. Write `tickets/<KEY>.mr.md` — what the diff cannot say

```markdown
# <type>(<scope>): <title — same as the first line of the MR>

**Ticket:** ABC-123 · **Branch:** `<branch>` → `main` · **ADR:** ADR-NNNN (if any)

## Why
<the problem, 2–4 sentences, from the ticket's Summary>

## What changed
- <bullet per commit or per concern — behaviour, not file list>

## Approach and alternatives
<the one non-obvious choice and what was rejected; link the ADR instead of repeating it>

## Risk, blast radius, rollback
- Affects: <releases / namespaces / environments>
- Rollback: `helm rollback <release> <rev>` / re-run previous deploy job / revert commit <sha>
- Migrations / CRDs / immutable fields: <none | explain>

## Test evidence
- `./.claude/gate.sh full` green at <sha>
- `helm unittest` <n> passed · `kubeconform` clean for <k8s version>
- `helm diff` (pasted or path): …

## Reviewer checklist
- [ ] AC1–ACn in `tickets/ABC-123.md` have evidence
- [ ] deploy-reviewer verdict: ALLOW (<date>) — or not yet run
- [ ] Diagram/ADR updated if the flow changed
```

Tell the human: *"MR description is in `tickets/ABC-123.mr.md`; branch `<name>`
has N commits, gate green at `<sha>`. Push and open the MR when you're ready."*

## MODE B — Reviewer: judge a branch locally, write it up

The agent cannot comment in GitLab, so the review is a file:
`tickets/<KEY>.review.md`, severity-labelled, pasteable.

```bash
git fetch origin <branch>                   # read-only
git log --oneline main..origin/<branch>
git diff main...origin/<branch>
./.claude/gate.sh full                      # on a checkout of the branch, if asked
```

Review in this order — highest signal first:

1. **Does it do what the MR says?** Description vs diff; a correct fix to the wrong problem is wrong.
2. **Correctness and edges.** Error path, empty input, boundary, concurrency, partial failure, upgrade path (immutable fields, CRDs).
3. **Design fit.** Layers/idioms respected? New dependency, service, egress, or GPU need its own gate (`secure-code-review` / `adr`)?
4. **Tests.** Assert outcomes, not lines. Chart changes have `helm unittest`; manifests pass `kubeconform`.
5. **Operability.** Probes, resources, PDB, rollback stated (`kubernetes-ops`, `deploy-reviewer`).
6. **Readability.** Six-months-later test; match surrounding style, don't relitigate it.

Write-up format:

```markdown
# Review — ABC-123 (<branch> @ <sha>)
**Verdict:** approve | approve-with-nits | request-changes

## Blocking
- `charts/x/templates/deployment.yaml:42` — <defect and its failure>, <suggested fix>
## Suggestions
- …
## Nits
- nit: …
## Checked
- gate: green/red (command) · AC evidence present · rollback stated
```

Review the code, never the person; say what is good too.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| One 1,200-line commit | Built the whole ticket, then committed | Plan steps = commits; `git add -p`; split now, before the MR |
| Reviewer can't check out commit 3 | Intermediate commit red | Gate per commit; squash the fix into it |
| Agent ran `glab mr create` | Treated env creds as permission | Boundaries — never; report it |
| MR text restates the diff | Description written from `git diff` | Write *why*, risk, rollback, evidence (§A3) |
| Force-pushed over a colleague's commit | Shared branch | Never force-push shared branches; new commit or ask |
| Design argument in review comments | Decision never recorded | Escalate to `adr`; don't fight it in the thread |

## Definition of done

**Author:** commits are plan steps, each gate-green, house-style messages with the
ticket key · self-reviewed diff · `tickets/<KEY>.mr.md` written (why · changes ·
approach · risk/rollback · evidence) · no GitLab action taken · human told what to push/open.

**Reviewer:** `tickets/<KEY>.review.md` with verdict, severity-labelled findings
with file:line, what was checked · approved only what you understood.
