# Application Signals Steering Guide

## When to Use Application Signals Tools

Use these tools when you need to:
- **Audit service health** - Check status across all or specific services
- **Investigate SLO breaches** - Understand why SLOs are failing
- **Analyze operation performance** - Deep dive into specific API endpoints
- **Perform root cause analysis** - Correlate traces, logs, metrics, and dependencies
- **Debug canary failures** - Investigate CloudWatch Synthetics issues

---

## Target Format Reference

### Service Targets

**All services:**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]
```

**Wildcard pattern:**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*payment*"}}}]
```

**Specific service:**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"checkout-service","Environment":"eks:prod-cluster"}}}]
```

### SLO Targets

**All SLOs:**
```json
[{"Type":"slo","Data":{"Slo":{"SloName":"*"}}}]
```

**Wildcard pattern:**
```json
[{"Type":"slo","Data":{"Slo":{"SloName":"*latency*"}}}]
```

**Specific SLO:**
```json
[{"Type":"slo","Data":{"Slo":{"SloName":"checkout-latency-slo"}}}]
```

**By ARN:**
```json
[{"Type":"slo","Data":{"Slo":{"SloArn":"arn:aws:application-signals:us-east-1:123456789:slo/my-slo"}}}]
```

### Operation Targets

**All operations in payment services (Latency):**
```json
[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"*payment*"},"Operation":"*","MetricType":"Latency"}}}]
```

**GET operations only:**
```json
[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"*"},"Operation":"*GET*","MetricType":"Latency"}}}]
```

**Specific operation:**
```json
[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"api-service","Environment":"eks:prod"},"Operation":"POST /api/checkout","MetricType":"Availability"}}}]
```

**MetricType options:** `Latency`, `Availability`, `Fault`, `Error`

---

## Auditor Selection Guide

### Default Auditors (Fast)
- `audit_services`: `slo,operation_metric`
- `audit_slos`: `slo`
- `audit_service_operations`: `operation_metric`

### All Auditors (Comprehensive)
Use `auditors="all"` for root cause analysis:
- `slo` - SLO compliance status
- `operation_metric` - Operation performance metrics
- `trace` - Distributed trace analysis
- `log` - Log pattern analysis
- `dependency_metric` - Dependency health
- `top_contributor` - Identify outliers/lemon hosts
- `service_quota` - AWS service quota usage

### When to Use Each

| Scenario | Auditors |
|----------|----------|
| Quick health check | Default (omit parameter) |
| Root cause analysis | `all` |
| SLO breach investigation | `all` |
| Error investigation | `log,trace` |
| Dependency issues | `dependency_metric,trace` |
| Find outlier hosts | `top_contributor,operation_metric` |
| Quota monitoring | `service_quota,operation_metric` |

---

## Primary Workflows

### 1. Service Health Audit (Daily Check)

```
1. audit_services(service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]')
2. Review findings summary
3. User selects service to investigate
4. audit_services(service_targets='[specific-service]', auditors="all")
```

### 2. SLO Breach Investigation

```
1. get_slo(slo_id="breached-slo-name") - Understand configuration
2. audit_slos(slo_targets='[{"Type":"slo","Data":{"Slo":{"SloName":"breached-slo-name"}}}]', auditors="all")
3. Follow recommendations from findings
```

### 3. Operation Performance Analysis

```
1. audit_service_operations(operation_targets='[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"*"},"Operation":"*","MetricType":"Latency"}}}]')
2. Identify slow operations from findings
3. audit_service_operations(operation_targets='[specific-operation]', auditors="all")
```

### 4. Error Spike Investigation

```
1. audit_services(service_targets='[affected-service]', auditors="log,trace")
2. search_transaction_spans() for 100% trace data
3. Correlate with deployment or dependency changes
```

### 5. Canary Failure Analysis

```
1. analyze_canary_failures(canary_name="failing-canary")
2. Review artifact analysis (logs, screenshots, HAR)
3. Check backend service correlation
4. Follow remediation recommendations
```

---

## Transaction Search Query Patterns

### Error Analysis
```
FILTER attributes.aws.local.service = "service-name" 
  and attributes.http.status_code >= 400
| STATS count() as error_count by attributes.aws.local.operation
| SORT error_count DESC
| LIMIT 20
```

### Latency Analysis
```
FILTER attributes.aws.local.service = "service-name"
| STATS avg(duration) as avg_latency, 
        pct(duration, 99) as p99_latency 
  by attributes.aws.local.operation
| SORT p99_latency DESC
| LIMIT 20
```

### Dependency Calls
```
FILTER attributes.aws.local.service = "service-name"
| STATS count() as call_count, avg(duration) as avg_latency 
  by attributes.aws.remote.service, attributes.aws.remote.operation
| SORT call_count DESC
| LIMIT 20
```

### GenAI Token Usage
```
FILTER attributes.aws.local.service = "service-name" 
  and attributes.aws.remote.operation = "InvokeModel"
| STATS sum(attributes.gen_ai.usage.output_tokens) as total_tokens 
  by attributes.gen_ai.request.model, bin(1h)
```

---

## X-Ray Filter Expressions

Use with `query_sampled_traces` (5% sampled):

```
# Faults for a service
service("service-name"){fault = true}

# Slow requests
service("service-name") AND duration > 5

# Specific operation
annotation[aws.local.operation]="GET /api/orders"

# HTTP errors
http.status = 500

# Combined
service("api"){fault = true} AND annotation[aws.local.operation]="POST /checkout"
```

---

## Best Practices

### Present Findings First
When audit returns multiple findings:
1. Show summary of ALL findings to user
2. Let user choose which to investigate
3. Then perform targeted root cause analysis

### Pagination for Large Results
Wildcard patterns process in batches (default: 5 services/SLOs per call):
1. First call returns findings + `next_token`
2. Continue with `next_token` to process remaining
3. Repeat until no `next_token` returned

### Time Range Selection
- **Quick check**: Last 1 hour (default for some tools)
- **Daily audit**: Last 24 hours (default)
- **Incident investigation**: Narrow to incident window
- **Trend analysis**: Last 7 days with specific time parameters

### Wildcard Patterns
- `*` - All services/SLOs
- `*payment*` - Contains "payment"
- `*-prod` - Ends with "-prod"
- `checkout-*` - Starts with "checkout-"
