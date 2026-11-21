# SOP: Diagnose a Failed HealthOmics Run

## Purpose

This SOP defines how you, the agent, diagnose a specific failed AWS HealthOmics workflow run and guide the user to remediation. Use it when the user names a failed run (by run ID or from a run list) and asks why it failed or how to fix it.

For workflow *creation* failures or VPC connectivity failures, use the [Troubleshooting SOP](./troubleshooting.md) instead. For metric semantics, availability rules, and deeper metric queries, see the [Vended Metrics Analysis SOP](./metrics-analysis.md).

## Procedure

1. **Diagnose.** Call `DiagnoseAHORunFailure` with the run ID. This aggregates the run details and failure reason, engine logs from CloudWatch, run manifest logs, task logs from failed tasks, and common error patterns.
2. **Classify the failure.**
    - IF the failure is a service error (5xx): a transient error occurred in the HealthOmics service. Re-start the run with identical inputs (and the same run cache if one was used). No further diagnosis is needed.
    - IF the failure is a customer error (4xx): continue with the steps below.
3. **Add resource evidence when relevant.** IF the failure signature suggests resource exhaustion (out-of-memory kills, disk-full / no-space-left errors, tasks dying near their limits), ALSO call `AnalyzeAHORunPerformance` with the run ID. Its vended-metrics section (when available) shows per-task memory/CPU/scratch usage against limits and flags `MEMORY_PRESSURE` and `SCRATCH_NEAR_LIMIT` tasks — use it to confirm or rule out resource causes. IF vended metrics are unavailable for the run, the report says why; rely on the manifest-based sections.
4. **Identify the root cause.** State specifically what went wrong: the failing task, the error message and its meaning, and whether the cause is the workflow definition, container image, input parameters, service role permissions, or resource sizing.
    - For feature-specific failure reasons, load the matching SOP:
        - `S3_STORAGE_*` or `ECR_RUN_ROLE_PERMISSION_ERROR` on a run with `storageType: S3` -> [S3 Run Storage SOP](./s3-run-storage.md#troubleshooting)
        - `RUN_TIMED_OUT` on a run with `runMode: EXPRESS` -> [EXPRESS Run Mode SOP](./express-run-mode.md#troubleshooting)
        - `UNSUPPORTED_RUNTIME_PLATFORM_TYPE`, or `UNSUPPORTED_GPU_INSTANCE_TYPE` mentioning ARM64 -> [Runtime Platform SOP](./runtime-platform.md#troubleshooting)
5. **Remediate.**
    - IF you modify the workflow definition you MUST create a new version via `CreateAHOWorkflowVersion` (never edit in place).
    - IF the previous run used a run cache you MUST reference that cache when starting the new run; otherwise you MAY create one so the retry skips completed work.
    - Start a new run with identical or corrected inputs as appropriate.
6. **Prevent recurrence.** Close with the best-practice changes that would prevent this class of failure (e.g. right-sized task resources, linting before deployment via `LintAHOWorkflowDefinition`/`LintAHOWorkflowBundle`, pinned container digests).

## Expected Output

Report to the user:

- A clear diagnosis of the failure cause, naming the failing task(s)
- The specific error messages and what they mean
- Step-by-step remediation instructions (including exact tool calls or code/definition changes)
- Recommendations for preventing similar failures
- Links to relevant AWS documentation when applicable
