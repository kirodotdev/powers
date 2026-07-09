# Generate Phase: Migration Script Generation

> Loaded by generate.md after generate-artifacts-infra.md completes (terraform files generated).

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Transform the migration plan (`generation-infra.json`) into numbered migration scripts for data, container, secrets, and validation tasks.

**Outputs:**

- `scripts/` directory — Numbered migration scripts for data and service migration

## Prerequisites

Read the following artifacts from `$MIGRATION_DIR/`:

- `aws-design.json` (REQUIRED) — AWS architecture design with cluster-level resource mappings
- `generation-infra.json` (REQUIRED) — Migration plan with timeline and service assignments
- `preferences.json` (REQUIRED) — User preferences including target region, sizing, compliance

If any REQUIRED file is missing: **STOP**. Output: "Missing required artifact: [filename]. Complete the prior phase that produces it."

## Step 1: Detect Resource Categories

Scan `aws-design.json` clusters[].resources[] to determine which resource categories exist.
Set boolean flags for downstream script generation:

- **has_databases**: true if ANY resource has `aws_service` containing "RDS", "Aurora", "DynamoDB",
  "ElastiCache", "Redshift" OR `gcp_type` starting with `google_sql_`, `google_firestore_`,
  `google_bigtable_`, `google_bigquery_`, `google_redis_`
- **has_storage**: true if ANY resource has `aws_service` = "S3" OR `gcp_type` = `google_storage_bucket`
- **has_containers**: true if ANY resource has `aws_service` containing "Fargate", "ECS", "EKS"
  OR `gcp_type` starting with `google_cloud_run_`, `google_container_cluster`
- **has_secrets**: true if ANY resource has `aws_service` containing "Secrets Manager"
  OR `gcp_type` starting with `google_secret_manager_`
- **has_data_migration**: has_databases OR has_storage (used for script 02)

Report detected categories to user: "Resource categories detected: [list active flags]"

## Output Structure

Scripts 02-04 are generated **only** when the corresponding resource categories are detected:

```
$MIGRATION_DIR/
├── scripts/
│   ├── 01-validate-prerequisites.sh          # Always
│   ├── 02-migrate-data.sh                    # Only if has_data_migration
│   ├── 03-migrate-containers.sh              # Only if has_containers
│   ├── 04-migrate-secrets.sh                 # Only if has_secrets
│   └── 05-validate-migration.sh              # Always (adapts checks)
```

## Step 2: Generate Migration Scripts

### Script Rules

- Every script defaults to **dry-run mode** — requires `--execute` flag to make changes
- Every script includes a verification step after execution
- Scripts are numbered for execution order
- Scripts use `set -euo pipefail` for safety
- Scripts log all actions to `$MIGRATION_DIR/logs/`

### 01-validate-prerequisites.sh

Verify all prerequisites before migration:

- AWS CLI configured and authenticated
- Required IAM permissions present
- Target VPC and subnets exist (Terraform applied)
- GCP connectivity established (for data transfer)
- Required tools installed (aws, gcloud, terraform, jq)

### 02-migrate-data.sh — IF has_data_migration

**Skip this script entirely if `has_data_migration` is false.**

Based on database and storage resources in `aws-design.json`:

**Cloud SQL to RDS/Aurora** — include only if `has_databases`:

Read `preferences.json` → `design_constraints.db_size.value` to select the migration tool:

- `"<10GB"` → use **pg_dump/pg_restore**
- `"10-100GB"` or `"100-500GB"` → use **pgcopydb** (parallel copy; requires `wal_level=logical` on Cloud SQL)
- `">500GB"` → use **AWS DMS** (continuous replication; generate DMS task config instead of a shell export script)
- `"unknown"` → default to **pgcopydb** with a TODO comment to verify size before running

Generate the script with conditional branches based on `db_size`:

```bash
#!/usr/bin/env bash
set -euo pipefail
# Cloud SQL → RDS data migration
# Usage: ./02-migrate-data.sh [--execute]
#
# Tool selection based on database size (preferences.json design_constraints.db_size.value):
# <10GB: pg_dump/pg_restore
# 10-500GB: pgcopydb (parallel copy, 3-5x faster than pg_dump)
# >500GB: AWS DMS recommended — see README-DMS.md if generated
# unknown: pgcopydb (safer default at unknown scale)
# TODO: Verify database size before running — wrong tool choice can exceed your maintenance window.

DRY_RUN=true
[[ "${1:-}" == "--execute" ]] && DRY_RUN=false

echo "=== Database Migration: Cloud SQL → RDS ==="
echo "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY RUN' || echo 'EXECUTE')"

SOURCE_HOST="" # TODO: Set Cloud SQL IP
TARGET_HOST="" # From terraform output database_endpoint
DATABASE_NAME="" # TODO: Set database name
```

Then emit ONE of the following tool-specific blocks based on `db_size`:

**If `db_size` is `"<10GB"`** — emit pg_dump block:

```bash
# Tool: pg_dump/pg_restore (database < 10GB)
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would export from Cloud SQL using pg_dump: $DATABASE_NAME"
  echo "[DRY RUN] Would import to RDS using pg_restore: $TARGET_HOST"
else
  echo "Exporting from Cloud SQL with pg_dump..."
  PGPASSWORD="$SOURCE_DB_PASSWORD" pg_dump \
    -h "$SOURCE_HOST" -U postgres -d "$DATABASE_NAME" \
    -Fc -f /tmp/migration_dump.pgc
  echo "Importing to RDS with pg_restore..."
  PGPASSWORD="$TARGET_DB_PASSWORD" pg_restore \
    -h "$TARGET_HOST" -U postgres -d "$DATABASE_NAME" \
    -Fc /tmp/migration_dump.pgc
  rm -f /tmp/migration_dump.pgc
fi
```

**If `db_size` is `"10-100GB"` or `"100-500GB"`** — emit pgcopydb block:

```bash
# Tool: pgcopydb (database 10GB–500GB — parallel copy, 3-5x faster than pg_dump)
# Requires: pgcopydb installed, wal_level=logical on Cloud SQL source
# See: https://pgcopydb.readthedocs.io/
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would copy database using pgcopydb: $DATABASE_NAME"
  echo "[DRY RUN] Source: $SOURCE_HOST → Target: $TARGET_HOST"
else
  echo "Copying database with pgcopydb (parallel)..."
  pgcopydb copy db \
    --source "postgresql://postgres:${SOURCE_DB_PASSWORD}@${SOURCE_HOST}/${DATABASE_NAME}" \
    --target "postgresql://postgres:${TARGET_DB_PASSWORD}@${TARGET_HOST}/${DATABASE_NAME}" \
    --table-jobs 4 \
    --index-jobs 4
fi
```

**If `db_size` is `">500GB"`** — emit DMS guidance block instead of a shell script:

```bash
# Tool: AWS DMS (database > 500GB — continuous replication recommended)
# Single-pass export/import at this scale is high-risk and likely to exceed any maintenance window.
# AWS DMS provides continuous replication with a minimal cutover window (minutes, not hours).
#
# Steps:
# 1. Create a DMS replication instance in the target VPC
# 2. Create source endpoint (Cloud SQL PostgreSQL) and target endpoint (Aurora PostgreSQL)
# 3. Create a full-load + CDC replication task
# 4. Run full load, then let CDC catch up to < 1 second lag
# 5. Cut over DNS during the minimal lag window
#
# TODO: Configure DMS endpoints and task — see AWS DMS documentation:
# https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Source.PostgreSQL.html
echo "Database size > 500GB: AWS DMS is strongly recommended."
echo "See README-DMS.md for setup instructions."
echo "This script does not perform the migration directly at this scale."
```

**If `db_size` is `"unknown"`** — emit pgcopydb block with prominent TODO:

```bash
# Tool: pgcopydb (database size unknown — safer default than pg_dump at unknown scale)
# TODO: Verify your database size before running. If > 500GB, use AWS DMS instead.
# Requires: pgcopydb installed, wal_level=logical on Cloud SQL source
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would copy database using pgcopydb: $DATABASE_NAME"
  echo "[DRY RUN] TODO: Verify database size before executing"
else
  echo "Copying database with pgcopydb..."
  pgcopydb copy db \
    --source "postgresql://postgres:${SOURCE_DB_PASSWORD}@${SOURCE_HOST}/${DATABASE_NAME}" \
    --target "postgresql://postgres:${TARGET_DB_PASSWORD}@${TARGET_HOST}/${DATABASE_NAME}" \
    --table-jobs 4 \
    --index-jobs 4
fi
```

```bash
# Verification
echo "=== Verification ==="
echo "TODO: Compare row counts between source and target"
```

**BigQuery to S3** — include only if `has_databases`:

```bash
# BigQuery → S3 data export
# TODO: Configure BigQuery dataset and S3 bucket
# bq extract --destination_format=PARQUET 'dataset.table' 'gs://bucket/export/'
# aws s3 sync gs://bucket/export/ s3://target-bucket/import/
```

**Firestore to DynamoDB** — include only if `has_databases`:

```bash
# Firestore → DynamoDB migration
# TODO: Use AWS DMS or custom export/import script
```

### 03-migrate-containers.sh — IF has_containers

**Skip this script entirely if `has_containers` is false.**

Migrate container images from GCR/Artifact Registry to ECR:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Container image migration: GCR → ECR
# Usage: ./03-migrate-containers.sh [--execute]

DRY_RUN=true
[[ "${1:-}" == "--execute" ]] && DRY_RUN=false

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="us-east-1"  # From preferences.json target_region
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# TODO: List container images from aws-design.json compute resources
IMAGES=(
  "gcr.io/project/image1:latest"
  # Add more images from your GCP container registry
)

for IMAGE in "${IMAGES[@]}"; do
  IMAGE_NAME=$(echo "$IMAGE" | rev | cut -d'/' -f1 | rev | cut -d':' -f1)
  IMAGE_TAG=$(echo "$IMAGE" | rev | cut -d':' -f1 | rev)

  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would migrate: $IMAGE → $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
  else
    echo "Creating ECR repository: $IMAGE_NAME"
    aws ecr create-repository --repository-name "$IMAGE_NAME" --region "$AWS_REGION" 2>/dev/null || true

    echo "Pulling from GCR: $IMAGE"
    docker pull "$IMAGE"

    echo "Tagging for ECR: $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    docker tag "$IMAGE" "$ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

    echo "Pushing to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
    docker push "$ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
  fi
done

# Verification
echo "=== Verification ==="
echo "Listing ECR repositories..."
aws ecr describe-repositories --region "$AWS_REGION" --query 'repositories[].repositoryName' --output table
```

### 04-migrate-secrets.sh — IF has_secrets

**Skip this script entirely if `has_secrets` is false.**

Migrate secrets from GCP Secret Manager to AWS Secrets Manager:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Secrets migration: GCP Secret Manager → AWS Secrets Manager
# Usage: ./04-migrate-secrets.sh [--execute]

DRY_RUN=true
[[ "${1:-}" == "--execute" ]] && DRY_RUN=false

# TODO: List secrets to migrate
SECRETS=(
  "database-password"
  "api-key"
  # Add more secrets from your GCP project
)

for SECRET_NAME in "${SECRETS[@]}"; do
  if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would migrate secret: $SECRET_NAME"
  else
    echo "Reading secret from GCP: $SECRET_NAME"
    # Write to a restricted temp file — avoids secret values appearing in shell
    # variables, process lists (ps aux), or shell history. Cleaned up on exit.
    TMPFILE=$(mktemp)
    chmod 600 "$TMPFILE"
    trap 'rm -f "$TMPFILE"' EXIT

    gcloud secrets versions access latest --secret="$SECRET_NAME" > "$TMPFILE"

    echo "Creating/updating secret in AWS: $SECRET_NAME"
    aws secretsmanager create-secret \
      --name "$SECRET_NAME" \
      --secret-string "file://$TMPFILE" \
      --tags Key=MigrationSource,Value=gcp-secret-manager 2>/dev/null || \
    aws secretsmanager put-secret-value \
      --secret-id "$SECRET_NAME" \
      --secret-string "file://$TMPFILE"

    rm -f "$TMPFILE"
    trap - EXIT
  fi
done

# Verification
echo "=== Verification ==="
aws secretsmanager list-secrets --query 'SecretList[].Name' --output table
```

### 05-validate-migration.sh

Post-migration validation script. **Always generated**, but adapt checks based on which resource
categories were detected in Step 1. Only include validation sections for resources that exist.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Post-migration validation
# Usage: ./05-validate-migration.sh

echo "=== Migration Validation ==="

# Check Terraform state (always included)
echo "--- Terraform Resources ---"
cd terraform/
terraform state list | wc -l
echo "resources in Terraform state"

# --- Include ONLY if has_containers ---
# Check ECS services
echo "--- ECS Services ---"
aws ecs list-services --cluster "${PROJECT_NAME:-gcp-migration}" --query 'serviceArns' --output table 2>/dev/null || echo "No ECS cluster found"

# --- Include ONLY if has_databases ---
# Check RDS instances
echo "--- RDS Instances ---"
aws rds describe-db-instances --query 'DBInstances[].{ID:DBInstanceIdentifier,Status:DBInstanceStatus,Endpoint:Endpoint.Address}' --output table 2>/dev/null || echo "No RDS instances found"

# --- Include ONLY if has_storage ---
# Check S3 buckets
echo "--- S3 Buckets ---"
aws s3 ls | grep "${PROJECT_NAME:-gcp-migration}" || echo "No matching S3 buckets found"

# --- Include ONLY if has_secrets ---
# Check secrets
echo "--- Secrets Manager ---"
aws secretsmanager list-secrets --query 'SecretList[].Name' --output table 2>/dev/null || echo "No secrets found"

echo "=== Validation Complete ==="
echo "Review the output above. All resources should show healthy status."
echo "TODO: Run application-level health checks"
echo "TODO: Compare performance metrics against GCP baseline"
```

## Step 3: Self-Check

After generating all scripts, verify the following quality rules:

### Script Quality Rules

1. All scripts use `set -euo pipefail`
2. All scripts default to dry-run mode
3. All scripts include verification steps
4. All scripts are numbered for execution order
5. All TODO markers are clearly marked with context

## Phase Completion

Report the list of generated script files to the parent orchestrator. **Do NOT update `.phase-status.json`** — the parent `generate.md` handles phase completion.

Only list scripts that were actually generated (based on Step 1 resource detection flags):

```
Resource categories detected: [list active flags from Step 1]

Generated migration scripts:
- scripts/01-validate-prerequisites.sh
- scripts/02-migrate-data.sh                    # only if has_data_migration
- scripts/03-migrate-containers.sh              # only if has_containers
- scripts/04-migrate-secrets.sh                 # only if has_secrets
- scripts/05-validate-migration.sh

Total: [N] migration scripts
TODO markers: [N] items requiring manual configuration
Skipped scripts: [list any scripts not generated, with reason]
```
