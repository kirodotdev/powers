---
_phase: migration-plan
_title: "Migration Plan — inline execution of gcp-to-aws phases"
_requires_phase: generate
_input:
  - design.json
  - confirm.json
  - answers.json
_fragments:
  - _id: migration-plan-gcp-constraints
    _trigger: { _when: "always (gcp-to-aws is the migration engine)" }
    _file: agent-advisor-migration-plan-gcp-constraints.md
_assemble:
  _file: agent-advisor-migration-plan-assemble.md
_produces:
  - { file: migration-plan-injection.json, _when: "the target repo exists (not an idea-only migrate — otherwise migration_plan is not_applicable and the phase stops)" }
_advances_to: poc
_preconditions:
  - _check_phase_completed: generate
    _on_failure: _halt_and_inform
_postconditions:
  - _assert: "unless migration_plan was set not_applicable (idea-only) — migration-plan-injection.json exists and is valid JSON, carrying the translated injected constraints, the advisor rationale, and the absolute repo + migration_dir paths"
    _on_failure: _halt_and_inform
  - _assert: "the inline engine's Generate phase reached HANDOFF_OK (aws-design-ai.json exists with a non-empty ai_architecture in the recorded migration_dir), and migration_plan_ctx {repo, migration_dir} was recorded in .phase-status.json"
    _on_failure: _halt_and_inform
  - _assert: "model reconciliation (Step 3.5) is settled — for every unit whose plan-chosen Bedrock model differs from its design.json model, design.json.units[<id>].model_recommendation.model now equals the plan's model, the unit carries model_refined_by_plan: true, and recommendation.md AND recommendation-report.html name that unit's new model at every occurrence (table row, Mermaid node, ASCII overview, prose, and all-units roll-up/summary sentences) with no stale model left as that unit's chosen model; when no unit's model differs, this is a no-op"
    _on_failure: _halt_and_inform
---

# Phase: Migration Plan — inline execution of gcp-to-aws phases

Reached after Generate when the user confirmed **Gate 1** (offered in agent-advisor-generate.md Step 6).
This phase produces a complete migration plan by directly reading and executing
the gcp-to-aws engine's phase instruction files, which are flat steering files in this
same namespace — no separate invocation, no turn boundary. Everything runs inside the current agent-advisor session, so Steps 5–6
(record artifacts, offer Gate 2) execute in the same turn without interruption.

gcp-to-aws files are **read-only**: this phase never edits them.

## Path definitions (resolve first, before any other step)

```
$GCP_BASE = $STEERING
```

**IMPORTANT — path resolution:** the gcp-to-aws engine is FLAT. Every one of its
instruction files lives directly in `$STEERING` under its own flattened name, so there
are no references, design-refs, clustering, phases, shared, or data
subdirectories to resolve. Where a gcp instruction names a bare file, read
`$STEERING/<that filename>`. Design references are prefixed `design-ref-`; the lookup
table from a GCP resource type to its reference is `$STEERING/design-ref-index.md`.
`$MIGRATION_DIR` is the exception — it stays under the target repo per Step 1, not under
`$STEERING`.

Examples:

- `cached-prices.md` → `cached-prices.md`
- `sdk-capability-map.json` → `sdk-capability-map.json`
- `clustering-classification-rules.md` → `clustering-classification-rules.md`

## Step 0 — Update agent-advisor state immediately

Before doing anything else, read-merge-write agent-advisor's `.phase-status.json`:

- `current_phase` = `"migration_plan"`
- `phases.migration_plan` = `"in_progress"`

This must happen **first** so that if the session is interrupted at any point, the advisor
resumes at agent-advisor-migration-plan.md rather than at agent-advisor-generate.md.

## Step 1 — Resolve the target repo and set $MIGRATION_DIR

The plan needs the repo containing the workload to migrate. If Discover ran (`phases.discover
== "completed"`), reuse the repo path the user gave then (from `context-notes.md` or
`context-signals.json`). Otherwise ask for it now. Resolve to an absolute path (`$REPO`).

If the user has no code (idea-only migrate), STOP: tell them a migration plan needs an
existing workload, set `phases.migration_plan = "not_applicable"`, and continue to the Gate
2 branch in agent-advisor-generate.md Step 7.

Set `$MIGRATION_DIR` using the gcp-to-aws convention: `$REPO/.migration/<MMDD-HHMM>/`
(current timestamp). Create the directory and `.migration/.gitignore` (`*\n!.gitignore`).
All gcp-to-aws artifacts are written here.

## Step 2 — Assemble the injection context

Read ALL of: `$RUN_DIR/answers.json`, `$RUN_DIR/design.json`, `$RUN_DIR/confirm.json`, and
`$RUN_DIR/handoff-summary.md`. If `handoff-summary.md` does not exist (build_deploy path),
write it first by following `agent-advisor-handoff-migration.md` Step 1, then return.

**`answers.json` is nested:** shape is `{"entry_point": "...", "answers": {...}}`.
Every answer key is read from the inner `answers` object.

Build the injection context — this is carried forward into every gcp-to-aws phase execution
as the set of already-determined constraints. Translate per this table (never inject `unknown`).
The translated constraint fields derive from the PRIMARY unit (`answers.json.primary_unit`) —
consistent with design.json's legacy mirror; gcp's existing consumption is unchanged:

| Source                                                                             | Inject as (gcp-to-aws field)                | Translation                                                                    |
| ---------------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------ |
| `design.json.deployment_model == "harness"`                                        | `ai_constraints.agentic.migration_approach` | `"harness"`                                                                    |
| `deployment_model == "framework_on_runtime"` AND `.answers.framework == "strands"` | same                                        | `"strands"`                                                                    |
| `deployment_model == "framework_on_runtime"` (langgraph/crewai/custom)             | same                                        | `"retarget"`                                                                   |
| winning runtime NOT agentcore (ecs/eks/lambda/lambda_microvms/batch/fargate)       | same                                        | `"retarget"` + compute note                                                    |
| `.answers.memory_needs`                                                            | `ai_constraints.agentic.memory_requirement` | `cross_session`→`"cross_session"`, `session_only`→`"session"`, `none`→`"none"` |
| `.answers.session_duration`                                                        | `ai_constraints.agentic.task_duration`      | `under_15min`→`"medium"`, `15min_to_8hr`→`"long"`, `over_8hr`→`"very_long"`    |
| `.answers.region` — only when a **specific** region was named                      | `design_constraints.target_region`          | pass through; bare single/multi/global → do not inject                         |
| `ai_constraints.agentic.incremental_migration`                                     | —                                           | never injected                                                                 |

**Non-AgentCore verdicts:** inject `migration_approach: "retarget"` and add a note:
"Compute target is `<runtime>` per agent-advisor scoring — do not recommend AgentCore
Runtime as the compute layer."

**Consolidated platform overrides the top-level approach.** The table above reads the
top-level legacy mirror (the PRIMARY unit's fields). When `design.json.platform.mode ==
"consolidated"`, the whole system deploys on `platform.runtime` (the superset), NOT the
primary unit's own verdict/deployment_model. So when consolidated:

- Derive `migration_approach` from `platform.runtime`, not the primary unit's
  `deployment_model`: any non-AgentCore superset (`ecs` / `eks` / `lambda` / `lambda_microvms`)
  → `"retarget"` + the compute note ("Compute target is `<platform.runtime>` for ALL units per
  the consolidation decision — do not recommend AgentCore Runtime"). Only inject
  `"harness"`/`"strands"` when the superset is itself AgentCore (rare — consolidation is usually
  onto ECS/EKS). The rule is: harness/strands ONLY when `platform.runtime == "agentcore"`, else
  retarget — so a primary unit that scored AgentCore never leaks harness into a Lambda/MicroVMs
  consolidation.
- The AgentCore endpoint/services note follows `platform.runtime`, NOT the primary unit's raw
  verdict: inject it ONLY when `platform.runtime == "agentcore"` (a consolidation onto AgentCore
  — still tell the engine to implement `POST /invocations` + `GET /ping` and the confirmed
  services). When the superset is NOT AgentCore (ecs/eks/lambda/lambda_microvms), do NOT inject
  the AgentCore note even if the primary unit scored AgentCore — its AgentCore services do not
  apply on the superset. (Split mode is unchanged: the note follows each unit's own runtime.)

This keeps the top-level injection consistent with the per-unit rows (which already use each
unit's `effective_runtime` as `target_runtime`) and with what the POC actually deploys.

**AgentCore endpoint note — PER UNIT, keyed on each unit's `effective_runtime`:** attach the
deployment-target note to EVERY unit whose `effective_runtime == "agentcore"`, NOT just the
primary/winning unit. (This is a serving requirement of the target runtime, NOT a
migration-approach constraint — it does not conflict with `retarget`.) The note text: "The app
will be deployed on AgentCore Runtime, which invokes it via `POST /invocations` and health-checks
it via `GET /ping`. The Design phase's `code_migration` output should account for exposing these
entrypoints alongside the app's existing interface." Because gcp-to-aws has no per-unit schema
field for this, carry it inline on that unit's row (an `endpoint_contract` string on the row, or
appended to the row's context) — do NOT collapse it to a single top-level note keyed on the
primary. So in a split system with primary=Lambda + a secondary AgentCore unit, the AgentCore
unit STILL gets the `/invocations`+`/ping` note while the Lambda unit does not; under a
consolidation the note appears iff `platform.runtime == "agentcore"` (every unit's
effective_runtime is then agentcore). The POC phase tolerates the note's absence from
`aws-design-ai.json` and applies the standard AgentCore contract regardless.

Inject the FULL unit set: for each `design.json.units[]` entry, one AI-architecture
input row — using `unit.effective_runtime` as `target_runtime` (Design already resolved it:
platform.runtime when consolidated, else the unit's resolved verdict — never `co_recommend`),
`unit.model_recommendation` (→ model), and `unit.agentcore_services` (→ services).

**`deployment_model` MUST be consistent with `target_runtime`, not carried raw.** A raw
`deployment_model: "harness"` comes from an AgentCore verdict; if the unit's effective runtime
is NOT agentcore (e.g. consolidated onto ECS, or a co_recommend pick that landed on Lambda),
`harness` is meaningless there. Rule: inject `deployment_model` only when `target_runtime ==
"agentcore"`; otherwise inject `"framework_on_runtime"` (the code runs as-is on the container/
function runtime — a container image or zip, no Harness). Never emit `target_runtime: ecs`
with `deployment_model: harness`.

The unit's raw `verdict` still rides along in `raw_verdict` so the report can show what
consolidation traded away. Each row also carries `"evidence": "<path>"` from the matching
`context-signals.json.units[]` entry (matched by `unit.id`) — this is the correlation key
that enables Tier 2 alignment (evidence paths are how gcp workloads are joined to units).
The platform block rides along (`consolidated`/`split`, interconnect).
gcp-to-aws still runs ONCE for the whole system — units are inputs to its AI-architecture
sections, not separate engine runs. Single unit: identical to today's injection plus the
one-row table.

Write the injection context to `$RUN_DIR/migration-plan-injection.json`:

```json
{
  "injected_constraints": {/* the translated fields above */},
  "deployment_target_note": "<system-level AgentCore entrypoint note: set only when platform.runtime==agentcore (consolidation onto AgentCore); null otherwise. Per-unit AgentCore units carry their own note in units[].endpoint_contract — do NOT rely on this top-level field for a split system's secondary AgentCore unit>",
  "units": [
    {
      "unit_id": "<from design.json.units[].id>",
      "workload_class": "<from unit.workload_class>",
      "target_runtime": "<effective runtime: platform.runtime when platform.mode==consolidated, else unit.verdict>",
      "raw_verdict": "<from unit.verdict — the split-mode verdict, for report trade-off display>",
      "deployment_model": "<unit.deployment_model when target_runtime==agentcore, else 'framework_on_runtime'>",
      "endpoint_contract": "<the POST /invocations + GET /ping note when target_runtime==agentcore, else null — PER UNIT, so a secondary AgentCore unit in a split system still carries it>",
      "model": "<from unit.model_recommendation>",
      "services": "<from unit.agentcore_services[]>",
      "evidence": "<from context-signals.json.units[].evidence, matched by unit.id>"
    }
  ],
  "platform": {
    "mode": "<from design.json.platform.mode>",
    "interconnect": "<from design.json.platform.interconnect>"
  },
  "advisor_rationale": "<top 3 scoring signals from handoff-summary.md>",
  "repo": "<abs $REPO>",
  "migration_dir": "<abs $MIGRATION_DIR>"
}
```

**Suppression is best-effort:** gcp-to-aws's Clarify may still ask questions whose answers
were injected — present the injected value as the pre-selected default so the user can
confirm with one keypress.

## Step 2.5 — Load global constraints

Read `agent-advisor-migration-plan-gcp-constraints.md` and follow everything in it
for the duration of this phase. It covers: design principles (dev sizing, no human costs,
re-platform default, BigQuery gate), context loading budget, conditional file table,
feedback sidebar auto-skip, and hybrid stack warning.

## Step 3 — Announce the transition

Tell the user:

> "I'm now generating the full migration plan. I'll run the migration analysis directly
> (Discover → Clarify → Design → Estimate → Generate) in this same session, so your
> runtime and deployment choices carry over — you won't be asked those again. It may ask
> a few additional questions that weren't covered above, such as monthly AI spend and
> migration priority."

## Step 4 — Execute gcp-to-aws phases in order

Execute each phase by reading its instruction file and following it **exactly** as if it
were loaded by gcp-to-aws's own state machine. The path rule from the header applies: all
relative references in those files resolve from `$GCP_BASE`.

**Two separate state files — do NOT mix them up:**

- `$MIGRATION_DIR/.phase-status.json` — gcp-to-aws's own state. Each phase file
  (agent-advisor-discover.md, agent-advisor-clarify.md, etc.) writes and reads this file itself per its own protocol.
  agent-advisor-migration-plan.md does NOT touch it — let each phase file manage it.
- `$RUN_DIR/.phase-status.json` — agent-advisor's state. Already set to
  `current_phase = "migration_plan"` in Step 0 and NOT touched again until Step 5.
  gcp-to-aws's files never read or write this file (they only know about `$MIGRATION_DIR`).

This separation is what keeps the two state machines independent. After each phase's
`HANDOFF_OK`, simply proceed to the next phase — no extra state writes needed.

### Phase A — Discover

Read and execute: `discover.md`

Key behaviors:

- `$MIGRATION_DIR` is already created (Step 1) — when agent-advisor-discover.md Step 0 checks for
  existing runs, the directory exists but has no `.phase-status.json` yet → treat as
  fresh run (skip the resume/fresh/cancel prompt)
- agent-advisor-discover.md writes its own `.phase-status.json` to `$MIGRATION_DIR` — let it do so
- Injection context is NOT applied at this stage; it's carried as live context for Clarify
- On `HANDOFF_OK`: `ai-workload-profile.json` (and/or IaC artifacts) present in `$MIGRATION_DIR`

### Phase B — Clarify

Read and execute: `clarify.md`
(which in turn loads `clarify-ai-only.md` or `clarify-ai.md` as appropriate)

Key behavior — apply injection context:
When Clarify asks a question whose answer is already in the injection context (Step 2),
treat it as extracted (`chosen_by: "extracted"`) and do NOT re-ask it — present it in the
detection summary as pre-filled. Only ask what remains (typically: monthly AI spend, migration
priority, cross-cloud preference).

Also inject `design_constraints.target_region` into `preferences.json` directly when a
specific region was named (mark `chosen_by: "extracted"`).

On `HANDOFF_OK`: `preferences.json` present in `$MIGRATION_DIR`.

### Phase C — Design

Read and execute: `design.md`
(which routes to `design-ai.md`, `design-infra.md`, etc.)

**Key behavior — unit correlation (multi-unit runs only):**

After design-ai reaches HANDOFF_OK and writes `aws-design-ai.json` to `$MIGRATION_DIR`,
YOU (the advisor's migration-plan interpreter) annotate each design_block with advisor
unit context — this is a post-write annotation of the artifact FILE; gcp's instructions
are not modified and gcp never sees this step:

1. Read `aws-design-ai.json` → `design_blocks[]` (gcp's per-workload design output)
2. For each design_block, match its `source_paths[]` against the injected units' `evidence` fields (from Step 2)
3. If a match is found (any source path overlaps with evidence): ANNOTATE the design_block with ADDITIVE keys:
   - `"advisor_unit": "<unit_id>"`
   - `"advisor_target_runtime": "<target_runtime>"`
   - For non-agent units: `"advisor_compute_note": "compute layer fixed to <target_runtime> per agent-advisor (rule cited in design.json); do not re-map"`
4. If no match is found (no evidence overlap): annotate `"advisor_unit": null` — visible, not guessed
5. When agent-class units have DIFFERING migration approaches (multiple agent units with different `deployment_model` values), record on the non-primary unit's block:
   `"advisor_approach_note": "this unit's approach is <deployment_model> per advisor; the plan's code_migration follows the primary unit — see Tier-1 proposal"`

**Additive-only rule:** These annotations are purely ADDITIVE — never modify or remove any gcp-written fields. gcp's own validation checklists must keep passing.

### Step 3.5 — Reconcile the model choice (plan wins, but the recommendation must not lie)

The advisor injected each unit's `model_recommendation` (Step 2) as the gcp engine's model
constraint, but the engine's AI-design phase may **refine** it — the plan sees the _source_
model per unit (e.g. `gpt-4o-mini` vs `gpt-4o`) and the per-workload task, so it may pick a
different, better-fitting Bedrock model than the advisor's family-level baseline (e.g. a
`gpt-4o-mini` binary-moderation unit → Nova Lite, not the balanced-baseline Sonnet). **The
plan's per-unit model wins** — it is finer-grained and region-validated. But the advisor's
own `design.json` and `recommendation.md`/`recommendation-report.html` were written _before_
the plan ran, so a stale model there would contradict the POC (which reads the plan-backed
model in `agent-advisor-poc.md` Step 2). Reconcile so the deliverables agree:

For each design_block matched to a unit (Step 3) **whose `model_recommendation` is non-null**,
compare the block's chosen target Bedrock model (`target_bedrock_model`, or the block's first
`bedrock_models[].aws_model_id`) against that unit's injected `model` (from
`design.json.units[<id>].model_recommendation.model`). **Skip model-less units** — a non-agent
unit (batch/service/light_io) can have `model_recommendation: null`; it has no model to reconcile,
so leave it null and do NOT dereference `.model`:

1. **If they name the same model** — nothing to do.
2. **If they differ** — the plan wins. You MUST do BOTH of the following:

   **(a) Update `design.json`** for that unit:
   - Set `units[<id>].model_recommendation.model` to the plan's model id.
   - Append to `units[<id>].model_recommendation.reasoning`:
     `" — refined by the migration plan (was <old model>): <the plan's block rationale>"`.
   - Set `units[<id>].model_refined_by_plan` to `true` (a top-level key ON THE UNIT, a
     sibling of `model_recommendation` — NOT inside it) so the change is auditable. This key
     is mandatory whenever you changed the model; a reconciled unit with no
     `model_refined_by_plan: true` is a bug.

   **(b) Back-write the recommendation in BOTH `recommendation.md` AND
   `recommendation-report.html`.** The stale model id can appear in MORE THAN ONE place per
   file — you must replace EVERY occurrence for that unit, not just the first. Grep each file
   for the old model id/key and check at least these locations before you finish:
   - the per-unit verdict/summary table row (e.g. `| content-review | … | <model> | …`);
   - the **Mermaid architecture diagram** node labels (e.g.
     `content_review_node["AWS Lambda<br/><model>"]` in the `mermaid` block);
   - any **ASCII/plain-text overview or unit list** (e.g. `[ content-review: … (<model>) ]`);
   - any prose sentence naming that unit's model;
   - **roll-up / summary statements that collapse ALL units into one model** — these are the
     easily-missed ones. The executive summary, a section header, or a lede often say
     something like "all three agents migrate from OpenAI to Claude Sonnet 4.6." Once one
     unit is refined to a different model, that blanket claim is FALSE and must be corrected
     (e.g. "support-chat and insights-writer → Claude Sonnet 4.6; content-review → Nova Lite").
     Check the exec summary, every section header, and any opening/closing sentence.
   - in the HTML, ALL of the above surfaces (table cell, SVG/Mermaid label, inline text,
     AND the lede/summary sentences).
     Replace the stale model everywhere it names or implies THIS unit, then add a one-line note
     in that unit's section:
     `"Model refined by the migration plan: <old model> → <new model> (<rationale>)."`
     After editing, re-grep both files for the OLD model id/name scoped to this unit — it must
     return zero hits AS THIS UNIT'S MODEL. Pay special attention to blanket phrases like
     "across all three", "all agents", "every unit" sitting next to the old model name: if such
     a phrase still implies this unit uses the old model, it is a miss. The old id may still
     legitimately appear elsewhere (another unit's model, or a "backup: Haiku 4.5" note), but
     never as THIS unit's chosen model and never inside an all-units roll-up.
     Keep every other section untouched; this is a targeted find-and-replace on this unit's
     model only, NOT a re-render of the report.
3. Never invent a model here — only carry across the id the plan already chose and
   region-validated.

**Single-unit runs:** SKIP the unit-correlation overlay above (steps 1–5) — the collapse
invariant means zero annotation behavior change when there's only one unit. Step 3.5 model
reconciliation still applies: reconcile the one unit's model (the same stale-recommendation
risk exists), but there is no per-unit ambiguity.

On `HANDOFF_OK`: `aws-design-ai.json` (and/or other design artifacts) present, with unit annotations when multi-unit.

### Phase D — Estimate

Read and execute: `estimate.md`

On `HANDOFF_OK`: `estimation-ai.json` (and/or other estimate artifacts) present.

### Phase E — Generate

Read and execute: `generate.md`
(which routes to `generate-ai.md`, `generate-artifacts-ai.md`, etc.)

**Context firewall (important — gcp-to-aws is read-only and owns its own output).** Every
artifact this phase produces — including `migration-report.html` — is rendered ENTIRELY by
gcp-to-aws's own generator templates, exactly as if gcp-to-aws ran standalone. Do NOT apply
agent-advisor's `agent-advisor-report-shell.md` (its `.doc-head`, `--ink` tokens, numbered
document sections, unit cards, etc.) to any gcp artifact. The v3 document shell is for
agent-advisor's OWN `recommendation-report.html` only; `migration-report.html` must keep
gcp-to-aws's native layout (its "GCP to AWS Migration Assessment" header, Executive Summary,
verdict badge, Appendix A–G). If the advisor shell is still in your context from this run's
earlier Generate, discard it here — follow gcp's report instructions verbatim.

The MIGRATION_GUIDE's AI sections carry the unit annotations through: each annotated
workload section names its `advisor_unit` and target runtime (from the design_blocks[]
annotations in Phase C).

**Skip the Feedback phase** — feedback is optional user telemetry and produces no data
artifacts needed by the POC. After generate's `HANDOFF_OK`, go directly to Step 5 below
— do NOT load `feedback.md`.

On `HANDOFF_OK`: `generation-ai.json` + `MIGRATION_GUIDE.md` + `README.md` + artifact
files present in `$MIGRATION_DIR`.

## Step 5 — Record context and validate artifacts

Read-merge-write `$RUN_DIR/.phase-status.json`:

- `phases.migration_plan` = `"completed"`
- `migration_plan_ctx` = `{"repo": "<abs $REPO>", "migration_dir": "<abs $MIGRATION_DIR>"}`

Verify `$MIGRATION_DIR/aws-design-ai.json` exists and has a non-empty `ai_architecture`.
If missing → AI path did not complete; show the error, set `phases.migration_plan =
"in_progress"`, and stop. `estimation-ai.json` may be absent on some routes — note it,
don't fail.

**Verdict check:** if agent-advisor's winning runtime is NOT agentcore but the produced
plan centers AgentCore as the compute layer, surface the disagreement explicitly: show
both choices, state that agent-advisor's deterministic scoring is authoritative, and let
the user decide.

## Step 5.5 — Regenerate the architecture diagram (plan-backed)

The diagram written during Generate is the generic Path 1 selection diagram — it does not
show the app's real components. Now that `aws-design-ai.json` exists, re-generate it as the
**Path 2 plan-backed app architecture**: load `agent-advisor-build-diagram.md` and
follow its **Path 2**, overwrite `$RUN_DIR/diagram.md`, and re-embed the new diagram into
Section 4 of `$RUN_DIR/recommendation.md` (replacing the Path 1 diagram). If an HTML report
was already generated, note that it will show the updated diagram only if regenerated — it
is acceptable to leave the HTML report's diagram as-is (it links to recommendation.md for
the authoritative version).

## Step 5.6 — Inject the help banner into the migration report (post-process)

gcp-to-aws's Generate produces `$MIGRATION_DIR/migration-report.html` in gcp-to-aws's OWN
native format (see the Context firewall in Phase E — do not restyle it). gcp-to-aws is
read-only, so do NOT edit its report generator. This step is a SURGICAL, ADDITIVE-ONLY
post-process of the OUTPUT file — inject ONLY the help banner, change NOTHING else:
load `agent-advisor-report-help-banner.md` and check its `banner_status` FIRST. **While
`banner_status` reads `SUPPRESSED` (current state — the support page is not launched), SKIP
this injection entirely: inject NO CSS and NO HTML, leave `migration-report.html` untouched.**
Only when it reads `LIVE` do the following: if `migration-report.html` exists, inject the
banner's CSS rules before `</style>` (or add a new `<style>` before `</head>` if none) and
the banner's HTML block at the TOP — right after the opening `<body>` / the report's header,
before the first content block, substituting `{{ HELP_URL }}`. Do NOT touch the report's
existing markup, sections, classes, or CSS tokens — the banner is a self-contained addition.
This gives the migration report the same top-of-page "Need help?" CTA as the recommendation
and POC reports, without touching gcp-to-aws or its layout. If the file doesn't exist (report
generation was skipped), skip this step silently.

## Step 6 — Offer Gate 2 (immediately after gcp-to-aws Generate's own summary)

gcp-to-aws's `agent-advisor-generate.md` already outputs a full structured summary (artifacts produced,
timelines, risks, TODOs, next steps) — that IS the plan summary. Do not re-summarize it.

Immediately after that summary, add ONE follow-up message that contains:

1. The recommendation one-liner: "Recommendation: `<runtime>` + `<deployment model>`, model `<model>`"
2. Gate 2 via AskUserQuestion:

> "Do you want a deployable proof-of-concept for this recommendation? I'll generate the
> agent code, deployment plan, and scripts."
>
> - **Yes** → set `phases.poc = "in_progress"`, load `agent-advisor-poc.md`
> - **No** → set `phases.poc = "skipped"` — flow complete

Gate 2 is asked for the primary unit's `effective_runtime` (agentcore / ecs / eks / lambda /
lambda_microvms — the primary is always an agent unit per Clarify's scope gate). Each non-primary
unit still gets its own POC per agent-advisor-poc.md Step 3 dispatch, whose shape follows that unit's
effective_runtime (incl. batch / fargate / serverless_workers).

## Failure handling

If any phase fails mid-execution (error in a tool call, user aborts): keep all previously
written artifacts, set `phases.migration_plan = "in_progress"` (resumable — re-entering
this phase checks `$MIGRATION_DIR/.phase-status.json` and resumes from the last completed
phase). Then, by entry point:

- `build_deploy`: offer Gate 2 with the fallback clearly labeled — POC from `design.json`
  only, not plan-backed.
- `migrate`: no fallback POC. Offer to resume the migration plan later, or end with
  Stage 1 outputs + `handoff-summary.md`.
