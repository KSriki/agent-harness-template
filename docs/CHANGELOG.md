# Context Changelog

Every promotion into `docs/` gets one entry. A PR that changes `docs/` without
changing this file is a promotion without a record — gate on it.

**Version semantics** — pinned to *agent behaviour*, not edit size:

- **MAJOR** — agent-breaking. A rule changed such that previously-correct behaviour is
  now wrong. Every entry carries a **Re-check:** line.
- **MINOR** — additive. New guidance; everything previously correct still is.
- **PATCH** — no behavioural change. Clarification, link fix, formatting.

The test for MAJOR: *if an agent had memorised the previous version and acted on it,
would it now be wrong?* If yes, major. If it would merely be missing something, minor.

---

## 2026-08-17

- `multi-agent-orchestration` — → **2.0.0** (MAJOR — agent-breaking)
  - **Beads is now the tracker preset.** Frontier = `bd ready --json`; assignment =
    `bd update <id> --claim`. Membership in `bd ready` IS the ready-for-agent signal.
  - Added the **BOUNDARY**: Beads holds the work graph only. Never `bd remember`.
    Never `bd setup claude`.
  - Added §0 (operational roles vs. org-chart simulation), §3 (what actually caps
    worker count), §9 (why a fleet framework was not adopted).
  - Added abort-recording to the guardrails, and the review-only caveat.
  - **Re-check:** any orchestration procedure that dispatches without claiming, or
    that treats a hand-maintained list as the frontier. Double-dispatch is now
    preventable and therefore a defect.

- **All `docs/*.md` — provenance headers added** (PATCH, no behavioural change)
  - Every doc now carries `version`, `source`, `source_version`, `derivation`, and
    `review_after`. Before this there was no way to tell a current derived doc from a
    stale one by looking at it.
  - `derivation: compressed` docs also carry a one-line note under the title so an
    agent knows it is reading a derivation and should say so rather than infer detail
    the file doesn't carry.

- `architecture-patterns-FULL-KB` — read guard added (PATCH)
  - Header now states the file is opened **at a cited §**, never read whole. The
    policy already existed in `docs/README.md`; nothing enforced it, and one
    whole-file read spends the entire budget the tier system protects.

---

<!--
TEMPLATE — copy for the next entry:

## YYYY-MM-DD

- `<doc-name>` X.Y.Z → **A.B.C** (MAJOR|MINOR|PATCH — short reason)
  - What changed, in terms of what an agent would now do differently.
  - **Re-check:** <MAJOR only — what has to be revisited>
-->
