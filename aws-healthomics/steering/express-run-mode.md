# SOP: EXPRESS Run Mode (`runMode: EXPRESS`)

## Purpose

This SOP defines how you, the agent, decide whether to use the `EXPRESS` run mode, start an
`EXPRESS` run, and handle its specific failures.

## Trigger Conditions

Follow this SOP WHEN:
- The user asks about `runMode`, `EXPRESS`, or "faster startup" / "lower startup latency"
  for HealthOmics runs.
- The user runs many short workflows (for example, small-sample or test runs) and wants them
  to start faster.
- An `EXPRESS` run is rejected at `StartRun` or fails with `RUN_TIMED_OUT`.

DO NOT follow this SOP WHEN:
- The user only wants to choose the CPU architecture (x86_64 vs ARM64) — see the
  [Runtime Platform SOP](./runtime-platform.md).
- The question is about which workflow *tasks* use faster-startup compute — that is a
  property of S3 run storage, not of `runMode`. See the
  [S3 Run Storage SOP](./s3-run-storage.md#faster-startup-compute-for-tasks).
- The run is expected to take longer than 8 hours — use the default `STANDARD` mode.

## Key Concepts

- **`runMode`** — An optional `StartRun` parameter:
  - `STANDARD` (default) — standard startup behavior.
  - `EXPRESS` — starts the run's workflow engine on faster-startup compute to reduce run
    startup latency. It does NOT change how workflow tasks are placed: tasks get the same treatment in `STANDARD` and `EXPRESS` runs (see the
    [S3 Run Storage SOP](./s3-run-storage.md#faster-startup-compute-for-tasks)).
- **Requirements** for `EXPRESS`:
  - The run MUST use S3 run storage (`storageType: S3`, set on the run, or inherited from
    the workflow, workflow version, or — for a rerun — the source run). See the
    [S3 Run Storage SOP](./s3-run-storage.md).
  - The run MUST complete within **8 hours**. When the engine runs on faster-startup
    compute, the effective run timeout is the lowest of 8 hours, the run's `maxDuration`,
    the run group's `maxDuration`, and the account's maximum run duration quota. The timer
    starts when the engine starts. A run that exceeds it fails with `RUN_TIMED_OUT`; it is
    NOT automatically moved to `STANDARD`.
- **Networking** — `EXPRESS` works only with `networkingMode: RESTRICTED` (the default).
  With `VPC` networking, the service accepts `EXPRESS` and `GetRun` shows `runMode: EXPRESS`,
  but the engine starts on standard compute, so the run gets neither faster startup nor the
  8-hour limit.
- **Reruns** do NOT inherit `runMode`. Pass `--run-mode EXPRESS` again on the rerun if
  wanted.
- **Batch runs** — `StartRunBatch` does not accept `runMode`; batch runs use `STANDARD`.
- `GetRun` returns `runMode` (`STANDARD` when it was not set). `ListRuns` does not return
  `runMode`; check an individual run with `aws omics get-run --id <run-id>`.

## Procedure

### Step 1: Decide Whether `EXPRESS` Fits

Recommend `EXPRESS` ONLY WHEN all of the following hold:
1. The run is expected to finish well within 8 hours (check prior runs' durations with
   `GetAHORun` / `ListAHORuns` IF available). Leave headroom — a run that hits the 8-hour
   limit fails and must be restarted from the beginning.
2. The user can use S3 run storage.
3. The run does not use `networkingMode: VPC`.

OTHERWISE keep `STANDARD`, and explain which condition was not met. Task shape (CPU,
memory, GPU, image architecture) does NOT decide whether `EXPRESS` helps, because tasks are
treated the same in either mode.

### Step 2: Start the Run

```bash
aws omics start-run \
    --workflow-id <workflow-id> \
    --role-arn arn:aws:iam::<account>:role/<role> \
    --output-uri s3://<output-bucket>/<output-prefix>/ \
    --storage-type S3 \
    --work-dir-uri s3://<work-bucket>/<work-prefix>/ \
    --run-mode EXPRESS \
    --parameters file:///path/to/parameters.json
```

The service role needs the S3 run storage permissions in the
[S3 Run Storage SOP](./s3-run-storage.md#step-2-grant-the-service-role-s3-access).

### Step 3: Verify

Run `aws omics get-run --id <run-id>` and confirm `runMode` is `EXPRESS` and `storageType`
is `S3`. Use the AWS CLI for this check: the `GetAHORun` MCP tool does not return `runMode` or
`storageType`.

## Tooling Support

`runMode` is part of the HealthOmics API but is NOT yet exposed by every client:
- Older AWS CLI/SDK versions reject `--run-mode` as an unknown parameter. Check
  `aws omics start-run help` lists `--run-mode`; IF not, ask the user to upgrade.
- The `GetAHORun` MCP tool does not return `runMode`; use `aws omics get-run` to read it.
- HealthOmics MCP server versions without a `run_mode` parameter cannot start `EXPRESS`
  runs — use the AWS CLI for `StartRun` in that case, and DO NOT silently start the run as
  `STANDARD`.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `EXPRESS run mode is only supported with the S3 storage type` | Set `--storage-type S3` (and a `workDirUri`), or drop `--run-mode EXPRESS`. |
| Run fails with `RUN_TIMED_OUT` about 8 hours after the engine started | The run is too long for `EXPRESS`. Restart it with `STANDARD` (omit `--run-mode`). The minutes in the message can be higher than 480 — it may show the run's configured maximum duration — but the 8-hour `EXPRESS` limit still applied. |
| Run fails with `ECR_RUN_ROLE_PERMISSION_ERROR` | Not specific to `EXPRESS` — a workflow task's image could not be pulled with the service role. See the [S3 Run Storage SOP](./s3-run-storage.md#troubleshooting). |
| Run fails with a transient `SERVICE_ERROR` | Retry the run without changes per the [Troubleshooting SOP](./troubleshooting.md). |

## Related Documentation
- [S3 Run Storage SOP](./s3-run-storage.md)
- [Runtime Platform SOP](./runtime-platform.md)
- [Running a Workflow SOP](./running-a-workflow.md)
- [Diagnose Run Failure SOP](./diagnose-run-failure.md)
