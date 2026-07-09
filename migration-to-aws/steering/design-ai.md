# Design Phase: AI Workloads (Bedrock)

> Loaded by `design.md` when `ai-workload-profile.json` exists.

**Execute ALL steps in order. Do not skip or optimize.**

---

## Step 0: Load Inputs

Read `$MIGRATION_DIR/ai-workload-profile.json`:

- `summary.ai_source` — `"gemini"`, `"openai"`, `"anthropic"`, `"both"`, `"other"`
- `models[]` — Detected AI models with service, capabilities, evidence
- `integration` — SDK, frameworks, languages, gateway type, capability summary
- `infrastructure[]` — Terraform resources related to AI (may be empty)
- `current_costs` — Present only if billing data was provided

Read `$MIGRATION_DIR/preferences.json` → `ai_constraints` (if present). If absent: use defaults (prefer managed Bedrock, no latency constraint, no budget cap).

**Region selection for AI workloads:** If `design_constraints.target_region` was derived from GCP region proximity (not explicitly chosen by the user), verify the selected Bedrock models are available in that region. Use the AWS Documentation MCP server to check model availability. If the target region lacks the selected model, prefer the geographically closest AWS region where it is available.

**Load source-specific design reference based on `ai_source`:**

- `"gemini"` → load `steering/design-ref-ai-gemini-to-bedrock.md`
- `"openai"` → load `steering/design-ref-ai-openai-to-bedrock.md`
- `"anthropic"` → load `steering/design-ref-ai-anthropic-to-bedrock.md` (Anthropic SDK → Bedrock Converse API client swap; do NOT use design-ref-ai-openai-to-bedrock.md for Anthropic SDK users)
- `"both"` → load both `design-ref-ai-gemini-to-bedrock.md` and `design-ref-ai-openai-to-bedrock.md`
- `"other"` or absent → load `steering/design-ref-ai.md` (traditional ML rubric — Vision API, Speech API, Document AI, custom models only; do NOT use for Anthropic SDK users)

---

## Step 0.5: Regional Availability Validation

Read target region from `preferences.json` → `design_constraints.target_region` (default: `us-east-1`).

Call `get_regional_availability` from the `awsknowledge` MCP server for:

1. Each Bedrock model ID being considered (from the loaded model mapping tables)
2. If `agentic_profile.is_agentic == true`: check `bedrock-agentcore` (Runtime)
3. If `agentic_profile.is_agentic == true` AND `ai_constraints.agentic.migration_approach == "harness"`: check `bedrock-agentcore` harness capability

**If any recommended service is unavailable in target region:**

- Add to `regional_warnings[]` in output: `{"service": "...", "target_region": "...", "nearest_available": "...", "impact": "..."}`
- Note in user summary with alternative region suggestion
- Do NOT block the design — proceed with the recommendation and flag the constraint

**If MCP call fails after 3 attempts:** Use the static table in `steering/ai-migration-guardrails.md` as fallback. Add `"regional_validation": "fallback_static"` to output metadata.

---

## Step 0.6: Agentic Design Routing

**Skip this step if `agentic_profile` is absent from `ai-workload-profile.json`.**

If `agentic_profile.is_agentic == true`:

1. Load `steering/ai-migration-guardrails.md` (shared warnings — load once, do not reload in sub-files)
2. Read `preferences.json` → `ai_constraints.agentic.migration_approach`
3. Route based on approach:

| `migration_approach` | Action                                                                                                                                                                                                                                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"retarget"`         | Continue with standard model-swap design below (Parts 1–6). The existing framework stays; only the model layer changes. Load `steering/retarget-gotchas.md` for framework-specific migration pitfalls to include in the code migration plan (Part 5).                                                                                            |
| `"harness"`          | Load `steering/design-ref-harness.md`. If file does not exist: continue with standard model-swap design, add note to user summary: "AgentCore Harness design reference not yet available. Proceeding with model-layer migration only. For Harness guidance, see https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html" |
| `"strands"`          | Load `steering/design-ref-agentic-to-agentcore.md`.                                                                                                                                                                                                                                                                                         |
| `"undecided"`        | Treat as `"retarget"` (safest default). Note in user summary: "No migration approach selected — defaulting to retarget (keep framework, swap model layer). Re-run Clarify to select a different approach."                                                                                                                                                |

**Regardless of approach:** Continue with Parts 1–6 below for model selection and mapping. The agentic design ref (Harness/Strands) adds agent infrastructure on top of the model-layer design — it does not replace it.

---

## Part 1: Bedrock Model Selection

**Multi-workload iteration (when `workloads[]` is present):**

If `preferences.json` contains a non-empty `workloads[]` array (written by Clarify after user confirmation), iterate per workload instead of per model. **Design MUST read workloads from `preferences.json` (not `ai-workload-profile.json`)** because Clarify may have edited, dropped, or re-confirmed rows.

Fallback: if `preferences.json` has no `workloads[]` field but `ai-workload-profile.json` does, use the profile's `workloads[]` directly (no user edits were made).

For each `workloads[]` entry:

1. **Use the workload's `capability` to select the Bedrock target class:**

   | Capability          | Target Class                                           | Default Model                  |
   | ------------------- | ------------------------------------------------------ | ------------------------------ |
   | `text_generation`   | Text/reasoning                                         | Apply override hierarchy below |
   | `structured_output` | Text/reasoning (same models support structured output) | Apply override hierarchy below |
   | `image_generation`  | Image generation                                       | Amazon Nova Canvas             |
   | `embedding`         | Embedding                                              | Amazon Titan Embed Text v2     |
   | `speech_to_text`    | Speech-to-text                                         | Amazon Transcribe              |
   | `text_to_speech`    | Text-to-speech                                         | Amazon Polly                   |
   | `unknown`           | Text/reasoning (default)                               | Apply override hierarchy below |

2. **For text/reasoning capabilities:** Apply the existing override hierarchy from `ai_constraints`:
   - Q17 special features (hard override) > Q16 priority > Q18/Q21 volume and latency > source model baseline
   - This ensures single-workload sophistication is preserved per workload

3. **Emit one `design_block` per workload** in `aws-design-ai.json`:

   ```json
   "design_blocks": [
     {
       "workload_id": "wl_3a1f2c",
       "model_id": "gemini-2.5-flash",
       "target_bedrock_model": "amazon.nova-lite-v1:0",
       "capability": "text_generation",
       "capability_confidence": "medium",
       "rationale": "text_generation + medium confidence + balanced priority → Nova Lite",
       "confidence_warning": null
     }
   ]
   ```

4. **Confidence warning:** Set `confidence_warning` to a non-null string (identifying the workload and noting manual review required) when `capability_confidence == "low"`. Null for `high` and `medium`.

5. **Preserve input order:** `design_blocks[]` order matches `workloads[]` order.

6. **Empty workloads:** If `workloads[]` is empty, emit `aws-design-ai.json` with `"design_blocks": []` and proceed with the existing `models[]` path below as fallback.

**Fallback (no `workloads[]` or single entry):** If `workloads[]` is absent or has exactly one entry, fall through to the existing per-model logic below (backward compatible).

---

For each model in `models[]`, select the best-fit Bedrock model using the loaded design reference mapping tables. Do NOT use a hardcoded mapping — the design-ref files contain tier-organized tables with pricing and competitive analysis.

Treat model mapping as compatibility-guided, not 1:1 parity. Before cutover, require validation of prompts, tool-calling behavior, and eval metrics for the selected Bedrock model.

**If `models[]` is empty:** Skip per-model rows; output a short **placeholder strategy** (one representative Bedrock model family per `ai_source` rubric) and dependency on Clarify answers — do not fabricate `models[]` entries.

**Apply user preference overrides from `ai_constraints`:**

| Preference                | Override                                          |
| ------------------------- | ------------------------------------------------- |
| `ai_priority = "cost"`    | Prefer "Winner" column; flag if source is cheaper |
| `ai_priority = "quality"` | Prefer Claude Sonnet/Opus regardless of cost      |
| `ai_priority = "speed"`   | Prefer Claude Sonnet (fastest integration)        |
| `ai_latency = "critical"` | Prefer smaller/faster models (Haiku, Nova Lite)   |
| `ai_latency = "flexible"` | Any model; flag Batch API for 50% savings         |

**Stay-or-migrate assessment per model:**

- Bedrock cheaper → `"strong_migrate"`
- Bedrock within 25% of source AND priority != cost → `"moderate_migrate"`
- Source > 25% cheaper AND priority = cost → `"weak_migrate"` or `"recommend_stay"`

Overall assessment = weakest across all models. If any `"recommend_stay"`, flag prominently.

**Model comparison table** (include in output and user summary): Model, Provider, Max Context, Input/Output Price per 1M, Price Comparison, Streaming, Function Calling, Assessment.

**Quota risk assessment** (per `steering/bedrock-quotas.md`):

After selecting models, assess quota risk based on `ai_token_volume` from `preferences.json`:

| `ai_token_volume`         | Selected Model Family              | `quota_risk` | Action                                                                            |
| ------------------------- | ---------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| `"high"` or `"very_high"` | Any                                | `"high"`     | Flag: "Request Bedrock quota increase before migration (allow 1–5 business days)" |
| `"medium"`                | Claude (5× burndown)               | `"medium"`   | Flag: "Monitor TPM usage; quota increase may be needed at peak"                   |
| `"medium"`                | Nova / Llama / other (1× burndown) | `"low"`      | No action                                                                         |
| `"low"`                   | Any                                | `"low"`      | No action                                                                         |

Include `quota_risk` in `aws-design-ai.json` → `ai_architecture` alongside `honest_assessment`.

---

## Part 1B: Volume-Based Strategy

If `ai_token_volume` is `"high"`, generate a `tiered_strategy`:

| Tier | Traffic | Model Selection              | Use Cases                                            |
| ---- | ------- | ---------------------------- | ---------------------------------------------------- |
| 1    | 60%     | Nova Micro or Llama 4 Scout  | Classification, extraction, short answers, routing   |
| 2    | 30%     | Llama 4 Maverick or Nova Pro | Summarization, moderate generation, Q&A with context |
| 3    | 10%     | Claude Sonnet 4.6            | Reasoning, long-form, agentic tasks, tool use        |

Set `tiered_strategy: null` for low/medium volume.

**Intelligent Prompt Routing — automated alternative to manual tiering:**
If `ai_token_volume` is `"high"` AND the selected models are within the same family
(e.g., Claude Haiku + Claude Sonnet, or Nova Lite + Nova Pro), note Bedrock Intelligent
Prompt Routing as an option. It automatically routes each request to the cheapest model
that can handle it at adequate quality — the AWS-native automation of the tiered strategy above.

> Intelligent Prompt Routing only routes within a single model family. It does NOT replace
> cross-provider routing (e.g., Claude ↔ GPT-4o). If the startup was using OpenRouter or
> LiteLLM to route across providers, they still need app-level routing for cross-family calls.
> One-line caveat: adds a routing-prediction latency hop; verify model support at
> docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html before recommending.

---

## Part 1C: Multi-Model Coordination Warnings

If `models[]` contains more than one model, check for coordination patterns and generate warnings. These help the user understand that migrating multiple models requires coordinated testing, not independent swaps.

**Check and warn:**

1. **Embeddings + generation model detected** — If `models[]` contains both an embeddings model (capabilities_used includes `"embeddings"`) AND a text generation model:
   > ⚠️ "Migrating the embedding model (e.g., text-embedding-3-small → Titan Embeddings v2) requires re-embedding all documents in your vector store. Plan for re-indexing time and temporary storage. Test retrieval quality with the new embeddings before switching generation model."
   > ⚠️ "Verify vector index dimension compatibility before cutover. OpenAI text-embedding-3-small outputs 1536 dimensions; Titan Embeddings v2 is configurable (256, 512, or 1024). A mismatch will cause insert failures at the vector store layer — your index must be rebuilt at the target dimension before any data is written."

2. **Models at different price tiers** — If `models[]` contains both a mini/nano/lite model AND a flagship model (infer from model_id naming: `*-mini`, `*-nano`, `*-lite` vs flagship):
   > ⚠️ "These models appear to work as a cascade or routing pattern (cheap model for classification/filtering, expensive model for generation). Test the Bedrock replacement pair together — validate that the cheaper model's classification accuracy is preserved with its Bedrock equivalent before testing the expensive model."

3. **More than 3 models** — If `models[]` count > 3:
   > ⚠️ "Multiple models detected ([count]). Recommend a tiered migration strategy: migrate and validate one model at a time, starting with the lowest-risk (highest-volume, simplest task). See Part 1B for tiered routing recommendations."

4. **Text generation + image generation** — If `models[]` contains both text generation AND image generation capabilities:
   > ⚠️ "Image generation migration (e.g., DALL-E/gpt-image → Nova Canvas) requires separate evaluation. Image quality is subjective — plan for human evaluation alongside automated metrics."

5. **Speech models** — If `models[]` contains speech-to-text or text-to-speech capabilities:
   > ⚠️ "Speech model migration targets different AWS services (Whisper → Amazon Transcribe, TTS → Amazon Polly or Nova Sonic) with different pricing models and APIs. These are not Bedrock model swaps — they require separate integration work."

Record all triggered warnings in `aws-design-ai.json` → `multi_model_warnings[]`. Each warning: `{"type": "embeddings_reindex|cascade_pair|multi_model_tiered|image_separate|speech_separate", "message": "..."}`.

---

## Part 2: Feature Parity Validation

For each capability in `integration.capabilities_summary` that is `true`, check Bedrock parity:

| Capability        | Vertex AI               | Amazon Bedrock                   | Parity  |
| ----------------- | ----------------------- | -------------------------------- | ------- |
| Text Generation   | GenerativeModel API     | Converse API                     | Full    |
| Streaming         | stream_generate_content | InvokeModelWithResponseStream    | Full    |
| Function Calling  | Tool declarations       | Tool use in Converse API         | Full    |
| Embeddings        | TextEmbeddingModel      | Titan Embeddings via InvokeModel | Full    |
| Vision/Multimodal | Gemini multimodal input | Claude multimodal messages       | Full    |
| Batch Processing  | BatchPredictionJob      | Batch Inference (async)          | Partial |
| Fine-tuning       | Vertex AI tuning        | Bedrock Custom Model             | Partial |
| Grounding / RAG   | Vertex AI Search & RAG  | Bedrock Knowledge Bases          | Full    |
| Agents            | Vertex AI Agent Builder | Bedrock Agents                   | Full    |

Record `capability_gaps[]` for any Partial or None parity.

---

## Part 3: Analyze Detected Workloads

For each model in `models[]`, record:

- **Workload type**: text generation, embeddings, vision, code generation, custom model
- **Integration pattern mapping**:

| GCP Pattern  | AWS Pattern                                      | Effort  |
| ------------ | ------------------------------------------------ | ------- |
| `direct_sdk` | Mantle OpenAI-compat (if OpenAI source + region) | Minimal |
| `direct_sdk` | Bedrock SDK (boto3 / AWS SDK)                    | Medium  |
| `framework`  | LangChain/LlamaIndex + Bedrock                   | Low     |
| `rest_api`   | Bedrock REST API                                 | Medium  |
| `mixed`      | Match per-model                                  | Varies  |

- **Migration complexity**: Low / Medium / High

---

## Part 4: Infrastructure Mapping

Map GCP AI infrastructure to AWS equivalents:

| GCP Resource                              | AWS Equivalent                                  |
| ----------------------------------------- | ----------------------------------------------- |
| `google_vertex_ai_endpoint`               | Bedrock Model Access (serverless, no infra)     |
| `google_vertex_ai_index` / index_endpoint | OpenSearch Serverless or Bedrock Knowledge Base |
| `google_vertex_ai_featurestore`           | SageMaker Feature Store                         |
| `google_vertex_ai_dataset`                | S3 + Bedrock training job config                |
| `google_vertex_ai_pipeline_job`           | Step Functions + Bedrock                        |

Service accounts with `role: "supports_ai"` → IAM role with Bedrock permissions. Confidence = `inferred`.

---

## Part 5: Code Migration Plan

For each detected `integration.pattern` and `ai_source`, generate before/after migration examples.

**Patterns to include (matched to detected language and source):**

| Pattern              | Source                    | Target                 | Key Change                                                                                           |
| -------------------- | ------------------------- | ---------------------- | ---------------------------------------------------------------------------------------------------- |
| Direct SDK (OpenAI)  | OpenAI                    | Mantle (OpenAI-compat) | Change `OPENAI_BASE_URL` + `OPENAI_API_KEY` + model string (zero code changes)                       |
| Direct SDK           | Vertex AI                 | boto3 Converse API     | `generate_content()` → `converse()`                                                                  |
| Direct SDK           | OpenAI                    | boto3 Converse API     | `completions.create()` → `converse()` (use if Mantle region unavailable or Converse features needed) |
| Direct SDK           | Anthropic                 | boto3 Converse API     | `messages.create()` → `converse()` with Claude model ID on Bedrock                                   |
| LangChain            | ChatVertexAI / ChatOpenAI | ChatBedrock            | Swap import and model_id                                                                             |
| LlamaIndex           | Vertex / OpenAI LLM       | BedrockConverse        | Swap import                                                                                          |
| LLM Router (LiteLLM) | Any                       | Config change          | `model="bedrock/<model_id>"` (1 line)                                                                |
| Embeddings           | TextEmbeddingModel        | Titan Embeddings v2    | `invoke_model` with JSON body                                                                        |
| Streaming            | `stream=True`             | `converse_stream`      | Event loop over `contentBlockDelta`                                                                  |

**Mantle (OpenAI-compatible endpoints):** If `ai_source = "openai"` and `integration.pattern = "direct_sdk"`, prefer the Mantle path as the primary migration option. Mantle provides OpenAI-compatible Chat Completions and Responses APIs on Bedrock — the existing OpenAI SDK code works with zero changes, only environment variable updates. Check [Mantle regional availability](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html) — if the target region does not have Mantle, fall back to the boto3 Converse API path. Record `migration_path: "mantle"` or `migration_path: "converse"` in `aws-design-ai.json` → `ai_architecture.code_migration`.

**Mantle throughput caveat (medium/high volume):** Mantle runs on a shared 10,000 RPM account limit. For workloads with `ai_token_volume = "medium"` or `"high"`, add a note in the design summary: "Mantle is subject to a shared 10K RPM account limit. At medium/high volume, monitor for 429s and consider migrating to `bedrock-runtime` (Converse API) for dedicated throughput." See `steering/ai-migration-guardrails.md` for the full risk table.

**gpt-oss migration path:** If `ai_source = "openai"` and the user wants to preserve OpenAI model architecture while consolidating on AWS, offer `gpt-oss` on Bedrock as a fourth migration path alongside Mantle, Converse API, and framework swap. Record `migration_path: "gpt-oss"` in `aws-design-ai.json` → `ai_architecture.code_migration`. The gpt-oss path uses the Converse API with the gpt-oss Bedrock model ID — it is not an OpenAI-compatible endpoint. Note the Claude 4.7+ output TPM cap (2M) if the user is migrating from a high-output OpenAI workload.

Generate concrete code examples using actual model IDs from the selected Bedrock models. Only include patterns matching the detected integration.

**OpenRouter-specific guidance** (if `gateway_type == "llm_router"` AND `detection_signals` contains OpenRouter evidence):

OpenRouter is a hosted routing service (not self-hosted like LiteLLM). It adds a margin on top of provider pricing. Present three options to the user:

> **If the startup was using OpenRouter primarily for cost-based routing within one model family**
> (e.g., routing between Claude Haiku and Claude Sonnet, or Nova Lite and Nova Pro),
> Bedrock Intelligent Prompt Routing is the AWS-native replacement — no routing infrastructure
> needed. If they routed across providers (e.g., Claude ↔ GPT-4o), they still need
> app-level or LiteLLM routing after migration.

| Option                          | Action                                                    | Effort    | Trade-off                                                                  |
| ------------------------------- | --------------------------------------------------------- | --------- | -------------------------------------------------------------------------- |
| A) Direct Bedrock (recommended) | Remove OpenRouter, call Bedrock API directly              | 1–2 weeks | Removes middleman + margin; requires SDK changes                           |
| B) Self-hosted LiteLLM          | Replace OpenRouter with LiteLLM proxy pointing to Bedrock | 1–3 days  | Preserves router pattern; removes OpenRouter dependency; adds self-hosting |
| C) Keep OpenRouter              | Use OpenRouter with `amazon/` prefixed Bedrock models     | Hours     | Lowest effort; retains OpenRouter dependency and margin                    |

Record user's choice (or recommend A if not asked) in `aws-design-ai.json` → `code_migration.openrouter_path`: `"direct"` / `"litellm"` / `"keep_openrouter"`.

---

## Part 6: Generate Output

Write `aws-design-ai.json` to `$MIGRATION_DIR/`.

**Schema — top-level fields:**

| Field                                 | Type        | Description                                                                                                                                                                                         |
| ------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `metadata`                            | object      | `phase`, `focus`, `ai_source`, `bedrock_models_selected`, `timestamp`                                                                                                                               |
| `ai_architecture.honest_assessment`   | string      | `"strong_migrate"`, `"moderate_migrate"`, `"weak_migrate"`, `"recommend_stay"`                                                                                                                      |
| `ai_architecture.tiered_strategy`     | object/null | Tiered model routing (null for low/medium volume)                                                                                                                                                   |
| `ai_architecture.bedrock_models`      | array       | Per-model: `gcp_model_id`, `aws_model_id`, `capabilities_matched[]`, `capability_gaps[]`, `honest_assessment`, `source_provider_price`, `bedrock_price`, `price_comparison`, `migration_complexity` |
| `ai_architecture.capability_mapping`  | object      | Per-capability: `parity` (full/partial/none), `notes`                                                                                                                                               |
| `ai_architecture.code_migration`      | object      | `primary_pattern`, `framework`, `files_to_modify[]`, `dependency_changes`                                                                                                                           |
| `ai_architecture.infrastructure`      | array       | GCP resource → AWS equivalent mappings with confidence                                                                                                                                              |
| `ai_architecture.services_to_migrate` | array       | GCP service → AWS service with effort and notes                                                                                                                                                     |
| `regional_warnings`                   | array       | Per-service: `service`, `target_region`, `nearest_available`, `impact` (empty array if all services available)                                                                                      |
| `multi_model_warnings`                | array       | Per-warning: `type`, `message` (empty array if single model or no coordination issues)                                                                                                              |
| `agentic_design`                      | object/null | Present only when `agentic_profile.is_agentic == true`. Contains `migration_approach`, path-specific config (e.g., `harness_config`). Null or absent for non-agentic workloads.                     |

## Validation Checklist

- [ ] `metadata.ai_source` matches `summary.ai_source` from input
- [ ] Every model in `models[]` has a corresponding `bedrock_models` entry
- [ ] Every `bedrock_models[]` entry has pricing (`source_provider_price`, `bedrock_price`, `price_comparison`)
- [ ] `capability_mapping` covers every `true` capability from `capabilities_summary`
- [ ] `code_migration.primary_pattern` matches `integration.pattern`
- [ ] All model IDs use current Bedrock identifiers (Active status per `steering/ai-model-lifecycle.md`)
- [ ] No Legacy model is used as `bedrock_models[].aws_model_id` unless no Active alternative exists (with EOL date noted)
- [ ] `honest_assessment` logic is consistent (weakest model drives overall)
- [ ] `regional_warnings` is present (empty array `[]` if no issues; populated if any service unavailable in target region)
- [ ] `multi_model_warnings` is present (empty array `[]` if single model or no coordination issues)
- [ ] If `agentic_profile.is_agentic == true`: `agentic_design` object is present with `migration_approach` matching `preferences.json`
- [ ] If `agentic_profile.is_agentic == false` or absent: `agentic_design` is null or absent

## Completion Handoff Gate (Fail Closed)

Before returning control to `design.md`, require:

- `aws-design-ai.json` exists and passes the Validation Checklist above.

If this gate fails: STOP and output: "design-ai did not produce a valid `aws-design-ai.json`; do not complete Phase 3."

## Present Summary

After writing `aws-design-ai.json`, present under 25 lines:

1. Overall honest assessment
2. Model comparison table (source → Bedrock, price comparison, assessment per model)
3. Integration pattern and migration complexity
4. Capability gaps (if any)
5. If weak_migrate or recommend_stay: flag prominently with cost justification
