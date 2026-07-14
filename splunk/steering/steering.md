# Splunk SPL Steering Guide

This steering file covers the Splunk MCP server to query logs, events, metrics, and security data using SPL (Search Processing Language).

## When to Use the Splunk MCP Server

Use Splunk MCP tools when you need to:
- **Search logs**: Find application errors, warnings, and debug information
- **Investigate incidents**: Correlate events across multiple sources
- **Security analysis**: Detect threats, investigate breaches, audit access
- **Performance monitoring**: Analyze response times, throughput, resource usage
- **Operational intelligence**: Track deployments, changes, and system health
- **Compliance auditing**: Search for policy violations and access patterns

## Core Principles

### 1. Always Specify Index and Sourcetype
Every search should start with `index=` and ideally `sourcetype=`:
```spl
index=main sourcetype=application level=ERROR
```
This dramatically improves performance by limiting the data scanned.

### 2. Filter Early, Aggregate Late
Put the most restrictive conditions first:
```spl
# Good - filters before stats
index=web status>=400 | stats count by uri_path

# Bad - scans everything then filters
index=web | stats count by uri_path, status | where status >= 400
```

### 3. Use Appropriate Time Ranges
Start narrow and expand:
- Quick check: `-15m` to `-1h`
- Investigation: `-4h` to `-24h`
- Trend analysis: `-7d`
- Historical: Use specific timestamps

---

## SPL Command Reference

### Search & Filter Commands

#### search (implicit)
The first command in any query; filters raw events:
```spl
index=main sourcetype=application level=ERROR service=payment-api
```

#### where
Filter with expressions after transformations:
```spl
| stats count by host | where count > 100
```

#### dedup
Remove duplicate events:
```spl
| dedup user, src_ip | table _time, user, src_ip, action
```

#### rex
Extract fields with regex:
```spl
| rex field=message "user=(?<username>\w+)"
```

### Aggregation Commands

#### stats
Compute statistics:
```spl
| stats count, avg(response_time) as avg_rt, p95(response_time) as p95_rt by service
```

**Functions:** count, sum, avg, min, max, dc (distinct count), values, list, first, last, p50, p90, p95, p99, stdev, var, median, mode, range

#### timechart
Time-series aggregation:
```spl
| timechart span=5m count by level
| timechart span=1h avg(response_time) by service
```

**Span options:** 1s, 5s, 30s, 1m, 5m, 15m, 30m, 1h, 4h, 1d

#### chart
Pivot table:
```spl
| chart count over status by service
| chart avg(duration) over host by sourcetype
```

#### eventstats
Add statistics as new fields without reducing events:
```spl
| eventstats avg(response_time) as global_avg by service
| where response_time > global_avg * 2
```

#### streamstats
Running/cumulative statistics:
```spl
| streamstats count as event_num by session_id
| streamstats window=5 avg(response_time) as rolling_avg
```

### Transformation Commands

#### eval
Create calculated fields:
```spl
| eval duration_sec = duration / 1000
| eval status_category = case(status<300, "success", status<400, "redirect", status<500, "client_error", true(), "server_error")
| eval is_slow = if(response_time > 2000, "yes", "no")
```

**Functions:** case(), if(), coalesce(), null(), tonumber(), tostring(), len(), lower(), upper(), substr(), replace(), split(), mvcount(), mvindex(), now(), relative_time(), strftime(), strptime(), round(), ceil(), floor(), abs(), log(), pow(), sqrt()

#### rename
Rename fields:
```spl
| rename src_ip as source_address, dest_ip as destination_address
```

#### table
Select and order fields:
```spl
| table _time, host, service, level, message
```

#### fields
Include/exclude fields (faster than table for filtering):
```spl
| fields + _time, host, message
| fields - _raw, _indextime
```

### Correlation Commands

#### transaction
Group related events:
```spl
| transaction session_id maxspan=30m maxpause=5m
| where eventcount > 1
| table session_id, duration, eventcount
```

**Options:** maxspan, maxpause, startswith, endswith, maxevents

#### join
Join with subsearch results:
```spl
index=web status>=500
| join src_ip [search index=auth action=login | stats latest(user) by src_ip]
```

#### append / appendcols
Combine results:
```spl
# Append rows
| append [search index=main earliest=-2d latest=-1d | stats count as yesterday_count]

# Append columns (for comparison)
| appendcols [search index=main earliest=-2d latest=-1d | timechart span=1h count as baseline]
```

#### subsearch
Inline subsearch for filtering:
```spl
index=web [search index=auth action=failure | stats count by src_ip | where count > 5 | fields src_ip]
```

### Lookup & Enrichment

#### lookup
Enrich events with lookup tables:
```spl
| lookup geo_ip src_ip OUTPUT city, country, lat, lon
| lookup users_lookup user_id OUTPUT department, manager
```

#### inputlookup
Read lookup table directly:
```spl
| inputlookup known_bad_ips.csv | rename ip as src_ip
```

### Formatting Commands

#### sort
Order results:
```spl
| sort -count, +_time    # descending count, ascending time
| sort 10 -response_time  # top 10 by response time
```

#### head / tail
Limit results:
```spl
| head 50    # first 50 results
| tail 10    # last 10 results
```

#### fillnull
Replace null values:
```spl
| fillnull value=0 count, errors
| fillnull value="unknown" service
```

---

## Common Query Patterns

### Error Analysis

**Error rate over time:**
```spl
index=main sourcetype=application
| timechart span=5m count(eval(level="ERROR")) as errors, count as total
| eval error_rate = round(errors/total*100, 2)
```

**Top errors by message:**
```spl
index=main sourcetype=application level=ERROR
| stats count by message | sort -count | head 20
```

**Errors by service and host:**
```spl
index=main sourcetype=application level=ERROR
| stats count, dc(host) as affected_hosts, values(host) as hosts by service
| sort -count
```

**New errors (not seen before):**
```spl
index=main sourcetype=application level=ERROR earliest=-1h
| stats count by message
| join type=left message [search index=main sourcetype=application level=ERROR earliest=-8d latest=-1h | stats count as historical_count by message]
| where isnull(historical_count)
```

### Performance Analysis

**Response time percentiles:**
```spl
index=web sourcetype=access_combined
| stats count, avg(response_time) as avg_ms, p50(response_time) as p50, p95(response_time) as p95, p99(response_time) as p99 by uri_path
| sort -p99 | head 20
```

**Slow requests:**
```spl
index=web sourcetype=access_combined response_time>5000
| table _time, host, method, uri_path, status, response_time, user_agent
| sort -response_time
```

**Throughput analysis:**
```spl
index=web sourcetype=access_combined
| timechart span=1m count as requests_per_min by host
```

**Response time degradation detection:**
```spl
index=web sourcetype=access_combined
| timechart span=15m avg(response_time) as current_avg
| appendcols [search index=web sourcetype=access_combined earliest=-8d latest=-7d | timechart span=15m avg(response_time) as baseline_avg]
| eval degradation_pct = round((current_avg - baseline_avg) / baseline_avg * 100, 1)
| where degradation_pct > 50
```

### Security Investigation

**Brute force detection:**
```spl
index=security sourcetype=auth action=failure
| stats count, dc(user) as targeted_users, values(user) as users by src_ip
| where count > 10
| sort -count
```

**Privilege escalation:**
```spl
index=security sourcetype=auth (action=privilege_change OR action=role_change)
| table _time, user, src_ip, action, old_role, new_role
| sort -_time
```

**Data exfiltration indicators:**
```spl
index=network sourcetype=firewall direction=outbound
| stats sum(bytes_out) as total_bytes by src_ip, dest_ip
| eval total_mb = round(total_bytes/1024/1024, 2)
| where total_mb > 100
| sort -total_mb
```

**Account compromise timeline:**
```spl
index=security user=compromised_user
| transaction user maxspan=24h
| table _time, user, src_ip, action, dest, app
| sort _time
```

### Infrastructure Monitoring

**Host health overview:**
```spl
index=os sourcetype=cpu OR sourcetype=memory OR sourcetype=disk
| stats latest(cpu_load_percent) as cpu, latest(mem_used_percent) as memory, latest(disk_used_percent) as disk by host
| eval health = case(cpu>90 OR memory>95 OR disk>90, "critical", cpu>70 OR memory>80 OR disk>80, "warning", true(), "healthy")
| sort -cpu
```

**Container resource usage:**
```spl
index=containers sourcetype=docker_stats
| stats avg(cpu_percent) as avg_cpu, avg(mem_percent) as avg_mem, max(cpu_percent) as max_cpu by container_name
| where avg_cpu > 50 OR avg_mem > 70
| sort -avg_cpu
```

**Disk space trending:**
```spl
index=os sourcetype=disk
| timechart span=1d avg(disk_used_percent) by host
| predict disk_used_percent as predicted future_timespan=7d
```

### Application Tracing

**Slow transactions:**
```spl
index=apm sourcetype=traces duration>5000
| stats count, avg(duration) as avg_ms, max(duration) as max_ms by service, operation
| sort -avg_ms | head 20
```

**Error traces:**
```spl
index=apm sourcetype=traces status=error
| stats count by service, operation, error_type
| sort -count
```

**Service dependency map:**
```spl
index=apm sourcetype=traces
| stats count, avg(duration) as avg_latency by caller_service, callee_service
| sort -count
```

### Deployment Correlation

**Deploy impact analysis:**
```spl
index=main sourcetype=application level=ERROR
| timechart span=5m count as errors
| appendcols [search index=deploy | eval deploy_marker=1 | timechart span=5m sum(deploy_marker) as deploys]
| where deploys > 0 OR errors > 0
```

**Post-deploy error comparison:**
```spl
index=main sourcetype=application level=ERROR service=my-service
| stats count as current_errors
| appendcols [search index=main sourcetype=application level=ERROR service=my-service earliest=-2d latest=-1d | stats count as previous_errors]
| eval change_pct = round((current_errors - previous_errors) / previous_errors * 100, 1)
```

---

## Time Range Best Practices

### Relative Time Syntax
| Modifier | Meaning |
|----------|---------|
| `-15m` | 15 minutes ago |
| `-1h` | 1 hour ago |
| `-4h` | 4 hours ago |
| `-24h` or `-1d` | 1 day ago |
| `-7d` | 7 days ago |
| `-30d` | 30 days ago |
| `@d` | Beginning of today |
| `-1d@d` | Beginning of yesterday |
| `@w0` | Beginning of this week (Sunday) |
| `-1mon@mon` | Beginning of last month |

### Recommended Approach
1. **Active incident**: `-15m` to `-1h`
2. **Recent investigation**: `-4h` to `-24h`
3. **Pattern analysis**: `-7d`
4. **Baseline comparison**: Use `earliest=-8d latest=-7d` for week-ago baseline

---

## Search Optimization Tips

### Performance Best Practices

1. **Be specific with index and sourcetype:**
   ```spl
   # Fast
   index=web sourcetype=access_combined status>=500
   
   # Slow
   index=* status>=500
   ```

2. **Use indexed fields for filtering:**
   ```spl
   # Fast (indexed fields)
   index=main host=web-01 source=/var/log/app.log
   
   # Slower (extracted fields)
   index=main | where custom_field="value"
   ```

3. **Avoid leading wildcards:**
   ```spl
   # Fast
   index=main error*
   
   # Slow
   index=main *error
   ```

4. **Use stats instead of transaction when possible:**
   ```spl
   # Faster
   | stats count, min(_time) as start, max(_time) as end, values(action) as actions by session_id
   
   # Slower
   | transaction session_id
   ```

5. **Limit subsearch results:**
   ```spl
   # Good
   [search index=auth action=failure | stats count by src_ip | where count > 5 | fields src_ip | head 100]
   
   # Bad (unbounded subsearch)
   [search index=auth action=failure | fields src_ip]
   ```

### Result Size Management
- Use `| head N` or `max_results` parameter to limit output
- Use `| stats` to aggregate rather than returning raw events
- Use `| fields` to reduce field count in results
- Use `| table` only for final display formatting

---

## Anti-Patterns and Common Mistakes

### ❌ DON'T: Search all indexes
```spl
# Wrong - scans everything
index=* error

# Correct - specify index
index=main sourcetype=application level=ERROR
```

### ❌ DON'T: Use leading wildcards
```spl
# Wrong - very slow
index=main *timeout*

# Better - use field search
index=main message=*timeout*

# Best - use specific field
index=main sourcetype=application error_type=timeout
```

### ❌ DON'T: Forget time constraints
```spl
# Wrong - searches all time
index=main level=ERROR | stats count

# Correct - always use time range
index=main level=ERROR earliest=-1h | stats count
```

### ❌ DON'T: Use join when stats works
```spl
# Wrong - expensive join
index=web | join src_ip [search index=auth | stats count by src_ip]

# Better - use stats with subsearch filter
index=web [search index=auth | stats count by src_ip | where count > 5 | fields src_ip]
```

### ❌ DON'T: Return too many raw events
```spl
# Wrong - returns millions of events
index=main sourcetype=application

# Correct - aggregate or limit
index=main sourcetype=application | stats count by level, service | sort -count
```

### ❌ DON'T: Use eval before stats when stats can do it
```spl
# Wrong - unnecessary eval
| eval is_error = if(status>=400, 1, 0) | stats sum(is_error) as errors

# Better - use conditional count
| stats count(eval(status>=400)) as errors
```

---

## Troubleshooting

### No Results Found
1. Check index name: `| eventcount summarize=false index=*` to list indexes
2. Verify sourcetype: `index=main | stats count by sourcetype | head 20`
3. Widen time range
4. Check field names: `index=main | fieldsummary | where count > 0`
5. Remove filters one at a time to identify the restrictive condition

### Search Too Slow
1. Add `index=` and `sourcetype=` if missing
2. Narrow time range
3. Move restrictive filters before pipes
4. Replace `transaction` with `stats` where possible
5. Limit subsearch results with `| head 1000`
6. Use `| fields` to reduce data passed between commands

### Unexpected Results
1. Check field extraction: `| table _raw, field_name` to verify
2. Use `| fieldsummary` to check field types and values
3. Verify time zone settings
4. Check for multivalue fields: `| mvexpand field_name`
5. Use `| eval test=typeof(field)` to check data types

---

## Summary Checklist

Before making Splunk queries, ensure you:
- ✅ Specify `index=` and `sourcetype=` for performance
- ✅ Set appropriate time range with `earliest_time`/`latest_time`
- ✅ Put restrictive filters before pipe commands
- ✅ Use `stats`/`timechart` for aggregation instead of raw events
- ✅ Limit results with `head` or `max_results`
- ✅ Use indexed fields for filtering when available
- ✅ Avoid leading wildcards in search terms
- ✅ Use `transaction` only when event grouping is truly needed
- ✅ Consider search performance impact for large time ranges

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `SPLUNK_TOKEN` or `SPLUNK_URL` values in responses
- When referencing credentials, use placeholder names only
- If query results contain PII (usernames, IPs, emails, session tokens), summarize patterns rather than reproducing verbatim

### Query Scope Restrictions
- **Always specify `index=`** - never run `index=*` queries that scan all indexes
- **Always specify `sourcetype=`** when possible to further restrict scope
- **Do not query audit indexes** (`_audit`, `_internal`) unless explicitly requested - they contain sensitive operational data
- **Limit log output** - raw events may contain secrets, tokens, or credentials embedded in log messages
- When returning `_raw` fields, scan for and redact patterns that look like API keys, passwords, or tokens

### Data Sensitivity
- Treat all search results as potentially containing sensitive information
- Do not expose internal hostnames, IP addresses, or network topology unless explicitly asked
- When presenting security investigation results, be careful not to expose vulnerability details that could be exploited
- Do not return full authentication logs that could reveal valid credentials or session tokens
- Summarize patterns in security data rather than listing individual user activities

### Access Control
- Only query indexes the configured token has access to
- Do not attempt to enumerate users, roles, or capabilities
- If a search returns "unauthorized" or "insufficient permissions", report the error without retrying
- Do not attempt to access `| rest` commands or management endpoints

## Anti-Hallucination Guardrails

### Query Accuracy
- **Only use documented SPL commands** - do not invent command names. Common valid commands include: `search`, `stats`, `timechart`, `chart`, `table`, `eval`, `where`, `sort`, `head`, `tail`, `dedup`, `transaction`, `rex`, `lookup`, `join`, `append`, `appendcols`, `eventstats`, `streamstats`, `rename`, `fields`, `fillnull`, `top`, `rare`, `spath`
- **Only use documented stats functions** - valid functions include: `count`, `sum`, `avg`, `min`, `max`, `dc`, `values`, `list`, `first`, `last`, `stdev`, `var`, `median`, `mode`, `range`, `p50`, `p90`, `p95`, `p99`, `perc50`, `perc95`, `perc99`
- **Do not fabricate field names** - if unsure whether a field exists, suggest using `| fieldsummary` or `| fields` to discover available fields
- **Do not invent index or sourcetype names** - suggest using `| eventcount summarize=false index=*` or `| metadata type=sourcetypes` to discover available data

### Result Interpretation
- **Never invent search results** - if a search hasn't been run, say "I need to search for this" rather than guessing
- **Do not assume causation** - correlation in time does not prove causation; state this explicitly
- **Clearly distinguish between data and interpretation** - prefix analysis with "This suggests..." or "Based on the pattern..."
- **If a search returns no results**, report that clearly and suggest broadening filters
- **Do not extrapolate** beyond the searched time range without explicitly stating the assumption

### Tool Capability Boundaries
- Do not claim the Splunk MCP server can create alerts, modify saved searches, or change configurations - verify tool capabilities first
- Do not claim access to features not listed in the available tools
- If the user asks for something outside tool capabilities, clearly state the limitation and suggest alternatives (e.g., "You'll need to do this in the Splunk Web UI")

## Operational Optimization Guardrails

### Search Performance
- **Always specify `index=` and `sourcetype=`** - this is the single most impactful optimization
- **Put restrictive terms before the first pipe** - Splunk's search-time filtering is fastest on raw indexed data
- **Use time ranges appropriate to the question:**
 - Active incident: `earliest=-15m` to `earliest=-1h`
 - Investigation: `earliest=-4h` to `earliest=-24h`
 - Trend analysis: `earliest=-7d`
- **Prefer `stats` over `transaction`** - `stats` is significantly faster for most aggregation use cases
- **Limit subsearch results** - always add `| head 1000` or similar to subsearches to prevent unbounded scans

### Rate Limiting and Resource Management
- **Do not run multiple expensive searches simultaneously** - space them apart
- **Use `| head N` or `max_results`** to limit output size
- **Avoid leading wildcards** - `*error` is extremely slow; use `error*` or field-specific searches instead
- **Use `| fields` early in the pipeline** to reduce data passed between commands
- If a search is taking too long, suggest narrowing the time range or adding more specific filters

### Resource Efficiency
- **Prefer `stats` over returning raw events** - aggregated results are cheaper and more useful
- **Use `timechart` with appropriate `span`** - match span to time range:
 - < 1h: `span=1m` or `span=5m`
 - 1-6h: `span=5m` or `span=15m`
 - 6-24h: `span=15m` or `span=1h`
 - > 24h: `span=1h` or `span=4h`
- **Avoid `| join` when `stats` with `by` clause works** - joins are expensive
- **Use `| fields + field1, field2`** to reduce data volume in the pipeline
- **Avoid `| eval` before `| stats`** when stats can do the calculation directly (e.g., `count(eval(status>=400))`)

## Cost Optimization Guardrails

### Search Cost Awareness
- **Longer time ranges = higher cost** - always start narrow and expand only if needed
- **High-cardinality FACET/BY clauses are expensive** - avoid `by _raw` or `by message`
- **Avoid redundant searches** - if you already have data from a previous search, reuse it
- **Use `| head` for exploration** - start with `| head 10` to verify query correctness before running full searches

### Query Planning
- **Plan before searching** - determine what information is needed and write the minimum number of searches
- **Combine related questions** - use `stats count by field1, field2` instead of separate searches per field
- **Use `| appendcols` for comparisons** instead of running two separate searches and comparing manually
- **Cache results mentally** - if a search returned useful context, reference it rather than re-running

### License and Capacity
- Be aware that Splunk licenses are typically based on daily ingestion volume - searches don't directly consume license but do consume compute
- For very large environments, suggest using summary indexes or data models for frequently-needed aggregations
- Recommend `tstats` over raw search when data models are available (much faster)
- Suggest scheduled searches for recurring analysis rather than ad-hoc repeated queries
