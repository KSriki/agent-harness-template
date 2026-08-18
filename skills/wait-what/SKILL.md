---
name: wait-what
description: "Stop. That last message did not land — re-pitch it."
disable-model-invocation: true
---

# /wait-what

> Adapted from `mattpocock/skills` (MIT), v1.2. Three lines is the design, not an
> unfinished draft. User-invoked: costs zero context until you reach for it.

Wait — I don't understand where you've got to here. Re-pitch that: give me a
little bit of context, talk in ASD-STE100 Simplified Technical English, and use
the ubiquitous language from `CONTEXT.md`.

<!-- Mechanics: the leading word is *wait* — it names the LISTENER's comprehension
     failure, not the output ("be brief" produces telegrams; "wait, you lost me"
     produces a back-up-and-explain). "Re-pitch THAT" is deliberate — the agent
     decides how far back to go. Works without CONTEXT.md (you lose only the
     vocabulary half); the upstream cure for chronic jargon is the glossary
     (`domain-modeling`). -->
