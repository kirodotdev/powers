# SOP: Choosing the Compute Architecture (`runtimePlatformPreference`)

## Purpose

This SOP defines how you, the agent, choose whether a HealthOmics run's workflow tasks run
on `X86_64` or `ARM64` compute, at the run level and per task.

## Trigger Conditions

Follow this SOP WHEN:
- The user asks to run tasks on ARM64 / AWS Graviton, or to force x86_64.
- The user asks about `runtimePlatformPreference`, the task-level `runtimePlatform` setting,
  or the `runtimePlatform` / `supportedArchitectures` fields on a task.
- A run fails with failure reason `UNSUPPORTED_RUNTIME_PLATFORM_TYPE`, or
  `UNSUPPORTED_GPU_INSTANCE_TYPE` mentioning ARM64.

## Key Concepts

- **`runtimePlatformPreference`** — Optional `StartRun` parameter (`X86_64` or `ARM64`)
  applied to every workflow task that does not set its own architecture. For batch runs,
  set it in `defaultRunSetting`; a run's own `inlineSettings` / `s3UriSettings` entry
  overrides it. The value MUST be exactly `X86_64` or `ARM64` (uppercase); any other value
  is rejected with `RuntimePlatformPreference has an invalid value`. In a batch, an invalid
  per-run value fails only that run, when the batch submits it.
- **Task-level override** — Set the architecture for one task in the workflow definition:
  - WDL: `runtime { runtimePlatform: "ARM64" }`
  - Nextflow: `ext.runtimePlatform = 'ARM64'` (in the process definition or `withName:`
    config)
  - CWL: `runtimePlatform: ARM64` in the task's `ResourceRequirement`

  Task-level values are case-insensitive (`arm64` is accepted). An unrecognized task-level
  value is silently ignored and the architecture is inferred.
- **Precedence** — task-level setting > `runtimePlatformPreference` > inferred from the
  container image.
- **Inference** (when nothing is set):
  - an ARM64-only image runs on ARM64;
  - an x86-only image, or one whose architecture cannot be detected, runs on x86_64;
  - a multi-architecture image runs on ARM64 for runs with `storageType: S3` (where ARM64 is
    available in the Region) and on x86_64 otherwise.

  Tasks that request GPUs, an `acceleratorType`, or a GPU fallback profile are inferred as
  x86_64; explicitly requesting `ARM64` for them fails the run.
- **Scope** — The preference applies to workflow tasks only.
- **Reruns** inherit `runtimePlatformPreference` from the source run unless the rerun sets
  one.
- `GetRun` / `ListRuns` return `runtimePlatformPreference`. `GetRunTask` returns
  `runtimePlatform` (the architecture the task was placed on, when reported) and
  `supportedArchitectures` (the architectures in the task's container image manifest).

## Procedure

1. Check that every container image used by the affected tasks has an image for the chosen
   architecture (for example, `docker manifest inspect <image>` or
   `aws ecr batch-get-image`). An explicit architecture is honored even if the image does
   not support it — an `ARM64` request on an x86-only image, or an `X86_64` request on an
   ARM64-only image, places the task on an architecture its container cannot run on.
2. Prefer setting the architecture per task when only some tools have ARM64 images; use
   `runtimePlatformPreference` when the whole workflow is ARM64-ready.
3. DO NOT request `ARM64` for GPU tasks — GPU instance types are not supported with ARM64.
4. Start the run:

   ```bash
   aws omics start-run \
       --workflow-id <workflow-id> \
       --role-arn arn:aws:iam::<account>:role/<role> \
       --output-uri s3://<output-bucket>/<output-prefix>/ \
       --runtime-platform-preference ARM64 \
       --parameters file:///path/to/parameters.json
   ```

5. Verify with `aws omics get-run-task --id <run-id> --task-id <task-id>` (the
   `GetAHORunTask` MCP tool does not return this field): when reported, `runtimePlatform`
   shows where each task ran.

IF you change task-level `runtimePlatform` settings in the workflow definition, create a new
workflow version — see the [Workflow Versioning SOP](./workflow-versioning.md).

## Tooling Support

`runtimePlatformPreference` is part of the HealthOmics API but is not exposed by every
client. Check `aws omics start-run help` lists `--runtime-platform-preference`; IF not, ask
the user to upgrade the CLI/SDK. IF the HealthOmics MCP server's run tools lack the
parameter, use the AWS CLI for that call. The `GetAHORun` and `GetAHORunTask` MCP tools do
not return `runtimePlatformPreference` or `runtimePlatform`; read them with
`aws omics get-run` / `aws omics get-run-task`.

## Troubleshooting

| Run failure reason / error | Fix |
| --- | --- |
| `UNSUPPORTED_GPU_INSTANCE_TYPE` (mentions ARM64) | Remove the ARM64 request for GPU tasks (task-level setting or run preference). |
| `UNSUPPORTED_RUNTIME_PLATFORM_TYPE` | ARM64 compute is not available in this Region (currently Israel (Tel Aviv)). Remove the ARM64 request, or, IF the task's image is ARM64-only, use an x86_64 or multi-architecture image. |
| `RuntimePlatformPreference has an invalid value` | Use exactly `X86_64` or `ARM64`. |

## Related Documentation
- [Running a Workflow SOP](./running-a-workflow.md)
- [Batch Runs SOP](./batch-runs.md)
- [EXPRESS Run Mode SOP](./express-run-mode.md)
