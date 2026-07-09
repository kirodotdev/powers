# SOP: Batch Runs in HealthOmics

## Purpose

This SOP defines how you, the agent, submit, monitor, and manage batch runs in AWS HealthOmics. Batch runs let users submit multiple runs in a single API request, sharing a common base configuration with per-run parameter overrides. Use batch runs to reduce submission overhead and simplify lifecycle management for large-scale workflow processing.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to run the same workflow across multiple samples or inputs.
- User wants to submit many runs at once (up to 100,000).
- User mentions "batch", "batch run", or "multiple samples" in the context of running workflows.
- User wants to cancel or delete multiple runs that were submitted together.
- User wants to monitor progress across a group of related runs.

DO NOT follow this SOP WHEN:
- User wants to run a single workflow with a single set of inputs — use the [Running a Workflow SOP](./running-a-workflow.md).
- User wants to re-run a single failed run — use the [Running a Workflow SOP](./running-a-workflow.md).

## Key Concepts

- **Batch** — A collection of workflow runs sharing common configuration, managed as a single resource with its own ARN and lifecycle status.
- **defaultRunSetting** — Shared configuration for all runs in the batch (workflow ID, IAM role, output URI, common parameters).
- **Run-specific settings** — Per-run configurations (via `inlineSettings` or `s3UriSettings`) that override or merge with the default. Each MUST include a unique `runSettingId`.
- **runSettingId** — A required, customer-provided unique identifier for each run configuration. Use `ListRunsInBatch` to map each `runSettingId` to the HealthOmics-generated `runId`.
- **Parameter merging** — Per-run parameters are merged with `defaultRunSetting` parameters. Run-specific values take precedence when keys overlap. The same merging applies to `runTags`.

### Batch Status Lifecycle

`PENDING` → `SUBMITTING` → `INPROGRESS` → `PROCESSED`

Other terminal states: `CANCELLED`, `FAILED`, `RUNS_DELETED`.

## Prerequisites

1. An active HealthOmics private workflow. Batch runs are NOT supported with Ready2Run workflows.
2. An IAM service role with permissions to run HealthOmics workflows and access S3 buckets.
3. S3 locations for input data and output results.
4. Run-specific parameters for each sample or configuration.
5. ALWAYS read and use preferences/defaults from `.healthomics/config.toml` if present.

## IAM Permissions

The user's IAM identity MUST have permissions for both batch operations and the underlying run operations. `StartRunBatch` requires dual authorization: `omics:StartRunBatch` on the batch resource AND `omics:StartRun` on the run, workflow, and run group resources.

Required batch actions:
- `omics:StartRunBatch`
- `omics:GetBatch`
- `omics:ListBatch`
- `omics:ListRunsInBatch`
- `omics:CancelRunBatch`
- `omics:DeleteRunBatch`
- `omics:DeleteBatch`

The IAM service role passed in `roleArn` requires the same permissions as for individual `StartRun` calls.

## Procedure

### Step 1: Prepare the Batch Configuration

1. Verify the workflow is deployed and `ACTIVE` via `GetAHOWorkflow`.
2. Identify the shared configuration for `defaultRunSetting`:
   - `workflowId` — The deployed workflow ID.
   - `roleArn` — IAM service role ARN (check `.healthomics/config.toml`).
   - `outputUri` — S3 output location (check `.healthomics/config.toml`).
   - `storageType` — Use `DYNAMIC` (recommended).
   - `parameters` — Common parameters shared across all runs (e.g., reference genome).
3. Prepare per-run configurations, each with a unique `runSettingId` and any parameter overrides.

### Step 2: Choose Submission Method

- **Inline settings (≤100 runs):** Provide run configurations directly via `inlineSettings` array.
- **S3 settings (>100 runs, up to 100,000):** Store run configurations as a JSON array in S3 and provide the URI via `s3UriSettings`.

IF using `s3UriSettings`:
- The S3 file MUST be a JSON array of run setting objects.
- Maximum file size is 6 GB.
- The IAM service role in `roleArn` MUST have read access to the S3 file.
- DO NOT modify the S3 file after submission — HealthOmics validates the file's ETag and fails the batch if the file changes.

### Step 3: Submit the Batch

Call `StartAHORunBatch` with:
- `batchName` — A human-readable name for the batch.
- `defaultRunSetting` — The shared configuration.
- `batchRunSettings` — Either `inlineSettings` (array) or `s3UriSettings` (S3 URI).
- `requestId` — An idempotency token to prevent duplicate submissions (optional but recommended).
- `tags` — Tags for the batch resource itself (optional).

The API validates common fields synchronously and returns a batch ID with status `PENDING`. Runs are submitted gradually and asynchronously according to throughput quotas.

### Step 4: Monitor Batch Progress

1. Call `GetAHOBatch` to check overall status and submission progress.
   - `status` — Overall batch state.
   - `submissionSummary` — Counts of successful and failed submissions.
   - `runSummary` — Counts of runs in each execution state.
2. Call `ListAHORunsInBatch` to get details for individual runs.
   - Each entry maps `runSettingId` to the HealthOmics-generated `runId`.
   - Filter by `submissionStatus` to find failed submissions.

Run execution summaries are eventually consistent and may lag behind actual run states. Final counts are accurate once the batch reaches `PROCESSED`.

### Step 5: Handle Failures

There are two distinct failure types:

#### Batch-level failures
The batch itself failed — no runs were created (or only some were). Batch status is `FAILED`.
1. Call `GetAHOBatch` and check the `failureReason` field.
2. Fix the issue (e.g., too many runs, invalid workflow ID, inaccessible S3 URI).
3. Submit a new batch with corrected configuration.

#### Run-level failures
The batch succeeded but individual runs failed to submit. The batch continues processing other runs.
1. Call `GetAHOBatch` and check `submissionSummary.failedStartSubmissionCount`.
2. Call `ListAHORunsInBatch` with `submissionStatus=FAILED` to identify which runs failed.
3. Check `submissionFailureReason` and `submissionFailureMessage` for each failed run.
4. Create a new batch containing only the corrected run configurations with the same `defaultRunSetting`.

HealthOmics automatically retries transient errors (`ThrottlingException`, `RequestTimeoutException`, `InternalServerException`). A run is marked `FAILED` only after all retries are exhausted. Non-retryable errors (`ValidationException`, `AccessDeniedException`, `ResourceNotFoundException`) fail immediately.

## Canceling a Batch

Call `CancelAHORunBatch` to cancel a batch in progress.
- Cancel is only allowed on batches in `PENDING`, `SUBMITTING`, or `INPROGRESS` state.
- Only one cancel or delete operation per batch is allowed at a time.
- Cancel operations are non-atomic and may be partially successful. Use `GetAHOBatch` to review `successfulCancelSubmissionCount` and `failedCancelSubmissionCount`.

## Deleting Batch Runs

Call `DeleteAHORunBatch` to delete the individual runs within a batch.
- Delete is only allowed on batches in `PROCESSED` or `CANCELLED` state.
- Only one cancel or delete operation per batch is allowed at a time.
- Delete operations are non-atomic and may be partially successful.

## Deleting Batch Metadata

Call `DeleteAHOBatch` to remove the batch resource and its metadata.
- Requires the batch to be in a terminal state (`PROCESSED`, `FAILED`, `CANCELLED`, or `RUNS_DELETED`).
- Does NOT delete individual runs. Call `DeleteAHORunBatch` first if you want to remove runs.
- After deletion, the batch metadata is no longer accessible.

## Example

### Inline settings (small batch)

```json
{
  "batchName": "cohort-analysis",
  "defaultRunSetting": {
    "workflowId": "1234567",
    "roleArn": "arn:aws:iam::123456789012:role/OmicsRole",
    "outputUri": "s3://my-bucket/output/",
    "storageType": "DYNAMIC",
    "parameters": {
      "referenceUri": "s3://my-bucket/reference/genome.fasta"
    }
  },
  "batchRunSettings": {
    "inlineSettings": [
      {
        "runSettingId": "sample-A",
        "name": "Sample-A-Analysis",
        "parameters": {
          "inputUri": "s3://my-bucket/input/sample-A.fastq"
        }
      },
      {
        "runSettingId": "sample-B",
        "name": "Sample-B-Analysis",
        "parameters": {
          "inputUri": "s3://my-bucket/input/sample-B.fastq"
        }
      }
    ]
  }
}
```

### S3 settings (large batch)

```json
{
  "batchName": "large-cohort",
  "defaultRunSetting": {
    "workflowId": "1234567",
    "roleArn": "arn:aws:iam::123456789012:role/OmicsRole",
    "outputUri": "s3://my-bucket/output/",
    "storageType": "DYNAMIC",
    "parameters": {
      "referenceUri": "s3://my-bucket/reference/genome.fasta"
    }
  },
  "batchRunSettings": {
    "s3UriSettings": "s3://my-bucket/configs/run-configs.json"
  }
}
```

The S3 file at `s3://my-bucket/configs/run-configs.json` is a JSON array with the same structure as `inlineSettings`:

```json
[
  {
    "runSettingId": "sample-001",
    "parameters": { "inputUri": "s3://my-bucket/input/sample-001.fastq" }
  },
  {
    "runSettingId": "sample-002",
    "parameters": { "inputUri": "s3://my-bucket/input/sample-002.fastq" }
  }
]
```

## Limitations and Considerations

- **Shared throughput quotas** — Batch operations share the same per-account quotas as individual API counterparts. Avoid calling individual run APIs while a large batch is in progress.
- **Non-atomic operations** — `StartRunBatch`, `CancelRunBatch`, and `DeleteRunBatch` can all be partially successful. Always check submission summaries.
- **Eventual consistency** — Run execution status counts in `GetBatch` may lag behind actual run states.
- **Single filter per list call** — `ListRunsInBatch` and `ListBatch` support only one filter per API call.
- **Re-run not supported** — The `runId` (re-run) field is not supported in `StartRunBatch`. Each batch always creates new runs.
- **Ready2Run workflows** — Not supported with batch runs.
- **Inline limit** — `inlineSettings` supports up to 100 entries. For larger batches, use `s3UriSettings`.
- **S3 file immutability** — Do not modify the S3 configuration file after submitting the batch.
