---
name: "datadog"
description: "Query Datadog logs, metrics, APM traces, RUM events, incidents, monitors, services and dashboards through the Datadog MCP server for production debugging and performance analysis. Use when investigating production issues, analyzing performance or user experience, or checking incidents and monitors."
metadata:
  author: "Datadog"
  version: "1.0.0"
---

# Onboarding

The Datadog MCP server is generally available. Before proceeding, let the user know what it needs:
- An organization admin must allow MCP access in Organization Settings.
- The user's Datadog role needs MCP Server permissions (the Standard Role has them by default; custom roles need `mcp_read` and/or `mcp_write`).
- Datadog government sites (`app.ddog-gov.com`, `us2.ddog-gov.com`) are not supported.

Setup details: https://docs.datadoghq.com/bits_ai/mcp_server/setup

# Overview

The Datadog Observability plugin provides comprehensive access to your Datadog monitoring data across logs, metrics, APM traces, Real User Monitoring (RUM), incidents, and monitors. Query and analyze production systems for debugging, performance optimization, and incident response.

**Key capabilities:**
- **Log Search**: Query application and infrastructure logs with powerful filtering
- **Metrics**: Analyze time-series data for performance and resource utilization
- **APM/Traces**: Investigate distributed traces and service dependencies
- **RUM**: Analyze user experience, page performance, and frontend errors
- **Incidents**: Track and manage production incidents
- **Monitors**: Search alerting rules and monitor status

**Authentication**: OAuth 2.0 (recommended; your MCP client completes the login flow). A Datadog Personal or Service Access Token, or a Datadog API key and application key, can be used instead when OAuth is not possible. See [Configuration](#configuration).

## Related Skills

This plugin has the following related skill:
- **[datadog-query-syntax](../datadog-query-syntax/SKILL.md)** - Comprehensive query syntax guide with examples, workflows, and troubleshooting

## Available MCP Servers

### datadog
**Connection:** Remote MCP server over streamable HTTP
**Endpoint:** `https://mcp.datadoghq.com/v1/mcp` (US1), configured in this plugin's `mcp.json`. No npx or `mcp-remote` is needed.

**Tools:**

1. **search_datadog_logs** - Search application and infrastructure logs
   - Required: `query` (string) - Log search query
   - Optional: `from` (string) - Start time (default: "now-1h")
   - Optional: `to` (string) - End time (default: "now")
   - Optional: `head_limit` (number) - Max results (default: 100)
   - Optional: `max_tokens` (number) - Token limit for output
   - Optional: `group_by_message` (boolean) - Group similar logs
   - Optional: `extra_fields` (array) - Additional fields to include
   - Returns: Matching log entries with timestamps and attributes

2. **get_datadog_metric** - Query time-series metrics
   - Required: `query` (string) - Metric query
   - Required: `from` (string) - Start time
   - Required: `to` (string) - End time
   - Optional: `raw_data` (boolean) - Return raw datapoints vs binned
   - Optional: `use_cloud_cost` (boolean) - Query cloud cost data
   - Returns: Metric values over time with aggregations

3. **search_datadog_spans** - Search APM traces and spans
   - Required: `query` (string) - Span search query
   - Optional: `from` (string) - Start time (default: "now-1h")
   - Optional: `to` (string) - End time (default: "now")
   - Optional: `head_limit` (number) - Max results (default: 100)
   - Optional: `max_tokens` (number) - Token limit for output
   - Optional: `custom_attributes` (array) - Custom span attributes to include
   - Returns: Matching spans with trace IDs and timing

4. **get_datadog_trace** - Get full trace details by trace ID
   - Required: `trace_id` (string) - Trace ID to retrieve
   - Returns: Complete trace with all spans and relationships

5. **search_datadog_rum_events** - Search Real User Monitoring events
   - Required: `query` (string) - RUM event query
   - Optional: `from` (string) - Start time (default: "now-15m")
   - Optional: `to` (string) - End time (default: "now")
   - Optional: `head_limit` (number) - Max results (default: 100)
   - Optional: `max_tokens` (number) - Token limit for output
   - Optional: `detailed_output` (boolean) - Include full event details
   - Returns: RUM events (views, actions, errors, resources)

6. **search_datadog_incidents** - Search and list incidents
   - Optional: `query` (string) - Incident search query (default: "state:active")
   - Optional: `from` (string) - Start time
   - Optional: `to` (string) - End time
   - Returns: Incidents with severity, status, and affected services

7. **get_datadog_incident** - Get detailed incident information
   - Required: `incident_id` (string) - Incident ID
   - Returns: Full incident details with timeline and updates

8. **search_datadog_monitors** - Search alerting monitors
   - Optional: `query` (string) - Monitor search query
   - Returns: Monitors with status and configuration

9. **search_datadog_services** - List APM services
   - Optional: `detailed_output` (boolean) - Include service details
   - Returns: Services with metadata and dependencies

10. **search_datadog_dashboards** - Search dashboards
    - Optional: `query` (string) - Dashboard search query
    - Optional: `max_queries_per_dashboard` (number) - Extract widget queries
    - Returns: Dashboards with metadata and widget queries

## Tool Usage Examples

In the examples below, `tool_name({...})` means: call that MCP tool with the given arguments.

### Searching Logs

**Find error logs:**
```javascript
search_datadog_logs({
  "query": "service:api env:prod status:error",
  "from": "now-1h",
  "to": "now"
})
// Returns: Error logs from API service in last hour
```

**Search with custom attributes:**
```javascript
search_datadog_logs({
  "query": "service:checkout @http.status_code:[400 TO 599]",
  "from": "now-1h",
  "to": "now",
  "extra_fields": ["@user.id", "@order.id", "@http.*"]
})
// Returns: HTTP errors with user and order context
```

### Querying Metrics

**Service response time:**
```javascript
get_datadog_metric({
  "query": "avg:trace.servlet.request.duration{service:api,env:prod} by {resource_name}",
  "from": "now-4h",
  "to": "now"
})
// Returns: Average response time per endpoint
```

**CPU usage by host:**
```javascript
get_datadog_metric({
  "query": "avg:system.cpu.user{env:prod} by {host}",
  "from": "now-1h",
  "to": "now"
})
// Returns: CPU usage for each production host
```

**Cloud costs:**
```javascript
get_datadog_metric({
  "query": "sum:all.cost{*} by {providername}.rollup(sum, daily)",
  "from": "now-30d",
  "to": "now",
  "use_cloud_cost": true
})
// Returns: Daily costs by cloud provider
```

### Searching Traces

**Find slow requests:**
```javascript
search_datadog_spans({
  "query": "service:api @duration:>100000000",  // >100ms in nanoseconds
  "from": "now-1h",
  "to": "now"
})
// Returns: Slow API requests with trace IDs
```

**Get full trace details:**
```javascript
get_datadog_trace({
  "trace_id": "7d5d747be160e280504c099d984bcfe0"
})
// Returns: Complete trace with all spans and timing
```

### RUM Analysis

**Find slow page loads:**
```javascript
search_datadog_rum_events({
  "query": "@type:view @view.loading_time:>3000",
  "from": "now-1h",
  "to": "now",
  "detailed_output": true
})
// Returns: Pages taking >3 seconds to load
```

**Frontend errors:**
```javascript
search_datadog_rum_events({
  "query": "@type:error @application.name:\"My App\" @device.type:mobile",
  "from": "now-1h",
  "to": "now"
})
// Returns: Mobile frontend errors
```

### Incident Management

**List active incidents:**
```javascript
search_datadog_incidents({
  "query": "state:(active OR stable)"
})
// Returns: Current incidents being worked on
```

**Get incident details:**
```javascript
get_datadog_incident({
  "incident_id": "12345"
})
// Returns: Full incident timeline and updates
```

### Monitor Search

**Find alerting monitors:**
```javascript
search_datadog_monitors({
  "query": "status:alert muted:false env:prod"
})
// Returns: Active unmuted alerts in production
```

## Combining Tools (Workflows)

### Workflow 1: Production Error Investigation

```javascript
// Step 1: Find recent errors in logs
const errorLogs = search_datadog_logs({
  "query": "service:checkout env:prod status:error",
  "from": "now-1h",
  "to": "now",
  "extra_fields": ["@error.message", "@user.id"]
})

// Step 2: Find related error traces
const errorSpans = search_datadog_spans({
  "query": "service:checkout status:error",
  "from": "now-1h",
  "to": "now"
})

// Step 3: Get full trace for first error
const fullTrace = get_datadog_trace({
  "trace_id": errorSpans[0].trace_id
})

// Step 4: Check if there's an active incident
const incidents = search_datadog_incidents({
  "query": "state:active"
})

// Step 5: Check related monitors
const monitors = search_datadog_monitors({
  "query": "tag:\"service:checkout\" status:alert"
})
```

### Workflow 2: Performance Degradation Analysis

```javascript
// Step 1: Identify slow requests
const slowSpans = search_datadog_spans({
  "query": "service:api @duration:>100000000",  // >100ms
  "from": "now-1h",
  "to": "now"
})

// Step 2: Check response time metrics
const latencyMetrics = get_datadog_metric({
  "query": "avg:trace.servlet.request.duration{service:api} by {resource_name}",
  "from": "now-4h",
  "to": "now"
})

// Step 3: Check infrastructure metrics
const cpuMetrics = get_datadog_metric({
  "query": "avg:system.cpu.user{service:api} by {host}",
  "from": "now-4h",
  "to": "now"
})

// Step 4: Check for deployment correlation
const deploymentLogs = search_datadog_logs({
  "query": "service:api @deployment.version:*",
  "from": "now-4h",
  "to": "now"
})

// Step 5: Get full trace of slowest request
const slowestTrace = get_datadog_trace({
  "trace_id": slowSpans[0].trace_id
})
```

### Workflow 3: User Experience Investigation

```javascript
// Step 1: Find slow page loads
const slowPages = search_datadog_rum_events({
  "query": "@type:view @view.loading_time:>3000",
  "from": "now-1h",
  "to": "now",
  "detailed_output": true
})

// Step 2: Check for frontend errors
const frontendErrors = search_datadog_rum_events({
  "query": "@type:error",
  "from": "now-1h",
  "to": "now"
})

// Step 3: Check backend API performance
const apiLatency = get_datadog_metric({
  "query": "avg:trace.servlet.request.duration{service:api,env:prod}",
  "from": "now-1h",
  "to": "now"
})

// Step 4: Check resource loading issues
const resourceErrors = search_datadog_rum_events({
  "query": "@type:resource @resource.status_code:[400 TO 599]",
  "from": "now-1h",
  "to": "now"
})
```

### Workflow 4: Service Dependency Analysis

```javascript
// Step 1: List all services
const services = search_datadog_services({
  "detailed_output": true
})

// Step 2: Find traces for a service
const serviceSpans = search_datadog_spans({
  "query": "service:frontend",
  "from": "now-1h",
  "to": "now"
})

// Step 3: Get full trace to see downstream calls
const dependencyTrace = get_datadog_trace({
  "trace_id": serviceSpans[0].trace_id
})

// Step 4: Check latency between services
const serviceLatency = get_datadog_metric({
  "query": "avg:trace.servlet.request.duration{env:prod} by {service}",
  "from": "now-4h",
  "to": "now"
})
```

## Query Syntax Guide

### Log Search Syntax

**Tags** (no @ prefix):
- `service:api` - Service name
- `env:prod` - Environment
- `status:error` - Log status level
- `host:web-1` - Hostname

**Attributes** (@ prefix required):
- `@http.status_code:500` - HTTP status
- `@user.id:abc123` - User identifier
- `@duration:>1000` - Duration in milliseconds
- `@error.message:"timeout"` - Error message

**Boolean operators:**
- AND (default): `service:api status:error`
- OR: `env:(prod OR staging)`
- Exclusion: `-status:info`

**Wildcards:**
- `service:web*` - Matches web-api, web-worker
- `@url:/api/*` - Matches any /api/ path

### Metric Query Syntax

**Structure:**
```
<AGGREGATOR>:<METRIC_NAME>{<SCOPE>} by {<GROUPING>}
```

**Aggregators:**
- `avg` - Average across series
- `sum` - Sum all series
- `min` / `max` - Min/max values
- `p95` / `p99` - Percentiles

**Examples:**
```
avg:system.cpu.user{env:prod} by {host}
sum:trace.requests.count{service:api}.rollup(sum, 300)
p95:trace.servlet.request.duration{env:prod}
```

### APM/Trace Query Syntax

**Reserved fields** (NO @ prefix):
- `service` - Service name
- `resource_name` - Endpoint/operation
- `operation_name` - Span operation
- `status` - ok or error
- `trace_id` - Specific trace

**Span attributes** (@ prefix required):
- `@http.status_code` - HTTP status
- `@http.method` - HTTP method
- `@duration` - Duration in **nanoseconds**
- `@error.message` - Error message

**Duration conversions:**
- 1ms = 1,000,000 nanoseconds
- 100ms = 100,000,000 nanoseconds
- 1s = 1,000,000,000 nanoseconds

**Examples:**
```
service:api status:error
service:api @duration:>100000000
operation_name:db.query @duration:>1000000000
```

### RUM Query Syntax

**Event types:**
- `@type:view` - Page views
- `@type:action` - User interactions
- `@type:error` - Frontend errors
- `@type:resource` - Resource loading
- `@type:vital` - Core Web Vitals

**Common attributes:**
- `@application.name` - RUM app name
- `@view.url_path` - Page URL
- `@view.loading_time` - Load duration (ms)
- `@device.type` - Device type
- `@browser.name` - Browser name
- `@user.id` - User identifier

**Examples:**
```
@type:view @view.loading_time:>3000
@type:error @browser.name:Safari
@type:resource @resource.status_code:[400 TO 599]
```

### Incident Query Syntax

**Fields:**
- `state` - active, stable, resolved
- `severity` - SEV-1, SEV-2, SEV-3, SEV-4, SEV-5
- `customer_impacted` - true or false

**Important:** Group multiple values of same field:
```
severity:(SEV-1 OR SEV-2)  ✅
severity:SEV-1 OR severity:SEV-2  ❌
```

**Examples:**
```
state:active
severity:(SEV-1 OR SEV-2) AND state:active
customer_impacted:true AND state:active
```

### Monitor Query Syntax

**Fields:**
- `status` - alert, warn, ok
- `muted` - true or false
- `tag` - Monitor tags
- `env` - Environment
- `priority` - p1, p2, etc.

**Examples:**
```
status:alert muted:false
priority:(p1 OR p2)
tag:"service:api" status:alert
```

## Best Practices

### ✅ Do:

- **Start with narrow time ranges** (15m-1h) and expand if needed
- **Use unified service tags** (service, env, version) together
- **Filter by service first** to scope queries
- **Use @ prefix correctly** (attributes yes, reserved fields no)
- **Remember duration units** (nanoseconds for spans, milliseconds for logs/RUM)
- **Group similar logs** with `group_by_message: true`
- **Set appropriate max_tokens** (5000 for overview, 50000 for details)
- **Use extra_fields/custom_attributes** for custom data
- **Check incidents first** when investigating issues

### ❌ Don't:

- **Use very long time ranges** without reason (expensive and slow)
- **Forget @ prefix** for log/span attributes
- **Use @ prefix** for reserved trace fields (service, status, etc.)
- **Forget duration conversions** (5ms = 5,000,000 nanoseconds)
- **Use wildcards inside quotes** (they become literal)
- **Skip escaping special characters** (: = / \ etc.)
- **Use excessive free-text searches** (use structured tags instead)
- **Ignore unified service tagging** (always include service, env, version)
- **Query without time filters** (expensive and slow)

## Troubleshooting

### Error: "No results found"
**Cause:** Filters too restrictive or wrong field names
**Solution:**
1. Widen time range
2. Check field names (use @ for attributes)
3. Verify case-sensitivity
4. Use wildcards for partial matches

### Error: "Query timeout"
**Cause:** Query too expensive or time range too large
**Solution:**
1. Narrow time range (start with now-1h)
2. Add specific filters (service, env)
3. Reduce aggregation cardinality
4. Use head_limit to restrict results

### Error: "Invalid query syntax"
**Cause:** Malformed query string
**Solution:**
1. Check @ prefix usage
2. Escape special characters (: = / \)
3. Use double quotes for strings with spaces
4. Group OR conditions: `field:(value1 OR value2)`

### Error: "Trace not found"
**Cause:** Invalid trace ID or trace expired
**Solution:**
1. Verify trace_id format (hex string)
2. Check if trace is within retention period
3. Ensure trace exists in correct environment

## Configuration

This plugin's `mcp.json` connects to the Datadog remote MCP server (streamable HTTP) at `https://mcp.datadoghq.com/v1/mcp`, the US1 endpoint. Nothing needs to be installed locally.

**Authentication:**

1. **OAuth 2.0 (recommended):** Your MCP client starts the login flow when the server connects. Complete the OAuth login flow when prompted. You don't manage long-lived credentials.
2. **Personal or Service Access Token:** When OAuth is not possible, for example on a server or in CI, pass the token as a bearer token in the `Authorization` header. No API key is required.
3. **API key and application key:** Alternatively, provide a Datadog API key and application key as the `DD_API_KEY` and `DD_APPLICATION_KEY` HTTP headers. Use a scoped key pair from a service account that has only the required permissions.

Don't commit tokens or keys to a shared `mcp.json`.

**Other Datadog sites:** The bundled endpoint is for US1. On another site, point the server at that site's endpoint:
- US3: `https://mcp.us3.datadoghq.com/v1/mcp`
- US5: `https://mcp.us5.datadoghq.com/v1/mcp`
- EU: `https://mcp.datadoghq.eu/v1/mcp`
- AP1: `https://mcp.ap1.datadoghq.com/v1/mcp`
- AP2: `https://mcp.ap2.datadoghq.com/v1/mcp`
- UK1: `https://mcp.uk1.datadoghq.com/v1/mcp`

The US1-FED and US2-FED sites are not supported. For client-specific setup, toolsets and other options, see [Set Up the Datadog MCP Server](https://docs.datadoghq.com/bits_ai/mcp_server/setup/).

## Tips

1. **Start narrow** - Use 15m-1h time ranges, expand if needed
2. **Use the [datadog-query-syntax](../datadog-query-syntax/SKILL.md) skill** - Comprehensive syntax guide with examples
3. **Check incidents first** - Active incidents often point to root cause
4. **Leverage unified tags** - Always use service, env, version together
5. **Group logs** - Use `group_by_message` to reduce duplicate entries
6. **Get full traces** - Use trace_id from spans to get complete picture
7. **Monitor your monitors** - Check alert status during investigations
8. **Analyze dependencies** - Use full traces to understand service relationships
9. **Remember units** - Nanoseconds for spans, milliseconds for logs/RUM

---

**Server:** Datadog remote MCP server (streamable HTTP)  
**Source:** Official Datadog  
**License:** Apache 2.0  
**Connection:** Remote MCP server with OAuth 2.0 authentication (or access token / API and application keys)
