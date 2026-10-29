---
name: "splunk"
displayName: "Splunk Observability"
description: "Search logs, analyze events, query metrics, investigate security incidents, and manage alerts in Splunk for production debugging and operational intelligence"
keywords: ["splunk", "spl", "splunk-cloud", "splunk-enterprise", "siem", "indexed-search", "sourcetype"]
author: "Community"
---

# Splunk Observability Power

## Overview

The Splunk Observability Power connects to your Splunk platform for log analysis, event correlation, security investigation, metrics querying, and operational intelligence. Use SPL (Search Processing Language) to query indexed data across all your sources.

**Key capabilities:**
- **Log Search**: Query and analyze logs across all indexed sources
- **Event Correlation**: Correlate events across multiple data sources and time ranges
- **Security Investigation**: SIEM capabilities for threat detection and incident response
- **Metrics & Statistics**: Compute statistics, trends, and anomalies from machine data
- **Alerts & Reports**: Manage saved searches, alerts, and scheduled reports
- **Dashboards**: Query and retrieve dashboard panels and visualizations
- **Knowledge Objects**: Use lookups, field extractions, and data models
- **Index Management**: Search across multiple indexes with fine-grained filtering

**Authentication**: Requires Splunk instance URL and authentication token.

## Onboarding

### Prerequisites

1. **Splunk instance** - Splunk Cloud or Splunk Enterprise with API access enabled (port 8089)
2. **Authentication token** - A Splunk auth token with search capabilities
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your Splunk instance URL and token
3. Test with: *"Search for errors in the last hour"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_SPLUNK_INSTANCE.splunkcloud.com:8089`**: Your Splunk instance management URL with port 8089.
 - **How to get it:** Log in to Splunk Web → Settings → Server settings → General settings → note the management URI. For Splunk Cloud, it's typically `https://your-stack.splunkcloud.com:8089`

- **`YOUR_SPLUNK_AUTH_TOKEN`**: Your Splunk authentication token.
 - **How to get it:**
    1. Log in to Splunk Web
    2. Go to Settings → Tokens
    3. Click "New Token"
    4. Set audience and expiration
    5. Copy the generated token value

## Available Steering Files

- **steering/steering.md** - Complete SPL syntax guide with query patterns, workflows, and troubleshooting

## Available MCP Servers

### splunk
**Package:** `@splunk/mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **search** - Execute an SPL search query
  - Required: `query` (string) - SPL search query
  - Optional: `earliest_time` (string) - Start time (default: "-1h")
  - Optional: `latest_time` (string) - End time (default: "now")
  - Optional: `max_results` (number) - Maximum results to return
  - Optional: `output_mode` (string) - json, csv, xml
  - Returns: Search results with fields and events

2. **get_indexes** - List available indexes
  - Returns: Index names with event counts and sizes

3. **get_saved_searches** - List saved searches and alerts
  - Optional: `owner` (string) - Filter by owner
  - Returns: Saved searches with schedules and actions

4. **get_search_job_status** - Check async search job status
  - Required: `job_id` (string) - Search job ID
  - Returns: Job status, progress, and result count

5. **get_search_results** - Get results from completed search job
  - Required: `job_id` (string) - Search job ID
  - Optional: `offset` (number) - Result offset for pagination
  - Optional: `count` (number) - Number of results
  - Returns: Search results

6. **list_alerts** - List triggered alerts
  - Optional: `severity` (string) - Filter by severity
  - Returns: Alert list with trigger details

7. **get_field_summary** - Get field statistics for an index
  - Required: `index` (string) - Index name
  - Optional: `earliest_time` (string) - Time range start
  - Returns: Field names, types, and value distributions

8. **list_dashboards** - List available dashboards
  - Optional: `query` (string) - Search filter
  - Returns: Dashboard list with metadata

## Tool Usage Examples

### Log Search

**Find error events:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=main sourcetype=application level=ERROR | head 100",
  "earliest_time": "-1h",
  "latest_time": "now"
})
```

**Search with statistics:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=web sourcetype=access_combined status>=400 | stats count by status, uri_path | sort -count",
  "earliest_time": "-4h",
  "latest_time": "now"
})
```

**Time-series analysis:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=main sourcetype=application | timechart span=5m count by level",
  "earliest_time": "-6h",
  "latest_time": "now"
})
```

### Security Investigation

**Failed login attempts:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=security sourcetype=auth action=failure | stats count by src_ip, user | where count > 5 | sort -count",
  "earliest_time": "-24h",
  "latest_time": "now"
})
```

**Suspicious network activity:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=network sourcetype=firewall action=blocked | stats count by src_ip, dest_port | where count > 100",
  "earliest_time": "-1h",
  "latest_time": "now"
})
```

### Infrastructure Monitoring

**Host performance:**
```javascript
usePower("splunk", "splunk", "search", {
  "query": "index=os sourcetype=cpu | stats avg(cpu_load_percent) as avg_cpu, max(cpu_load_percent) as max_cpu by host | where avg_cpu > 80",
  "earliest_time": "-30m",
  "latest_time": "now"
})
```

## Combining Tools (Workflows)

### Workflow 1: Production Error Investigation

```javascript
// Step 1: Find recent errors
const errors = usePower("splunk", "splunk", "search", {
  "query": "index=main sourcetype=application level=ERROR | stats count by message, host | sort -count | head 10",
  "earliest_time": "-1h"
})

// Step 2: Get error timeline
const timeline = usePower("splunk", "splunk", "search", {
  "query": "index=main sourcetype=application level=ERROR | timechart span=5m count by host",
  "earliest_time": "-4h"
})

// Step 3: Correlate with deployments
const deploys = usePower("splunk", "splunk", "search", {
  "query": "index=deploy sourcetype=deployment | table _time, service, version, environment, deployer",
  "earliest_time": "-4h"
})

// Step 4: Check related service logs
const serviceLogs = usePower("splunk", "splunk", "search", {
  "query": "index=main sourcetype=application service=payment-api (level=ERROR OR level=WARN) | transaction session_id maxspan=5m | table _time, session_id, level, message",
  "earliest_time": "-1h"
})

// Step 5: Check alerts
const alerts = usePower("splunk", "splunk", "list_alerts", {
  "severity": "critical"
})
```

### Workflow 2: Security Incident Response

```javascript
// Step 1: Identify suspicious activity
const suspicious = usePower("splunk", "splunk", "search", {
  "query": "index=security (action=failure OR action=blocked) | stats count by src_ip | where count > 10 | sort -count",
  "earliest_time": "-1h"
})

// Step 2: Investigate top offender
const investigation = usePower("splunk", "splunk", "search", {
  "query": "index=security src_ip=10.0.0.50 | stats count by action, dest, dest_port, user | sort -count",
  "earliest_time": "-24h"
})

// Step 3: Check for lateral movement
const lateral = usePower("splunk", "splunk", "search", {
  "query": "index=security src_ip=10.0.0.50 action=success | stats dc(dest) as unique_targets, values(dest) as targets by user",
  "earliest_time": "-24h"
})

// Step 4: Timeline of activity
const activityTimeline = usePower("splunk", "splunk", "search", {
  "query": "index=security src_ip=10.0.0.50 | timechart span=1h count by action",
  "earliest_time": "-7d"
})
```

### Workflow 3: Performance Degradation Analysis

```javascript
// Step 1: Check response times
const latency = usePower("splunk", "splunk", "search", {
  "query": "index=web sourcetype=access_combined | stats avg(response_time) as avg_rt, p95(response_time) as p95_rt, count by uri_path | where avg_rt > 2000 | sort -avg_rt",
  "earliest_time": "-1h"
})

// Step 2: Compare with baseline
const baseline = usePower("splunk", "splunk", "search", {
  "query": "index=web sourcetype=access_combined | timechart span=1h avg(response_time) as current | appendcols [search index=web sourcetype=access_combined earliest=-8d latest=-7d | timechart span=1h avg(response_time) as baseline]",
  "earliest_time": "-1d"
})

// Step 3: Check infrastructure
const infra = usePower("splunk", "splunk", "search", {
  "query": "index=os (sourcetype=cpu OR sourcetype=memory) | stats avg(cpu_load_percent) as cpu, avg(mem_used_percent) as memory by host | where cpu > 80 OR memory > 90",
  "earliest_time": "-30m"
})
```

## SPL Query Syntax Guide

### Basic Structure
```spl
index=<index> sourcetype=<sourcetype> <search_terms>
| <command1> <arguments>
| <command2> <arguments>
```

### Common Commands
- `search` - Filter events (implicit first command)
- `stats` - Compute statistics (count, avg, sum, min, max, dc, values, list)
- `timechart` - Time-series aggregation
- `chart` - Pivot table aggregation
- `table` - Select and display fields
- `eval` - Create calculated fields
- `where` - Filter with expressions
- `sort` - Order results
- `head` / `tail` - Limit results
- `dedup` - Remove duplicates
- `transaction` - Group related events
- `rex` - Extract fields with regex
- `lookup` - Enrich with lookup tables
- `join` - Join results from subsearches
- `append` / `appendcols` - Combine results

### Time Modifiers
- `-1h` / `-30m` / `-24h` / `-7d` - Relative time
- `@d` - Snap to day boundary
- `-1d@d` - Yesterday start
- `2024-01-15T10:00:00` - Absolute time

### Statistical Functions
- `count` - Event count
- `avg(field)` - Average
- `sum(field)` - Total
- `min(field)` / `max(field)` - Extremes
- `dc(field)` - Distinct count
- `values(field)` - Unique values
- `list(field)` - All values
- `p95(field)` / `p99(field)` - Percentiles
- `stdev(field)` - Standard deviation
- `median(field)` - Median value

### Common Patterns

**Error rate over time:**
```spl
index=main sourcetype=application
| timechart span=5m count(eval(level="ERROR")) as errors, count as total
| eval error_rate = round(errors/total*100, 2)
```

**Top N analysis:**
```spl
index=web sourcetype=access_combined status>=400
| stats count by uri_path, status
| sort -count | head 20
```

**Transaction correlation:**
```spl
index=main sourcetype=application
| transaction request_id maxspan=30s
| where duration > 5
| table _time, request_id, duration, eventcount
```

## Best Practices

### ✅ Do:
- **Specify index and sourcetype** - Dramatically improves search performance
- **Use time ranges** - Always constrain with earliest/latest
- **Filter early** - Put restrictive terms before pipes
- **Use stats over raw events** - Aggregations are faster than scanning
- **Use field extractions** - Use indexed fields when available
- **Use timechart for trends** - Visualize patterns over time
- **Transaction for correlation** - Group related events by ID
- **Limit results** - Use head/limit to control output size

### ❌ Don't:
- **Search all indexes** - Always specify `index=`
- **Use wildcards at start** - `*error` is slow; `error*` is fast
- **Skip time constraints** - Unbounded searches are expensive
- **Over-use join** - Prefer stats with BY clause instead
- **Forget field names** - Check with `| fieldsummary` first
- **Use raw search for analytics** - Use stats/timechart commands
- **Ignore search job limits** - Large searches may timeout

## Configuration

**Authentication Required**: Splunk instance URL and authentication token

**Setup Steps:**

1. **Get Splunk Credentials:**
  - Log in to Splunk Web
  - Go to Settings → Tokens (or Settings → Users for basic auth)
  - Create a new authentication token with appropriate roles

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "splunk": {
         "command": "npx",
         "args": ["-y", "@splunk/mcp-server"],
         "env": {
           "SPLUNK_URL": "https://your-instance.splunkcloud.com:8089",
           "SPLUNK_TOKEN": "your-auth-token"
         }
       }
     }
   }
   ```

3. **For Splunk Enterprise (on-prem):**
   ```json
   "env": {
     "SPLUNK_URL": "https://splunk.yourcompany.com:8089",
     "SPLUNK_TOKEN": "your-auth-token",
     "SPLUNK_VERIFY_SSL": "false"
   }
   ```

## Tips

1. **Always specify index** - `index=main` is 10x faster than searching all
2. **Use sourcetype** - Further narrows search scope
3. **Filter before stats** - Put WHERE conditions before pipe commands
4. **Use timechart for trends** - Better than raw event scanning
5. **Use transactions** - Group related events by session/request ID
6. **Check field summary** - Use `| fieldsummary` to discover available fields
7. **Use eval for calculations** - Create derived fields inline
8. **Compare time periods** - Use `| appendcols` with different time ranges
9. **Save frequent searches** - Use saved searches for repeated queries
10. **Monitor search performance** - Check job inspector for slow queries

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@splunk/mcp-server`
**Source:** Splunk
**License:** MIT-0
**Documentation:** https://docs.splunk.com/Documentation/Splunk
