# SOP: Local Scratch (Ephemeral) Storage for Workflow Tasks

## Purpose

This SOP defines how you, the agent, configure and troubleshoot local scratch storage
(EBS-backed ephemeral `/tmp`) for HealthOmics workflow tasks.

## Trigger Conditions

Follow this SOP WHEN:
- User asks about `/tmp`, scratch space, or ephemeral storage for workflow tasks.
- User wants to speed up I/O-bound tasks or reduce shared filesystem contention.
- A task or run fails due to `/tmp` filling up or a disk-exhaustion error.
- User wants to size a `disk`/`disks`/`tmpdirMin` directive for a task.

DO NOT follow this SOP WHEN:
- The user is asking about `storageType` (`STATIC`/`DYNAMIC`/`S3`) or overall run storage
  sizing — that is separate from per-task `/tmp` scratch storage. See the
  [Running a Workflow SOP](./running-a-workflow.md) and, for `S3`, the
  [S3 Run Storage SOP](./s3-run-storage.md).
- The user is diagnosing a generic run failure unrelated to disk space — see the
  [Troubleshooting SOP](./troubleshooting.md).
- The run uses `storageType: S3`, including `S3_STORAGE_LOCAL_STORAGE_EXHAUSTED` failures —
  see [Local Storage on S3 Runs](./s3-run-storage.md#local-storage-on-s3-runs) in the S3 Run
  Storage SOP. S3 runs always use local scratch, so the `scratchStorageMode` guidance here
  does not apply to them.

## Key Concepts

- **Ephemeral storage** — A dedicated, per-task local storage volume mounted at `/tmp`.
  It exists only for the lifetime of the task; it is deleted when the task terminates
  and is never shared between tasks or persisted across runs.
- **`scratchStorageMode`** — A `StartRun`/`StartRunBatch` setting controlling where
  scratch I/O (`/tmp`, `$TMP`, `$TMPDIR`) is written for CPU tasks:
  - `LOCAL` — scratch I/O goes to a dedicated local EBS volume with its own IOPS/throughput.
  - `SHARED` (default) — `/tmp` is backed by the shared run filesystem; scratch I/O
    contends with the working directory.
- **Default allocation** — 16 GiB per task on CPU instances when `LOCAL` is enabled, at
  no extra cost. No `disk` directive is required to get this default.
- **`disk` directive** — A per-task hint (WDL `disks`, Nextflow `disk`, CWL `tmpdirMin`)
  requesting more than the 16 GiB default. Only takes effect when
  `scratchStorageMode` is `LOCAL`, or on runs with `storageType: S3` (which always use
  local scratch — see the [S3 Run Storage SOP](./s3-run-storage.md#local-storage-on-s3-runs)).
  For `STATIC`/`DYNAMIC` runs, rounded up to the next 16 GiB tier, maximum 3,072 GiB per task
  (CPU). S3 runs size the volume differently — see the S3 Run Storage SOP. Does NOT affect instance type selection (`cpu`/`memory`/`acceleratorType`
  still drive that).
- **GPU tasks** — Always use local NVMe ephemeral storage; capacity is fixed per instance
  type at no extra cost. `scratchStorageMode` and `disk` directives have no effect on GPU
  tasks — HealthOmics ignores both.

## Procedure

### Step 1: Decide Whether to Enable Local Scratch Storage

Enable `scratchStorageMode: LOCAL` WHEN:
- The task is I/O-bound and writes meaningful scratch data to `/tmp` (sorting, dedup,
  assembly, alignment buffers).
- The user wants predictable performance without contention from other concurrently
  running tasks on the shared filesystem.
- For `STATIC` run storage, the user wants to reduce provisioned run storage
  requirements. `DYNAMIC` runs need no changes either way.

Leave it as `SHARED` (default) or explicitly set `SHARED` WHEN:
- The user wants to isolate whether a failure is storage-related (a fast way to rule out
  ephemeral-storage sizing as a cause).
- The workflow does not write meaningful scratch data to `/tmp`.

### Step 2: Enable at the Run Level

Set `scratchStorageMode` on `StartRun` (single run) or inside `defaultRunSetting` on
`StartRunBatch` (applies to every run in the batch — see the
[Batch Runs SOP](./batch-runs.md)):

```bash
aws omics start-run \
    --workflow-id <workflow-id> \
    --role-arn arn:aws:iam::<account>:role/<role> \
    --output-uri s3://<bucket>/<output-folder>/ \
    --parameters file:///path/to/parameters.json \
    --scratch-storage-mode LOCAL
```

To opt back out for a specific run (for example, to isolate a failure), either omit
`--scratch-storage-mode` entirely or pass it explicitly:

```bash
--scratch-storage-mode SHARED
```

Notes:
- `scratchStorageMode` applies to CPU instances only; it has no effect on GPU tasks.
- IF omitted from `StartRun`, the effective mode is `SHARED` — omitting the flag and
  explicitly passing `SHARED` are equivalent.
- `scratchStorageMode` is only echoed back in `GetRun` when it was explicitly passed in
  `StartRun` — a missing field means `SHARED` was in effect. To confirm the effective
  mode for a run, call `GetRun` and check the field directly.
- WHEN `scratchStorageMode` is `SHARED`, ALL `disk`/`disks`/`tmpdirMin` directives are
  ignored for CPU tasks — no local volume is provisioned. GPU tasks are unaffected.
  EXCEPTION: on runs with `storageType: S3`, CPU workflow tasks always get local scratch and
  `disk` directives apply whatever `scratchStorageMode` is.

### Step 3: Size Per-Task Storage (Optional)

ONLY relevant when `scratchStorageMode` is `LOCAL` (or the run uses `storageType: S3`)
and the default allocation is insufficient — 16 GiB for `STATIC`/`DYNAMIC` runs; S3 runs size
the volume differently (see the [S3 Run Storage SOP](./s3-run-storage.md#local-storage-on-s3-runs)).
This applies, for example, to RNA-seq fusion detection, de novo assembly, or BAM sort/dedup
steps that repeatedly rewrite large intermediate files.

Use the engine-appropriate directive in the task/process definition — see the
[Workflow Development SOP](./workflow-development.md) for where task resource
directives live:

| Engine | Directive | Example |
| --- | --- | --- |
| WDL 1.1 | `disks` | `disks: "700 GiB"` |
| Nextflow | `disk` | `disk '700 GB'` |
| CWL | `tmpdirMin` | `tmpdirMin: 716800` (value in MiB) |

Rules (`STATIC`/`DYNAMIC` runs; for S3 runs, see
[Local Storage on S3 Runs](./s3-run-storage.md#local-storage-on-s3-runs)):
- Values are rounded UP to the next 16 GiB tier (16, 32, 48, ... up to 3,072 GiB per task).
- A task cannot receive less than the 16 GiB default.
- Requests above 3,072 GiB are capped at 3,072 GiB with a run-log warning — the task is
  NOT failed.
- Expression-based directives (e.g. a WDL `disks: ceil(size(input_bam, "GiB") * 2.5)` or
  a Nextflow closure) are evaluated at task start, not at `CreateWorkflow`/lint time. IF
  the evaluated size exceeds 3,072 GiB, the task fails at runtime and any compute cost
  incurred up to that point is still billed.
- GPU tasks: `disk`/`tmpdirMin` directives are ignored. NVMe capacity is fixed by the
  selected instance type.

### Step 4: Ensure Task Commands Actually Write to `/tmp`

Enabling `LOCAL` mode only helps if the task process writes its scratch data to `/tmp`
(or `$TMP`/`$TMPDIR`). Workflows that write scratch to the working directory (e.g.
`input/`, `./`, `out/`) do NOT benefit automatically — redirect the tool's temp-file flag
explicitly. Common examples:

```bash
# samtools: -T sets the temp-file prefix
samtools sort -T /tmp/sort_buffer input.bam -o sorted.bam

# GATK / Picard: --TMP_DIR flag (older Picard: TMP_DIR=/tmp)
gatk MarkDuplicates -I sorted.bam -O dedup.bam --TMP_DIR /tmp

# STAR: --outTmpDir (path must not pre-exist; STAR creates it)
STAR --runThreadN 16 --readFilesIn reads.fastq --outTmpDir /tmp/star_tmp --outFileNamePrefix out_

# bcftools sort: -T / --temp-dir
bcftools sort -T /tmp input.vcf -o sorted.vcf

# GNU sort: -T / --temporary-directory
sort -T /tmp big_table.tsv -o sorted_table.tsv
```

IF the task command sets `TMPDIR`/`TMP` to a different path, that mapping overrides the
ephemeral volume — verify it has NOT been redirected elsewhere.

For Nextflow workflows specifically, the `scratch` directive also controls where a
process stages its working files; consider it alongside `disk` when tuning I/O.

## Monitoring

HealthOmics writes per-task ephemeral storage metrics to the CloudWatch manifest log:
- `scratchStorageReservedGiB` — the provisioned volume size for the task.
- `scratchStorageUtilizedGiB` — actual usage for the task.

Use these to right-size the `disk` directive (avoid over- or under-provisioning) without
querying CloudWatch metrics directly. See
[Monitoring HealthOmics with CloudWatch Logs](https://docs.aws.amazon.com/omics/latest/dev/monitoring-cloudwatch-logs.html)
for manifest log details.

## Billing

Only storage provisioned ABOVE the default 16 GiB is billed, rounded up to the nearest
supported tier. GPU instance ephemeral (NVMe) storage is included in instance pricing —
there is no additional charge.

## Troubleshooting

### Task fails from `/tmp` exhaustion

A task fails when its ephemeral volume reaches capacity (~99% used). This is a customer
error (4xx) surfaced via `DiagnoseAHORunFailure` — treat it like any other run failure
per the [Troubleshooting SOP](./troubleshooting.md#run-failures):

1. Call `DiagnoseAHORunFailure` to confirm scratch-storage exhaustion is the cause and to
   review the CloudWatch manifest log (`scratchStorageUtilizedGiB`) for the actual usage.
2. Increase the `disk`/`disks`/`tmpdirMin` directive for the affected task to a tier
   comfortably above observed usage.

   ```
   # Before: 4-vCPU task using the 16 GiB default
   runtime { cpu: 4 }

   # After: explicitly request 400 GiB
   runtime { cpu: 4, disks: "400 GiB" }
   ```

3. IF you modify the workflow definition, you MUST create a new version via
   `CreateAHOWorkflowVersion` — see the [Workflow Versioning SOP](./workflow-versioning.md).
4. Retry the run. Alternatively, the user MAY opt out entirely by omitting
   `scratchStorageMode` or explicitly setting it to `SHARED` for that run, which removes
   the per-task capacity limit at the cost of shared-filesystem contention. This does NOT
   apply to runs with `storageType: S3`: they always use local scratch, so increase the
   `disk` directive instead (see the [S3 Run Storage SOP](./s3-run-storage.md#local-storage-on-s3-runs)).

### Ephemeral storage does not appear to be used

1. Call `GetRun` and check `scratchStorageMode`. IF the field is absent or `SHARED`,
   local ephemeral storage was never enabled for that run — re-run with
   `--scratch-storage-mode LOCAL`.
2. IF `LOCAL` was set but usage still looks like it is hitting the shared filesystem,
   verify the task command is not redirecting `$TMPDIR`/`$TMP` elsewhere (see Step 4
   above), and confirm the tool actually uses a temp-file flag that points at `/tmp`.

### Task output ends up missing

Data written to `/tmp` on ephemeral storage cannot be a task output or workflow output —
it is deleted when the task terminates and is never exported. IF a task or workflow
output is missing, verify the workflow definition does NOT declare an output path under
`/tmp`; outputs must be written to the working directory / declared output paths that
HealthOmics copies to the run's S3 output location.

## Considerations and Limitations

- Ephemeral storage is per-task only — tasks cannot read each other's `/tmp`. Data that
  must be shared between tasks MUST go through the shared run filesystem or S3.
- Storage size is fixed at task start and cannot be resized while the task is running.
- All ephemeral storage is encrypted at rest with a service-managed KMS key; no
  additional IAM permissions are required in the task execution role.
- `scratchStorageMode` and `disk` directives apply to CPU tasks only. GPU tasks always
  use local NVMe storage with fixed, instance-type-determined capacity.

## Related Documentation
- For starting runs and `engineSettings`, see the [Running a Workflow SOP](./running-a-workflow.md).
- For batch runs (`defaultRunSetting.scratchStorageMode`), see the [Batch Runs SOP](./batch-runs.md).
- For task resource directives (`cpu`, `memory`, `container`), see the [Workflow Development SOP](./workflow-development.md).
- For general run failure handling, see the [Troubleshooting SOP](./troubleshooting.md).
- Authoritative reference: [Ephemeral storage for HealthOmics workflow tasks](https://docs.aws.amazon.com/omics/latest/dev/workflows-ephemeral-storage.html).
