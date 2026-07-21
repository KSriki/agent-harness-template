@AGENTS.md

<!--
  CLAUDE.md is Claude Code's entry point, and it is loaded on every turn. The
  @import above pulls AGENTS.md — the portable source of truth — into always-on
  context, and AGENTS.md in turn @-imports the steering doc (imports chain up to
  4 hops deep).

  THIS @import IS LOAD-BEARING. A plain markdown link ("See AGENTS.md") imports
  NOTHING — with only a link here, the always-on context, INCLUDING the security
  guardrails in AGENTS.md, silently fails to load in Claude Code. Do not turn this
  back into a link. Verify it with SETUP.md §6, test 3 (the leftpad refusal).

  Other agent tools (Cursor, Copilot, …) read AGENTS.md directly; this file is the
  Claude Code-specific shim that makes them equivalent.
-->
