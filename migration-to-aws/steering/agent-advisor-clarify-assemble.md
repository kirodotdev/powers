---
_assemble: assemble-clarify
_of_phase: clarify
_reads:
  - technical wording fragment (agent-advisor-clarify-technical.md contribution, when audience is technical)
  - business wording fragment (agent-advisor-clarify-business.md contribution, when audience is business)
  - interpreted core-question answers (collected inline in agent-advisor-clarify.md)
_produces:
  - answers.json
  - scoring-result.json
---

# Clarify — Assemble answers.json and run scoring

> **Assembler unit.** The Clarify phase presents the core scoring questions (in
> the audience-specific wording loaded from agent-advisor-clarify-technical.md /
> agent-advisor-clarify-business.md), interprets the answers, and writes `answers.json`
> inline within `agent-advisor-clarify.md` (Step 4), then runs the deterministic scoring
> engine, which writes `scoring-result.json` (Step 5). This unit records the
> artifact-level contract for the phase: it is the single creator of both
> `answers.json` and `scoring-result.json`, and its postconditions (declared on
> the phase) are the phase's completion gate. See `agent-advisor-clarify.md` § Step 4–5 for
> the legal answer keys/values and the scoring command.
