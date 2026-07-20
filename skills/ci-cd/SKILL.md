---
name: ci-cd
description: >
  Use when setting up or debugging a CI pipeline, adding a workflow or gate,
  promoting a build through environments, deploying, cutting a versioned release,
  or rolling one back. Triggers on "the pipeline is red", "add a CI step",
  "GitHub Actions/GitLab CI", "deploy to staging/prod", "canary", "blue-green",
  "bump the version", "changelog", "tag a release", "how do we roll back".
  Do NOT use for writing/running the tests themselves (that's `run-tests`), for
  reviewing a dependency's safety (`secure-code-review`), or for production
  monitoring and incident triage (`observability`).
---

# CI/CD: pipeline, deploy, release, rollback

## When to use this

Code is proven correct locally and now has to be **built, moved between
environments, and shipped** — reproducibly, and reversibly. This skill is the
machinery that carries a green diff to production and back if it's wrong.

**Not this skill if:** you're making tests pass → `run-tests`. You're vetting an
external package → `secure-code-review`. It's already in prod and misbehaving →
`observability`.

## Prerequisites

- The full local gate is green first: 〈`run-tests` skill — tests, lint, typecheck〉.
  **CI enforces the gate; it does not discover it.** A pipeline is not a place to
  find out your tests fail.
- Deploy credentials are **CI-scoped, not personal**, and **never prod creds on a
  laptop**. See §5.

## §1 — Pipeline shape: cheapest gate first, fail fast

Order stages so the fastest, most likely-to-fail check runs first. A 40-minute
e2e suite behind a lint error that would've failed in 3 seconds is wasted money
and wasted wall-clock.

```
push / PR ──▶ lint + format ──▶ typecheck ──▶ unit ──▶ build ──▶ integration ──▶ e2e ──▶ [merge] ──▶ deploy
              (seconds)          (seconds)     (fast)   (min)     (needs stack)   (slow)            (gated)
```

- **PR pipeline** runs everything up to and including the slow suites. Red = no merge.
- **Merge/main pipeline** rebuilds the artifact **once**, tags it, and deploys.
  Never rebuild between environments — **promote the same immutable artifact**, or
  staging and prod are not the same thing you tested.
- **Cache** deps and build layers keyed on the lockfile hash; **never** cache test
  results or coverage.
- Pin the CI runner image and action/tool versions. A floating `@latest` in CI is
  a supply-chain hole and a source of "worked yesterday" flakes.

## §2 — Environments & promotion

| Env | Fed by | Data | Purpose |
|---|---|---|---|
| 〈dev / preview〉 | every PR | synthetic | see it run before merge |
| 〈staging〉 | merge to main | prod-like, **no real PII** | last check before prod |
| 〈prod〉 | **promotion of the staging artifact** | real | the real thing |

**Promote, don't rebuild.** The build that passed staging is the *bytes* that go
to prod. Rebuilding re-rolls the dice on dependency resolution and build
non-determinism.

## §3 — Deploy strategy: pick for blast radius, not novelty

| Strategy | How | Use when |
|---|---|---|
| **Recreate** | stop old, start new | brief downtime is fine; dev/internal tools |
| **Rolling** | replace instances N at a time | the default for stateless services |
| **Blue-green** | stand up full new version, flip traffic | need instant rollback; DB is compatible both ways |
| **Canary** | 〈1% → 10% → 100%〉, watch metrics between | high-risk change; want to catch it on 1% of traffic |

**The pivotal question is the same as for a new service:** *what's the blast
radius if this deploy is wrong, and how fast can I undo it?* That answer picks the
strategy. High blast radius → canary + a tested rollback, never recreate.

Non-negotiables for any deployed service:
- [ ] **Health/readiness endpoint** the deployer waits on before shifting traffic
- [ ] **`min=2` instances** so a deploy or crash always leaves a healthy target
- [ ] Deploy is **idempotent** — re-running it converges, doesn't duplicate

## §4 — Cutting a release

1. **Version with SemVer** — `MAJOR.MINOR.PATCH`. Breaking change → MAJOR. A
   breaking change shipped as a PATCH is how you page three teams at once.
2. **Changelog** — human-readable, grouped (Added / Changed / Fixed / **Breaking**).
   Generated from conventional commits is fine; a wall of raw SHAs is not a changelog.
3. **Tag the commit** 〈`git tag -a vX.Y.Z -m ...` / release workflow〉. The tag,
   the artifact, and the changelog entry all name the **same version**.
4. **Migrations ship before the code that needs them** and are backward-compatible
   (expand → migrate → contract). Old code must survive the window where new schema
   and old instances coexist during a rolling deploy.

## §5 — Secrets & config in CI (guardrail surface)

- Secrets come from the **CI secret store / OIDC**, never committed, never
  `echo`'d, never in a log line. Mask them. A secret printed in a build log is a
  leaked secret — rotate it.
- Prefer **short-lived OIDC federation** over long-lived cloud keys stored in CI.
- **No prod credentials in PR pipelines.** A PR runs untrusted contributor code;
  giving it prod creds hands prod to anyone who opens a PR.
- New env var? It goes in 〈`.env.example`〉 **and** the deploy config, and it's
  named in the PR. An undocumented required env var is a 3am outage.

## §6 — Rollback: the part you build *first*, not last

> A deploy you cannot undo is not a deploy, it's a gamble. **Have the rollback
> before you have the deploy.**

- **Know the exact command** to go back one version 〈`kubectl rollout undo` /
  re-promote the previous tag / flip blue-green〉 — and that it's tested, not theoretical.
- **Forward-only for data.** You can roll back code instantly; you often *cannot*
  roll back a destructive migration. Never combine a `DROP`/`DELETE`/`TRUNCATE`
  with the deploy that depends on it — split into expand/contract releases so
  each step is independently reversible.
- **Feature-flag risky behavior** so "roll back" can mean flip a flag in seconds,
  with no redeploy.
- If rollback needs a human decision at 3am, the runbook for it is written **now**,
  in daylight — see `observability` §B.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Green locally, red in CI | Env drift; unpinned tool/runner; test ordering | Pin the runner + tool versions; run tests in CI's order locally |
| Staging ≠ prod behavior | Artifact rebuilt per env | **Promote one immutable artifact**; don't rebuild |
| Deploy "succeeds", service is down | No readiness gate; traffic shifted to a sick box | Add health check the deployer waits on; `min=2` |
| Can't roll back the DB | Destructive migration shipped with the code | Expand/contract; forward-only data; never `DROP` in the same release |
| Secret leaked in build log | Unmasked secret `echo`'d | Rotate it now; mask; move to OIDC |
| Flaky pipeline | Unpinned deps/actions; shared state between jobs | Pin everything; isolate job state |

## Definition of done

- [ ] Full gate runs in CI, fail-fast ordered; **PR does not merge on red**
- [ ] One immutable artifact built once and **promoted**, not rebuilt per env
- [ ] Deploy strategy chosen for **blast radius**; health gate + `min=2` in place
- [ ] Release versioned (SemVer), changelog written, tag == artifact == changelog
- [ ] Migrations backward-compatible and shipped before dependent code
- [ ] **Rollback command known and tested**; destructive data ops split out
- [ ] No secret in any log; no prod creds in PR pipelines; new env vars documented
