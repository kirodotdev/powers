---
name: "grafana"
displayName: "Grafana Observability"
description: "Query dashboards, data sources, alerts, and visualizations in Grafana for monitoring, performance analysis, and incident response"
keywords: ["grafana", "promql", "logql", "grafana-cloud", "grafana-dashboards", "loki", "prometheus"]
author: "Community"
---

# Grafana Observability Power

## Overview

The Grafana Observability Power connects to your Grafana instance for dashboard management, data source querying, alert management, and visualization. Query Prometheus metrics, Loki logs, and other data sources through Grafana's unified interface.

**Key capabilities:**
- **Dashboard Management**: Search, retrieve, and analyze dashboard configurations
- **Data Source Querying**: Query Prometheus, Loki, InfluxDB, Elasticsearch, and more
- **Alert Management**: List, query, and manage alert rules and notifications
- **Panel Analysis**: Extract queries from dashboard panels for reuse
- **Annotation Management**: Create and query annotations for event correlation
- **Folder Organization**: Navigate dashboard folders and permissions
- **Explore**: Execute ad-hoc queries against any configured data source

**Authentication**: Requires Grafana URL and service account token.

## Onboarding

### Prerequisites

1. **Grafana instance** - Grafana Cloud or self-hosted Grafana (v9.0+)
2. **Service account token** - A Grafana service account with Viewer or Editor role
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your Grafana URL and service account token
3. Test with: *"List my dashboards"* or *"Show firing alerts"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_GRAFANA_INSTANCE.grafana.net`**: Your Grafana instance URL.
 - **How to get it:** This is the URL you use to access Grafana in your browser. For Grafana Cloud, it's typically `https://your-org.grafana.net`. For self-hosted, it's your Grafana server URL.

- **`YOUR_GRAFANA_SERVICE_ACCOUNT_TOKEN`**: A Grafana service account token.
 - **How to get it:**
    1. Log in to Grafana
    2. Go to Administration → Service Accounts
    3. Click "Add service account"
    4. Set role to "Viewer" (or "Editor" for write operations)
    5. Click "Add service account token"
    6. Copy the generated token (starts with `glsa_`)

## Available Steering Files

- **steering/steering.md** - PromQL/LogQL syntax guide, dashboard patterns, and alert workflows

## Available MCP Servers

### grafana
**Package:** `@grafana/mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **search_dashboards** - Search dashboards by title or tag
  - Optional: `query` (string) - Search query
  - Optional: `tag` (string) - Filter by tag
  - Optional: `type` (string) - dash-db, dash-folder
  - Returns: Matching dashboards with UIDs and metadata

2. **get_dashboard** - Get full dashboard configuration
  - Required: `uid` (string) - Dashboard UID
  - Returns: Complete dashboard JSON with panels and queries

3. **list_datasources** - List configured data sources
  - Returns: Data sources with types, URLs, and status

4. **query_datasource** - Execute a query against a data source
  - Required: `datasource_uid` (string) - Data source UID
  - Required: `query` (string) - Query expression (PromQL, LogQL, etc.)
  - Optional: `from` (string) - Start time (default: "now-1h")
  - Optional: `to` (string) - End time (default: "now")
  - Optional: `interval` (string) - Step interval
  - Returns: Query results (metrics, logs, or traces)

5. **list_alert_rules** - List alert rules
  - Optional: `folder_uid` (string) - Filter by folder
  - Optional: `state` (string) - firing, pending, inactive
  - Returns: Alert rules with conditions and states

6. **get_alert_rule** - Get alert rule details
  - Required: `uid` (string) - Alert rule UID
  - Returns: Full alert rule configuration

7. **list_alert_instances** - List current alert instances
  - Optional: `state` (string) - alerting, pending, normal
  - Returns: Active alert instances with labels

8. **create_annotation** - Create a dashboard annotation
  - Required: `text` (string) - Annotation text
  - Optional: `dashboard_uid` (string) - Target dashboard
  - Optional: `panel_id` (number) - Target panel
  - Optional: `time` (number) - Unix timestamp (ms)
  - Optional: `tags` (array) - Annotation tags
  - Returns: Created annotation details

9. **list_annotations** - List annotations
  - Optional: `from` (string) - Start time
  - Optional: `to` (string) - End time
  - Optional: `tags` (array) - Filter by tags
  - Optional: `dashboard_uid` (string) - Filter by dashboard
  - Returns: Annotations with timestamps and text

10. **list_folders** - List dashboard folders
   - Returns: Folders with UIDs and permissions

11. **get_datasource_health** - Check data source connectivity
   - Required: `uid` (string) - Data source UID
   - Returns: Health status and response time

## Tool Usage Examples

### Dashboard Discovery

**Search dashboards:**
```javascript
usePower("grafana", "grafana", "search_dashboards", {
  "query": "production",
  "tag": "team:backend"
})
```

**Get dashboard details:**
```javascript
usePower("grafana", "grafana", "get_dashboard", {
  "uid": "abc123def"
})
```

### Data Source Querying

**Prometheus metrics (PromQL):**
```javascript
usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "rate(http_requests_total{service=\"api\", status=~\"5..\"}[5m])",
  "from": "now-1h",
  "to": "now"
})
```

**Loki logs (LogQL):**
```javascript
usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "loki-1",
  "query": "{namespace=\"production\", app=\"checkout\"} |= \"error\" | json | level=\"error\"",
  "from": "now-30m",
  "to": "now"
})
```

**Infrastructure metrics:**
```javascript
usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
  "from": "now-1h",
  "to": "now"
})
```

### Alert Management

**List firing alerts:**
```javascript
usePower("grafana", "grafana", "list_alert_instances", {
  "state": "alerting"
})
```

**Get alert rule details:**
```javascript
usePower("grafana", "grafana", "get_alert_rule", {
  "uid": "alert-rule-123"
})
```

### Annotations

**Create deployment annotation:**
```javascript
usePower("grafana", "grafana", "create_annotation", {
  "text": "Deployed v2.3.1 to production",
  "tags": ["deployment", "production", "v2.3.1"]
})
```

## Combining Tools (Workflows)

### Workflow 1: Incident Investigation

```javascript
// Step 1: Check firing alerts
const alerts = usePower("grafana", "grafana", "list_alert_instances", {
  "state": "alerting"
})

// Step 2: Get alert rule details
const alertRule = usePower("grafana", "grafana", "get_alert_rule", {
  "uid": alerts[0].rule_uid
})

// Step 3: Query the metric that triggered the alert
const metrics = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "rate(http_requests_total{service=\"checkout\", status=~\"5..\"}[5m])",
  "from": "now-2h",
  "to": "now"
})

// Step 4: Check related logs
const logs = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "loki-1",
  "query": "{service=\"checkout\"} |= \"error\" | json | line_format \"{{.timestamp}} {{.level}} {{.message}}\"",
  "from": "now-30m",
  "to": "now"
})

// Step 5: Check deployment annotations
const annotations = usePower("grafana", "grafana", "list_annotations", {
  "from": "now-4h",
  "to": "now",
  "tags": ["deployment"]
})

// Step 6: Find related dashboard
const dashboards = usePower("grafana", "grafana", "search_dashboards", {
  "query": "checkout",
  "tag": "service:checkout"
})
```

### Workflow 2: Performance Analysis

```javascript
// Step 1: Query response time
const latency = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=\"api\"}[5m]))",
  "from": "now-6h",
  "to": "now"
})

// Step 2: Check error rate
const errors = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "sum(rate(http_requests_total{service=\"api\", status=~\"5..\"}[5m])) / sum(rate(http_requests_total{service=\"api\"}[5m])) * 100",
  "from": "now-6h",
  "to": "now"
})

// Step 3: Check resource utilization
const cpu = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "avg by (pod) (rate(container_cpu_usage_seconds_total{namespace=\"production\", container=\"api\"}[5m]))",
  "from": "now-6h",
  "to": "now"
})

// Step 4: Check saturation
const memory = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": "prometheus-1",
  "query": "container_memory_working_set_bytes{namespace=\"production\", container=\"api\"} / container_spec_memory_limit_bytes{namespace=\"production\", container=\"api\"} * 100",
  "from": "now-6h",
  "to": "now"
})
```

### Workflow 3: Dashboard Analysis

```javascript
// Step 1: Find relevant dashboards
const dashboards = usePower("grafana", "grafana", "search_dashboards", {
  "tag": "production"
})

// Step 2: Get dashboard configuration
const dashboard = usePower("grafana", "grafana", "get_dashboard", {
  "uid": dashboards[0].uid
})

// Step 3: Extract and run key queries from panels
const panelQuery = dashboard.panels[0].targets[0].expr
const results = usePower("grafana", "grafana", "query_datasource", {
  "datasource_uid": dashboard.panels[0].datasource.uid,
  "query": panelQuery,
  "from": "now-1h",
  "to": "now"
})

// Step 4: Check data source health
const health = usePower("grafana", "grafana", "get_datasource_health", {
  "uid": "prometheus-1"
})
```

## Query Syntax by Data Source

### PromQL (Prometheus)

**Instant queries:**
```promql
http_requests_total{service="api", status="500"}
```

**Range queries with rate:**
```promql
rate(http_requests_total{service="api"}[5m])
```

**Aggregations:**
```promql
sum by (service) (rate(http_requests_total[5m]))
avg by (instance) (node_cpu_seconds_total{mode="idle"})
```

**Histograms:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Operators:**
```promql
# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Comparison
http_requests_total > 1000
```

### LogQL (Loki)

**Log stream selection:**
```logql
{namespace="production", app="checkout"}
```

**Filter expressions:**
```logql
{app="api"} |= "error"           # contains
{app="api"} != "healthcheck"      # not contains
{app="api"} |~ "timeout|error"    # regex match
{app="api"} !~ "debug|trace"      # regex not match
```

**Parser and label filter:**
```logql
{app="api"} | json | level="error" | status >= 400
{app="api"} | logfmt | duration > 5s
```

**Metric queries:**
```logql
# Count errors per minute
sum(rate({app="api"} |= "error" [1m])) by (namespace)

# Bytes rate
sum(bytes_rate({app="api"}[5m])) by (pod)
```

## Best Practices

### ✅ Do:
- **Use label selectors** to narrow queries before applying functions
- **Start with short time ranges** (1h) and expand if needed
- **Use rate() for counters** - never graph raw counter values
- **Use dashboard queries** - extract PromQL from existing panels
- **Check data source health** before investigating missing data
- **Use annotations** to mark deployments and incidents
- **Filter alerts by state** - focus on firing/pending first
- **Use histogram_quantile** for latency percentiles

### ❌ Don't:
- **Query without label selectors** - `http_requests_total` scans everything
- **Use very long ranges with high resolution** - causes timeouts
- **Forget rate() on counters** - raw counters are meaningless
- **Ignore recording rules** - use pre-computed metrics when available
- **Skip data source verification** - check health if queries return empty

## Configuration

**Authentication Required**: Grafana URL and service account token

**Setup Steps:**

1. **Create a Service Account Token:**
  - Go to Grafana → Administration → Service Accounts
  - Create a new service account with Viewer or Editor role
  - Generate a token for the service account

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "grafana": {
         "command": "npx",
         "args": ["-y", "@grafana/mcp-server"],
         "env": {
           "GRAFANA_URL": "https://your-instance.grafana.net",
           "GRAFANA_API_KEY": "glsa_your_service_account_token"
         }
       }
     }
   }
   ```

3. **For self-hosted Grafana:**
   ```json
   "env": {
     "GRAFANA_URL": "https://grafana.yourcompany.com",
     "GRAFANA_API_KEY": "glsa_your_token"
   }
   ```

## Tips

1. **Search dashboards first** - Find existing queries before writing new ones
2. **Check data source health** - Verify connectivity before debugging queries
3. **Use annotations** - Mark deployments for correlation with metrics
4. **Extract panel queries** - Reuse PromQL/LogQL from existing dashboards
5. **Start with alerts** - Firing alerts point to active issues
6. **Use label matchers** - Always filter by service/namespace/environment
7. **Rate for counters** - Always wrap counters in rate() or increase()
8. **Histogram quantiles** - Use histogram_quantile for latency SLOs
9. **Check folders** - Dashboards are organized by team/service in folders
10. **Combine sources** - Correlate Prometheus metrics with Loki logs

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@grafana/mcp-server`
**Source:** Grafana Labs
**License:** MIT-0
**Documentation:** https://grafana.com/docs/grafana/latest/
