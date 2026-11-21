# SOP: S3 Run Storage (`storageType: S3`)

## Purpose

This SOP defines how you, the agent, configure and troubleshoot HealthOmics workflow runs
that use **S3 run storage** — the `S3` value of `storageType`, where the run's working
files are read from and written to an Amazon S3 location you own instead of a
service-managed `STATIC` or `DYNAMIC` filesystem.

## Trigger Conditions

Follow this SOP WHEN:
- The user asks about `storageType: S3`, S3 run storage, or the `workDirUri` /
  `taskWorkDirS3Uri` fields.
- The user wants run intermediates kept in their own S3 bucket, or wants to manage the
  lifecycle of intermediates separately from final outputs.
- The user wants to use the `EXPRESS` run mode (it requires S3 run storage) — also see the
  [EXPRESS Run Mode SOP](./express-run-mode.md).
- A run that uses S3 storage fails at `StartRun` validation or with an S3 storage failure
  reason (see [Troubleshooting](#troubleshooting)).
- The user asks about `/tmp`, scratch space, or the `disk` directive on a run that uses S3
  storage — follow [Local Storage on S3 Runs](#local-storage-on-s3-runs) here first; it
  differs from the defaults in the [Local Scratch Storage SOP](./ephemeral-storage.md).

DO NOT follow this SOP WHEN:
- The user is asking about per-task `/tmp` scratch space on a `STATIC` or `DYNAMIC` run —
  see the [Local Scratch Storage SOP](./ephemeral-storage.md).
- The user is choosing between `STATIC` and `DYNAMIC` only — see the
  [Running a Workflow SOP](./running-a-workflow.md).

## Key Concepts

- **`storageType`** — `STATIC` (fixed-size filesystem), `DYNAMIC` (default; scales with
  usage), or `S3` (S3-backed filesystem; intermediates and outputs live in your S3
  buckets, so you control their lifecycle independently).
- **`workDirUri`** — An S3 URI where the run writes intermediates (staging files) and task
  logs. Applies only to runs with `storageType: S3`. You SHOULD always set it for S3 runs:
  some accounts require it (the run is rejected with
  `workDirUri is required for S3 storage mode` otherwise), and a separate work directory
  keeps intermediates on their own lifecycle. Fallback only: where it is not required and
  not set at any level, it defaults to the run's `outputUri`.
- **Where `workDirUri` can be set** (most specific wins):
  `StartRun` > run group (`CreateRunGroup`/`UpdateRunGroup`) > workflow version
  (`CreateWorkflowVersion`/`UpdateWorkflowVersion`) > workflow (`CreateWorkflow`/`UpdateWorkflow`)
  > the source run of a rerun > `outputUri`.
  For batch runs, set it in `defaultRunSetting` (overridable per run in `inlineSettings` or
  `s3UriSettings` entries; `storageType` applies to the whole batch).
  A `workDirUri` on a workflow or workflow version shared from another account is not used.
  IF `GetRun` shows no `workDirUri`, the run used its `outputUri` as the work directory.
- **`taskWorkDirS3Uri`** — Returned by `GetRunTask` / `ListRunTasks` for workflow tasks of
  S3 runs: the S3 URI of the task's work directory, where its staging files and execution
  logs are stored.
- **Lifecycle** — HealthOmics does NOT delete objects under `workDirUri` when a run ends or
  is deleted. Recommend an S3 Lifecycle rule on the work-directory prefix (and keeping it
  separate from `outputUri`) so intermediates expire without touching final outputs.
- **`storageCapacity`** is not used for S3 runs (it only applies to `STATIC`). DO NOT pass
  `--storage-capacity` without `--storage-type`: that makes the run `STATIC`, even when the
  workflow defaults to `S3`.

## Procedure

### Step 1: Confirm Prerequisites

1. **Engine version** — Nextflow workflows MUST use Nextflow 23.10 or later. IF the engine
   version is pinned to an older version at `StartRun`, the request is rejected; an older
   version that is not pinned is not caught at `StartRun` and the run fails later.
2. **Networking** — `RESTRICTED` (the default) works with S3 storage. IF `StartRun` rejects
   a `VPC` run with `S3 storage mode does not support VPC networking mode`, use `RESTRICTED`.
3. **Region** — The `workDirUri` bucket MUST be in the same Region as the run.
4. **Tooling** — See the [tooling note](#tooling-support) below before choosing a client.

### Step 2: Grant the Service Role S3 Access

The run's service role (`roleArn`) MUST allow the following, in addition to the permissions
in the [Running a Workflow SOP](./running-a-workflow.md):

| Location | Required actions |
| --- | --- |
| Work directory (`workDirUri`; or `outputUri` when `workDirUri` is not set) | `s3:GetObject`, `s3:PutObject`, `s3:AbortMultipartUpload`, `s3:DeleteObject`, `s3:ListBucket` |
| Output location (`outputUri`), when a separate `workDirUri` is set | `s3:GetObject`, `s3:PutObject`, `s3:AbortMultipartUpload`, `s3:ListBucket` |
| Input buckets | `s3:GetObject`, `s3:ListBucket` — the same read access as for `DYNAMIC`/`STATIC` runs; existing input policies keep working |
| HealthOmics | `omics:AuthorizeRunProcessing` on `arn:aws:omics:<region>:<account-id>:run/*` |

Keep the work-directory permissions in their own statement, separate from the output
location. IF `workDirUri` is not set, the output location is the work directory and needs
the work-directory permissions, including `s3:DeleteObject`.

Notes:
- The service role SHOULD be allowed to pull the run's container images from their Amazon
  ECR repositories — tasks on faster-startup compute may pull images with this role (see
  [Faster-Startup Compute for Tasks](#faster-startup-compute-for-tasks)).
- `s3:DeleteObject` is required on the work directory only, because files there are renamed
  by copying and then deleting the source object.
- IF a bucket uses SSE-KMS with a customer managed key, BOTH the service role AND the
  identity calling `StartRun` need `kms:GenerateDataKey` and `kms:Decrypt` on the
  work-directory and output keys; the role also needs `s3:GetEncryptionConfiguration`.
  `StartRun` otherwise fails with `Insufficient permissions on S3 bucket <bucket>`.
- IF the work directory is an S3 directory bucket (S3 Express One Zone), also allow
  `s3express:CreateSession`. Note that `s3:*` and `AmazonS3FullAccess` do NOT cover
  `s3express:*` actions.
- At `StartRun` and `StartRunBatch`, HealthOmics verifies the role can write, read, list,
  and delete a small probe object under `<workDir>/omics-permission-preflight/` and fails
  the request with a message naming the missing action. Add the named permission and retry.

Example policy statements with a separate work directory (replace placeholders). IF
`workDirUri` is not set, give the output location the `WorkDirReadWrite` statement instead
of `OutputWrite`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WorkDirReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:AbortMultipartUpload",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<workdir-bucket>",
        "arn:aws:s3:::<workdir-bucket>/*"
      ]
    },
    {
      "Sid": "OutputWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:AbortMultipartUpload",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<output-bucket>",
        "arn:aws:s3:::<output-bucket>/*"
      ]
    },
    {
      "Sid": "InputRead",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::<input-bucket>",
        "arn:aws:s3:::<input-bucket>/*"
      ]
    },
    {
      "Sid": "OmicsAccess",
      "Effect": "Allow",
      "Action": "omics:AuthorizeRunProcessing",
      "Resource": "arn:aws:omics:<region>:<account-id>:run/*"
    }
  ]
}
```

### Step 3: Start the Run

```bash
aws omics start-run \
    --workflow-id <workflow-id> \
    --role-arn arn:aws:iam::<account>:role/<role> \
    --output-uri s3://<output-bucket>/<output-prefix>/ \
    --storage-type S3 \
    --work-dir-uri s3://<work-bucket>/<work-prefix>/ \
    --parameters file:///path/to/parameters.json
```

- To make S3 the default for a workflow, set `storageType: S3` (and optionally `workDirUri`)
  on `CreateWorkflow` / `CreateWorkflowVersion`; `StartRun` can still override both.
- For batch runs, set `storageType` and `workDirUri` in `defaultRunSetting` — see the
  [Batch Runs SOP](./batch-runs.md).
- IF the user records defaults in `.healthomics/config.toml`, store
  `run_storage_type = "S3"` and a `work_dir_uri` value and ALWAYS use them when set.

### Step 4: Monitor and Locate Intermediates

1. Run `aws omics get-run --id <run-id>` — confirm `storageType` is `S3` and check
   `workDirUri`.
2. Run `aws omics list-run-tasks --id <run-id>` or
   `aws omics get-run-task --id <run-id> --task-id <task-id>` — `taskWorkDirS3Uri` points at each task's staging
   files and execution logs. Use it when investigating a failed task.

### Run Cache with S3 Storage

- `cacheId` is not supported with S3 storage. To enable call caching, pass
  `--cache-behavior CACHE_ALWAYS` without `--cache-id`; HealthOmics manages cache entries in
  the work directory.
- Any `cacheBehavior` other than `CACHE_ALWAYS` is rejected.
- Use the AWS CLI to start S3 runs with caching: the `StartAHORun` MCP tool rejects
  `cache_behavior` without `cache_id`, which is the combination S3 storage requires.
- Cache entries are stored under `workDirUri` (or `outputUri` when it is not set), so
  changing `workDirUri` between runs causes cache misses.

### Reruns

A rerun resolves `workDirUri` with the same order as any run (see Key Concepts): the rerun
request, then its run group, workflow version, and workflow, and only then the source run.
`storageType` resolves from the rerun request, then the workflow version and workflow, then
the source run.

### Local Storage on S3 Runs

- CPU workflow tasks on S3 runs ALWAYS get a local scratch volume, whatever
  `scratchStorageMode` is set to (`LOCAL`, `SHARED`, or unset). DO NOT add
  `--scratch-storage-mode LOCAL` for S3 runs — it changes nothing.
- HealthOmics sizes this volume automatically for S3 runs. The volume holds both `/tmp` and
  data being saved to S3. DO NOT quote a fixed default size to the user.
- IF a task needs more space for its own scratch data, set the `disk` directive (WDL `disks`,
  Nextflow `disk`, CWL `tmpdirMin`). It applies on S3 runs regardless of
  `scratchStorageMode`.
- IF a task fails with `S3_STORAGE_LOCAL_STORAGE_EXHAUSTED`, check the task's actual scratch
  usage (`scratchStorageUtilizedGiB` in the run manifest log, or `DiagnoseAHORunFailure`),
  then set the `disk` directive comfortably above it, or reduce the number of tasks writing
  concurrently.
- GPU tasks use the instance's local storage; `disk` directives do not apply to them.
- A large `disk` request can take the task off faster-startup compute (see below).

### Faster-Startup Compute for Tasks

Eligible workflow tasks in S3 runs are placed on faster-startup
compute in both `STANDARD` and `EXPRESS` run modes (`EXPRESS` additionally starts the
workflow engine there — see the [EXPRESS Run Mode SOP](./express-run-mode.md)). Tasks that
are not eligible run on standard compute and still run normally. A task is generally NOT
eligible when it:
- requests a GPU, or uses `omicsResourceFallbackOrder`;
- requests more than 16 vCPUs or 32 GiB of memory, or a large `disk`;
- uses a container image from another account's workflow;
- uses a container image without an ARM64 variant (prefer multi-architecture images — see
  the [Runtime Platform SOP](./runtime-platform.md));
- runs in `VPC` networking mode.

Tasks on faster-startup compute pull their container images with the run's service role,
so the service role MUST be allowed to pull each image from its Amazon ECR repository (see
Step 2).

## Tooling Support

`storageType: S3`, `workDirUri`, and `taskWorkDirS3Uri` are part of the HealthOmics API but are
NOT yet supported by every client:
- AWS CLI/SDK versions released before these fields reject `--storage-type S3` and
  `--work-dir-uri`. Check `aws omics start-run help` lists `--work-dir-uri`; IF not, ask the
  user to upgrade the CLI/SDK.
- HealthOmics MCP server versions that validate `storage_type` against `STATIC`/`DYNAMIC`
  only reject `S3`. The `GetAHORun`, `GetAHORunTask`, and `ListAHORunTasks` MCP tools do not
  return `storageType`, `workDirUri`, or `taskWorkDirS3Uri` — read them with the AWS CLI
  (`aws omics get-run`, `get-run-task`, `list-run-tasks`). IF the MCP tool
  rejects `S3` or lacks a work-directory parameter, use the AWS CLI for that call instead.
  DO NOT silently fall back to `DYNAMIC`.

## Troubleshooting

### Rejected at `StartRun`

| Message contains | Fix |
| --- | --- |
| `Work directory URI must be a valid S3 URI` | Use an `s3://bucket/prefix/` URI. |
| `S3 bucket not located in <region> region` | Use a work-directory bucket in the run's Region. |
| `S3 bucket not found` | Create the bucket or fix the URI. |
| `S3 access denied: <uri>` | Allow `s3:ListBucket` on the work-directory bucket. |
| `Insufficient permissions on S3 bucket` | Grant `kms:GenerateDataKey` / `kms:Decrypt` on the bucket's KMS key to the role and/or the caller, as the message states. |
| Names a missing `s3:` or `s3express:` action | Add that action for the work directory (Step 2). |
| `omics:AuthorizeRunProcessing` | Add `omics:AuthorizeRunProcessing` to the service role. |
| `does not support VPC networking mode` | IF `StartRun` returns this for a `VPC` run, retry with `RESTRICTED` networking mode. |
| `requires Nextflow 23.10 or later` | Pin Nextflow 23.10 or later (upgrade the workflow and create a new workflow version if needed). |
| `--cache-id parameter is not supported` | Remove `cacheId`; use `CACHE_ALWAYS` only. |
| `Cache behavior '...' is not supported for S3 storage type` | Use `--cache-behavior CACHE_ALWAYS`. |
| `workDirUri is required for S3 storage mode` | Set `workDirUri` on `StartRun`, the run group, or the workflow. |

### Run failure reasons specific to S3 storage

Call `DiagnoseAHORunFailure` (see the [Diagnose Run Failure SOP](./diagnose-run-failure.md)),
then match the failure reason:

| Failure reason | Meaning and fix |
| --- | --- |
| `S3_STORAGE_READ_ERROR` | An input could not be read. Check `s3:GetObject`, `s3:ListBucket`, and (for SSE-KMS) `kms:Decrypt` on the input location. |
| `S3_STORAGE_WRITE_ERROR` | A file could not be written. Check the bucket is in the run's Region and that the role, bucket policy, and KMS key policy allow writes. |
| `S3_STORAGE_MOUNT_ACCESS_ERROR` | The work-directory bucket could not be reached at task start. Check it exists in the Region and `s3:ListBucket` is allowed. |
| `S3_STORAGE_INVALID_OBJECT_STATE` | An input is in an archive storage class (S3 Glacier Flexible Retrieval / Deep Archive). Restore it first. |
| `S3_STORAGE_THROTTLING_ERROR` | S3 returned `SlowDown`. Retry, or reduce concurrent tasks writing under the same prefix. |
| `S3_STORAGE_LOCAL_STORAGE_EXHAUSTED` | The task's local storage filled up while saving data to S3. On CPU tasks, increase the task's `disk` directive (see the [Local Scratch Storage SOP](./ephemeral-storage.md)) or reduce concurrent writers; on GPU tasks, choose an instance type with more local storage. |
| `S3_STORAGE_WRITEBACK_STALLED` | Transient service-side issue — retry the run without changes. |
| `ECR_RUN_ROLE_PERMISSION_ERROR` (task failure reason `IMAGE_ACCESS_DENIED`) | The service role could not pull a task's container image. Grant the role permission to pull from that ECR repository, then retry. |

IF the run fails with a generic service error, retry it without changes per the
[Troubleshooting SOP](./troubleshooting.md).

## Considerations and Limitations

- `cacheId` is not supported; use `CACHE_ALWAYS`.
- Nextflow workflows require Nextflow 23.10 or later.
- Objects under `workDirUri` are retained until you delete them — S3 storage and request
  charges for intermediates apply.
- `scratchStorageMode` has no effect on S3 runs — CPU workflow tasks always get local
  scratch.
- There is a per-account limit on concurrently active S3-storage runs; runs above the limit
  wait until active ones finish.

## Related Documentation
- [Running a Workflow SOP](./running-a-workflow.md)
- [Batch Runs SOP](./batch-runs.md)
- [EXPRESS Run Mode SOP](./express-run-mode.md)
- [Local Scratch Storage SOP](./ephemeral-storage.md)
- [Diagnose Run Failure SOP](./diagnose-run-failure.md)
- Authoritative reference: [Run storage types in HealthOmics workflows](https://docs.aws.amazon.com/omics/latest/dev/workflows-run-types.html).
