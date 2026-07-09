---
name: "aws-observability"
displayName: "AWS Observability"
description: "Comprehensive AWS observability platform combining CloudWatch Logs, Metrics, Alarms, Application Signals (APM), CloudTrail security auditing, Amazon Managed Prometheus (AMP) metric querying, and automated codebase observability gap analysis, for complete monitoring, troubleshooting, and optimization."
keywords: ["cloudwatch", "logs", "metrics", "traces", "alarms", "alerts", "monitoring", "observability", "application signals", "apm", "distributed tracing", "x-ray", "opentelemetry", "otel", "slow", "latency", "performance", "bottleneck", "degradation", "timeout", "high latency", "slow api", "api performance", "service performance", "response time", "p50", "p90", "p95", "p99", "errors", "error rate", "fault rate", "failure rate", "5xx", "4xx", "exceptions", "availability", "uptime", "downtime", "outage", "sev1", "sev2", "slo", "sli", "service level", "error budget", "breach", "troubleshooting", "root cause", "rca", "investigate", "diagnose", "log analysis", "log insights", "log query", "log patterns", "audit", "cloudtrail", "security audit", "access logs", "iam changes", "change events", "service map", "cascading failure", "canary", "synthetic monitoring", "health check", "observability gaps", "missing instrumentation", "monitoring instrumentation", "structured logging", "silent failures", "logging gaps", "alarm investigation", "trace analysis", "span analysis", "request tracing", "prometheus", "promql", "amp", "amazon managed prometheus", "prometheus metrics", "prometheus query", "prometheus workspace"]
author: "AWS"
---

# ⚠️ CRITICAL: ALWAYS LOAD STEERING FILES FIRST

**BEFORE using ANY tools, you MUST:**

1. **Identify the user's scenario** from their request
2. **Load the appropriate steering file** using `kiroPowers` action with `readSteering`
3. **Follow the steering file's workflow** before making tool calls

## Scenario Detection & Steering File Selection

### 🚨 Incident Response & Troubleshooting → `incident-response.md`

**Load when user mentions:**
- Service health: "unhealthy", "down", "broken", "failing", "degraded", "not working"
- Investigation: "investigate", "troubleshoot", "debug", "what's wrong", "help me check", "root cause"
- Performance: "slow", "timeout", "errors", "high latency", "issues", "performance problems"
- Incidents: "outage", "incident", "production issue", "emergency", "sev1", "sev2"
- Vague concerns: "something's wrong", "having problems", "seems off"

### 📊 Log Analysis → `log-analysis.md`

**Load when user mentions:**
- "query logs", "search logs", "find in logs", "show me logs"
- "log patterns", "parse logs", "filter logs", "extract from logs"
- "aggregate logs", "log statistics", "count errors"

### 🔔 Alerting Setup → `alerting-setup.md`

**Load when user mentions:**
- "set up monitoring", "create alarms", "configure alerts"
- "improve alarms", "reduce false positives", "alarm fatigue"

### � Performance Monitoring → `performance-monitoring.md`

**Load when user mentions:**
- "monitor performance", "check service health", "service metrics"
- "distributed traces", "trace analysis", "X-Ray"
- "SLOs", "Service Level Objectives", "error rates", "latency"

### � Security Auditing → `security-auditing.md`

**Load when user mentions:**
- "security audit", "compliance", "CloudTrail"
- "who did what", "track changes", "API activity"
- "IAM changes", "unauthorized access"

### 🔍 Observability Gaps → `observability-gap-analysis.md`

**Load when user mentions:**
- "audit codebase", "check instrumentation", "observability gaps"
- "missing logs", "improve observability"

### 📈 Prometheus / AMP Metrics → `prometheus-metrics.md`

**Load when user mentions:**
- "prometheus", "promql", "AMP", "managed prometheus"
- "prometheus metrics", "prometheus query", "prometheus workspace"
- "PromQL range query", "list metrics"

### ⚙️ Application Signals Setup → `application-signals-setup.md`

**Load when user mentions:**
- "enable Application Signals", "set up monitoring", "instrument service"
- "auto-instrumentation", "getting started"

---

# Onboarding

## Prerequisites

1. **AWS CLI configured** with credentials (`aws configure` or `~/.aws/credentials`)
2. **Python 3.10+** and `uv` installed ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
3. **Application Signals enabled** in your AWS account whenever applicable ([Getting started with Application Signals](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Monitoring-Intro.html))
4. **Required AWS Permissions**: Your IAM user/role needs:
   - `cloudwatch:*` for CloudWatch Metrics and Alarms
   - `logs:*` for CloudWatch Logs operations (includes CloudTrail log querying)
   - `xray:*` for distributed tracing
   - `cloudtrail:*` for CloudTrail queries
   - `application-signals:*` for Application Signals
   - `synthetics:GetCanary`, `synthetics:GetCanaryRuns` for canary analysis
   - `s3:GetObject`, `s3:ListBucket` for canary artifacts
   - `iam:GetRole`, `iam:ListAttachedRolePolicies`, `iam:GetPolicy`, `iam:GetPolicyVersion` for the enablement guide

## Configuration

After installing this power, update the MCP server configuration with your AWS profile and region:

1. Open Kiro Settings → MCP Servers (or edit `~/.kiro/settings/mcp.json`)
2. Find the `awslabs.cloudwatch-mcp-server` entry
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

After configuration, try: *"Show me my CloudWatch log groups"*

---

# Overview

The comprehensive AWS observability platform combining monitoring, troubleshooting, security, and optimization tools in one power.

**Key capabilities:**
- **CloudWatch Logs** - Query and analyze logs using CloudWatch Logs Insights
- **Metrics & Alarms** - Metric querying with Metrics Insights and intelligent alarm recommendations
- **Application Signals** - APM with distributed tracing, service maps, SLOs, and enablement guides
- **Amazon Managed Prometheus** - PromQL queries against AMP workspaces with SigV4 authentication
- **Codebase Observability Analysis** - Automated analysis of codebases to identify observability gaps
- **CloudTrail Integration** - Security auditing and compliance tracking
- **AWS Documentation** - Direct access to official AWS docs for troubleshooting

**Authentication**: Requires AWS credentials (AWS CLI profile or IAM role).

## Core Capabilities

### 1. CloudWatch Logs

**Primary Use Case**: Query and analyze logs using CloudWatch Logs Insights

**Key Features**:
- CloudWatch Logs Insights query syntax for log analysis
- Multi-log-group queries across up to 50 log groups
- JSON field extraction with parse and filter commands
- Statistical functions and aggregations
- Pattern detection and anomaly analysis
- Log group discovery and metadata
- Saved queries support

**When to Use**:
- Searching and filtering log data across services
- Aggregations and statistical analysis
- Querying multiple log groups simultaneously
- Extracting structured data from JSON logs
- Troubleshooting distributed application issues

### 2. CloudWatch Metrics & Alarms

**Primary Use Case**: Monitor resource performance and set up intelligent alerting

**Key Features**:
- Retrieve metric data with multiple statistics (Average, Sum, Min, Max, percentiles)
- Metrics Insights for advanced filtering and grouping
- Analyze metric trends, seasonality, and anomalies
- Get recommended alarm configurations based on AWS best practices
- View active alarms and alarm history
- Support for custom metrics and composite alarms

**When to Use**:
- Monitoring EC2, Lambda, RDS, and other AWS service metrics
- Setting up performance baselines and thresholds
- Creating intelligent alarms with recommended configurations
- Investigating active alarms and reviewing alarm history
- Analyzing metric trends and detecting anomalies
- Troubleshooting performance degradation

### 3. Application Signals (APM)

**Primary Use Case**: Application performance monitoring with distributed tracing

**Key Features**:
- Service-level metrics and SLOs
- Distributed tracing with AWS X-Ray integration
- Service maps showing dependencies and call paths
- Error rate and latency tracking (P50, P90, P95, P99)
- Automatic service discovery
- SLO compliance monitoring and error budget tracking
- Enablement guide for setup assistance
- Primary audit tools (`audit_services`, `audit_slos`, `audit_service_operations`) as recommended entry points for all investigation workflows, with wildcard targeting and 7 auditor types (`slo`, `operation_metric`, `trace`, `log`, `dependency_metric`, `top_contributor`, `service_quota`)
- 100% Trace Visibility via `search_transaction_spans` querying OpenTelemetry spans through CloudWatch Logs Insights (vs X-Ray's 5% sampling)
- Canary Failure Analysis via `analyze_canary_failures` for root cause investigation of CloudWatch Synthetics canaries

**When to Use**:
- Monitoring microservices health and performance
- Troubleshooting latency and error rate issues
- Understanding service dependencies and bottlenecks
- Setting up and tracking SLOs
- Root cause analysis for distributed systems
- Getting started with Application Signals setup

### 4. CloudTrail Security Auditing

**Primary Use Case**: Security auditing, compliance, and governance

**Data Source Priority**: CloudTrail data is accessed through multiple sources in priority order:
1. **CloudTrail Lake** (Priority 1) - SQL-based querying with 7-year retention
2. **CloudWatch Logs** (Priority 2) - Real-time analysis with CloudWatch integration
3. **Lookup Events API** (Priority 3) - Fallback for basic queries (90-day limit)

See `cloudtrail-data-source-selection.md` steering file for detailed decision tree.

**Key Features**:
- API call history and analysis
- User activity tracking across AWS accounts
- Resource change tracking and audit trails
- IAM permission change monitoring
- Compliance reporting and security investigations
- Multiple data source options for flexibility

**When to Use**:
- Investigating security incidents
- Tracking resource modifications and deletions
- Compliance auditing and reporting
- Understanding who did what and when
- Detecting unauthorized access attempts
- Root cause analysis for configuration changes

### 5. Amazon Managed Prometheus (AMP)

**Primary Use Case**: Query and analyze Prometheus metrics from AWS Managed Prometheus workspaces

**Key Features**:
- Execute instant and range PromQL queries
- List available metrics in a workspace
- Discover and manage AMP workspaces
- AWS SigV4 authentication for secure access
- Retrieve server configuration details

**When to Use**:
- Querying Prometheus metrics from AMP workspaces
- Analyzing container and Kubernetes metrics
- Running PromQL range queries for trend analysis
- Listing available metrics across workspaces
- Correlating Prometheus metrics with CloudWatch data

### 6. Codebase Observability Analysis

**Primary Use Case**: Automated analysis of application codebases to identify observability gaps

**Key Features**:
- Multi-language support (Python, Java, JavaScript/TypeScript, Go, Ruby, C#/.NET)
- Logging pattern analysis and gap identification
- Metrics instrumentation assessment
- Distributed tracing coverage evaluation
- Error handling review
- Health check and readiness probe validation
- Actionable recommendations with code examples
- Prioritized gap reports by severity

**When to Use**:
- Auditing existing applications for observability best practices
- Onboarding new services to observability standards
- Improving debugging and troubleshooting capabilities
- Preparing for production deployments
- Establishing observability baselines
- Training teams on observability patterns

### 7. AWS Documentation Access

**Primary Use Case**: Quick access to official AWS documentation

**Key Features**:
- Search AWS documentation directly
- Read documentation pages in markdown format
- Get content recommendations for related topics
- Access service-specific guides and API references

**When to Use**:
- Looking up AWS service documentation
- Understanding API parameters and behavior
- Finding best practices and tutorials
- Troubleshooting with official guidance

## Available Steering Files

The following steering files provide detailed workflows for each scenario. **Always load the appropriate file first** using the decision tree at the top of this document.

### 1. `incident-response.md`
Comprehensive incident response framework with multi-tool correlation strategies.

### 2. `log-analysis.md`
CloudWatch Logs Insights query patterns and log analysis techniques.

### 3. `alerting-setup.md`
Intelligent alarm configuration and notification strategies.

### 4. `performance-monitoring.md`
Application Signals APM workflows and performance optimization.

### 5. `security-auditing.md`
CloudTrail security analysis and compliance auditing.

### 6. `observability-gap-analysis.md`
Codebase instrumentation assessment and recommendations.

### 7. `application-signals-setup.md`
Step-by-step Application Signals enablement guide.

### 8. `cloudtrail-data-source-selection.md`
CloudTrail data source priority logic (referenced by security-auditing.md).

### 9. `prometheus-metrics.md`
PromQL querying, metric exploration, and AMP workspace management.

## Quick Start Examples

### Example 1: Investigate High Error Rate

```
1. Load incident-response.md steering file
2. Follow the structured workflow:
   - Check active alarms for service health
   - Query CloudWatch Logs for error patterns
   - Review CloudTrail for recent changes
   - Analyze traces for root cause
   - Check AWS Documentation for error codes
```

### Example 2: Performance Optimization

```
1. Load performance-monitoring.md steering file
2. Follow the workflow:
   - Analyze CloudWatch Metrics
   - Query Application Signals for P95/P99 latency
   - Examine logs for patterns
```

### Example 3: Security Audit

```
1. Load security-auditing.md steering file
2. Follow the workflow:
   - Query CloudTrail events
   - Correlate with CloudWatch Logs
   - Check Application Signals for unusual patterns
   - Document findings with AWS documentation
```

### Example 4: Codebase Observability Gap Audit

```
1. Load observability-gap-analysis.md steering file
2. Follow the workflow:
   - Analyze codebase structure
   - Assess logging coverage
   - Evaluate metrics instrumentation
   - Review distributed tracing
   - Generate actionable report
```

## Available MCP Servers

### awslabs.cloudwatch-mcp-server
CloudWatch Logs querying, Metrics, Alarms, and log group analysis.

### awslabs.cloudwatch-applicationsignals-mcp-server
Application Signals APM with service health, SLOs, and distributed tracing.

### awslabs.cloudtrail-mcp-server
CloudTrail security auditing and API activity tracking.

### awslabs.prometheus-mcp-server
Amazon Managed Prometheus PromQL queries, metric listing, and workspace management.

### awslabs.aws-documentation-mcp-server
Search and read official AWS documentation.

## License
This power integrates with CloudWatch MCP Server, CloudWatch Application Signals MCP Server, CloudTrail MCP Server, Prometheus MCP Server, and AWS Documentation MCP Server from [AWS Labs](https://github.com/awslabs/mcp) (Apache-2.0 license). All steering files and power configuration are licensed under Apache-2.0.

---

**Source:** AWS Labs
**License:** Apache 2.0
**Documentation:** https://github.com/awslabs/mcp
