---
name: review-pr
description: >
  Use when preparing your own change for review (self-review, commit hygiene,
  writing the PR description) or when reviewing someone else's pull request for
  correctness, design fit, tests, and blast radius. Triggers on "open a PR",
  "write the PR description", "review this PR", "is this ready to merge",
  "self-review", "squash these commits", "approve".
  Do NOT use for security/trust-boundary review of external code or dependencies
  (that's `secure-code-review` / the `security-reviewer` agent), for the
  test/lint/typecheck gate commands (`run-tests`), or for whether a component
  should exist at all (`new-service` / `architecture-patterns`).
---

# Pull requests: opening one, and reviewing one

## When to use this

The change is written and gated green; now it has to be **communicated and
scrutinized** before it merges. Two modes below — you're either the author
preparing the PR, or the reviewer judging it.

**Not this skill if:** the code came from outside the repo or adds a dependency →
`secure-code-review` first (that's a trust-boundary review, this is a craft
review — do both, security first). You're deciding whether the thing should exist
→ `new-service` / `architecture-patterns`. You're running the gate → `run-tests`.

---

## MODE A — Opening a PR

### 1. Self-review the diff first

Read your **own diff line by line** before anyone else does. Half of all review
comments are things the author would've caught reading their own change cold. Look
for: leftover debug prints, commented-out code, a `TODO` you meant to resolve, a
file you didn't mean to touch, a secret or a hardcoded path.

### 2. Keep it small and single-purpose

One PR = one reviewable idea. A 1,500-line PR gets rubber-stamped because nobody
can hold it in their head; a 150-line PR gets *actually* reviewed. If it's big,
split it — refactor-then-feature as two PRs beats both tangled in one.

### 3. Commit hygiene

Commits tell the story of *how* you got there. Each commit builds and passes;
messages say **why**, not just what 〈imperative subject; body explains the reason〉.
Squash the "fix typo" / "address review" noise before merge.

### 4. Write the PR description — what a reviewer needs, not what git already shows

The diff shows *what changed*. The description must supply what the diff can't:

- **Why** — the problem, linked to the issue/ticket. A reviewer can't judge a
  solution to a problem they have to guess.
- **Approach & alternatives** — the one non-obvious design choice and what you
  rejected. Pre-empts the reviewer's first question.
- **Risk & blast radius** — what could this break, and **how do you roll it back**
  (`ci-cd` §6). Migrations, config, or contract changes get called out explicitly.
- **Test evidence** — what you ran and that it's green (`run-tests`), plus how a
  reviewer can exercise it themselves.
- **Screenshots/logs** for anything user-visible.

## MODE B — Reviewing a PR

> **You are accountable for what you approve.** "LGTM" on code you didn't
> understand is not a review — it's a signature on a blank check. Approve only
> what you can explain.

### Review in this order — highest signal first

1. **Does it do what the PR says it does?** Read the description, then check the
   diff delivers *that*. A correct solution to the wrong problem is still wrong.
2. **Correctness & edges.** The error path, empty input, the boundary, the
   concurrent/duplicate case, the partial failure. **That's where bugs live** — not
   in the happy path the author already tested.
3. **Design fit.** Does it match the repo's layers and idioms? Does it add a
   dependency, a service, or a network hop that needs its own gate
   (`secure-code-review` / `new-service`)? Right-sized, or over-built?
4. **Tests.** Are the new/changed behaviors *actually* tested — asserting outcomes,
   not just executing lines? Missing edge tests is a review comment, not a nit.
5. **Readability.** Will the next person understand this in six months? Names,
   not cleverness. But **match the surrounding code** — don't relitigate the
   repo's style in one PR.

### Comment discipline — say what kind of comment it is

Label severity so the author knows what blocks merge:

- **Blocking** — a correctness/security/design defect. Merge does not happen until
  it's resolved. Explain the *failure*, not just the preference.
- **Suggestion** — a real improvement the author should weigh; not a merge blocker.
- **Nit** — style/taste, explicitly optional. Mark it `nit:` so it's ignorable.

Review the code, **never the person.** "This misses the empty-list case" — not
"you always forget." And when it's good, **say so** — review isn't only defect-finding.

### Before you approve

- [ ] The gate is green (`run-tests`) — CI, not vibes
- [ ] External code / new deps got `secure-code-review` (or the `security-reviewer` agent)
- [ ] You understand every change you're approving; unexplained code is a blocking question
- [ ] Blast radius + rollback are stated and acceptable

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Rubber-stamp `LGTM` | PR too big to hold in head | Author splits it; reviewer requests smaller PRs |
| Bikeshedding on style | Taste dressed up as blocking | Mark taste as `nit:`; block only on defects |
| "Approved" then prod breaks | Reviewed the happy path only | Review edges/errors/concurrency first, happy path last |
| Endless back-and-forth | Design disagreement surfacing at PR time | Escalate to a quick design conversation (`write-design-doc`), don't fight it in comments |
| Reviewer missed a leaked secret / exfil | Craft review used where a security review was needed | Route external code through `secure-code-review` — this skill is not that |

## Definition of done

**As author:** self-reviewed diff · small single-purpose · clean commits · description
covers why/approach/risk/rollback/test-evidence · gate green.

**As reviewer:** confirmed it does what it claims · checked edges before happy path ·
tests assert real behavior · severity-labeled comments · **approved only what you
understand**, with rollback/blast-radius acceptable.
