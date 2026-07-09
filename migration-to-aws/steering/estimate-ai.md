# Estimate Phase: AI Workload Cost Analysis

> Loaded by estimate.md when aws-design-ai.json exists.

**Execute ALL steps in order. Do not skip or optimize.**

## Pricing Mode

The parent `estimate.md` selects the pricing mode before loading this file.

**Price lookup order:**

1. **`steering/cached-prices.md` (primary)** — Look up Bedrock model pricing and source provider pricing by table. Set `pricing_source: "cached"`.
2. **MCP (secondary)** — If a model is NOT in cached-prices.md and MCP is available, query `get_pricing("AmazonBedrock", ...)` with model filter and the user's target region. Set `pricing_source: "live"`.
3. **Cache after MCP failure** — If MCP was attempted but failed, and the model IS in the cache, use the cached price. Set `pricing_source: "cached_fallback"`.
4. **Unavailable** — If a model is NOT in the cache AND MCP failed, set `pricing_source: "unavailable"` and warn the user.

For typical migrations (Claude, Llama, Nova, Mistral, DeepSeek, Gemma, OpenAI gpt-oss, Gemini source pricing), ALL prices are in `cached-prices.md`. Zero MCP calls needed.

**Model lifecycle:** When building the model comparison table, check `steering/ai-model-lifecycle.md` and apply the 90-day exclusion rule:

- **Excluded** (≤90 days to EOL): omit entirely from `model_comparison`, `recommended_model`, and `backup_model`.
- **Legacy** (>90 days to EOL): include in `model_comparison` with `(Legacy — EOL YYYY-MM-DD)` annotation. Do not select as `recommended_model` unless no Active alternative exists.
- **Active**: no restrictions.

## Prerequisites

Read from `$MIGRATION_DIR/`:

- **`ai-workload-profile.json`** — `current_costs.monthly_ai_spend`, `current_costs.services_detected`, `models[]`, `metadata.profile_source`, `summary.inferred_from_iac`
- **`preferences.json`** — `ai_constraints.ai_token_volume.value`, `ai_constraints.ai_capabilities_required.value`
- **`aws-design-ai.json`** — `metadata.ai_source`, `ai_architecture.honest_assessment`, `ai_architecture.tiered_strategy`, `ai_architecture.bedrock_models[]` (with `source_provider_price`, `bedrock_price`, `honest_assessment`), `ai_architecture.capability_mapping`

---

## Part 1: Establish Current GCP AI Costs

Determine current Vertex AI spending from the best available source:

1. **Billing data (preferred)** — Use `current_costs.monthly_ai_spend` from `ai-workload-profile.json`
2. **Estimated from token volume** — Use `ai_constraints.ai_token_volume.value` from `preferences.json` with Gemini pricing from `cached-prices.md` (under "Source Provider Pricing"). Apply 60/40 input/output ratio if actual ratio unknown.
3. **Neither available** — Note in output and present model comparison at multiple volume tiers so user can find their range.

**IaC-only profile:** If `metadata.profile_source` is `iac_vertex` or `summary.inferred_from_iac` is true and billing/token data is missing, state explicitly that **current GCP AI spend is unverified** and widen uncertainty bands (use the same multi-tier comparison approach as in case 3).

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

## Part 4: Human One-Time Migration Costs (Out of Scope)

**Do not** present human labor, contractors, professional services, or engineering effort as one-time migration **costs** or budget line items (no dollar figures, no "budget for people work" lists, no "one-time migration cost" categories for implementation).

Populate `migration_cost_considerations.categories` as an **empty array** `[]`. Use `migration_cost_considerations.note` to state that human and professional-services one-time migration costs are intentionally excluded from this advisor.

**Technical integration complexity** (for internal JSON and risk context only — not framed as money):

From `ai-workload-profile.json`, record non-monetary factors in `migration_cost_considerations.complexity_factors[]` as short strings, for example:

- `integration.pattern = "framework"` → lower integration touch surface
- `integration.pattern = "direct_sdk"` → moderate SDK and API pattern changes
- `integration.pattern = "rest_api"` → higher endpoint, auth, and parsing changes
- `summary.total_models_detected` > 3 → multi-model coordination
- `quota_risk = "high"` (from `aws-design-ai.json`) → Bedrock quota increase required before migration; allow 1–5 business days (see `steering/bedrock-quotas.md`)

Do **not** repeat these as "costs" in the user-facing summary.

---

## Part 5: ROI Analysis

Present the monthly and annual cost difference between current GCP AI spend and projected Bedrock cost:

- **If Bedrock is cheaper**: present monthly and annual savings clearly
- **If Bedrock is more expensive**: state clearly, justify with non-cost benefits or note "not justified if cost is the only priority"

Reference `aws-design-ai.json` → `honest_assessment`. If `"recommend_stay"`, present prominently.

**Non-cost benefits to present:** model flexibility (30+ models), prompt caching (Claude, 90% savings), AWS ecosystem (Guardrails, Knowledge Bases, Agents), vendor diversification, multi-model strategy.

**Note:** Human/professional-services one-time migration costs are intentionally out of scope for this advisor and excluded from ROI calculations.

---

## Part 6: Cost Optimization Opportunities

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

**Post-migration optimization (do not surface during migration):** Model distillation — training a smaller, faster student model from a larger teacher model — can reduce inference costs up to ~75% for high-volume, stable workloads. Requires production traffic, labeled examples, and a teacher/student eval loop. Mention in the estimate summary as: "Once you have 2–4 weeks of Bedrock production traffic, consider model distillation to further reduce costs. See docs.aws.amazon.com/bedrock/latest/userguide/model-distillation.html." Do not recommend distillation before the startup has migrated and validated their workload.

---

## Part 7: Migration Recommendation (REQUIRED)

Produce a clear migrate/stay/optimize verdict for the AI workload migration. This is the AI-only equivalent of `estimate-infra.md` Part 7.

**Decision logic:**

| Condition                                                                                                                         | Verdict             | `recommendation.path` |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------- | --------------------- |
| Bedrock cheaper AND capabilities match                                                                                            | Migrate             | `migrate_optimized`   |
| Bedrock more expensive BUT non-cost benefits justify (vendor diversification, Guardrails, multi-model) AND user priority ≠ `cost` | Migrate with caveat | `migrate_optimized`   |
| Bedrock more expensive AND user priority = `cost` AND no compelling non-cost reason                                               | Stay                | `stay`                |
| Design `honest_assessment` = `recommend_stay`                                                                                     | Stay                | `stay`                |
| Mixed (some workloads cheaper, some not)                                                                                          | Migrate selectively | `migrate_phased`      |

**Output fields** (add to `estimation-ai.json` top-level):

```json
"recommendation": {
  "path": "migrate_optimized | migrate_phased | stay",
  "path_label": "Migrate to Bedrock | Migrate selectively | Stay on current provider",
  "migrate_if": "Brief condition under which migration makes sense (1 sentence)",
  "stay_if": "Brief condition under which staying makes sense (1 sentence)",
  "confidence": "high | medium | low",
  "rationale": "2-3 sentence justification citing cost delta and non-cost factors"
}
```

**Rules:**

- MUST emit `recommendation` — never omit. If data is insufficient, set `confidence: "low"` and state why in `rationale`.
- If `honest_assessment` from `aws-design-ai.json` says `recommend_stay`, `recommendation.path` MUST be `stay` regardless of cost numbers.
- For multi-workload runs: if some workloads favor migration and others don't, use `migrate_phased` and list which workloads to migrate vs. keep in `rationale`.

---

## Output

Write `estimation-ai.json` to `$MIGRATION_DIR/`.

**Schema — top-level fields:**

| Field                           | Type   | Description                                                                                                                     |
| ------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `phase`                         | string | `"estimate"`                                                                                                                    |
| `timestamp`                     | string | ISO 8601                                                                                                                        |
| `pricing_source`                | string | `"cached"` or `"live"`                                                                                                          |
| `accuracy_confidence`           | string | `"±5-10%"` or `"±15-25%"`                                                                                                       |
| `current_costs`                 | object | `source`, `gcp_monthly_ai_spend`, `services[]`                                                                                  |
| `token_volume`                  | object | `source`, `monthly_input_tokens`, `monthly_output_tokens`, ratio                                                                |
| `model_comparison`              | array  | All viable models: `model`, `monthly_cost`, `vs_current`, `quality`, `capabilities_match`, `missing_capabilities[]`             |
| `recommended_model`             | object | `model`, `monthly_cost`, `breakdown` (input/output/embeddings), `rationale`                                                     |
| `backup_model`                  | object | `model`, `monthly_cost`, `rationale`                                                                                            |
| `embeddings`                    | object | `model`, `monthly_cost`, `monthly_tokens`, `note` (if applicable)                                                               |
| `cost_comparison`               | object | `current_gcp_monthly`, `projected_bedrock_monthly`, `monthly_difference`, `annual_difference`, `percent_change`                 |
| `migration_cost_considerations` | object | `categories[]` (always `[]`), `complexity_factors[]` (technical integration only), `note` (must state human/pro costs excluded) |
| `roi_analysis`                  | object | `monthly_cost_delta`, `annual_cost_delta`, `justification`, `non_cost_benefits[]`                                               |
| `optimization_opportunities`    | array  | `opportunity`, `potential_savings_monthly`, `implementation_effort`, `description`                                              |
| `optimized_projection`          | object | `monthly_with_optimizations`, `vs_current`, `note`                                                                              |
| `recommendation`                | object | `path`, `path_label`, `migrate_if`, `stay_if`, `confidence`, `rationale` (see Part 7)                                           |

All cost values are numbers, not strings. Output must be valid JSON.

## Validation Checklist

- [ ] `recommendation` field is present with non-empty `path`, `path_label`, `migrate_if`, `stay_if`, and `rationale`
- [ ] `recommendation.path` is one of: `migrate_optimized`, `migrate_phased`, `stay`
- [ ] If Design `honest_assessment` = `recommend_stay`, then `recommendation.path` = `stay`
- [ ] `model_comparison` includes ALL viable Bedrock models, not just recommended
- [ ] Legacy models in `model_comparison` are annotated with EOL dates (per `steering/ai-model-lifecycle.md`)
- [ ] `recommended_model` is an Active model (not Legacy) unless no Active alternative exists
- [ ] Every model has `capabilities_match` checked against `ai_capabilities_required`
- [ ] `recommended_model.rationale` references user's priority, preference, and volume
- [ ] `roi_analysis` is honest — if migration increases cost, says so
- [ ] `optimization_opportunities` only includes strategies relevant to user's workload
- [ ] No compute, database, storage, or networking costs (those belong in `estimate-infra.md`)
- [ ] `migration_cost_considerations.categories` is `[]` — no human one-time migration costs presented

## Completion Handoff Gate (Fail Closed)

Before returning control to `estimate.md`, require:

- `estimation-ai.json` exists and passes the Validation Checklist above.

If this gate fails: STOP and output: "estimate-ai did not produce a valid `estimation-ai.json`; do not complete Phase 4."

## Present Summary

After writing `estimation-ai.json`, present under 25 lines:

1. **Pricing source and accuracy**: State whether prices came from cache or live API, and the accuracy range (±15-25% for AI models from cache, ±5-10% from live API). Example: "AI model estimates based on cached pricing (2026-03-07), accuracy ±15-25%."
2. Current GCP AI spend vs projected Bedrock cost (recommended model)
3. Model comparison table: model name, monthly cost, vs source provider %, capabilities match
4. Recommended model with cost breakdown
5. If migration increases cost: flag honestly with non-cost justification
6. Top 2-3 optimization opportunities with potential savings
7. Optimized projection

## Generate Phase Integration

The Generate phase uses `estimation-ai.json`:

1. **`recommended_model`** — Which Bedrock model to provision and test
2. **`migration_cost_considerations`** — `complexity_factors[]` only for integration risk context; **never** present human one-time migration **costs** to the user (`categories` stays `[]`)
3. **`optimization_opportunities`** — Which optimizations to implement and when
4. **`cost_comparison`** — Cost monitoring targets and alerts in production
5. **`model_comparison`** — Fallback options if recommended model doesn't meet quality bar

## Scope Boundary

**This phase covers financial analysis ONLY for AI workloads.**

FORBIDDEN — Do NOT include compute, database, storage, networking cost calculations, infrastructure provisioning, code migration examples, or detailed migration timelines.
