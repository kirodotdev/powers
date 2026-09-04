# New Relic MCP Server Steering Guide

This steering file covers the New Relic MCP server to query application performance, infrastructure metrics, logs, distributed traces, and alerts using NRQL.

## When to Use the New Relic MCP Server

Use New Relic MCP tools when you need to:
- **Investigate errors**: Find error rates, stack traces, and affected transactions
- **Analyze performance**: Response times, throughput, and bottlenecks
- **Monitor infrastructure**: CPU, memory, disk, and network metrics
- **Search logs**: Find application and infrastructure log entries
- **Trace requests**: Follow distributed traces across services
- **Check alerts**: View active incidents and alert conditions
- **Compare deployments**: Before/after analysis with COMPARE WITH

## Core Principles

### 1. Start with Golden Signals
Always check the four golden signals first:
- **Latency** - Response time (average, p95, p99)
- **Traffic** - Request rate (throughput)
- **Errors** - Error rate percentage
- **Saturation** - Resource utilization (CPU, memory)

### 2. Use FACET for Breakdown
Break down metrics by dimensions to identify specific problems:
```sql
SELECT average(duration) FROM Transaction FACET name SINCE 1 hour ago
```

### 3. Use TIMESERIES for Trends
Visualize patterns over time to identify when issues started:
```sql
SELECT average(duration) FROM Transaction SINCE 4 hours ago TIMESERIES 5 minutes
```

---

## NRQL Reference

### Query Structure
```sql
SELECT <function>(<attribute>)
FROM <event_type>
WHERE <condition>
FACET <attribute>
SINCE <time>
UNTIL <time>
TIMESERIES <bucket>
LIMIT <count>
COMPARE WITH <time>
```

### Event Types

| Event Type | Description | Key Attributes |
|-----------|-------------|----------------|
| `Transaction` | APM transactions | duration, name, appName, host, httpResponseCode, error |
| `TransactionError` | Application errors | error.class, error.message, transactionName, appName |
| `Span` | Distributed trace spans | duration, service.name, name, error.message, traceId |
| `Log` | Log entries | message, level, service, hostname, timestamp |
| `SystemSample` | Host metrics | cpuPercent, memoryUsedPercent, diskUsedPercent, hostname |
| `NetworkSample` | Network metrics | receiveBytesPerSecond, transmitBytesPerSecond |
| `ProcessSample` | Process metrics | cpuPercent, memoryResidentSizeBytes, commandName |
| `ContainerSample` | Container metrics | cpuPercent, memoryUsageBytes, containerName |
| `K8sContainerSample` | K8s containers | cpuUsedCores, memoryWorkingSetBytes, podName |
| `K8sPodSample` | K8s pods | status, podName, namespace, clusterName |
| `PageView` | Browser page views | duration, pageUrl, userAgentName, city |
| `JavaScriptError` | Frontend errors | errorMessage, pageUrl, browserInteractionName |
| `SyntheticCheck` | Synthetic monitors | duration, monitorName, result, locationLabel |
| `Metric` | Dimensional metrics | Various (use with WHERE/FACET) |
| `NrAiIncident` | Alert incidents | priority, conditionName, policyName, state |

### Aggregation Functions

| Function | Description | Example |
|----------|-------------|---------|
| `count(*)` | Count events | `SELECT count(*) FROM Transaction` |
| `average(attr)` | Mean value | `SELECT average(duration) FROM Transaction` |
| `sum(attr)` | Total | `SELECT sum(databaseDuration) FROM Transaction` |
| `min(attr)` / `max(attr)` | Extremes | `SELECT max(duration) FROM Transaction` |
| `percentile(attr, N)` | Nth percentile | `SELECT percentile(duration, 95) FROM Transaction` |
| `rate(count(*), 1 minute)` | Rate per time | `SELECT rate(count(*), 1 minute) FROM Transaction` |
| `uniqueCount(attr)` | Distinct values | `SELECT uniqueCount(host) FROM Transaction` |
| `percentage(count(*), WHERE cond)` | Percentage | `SELECT percentage(count(*), WHERE error IS true)` |
| `filter(func, WHERE cond)` | Filtered agg | `SELECT filter(count(*), WHERE duration > 1)` |
| `latest(attr)` | Most recent | `SELECT latest(cpuPercent) FROM SystemSample` |
| `earliest(attr)` | Oldest | `SELECT earliest(version) FROM Transaction` |
| `histogram(attr, width, count)` | Distribution | `SELECT histogram(duration, 0.1, 20) FROM Transaction` |
| `apdex(attr, threshold)` | Apdex score | `SELECT apdex(duration, 0.5) FROM Transaction` |
| `funnel(...)` | Funnel analysis | Complex multi-step |

### Time Ranges

| Syntax | Description |
|--------|-------------|
| `SINCE 30 minutes ago` | Last 30 minutes |
| `SINCE 1 hour ago` | Last hour |
| `SINCE 1 day ago` | Last 24 hours |
| `SINCE 7 days ago` | Last week |
| `SINCE '2024-01-15 10:00:00'` | Specific start time |
| `SINCE 1 hour ago UNTIL 30 minutes ago` | Time window |
| `COMPARE WITH 1 day ago` | Side-by-side comparison |
| `COMPARE WITH 1 week ago` | Week-over-week |

### TIMESERIES Buckets
- `TIMESERIES 1 minute` - High resolution
- `TIMESERIES 5 minutes` - Standard
- `TIMESERIES 15 minutes` - Medium
- `TIMESERIES 1 hour` - Low resolution
- `TIMESERIES AUTO` - Auto-select based on range
- `TIMESERIES MAX` - Maximum resolution

---

## Common Query Patterns

### Error Analysis

**Error rate over time:**
```sql
SELECT percentage(count(*), WHERE error IS true) AS 'Error Rate'
FROM Transaction
WHERE appName = 'my-service'
SINCE 4 hours ago TIMESERIES 5 minutes
```

**Top errors by class:**
```sql
SELECT count(*) FROM TransactionError
WHERE appName = 'my-service'
FACET error.class, error.message
SINCE 1 hour ago LIMIT 20
```

**Error rate by endpoint:**
```sql
SELECT percentage(count(*), WHERE error IS true) AS 'Error Rate', count(*)
FROM Transaction
WHERE appName = 'my-service'
FACET name
SINCE 1 hour ago
ORDER BY count(*) DESC LIMIT 20
```

**HTTP error codes:**
```sql
SELECT count(*) FROM Transaction
WHERE appName = 'my-service' AND httpResponseCode >= 400
FACET httpResponseCode, name
SINCE 1 hour ago
```

**New errors (not seen yesterday):**
```sql
SELECT count(*) FROM TransactionError
WHERE appName = 'my-service'
FACET error.class
SINCE 1 hour ago
COMPARE WITH 1 day ago
```

### Performance Analysis

**Response time percentiles:**
```sql
SELECT percentile(duration, 50, 90, 95, 99)
FROM Transaction
WHERE appName = 'my-service'
SINCE 1 hour ago TIMESERIES 5 minutes
```

**Slowest transactions:**
```sql
SELECT average(duration), count(*), percentile(duration, 95)
FROM Transaction
WHERE appName = 'my-service'
FACET name
SINCE 1 hour ago
ORDER BY average(duration) DESC LIMIT 20
```

**Database time breakdown:**
```sql
SELECT average(databaseDuration), average(duration), average(externalDuration)
FROM Transaction
WHERE appName = 'my-service'
SINCE 4 hours ago TIMESERIES 5 minutes
```

**Throughput by endpoint:**
```sql
SELECT rate(count(*), 1 minute) AS 'RPM'
FROM Transaction
WHERE appName = 'my-service'
FACET name
SINCE 1 hour ago
ORDER BY rate(count(*), 1 minute) DESC LIMIT 20
```

**Apdex score:**
```sql
SELECT apdex(duration, 0.5) AS 'Apdex'
FROM Transaction
WHERE appName = 'my-service'
SINCE 4 hours ago TIMESERIES 15 minutes
```

### Infrastructure Monitoring

**CPU usage by host:**
```sql
SELECT average(cpuPercent), max(cpuPercent)
FROM SystemSample
WHERE hostname LIKE 'prod-%'
FACET hostname
SINCE 30 minutes ago
```

**Memory pressure:**
```sql
SELECT average(memoryUsedPercent), average(memoryFreeBytes/1e9) AS 'Free GB'
FROM SystemSample
WHERE hostname LIKE 'prod-%'
FACET hostname
SINCE 1 hour ago TIMESERIES 5 minutes
```

**Disk usage:**
```sql
SELECT latest(diskUsedPercent)
FROM SystemSample
WHERE hostname LIKE 'prod-%'
FACET hostname, mountPoint
SINCE 5 minutes ago
```

**Container resource usage:**
```sql
SELECT average(cpuPercent), average(memoryUsageBytes/1e6) AS 'Memory MB'
FROM ContainerSample
WHERE containerName LIKE 'api-%'
FACET containerName
SINCE 30 minutes ago
```

**Kubernetes pod status:**
```sql
SELECT latest(status), latest(podName)
FROM K8sPodSample
WHERE namespace = 'production' AND status != 'Running'
FACET podName
SINCE 15 minutes ago
```

### Log Analysis

**Error logs:**
```sql
SELECT message, level, hostname
FROM Log
WHERE level = 'ERROR' AND service = 'payment-api'
SINCE 1 hour ago LIMIT 100
```

**Log volume by level:**
```sql
SELECT count(*)
FROM Log
WHERE service = 'my-service'
FACET level
SINCE 4 hours ago TIMESERIES 15 minutes
```

**Search for specific patterns:**
```sql
SELECT message, timestamp, hostname
FROM Log
WHERE message LIKE '%timeout%' AND service = 'checkout-service'
SINCE 30 minutes ago LIMIT 50
```

**Log error rate:**
```sql
SELECT percentage(count(*), WHERE level = 'ERROR') AS 'Error %'
FROM Log
WHERE service = 'my-service'
SINCE 4 hours ago TIMESERIES 5 minutes
```

### Distributed Tracing

**Slow spans:**
```sql
SELECT average(duration), count(*)
FROM Span
WHERE service.name = 'checkout-service'
FACET name
SINCE 1 hour ago
ORDER BY average(duration) DESC LIMIT 20
```

**Error spans:**
```sql
SELECT count(*), latest(error.message)
FROM Span
WHERE service.name = 'checkout-service' AND error.message IS NOT NULL
FACET error.message
SINCE 1 hour ago LIMIT 10
```

**Cross-service latency:**
```sql
SELECT average(duration)
FROM Span
WHERE service.name IN ('api-gateway', 'checkout', 'payment', 'inventory')
FACET service.name
SINCE 1 hour ago TIMESERIES 5 minutes
```

**Find trace IDs for errors:**
```sql
SELECT traceId, duration, error.message, name
FROM Span
WHERE service.name = 'checkout-service' AND error.message IS NOT NULL
SINCE 30 minutes ago LIMIT 10
```

### Deployment Analysis

**Before/after comparison:**
```sql
SELECT average(duration), percentage(count(*), WHERE error IS true) AS 'Error Rate'
FROM Transaction
WHERE appName = 'my-service'
SINCE 2 hours ago
COMPARE WITH 2 hours ago
TIMESERIES 5 minutes
```

**Error rate change after deploy:**
```sql
SELECT percentage(count(*), WHERE error IS true) AS 'Error Rate'
FROM Transaction
WHERE appName = 'my-service'
SINCE 1 hour ago
COMPARE WITH 1 day ago
```

**New error types after deploy:**
```sql
SELECT count(*)
FROM TransactionError
WHERE appName = 'my-service'
FACET error.class
SINCE 1 hour ago
```

### Browser/RUM

**Page load times:**
```sql
SELECT average(duration), percentile(duration, 95)
FROM PageView
WHERE appName = 'my-frontend'
FACET pageUrl
SINCE 1 hour ago
ORDER BY average(duration) DESC LIMIT 20
```

**JavaScript errors:**
```sql
SELECT count(*)
FROM JavaScriptError
WHERE appName = 'my-frontend'
FACET errorMessage, pageUrl
SINCE 1 hour ago LIMIT 20
```

**Performance by geography:**
```sql
SELECT average(duration), count(*)
FROM PageView
WHERE appName = 'my-frontend'
FACET countryCode
SINCE 1 hour ago
```

### Alert Analysis

**Active incidents:**
```sql
SELECT count(*)
FROM NrAiIncident
WHERE state = 'open'
FACET priority, conditionName
SINCE 24 hours ago
```

**Incident frequency:**
```sql
SELECT count(*)
FROM NrAiIncident
FACET policyName
SINCE 7 days ago TIMESERIES 1 day
```

---

## Investigation Workflows

### Workflow 1: Error Spike Investigation

1. **Confirm the spike:**
```sql
SELECT percentage(count(*), WHERE error IS true) FROM Transaction
WHERE appName = 'my-service' SINCE 4 hours ago TIMESERIES 5 minutes
```

2. **Identify error types:**
```sql
SELECT count(*) FROM TransactionError WHERE appName = 'my-service'
FACET error.class, error.message SINCE 1 hour ago LIMIT 10
```

3. **Find affected endpoints:**
```sql
SELECT percentage(count(*), WHERE error IS true), count(*)
FROM Transaction WHERE appName = 'my-service'
FACET name SINCE 1 hour ago ORDER BY percentage(count(*), WHERE error IS true) DESC
```

4. **Check logs for details:**
```sql
SELECT message FROM Log WHERE service = 'my-service' AND level = 'ERROR'
SINCE 30 minutes ago LIMIT 50
```

5. **Find error traces:**
```sql
SELECT traceId, duration, error.message FROM Span
WHERE service.name = 'my-service' AND error.message IS NOT NULL
SINCE 30 minutes ago LIMIT 10
```

6. **Check for deployment correlation:**
```sql
SELECT percentage(count(*), WHERE error IS true) FROM Transaction
WHERE appName = 'my-service' SINCE 2 hours ago COMPARE WITH 2 hours ago TIMESERIES 5 minutes
```

### Workflow 2: Latency Degradation

1. **Confirm degradation:**
```sql
SELECT percentile(duration, 50, 95, 99) FROM Transaction
WHERE appName = 'my-service' SINCE 6 hours ago TIMESERIES 10 minutes
```

2. **Identify slow endpoints:**
```sql
SELECT average(duration), count(*) FROM Transaction
WHERE appName = 'my-service' AND duration > 2
FACET name SINCE 1 hour ago ORDER BY average(duration) DESC LIMIT 10
```

3. **Check database impact:**
```sql
SELECT average(databaseDuration), average(externalDuration), average(duration)
FROM Transaction WHERE appName = 'my-service'
SINCE 4 hours ago TIMESERIES 5 minutes
```

4. **Check infrastructure:**
```sql
SELECT average(cpuPercent), average(memoryUsedPercent) FROM SystemSample
WHERE hostname LIKE 'api-%' SINCE 4 hours ago TIMESERIES 5 minutes
```

5. **Check external dependencies:**
```sql
SELECT average(duration), count(*) FROM ExternalTransaction
WHERE appName = 'my-service' FACET host
SINCE 1 hour ago ORDER BY average(duration) DESC
```

### Workflow 3: Infrastructure Alert Response

1. **Check host metrics:**
```sql
SELECT average(cpuPercent), max(cpuPercent), average(memoryUsedPercent)
FROM SystemSample WHERE hostname = 'prod-api-01'
SINCE 1 hour ago TIMESERIES 1 minute
```

2. **Check processes:**
```sql
SELECT average(cpuPercent), average(memoryResidentSizeBytes/1e6) AS 'Memory MB'
FROM ProcessSample WHERE hostname = 'prod-api-01'
FACET commandName SINCE 30 minutes ago ORDER BY average(cpuPercent) DESC LIMIT 10
```

3. **Check application impact:**
```sql
SELECT average(duration), rate(count(*), 1 minute) FROM Transaction
WHERE host = 'prod-api-01' SINCE 1 hour ago TIMESERIES 5 minutes
```

4. **Check disk:**
```sql
SELECT latest(diskUsedPercent), latest(diskFreeBytes/1e9) AS 'Free GB'
FROM SystemSample WHERE hostname = 'prod-api-01'
FACET mountPoint SINCE 5 minutes ago
```

---

## Anti-Patterns

### ❌ DON'T: Query without time filter
```sql
-- Wrong: scans all data
SELECT count(*) FROM Transaction WHERE appName = 'my-service'

-- Correct: always use SINCE
SELECT count(*) FROM Transaction WHERE appName = 'my-service' SINCE 1 hour ago
```

### ❌ DON'T: Use only averages
```sql
-- Misleading: hides tail latency
SELECT average(duration) FROM Transaction

-- Better: use percentiles
SELECT percentile(duration, 50, 95, 99) FROM Transaction
```

### ❌ DON'T: Forget LIMIT on FACET
```sql
-- May return too few results (default limit)
SELECT count(*) FROM Transaction FACET name SINCE 1 hour ago

-- Explicit: control result count
SELECT count(*) FROM Transaction FACET name SINCE 1 hour ago LIMIT 50
```

### ❌ DON'T: Use long ranges without TIMESERIES
```sql
-- Single number for 7 days isn't useful
SELECT average(duration) FROM Transaction SINCE 7 days ago

-- Better: see the trend
SELECT average(duration) FROM Transaction SINCE 7 days ago TIMESERIES 1 hour
```

### ❌ DON'T: Ignore infrastructure
```sql
-- Only checking application metrics
SELECT average(duration) FROM Transaction WHERE appName = 'my-service'

-- Also check: host metrics, container metrics, external calls
```

---

## Tips for Effective Queries

1. **Start with SINCE 1 hour ago** - Expand if needed
2. **Use FACET for breakdown** - Identify specific problematic areas
3. **Use TIMESERIES for trends** - See when issues started
4. **Use COMPARE WITH** - Instant before/after comparison
5. **Combine event types** - Transaction + Log + Span for full picture
6. **Use percentage()** - Better than raw counts for error rates
7. **Use percentile()** - More meaningful than average for latency
8. **Filter by appName first** - Scopes query efficiently
9. **Use rate()** - For throughput metrics (requests per minute)
10. **Check golden metrics first** - Latency, traffic, errors, saturation

---

## Summary Checklist

Before querying New Relic:
- ✅ Always include SINCE clause for time range
- ✅ Start with golden signals (latency, traffic, errors, saturation)
- ✅ Use FACET to break down by service, host, endpoint
- ✅ Use TIMESERIES to visualize trends
- ✅ Use percentiles over averages for latency
- ✅ Use COMPARE WITH for deployment analysis
- ✅ Check multiple event types (Transaction, Log, Span, SystemSample)
- ✅ Set explicit LIMIT on FACET queries
- ✅ Filter by appName/service first for performance
- ✅ Use entity search to find correct names before querying

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `NEW_RELIC_API_KEY` or `NEW_RELIC_ACCOUNT_ID` values in responses
- **NEVER** include API keys in NRQL queries or query results shared with users
- When referencing credentials, use placeholder names (e.g., "your API key") not actual values
- If a query result contains PII (user IDs, emails, IP addresses), summarize rather than reproduce verbatim

### Query Scope Restrictions
- **Always filter by `appName` or `service.name`** - never run unscoped queries that scan all applications
- **Avoid `SELECT *`** patterns - explicitly name the fields you need
- **Do not query `NrAuditEvent`** unless explicitly requested - audit logs may contain sensitive operational data
- **Limit log queries** - log messages may contain secrets, tokens, or PII; summarize patterns rather than returning raw content
- When querying `Log` events, avoid returning full `message` fields if they may contain credentials or tokens

### Data Sensitivity
- Treat all query results as potentially containing sensitive information
- Do not expose internal hostnames, IP addresses, or infrastructure topology unless the user explicitly asks
- When presenting trace data, redact or summarize request/response bodies that may contain user data
- Do not correlate user IDs across queries to build user profiles unless explicitly requested

### Access Control
- Only query accounts the user has explicitly configured
- Do not attempt to enumerate accounts, users, or permissions
- If a query returns "unauthorized" or "forbidden", report the error without retrying with different credentials

## Anti-Hallucination Guardrails

### Query Accuracy
- **Only use documented NRQL event types** - do not invent event type names. Valid types include: `Transaction`, `TransactionError`, `Span`, `Log`, `SystemSample`, `NetworkSample`, `ProcessSample`, `ContainerSample`, `K8sContainerSample`, `K8sPodSample`, `PageView`, `JavaScriptError`, `SyntheticCheck`, `Metric`, `NrAiIncident`
- **Only use documented NRQL functions** - do not invent aggregation functions. Valid functions include: `count`, `average`, `sum`, `min`, `max`, `percentile`, `rate`, `uniqueCount`, `percentage`, `filter`, `latest`, `earliest`, `histogram`, `apdex`
- **Only use documented NRQL clauses** - valid clauses are: `SELECT`, `FROM`, `WHERE`, `FACET`, `SINCE`, `UNTIL`, `TIMESERIES`, `LIMIT`, `COMPARE WITH`, `ORDER BY`, `AS`
- **Do not fabricate attribute names** - if unsure whether a field exists, suggest the user verify with `SELECT keyset() FROM <EventType> SINCE 1 hour ago`

### Result Interpretation
- **Never invent metric values** - if a query hasn't been run, say "I need to query this" rather than guessing
- **Do not assume causation from correlation** - when metrics change at the same time, note the correlation but do not assert causation without evidence
- **Clearly distinguish between observed data and inference** - prefix interpretations with "This suggests..." or "This may indicate..."
- **If a query returns no results**, report that clearly rather than speculating about what the data might show
- **Do not extrapolate trends** beyond the queried time range without explicitly stating the assumption

### Tool Capability Boundaries
- Do not claim the New Relic MCP server can create alerts, modify configurations, or deploy changes - it is read-only
- Do not claim access to features not listed in the tools (e.g., Synthetics management, deployment markers creation)
- If the user asks for something outside tool capabilities, clearly state the limitation

## Operational Optimization Guardrails

### Query Performance
- **Start with 1-hour time ranges** - expand only if insufficient data is found
- **Use TIMESERIES with appropriate buckets** - match bucket size to time range:
 - < 1h: `TIMESERIES 1 minute`
 - 1-6h: `TIMESERIES 5 minutes`
 - 6-24h: `TIMESERIES 15 minutes`
 - > 24h: `TIMESERIES 1 hour`
- **Always include LIMIT** on FACET queries - default to `LIMIT 20` unless more is needed
- **Filter before aggregating** - put WHERE clauses before FACET to reduce scan size
- **Avoid nested subqueries** when a single query with FACET achieves the same result

### Rate Limiting
- **Space queries apart** - do not fire more than 3-5 queries in rapid succession
- **Use a single query with multiple functions** when possible:
  ```sql
 -- Good: one query
  SELECT average(duration), percentile(duration, 95), count(*) FROM Transaction SINCE 1 hour ago
  
 -- Bad: three separate queries for the same data
  ```
- **Cache entity GUIDs** - once you've found an entity, reuse its GUID rather than searching again
- If rate-limited, wait before retrying and inform the user of the delay

### Resource Efficiency
- **Prefer `TIMESERIES` over raw events** for trend analysis - aggregated data is cheaper to process
- **Use `SINCE` and `UNTIL`** to bound every query - never query without time constraints
- **Avoid `SELECT *` from Log events** - logs can be extremely high volume; always filter by level, service, or message pattern
- **Use `uniqueCount()` sparingly** on high-cardinality fields - it's expensive
- **Prefer `percentage()` over separate count queries** for error rate calculations

## Cost Optimization Guardrails

### Data Ingestion Awareness
- **Be aware of query costs** - longer time ranges and higher cardinality FACET queries consume more compute
- **Avoid redundant queries** - if you already have the data from a previous query, reuse it
- **Use `LIMIT` aggressively** - start with `LIMIT 10` for exploration, increase only when needed
- **Prefer `latest()` over full scans** for current-state queries (e.g., host health)

### Query Planning
- **Plan before querying** - determine what information is needed and write the minimum number of queries to get it
- **Combine related questions into single queries** using multiple SELECT functions
- **Use COMPARE WITH instead of two separate queries** for before/after analysis
- **Avoid repeated identical queries** - if the same data is needed multiple times in a workflow, query once and reference the results

### Alerting on Costs
- When users ask about setting up monitoring, recommend efficient query patterns that minimize NRDB consumption
- Suggest using `rate()` with appropriate windows rather than raw `count(*)` for high-volume event types
- Recommend `TIMESERIES AUTO` for dashboards to let New Relic optimize bucket sizes
