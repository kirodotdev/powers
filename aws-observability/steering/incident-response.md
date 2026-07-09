# Incident Response and Troubleshooting

## Purpose
This steering file provides comprehensive guidance for responding to incidents and troubleshooting issues using the full AWS observability stack.

## Incident Response Framework

### Phase 1: Detection and Triage

**Objectives**:
- Quickly identify the issue
- Assess severity and impact
- Determine affected services and users

**Actions**:
1. **Check Active Alarms**
   - Query CloudWatch for alarms in ALARM state
   - Review alarm history to understand timing
   - Identify which metrics triggered alarms

2. **Review Application Signals**
   - Check service health and SLO status
   - Identify services with elevated error rates
   - Review service maps for dependency issues

3. **Assess Impact**
   - Query logs for error volume
   - Check request counts and success rates
   - Determine user-facing impact

**Severity Classification**:
- **SEV1 (Critical)**: Complete service outage, data loss, security breach
- **SEV2 (High)**: Major functionality impaired, significant user impact
- **SEV3 (Medium)**: Partial functionality impaired, workaround available
- **SEV4 (Low)**: Minor issue, minimal user impact
- **SEV5 (Informational)**: No immediate impact, cosmetic or non-urgent improvement

### Phase 2: Investigation

**Objectives**:
- Gather evidence and data
- Identify root cause
- Understand the failure chain

**Data Collection**:

1. **CloudWatch Logs Insights**
   For detailed log query patterns and syntax, see `log-analysis.md`.
   Key query for incident context:
   ```
   # Quick error snapshot for incident timeframe
   fields @timestamp, @logStream, @message, level, errorType, requestId
   | filter level = "ERROR"
   | sort @timestamp asc
   | limit 1000
   ```

2. **Application Signals Traces**
   - Search for failed traces during incident window
   - Analyze trace timelines for bottlenecks
   - Examine error spans for exception details
   - Review service dependencies

3. **CloudWatch Metrics**
   - Get metric data for affected resources
   - Compare with baseline/normal behavior
   - Identify metric anomalies
   - Check for resource exhaustion (CPU, memory, connections)

4. **CloudTrail Events**
   For detailed CloudTrail query patterns and security analysis, see `security-auditing.md`.
   - **Follow CloudTrail data source priority** (see `cloudtrail-data-source-selection.md`):
     - Priority 1: Check CloudTrail Lake event data stores
     - Priority 2: Check CloudWatch Logs for CloudTrail integration
     - Priority 3: Use CloudTrail Lookup Events API
   - Query for recent configuration changes
   - Check for deployments or infrastructure modifications
   - Identify who made changes and when
   - Review IAM permission changes

**Correlation Workflow**:
```
1. Identify incident start time from alarms
2. Query logs for errors starting at that time
3. Extract trace IDs from error logs
4. Analyze traces for failure points
5. Check CloudTrail for changes before incident (use priority order)
6. Correlate metrics with error patterns
```

### Phase 3: Mitigation

**Objectives**:
- Stop the bleeding
- Restore service functionality
- Minimize user impact

**Common Mitigation Strategies**:

1. **Rollback Deployment**
   - Check CloudTrail for recent deployments (use data source priority)
   - Identify deployment time vs incident start
   - Rollback to previous stable version
   - Verify service recovery

2. **Scale Resources**
   - Check CloudWatch Metrics for resource constraints
   - Increase capacity (EC2 instances, Lambda concurrency)
   - Add read replicas for database load
   - Enable auto-scaling if not already active

3. **Circuit Breaker**
   - Identify failing downstream dependency
   - Implement circuit breaker or fallback
   - Route traffic away from failing component
   - Enable degraded mode operation

4. **Rate Limiting**
   - Identify traffic spike or abuse
   - Implement rate limiting at API Gateway
   - Block malicious IPs
   - Enable WAF rules

5. **Database Optimization**
   - Identify slow queries in logs
   - Add missing indexes
   - Optimize query patterns
   - Scale database resources

### Phase 4: Recovery Verification

**Objectives**:
- Confirm service is restored
- Validate metrics are normal
- Ensure no secondary issues

**Verification Steps**:

1. **Check Alarms**
   - Verify alarms have returned to OK state
   - Monitor for alarm flapping
   - Review alarm history

2. **Validate Application Signals**
   - Check error rates have normalized
   - Verify latency is within SLO targets
   - Review service map for healthy dependencies

3. **Query Logs**
   ```
   # Verify error rate has decreased
   fields @timestamp, level
   | stats count(*) as totalLogs, 
          sum(level = "ERROR") as errorCount 
     by bin(1m)
   | sort @timestamp asc
   | limit 60
   ```

4. **Monitor Metrics**
   - Check CPU, memory, and network utilization
   - Verify request rates and latencies
   - Monitor error rates and success rates

### Phase 5: Root Cause Analysis

**Objectives**:
- Understand why the incident occurred
- Identify contributing factors
- Document findings

**Analysis Framework**:

1. **Timeline Construction**
   - Create detailed timeline of events
   - Include all changes and observations
   - Mark incident start, detection, mitigation, and resolution

2. **Five Whys Analysis**
   ```
   Problem: API returned 500 errors
   
   Why? Lambda function timed out
   Why? Database queries were slow
   Why? Database was under heavy load
   Why? New feature caused N+1 query problem
   Why? Code review didn't catch the inefficient query pattern
   
   Root Cause: Insufficient code review process for database queries
   ```

3. **Contributing Factors**
   - Technical factors (code bugs, configuration errors)
   - Process factors (inadequate testing, missing monitoring)
   - Human factors (knowledge gaps, communication issues)

4. **Evidence Collection**
   - Log excerpts showing errors
   - Metric graphs showing anomalies
   - Trace examples demonstrating failures
   - CloudTrail events showing changes
   - Cost data showing resource usage

### Phase 6: Postmortem and Prevention

**Objectives**:
- Document incident for future reference
- Identify preventive measures
- Implement improvements

**Postmortem Template**:

```markdown
# Incident Postmortem: [Incident Title]

## Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours Y minutes
- **Severity**: SEVX
- **Impact**: Description of user impact
- **Root Cause**: Brief root cause statement

## Timeline
- HH:MM - Incident began
- HH:MM - First alert triggered
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Service restored
- HH:MM - Incident closed

## What Happened
Detailed description of the incident

## Root Cause
Detailed root cause analysis with evidence

## Resolution
How the incident was resolved

## Impact
- Users affected: X
- Requests failed: Y
- Latency impact: P50/P95/P99 degradation during incident window
- Revenue impact: $Z
- SLO impact: A% error budget consumed

## Action Items
1. [ ] Immediate fix (Owner, Due Date)
2. [ ] Monitoring improvement (Owner, Due Date)
3. [ ] Process change (Owner, Due Date)
4. [ ] Documentation update (Owner, Due Date)

## Lessons Learned
What went well and what could be improved
```

**Prevention Strategies**:

1. **Monitoring Improvements**
   - Add missing alarms
   - Improve alarm thresholds
   - Create composite alarms for complex scenarios
   - Set up SLOs for critical services

2. **Testing Enhancements**
   - Add test cases for failure scenario
   - Implement chaos engineering
   - Load testing for capacity planning
   - Integration testing for dependencies

3. **Process Changes**
   - Update deployment procedures
   - Improve code review checklist
   - Enhance runbook documentation
   - Implement gradual rollouts

4. **Architecture Improvements**
   - Add redundancy for single points of failure
   - Implement circuit breakers
   - Add caching layers
   - Improve error handling

## Common Incident Patterns

### Pattern 1: Deployment-Related Incident

**Symptoms**:
- Errors spike immediately after deployment
- Specific service shows elevated error rate
- Traces show new error types

**Investigation**:
For detailed log query patterns and syntax, see `log-analysis.md`. Key incident-specific approach:
- Query logs for errors immediately after deployment timestamp
- Group errors by type to identify new error patterns introduced by the deployment
- Compare error types before and after deployment

**Mitigation**: Rollback deployment

**Prevention**: 
- Implement canary deployments
- Add integration tests
- Improve staging environment

### Pattern 2: Resource Exhaustion

**Symptoms**:
- Gradual performance degradation
- Timeouts and connection errors
- High CPU or memory utilization

**Investigation**:
- Check CloudWatch Metrics for resource utilization
- Query logs for timeout errors
- Review Application Signals for latency increases
- Check Cost Explorer for usage spikes

**Mitigation**: Scale resources, optimize code

**Prevention**:
- Set up auto-scaling
- Implement resource limits
- Add capacity planning alarms

### Pattern 3: Dependency Failure

**Symptoms**:
- Errors calling external service
- Traces show failures in downstream calls
- Service map shows unhealthy dependency

**Investigation**:
For detailed log query patterns (including field parsing and aggregation), see `log-analysis.md`. Key incident-specific approach:
- Filter logs for dependency-related errors and parse service names and status codes
- Correlate with Application Signals service map to identify unhealthy dependencies
- Check traces for failures in downstream calls

**Mitigation**: 
- Implement circuit breaker
- Add fallback behavior
- Route around failed dependency

**Prevention**:
- Add dependency health checks
- Implement retry logic with backoff
- Set up dependency SLOs

### Pattern 4: Database Performance

**Symptoms**:
- Slow query performance
- Database connection pool exhaustion
- High database CPU utilization

**Investigation**:
For detailed log query patterns (including duration parsing and aggregation), see `log-analysis.md`. Key incident-specific approach:
- Parse SQL queries and durations from logs, filtering for slow queries (e.g., duration > 1000ms)
- Aggregate by query pattern to identify the most impactful slow queries
- Correlate with database CloudWatch Metrics (CPU, connections, IOPS)

**Mitigation**:
- Add database indexes
- Optimize queries
- Scale database resources
- Implement query caching

**Prevention**:
- Regular query performance reviews
- Database monitoring and alerting
- Connection pool tuning

### Pattern 5: Traffic Spike

**Symptoms**:
- Sudden increase in request volume
- Rate limiting errors
- Resource exhaustion

**Investigation**:
- Check CloudWatch Metrics for request rates
- Query logs for request patterns
- Review Application Signals for traffic sources
- Check Cost Explorer for usage spikes

**Mitigation**:
- Enable auto-scaling
- Implement rate limiting
- Add caching layer
- Scale resources manually

**Prevention**:
- Capacity planning
- Load testing
- Auto-scaling configuration
- DDoS protection

## Integration with All Observability Tools

For detailed patterns on individual tools, see the specialized guides: `log-analysis.md` for log queries, `performance-monitoring.md` for Application Signals and APM, and `security-auditing.md` for CloudTrail analysis.

### Complete Investigation Workflow

```
1. Detection (CloudWatch Alarms)
   ↓
2. Service Health (Application Signals)
   ↓
3. Error Analysis (CloudWatch Logs Insights)
   ↓
4. Trace Analysis (Application Signals Traces)
   ↓
5. Metric Correlation (CloudWatch Metrics)
   ↓
6. Change Detection (CloudTrail)
   ↓
7. Cost Impact (Cost Explorer)
   ↓
8. Documentation (AWS Documentation)
```

### Example: Complete Incident Investigation

**Scenario**: API returning 500 errors

**Step 1: Check Alarms**
```
Query: get_active_alarms(state_value="ALARM")
Result: "api-error-rate" alarm in ALARM state
```

**Step 2: Check Application Signals**
For detailed Application Signals patterns and APM deep-dive, see `performance-monitoring.md`.
```
Query: audit_services(
  service_targets='[{"Type":"service","Data":{"Service":{"Type":"Service","Name":"*"}}}]'
)
Result: "api-service" flagged with 15% error rate (normal: 0.1%)
```

**Step 3: Query Logs**
```
fields @timestamp, @message, errorType, requestId, traceId
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

**Step 4: Analyze Traces**
For detailed trace analysis patterns, see `performance-monitoring.md`.
```
Query: search_transaction_spans(
  query_string='FILTER attributes.aws.local.service = "api-service"
    and attributes.http.status_code >= 500
    | LIMIT 20'
)
Result: Traces show timeout calling database
```

**Step 5: Check Metrics**
```
Query: get_metric_data(
  namespace="AWS/RDS",
  metric_name="CPUUtilization",
  dimensions=[{name: "DBInstanceIdentifier", value: "prod-db"}]
)
Result: Database CPU at 95%
```

**Step 6: Check CloudTrail for Changes**
```
# Follow CloudTrail data source priority (see cloudtrail-data-source-selection.md)
# For detailed CloudTrail query patterns and security analysis, see security-auditing.md.
#
# 1. Check CloudTrail Lake (if available)
# 2. Check CloudWatch Logs (if CloudTrail integrated)
# 3. Use Lookup Events API (fallback)
#
# Query for recent changes to the affected service (e.g., RDS):
# - Filter by eventSource for the relevant AWS service
# - Sort by eventTime descending to find recent changes

Result: No recent database changes
```

**Step 7: Check Logs for Query Patterns**
For detailed log query patterns including duration parsing, see `log-analysis.md`.
```
# Analyze slow query patterns - parse SQL and duration from logs,
# aggregate by query to find the most frequent/slowest patterns.
# See log-analysis.md for parse and stats syntax reference.

Result: N+1 query pattern detected - 10,000+ queries for single API request
```

**Step 8: Root Cause**
```
Finding: New feature deployed 1 hour ago
Issue: N+1 query problem causing excessive database load
Evidence: 10,000+ queries for single API request
```

**Step 9: Mitigation**
```
Action: Rollback deployment
Verification: Error rate returns to normal
Follow-up: Fix N+1 query, add database query monitoring
```

## Quick Reference

### Incident Checklist

- [ ] Check active alarms
- [ ] Review Application Signals service health
- [ ] Query logs for errors
- [ ] Analyze traces for failures
- [ ] Check metrics for anomalies
- [ ] Review CloudTrail for changes
- [ ] Assess cost impact
- [ ] Document timeline
- [ ] Implement mitigation
- [ ] Verify recovery
- [ ] Conduct root cause analysis
- [ ] Write postmortem
- [ ] Implement preventive measures

### Key Logs Insights Queries

For detailed log query patterns, syntax reference, and common query templates, see `log-analysis.md`. During incidents, focus on:
- Error rate over time (bin by 1m for incident granularity)
- Top error types to identify the dominant failure mode
- Request tracing using requestId or traceId from error logs

---

**Remember**: Effective incident response requires quick detection, thorough investigation, decisive mitigation, and comprehensive follow-up. Use all available observability tools to build a complete picture of the incident.
