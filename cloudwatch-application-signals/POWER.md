---
name: "cloudwatch-application-signals"
displayName: "[DEPRECATED] Amazon CloudWatch Application Signals"
description: ":warning: DEPRECATED: This power has been merged into the AWS Observability power, which provides expanded capabilities including CloudWatch Logs, Metrics, Alarms, Application Signals (APM), CloudTrail security auditing, and automated codebase observability gap analysis. We recommend installing the AWS Observability power for a more comprehensive monitoring experience. See steps in `Migrating to AWS Observability power`"
keywords: ["application-signals", "aws", "observability", "apm", "slo", "traces", "monitoring", "cloudwatch", "audit"]
author: "AWS"
---

# Migrating to AWS Observability power

1. **Install the AWS Observability power:**
- Open Kiro Powers panel
- Search for "AWS Observability"
- Click Install

2. **Uninstall this power:**
- Your Application Signals MCP server will continue working
- All functionality is available in AWS Observability

3. **No configuration changes needed:**
- The MCP server configuration is identical
- All tools and workflows remain the same

## Timeline

- **Now:** This power is deprecated but still functional
- **March 27, 2026:** This power will be removed from the registry
- **After March 27, 2026::** Only available through AWS Observability power

# Onboarding

## Prerequisites

1. **AWS CLI configured** with credentials (`aws configure` or `~/.aws/credentials`)
2. **Application Signals enabled** in your AWS account ([Getting started with Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Intro.html))
3. **Python 3.10+** and `uv` installed ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

## Configuration

After installing this power, update the MCP server configuration with your AWS profile and region:

1. Open Kiro Settings → MCP Servers (or edit `~/.kiro/settings/mcp.json`)
2. Find `awslabs.cloudwatch-applicationsignals-mcp-server`
3. Update the `env` section:

```json
"env": {
  "AWS_PROFILE": "your-profile-name",  // ← Change to your AWS profile
  "AWS_REGION": "us-east-1",           // ← Change to your region
  "FASTMCP_LOG_LEVEL": "ERROR"
}
```

**Default:** Uses `default` AWS profile and `us-east-1` region.

## Quick Test

After configuration, try: *"List all my monitored services"*

---

# Overview

The Amazon CloudWatch Application Signals Power provides comprehensive tools for monitoring and analyzing AWS services using Application Signals. Perform service health audits, track SLO compliance, investigate performance issues, and conduct root cause analysis with distributed tracing.

**Key capabilities:**
- **Service Health Auditing** - Comprehensive health assessment with actionable insights
- **SLO Compliance Monitoring** - Track Service Level Objectives with breach detection
- **Operation-Level Analysis** - Deep dive into specific API endpoints and operations
- **100% Trace Visibility** - Query OpenTelemetry spans via Transaction Search
- **Canary Failure Analysis** - Root cause investigation for CloudWatch Synthetics canaries
- **Enablement Guidance** - AI-guided setup for Application Signals instrumentation

**Authentication**: Requires AWS credentials (AWS CLI profile or IAM role).

## Available Steering Files

- **steering/steering.md** - Audit workflows, investigation patterns, and target format reference

## Available MCP Servers

### awslabs.cloudwatch-applicationsignals-mcp-server

**Package:** `awslabs.cloudwatch-applicationsignals-mcp-server`

#### Configuration

Requires AWS credentials and appropriate IAM permissions. Configure via `mcp.json`:

```json
{
  "mcpServers": {
    "awslabs.cloudwatch-applicationsignals-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.cloudwatch-applicationsignals-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

#### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "application-signals:ListServices",
        "application-signals:GetService",
        "application-signals:ListServiceOperations",
        "application-signals:ListServiceLevelObjectives",
        "application-signals:GetServiceLevelObjective",
        "application-signals:BatchGetServiceLevelObjectiveBudgetReport",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "logs:GetQueryResults",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:FilterLogEvents",
        "xray:GetTraceSummaries",
        "xray:BatchGetTraces",
        "xray:GetTraceSegmentDestination",
        "synthetics:GetCanary",
        "synthetics:GetCanaryRuns",
        "s3:GetObject",
        "s3:ListBucket",
        "iam:GetRole",
        "iam:ListAttachedRolePolicies",
        "iam:GetPolicy",
        "iam:GetPolicyVersion"
      ],
      "Resource": "*"
    }
  ]
}
```

## Tools Reference

### Primary Audit Tools

#### audit_services ⭐
**Primary tool for service health auditing**

- `service_targets` (required): JSON array of service targets with wildcard support
- `auditors` (optional): Comma-separated auditors (default: `slo,operation_metric`, use `all` for root cause analysis)
- `start_time` / `end_time` (optional): Time range (default: last 24h)

#### audit_slos ⭐
**Primary tool for SLO compliance monitoring**

- `slo_targets` (required): JSON array of SLO targets with wildcard support
- `auditors` (optional): Comma-separated auditors (default: `slo`, use `all` for root cause analysis)
- `start_time` / `end_time` (optional): Time range

#### audit_service_operations ⭐
**Primary tool for operation-specific analysis**

- `operation_targets` (required): JSON array of operation targets with wildcard support
- `auditors` (optional): Comma-separated auditors (default: `operation_metric`)
- `start_time` / `end_time` (optional): Time range

### Service Discovery Tools

#### list_monitored_services
Lists all services monitored by Application Signals.

#### get_service_detail
Get metadata and configuration for a specific service.
- `service_name` (required): Service name (case-sensitive)

#### list_service_operations
List operations for a service (only recently invoked operations).
- `service_name` (required): Service name
- `hours` (optional): Lookback hours (default: 24, max: 24)

### SLO Management Tools

#### get_slo
Get detailed SLO configuration.
- `slo_id` (required): SLO ARN or name

#### list_slos
List all SLOs in the account.
- `key_attributes` (optional): JSON filter by service attributes
- `max_results` (optional): Max results (default: 50)

#### list_slis
Legacy SLI status report with breach summary.
- `hours` (optional): Lookback hours (default: 24)

### Metrics Tools

#### query_service_metrics
Get CloudWatch metrics for a service.
- `service_name` (required): Service name
- `metric_name` (required): Metric name (Latency, Error, Fault)
- `hours` (optional): Lookback hours (default: 1)
- `statistic` (optional): Average, Sum, Maximum, Minimum, SampleCount
- `extended_statistic` (optional): p99, p95, p90, p50

### Trace & Log Analysis Tools

#### search_transaction_spans
Query OpenTelemetry spans (100% sampled) via CloudWatch Logs Insights.
- `query_string` (required): CloudWatch Logs Insights query
- `log_group_name` (optional): Log group (default: `aws/spans`)
- `start_time` / `end_time` (optional): Time range
- `limit` (optional): Max results

#### query_sampled_traces
Query X-Ray traces (5% sampled).
- `filter_expression` (optional): X-Ray filter expression
- `start_time` / `end_time` (optional): Time range

### Canary Analysis Tools

#### analyze_canary_failures
Deep dive into CloudWatch Synthetics canary failures.
- `canary_name` (required): Canary name
- `region` (optional): AWS region (default: us-east-1)

### Enablement Tools

#### get_enablement_guide
Get step-by-step guide for enabling Application Signals.
- `service_platform` (required): ec2, ecs, lambda, or eks
- `service_language` (required): python, nodejs, java, or dotnet
- `iac_directory` (required): Absolute path to IaC code
- `app_directory` (required): Absolute path to application code

## Tool Usage Examples

### Audit All Services

```javascript
audit_services({
  "service_targets": "[{\"Type\":\"service\",\"Data\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"*\"}}}]"
})
// Returns: Health status for all monitored services
```

### Audit Payment Services with Root Cause Analysis

```javascript
audit_services({
  "service_targets": "[{\"Type\":\"service\",\"Data\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"*payment*\"}}}]",
  "auditors": "all"
})
// Returns: Comprehensive analysis with traces, logs, metrics, dependencies
```

### Audit All SLOs

```javascript
audit_slos({
  "slo_targets": "[{\"Type\":\"slo\",\"Data\":{\"Slo\":{\"SloName\":\"*\"}}}]"
})
// Returns: SLO compliance status for all SLOs
```

### Audit GET Operations in Payment Services

```javascript
audit_service_operations({
  "operation_targets": "[{\"Type\":\"service_operation\",\"Data\":{\"ServiceOperation\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"*payment*\"},\"Operation\":\"*GET*\",\"MetricType\":\"Latency\"}}}]"
})
// Returns: Latency analysis for GET operations
```

### Search Transaction Spans

```javascript
search_transaction_spans({
  "query_string": "FILTER attributes.aws.local.service = \"checkout-service\" and attributes.http.status_code >= 400 | STATS count() as error_count by attributes.aws.local.operation | LIMIT 20",
  "start_time": "2025-01-15T10:00:00Z",
  "end_time": "2025-01-15T11:00:00Z"
})
// Returns: Error counts by operation (100% sampled data)
```

### Analyze Canary Failures

```javascript
analyze_canary_failures({
  "canary_name": "checkout-canary",
  "region": "us-east-1"
})
// Returns: Root cause analysis with artifacts, logs, and recommendations
```

## Combining Tools (Workflows)

### Workflow 1: Service Health Investigation

```javascript
// Step 1: Audit all services for issues
const findings = audit_services({
  "service_targets": "[{\"Type\":\"service\",\"Data\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"*\"}}}]"
})

// Step 2: Deep dive into problematic service
const rootCause = audit_services({
  "service_targets": "[{\"Type\":\"service\",\"Data\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"payment-service\"}}}]",
  "auditors": "all"
})
```

### Workflow 2: SLO Breach Investigation

```javascript
// Step 1: Get SLO configuration
const sloConfig = get_slo({
  "slo_id": "checkout-latency-slo"
})

// Step 2: Comprehensive root cause analysis
const analysis = audit_slos({
  "slo_targets": "[{\"Type\":\"slo\",\"Data\":{\"Slo\":{\"SloName\":\"checkout-latency-slo\"}}}]",
  "auditors": "all"
})
```

### Workflow 3: Operation Performance Analysis

```javascript
// Step 1: Identify slow operations
const operations = audit_service_operations({
  "operation_targets": "[{\"Type\":\"service_operation\",\"Data\":{\"ServiceOperation\":{\"Service\":{\"Type\":\"Service\",\"Name\":\"api-service\"},\"Operation\":\"*\",\"MetricType\":\"Latency\"}}}]"
})

// Step 2: Get 100% trace data for slow operation
const traces = search_transaction_spans({
  "query_string": "FILTER attributes.aws.local.service = \"api-service\" and attributes.aws.local.operation = \"GET /api/orders\" | STATS avg(duration) as avg_latency, count() as request_count | LIMIT 50"
})
```

## Best Practices

### ✅ Do:
- **Start with primary audit tools** (`audit_services`, `audit_slos`, `audit_service_operations`)
- **Use wildcard patterns** for service discovery (`*payment*`, `*`)
- **Use `auditors="all"`** for root cause analysis
- **Present findings first**, let user choose what to investigate
- **Use Transaction Search** (`search_transaction_spans`) for 100% trace visibility
- **Narrow time ranges** for faster queries

### ❌ Don't:
- **Jump to root cause analysis** without showing overview first
- **Use X-Ray traces** (`query_sampled_traces`) as primary tool - only 5% sampled
- **Hardcode service names** - use wildcards for discovery
- **Query without time filters** - always specify time range for large datasets

## Environment Variables

- `AWS_PROFILE` - AWS profile name (defaults to `default`)
- `AWS_REGION` - AWS region (defaults to `us-east-1`)
- `FASTMCP_LOG_LEVEL` - Logging level (defaults to `INFO`)
- `AUDITOR_LOG_PATH` - Path for audit log files (defaults to `/tmp`)

## Tips

1. **Start with audit tools** - They provide comprehensive analysis with recommendations
2. **Use wildcards** - `*payment*` discovers all payment-related services
3. **Check SLOs first** - SLO breaches often point to root cause
4. **Use Transaction Search** - 100% sampled data vs X-Ray's 5%
5. **Enable Application Signals** - Use `get_enablement_guide` for setup assistance

---

**Package:** `awslabs.cloudwatch-applicationsignals-mcp-server`
**Source:** AWS Labs
**License:** Apache 2.0
**Documentation:** https://awslabs.github.io/mcp/servers/cloudwatch-applicationsignals-mcp-server
