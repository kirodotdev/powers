# SOP: Optimize a Completed HealthOmics Run

## Purpose

This SOP defines how you, the agent, analyze a completed AWS HealthOmics workflow run and recommend cost and performance optimizations. Use it when the user asks how to make a run cheaper or faster, whether resources are over-provisioned, or how a completed run performed.

For metric semantics, availability rules, and direct metric queries (specific values, graphs, run comparisons), see the [Vended Metrics Analysis SOP](./metrics-analysis.md).

## Procedure

1. **Get run context.** Call `GetAHORun` for the run's configuration: storage type and capacity, scratch storage mode, run duration, and workflow ID.
2. **Analyze performance.** Call `AnalyzeAHORunPerformance` with the run ID. The report contains:
    - Manifest-based analysis: execution timeline, task durations, per-task cost estimates, CPU/memory efficiency, and potential savings.
    - A vended-metrics section (when available): per-task resource signatures against limits with bottleneck categories (`CPU_BOUND`, `MEMORY_PRESSURE`, `IO_BOUND`, `GPU_IDLE`, `SCRATCH_NEAR_LIMIT`, `OVER_PROVISIONED`), and observed-peak right-sizing suggestions with headroom. Prefer these fine-grained signatures over manifest-only numbers when both are present. IF the section says vended metrics are unavailable (run predates the feature launch, unsupported region, storage configuration), say so and rely on the manifest-based sections.
3. **Broaden the evidence when asked about the workflow generally.** IF the question is about the workflow rather than a single run ("how does this workflow perform", "what should I set for future runs"), ALSO call `GetAHOWorkflowMetrics` with the workflow ID for per-task-name p50/p90/max distributions across recent runs — recommendations based on one run can be skewed by one unusual input.
4. **Identify optimizations**, in priority order:
    - **Over-provisioned tasks**: sustained low CPU/GPU/memory usage against limits → lower the task's requested resources (the right-sizing section gives observed peak + headroom values).
    - **Bottleneck tasks**: the longest tasks on the critical path; check their category — an `IO_BOUND` task won't get faster with more CPU.
    - **Sequential scatter**: scattered tasks of the same name running one after another instead of in parallel indicates a service quota ceiling — suggest a quota increase.
    - **Storage sizing**: run storage and scratch sized far above observed peaks; suggest smaller values (or DYNAMIC storage where appropriate).
5. **Make recommendations concrete.** For each recommendation give the specific configuration change (task resource declaration, storage capacity value, quota name) with example code where the workflow definition changes, and the estimated saving or speedup. IF you modify the workflow definition you MUST create a new version via `CreateAHOWorkflowVersion`.

## Expected Output

Report to the user:

- A summary of the run's performance (duration, cost estimate, overall efficiency)
- A prioritized list of optimization opportunities with the evidence behind each
- Specific configuration changes to implement (with example code where relevant)
- The estimated impact of each recommendation
- A confidence note when recommendations rest on limited data (single run, missing vended metrics, short tasks)
