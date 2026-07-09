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

### Pass 1: Fast-Path Lookup

For each PRIMARY resource in the cluster:

1. Extract GCP type (e.g., `google_sql_database_instance`)
2. Look up in `steering/design-ref-fast-path.md` → Direct Mappings table
3. If found (deterministic 1:1 match): assign AWS service with confidence = `deterministic`
4. If not found: proceed to Pass 2

### Pass 2: Rubric-Based Selection

For resources not covered by fast-path:

1. Determine service category (via `steering/design-ref-index.md`):
   - `google_compute_instance` → compute
   - `google_cloudfunctions_function` → compute
   - `google_sql_database_instance` → database
   - `google_storage_bucket` → storage
   - `google_compute_network` → networking
   - etc.

   **Catch-all for unknown types**: If resource type not found in `design-ref-index.md`:
   - Check resource name pattern (e.g., "scheduler" → orchestration, "log" → monitoring, "metric" → monitoring)
   - If pattern match: use that category
   - If no pattern match: **STOP**. Output: "Unknown GCP resource type: [type]. Not in fast-path.md or index.md. Cannot auto-map. Please file an issue with this resource type."

2. Load rubric from corresponding `steering/design-ref-*.md` file (e.g., `design-ref-compute.md`, `design-ref-database.md`)

3. Evaluate 6 criteria (1-sentence each):
   - **Eliminators**: Feature incompatibility (hard blocker)
   - **Operational Model**: Managed vs self-hosted fit
   - **User Preference**: From `preferences.json` design_constraints
   - **Feature Parity**: GCP feature → AWS feature availability
   - **Cluster Context**: Affinity with other resources in this cluster
   - **Simplicity**: Prefer fewer resources / less config

4. Select best-fit AWS service. Confidence = `inferred`

## Step 3: Handle Secondary Resources

For each SECONDARY resource:

1. Use `steering/design-ref-index.md` for category
2. Apply fast-path (most secondaries have deterministic mappings)
3. If rubric needed: apply same 6-criteria approach

## Step 3.5: Validate AWS Architecture (using awsknowledge)

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
          "confidence": "deterministic",
          "rationale": "1:1 compute mapping with Cold Start considerations",
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
- All `confidence` values are either `"deterministic"` or `"inferred"`
- All `rationale` fields are non-empty
- Every resource from every evaluated cluster appears in the output
- No duplicate `gcp_address` values across clusters
- Output is valid JSON

## Present Summary

After writing `aws-design.json`, present a concise summary to the user:

1. Total resources mapped and cluster count
2. Per-cluster table: GCP resource → AWS service (one line each, include confidence)
3. Any warnings (regional fallbacks, inferred mappings with low confidence)

Keep it under 20 lines. The user can ask for details or re-read `aws-design.json` at any time.
