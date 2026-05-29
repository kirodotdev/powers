# Design Phase: AI Workloads (Bedrock)

> Loaded by `design.md` when `ai-workload-profile.json` exists.

**Execute ALL steps in order. Do not skip or optimize.**

---

## Step 0: Load Inputs

Read `$MIGRATION_DIR/ai-workload-profile.json`:

- `summary.ai_source` — `"gemini"`, `"openai"`, `"both"`, `"other"`
- `models[]` — Detected AI models with service, capabilities, evidence
- `integration` — SDK, frameworks, languages, gateway type, capability summary
- `infrastructure[]` — Terraform resources related to AI (may be empty)
- `current_costs` — Present only if billing data was provided

Read `$MIGRATION_DIR/preferences.json` → `ai_constraints` (if present). If absent: use defaults (prefer managed Bedrock, no latency constraint, no budget cap).

**Load source-specific design reference based on `ai_source`:**

- `"gemini"` → load `steering/design-ref-ai-gemini-to-bedrock.md`
- `"openai"` → load `steering/design-ref-ai-openai-to-bedrock.md`
- `"both"` → load both files
- `"other"` or absent → load `steering/design-ref-ai.md` (traditional ML rubric)

---

## Part 1: Bedrock Model Selection

For each model in `models[]`, select the best-fit Bedrock model using the loaded design reference mapping tables. Do NOT use a hardcoded mapping — the design-ref files contain tier-organized tables with pricing and competitive analysis.

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

---

## Part 1B: Volume-Based Strategy

If `ai_token_volume` is `"high"`, generate a `tiered_strategy`:

| Tier | Traffic | Model Selection              | Use Cases                                            |
| ---- | ------- | ---------------------------- | ---------------------------------------------------- |
| 1    | 60%     | Nova Micro or Llama 4 Scout  | Classification, extraction, short answers, routing   |
| 2    | 30%     | Llama 4 Maverick or Nova Pro | Summarization, moderate generation, Q&A with context |
| 3    | 10%     | Claude Sonnet 4.6            | Reasoning, long-form, agentic tasks, tool use        |

Set `tiered_strategy: null` for low/medium volume.

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

| GCP Pattern  | AWS Pattern                    | Effort |
| ------------ | ------------------------------ | ------ |
| `direct_sdk` | Bedrock SDK (boto3 / AWS SDK)  | Medium |
| `framework`  | LangChain/LlamaIndex + Bedrock | Low    |
| `rest_api`   | Bedrock REST API               | Medium |
| `mixed`      | Match per-model                | Varies |

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

| Pattern              | Source                    | Target              | Key Change                            |
| -------------------- | ------------------------- | ------------------- | ------------------------------------- |
| Direct SDK           | Vertex AI                 | boto3 Converse API  | `generate_content()` → `converse()`   |
| Direct SDK           | OpenAI                    | boto3 Converse API  | `completions.create()` → `converse()` |
| LangChain            | ChatVertexAI / ChatOpenAI | ChatBedrock         | Swap import and model_id              |
| LlamaIndex           | Vertex / OpenAI LLM       | BedrockConverse     | Swap import                           |
| LLM Router (LiteLLM) | Any                       | Config change       | `model="bedrock/<model_id>"` (1 line) |
| Embeddings           | TextEmbeddingModel        | Titan Embeddings v2 | `invoke_model` with JSON body         |
| Streaming            | `stream=True`             | `converse_stream`   | Event loop over `contentBlockDelta`   |

Generate concrete code examples using actual model IDs from the selected Bedrock models. Only include patterns matching the detected integration.

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

## Validation Checklist

- [ ] `metadata.ai_source` matches `summary.ai_source` from input
- [ ] Every model in `models[]` has a corresponding `bedrock_models` entry
- [ ] Every `bedrock_models[]` entry has pricing (`source_provider_price`, `bedrock_price`, `price_comparison`)
- [ ] `capability_mapping` covers every `true` capability from `capabilities_summary`
- [ ] `code_migration.primary_pattern` matches `integration.pattern`
- [ ] All model IDs use current Bedrock identifiers
- [ ] `honest_assessment` logic is consistent (weakest model drives overall)

## Present Summary

After writing `aws-design-ai.json`, present under 25 lines:

1. Overall honest assessment
2. Model comparison table (source → Bedrock, price comparison, assessment per model)
3. Integration pattern and migration complexity
4. Capability gaps (if any)
5. If weak_migrate or recommend_stay: flag prominently with cost justification
