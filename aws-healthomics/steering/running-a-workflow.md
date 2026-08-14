# SOP: Running a HealthOmics Workflow

## Purpose

This SOP defines how you, the agent, run a deployed HealthOmics workflow and handle run failures.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to execute/run a workflow that has already been deployed to HealthOmics.
- User wants to re-run a workflow after fixing a failure.
- User wants to test a workflow on HealthOmics.

## Procedure

### Pre-conditions

1. Verify the workflow has been deployed successfully via `GetAHOWorkflow`.
2. Verify a `parameters.json` or `inputs.json` exists with valid, accessible inputs.
   - IF `parameters.json` contains placeholder inputs you MUST offer to find suitable inputs using `SearchGenomicsFiles` tool.
   - IF you cannot find suitable inputs STOP and ASK the user to provide values. DO NOT proceed until values are provided. 
3. ALL file inputs MUST come from S3 locations in the same region as the workflow run.
4. Verify all S3 objects exist.
5. ALWAYS read and use preferences/defaults from `.healthomics/config.toml` if present.
6. A run requires an S3 output location that is writable — ASK the user where they want outputs written.
7. You MUST identify an IAM service role's ARN to run the workflow, this may already be in `.healthomics/config.toml`. A run requires a Service Role with:
   - A trust policy allowing `omics` to assume the role.
   - Permissions to read inputs and write to the output location.
   - Permissions to write HealthOmics logs to CloudWatch.
   - Access to ECR containers used in the run.
8. PREFER `ValidateAHORunReadiness` over checking these pre-conditions individually. It reports the workflow status, the role's trust policy, whether the output bucket exists in the run's region, whether the role can write there, and whether the input objects exist — in one call, and before any compute is billed. See [Pre-Run Validation](#pre-run-validation).

### Parameter Types

Parameter values passed to `StartAHORun` MUST match the types declared in the workflow definition:

| WDL type | JSON form | Example |
| --- | --- | --- |
| `String` | string | `"NA12878"` |
| `Int`, `Float` | number | `42`, `3.14` |
| `Boolean` | boolean | `true` |
| `File`, `Directory` | string holding an S3 URI | `"s3://bucket/sample.bam"` |
| `Array[T]` | array | `["s3://bucket/a.fq", "s3://bucket/b.fq"]` |
| `Map[K, V]` | object | `{"chr1": "s3://bucket/chr1.bed"}` |
| `Pair[L, R]` | object with `left` and `right` | `{"left": "a", "right": 1}` |
| struct | object | `{"owner": "user", "id": 123}` |

A struct MUST be passed as a JSON object. Passing it as a JSON-encoded string is rejected at run time:

```
# Wrong — the value is a string that happens to contain JSON
{"sample_meta": "{\"owner\": \"user\"}"}

# Right
{"sample_meta": {"owner": "user"}}
```

The resulting failure names the struct rather than the mistake: `InputError: check JSON input; couldn't construct SampleMeta from "{\"owner\": \"user\"}" (in sample_meta)`. It arrives minutes into the run, after PENDING, because inputs are validated by the engine rather than by `StartRun`.

`parameterTemplate` from `GetAHOWorkflow` will NOT tell you which parameters are structs — it carries only `description` and `optional`. To determine types, read the `input {}` block of the main workflow definition.

### Execution

1. Call `StartAHORun` to start the run.
2. Call `WaitForAHORun` to wait for the run to finish. It polls until the run reaches a terminal status (`COMPLETED`, `FAILED` or `CANCELLED`) and returns the full run details.
   - DO NOT poll by calling `GetAHORun` in a loop.
   - Reaching the wait timeout does NOT cancel the run. The result carries `timedOut` with the last observed status; call `WaitForAHORun` again to keep waiting.
   - A `FAILED` status is a successful wait, not a tool error. Branch on `status`.
   - `GetAHORun` remains the right call for a one-off status check.
3. WHEN the workflow completes, outputs will be at the specified output location.

### Pre-Run Validation

`ValidateAHORunReadiness` checks a run's prerequisites without starting it. Every check is attempted regardless of earlier results, so one call reports every problem rather than surfacing them one failed run at a time.

Call it before `StartAHORun` whenever the role, output location, or inputs have not already been proven by a successful run — a first run, a new output bucket, a new region, or a role you have not used before.

```
ValidateAHORunReadiness(
    workflow_id="1234567",
    role_arn="<from .healthomics/config.toml>",
    output_uri="<from .healthomics/config.toml>",
    parameters={...},                  # S3 URIs in the values are checked for existence
    container_images=["<ecr uri>"],    # optional; see below
)
```

Reading the result:

- `ready` is true only when nothing failed.
- A `fail` means the run will not succeed as configured. Fix it before starting the run.
- A `warn` means the check could not be completed, not that something is wrong. `role_s3_write` warns when the caller lacks `iam:SimulatePrincipalPolicy`; an input object warns when the caller cannot read it but the run role may still be able to. Warnings do NOT affect `ready`.

`container_images` is not populated automatically. Supply the image URIs from the `runtime`/`container` directives of the workflow definition when you want them verified. IF `validate_containers = true` is set in `.healthomics/config.toml`, you MUST collect those URIs and pass them.

Passing checks do not guarantee a successful run. Parameter types, workflow logic and container contents are outside its scope — see [Parameter Types](#parameter-types) and Phase 1 of the [WDL migration SOP](./migration-guide-for-wdl.md) for verifying container contents.

### Engine Settings

`StartRun` accepts an `engineSettings` map that customizes how HealthOmics invokes the workflow engine. The map is engine-agnostic in concept; today only Nextflow keys are implemented, so pass it only for Nextflow workflows. Pass it only when the user requests the corresponding behavior.

> **Tooling support**: `engineSettings` is part of the HealthOmics REST API, but it is NOT yet exposed by every released AWS CLI/SDK version — older clients reject it with `Unknown parameter: "engineSettings"`. Prefer the HealthOmics MCP server (which sends the field directly) to start runs that use `engineSettings`. If you must use the AWS CLI, first confirm the installed version accepts it (`aws omics start-run help` lists `--engine-settings`); if it does not, upgrade the CLI/SDK. Do not assume the `--engine-settings` flag exists on the user's installed CLI.

Currently supported keys (Nextflow):

| Key | Purpose | Notes |
| --- | --- | --- |
| `profile` | Selects one or more profiles defined in the workflow's `nextflow.config`. | Comma-separated for multiple (e.g. `"test,docker"`). Order matters: v26.04+ applies in command-line order; earlier versions apply in definition order. A nonexistent profile = validation error. Profiles MUST be inside the workflow zip. |
| `syntaxVersion` | Selects the Nextflow parser syntax. | v26.04 defaults to strict (v2) syntax. Set to `"v1"` to run a workflow authored against the legacy parser. Not supported on v25.10 and earlier. |
| `outputFormat` | Format for the workflow output summary printed on completion. | v26.04+ only. |
| `agentMode` | Enables Nextflow agent logging mode. | v26.04+ only. |

Behavior to know (Nextflow profiles):
- IF the workflow defines a `standard` profile and the user does not specify one, HealthOmics applies `standard` automatically.
- Explicit run parameters (in `parameters.json`) override profile-defined parameter values.
- Recommend pinning `manifest.nextflowVersion` in the workflow when profiles are in use, so profile application is consistent across runs.

### Handling Failures

IF the workflow run fails:
1. Call `DiagnoseAHORunFailure` to get failure details.
2. Fix the cause. Not every failure is a workflow defect — a run also fails on an unusable role, an output bucket in the wrong region, a missing input, or a mistyped parameter. See [Common Run Failure Patterns](./troubleshooting.md#common-run-failure-patterns) for what to check first for a given error message.
3. IF you modified the workflow definition, create a new version via `CreateAHOWorkflowVersion` — see the [Workflow Versioning SOP](./workflow-versioning.md). IF you only changed inputs, the role, or the output location, the existing workflow is reusable and a new version is NOT needed.
4. Retry the run.

IF the run fails with a service error (5xx), a transient error occurred — re-start the run without changes. See the [Troubleshooting SOP](./troubleshooting.md) for more detail.
