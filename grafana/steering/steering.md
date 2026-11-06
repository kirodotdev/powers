# Grafana MCP Server Steering Guide

This steering file covers the Grafana MCP server to query dashboards, data sources, alerts, and annotations.

## When to Use the Grafana MCP Server

Use Grafana MCP tools when you need to:
- **Query metrics**: Execute PromQL against Prometheus data sources
- **Search logs**: Execute LogQL against Loki data sources
- **Investigate alerts**: Check firing alerts and their conditions
- **Analyze dashboards**: Extract queries and configurations from existing dashboards
- **Correlate events**: Use annotations to mark and query deployment/incident events
- **Check health**: Verify data source connectivity and status

## Core Principles

### 1. Start with Dashboards
Existing dashboards contain curated queries built by your team. Search for relevant dashboards first, then extract and adapt their queries.

### 2. Use Label Selectors
Always filter with label matchers to scope queries:
```promql
# Good - scoped
rate(http_requests_total{service="api", namespace="production"}[5m])

# Bad - scans everything
rate(http_requests_total[5m])
```

### 3. Check Alerts First
When investigating issues, start with firing alerts - they often point directly to the problem.

---

## PromQL Reference

### Selectors

**Exact match:**
```promql
http_requests_total{service="api", method="GET"}
```

**Regex match:**
```promql
http_requests_total{service=~"api|web", status=~"5.."}
```

**Negative match:**
```promql
http_requests_total{service!="internal", status!~"2.."}
```

### Range Vectors and Functions

**rate()** - Per-second rate of increase (for counters):
```promql
rate(http_requests_total{service="api"}[5m])
```

**increase()** - Total increase over time range:
```promql
increase(http_requests_total{service="api"}[1h])
```

**irate()** - Instant rate (last two samples):
```promql
irate(http_requests_total{service="api"}[5m])
```

**Range vector intervals:**
- `[1m]` - 1 minute (high resolution, noisy)
- `[5m]` - 5 minutes (standard for rate calculations)
- `[15m]` - 15 minutes (smoother, less responsive)
- `[1h]` - 1 hour (trend analysis)

### Aggregation Operators

```promql
# Sum across all instances
sum(rate(http_requests_total[5m]))

# Average by label
avg by (service) (rate(http_requests_total[5m]))

# Count unique series
count by (namespace) (up)

# Top/bottom K
topk(5, rate(http_requests_total[5m]))
bottomk(3, up)

# Quantile across series
quantile(0.95, rate(http_requests_total[5m]))
```

**Aggregation functions:** sum, avg, min, max, count, stddev, stdvar, topk, bottomk, quantile, count_values, group

**Grouping:**
- `by (label1, label2)` - Keep only these labels
- `without (label1)` - Remove these labels, keep rest

### Histogram Queries

**Percentile from histogram:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service="api"}[5m]))
```

**Percentile by label:**
```promql
histogram_quantile(0.99, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
```

**Average from histogram:**
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Binary Operators

**Arithmetic:**
```promql
# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Memory usage percentage
container_memory_working_set_bytes / container_spec_memory_limit_bytes * 100
```

**Comparison (for alerting):**
```promql
# Services with error rate > 5%
(sum by (service) (rate(http_requests_total{status=~"5.."}[5m])) / sum by (service) (rate(http_requests_total[5m]))) > 0.05
```

**Vector matching:**
```promql
# Match on specific labels
metric_a{service="api"} / on(service) metric_b{service="api"}

# Ignore labels for matching
metric_a / ignoring(instance) group_left metric_b
```

### Common PromQL Patterns

**RED Method (Rate, Errors, Duration):**
```promql
# Rate (requests per second)
sum by (service) (rate(http_requests_total[5m]))

# Errors (error percentage)
sum by (service) (rate(http_requests_total{status=~"5.."}[5m])) / sum by (service) (rate(http_requests_total[5m])) * 100

# Duration (p95 latency)
histogram_quantile(0.95, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
```

**USE Method (Utilization, Saturation, Errors):**
```promql
# CPU Utilization
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Saturation
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Disk Errors
rate(node_disk_io_time_weighted_seconds_total[5m])
```

**Kubernetes-specific:**
```promql
# Pod CPU usage
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="production"}[5m]))

# Pod memory usage percentage
sum by (pod) (container_memory_working_set_bytes{namespace="production"}) / sum by (pod) (kube_pod_container_resource_limits{resource="memory", namespace="production"}) * 100

# Pod restart count
sum by (pod) (increase(kube_pod_container_status_restarts_total{namespace="production"}[1h]))

# Deployment replicas
kube_deployment_status_replicas_available{namespace="production"} / kube_deployment_spec_replicas{namespace="production"}
```

---

## LogQL Reference (Loki)

### Stream Selectors

```logql
{namespace="production", app="checkout"}
{job="varlogs", filename="/var/log/syslog"}
{cluster="prod-us-east-1", container=~"api|web"}
```

### Line Filters

```logql
{app="api"} |= "error"              # contains (case-sensitive)
{app="api"} |= `"status":500`       # contains with backtick quoting
{app="api"} != "healthcheck"         # does not contain
{app="api"} |~ "(?i)error|timeout"   # regex match (case-insensitive)
{app="api"} !~ "debug|trace"         # regex does not match
```

### Parsers

**JSON parser:**
```logql
{app="api"} | json | level="error" | status >= 400
{app="api"} | json | line_format "{{.timestamp}} [{{.level}}] {{.message}}"
```

**Logfmt parser:**
```logql
{app="api"} | logfmt | duration > 5s | method="POST"
```

**Regex parser:**
```logql
{app="nginx"} | regexp `(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+)"`
```

**Pattern parser:**
```logql
{app="nginx"} | pattern `<ip> - - [<timestamp>] "<method> <path> <_>" <status> <size>`
```

### Label Filters (after parsing)

```logql
{app="api"} | json | level="error"                    # exact match
{app="api"} | json | status >= 400                    # numeric comparison
{app="api"} | json | duration > 5s                    # duration comparison
{app="api"} | json | message =~ "timeout.*"           # regex match
{app="api"} | json | ip != "10.0.0.1"                 # not equal
```

### Metric Queries

**Count rate:**
```logql
sum by (level) (rate({app="api"} | json [5m]))
```

**Error count:**
```logql
sum(count_over_time({app="api"} |= "error" [1h]))
```

**Bytes rate:**
```logql
sum by (app) (bytes_rate({namespace="production"}[5m]))
```

**Quantile from logs:**
```logql
quantile_over_time(0.95, {app="api"} | json | unwrap duration [5m]) by (endpoint)
```

### Common LogQL Patterns

**Error investigation:**
```logql
{namespace="production", app="checkout"} |= "error" | json | line_format "{{.timestamp}} {{.level}} {{.message}}"
```

**Slow requests:**
```logql
{app="api"} | json | duration > 5s | line_format "{{.method}} {{.path}} took {{.duration}}"
```

**Error rate by service:**
```logql
sum by (app) (rate({namespace="production"} |= "error" [5m]))
```

---

## Alert Investigation Workflow

### Step 1: List Firing Alerts
```javascript
const alerts = usePower("grafana", "grafana", "list_alert_instances", {
  "state": "alerting"
})
```

### Step 2: Get Alert Rule Details
```javascript
const rule = usePower("grafana", "grafana", "get_alert_rule", {
  "uid": alerts[0].rule_uid
})
// Examine: conditions, thresholds, evaluation interval
```

### Step 3: Query the Underlying Metric
```javascript
const metric = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": rule.datasource_uid,
  "query": rule.condition_query,
  "from": "now-2h",
  "to": "now"
})
```

### Step 4: Check for Correlating Events
```javascript
const annotations = usePower("grafana", "grafana", "list_annotations", {
  "from": "now-4h",
  "to": "now",
  "tags": ["deployment", "incident"]
})
```

### Step 5: Check Related Logs
```javascript
const logs = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "loki-1",
  "query": "{service=\"affected-service\"} |= \"error\" | json",
  "from": "now-30m",
  "to": "now"
})
```

---

## Dashboard Analysis Workflow

### Extract Queries from Dashboards
1. Search for relevant dashboard
2. Get full dashboard JSON
3. Extract panel queries (targets[].expr for Prometheus)
4. Execute queries with current time range
5. Compare results with panel thresholds

### Dashboard JSON Structure
```json
{
  "panels": [
    {
      "title": "Request Rate",
      "type": "timeseries",
      "datasource": {"uid": "prometheus-1"},
      "targets": [
        {"expr": "rate(http_requests_total[5m])", "legendFormat": "{{service}}"}
      ],
      "fieldConfig": {
        "defaults": {"thresholds": {"steps": [{"value": 0}, {"value": 100, "color": "red"}]}}
      }
    }
  ]
}
```

---

## Time Range Best Practices

### Supported Formats
- Relative: `now-5m`, `now-1h`, `now-24h`, `now-7d`
- Absolute: `2024-01-15T10:00:00Z`
- Unix ms: `1705312800000`

### Recommended Ranges by Use Case
| Use Case | Range | Interval |
|----------|-------|----------|
| Active incident | now-15m to now-1h | 1m |
| Recent investigation | now-4h to now-6h | 5m |
| Daily patterns | now-24h | 15m |
| Weekly trends | now-7d | 1h |
| Capacity planning | now-30d | 6h |

### Rate() Window vs Time Range
- Time range < 1h → use `[1m]` or `[2m]` rate window
- Time range 1-6h → use `[5m]` rate window
- Time range 6-24h → use `[15m]` rate window
- Time range > 24h → use `[1h]` rate window

---

## Anti-Patterns

### ❌ DON'T: Query without label selectors
```promql
# Scans all series - very expensive
rate(http_requests_total[5m])

# Always scope with labels
rate(http_requests_total{service="api", namespace="production"}[5m])
```

### ❌ DON'T: Graph raw counters
```promql
# Wrong - counters only go up, resets look like drops
http_requests_total

# Correct - use rate() for counters
rate(http_requests_total[5m])
```

### ❌ DON'T: Use irate() for alerting
```promql
# Wrong - too volatile for alerts
irate(http_requests_total[5m]) > 100

# Correct - rate() is smoother
rate(http_requests_total[5m]) > 100
```

### ❌ DON'T: Forget le label in histogram_quantile
```promql
# Wrong - missing le in by clause
histogram_quantile(0.95, sum by (service) (rate(http_request_duration_seconds_bucket[5m])))

# Correct - must include le
histogram_quantile(0.95, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m])))
```

### ❌ DON'T: Mix instant and range vectors
```promql
# Wrong - can't add range vector to instant
http_requests_total + rate(http_requests_total[5m])

# Correct - both must be instant vectors
http_requests_total + increase(http_requests_total[5m])
```

---

## Troubleshooting

### No Data Returned
1. Check data source health: `get_datasource_health`
2. Verify label names: query `{__name__=~"http.*"}` to find metrics
3. Check time range - data may not exist in the queried window
4. Verify label values: `label_values(metric_name, label_name)`

### Query Timeout
1. Narrow time range
2. Add more label selectors
3. Reduce cardinality in `by` clause
4. Use recording rules for expensive queries
5. Increase step interval

### Unexpected Results
1. Check if metric is counter vs gauge (use rate() for counters)
2. Verify label matching in binary operations
3. Check for stale series with `up` metric
4. Verify histogram bucket boundaries

---

## Summary Checklist

Before querying Grafana:
- ✅ Search existing dashboards for relevant queries
- ✅ Check data source health before debugging empty results
- ✅ Use label selectors to scope all queries
- ✅ Apply rate() to counter metrics
- ✅ Include `le` label when using histogram_quantile
- ✅ Start with short time ranges (1h) and expand
- ✅ Check firing alerts for active issues
- ✅ Use annotations to correlate with deployments
- ✅ Match rate window to time range appropriately

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `GRAFANA_API_KEY` or `GRAFANA_URL` values in responses
- When referencing credentials, use placeholder names only
- Do not include service account tokens in annotations, dashboard descriptions, or query results

### Query Scope Restrictions
- **Always use label selectors** in PromQL/LogQL - never run unscoped queries that scan all series
- **Do not query admin API endpoints** unless explicitly requested
- **Log queries may return sensitive data** - Loki logs can contain secrets, tokens, or PII; summarize patterns rather than reproducing raw log lines
- When presenting log results, scan for and avoid reproducing patterns that look like API keys, passwords, or tokens

### Data Sensitivity
- Dashboard configurations may contain sensitive data source URLs, query patterns, or internal service names
- Do not expose internal Grafana URLs, data source connection strings, or authentication details
- Annotation text may contain incident details - treat as potentially sensitive
- Alert rule configurations may reveal infrastructure thresholds and SLO targets - treat as internal information

### Access Control
- Only access dashboards and data sources the configured service account has permissions for
- Do not attempt to enumerate users, teams, or organization settings
- If an operation returns 403/401, report the error without retrying with different credentials
- Do not attempt to modify alert rules, notification channels, or data source configurations without explicit user approval
- Respect folder-level permissions - some dashboards may be restricted

## Anti-Hallucination Guardrails

### Query Accuracy
- **Only use valid PromQL syntax** - do not invent functions or operators. Valid aggregation operators: `sum`, `avg`, `min`, `max`, `count`, `stddev`, `stdvar`, `topk`, `bottomk`, `quantile`, `count_values`, `group`
- **Only use valid LogQL syntax** - do not invent parsers or filter operators. Valid parsers: `json`, `logfmt`, `regexp`, `pattern`, `unpack`
- **Do not fabricate metric names** - if unsure whether a metric exists, suggest querying `{__name__=~".*keyword.*"}` to discover metrics
- **Do not fabricate label names or values** - suggest using `label_values(metric, label)` to discover available labels
- **Do not invent dashboard UIDs** - always search for dashboards first

### Result Interpretation
- **Never invent query results** - if a query hasn't been run, say "I need to query this" rather than guessing
- **Do not assume metric behavior** - verify whether a metric is a counter, gauge, or histogram before applying functions
- **Clearly distinguish between observed data and inference** - prefix interpretations with "This suggests..." or "This may indicate..."
- **If a query returns no data**, report that clearly and suggest checking data source health or label selectors
- **Do not extrapolate trends** beyond the queried time range without explicitly stating the assumption

### Tool Capability Boundaries
- Do not claim ability to create or modify dashboards - verify tool capabilities first
- Do not claim ability to silence alerts or modify notification channels
- Do not claim ability to configure data sources or manage users
- Clearly state when an action requires the user to perform it in the Grafana UI

## Operational Optimization Guardrails

### Query Performance
- **Always use label selectors** - unscoped queries like `http_requests_total` scan all series and are extremely expensive
- **Match rate() window to time range:**
 - Time range < 1h → `[1m]` or `[2m]`
 - Time range 1-6h → `[5m]`
 - Time range 6-24h → `[15m]`
 - Time range > 24h → `[1h]`
- **Use recording rules when available** - pre-computed metrics are much faster than raw queries
- **Limit cardinality in `by` clauses** - avoid grouping by high-cardinality labels (e.g., `pod`, `instance`) unless necessary
- **Use `topk()` or `bottomk()`** instead of returning all series when only extremes matter

### Rate Limiting
- **Space queries apart** - do not fire many queries in rapid succession
- **Combine related queries** when possible - use PromQL binary operators to compute ratios in a single query
- **Cache dashboard UIDs and data source UIDs** - don't re-search for them repeatedly
- If rate-limited, wait before retrying and inform the user

### Resource Efficiency
- **Start with short time ranges** (1h) and expand only if needed
- **Use `step` parameter** appropriately - higher step = fewer data points = faster queries
- **Prefer instant queries** over range queries when you only need the current value
- **Avoid `{__name__=~".*"}` patterns** - they scan all metrics and are extremely expensive
- **Use LogQL metric queries** (`rate`, `count_over_time`) instead of fetching raw logs when you only need counts

## Cost Optimization Guardrails

### Query Cost Awareness
- **Grafana Cloud charges based on active series and query volume** - be mindful of query frequency
- **Longer time ranges with high resolution are expensive** - use appropriate step intervals
- **High-cardinality queries are expensive** - avoid `by (pod)` on large clusters unless necessary
- **Log queries are charged by volume scanned** - always use label selectors and line filters to reduce scan scope

### Query Planning
- **Plan before querying** - determine what information is needed and write the minimum number of queries
- **Reuse dashboard queries** - extract PromQL from existing dashboards rather than writing from scratch
- **Use annotations for context** - check existing annotations before querying for deployment/incident correlation
- **Avoid redundant queries** - if you already have the data, reference it rather than re-querying

### Dashboard Efficiency
- When analyzing dashboards, extract the most relevant panel queries rather than running all of them
- Suggest recording rules for expensive queries that are run frequently
- Recommend appropriate retention periods - not all metrics need long-term storage
- Suggest using Grafana's query caching features for frequently-accessed dashboards
