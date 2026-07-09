# AI-Only Migration — Clarify Requirements

**Standalone flow** — Used when ONLY `ai-workload-profile.json` exists (no infrastructure or billing artifacts). Infrastructure stays on GCP; only AI/LLM calls move to AWS Bedrock.

Produces the same `preferences.json` output but with `design_constraints` limited to region and `ai_constraints` fully populated. Questions are presented in **two progressive batches** with an intermediate save — partial answers persist across sessions.

---

## Step 0: Prior Run Check

Check `$MIGRATION_DIR/` for existing state:

**Case 1 — Completed preferences exist** (`preferences.json` present):

> "I found existing migration preferences from a previous run. Would you like to:"
>
> A) Re-use these preferences and skip questions
> B) Start fresh and re-answer all questions

- If A: skip to Step 3 (Validation), proceed with existing file.
- If B: delete `preferences.json`, continue to Step 1.

**Case 2 — Draft preferences exist** (`preferences-draft.json` present, no `preferences.json`):

> "I found a partial set of answers from a previous session (1 of 2 batches completed). Would you like to:"
>
> A) Resume from where you left off — I'll pick up the remaining questions
> B) Start fresh and re-answer all questions

- If A: load the draft, skip Batch 1 in Step 2, present Batch 2 directly.
- If B: delete `preferences-draft.json`, continue to Step 1.

**Case 3 — No prior state**: Continue to Step 1.

---

## Step 1: Present AI Detection Summary

> **AI-Only Migration Detected**
> Your project has AI workloads but no infrastructure artifacts (Terraform, billing). I'll focus on migrating your AI/LLM calls to AWS Bedrock while your infrastructure stays on GCP.
>
> **AI source:** [from `summary.ai_source`]
> **Models detected:** [from `models[].model_id`]
> **Capabilities in use:** [from `integration.capabilities_summary` where true]
> **Integration pattern:** [from `integration.pattern`] via [from `integration.primary_sdk`]
> **Gateway/router:** [from `integration.gateway_type`, or "None (direct SDK)"]

---

## Step 1.5: Fast-Path Check

If `migration-preview.json` exists and `ai_complexity_signal == "likely_simple"` (single model, non-agentic, no multi-provider, no multi-model routing):

> "Your AI migration looks straightforward — one model swapping to Bedrock. I only need 3 quick answers to complete your migration plan."

Present **only Q2, Q3, Q4** (Q1 framework is extracted; Q5 model is extracted; Q6 capabilities are extracted; Q7–Q10 use defaults). After answering, skip directly to Step 3.

If `ai_complexity_signal` is `"standard"` or `"complex"`, or `migration-preview.json` is absent, continue to Step 2 (full question set).

---

## Step 2: Ask Questions in Progressive Batches (Q1–Q10)

Questions are presented in two batches with a save after the first. The user can skip individual questions (defaults applied), say **"use defaults for the rest"** to apply defaults for all remaining questions and proceed immediately, or answer normally.

### Batch 1 — AI Strategy & Setup (Q1–Q5)

Present with this intro:

```
Before designing your Bedrock migration, I have two short sections of questions.
You can answer each, skip individual ones (I'll use sensible defaults),
or say "use defaults for the rest" at any point.

Let's start with your AI strategy and current setup.

--- AI Strategy & Setup ---
```

## Q1 — AI framework or orchestration layer (select all that apply)

Same decision logic, auto-detect signals, and interpretation as Q14 in `clarify-ai.md`.

Auto-detect: No framework → A, LiteLLM/OpenRouter/Kong/Apigee → B, LangChain/LangGraph → C, CrewAI/AutoGen → D, OpenAI Agents SDK → E, MCP/A2A → F, Vapi/Bland.ai/Retell → G.

_Skip when:_ `integration.gateway_type` AND `integration.frameworks` are both populated in `ai-workload-profile.json` — use extracted values with `chosen_by: "extracted"` and do not present this question.

> A) No framework — direct API calls | B) LLM router/gateway | C) LangChain / LangGraph | D) Multi-agent framework | E) OpenAI Agents SDK | F) MCP/A2A | G) Voice platform

Interpret → `ai_framework` array. Default: auto-detect, fallback `["direct"]`.

## Q2 — What matters most for your AI application?

> A) Best quality/reasoning | B) Fastest speed | C) Lowest cost | D) Specialized capability (→ Q10) | E) Balanced | F) I don't know

| Answer   | Model Impact                                                |
| -------- | ----------------------------------------------------------- |
| Quality  | Claude Sonnet 4.6 primary; Opus 4.7 / 4.6 for hardest tasks |
| Speed    | Claude Haiku 4.5; also Nova Micro/Lite                      |
| Cost     | Claude Haiku 4.5 or Nova Micro                              |
| Special  | Deferred to Q10                                             |
| Balanced | Claude Sonnet 4.6                                           |

Interpret → `ai_priority`. Default: E → `"balanced"`.

## Q3 — Monthly AI spend on OpenAI or Gemini?

> A) < $500 | B) $500–$2K | C) $2K–$10K | D) > $10K | E) Don't know

Interpret → `ai_monthly_spend`. Default: B → `"$500-$2K"`.

## Q4 — Cross-cloud API call concerns

Unique to AI-only: infrastructure stays on GCP while AI calls route to AWS.

> A) Latency critical — AI in hot path | B) Latency acceptable — async/users can wait | C) Concerned about egress costs | D) Want to test first — parallel running

| Answer           | Impact                                         |
| ---------------- | ---------------------------------------------- |
| Latency critical | VPC endpoint; closest region to GCP deployment |
| Acceptable       | Standard endpoint; region by cost              |
| Egress concerned | PrivateLink; egress cost analysis              |
| Test first       | Phased migration; parallel running guidance    |

Interpret → `cross_cloud`. Default: B → `"latency-acceptable"`.

## Q5 — Current model in use?

Establishes baseline Bedrock recommendation. Override hierarchy: Q10 special features > Q2 priority > Q7/Q8 volume/latency > Q5 baseline.

_Skip when:_ `models[].model_id` is populated in `ai-workload-profile.json` — auto-detect from detected model IDs with `chosen_by: "extracted"` and do not present this question. The detected models are already shown in the Step 1 summary.

> A) Gemini Flash | B) Gemini Pro | C) GPT-3.5 Turbo | D) GPT-4/4 Turbo | E) GPT-4o | F) GPT-5.4/Mini/Nano | G) GPT-5/5.x (older) | H) GPT-5.5/Pro | I) o-series | J) Claude (Anthropic SDK) | K) Other/Multiple | L) Don't know

| Source         | Baseline Recommendation           | Pricing Context                    |
| -------------- | --------------------------------- | ---------------------------------- |
| Gemini Flash   | Claude Haiku 4.5 ($1/$5)          | Strong savings                     |
| Gemini Pro     | Claude Sonnet 4.6 ($3/$15)        | Comparable tier                    |
| GPT-3.5 Turbo  | Claude Haiku 4.5 ($1/$5)          | Faster and cheaper                 |
| GPT-4/4 Turbo  | Claude Sonnet 4.6 ($3/$15)        | Major savings (GPT-4T: $10/$30)    |
| GPT-4o         | Claude Sonnet 4.6 ($3/$15)        | Modest savings on output           |
| GPT-5.4        | Claude Sonnet 4.6 ($3/$15)        | ~5% cheaper on OpenAI; near parity |
| GPT-5.4 Mini   | Nova Lite ($0.06/$0.24)           | 94% cheaper on Bedrock             |
| GPT-5.4 Nano   | Nova Micro ($0.035/$0.14)         | 87% cheaper on Bedrock             |
| GPT-5.4 Pro    | Nova 2 Pro ($1.38/$11)            | 94% cheaper on Bedrock             |
| GPT-5/5.x      | Claude Sonnet 4.6 ($3/$15)        | Savings story is quality, not cost |
| GPT-5 flagship | Claude Opus 4.7 / 4.6 ($5/$25)    | Cheaper than GPT-5 Pro ($15/$120)  |
| o-series       | Sonnet 4.6 with extended thinking | o1 $15/$60 → significant savings   |
| Claude (any)   | Same model on Bedrock             | Client swap only — no model change |

Override examples: GPT-4 + Q2=cost → Haiku; Flash + Q10=extended thinking → Sonnet; GPT-4o + Q10=speech → Nova 2 Sonic; GPT-5.5 + Q2=cost → Sonnet 4.6.

Interpret → `ai_model_baseline`. Default: auto-detect, fallback Q2 priority-based.

### Batch 1 → Save Draft and Present Batch 2

After the user responds to Batch 1:

1. Interpret all Batch 1 answers (apply interpret rules above; apply defaults for skipped questions).
2. Write `$MIGRATION_DIR/preferences-draft.json` with Batch 1 answers:

```json
{
  "metadata": {
    "draft": true,
    "batches_completed": ["ai-strategy"],
    "batches_remaining": ["ai-technical"],
    "migration_type": "ai-only",
    "timestamp": "<ISO timestamp>",
    "discovery_artifacts": ["ai-workload-profile.json"],
    "questions_asked": ["Q1", "Q2", ...],
    "questions_defaulted": [...]
  },
  "design_constraints": { ... },
  "ai_constraints": { ... }
}
```

1. Present Batch 2:

```
Got it — your AI strategy preferences are saved.

Last section — 5 questions about your technical requirements, then we're ready to design.
You can answer each, skip individual ones, or say "use defaults for the rest."

--- Technical Requirements ---
```

**"Use defaults for the rest" handling:** If the user says this during Batch 1, apply defaults for all unanswered Batch 1 questions and all Batch 2 questions, then skip directly to Step 3.

### Batch 2 — Technical Requirements (Q6–Q10)

## Q6 — What input types must the model accept: text only, images (vision), or audio/video?

_Skip when:_ `integration.capabilities_summary` in `ai-workload-profile.json` has definitive values for `vision` AND (`speech_to_text` or `text_to_speech`) — derive from capabilities with `chosen_by: "extracted"` and do not present this question. Only ask if capabilities are unknown or ambiguous (all false with no evidence either way).

> A) Text only | B) Vision required | C) Audio/Video inputs

| Answer      | Impact                                                                                                          |
| ----------- | --------------------------------------------------------------------------------------------------------------- |
| Text only   | Full model catalog                                                                                              |
| Vision      | Claude Sonnet or Haiku (both support multimodal vision); Nova Micro excluded (text-only)                        |
| Audio/Video | Nova 2 Sonic (audio); Nova Reel v1 for video (Legacy — EOL Sep 30, 2026); Claude excluded for audio/video input |

Interpret → `ai_vision`. Default: A → no constraint.

## Q7 — Monthly AI usage volume

> A) < 1M tokens | B) 1–10M | C) 10–100M | D) > 100M | E) Don't know

| Answer    | Impact                                             |
| --------- | -------------------------------------------------- |
| Low       | On-demand; no provisioned throughput               |
| Medium    | On-demand with prompt caching analysis             |
| High      | Provisioned throughput analysis; prompt caching    |
| Very high | Provisioned throughput required; capacity planning |

Interpret → `ai_token_volume`: A → `"low"`, B → `"medium"`, C → `"high"`, D → `"very_high"`. Default: B → `"medium"`.

## Q8 — Response speed importance

Present with concrete anchors: Critical = autocomplete/live chat; Important = chat assistant; Flexible = reports/batch.

> A) Critical (< 500ms) | B) Important (< 2s) | C) Flexible (2–10s)

| Answer    | Impact                                                       |
| --------- | ------------------------------------------------------------ |
| Critical  | Haiku/Nova Micro; streaming required; provisioned throughput |
| Important | Sonnet 4.6 with streaming; standard on-demand                |
| Flexible  | Any model; batch inference for cost savings                  |

Interpret → `ai_latency`. Default: B → `"important"`.

## Q9 — AI task complexity

Present with concrete examples: Simple = classify/extract/summarize; Moderate = analyze+JSON/few-shot; Complex = multi-turn reasoning/tool use/agentic.

> A) Simple | B) Moderate | C) Complex

| Answer   | Impact                                                                        |
| -------- | ----------------------------------------------------------------------------- |
| Simple   | Haiku/Nova Micro sufficient; significant cost savings                         |
| Moderate | Sonnet 4.6 recommended; Haiku may suffice with prompt engineering             |
| Complex  | Sonnet 4.6 required; extended thinking considered; Opus 4.7 / 4.6 for hardest |

Interpret → `ai_complexity`. Default: B → `"moderate"`.

## Q10 — Specialized features needed

Same decision logic as Q17 in `clarify-ai.md`.

> A) Function calling | B) Ultra-long context (> 300K) | C) Extended thinking | D) Prompt caching | E) RAG optimization | F) Agentic workflows | G) Real-time speed | H) Image generation | I) Conversational speech | J) None

Interpret → `ai_critical_feature`. Default: J → no override.

### Batch 2 Complete

After the user responds to Batch 2, interpret all Batch 2 answers and proceed to Step 3.

---

## Step 3: Assemble and Write preferences.json

Assemble all interpreted answers from both batches into the final file. If `preferences-draft.json` exists, use it as the base — merge in Batch 2 answers, remove draft-specific metadata fields (`draft`, `batches_completed`, `batches_remaining`), and set `metadata.timestamp` to the current time.

Write `$MIGRATION_DIR/preferences.json`:

**Schema — AI-only structure:**

| Field                      | Path                                      | Notes                                       |
| -------------------------- | ----------------------------------------- | ------------------------------------------- |
| `migration_type`           | `metadata.migration_type`                 | `"ai-only"` — downstream skips infra phases |
| `discovery_artifacts`      | `metadata.discovery_artifacts`            | `["ai-workload-profile.json"]`              |
| `questions_asked`          | `metadata.questions_asked`                | Array of Q IDs actually presented           |
| `questions_defaulted`      | `metadata.questions_defaulted`            | Array of Q IDs where defaults used          |
| `questions_extracted`      | `metadata.questions_extracted`            | Array of Q IDs skipped via auto-detect      |
| `target_region`            | `design_constraints.target_region`        | Derived from GCP region or cross-cloud pref |
| `ai_framework`             | `ai_constraints.ai_framework`             | From Q1                                     |
| `ai_priority`              | `ai_constraints.ai_priority`              | From Q2                                     |
| `ai_monthly_spend`         | `ai_constraints.ai_monthly_spend`         | From Q3                                     |
| `cross_cloud`              | `ai_constraints.cross_cloud`              | From Q4 (unique to AI-only)                 |
| `ai_model_baseline`        | `ai_constraints.ai_model_baseline`        | From Q5                                     |
| `ai_vision`                | `ai_constraints.ai_vision`                | From Q6                                     |
| `ai_token_volume`          | `ai_constraints.ai_token_volume`          | From Q7                                     |
| `ai_latency`               | `ai_constraints.ai_latency`               | From Q8                                     |
| `ai_complexity`            | `ai_constraints.ai_complexity`            | From Q9                                     |
| `ai_critical_feature`      | `ai_constraints.ai_critical_feature`      | From Q10                                    |
| `ai_capabilities_required` | `ai_constraints.ai_capabilities_required` | Derived from `capabilities_summary`         |

Each `ai_constraints` field uses `{ "value": ..., "chosen_by": "user"|"extracted"|"derived" }` format. No nulls. All schema rules from `clarify.md` apply.

After writing `preferences.json`, delete `$MIGRATION_DIR/preferences-draft.json` if it exists.

---

## Step 4: Update Phase Status

Before phase completion, enforce output gate:

- `preferences.json` must exist.
- `preferences.json.metadata.migration_type` must equal `"ai-only"`.

If either check fails: STOP and output: "AI-only clarify output validation failed. Fix `preferences.json` before completing Phase 2."

Use the Phase Status Update Protocol (read-merge-write) to update `.phase-status.json` in the same turn as the output message:

- Set `phases.clarify` to `"completed"`
- Set `current_phase` to `"design"`

Output: "Clarification complete. Proceeding to Phase 3: Design AI Migration Architecture."
