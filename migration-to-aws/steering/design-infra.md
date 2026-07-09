# Design Phase: Infrastructure Mapping

> Loaded by `design.md` when `gcp-resource-inventory.json` and `gcp-resource-clusters.json` exist.

**Execute ALL steps in order. Do not skip or optimize.**

## Step 0: Validate Inputs

Read `preferences.json`. If missing: **STOP**. Output: "Phase 2 (Clarify) not completed. Run Phase 2 first."

Read `gcp-resource-clusters.json`.

## Step 1: Order Clusters

Sort clusters by `creation_order_depth` (lowest first, representing foundational infrastructure).

## Step 2: Two-Pass Mapping per Cluster

For each cluster, process `primary_resources` first, then `secondary_resources` (as classified during discover phase — see `gcp-resource-clusters.json`).

### Pass 1: Fast-Path Lookup (Direct Mappings table only)

For each PRIMARY resource in the cluster:

1. Extract GCP type (e.g., `google_sql_database_instance`)
2. Look up in `steering/design-ref-fast-path.md` → **Direct Mappings** table (not the Preferred Target table — that applies later in Pass 2).
3. If found and conditions match: assign AWS service with confidence = **`deterministic`**. Set `human_expertise_required: false` (no Direct Mapping row requires it).
4. If `gcp_type` is `google_sql_database_instance` with PostgreSQL or MySQL engine: **always proceed to Pass 2** (Cloud SQL is not in Direct Mappings — see `design-ref-fast-path.md`). Confidence = **`inferred`** after rubric.
5. If not found: proceed to Pass 2 (confidence will be **`inferred`** after rubric, or **`billing_inferred`** on the billing-only path).

**Definitions:** See the top of `steering/design-ref-fast-path.md` for **`deterministic` vs `inferred` vs `billing_inferred`** and the note that **design-ref-index.md “Typical AWS target” ≠ deterministic**.

### Pass 2: Rubric-Based Selection

For resources not covered by fast-path:

**0. BigQuery specialist gate (mandatory — before rubric):** If `gcp_type` **starts with** `google_bigquery_` (e.g. `google_bigquery_dataset`, `google_bigquery_table`, `google_bigquery_routine`, `google_bigquery_data_transfer_config`, `google_bigquery_job`, `google_bigquery_ml_*`):

1. **Do not** recommend a specific AWS analytics or warehouse service (Athena, Redshift, Glue, EMR, Lake Formation, or a prescribed “data lake on S3” architecture).
2. Set `aws_service` to **`Deferred — specialist engagement`**, `human_expertise_required` to **`true`**, `confidence` to **`inferred`**, and `aws_config` to include `specialist_engagement` (text: engage **AWS account team** and/or **data analytics migration partner** before choosing any AWS target) and `no_automated_aws_target`: `true`. Set `rubric_applied` to `["BigQuery specialist gate — no automated AWS service target"]`.
3. **Skip** rubric steps 1–6 and the Preferred AWS target check for this resource.

4. Determine service category (via `steering/design-ref-index.md`):
   - `google_compute_instance` → compute
   - `google_cloudfunctions_function` → compute
   - `google_sql_database_instance` → database
   - `google_storage_bucket` → storage
   - `google_compute_network` → networking
   - etc.

   **Catch-all for unknown types**: If resource type not found in `design-ref-index.md`:
   - Check resource name pattern (e.g., "scheduler" → orchestration, "log" → monitoring, "metric" → monitoring)
   - If pattern match: use that category
   - If no pattern match: **STOP**. Output: "Unknown GCP resource type: [type]. Not in design-ref-fast-path.md or design-ref-index.md. Cannot auto-map. Please file an issue with this resource type."

5. Load rubric from corresponding `steering/design-ref-*.md` file (e.g., `design-ref-compute.md`, `design-ref-database.md`)

6. Evaluate 6 criteria (1-sentence each):
   - **Eliminators**: Feature incompatibility (hard blocker)
   - **Operational Model**: Managed vs self-hosted fit
   - **User Preference**: From `preferences.json` design_constraints
   - **Feature Parity**: GCP feature → AWS feature availability
   - **Cluster Context**: Affinity with other resources in this cluster
   - **Simplicity**: Prefer fewer resources / less config

7. Select best-fit AWS service. Confidence = `inferred`

7b. **Cloud SQL Q6 gate (mandatory — after rubric):** For `google_sql_database_instance` (PostgreSQL or MySQL), read `preferences.json` → `design_constraints.availability` and **enforce**:

| `availability`          | Required `aws_service`                                                                                                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `single-az`             | `RDS PostgreSQL` or `RDS MySQL` (engine match)                                                                                                                                                                                        |
| `multi-az`              | `RDS PostgreSQL` or `RDS MySQL` + `multi_az: true`                                                                                                                                                                                    |
| `multi-az-ha`           | `Aurora PostgreSQL` or `Aurora MySQL`                                                                                                                                                                                                 |
| `multi-region`          | `Aurora PostgreSQL` or `Aurora MySQL` Global Database                                                                                                                                                                                 |
| absent / null / missing | **Do not proceed** — Cloud SQL PostgreSQL/MySQL is present but Q6 was not answered. Return to Clarify to ask Q6 (or apply the documented Q6 default) before assigning RDS/Aurora topology. Do not infer Aurora from the rubric alone. |

**IaC extraction note:** Only `single-az` and `multi-az` can be auto-extracted from Terraform (`ZONAL` / `REGIONAL`). **`multi-az-ha` and `multi-region` are never inferred from IaC** — they require explicit user intent via Q6 (Mission-Critical / Catastrophic). Cloud SQL `REGIONAL` maps to `multi-az` (RDS Multi-AZ), not `multi-az-ha` (Aurora).

If rubric or fast-path would select Aurora when `availability` is `single-az` or `multi-az`, **replace with RDS**. If rubric would select RDS when `availability` is `multi-az-ha` or `multi-region`, **replace with Aurora**. Add `"User Preference: availability=<value>"` to `rubric_applied`. Q12/Q13 must not override this gate.

1. **Set `human_expertise_required`**: If the BigQuery specialist gate applied, already `true`. Otherwise set `false` unless another rubric explicitly requires it. This field is REQUIRED on every resource in the output.

1. **Preferred AWS target check**: **Skip** if `aws_service` is **`Deferred — specialist engagement`**. **Skip Aurora substitution** for Cloud SQL when Q6 availability is `single-az` or `multi-az` (RDS is correct). Otherwise verify the selected `aws_service` aligns with the Preferred AWS Target Services table in `steering/design-ref-fast-path.md`. If a non-preferred service is selected (e.g., App Runner for containerized workloads), substitute the preferred alternative (e.g., Fargate). Add a note to the rationale: "Preferred target: [alternative] selected for stronger ecosystem integration."

## Step 3: Handle Secondary Resources

For each SECONDARY resource:

1. Use `steering/design-ref-index.md` for category
2. Apply fast-path (most secondaries have deterministic mappings)
3. If rubric needed: apply the **BigQuery specialist gate** (Pass 2 step 0) first when `gcp_type` starts with `google_bigquery_`; otherwise apply the same 6-criteria approach as Pass 2

## Step 3.5: Validate AWS Architecture (using awsknowledge)

If `aws_service` is **`Deferred — specialist engagement`**, **do not** validate against concrete AWS analytics SKUs; add a `warnings[]` entry that specialist engagement is required.

**Validation checks** (if awsknowledge available):

For each mapped AWS service, verify:

1. **Regional Availability**: Is the service available in the target region (e.g., `us-east-1`)?
   - Use awsknowledge to check regional support
   - If unavailable: add warning, suggest fallback region

2. **Feature Parity**: Do required features exist in AWS service?
   - Match GCP features from `preferences.json` design_constraints
   - Check AWS feature availability via awsknowledge
   - If feature missing: add warning, suggest alternative service

3. **Service Compatibility**: Are there known issues or constraints?
   - Check best practices and gotchas via awsknowledge
   - Add to warnings if applicable

**If awsknowledge unavailable:**

- Set `validation_status: "skipped"` in output
- Note in summary: "Architecture validation unavailable (non-critical)"
- Continue with design (validation is informational, not blocking)

**If validation succeeds:**

- Set `validation_status: "completed"` in output
- List validated services in summary

## Step 4: Write Design Output

**File 1: `aws-design.json`**

```json
{
  "clusters": [
    {
      "cluster_id": "compute_instance_us-central1_001",
      "gcp_region": "us-central1",
      "aws_region": "us-east-1",
      "resources": [
        {
          "gcp_address": "google_compute_instance.web",
          "gcp_type": "google_compute_instance",
          "gcp_config": {
            "machine_type": "n2-standard-2",
            "zone": "us-central1-a",
            "boot_disk_size_gb": 100
          },
          "aws_service": "Fargate",
          "aws_config": {
            "cpu": "0.5",
            "memory": "1024",
            "region": "us-east-1"
          },
          "confidence": "inferred",
          "human_expertise_required": false,
          "rationale": "Rubric: Compute Engine → Fargate (example — not a Direct Mapping row; Cloud Run/Compute Engine use Pass 2)",
          "rubric_applied": [
            "Eliminators: PASS",
            "Operational Model: Managed Fargate",
            "User Preference: Speed (q2)",
            "Feature Parity: Full (always-on compute)",
            "Cluster Context: Standalone compute tier",
            "Simplicity: Fargate (managed, no EC2)"
          ]
        }
      ]
    }
  ],
  "warnings": [
    "service X not fully supported in us-east-1; fallback to us-west-2"
  ]
}
```

## Output Validation Checklist

- `clusters` array is non-empty
- Every cluster has `cluster_id` matching a cluster from `gcp-resource-clusters.json`
- Every cluster has `gcp_region` and `aws_region`
- Every resource has `gcp_address`, `gcp_type`, `gcp_config`, `aws_service`, `aws_config`
- Every resource has `human_expertise_required` (boolean) — `true` for all `google_bigquery_*` resources (specialist gate); `false` for others unless a rubric explicitly requires it
- Every `google_bigquery_*` resource has `aws_service` exactly **`Deferred — specialist engagement`** (not Athena, Redshift, Glue, etc.)
- Every `google_sql_database_instance` resource has `aws_service` ∈ {`RDS PostgreSQL`, `RDS MySQL`, `Aurora PostgreSQL`, `Aurora MySQL`} with non-empty `rationale` citing Q6 availability value. If `availability` is `single-az` or `multi-az`, `aws_service` MUST be RDS (not Aurora). If `multi-az-ha` or `multi-region`, MUST be Aurora.
- All `confidence` values are either `"deterministic"` or `"inferred"`
- All `rationale` fields are non-empty
- Every resource from every evaluated cluster appears in the output
- No duplicate `gcp_address` values across clusters
- Output is valid JSON

## Completion Handoff Gate (Fail Closed)

Before returning control to `design.md`, require:

- `aws-design.json` exists and passes the Output Validation Checklist above.

If this gate fails: STOP and output: "design-infra did not produce a valid `aws-design.json`; do not complete Phase 3."

## Present Summary

After writing `aws-design.json`, present a concise summary to the user:

1. Total resources mapped and cluster count
2. Per-cluster table: GCP resource → AWS service (one line each). For how each mapping was chosen, use **plain English** from `steering/design-ref-fast-path.md` → **User-facing vocabulary** — **Standard pairing** (`deterministic`), **Tailored to your setup** (`inferred`), or **Estimated from billing only** (`billing_inferred`). Lead with the bold phrase; include the JSON value in parentheses only if the user is technical.
3. Any warnings (regional fallbacks; call out **Tailored to your setup** rows that deserve extra review)
4. If any resource has **`Deferred — specialist engagement`**: state **prominently** that **no AWS analytics target was chosen**. Direct the user to **their AWS account team and/or a data analytics migration partner**. Do **not** recommend Athena, Redshift, Glue, or EMR in the chat summary.

Keep it under 20 lines. The user can ask for details or re-read `aws-design.json` at any time.
