---
_phase: discover
_title: "Discover — Lightweight Detection"
_requires_phase: intake
_input: workspace
_assemble:
  _file: agent-advisor-discover-assemble.md
_produces:
  - context-signals.json
_advances_to: clarify
_preconditions:
  - _check_phase_completed: intake
    _on_failure: _halt_and_inform
_postconditions:
  - _check_file_exists: context-signals.json
    _on_failure: _halt_and_inform
  - _validate_json: context-signals.json
    _on_failure: _halt_and_inform
  - _assert: "context-signals.json contains only signals detected with reasonable confidence, with a _detected array; model_provider recorded when detection succeeded; units[] is non-empty with legal workload_class, coupling.mode, and trigger values, kebab-case ids, and no in_process coupling (merged during grouping); when Temporal is detected, units include the temporal_worker_poll tier and per-Activity-class entries, and the temporal context object records server state; temporal_worker_poll units list their queues"
    _on_failure: _halt_and_inform
---

# Phase: Discover — Lightweight Detection

Only runs for build_deploy / migrate when the user provided a code path. Stays independent
(does NOT require the migration-to-aws plugin).

## Step 1 — Scan for signals (read-only)

In the provided path, look for:

- **Framework** (imports / requirements.txt / package.json): `strands`, `langgraph` /
  `langchain`, `crewai` / `autogen`, `openai` (Agents SDK), else `custom` / `none`.
- **Model provider**: openai / anthropic / google-genai / bedrock mentions.
- **Session/timeout hints**: timeout configs, long-running loops, queue/HITL patterns.
- **Multi-tenant hints**: per-user/tenant scoping, separate contexts.
- **Compute hints**: GPU instance types, heavy compute (compilation, ML inference).
- **Data store hints**: Redis/DynamoDB/vector store connections.
- **Temporal orchestration**: `temporalio` (Python) / `go.temporal.io` (Go) /
  `temporal-sdk` (Java) / `@temporalio/*` (TypeScript) imports or dependencies.
- **Unit inventory**: enumerate the system's workload units. Signals:
  - agent graphs/swarms (LangGraph graph, CrewAI crew, custom loop) → `agent_session`
  - cron/scheduler entries, queue consumers doing periodic bulk work → `batch`
  - webhook handlers, thin API routes, event handlers → `light_io`
  - long-running servers / WebSocket daemons that are not agents → `service`

  **Grouping rule (first, before writing units):** agents that interact IN-PROCESS —
  nodes of one framework graph, members of one swarm, direct in-process calls — are
  ONE unit; they deploy and scale together, and that unit's `multi_agent` scoring
  answer is `yes`. Workloads that interact across processes (`queue`, `api`, `a2a`)
  or not at all (`none`) are separate units. `in_process` therefore never appears in
  a written unit's `coupling.mode` — it is the merge criterion, not a link type.
  Closed vocabularies: `workload_class` ∈ {`agent_session`, `batch`, `light_io`,
  `service`, `temporal_worker_poll`}; `coupling.mode` ∈ {`queue`, `api`, `a2a`, `none`}.

  **Temporal detection** (when the signals above are found): create one
  `temporal_worker_poll` unit per worker fleet (task-queue group), plus one unit per
  Activity execution class. Activity classification uses the vocabulary in
  `agent-advisor-temporal.md` (Tier 2): agent-session Activities →
  `agent_session`; batch Activities → `batch`; light-IO Activities → `light_io`. Worker
  registration patterns (Python: `Worker.run()` or `client.execute_workflow()`,
  Go: `worker.RegisterWorkflow`, Java: `@WorkflowMethod` / `@ActivityMethod`,
  TypeScript: `Worker.create({workflowsPath})`) and task-queue names in config files or
  Worker constructors identify worker fleets. Each `temporal_worker_poll` unit gains
  `"queues": ["<task queue names this unit polls>"]` (from the detected task_queues,
  grouped per unit). Each **Activity-class unit** (agent_session / batch / light_io created
  from an Activity) gains `"task_queue": "<the task queue this Activity runs on>"` — the
  queue that ties it to the worker fleet that executes it (from the Activity's `task_queue=`
  in `execute_activity` / `proxyActivities` / Worker registration). This is the join key
  between a poll unit's `queues[]` and its Activity units: a diagram or plan connects ONLY
  the fleet whose `queues[]` contains an Activity's `task_queue`, never a cartesian product
  across all fleets. With a single fleet on a single queue, every Activity carries that one
  queue. On Temporal detection, record the following
  detection signals: `temporalio`, `go.temporal.io`, `@temporalio/*`, or `temporal-sdk`
  package imports; Worker registration calls (`Worker.run()`, `worker.RegisterWorkflow`,
  `Worker.create()`); task-queue names in source or config; Workflow decorators /
  annotations (`@workflow.defn`, `@WorkflowMethod`); Activity decorators / annotations
  (`@activity.defn`, `@ActivityMethod`); `workflow.ExecuteActivity` call sites;
  `proxyActivities<T>()` (TypeScript); server connection config (`*.tmprl.cloud` or
  self-hosted address). Write a top-level `temporal` context object in
  `context-signals.json`: `{ "detected": true, "server": "cloud|self_hosted|unknown",
  "sdks": [], "task_queues": [] }`.

  **Trigger detection:** each unit gains a `trigger` field capturing how it is invoked.
  Closed vocabulary: `trigger` ∈ {`request`, `event`, `schedule`, `temporal`, `unknown`}.
  Detect from handler type (REST/WebSocket handlers → `request`), cron entries or
  scheduler configs → `schedule`, event-source wiring (queue consumers, S3 listeners,
  SNS/webhook handlers) → `event`, Temporal Activity registration → `temporal`.

## Step 2 — Map to pre-filled answers

Write `$RUN_DIR/context-signals.json` mapping detected signals onto scoring keys, e.g.:

```json
{
  "framework": "langgraph",
  "multi_agent": "yes",
  "session_state": "hitl",
  "model_provider": "openai",
  "_detected": [
    "framework from imports",
    "multi_agent from graph with 2+ nodes",
    "model_provider from SDK imports"
  ],
  "units": [
    {
      "id": "chat-agent",
      "workload_class": "agent_session",
      "trigger": "request",
      "source": "detected",
      "framework": "langgraph",
      "coupling": {
        "interacts_with": ["summarizer"],
        "mode": "queue"
      },
      "evidence": "LangGraph StateGraph with 3 nodes; pushes summaries to Redis queue"
    },
    {
      "id": "summarizer",
      "workload_class": "batch",
      "trigger": "schedule",
      "source": "detected",
      "coupling": {
        "interacts_with": [],
        "mode": "none"
      },
      "evidence": "Celery worker consuming summary queue; runs nightly"
    }
  ]
}
```

Only include keys you can detect with reasonable confidence. Everything else stays for Clarify.

`model_provider` (openai | anthropic | google-genai | bedrock | none) is not a scoring key —
it records which AI provider the code calls, and gates the migration-plan offer in Generate
Step 6. Include it whenever provider detection succeeded.

## Step 3 — Tell the user what was detected

List the detected signals so the user can correct them in Clarify. These pre-fills let
Clarify skip questions (Clarify asks fewer for build_deploy/migrate).

**Determinism boundary (important):** these detections are a _best-effort LLM interpretation_
of code, NOT deterministic facts. They become inputs to the deterministic scoring engine, so a
wrong detection silently biases scoring. Mitigation: (1) only write a signal you can detect
with high confidence — when unsure, omit it and let Clarify ask; (2) always present detected
signals to the user as "detected: X (correct me if wrong)" so they have a correction
opportunity before scoring runs. This is the one point where LLM interpretation enters the
otherwise deterministic pipeline.

## Step 4 — Write state

Set `phases.discover` = completed.
