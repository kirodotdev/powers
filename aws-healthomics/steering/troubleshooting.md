# SOP: Troubleshooting HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, diagnose and resolve common HealthOmics workflow failures.

## Workflow Creation Failure

IF a workflow fails to reach `CREATED` status, check these causes in order:

1. The workflow zip package is corrupted or missing.
2. The workflow zip package has multiple workflow definition files at the top level. There MUST be only one `main.wdl`, `main.nf`, etc. at the top level — dependencies MUST be in sub-directories.
3. The workflow zip package is missing a dependency required by the workflow definition, or the dependency location is inconsistent with the import path.
4. The workflow has invalid syntax. Call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to verify.
5. After identifying and fixing the cause, redeploy the workflow by calling `CreateAHOWorkflow` (for a new workflow) or `CreateAHOWorkflowVersion` (for a new version of an existing workflow).

## Run Failures

- IF a run fails with a service error (5xx): a transient error occurred in the HealthOmics service. 
    1. Re-start the run with identical inputs.
    2. IF the previous run used a run cache you MUST also use that run cache for the re-run.
- IF a run fails with a customer error (4xx): 
    1. Call `DiagnoseAHORunFailure` to access important logs and run information. 
    2. Use the diagnosis to fix the workflow, service role permissions or input parameters as appropriate. 
    3. IF you modify the workflow definition you MUST create a new version via `CreateAHOWorkflowVersion`.
    4. IF the previous run used a Run Cache you MUST reference that when starting the new run. Otherwise, you MAY create a Run Cache for this run.
    5. Start a new run of the workflow/ workflow version using identical or modified inputs and Run Cache as appropriate.
