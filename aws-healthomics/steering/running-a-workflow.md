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

### Execution

1. Call `StartAHORun` to start the run.
2. Call `GetAHORun` to check status.
3. WHEN the workflow completes, outputs will be at the specified output location.

### Session Policy

`StartRun` accepts an optional `sessionPolicy` — an inline IAM policy (JSON string) that further scopes down the permissions of the run's `roleArn` for that run. The run's effective permissions are the intersection of the role's policies and this session policy, so it can only restrict, never grant, access. Pass it only when the user wants to limit what the run's tasks can reach (for example, restrict S3 access to specific buckets). For batch runs it is set in `defaultRunSetting`. See the [Session Policies SOP](./session-policy.md).

> **Tooling support**: `sessionPolicy` is part of the HealthOmics REST API but is not exposed by every AWS CLI/SDK/MCP client version. Confirm the client you use accepts it before relying on it (e.g., `aws omics start-run help` should list `--session-policy`); older clients reject it as an unknown parameter.

### Engine Settings

`StartRun` accepts an `engineSettings` map that customizes how HealthOmics invokes the workflow engine. The map is engine-agnostic in concept; today only Nextflow keys are implemented, so pass it only for Nextflow workflows. Pass it only when the user requests the corresponding behavior.

> **Tooling support**: `engineSettings` is part of the HealthOmics REST API, but the HealthOmics MCP server's `StartAHORun` tool does NOT currently accept it. To start a run that uses `engineSettings`, use the AWS CLI or an SDK. First confirm the installed CLI accepts it (`aws omics start-run help` lists `--engine-settings`); older clients reject it with `Unknown parameter: "engineSettings"` and must be upgraded. Do not assume the `--engine-settings` flag exists on the user's installed CLI.

Currently supported keys (Nextflow):

| Key | Purpose | Notes |
| --- | --- | --- |
| `profile` | Selects one or more profiles defined in the workflow's `nextflow.config`. | Comma-separated for multiple (e.g. `"test,docker"`). Order matters: v26.04+ applies in command-line order; earlier versions apply in definition order. A nonexistent profile = validation error. Profiles MUST be inside the workflow zip. |
| `syntaxVersion` | Selects the Nextflow parser syntax. | v26.04+ defaults to strict (v2) syntax. Set to `"v1"` to run a workflow authored against the legacy parser. Not supported on v25.10 and earlier. On v26.10, `"v1"` does NOT restore the removed `echo` directive — replace it with `debug`. |
| `outputFormat` | Format for the workflow output summary printed on completion. | v26.04+ only. |
| `agentMode` | Enables Nextflow agent logging mode. | v26.04+ only. |

Behavior to know (Nextflow profiles):
- IF the workflow defines a `standard` profile and the user does not specify one, HealthOmics applies `standard` automatically.
- Explicit run parameters (in `parameters.json`) override profile-defined parameter values.
- Recommend pinning `manifest.nextflowVersion` in the workflow when profiles are in use, so profile application is consistent across runs.

### Pinning the Nextflow Version

- To run a workflow on Nextflow v26.10, you MUST pin it exactly in the workflow's `nextflow.config`: `manifest.nextflowVersion = '=26.10.0'`.
- You SHOULD recommend an exact pin whenever the user needs a specific engine version or reproducible runs.
- IF a run used an unexpected engine version, check the workflow's `manifest.nextflowVersion` first. The engine log (from `DiagnoseAHORunFailure` or the run's CloudWatch logs) states the Nextflow version the run used.

### Handling Failures

IF the workflow run fails:
1. Call `DiagnoseAHORunFailure` to get failure details.
2. Fix the workflow definition based on the diagnosis.
3. Create a new version via `CreateAHOWorkflowVersion` — see the [Workflow Versioning SOP](./workflow-versioning.md).
4. Retry the run.

IF the run fails with a service error (5xx), a transient error occurred — re-start the run without changes. See the [Troubleshooting SOP](./troubleshooting.md) for more detail.
