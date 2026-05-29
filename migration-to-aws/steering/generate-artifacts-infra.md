# Generate Phase: Infrastructure Artifact Generation

> Loaded by generate.md when generation-infra.json and aws-design.json exist.

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Transform the design (`aws-design.json`) and migration plan (`generation-infra.json`) into deployable Terraform configurations. Migration scripts are generated separately by `generate-artifacts-scripts.md`.

## Prerequisites

Read from `$MIGRATION_DIR/`:

- `aws-design.json` (REQUIRED) — AWS architecture design with cluster-level resource mappings
- `generation-infra.json` (REQUIRED) — Migration plan with timeline and service assignments
- `preferences.json` (REQUIRED) — User preferences including target region, sizing, compliance
- `gcp-resource-clusters.json` (REQUIRED) — Cluster dependency graph for ordering

Reference files (read as needed): `steering/design-ref-index.md` and domain-specific files (`steering/design-ref-compute.md`, `steering/design-ref-database.md`, `steering/design-ref-storage.md`, `steering/design-ref-networking.md`, `steering/design-ref-messaging.md`, `steering/design-ref-ai.md`).

If any REQUIRED file is missing: **STOP**. Output: "Missing required artifact: [filename]. Complete the prior phase that produces it."

## Output Structure

Generate `$MIGRATION_DIR/terraform/` with only the files needed for domains that have resources in `aws-design.json`:

| File            | Domain     | Contains                                         |
| --------------- | ---------- | ------------------------------------------------ |
| `main.tf`       | core       | Provider config, backend, data sources           |
| `variables.tf`  | core       | All input variables with types and defaults      |
| `outputs.tf`    | core       | Resource outputs and migration summary           |
| `vpc.tf`        | networking | VPC, subnets, NAT, security groups, route tables |
| `security.tf`   | security   | IAM roles, policies, KMS keys                    |
| `storage.tf`    | storage    | S3 buckets, EFS, backup vaults                   |
| `database.tf`   | database   | RDS/Aurora instances, parameter groups           |
| `compute.tf`    | compute    | Fargate/ECS, Lambda, EC2                         |
| `monitoring.tf` | monitoring | CloudWatch dashboards, alarms, log groups        |

## Step 0: Plan Generation Scope

Build a generation manifest: read all resources from `aws-design.json` clusters, assign each to its target .tf file by `aws_service`:

| AWS Service                                           | Target File     |
| ----------------------------------------------------- | --------------- |
| VPC, Subnet, NAT Gateway, Security Group, Route Table | `vpc.tf`        |
| IAM Role, IAM Policy, KMS Key                         | `security.tf`   |
| S3, EFS, Backup Vault                                 | `storage.tf`    |
| RDS, Aurora, DynamoDB, ElastiCache                    | `database.tf`   |
| Fargate, ECS, Lambda, EC2                             | `compute.tf`    |
| CloudWatch, SNS (for alarms)                          | `monitoring.tf` |

## Step 1: Generate main.tf

**Requirements:**

- `terraform` block: `required_version >= 1.5.0`, `hashicorp/aws ~> 5.0`, commented S3 backend
- `provider "aws"` block: `region = var.aws_region`, `default_tags` with Project, Environment, ManagedBy, MigrationId
- Data sources: `aws_caller_identity`, `aws_region`, `aws_availability_zones`

## Step 2: Generate variables.tf

**Global variables (always include):** `aws_region` (from `preferences.json` target_region), `project_name`, `environment` (from `preferences.json`), `migration_id`.

**Per-cluster variables:** Extract configurable values from `aws_config` in `aws-design.json`. Infer types (`string`, `number`, `bool`, `list(string)`, `map(string)`). Use `aws_config` values as defaults. Deduplicate shared variables. Add GCP source as comment (e.g., `# GCP source: db-custom-2-7680`).

## Step 3: Generate Per-Domain .tf Files

For each domain with resources in the generation manifest:

**General rules:**

- Consult `steering/design-ref-*.md` for AWS configuration best practices
- A single GCP resource may map to multiple AWS resources (1:Many expansion)
- Use `gcp_config` values from `aws-design.json` to populate resource attributes
- For `confidence: "inferred"` resources, add comment: `# Inferred mapping — verify configuration`
- Include `secondary_resources` from the cluster (IAM roles, security groups)
- Tag every resource: Project, Environment, ManagedBy, MigrationId

**Domain-specific rules:**

| Domain     | Key Rules                                                                                                                     |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Networking | At least 2 AZs; public + private subnets; NAT gateway for private subnet internet                                             |
| Security   | Least-privilege IAM (specific ARNs, never wildcards); per-service roles for Fargate/Lambda                                    |
| Storage    | Versioning enabled; SSE-S3 or SSE-KMS encryption; block public access; lifecycle policies                                     |
| Database   | Private subnets; subnet group + parameter group + security group; backups; encryption                                         |
| Compute    | Fargate in private subnets; task definitions from `aws_config` CPU/memory; auto-scaling                                       |
| Monitoring | Log groups per service; dashboard with key metrics; alarms from `generation-infra.json` success_metrics; 30-day log retention |

## Step 4: Generate outputs.tf

Output identifiers for key resources (VPC ID, database endpoint, ECS cluster name, etc.) plus a `migration_summary` output with region, VPC ID, environment, service count, and migration ID.

## Step 5: Self-Check

Verify these quality rules before reporting completion:

- [ ] No wildcard IAM policies (`"Action": "*"` or `"Resource": "*"`)
- [ ] No default VPC references — all resources use the created VPC
- [ ] No hardcoded credentials in any .tf file
- [ ] Tags on every resource (Project, Environment, ManagedBy, MigrationId)
- [ ] Encryption at rest on all storage (S3, EBS, RDS)
- [ ] Databases and internal services use private subnets
- [ ] No `0.0.0.0/0` ingress except ALB port 443
- [ ] Every variable has `type` and `description`
- [ ] Every output has `description`
- [ ] Region from `var.aws_region`, never hardcoded

## Phase Completion

Report generated files to the parent orchestrator. **Do NOT update `.phase-status.json`** — the parent `generate.md` handles phase completion.

```
Generated terraform artifacts:
- terraform/main.tf
- terraform/variables.tf
- terraform/outputs.tf
- terraform/[domain].tf (for each domain with resources)

Total: [N] Terraform files
TODO markers: [N] items requiring manual configuration
```
