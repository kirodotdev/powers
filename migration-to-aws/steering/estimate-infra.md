# Estimate Phase: Infrastructure Cost Analysis

> Loaded by estimate.md when aws-design.json exists.

**Execute ALL steps in order. Do not skip or optimize.**

## Pricing Mode

The parent `estimate.md` determines pricing source before loading this file.

**Price lookup order for each AWS service in `aws-design.json`:**

1. **`steering/cached-prices.md` (primary)** — Read once. **Before using, check staleness:** compute `days_since_cache = today − cache "Last updated" date`. If `days_since_cache > 30`, set `pricing_source: "cached_stale"` for all AI model prices and prepend a warning to the estimate output: "Pricing cache is more than 30 days old — AI model prices may have changed. Verify via the AWS Pricing MCP server or aws.amazon.com/bedrock/pricing." Infrastructure prices (Fargate, RDS, S3, etc.) remain reliable; only AI model prices need the stale flag. If `days_since_cache ≤ 30`, use the price directly and set `pricing_source: "cached"`.
2. **MCP with recipes (secondary)** — If a service is NOT in cached-prices.md and MCP is available, use the Pricing Recipes table below. Set `pricing_source: "live"`.
3. **Cache after MCP failure** — If MCP was attempted but failed, and the service IS in the cache, use the cached price. Set `pricing_source: "cached_fallback"`.
4. **Unavailable** — If a service is NOT in the cache AND MCP failed, set `pricing_source: "unavailable"`. Add to `services_with_missing_fallback` and warn the user.

For typical migrations (Fargate, Aurora/RDS, Aurora Serverless v2, S3, ALB, NAT Gateway, Lambda, Secrets Manager, CloudWatch, ElastiCache, DynamoDB), ALL prices are in `cached-prices.md`. Zero MCP calls needed.

## Step 0: Validate Design Output

Before pricing queries, validate `aws-design.json`:

1. **File exists**: If missing, **STOP**. Output: "Phase 3 (Design) not completed. Run Phase 3 first."
2. **Valid JSON**: If parse fails, **STOP**. Output: "Design file corrupted (invalid JSON). Re-run Phase 3."
3. **Required fields**:
   - `clusters` array is not empty: If empty, **STOP**. Output: "No clusters in design. Re-run Phase 3."
   - Each cluster has `resources` array: If missing, **STOP**. Output: "Cluster [id] missing resources. Re-run Phase 3."
   - Each resource has `aws_service` field: If missing, **STOP**. Output: "Resource [address] missing aws_service. Re-run Phase 3."
   - Each resource has `aws_config` field: If missing, **STOP**. Output: "Resource [address] missing aws_config. Re-run Phase 3."

If all validations pass, proceed to Part 1.

## Pricing Recipes (MCP Fallback Only)

Only use these recipes when a service is NOT in `cached-prices.md` and MCP is available.
Do NOT call get_pricing_service_codes, get_pricing_service_attributes, or get_pricing_attribute_values — go directly to get_pricing.

| AWS Service          | service_code      | filters                                                                                                              | output_options                                                                                                                                     |
| -------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fargate              | AmazonECS         | `[{"Field":"productFamily","Value":"Compute"}]`                                                                      | `{"pricing_terms":["OnDemand"],"product_attributes":["usagetype","location"],"exclude_free_products":true}`                                        |
| Aurora PostgreSQL    | AmazonRDS         | `[{"Field":"databaseEngine","Value":"Aurora PostgreSQL"},{"Field":"deploymentOption","Value":"Single-AZ"}]`          | `{"pricing_terms":["OnDemand"],"product_attributes":["instanceType","databaseEngine","deploymentOption","location"],"exclude_free_products":true}` |
| RDS PostgreSQL       | AmazonRDS         | `[{"Field":"databaseEngine","Value":"PostgreSQL"},{"Field":"deploymentOption","Value":"Multi-AZ"}]`                  | `{"pricing_terms":["OnDemand"],"product_attributes":["instanceType","databaseEngine","deploymentOption","location"],"exclude_free_products":true}` |
| Aurora MySQL         | AmazonRDS         | `[{"Field":"databaseEngine","Value":"Aurora MySQL"},{"Field":"deploymentOption","Value":"Single-AZ"}]`               | `{"pricing_terms":["OnDemand"],"product_attributes":["instanceType","databaseEngine","deploymentOption","location"],"exclude_free_products":true}` |
| Aurora Serverless v2 | AmazonRDS         | `[{"Field":"usagetype","Value":["Aurora:ServerlessV2Usage","Aurora:ServerlessV2IOOptimizedUsage"],"Type":"ANY_OF"}]` | `{"pricing_terms":["OnDemand"],"product_attributes":["usagetype","databaseEngine","location"],"exclude_free_products":true}`                       |
| S3                   | AmazonS3          | `[{"Field":"storageClass","Value":"General Purpose"}]`                                                               | `{"pricing_terms":["OnDemand"],"product_attributes":["storageClass","volumeType","location"],"exclude_free_products":true}`                        |
| ALB                  | AWSELB            | `[{"Field":"productFamily","Value":"Load Balancer-Application"}]`                                                    | `{"pricing_terms":["OnDemand"],"product_attributes":["productFamily","location"],"exclude_free_products":true}`                                    |
| NAT Gateway          | AmazonEC2         | `[{"Field":"productFamily","Value":"NAT Gateway"}]`                                                                  | `{"pricing_terms":["OnDemand"],"product_attributes":["productFamily","location","group"],"exclude_free_products":true}`                            |
| Lambda               | AWSLambda         | `[{"Field":"group","Value":"AWS-Lambda-Duration"}]`                                                                  | `{"pricing_terms":["OnDemand"],"product_attributes":["group","location","usagetype"],"exclude_free_products":true}`                                |
| Secrets Manager      | AWSSecretsManager | `[]`                                                                                                                 | `{"pricing_terms":["OnDemand"],"exclude_free_products":true}`                                                                                      |
| CloudWatch Logs      | AmazonCloudWatch  | `[{"Field":"usagetype","Value":"DataProcessing-Bytes"}]`                                                             | `{"pricing_terms":["OnDemand"],"product_attributes":["productFamily","location","usagetype"],"exclude_free_products":true}`                        |
| ElastiCache Redis    | AmazonElastiCache | `[{"Field":"cacheEngine","Value":"Redis"},{"Field":"instanceType","Value":"cache.t4g","Type":"CONTAINS"}]`           | `{"pricing_terms":["OnDemand"],"product_attributes":["instanceType","cacheEngine","location"],"exclude_free_products":true}`                       |
| DynamoDB             | AmazonDynamoDB    | `[]`                                                                                                                 | `{"pricing_terms":["OnDemand"],"product_attributes":["group","location"],"exclude_free_products":true}`                                            |

**Important notes on MCP filters:**

- **Fargate**: Use `productFamily=Compute`, NOT EC2-style filters (operatingSystem, tenancy, capacitystatus do not exist in AmazonECS)
- **Aurora (PostgreSQL/MySQL)**: Use `deploymentOption=Single-AZ`. Aurora handles multi-AZ replication natively — there is no "Multi-AZ" pricing option for Aurora
- **Lambda**: Filter by `group=AWS-Lambda-Duration` for compute pricing, separate call with `group=AWS-Lambda-Requests` for request pricing
- **CloudWatch**: Filter by specific `usagetype=DataProcessing-Bytes` for log ingestion pricing (avoids pulling all vended log types)

**Batching rule:** If MCP calls are needed, group up to 4 requests in parallel per turn.

---

## Part 1: Calculate Current GCP Costs

Determine the current GCP monthly infrastructure costs. Use the best available source:

1. **`billing-profile.json` (preferred)** — Use actual billing data as the GCP baseline. Highest confidence (±5%).
2. **`gcp-resource-inventory.json` (fallback)** — Estimate costs from discovered resource configurations. Wider range (±20-30%).
3. **`preferences.json` → `gcp_monthly_spend`** — User-provided monthly spend from clarification.
4. **Ask the user** — If none of the above are available, ask: "I need your current GCP monthly spend to produce a meaningful cost comparison. What is your approximate GCP monthly infrastructure cost?" Use the user's answer. If the user declines or is unsure, present AWS costs without a GCP comparison and note: "GCP baseline unavailable — AWS costs shown without comparison."

Present the GCP baseline as a total and per-service breakdown, noting which source was used.

### CUD-Aware Baseline (when billing data available)

If `billing-profile.json` contains `commitments.has_active_cuds == true`:

1. **Use list price as the GCP baseline**: The `services[].monthly_cost` values already use list price (commitment fee rows excluded by discover phase). Use `cost_basis.total_at_list` as the total GCP baseline for comparison.
2. **Do not include commitment fees in workload costs**: Commitment fee rows are billing artifacts with no AWS equivalent — they are already excluded from `services[]`.
3. **Record the effective discount for Part 3**: Note `commitments.effective_discount_percent` — this is the customer's current GCP discount rate that will be compared against AWS Savings Plan rates.

This ensures the comparison is GCP list price vs. AWS on-demand (both uncommitted baselines), with commitment options presented separately as optimization opportunities.

---

## Part 2: Calculate Projected AWS Costs

**Security baseline coverage (always required):** Add a `security_baseline` entry to `projected_costs.breakdown` with `service: "AWS Security Baseline (Tier 1)"`, low/mid/high estimates of $3/$15/$30 per month, `accuracy: "±25%"`, and a `components` sub-object breaking down CloudTrail S3 storage (~$1.50/mo mid), GuardDuty (~~$13/mo mid after free trial), AWS Budgets ($0), and the free controls. If `preferences.json.compliance` contains any of `soc2`, `pci`, `hipaa`, `fedramp`, also add a sibling `security_baseline_compliance` entry with low/mid/high estimates of $3/$14/$25 per month, `accuracy: "±25%"`, `emission_reason` field citing the declared compliance values, and a `components` sub-object breaking down AWS Config (~$6/mo mid continuous), Config S3 storage (~~ $0.50/mo mid), Security Hub + FSBP (~$7/mo mid after free trial), and extra standards (free). Per-unit rates are grounded in the AWS Pricing API for us-east-1 as of 2026-05-04 (Config pricing effective 2025-09-01, Security Hub effective 2026-03-01). Cite source as `steering/cached-prices.md § Security Baseline` or live `get_pricing` calls for `AmazonGuardDuty`, `AWSConfig`, and `AWSSecurityHub` service codes. Both line items are added as flat additives to each tier total (Premium/Balanced/Optimized) rather than being tier-dependent.

For each service in `aws-design.json`, calculate monthly cost using rates from `cached-prices.md`. Track `pricing_source` per service.

**Secret Manager coverage (mandatory):** If any mapped resource has `gcp_type` of `google_secret_manager_secret` or `google_secret_manager_secret_version`, ensure an `aws_service` entry for **Secrets Manager** is present in the estimate breakdown. Do not collapse this into a generic "supporting" line item.

**BigQuery / deferred analytics (mandatory):** For any resource where `aws_service` is exactly **`Deferred — specialist engagement`** OR `gcp_type` starts with `google_bigquery_`:

- **Do not** apply Athena, Redshift, Glue, or EMR rates as the plugin’s “projected” analytics stack.
- **Exclude** these resources from Premium / Balanced / Optimized **numeric totals** (or list them under a `deferred_services[]` / `excluded_from_totals` section in `estimation-infra.json` with reason: _pending specialist engagement_).
- In the user-facing summary, state that **AWS analytics costs are unknown** until the **AWS account team** and/or **data analytics migration partner** defines the target architecture.

Calculate 3 cost tiers to show the optimization range:

| Tier          | Description                             | Examples                                                            |
| ------------- | --------------------------------------- | ------------------------------------------------------------------- |
| **Premium**   | Latest generation, highest availability | db.r6g instances, Fargate Spot disabled, Multi-AZ everything        |
| **Balanced**  | Standard generation, typical setup      | db.t4g instances, Fargate on-demand, Single-AZ where acceptable     |
| **Optimized** | Cost-minimized with trade-offs          | db.t4g with reserved pricing, Fargate Spot 70%, S3-IA for cold data |

**Per-service calculation approach:**

| Domain                     | Formula                                                                               | Key inputs from aws-design.json                                               |
| -------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Compute (Fargate)          | (vCPU × vCPU rate + memory GB × memory rate) × 730 hours × instance count             | `aws_config.cpu`, `aws_config.memory`                                         |
| Compute (Lambda)           | requests × request rate + (requests × duration × memory GB) × GB-second rate          | Estimated from usage patterns                                                 |
| Database (Aurora)          | instance rate × 730 hours × instance count + storage GB × storage rate + I/O estimate | `aws_config.instance_class`, `aws_config.allocated_storage`                   |
| Database (RDS)             | instance rate × 730 hours × instance count + storage GB × storage rate                | `aws_config.instance_class`, `aws_config.allocated_storage`                   |
| Storage (S3)               | GB × per-GB rate + request estimates                                                  | `aws_config.storage_gb` or source `gcp_config`                                |
| Networking (ALB)           | fixed monthly + LCU estimate                                                          | From compute service count                                                    |
| Networking (NAT)           | fixed monthly × count + GB processed × data rate                                      | From VPC design                                                               |
| Security (Secrets Manager) | secrets_count × per-secret monthly rate + api_calls_10k × per-10K API rate            | `aws_config.secrets_count`, `aws_config.api_calls_10k` (or inferred defaults) |
| Supporting                 | Per-unit rates × quantities (secrets, log GB, metrics)                                | Inferred from service count                                                   |

Show calculation breakdown per service: rate × quantity = cost. Present all 3 tiers side-by-side.

---

## Part 2B: Observability Cost Estimation (CloudWatch)

GCP Cloud Operations Suite has generous free tiers (50 GB/month logging free, 150M metric samples free, alerting free, profiling free). AWS CloudWatch charges from the first GB and first custom metric. This section ensures observability costs are not a surprise post-migration.

**Relationship to Part 2 "Supporting" line item:** The observability entry produced by this section REPLACES any CloudWatch/log/metric portion that would otherwise appear in the "Supporting" row of Part 2. Do NOT include CloudWatch log ingestion, metrics, or alarms in the Supporting line item — they are fully covered here. Supporting retains only Secrets Manager and any non-observability per-unit charges.

### Pricing source

All rates from `cached-prices.md § CloudWatch` and `§ X-Ray`. No MCP calls needed.

### Step 1: Determine log volume

**IF billing data IS available** (`billing-profile.json` exists):

Check for Cloud Logging line items:

- Look for `services[].sku` containing `Log Volume`, `Logging`, or `Cloud Logging`
- Extract volume in GiB from the SKU quantity/units field directly (preferred)
- OR derive from GCP cost: `gcp_logging_cost ÷ $0.50/GiB` (GCP's own list rate above free tier) = volume above free tier, then add 50 GiB for the free portion
- **Important:** Use GCP's own rate ($0.50/GiB) to reverse-engineer volume from GCP billing — not AWS rates. Apply AWS rates ($0.50/GB Standard) to the derived volume for the projected cost.
- Set `observability.log_volume_source: "billing"`

**IF billing data is NOT available:**

Use the per-service heuristic table to estimate monthly log volume:

| AWS Service (from aws-design.json) | Estimated log volume/month | Basis                                                                                                                                                  |
| ---------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Fargate task                       | 3 GB per task              | Container stdout/stderr, request logs                                                                                                                  |
| Lambda function                    | 0.2 GB per function        | Invocation logs at INFO level                                                                                                                          |
| RDS/Aurora instance                | 1 GB per instance          | Error log + slow query (audit log off)                                                                                                                 |
| RDS/Aurora instance (audit on)     | 8 GB per instance          | If source has `pgaudit.log`, `log_statement = 'all'`, `cloudsql.log_min_duration_statement`, or explicit audit/general log database flags in Terraform |
| ALB                                | 2 GB per load balancer     | Access logs (if enabled)                                                                                                                               |
| NAT Gateway                        | 1 GB per gateway           | Flow logs (if enabled)                                                                                                                                 |
| ElastiCache                        | 0.5 GB per node            | Slow log only                                                                                                                                          |

**RDS audit detection:** Check for database flags in the source `google_sql_database_instance` Terraform that indicate audit logging: `pgaudit.log`, `log_statement = 'all'`, `cloudsql.log_min_duration_statement`, or general/audit log flags for MySQL. Do NOT use `cloudsql.iam_authentication` as an audit proxy — IAM auth is access control, not audit logging.

Sum all applicable services. Set `observability.log_volume_source: "heuristic"`.

### Step 2: Determine custom metrics count

**IF billing data IS available:**

GCP Cloud Monitoring uses sample-based pricing ($0.10/1000 samples above 150M free) which does not map 1:1 to CloudWatch's per-metric-per-month pricing ($0.30/metric/month). Even with billing data, treat custom metrics as heuristic:

- Count `google_monitoring_alert_policy` resources in `gcp-resource-inventory.json` as a proxy for custom metric complexity
- Multiply alert policy count × 3 (typical metrics per alert: threshold metric + 2 related dimensions)
- Set `observability.metrics_source: "heuristic"` (even when billing data exists — GCP metric pricing is not cleanly convertible to CloudWatch's model)

**IF billing data is NOT available:**

Use the heuristic: `custom_metrics_count = (number of services in aws-design.json × 5) + (number of alert policies from source × 2)`

Default floor: 10 custom metrics.
Default ceiling for small startups: 50 custom metrics.

Set `observability.metrics_source: "heuristic"`.

### Step 2b: Determine alarm count

Count `google_monitoring_alert_policy` resources in `gcp-resource-inventory.json`.

- If count > 0: `alarm_count = count`
- If count is 0 or no alert policies found: `alarm_count = 5` (baseline — most teams set up basic health/error/latency alarms post-migration)

Set `observability.alarm_count_source: "inventory"` or `"default"`.

### Step 3: Determine tracing usage

**IF billing data IS available:**

Check for Cloud Trace line items:

- Extract span volume from SKU quantity/units field directly (preferred)
- OR derive from GCP cost: `gcp_trace_cost ÷ $0.20/million` (GCP's own list rate above 2.5M free tier) = millions of spans above free tier, then add 2.5M
- **Important:** Use GCP's rate ($0.20/M spans) to reverse-engineer volume from GCP billing. Apply AWS X-Ray rate ($5.00/M traces) to that volume for the projected cost.
- Set `observability.tracing_source: "billing"`

**IF billing data is NOT available:**

Check `gcp-resource-inventory.json` or application code for tracing libraries:

- If OpenTelemetry, `@google-cloud/trace-agent`, or `google.cloud.trace` imports detected: assume 1M spans/month (small app baseline)
- If no tracing signals: set `monthly_spans: 0` (tracing not in use; do not add X-Ray costs)

Set `observability.tracing_source: "heuristic"`.

### Step 4: Calculate CloudWatch costs

Default estimate uses Standard log class ($0.50/GB) for all logs. Infrequent Access ($0.25/GB) is an optimization opportunity surfaced in Step 6, not the baseline assumption.

```
log_ingestion_cost    = monthly_log_gb × $0.50
log_storage_cost      = monthly_log_gb × $0.03 × retention_months (default: 1)
custom_metrics_cost   = custom_metrics_count × $0.30  (flat rate; valid for ≤10K metrics at startup scale)
alarms_cost           = alarm_count × $0.10
tracing_cost          = max(0, monthly_spans - 100_000) / 1_000_000 × $5.00  (honors X-Ray 100K/month free tier)
dashboard_cost        = max(0, dashboards - 3) × $3.00  (default: 0 — assume ≤3)

total_observability   = log_ingestion_cost + log_storage_cost + custom_metrics_cost + alarms_cost + tracing_cost + dashboard_cost
```

### Step 5: Add to projected costs

Add an `observability` entry to `projected_costs.breakdown`. This entry REPLACES any CloudWatch/log/metric portion in the "Supporting" row — do not double-count.

```json
{
  "service": "CloudWatch + X-Ray (Observability)",
  "low": <total × 0.7>,
  "mid": <total>,
  "high": <total × 1.5>,
  "accuracy": "±30%",
  "pricing_source": "cached",
  "components": {
    "log_ingestion": <log_ingestion_cost>,
    "log_storage": <log_storage_cost>,
    "custom_metrics": <custom_metrics_cost>,
    "alarms": <alarms_cost>,
    "tracing": <tracing_cost>
  },
  "volume_source": "<billing|heuristic>  (reflects log volume source — the largest cost component; metrics are always heuristic regardless of this field)",
  "note": "GCP Cloud Operations includes 50 GB/month free logging, free alerting, and free profiling. CloudWatch charges from the first GB. Tracing is significantly more expensive on X-Ray ($5/M) vs Cloud Trace ($0.20/M). Actual costs depend on log verbosity and retention policy."
}
```

### Step 6: Surface GCP free tier delta in cost comparison

In Part 3 (Cost Comparison), if observability costs exceed $20/month, add a callout:

> **Observability cost note:** Your GCP Cloud Operations costs may appear low or zero due to generous free tiers (50 GB/month logging, 150M metric samples, free alerting). The CloudWatch estimate of $X/month reflects the same workload without those free tiers. Consider:
>
> - Reducing log verbosity (WARN-only for production services) to lower ingestion costs
> - Using CloudWatch Logs Infrequent Access class for non-critical logs ($0.25/GB — 50% cheaper than Standard)
> - Evaluating sampling rate for X-Ray traces (10% sampling = 90% cost reduction)
> - CloudWatch Logs Insights for ad-hoc queries instead of always-on metric filters

### Estimation rules

- Do NOT emit observability costs as $0 — even minimal apps produce logs on AWS
- Floor: $5/month (absolute minimum for any running Fargate + RDS workload)
- If tracing is not detected in source, do NOT add X-Ray costs (don't upsell)
- Container Insights is NOT included by default — add only if source uses Cloud Monitoring with per-container metrics or if production-tier observability is required
- The observability line item REPLACES CloudWatch entries in the "Supporting" row — never double-count

---

## Part 3: Cost Comparison

Present a side-by-side comparison:

- GCP current monthly total (at list price)
- AWS Premium / Balanced / Optimized monthly totals
- Difference (savings or increase) per tier vs GCP
- Per-service breakdown for the Balanced tier

### Commitment Context (if CUDs detected)

If `billing-profile.json` has `commitments.has_active_cuds == true`, add a `commitment_context` section to the comparison:

- **GCP effective committed rate**: The customer currently pays `effective_discount_percent`% below list via CUDs
- **AWS equivalent**:
  - **Compute Savings Plans** (Fargate, Lambda, EC2): up to 66% vs On-Demand at maximum term/discount; typical 1-year no-upfront **20–40%**
  - **Database Savings Plans** (Aurora, RDS, DynamoDB, ElastiCache, etc.): up to **35%** (serverless) / up to **~20%** (provisioned instances), 1-year no-upfront
  - **RDS Reserved Instances** (alternative to Database Savings Plans on the same workload): up to **69%** (3-year All Upfront); locked to instance family/region — mutually exclusive with Database Savings Plans per workload
- **Fair comparison framing**: Present both an uncommitted comparison (GCP list vs. AWS on-demand) and a committed comparison (GCP net-of-CUD vs. AWS with 1yr commitments where applicable)
- **Migration timing note**: If the customer has active CUDs, note that CUD fees continue regardless of usage — migrating mid-commitment means paying both GCP CUD fees and AWS costs until the CUD term expires. For **Cloud Run → Fargate** or **GKE → Fargate** (re-platform) workloads, recommend establishing a 30–90 day AWS compute baseline before purchasing Compute Savings Plans (see Part 6).

Include in `estimation-infra.json` under `cost_comparison`:

```json
"commitment_context": {
  "gcp_has_active_cuds": true,
  "gcp_effective_discount_percent": 8.2,
  "gcp_monthly_at_list": 2450.00,
  "gcp_monthly_net_of_discounts": 2280.00,
  "aws_compute_savings_plan_discount": "up to 66% (Fargate/Lambda/EC2; max term); typical 20-40% (1yr no-upfront)",
  "aws_database_savings_plan_discount": "up to 35% (serverless) / up to 20% (provisioned RDS/Aurora)",
  "aws_rds_reserved_instance_discount": "up to 69% (specific instance family, 3yr All Upfront)",
  "aws_1yr_savings_plan_typical_discount": "20-40%",
  "aws_3yr_savings_plan_typical_discount": "40-66%",
  "note": "GCP baseline uses list price for apples-to-apples comparison. Customer currently saves 8.2% via CUDs. AWS Savings Plans (compute + database) offer comparable or deeper discounts post-migration. Database Savings Plans and RDS Reserved Instances are mutually exclusive on the same workload. For Cloud Run → Fargate or GKE → Fargate (re-platform), commit Compute Savings Plans after establishing a 30-90 day AWS usage baseline."
}
```

If `commitments.has_active_cuds == false` or the section is absent, omit `commitment_context` from the output.

---

## Part 4: GCP Data Transfer Egress (Vendor Fees Only)

This section covers **GCP vendor/network charges** for outbound data during migration — not human labor or professional-services costs (those are never presented as dollar estimates by this advisor).

**Billing data check:** Before generating this section, check if `$MIGRATION_DIR/billing-profile.json` exists.

### IF billing data IS available (`billing-profile.json` exists):

**Data transfer** — egress fees from GCP during migration. GCP charges for outbound data transfer; volume depends on database sizes and storage to migrate. Use the billing data to estimate the volume of data that needs to move.

Set `billing_data_available: true` in the output `migration_cost_considerations` object.

### IF billing data is NOT available (`billing-profile.json` does not exist):

**Omit GCP data transfer fee estimates.** Without billing data, there is no grounding for egress projections. Instead, include only this note in the output:

Set `migration_cost_considerations` to:

```json
{
  "categories": [],
  "billing_data_available": false,
  "note": "Data transfer cost estimates require GCP billing data. Re-run discovery with a GCP billing export to see GCP egress fee projections."
}
```

In the user-facing summary, when billing data is missing, state: "GCP data transfer egress estimates require billing data. Provide a billing export and re-run discovery to see vendor egress projections."

---

## Part 5: ROI Analysis

Present the monthly and annual cost difference between GCP baseline and each AWS tier (Premium, Balanced, Optimized). This is the recurring savings (or increase) the customer can expect.

- If AWS is cheaper: present the monthly and annual savings for each tier
- If AWS is more expensive: state clearly and note that cost savings alone do not justify migration — operational benefits must be the driver

**Operational efficiency factors to highlight** (qualitative — do not assign dollar values):

- Reduction in operational overhead from managed services (Fargate vs self-managed, RDS vs self-hosted DB)
- Reduced on-call burden from AWS-managed HA, patching, and scaling
- Engineering time freed for product work instead of infrastructure maintenance

**Non-cost benefits to present:** operational efficiency, global reach, service breadth, enterprise integration, vendor diversification, scaling flexibility (auto-scaling, spot instances, savings plans).

**Note:** GCP data transfer egress fees (if estimated in Part 4) are **vendor** one-time charges excluded from recurring ROI calculations — not human migration costs.

---

## Part 6: Cost Optimization Opportunities

**Relationship to cost tiers:** Premium / Balanced / Optimized totals in Part 2 are **pricing scenarios** for the same design. The **Optimized** tier already assumes illustrative trade-offs (e.g. reserved DB pricing, Fargate Spot). Entries in `optimization_opportunities` are **incremental post-migration actions** beyond the Balanced on-demand baseline — do **not** add their savings on top of Optimized tier totals (which already embed assumptions).

Present applicable optimizations with estimated savings:

| Optimization                   | Savings Range                               | Applies To                                                                          | When                                            |
| ------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------- |
| Compute Savings Plans          | 20–66%                                      | Fargate, Lambda, EC2                                                                | Post-migration (after 30–90 day usage baseline) |
| Database Savings Plans         | Up to 35% (serverless) / ~20% (provisioned) | Aurora, RDS, DynamoDB, ElastiCache, DocumentDB, Neptune, Keyspaces, Timestream, DMS | Post-migration or after instance right-sizing   |
| RDS Reserved Instances         | Up to 69%                                   | RDS, Aurora (provisioned)                                                           | Post-migration (after architecture stabilizes)  |
| S3 Intelligent-Tiering / S3-IA | 38–50%                                      | S3 storage                                                                          | During migration                                |
| Spot Instances                 | 60–90%                                      | Batch/non-critical EC2 workloads                                                    | If batch jobs exist                             |

For each applicable optimization:

- **Compute Savings Plans:** emit percent range and post-migration timing; **omit `savings_monthly`** unless 30+ days of AWS usage data exist — do not size commitments from GCP Cloud Run or GKE billing alone (see below).
- **Database Savings Plans / RDS RIs:** may include preliminary `savings_monthly` when the Design phase mapped a target instance class **and** projected monthly DB on-demand cost exceeds **$50/month**; otherwise percent-only guidance.
- **S3 / Spot:** calculate before/after monthly cost when quantities are known from design.

Cross-reference Clarify when available: `cloud_run_traffic_pattern = business-hours` strengthens post-migration baseline guidance for compute; `constant-24-7` allows slightly more confidence in floor sizing — still post-migration for Compute Savings Plans.

### Compute Savings Plans (Fargate / Lambda)

**Relevance to GCP migrations:**

| Source                                 | Fargate commitment sizing from GCP data?               | Notes                                                                                                                                                                                                                                            |
| -------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Cloud Run → Fargate**                | **Unreliable**                                         | Variable-priced, scales to zero, bills per-request. GCP billing does not map 1:1 to Fargate vCPU-hours.                                                                                                                                          |
| **GKE → Fargate** (re-platform to ECS) | **Unreliable for commitment; useful for sanity check** | Node pools are often 24/7 with known machine types — you can rough-estimate vCPU-hours from node count × machine type. But re-platforming changes task sizing, autoscaling, and bin-packing; do not purchase a Savings Plan from GCP data alone. |
| **GKE → EKS** (keep Kubernetes)        | **Partial**                                            | Compute Savings Plans apply to **EC2 worker nodes** or **EKS Fargate profiles**, not the EKS control plane fee (~$0.10/hr per cluster). Post-migration baseline still recommended after right-sizing.                                            |

**What Compute Savings Plans offer:**

- Up to **66%** savings on Fargate, Lambda, and EC2 vs On-Demand at maximum term/discount ([source](https://aws.amazon.com/savingsplans/compute-pricing/))
- Commitment measured in **$/hour** — not tied to specific instance types, regions, or services
- Applies automatically across EC2, Fargate, and Lambda regardless of instance family, size, AZ, region, OS, or tenancy ([source](https://aws.amazon.com/savingsplans/faqs/))
- 1-year or 3-year terms; deeper discounts for longer terms and higher upfront payment

**Guidance for workloads migrating to Fargate (Cloud Run or GKE re-platform):**

The plugin SHALL present Compute Savings Plans as a **post-migration optimization** and SHALL NOT size a commitment from GCP billing data alone:

1. **Run on On-Demand for 30–90 days post-migration** to establish an AWS usage baseline
2. **Use AWS Cost Explorer Savings Plans Recommendations** — after 30+ days, Cost Explorer generates personalized recommendations based on actual hourly usage floor
3. **Commit to the usage floor, not the average** — cover minimum sustained usage; burst above the commitment bills at On-Demand with no penalty
4. **Consider rolling Savings Plans** — purchase smaller plans staggered quarterly to reduce risk if usage patterns change ([source](https://aws.amazon.com/blogs/aws-cloud-financial-management/how-can-i-use-rolling-savings-plans-to-reduce-commitment-risk/))

**Emit in `optimization_opportunities` when Fargate or Lambda is in `aws-design.json`:**

```json
{
  "opportunity": "Compute Savings Plans",
  "type": "compute_savings_plan",
  "target_services": ["Fargate", "Lambda"],
  "savings_percent": "20-66%",
  "savings_monthly": null,
  "commitment": "1-year or 3-year",
  "timing": "post-migration (after 30-90 days of usage data)",
  "implementation_effort": "low",
  "prerequisite": "Establish AWS compute usage baseline before committing",
  "description": "GCP compute billing (Cloud Run variable pricing or GKE re-platform to Fargate) makes pre-migration commitment sizing unreliable. GKE node pool sizing may sanity-check the floor but do not commit from GCP data alone. Use AWS Cost Explorer recommendations after migration to size the commitment to your actual usage floor.",
  "references": [
    "https://aws.amazon.com/savingsplans/compute-pricing/",
    "https://aws.amazon.com/savingsplans/faqs/"
  ]
}
```

### Database Savings Plans and Reserved Instances (Aurora / RDS)

**Relevance to GCP migrations:** Cloud SQL instances typically run 24/7 with a known instance size. Unlike Cloud Run, Cloud SQL usage translates well to AWS RDS/Aurora steady-state workloads — commitment sizing is more predictable from source configuration.

**What Database Savings Plans offer:**

- Up to **35%** on serverless deployments; up to **~20%** on provisioned RDS/Aurora instances ([source](https://aws.amazon.com/blogs/aws/introducing-database-savings-plans-for-aws-databases/))
- **1-year term only**, no upfront payment required ([source](https://aws.amazon.com/about-aws/whats-new/2025/12/database-savings-plans-savings/))
- Applies across eligible usage regardless of engine, instance family, size, deployment option, or Region
- **Mutually exclusive with RDS Reserved Instances on the same workload** — choose one discount model per database workload; you may use RIs on one workload and Database Savings Plans on another

**What RDS Reserved Instances offer (alternative):**

- Up to **69%** savings for 1-year or 3-year terms ([source](https://aws.amazon.com/rds/reserved-instances/))
- Payment options: No Upfront (~30%), Partial Upfront (~36% 1yr), All Upfront (~42% 1yr); 3-year terms up to 69%
- Locked to specific instance family, size, and region — less flexible but deeper discounts than Database Savings Plans

**Guidance for Cloud SQL → Aurora/RDS migrations:**

When Cloud SQL maps to a prod-tier instance with **> $50/month** projected on-demand DB cost:

1. Map source instance to AWS instance class (from Design phase)
2. Present Database Savings Plan benefit — 1-year, up to 35% (serverless) or ~20% (provisioned), flexible engine/instance changes
3. Present RI alternative for deeper savings when instance family is stable for 1+ years
4. **Recommend Database Savings Plans over RIs for migrations** — post-migration right-sizing flexibility outweighs RI depth for most customers

For dev-tier databases (< $50/month on-demand), emit percent-only guidance without dollar `savings_monthly`.

**Emit in `optimization_opportunities` when RDS or Aurora is in `aws-design.json`:**

```json
{
  "opportunity": "Database Savings Plans",
  "type": "database_savings_plan",
  "target_services": ["Aurora", "RDS"],
  "savings_percent": "up to 35% (serverless) / up to 20% (provisioned)",
  "savings_monthly": 4.50,
  "commitment": "1-year no-upfront",
  "timing": "immediately post-migration or after instance right-sizing",
  "implementation_effort": "low",
  "prerequisite": "Confirm target instance class and expected steady-state usage; omit savings_monthly when DB on-demand < $50/month",
  "description": "Cloud SQL 24/7 usage is predictable. Database Savings Plans offer flexibility to change engines/instances post-migration. Mutually exclusive with RDS RIs on the same workload.",
  "alternative": {
    "opportunity": "RDS Reserved Instances",
    "type": "rds_reserved_instances",
    "savings_percent": "up to 69%",
    "trade_off": "Locked to specific instance family and region — less flexibility during post-migration optimization"
  },
  "references": [
    "https://aws.amazon.com/savingsplans/database-pricing/",
    "https://aws.amazon.com/rds/reserved-instances/",
    "https://aws.amazon.com/about-aws/whats-new/2025/12/database-savings-plans-savings/"
  ]
}
```

---

## Part 7: Recommendation

Present 3 paths:

1. **Migrate with Optimizations (Best ROI)** — optimized service choices, monthly cost, projected annual savings
2. **Phased Migration (Lower Risk)** — cluster-by-cluster per design evaluation order, validate each before proceeding
3. **Stay on GCP (Lowest Cost)** — only if AWS is more expensive and costs are the sole metric

Include migrate/stay decision factors:

- **Migrate if:** operational efficiency matters, AWS-specific services needed, batch workloads (Spot savings), long-term AWS strategy, growing infrastructure
- **Stay if:** cost is the only metric and AWS is more expensive, team deeply experienced with GCP, no need for AWS-specific services

### Persist recommendation to estimation-infra.json

Part 7 MUST write the following `recommendation` block to `estimation-infra.json`. This is the single source of truth consumed by the HTML migration report (Section 0) and the Estimate chat summary. Do NOT duplicate this logic elsewhere.

```json
"recommendation": {
  "path": "migrate_optimized|migrate_phased|stay",
  "path_label": "Migrate with Optimizations|Phased Migration|Stay on GCP",
  "roi_justification": "string — one-sentence ROI case from Part 5",
  "confidence": "high|medium|low",
  "migrate_if": [
    "string — each factor that favors migration for THIS stack"
  ],
  "stay_if": [
    "string — each factor that favors staying for THIS stack"
  ],
  "next_steps": [
    "string — actionable items from Part 7"
  ]
}
```

**Enum normalization for `path`:**

| Scenario                                     | `path` value          | `path_label` (display)         |
| -------------------------------------------- | --------------------- | ------------------------------ |
| AWS cheaper or operational benefits justify  | `"migrate_optimized"` | `"Migrate with Optimizations"` |
| Complex stack, phase-by-phase safer          | `"migrate_phased"`    | `"Phased Migration"`           |
| AWS more expensive AND costs are sole metric | `"stay"`              | `"Stay on GCP"`                |

Use `path` for machine consumption; `path_label` for display in report and chat.

**Required fields:** `path`, `path_label`, `confidence`, `migrate_if` (non-empty array), `stay_if` (non-empty array), `next_steps` (non-empty array). `roi_justification` is optional (omit when `path` is `"stay"`).

Tailor `migrate_if` and `stay_if` to THIS stack (deferred services, AI cost delta, CUD lock-in, team GCP depth, etc.) — do not copy the generic Part 7 bullets verbatim unless they apply.

---

## Output

Read `steering/schema-estimate-infra.md` for the `estimation-infra.json` schema and validation checklist, then write `estimation-infra.json` to `$MIGRATION_DIR/`.

## Completion Handoff Gate (Fail Closed)

Load `steering/handoff-gates.md`. **Re-read from disk** before checking.

Before returning control to `estimate.md`, require:

- `estimation-infra.json` exists and passes `steering/schema-estimate-infra.md` validation.
- `recommendation.path` is one of `migrate_optimized`, `migrate_phased`, or `stay`
- `recommendation.path_label` is non-empty
- `recommendation.migrate_if` and `recommendation.stay_if` are non-empty arrays (Part 7 MUST persist `recommendation`)

**On FAIL:** Emit `GATE_FAIL | phase=estimate | field=<path> | reason=missing`. **Do NOT patch `estimation-infra.json` to pass the gate.** STOP — do not return control to `estimate.md` for phase completion.

**On PASS:** Emit `HANDOFF_OK | phase=estimate | artifacts=estimation-infra.json` (parent `estimate.md` emits the combined handoff after all routes pass).

## Present Summary

After writing `estimation-infra.json`, present a concise summary to the user:

1. **Pricing source and accuracy**: State whether prices came from cache or live API, and the accuracy range (±5-10% for infrastructure from cache/live, ±15-25% if cache is stale). Example: "Estimates based on cached AWS pricing (2026-03-07), accuracy ±5-10%."
2. GCP baseline vs AWS projected (balanced tier) — one-line comparison
3. Three-tier table: **Premium**, **Balanced**, **Optimized** with monthly totals. Under or beside each label, use the **short subtitles**: Premium — _Highest resilience / highest monthly estimate in this model_; Balanced — _Default scenario; compare GCP to this first_; Optimized — _Lower monthly estimate; reservations / Spot / storage trade-offs assumed_. Add a one-line **How to read**: three figures are **pricing scenarios** for the same architecture (high → mid → low); **not** three Terraform stacks. When Terraform is generated later, it aligns with **Balanced**.
4. Per-service cost breakdown (balanced tier, 1 line per service)
5. **If billing data available**: Estimated GCP data transfer egress fees. **If billing data NOT available**: "Data transfer cost estimates require GCP billing data."
6. Monthly and annual savings (or increase) vs GCP per tier
7. Top 2-3 optimization opportunities with savings amounts
8. **Recommendation:** `recommendation.path_label` with one-line ROI justification when present

Keep it under 25 lines. The user can ask for details or re-read `estimation-infra.json` at any time.

## Generate Phase Integration

The Generate phase (`generate.md`) uses `estimation-infra.json` as follows:

1. **`projected_costs.breakdown`** — Budget allocation per cluster migration phase
2. **`migration_cost_considerations`** — Data transfer egress cost estimates (if billing data available)
3. **`optimization_opportunities`** — Which optimizations to implement and when (some during initial migration, some post-migration)
4. **`cost_comparison`** — Set cost monitoring targets and alerts for each migrated cluster
5. **`recommendation`** — Migrate/stay guidance (`path`, `path_label`, `migrate_if`, `stay_if`, `next_steps`); consumed by HTML report Section 0
6. **Cost tier vs Terraform** — Generated **`terraform/`** implements **one** baseline aligned with the **Balanced** scenario; **Premium** and **Optimized** are **estimate-only** bands unless the user changes IaC. See `generate-artifacts-infra.md` (`terraform/README.md`, `migration_summary` output).

The generated artifacts reference the cost estimates to set per-cluster cost monitoring thresholds and validate that actual AWS spend aligns with projections after each cluster migration.
