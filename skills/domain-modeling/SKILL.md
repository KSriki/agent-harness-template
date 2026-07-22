---
name: domain-modeling
description: >
  Use to actively build and sharpen a project's domain model — pin down
  terminology / ubiquitous language, resolve fuzzy or overloaded terms, and record
  the occasional architectural decision (ADR) — writing the glossary down the moment
  a term crystallizes. Triggers on "what do we call this", "'account' — is that the
  Customer or the User?", "pin down the terminology", "record this decision / ADR",
  "update the glossary / CONTEXT.md".
  Do NOT use for a full design doc on a big, expensive-to-reverse decision
  (`write-design-doc`), for module interface design (`codebase-design`), or for
  product requirements (`write-a-prd`). This skill is the glossary + light ADRs.
---

# Domain modeling: the glossary as you go

> Adapted from `mattpocock/skills` (MIT) — reimplemented in this repo's style.

## When to use this

While designing or discussing — the *active* discipline of challenging terms,
inventing edge cases, and **writing the glossary and decisions down as they
crystallize**. (Merely *reading* the glossary is a one-line habit, not this skill;
this skill is for *changing* the model.)

**Not this skill if:** it's a big irreversible design decision needing a full doc →
`write-design-doc`. It's a module interface → `codebase-design`. It's product
requirements → `write-a-prd`.

## Where it lives

- **Single context:** a root `CONTEXT.md` (the glossary) + ADRs under 〈`docs/adr/` or `docs/design/`〉, numbered `0001-…md`.
- **Multi-context (monorepo):** a root `CONTEXT-MAP.md` pointing to a per-context `CONTEXT.md` + context-scoped ADRs.
- **Create files lazily** — only when there's something to write.

## Procedure (during the session)

1. **Challenge against the glossary.** When a term conflicts with `CONTEXT.md`, call
   it out immediately.
2. **Sharpen fuzzy language.** Propose a precise canonical term for a vague or
   overloaded word — *"'account' — do we mean Customer or User?"*
3. **Discuss concrete scenarios.** Invent edge-case scenarios that force precise
   boundaries between concepts.
4. **Cross-reference with code.** Check whether the code agrees with the stated
   behavior; surface contradictions.
5. **Update `CONTEXT.md` inline** the moment a term resolves — don't batch.
   > **`CONTEXT.md` is a glossary and nothing else — totally devoid of
   > implementation details.**
6. **Offer an ADR — sparingly.** Record one *only when all three hold:*
   **(1) hard to reverse, (2) surprising without context, (3) the result of a real
   trade-off.** Miss any one → skip it. (This is the steering doc's
   penalty-for-being-wrong test, applied to decisions.)

## Definition of done

- [ ] Conflicting/fuzzy terms resolved to canonical names
- [ ] `CONTEXT.md` updated inline — glossary only, no implementation detail
- [ ] ADR recorded **only** if hard-to-reverse **and** surprising **and** a real trade-off
- [ ] Code contradictions surfaced (not silently left)
