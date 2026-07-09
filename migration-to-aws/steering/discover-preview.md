# Migration Preview Heuristic

> Loaded by `discover.md` Step 3 to compute a lightweight preview signal and rough cost
> estimate from discovery artifacts alone — before Clarify, Design, or Estimate run.
> This is NOT the full complexity tier (that lives in `migration-complexity.md` and requires
> preferences + billing). This is a fast, honest "at a glance" for the user.

---

## Route Detection

Before executing Steps 1–6, determine which route applies:

```
IF gcp-resource-inventory.json does NOT exist
   AND ai-workload-profile.json exists
THEN route = "ai_only"

ELSE
  route = "infra"   // covers infra-only, hybrid infra+AI, and billing-only
END
```

**AI-only route** executes Steps 1A–6A below.
**Infra route** executes Steps 1–6 below (original behavior, unchanged).

---

## AI-Only Route (Steps 1A–6A)

> Used when only `ai-workload-profile.json` exists — no Terraform, no billing data.
> Infrastructure stays on GCP; only AI/LLM calls move to AWS Bedrock.

### Step 1A: Compute AI complexity_signal

Read from `ai-workload-profile.json`:

| Input                     | Source                     | Key                                                                                |
| ------------------------- | -------------------------- | ---------------------------------------------------------------------------------- |
| `model_count`             | `ai-workload-profile.json` | Count of distinct entries in `models[]`                                            |
| `is_agentic`              | `ai-workload-profile.json` | `agentic_profile.is_agentic == true`                                               |
| `has_multi_model_routing` | `ai-workload-profile.json` | `integration.gateway_type` is `"openrouter"`, `"litellm"`, `"kong"`, or `"apigee"` |
| `has_multiple_providers`  | `ai-workload-profile.json` | `summary.ai_source == "both"` or distinct provider values across `models[]` > 1    |
| `capability_count`        | `ai-workload-profile.json` | Count of `true` values in `integration.capabilities_summary`                       |

**Classify (first match wins, top to bottom):**

```
IF is_agentic == true
   OR has_multi_model_routing == true
   OR model_count > 3
   OR has_multiple_providers == true
THEN ai_complexity_signal = "complex"

ELSE IF model_count == 1
        AND is_agentic != true
        AND has_multi_model_routing != true
        AND capability_count <= 2
THEN ai_complexity_signal = "likely_simple"

ELSE
  ai_complexity_signal = "standard"
END
```

**Fast-path eligibility:** Always `false` for AI-only route — AI profiles always route to full Clarify.

```
eligible_for_clarify_fast_path = false
```

---

### Step 2A: Build per-token price comparison

**Purpose:** Show the user what their models map to on Bedrock and whether the per-token
price is higher, lower, or roughly equivalent. Do NOT compute a monthly dollar total —
usage volume is unknown at Discover time and will be collected in Clarify (Q3, Q7).

For each model in `models[]` of `ai-workload-profile.json`, map to the closest Bedrock
equivalent using the table below, then look up both source and Bedrock per-token prices
from `steering/cached-prices.md` (Source Provider Pricing + Bedrock Models sections).

**Source model → Bedrock equivalent mapping:**

| Source model pattern                            | Bedrock equivalent         | Bedrock model ID                           |
| ----------------------------------------------- | -------------------------- | ------------------------------------------ |
| `gpt-4o`, `gpt-4.1`, `gpt-5.*` flagship         | Claude Sonnet 4.6          | `anthropic.claude-sonnet-4-6`              |
| `gpt-4o-mini`, `gpt-4.1-mini`, `gpt-5.*-mini`   | Claude Haiku 4.5           | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| `gpt-3.5-turbo`, `gpt-4.1-nano`, `gpt-5.*-nano` | Amazon Nova Micro          | `amazon.nova-micro-v1:0`                   |
| `o3`, `o4-mini`, reasoning models               | Claude Sonnet 4.6          | `anthropic.claude-sonnet-4-6`              |
| `gemini-2.5-pro`, `gemini-3.*-pro`              | Claude Sonnet 4.6          | `anthropic.claude-sonnet-4-6`              |
| `gemini-2.5-flash`, `gemini-2.0-flash`          | Claude Haiku 4.5           | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| `gemini-2.0-flash-lite`                         | Amazon Nova Lite           | `amazon.nova-lite-v1:0`                    |
| `claude-3-5-sonnet`, `claude-sonnet-*`          | Claude Sonnet 4.6          | `anthropic.claude-sonnet-4-6`              |
| `claude-3-5-haiku`, `claude-haiku-*`            | Claude Haiku 4.5           | `anthropic.claude-haiku-4-5-20251001-v1:0` |
| `claude-3-opus`, `claude-opus-*`                | Claude Opus 4.6            | `anthropic.claude-opus-4-6-v1`             |
| `text-embedding-*`, `*-embedding-*`             | Amazon Titan Embeddings v2 | `amazon.titan-embed-text-v2:0`             |
| `dall-e-*`, `imagen-*`, image generation        | Amazon Nova Canvas         | `amazon.nova-canvas-v1:0`                  |
| `whisper-*`, speech-to-text                     | Amazon Transcribe          | (non-token service — note separately)      |
| `tts-*`, text-to-speech                         | Amazon Polly               | (non-token service — note separately)      |
| Unknown / other                                 | Amazon Nova Pro            | `amazon.nova-pro-v1:0`                     |

For each mapped model pair, record `source_model` and `bedrock_equivalent` (model name only).
Do NOT compute or display per-token pricing comparisons at this stage — cost analysis
belongs in the Estimate phase where full usage volume context is available.

---

### Step 3A: Build key_decisions_ahead

Generate 2-4 bullets based on what was detected in `ai-workload-profile.json`:

| Signal                               | Decision bullet                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------- |
| Always                               | "Bedrock model selection for [list detected model IDs, max 3, then '+ N more']" |
| `is_agentic == true`                 | "Agentic migration path (retarget / AgentCore Harness / Strands)"               |
| `has_multi_model_routing == true`    | "Multi-model routing strategy on Bedrock (LiteLLM adapter vs native routing)"   |
| `has_multiple_providers == true`     | "Re-embedding requirements and cascade pair testing across providers"           |
| `integration.pattern == "streaming"` | "Streaming transport layer (Bedrock streaming vs current SDK)"                  |

Cap at 4 bullets.

---

### Step 4A: Build timeline_hint string

| ai_complexity_signal | timeline_hint                                                        |
| -------------------- | -------------------------------------------------------------------- |
| `likely_simple`      | "1-3 weeks (single model swap; confirm after Clarify)"               |
| `standard`           | "2-6 weeks (multi-model migration; confirm after Clarify)"           |
| `complex`            | "4-8 weeks (agentic or multi-provider stack; confirm after Clarify)" |

Always append "(confirm after Clarify)" — full classification requires preferences.

---

### Step 5A: Write migration-preview.json (AI-only)

Write `$MIGRATION_DIR/migration-preview.json`:

```json
{
  "preview_version": 1,
  "computed_at": "<ISO 8601 UTC>",
  "route": "ai_only",
  "primary_resource_count": 0,
  "complexity_signal": "standard",
  "ai_complexity_signal": "standard",
  "eligible_for_clarify_fast_path": false,
  "services_summary": [],
  "ai_summary": {
    "model_count": 2,
    "model_ids": ["gpt-4o", "text-embedding-3-small"],
    "bedrock_targets": [
      {
        "source_model": "gpt-4o",
        "source_input_per_1m": 2.50,
        "source_output_per_1m": 10.00,
        "bedrock_equivalent": "Claude Sonnet 4.6",
        "bedrock_model_id": "anthropic.claude-sonnet-4-6",
        "bedrock_input_per_1m": 3.00,
        "bedrock_output_per_1m": 15.00,
        "cost_direction": "higher"
      },
      {
        "source_model": "text-embedding-3-small",
        "source_input_per_1m": 0.02,
        "source_output_per_1m": null,
        "bedrock_equivalent": "Amazon Titan Embeddings v2",
        "bedrock_model_id": "amazon.titan-embed-text-v2:0",
        "bedrock_input_per_1m": 0.02,
        "bedrock_output_per_1m": null,
        "cost_direction": "lower"
      }
    ],
    "is_agentic": false,
    "has_multi_model_routing": false,
    "gateway_type": "direct"
  },
  "cost_preview": {
    "monthly_estimate": null,
    "monthly_estimate_note": "Monthly estimate available after Clarify (usage volume collected in Q3, Q7)",
    "disclaimer": "Per-token prices from cached-prices.md; full cost analysis in Estimate phase"
  },
  "timeline_hint": "2-6 weeks (multi-model migration; confirm after Clarify)",
  "ai_detected": true,
  "key_decisions_ahead": [
    "Bedrock model selection for gpt-4o, text-embedding-3-small",
    "Streaming transport layer (Bedrock streaming vs current SDK)"
  ]
}
```

**Field rules:**

- `route` is `"ai_only"` for this path
- `primary_resource_count` is `0` for AI-only runs (no IaC)
- `complexity_signal` mirrors `ai_complexity_signal` for downstream consumers
- `services_summary` is `[]` for AI-only runs
- `ai_summary.bedrock_targets` lists one entry per distinct source model with actual per-token prices
- `cost_preview.monthly_estimate` is always `null` at Discover time — no invented token volumes
- `eligible_for_clarify_fast_path` is always `false` for AI-only route

---

### Step 6A: Build preview chat message (AI-only)

Output this block as part of `discover.md` Step 3's user message (chat only — not a file):

```
### Your AI migration at a glance *(preview — not final)*

| | |
|---|---|
| **Models detected** | [model_ids joined by ", "] |
| **Bedrock targets** | [for each bedrock_target: "source_model → bedrock_equivalent"] |
| **Routing** | [if has_multi_model_routing: gateway_type + " (multi-model routing)" else "Direct SDK"] |
| **Monthly estimate** | Available after Estimate phase |
| **Timeline (rough)** | [timeline_hint] |
| **Decisions ahead** | [key_decisions_ahead joined by "; "] |

*Full cost breakdown in Estimate; runnable adapter code in Generate.*
AI workload detected — full Clarify recommended for best results.
```

Do NOT write this to a file. Chat output only.

---

## Infra Route (Steps 1–6)

> Used when `gcp-resource-inventory.json` exists (infra-only, hybrid infra+AI, or billing-only).
> Original behavior — unchanged.

## Step 1: Compute complexity_signal

Read from available discovery artifacts:

| Input                    | Source                                                  | Key                                                                             |
| ------------------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `primary_resource_count` | `gcp-resource-inventory.json`                           | Count resources where `classification: "PRIMARY"`                               |
| `has_database`           | `gcp-resource-inventory.json`                           | Any resource type matching `google_sql_*`, `google_spanner_*`, `google_redis_*` |
| `has_bigquery`           | `gcp-resource-inventory.json` or `billing-profile.json` | Any `google_bigquery_*` resource or BigQuery billing SKU                        |
| `has_ai_profile`         | File presence                                           | `ai-workload-profile.json` exists                                               |
| `is_agentic`             | `ai-workload-profile.json`                              | `agentic_profile.is_agentic == true` (if file exists)                           |
| `billing_monthly_usd`    | `billing-profile.json`                                  | `summary.total_monthly_spend` (null if absent)                                  |

**Classify (first match wins, top to bottom):**

```
IF has_bigquery
   OR is_agentic == true
   OR primary_resource_count > 8
   OR (billing_monthly_usd != null AND billing_monthly_usd > 10000)
THEN complexity_signal = "complex"
ELSE IF primary_resource_count <= 3
        AND has_database == false
        AND has_bigquery == false
        AND is_agentic != true
        AND (billing_monthly_usd == null OR billing_monthly_usd < 1000)
THEN complexity_signal = "likely_simple"
ELSE
  complexity_signal = "standard"
END
```

**Fast-path eligibility:**

```
eligible_for_clarify_fast_path =
   complexity_signal == "likely_simple"
   AND has_ai_profile == false

eligible_for_clarify_simple_path =
   complexity_signal == "likely_simple"
   AND has_ai_profile == true
   AND is_agentic != true
   AND ai_complexity_signal == "likely_simple"
```

**`ai_complexity_signal`** (compute when `ai-workload-profile.json` exists):

```
IF agentic_profile.is_agentic == true
   OR integration.frameworks is non-empty (LangChain, CrewAI, etc.)
   OR models.length > 3
THEN ai_complexity_signal = "standard"

ELSE IF integration.pattern in ("direct_sdk", "direct")
   AND models.length <= 2
   AND agentic_profile is absent
THEN ai_complexity_signal = "likely_simple"

ELSE
   ai_complexity_signal = "standard"
END
```

---

## Step 2: Compute rough AWS cost range

**Purpose:** Give the user a ballpark before Estimate runs. Always label as rough. Never invent GCP spend if billing data is absent.

### Service type -> dev-tier AWS line item mapping

For each PRIMARY resource in `gcp-resource-inventory.json`, map to a dev-tier AWS equivalent and look up its monthly cost from `steering/cached-prices.md`:

| GCP Primary Type                                                     | Typical AWS Target          | Dev-tier sizing for preview      |
| -------------------------------------------------------------------- | --------------------------- | -------------------------------- |
| `google_cloud_run_v2_service` / `google_cloud_run_service`           | Fargate                     | 0.5 vCPU, 1GB RAM, 730 hrs/mo    |
| `google_cloudfunctions_function` / `google_cloudfunctions2_function` | Lambda                      | 1M requests, 128MB, 200ms avg    |
| `google_compute_instance`                                            | EC2 t4g.small               | On-demand, us-east-1             |
| `google_container_cluster`                                           | EKS (2x t4g.small nodes)    | On-demand, us-east-1             |
| `google_sql_database_instance`                                       | RDS db.t4g.micro            | Single-AZ, gp3 20GB              |
| `google_redis_instance`                                              | ElastiCache cache.t4g.micro | Single-AZ                        |
| `google_storage_bucket`                                              | S3                          | 50GB standard + 10K GET + 1K PUT |
| `google_pubsub_topic`                                                | SQS                         | 1M requests/mo                   |
| `google_filestore_instance`                                          | EFS                         | 10GB standard                    |
| `google_spanner_instance`                                            | Aurora Serverless v2        | 0.5-1 ACU                        |
| `google_bigquery_dataset`                                            | Deferred -- specialist      | $0 (not estimated)               |

Sum the dev-tier line items to get `aws_monthly_range_usd.low`. Multiply by 1.5 for `high` (accounts for NAT gateway, data transfer, CloudWatch, and sizing variance).

**If `billing-profile.json` exists:** Set `gcp_monthly_usd` from `summary.total_monthly_spend`. Show both GCP actual and AWS range.

**If only IaC:** Set `gcp_monthly_usd: null`. Show AWS range only -- never invent GCP spend.

**If neither IaC nor billing:** Omit cost preview entirely (`cost_preview: null`).

---

## Step 3: Build key_decisions_ahead

Generate 2-4 bullets based on what was detected. Use only signals present in discovery artifacts:

| Signal                   | Decision bullet                                              |
| ------------------------ | ------------------------------------------------------------ |
| Any compute resource     | "Target region and deployment model (Fargate vs EKS)"        |
| `has_database == true`   | "Database migration tooling and cutover window"              |
| `has_ai_profile == true` | "Bedrock model selection for [detected model IDs]"           |
| `is_agentic == true`     | "Agentic migration path (retarget / Harness / Strands)"      |
| `has_bigquery == true`   | "BigQuery analytics target (specialist engagement required)" |

Always include "Target region" if any compute is present. Cap at 4 bullets.

---

## Step 4: Build timeline_hint string

| complexity_signal | timeline_hint                                            |
| ----------------- | -------------------------------------------------------- |
| `likely_simple`   | "3-6 weeks (likely simple infra; confirm after Clarify)" |
| `standard`        | "8-12 weeks (standard migration; confirm after Clarify)" |
| `complex`         | "12-16+ weeks (complex stack; confirm after Clarify)"    |

Always append "(confirm after Clarify)" -- full tier classification requires preferences.

---

## Step 5: Write migration-preview.json

Write `$MIGRATION_DIR/migration-preview.json`:

```json
{
  "preview_version": 1,
  "computed_at": "<ISO timestamp>",
  "primary_resource_count": 3,
  "complexity_signal": "likely_simple",
  "eligible_for_clarify_fast_path": true,
  "eligible_for_clarify_simple_path": false,
  "ai_complexity_signal": null,
  "services_summary": [
    { "gcp_type": "google_cloud_run_v2_service", "typical_aws_target": "Fargate" },
    { "gcp_type": "google_storage_bucket", "typical_aws_target": "S3" }
  ],
  "cost_preview": {
    "gcp_monthly_usd": 240.00,
    "aws_monthly_range_usd": { "low": 120, "high": 180 },
    "disclaimer": "Dev-tier rough estimate (+-30%); full analysis in Estimate phase"
  },
  "timeline_hint": "3-6 weeks (likely simple infra; confirm after Clarify)",
  "ai_detected": false,
  "key_decisions_ahead": [
    "Target region and deployment model (Fargate vs EKS)",
    "Cutover window"
  ]
}
```

**Field rules:**

- `cost_preview` is `null` if neither IaC nor billing data was available
- `cost_preview.gcp_monthly_usd` is `null` if no billing data (IaC-only run)
- `ai_detected` is `true` if `ai-workload-profile.json` exists
- `services_summary` lists only PRIMARY resources, deduplicated by `gcp_type`
- `eligible_for_clarify_fast_path` is `false` whenever `ai_detected == true`, regardless of infra complexity
- `eligible_for_clarify_simple_path` is `true` only when `ai_detected == true`, `complexity_signal == "likely_simple"`, and `ai_complexity_signal == "likely_simple"` (non-agentic direct SDK, ≤2 models)
- `ai_complexity_signal` is `null` when no AI profile exists; otherwise `"likely_simple"` or `"standard"`

---

## Step 6: Build preview chat message

Output this block as part of `discover.md` Step 3's user message (chat only -- not a file):

```
### Your migration at a glance *(preview -- not final)*

| | |
|---|---|
| **Services** | [primary_resource_count] resources -> [services_summary as "Fargate, S3"] *(standard pairings)* |
| **AWS cost (rough)** | ~$[low]-$[high]/mo [vs GCP ~$[gcp]/mo if billing present] *(dev-tier estimate, +-30%)* |
| **Timeline (rough)** | [timeline_hint] |
| **AI** | [if ai_detected: "[model IDs] detected -- AI migration path will run" else "None detected"] |
| **Decisions ahead** | [key_decisions_ahead joined by "; "] |

*Full cost breakdown in Estimate; runnable Terraform in Generate.*

[if eligible_for_clarify_fast_path: "Your stack looks straightforward -- next step is 3 quick questions."]
[if eligible_for_clarify_simple_path: "Simple stack with lightweight AI detected -- next step is a short question set (~6 questions)."]
[if ai_detected and not eligible_for_clarify_simple_path and not eligible_for_clarify_fast_path: "AI workload detected -- full Clarify recommended for best results."]
```

Do NOT write this to a file. Chat output only.
