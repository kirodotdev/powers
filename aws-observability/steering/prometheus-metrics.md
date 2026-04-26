# Prometheus Metrics Steering File

## When to Use
Load this steering file when the user asks about:
- Querying Prometheus or AMP metrics
- PromQL queries (instant or range)
- Listing metrics in a Prometheus workspace
- Managing AMP workspaces
- Correlating Prometheus metrics with CloudWatch data

## Workflow

### Step 1: Identify the Workspace
If the user hasn't specified a workspace:
1. Use `GetAvailableWorkspaces` to list AMP workspaces
2. Present the available workspaces (ID, alias, status) and ask the user to select one

### Step 2: Understand the Query Intent
Determine what the user needs:
- **Instant query**: Current value of a metric → use `ExecuteQuery`
- **Range query**: Metric values over time → use `ExecuteRangeQuery`
- **Metric discovery**: What metrics are available → use `ListMetrics`
- **Server info**: Workspace configuration → use `GetServerInfo`

### Step 3: Execute the Query

#### Instant Queries
Use `ExecuteQuery` with:
- `workspace_id`: The AMP workspace ID
- `query`: The PromQL expression
- `time` (optional): Evaluation timestamp

Common PromQL patterns:
- `up` — Check target health
- `rate(http_requests_total[5m])` — Request rate
- `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` — P95 latency
- `sum by (namespace) (container_memory_usage_bytes)` — Memory by namespace

#### Range Queries
Use `ExecuteRangeQuery` with:
- `workspace_id`: The AMP workspace ID
- `query`: The PromQL expression
- `start`: Start time (ISO 8601)
- `end`: End time (ISO 8601)
- `step`: Resolution step (e.g., `1m`, `5m`, `1h`)

Choose step based on time range:
- Last hour → `1m` step
- Last day → `5m` step
- Last week → `1h` step

### Step 4: Present Results
- Format metric values clearly with labels
- For range queries, summarize trends (increasing, decreasing, stable)
- Highlight any anomalous values
- Suggest follow-up queries if patterns warrant deeper investigation

## Cross-Tool Correlation
When investigating issues, combine Prometheus data with other observability tools:
- Use CloudWatch Logs to find error details for metrics showing elevated error rates
- Use Application Signals to correlate Prometheus metrics with distributed traces
- Use CloudTrail to check for infrastructure changes that may explain metric shifts
