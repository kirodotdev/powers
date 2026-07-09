# CloudTrail Security Auditing Steering

## Purpose
This steering file provides guidance for accessing and analyzing CloudTrail audit data for security auditing, compliance monitoring, and governance analysis.

## Prerequisites and Data Source Selection

**IMPORTANT**: CloudTrail audit data can be accessed through multiple sources. Always follow the priority order defined in `cloudtrail-data-source-selection.md`:

### Priority 1: CloudTrail Lake (Preferred)
Check first for CloudTrail Lake event data stores using the CloudTrail MCP server:
- Use `list_event_data_stores` to check for enabled event data stores
- If available, use `lake_query` for SQL-based analysis
- Best for complex queries, long-term retention (7 years), and cost efficiency

### Priority 2: CloudWatch Logs (If CloudTrail Lake not available)
Check for CloudTrail integration with CloudWatch Logs:
- Use `describe_log_groups` to look for log groups containing "cloudtrail" in the name
- Common patterns: `/aws/cloudtrail/logs`, `/aws/cloudtrail/<trail-name>`, `CloudTrail/logs`
- Use `execute_log_insights_query` for CloudWatch Logs Insights analysis
- Good for real-time monitoring and CloudWatch Alarms integration

### Priority 3: CloudTrail Lookup Events API (Fallback)
If neither CloudTrail Lake nor CloudWatch Logs available:
- Use `lookup_events` from CloudTrail MCP server
- Limited to last 90 days of events
- Basic filtering with LookupAttributes
- Good for quick lookups but limited query capabilities

**See `cloudtrail-data-source-selection.md` for detailed decision tree and implementation workflow.**

## When to Load This Steering
Load this when the user needs to:
- Investigate security incidents
- Track API activity and resource changes
- Perform compliance audits
- Monitor IAM changes
- Detect unauthorized access attempts
- Generate audit reports
- Correlate security events with application logs

## CloudTrail Overview

CloudTrail provides governance, compliance, and audit capabilities by logging all API calls in your AWS account. When integrated with CloudWatch Logs, you can:

- **Real-time Analysis**: Query events as they arrive
- **CloudWatch Logs Insights**: Use powerful query syntax for complex analysis
- **Cross-Service Correlation**: Correlate CloudTrail events with application logs
- **Long-term Retention**: Configure retention policies in CloudWatch Logs
- **Multi-Region Support**: Capture events across all regions
- **Multi-Account Support**: Aggregate logs from organization

## Core Concepts

### Event Types

**1. Management Events**
- Control plane operations
- Resource creation, modification, deletion
- IAM changes
- Security group modifications
- Examples: CreateBucket, RunInstances, CreateUser

**2. Data Events**
- Data plane operations
- S3 object-level operations
- Lambda function invocations
- DynamoDB table operations
- Examples: GetObject, PutObject, Invoke

**3. Insights Events**
- Unusual API activity detected by ML
- Rate-based anomalies
- Error rate anomalies
- Requires CloudTrail Insights enabled

### Event Structure

CloudTrail events in CloudWatch Logs contain these key fields:

```json
{
  "eventTime": "2024-12-08T10:30:00Z",
  "eventName": "CreateBucket",
  "eventSource": "s3.amazonaws.com",
  "userIdentity": {
    "type": "IAMUser",
    "principalId": "AIDAI...",
    "arn": "arn:aws:iam::123456789012:user/alice",
    "userName": "alice"
  },
  "sourceIPAddress": "203.0.113.0",
  "userAgent": "aws-cli/2.0.0",
  "requestParameters": {
    "bucketName": "my-new-bucket"
  },
  "responseElements": {
    "location": "https://my-new-bucket.s3.amazonaws.com/"
  },
  "errorCode": null,
  "errorMessage": null
}
```

## Querying CloudTrail Data

### Using CloudTrail Lake (Priority 1)

When CloudTrail Lake event data store is available, use SQL-based queries:

**Tool**: `lake_query` from CloudTrail MCP server

**Example Query:**
```sql
SELECT 
    eventTime,
    eventName,
    userIdentity.userName,
    sourceIPAddress,
    requestParameters
FROM <event_data_store_id>
WHERE eventName IN ('DeleteBucket', 'TerminateInstances')
    AND eventTime > timestamp '2024-01-01 00:00:00'
ORDER BY eventTime DESC
LIMIT 50
```

**Advantages**:
- Full SQL support with JOINs, aggregations, and window functions
- 7-year retention by default
- Cross-account and cross-region queries
- Cost-effective for large-scale analysis
- Advanced filtering and partitioning

### Using CloudWatch Logs (Priority 2)

When CloudTrail is integrated with CloudWatch Logs:

**Tool**: `execute_log_insights_query` from CloudWatch MCP server

**Example Query:**
```
fields eventTime, eventName, userIdentity.userName, sourceIPAddress, requestParameters
| filter eventName = "DeleteBucket" or eventName = "TerminateInstances"
| sort eventTime desc
| limit 50
```

**Query Parameters:**
```
- log_group_names: ["/aws/cloudtrail/logs"]  # Or your CloudTrail log group name
- query_string: CloudWatch Logs Insights query (see above)
- start_time: ISO 8601 format (e.g., "2024-01-01T00:00:00Z")
- end_time: ISO 8601 format
- limit: 50 (or as needed)
```

**Advantages**:
- Real-time event streaming
- CloudWatch Alarms integration
- Cross-service log correlation
- Familiar CloudWatch interface

### Using Lookup Events API (Priority 3 - Fallback)

When neither CloudTrail Lake nor CloudWatch Logs available:

**Tool**: `lookup_events` from CloudTrail MCP server

**Example Usage:**
```
lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'EventName',
            'AttributeValue': 'DeleteBucket'
        }
    ],
    StartTime='2024-01-01T00:00:00Z',
    EndTime='2024-12-31T23:59:59Z',
    MaxResults=50
)
```

**Limitations**:
- Only last 90 days of events
- Limited to 50 results per API call
- Basic filtering capabilities
- No SQL or complex query support

#### Pattern 2: Security Incident Investigation
```
# 1. Identify suspicious activity (failed access attempts)
fields eventTime, eventName, userIdentity.userName, sourceIPAddress, errorCode, errorMessage
| filter errorCode = "AccessDenied" or errorCode = "UnauthorizedOperation"
| sort eventTime desc
| limit 100

# 2. Trace user activity
fields eventTime, eventName, requestParameters, responseElements
| filter userIdentity.userName = "suspect-user"
| sort eventTime desc
| limit 100

# 3. Check IAM changes before incident
fields eventTime, eventName, userIdentity.userName, requestParameters
| filter eventSource = "iam.amazonaws.com"
| filter eventName like /Create|Delete|Update|Attach|Detach/
| sort eventTime desc
| limit 50
```


#### Pattern 3: Compliance Audit
```
# 1. List all IAM changes
fields eventTime, eventName, userIdentity.userName, userIdentity.principalId, requestParameters
| filter eventSource = "iam.amazonaws.com"
| filter eventName like /Create|Delete|Update|Attach|Detach/
| sort eventTime desc
| limit 100

# 2. Track privileged actions
fields eventTime, eventName, userIdentity.userName, userIdentity.sessionContext.sessionIssuer.userName, requestParameters
| filter eventName = "AssumeRole" or eventName = "GetFederationToken"
| sort eventTime desc
| limit 100

# 3. Review resource deletions
fields eventTime, eventName, userIdentity.userName, requestParameters, responseElements
| filter eventName like /Delete|Terminate/
| sort eventTime desc
| limit 100
```

#### Pattern 4: Resource Change Tracking
```
# 1. Find specific resource changes (replace with actual resource ARN)
fields eventTime, eventName, userIdentity.userName, requestParameters, responseElements
| filter requestParameters like /arn:aws:s3:::my-bucket/
| sort eventTime desc
| limit 50

# 2. Track configuration changes for a service
fields eventTime, eventName, userIdentity.userName, requestParameters
| filter eventSource = "ec2.amazonaws.com"
| filter eventName like /Update|Modify|Put/
| sort eventTime desc
| limit 100
```

## Security Monitoring Use Cases

### Use Case 1: Unauthorized Access Detection

**Indicators**:
- Failed authentication attempts
- Access from unusual IP addresses
- Access outside business hours
- Privilege escalation attempts

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, userIdentity.userName, sourceIPAddress, errorCode, errorMessage
| filter (eventName = "ConsoleLogin" or eventName = "AssumeRole")
| filter errorCode like /AccessDenied|AuthFailure|UnauthorizedOperation/
| stats count() as failedAttempts by userIdentity.userName, sourceIPAddress
| sort failedAttempts desc
| limit 50
```

### Use Case 2: IAM Changes Audit

**Monitor for**:
- User/role creation and deletion
- Policy modifications
- Permission boundary changes
- Access key creation
- MFA changes

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, userIdentity.userName as actor, requestParameters.userName as targetUser, requestParameters.policyName as policyName, sourceIPAddress
| filter eventSource = "iam.amazonaws.com"
| filter eventName in ["CreateUser", "DeleteUser", "CreateRole", "DeleteRole", "PutUserPolicy", "PutRolePolicy", "AttachUserPolicy", "AttachRolePolicy", "CreateAccessKey", "DeactivateMFADevice"]
| sort eventTime desc
| limit 100
```

**Aggregated IAM Changes**:
```
fields eventName, userIdentity.userName as actor
| filter eventSource = "iam.amazonaws.com"
| stats count() as changeCount by eventName, actor
| sort changeCount desc
| limit 50
```

### Use Case 3: Resource Deletion Tracking

**Monitor deletions of**:
- S3 buckets
- EC2 instances
- RDS databases
- Lambda functions
- DynamoDB tables

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, userIdentity.userName, requestParameters, sourceIPAddress
| filter eventName like /Delete|Terminate/
| sort eventTime desc
| limit 100
```

**Deletion Summary by Service**:
```
fields eventSource, eventName
| filter eventName like /Delete|Terminate/
| stats count() as deletionCount by eventSource, eventName
| sort deletionCount desc
| limit 50
```

### Use Case 4: Security Group Changes

**Monitor**:
- New security group rules
- Overly permissive rules (0.0.0.0/0)
- Rule deletions

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, userIdentity.userName as user, requestParameters.groupId as securityGroupId, requestParameters, sourceIPAddress
| filter eventSource = "ec2.amazonaws.com"
| filter eventName in ["AuthorizeSecurityGroupIngress", "AuthorizeSecurityGroupEgress", "RevokeSecurityGroupIngress", "RevokeSecurityGroupEgress"]
| sort eventTime desc
| limit 100
```

**Check for Overly Permissive Rules**:
```
fields eventTime, eventName, userIdentity.userName, requestParameters
| filter eventName = "AuthorizeSecurityGroupIngress"
| filter requestParameters like /0.0.0.0\/0/
| sort eventTime desc
| limit 50
```

### Use Case 5: Root Account Activity

**Critical to Monitor**:
- Root account usage should be rare
- MFA should always be used
- All root actions should be justified

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, eventSource, userIdentity.type as userType, sourceIPAddress, userIdentity.sessionContext.attributes.mfaAuthenticated as mfaUsed
| filter userIdentity.type = "Root"
| sort eventTime desc
| limit 100
```

**Root Account Activity Summary**:
```
fields eventName, eventSource
| filter userIdentity.type = "Root"
| stats count() as actionCount by eventName, eventSource
| sort actionCount desc
| limit 50
```

### Use Case 6: Cross-Account Access

**Monitor**:
- AssumeRole calls from external accounts
- Cross-account resource access
- Federated user activity

**CloudWatch Logs Insights Query**:
```
fields eventTime, eventName, userIdentity.principalId, userIdentity.accountId, recipientAccountId, requestParameters, sourceIPAddress
| filter eventName = "AssumeRole"
| filter userIdentity.accountId != recipientAccountId
| sort eventTime desc
| limit 100
```

**AssumeRole Activity Summary**:
```
fields userIdentity.accountId as sourceAccount, recipientAccountId as targetAccount, requestParameters.roleArn
| filter eventName = "AssumeRole"
| stats count() as assumeCount by sourceAccount, targetAccount, requestParameters.roleArn
| sort assumeCount desc
| limit 50
```


## Incident Investigation Workflows

### Workflow 1: Suspicious IAM Activity

**Scenario**: Alert for unusual IAM activity

**Investigation Steps**:

1. **Identify the event**:
   ```
   fields eventTime, eventName, userIdentity.userName, requestParameters, sourceIPAddress
   | filter eventSource = "iam.amazonaws.com"
   | sort eventTime desc
   | limit 100
   ```

2. **Trace user activity**:
   ```
   # Trace all activity for suspect user
   fields eventTime, eventName, eventSource, sourceIPAddress, userAgent
   | filter userIdentity.userName = "suspect-user"
   | sort eventTime asc
   | limit 500
   ```

3. **Check for privilege escalation**:
   ```
   # Check for privilege escalation attempts
   fields eventTime, eventName, requestParameters.policyDocument as policy, requestParameters
   | filter userIdentity.userName = "suspect-user"
   | filter eventName in ["CreatePolicy", "AttachUserPolicy", "PutUserPolicy", "AttachRolePolicy", "PutRolePolicy"]
   | sort eventTime asc
   | limit 100
   ```

4. **Identify affected resources**:
   ```
   # Find resources accessed by suspect user
   fields eventName, eventSource, requestParameters
   | filter userIdentity.userName = "suspect-user"
   | stats count() as accessCount by eventName, eventSource
   | sort accessCount desc
   | limit 100
   ```

5. **Check access key usage**:
   ```
   fields eventTime, eventName, requestParameters.userName as targetUser, requestParameters.accessKeyId
   | filter eventName = "CreateAccessKey"
   | filter userIdentity.userName = "suspect-user" or requestParameters.userName = "suspect-user"
   | sort eventTime desc
   | limit 50
   ```

### Workflow 2: Resource Deletion Investigation

**Scenario**: Critical resource was deleted

**Investigation Steps**:

1. **Find the deletion event**:
   ```
   fields eventTime, eventName, userIdentity.userName, requestParameters, sourceIPAddress
   | filter eventName like /Delete|Terminate/
   | sort eventTime desc
   | limit 100
   ```

2. **Identify who deleted it**:
   ```
   fields eventTime, userIdentity.userName, userIdentity.principalId, userIdentity.arn, sourceIPAddress, userAgent
   | filter eventName = "DeleteBucket"  # Replace with actual deletion event
   | filter requestParameters.bucketName = "my-critical-bucket"  # Replace with actual resource
   | sort eventTime desc
   | limit 10
   ```

3. **Check user's recent activity**:
   ```
   fields eventTime, eventName, eventSource, sourceIPAddress
   | filter userIdentity.userName = "user-who-deleted"
   | filter eventName in ["ConsoleLogin", "GetSessionToken", "AssumeRole"]
   | sort eventTime desc
   | limit 10
   ```

4. **Check for automation**:
   ```
   fields eventTime, userAgent, sourceIPAddress
   | filter userIdentity.userName = "user-who-deleted"
   | stats count() as eventCount by userAgent
   | sort eventCount desc
   ```
   Look at userAgent field:
   - `aws-cli/*` indicates CLI usage
   - `Boto3/*` indicates Python SDK usage
   - `aws-sdk-*` indicates SDK usage
   - Check if expected for this user

### Workflow 3: Compliance Audit

**Scenario**: Quarterly compliance audit

**Audit Tasks**:

1. **IAM User Audit**:
   ```
   # List all users created in the audit period
   fields eventTime, eventName, userIdentity.userName as creator, requestParameters.userName as newUser
   | filter eventName = "CreateUser"
   | sort eventTime asc
   | limit 500
   ```

2. **Access Key Rotation**:
   ```
   # Find access keys created in the audit period
   fields eventTime, requestParameters.userName as user, responseElements.accessKey.accessKeyId as keyId
   | filter eventName = "CreateAccessKey"
   | sort eventTime asc
   | limit 500
   ```

3. **Policy Changes**:
   ```
   # Track policy modifications
   fields eventTime, eventName, userIdentity.userName as actor, requestParameters.policyName as policy
   | filter eventName in ["CreatePolicy", "CreatePolicyVersion", "DeletePolicy", "DeletePolicyVersion"]
   | sort eventTime asc
   | limit 500
   ```

4. **Encryption Changes**:
   ```
   # Track KMS key operations
   fields eventTime, eventName, userIdentity.userName as user, requestParameters.keyId as keyId
   | filter eventSource = "kms.amazonaws.com"
   | filter eventName in ["CreateKey", "ScheduleKeyDeletion", "DisableKey", "EnableKeyRotation"]
   | sort eventTime asc
   | limit 500
   ```

## Security Alerting Patterns

### Critical Alerts

**1. Root Account Usage**
```
# Alert: Root account activity
fields eventTime, eventName, sourceIPAddress, userIdentity.sessionContext.attributes.mfaAuthenticated as mfaUsed
| filter userIdentity.type = "Root"
| sort eventTime desc
| limit 50
```
**Action**: Page security team immediately

**2. IAM Policy Modifications**
```
# Alert: IAM policy modifications
fields eventTime, eventName, userIdentity.userName as user, requestParameters.policyDocument as policy, requestParameters
| filter eventName in ["PutUserPolicy", "PutRolePolicy", "AttachUserPolicy", "AttachRolePolicy"]
| sort eventTime desc
| limit 50
```
**Action**: Review policy changes, alert if suspicious

**3. Security Group Opening to Internet**
```
# Alert: Security group opened to 0.0.0.0/0
fields eventTime, userIdentity.userName as user, requestParameters
| filter eventName = "AuthorizeSecurityGroupIngress"
| filter requestParameters like /0.0.0.0\/0/
| sort eventTime desc
| limit 50
```
**Action**: Verify business justification

**4. KMS Key Deletion Scheduled**
```
# Alert: KMS key scheduled for deletion
fields eventTime, userIdentity.userName as user, requestParameters.keyId as keyId
| filter eventName = "ScheduleKeyDeletion"
| sort eventTime desc
| limit 50
```
**Action**: Confirm key is no longer needed

## Cross-Service Correlation

### Correlate CloudTrail with Application Logs

One of the key advantages of using CloudWatch Logs for CloudTrail is the ability to correlate security events with application behavior. While CloudWatch Logs Insights doesn't support JOINs across log groups in a single query, you can:

1. **Query CloudTrail for security events**
2. **Extract timestamps and user information**
3. **Query application logs for the same time period**
4. **Correlate results manually or programmatically**

**Example Workflow**:
```
# Step 1: Find IAM policy changes
fields eventTime, eventName, userIdentity.userName, requestParameters
| filter eventSource = "iam.amazonaws.com"
| filter eventName like /Policy/
| sort eventTime desc
| limit 50

# Step 2: Use the timestamps from above to query application logs
# Query application logs for errors after the policy change time
fields @timestamp, level, message
| filter level = "ERROR"
| filter @timestamp > "2024-01-01T10:00:00Z"  # Use timestamp from Step 1
| sort @timestamp desc
| limit 100
```

## Best Practices

### 1. Trail Configuration
- Enable CloudTrail in all regions
- Enable for all accounts (AWS Organizations)
- Enable log file validation
- **Configure CloudTrail to send events to CloudWatch Logs**
- Set up S3 lifecycle policies for cost optimization

### 2. Monitoring
- Set up CloudWatch Alarms for critical events
- Create metric filters for suspicious patterns
- Regular review of CloudTrail Insights
- Automate response to known threats
- Use CloudWatch Logs Insights for real-time analysis

### 3. Analysis
- Use CloudWatch Logs Insights for complex queries
- Correlate CloudTrail with application logs using time-based analysis
- Build CloudWatch Dashboards for security metrics
- Regular audit log reviews with saved queries

### 4. Retention
- Configure CloudWatch Logs retention for CloudTrail log groups
- Keep CloudTrail logs for required compliance period
- Consider separate retention for security events
- Archive to S3/Glacier for cost optimization
- Ensure immutability (S3 Object Lock for S3 archives)

### 5. Access Control
- Restrict access to CloudTrail log groups
- Use IAM policies to control CloudWatch Logs access
- Enable CloudWatch Logs encryption
- Monitor access to CloudTrail logs using CloudTrail itself

## Integration with Other Observability Tools

### CloudWatch Logs Insights
CloudTrail events in CloudWatch Logs enable:
- Real-time alerting with CloudWatch Alarms
- Complex queries for security analysis
- Time-based correlation with application logs
- Dashboard visualization with CloudWatch Dashboards

### Application Signals
Correlate CloudTrail security events with Application Signals service health:
- Track deployments that caused security policy changes
- Correlate IAM changes with service performance degradation
- Identify security events during SLO breaches

### AWS Security Hub
```
Security Hub integrates with CloudTrail for:
- Centralized security findings
- Compliance standard mapping
- Multi-account aggregation
- Automated remediation
```

### GuardDuty
```
GuardDuty uses CloudTrail for:
- Threat detection
- Unusual API activity
- Compromised credentials
- Cryptocurrency mining
```

## Quick Reference

### Common Event Names
- **IAM**: CreateUser, DeleteUser, AttachUserPolicy, CreateAccessKey
- **EC2**: RunInstances, TerminateInstances, AuthorizeSecurityGroupIngress
- **S3**: CreateBucket, DeleteBucket, PutBucketPolicy
- **RDS**: CreateDBInstance, DeleteDBInstance, ModifyDBInstance
- **Lambda**: CreateFunction, DeleteFunction, UpdateFunctionCode

### User Identity Types
- **IAMUser**: Standard IAM user
- **AssumedRole**: Assumed role via STS
- **Root**: Root account
- **FederatedUser**: Federated identity
- **AWSService**: AWS service acting on your behalf

### Error Codes
- **AccessDenied**: Permission denied
- **UnauthorizedOperation**: Not authorized for operation
- **InvalidParameter**: Invalid request parameter
- **ResourceNotFound**: Resource doesn't exist

### Common CloudWatch Logs Insights Filters

```
# Filter by event source
| filter eventSource = "iam.amazonaws.com"

# Filter by event name pattern
| filter eventName like /Delete|Terminate/

# Filter by user
| filter userIdentity.userName = "specific-user"

# Filter by error codes
| filter errorCode in ["AccessDenied", "UnauthorizedOperation"]

# Filter by IP address
| filter sourceIPAddress = "203.0.113.0"

# Filter by time range (in query, not tool parameters)
| filter eventTime > "2024-01-01T00:00:00Z"
```

---

**Remember**: CloudTrail security auditing via CloudWatch Logs provides real-time analysis and time-based correlation with application logs. Always correlate CloudTrail events with application logs and metrics for complete visibility. Configure CloudTrail → CloudWatch Logs integration first to enable these capabilities.
