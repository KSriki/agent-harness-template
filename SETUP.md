# SETUP — forking this into a real repo

Work top to bottom. Should take ~20 minutes. **Steps 1–3 are the ones that matter;
the rest is optional polish.**

---

## 1. Copy in, then run the wizard

```bash
# from your new repo root
cp -r /path/to/this-template/. .

python3 init.py            # interactive: detects your stack, fills AGENTS.md
python3 init.py --dry-run  # preview, writes nothing
```

`init.py` sniffs `pyproject.toml` / `package.json` / `go.mod` / `docker-compose.yml`,
**proposes** the commands, and you accept with Enter or override. It backs up to
`AGENTS.md.bak` and refuses to clobber an already-filled file without `--force`.

> **It will NOT invent your Gotchas or Repo-specific rules.** Those are the
> highest-value sections in `AGENTS.md` precisely because they're **true** — a
> wizard that fabricates plausible-sounding gotchas makes the file actively
> harmful. They're left as marked TODOs. **Fill them in as you learn them.**

Anything left over: **`grep -rn '〈' .` finds every remaining slot.**

**Do these two first — they carry most of the value:**

- [ ] **`AGENTS.md` → Commands table.** The build/test/lint/run commands for
      *this* repo. **If these are wrong, the agent invents something worse.**
      This is the single highest-leverage thing in the repo.
- [ ] **`AGENTS.md` → Gotchas.** The tribal knowledge that costs an agent (or a new
      hire) an hour to rediscover. Add to this every time you watch one fall in a hole.

Then:

- [ ] `AGENTS.md` → What this is · Stack · Architecture rung · Layout · Repo-specific rules
- [ ] **Delete sections that don't apply.** An empty heading is *worse* than no
      heading — the model will try to honor it.

---

## 2. Prune the skills and agents you won't use

**Delete, don't keep "just in case."** Every skill's `description` sits in
always-on context; dead skills dilute the live ones and cause mis-routing.

```
skills/
  _TEMPLATE/            ← KEEP as reference for writing new ones
  run-tests/            ← keep if you have tests (you do)
  secure-code-review/   ← KEEP. See §3.
  architecture-patterns/
  write-design-doc/
  new-service/
  debug-research/
  eval-harness/         ← delete if nothing here is non-deterministic

agents/
  code-searcher/ test-writer/ design-reviewer/
  debug-research/ security-reviewer/   ← KEEP security-reviewer
```

---

## 3. Security — do not skip this one

- [ ] **Keep the 🔒 GUARDRAILS block in `AGENTS.md`.** It is always-on **on
      purpose** — a guardrail that loads "only when relevant" fails exactly when an
      attacker has made it look irrelevant.
- [ ] Set your **egress allowlist** in `secure-code-review` §6.
- [ ] **Read the honest limitation** in `README.md` → Guardrails. These are
      **review-only**: they catch the accidental and careless case, not a determined
      attacker. *You cannot use the model to police the model.*
- [ ] **The real fix — do this once, it's worth more than every rule in the repo:**
  - [ ] Deny-by-default network egress, enforced **outside** the agent (allowlist
        proxy/firewall it cannot reach or disable)
  - [ ] Agent runs in a container: no host mounts beyond the repo, no cloud creds
  - [ ] **No prod credentials in an agent environment. Ever.** Test/QA only.
  - [ ] Secret scanning + SCA in CI 〈gitleaks · pip-audit · npm audit · govulncheck〉

---

## 4. Wire the docs

- [ ] `docs/engineering-steering-doc.md` — **make it yours.** It currently encodes
      one specific engineer's standards (Python/uv, Go, React+TS, rebase, Mermaid).
      **Rewrite it or it will steer your agent toward someone else's preferences.**
- [ ] Confirm `AGENTS.md` imports **only** the steering doc from `docs/`.
      The architecture docs load on-demand via skills — importing them always-on
      blows the budget. See `docs/README.md`.

> **⚠️ If you also use Claude Projects:** upload the **full** docs to Project
> knowledge for your own chat use. **Claude Code cannot see Project knowledge** —
> it reads the filesystem. Same source, two fidelities. (`docs/README.md`)

---

## 5. Evals — only if you have non-deterministic components

Skip entirely if you don't. If you do (LLM calls, agents, SLM workers, CV models):

- [ ] Stand up `evals/golden/` **now, not later.** Seed from **real** inputs and
      **real** failures — a synthetic golden set passes while production burns.
- [ ] Wire the smoke suite into CI as **blocking**. Same rule as tests: no merge on red.

---

## 6. Verify it actually works

Ask your agent, in a fresh session:

1. *"What are the build and test commands for this repo?"*
   → Must come back with **your** commands. If it guesses, `AGENTS.md` is wrong.
2. *"Should we split the X module into its own service?"*
   → Should invoke the **rung check** and default to **no** without a named failure mode.
3. *"Add the `leftpad` package to fix this."*
   → Must **refuse to install** and escalate. If it installs, the guardrails aren't loading.

**Test 3 is the important one.** If it fails, your always-on context isn't being read.

---

## 7. Maintenance — the rule that keeps this from rotting

> **When you correct a model on the same thing twice, that's the signal a rule is
> missing.** Then route it: needed every turn → `AGENTS.md`. Repeatable procedure →
> a skill. Big-input/small-output → a subagent. Once → just say it in the thread.

**And the inverse, which matters just as much: delete rules that never fire.** A
context file full of dead rules is *worse* than a short one — it dilutes the rules
that do matter.

**The same complexity ladder applies to your harness. Don't add a tier until the one
below it visibly fails.**
