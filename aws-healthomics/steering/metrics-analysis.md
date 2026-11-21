# SOP: Vended Metrics Analysis

## Purpose

This SOP defines how you, the agent, answer questions about HealthOmics run and workflow resource utilization, performance, and metrics using the **vended metrics** — the fine-grained CPU, memory, GPU, network, filesystem-I/O, and scratch-storage metrics HealthOmics delivers into the customer's account as CloudWatch OpenTelemetry metrics.

Use it for: "why is my run slow?", "what is the CPU/GPU/filesystem utilization?", "is this run stuck?", "show me DataReadThroughput for run X", aggregation and metric math across tasks or runs, storage-type comparisons, I/O bottleneck/imbalance questions, trends over a run's duration, and cross-run comparisons.

Related SOPs: a *failed* run → [diagnose-run-failure.md](./diagnose-run-failure.md); holistic optimization of a completed run → [optimize-run.md](./optimize-run.md). Both may pull you back here for metric evidence.

## Rule 1: Check availability before answering

You MUST call `ListAHORunMetrics` with the run ID before answering any metrics question about a specific run. It reports which metric series actually exist (per task), which are expected absent for the run's configuration (with reasons), and caveats. Never assume a metric exists, and never treat an absence as an error before reading its reason.

Vended metrics exist ONLY for runs started after the feature's production launch (**2026-09-09**). For older runs, say so plainly and fall back to `AnalyzeAHORunPerformance` (manifest/timeline based) — do not present the absence as a failure.

## Metric semantics you MUST apply

- **Counters vs gauges.** `network.io`, `filesystem.io`, and `filesystem.operations` are *cumulative counters* (raw totals since container/mount start), not rates. The tools return `total_delta` (increase over the window) and `average_rate` (per second) — report those, never the raw counter values. Everything else is a gauge (`minimum`/`maximum`/`average`/`last`).
- **Task-level vs run-level.** Task identity exists on all `aws.omics.task.*` metrics. The only run-level metrics are `aws.omics.run.filesystem.usage`/`.limit`. **There is no run-level I/O metric** — for "run-level throughput", sum across tasks (`GetAHORunMetrics` returns per-task series; state that you aggregated).
- **Directions.** Filesystem I/O has `read`/`write` datapoints; network I/O has `receive`/`transmit`. Use the `direction` filter for imbalance questions ("reads vs writes side by side").
- **GPU metrics are per-device** (`gpu.id`); aggregate across devices when a task has several.

## Expected absences (explain, never fail)

| Configuration | Absent metrics | Why |
|---|---|---|
| No GPU tasks | `gpu.*` (3 metrics) | Only emitted when a task requests accelerators |
| SHARED scratch mode | `scratch.storage.limit` | Shared run filesystem has no per-task limit |
| DYNAMIC (EFS) storage | `run.filesystem.limit` | EFS has no fixed capacity |
| S3 run storage | all filesystem metrics | No run filesystem exists |
| Run started before 2026-09-09 | everything | Predates production launch |

## Timing caveats you MUST mention when relevant

- **Ingestion lag ~2 minutes**: for active runs, the latest datapoints may not be queryable yet.
- **EFS (DYNAMIC) run-filesystem usage lags ~35 minutes** behind real time — never interpret the lag as "storage not growing".
- **Scratch storage usage is sampled every ~20 minutes** (measuring it walks the filesystem): tasks shorter than that may have no scratch datapoints, and short-lived scratch peaks can be missed.
- **Tasks shorter than ~60 seconds** may have produced no datapoints at all (~30s sampling cadence).
- **Delivery is at-least-once, not guaranteed** — isolated gaps are possible and are not evidence of a problem.
- **Query responses cap at 500 series.** The tools split I/O metrics by direction automatically and set `possibly_truncated` when a response may have hit the cap. IF you see `possibly_truncated` on a run with many hundreds of tasks, narrow the query (`task_id`, `direction`) before trusting aggregations, and say the totals may undercount.

## Confidence and output discipline

- Every claim MUST cite the metric and scope that supports it (e.g. "task `align` peaked at 92% of its 16 GiB memory limit").
- State datapoint counts or sample sizes when they are small; recommendations from a single run or sparse series MUST carry a confidence note.
- Graph (plot the returned time series) when the user asks for trends, "over time", or comparisons where shape matters; otherwise summary statistics are enough. `GetAHORunMetrics` returns downsampled `[timestamp, value]` pairs for this — set `include_timeseries` false when you only need summaries.

---

## Skill: analyze-run-metrics

The workhorse for: why slow, utilization, insights, "is this run stuck?", basic retrieval, aggregation, storage-type filtering, I/O bottleneck/imbalance, and trends. Variables: run ID (and optionally task, metric names, window).

1. `ListAHORunMetrics(run_id)` — availability and caveats (Rule 1).
2. For verdicts ("why slow", "insights", "is it stuck?"): `AnalyzeAHORunPerformance(run_ids=[run_id])`. Its vended-metrics section gives per-task signatures with bottleneck categories (`CPU_BOUND`, `MEMORY_PRESSURE`, `IO_BOUND`, `GPU_IDLE`, `SCRATCH_NEAR_LIMIT`, `OVER_PROVISIONED`) and — for active runs — stuck-task verdicts (`POSSIBLY_HUNG` = ~zero CPU and no I/O progress; `MEMORY_THRASH_SUSPECT` = memory pinned at limit with low CPU, refaulting instead of progressing; `PROGRESSING`; `NO_RECENT_DATA`). Distinguish genuinely-hung from slow-but-progressing in your answer.
3. For raw families, metric math, filtering, or graphing: `GetAHORunMetrics(run_id, metric_names?, task_id?, direction?, start_time?, end_time?, include_timeseries?)`.

Expected output: the bottleneck task(s), the 1–2 metrics that prove it, right-sizing suggestions when over/under-provisioning is visible, a confidence note, and — for edge cases — a plain explanation of missing/lagged/task-level-only data instead of a failure.

## Skill: right-size-storage

For "what local disk / how much storage should I set?". Variables: workflow ID (preferred) or run ID.

1. `GetAHOWorkflowMetrics(workflow_id)` — per-task-name p50/p90/max distributions of scratch and storage peaks across recent completed runs. (Single run only available → use `GetAHORunMetrics` scratch/run-filesystem families and say the recommendation rests on one run.)
2. Recommend: observed p90–max peak plus headroom (~20%). For LOCAL scratch give a per-task size; for STATIC run storage give a run-level capacity; remind that DYNAMIC storage removes the sizing decision.
3. Output: recommended value, the observed distribution it rests on (p50/p90/max, sample count), and confidence.

## Skill: right-size-compute

For "am I under-utilizing compute?" / "over-provisioned?". Variables: workflow ID or run ID.

1. `GetAHOWorkflowMetrics(workflow_id)` for distributions, and/or `AnalyzeAHORunPerformance(run_ids=[run_id])` for per-task verdicts and right-sizing suggestions.
2. Output per task name: over/under-provisioning verdict with the cpu/gpu/memory usage-vs-limit evidence (e.g. "requests 8 vCPU, p90 peak 1.4 → suggest 2"), plus `GPU_IDLE` flags where a GPU is requested but unused.

## Skill: compare-runs

For "why did run B take longer than run A?" and Static-vs-Dynamic / today-vs-yesterday comparisons. Variables: two run IDs.

1. `ListAHORunMetrics(run_id_a)` and `ListAHORunMetrics(run_id_b)` — availability and caveats for each run (Rule 1). IF either run has no vended metrics (e.g. it predates the launch, or S3 storage), say which run and why; the comparison then degrades to wall-clock/timeline only.
2. `CompareAHORunMetrics(run_id_a, run_id_b)` — aligns tasks **by task name**, diffs wall-clock and per-task durations, and reports each task's largest metric deltas (window totals for counters, peaks for gauges).
3. Lead with which phase/task drove the wall-clock delta and its metric signature (e.g. "+1841s, driven by 4.6× more filesystem operations on the STATIC run"). Note configuration differences (storage type, scratch mode) from the run configs in the response.
4. IF the runs share no task names (different workflows), the comparison degrades to wall-clock only — say so and suggest comparing runs of the same workflow.

---

## Prompt → tool quick reference

| User asks | Use |
|---|---|
| Why slow / insights / utilization / is it stuck | `AnalyzeAHORunPerformance` (after `ListAHORunMetrics`) |
| Specific metric value / graph / trend | `GetAHORunMetrics` |
| Total/highest/average across tasks | `GetAHORunMetrics` (aggregate across returned per-task series) |
| Across recent runs (averages, distributions) | `GetAHOWorkflowMetrics` |
| Compare two runs | `CompareAHORunMetrics` (after `ListAHORunMetrics` on both, per Rule 1) |
| What disk/storage should I set | `GetAHOWorkflowMetrics` → recommendation (right-size-storage) |
| Am I over-provisioned | `GetAHOWorkflowMetrics` + `AnalyzeAHORunPerformance` (right-size-compute) |
| Metric seems missing | `ListAHORunMetrics` → report its reason, don't fail |
