---
_phase: confirm
_title: "Confirm — Winner-specific follow-ups"
_requires_phase: clarify
_input:
  - scoring-result.json
  - answers.json
_assemble:
  _file: agent-advisor-confirm-assemble.md
_produces:
  - confirm.json
_advances_to: design
_preconditions:
  - _check_phase_completed: clarify
    _on_failure: _halt_and_inform
  - _check_file_exists: scoring-result.json
    _on_failure: _unrecoverable
  - _validate_json: scoring-result.json
    _on_failure: _unrecoverable
_postconditions:
  - _check_file_exists: confirm.json
    _on_failure: _halt_and_inform
  - _validate_json: confirm.json
    _on_failure: _halt_and_inform
  - _assert: "confirm.json has one units[<unit_id>] entry per agent_session unit (each with its own confirmed deployment_model, agentcore_services, tool_choices, and chosen_runtime when that unit's verdict was co_recommend), plus top-level fields mirroring the primary unit; a single-unit run may use the flat top-level shape alone; confirm.json carries resolved_runtimes{<unit_id>: <runtime>} for every unit (the per-unit rule/Tier-1 picks used by the platform gate); confirm.json records platform_decision {mode, platform} — asked only when the resolved runtimes diverge, silent split otherwise; when the gate was asked, platform_decision.offer records the superset and per-unit sacrifices; every temporal_worker_poll unit's Tier-1 pick (including any user AskUserQuestion choice for Tier-1 rules 1/4) is persisted in resolved_runtimes so Design consumes it verbatim and never re-asks"
    _on_failure: _halt_and_inform
---

# Phase: Confirm — Winner-specific follow-ups

Runs after scoring, before Design. Only asks what the winning runtime needs.

## Step 1 — Read the scoring result

Read `$RUN_DIR/scoring-result.json`.

**Per-unit confirm (multi-unit systems).** `scoring-result.json.units` carries one scored
result per `agent_session` unit — each has its OWN `verdict`, `deployment_model`, and
`agentcore_services`. Steps 2–5 below run **once per `agent_session` unit**, keyed on that
unit's own scored result — NOT once globally on a top-level verdict. A system with two agent
units where one scored `agentcore` and the other `co_recommend` (AgentCore vs Lambda MicroVMs)
must resolve BOTH: confirm the first's deployment model and services, AND break the second's
tie and confirm its own services. Never apply one agent unit's deployment_model, services, or
runtime pick to another.

Non-agent units (`batch`, `light_io`, `service`, `temporal_worker_poll`) are not scored and
have no agentcore confirm — their verdict comes from workload-classes/temporal rules in Design.

**Single-unit collapse:** when there is exactly one unit, "per unit" is the one unit and
confirm.json's top-level fields ARE that unit's confirm (today's behavior, unchanged).

For each `agent_session` unit, branch on THAT unit's `verdict` through Steps 2–4, and record
its confirmed choices into `confirm.json.units[<unit_id>]` (Step 5). The primary unit
(`answers.json.primary_unit`) ALSO mirrors to the top-level fields for backward compatibility.

## Step 2 — If a unit's verdict includes agentcore

Present the deployment model (`deployment_model` from the result) and let the user **confirm or
switch** between **Harness** (no-code, managed loop — declare the agent as config) and
**Framework on Runtime** (bring Strands/LangGraph/CrewAI/custom code). If they picked a
`deployment_preference` in Clarify, it already drove this — restate it and let them change their
mind here. Record the final choice in `confirm.json`.

Then ask which AgentCore services to enable beyond the always-on set (identity, observability,
evaluations, optimization). Multi-select, seeded from `agentcore_services`:

- Gateway (external APIs / MCP), enhanced Identity (OAuth), Policy (high-risk / multi-tenant),
  Memory (cross-session), Managed KB (internal docs), Code Interpreter, Browser, Web Search,
  Sandbox.
- **Conditional (mention only when signals fit — not by default):** Payments (agent pays /
  transacts on the user's behalf — surface if high-risk/transactional actions are detected) and
  Registry (multi-agent discovery / orchestration — surface if `multi_agent == "yes"`). If
  neither signal is present, leave them out rather than listing them.
  For any selected service that can front external tools/data (Gateway, Managed KB, Web Search,
  Memory), **ask** whether they already use a third-party tool for it (e.g. Tavily, Pinecone,
  Browserbase, a REST/MCP server) — do NOT assume greenfield. If yes: switch to AgentCore native,
  or keep existing and connect via Gateway. If no: default to native. Record the choice in
  `tool_choices`.

## Step 3 — If a unit's verdict is any non-AgentCore runtime (ecs / eks / lambda / lambda_microvms / batch / fargate)

These run the agent on non-AgentCore compute. Still ask which AgentCore **add-on** services
they want for THIS unit (services run on any runtime). Record them under this unit. This branch
is the fallthrough for EVERY non-agentcore runtime — including `lambda_microvms` picked from a
co_recommend tie in Step 4 — so no runtime pick skips its services/tool_choices confirm.

## Step 4 — If a unit's verdict is co_recommend or no_viable_runtime

- co_recommend: present THIS unit's tied runtimes with "choose A if X / B if Y" framing; ask the
  user to pick one FOR THIS UNIT. Record the pick as this unit's `chosen_runtime` (Step 5). Then
  run Step 2/3 for the pick. Each co_recommend unit is broken independently — two agent units can
  land on different runtimes.
- no_viable_runtime: show `blocking_constraints`; ask which constraint can relax; if one
  changes, rewrite `$RUN_DIR/answers.json` with the changed value and re-run scoring by executing
  **agent-advisor-clarify.md Step 5's exact bash block** (the PYTHONPATH multi-unit loop that reads
  answers.json — each unit's own `workload_class` — for the agent_session filter and writes the
  wrapper `{ "units": { ... }, ...primary mirror }`).

  Do NOT invoke `agent-advisor-scoring.py` directly on `answers.json` here — that scores only the top-level
  primary mirror and OVERWRITES the wrapped result with a flat one, deleting every `units[<id>]`
  entry so this phase's per-unit loop is left with no inputs. Only the wrapper-producing command
  is safe for rescoring.

  Re-running agent-advisor-clarify.md Step 5 overwrites `$RUN_DIR/scoring-result.json` with the correctly-shaped
  result. Re-read it and return to Step 1.

## Step 5 — Write confirm.json and state

Write `$RUN_DIR/confirm.json` with a `units` object — one entry per `agent_session` unit
confirmed in Steps 2–4, keyed by unit id — plus top-level fields mirroring the PRIMARY unit
(backward compatibility; single-unit runs are exactly today's flat shape).

Each `units[<unit_id>]` entry carries:

- `deployment_model` (confirmed; for a `co_recommend` pick, the deployment model of the runtime
  the user CHOSE for THIS unit — recompute for the chosen runtime, do not carry a stale value
  from the tie),
- `agentcore_services` (final list for this unit),
- `chosen_runtime` (REQUIRED when this unit's verdict was `co_recommend` — the runtime id the
  user picked in Step 4; omit for single-winner verdicts),
- `tool_choices` (per-capability native-vs-gateway choices for this unit).

The top-level `deployment_model` / `agentcore_services` / `chosen_runtime` / `tool_choices`
mirror the primary unit's entry.

```json
{
  "units": {
    "support-chat": {
      "deployment_model": "framework_on_runtime",
      "agentcore_services": ["identity", "memory"],
      "tool_choices": { "memory": "native" }
    },
    "triage-agent": {
      "deployment_model": "harness",
      "agentcore_services": ["identity"],
      "chosen_runtime": "lambda_microvms"
    }
  },
  "deployment_model": "framework_on_runtime",
  "agentcore_services": ["identity", "memory"],
  "tool_choices": { "memory": "native" }
}
```

Design reads `confirm.json.units[<unit_id>]` for each agent unit's confirmed
deployment_model/services/runtime; it falls back to the top-level fields for a single-unit run.

## Step 6 — Platform divergence gate (only when unit verdicts span more than one runtime)

Collect every unit's **resolved runtime** — NOT its raw verdict. A `co_recommend` verdict is
NOT a runtime; use the `chosen_runtime` the user just picked for that unit in Step 4 (recorded
in `confirm.json.units[<id>].chosen_runtime`). So per unit: agent_session → its
`chosen_runtime` if the verdict was `co_recommend`, else its scored `verdict`;
`temporal_worker_poll` → its **agent-advisor-temporal.md Tier 1** pick (load
`agent-advisor-temporal.md` — agent-advisor-workload-classes.md has NO temporal rule, so a Temporal
worker unit in a mixed system resolves its polling runtime here for the platform gate); other
non-agent → the workload-classes rule pick (load `agent-advisor-workload-classes.md`).
Never
compare the literal string `"co_recommend"` — two tied units that the user sent to different
runtimes (e.g. AgentCore vs Lambda) DIVERGE and must trigger the gate; comparing raw verdicts
would wrongly see them as "both co_recommend" and skip it.

**Persist the resolution as `confirm.json.resolved_runtimes` — a `{<unit_id>: <runtime>}` map
covering EVERY unit (agent and non-agent).** This is resolved ONCE here and Design consumes it
verbatim (Design does NOT re-evaluate temporal Tier 1). For a `temporal_worker_poll` unit whose
Tier-1 rule needs a user choice (rules 1 and 4 — EKS vs Serverless Workers), ask the
AskUserQuestion HERE, in this phase, and record the picked runtime in `resolved_runtimes` (and
cite the fired rule id). Design must find every unit's runtime already decided in
`resolved_runtimes`, so it never re-asks and platform_decision can never disagree with the
effective_runtime Design writes.

If ALL resolved runtimes name one
runtime, write `platform_decision: { "mode": "split", "platform": null, "offer": null }`
silently and continue — no question (collapse invariant).

Otherwise AskUserQuestion:

- **[A] Consolidate onto `<superset runtime>`** — the runtime satisfying every unit's HARD
  constraints (eliminations) with the highest summed score; in practice ECS or EKS. (Every run
  has ≥1 agent unit per Clarify's scope gate, so agent scores always exist to sum.)
  State the sacrifice per unit ("chat-agent loses AgentCore's built-in memory/identity —
  self-managed on ECS"). AgentCore is offered as the superset ONLY when every unit is
  `agent_session`. Choosing [A] writes `platform_decision: { "mode": "consolidated",
  "platform": "<runtime>" }`.
- **[B] Keep the split** — each unit on its own verdict; state the ops cost (two
  runtimes: two deploy pipelines, two scaling models). Choosing [B] writes
  `platform_decision: { "mode": "split", "platform": null }`.

Whichever the user picks, `platform_decision` also records the offer that was made —
the report retells it either way:

```json
"offer": {
  "superset": "<runtime>",
  "sacrifices": ["<unit>: <what it loses>", "..."]
}
```

`superset` is the runtime option [A] proposed; `sacrifices` lists, per unit, what that
unit gives up under consolidation (the same statements presented in the question).

Record the choice as `platform_decision` in confirm.json. The decision does NOT rewrite
per-unit verdicts — Design keeps both (unit verdict + platform decision) so the report
can show what consolidation traded away.

Set `phases.confirm` = completed (read-merge-write). The flow now advances to Design.
