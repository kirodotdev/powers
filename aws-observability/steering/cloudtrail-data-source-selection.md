# CloudTrail Data Source Selection Strategy

## Purpose
This is a utility guide referenced by `security-auditing.md` and other steering files for CloudTrail data access priority logic. It is not intended to be loaded directly in response to user queries. For CloudTrail security analysis, use `security-auditing.md` instead.

This steering file defines the priority order for accessing CloudTrail audit data across different AWS services. It ensures the agent always uses the most efficient and comprehensive data source available.

## Data Source Priority

When CloudTrail or security auditing data is needed, follow this priority order:

### Priority 1: CloudTrail Lake (Event Data Store)
**Check First**: Use CloudTrail MCP server to check for CloudTrail Lake event data stores

**Tool**: `list_event_data_stores` from CloudTrail MCP server

**When to Use**:
- Event data store exists with management events enabled
- Provides SQL-based querying with advanced filtering
- Best for complex queries and long-term retention
- Most cost-effective for large-scale analysis

**Advantages**:
- Native SQL support for complex queries
- 7-year retention by default
- Cross-account and cross-region aggregation
- Advanced filtering and partitioning
- Lower query costs for large datasets

**Example Check**:
```
Use CloudTrail MCP server's list_event_data_stores tool to check if any event data stores exist with:
- Status: ENABLED
- AdvancedEventSelectors configured for management events
```

### Priority 2: CloudWatch Logs (CloudTrail Integration)
**Check Second**: If no CloudTrail Lake event data store, check CloudWatch Logs

**Tool**: `describe_log_groups` from CloudWatch MCP server

**When to Use**:
- CloudTrail is configured to send events to CloudWatch Logs
- Log group exists with "cloudtrail" in the name
- Good for real-time analysis and alerting
- Integrates with CloudWatch Alarms

**Advantages**:
- Real-time event streaming
- CloudWatch Logs Insights query support
- Integration with CloudWatch Alarms and metrics
- Cross-service log correlation
- Familiar CloudWatch Logs interface

**Common Log Group Patterns**:
- `/aws/cloudtrail/logs`
- `/aws/cloudtrail/<trail-name>`
- `CloudTrail/logs`
- `<organization-name>-cloudtrail`
- Any log group with "cloudtrail" in the name

**Example Check**:
```
Use CloudWatch MCP server's describe_log_groups tool with:
- log_group_name_prefix: "/aws/cloudtrail" or search for "cloudtrail"
```

### Priority 3: CloudTrail Lookup Events API
**Fallback**: If neither CloudTrail Lake nor CloudWatch Logs available

**Tool**: `lookup_events` from CloudTrail MCP server

**When to Use**:
- No CloudTrail Lake event data store configured
- CloudTrail not sending to CloudWatch Logs
- Quick lookups for recent events (last 90 days)
- Simple queries without complex filtering

**Limitations**:
- Only last 90 days of events
- Limited to 50 results per API call
- Basic filtering capabilities
- Higher API costs for large queries
- No SQL support

**Advantages**:
- Always available if CloudTrail is enabled
- No additional configuration required
- Simple API for basic queries
- Good for quick investigations

**Example Usage**:
```
Use CloudTrail MCP server's lookup_events tool with:
- StartTime and EndTime for date range
- LookupAttributes for filtering (EventName, Username, ResourceName, etc.)
- MaxResults for pagination
```

## Implementation Workflow

### Step 1: Check CloudTrail Lake
```
1. Call list_event_data_stores from CloudTrail MCP server
2. Check if any event data stores exist with:
   - Status = ENABLED
   - Management events enabled in AdvancedEventSelectors
3. If found, use CloudTrail Lake for queries
   - Use lake_query for SQL-based analysis
   - Leverage advanced filtering and aggregation
```

### Step 2: Check CloudWatch Logs (if Step 1 fails)
```
1. Call describe_log_groups from CloudWatch MCP server
2. Search for log groups with "cloudtrail" in the name
3. If found, use CloudWatch Logs Insights
   - Use execute_log_insights_query for analysis
   - Leverage CloudWatch Logs query syntax
   - Set up alarms if needed
```

### Step 3: Use Lookup Events API (if Steps 1 and 2 fail)
```
1. Use lookup_events from CloudTrail MCP server
2. Apply basic filtering with LookupAttributes
3. Paginate through results if needed
4. Note: Limited to last 90 days and 50 results per call
```

## Decision Tree

```
Need CloudTrail Data?
    |
    v
Check CloudTrail Lake (list_event_data_stores)
    |
    +-- Event Data Store Enabled? --> YES --> Use CloudTrail Lake (lake_query)
    |
    +-- NO
        |
        v
    Check CloudWatch Logs (describe_log_groups)
        |
        +-- CloudTrail Log Group Exists? --> YES --> Use CloudWatch Logs (execute_log_insights_query)
        |
        +-- NO
            |
            v
        Use CloudTrail Lookup Events API (lookup_events)
            |
            v
        Limited to 90 days, basic filtering
```

## Query Translation Examples

### Example 1: Find IAM User Deletions

**CloudTrail Lake (SQL)**:
```sql
SELECT 
    eventTime,
    userIdentity.userName,
    requestParameters.userName AS deletedUser,
    sourceIPAddress
FROM <event_data_store_id>
WHERE eventName = 'DeleteUser'
    AND eventTime > timestamp '2024-01-01 00:00:00'
ORDER BY eventTime DESC
```

**CloudWatch Logs Insights**:
```
fields eventTime, userIdentity.userName, requestParameters.userName, sourceIPAddress
| filter eventName = "DeleteUser"
| filter @timestamp > "2024-01-01T00:00:00Z"
| sort eventTime desc
| limit 50
```

**Lookup Events API**:
```
lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'EventName',
            'AttributeValue': 'DeleteUser'
        }
    ],
    StartTime='2024-01-01T00:00:00Z',
    MaxResults=50
)
```

### Example 2: Track S3 Bucket Deletions

**CloudTrail Lake (SQL)**:
```sql
SELECT 
    eventTime,
    userIdentity.principalId,
    requestParameters.bucketName,
    sourceIPAddress,
    errorCode
FROM <event_data_store_id>
WHERE eventName = 'DeleteBucket'
    AND eventTime > timestamp '2024-01-01 00:00:00'
ORDER BY eventTime DESC
```

**CloudWatch Logs Insights**:
```
fields eventTime, userIdentity.principalId, requestParameters.bucketName, sourceIPAddress, errorCode
| filter eventName = "DeleteBucket"
| filter @timestamp > "2024-01-01T00:00:00Z"
| sort eventTime desc
| limit 50
```

**Lookup Events API**:
```
lookup_events(
    LookupAttributes=[
        {
            'AttributeKey': 'EventName',
            'AttributeValue': 'DeleteBucket'
        }
    ],
    StartTime='2024-01-01T00:00:00Z',
    MaxResults=50
)
```

## Best Practices

### 1. Always Check in Priority Order
- Start with CloudTrail Lake for best performance and cost
- Fall back to CloudWatch Logs for real-time analysis
- Use Lookup Events API only as last resort

### 2. Cache Data Source Discovery
- Once you've identified the available data source, remember it for the session
- Don't re-check on every query unless explicitly needed

### 3. Choose the Right Tool for the Job
- **Complex Analysis**: CloudTrail Lake (SQL support)
- **Real-time Alerting**: CloudWatch Logs (alarm integration)
- **Quick Lookups**: Lookup Events API (simple queries)

### 4. Consider Time Range
- **> 90 days**: Must use CloudTrail Lake or CloudWatch Logs
- **< 90 days**: All three options available
- **Real-time**: CloudWatch Logs preferred

### 5. Query Optimization
- **CloudTrail Lake**: Use SQL optimizations (WHERE clauses, partitioning)
- **CloudWatch Logs**: Use indexed fields, limit time ranges
- **Lookup Events**: Use specific LookupAttributes to reduce results

## Error Handling

### CloudTrail Lake Not Available
```
If list_event_data_stores returns empty or no enabled stores:
- Log: "CloudTrail Lake not configured, checking CloudWatch Logs"
- Proceed to Priority 2
```

### CloudWatch Logs Not Available
```
If describe_log_groups finds no CloudTrail log groups:
- Log: "CloudTrail not integrated with CloudWatch Logs, using Lookup Events API"
- Proceed to Priority 3
```

### Lookup Events API Limitations
```
If query requires:
- Data older than 90 days: Inform user CloudTrail Lake or CloudWatch Logs needed
- Complex filtering: Suggest enabling CloudTrail Lake
- Large result sets: Warn about pagination and API costs
```

## Migration Recommendations

If using Lookup Events API, recommend:

1. **Enable CloudTrail Lake** for:
   - Long-term retention (7 years)
   - Complex SQL queries
   - Cost-effective large-scale analysis
   - Cross-account aggregation

2. **Enable CloudWatch Logs Integration** for:
   - Real-time monitoring
   - CloudWatch Alarms
   - Log correlation with applications
   - Familiar CloudWatch interface

## Summary

This priority-based approach ensures:
- ✅ Most efficient data source is used first
- ✅ Graceful fallback to available alternatives
- ✅ Clear guidance for users on capabilities
- ✅ Cost optimization through appropriate tool selection
- ✅ Consistent behavior across all steering files

---

**Remember**: Always check data sources in priority order (CloudTrail Lake → CloudWatch Logs → Lookup Events API) to ensure optimal performance and cost efficiency.
