---
name: "new-relic"
displayName: "New Relic Observability"
description: "Query application performance, infrastructure metrics, logs, distributed traces, alerts, and dashboards from New Relic using NRQL for production debugging and performance analysis"
keywords: ["new-relic", "newrelic", "observability", "monitoring", "apm", "nrql", "logs", "metrics", "traces", "alerts", "infrastructure"]
author: "Community"
---

# New Relic Observability Power

## Overview

The New Relic Observability Power connects to your New Relic monitoring data through NRQL (New Relic Query Language). Query application performance, infrastructure metrics, logs, distributed traces, browser performance, synthetic monitors, and alerts.

**Key capabilities:**
- **NRQL Querying**: Execute powerful queries against all New Relic data types
- **APM**: Analyze application performance, transactions, and error rates
- **Infrastructure**: Monitor hosts, containers, and cloud resources
- **Logs**: Search and analyze application and infrastructure logs
- **Distributed Tracing**: Investigate request flows across services
- **Browser/RUM**: Analyze frontend performance and user experience
- **Alerts**: Query alert conditions, incidents, and notification channels
- **Dashboards**: Search and retrieve dashboard configurations

**Authentication**: Requires New Relic User API Key and Account ID.

## Onboarding

### Prerequisites

1. **New Relic account** - Any New Relic plan with API access
2. **User API Key** - A New Relic User API key (starts with `NRAK-`)
3. **Account ID** - Your New Relic account number
4. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your API key and account ID
3. Test with: *"Show error rate for my services"* or *"List active alert incidents"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_NEW_RELIC_USER_API_KEY`**: Your New Relic User API Key.
 - **How to get it:**
    1. Log in to New Relic
    2. Click your user menu (bottom-left) → API Keys
    3. Click "Create a key" → Key type: "User"
    4. Copy the generated key (starts with `NRAK-`)

- **`YOUR_ACCOUNT_ID`**: Your New Relic Account ID.
 - **How to get it:** Visible in the URL when logged in (`https://one.newrelic.com/...?account=ACCOUNT_ID`), or go to Administration → Access Management → Accounts

## Available Steering Files

- **steering/steering.md** - Complete NRQL syntax reference, investigation workflows, query patterns, and best practices

## Available MCP Servers

### newrelic
**Package:** `@newrelic/mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **run_nrql_query** - Execute an NRQL query
  - Required: `query` (string) - NRQL query to execute
  - Required: `accountId` (number) - New Relic account ID
  - Optional: `timeout` (number) - Query timeout in seconds
  - Returns: Query results with facets and timeseries data

2. **get_alert_incidents** - List alert incidents
  - Required: `accountId` (number)
  - Optional: `state` (string) - open, closed, all
  - Optional: `priority` (string) - critical, warning
  - Returns: Alert incidents with details

3. **get_entity** - Get entity details by GUID
  - Required: `guid` (string) - Entity GUID
  - Returns: Entity metadata, tags, and relationships

4. **search_entities** - Search for monitored entities
  - Required: `query` (string) - Search query
  - Optional: `type` (string) - Entity type (APPLICATION, HOST, etc.)
  - Optional: `domain` (string) - APM, INFRA, BROWSER, etc.
  - Returns: Matching entities with GUIDs

5. **get_entity_golden_metrics** - Get golden signals for an entity
  - Required: `guid` (string) - Entity GUID
  - Returns: Response time, throughput, error rate

6. **list_dashboards** - List dashboards
  - Optional: `query` (string) - Search filter
  - Returns: Dashboard list with metadata

7. **get_dashboard** - Get dashboard details
  - Required: `guid` (string) - Dashboard GUID
  - Returns: Dashboard with widgets and NRQL queries

8. **get_distributed_trace** - Get trace details
  - Required: `traceId` (string) - Trace ID
  - Returns: Complete trace with spans

9. **get_alert_policies** - List alert policies
  - Required: `accountId` (number)
  - Returns: Alert policies with conditions

10. **get_alert_conditions** - Get conditions for a policy
   - Required: `accountId` (number), `policyId` (number)
   - Returns: Alert conditions with thresholds

## Tool Usage Examples

### NRQL Queries

**Application error rate:**
```javascript
usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT percentage(count(*), WHERE error IS true) AS 'Error Rate' FROM Transaction WHERE appName = 'my-service' SINCE 1 hour ago TIMESERIES 5 minutes"
})
```

**Slowest transactions:**
```javascript
usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(duration), count(*) FROM Transaction WHERE appName = 'my-service' FACET name SINCE 1 hour ago ORDER BY average(duration) DESC LIMIT 20"
})
```

**Infrastructure CPU usage:**
```javascript
usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(cpuPercent), max(cpuPercent) FROM SystemSample WHERE hostname LIKE 'prod-%' FACET hostname SINCE 30 minutes ago"
})
```

**Log search:**
```javascript
usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT message, level, service FROM Log WHERE level = 'ERROR' AND service = 'payment-api' SINCE 1 hour ago LIMIT 100"
})
```

**Distributed trace analysis:**
```javascript
usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT count(*) FROM Span WHERE service.name = 'checkout-service' AND error.message IS NOT NULL FACET error.message SINCE 1 hour ago"
})
```

### Entity Discovery

**Find application entities:**
```javascript
usePower("new-relic", "newrelic", "search_entities", {
  "query": "payment",
  "type": "APPLICATION",
  "domain": "APM"
})
```

**Get golden metrics:**
```javascript
usePower("new-relic", "newrelic", "get_entity_golden_metrics", {
  "guid": "MXxBUE18QVBQTElDQVRJT058MTIzNDU2Nzg"
})
```

### Alert Management

**Check active incidents:**
```javascript
usePower("new-relic", "newrelic", "get_alert_incidents", {
  "accountId": 1234567,
  "state": "open",
  "priority": "critical"
})
```

## Combining Tools (Workflows)

### Workflow 1: Production Error Investigation

```javascript
// Step 1: Check for active alerts
const incidents = usePower("new-relic", "newrelic", "get_alert_incidents", {
  "accountId": 1234567,
  "state": "open"
})

// Step 2: Find the affected service
const entities = usePower("new-relic", "newrelic", "search_entities", {
  "query": "checkout",
  "type": "APPLICATION"
})

// Step 3: Check error rate trend
const errorRate = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'checkout-service' SINCE 4 hours ago TIMESERIES 5 minutes"
})

// Step 4: Find top errors
const topErrors = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT count(*) FROM TransactionError WHERE appName = 'checkout-service' FACET error.class, error.message SINCE 1 hour ago LIMIT 10"
})

// Step 5: Check error logs
const errorLogs = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT message, timestamp FROM Log WHERE service = 'checkout-service' AND level = 'ERROR' SINCE 30 minutes ago LIMIT 50"
})

// Step 6: Trace a specific error
const errorTraces = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT traceId, duration, error.message FROM Span WHERE service.name = 'checkout-service' AND error.message IS NOT NULL SINCE 30 minutes ago LIMIT 10"
})
```

### Workflow 2: Performance Degradation Analysis

```javascript
// Step 1: Check response time trend
const latency = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(duration), percentile(duration, 95, 99) FROM Transaction WHERE appName = 'api-gateway' SINCE 6 hours ago TIMESERIES 10 minutes"
})

// Step 2: Identify slow transactions
const slowTx = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(duration), count(*) FROM Transaction WHERE appName = 'api-gateway' AND duration > 2 FACET name SINCE 1 hour ago ORDER BY average(duration) DESC LIMIT 10"
})

// Step 3: Check database performance
const dbPerf = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(databaseDuration), average(duration) FROM Transaction WHERE appName = 'api-gateway' SINCE 4 hours ago TIMESERIES 5 minutes"
})

// Step 4: Check infrastructure
const infra = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(cpuPercent), average(memoryUsedPercent) FROM SystemSample WHERE hostname LIKE 'api-%' SINCE 4 hours ago TIMESERIES 5 minutes"
})

// Step 5: Check external service calls
const external = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT average(duration), count(*) FROM ExternalTransaction WHERE appName = 'api-gateway' FACET host SINCE 1 hour ago ORDER BY average(duration) DESC"
})
```

### Workflow 3: Deployment Impact Analysis

```javascript
// Step 1: Compare error rates before/after deploy
const comparison = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'my-service' SINCE 2 hours ago COMPARE WITH 2 hours ago TIMESERIES 5 minutes"
})

// Step 2: Check throughput changes
const throughput = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT rate(count(*), 1 minute) FROM Transaction WHERE appName = 'my-service' SINCE 2 hours ago COMPARE WITH 2 hours ago TIMESERIES 5 minutes"
})

// Step 3: Check for new error types
const newErrors = usePower("new-relic", "newrelic", "run_nrql_query", {
  "accountId": 1234567,
  "query": "SELECT count(*) FROM TransactionError WHERE appName = 'my-service' FACET error.class SINCE 1 hour ago"
})
```

## NRQL Query Syntax Guide

### Basic Structure
```sql
SELECT <function>(<attribute>) FROM <event_type>
WHERE <condition>
FACET <attribute>
SINCE <time>
UNTIL <time>
TIMESERIES <bucket>
LIMIT <count>
```

### Event Types
- `Transaction` - APM transactions (web/non-web)
- `TransactionError` - Application errors
- `Span` - Distributed trace spans
- `Log` - Log entries
- `SystemSample` - Host metrics (CPU, memory, disk)
- `NetworkSample` - Network metrics
- `ProcessSample` - Process-level metrics
- `ContainerSample` - Container metrics
- `K8sContainerSample` - Kubernetes container metrics
- `PageView` - Browser page views
- `JavaScriptError` - Frontend errors
- `SyntheticCheck` - Synthetic monitor results
- `Metric` - Dimensional metrics

### Aggregation Functions
- `count(*)` - Count events
- `average(attribute)` - Mean value
- `sum(attribute)` - Total
- `min(attribute)` / `max(attribute)` - Extremes
- `percentile(attribute, N)` - Nth percentile
- `rate(count(*), 1 minute)` - Rate per time unit
- `uniqueCount(attribute)` - Distinct values
- `percentage(count(*), WHERE condition)` - Percentage matching condition
- `filter(function, WHERE condition)` - Filtered aggregation
- `latest(attribute)` - Most recent value

### Time Ranges
- `SINCE 30 minutes ago`
- `SINCE 1 hour ago`
- `SINCE 1 day ago`
- `SINCE '2024-01-15 10:00:00'`
- `SINCE 1 hour ago UNTIL 30 minutes ago`
- `COMPARE WITH 1 day ago` - Side-by-side comparison

### Common Patterns

**Error rate over time:**
```sql
SELECT percentage(count(*), WHERE error IS true) FROM Transaction
WHERE appName = 'my-service' SINCE 4 hours ago TIMESERIES 5 minutes
```

**Top N by attribute:**
```sql
SELECT count(*) FROM TransactionError
FACET error.class SINCE 1 hour ago LIMIT 10
```

**Percentile latency:**
```sql
SELECT percentile(duration, 50, 90, 95, 99) FROM Transaction
WHERE appName = 'my-service' SINCE 1 hour ago TIMESERIES 5 minutes
```

**Deployment marker comparison:**
```sql
SELECT average(duration) FROM Transaction
WHERE appName = 'my-service' SINCE 2 hours ago COMPARE WITH 2 hours ago
```

**Multi-service comparison:**
```sql
SELECT average(duration), rate(count(*), 1 minute) FROM Transaction
FACET appName SINCE 1 hour ago WHERE appName IN ('service-a', 'service-b', 'service-c')
```

## Best Practices

### ✅ Do:
- **Start with narrow time ranges** (30m-1h) and expand if needed
- **Use FACET** to break down by dimensions (service, host, endpoint)
- **Use TIMESERIES** for trend analysis
- **Filter by appName/service first** to scope queries
- **Use COMPARE WITH** for before/after analysis
- **Check golden metrics first** (response time, throughput, error rate)
- **Use entity search** to find GUIDs before querying
- **Use percentiles** (p95, p99) over averages for latency

### ❌ Don't:
- **Query without time filters** - always use SINCE
- **Use very long time ranges** without TIMESERIES bucketing
- **Rely only on averages** - percentiles reveal tail latency
- **Forget LIMIT** on FACET queries - default may be too low
- **Ignore infrastructure** - check host metrics alongside APM
- **Skip entity discovery** - use search_entities to find correct names

## Configuration

**Authentication Required**: New Relic User API Key and Account ID

**Setup Steps:**

1. **Get New Relic Credentials:**
  - Log in to New Relic → API Keys (under user menu)
  - Create or copy a User API Key (starts with `NRAK-`)
  - Note your Account ID (visible in URL or account settings)

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "newrelic": {
         "command": "npx",
         "args": ["-y", "@newrelic/mcp-server"],
         "env": {
           "NEW_RELIC_API_KEY": "NRAK-your-api-key-here",
           "NEW_RELIC_ACCOUNT_ID": "1234567"
         }
       }
     }
   }
   ```

3. **For EU region:**
   Add the API URL:
   ```json
   "env": {
     "NEW_RELIC_API_KEY": "NRAK-your-api-key",
     "NEW_RELIC_ACCOUNT_ID": "1234567",
     "NEW_RELIC_API_URL": "https://api.eu.newrelic.com"
   }
   ```

## Tips

1. **Start with golden metrics** - Response time, throughput, error rate tell the story
2. **Use COMPARE WITH** - Instantly see before/after for deployments
3. **FACET for breakdown** - Split by service, host, endpoint, user
4. **TIMESERIES for trends** - Visualize patterns over time
5. **Check alerts first** - Active incidents point to root cause
6. **Use entity search** - Find the right entity GUID before deep queries
7. **Percentiles over averages** - p95/p99 reveal real user experience
8. **Cross-reference data types** - Combine Transaction, Log, and Span queries
9. **Use SINCE/COMPARE** - Compare current vs baseline periods
10. **Filter early** - WHERE clauses before FACET improve performance

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@newrelic/mcp-server`
**Source:** New Relic
**License:** MIT-0
**Documentation:** https://docs.newrelic.com/docs/apis/nerdgraph/
