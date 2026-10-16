---
name: adr
description: >
  Use to record ONE architectural decision as a numbered ADR under `docs/adr/`
  (context, decision, alternatives, consequences, index entry), or to look up why
  something is the way it is by reading the existing ADRs. Triggers on "ADR this",
  "record this decision", "why did we choose X", "which ADR covers Y", "supersede
  ADR-0007", a chart/cluster/model-serving choice being settled in conversation, or
  an MR that changes infrastructure shape without a decision record.
  Do NOT use for a multi-page design of a new system or subsystem — that is
  `write-design-doc` (which may spawn several ADRs); not for CHOOSING the pattern —
  `write-design-doc`; not for the ticket's acceptance criteria — `ticket-docs`.
metadata:
  origin: adapted from ECC `architecture-decision-records` (MIT, affaan-m/ECC) — reshaped to this harness's style
---

# ADR — record one decision, in one page, next to the code

## When to use this

A decision with consequences has just been made (or is about to be) and nothing
durable records it: which Helm chart layout, which secrets operator, which GPU SKU,
why one gateway sits in front of every model, why the cluster is private. The ADR is
the two-minute read a future engineer (or agent) needs before touching that area.

**Not this skill if:** the decision is still open and expensive → `write-design-doc`
to work it through (the ladder in steering §0 is the first check). It is a cheap-to-reverse
knob (a timeout, a label) → no ADR, just change it.

## Prerequisites

- Know the repo's ADR home. Default `docs/adr/`. If the repo already keeps ADRs
  elsewhere (`doc/decisions/`, `architecture/adr/`), **use that** — never start a
  second series.
- Read the existing index first (`docs/adr/README.md`). A decision that supersedes
  an earlier one must say so in both files.

## Procedure

### 1. Find the series and the next number

```bash
ls docs/adr/ 2>/dev/null | sort | tail -5          # existing ADRs, highest number last
grep -il '<topic keyword>' docs/adr/*.md 2>/dev/null   # anything already covering this?
```

Numbers are four digits, zero-padded, never reused. If `docs/adr/` does not exist,
**ask before creating it** (a new top-level doc series is a repo-wide convention,
not a local edit), then seed `README.md` with the index header below.

### 2. Draft from the template

File name: `docs/adr/NNNN-short-kebab-title.md`. Keep Context under ten lines;
if it needs more, the decision wants a design doc, not an ADR.

```markdown
# ADR-NNNN: <Decision as a statement — "Route all model traffic through the gateway">

- **Date:** YYYY-MM-DD
- **Status:** proposed | accepted | deprecated | superseded by ADR-NNNN
- **Deciders:** <names / team>
- **Related:** <design doc, ticket, MR, other ADRs>

## Context

<The forces: what hurt, what constraint applies (no egress, GPU quota, audit
requirement, team skill), what triggered deciding now. 3–8 sentences.>

## Decision

<One to three sentences, present tense: "We run one model-server Deployment per model;
the gateway is the only endpoint clients may call.">

## Alternatives considered

### <Alternative 1>
- Pros: …
- Cons: …
- Why not: <the specific reason it lost — never "we just picked it">

### <Alternative 2>
…

## Consequences

**Positive:** …
**Negative / cost:** <the tax: ops burden, lock-in, latency, licence, quota>
**Risks and mitigations:** …
**Follow-ups:** <tickets this creates>
```

### 3. Confirm, then write

Show the draft to the human before writing the file — an ADR records *their*
decision. On approval write the file and append to the index:

```markdown
| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-private-cluster-no-egress.md) | Private cluster, no internet egress | accepted | 2026-10-11 |
```

Keep the index sorted by number. Status in the index must match the file.

### 4. Supersede, don't rewrite

A changed decision gets a **new** ADR. In the old one set
`Status: superseded by ADR-NNNN`; in the new one list the old under *Related*.
Editing history out of an ADR destroys the one thing it is for.

### 5. Verify

- [ ] Alternatives section names at least one real alternative with a "why not"
- [ ] Consequences names a cost, not only benefits
- [ ] Index row present and status matches
- [ ] Any superseded ADR updated in the same MR

## Reading ADRs (the "why is it like this" path)

```bash
cat docs/adr/README.md                      # scan titles
grep -l -i 'keyword' docs/adr/*.md | xargs -I{} sed -n '1,/^## Decision/p' {}
```

Answer from Context + Decision. If no ADR covers it, say so and offer to record one
(backfilled ADRs state the **original** date and mark `backfilled` in Related).

## What earns an ADR here

| Yes | No |
|---|---|
| Umbrella chart vs one chart per service | A values default |
| Secrets: CSI vault driver vs External Secrets Operator | A secret's name |
| Private cluster + user-defined routing for egress | A single firewall rule |
| GPU SKU / node pool strategy for model serving | One Deployment's replica count |
| One mandatory gateway; one model server per model | A model's context-length flag |
| How a branch reaches the testing namespace | A job's cache key |
| Quantization policy (what precision ships to prod) | One model's dtype flag |

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Two ADR series in one repo | Didn't look before creating `docs/adr/` | Merge into the existing series; renumber the newcomer |
| ADR with no alternatives | Written after the fact as justification | Add the real alternatives or downgrade it to a note in the design doc |
| Status drift | File says superseded, index says accepted | Fix both in one MR; the index is derived, the file is truth |
| 40-line Context | A design doc wearing an ADR costume | Move to `write-design-doc`; leave a one-page ADR pointing at it |
| Agent "records" a decision nobody made | Drafted and wrote without confirming | Always confirm before writing (step 3) |

## Definition of done

- [ ] `docs/adr/NNNN-title.md` written from the template, status set
- [ ] Index row added; superseded ADRs cross-linked
- [ ] Human confirmed the wording of *Decision* before the file was written
- [ ] The MR that changes the infrastructure links the ADR
