---
name: "datadog-query-syntax"
description: "Apply Datadog query syntax and best practices for logs, metrics, APM spans, RUM events, incidents and monitors when calling the Datadog MCP tools. Use when composing or debugging a Datadog search query, choosing time ranges, applying unified service tags, or avoiding common query mistakes."
metadata:
  author: "Datadog"
  version: "1.0.0"
---

# Datadog MCP Server Query Guide

This skill provides comprehensive guidance for using the Datadog MCP (Model Context Protocol) server to query observability data including logs, metrics, traces, RUM events, incidents, and more.

## When to Use the Datadog MCP Server

Use Datadog MCP tools when you need to:
- **Investigate production issues**: Errors, performance degradation, service outages
- **Analyze application behavior**: User experience, service dependencies, resource utilization
- **Monitor system health**: Infrastructure metrics, service status, host information
- **Track incidents**: Active incidents, incident history, severity analysis
- **Optimize performance**: Slow queries, high latency, resource bottlenecks
- **Analyze costs**: Cloud spending, resource allocation, cost trends
- **Debug specific requests**: Trace analysis, span details, distributed tracing
- **Set up services and instrumentation**: Look up how to configure services for Datadog monitoring, add APM, logs, or RUM instrumentation
- **Look up Datadog platform functionality**: Understand features, integrations, configuration options, and best practices

## Core Principles

### 1. Start Narrow, Expand if Needed
Always begin with narrow time ranges and specific queries, then expand:
- Start: `now-15m` or `now-1h`
- Expand to: `now-24h` or `now-7d` if needed
- Narrower ranges = faster queries and more relevant results

### 2. Use Unified Service Tagging
Always query with these three tags together when available:
- `service`: Application/service name
- `env`: Environment (production, staging, dev)
- `version`: Deployed version (semantic version or git SHA)

### 3. Prefer Structured Queries
Use tag/attribute searches over free-text searches for better performance:
- Good: `service:checkout env:prod status:error`
- Avoid: `"checkout error in production"`

---

## Query Syntax Fundamentals

These concepts apply across most Datadog query types:

### Boolean Operators (Case-Sensitive!)
- **AND** (default): Both conditions must match
  - `service:api status:error` (implicit AND)
  - `service:api AND env:prod` (explicit AND)
- **OR**: Either condition can match
  - `env:(prod OR staging)` ← Preferred for same field
  - `service:api OR service:worker`
- **- (exclusion)**: Exclude matching results
  - `service:api -status:info`
  - `-version:beta`

### Wildcards
- **`*`**: Multi-character wildcard (only works outside quotes)
  - `service:web*` matches `web-api`, `web-worker`
  - `@http.url:/api/*` matches any `/api/` endpoint
- **`?`**: Single-character wildcard
  - `@hostname:web-?` matches `web-1`, `web-2`

### Special Characters and Escaping
Escape these characters: `?`, `>`, `<`, `:`, `=`, `"`, `~`, `/`, `\`
- Use backslash `\` or double quotes:
  - `@message:hello\:world` or `@message:"hello:world"`
  - `@url:https\:\/\/example.com\/api\-v1\/*`

### Numerical Ranges
- Comparison: `<`, `>`, `<=`, `>=`
  - `@http.status_code:>=400`
- Ranges: `[x TO y]`
  - `@http.status_code:[400 TO 499]`

### @ Prefix Rules
- **Use @ prefix**: For log/span attributes (`@http.status_code`, `@user.id`)
- **NO @ prefix**: For reserved trace fields (`service`, `resource_name`, `operation_name`, `status`, `trace_id`, `type`)
- **NO @ prefix**: For tags (`env:prod`, `host:web-1`)

---

## Log Search Query Syntax

### Tags vs Attributes
- **Tags**: Direct format `key:value`
  - Examples: `env:prod`, `service:api`, `host:web-1`
- **Attributes**: Use `@` prefix for log-specific fields
  - Examples: `@http.status_code:500`, `@user.id:123`, `@error.message:"timeout"`

### Common Examples
```
# Error logs from production API service
service:api env:prod status:error

# 4xx or 5xx HTTP errors
@http.status_code:[400 TO 599]

# Database queries taking over 1 second
service:database @duration:>1000

# Specific user's session
@user.id:abc123

# All logs except health checks
service:api -@url:/health

# Search across multiple services
(service:api OR service:worker) AND status:error

# URL pattern matching
@http.url:/api/v*/users/*
```

### Best Practices for Logs
- Use `status:error` to find errors quickly
- Filter by `service` first to narrow scope
- Use `group_by_message: true` to reduce duplicate log entries
- Set `max_tokens` appropriately (5000-10000 for overview, 20000-50000 for details)
- Specify `extra_fields` array for custom attributes (use wildcards like `experiments*`)

---

## Metrics Query Syntax

Use `get_datadog_metric` with metric query strings:

### Basic Structure
```
<AGGREGATOR>:<METRIC_NAME>{<SCOPE>} by {<GROUPING_TAGS>}
```

### Space Aggregators
Combine multiple timeseries into one:
- **avg**: Average across all series
- **sum**: Sum all series
- **min**: Minimum value
- **max**: Maximum value
- **count**: Count of datapoints

### Scope (Filter)
Filter which hosts/services to include:
- `{*}` - All sources
- `{env:prod}` - Specific tag
- `{env:prod,service:api}` - Multiple tags (AND logic)
- `{host:web-1}` - Specific host

### Grouping
Split metrics by tag values using `by {tag1,tag2}`:
```
avg:system.cpu.user{env:prod} by {host}
```
Returns separate series for each host in production.

### Rollup (Time Aggregation)
Control how datapoints are aggregated over time:
```
.rollup(<AGGREGATOR>, <INTERVAL_SECONDS>)
```

Aggregators: `avg`, `sum`, `min`, `max`, `count`

Examples:
- `.rollup(avg, 60)` - Average over 1-minute buckets
- `.rollup(sum, 3600)` - Sum over 1-hour buckets
- `.rollup(max, 300)` - Max over 5-minute buckets

### Complete Examples
```
# Average CPU per host in production
avg:system.cpu.user{env:prod} by {host}

# Total requests per service, 5-minute buckets
sum:trace.requests.count{env:prod} by {service}.rollup(sum, 300)

# 95th percentile latency across all services
p95:trace.servlet.request.duration{env:prod}

# Memory usage with hourly averages
avg:system.mem.used{env:prod} by {host}.rollup(avg, 3600)
```

### Output Modes
- **Binned data** (default): 20 statistical buckets with min/max/avg
  - Fast, good for trends and patterns
  - Use for timeframes > 1 hour
- **Raw/CSV data** (`raw_data: true`): Exact datapoint values
  - Use for debugging short-lived issues
  - Best for timeframes < 45 minutes

### Cloud Cost Management
Set `use_cloud_cost: true` for cost queries:
```
# Daily costs by provider
sum:all.cost{*} by {providername}.rollup(sum, daily)

# Monthly total costs
sum:all.cost{*}.rollup(sum, monthly)

# AWS costs for specific resource
sum:aws.cost.net.amortized.shared.resources.allocated{aws_resource_id:xyz}.rollup(sum, daily)
```

### Best Practices for Metrics
- Use appropriate aggregators (avg for gauges, sum for counters)
- Apply rollup for longer time ranges to reduce data points
- Use `by {tag}` to identify specific problematic hosts/services
- Use binned data for trends, raw data for debugging

---

## APM/Trace Query Syntax

Use `search_datadog_spans` for distributed trace analysis:

### Reserved Attributes (NO @ prefix)
- `service` - Service name
- `resource_name` - Resource path/operation
- `operation_name` - Span operation type
- `status` - Span status (ok, error)
- `trace_id` - Specific trace ID
- `type` - Span type (web, db, cache, custom)

### Span Attributes (@ prefix required)
- `@http.status_code` - HTTP status
- `@http.method` - HTTP method (GET, POST, etc.)
- `@http.url` - Request URL
- `@error.message` - Error message
- `@error.type` - Error type/class
- `@duration` - Span duration in **nanoseconds**
- Custom attributes: `@user.id`, `@order.total`, etc.

### Duration Queries (Nanoseconds!)
Critical: Duration is in nanoseconds, not milliseconds!
- 1ms = 1,000,000 nanoseconds
- 5ms = 5,000,000 nanoseconds
- 100ms = 100,000,000 nanoseconds

Examples:
```
# Spans taking more than 5ms
@duration:>5000000

# Spans between 1ms and 10ms
@duration:[1000000 TO 10000000]

# Very slow database queries (>1 second)
operation_name:db.query @duration:>1000000000
```

### Complete Examples
```
# All errors in checkout service
service:checkout status:error

# Slow API requests
service:api resource_name:/api/* @duration:>100000000

# Database queries with errors
operation_name:db.query status:error

# HTTP 5xx errors
service:web @http.status_code:[500 TO 599]

# Multiple span types
type:(http OR rpc OR db)

# Exclude health checks
service:api -resource_name:/health

# Specific error type
@error.type:"TimeoutException"
```

### Retrieving Full Traces
Use `get_datadog_trace` with a specific `trace_id`:
```
trace_id: "7d5d747be160e280504c099d984bcfe0"
```
Returns all spans in the trace with detailed timing and relationships.

### Best Practices for APM
- Filter by `service` first to scope your search
- Use `@duration` for performance investigations (remember nanoseconds!)
- Combine `service` and `resource_name` to target specific endpoints
- Use `custom_attributes` parameter with wildcards for custom span tags
- Find trace IDs from spans, then use `get_datadog_trace` for full details

---

## RUM Event Query Syntax

Use `search_datadog_rum_events` for Real User Monitoring data:

### Event Types
Filter by `@type`:
- `@type:view` - Page views
- `@type:action` - User interactions (clicks, taps)
- `@type:error` - Frontend errors
- `@type:resource` - Resource loading (JS, CSS, images)
- `@type:long_task` - Long-running tasks (>50ms)
- `@type:vital` - Core Web Vitals

### Common Attributes
- `@application.name` - RUM application name
- `@view.url_path` - Page URL path
- `@view.loading_time` - Page load duration
- `@session.type` - Session type (user, synthetics)
- `@device.type` - Device type (mobile, tablet, desktop)
- `@browser.name` - Browser (Chrome, Firefox, Safari)
- `@user.id` - User identifier
- `@error.message` - Error message
- `@error.source` - Error origin (network, source, custom)
- `@geo.country` - User country

### Performance Metrics
Use ranges for performance analysis:
```
# Slow page loads (>3 seconds)
@type:view @view.loading_time:>3000

# Loading time between 1-3 seconds
@view.loading_time:[1000 TO 3000]

# Large Contentful Paint (Core Web Vital)
@type:vital @view.largest_contentful_paint:>2500
```

### Complete Examples
```
# Frontend errors for specific user
@type:error @user.id:abc123

# Slow mobile page loads
@type:view @device.type:mobile @view.loading_time:>5000

# Failed resource loads
@type:resource @resource.status_code:[400 TO 599]

# High interaction latency
@type:action @action.loading_time:>1000

# Safari-specific errors
@type:error @browser.name:Safari
```

### Best Practices for RUM
- Use `detailed_output: true` for comprehensive event data
- Set higher `max_tokens` (50000+) for detailed analysis
- Filter by `@application.name` and `env` first
- Use wildcards in `@view.url_path` to match patterns

---

## Incident Search Query Syntax

Use `search_datadog_incidents` to find and track incidents:

### Search Fields
- `state` - Incident state
  - Values: `active`, `stable`, `resolved`
- `severity` - Incident severity
  - Values: `SEV-1`, `SEV-2`, `SEV-3`, `SEV-4`, `SEV-5`
- `customer_impacted` - Customer impact flag
  - Values: `true`, `false`
- `title` - Incident title (supports partial matches)
- `team` - Team responsible

### Boolean Logic
Supports **AND**, **OR**, and field-grouped OR syntax:
```
# Standard AND
state:active AND severity:SEV-1

# Standard OR
state:active OR state:stable

# Field-grouped OR (REQUIRED for same field!)
severity:(SEV-1 OR SEV-2 OR SEV-3)

# Combined
state:active AND severity:(SEV-1 OR SEV-2)
```

**Important**: When querying multiple values of the same field, you MUST group them:
- ✅ Correct: `severity:(SEV-1 OR SEV-2)`
- ❌ Wrong: `severity:SEV-1 OR severity:SEV-2`

### Time Filtering
Use `from` and `to` parameters to filter by incident creation time:
```
from: "now-7d"
to: "now"
query: "state:(active OR stable)"
```

### Common Examples
```
# Default query (recommended starting point)
state:active

# All active incidents
state:(active OR stable)

# High-severity incidents
severity:(SEV-1 OR SEV-2) AND state:active

# Customer-impacting incidents
customer_impacted:true AND state:active

# Resolved incidents in last 7 days
state:resolved
from: now-7d
```

### Best Practices for Incidents
- Default query is `state:active` - use this for current issues
- For ongoing work, use `state:(active OR stable)` to include post-mitigation
- Always group multiple values of same field together

---

## Monitor Search Query Syntax

Use `search_datadog_monitors` to find alerting rules:

### Search Fields
- `id` - Monitor ID: `id:167097893`
- `title` - Monitor name: `title:my-monitor`
- `status` - Alert status: `status:alert`, `status:warn`, `status:ok`
- `muted` - Mute status: `muted:true`, `muted:false`
- `tag` - Monitor tags: `tag:"monitor_gate:true"`
- `env` - Environment: `env:prod`
- `team` - Team: `team:backend`
- `priority` - Priority: `priority:p1`, `priority:p2`, etc.
- `notification` - Notification target: `notification:slack-logs-team-ops`
- `type` - Monitor type: `type:metric`, `type:log`, `type:apm`

### Boolean Logic
Supports **AND**, **OR**, and parentheses:
```
# Multiple conditions
status:alert muted:false

# OR logic
priority:p1 OR priority:p2

# Complex queries
priority:p2 AND (title:api OR title:database)
```

### Complete Examples
```
# All alerting monitors
status:alert

# Unmuted alerts in production
status:alert muted:false env:prod

# High-priority monitors
priority:(p1 OR p2)

# Specific notification channel
notification:slack-alerts

# Service-specific monitors
tag:"service:api"
```

### Best Practices for Monitors
- Start with `status:alert` to find active alerts
- Filter by `env` to scope to specific environment
- Use `muted:false` to exclude silenced alerts

---

## Common Tags Reference

### Unified Service Tags (Always Use Together)
These three tags correlate data across all Datadog products:
- **service** - Application/service name
  - Examples: `checkout-api`, `user-service`, `payment-worker`
- **env** - Environment
  - Examples: `production`, `staging`, `development`, `qa`
- **version** - Deployed version
  - Examples: `v1.2.3`, `abc123` (git SHA), `2024-01-15`

### Infrastructure Tags
- **host** - Host/instance name
- **availability-zone** - AWS/cloud AZ
- **region** - Cloud region
- **instance-type** - Instance size/type

### Application Tags
- **team** - Owning team
- **source** - Technology source (logs)
  - Examples: `nginx`, `postgres`, `redis`, `python`
- **status** - Status level
  - Log values: `info`, `warn`, `error`, `debug`
  - Span values: `ok`, `error`

### Tag Usage in Queries
```
# Single value
env:production

# Multiple values (OR)
env:(production OR staging)

# Wildcards
service:web*

# Exclusion
-env:development

# Multiple tags (AND)
service:api env:prod team:backend
```

---

## Time Range Best Practices

### Supported Formats
1. **Relative time** (recommended):
   - `now-15m`, `now-1h`, `now-24h`, `now-7d`
   - Units: `m` (minutes), `h` (hours), `d` (days), `w` (weeks), `mo` (months)
2. **ISO 8601**: `2023-01-01T00:00:00Z`
3. **Unix timestamp** (milliseconds): `1672531200000`

### Recommended Workflow
Start narrow and expand based on findings:

1. **Recent issues** (start here):
   ```
   from: "now-15m"  or  "now-1h"
   to: "now"
   ```

2. **Past day** (if nothing found):
   ```
   from: "now-24h"
   to: "now"
   ```

3. **Historical analysis**:
   ```
   from: "now-7d"
   to: "now"
   ```

### Tool-Specific Defaults
- **Logs**: Default `now-1h`
- **RUM**: Default `now-15m`
- **Spans**: Default `now-1h`
- **Incidents**: No default time filter (shows all)

---

## Common Use Cases, Anti-Patterns and Performance Tips

Step-by-step investigation examples (production errors, performance degradation, user experience, incidents, service dependencies), common mistakes to avoid, and query/result-size performance tips are in [references/use-cases-and-pitfalls.md](references/use-cases-and-pitfalls.md).

---

## Additional Resources

### Dashboard Analysis
Use `search_datadog_dashboards` to:
- Find existing dashboards by name or tags
- Extract metric queries from dashboards
- Discover team-maintained visualizations
- Set `max_queries_per_dashboard` to see widget queries

---

## Summary Checklist

Before making Datadog queries, ensure you:
- ✅ Start with narrow time ranges (15m-1h)
- ✅ Include unified service tags (service, env, version)
- ✅ Use appropriate tool for the data type
- ✅ Apply @ prefix correctly (attributes yes, reserved fields no)
- ✅ Escape special characters in queries
- ✅ Use grouped OR syntax for multiple values of same field
- ✅ Consider duration is in nanoseconds for APM
- ✅ Set appropriate max_tokens for expected result size
- ✅ Use structured tag queries instead of free-text when possible

This skill represents the essential knowledge for effectively querying Datadog observability data through the MCP server. Follow these patterns for accurate, performant, and actionable results.