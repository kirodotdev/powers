# Databricks Power — Steering Files

This directory holds expert skill files that provide guidance for Databricks capabilities. Skills are loaded on-demand when the Power is activated.

## How Skills Get Here

Skills are installed by the official Databricks AI Dev Kit installer during onboarding:

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --silent
```

The installer downloads skills from the [ai-dev-kit repository](https://github.com/databricks-solutions/ai-dev-kit/tree/main/databricks-skills) and places them in this directory.

## Available Skill Categories

| Skill | Description |
|-------|-------------|
| databricks-spark-declarative-pipelines | Streaming tables, CDC, SCD Type 2, Auto Loader |
| databricks-jobs | Scheduled workflows, multi-task DAGs, serverless |
| databricks-aibi-dashboards | Interactive visualizations, KPIs, analytics |
| databricks-unity-catalog | Tables, volumes, governance, system tables |
| databricks-genie | Natural language data exploration |
| databricks-agent-bricks | Knowledge Assistants, Supervisor Agents |
| databricks-vector-search | Semantic search and RAG applications |
| databricks-model-serving | Deploy ML models and AI agents |
| databricks-mlflow-evaluation | Model evaluation, scoring, traces |
| databricks-app-python | Full-stack web applications |
| databricks-lakebase-provisioned | Managed PostgreSQL (provisioned) |
| databricks-lakebase-autoscale | Managed PostgreSQL (autoscale) |
| databricks-metric-views | Reusable business metrics |
| databricks-spark-structured-streaming | Kafka, stateful ops, stream joins |
| databricks-dbsql | SQL best practices, materialized views |
| databricks-iceberg | Iceberg tables, UniForm, interop |
| databricks-bundles | Databricks Asset Bundles |
| databricks-config | Workspace configuration |
| databricks-python-sdk | Python SDK patterns and examples |
| databricks-synthetic-data-gen | Synthetic data generation |
| databricks-zerobus-ingest | Zero-copy ingestion |
| databricks-ai-functions | AI functions, forecasting, document processing |
| databricks-app-apx | App frontend/backend patterns |
| databricks-unstructured-pdf-generation | PDF generation and upload |
| databricks-docs | Documentation search |
| mlflow-onboarding | MLflow getting started |
| instrumenting-with-mlflow-tracing | MLflow tracing instrumentation |
| querying-mlflow-metrics | Querying MLflow metrics |
| retrieving-mlflow-traces | Retrieving MLflow traces |
| searching-mlflow-docs | Searching MLflow documentation |
| analyze-mlflow-trace | Analyzing MLflow traces |
| analyze-mlflow-chat-session | Analyzing MLflow chat sessions |
| agent-evaluation | Agent evaluation patterns |
| spark-python-data-source | Custom Spark data sources |

## Skill Profiles

You can install a subset of skills using profiles:

- `all` — All 34+ skills (default)
- `data-engineer` — Pipelines, Spark, Jobs, Streaming
- `analyst` — Dashboards, SQL, Genie, Metrics
- `ai-ml-engineer` — Agents, RAG, Vector Search, MLflow
- `app-developer` — Apps, Lakebase, Deployment

## Updating Skills

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --skills-only --force --silent
```
