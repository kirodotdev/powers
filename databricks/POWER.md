---
name: "databricks"
displayName: "Databricks AI Dev Kit"
description: "Comprehensive Databricks development toolkit with 44 MCP tools (180+ operations) and expert guidance for building data pipelines, ML workflows, dashboards, jobs, and applications on Databricks platform."
keywords: ["databricks", "spark", "delta", "mlflow", "unity catalog", "pipelines", "jobs", "sql", "data engineering", "machine learning"]
author: "Databricks"
---

# Databricks AI Dev Kit Power

## Overview

The Databricks AI Dev Kit Power provides comprehensive access to the Databricks Lakehouse platform through 44 MCP tools (180+ operations) and expert steering files for every Databricks capability — pipelines, jobs, dashboards, ML, governance, and apps.

**Key capabilities:**
- **SQL & Compute**: Execute SQL on warehouses, run Python/Scala on clusters, manage compute lifecycle
- **Pipelines & Jobs**: Build Spark Declarative Pipelines (streaming tables, CDC, SCD Type 2, Auto Loader) and orchestrate multi-task DAGs
- **Unity Catalog**: Manage tables, volumes, grants, tags, storage credentials, system tables, metric views, and External Iceberg Reads (cross-engine interop via UC IRC)
- **AI/BI Dashboards**: Create interactive visualizations, KPIs, and analytics dashboards
- **Genie Spaces**: Natural-language data exploration over governed datasets
- **Agent Bricks**: Build Knowledge Assistants (RAG) and Multi-Agent Supervisors
- **Vector Search**: Semantic search and RAG with managed indexes
- **Model Serving**: Deploy ML models, AI agents, and pay-per-token Foundation Model APIs (FMAPI) to scalable endpoints; route through AI Gateway for guardrails, fallbacks, and rate limiting
- **MLflow**: Track experiments, evaluate models, instrument tracing, query metrics
- **Lakebase**: Provisioned and autoscale managed PostgreSQL for OLTP workloads
- **Databricks Apps**: Full-stack web applications on the Lakehouse
- **Asset Bundles**: Infrastructure-as-code for Databricks resources

**Authentication**: Requires a Databricks workspace and either an OAuth-authenticated CLI profile, an existing `~/.databrickscfg` profile, or a Personal Access Token (PAT).

## Agent First-Action Protocol (CRITICAL)

> **⚠️ MANDATORY pre-flight gate — read before any tool call:**
>
> On the **first turn** of any new conversation in this Power — and **before invoking any Databricks MCP tool** — the agent MUST run the credential-detection flow defined in [Step 3: Configure Authentication](#step-3-configure-authentication). Do not enumerate tools, call `get_current_user`, or attempt any MCP operation until detection has completed and the user has confirmed which credentials to use.
>
> **In-session auth-failure recovery.** If at any point during the session a Databricks MCP tool returns `Invalid access token`, `401 Unauthorized`, `403 token expired`, or any equivalent auth-failure status:
>
> 1. **Stop** further tool calls immediately. Do not retry the failed call.
> 2. **Re-enter** the credential-detection flow — surface the current credential summary to the user and ask which option (A / B / C / D) they want to repair or switch to.
> 3. **Recommend OAuth U2M (Option A)** as the first fix for interactive use. It auto-refreshes hourly and avoids the long-lived-secret expiry that typically causes these errors.
>
> **No-credentials default.** When no Databricks credentials are detected on first run, the agent's default recommendation is **Option A — OAuth U2M via the Databricks CLI**, since it's the safest interactive flow and covers the most common use case (a single human developer on a workstation).

## Available Steering Files

This Power's steering files are downloaded from the [ai-dev-kit repository](https://github.com/databricks-solutions/ai-dev-kit/tree/main/databricks-skills) during onboarding and copied into the Power's `steering/` directory. Skills load on-demand based on your task.

### Skill Catalog (34+ skills)

| Skill | Domain | Description |
|-------|--------|-------------|
| databricks-spark-declarative-pipelines | Data Engineering | Streaming tables, CDC, SCD Type 2, Auto Loader |
| databricks-spark-structured-streaming | Data Engineering | Kafka, stateful ops, stream joins |
| databricks-jobs | Data Engineering | Scheduled workflows, multi-task DAGs, serverless |
| databricks-zerobus-ingest | Data Engineering | Zero-copy ingestion |
| databricks-execution-compute | Data Engineering | Code execution + cluster / warehouse lifecycle |
| databricks-iceberg | Data Engineering | Iceberg tables, UniForm, interop |
| databricks-aibi-dashboards | Analytics | Interactive visualizations, KPIs, analytics |
| databricks-dbsql | Analytics | SQL best practices, materialized views |
| databricks-genie | Analytics | Natural language data exploration |
| databricks-metric-views | Analytics | Reusable business metrics |
| databricks-unity-catalog | Governance | Tables, volumes, governance, system tables |
| databricks-agent-bricks | AI/ML | Knowledge Assistants, Supervisor Agents |
| databricks-vector-search | AI/ML | Semantic search and RAG applications |
| databricks-model-serving | AI/ML | Deploy ML models and AI agents |
| databricks-mlflow-evaluation | AI/ML | Model evaluation, scoring, traces |
| databricks-ai-functions | AI/ML | AI functions, forecasting, document processing |
| databricks-synthetic-data-gen | AI/ML | Synthetic data generation |
| databricks-apps-python | App Development | Full-stack web applications |
| databricks-app-apx | App Development | App frontend/backend patterns |
| databricks-lakebase-provisioned | App Development | Managed PostgreSQL (provisioned) |
| databricks-lakebase-autoscale | App Development | Managed PostgreSQL (autoscale) |
| databricks-bundles | Platform | Databricks Asset Bundles |
| databricks-config | Platform | Workspace configuration |
| databricks-python-sdk | Platform | Python SDK patterns and examples |
| databricks-unstructured-pdf-generation | Platform | PDF generation and upload |
| databricks-docs | Platform | Documentation search |
| mlflow-onboarding | MLflow | MLflow getting started |
| instrumenting-with-mlflow-tracing | MLflow | MLflow tracing instrumentation |
| querying-mlflow-metrics | MLflow | Querying MLflow metrics |
| retrieving-mlflow-traces | MLflow | Retrieving MLflow traces |
| searching-mlflow-docs | MLflow | Searching MLflow documentation |
| analyze-mlflow-trace | MLflow | Analyzing MLflow traces |
| analyze-mlflow-chat-session | MLflow | Analyzing MLflow chat sessions |
| agent-evaluation | MLflow | Agent evaluation patterns |
| spark-python-data-source | Data Engineering | Custom Spark data sources |

### Skill Loading

This Power installs **all 34+ skills** (`--skills-profile all`). Skills are markdown files that load on demand based on the task at hand — having the full set present incurs no runtime cost, and it avoids re-running the installer when work crosses domains (e.g., an ML engineer who occasionally builds a dashboard). Persona-specific subsets are not used.

## Available MCP Servers

### databricks
**Package:** `databricks-solutions/ai-dev-kit` (`databricks-mcp-server`)
**Connection:** Local Python process (`uv` venv) configured via `~/.kiro/settings/mcp.json`

44 tools spanning 180+ operations. The most frequently used are itemized below; see the full category index further down.

#### SQL & Compute

1. **execute_sql** — Run a SQL statement on a SQL warehouse
   - Required: `statement` (string), `warehouse_id` (string)
   - Optional: `catalog`, `schema`, `parameters`, `wait_timeout`
   - Returns: Result rows, schema, statement state

2. **execute_sql_multi** — Run multiple SQL statements in sequence
   - Required: `statements` (string[]), `warehouse_id` (string)
   - Returns: Results per statement

3. **execute_code** — Execute Python/Scala/R/SQL on an interactive cluster
   - Required: `cluster_id` (string), `language` (string), `code` (string)
   - Returns: Execution output

4. **manage_cluster** — Create / get / list / start / restart / terminate / edit clusters
   - Required: `action` (string)
   - Optional: cluster spec fields per action
   - Returns: Cluster object or list

5. **manage_sql_warehouse** — Create / get / list / start / stop / edit / delete SQL warehouses
   - Required: `action` (string)
   - Optional: warehouse spec fields per action
   - Returns: Warehouse object or list

6. **manage_warehouse** — Companion warehouse helper for SQL workflows
   - Required: `action` (string)
   - Returns: Warehouse state

7. **list_compute** — List available compute resources (clusters + warehouses)
   - Optional: `filter_type`
   - Returns: Compute summary

8. **get_table_stats_and_schema** — Inspect table schema, row counts, partitioning
   - Required: `table_name` (fully-qualified, e.g. `catalog.schema.table`)
   - Returns: Schema, statistics, partition info

#### Jobs & Pipelines

9. **manage_jobs** — Create / get / list / update / delete jobs
   - Required: `action` (string)
   - Optional: job spec (`tasks`, `schedule`, `parameters`, `email_notifications`)
   - Returns: Job object or list

10. **manage_job_runs** — Run / wait / cancel / get-output for job runs
    - Required: `action` (string), `job_id` or `run_id`
    - Returns: Run state, output, logs

11. **manage_pipeline** — Create / get / list / update / delete Spark Declarative Pipelines (DLT)
    - Required: `action` (string)
    - Optional: pipeline spec, libraries, target schema
    - Returns: Pipeline object

12. **manage_pipeline_run** — Start / stop / get-update for pipeline runs
    - Required: `action` (string), `pipeline_id`
    - Returns: Run/update state

#### Unity Catalog

13. **manage_uc_objects** — Create / get / list / update / delete catalogs, schemas, tables, volumes, functions
    - Required: `action` (string), `object_type` (string)
    - Optional: object spec
    - Returns: UC object or list

14. **manage_uc_grants** — Grant / revoke / list privileges on UC objects
    - Required: `action` (string), `securable_type`, `full_name`
    - Returns: Permission assignments

15. **manage_uc_storage** — Manage external locations and storage credentials
    - Required: `action` (string)
    - Returns: Storage credential / external location

16. **manage_uc_tags** — Apply / remove tags on UC objects
    - Required: `action` (string), `object`, `tags`
    - Returns: Tag assignments

17. **manage_uc_connections** — Manage federated catalog connections
    - Required: `action` (string)
    - Returns: Connection object

18. **manage_uc_sharing** — Manage Delta Sharing shares and recipients
    - Required: `action` (string)
    - Returns: Share / recipient

19. **manage_uc_monitors** — Manage Lakehouse Monitoring profiles
    - Required: `action` (string), `table_name`
    - Returns: Monitor state

20. **manage_uc_security_policies** — Manage row-level / column-level security policies
    - Required: `action` (string)
    - Returns: Policy object

21. **manage_metric_views** — Create / list / update reusable business metrics
    - Required: `action` (string)
    - Returns: Metric view definition

#### Dashboards, Genie & Agent Bricks

22. **manage_dashboard** — Create / get / list / delete / publish AI/BI dashboards
    - Required: `action` (string)
    - Optional: dashboard JSON, draft/publish flags
    - Returns: Dashboard object

23. **manage_genie** — Create / list / configure Genie Spaces
    - Required: `action` (string)
    - Returns: Genie Space object

24. **ask_genie** — Ask a question against a Genie Space
    - Required: `space_id`, `question`
    - Returns: Generated SQL, result rows, explanation

25. **manage_ka** — Create / list / update Knowledge Assistants (RAG agents)
    - Required: `action` (string)
    - Returns: Knowledge Assistant object

26. **manage_mas** — Create / list / update Multi-Agent Supervisors
    - Required: `action` (string)
    - Returns: Multi-Agent Supervisor object

#### Model Serving & Vector Search

27. **manage_serving_endpoint** — Get / list / query serving endpoints
    - Required: `action` (string)
    - Optional: `endpoint_name`, `inputs` (for query)
    - Returns: Endpoint object or model output

28. **manage_vs_endpoint** — Create / list / delete vector search endpoints
    - Required: `action` (string)
    - Returns: VS endpoint object

29. **manage_vs_index** — Create / list / sync / delete vector search indexes
    - Required: `action` (string)
    - Returns: VS index object

30. **manage_vs_data** — Upsert / delete documents in a direct-access VS index
    - Required: `action` (string), `index_name`, `data`
    - Returns: Operation status

31. **query_vs_index** — Similarity search against a VS index
    - Required: `index_name`, `query_text` or `query_vector`
    - Optional: `num_results`, `filters`
    - Returns: Top-k matched documents

#### Lakebase, Apps & Files

32. **manage_lakebase_database** — Create / get / list / delete Lakebase databases
    - Required: `action` (string)
    - Returns: Lakebase database object

33. **manage_lakebase_branch** — Manage Lakebase branches
    - Required: `action` (string)
    - Returns: Branch state

34. **manage_lakebase_sync** — Configure Lakebase ↔ UC sync
    - Required: `action` (string)
    - Returns: Sync configuration

35. **generate_lakebase_credential** — Issue short-lived Lakebase credentials
    - Required: `database_name`
    - Returns: Credential

36. **manage_app** — Create / get / list / delete / deploy Databricks Apps
    - Required: `action` (string)
    - Returns: App object

37. **manage_workspace_files** — Read / write / list / delete workspace files
    - Required: `action` (string), `path`
    - Returns: File contents or status

38. **manage_volume_files** — Read / write / list / delete volume files
    - Required: `action` (string), `path`
    - Returns: File contents or status

39. **get_volume_folder_details** — Inspect a UC volume folder
    - Required: `volume_path`
    - Returns: Folder listing with metadata

#### Workspace, Tracking & Utilities

40. **manage_workspace** — Workspace-level operations (notebooks, folders, permissions)
    - Required: `action` (string)
    - Returns: Workspace object

41. **get_current_user** — Identify the authenticated principal
    - No parameters required
    - Returns: User profile, workspace, entitlements

42. **generate_and_upload_pdf** — Render HTML to PDF and upload to a volume
    - Required: `html`, `volume_path`
    - Returns: Uploaded file path

43. **list_tracked_resources** — List resources created/tracked by this MCP session
    - Optional: `resource_type`
    - Returns: Tracked resources

44. **delete_tracked_resource** — Delete a previously tracked resource
    - Required: `resource_type`, `resource_id`
    - Returns: Deletion status

### Full Tool Index

| Category | Tool count | Operations |
|----------|-----------|------------|
| SQL & Compute | 8 | execute_sql, execute_sql_multi, execute_code, manage_cluster, manage_sql_warehouse, manage_warehouse, list_compute, get_table_stats_and_schema |
| Jobs & Pipelines | 4 | manage_jobs, manage_job_runs, manage_pipeline, manage_pipeline_run |
| Unity Catalog | 9 | manage_uc_objects, manage_uc_grants, manage_uc_storage, manage_uc_tags, manage_uc_connections, manage_uc_sharing, manage_uc_monitors, manage_uc_security_policies, manage_metric_views |
| Dashboards / Genie / Agents | 5 | manage_dashboard, manage_genie, ask_genie, manage_ka, manage_mas |
| Model Serving / Vector Search | 5 | manage_serving_endpoint, manage_vs_endpoint, manage_vs_index, manage_vs_data, query_vs_index |
| Lakebase / Apps / Files | 8 | manage_lakebase_database, manage_lakebase_branch, manage_lakebase_sync, generate_lakebase_credential, manage_app, manage_workspace_files, manage_volume_files, get_volume_folder_details |
| Workspace / Utilities | 5 | manage_workspace, get_current_user, generate_and_upload_pdf, list_tracked_resources, delete_tracked_resource |

## Tool Usage Examples

### Executing SQL

**Run a query on a warehouse:**
```javascript
usePower("databricks", "databricks", "execute_sql", {
  "statement": "SELECT current_catalog(), current_schema()",
  "warehouse_id": "abc123def456"
})
// Returns: Single-row result with current catalog and schema
```

**Inspect a table:**
```javascript
usePower("databricks", "databricks", "get_table_stats_and_schema", {
  "table_name": "main.sales.orders"
})
// Returns: Columns, types, row count, partition info
```

### Managing Jobs

**Create a job:**
```javascript
usePower("databricks", "databricks", "manage_jobs", {
  "action": "create",
  "name": "nightly_orders_etl",
  "tasks": [{
    "task_key": "transform",
    "notebook_task": { "notebook_path": "/Workspace/etl/transform_orders" },
    "job_cluster_key": "main"
  }],
  "schedule": { "quartz_cron_expression": "0 0 2 * * ?", "timezone_id": "UTC" }
})
// Returns: job_id of the created job
```

**Run and wait:**
```javascript
usePower("databricks", "databricks", "manage_job_runs", {
  "action": "run_now_and_wait",
  "job_id": 123456789
})
// Returns: Run state and task outputs
```

### Spark Declarative Pipelines

**Create a streaming pipeline:**
```javascript
usePower("databricks", "databricks", "manage_pipeline", {
  "action": "create",
  "name": "bronze_to_silver_orders",
  "target": "main.silver",
  "libraries": [{ "notebook": { "path": "/Workspace/dlt/orders_silver" } }],
  "continuous": true
})
// Returns: pipeline_id
```

### Unity Catalog

**Create a managed table:**
```javascript
usePower("databricks", "databricks", "manage_uc_objects", {
  "action": "create",
  "object_type": "table",
  "full_name": "main.sandbox.customer",
  "columns": [
    { "name": "id", "type_text": "BIGINT" },
    { "name": "email", "type_text": "STRING" }
  ]
})
// Returns: Table object with metadata
```

**Grant SELECT to a group:**
```javascript
usePower("databricks", "databricks", "manage_uc_grants", {
  "action": "grant",
  "securable_type": "table",
  "full_name": "main.sales.orders",
  "principal": "analysts",
  "privileges": ["SELECT"]
})
// Returns: Updated permission assignments
```

### Genie & Knowledge Assistants

**Ask Genie a natural-language question:**
```javascript
usePower("databricks", "databricks", "ask_genie", {
  "space_id": "01ef...",
  "question": "What were the top 5 products by revenue last month?"
})
// Returns: Generated SQL, result rows, narrative explanation
```

### Vector Search

**Similarity search over a managed index:**
```javascript
usePower("databricks", "databricks", "query_vs_index", {
  "index_name": "main.search.docs_idx",
  "query_text": "How do I configure Auto Loader for Parquet?",
  "num_results": 5
})
// Returns: Top-5 matched documents with scores
```

### Model Serving

**Query an endpoint:**
```javascript
usePower("databricks", "databricks", "manage_serving_endpoint", {
  "action": "query",
  "endpoint_name": "claims-classifier",
  "inputs": { "dataframe_records": [{ "claim_text": "..." }] }
})
// Returns: Model predictions
```

## Combining Tools (Workflows)

### Workflow 1: Build a Streaming ETL with Job Orchestration

```javascript
// Step 1: Create the bronze→silver pipeline
const pipeline = usePower("databricks", "databricks", "manage_pipeline", {
  "action": "create",
  "name": "orders_silver",
  "target": "main.silver",
  "libraries": [{ "notebook": { "path": "/Workspace/dlt/orders_silver" } }]
})

// Step 2: Wrap the pipeline in a scheduled job
const job = usePower("databricks", "databricks", "manage_jobs", {
  "action": "create",
  "name": "orders_silver_orchestrator",
  "tasks": [{
    "task_key": "run_dlt",
    "pipeline_task": { "pipeline_id": pipeline.pipeline_id }
  }],
  "schedule": { "quartz_cron_expression": "0 0 * * * ?", "timezone_id": "UTC" }
})

// Step 3: Trigger an initial run and wait
const run = usePower("databricks", "databricks", "manage_job_runs", {
  "action": "run_now_and_wait",
  "job_id": job.job_id
})

// Step 4: Verify rows landed in silver
const stats = usePower("databricks", "databricks", "get_table_stats_and_schema", {
  "table_name": "main.silver.orders"
})
```

### Workflow 2: Govern a New Table and Publish a Dashboard

```javascript
// Step 1: Create the table
usePower("databricks", "databricks", "manage_uc_objects", {
  "action": "create",
  "object_type": "table",
  "full_name": "main.analytics.daily_revenue",
  "columns": [
    { "name": "day", "type_text": "DATE" },
    { "name": "revenue", "type_text": "DECIMAL(18,2)" }
  ]
})

// Step 2: Grant access
usePower("databricks", "databricks", "manage_uc_grants", {
  "action": "grant",
  "securable_type": "table",
  "full_name": "main.analytics.daily_revenue",
  "principal": "analysts",
  "privileges": ["SELECT"]
})

// Step 3: Tag for discovery
usePower("databricks", "databricks", "manage_uc_tags", {
  "action": "set",
  "object": { "type": "table", "full_name": "main.analytics.daily_revenue" },
  "tags": { "domain": "finance", "tier": "gold" }
})

// Step 4: Publish a dashboard
usePower("databricks", "databricks", "manage_dashboard", {
  "action": "create",
  "name": "Daily Revenue",
  "warehouse_id": "abc123def456",
  "dataset_query": "SELECT * FROM main.analytics.daily_revenue ORDER BY day DESC"
})
```

### Workflow 3: Build a RAG Knowledge Assistant

```javascript
// Step 1: Create a vector search endpoint
usePower("databricks", "databricks", "manage_vs_endpoint", {
  "action": "create",
  "name": "kb-endpoint"
})

// Step 2: Create an index over governed docs
usePower("databricks", "databricks", "manage_vs_index", {
  "action": "create",
  "endpoint_name": "kb-endpoint",
  "index_name": "main.kb.docs_idx",
  "source_table": "main.kb.docs",
  "primary_key": "doc_id",
  "embedding_source_column": "content"
})

// Step 3: Wire up the Knowledge Assistant
const ka = usePower("databricks", "databricks", "manage_ka", {
  "action": "create",
  "name": "internal-kb-assistant",
  "vector_index": "main.kb.docs_idx"
})

// Step 4: Query Genie or the assistant directly
usePower("databricks", "databricks", "query_vs_index", {
  "index_name": "main.kb.docs_idx",
  "query_text": "What is our incident escalation policy?",
  "num_results": 5
})
```

## SQL & DBSQL Syntax Guide

The MCP server runs SQL through Databricks SQL warehouses (Photon-accelerated ANSI SQL with Delta and Unity Catalog extensions).

### Core Patterns

**Three-part naming (always use it):**
```sql
SELECT * FROM <catalog>.<schema>.<table>
```

**Time travel:**
```sql
SELECT * FROM main.sales.orders VERSION AS OF 42;
SELECT * FROM main.sales.orders TIMESTAMP AS OF '2026-05-01';
```

**MERGE for upserts:**
```sql
MERGE INTO target t USING source s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

**Materialized views (Delta Live / DBSQL):**
```sql
CREATE MATERIALIZED VIEW main.gold.orders_daily AS
SELECT order_date, COUNT(*) AS n FROM main.silver.orders GROUP BY order_date;
```

**Streaming tables (DLT):**
```sql
CREATE OR REFRESH STREAMING TABLE bronze_orders
AS SELECT * FROM cloud_files('/Volumes/main/raw/orders', 'json');
```

### Critical Rules

1. **Always fully qualify** with `catalog.schema.table` — UC enforces three-part naming
2. **Use parameter markers** for user input: `:param_name` (passed in `parameters` arg)
3. **Set a `wait_timeout`** for long queries (e.g., `"30s"`); poll with subsequent calls if needed
4. **Prefer warehouses over clusters** for SQL — cheaper, faster cold start, Photon-enabled
5. **Use `OPTIMIZE` and `VACUUM`** on Delta tables for performance/storage hygiene
6. **Check warehouse state** before executing — start with `list_compute` if unsure

## Best Practices

### ✅ Do

- **Start with `get_current_user`** to confirm workspace, profile, and entitlements before doing real work
- **Use SQL warehouses for SQL** — they're cheaper, auto-suspend, and Photon-accelerated
- **Use Unity Catalog three-part names** everywhere (`catalog.schema.object`)
- **Tag and grant on creation** — wire up `manage_uc_tags` and `manage_uc_grants` immediately after `manage_uc_objects`
- **Track resources** — use `list_tracked_resources` to audit what this session created; clean up with `delete_tracked_resource`
- **Pin pipelines and jobs** to specific cluster policies for cost control
- **Validate schemas** with `get_table_stats_and_schema` before writing transformations
- **Prefer DLT (manage_pipeline)** over hand-rolled jobs for streaming and CDC
- **Wait on runs** explicitly (`run_now_and_wait`) when downstream steps depend on output
- **Load skill files on demand** — don't pre-load all 33 skills; the on-demand pattern is faster

### ❌ Don't

- **Don't run SQL on interactive clusters** when a warehouse will do — cost spikes and cold-start delays
- **Don't omit catalog/schema** — relying on session defaults breaks portability
- **Don't hardcode warehouse IDs or job IDs** — fetch them with `list_compute` and `manage_jobs` (action: list)
- **Don't grant `ALL_PRIVILEGES`** when `SELECT` or `MODIFY` is enough
- **Don't create resources without tagging** — UC tags are the only durable discovery mechanism
- **Don't skip `wait_timeout`** on `execute_sql` — the default may not suit long-running statements
- **Don't disable workspace safeguards** (deletion protection, cluster policies) without explicit need
- **Don't store PATs in source code** — use `~/.databrickscfg` profiles or environment variables

## Troubleshooting

### Error: "The MCP server is disabled"
**Cause:** `mcp.json` has `"disabled": true` (default state ships disabled for safety).
**Solution:**
1. Complete the onboarding steps (see Configuration)
2. Set `"disabled": false` in `~/.kiro/settings/mcp.json` under the Power's `mcpServers.databricks` entry
3. Reload Kiro to reconnect the server

### Error: "Authentication failed" / "401 Unauthorized"
**Cause:** Profile in `~/.databrickscfg` is missing, expired, or doesn't match `DATABRICKS_CONFIG_PROFILE`.
**Solution:**
1. Run `databricks auth login --profile <name>` to refresh OAuth
2. Or update `mcp.json` to use explicit `DATABRICKS_HOST` + `DATABRICKS_TOKEN` env vars
3. Verify with `get_current_user` — it should return a valid user

### Error: "Warehouse not running" / "Cluster not running"
**Cause:** Compute is stopped; `execute_sql` / `execute_code` requires a running compute.
**Solution:**
1. Use `manage_sql_warehouse` (action: start) or `manage_cluster` (action: start)
2. Or rely on serverless warehouses — they auto-start on first query
3. Re-run the original tool call

### Error: "Permission denied on UC object"
**Cause:** The authenticated user lacks the required UC privilege.
**Solution:**
1. Use `manage_uc_grants` (action: list) to inspect current grants
2. Have a metastore admin grant the missing privilege
3. Confirm `USE CATALOG` and `USE SCHEMA` are also granted (often forgotten)

### Error: "Pipeline failed with EXPECTATION_VIOLATED"
**Cause:** A DLT expectation rejected rows.
**Solution:**
1. Inspect pipeline events with `manage_pipeline_run` (action: get_update)
2. Loosen `EXPECT` constraints or move to `EXPECT ... ON VIOLATION DROP ROW` if the data is genuinely dirty
3. Check upstream sources for schema drift

### Error: "Installer ran but `~/.ai-dev-kit/.venv/bin/python` is missing"
**Cause:** Installer non-zero exit can be misleading; sometimes the genuine failure is a missing prerequisite.
**Solution:**
1. Verify `uv` and `git` are installed and on `PATH`
2. Re-run with `--force` and watch for the line that mentions `uv venv` failing
3. Check disk space in `$HOME`

### Warning: "SKILL.md not for skill: …databricks-app-apx/SKILL.md"
**Cause:** The upstream `databricks-solutions/apx` repository ships `SKILL.md` with a frontmatter `name:` field (`apx`) that doesn't match the directory name (`databricks-app-apx`) the installer creates. Kiro flags the mismatch but loads the skill anyway.
**Impact:** None — the skill is functional, just registered under a different internal name. The warning is cosmetic.
**Solution:** No action needed. Patching the local file isn't durable (the next skill update overwrites it). The proper fix is upstream: file an issue at https://github.com/databricks-solutions/apx requesting the frontmatter `name:` field be aligned with the distributed directory name.

## Configuration

### Prerequisites

- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **git** — Version control
- **Databricks workspace** — AWS, Azure, or GCP
- **Databricks CLI** (optional, for OAuth login) — [install](https://docs.databricks.com/en/dev-tools/cli/install.html)
- **jq** (recommended) — Steps 2.5 / 2.6 / 2.7 below use `jq` for idempotent `mcp.json` edits. Each step also includes a non-`jq` fallback, but installing `jq` (`brew install jq` on macOS, `apt install jq` on Linux) makes the onboarding flow fully scriptable.

### Install at a glance

The flow has three install-bug workarounds (Steps 2.5 / 2.6 / 2.7) that look optional but aren't — every fresh Kiro install of this Power hits at least one of them today. Skim this checklist before starting so the ordering is clear:

| Step | What it does | Why it's there |
|------|--------------|----------------|
| 1 | Snapshot `~/.kiro/skills`, then run the official installer | Snapshot lets Step 2 know exactly which skills the installer added |
| 2 | Diff the post-install state, write a `.skill-manifest.txt`, move skills into the Power's `steering/` directory | Manifest-driven move beats glob-based cleanup — safe with upstream additions and other tools |
| 2.5 | Add the top-level `mcpServers` key to `~/.kiro/settings/mcp.json` if missing | Kiro's schema requires it; fresh installs error out without this |
| 2.6 | Remove the standalone `mcpServers.databricks` entry the installer writes | Otherwise Kiro launches two copies of the same MCP server |
| 2.7 | Expand `~` to `$HOME` in the Power's `command` and `args` paths | Node's `spawn()` doesn't expand `~` — server fails with `ENOENT` if you skip this |
| 3 | Configure authentication (Options A → D; Option A = OAuth U2M recommended for interactive) | Power ships `disabled: true` until you pick a method |
| 4 | Smoke-test the connection with `get_current_user` | Verifies auth + env-var resolution + server enablement in one call |

### Step 1: Run the Official Installer (with pre-snapshot)

The installer pulls skills from **four upstream sources** (`databricks-solutions/ai-dev-kit/databricks-skills/`, `mlflow/skills/`, `databricks-solutions/apx/`, `databricks/databricks-agent-skills/`) and writes them into `~/.kiro/skills/`. To track exactly which skills this Power is responsible for — so we can move them precisely in Step 2 and clean them up precisely on uninstall — snapshot the directory **before** the installer runs.

```bash
# Snapshot the pre-install state (empty list is fine if the directory doesn't exist yet)
mkdir -p "$HOME/.kiro/skills"
ls -1 "$HOME/.kiro/skills" 2>/dev/null | sort > /tmp/kiro-skills-before.txt

# Run the installer
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --silent
```

> The installer may exit non-zero even on success. Verify with:
> ```bash
> ls ~/.ai-dev-kit/.venv/bin/python && ls ~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py && ls ~/.kiro/skills/ | head -5
> ```

**Installer flags:**
- `--tools kiro` — Configure for Kiro only
- `--global` — Install skills to `~/.kiro/skills/` and MCP config to `~/.kiro/settings/mcp.json`
- `--silent` — Non-interactive (defaults: all skills, DEFAULT profile)
- `--profile PROFILE_NAME` — Use a specific Databricks CLI profile
- `--force` — Reinstall even if up to date
- `--skills-only` — Skip MCP server setup

### Step 2: Build a Manifest, Then Copy Skills to the Power's Steering Directory

Use the pre-install snapshot from Step 1 to compute exactly which skill directories the installer added. Persist that list as a manifest inside the Power's installed directory so future updates and the uninstall flow operate on the exact same set of files (no glob guessing, no leftover skills, no accidental deletion of unrelated files).

**Agent execution note:** Run the bash block below as a single inline `bash -c '...'` invocation. Do **not** write it to a scratch file like `/tmp/kiro-step2.sh` first — Kiro's sandbox blocks `Write`-tool writes to `/tmp/`, even though shell-internal redirects (e.g., `> /tmp/kiro-skills-after.txt` *from inside* `bash -c`) are allowed. Skipping the file-write attempt avoids a noisy "Access denied" error and lets execution succeed on the first try.

```bash
POWER_DIR="$HOME/.kiro/powers/installed/databricks"
POWER_STEERING="$POWER_DIR/steering"
MANIFEST="$POWER_DIR/.skill-manifest.txt"

# Snapshot post-install state
ls -1 "$HOME/.kiro/skills" 2>/dev/null | sort > /tmp/kiro-skills-after.txt

# Compute the diff: skills that exist now but didn't before. This is what the installer added.
comm -13 /tmp/kiro-skills-before.txt /tmp/kiro-skills-after.txt > "$MANIFEST.tmp"

# Reset the steering directory and write the manifest
rm -rf "$POWER_STEERING"
mkdir -p "$POWER_STEERING"
mv "$MANIFEST.tmp" "$MANIFEST"

# Copy each manifested skill into the Power's steering directory, then delete the original
while IFS= read -r skill; do
  [ -z "$skill" ] && continue
  src="$HOME/.kiro/skills/$skill"
  if [ -e "$src" ]; then
    cp -r "$src" "$POWER_STEERING/$skill"
    rm -rf "$src"
  fi
done < "$MANIFEST"

# Clean up scratch files
rm -f /tmp/kiro-skills-before.txt /tmp/kiro-skills-after.txt

echo "Installed $(wc -l < "$MANIFEST" | tr -d ' ') skills to $POWER_STEERING"
echo "Manifest saved to $MANIFEST"
```

**Why this is more robust than glob-based cleanup:**

- The manifest captures the **exact** set of skills the installer wrote, regardless of upstream naming conventions or new skill sources added later
- Uninstall and update flows can replay the manifest to remove or refresh only what the Power owns — no risk of deleting skills installed by other tools
- The manifest is human-readable; you can `cat ~/.kiro/powers/installed/databricks/.skill-manifest.txt` to audit what the Power is responsible for

**Edge case — incremental reinstall:** if `comm -13` returns an empty manifest (e.g., you re-ran Step 1 without first removing `~/.kiro/skills/`), the installer detected the skills were already installed and skipped them. In that case, regenerate the manifest from the existing steering directory:

```bash
ls -1 "$POWER_STEERING" 2>/dev/null | sort > "$MANIFEST"
```

This scopes skills to the Power (loaded only when the Power is active) and removes duplicates from the global skills namespace. Click **Update** on the Databricks Power in Kiro afterward to refresh the steering files list.

### Step 2.5: Ensure `~/.kiro/settings/mcp.json` Schema is Valid

> **⚠️ Agent behavior (REQUIRED):** Kiro's user-level `mcp.json` schema requires a **top-level `mcpServers` key** to exist (even if empty) alongside the `powers` block. After a fresh install of just this Power, that top-level key may be missing, and Kiro will surface this error:
>
> ```
> Invalid mcp.json format in user directory:
> [{ "code": "invalid_type", "expected": "object", "received": "undefined",
>    "path": ["mcpServers"], "message": "Required" }]
> ```
>
> Before proceeding to Step 3, the agent MUST check `~/.kiro/settings/mcp.json` and fix it if needed.

**Three cases to handle:**

**Case 1 — File does not exist.** Create it with the minimum valid shape:
```json
{
  "mcpServers": {},
  "powers": {
    "mcpServers": {}
  }
}
```

**Case 2 — File exists but the top-level `mcpServers` key is missing.** This is the usual post-install state. Add the key without disturbing anything else:

*Before:*
```json
{
  "powers": {
    "mcpServers": {
      "power-databricks-databricks": { ... }
    }
  }
}
```

*After:*
```json
{
  "mcpServers": {},
  "powers": {
    "mcpServers": {
      "power-databricks-databricks": { ... }
    }
  }
}
```

**Case 3 — Top-level `mcpServers` already exists** (e.g., the ai-dev-kit installer wrote its own `databricks` entry there, or another Power did). Leave it alone — schema is already valid. Proceed to Step 2.6.

**Idempotent fix command** (Unix; uses `jq` if available, otherwise prints instructions):

```bash
MCP_CFG="$HOME/.kiro/settings/mcp.json"

if [ ! -f "$MCP_CFG" ]; then
  mkdir -p "$(dirname "$MCP_CFG")"
  printf '%s\n' '{' '  "mcpServers": {},' '  "powers": { "mcpServers": {} }' '}' > "$MCP_CFG"
  echo "Created $MCP_CFG with minimum valid shape."
elif command -v jq >/dev/null 2>&1; then
  if ! jq -e '.mcpServers' "$MCP_CFG" >/dev/null 2>&1; then
    tmp=$(mktemp)
    jq '. + {mcpServers: (.mcpServers // {})}' "$MCP_CFG" > "$tmp" && mv "$tmp" "$MCP_CFG"
    echo "Added top-level mcpServers: {} to $MCP_CFG."
  else
    echo "Top-level mcpServers already present — no changes needed."
  fi
else
  echo "jq not installed. Open $MCP_CFG and ensure the top-level object contains a 'mcpServers' key (use {} if you have no top-level MCP servers)."
fi
```

After fixing, reload Kiro to clear the validation error before continuing to Step 2.6.

### Step 2.6: Remove the Standalone `databricks` Entry the Installer Wrote

> **⚠️ Agent behavior (REQUIRED):** Step 1's installer (`install.sh`) writes a top-level `mcpServers.databricks` entry to `~/.kiro/settings/mcp.json`. That entry was designed for users running ai-dev-kit *without* a Kiro Power — for our flow it is a duplicate registration of the same MCP server the Power owns. Leaving both entries in place causes Kiro to launch two copies of the server (same binary, two different env blocks), which can confuse tool routing.
>
> The agent MUST delete the top-level `mcpServers.databricks` entry after the installer runs, leaving only the Power's entry under `powers.mcpServers.power-databricks-databricks`.

**Idempotent fix command:**

```bash
MCP_CFG="$HOME/.kiro/settings/mcp.json"

if command -v jq >/dev/null 2>&1; then
  if jq -e '.mcpServers.databricks' "$MCP_CFG" >/dev/null 2>&1; then
    tmp=$(mktemp)
    jq 'del(.mcpServers.databricks)' "$MCP_CFG" > "$tmp" && mv "$tmp" "$MCP_CFG"
    echo "Removed standalone mcpServers.databricks entry."
  else
    echo "No standalone entry to remove — already clean."
  fi
else
  echo "jq not installed. Open $MCP_CFG and delete the 'mcpServers.databricks' object manually, leaving 'mcpServers' as {} or with other entries you intentionally configured."
fi
```

**Before:**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "/Users/<you>/.ai-dev-kit/.venv/bin/python",
      "args": ["/Users/<you>/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "defer_loading": true,
      "env": { "DATABRICKS_CONFIG_PROFILE": "DEFAULT" }
    }
  },
  "powers": {
    "mcpServers": {
      "power-databricks-databricks": { ... }
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {},
  "powers": {
    "mcpServers": {
      "power-databricks-databricks": { ... }
    }
  }
}
```

Reload Kiro to drop the now-removed standalone server connection. The Power's entry under `powers.mcpServers` is the one that runs from here on.

> **If you have OTHER MCP servers** (not `databricks`) under top-level `mcpServers` that you intentionally configured for non-Power use, the `jq` snippet above leaves them alone — it only removes the `databricks` key.

### Step 2.7: Expand `~` in the Power's `command` and `args` Paths

> **⚠️ Agent behavior (REQUIRED):** The Power's bundled `mcp.json` ships with `~/.ai-dev-kit/...` paths (tilde for the user's home directory). Kiro copies these paths verbatim into `~/.kiro/settings/mcp.json` under `powers.mcpServers.power-databricks-databricks`. **Node's `child_process.spawn()` does not expand `~`** — it looks for a literal directory named `~`, which doesn't exist, and the MCP server fails to launch with:
>
> ```
> Error connecting to MCP server: spawn ~/.ai-dev-kit/.venv/bin/python ENOENT
> ```
>
> The agent MUST replace `~` with the absolute home path in both `command` and every entry in `args` before the server can launch.

**Idempotent fix command:**

```bash
MCP_CFG="$HOME/.kiro/settings/mcp.json"
HOME_PATH="$HOME"

if command -v jq >/dev/null 2>&1; then
  tmp=$(mktemp)
  jq --arg h "$HOME_PATH" '
    if .powers.mcpServers["power-databricks-databricks"] then
      .powers.mcpServers["power-databricks-databricks"].command |= ($h + (.|ltrimstr("~"))) |
      .powers.mcpServers["power-databricks-databricks"].args    |= map($h + (.|ltrimstr("~")))
    else . end
  ' "$MCP_CFG" > "$tmp" && mv "$tmp" "$MCP_CFG"
  echo "Expanded ~ to $HOME_PATH in command and args."
else
  echo "jq not installed. Open $MCP_CFG and replace ~/.ai-dev-kit/... with $HOME/.ai-dev-kit/... in both 'command' and every entry of 'args'."
fi
```

**Before:**
```json
"command": "~/.ai-dev-kit/.venv/bin/python",
"args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"]
```

**After** (assuming `$HOME = /Users/<you>`):
```json
"command": "/Users/<you>/.ai-dev-kit/.venv/bin/python",
"args": ["/Users/<you>/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"]
```

The transformation is per-user (your `$HOME` ends up baked in), so this fix has to run on each developer's machine — it can't be pre-applied in the bundled file.

Verify the binaries exist at the expanded paths:

```bash
ls -la "$HOME/.ai-dev-kit/.venv/bin/python"
ls -la "$HOME/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"
```

If either is missing, Step 1's installer didn't complete — re-run it. Otherwise, reload Kiro; the `ENOENT` error should clear.

### Step 3: Configure Authentication

The Power ships with a baseline `mcp.json` that uses an env-var reference for the profile name and is **disabled by default** for safety. Pick one of the four options below and apply the matching "after" configuration.

> **⚠️ Agent behavior during onboarding (REQUIRED):**
>
> Before configuring or modifying any credentials, the agent MUST:
>
> 1. **Check for existing credentials** in two locations:
>    - The top-level `mcpServers` block in `~/.kiro/settings/mcp.json` (e.g., from a prior installation or another Databricks-using Power)
>    - Profiles in `~/.databrickscfg`
> 2. **Show the user enough to identify the credentials, but never the full secret.** The user needs to recognize *which* credential they are looking at — show identifiers and short prefix/suffix fingerprints — but the bulk of the secret must not be echoed.
>
>    | Display this | Hide this |
>    |---|---|
>    | Profile name (e.g., `[DEFAULT]`, `[prod-aws]`) | — |
>    | Workspace host URL | — |
>    | `auth_type` field value | — |
>    | `client_id` (full — it's a public identifier) | `client_secret` (only first 4 + last 4 chars; never the middle) |
>    | PAT in the form `dapi` + 4 chars + `***` + last 4 chars (e.g., `dapi5f2a***4f2c`), plus token comment if present | The middle of the PAT |
>    | OAuth secret first 4 + `***` + last 4 chars (e.g., `abcd***9z8y`), plus last-modified date if known | The middle of the secret |
>    | OAuth U2M `auth_type = databricks-cli` label only | Cached access/refresh tokens from `~/.databricks/token-cache.json` |
>
>    Preserving the `dapi` prefix on PATs makes the token type unmistakable; the 4-char fingerprints on either side are enough for the user to recognize a credential they generated themselves (matching it against their notes or a credential manager) without exposing usable token material.
>
> 3. **Ask for explicit confirmation** before reusing detected credentials. Offer three choices:
>    - Reuse the detected credentials for this Power
>    - Configure a different authentication option (A / B / C / D below) — **default recommendation is Option A (OAuth U2M)** for interactive use; auto-refreshes hourly and avoids the long-lived-secret expiry that PATs and OAuth M2M secrets eventually hit
>    - Skip — the user will edit `mcp.json` themselves
>
>    If **no credentials at all** are detected, skip the "reuse" choice and walk the user directly through Option A (OAuth U2M) unless they explicitly ask for a different option.
> 4. **Never copy credentials between configurations without explicit user approval.** Silent reuse is not acceptable, even when the credentials appear identical or compatible.
> 5. **Present the choices neutrally.** Do not label any option as "recommended", "quickest", or "easiest" — credential reuse is the user's decision on its merits, not the agent's recommendation.
> 6. **Always present all four options in A → B → C → D order**, even when no credentials are detected for a given option. Do **not** skip an option because detection found nothing for it — instead, show it with the "no credentials found, here's how to set up" path. Skipping options (e.g., showing only B/C/D, or A/C/D) makes the list look broken and confuses the user. The list must always read A, B, C, D — never B, C, D or A, B, D.
> 7. **On auth failure during a session, loop back to detection.** If a Databricks MCP tool returns `Invalid access token`, `401 Unauthorized`, `403 token expired`, or any equivalent auth-failure status, immediately pause tool execution and re-enter this detection flow. Do not retry the failed tool, attempt a silent token refresh, or guess at a fix. Surface the current credential summary and recommend Option A (OAuth U2M) as the first repair path.
>
> Example of an acceptable summary the agent shows the user:
> ```
> Found existing Databricks configuration:
>
>   ~/.kiro/settings/mcp.json (top-level mcpServers.databricks):
>     host        = https://<your-workspace>.cloud.databricks.com
>     auth method = OAuth U2M (via DATABRICKS_CONFIG_PROFILE=DEFAULT)
>
>   ~/.databrickscfg:
>     [DEFAULT]
>       host       = https://<your-workspace>.cloud.databricks.com
>       auth_type  = databricks-cli
>     [prod-aws]
>       host       = https://<your-workspace-prod>.cloud.databricks.com
>       auth_type  = pat
>       token      = dapi5f2a***4f2c     (dapi prefix + 4 + last 4)
>       comment    = "Power onboarding 2026-05-19"
>     [ci-sp]
>       host          = https://<your-workspace>.cloud.databricks.com
>       client_id     = 1a2b3c4d-5e6f-7890-abcd-ef1234567890
>       client_secret = abcd***9z8y    (first 4 + last 4 only)
>
> Would you like to:
>   1. Reuse the [DEFAULT] profile for this Power
>   2. Configure a different auth option (A / B / C / D below)
>   3. Skip — I'll edit mcp.json myself
> ```

#### Baseline (as shipped — before any configuration)

This is the file you'll find at `~/.kiro/powers/installed/databricks/mcp.json` immediately after installation. The `${DATABRICKS_CONFIG_PROFILE}` reference is resolved from your shell environment when Kiro launches the server.

```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": true
    }
  }
}
```

> All four options below modify the **runtime** MCP config at `~/.kiro/settings/mcp.json` (under `powers.mcpServers.power-databricks-databricks`), not the bundled file above. Kiro mirrors the bundled config there during Power activation.
>
> **Where credentials are read from:** the MCP server reads its environment from the `env` block of `mcp.json` at the moment Kiro launches it. Pick the option whose env block matches the credentials you have, then edit `mcp.json` directly.

#### Recommended setup before you pick an option: a multi-environment `~/.databrickscfg`

The cleanest long-term setup is to keep **all** your Databricks credentials in one place: `~/.databrickscfg`. Every Databricks tool on your machine — the CLI, Terraform provider, VS Code extension, local notebooks, this Power — reads the same file, so you set it up once and get a consistent identity everywhere. Switching environments becomes a one-line shell change (`export DATABRICKS_CONFIG_PROFILE=u2m-prod`) instead of editing `mcp.json` every time.

Use a naming convention that encodes both the environment **and** the auth method, so it's obvious what each profile does at a glance: `<auth>-<env>` (e.g., `u2m-dev`, `m2m-dev`, `pat-dev`, then the same for `qa` and `prod`).

**Step-by-step:**

1. **Create your U2M profiles first** with `databricks auth login` — one per environment. The CLI writes the `[u2m-*]` blocks for you:
   ```bash
   databricks auth login --host https://<dev-workspace>.cloud.databricks.com  --profile u2m-dev
   databricks auth login --host https://<qa-workspace>.cloud.databricks.com   --profile u2m-qa
   databricks auth login --host https://<prod-workspace>.cloud.databricks.com --profile u2m-prod
   ```

2. **Add M2M and PAT profiles by hand** if you need them. Open `~/.databrickscfg` in an editor and append blocks. The CLI does not write these for you.

3. **Lock the file down** so secrets aren't world-readable:
   ```bash
   chmod 600 ~/.databrickscfg
   ```

**Reference template** — fill in only the environments and auth methods you actually use:

```ini
# ~/.databrickscfg
# Naming: <auth>-<env>
# Auth methods: u2m (interactive), m2m (service principal), pat (legacy)

[u2m-dev]
host       = https://<dev-workspace>.cloud.databricks.com
auth_type  = databricks-cli

[u2m-qa]
host       = https://<qa-workspace>.cloud.databricks.com
auth_type  = databricks-cli

[u2m-prod]
host       = https://<prod-workspace>.cloud.databricks.com
auth_type  = databricks-cli

[m2m-dev]
host          = https://<dev-workspace>.cloud.databricks.com
client_id     = <dev-service-principal-application-id>
client_secret = <dev-oauth-secret>

[m2m-qa]
host          = https://<qa-workspace>.cloud.databricks.com
client_id     = <qa-service-principal-application-id>
client_secret = <qa-oauth-secret>

[m2m-prod]
host          = https://<prod-workspace>.cloud.databricks.com
client_id     = <prod-service-principal-application-id>
client_secret = <prod-oauth-secret>

[pat-dev]
host  = https://<dev-workspace>.cloud.databricks.com
token = dapi...

[pat-qa]
host  = https://<qa-workspace>.cloud.databricks.com
token = dapi...

[pat-prod]
host  = https://<prod-workspace>.cloud.databricks.com
token = dapi...
```

**Switching environments at runtime:**

```bash
export DATABRICKS_CONFIG_PROFILE=u2m-dev    # work in dev
# Kiro restart / MCP server reconnect

export DATABRICKS_CONFIG_PROFILE=u2m-prod   # switch to prod
# Kiro restart / MCP server reconnect
```

The Power's `mcp.json` env block stays exactly what ships by default — `{"DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"}` — and Option C (Existing profile) handles all three auth methods because the Databricks SDK reads the profile and picks the matching flow. Once `~/.databrickscfg` is set up, you rarely need to switch options.

**When you don't need this:**
- You only ever work against one Databricks workspace with one auth method → a single `[DEFAULT]` profile (or the env-var options below) is fine.
- You don't have permission to install/run `databricks auth login` and don't want to hand-write profiles → skip to Options B or D and use shell env vars directly.

**Quick reference (Databricks-recommended order):**

| Option | Method | Best for | Token lifetime | Status |
|--------|--------|----------|----------------|--------|
| A | OAuth U2M (CLI login) | Interactive use by a human | 1 h, auto-refreshed | Recommended |
| B | OAuth M2M (service principal) | Headless / CI/CD / production agents | 1 h access token; secret up to 730 days | Recommended |
| C | Existing `~/.databrickscfg` profile | You already have a working profile | Depends on the underlying auth in the profile | Recommended |
| D | Personal Access Token (PAT) | Tools that don't support OAuth | Up to 730 days; auto-revoked after 90 days unused | **Legacy** — Databricks recommends OAuth instead |

Reference: [PAT (legacy)](https://docs.databricks.com/aws/en/dev-tools/auth/pat) · [OAuth U2M](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m) · [OAuth M2M](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m)

---

#### Option A — OAuth U2M via Databricks CLI (recommended for interactive use)

OAuth user-to-machine: the Databricks CLI opens a browser, you authenticate as yourself, and credentials land in `~/.databrickscfg`. Each access token is valid for one hour and is auto-refreshed by the Databricks SDK. This is the safest interactive flow because there's no long-lived secret to leak.

> **Agent reuse-detection for Option A:** If `~/.databrickscfg` contains profiles with `auth_type = databricks-cli`, the agent MUST list each one with its host so the user can pick which to use, e.g.:
> ```
> Found OAuth U2M profiles in ~/.databrickscfg:
>   1. [DEFAULT]    host = https://<your-workspace>.cloud.databricks.com
>   2. [prod-aws]   host = https://<your-workspace-prod>.cloud.databricks.com
>   3. Run a fresh databricks auth login (creates a new profile)
> ```
> If no U2M profiles exist, say so explicitly and walk the user through `databricks auth login` below.

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com --profile DEFAULT
```

This writes a profile to `~/.databrickscfg` like:
```ini
[DEFAULT]
host       = https://<your-workspace>.cloud.databricks.com
auth_type  = databricks-cli
```

Then export the profile name in your shell so the `${DATABRICKS_CONFIG_PROFILE}` reference in `mcp.json` resolves correctly when Kiro launches the MCP server:

```bash
export DATABRICKS_CONFIG_PROFILE=DEFAULT
```

**Before** (`~/.kiro/settings/mcp.json` — Power entry as shipped):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": true
    }
  }
}
```

**After** (Option A applied):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": false
    }
  }
}
```

The only edit is `"disabled": true` → `"disabled": false`. The env reference and shell variable do the rest.

---

#### Option B — OAuth M2M with Service Principal (recommended for headless / CI/CD)

OAuth machine-to-machine: a Databricks service principal authenticates with `client_id` + `client_secret` and the SDK auto-issues 1-hour access tokens with no browser flow. Use this for production agents, scheduled jobs, and shared environments. Per Databricks docs, this is intended for *"unattended processes, such as automated CLI commands or REST API calls made from scripts or applications."*

> **Agent reuse-detection for Option B:** If `~/.databrickscfg` contains profiles with `client_id` set, or the shell environment has `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`, the agent MUST list each candidate with its `client_id` (full) and secret fingerprint so the user can recognize it, e.g.:
> ```
> Found OAuth M2M credentials:
>   1. ~/.databrickscfg [ci-sp]
>      host          = https://<your-workspace>.cloud.databricks.com
>      client_id     = 1a2b3c4d-5e6f-7890-abcd-ef1234567890
>      client_secret = abcd***9z8y     (first 4 + last 4 only)
>   2. Shell env DATABRICKS_CLIENT_ID
>      host          = https://<your-workspace>.cloud.databricks.com
>      client_id     = 9z8y7x6w-...-fedcba0987654321
>      client_secret = wxyz***1234     (first 4 + last 4 only)
>   3. Generate a new service principal + OAuth secret (steps below)
> ```
> If no M2M credentials are detected, say so explicitly and walk the user through the **Prerequisites** below.

**Prerequisites:**
1. **Create a service principal** in the Databricks account console (Identity and access → Service principals)
2. **Grant workspace entitlements and permissions** so the SP can do what you need
3. **Generate an OAuth secret** — Settings → Identity and access → Service principals → select SP → Secrets tab → Generate secret. Set lifetime up to 730 days (max). Copy `client_id` and `client_secret` immediately — the secret is shown only once. A service principal can have up to 5 active OAuth secrets.

Export the three environment variables in your shell so the `${VAR}` references in `mcp.json` resolve when Kiro launches the MCP server:

```bash
export DATABRICKS_HOST="https://<your-workspace>.cloud.databricks.com"
export DATABRICKS_CLIENT_ID="<service-principal-application-id>"
export DATABRICKS_CLIENT_SECRET="<oauth-secret>"
```

**Before** (as shipped):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": true
    }
  }
}
```

**After** (Option B applied — replace profile env with host + client credentials):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_HOST": "${DATABRICKS_HOST}",
        "DATABRICKS_CLIENT_ID": "${DATABRICKS_CLIENT_ID}",
        "DATABRICKS_CLIENT_SECRET": "${DATABRICKS_CLIENT_SECRET}"
      },
      "disabled": false
    }
  }
}
```

> **Never hardcode `client_secret`** in the JSON file. Reference it through `${DATABRICKS_CLIENT_SECRET}` and source it from a secret manager (HashiCorp Vault, AWS Secrets Manager, OS keychain) or environment-injection mechanism appropriate to your runtime.
>
> ai-dev-kit's MCP server README only documents PAT and profile auth, but the underlying Databricks SDK's unified-auth chain detects M2M credentials automatically — no MCP-server-side change required beyond the env block above.

---

#### Option C — Existing `~/.databrickscfg` Profile

If you already have a working profile (e.g., `prod-aws`) in `~/.databrickscfg` — set up earlier via `databricks auth login`, manual editing, or a configuration-management tool — just point the env reference at it. The underlying auth method (OAuth U2M, OAuth M2M, or PAT) is whatever the profile already uses.

> **Agent reuse-detection for Option C:** The agent MUST enumerate every profile in `~/.databrickscfg`, showing host, `auth_type`, and a credential fingerprint appropriate to the profile's auth method, so the user can pick one explicitly. Example:
> ```
> Profiles in ~/.databrickscfg:
>   1. [DEFAULT]
>      host       = https://<your-workspace>.cloud.databricks.com
>      auth_type  = databricks-cli       (OAuth U2M — no static credential)
>   2. [prod-aws]
>      host       = https://<your-workspace-prod>.cloud.databricks.com
>      auth_type  = pat
>      token      = dapi5f2a***4f2c     (dapi prefix + 4 + last 4)
>   3. [ci-sp]
>      host          = https://<your-workspace>.cloud.databricks.com
>      client_id     = 1a2b3c4d-5e6f-7890-abcd-ef1234567890
>      client_secret = abcd***9z8y     (first 4 + last 4 only)
> ```
> If `~/.databrickscfg` does not exist or has no profiles, the agent MUST say so explicitly and offer to switch the user to Option A.

```bash
export DATABRICKS_CONFIG_PROFILE=prod-aws
```

**Before** (as shipped):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": true
    }
  }
}
```

**After** (Option C applied — same env reference, just enable the server):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": false
    }
  }
}
```

> Per Databricks docs, *"Values in `.databrickscfg` take precedence over environment variables"* — so if your profile has a `host` set, that takes precedence over `DATABRICKS_HOST`.

---

#### Option D — Personal Access Token (legacy)

> **Databricks officially marks PAT as legacy.** From the docs: *"Where possible, Databricks recommends using OAuth instead of PATs for user account authentication because OAuth provides stronger security."* Use this only if Options A–C aren't available — for example, an automated tool that doesn't support OAuth and where you can't use a service principal.

> **Agent reuse-detection for Option D:** If `~/.databrickscfg` contains profiles with `token` set (or `auth_type = pat`), or the shell environment has `DATABRICKS_TOKEN`, or the top-level `mcpServers` block in `~/.kiro/settings/mcp.json` already has a PAT configured, the agent MUST list each candidate with its host and PAT fingerprint, e.g.:
> ```
> Found existing PATs:
>   1. ~/.kiro/settings/mcp.json (top-level mcpServers.databricks)
>      host  = https://<your-workspace>.cloud.databricks.com
>      token = dapi5f2a***4f2c     (dapi prefix + 4 + last 4)
>   2. ~/.databrickscfg [prod-aws]
>      host    = https://<your-workspace-prod>.cloud.databricks.com
>      token   = dapie8cf***84fc     (dapi prefix + 4 + last 4)
>      comment = "Power onboarding 2026-05-19"
>   3. Generate a new PAT (workspace UI steps below)
> ```
> If no PAT is detected, say so explicitly and walk the user through the **Generate a PAT in the workspace UI** steps below.

PATs are simple bearer tokens. **Constraints worth knowing:**
- Lifetime up to ~730 days (set at creation)
- *"Databricks automatically revokes PATs that haven't been used for 90 days"*
- Up to 600 PATs per workspace
- *"You can't use personal access tokens to automate Databricks account-level functionality"*

**Generate a PAT in the workspace UI:**
1. Top bar → username → Settings → Developer
2. Next to **Access tokens**, click **Manage** → **Generate new token**
3. Add a comment, set lifetime in days, optionally restrict scopes
4. Click **Generate** and copy the token immediately (it is shown only once)

Export the host and token in your shell so the `${VAR}` references in `mcp.json` resolve when Kiro launches the MCP server:

```bash
export DATABRICKS_HOST="https://<your-workspace>.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."
```

**Before** (as shipped):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_CONFIG_PROFILE": "${DATABRICKS_CONFIG_PROFILE}"
      },
      "disabled": true
    }
  }
}
```

**After** (Option D applied — replace profile env with host + token):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_HOST": "${DATABRICKS_HOST}",
        "DATABRICKS_TOKEN": "${DATABRICKS_TOKEN}"
      },
      "disabled": false
    }
  }
}
```

> **Never hardcode a PAT in the JSON file.** Always reference it through `${DATABRICKS_TOKEN}` and keep the secret in your shell environment, a secret manager, or your OS keychain.

### Step 4: Verify the Connection

After saving, Kiro auto-reconnects the MCP server. Verify by calling:

```javascript
usePower("databricks", "databricks", "get_current_user", {})
// Returns: { user_name: "...", workspace_url: "...", entitlements: [...] }
```

A successful response confirms auth, env-var resolution, and server enablement are all wired correctly.

### Updating Skills

Re-run the snapshot/installer/diff pattern from Steps 1 and 2 so the manifest gets regenerated with any newly-added or removed skills:

```bash
# 1. Snapshot the current Power-owned manifest as the "before" baseline
POWER_DIR="$HOME/.kiro/powers/installed/databricks"
ls -1 "$POWER_DIR/steering" 2>/dev/null | sort > /tmp/kiro-skills-before.txt

# 2. Re-run the installer in skills-only force-refresh mode
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --skills-only --force --silent

# 3. Re-run Step 2's diff-and-move snippet to refresh the manifest and steering directory
```

After updating, click **Update** on the Power in Kiro to pick up any new skills.

### Uninstalling Skills

The manifest makes uninstall surgical — only the skills this Power owns get removed:

```bash
POWER_DIR="$HOME/.kiro/powers/installed/databricks"
MANIFEST="$POWER_DIR/.skill-manifest.txt"

if [ -f "$MANIFEST" ]; then
  while IFS= read -r skill; do
    [ -z "$skill" ] && continue
    rm -rf "$HOME/.kiro/skills/$skill"
  done < "$MANIFEST"
fi

rm -rf "$POWER_DIR"
```

This will not touch skills installed by other tools or other Powers, even if they happen to share a name prefix.

## Tips

1. **Start with `get_current_user`** to verify your identity, workspace, and entitlements
2. **Use `list_compute` first** when you don't know warehouse/cluster IDs — never hardcode them
3. **Prefer `ask_genie` for ad-hoc questions** — it generates SQL and explanations in one shot
4. **Lean on the steering files** — each skill encodes idiomatic patterns and gotchas for its domain
5. **Use Asset Bundles (`databricks-bundles` skill)** for production-grade resource definitions over imperative tool calls
6. **Combine `manage_uc_objects` + `manage_uc_grants` + `manage_uc_tags`** in every table-creation flow
7. **Wait explicitly on long-running runs** with `run_now_and_wait` rather than polling
8. **Track and clean up** sandbox resources with `list_tracked_resources` / `delete_tracked_resource`
9. **Use `get_table_stats_and_schema`** before authoring transformations — schema-on-read surprises are common
10. **Keep `disabled: true` until onboarding is complete** — flip it only after auth is verified

## License, Trademarks, and Support

### Power packaging

This Power's manifest (`POWER.md`, `mcp.json`, `steering/`) is published by community contributors (see Contributors below) under the same license terms as the [kirodotdev/powers](https://github.com/kirodotdev/powers) catalog.

### Upstream Databricks AI Dev Kit

The MCP server and skills installed by this Power are sourced from the [databricks-solutions/ai-dev-kit](https://github.com/databricks-solutions/ai-dev-kit) repository and are subject to the [Databricks License](https://databricks.com/db-license-source). See ai-dev-kit's [LICENSE.md](https://github.com/databricks-solutions/ai-dev-kit/blob/main/LICENSE.md) and [NOTICE.txt](https://github.com/databricks-solutions/ai-dev-kit/blob/main/NOTICE.txt) for full terms and third-party attribution. Users accept those terms when they run the installer.

### Trademarks

"Databricks", "Databricks AI Dev Kit", "Unity Catalog", "Delta Lake", "Mosaic AI", "Agent Bricks", "Genie", "Lakebase", and other Databricks product names referenced in this Power are trademarks of Databricks, Inc., used here for descriptive purposes to identify the upstream product this Power integrates with. This Power is not authored, endorsed, or maintained by Databricks, Inc.; it is a community-published integration that calls Databricks's public installer.

"Amazon Web Services", "AWS", and "Kiro" are trademarks of Amazon.com, Inc. or its affiliates.

### Contributors

- **Antony Prasad Thevaraj** ([@antonyprasad-db](https://github.com/antonyprasad-db)) — Senior Specialist Solutions Architect, Databricks (AWS Partnership). Built the underlying **Databricks AI Dev Kit** (the MCP server, skills, and unified installer) at [databricks-solutions/ai-dev-kit](https://github.com/databricks-solutions/ai-dev-kit), including the Kiro IDE installer support in [PR #511](https://github.com/databricks-solutions/ai-dev-kit/pull/511) that this Power depends on. Authored the **v2 of this Power** for submission to the [kirodotdev/powers](https://github.com/kirodotdev/powers) catalog — adding the Agent First-Action Protocol (credential pre-flight + 401 recovery), the manifest-driven install/uninstall flow, the install-blocking `mcp.json` fixes (Steps 2.5 / 2.6 / 2.7), the SKILL.md naming-warning troubleshooting entry, and the Trademarks subsection.
- **Venkatavaradhan Viswanathan** ([@venkatavaradhanv](https://github.com/venkatavaradhanv)) — Senior Solutions Architect, AWS. Created the original wrapper Power around the Databricks AI Dev Kit at [venkatavaradhanv/databricks](https://github.com/venkatavaradhanv/databricks), packaging the catalog-ready `POWER.md`, the parametrized `mcp.json`, the four-option auth documentation (OAuth U2M / OAuth M2M / existing profile / PAT), and the security-conscious credential-detection onboarding flow (8 use-cases across the 4 auth options with safe fingerprinting rules).

### Support

- **Power packaging / installation issues** — [github.com/venkatavaradhanv/databricks/issues](https://github.com/venkatavaradhanv/databricks/issues)
- **MCP server, skills, or installer issues** — [github.com/databricks-solutions/ai-dev-kit/issues](https://github.com/databricks-solutions/ai-dev-kit/issues)
- **Databricks platform support** — [help.databricks.com](https://help.databricks.com)
- **Privacy** — [databricks.com/legal/privacynotice](https://www.databricks.com/legal/privacynotice)

---

**Package:** `databricks-solutions/ai-dev-kit` (`databricks-mcp-server`)
**Source:** [github.com/databricks-solutions/ai-dev-kit](https://github.com/databricks-solutions/ai-dev-kit)
**License:** [Databricks License](https://databricks.com/db-license-source)
**Connection:** Local Python process via `~/.kiro/settings/mcp.json`
