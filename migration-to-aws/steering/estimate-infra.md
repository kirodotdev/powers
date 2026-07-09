# Estimate Phase: Infrastructure Cost Analysis

> Loaded by estimate.md when aws-design.json exists.

**Execute ALL steps in order. Do not skip or optimize.**

## Pricing Mode

The parent `estimate.md` determines pricing source before loading this file.

**Price lookup order for each AWS service in `aws-design.json`:**

1. **`steering/cached-prices.md` (primary)** — Read once. Look up each service by table. If found, use the price directly. No MCP call needed. Set `pricing_source: "cached"`.
2. **MCP with recipes (secondary)** — If a service is NOT in cached-prices.md and MCP is available, use the Pricing Recipes table below. Set `pricing_source: "live"`.

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
4. **Conservative default** — If none of the above: use `AWS monthly balanced × 1.25`.

Present the GCP baseline as a total and per-service breakdown, noting which source was used.

---

## Part 2: Calculate Projected AWS Costs

For each service in `aws-design.json`, calculate monthly cost using rates from `cached-prices.md`. Track `pricing_source` per service.

Calculate 3 cost tiers to show the optimization range:

| Tier          | Description                             | Examples                                                            |
| ------------- | --------------------------------------- | ------------------------------------------------------------------- |
| **Premium**   | Latest generation, highest availability | db.r6g instances, Fargate Spot disabled, Multi-AZ everything        |
| **Balanced**  | Standard generation, typical setup      | db.t4g instances, Fargate on-demand, Single-AZ where acceptable     |
| **Optimized** | Cost-minimized with trade-offs          | db.t4g with reserved pricing, Fargate Spot 70%, S3-IA for cold data |

**Per-service calculation approach:**

| Domain            | Formula                                                                               | Key inputs from aws-design.json                             |
| ----------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Compute (Fargate) | (vCPU × vCPU rate + memory GB × memory rate) × 730 hours × instance count             | `aws_config.cpu`, `aws_config.memory`                       |
| Compute (Lambda)  | requests × request rate + (requests × duration × memory GB) × GB-second rate          | Estimated from usage patterns                               |
| Database (Aurora) | instance rate × 730 hours × instance count + storage GB × storage rate + I/O estimate | `aws_config.instance_class`, `aws_config.allocated_storage` |
| Database (RDS)    | instance rate × 730 hours × instance count + storage GB × storage rate                | `aws_config.instance_class`, `aws_config.allocated_storage` |
| Storage (S3)      | GB × per-GB rate + request estimates                                                  | `aws_config.storage_gb` or source `gcp_config`              |
| Networking (ALB)  | fixed monthly + LCU estimate                                                          | From compute service count                                  |
| Networking (NAT)  | fixed monthly × count + GB processed × data rate                                      | From VPC design                                             |
| Supporting        | Per-unit rates × quantities (secrets, log GB, metrics)                                | Inferred from service count                                 |

Show calculation breakdown per service: rate × quantity = cost. Present all 3 tiers side-by-side.

---

## Part 3: Cost Comparison

Present a side-by-side comparison:

- GCP current monthly total
- AWS Premium / Balanced / Optimized monthly totals
- Difference (savings or increase) per tier vs GCP
- Per-service breakdown for the Balanced tier

---

## Part 4: ROI Analysis

Present the monthly and annual cost difference between GCP baseline and each AWS tier (Premium, Balanced, Optimized). This is the recurring savings (or increase) the customer can expect.

- If AWS is cheaper: present the monthly and annual savings for each tier
- If AWS is more expensive: state clearly and note that cost savings alone do not justify migration — operational benefits must be the driver

**Operational efficiency factors to highlight** (qualitative — do not assign dollar values):

- Reduction in operational overhead from managed services (Fargate vs self-managed, RDS vs self-hosted DB)
- Reduced on-call burden from AWS-managed HA, patching, and scaling
- Engineering time freed for product work instead of infrastructure maintenance

**Non-cost benefits to present:** operational efficiency, global reach, service breadth, enterprise integration, vendor diversification, scaling flexibility (auto-scaling, spot instances, savings plans).

---

## Part 5: Cost Optimization Opportunities

Present applicable optimizations with estimated savings:

| Optimization                       | Savings Range | Applies To                       | When                                    |
| ---------------------------------- | ------------- | -------------------------------- | --------------------------------------- |
| Reserved Instances / Savings Plans | 40-60%        | RDS, Aurora                      | Post-migration (after validating usage) |
| Compute Savings Plans              | 20-50%        | Fargate, Lambda                  | Post-migration                          |
| S3 Intelligent-Tiering / S3-IA     | 38-50%        | S3 storage                       | During migration                        |
| Spot Instances                     | 60-90%        | Batch/non-critical EC2 workloads | If batch jobs exist                     |

For each applicable optimization, calculate the before and after monthly cost.

---

## Part 6: Recommendation

Present 3 paths:

1. **Migrate with Optimizations (Best ROI)** — optimized service choices, monthly cost, projected annual savings
2. **Phased Migration (Lower Risk)** — cluster-by-cluster per design evaluation order, validate each before proceeding
3. **Stay on GCP (Lowest Cost)** — only if AWS is more expensive and costs are the sole metric

Include migrate/stay decision factors:

- **Migrate if:** operational efficiency matters, AWS-specific services needed, batch workloads (Spot savings), long-term AWS strategy, growing infrastructure
- **Stay if:** cost is the only metric and AWS is more expensive, team deeply experienced with GCP, no need for AWS-specific services

---

## Output

Read `steering/schema-estimate-infra.md` for the `estimation-infra.json` schema and validation checklist, then write `estimation-infra.json` to `$MIGRATION_DIR/`.

## Present Summary

After writing `estimation-infra.json`, present a concise summary to the user:

1. GCP baseline vs AWS projected (balanced tier) — one-line comparison
2. Three-tier table: Premium / Balanced / Optimized with monthly totals
3. Per-service cost breakdown (balanced tier, 1 line per service)
4. Monthly and annual savings (or increase) vs GCP per tier
5. Top 2-3 optimization opportunities with savings amounts

Keep it under 25 lines. The user can ask for details or re-read `estimation-infra.json` at any time.

## Generate Phase Integration

The Generate phase (`steering/generate.md`) uses `estimation-infra.json` as follows:

1. **`projected_costs.breakdown`** — Budget allocation per cluster migration phase
2. **`optimization_opportunities`** — Which optimizations to implement and when (some during initial migration, some post-migration)
4. **`cost_comparison`** — Set cost monitoring targets and alerts for each migrated cluster
5. **`recommendation.next_steps`** — Prerequisites for starting generation

The generated artifacts reference the cost estimates to set per-cluster cost monitoring thresholds and validate that actual AWS spend aligns with projections after each cluster migration.
