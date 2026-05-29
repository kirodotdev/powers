# AI-Only Migration — Clarify Requirements

**Standalone flow** — Used when ONLY `ai-workload-profile.json` exists (no infrastructure or billing artifacts). Infrastructure stays on GCP; only AI/LLM calls move to AWS Bedrock.

This file replaces the category-based question system for AI-only migrations. It produces the same `preferences.json` output but with `design_constraints` limited to region and compliance, and `ai_constraints` fully populated.

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
> **Frameworks:** [from `integration.frameworks`, or "None"]

---

## Step 2: Ask Questions (Q1–Q10)

Present all questions at once with a progress indicator. Questions use their own numbering (Q1–Q10), independent of the full migration numbering.

```
I have a few questions to tailor your AI migration plan.
You can answer each, skip individual ones (I'll use sensible defaults),
or say "use all defaults" to proceed.
```

---

### AI Framework & Orchestration (Q1)

Always asked first. The orchestration layer determines the entire migration approach — gateway config change, provider swap, or full agent migration.

---

### Q1 — What AI framework or orchestration layer are you using? (select all that apply)

Same decision logic, auto-detect signals, combination logic, and interpretation as Q14 in `clarify-ai.md`. Refer to that file for full details.

**Auto-detect signals** — scan application code before asking:

- No AI framework imports, raw HTTP calls → A
- LiteLLM, OpenRouter, PortKey, Helicone, Kong, Apigee → B
- LangChain/LangGraph/LlamaIndex → C
- CrewAI, AutoGen, custom multi-agent → D
- OpenAI Agents SDK / Swarm → E
- MCP / A2A protocol → F
- Vapi, Bland.ai, Retell, Whisper → G

> How your AI calls reach the model determines migration effort.
>
> A) No framework — direct API calls
> B) LLM router/gateway (LiteLLM, OpenRouter, PortKey, Kong, Apigee)
> C) LangChain / LangGraph
> D) Multi-agent framework (CrewAI, AutoGen, custom)
> E) OpenAI Agents SDK / custom agent loop
> F) MCP servers or A2A protocol
> G) Voice/conversational agent platform (Vapi, Retell, Bland.ai)

Interpret: same as Q14 in `clarify-ai.md` → `ai_framework` array.

Default: _(auto-detect)_ — fall back to `["direct"]`.

---

### Priority & Cost (Q2–Q3)

Top-level filters for model selection and credits eligibility.

---

### Q2 — What matters most for your AI application?

Same decision logic as Q16 in `clarify-ai.md`.

**Context for user:** When asking, help the user think about their actual priority rather than defaulting to "best quality":

- **Best quality/reasoning** — accuracy and depth matter most; you'd pay more or wait longer for better answers (e.g., legal analysis, complex code generation, medical summarization)
- **Fastest speed** — response time is the primary constraint; users are waiting in real-time (e.g., chat UI, autocomplete, live suggestions)
- **Lowest cost** — volume is high and budget is tight; good-enough quality at scale (e.g., classification, tagging, bulk summarization)
- **Specialized capability** — you rely on a specific feature like vision, function calling, or extended thinking (covered in Q10)
- **Balanced** — no single dimension dominates; you want a solid all-rounder

> This determines our model selection strategy.
>
> A) Best quality/reasoning
> B) Fastest speed
> C) Lowest cost
> D) Specialized capability (covered in Q10)
> E) Balanced
> F) I don't know

| Answer                 | Recommendation Impact                                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Best quality/reasoning | Claude Sonnet 4.6 (latest, highest reasoning in Sonnet family) — primary; Claude Opus 4.6 for most demanding reasoning tasks |
| Fastest speed          | Claude Haiku 4.5 — lowest latency in Claude family; also consider Amazon Nova Micro/Lite for cost-optimized speed            |
| Lowest cost            | Claude Haiku 4.5 or Amazon Nova Micro — lowest cost per token                                                                |
| Specialized capability | Deferred to Q10 to determine which model                                                                                     |
| Balanced               | Claude Sonnet 4.6 as default balanced recommendation                                                                         |

Interpret: same as Q16 → `ai_priority`.

Default: E — `ai_priority: "balanced"`.

---

### Q3 — Approximately how much are you spending on OpenAI or Gemini per month?

Same decision logic as Q15 in `clarify-ai.md` — credits eligibility and cost baseline.

> AI spend helps me calculate migration credits eligibility and establish a Bedrock cost baseline.
>
> A) < $500/month
> B) $500–$2,000/month
> C) $2,000–$10,000/month
> D) > $10,000/month
> E) I don't know

Interpret: same as Q15 → `ai_monthly_spend`.

Default: B — `ai_monthly_spend: "$500-$2K"`.

---

### Cross-Cloud Architecture (Q4)

Unique to AI-only migrations where infrastructure stays on GCP while AI calls route to AWS.

---

### Q4 — Cross-cloud API call concerns

**Rationale:** AI-only migrations keep infrastructure on GCP while moving AI calls to AWS Bedrock. Cross-region API calls add latency and potential egress costs that may affect the recommendation. This question is unique to AI-only migrations.

**Context for user:** Explain the tradeoff concretely:

- **Yes — latency critical** — AI calls are in the hot path and every 20–50ms matters (e.g., real-time chat, autocomplete, live transcription)
- **No — latency acceptable** — AI calls are async or users expect a brief wait (e.g., background processing, batch jobs, report generation)
- **Concerned about egress costs** — sending large payloads (images, documents, audio) between GCP and AWS
- **Want to test first** — run both providers in parallel before committing

> Since your infrastructure stays on GCP, AI calls to Bedrock will cross cloud boundaries. This affects latency and data transfer costs.
>
> A) Yes — latency critical, AI calls are in the hot path
> B) No — latency acceptable, async or users can wait
> C) Concerned about egress costs for large payloads
> D) Want to test first — run both providers in parallel

| Answer                 | Recommendation Impact                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Latency critical       | VPC endpoint for Bedrock strongly recommended; us-east-1 or closest region to GCP deployment; latency benchmarks included |
| Latency acceptable     | Standard Bedrock endpoint; region selected for cost/availability                                                          |
| Concerned about egress | AWS PrivateLink for Bedrock recommended; egress cost analysis included                                                    |
| Want to test first     | Phased migration plan; parallel running guidance included                                                                 |

Interpret:

```
A -> cross_cloud: "latency-critical" — VPC endpoint; closest region to GCP
B -> cross_cloud: "latency-acceptable" — Standard endpoint; region by cost
C -> cross_cloud: "egress-concerned" — PrivateLink; egress analysis
D -> cross_cloud: "test-first" — Phased migration; parallel running
```

Default: B — `cross_cloud: "latency-acceptable"`.

---

### Model & Modality (Q5–Q6)

Establish the baseline model recommendation and whether multimodal capabilities are needed.

---

### Q5 — Which model are you currently using?

**Rationale:** The source model establishes the baseline Bedrock recommendation — a like-for-like capability match. This is a starting point only; answers to Q2 (priority), Q7 (volume), Q8 (latency), Q9 (complexity), and Q10 (special features) can all override this baseline.

**Override hierarchy:**

1. Q10 special features — hard overrides (e.g., speech-to-speech forces Nova Sonic regardless of source model)
2. Q2 priority — adjusts up or down within the Claude family (e.g., "lowest cost" downgrades Sonnet → Haiku even if source model was GPT-4)
3. Q7/Q8 volume and latency — may adjust toward provisioned throughput or faster models
4. Q5 source model — baseline only, used when no overrides apply

> The model you're currently using helps me recommend the closest Bedrock equivalent.
>
> A) Gemini Flash (1.5/2.0/2.5 Flash)
> B) Gemini Pro (1.5/2.5/3 Pro)
> C) GPT-3.5 Turbo
> D) GPT-4 / GPT-4 Turbo
> E) GPT-4o
> F) GPT-5 / GPT-5.x
> G) o-series (o1, o3)
> H) Other / Multiple models
> I) I don't know

| Source Model              | Baseline Bedrock Recommendation                                       | Pricing Context                                                  |
| ------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Gemini Flash variants     | Claude Haiku 4.5 ($1/$5) — speed and cost optimized                   | Strong savings vs Gemini Flash pricing                           |
| Gemini Pro variants       | Claude Sonnet 4.6 ($3/$15) — quality match                            | Comparable pricing tier                                          |
| GPT-3.5 Turbo             | Claude Haiku 4.5 ($1/$5) — cost-equivalent                            | Haiku is faster and cheaper                                      |
| GPT-4 / GPT-4 Turbo       | Claude Sonnet 4.6 ($3/$15) — quality equivalent                       | Major savings: GPT-4 Turbo is $10/$30 vs Sonnet $3/$15           |
| GPT-4o                    | Claude Sonnet 4.6 ($3/$15) — performance equivalent                   | Modest savings on output; input slightly higher on Bedrock       |
| GPT-5 / GPT-5.x           | Claude Sonnet 4.6 ($3/$15) — performance equivalent                   | GPT-5 is $1.25/$10 — savings story is quality/features, not cost |
| GPT-5 (flagship use case) | Claude Opus 4.6 ($5/$25) — flagship-to-flagship                       | Opus still cheaper than GPT-5 Pro ($15/$120)                     |
| o-series (o1, o3)         | Claude Sonnet 4.6 with extended thinking; Opus 4.6 for most demanding | o1 is $15/$60 — significant savings with Sonnet 4.6 at $3/$15    |

**Example overrides:**

- GPT-4 user (baseline: Sonnet 4.6) + Q2=lowest cost → **Haiku 4.5**
- Gemini Flash user (baseline: Haiku 4.5) + Q10=extended thinking → **Sonnet 4.6 with extended thinking**
- GPT-4o user (baseline: Sonnet 4.6) + Q10=real-time speech → **Nova Sonic** (Claude has no speech capability)
- GPT-3.5 user (baseline: Haiku 4.5) + Q9=complex reasoning → **Sonnet 4.6** (task complexity overrides cost-equivalent mapping)
- GPT-5 user (baseline: Opus 4.6) + Q2=balanced → **Sonnet 4.6** (priority overrides flagship-to-flagship mapping)

Interpret: same as Q19 in `clarify-ai.md` → `ai_model_baseline`.

Default: _(auto-detect)_ — fall back to Q2 priority-based selection.

---

### Q6 — Do you need vision or just text?

**Rationale:** Vision capability narrows the model selection to multimodal-capable models only.

> Vision capability limits which models are available.
>
> A) Text only
> B) Vision required
> C) Audio/Video inputs needed

| Answer             | Recommendation Impact                                                                 |
| ------------------ | ------------------------------------------------------------------------------------- |
| Text only          | Full model catalog available; cheapest/fastest text model per Q2 priority             |
| Vision required    | Claude Sonnet family (multimodal) required; Haiku excluded for vision tasks           |
| Audio/Video inputs | Amazon Nova Reel (video) or Nova Sonic (audio); Claude excluded for audio/video input |

Interpret: same as Q20 → `ai_vision`.

Default: A — no constraint (text only).

---

### Workload Characteristics (Q7–Q10)

These questions refine the model recommendation based on actual usage patterns — volume, latency, complexity, and specialized features can all override the baseline from Q5.

---

### Q7 — Monthly AI usage volume

**Rationale:** Volume determines whether on-demand or provisioned throughput is more cost-effective.

> Volume determines pricing strategy — on-demand vs provisioned throughput.
>
> A) Low (< 1M tokens/month)
> B) Medium (1–10M tokens/month)
> C) High (10–100M tokens/month)
> D) Very high (> 100M tokens/month)
> E) I don't know

| Answer    | Recommendation Impact                                                                  |
| --------- | -------------------------------------------------------------------------------------- |
| Low       | On-demand pricing; no provisioned throughput needed                                    |
| Medium    | On-demand with prompt caching analysis                                                 |
| High      | Provisioned throughput analysis; prompt caching strongly recommended                   |
| Very high | Provisioned throughput required for cost control; dedicated capacity planning included |

Interpret:

```
A -> ai_token_volume: "<1M" — On-demand; no provisioned throughput
B -> ai_token_volume: "1M-10M" — On-demand; prompt caching analysis
C -> ai_token_volume: "10M-100M" — Provisioned throughput analysis; prompt caching
D -> ai_token_volume: ">100M" — Provisioned throughput required; capacity planning
E -> same as default (B)
```

Default: B — `ai_token_volume: "1M-10M"`.

---

### Q8 — How important is response speed?

**Rationale:** Latency requirements can override cost and quality preferences from Q2.

**Context for user:** When asking, anchor each option in a real scenario:

- **Critical (< 500ms)** — users are staring at a loading spinner; every millisecond matters (e.g., autocomplete, live chat, real-time transcription)
- **Important (< 2s)** — users expect a quick response but a brief pause is acceptable (e.g., chat assistant, search augmentation, inline suggestions)
- **Flexible (2–10s)** — users submit a request and can wait; background or async is fine (e.g., report generation, batch analysis, email drafting)

> Latency requirements can override cost and quality preferences.
>
> A) Critical (< 500ms)
> B) Important (< 2s)
> C) Flexible (2–10s)

| Answer             | Recommendation Impact                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| Critical (< 500ms) | Claude Haiku 4.5 or Nova Micro; streaming required; provisioned throughput for consistent latency |
| Important (< 2s)   | Claude Sonnet 4.6 with streaming; standard on-demand acceptable                                   |
| Flexible (2–10s)   | Any model; batch inference considered for cost savings at high volume                             |

Interpret: same as Q21 → `ai_latency`.

Default: B — `ai_latency: "important"`.

---

### Q9 — How complex are your AI tasks?

**Rationale:** Task complexity determines whether a cheaper/faster model can handle the workload or whether a more capable model is required.

**Context for user:** When asking, give concrete examples so the user doesn't over- or under-estimate:

- **Simple** — single-step tasks with short prompts: classify this text, extract these fields, summarize this paragraph
- **Moderate** — multi-step prompts with examples or structured output: analyze this document and return JSON, generate content following a template, few-shot classification
- **Complex** — multi-turn reasoning, tool use, or long chain-of-thought: agentic workflows, code generation with debugging loops, research tasks that require planning and iteration

> Task complexity determines whether cheaper models can handle your workload.
>
> A) Simple (classification, short summaries, extraction)
> B) Moderate (analysis, structured content, few-shot)
> C) Complex (multi-step reasoning, tool use, agentic workflows)

| Answer   | Recommendation Impact                                                                       |
| -------- | ------------------------------------------------------------------------------------------- |
| Simple   | Claude Haiku 4.5 or Nova Micro sufficient; significant cost savings vs larger models        |
| Moderate | Claude Sonnet 4.6 recommended; Haiku may suffice with prompt engineering                    |
| Complex  | Claude Sonnet 4.6 required; extended thinking considered; Claude Opus 4.6 for hardest tasks |

Interpret: same as Q22 → `ai_complexity`.

Default: B — `ai_complexity: "moderate"`.

---

### Q10 — Specialized features needed

Same decision logic as Q17 in `clarify-ai.md`.

> Some features are only available in specific models. What's your most critical specialized requirement?
>
> A) Function calling / Tool use
> B) Ultra-long context (> 300K tokens)
> C) Extended thinking / Chain-of-thought
> D) Prompt caching
> E) RAG optimization
> F) Agentic workflows
> G) Real-time speed (< 500ms)
> H) Multimodal with image generation
> I) Real-time conversational speech
> J) None — standard features sufficient

Interpret: same as Q17 → `ai_critical_feature`.

Default: J — no additional override.

---

## Step 3: Write preferences.json

Write `$MIGRATION_DIR/preferences.json` with AI-only structure:

```json
{
  "metadata": {
    "timestamp": "<ISO timestamp>",
    "migration_type": "ai-only",
    "discovery_artifacts": ["ai-workload-profile.json"],
    "questions_asked": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"],
    "questions_defaulted": [],
    "questions_skipped_extracted": [],
    "questions_skipped_not_applicable": []
  },
  "design_constraints": {
    "target_region": { "value": "us-east-1", "chosen_by": "derived" }
  },
  "ai_constraints": {
    "ai_framework": { "value": ["langchain"], "chosen_by": "extracted" },
    "ai_priority": { "value": "balanced", "chosen_by": "user" },
    "ai_monthly_spend": { "value": "$500-$2K", "chosen_by": "user" },
    "cross_cloud": { "value": "latency-acceptable", "chosen_by": "user" },
    "ai_model_baseline": { "value": "claude-sonnet-4-6", "chosen_by": "derived" },
    "ai_vision": { "value": "text-only", "chosen_by": "user" },
    "ai_token_volume": { "value": "1M-10M", "chosen_by": "user" },
    "ai_latency": { "value": "important", "chosen_by": "user" },
    "ai_complexity": { "value": "moderate", "chosen_by": "user" },
    "ai_critical_feature": { "value": "none", "chosen_by": "user" },
    "ai_capabilities_required": {
      "value": ["text_generation", "streaming"],
      "chosen_by": "derived"
    }
  }
}
```

### Schema Notes (AI-Only)

1. `metadata.migration_type` is `"ai-only"` — downstream phases use this to skip infrastructure design/estimation.
2. `design_constraints` is minimal — only `target_region` (derived from GCP deployment region or cross-cloud latency preference).
3. `ai_constraints.cross_cloud` is unique to AI-only migrations — not present in full migration preferences.
4. `ai_constraints.ai_token_volume` uses different tiers than full migration Q18 — more granular for AI-only cost analysis.
5. All other schema rules from `clarify.md` apply (value/chosen_by fields, no nulls, derived capabilities).

---

## Step 4: Update Phase Status

Update `$MIGRATION_DIR/.phase-status.json`:

- Set `phases.clarify` to `"completed"`
- Update `last_updated` to current timestamp

Output to user: "Clarification complete. Proceeding to Phase 3: Design AI Migration Architecture."
