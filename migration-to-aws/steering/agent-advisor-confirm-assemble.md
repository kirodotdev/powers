---
_assemble: assemble-confirm
_of_phase: confirm
_reads:
  - winner-specific follow-up answers (collected inline in agent-advisor-confirm.md)
_produces:
  - confirm.json
---

# Confirm — Assemble confirm.json

> **Assembler unit.** Confirm reads the scoring result, asks only what the
> winning runtime needs (deployment model, AgentCore services, co_recommend
> pick, native-vs-gateway tool choices), and writes `confirm.json` inline within
> `agent-advisor-confirm.md` (Step 5). This unit records the artifact-level contract for
> the phase: it is the single creator of `confirm.json`, and its postconditions
> (declared on the phase) are the phase's completion gate. See `agent-advisor-confirm.md`
> § Step 5 for the confirm.json shape (`deployment_model`, `agentcore_services`,
> `chosen_runtime` when co_recommend, `tool_choices`).
