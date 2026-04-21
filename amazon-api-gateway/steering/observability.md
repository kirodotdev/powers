# Observability and Monitoring

## Table of Contents

- [Logging](#logging)
  - [Execution Logging](#execution-logging-rest-api-and-websocket)
  - [Access Logging](#access-logging)
  - [Log Retention](#log-retention)
  - [REST API Access Log Format](#recommended-access-log-format-rest-api)
  - [HTTP API Access Log Format](#http-api-access-log-format)
  - [WebSocket API Access Log Format](#websocket-api-access-log-format)
  - [Enhanced Observability Variables](#enhanced-observability-variables)
- [Setting Up Logging](#setting-up-logging)
- [CloudWatch Metrics](#cloudwatch-metrics)
- [CloudWatch Alarms](#cloudwatch-alarms)
- [CloudWatch Metric Filters](#cloudwatch-metric-filters)
- [X-Ray Tracing](#x-ray-tracing)
- [CloudWatch Logs Insights Queries](#cloudwatch-logs-insights-queries)
- [Additional Monitoring Tools](#additional-monitoring-tools)
- [API Analytics Pipeline](#api-analytics-pipeline)
- [Cross-Account and Centralized Logging](#cross-account-and-centralized-logging)
- [CloudTrail](#cloudtrail)

---

## Logging

### Execution Logging (REST API and WebSocket)

- Full request/response logs including mapping template output, integration request/response, authorizer output
- Levels: OFF, ERROR, INFO
- **Log events truncated at 1,024 bytes**; use access logs for complete data
- Log group: `API-Gateway-Execution-Logs_<apiId>/<stageName>` (both REST and WebSocket)
- HTTP API does NOT support execution logging
- **Cost warning**: INFO-level execution logging generates many log events per request (10-60+ depending on API complexity: authorizers, mapping templates, and integration details all add entries). At scale, CloudWatch Logs costs can exceed Lambda + API Gateway costs combined. Use ERROR level in production and enable INFO only for targeted debugging

### What API Gateway Does NOT Log

- 413 Request Entity Too Large
- Excessive 429 throttling responses
- 400 errors to unmapped custom domains
- Internal 500 errors from API Gateway itself

### Access Logging

- Customizable log format using `$context` variables
- Formats: CLF, JSON, XML, CSV
- Access log template max: 3 KB
- Destinations: CloudWatch Logs or Kinesis Data Firehose (REST only for Firehose)
- HTTP API: Only access logging supported (no execution logging)
- **Delivery latency**: Access logs can be delayed by several minutes. Use CloudWatch metrics (near-real-time) for dashboards and alarms; use access logs for investigation and deep analysis

### Log Retention

CloudWatch Logs default to **Never Expire**, which causes unbounded storage costs. Always set retention policies:

- **Execution logs (INFO)**: 3-7 days (debugging only, high volume)
- **Execution logs (ERROR)**: 14-30 days
- **Access logs**: 30-90 days (or longer for compliance)
- **Compliance/audit logs**: 1-3 years per organizational policy

Define log groups explicitly in SAM/CloudFormation to control retention:

```yaml
ApiAccessLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub "/aws/apigateway/${MyApi}/access-logs"
    RetentionInDays: 90
```

### Recommended Access Log Format (REST API)

Use this JSON format for maximum troubleshooting capability with enhanced observability variables:

**Note**: This format is for REST APIs. HTTP API and WebSocket API use different `$context` variables; see the API-specific formats below.

```json
{
  "requestId": "$context.requestId",
  "extendedRequestId": "$context.extendedRequestId",
  "ip": "$context.identity.sourceIp",
  "caller": "$context.identity.caller",
  "user": "$context.identity.user",
  "accountId": "$context.identity.accountId",
  "userAgent": "$context.identity.userAgent",
  "requestTime": "$context.requestTime",
  "requestTimeEpoch": "$context.requestTimeEpoch",
  "httpMethod": "$context.httpMethod",
  "resourcePath": "$context.resourcePath",
  "path": "$context.path",
  "status": "$context.status",
  "protocol": "$context.protocol",
  "responseLength": "$context.responseLength",
  "responseLatency": "$context.responseLatency",
  "integrationLatency": "$context.integrationLatency",
  "domainName": "$context.domainName",
  "apiId": "$context.apiId",
  "stage": "$context.stage",
  "error-message": "$context.error.message",
  "error-responseType": "$context.error.responseType",
  "waf-error": "$context.waf.error",
  "waf-status": "$context.waf.status",
  "waf-latency": "$context.waf.latency",
  "waf-response": "$context.wafResponseCode",
  "authenticate-error": "$context.authenticate.error",
  "authenticate-status": "$context.authenticate.status",
  "authenticate-latency": "$context.authenticate.latency",
  "authorizer-error": "$context.authorizer.error",
  "authorizer-status": "$context.authorizer.status",
  "authorizer-latency": "$context.authorizer.latency",
  "authorizer-integrationLatency": "$context.authorizer.integrationLatency",
  "authorize-error": "$context.authorize.error",
  "authorize-status": "$context.authorize.status",
  "authorize-latency": "$context.authorize.latency",
  "integration-error": "$context.integration.error",
  "integration-status": "$context.integration.status",
  "integration-latency": "$context.integration.latency",
  "integration-requestId": "$context.integration.requestId",
  "integration-integrationStatus": "$context.integration.integrationStatus"
}
```

Key variables explained:

- `requestTimeEpoch`: Epoch-millisecond timestamp. Use for programmatic analysis and Athena queries
- `extendedRequestId`: Maps to `x-amz-apigw-id` header. Needed for AWS Support escalations
- `accountId`: AWS account of the caller. Critical for IAM-authenticated and cross-account APIs
- `error-message`: API Gateway's own error message (e.g., "Authorizer error", "Endpoint request timed out")
- `error-responseType`: Gateway Response type triggered (e.g., `AUTHORIZER_FAILURE`, `INTEGRATION_TIMEOUT`, `THROTTLED`). Categorizes errors without execution logs
- `integration-integrationStatus`: Status code from the Lambda service itself (usually 200 even when the function errors)
- `integration-status`: Status code from your Lambda function code (for proxy integrations)

### HTTP API Access Log Format

HTTP API uses different `$context` variables. Key differences from REST API:

- Uses `$context.routeKey` instead of `$context.resourcePath`
- No WAF, authenticate, or authorize phase variables (HTTP API does not have these phases)
- Authorizer variables are available (HTTP API supports JWT and Lambda authorizers)
- No execution logging; access logs are the only log source

```json
{
  "requestId": "$context.requestId",
  "ip": "$context.identity.sourceIp",
  "userAgent": "$context.identity.userAgent",
  "requestTime": "$context.requestTime",
  "requestTimeEpoch": "$context.requestTimeEpoch",
  "routeKey": "$context.routeKey",
  "path": "$context.path",
  "status": "$context.status",
  "protocol": "$context.protocol",
  "responseLength": "$context.responseLength",
  "responseLatency": "$context.responseLatency",
  "integrationLatency": "$context.integrationLatency",
  "domainName": "$context.domainName",
  "apiId": "$context.apiId",
  "stage": "$context.stage",
  "error-message": "$context.error.message",
  "authorizer-error": "$context.authorizer.error",
  "integration-error": "$context.integration.error",
  "integration-status": "$context.integration.status",
  "integration-latency": "$context.integration.latency",
  "integration-integrationStatus": "$context.integration.integrationStatus"
}
```

### WebSocket API Access Log Format

WebSocket APIs use connection-oriented variables instead of HTTP method/path:

```json
{
  "requestId": "$context.requestId",
  "extendedRequestId": "$context.extendedRequestId",
  "connectionId": "$context.connectionId",
  "eventType": "$context.eventType",
  "routeKey": "$context.routeKey",
  "connectedAt": "$context.connectedAt",
  "requestTime": "$context.requestTime",
  "requestTimeEpoch": "$context.requestTimeEpoch",
  "ip": "$context.identity.sourceIp",
  "userAgent": "$context.identity.userAgent",
  "accountId": "$context.identity.accountId",
  "status": "$context.status",
  "domainName": "$context.domainName",
  "apiId": "$context.apiId",
  "stage": "$context.stage",
  "error-message": "$context.error.message",
  "error-responseType": "$context.error.responseType",
  "authorizer-error": "$context.authorizer.error",
  "authorizer-status": "$context.authorizer.status",
  "authorizer-latency": "$context.authorizer.latency",
  "authorizer-integrationLatency": "$context.authorizer.integrationLatency",
  "integration-error": "$context.integration.error",
  "integration-status": "$context.integration.status",
  "integration-latency": "$context.integration.latency",
  "integration-requestId": "$context.integration.requestId"
}
```

Key WebSocket-specific variables:

- `connectionId`: Unique ID for the persistent WebSocket connection
- `eventType`: `CONNECT`, `MESSAGE`, or `DISCONNECT`
- `routeKey`: The matched route (`$connect`, `$disconnect`, `$default`, or custom route keys)
- `connectedAt`: Epoch timestamp when the connection was established

### Enhanced Observability Variables

API Gateway divides REST API requests into phases: **WAF -> Authenticate -> Authorizer -> Authorize -> Integration**

Each phase exposes `$context.{phase}.status`, `$context.{phase}.latency`, and `$context.{phase}.error`.

**Note on authorizer phase**: The authorizer has both `$context.authorizer.latency` (total authorizer latency) and `$context.authorizer.integrationLatency` (time spent in the authorizer Lambda/Cognito call). The difference is API Gateway overhead for the authorizer phase.

**Diagnosing 403 errors by phase:**

- `$context.waf.status: 403` = WAF blocked the request
- `$context.authenticate.status: 403` = Invalid credentials (e.g., malformed SigV4)
- `$context.authorizer.status: 403` = Lambda authorizer returned Deny policy
- `$context.authorize.status: 403` with `$context.authorize.error: "The client is not authorized"` = Valid credentials but insufficient permissions (resource policy or IAM policy denied)

**Key distinction (Lambda proxy integration):**

- `$context.integration.integrationStatus`: Status code from the Lambda **service** (usually 200 even when the function throws an error)
- `$context.integration.status`: Status code from your Lambda **function code** (the `statusCode` field in your function's response)

### Additional Access Log Variables

- `$context.identity.apiKey`: Track which API keys are making requests
- `$context.identity.accountId`: Identify which AWS account is calling (IAM auth, cross-account)
- `$context.domainName`: Differentiate traffic across custom domains
- `$context.customDomain.routingRuleIdMatched`: Track routing rule matches
- `$context.tlsVersion`, `$context.cipherSuite`: Monitor TLS migration
- `$context.authorizer.principalId`: Principal from Lambda authorizer (for user-level tracing)
- `$context.authorizer.claims.sub`: Cognito user pool subject claim (for Cognito-authenticated APIs)
- Response streaming (REST only): `$context.integration.responseTransferMode`, `$context.integration.timeToAllHeaders`, `$context.integration.timeToFirstContent`

## Setting Up Logging

### Prerequisites for REST API and WebSocket

1. Create IAM role with `AmazonAPIGatewayPushToCloudWatchLogs` managed policy
2. Set CloudWatch log role ARN in API Gateway Settings (region-level, one-time configuration)
3. Enable logging per stage

### Prerequisites for HTTP API

HTTP APIs do **not** use the account-level CloudWatch log role. Instead:

1. Create the CloudWatch Logs log group
2. Specify the log group ARN when configuring the stage's access logging
3. API Gateway uses a service-linked role to write logs. Ensure the log group's resource-based policy allows `logs:CreateLogStream` and `logs:PutLogEvents` from the API Gateway service principal

### Missing Logs Troubleshooting

- IAM permissions incorrect (most common for REST/WebSocket)
- Log group resource policy missing (most common for HTTP API)
- Logging not enabled at stage level
- Method-level override disabling logging
- Log group does not exist (create it first or let API Gateway create it)

## CloudWatch Metrics

| Metric               | Description                                                                                                             |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `Count`              | Total API requests                                                                                                      |
| `Latency`            | Time from API Gateway receiving the request to returning the response (does not include client-to-gateway network time) |
| `IntegrationLatency` | Time spent in backend integration                                                                                       |
| `4XXError` / `4xx`   | Client error count. REST API: `4XXError`; HTTP API: `4xx`                                                               |
| `5XXError` / `5xx`   | Server error count. REST API: `5XXError`; HTTP API: `5xx`                                                               |
| `CacheHitCount`      | Cache hits (REST only)                                                                                                  |
| `CacheMissCount`     | Cache misses (REST only)                                                                                                |
| `DataProcessed`      | Amount of data processed in bytes (HTTP API only)                                                                       |

- Default: metrics per API stage
- Detailed metrics: per method (enable on stage)
- Use CloudWatch Embedded Metric Format for business-specific metrics

## CloudWatch Alarms

### Recommended Alarms

Always configure these alarms for production APIs:

**Error rate alarms:**

- `5XXError` rate > 1% of total requests: server errors indicate backend or configuration problems
- `4XXError` rate anomaly detection: spikes indicate breaking changes, auth failures, or abuse
- `IntegrationLatency` p99 > SLA threshold: detect backend degradation before timeouts

**Throttling alarm:**

- `Count` approaching account throttle limit (10,000 rps default). Alert at 80% utilization to request limit increases proactively

**Cache alarms (REST API):**

- Cache hit ratio (`CacheHitCount / (CacheHitCount + CacheMissCount)`) drop below threshold: indicates cache invalidation issues or misconfiguration

### Alarm Examples (CloudFormation)

```yaml
# REST API alarms: use ApiName dimension and 5XXError/4XXError metric names
# HTTP API alarms: use ApiId dimension and 5xx/4xx metric names instead
Api5xxAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${AWS::StackName}-api-5xx-errors"
    MetricName: 5XXError
    Namespace: AWS/ApiGateway
    Dimensions:
      - Name: ApiName
        Value: !Ref MyApi
    Statistic: Sum
    Period: 60
    EvaluationPeriods: 3
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    TreatMissingData: notBreaching
    AlarmActions:
      - !Ref AlertSnsTopic

ApiLatencyAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${AWS::StackName}-api-p99-latency"
    MetricName: Latency
    Namespace: AWS/ApiGateway
    Dimensions:
      - Name: ApiName
        Value: !Ref MyApi
    ExtendedStatistic: p99
    Period: 300
    EvaluationPeriods: 3
    Threshold: 5000
    ComparisonOperator: GreaterThanThreshold
    TreatMissingData: notBreaching
    AlarmActions:
      - !Ref AlertSnsTopic
```

### Composite Alarms

Combine signals to reduce noise:

- High 5xx AND high latency = likely backend failure (page on-call)
- High 4xx only = likely client-side issue (lower priority)

## CloudWatch Metric Filters

Create custom CloudWatch metrics from access log patterns. Metric filters run on the log group and extract numeric values or count pattern matches.

### Error Count by Response Type

```
{ $.["error-responseType"] = "THROTTLED" }
```

Publishes a metric counting throttled requests. Useful since excessive 429s may not be logged by API Gateway itself.

### Slow Requests

```
{ $.responseLatency > 5000 }
```

Counts requests exceeding 5 seconds. Can alarm on this custom metric for tighter latency SLOs than the built-in p99.

### Requests by API Key

Add `"apiKey": "$context.identity.apiKey"` to your log format first, then use:

```
{ $.apiKey != "-" }
```

Use with metric dimensions to track per-consumer request volumes.

## X-Ray Tracing

- **REST API**: Active tracing supported; enable per stage. API Gateway creates the trace segment and adds trace headers to integration requests
- **HTTP API**: X-Ray tracing is [not supported](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html). For distributed tracing, enable X-Ray active tracing on downstream Lambda functions and correlate using the `$context.integration.requestId` access log variable
- Configure sampling rules to control costs and recording criteria
- Service map for latency visualization
- Cross-account tracing requires CloudWatch Observability Access Manager (OAM) configuration between monitoring and source accounts

### Enabling X-Ray in SAM/CloudFormation

```yaml
# REST API with SAM implicit API
Globals:
  Api:
    TracingEnabled: true

# Explicit REST API stage
MyApiStage:
  Type: AWS::ApiGateway::Stage
  Properties:
    TracingEnabled: true
    StageName: prod
    RestApiId: !Ref MyApi
```

For end-to-end distributed tracing, enable X-Ray in both API Gateway and downstream Lambda functions (`Tracing: Active` in SAM function properties). Use X-Ray Groups to filter traces by error, fault, or latency thresholds.

## CloudWatch Logs Insights Queries

### Find 5xx Errors

```
fields @timestamp, status, requestId, ip, resourcePath, integrationLatency
| filter status >= 500
| sort @timestamp desc
| limit 100
```

### Latency Analysis

```
fields @timestamp, responseLatency, integrationLatency, resourcePath
| stats avg(responseLatency) as avgLatency, max(responseLatency) as maxLatency,
        avg(integrationLatency) as avgIntegration by resourcePath
| sort avgLatency desc
```

### Top Talkers

```
fields ip
| stats count(*) as requestCount by ip
| sort requestCount desc
| limit 20
```

### Per-Domain Analytics

```
filter domainName like /(?i)(api.example.com)/
| stats count(*) as requests, avg(responseLatency) as avgLatency by resourcePath
| sort requests desc
```

### Diagnose 403 Errors by Phase

```
fields @timestamp, requestId, ip, resourcePath
| filter status = 403
| stats count(*) as cnt
    by coalesce(`waf-status`, "-") as waf,
       coalesce(`authenticate-status`, "-") as authn,
       coalesce(`authorizer-status`, "-") as authzr,
       coalesce(`authorize-status`, "-") as authz
| sort cnt desc
```

### Find Specific Gateway Response Types

```
fields @timestamp, requestId, `error-responseType`, `error-message`, status
| filter ispresent(`error-responseType`)
| stats count(*) as cnt by `error-responseType`
| sort cnt desc
```

## Additional Monitoring Tools

- **CloudWatch Synthetics**: Canaries for synthetic monitoring of endpoints on schedule
- **CloudWatch Application Insights**: Automated dashboards for problem detection
- **CloudWatch Contributor Insights**: Find top talkers and contributors; pre-built sample rules for API Gateway
- **CloudWatch Dashboards**: Include dashboard definitions in IaC templates
- **CloudWatch ServiceLens**: Integrates traces, metrics, logs, alarms, resource health

## CloudWatch Embedded Metrics Format

- Include metric data in structured logs sent to CloudWatch Logs
- CloudWatch extracts metrics automatically (**cheaper than PutMetricData API**)
- Use for custom business metrics (e.g., orders per minute, revenue per endpoint)
- Include dashboard definitions in IaC templates with both operational and business metrics

## AI-Assisted Operations

- **CloudWatch AI Operations**: Specify a time window, it correlates logs across services and generates root cause hypothesis
- **Amazon Q CLI**: Natural language troubleshooting ("Why do I see increased 500 errors from API Gateway in this stack?")
- **CloudWatch Logs Insights**: Supports natural language to query translation and auto-generated pattern summaries

## API Analytics Pipeline

For deep analytics beyond CloudWatch dashboards:

1. Stream access logs via Amazon Data Firehose
2. Enrich with Lambda transformation (add business context, geo-IP lookup)
3. Store in S3 (partitioned by date/API/stage)
4. Query with Amazon Athena
5. Visualize with Amazon QuickSight

**Cost tip**: Firehose-to-S3 ingestion (~$0.029/GB) is significantly cheaper than CloudWatch Logs ingestion (~$0.50/GB). For high-volume APIs, stream access logs to Firehose instead of CloudWatch Logs and query with Athena. Use CloudWatch Logs for execution logs (lower volume) and real-time Logs Insights queries.

## Cross-Account and Centralized Logging

For multi-account AWS Organizations setups:

1. **CloudWatch cross-account observability**: Use Observability Access Manager (OAM) to share metrics, logs, and traces from source accounts to a central monitoring account. Enables unified dashboards and alarms across all API Gateways
2. **Subscription filters**: Stream access logs from each account to a central Kinesis Data Stream or Firehose in the monitoring account for aggregated analysis
3. **Consistent log group naming**: Use a standard naming convention across accounts (e.g., `/aws/apigateway/<account-alias>/<api-name>/access-logs`) to simplify cross-account queries and cost attribution

## CloudTrail

- Captures all API Gateway management calls as control plane events
- Does NOT log data plane events (actual API requests); use access logs for that
- Determines: request made, IP address, who made it, when
- Use for audit and compliance, not operational monitoring
- **Do not forget CloudTrail for control plane audit**: who changed API configuration and when
