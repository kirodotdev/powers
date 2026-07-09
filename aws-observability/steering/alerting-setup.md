# Intelligent Alerting Setup

## Purpose
This steering file provides guidance for setting up effective CloudWatch alarms using recommended configurations and best practices.

## Core Concepts

### Alarm States
- **OK**: Metric is within acceptable threshold
- **ALARM**: Metric has breached threshold
- **INSUFFICIENT_DATA**: Not enough data to evaluate

### Alarm Components
- **Metric**: What to monitor (CPU, errors, latency, etc.)
- **Statistic**: How to aggregate (Average, Sum, Maximum, percentiles)
- **Threshold**: Value that triggers alarm
- **Evaluation Period**: How long to evaluate
- **Datapoints to Alarm**: How many periods must breach

### Alarm Types
- **Metric Alarm**: Based on single CloudWatch metric
- **Composite Alarm**: Combines multiple alarms with logic (AND, OR, NOT)
- **Anomaly Detection Alarm**: Uses ML to detect unusual patterns

## Getting Recommended Alarm Configurations

### Using get_recommended_metric_alarms

The power includes intelligent alarm recommendations based on AWS best practices:

```
Tool: get_recommended_metric_alarms

Parameters:
  - namespace: AWS service namespace (e.g., "AWS/Lambda")
  - metric_name: Metric to monitor (e.g., "Errors")
  - dimensions: Resource identifiers
  - statistic: Appropriate statistic for metric type

Returns:
  - Recommended threshold values
  - Evaluation periods
  - Datapoints to alarm
  - Alarm description
  - Rationale for recommendations
```

### Choosing the Right Statistic

**Critical Rule**: The statistic must match the metric type:

**Count Metrics** (use `Sum`):
- Errors, Faults, Throttles
- Invocations, RequestCount
- CacheHits, CacheMisses
- Connections, EventsProcessed

**Utilization Metrics** (use `Average`):
- CPUUtilization, MemoryUtilization
- DiskUtilization, NetworkUtilization
- DatabaseConnections (as percentage)

**Latency/Time Metrics** (use `Average` or percentiles):
- Duration, Latency, ResponseTime
- ProcessingTime, ExecutionTime
- Delay, WaitTime

**Size Metrics** (use `Average`):
- PayloadSize, MessageSize
- RequestSize, BodySize

## Alarm Configuration Patterns

### Pattern 1: Lambda Function Errors

**Recommended Configuration**:
```
Metric: AWS/Lambda - Errors
Statistic: Sum
Threshold: > 5 errors
Evaluation Period: 5 minutes
Datapoints to Alarm: 2 out of 3
Treat Missing Data: notBreaching

Rationale:
- Sum is correct for count metrics
- 5 errors allows for occasional failures
- 2 out of 3 reduces false positives
- 5-minute periods balance responsiveness and stability
```

**Example**:
```
get_recommended_metric_alarms(
  namespace="AWS/Lambda",
  metric_name="Errors",
  dimensions=[{name: "FunctionName", value: "my-function"}],
  statistic="Sum"
)
```

### Pattern 2: EC2 CPU Utilization

**Recommended Configuration**:
```
Metric: AWS/EC2 - CPUUtilization
Statistic: Average
Threshold: > 80%
Evaluation Period: 5 minutes
Datapoints to Alarm: 3 out of 3
Treat Missing Data: notBreaching

Rationale:
- Average smooths out spikes
- 80% allows for burst capacity
- 3 out of 3 ensures sustained high CPU
- Prevents alarms during brief spikes
```

### Pattern 3: API Gateway Latency

**Recommended Configuration**:
```
Metric: AWS/ApiGateway - Latency
Statistic: p99 (99th percentile)
Threshold: > 1000ms
Evaluation Period: 5 minutes
Datapoints to Alarm: 2 out of 3
Treat Missing Data: notBreaching

Rationale:
- p99 catches tail latency issues
- 1000ms threshold for user experience
- 2 out of 3 balances sensitivity
- Focuses on worst-case performance
```

### Pattern 4: RDS Database Connections

**Recommended Configuration**:
```
Metric: AWS/RDS - DatabaseConnections
Statistic: Average
Threshold: > 80% of max_connections
Evaluation Period: 5 minutes
Datapoints to Alarm: 3 out of 3
Treat Missing Data: notBreaching

Rationale:
- Average shows sustained connection usage
- 80% threshold provides buffer
- 3 out of 3 ensures real issue
- Prevents connection pool exhaustion
```

### Pattern 5: DynamoDB Throttles

**Recommended Configuration**:
```
Metric: AWS/DynamoDB - UserErrors
Statistic: Sum
Threshold: > 10 errors
Evaluation Period: 1 minute
Datapoints to Alarm: 2 out of 2
Treat Missing Data: notBreaching

Rationale:
- Sum is correct for error counts
- 10 errors indicates capacity issue
- 1-minute periods for quick detection
- 2 out of 2 confirms sustained throttling
```

## Composite Alarms

### Use Cases for Composite Alarms

**Scenario 1: Service Health**
Combine multiple metrics to determine overall service health:

```
Composite Alarm: "api-service-unhealthy"

Logic: (high-error-rate OR high-latency) AND low-success-rate

Component Alarms:
  - high-error-rate: Errors > 5%
  - high-latency: p99 Latency > 2000ms
  - low-success-rate: Success rate < 95%

Rationale: Service is unhealthy if errors OR latency are high AND success rate is low
```

**Scenario 2: Dependency Failure**
Detect when a service and its dependencies are failing:

```
Composite Alarm: "service-and-dependency-down"

Logic: service-errors AND (database-errors OR cache-errors)

Component Alarms:
  - service-errors: Lambda Errors > 10
  - database-errors: RDS CPUUtilization > 90%
  - cache-errors: ElastiCache Evictions > 1000

Rationale: Service errors combined with dependency issues indicate cascading failure
```

## Anomaly Detection Alarms

### When to Use Anomaly Detection

**Good Use Cases**:
- Metrics with predictable patterns (daily, weekly cycles)
- Metrics where absolute thresholds are hard to define
- Detecting unusual behavior vs normal patterns

**Example: Request Count Anomaly**:
```
Metric: AWS/ApiGateway - Count
Anomaly Detection: Enabled
Threshold: 2 standard deviations
Evaluation Period: 10 minutes

Rationale:
- Request patterns vary by time of day
- Anomaly detection learns normal patterns
- 2 std dev catches significant deviations
- Adapts to traffic growth over time
```

## Alarm Best Practices

### 1. Alarm Naming Convention

Use descriptive, consistent names:
```
Format: [severity]-[service]-[metric]-[condition]

Examples:
- critical-api-error-rate-high
- warning-lambda-duration-p99-high
- info-rds-connections-approaching-limit
```

### 2. Alarm Descriptions

Include actionable information:
```
Description Template:
"[Service] [Metric] is [Condition]. 
Current value: {{value}} {{unit}}
Threshold: {{threshold}} {{unit}}
Runbook: [link to runbook]
Dashboard: [link to dashboard]"

Example:
"API Gateway error rate is above 5%.
Current value: 8.2%
Threshold: 5%
Runbook: https://wiki.company.com/runbooks/api-errors
Dashboard: https://console.aws.amazon.com/cloudwatch/dashboards/api-health"
```

### 3. Alarm Actions

Configure appropriate actions for each severity:

**Critical Alarms**:
- Page on-call engineer (PagerDuty, Opsgenie)
- Post to critical alerts channel (Slack, Teams)
- Create high-priority ticket

**Warning Alarms**:
- Post to team channel
- Create normal-priority ticket
- Email team distribution list

**Info Alarms**:
- Log to monitoring system
- Email individual owner
- No immediate action required

### 4. Treat Missing Data

Choose appropriate behavior:

- **notBreaching**: Use for most alarms (default)
- **breaching**: Use when missing data indicates problem
- **ignore**: Use when data is expected to be sparse
- **missing**: Treat as INSUFFICIENT_DATA

### 5. Evaluation Periods

Balance responsiveness vs stability:

**Fast Detection** (1-2 minutes):
- Critical services
- User-facing errors
- Security events

**Balanced** (5 minutes):
- Most application metrics
- Resource utilization
- Performance metrics

**Slow Detection** (10-15 minutes):
- Cost metrics
- Capacity planning
- Trend analysis

## SLO-Based Alerting

### Integrating with Application Signals SLOs

**Approach**: Use SLO error budget consumption for alerting

**Example: Availability SLO**:
```
SLO: 99.9% availability (30-day window)
Error Budget: 0.1% = 43.2 minutes downtime/month

Alerts:
1. Warning: 50% error budget consumed (21.6 min)
2. Critical: 80% error budget consumed (34.6 min)
3. Emergency: 100% error budget consumed (43.2 min)

Actions:
- Warning: Notify team, review recent changes
- Critical: Page on-call, implement feature freeze
- Emergency: All hands, immediate mitigation
```

**Implementation**:
```
1. Set up SLO in Application Signals
2. Create CloudWatch alarm on error budget metric
3. Configure multi-level thresholds
4. Link to incident response procedures
```

## Alarm Tuning and Maintenance

### Reducing False Positives

**Symptoms**:
- Alarms trigger frequently but no real issue
- Team ignores alarms (alarm fatigue)
- Alarms trigger during known maintenance

**Solutions**:

1. **Adjust Thresholds**:
   - Review alarm history
   - Analyze metric patterns
   - Increase threshold if too sensitive
   - Use percentiles instead of max/min

2. **Increase Datapoints to Alarm**:
   - Change from 1 out of 1 to 2 out of 3
   - Requires sustained breach
   - Reduces transient spikes

3. **Use Composite Alarms**:
   - Combine multiple signals
   - Require multiple conditions
   - More accurate detection

4. **Implement Maintenance Windows**:
   - Suppress alarms during deployments
   - Use CloudWatch alarm actions
   - Document maintenance schedules

### Handling Alarm Flapping

**Symptoms**:
- Alarm rapidly switches between OK and ALARM
- Metric oscillates around threshold
- Unclear if real issue exists

**Solutions**:

1. **Increase Evaluation Period**:
   - Use longer time windows
   - Smooth out oscillations
   - Focus on sustained issues

2. **Add Hysteresis**:
   - Use different thresholds for alarm and recovery
   - Example: Alarm at 80%, recover at 70%
   - Prevents rapid state changes

3. **Use Anomaly Detection**:
   - Adapts to metric patterns
   - Less sensitive to threshold proximity
   - Better for variable metrics

## Alarm Testing

### Validating Alarm Configuration

**Test Checklist**:
- [ ] Alarm triggers when metric breaches threshold
- [ ] Alarm recovers when metric returns to normal
- [ ] Alarm actions execute correctly (notifications sent)
- [ ] Alarm description is clear and actionable
- [ ] Runbook link works and is up-to-date
- [ ] On-call receives notification within SLA

**Testing Approaches**:

1. **Synthetic Testing**:
   - Inject errors or load
   - Verify alarm triggers
   - Confirm notifications

2. **Historical Analysis**:
   - Review past incidents
   - Check if alarm would have triggered
   - Adjust configuration if needed

3. **Chaos Engineering**:
   - Deliberately cause failures
   - Validate detection and alerting
   - Test incident response procedures

## Integration with Incident Response

### Alarm-Driven Workflows

**Workflow 1: Alarm Triggers Investigation**:
```
1. Alarm triggers → Notification sent
2. On-call checks alarm details
3. Query CloudWatch Logs for errors
4. Analyze Application Signals traces
5. Check CloudTrail for recent changes (use data source priority)
6. Implement mitigation
7. Update alarm if needed
```

**Workflow 2: Proactive Monitoring**:
```
1. Review alarm history daily
2. Identify patterns and trends
3. Tune thresholds before issues occur
4. Add missing alarms for gaps
5. Document learnings in runbooks
```

## Quick Reference

### Get Alarm Recommendations

```
# Lambda Errors
get_recommended_metric_alarms(
  namespace="AWS/Lambda",
  metric_name="Errors",
  dimensions=[{name: "FunctionName", value: "my-function"}],
  statistic="Sum"
)

# EC2 CPU
get_recommended_metric_alarms(
  namespace="AWS/EC2",
  metric_name="CPUUtilization",
  dimensions=[{name: "InstanceId", value: "i-1234567890abcdef0"}],
  statistic="Average"
)

# API Gateway Latency
get_recommended_metric_alarms(
  namespace="AWS/ApiGateway",
  metric_name="Latency",
  dimensions=[{name: "ApiName", value: "my-api"}],
  statistic="p99"
)
```

### Check Active Alarms

```
get_active_alarms(state_value="ALARM")
```

### Review Alarm History

```
get_alarm_history(
  alarm_name="my-alarm",
  history_item_type="StateUpdate",
  start_time="2026-01-01T00:00:00Z",
  end_time="2026-01-20T00:00:00Z"
)
```

---

**Remember**: Effective alerting requires continuous tuning. Start with recommended configurations, monitor for false positives, and adjust based on your specific needs and patterns.
