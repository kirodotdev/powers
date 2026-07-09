# Application Signals Performance Monitoring Steering

## Purpose
This steering file provides guidance for using AWS CloudWatch Application Signals to monitor application performance, health, and dependencies.

## Application Signals Overview

Application Signals provides automatic instrumentation for application performance monitoring with:
- **Service-level metrics**: Latency, error rate, request volume
- **Distributed tracing**: End-to-end request flows with X-Ray
- **Service maps**: Visual representation of dependencies
- **SLOs**: Define and track service level objectives
- **Automatic discovery**: No code changes required for common frameworks

## Core Concepts

### 1. Services
A service represents a logical component of your application:
- Microservice
- Lambda function
- API endpoint
- Database connection

### 2. Operations
Operations are specific actions within a service:
- API endpoints
- Database queries
- External service calls
- Message queue operations

### 3. Service Level Objectives (SLOs)
Define expected service performance:
- **Availability SLO**: % of successful requests
- **Latency SLO**: % of requests under threshold
- **Custom SLO**: Based on specific metrics

### 4. Traces
End-to-end view of request flows:
- Trace ID: Unique identifier for request
- Spans: Individual operations within trace
- Annotations: Metadata and custom data
- Subsegments: Nested operations

## Common Monitoring Tasks

### Task 1: View Service Health
Check overall health of a service:

```
Operation: List services
Filters: 
  - Time range: Last 1 hour
  - Status: All / Healthy / Degraded / Unhealthy

Metrics to check:
  - Request count
  - Error rate
  - Average latency
  - P99 latency
```

### Task 2: Analyze Service Dependencies
Understand how services interact:

```
Operation: Get service map
Service: [target-service-name]
Time range: Last 24 hours

Look for:
  - Downstream dependencies
  - Upstream callers
  - External services
  - Database connections
  - Bottlenecks (high latency links)
```

### Task 3: Investigate Performance Issues
When latency increases or errors spike:

```
1. Check service metrics:
   - Compare current vs baseline latency
   - Identify error rate changes
   - Check request volume

2. Examine traces:
   - Filter by slow traces (p99)
   - Look for common patterns
   - Identify slowest operations

3. Analyze dependencies:
   - Check downstream service health
   - Identify external API issues
   - Review database query performance
```

### Task 4: Set Up SLOs
Define service level objectives:

```
Availability SLO Example:
  - Name: "API Availability"
  - Target: 99.9%
  - Evaluation period: 30 days
  - Metric: Success rate
  - Threshold: statusCode < 500

Latency SLO Example:
  - Name: "API Response Time"
  - Target: 95%
  - Evaluation period: 7 days
  - Metric: Request duration
  - Threshold: duration < 500ms
```

## Application Signals MCP Server Tools

### Primary Audit Tools (Recommended Entry Points)

1. **audit_services** ⭐: Comprehensive service health auditing with wildcard support
2. **audit_slos** ⭐: SLO compliance monitoring and breach analysis
3. **audit_service_operations** ⭐: Operation-specific performance analysis (GET, POST, etc.)

### Service Discovery Tools

4. **list_monitored_services**: Get all monitored services
5. **get_service_detail**: Get metadata and configuration for a specific service
6. **list_service_operations**: List recently invoked operations within a service (max 24h lookback)

### SLO Management Tools

7. **list_slos**: View configured SLOs
8. **get_slo**: Get detailed SLO configuration
9. **list_slis**: Legacy SLI status report with breach summary

### Metrics Tools

10. **query_service_metrics**: Retrieve metrics for a specific service (Latency, Error, Fault)

### Trace & Log Analysis Tools

11. **search_transaction_spans**: Query OpenTelemetry spans (100% sampled) via CloudWatch Logs Insights
12. **query_sampled_traces**: Query X-Ray traces (5% sampled) with filter expressions

### Canary, Change Events & Enablement Tools

13. **analyze_canary_failures**: Root cause investigation for CloudWatch Synthetics canaries
14. **list_change_events**: Query change events (deployments, config changes) to correlate with performance issues. Supports `comprehensive_history=True` (ListEntityEvents API, requires `service_key_attributes`) for full change history, or `comprehensive_history=False` (ListServiceStates API) for current service state.
15. **get_enablement_guide**: Step-by-step Application Signals setup instructions

### Target Format Reference

Audit tools require JSON target arrays. Examples:

**All services:**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]
```

**Wildcard pattern (e.g., payment services):**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*payment*"}}}]
```

**Specific service:**
```json
[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"checkout-service","Environment":"eks:prod-cluster"}}}]
```

**All SLOs:**
```json
[{"Type":"slo","Data":{"Slo":{"SloName":"*"}}}]
```

**Operation targets (e.g., GET operations, Latency):**
```json
[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"*payment*"},"Operation":"*GET*","MetricType":"Latency"}}}]
```

MetricType options: `Latency`, `Availability`, `Fault`, `Error`

### Auditor Selection Guide

| Scenario | Auditors |
|----------|----------|
| Quick health check | Default (omit parameter) |
| Root cause analysis | `all` |
| SLO breach investigation | `all` |
| Error investigation | `log,trace` |
| Dependency issues | `dependency_metric,trace` |
| Find outlier hosts | `top_contributor,operation_metric` |
| Quota monitoring | `service_quota,operation_metric` |

The 7 auditor types: `slo`, `operation_metric`, `trace`, `log`, `dependency_metric`, `top_contributor`, `service_quota`

### Transaction Search Query Patterns

Use with `search_transaction_spans` (100% sampled, queries `aws/spans` log group):

**Error analysis:**
```
FILTER attributes.aws.local.service = "service-name"
  and attributes.http.status_code >= 400
| STATS count() as error_count by attributes.aws.local.operation
| SORT error_count DESC
| LIMIT 20
```

**Latency analysis:**
```
FILTER attributes.aws.local.service = "service-name"
| STATS avg(duration) as avg_latency,
        pct(duration, 99) as p99_latency
  by attributes.aws.local.operation
| SORT p99_latency DESC
| LIMIT 20
```

**Dependency calls:**
```
FILTER attributes.aws.local.service = "service-name"
| STATS count() as call_count, avg(duration) as avg_latency
  by attributes.aws.remote.service, attributes.aws.remote.operation
| SORT call_count DESC
| LIMIT 20
```

**GenAI token usage:**
```
FILTER attributes.aws.local.service = "service-name"
  and attributes.aws.remote.operation = "InvokeModel"
| STATS sum(attributes.gen_ai.usage.output_tokens) as total_tokens
  by attributes.gen_ai.request.model, bin(1h)
```

### X-Ray Filter Expressions

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

### Pagination (`next_token`) Guidance

Wildcard patterns process services/SLOs in batches (default: 5 per call):
1. First call returns findings + `next_token` if more results exist
2. Continue with same parameters + `next_token` to process remaining
3. Repeat until no `next_token` is returned

### Tool Usage Patterns

#### Pattern 1: Service Health Check
```
1. Audit all services:
   audit_services(
     service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]'
   )

2. For services with issues, deep dive:
   audit_services(
     service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"problem-service"}}}]',
     auditors="all"
   )

3. Review findings and follow recommendations
```

#### Pattern 2: Latency Investigation
```
1. Audit operations for latency:
   audit_service_operations(
     operation_targets='[{"Type":"service_operation","Data":{"ServiceOperation":{"Service":{"Type":"Service","Name":"service-name"},"Operation":"*","MetricType":"Latency"}}}]'
   )

2. Get detailed metrics:
   query_service_metrics(
     service_name="service-name",
     metric_name="Latency",
     statistic="Average",
     extended_statistic="p99"
   )

3. Search 100% sampled traces for slow requests:
   search_transaction_spans(
     query_string='FILTER attributes.aws.local.service = "service-name"
       | STATS avg(duration) as avg_latency, pct(duration, 99) as p99
         by attributes.aws.local.operation
       | SORT p99 DESC | LIMIT 20'
   )
```

#### Pattern 3: Dependency Analysis
```
1. Audit service with dependency auditor:
   audit_services(
     service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"service-name"}}}]',
     auditors="dependency_metric,trace"
   )

2. For each dependency, check metrics:
   query_service_metrics(
     service_name="dependency-name",
     metric_name="Latency"
   )
```

#### Pattern 4: SLO Monitoring
```
1. Audit all SLOs:
   audit_slos(
     slo_targets='[{"Type":"slo","Data":{"Slo":{"SloName":"*"}}}]'
   )

2. For breached SLOs, get configuration:
   get_slo(slo_id="breached-slo-name")

3. Deep dive with root cause analysis:
   audit_slos(
     slo_targets='[{"Type":"slo","Data":{"Slo":{"SloName":"breached-slo-name"}}}]',
     auditors="all"
   )
```

## Performance Metrics Reference

### Request Metrics
- **RequestCount**: Total number of requests
- **SuccessCount**: Number of successful requests (statusCode < 400)
- **FaultCount**: Number of server errors (statusCode >= 500)
- **ErrorCount**: Number of client errors (400 <= statusCode < 500)

### Latency Metrics
- **Duration**: Request processing time
- **P50**: 50th percentile latency (median)
- **P90**: 90th percentile latency
- **P95**: 95th percentile latency
- **P99**: 99th percentile latency
- **P99.9**: 99.9th percentile latency

### Rate Metrics
- **ErrorRate**: (ErrorCount / RequestCount) * 100
- **FaultRate**: (FaultCount / RequestCount) * 100
- **SuccessRate**: (SuccessCount / RequestCount) * 100

### Throughput Metrics
- **RequestsPerSecond**: RequestCount / time_window
- **BytesIn**: Incoming payload size
- **BytesOut**: Outgoing response size

## Distributed Tracing Analysis

### Trace Structure
```
Trace (Request ID: abc123)
├── Root Span: API Gateway Request
│   ├── Span: Lambda Execution
│   │   ├── Subsegment: DynamoDB Query
│   │   ├── Subsegment: S3 GetObject
│   │   └── Subsegment: External API Call
│   └── Span: Response Processing
```

### Analyzing Traces

**Look for**:
1. **Long spans**: Operations taking significant time
2. **Sequential calls**: Opportunities for parallelization
3. **Repeated operations**: Caching opportunities
4. **External dependencies**: Third-party service issues
5. **Error spans**: Failed operations and exceptions

**Common Patterns**:

```
Pattern: N+1 Query Problem
└── Multiple sequential database queries
    Solution: Use batch operations or caching

Pattern: Sequential External Calls
└── External API calls in sequence
    Solution: Parallelize independent calls

Pattern: Long Cold Start
└── Lambda initialization taking > 1s
    Solution: Provisioned concurrency or runtime optimization

Pattern: Downstream Service Timeout
└── Waiting for slow dependency
    Solution: Circuit breaker, timeout adjustment
```

## SLO Configuration Best Practices

### Availability SLOs

**Example 1: High-Availability Service**
```
Name: "Critical API Availability"
Target: 99.95%
Evaluation period: 30 days
Metric: (SuccessCount / RequestCount) * 100
Threshold: >= 99.95%

Alert when:
  - SLO at risk: Error budget < 20%
  - SLO breach: < 99.95%
```

**Example 2: Standard Service**
```
Name: "Standard API Availability"
Target: 99.9%
Evaluation period: 7 days
Metric: Success rate
Threshold: >= 99.9%
```

### Latency SLOs

**Example 1: User-Facing API**
```
Name: "API Response Time"
Target: 95% of requests < 500ms
Evaluation period: 7 days
Metric: Duration P95
Threshold: < 500ms

Rationale: Users expect fast responses
```

**Example 2: Background Processing**
```
Name: "Batch Job Latency"
Target: 99% of jobs < 30s
Evaluation period: 30 days
Metric: Duration P99
Threshold: < 30000ms

Rationale: Less critical than user-facing
```

### Custom SLOs

**Example: Data Freshness**
```
Name: "Data Pipeline Freshness"
Target: 99% of updates < 5 minutes old
Evaluation period: 24 hours
Metric: Custom metric (data_age)
Threshold: < 300000ms
```

## Performance Troubleshooting Workflows

### Workflow 1: High Error Rate

**Steps**:
1. Identify service with high error rate
2. Get error breakdown by operation
3. Sample error traces
4. Analyze error patterns:
   - Client errors (4xx): Input validation, auth issues
   - Server errors (5xx): Application bugs, dependency failures
5. Check dependencies for issues
6. Review recent deployments
7. Check CloudWatch Logs for detailed error messages

**Logs Insights Query for Error Analysis**:
```
# Analyze errors by endpoint and status code
fields @timestamp, endpoint, statusCode, errorType
| filter statusCode >= 400
| stats count(*) as errorCount by endpoint, statusCode
| sort errorCount desc
| limit 20
```

### Workflow 2: Increased Latency

**Steps**:
1. Compare current P95/P99 vs baseline
2. Identify slow operations
3. Analyze slow traces:
   - Which spans are slowest?
   - Are downstream services slow?
   - Database query performance?
4. Check for:
   - Increased load (scale out)
   - Code changes (rollback if needed)
   - Dependency issues (circuit breaker)
   - Resource constraints (CPU, memory)
5. Correlate with Application Signals service map

**Logs Insights Query for Latency Analysis**:
```
# Analyze latency by endpoint
fields @timestamp, endpoint, duration
| filter ispresent(duration)
| stats count(*) as requestCount, 
        avg(duration) as avgDuration,
        pct(duration, 95) as p95,
        pct(duration, 99) as p99,
        max(duration) as maxDuration 
  by endpoint
| sort p95 desc
| limit 20
```

### Workflow 3: SLO Breach Investigation

**Steps**:
1. Identify which SLO was breached
2. Determine time of breach
3. Get metrics during breach period:
   - Error rate spike?
   - Latency increase?
   - Traffic surge?
4. Check for correlated events:
   - Deployments (CloudTrail - use data source priority)
   - Infrastructure changes
   - Dependency failures
5. Review traces from breach period
6. Document root cause
7. Update runbooks

## Integration with Other Observability Tools

### CloudWatch Logs
Use Logs Insights queries to correlate Application Signals metrics with logs:

```
# Find slow requests with trace correlation
fields @timestamp, @message, requestId, traceId, duration, level
| filter duration > 1000
| sort duration desc
| limit 100
```

### CloudTrail
Check for recent changes that might affect performance:
```
Follow CloudTrail data source priority (see cloudtrail-data-source-selection.md):
1. Check CloudTrail Lake event data stores (preferred)
2. Check CloudWatch Logs for CloudTrail integration
3. Use CloudTrail Lookup Events API (fallback)

Query for:
- Recent deployments
- Configuration changes
- IAM policy updates
- Resource modifications
```

### X-Ray
Deep dive into specific traces:
```
1. Get trace IDs from Application Signals
2. Open X-Ray console for detailed analysis
3. Review service map and trace timeline
4. Check for errors and exceptions
5. Examine annotations and metadata
```

## Alerting Configuration

### Critical Alerts

**High Error Rate**:
```
Metric: ErrorRate
Threshold: > 5%
Evaluation period: 5 minutes
Datapoints to alarm: 3 of 5
Action: Page on-call engineer
```

**P99 Latency Breach**:
```
Metric: Duration P99
Threshold: > 2000ms
Evaluation period: 10 minutes
Datapoints to alarm: 2 of 2
Action: Notify team channel
```

**SLO At Risk**:
```
Metric: Error budget remaining
Threshold: < 20%
Evaluation period: 1 hour
Action: Notify team, consider feature freeze
```

### Warning Alerts

**Elevated Error Rate**:
```
Metric: ErrorRate
Threshold: > 1%
Evaluation period: 15 minutes
Action: Notify team channel
```

**P95 Latency Increase**:
```
Metric: Duration P95
Threshold: > 1000ms
Evaluation period: 15 minutes
Action: Log to monitoring channel
```

## Best Practices

### 1. Service Instrumentation
- Use AWS X-Ray SDK for custom instrumentation
- Add meaningful service names
- Include environment in service name (e.g., "api-prod")
- Use consistent naming conventions

### 2. SLO Management
- Start with realistic targets (99% before 99.99%)
- Align SLOs with business requirements
- Review and adjust quarterly
- Track error budget consumption
- Plan for error budget-based decisions

### 3. Trace Sampling
- Use adaptive sampling for high-volume services
- Always capture error traces
- Sample 100% of traces during incidents
- Include custom annotations for business context

### 4. Metric Collection
- Monitor latency percentiles (P50, P95, P99)
- Track error rates by type (4xx vs 5xx)
- Measure request volume trends
- Monitor dependency health

### 5. Performance Baselines
- Establish normal latency baselines
- Document expected error rates
- Track seasonal patterns
- Update baselines after optimization

## Common Performance Patterns

### Pattern 1: Cold Start Impact
**Symptom**: High P99 latency, spiky performance
**Detection**: Large gap between P50 and P99
**Solution**: Provisioned concurrency, keep-alive strategies

### Pattern 2: Database Connection Pooling
**Symptom**: Latency increases with load
**Detection**: Slow database spans in traces
**Solution**: Connection pooling, query optimization

### Pattern 3: Cascading Failures
**Symptom**: Multiple services showing errors simultaneously
**Detection**: Service map shows downstream failures
**Solution**: Circuit breakers, timeout configuration, bulkheads

### Pattern 4: Cache Invalidation
**Symptom**: Periodic latency spikes
**Detection**: Traces show increased database/API calls
**Solution**: Optimize cache strategy, cache warming

### Pattern 5: Traffic Bursts
**Symptom**: Error rate increases during peak load
**Detection**: Correlation between RequestCount and ErrorRate
**Solution**: Auto-scaling, rate limiting, queue buffering

## Quick Reference Commands

### Get Service Health
```
1. audit_services(service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]')
2. query_service_metrics(service_name="service-name", metric_name="Latency")
```

### Investigate Slow Request
```
1. search_transaction_spans(query_string='FILTER attributes.aws.local.service = "service-name" and duration > 5000 | LIMIT 20')
2. Analyze span durations from results
```

### Check Dependencies
```
1. audit_services(service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"service-name"}}}]', auditors="dependency_metric,trace")
```

### Monitor SLO
```
1. audit_slos(slo_targets='[{"Type":"slo","Data":{"Slo":{"SloName":"*"}}}]')
2. get_slo(slo_id="slo-name")
3. If breached: audit_slos(slo_targets='[{"Type":"slo","Data":{"Slo":{"SloName":"slo-name"}}}]', auditors="all")
```

---

**Remember**: Application Signals works best when services are properly instrumented and SLOs are aligned with business requirements. Always correlate metrics with traces and logs for complete visibility.
