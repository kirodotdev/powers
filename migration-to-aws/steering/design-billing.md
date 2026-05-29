# Design Phase: Billing-Only Service Mapping

> Loaded by `design.md` when `billing-profile.json` exists and `gcp-resource-inventory.json` does NOT exist.

**Execute ALL steps in order. Do not skip or optimize.**

This is the fallback design path when only billing data is available (no Terraform/IaC). Mappings are inferred from billing service names and SKU descriptions — confidence is always `billing_inferred`.

---

## Step 0: Load Inputs

Read `$MIGRATION_DIR/billing-profile.json`. This file contains:

- `services[]` — Each GCP service with monthly cost, SKU breakdown, and AI signals
- `summary` — Total monthly spend and service count

Read `$MIGRATION_DIR/preferences.json` → `design_constraints` (target region, compliance, etc.).

Also read `preferences.json` → `metadata.inventory_clarifications` (may be empty if user defaulted all Category B questions). These are billing-only configuration answers collected during Clarify.

---

## Step 1: Load Billing Services

For each entry in `billing-profile.json` → `services[]`:

1. Extract `gcp_service` (display name, e.g., "Cloud Run")
2. Extract `gcp_service_type` (Terraform-style type, e.g., "google_cloud_run_service")
3. Extract `top_skus[]` for additional context (SKU descriptions hint at specific features)
4. Extract `monthly_cost` for cost context

---

## Step 2: Service Lookup

For each billing service, attempt lookup in order:

**2a. Fast-path lookup:**

1. Look up `gcp_service_type` in `steering/design-ref-fast-path.md` → Direct Mappings table
2. If found: assign AWS service
3. Enrich with SKU hints:
   - If `top_skus` mention "PostgreSQL" → specify "RDS Aurora PostgreSQL"
   - If `top_skus` mention "MySQL" → specify "RDS Aurora MySQL"
   - If `top_skus` mention "CPU Allocation" → indicates compute (Fargate)
   - If `top_skus` mention "Storage" → check if object storage (S3) or block storage (EBS)

**2b. Billing heuristic lookup (if not in fast-path):**

Look up `gcp_service_type` in the table below. These are default mappings for common GCP services when no configuration data is available. The IaC path uses the full rubric in category files and may select a different AWS target based on actual configuration.

| `gcp_service_type`               | Billing Name         | Default AWS Target | Alternatives (chosen by IaC path) |
| -------------------------------- | -------------------- | ------------------ | --------------------------------- |
| `google_cloud_run_service`       | Cloud Run            | Fargate            | Lambda, EC2                       |
| `google_cloudfunctions_function` | Cloud Functions      | Lambda             | Fargate                           |
| `google_compute_instance`        | Compute Engine       | EC2                | Fargate, ASG                      |
| `google_container_cluster`       | GKE                  | EKS                | ECS, Fargate                      |
| `google_app_engine_application`  | App Engine           | Fargate            | Amplify, Lambda                   |
| `google_firestore_database`      | Firestore            | DynamoDB           | —                                 |
| `google_bigquery_dataset`        | BigQuery             | Athena             | Redshift                          |
| `google_compute_forwarding_rule` | Cloud Load Balancing | ALB                | NLB                               |
| `google_compute_backend_service` | Cloud Load Balancing | ALB Target Groups  | NLB                               |
| `google_pubsub_topic`            | Pub/Sub              | SNS                | SQS, SNS FIFO                     |
| `google_pubsub_subscription`     | Pub/Sub              | SQS                | SNS Subscription                  |
| `google_cloud_tasks_queue`       | Cloud Tasks          | SQS                | EventBridge                       |

If found: assign the Default AWS Target. Set rationale to: "Billing heuristic: [GCP service] → [AWS service]. Provide Terraform files for configuration-aware mapping."

**2c. If not found in either table:** proceed to Step 3.

**2d. Enrich with Category B answers (if available):**

After lookup, check `metadata.inventory_clarifications` for user-provided configuration data and merge into `aws_config`:

- If `inventory_clarifications.cloud_sql_ha` exists → add `"high_availability": true/false` to the Cloud SQL / Aurora design entry
- If `inventory_clarifications.cloud_run_count` exists → set `"service_count"` in the Cloud Run / Fargate design entry
- If `inventory_clarifications.memorystore_memory` exists → set `"memory_gb"` in the Redis / ElastiCache design entry
- If `inventory_clarifications.cloud_functions_gen` exists → note `"functions_generation"` in the Cloud Functions / Lambda design entry

When a clarification is applied, add `"inventory_clarifications_applied": true` to the service's `aws_config`.

**No rubric evaluation** — without IaC config, there is insufficient data for the 6-criteria rubric.

---

## Step 3: Flag Unknowns

For each service not found in fast-path or billing heuristic table:

1. Record in `unknowns[]` with:
   - `gcp_service` — Display name
   - `gcp_service_type` — Resource type
   - `monthly_cost` — How much is spent on this service
   - `reason` — "No IaC configuration available; service does not match any fast-path or billing heuristic entry"
   - `suggestion` — "Provide Terraform files for accurate mapping, or manually specify the AWS equivalent"

---

## Step 4: Generate Output

**File 1: `aws-design-billing.json`**

Write to `$MIGRATION_DIR/aws-design-billing.json`:

```json
{
  "metadata": {
    "phase": "design",
    "design_source": "billing_only",
    "confidence_note": "All mappings inferred from billing data only — no IaC configuration available. Confidence is billing_inferred for all services.",
    "total_services": 8,
    "mapped_services": 6,
    "unmapped_services": 2,
    "timestamp": "2026-02-26T14:30:00Z"
  },
  "services": [
    {
      "gcp_service": "Cloud Run",
      "gcp_service_type": "google_cloud_run_service",
      "aws_service": "Fargate",
      "aws_config": {
        "region": "us-east-1"
      },
      "monthly_cost": 450.00,
      "confidence": "billing_inferred",
      "rationale": "Fast-path: Cloud Run → Fargate. SKU hints: CPU + Memory allocation.",
      "sku_hints": ["CPU Allocation Time", "Memory Allocation Time"]
    },
    {
      "gcp_service": "Cloud SQL",
      "gcp_service_type": "google_sql_database_instance",
      "aws_service": "RDS Aurora PostgreSQL",
      "aws_config": {
        "region": "us-east-1",
        "high_availability": false,
        "inventory_clarifications_applied": true
      },
      "monthly_cost": 800.00,
      "confidence": "billing_inferred",
      "rationale": "Fast-path: Cloud SQL → RDS Aurora. SKU hints: PostgreSQL engine. User confirmed single-zone (Category B).",
      "sku_hints": ["DB custom CORE", "DB custom RAM"]
    }
  ],
  "unknowns": [
    {
      "gcp_service": "Cloud Armor",
      "gcp_service_type": "google_compute_security_policy",
      "monthly_cost": 50.00,
      "reason": "No IaC configuration available; billing name does not match any fast-path entry",
      "suggestion": "Provide Terraform files for accurate mapping, or manually specify the AWS equivalent"
    }
  ]
}
```

## Output Validation Checklist

- `metadata.design_source` is `"billing_only"`
- `metadata.total_services` equals `mapped_services` + `unmapped_services`
- Every service from `billing-profile.json` appears in either `services[]` or `unknowns[]`
- All `confidence` values are `"billing_inferred"`
- Every `services[]` entry has `gcp_service`, `aws_service`, `monthly_cost`, `rationale`
- Every `unknowns[]` entry has `gcp_service`, `monthly_cost`, `reason`, `suggestion`
- Output is valid JSON

## Present Summary

After writing `aws-design-billing.json`, present a concise summary to the user:

1. Mapped X of Y GCP billing services to AWS equivalents
2. Accuracy notice: billing-inferred confidence, provide .tf files for higher accuracy
3. Per-service table: GCP service → AWS service (with monthly GCP cost)
4. Unmapped services list with suggestions
5. Total monthly GCP spend

Keep it under 20 lines. The user can ask for details or re-read `aws-design-billing.json` at any time.
