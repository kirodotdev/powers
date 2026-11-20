# Datadog Query Use Cases, Anti-Patterns and Performance Tips

Companion reference for the [datadog-query-syntax](../SKILL.md) skill.

## Common Use Cases

### 1. Investigating Production Errors
```
# Step 1: Search logs for errors in last hour
Tool: search_datadog_logs
Query: service:api env:prod status:error
Time: from="now-1h", to="now"

# Step 2: If errors found, get error details
Enable: extra_fields=["*"]  # Get all attributes
Check: Error messages, stack traces, affected users

# Step 3: Find related traces
Tool: search_datadog_spans
Query: service:api status:error
Time: Same as log time range

# Step 4: Get full trace for detailed analysis
Tool: get_datadog_trace
trace_id: <from span search>
```

### 2. Performance Degradation Analysis
```
# Step 1: Check for slow requests
Tool: search_datadog_spans
Query: service:api @duration:>100000000  # >100ms
Time: from="now-1h", to="now"

# Step 2: Examine metrics for patterns
Tool: get_datadog_metric
Query: avg:trace.servlet.request.duration{service:api} by {resource_name}
Time: from="now-4h", to="now"

# Step 3: Check for infrastructure issues
Tool: get_datadog_metric
Query: avg:system.cpu.user{service:api} by {host}
Time: Same range

# Step 4: Review related monitors
Tool: search_datadog_monitors
Query: tag:"service:api" status:alert
```

### 3. User Experience Issues (RUM)
```
# Step 1: Find slow page loads
Tool: search_datadog_rum_events
Query: @type:view @view.loading_time:>3000
detailed_output: true
Time: from="now-1h", to="now"

# Step 2: Check for frontend errors
Tool: search_datadog_rum_events
Query: @type:error @application.name:"My App"
Time: Same range

# Step 3: Analyze by device/browser
Query: @type:view @view.loading_time:>3000
Group findings by @device.type and @browser.name
```

### 4. Incident Investigation
```
# Step 1: Find active incidents
Tool: search_datadog_incidents
Query: state:(active OR stable)

# Step 2: Get incident details
Tool: get_datadog_incident
incident_id: <from search results>

# Step 3: Check related metrics/logs
Use incident time range to query logs and metrics
Filter by affected services/hosts from incident
```

### 5. Service Dependency Analysis
```
# Step 1: List all services
Tool: search_datadog_services
detailed_output: true

# Step 2: Find traces spanning multiple services
Tool: search_datadog_spans
Query: service:frontend
Check spans for downstream service calls

# Step 3: Analyze service-to-service latency
Tool: get_datadog_metric
Query: avg:trace.servlet.request.duration{env:prod} by {service}
```

---

## Anti-Patterns and Common Mistakes

### ❌ DON'T: Use Very Long Time Ranges Without Reason
```
# Slow and often not helpful
from: "now-30d"
```
**Instead**: Start with `now-1h` or `now-24h`, expand if needed.

### ❌ DON'T: Forget @ Prefix for Span/Log Attributes
```
# Wrong
http.status_code:500

# Correct
@http.status_code:500
```

### ❌ DON'T: Use @ Prefix for Reserved Trace Attributes
```
# Wrong
@service:api

# Correct
service:api
```

### ❌ DON'T: Forget Duration is in Nanoseconds
```
# Wrong (this is 5 nanoseconds!)
@duration:>5

# Correct (5 milliseconds)
@duration:>5000000
```

### ❌ DON'T: Use Wildcards Inside Quotes
```
# Wrong (wildcard becomes literal)
@url:"*/api/*"

# Correct
@url:*/api/*
```

### ❌ DON'T: Separate Multi-Value OR Queries
```
# Wrong for incidents
severity:SEV-1 OR severity:SEV-2

# Correct
severity:(SEV-1 OR SEV-2)
```

### ❌ DON'T: Use Excessive Free-Text Searches
```
# Slow and imprecise
"timeout error in production"

# Better - use structured tags
service:api env:prod @error.message:*timeout*
```

### ❌ DON'T: Ignore Unified Service Tagging
```
# Missing critical context
status:error

# Much better
service:api env:prod version:v1.2.3 status:error
```

### ❌ DON'T: Skip Escaping Special Characters
```
# Wrong (colon breaks parsing)
@url:https://example.com

# Correct
@url:https\:\/\/example.com
```

---

## Performance Tips

### 1. Query Optimization
- **Filter first**: Use `service`, `env` before complex conditions
- **Use facets**: Ensure frequently queried attributes are facets
- **Limit wildcards**: Avoid leading wildcards when possible
- **Use tag searches**: More efficient than free-text

### 2. Result Size Management
- **max_tokens**: Adjust based on needs (5000 for overview, 50000 for details)
- **head_limit**: Limit result count for faster responses
- **group_by_message**: For logs, group similar messages to reduce output
- **Binned metrics**: Use binned data for trends instead of raw

### 3. Time Range Strategy
```
# Good progression
1. now-15m → Quick check for recent issues
2. now-1h → Standard investigation window
3. now-24h → Broader pattern analysis
4. now-7d → Historical trends only when needed
```

### 4. Parallel Investigations
When investigating incidents, query multiple sources in parallel:
- Logs for error messages
- Spans for trace analysis
- Metrics for resource utilization
- Monitors for alert status
