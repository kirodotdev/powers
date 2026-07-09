# Estimate Phase: AI Workload Cost Analysis

> Loaded by estimate.md when aws-design-ai.json exists.

**Execute ALL steps in order. Do not skip or optimize.**

## Pricing Mode

The parent `estimate.md` selects the pricing mode before loading this file.

**Price lookup order:**

1. **`steering/cached-prices.md` (primary)** — Look up Bedrock model pricing and source provider pricing by table. Set `pricing_source: "cached"`.
2. **MCP (secondary)** — If a model is NOT in cached-prices.md and MCP is available, query `get_pricing("AmazonBedrock", "us-east-1")` with model filter. Set `pricing_source: "live"`.

For typical migrations (Claude, Llama, Nova, Mistral, DeepSeek, Gemma, OpenAI gpt-oss, Gemini source pricing), ALL prices are in `cached-prices.md`. Zero MCP calls needed.

## Prerequisites

Read from `$MIGRATION_DIR/`:

- **`ai-workload-profile.json`** — `current_costs.monthly_ai_spend`, `current_costs.services_detected`, `models[]`
- **`preferences.json`** — `ai_constraints.ai_token_volume.value`, `ai_constraints.ai_capabilities_required.value`
- **`aws-design-ai.json`** — `metadata.ai_source`, `ai_architecture.honest_assessment`, `ai_architecture.tiered_strategy`, `ai_architecture.bedrock_models[]` (with `source_provider_price`, `bedrock_price`, `honest_assessment`), `ai_architecture.capability_mapping`

---

## Part 1: Establish Current GCP AI Costs

Determine current Vertex AI spending from the best available source:

1. **Billing data (preferred)** — Use `current_costs.monthly_ai_spend` from `ai-workload-profile.json`
2. **Estimated from token volume** — Use `ai_constraints.ai_token_volume.value` from `preferences.json` with Gemini pricing from `cached-prices.md` (under "Source Provider Pricing"). Apply 60/40 input/output ratio if actual ratio unknown.
3. **Neither available** — Note in output and present model comparison at multiple volume tiers so user can find their range.

---

## Part 2: Build Model Comparison Table

Calculate the monthly Bedrock cost for **every viable model** at the user's token volume.

**Token volume mapping** (from `ai_token_volume` in `preferences.json`):

| `ai_token_volume` | Input tokens/month | Output tokens/month | Ratio |
| ----------------- | ------------------ | ------------------- | ----- |
| `"low"`           | 6M                 | 4M                  | 60/40 |
| `"medium"`        | 60M                | 40M                 | 60/40 |
| `"high"`          | 600M               | 400M                | 60/40 |
| `"very_high"`     | 6B                 | 4B                  | 60/40 |

If design or discover phase has more specific token estimates, use those instead.

**Cost formula:** `Monthly = (input_tokens / 1M × input_rate) + (output_tokens / 1M × output_rate)`

**Long-context surcharge:** If `ai_critical_feature = "ultra_long_context"` in `preferences.json`, Claude models charge 2x the standard input rate for tokens beyond 200K context. Apply the surcharge to the portion of input tokens that exceeds 200K per request. If per-request token counts are unknown, assume 50% of input tokens fall in the long-context tier as a conservative estimate.

**Comparison table columns:** Model, Bedrock Monthly, vs Source Provider ($ and %), vs Current GCP, Quality, Capabilities Match (checked against `ai_capabilities_required`).

Include source provider pricing from `aws-design-ai.json` → `bedrock_models[].source_provider_price`.

If Bedrock is more expensive for the recommended model, flag prominently.

If embeddings are needed, add a separate line (additive to primary model cost).

---

## Part 3: Recommended Model Cost Breakdown

Using the model selected in the design phase, show:

- Input tokens × rate, output tokens × rate, embeddings × rate (if applicable)
- Total monthly cost
- Comparison to current GCP spend (monthly and annual difference)
- Backup model cost for comparison

---

## Part 4: ROI Analysis

Present the monthly and annual cost difference between current GCP AI spend and projected Bedrock cost:

- **If Bedrock is cheaper**: present monthly and annual savings clearly
- **If Bedrock is more expensive**: state clearly, justify with non-cost benefits or note "not justified if cost is the only priority"

Reference `aws-design-ai.json` → `honest_assessment`. If `"recommend_stay"`, present prominently.

**Non-cost benefits to present:** model flexibility (30+ models), prompt caching (Claude, 90% savings), AWS ecosystem (Guardrails, Knowledge Bases, Agents), vendor diversification, multi-model strategy.

---

## Part 5: Cost Optimization Opportunities

Present applicable optimizations with estimated savings:

| Optimization               | Savings | Applies When                                        |
| -------------------------- | ------- | --------------------------------------------------- |
| Model downsizing / tiering | 60-87%  | High volume, premium model selected                 |
| Prompt caching (Claude)    | ~30%    | Repeated system prompts                             |
| Batch API                  | 50%     | Non-real-time workloads (`ai_latency = "flexible"`) |
| Provisioned throughput     | Varies  | Token volume > 100M/month, predictable traffic      |
| Input token reduction      | 10-30%  | Prompt optimization, shorter context                |
| Multi-model tiered routing | 60-87%  | High/very-high volume, `tiered_strategy` in design  |

For each applicable optimization, calculate before/after monthly cost and show an `optimized_projection` (best-case monthly with all optimizations).

---

## Output

Write `estimation-ai.json` to `$MIGRATION_DIR/`.

**Schema — top-level fields:**

| Field                        | Type   | Description                                                                                                         |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------- |
| `phase`                      | string | `"estimate"`                                                                                                        |
| `timestamp`                  | string | ISO 8601                                                                                                            |
| `pricing_source`             | string | `"cached"` or `"live"`                                                                                              |
| `accuracy_confidence`        | string | `"±5-10%"` or `"±15-25%"`                                                                                           |
| `current_costs`              | object | `source`, `gcp_monthly_ai_spend`, `services[]`                                                                      |
| `token_volume`               | object | `source`, `monthly_input_tokens`, `monthly_output_tokens`, ratio                                                    |
| `model_comparison`           | array  | All viable models: `model`, `monthly_cost`, `vs_current`, `quality`, `capabilities_match`, `missing_capabilities[]` |
| `recommended_model`          | object | `model`, `monthly_cost`, `breakdown` (input/output/embeddings), `rationale`                                         |
| `backup_model`               | object | `model`, `monthly_cost`, `rationale`                                                                                |
| `embeddings`                 | object | `model`, `monthly_cost`, `monthly_tokens`, `note` (if applicable)                                                   |
| `cost_comparison`            | object | `current_gcp_monthly`, `projected_bedrock_monthly`, `monthly_difference`, `annual_difference`, `percent_change`     |
| `roi_analysis`                  | object | `monthly_cost_delta`, `annual_cost_delta`, `justification`, `non_cost_benefits[]`                                   |
| `optimization_opportunities` | array  | `opportunity`, `potential_savings_monthly`, `implementation_effort`, `description`                                  |
| `optimized_projection`       | object | `monthly_with_optimizations`, `vs_current`, `note`                                                                  |

All cost values are numbers, not strings. Output must be valid JSON.

## Validation Checklist

- [ ] `model_comparison` includes ALL viable Bedrock models, not just recommended
- [ ] Every model has `capabilities_match` checked against `ai_capabilities_required`
- [ ] `recommended_model.rationale` references user's priority, preference, and volume
- [ ] `roi_analysis` is honest — if migration increases cost, says so
- [ ] `optimization_opportunities` only includes strategies relevant to user's workload
- [ ] No compute, database, storage, or networking costs (those belong in `estimate-infra.md`)

## Present Summary

After writing `estimation-ai.json`, present under 25 lines:

1. Current GCP AI spend vs projected Bedrock cost (recommended model)
2. Model comparison table: model name, monthly cost, vs source provider %, capabilities match
3. Recommended model with cost breakdown
4. If migration increases cost: flag honestly with non-cost justification
5. Top 2-3 optimization opportunities with potential savings
6. Optimized projection

## Generate Phase Integration

The Generate phase uses `estimation-ai.json`:

1. **`recommended_model`** — Which Bedrock model to provision and test
2. **`optimization_opportunities`** — Which optimizations to implement and when
4. **`cost_comparison`** — Cost monitoring targets and alerts in production
5. **`model_comparison`** — Fallback options if recommended model doesn't meet quality bar

## Scope Boundary

**This phase covers financial analysis ONLY for AI workloads.**

FORBIDDEN — Do NOT include compute, database, storage, networking cost calculations, infrastructure provisioning, code migration examples, or detailed migration timelines.
