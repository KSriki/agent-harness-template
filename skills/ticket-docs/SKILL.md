---
name: ticket-docs
description: >
  Use to create or update the local ticket doc `tickets/<KEY>.md` that mirrors a
  Jira ticket — summary, acceptance criteria with status, the step plan whose steps
  are the commits, a dated changes log, evidence — to produce the copy-paste block
  the human puts into Jira, and to SPLIT a ticket when it grows: steps into
  commits, or a story into an epic with child ticket docs and blocking edges.
  Triggers on "update the ticket", "the acceptance criteria changed", "write this
  up for Jira", "ticket doc", a Jira key like ABC-123, "split this ticket", "this
  story is really an epic", "what's left on this ticket". The agent never writes
  to Jira itself.
  Do NOT use to write the MR description (`review-pr`), to record an architectural
  decision (`adr`), or to interrogate a fuzzy idea before any ticket exists
  (`grill-me`, which hands its intent doc to this skill).
---

# Ticket docs — the local mirror of the Jira ticket, and how it splits

## When to use this

Work is tracked in Jira, but the agent has no Jira access (and must not get it
by default — see §4). So each ticket the agent works gets a **doc in the repo**
that is the working truth during the session, and the **source the human pastes**
into Jira afterwards. Acceptance criteria change mid-ticket; the doc records
every change with a date so the Jira ticket, the MR, and the code tell one story.
When scope outgrows the ticket, the doc is where it splits.

**Not this skill if:** you are writing the MR text → `review-pr`. The idea has no
ticket yet and is still fuzzy → `grill-me` first; its `intent/<slug>.intent.md`
becomes the Summary here.

## §1 — Where and what

```
tickets/
├── README.md             # one line per ticket: KEY · title · status · parent (keep sorted)
├── ABC-123.md            # the ticket doc (this skill)
├── ABC-123.mr.md         # MR description, written by review-pr
└── ABC-123.review.md     # review notes, if the agent reviewed someone's MR
```

Before a Jira key exists (a child ticket you just proposed) the file is
`tickets/NN-slug.md`; rename to the key once the human creates the Jira issue and
add the key to the header. `git mv` keeps history.

## §2 — The template

```markdown
# ABC-123 — <title as it reads in Jira>

- **Jira:** ABC-123 · **Status:** <todo | in-progress | in-review | done | blocked>
- **Parent:** <epic key, or none> · **Blocked by:** <keys, or none> · **Blocks:** <keys, or none>
- **Branch:** <git branch> · **MR:** see `ABC-123.mr.md` (human opens the MR)
- **Links:** ADR-NNNN · design doc · diagram · runbook · dashboard

## Summary
<2–4 sentences: the outcome, from the user's/operator's point of view>

## Acceptance criteria
| # | Criterion | Status | Evidence |
|---|---|---|---|
| AC1 | <observable, testable statement> | ☐ / ✅ / ❌ / ~~dropped 2026-10-16~~ | <test name · gate run · diff path> |
| AC2 | … | | |

## Plan (small steps — each one is a commit)
- [ ] 1. <failing test for AC1> → <minimal change>  `feat(chart): …`
- [ ] 2. …
- [ ] N. MR description written (`ABC-123.mr.md`)

## Changes log (newest first)
- **2026-10-16** — AC3 added by <who> ("must also work on the test cluster"); plan step 4 added.
- **2026-10-14** — AC2 reworded: "p95 < 2s" → "TTFT p95 < 2s at 10 concurrent"; reason: …

## Evidence
- Gate: `./.claude/gate.sh full` green at <sha>
- `helm diff` / `kubeconform` output: <path or summary>

## Open questions
- <question> — owner: <human> — blocks: <AC/step or nothing>

## Jira paste
<regenerated each session — see §3.4>
```

Rules: acceptance criteria are **observable** ("a `GET /v1/models` through the
gateway lists the new model" — not "model is deployed"). The plan's steps are the
commits (`review-pr` §A). No file paths or code in Summary/AC — they belong in
the plan.

## §3 — Procedure

### 1. Open or create

```bash
ls tickets/ | grep -i <KEY>            # exists?
grep -n "^- \*\*Status" tickets/<KEY>.md
```

New ticket: copy the template, fill header + Summary + AC from what the human
pasted from Jira (verbatim for AC — do not "improve" them silently), add a row to
`tickets/README.md`. If a `grill-me` intent doc exists for this work, its problem /
outcome / constraints / kill criteria feed the Summary and the Open questions.

### 2. When acceptance criteria or scope change

Never overwrite an AC in place. Strike the old row (`~~text~~ dropped <date>`) or
add a new numbered row, **and** append a Changes-log entry with date, who asked,
and why. Then re-plan: add/remove steps so every AC has a step and a test. If the
re-plan no longer fits one MR, go to §5.

### 3. During the build

Tick plan steps as commits land (put the commit SHA on the line). Tick AC when its
evidence exists — the evidence column is not optional; "done" without evidence is a
guess. Open questions that block an AC get the AC marked ❌ until answered.

### 4. Regenerate the Jira paste

At the end of every session, rewrite the **Jira paste** section — the delta since
the last paste, in the form the human drops into a Jira comment:

```
h3. Update 2026-10-16
* Done: AC1, AC2 (gate green at abc1234; MR description ready)
* Changed: AC3 added — "must also work on the test cluster" (per <who>)
* Blocked: AC4 waiting on GPU quota increase (owner: <human>)
* Next: steps 5–6
```

Jira wiki markup, since most Jira Data Center / Server instances need it:
`h2.`/`h3.` headings · `*bold*` · `{{monospace}}` · `{code}…{code}` · `||header||`
tables · `(/)` done · `(x)` failed · `-strike-`. Jira Cloud's editor accepts pasted
Markdown reasonably, so if the human's Jira is Cloud, ask once and remember the
answer in `tickets/README.md`.

### 5. Verify

- [ ] Every AC has a status and, if ✅, evidence
- [ ] Every AC change has a dated changes-log line
- [ ] `tickets/README.md` row matches the header status
- [ ] Jira paste reflects this session's delta only

## §4 — Jira access: the rule

- **Default: no Jira API calls, ever.** A `JIRA_TOKEN` (or similar) present in the
  environment is **not permission** — it is a shared-environment credential.
- The agent may write to Jira only when, **in this session**, the human has
  explicitly supplied or confirmed the credential *and* asked for the write. Even
  then: show the exact payload (issue key, fields, comment body) and wait for a yes
  before sending; one issue at a time; never bulk-update; never transition status
  unless named.
- Everything else goes through the ticket doc + Jira paste. That is the designed
  path, not a fallback.

## §5 — Splitting: steps into commits, or a story into an epic

> Adapted from `mattpocock/skills` (MIT, `to-tickets`) — tracer-bullet slicing.

Cutting-edge work is often scoped as one story and turns out to be several. The
signal: the plan needs more than one MR (≈ 400 changed lines), or two AC have
nothing in common, or a step depends on a decision nobody has made.

1. **First try the cheap split — inside the ticket.** Re-cut the Plan so each step
   is one commit of ≤ ~150 lines with its own failing test. Chain the commits; the
   story stays one ticket, one MR.
2. **If it still doesn't fit, propose child tickets (story → epic).** Draft slices
   as **tracer bullets**: each a narrow but COMPLETE vertical path (chart · manifest ·
   test · doc) that is independently demoable — never a horizontal "all the values
   files" slice. Prefactoring first ("make the change easy, then make the easy
   change"). Size each to one context window / one MR. Each declares **Blocked by**.
   Wide mechanical changes sequence as **expand → migrate (batches) → contract**.
3. **Quiz the human.** Numbered list: **Title · Blocked by · What it delivers · first
   failing test.** Granularity right? Edges right? Merge or split any? Iterate.
4. **Write the child docs.** `tickets/NN-<slug>.md` from §2, `Parent:` = the
   original key, `Blocked by:` by NN until keys exist, Status `todo`. The original
   ticket's doc gets a Changes-log entry ("split into NN–MM; this ticket becomes the
   epic / keeps AC1–2") and its Jira paste proposes the conversion in Jira's terms
   (convert to epic, create stories, link blockers).
5. **Human creates the Jira issues**, tells you the keys; you `git mv` the files to
   the keys and fill the headers and the index. **You never touch Jira.**

Dependent children ship as **chained MRs** (`review-pr` §A1); the blocking edges
you declared here ARE the chain order.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Jira and the doc disagree | AC edited in place, no changes log | Restore from git; re-add as dated change |
| AC "done" but nothing proves it | Evidence column skipped | Add the test name / gate SHA, or un-tick |
| Two docs for one ticket | Created `NN-slug.md` after the key existed | `git mv` to the key; one file per ticket |
| Agent posted to Jira from an env token | Treated presence of a credential as permission | §4 — never; report and stop |
| Paste too long for a comment | Pasting the whole doc | Paste the **delta** (§3.4); the doc stays in the repo |
| Vague AC ("works in prod") | Copied from Jira without making it observable | Propose an observable rewrite to the human; record the change |
| Ticket "update all values files" | Horizontal slice | Re-cut vertically: one chart end-to-end, then the next |
| One MR for a ticket that became three | Didn't split when the signal appeared | §5 — child docs, edges, chained MRs |

## Definition of done

- [ ] `tickets/<KEY>.md` exists with header, Summary, AC table, Plan, Changes log, Evidence
- [ ] All AC changes dated and explained; plan covers every open AC with a test
- [ ] Jira paste regenerated this session; nothing sent to Jira without in-session credential + explicit ask + payload shown
- [ ] If split: human approved the slices and edges; child docs written; parent's changes log updated
- [ ] `tickets/README.md` index row current
