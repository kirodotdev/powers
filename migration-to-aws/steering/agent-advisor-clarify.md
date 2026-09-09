---
_phase: clarify
_title: "Clarify — Adaptive Questions"
_requires_phase: discover
_input: context-signals.json
_fragments:
  - _id: clarify-technical
    _trigger: { _when: "audience is technical" }
    _file: agent-advisor-clarify-technical.md
  - _id: clarify-business
    _trigger: { _when: "audience is business" }
    _file: agent-advisor-clarify-business.md
_assemble:
  _file: agent-advisor-clarify-assemble.md
_produces:
  - answers.json
  - scoring-result.json
_advances_to: confirm
_preconditions:
  - _check_phase_completed: discover
    _on_failure: _halt_and_inform
_postconditions:
  - _check_file_exists: answers.json
    _on_failure: _halt_and_inform
  - _validate_json: answers.json
    _on_failure: _halt_and_inform
  - _check_file_exists: scoring-result.json
    _on_failure: _halt_and_inform
  - _validate_json: scoring-result.json
    _on_failure: _halt_and_inform
  - _assert: "answers.json has the nested shape {entry_point, answers:{...}} carrying the legacy mirror (top-level entry_point and answers = primary unit's fully-merged dims), AND system/primary_unit/units with every unit's dimensions fully resolved (inheritance applied) and every unit carrying its workload_class; the scope gate passed — at least one agent_session unit exists (a purely non-agent system halted with _halt_and_inform BEFORE primary selection); primary_unit is an agent_session unit; every collected key uses a legal value from agent-advisor-clarify.md Step 3; scoring-result.json was written by agent-advisor-scoring.py (not hand-scored) with one result per agent_session unit under units{} AND a top-level verdict mirrored from the primary; every unit carries a provenance map naming each dimension's source"
    _on_failure: _halt_and_inform
---

# Phase: Clarify — Adaptive Questions

Asks the core scoring questions, writes `answers.json`, runs the scoring engine.

## Step 1 — Pick the wording file by audience

- audience == technical → Load `agent-advisor-clarify-technical.md`
- audience == business → Load `agent-advisor-clarify-business.md`
  Both map onto the SAME scoring keys/values below. Only wording differs.

## Step 2 — Pre-fill from Discover and the opening description

If `$RUN_DIR/context-signals.json` exists, treat its keys as already answered. Show them as
"detected: `<value>` (say so if wrong)" and skip asking those, unless the user corrects them.
Also scan the Turn-1 open-context notes for two tone-setting signals and pre-fill them:

- "keep it cheap / minimize cost / tight budget" → `model_priority = cost`
- "don't want to manage / touch code / no-code / just run it" → `deployment_preference = harness`

## Unit-aware questioning (two levels)

Read `units` from `$RUN_DIR/context-signals.json` (or, on the no-code path, the
declared draft in context-notes.md — normalize it to the same shape,
`source: "declared"`). With ONE unit, the per-unit _delta questioning_ collapses to today's
flow — skip the extra per-unit question steps. **But the Temporal Activity interview/classification
below and the scope gate are NOT skippable by the one-unit collapse** — they run regardless of
unit count (a single `temporal_worker_poll` seed still needs its Activities classified before the
gate, and every run must pass the gate). Only the multi-unit delta questioning is collapsed.

**No inventory at all (single-workload build_scratch / skipped-Discover with no draft).** Intake
records nothing for a single workload (agent-advisor-intake.md Step 4 collapse), and Discover was skipped, so
neither context-signals.json nor a context-notes.md draft has a unit. In that case Clarify
MATERIALIZES exactly one **complete** unit record itself — the same shape context-signals.json
would have produced — so downstream consumers that expect `coupling` / `trigger` /
`description` / `evidence` have a source (they otherwise read the absent context-signals.json):

```json
{
  "id": "<kebab-case from the app/idea name, else primary-agent>",
  "workload_class": "agent_session",
  "coupling": { "mode": "none", "interacts_with": [] },
  "trigger": "request",
  "description": "<one line from the user's description>",
  "evidence": "user-described (no repo)",
  "source": "materialized"
}
```

`workload_class` defaults to `agent_session` (a described agent) — override ONLY if the user
clearly described a non-agent workload (a batch job → `batch`, a plain long-running service →
`service`, an HTTP/webhook endpoint → `light_io`). Set `primary_unit` to this unit's id. Step 4
persists it (with `workload_class`) and Step 5 scores it if it's `agent_session` — so a typical
"I have an idea for one agent" build_scratch run produces a real agent_session unit, NOT an empty
inventory, and a "just run this batch job" run produces a complete non-agent unit.

### Scope gate — require at least one agent_session unit (BEFORE primary selection)

**agent-advisor is scoped to agentic systems.** Run this gate once the inventory is FULLY
classified — after materialization above AND after any Temporal Activity classification
(including the no-code Activity interview below, which turns a bare `temporal_worker_poll` seed
into its real Activity-execution units) — but BEFORE picking a primary or asking per-unit
questions. **Do NOT halt a Temporal system on the strength of a `temporal_worker_poll`-only seed:
its Activities are not yet classified, and agentic Activities become `agent_session` units.**
Only after Activities are classified, if NO unit has `workload_class == "agent_session"` (a purely
non-agent system: only `service`/`batch`/`light_io`, or a Temporal worker whose Activities are all
non-agent), STOP with `_halt_and_inform`:

> This system looks like a **pure compute/data migration** with no agentic component — no LLM
> agent loop, tool use, or model-backed reasoning. agent-advisor is focused on **agentic
> workloads** (choosing a runtime + model for AI agents), so it isn't the right fit here.
> For a straight compute migration, use the **`migration-to-aws`** main flow (containers, batch,
> services) or **`heroku-to-aws`**; for an LLM-SDK-to-Bedrock swap, use **`llm-to-bedrock`**.

Do NOT select a primary, ask questions, write answers.json, or score. This gate is the SINGLE
place the non-agent case is handled — every step after it (primary selection, questioning,
scoring, and every downstream phase) may assume ≥1 agent_session unit exists, so the primary is
always an agent unit. **It rarely fires:** the materialization above defaults a single described
workload to `agent_session`, so an ordinary "I have an idea for an agent" build_scratch run
passes; only a system UNAMBIGUOUSLY classified as all-non-agent halts. When in doubt (an ambiguous
single workload), treat it as `agent_session` and proceed.

- **System-level dimensions — asked once, apply to every unit:** `ops_preference`,
  `existing_cluster`, `multi_cloud`, `platform_fit`. Ask them in the first batch as
  today.
- **Primary unit:** the most complex `agent_session` unit (most tools / largest graph); confirm
  the default in the first batch ("I'll profile `<id>` in full — right one?"). (the scope gate above guarantees at least one agent_session unit exists, so the primary is always an agent unit;
  a purely non-agent system never reaches here.) The primary unit walks the FULL existing per-unit
  question set
  (`session_duration`, `traffic_pattern`, `session_state`, `isolation`,
  `memory_needs`, `multi_agent`, `framework`, `idle_resume`, `compute_tier`,
  `launch_concurrency`).
- **Every other unit: ONE batched delta question** — "How does `<id>` differ from
  `<primary>`? (session duration / traffic / compute / state / memory / isolation — name
  only what differs)". Parse the reply into per-dimension overrides; dimensions the
  user does not mention inherit the primary unit's answers. Non-agent units only need
  the dimensions their workload-classes rules read (traffic, duration, compute) —
  do not ask agent-only dimensions for them.
- **Temporal units (when `units` contains temporal units from Discover):**
  - **System-level Way question (asked ONCE):** "Temporal Cloud, self-hosted on AWS, or
    undecided?" — record `system.temporal_way` (`cloud` / `self_hosted` / `undecided`).
    Ask this only when temporal units exist. Current server state (detected
    `*.tmprl.cloud` endpoint vs self-hosted address) comes from Discover's temporal
    context — do not re-ask what was detected; this question is about the TARGET.
  - **`temporal_worker_poll` units:** take NO delta question. Their dimensions come from
    Tier 1 facts already in the temporal context (traffic shape, K8s reality) +
    `existing_cluster` (system-level).
  - **Agent-session Activity units (`agent_session` with temporal context):** are normal
    agent units whose answers are SEEDED from the adapter table in
    `agent-advisor-temporal.md § Tier 2 adapter`. Load that table; ask only
    dimensions the adapter maps to `unknown` (or that need user input per the adapter's
    rule). Dimensions the adapter can fill from temporal context (e.g., `session_duration`
    from max Activity runtime, `existing_cluster` from Tier 1) do NOT need a separate
    question here — they inherit from the adapter.
  - **No-code path:** when temporal units exist (detected by Discover, or declared at Intake
    on the no-code path), extend the gate from "temporal units from Discover" to "temporal
    units exist (any source)". For the no-code path, add one interview line: ask what the
    Activities do and classify them into units per `agent-advisor-temporal.md`
    Tier 2 (one batched question); every no-code temporal answer's rationale is labeled
    "based on interview, not code-verified". **This Activity classification is part of building
    the inventory — it runs BEFORE the scope gate concludes, so an agentic Temporal workload
    (Activities that classify as `agent_session`) is never falsely halted for having only a
    `temporal_worker_poll` seed.**

## Step 3 — Ask the core questions (AskUserQuestion, batched)

**First batch (ask these up front — they set the tone for the whole recommendation):**
`model_priority` (esp. cost) and `deployment_preference` (managed no-code vs bring-your-own),
unless already pre-filled in Step 2. These two decisions steer everything downstream, so surface
them early rather than mid-flow. Then collect the remaining keys in subsequent batches.

Collect answers for these keys. Legal values are fixed (Plan 1 Data Model):

- `session_duration`: under_15min | 15min_to_8hr | over_8hr | unknown
- `traffic_pattern`: bursty | steady | idle | unknown
- `session_state`: stateless | stateful | hitl | unknown
- `isolation`: required | nice_to_have | not_needed | unknown
- `memory_needs`: cross_session | session_only | none | unknown
- `ops_preference`: minimal | moderate | full_control | unknown
- `compute_tier`: light | heavy_non_gpu | gpu | unknown
- `idle_resume`: process_level | filesystem | none | unknown
- `launch_concurrency`: high | moderate | low | unknown
- `multi_agent`: yes | no | unknown
- `deployment_preference`: harness | framework | either | unknown — do you want a no-code
  **managed** agent runtime (AgentCore Harness — declare the agent as config, AWS runs the loop),
  bring your own **framework** code (Strands/LangGraph/CrewAI/custom on the runtime), or **either**
  (let the advisor pick)? Ask this early — it captures managed-vs-framework intent up front.
  Only affects the AgentCore deployment model, not the runtime score. Default: `either`.
- `framework`: strands | langgraph | crewai | custom | none | unknown
- `existing_cluster`: eks | ecs | none | unknown
- `multi_cloud`: yes | no | unknown
- `platform_fit`: ecs | eks | lambda | none | unknown
- `compliance` (multi-select list): none | soc2 | hipaa | pci | fedramp | gdpr | ccpa.
  Note: FedRAMP does NOT auto-eliminate AgentCore — AgentCore's FedRAMP authorization is in
  progress (WIP). If the user needs FedRAMP, Design surfaces a "verify current status" note and
  the GovCloud ECS/EKS fallback, rather than hard-eliminating AgentCore.
- model keys: `model_priority` (quality|speed|cost|balanced|unknown),
  `model_features` — the ONE most critical specialized feature; drives a hard model override
  (see `agent-advisor-model-selection.md`). Legal values:
  `tool_use | long_context | extended_thinking | rag | multimodal | image_generation | speech |
  embedding | none | unknown`. Ask only when priority is "specialized" or the user hints at a
  specific need (single-select — the most critical one).
  `current_model` (gpt4|gpt4o|gemini_flash|gemini_pro|claude|other|none|unknown) — migrate only.
- `region`: single | multi | global | unknown, plus (optionally) the specific region(s).
  Does NOT affect scoring — it gates two things in Design: (a) **availability** — AgentCore and
  especially Harness aren't in every region, so if the user's region doesn't support the
  recommended runtime, Design verifies via MCP and flags it; (b) **CRIS / data residency** — for
  EU users or when `compliance` includes `gdpr`, Design surfaces the geo-CRIS vs global-CRIS
  choice. Ask it; it's a compliance/feasibility gate, not a scoring input.

**Critical-question rule:** if `session_duration` is blank/unknown, **OR was only inferred by
Discover and not confirmed by the user**, ask it directly in chat before scoring — it gates hard
constraints, so an unconfirmed guess can silently eliminate runtimes. (Applies to every entry
point that reaches Clarify.)

## Step 4 — Write answers.json

Write `$RUN_DIR/answers.json` as:

```json
{
  "entry_point": "<from .phase-status.json (Intake wrote it there); passthrough unchanged>",
  "answers": {<primary unit's fully-merged dims (system + unit)>},
  "system": {<system dims>, "provenance": {"<dim>": "detected|asked|inherited|adapter|interview"}},
  "primary_unit": "<id>",
  "units": { "<id>": {"workload_class": "<class>", <per-unit dims>, "provenance": {"<dim>": "detected|asked|inherited|adapter|interview"}} }
}
```

**`entry_point` is read from `$RUN_DIR/.phase-status.json`** (Intake's Step 5 wrote it there —
it is NOT in context-signals.json, and context-signals.json does not exist on runs that skipped
Discover). A `migrate`/`build_deploy` run therefore keeps its real entry_point through scoring
(so agent-advisor-scoring.py applies migrate model-family mapping), instead of defaulting to `build_scratch`.

**Each unit's entry carries its `workload_class`** (from context-signals.json when Discover ran,
else from the no-code interview / grouping that produced the inventory). Persisting it here means
answers.json — which ALWAYS exists — is the single source scoring reads for the agent_session
filter; scoring never has to open context-signals.json (which is absent on skipped-Discover runs).

The **legacy mirror** (`entry_point` and `answers` at the top level) carries the same
values design.json and estimate.json write — the same pattern those phases use. `entry_point`
passes through unchanged. `answers` holds the PRIMARY unit's dimensions with system dims merged
in (exactly what downstream gcp-to-aws consumes). Single-unit runs therefore produce exactly
today's file PLUS the `primary_unit` and `units` keys. Each unit's entry in `units` is
COMPLETE (inheritance already applied — a reader never chases the primary to resolve a value).

**Provenance (additive):** dimension values stay flat; each unit's entry AND the `system`
block carry a sibling `provenance` map naming where each dimension's value came from —
`detected` (Discover/context-signals), `asked` (user answered in chat), `inherited`
(unmentioned in a delta question, inherited from the primary unit), `adapter` (seeded from
the Temporal Tier-2 adapter table), `interview` (no-code interview answer). Consumers that
ignore `provenance` keep working unchanged. Single-unit collapse: provenance is all
`detected`/`asked` — a harmless additive key.

## Step 5 — Run the scoring engine

Run scoring once per `agent_session` unit (agent-advisor-scoring.py is NOT modified — it is a pure
function; this loop is the only multiplicity). By the scope gate above at least one agent_session unit is
guaranteed, so `units{}` is never empty and there is always a scored primary to mirror:

```bash
# The scoring helper is loaded by file path, not imported by name — flattened, its filename
# contains hyphens and so is not a valid module name. All the loop needs is answers.json
# (ALWAYS present): each unit
# carries its own workload_class (persisted in Step 4) and entry_point is at the top level. This
# reads NO other file, so it works on runs that skipped Discover (no context-signals.json).
uv run python -c "
import json, importlib.util
_spec = importlib.util.spec_from_file_location('scoring', '$STEERING/agent-advisor-scoring.py')
scoring = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(scoring)
a = json.load(open('$RUN_DIR/answers.json'))
ep = a.get('entry_point', 'build_scratch')
units = {
    u: scoring.score({'entry_point': ep, 'answers': {**a['system'], **{k: v for k, v in info.items() if k not in ('workload_class', 'provenance')}}})
    for u, info in a['units'].items()
    if info.get('workload_class') == 'agent_session'
}
out = {'units': units}
# Collapse mirror: copy the primary agent unit's result to the top level so single-unit
# consumers that read scoring-result.verdict keep working (backward compat). The scope gate
# guarantees >=1 agent_session unit, so `units` is non-empty and a mirror always exists.
primary = a.get('primary_unit')
mirror = units.get(primary) or next(iter(units.values()))
out.update(mirror)
print(json.dumps(out, indent=2))
" > $RUN_DIR/scoring-result.json
```

(Once per agent unit, merging system + unit answers — excluding the `workload_class`/`provenance`
metadata keys — for each call; the file is `{ "units": { "<id>": <result> }, ...primary-unit
fields mirrored at top level }`. The top-level mirror is what single-unit consumers and the
legacy `scoring-result.verdict` read. The agent_session filter reads `workload_class` straight
from answers.json — no dependency on context-signals.json, which may not exist.)

Non-agent units are NOT scored — Design resolves them from
`agent-advisor-workload-classes.md`.

## Step 6 — Write state and continue to Confirm

Set `phases.clarify` = completed (leave `phases.confirm` = pending). Do NOT jump to Design.
The state machine now routes to **Confirm** (`agent-advisor-confirm.md`), which
confirms the deployment model / services / co_recommend pick and writes `confirm.json` — Design and
the diagram require it.
