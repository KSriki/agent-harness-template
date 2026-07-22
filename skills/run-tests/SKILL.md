---
name: run-tests
description: >
  Use when running, writing, debugging, or adding tests; when a test fails; when
  a CI quality gate fails (SonarQube, coverage threshold, lint, typecheck); or
  before declaring any code change complete. Covers unit, integration, contract,
  and e2e tests plus the full local quality-gate sequence.
  Do NOT use for evaluating LLM/agent outputs (`eval-harness`), or for building a
  feature TEST-FIRST — the red→green loop is `tdd`; this skill is the gate you run
  on code that exists.
---

# Running tests and quality gates

## When to use this

Any time code changed and you need to prove it still works — and *always* before
claiming a task is done. A change without passing tests is not done, it is
in progress.

**Not this skill if:** you're scoring non-deterministic LLM/agent output →
`eval-harness`. Tests assert; evals score.

## Prerequisites

- Deps installed: 〈`uv sync`〉
- Integration/e2e need the local stack: 〈`docker compose up -d`〉

## The gate sequence

Run in this order — each is cheaper than the next, so fail fast.

### 1. Fast feedback: the one test you care about

```bash
〈uv run pytest tests/unit/test_thing.py::test_case -x -q〉
```

### 2. Unit suite (no I/O, must be fast)

```bash
〈uv run pytest tests/unit -q〉
```

If unit tests need the DB or the network, that's a design smell — the logic
under test belongs in a layer that doesn't do I/O. Say so rather than
mocking around it.

### 3. Integration (real deps)

```bash
〈docker compose up -d && uv run pytest tests/integration -q〉
```

### 4. Static gates

```bash
〈uv run ruff check --fix . && uv run ruff format .〉   # lint + format
〈uv run mypy src/〉                                     # types
```

### 5. Coverage

```bash
〈uv run pytest --cov=src --cov-report=term-missing〉
```

**Coverage is a floor, not a trophy.** Do not add assertion-free tests to move
the number. If coverage dropped, find the *behavior* that's now untested and test
that. Report an honest gap rather than gaming it.

### 6. SonarQube / CI parity

〈`sonar-scanner` or: push and read the PR check〉

Watch for: duplication, cyclomatic complexity, unused code, security hotspots.
If Sonar flags duplication, check it's *real* repetition before deduplicating —
two things that merely look alike are not yet an abstraction.

## Writing tests (when adding them)

- **Test behavior and edges, not lines.** The error path, the empty input, the
  boundary, the concurrent case — that's where bugs live.
- **Match the level to the thing.** Pure logic → unit. Crossing a boundary
  (DB/queue/API) → integration. A contract with another service → contract test.
- **Tests are part of the same commit as the code.** Not a follow-up commit,
  not a follow-up PR.
- **Deterministic.** No sleeps, no real clocks, no live network, no test that
  passes or fails based on ordering.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Integration tests hang, no error | Local stack not up | 〈`docker compose up -d`〉 |
| `ModuleNotFoundError` | Bare `python` instead of `uv run` | Use 〈`uv run`〉 |
| Passes locally, fails in CI | Env drift / missing fixture / ordering | Run with 〈`-p no:randomly`〉 off to check ordering; diff env |
| Coverage dropped after refactor | New branch untested | Test the branch; don't lower the threshold |
| Flaky | Time, ordering, or shared state | Fix it or delete it — a flaky test is worse than none |

## Definition of done

- [ ] Tests written **and passing** for the change
- [ ] Unit suite green; integration green if a boundary was touched
- [ ] Lint + format + typecheck clean
- [ ] Coverage not regressed
- [ ] Sonar gate clean (or the flag consciously triaged, with a reason)
- [ ] **PR is not merged on red**
