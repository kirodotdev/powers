# Fast Path: Unconditional Mappings

> This file contains deterministic resource mappings that skip the evaluation rubric entirely. Use as a lookup table in Pass 1 of Design phase.
>
> **CRITICAL:** If a resource type appears in any table below, use the mapping directly. Do NOT proceed to Pass 2 rubric evaluation. This is not optional guidance — it is an authoritative lookup.

---

## Purpose

Fast-path mappings are 100% deterministic mappings with **zero viable alternatives** and **no config-dependent conditions**. They encode domain knowledge that doesn't change:

- Single candidate (no alternatives to evaluate)
- No eliminator rules apply (service limits don't matter)
- Operational model is identical
- No conflicts possible

Example: `google_compute_network` always maps to `aws_vpc`. There is no alternative VPC service on AWS. No rubric needed.

---

## Direct Mappings (Primary)

Unconditional mappings for primary resources. These resolve in Pass 1 without rubric evaluation.

**Usage:** If resource type matches column 1, use mapping in column 2. Set `confidence: "deterministic"`. Add `new_aws_resources` from column 4. Do not proceed to Pass 2.

| GCP Resource Type | AWS Target | Reason | new_aws_resources |
|---|---|---|---|
| `google_compute_network` | `aws_vpc` | Single candidate for VPC abstraction. No alternatives on AWS. Always 1:1. | `[aws_internet_gateway, aws_route_table, aws_route]` |
| `google_compute_subnetwork` | `aws_subnet` | Single candidate for subnet abstraction. Always 1:1. | `[]` |
| `google_storage_bucket` | `aws_s3_bucket` | Single candidate for object storage. Storage class affects S3 tier but destination is always S3. | `[]` |
| `google_compute_firewall` | `aws_security_group` | Single candidate for firewall rules. Always 1:1. | `[]` |
| `google_dns_record_set` | `aws_route53_record` | Single candidate for DNS records. Always 1:1. | `[]` |
| `google_dns_managed_zone` | `aws_route53_zone` | Single candidate for managed DNS zone. Always 1:1. | `[]` |
| `google_sql_database_instance` (PostgreSQL) | `aws_rds_cluster` (Aurora PostgreSQL) | 1:1 mapping; Serverless v2 for dev, Provisioned for prod. | `[aws_rds_cluster_instance]` |
| `google_sql_database_instance` (MySQL) | `aws_rds_cluster` (Aurora MySQL) | 1:1 mapping; Serverless v2 for dev, Provisioned for prod. | `[aws_rds_cluster_instance]` |
| `google_sql_database_instance` (SQL Server) | `aws_db_instance` (SQL Server) | 1:1 mapping; always provisioned (no serverless). | `[]` |
| `google_redis_instance` | `aws_elasticache_replication_group` | 1:1 mapping; preserve cluster mode and node type. | `[aws_elasticache_subnet_group]` |
| `google_service_account` | `aws_iam_role` | 1:1 mapping; map permissions directly, adjust service principals. | `[aws_iam_role_policy]` |

---

## Skip Mappings

Resources that should never be mapped to AWS resources. Record in "Skipped Resources" section of aws-design-report.md.

**Usage:** If resource type matches below, skip it entirely. Do NOT map to AWS. Record reason in report.

| GCP Resource Type | Reason |
|---|---|
| `google_project_service` | API enablement is implicit on AWS. Services are enabled by default. No AWS equivalent needed. |
| `data.google_service_account` | Data source only (read-only). No mapping needed. Use actual service account if created. |
| `null_resource` | Terraform orchestration artifact. Not needed on AWS. |
| `time_sleep` | Terraform orchestration artifact. Not needed on AWS. |

---

## Secondary Behavior Lookups

Determines how secondary resources map **based on what their primary became**.

**Usage (Pass 1):**
1. Primary is resolved (fast-path or rubric)
2. Secondary's `serves` array is checked
3. For each primary the secondary serves, look up behavior in this table
4. If found: apply behavior. If not found: check "Direct Mappings (Secondary)" table

**Format:** If secondary_role matches column 1 AND primary became the AWS service in column 2, apply column 3.

| Secondary Role | Primary Becomes | Behavior | Target | Notes |
|---|---|---|---|---|
| `identity` | `aws_lambda_function` | maps | `aws_iam_role` | Lambda requires explicit IAM role |
| `identity` | `aws_ecs_task_definition` | maps | `aws_iam_role` | ECS task requires explicit IAM role |
| `identity` | `aws_apprunner_service` | maps | `aws_iam_role` | App Runner requires explicit IAM role |
| `identity` | `aws_ec2_instance` | absorbed | `aws_iam_instance_profile` | Instance profile is attached to instance config |
| `identity` | `aws_rds_cluster` | absorbed | (not separate) | RDS uses DB-level authentication |
| `identity` | skip | skip | (not needed) | If primary is skipped, identity not needed |
| `network_path` | `aws_vpc` | absorbed | (not separate) | Subnet, firewall rules absorbed into VPC config |
| `network_path` | `aws_security_group` | absorbed | (not separate) | Rules absorbed into security group config |
| `network_path` | skip | skip | (not needed) | If primary is skipped, network not needed |
| `access_control` | any | maps | `aws_iam_policy_statement` | IAM bindings become policy statements on roles |
| `access_control` | skip | skip | (not needed) | If primary is skipped, access control not needed |
| `configuration` | `aws_rds_db_instance` | absorbed | (db_name, db_user fields) | Database and user absorbed into RDS config |
| `configuration` | `aws_secretsmanager_secret` | absorbed | (secret fields) | Secret versions absorbed into secret config |
| `configuration` | `aws_route53_zone` | absorbed | (record config) | DNS records absorbed into zone config |
| `configuration` | skip | skip | (not needed) | If primary is skipped, configuration not needed |
| `encryption` | any | maps | `aws_kms_key_policy` | KMS permissions referenced in resource policy |
| `encryption` | skip | skip | (not needed) | If primary is skipped, encryption not needed |
| `orchestration` | any | skip | (not needed) | Terraform orchestration not needed on AWS |

---

## Direct Mappings (Secondary)

Mappings for secondary resources that don't depend on what their primary became. Use if not found in "Secondary Behavior Lookups" above.

**Usage (Pass 1):**
1. Secondary not resolved by "Secondary Behavior Lookups"
2. Check this table
3. If secondary type matches column 1: apply mapping in column 2

| GCP Secondary Type | AWS Target | Reason |
|---|---|---|
| `google_kms_crypto_key` | `aws_kms_key` | 1:1 mapping. Always separate resource. |
| `google_kms_key_ring` | (absorbed) | Key ring is metadata on aws_kms_key. Not separate. |
| `google_compute_router_nat` | `aws_nat_gateway` | 1:1 mapping. NAT routing rules absorbed into route table. |
| `google_compute_address` | `aws_eip` (if address_type=EXTERNAL) or `aws_nat_gateway` (if purpose=NAT) | Determined by config (address_type, purpose) — rubric needed if ambiguous. |

---

## Examples

### Example 1: Primary Fast-Path Resolution

**Resource:** `google_storage_bucket.data_lake`

**Pass 1 Evaluation:**
```
Check Direct Mappings (Primary) table:
  google_storage_bucket → aws_s3_bucket ✓ found

Result:
  source: "google_storage_bucket.data_lake"
  target: "aws_s3_bucket"
  confidence: "deterministic"
  reason: "Fast path: Object storage bucket → S3. Single candidate, no alternatives."
  source_config: { "storage_class": "NEARLINE", "lifecycle_rule": "delete after 90 days" }
  related: { "gcp": [], "aws": [] }
  new_aws_resources: []

Do NOT proceed to Pass 2 for this resource.
```

---

### Example 2: Secondary Fast-Path Resolution (After Primary)

**Primary Resolution (from fast-path or rubric):**
```
google_sql_database_instance → aws_rds_db_instance
```

**Secondary:** `google_sql_database.main` (secondary_role: configuration, serves: [google_sql_database_instance.main])

**Pass 1 Evaluation:**
```
Check Secondary Behavior Lookups:
  secondary_role=configuration, primary_becomes=aws_rds_db_instance
  → behavior: absorbed, target: (db_name field)  ✓ found

Result:
  source: "google_sql_database.main"
  target: "(absorbed into aws_rds_db_instance.database_name)"
  confidence: "deterministic"
  reason: "Fast path: Database configuration absorbed. Database name becomes db_name on RDS instance."
  related: { "gcp": ["google_sql_database_instance.main"] }

Do NOT proceed to Pass 2 for this resource.
```

---

### Example 3: Secondary Deferred to Pass 2

**Primary:** `google_cloud_run_service.api` (not in fast-path, needs rubric)

**Secondary:** `google_service_account.app` (secondary_role: identity, serves: [google_cloud_run_service.api])

**Pass 1 Evaluation:**
```
Check Secondary Behavior Lookups:
  secondary_role=identity, primary_becomes=??? (not yet resolved)

Primary not yet resolved. Cannot determine behavior.

Result: Leave secondary for Pass 2.

(After Pass 2 resolves primary to aws_apprunner_service,
 return to secondary in Pass 2 Phase 2)
```

---

### Example 4: Skip Mapping

**Resource:** `google_project_service.run`

**Pass 1 Evaluation:**
```
Check Skip Mappings table:
  google_project_service → skip ✓ found

Result:
  source: "google_project_service.run"
  target: "(skipped)"
  confidence: "deterministic"
  reason: "Fast path skip: API enablement not needed on AWS. Services are enabled by default."
  related: { "gcp": [], "aws": [] }

Note: Add to "Skipped Resources" section of aws-design-report.md

Do NOT proceed to Pass 2 for this resource.
```

---

## Pass 1 Algorithm

**For each resource in cluster (both primary and secondary):**

### Primary Resource

```
1. Is resource_type in "Direct Mappings (Primary)" table?
   YES → Record mapping. Set confidence=deterministic. Add new_aws_resources.
         Mark as RESOLVED. Do not proceed to Pass 2.
   NO  → Continue to step 2.

2. Is resource_type in "Skip Mappings" table?
   YES → Skip resource. Record in skipped list.
         Mark as RESOLVED. Do not proceed to Pass 2.
   NO  → Leave for Pass 2 (rubric evaluation)
```

### Secondary Resource

```
1. Are ALL primaries in secondary.serves[] already resolved?
   NO  → Leave for Pass 2 (wait for primaries)
   YES → Continue to step 2.

2. For each primary served:
   Check "Secondary Behavior Lookups" for (secondary_role, primary_became):
   FOUND → Record behavior. Mark secondary as RESOLVED. Do not proceed to Pass 2.
   NOT FOUND → Continue to step 3.

3. Is secondary_type in "Direct Mappings (Secondary)" table?
   YES → Record mapping. Mark as RESOLVED. Do not proceed to Pass 2.
   NO  → Leave for Pass 2 (rubric evaluation needed)
```

---

## After Pass 1

**If ALL resources resolved by Pass 1:**
- Write cluster block to aws-design.json
- Add all new_aws_resources to cluster's new_aws_resources array
- Update metadata: `resolved_by_fast_path` += count
- Move to next cluster (skip Pass 2 entirely)

**If ANY resources unresolved:**
- Record Pass 1 results (mapped, skipped, absorbed)
- Proceed to Pass 2 (rubric) for remaining resources
- Use Pass 1 results as context for Pass 2 evaluation

---

## Maintenance Notes

**Adding new fast-path mappings:**

1. Ensure mapping is **100% unconditional** (no config-dependent logic)
2. Verify **no viable alternative** exists on AWS
3. Include **clear reasoning** for why there's no ambiguity
4. Test with sample resources before committing

**Example (good candidate for fast-path):**
```
google_compute_instance → aws_ec2_instance
Reason: Single candidate. No serverless alternative for fixed VMs.
No config field changes this decision.
```

**Example (NOT a fast-path candidate):**
```
google_cloud_run_service → ??? (could be Lambda, App Runner, or ECS)
Reason: Timeout, memory, concurrency, GPU support, and scale behavior
determine candidate. Config-dependent. Needs rubric.
```

---

## Related Files

- `design.md` — Pass 1 (fast-path) and Pass 2 (rubric) algorithm
- `design-ref-index.md` — Lookup for which design-ref file contains resource
- `design-ref-compute.md` — Rubric rules for compute resources
- `design-ref-database.md` — Rubric rules for database resources
- `design-ref-networking.md` — Rubric rules for networking resources
- `design-ref-storage.md` — Rubric rules for storage resources
- `design-ref-messaging.md` — Rubric rules for messaging resources
- `design-ref-ai.md` — Rubric rules for AI/ML resources

---

**Last Updated:** 2026-02-24
**Status:** Active (Production)

