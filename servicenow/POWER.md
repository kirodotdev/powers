---
name: "servicenow"
displayName: "ServiceNow ITSM"
description: "Manage incidents, change requests, problems, service catalog items, and CMDB in ServiceNow for IT service management and operations"
keywords: ["servicenow", "snow", "itsm", "cmdb", "service-now", "itil", "change-request"]
author: "Community"
---

# ServiceNow ITSM Power

## Overview

The ServiceNow ITSM Power connects to ServiceNow's IT Service Management platform for managing incidents, change requests, problems, service catalog items, and the CMDB. Handle ITSM workflows directly from your IDE.

**Key capabilities:**
- **Incident Management**: Create, update, resolve, and query incidents
- **Change Management**: Create and track change requests through approval workflows
- **Problem Management**: Track root causes and known errors
- **Service Catalog**: Browse and request catalog items
- **CMDB**: Query configuration items and relationships
- **Knowledge Base**: Search and retrieve knowledge articles
- **SLA Tracking**: Monitor SLA compliance and breaches
- **Workflow Automation**: Trigger and monitor workflows

**Authentication**: Requires ServiceNow instance URL and credentials (username/password or OAuth).

## Onboarding

### Prerequisites

1. **ServiceNow instance** - Any ServiceNow instance with REST API enabled
2. **Service account** - A user account with appropriate roles (itil, admin, or custom)
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your instance URL and credentials
3. Test with: *"Show my open incidents"* or *"Query high priority bugs"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_INSTANCE.service-now.com`**: Your ServiceNow instance URL.
 - **How to get it:** This is the URL you use to access ServiceNow (e.g., `https://mycompany.service-now.com`). Check with your ServiceNow administrator if unsure.

- **`YOUR_USERNAME`**: ServiceNow username for API access.
 - **How to get it:** Use a dedicated service account rather than a personal account. Ask your ServiceNow admin to create one with the `itil` role for ITSM operations.

- **`YOUR_PASSWORD`**: Password for the ServiceNow service account.
 - **How to get it:** Set by your ServiceNow administrator. For better security, consider using OAuth instead (see Configuration section below).

## Available Steering Files

- **steering/steering.md** - ITSM workflows, query syntax, and best practices for incident and change management

## Available MCP Servers

### servicenow
**Package:** `@servicenow/mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **query_table** - Query any ServiceNow table
  - Required: `table` (string) - Table name (e.g., incident, change_request)
  - Optional: `query` (string) - Encoded query string
  - Optional: `fields` (string) - Comma-separated field list
  - Optional: `limit` (number) - Max results (default: 10)
  - Optional: `order_by` (string) - Sort field
  - Optional: `order_direction` (string) - asc, desc
  - Returns: Records matching the query

2. **get_record** - Get a specific record
  - Required: `table` (string) - Table name
  - Required: `sys_id` (string) - Record sys_id
  - Optional: `fields` (string) - Fields to return
  - Returns: Full record details

3. **create_record** - Create a new record
  - Required: `table` (string) - Table name
  - Required: `data` (object) - Field values
  - Returns: Created record with sys_id

4. **update_record** - Update an existing record
  - Required: `table` (string) - Table name
  - Required: `sys_id` (string) - Record sys_id
  - Required: `data` (object) - Fields to update
  - Returns: Updated record

5. **search_knowledge** - Search knowledge base
  - Required: `query` (string) - Search text
  - Optional: `knowledge_base` (string) - KB sys_id
  - Optional: `limit` (number) - Max results
  - Returns: Knowledge articles

6. **get_catalog_items** - List service catalog items
  - Optional: `category` (string) - Category filter
  - Optional: `query` (string) - Search text
  - Returns: Catalog items with descriptions

7. **submit_catalog_request** - Submit a catalog request
  - Required: `item_sys_id` (string) - Catalog item sys_id
  - Required: `variables` (object) - Request variables
  - Returns: Request details

8. **get_cmdb_ci** - Get CMDB configuration item
  - Required: `sys_id` (string) - CI sys_id
  - Optional: `include_relations` (boolean) - Include relationships
  - Returns: CI details with relationships

9. **query_cmdb** - Query CMDB
  - Required: `class` (string) - CI class (e.g., cmdb_ci_server, cmdb_ci_app_server)
  - Optional: `query` (string) - Encoded query
  - Optional: `limit` (number) - Max results
  - Returns: Configuration items

10. **add_work_note** - Add a work note to a record
   - Required: `table` (string) - Table name
   - Required: `sys_id` (string) - Record sys_id
   - Required: `note` (string) - Work note content
   - Returns: Updated record

11. **get_user** - Get user details
   - Required: `identifier` (string) - Username, email, or sys_id
   - Returns: User record with groups and roles

12. **list_assignment_groups** - List assignment groups
   - Optional: `query` (string) - Search filter
   - Returns: Groups with members

## Tool Usage Examples

### Incident Management

**Query open incidents:**
```javascript
usePower("servicenow", "servicenow", "query_table", {
  "table": "incident",
  "query": "state!=7^priority<=2^assignment_group.name=Backend Team",
  "fields": "number,short_description,priority,state,assigned_to,sys_updated_on",
  "limit": 20,
  "order_by": "priority",
  "order_direction": "asc"
})
```

**Create an incident:**
```javascript
usePower("servicenow", "servicenow", "create_record", {
  "table": "incident",
  "data": {
    "short_description": "Production API returning 500 errors on /checkout endpoint",
    "description": "Starting at 14:30 UTC, the checkout API endpoint began returning HTTP 500 errors. Error rate is approximately 15%. Affecting customer purchases.",
    "urgency": "1",
    "impact": "2",
    "category": "Software",
    "subcategory": "Application",
    "assignment_group": "Backend Engineering",
    "caller_id": "admin"
  }
})
```

**Update incident state:**
```javascript
usePower("servicenow", "servicenow", "update_record", {
  "table": "incident",
  "sys_id": "abc123def456",
  "data": {
    "state": "2",
    "work_notes": "Investigating. Found connection pool exhaustion in payment-service logs."
  }
})
```

**Resolve an incident:**
```javascript
usePower("servicenow", "servicenow", "update_record", {
  "table": "incident",
  "sys_id": "abc123def456",
  "data": {
    "state": "6",
    "close_code": "Solved (Permanently)",
    "close_notes": "Root cause: Connection leak in payment-service v2.3.1. Rolled back to v2.3.0 and deployed fix in v2.3.2."
  }
})
```

### Change Management

**Create a change request:**
```javascript
usePower("servicenow", "servicenow", "create_record", {
  "table": "change_request",
  "data": {
    "short_description": "Deploy payment-service v2.3.2 with connection pool fix",
    "description": "Deploying fix for connection pool leak identified in INC0012345. Changes include: connection pool timeout configuration, connection validation on checkout, and monitoring alerts.",
    "type": "normal",
    "risk": "moderate",
    "impact": "2",
    "category": "Software",
    "assignment_group": "Backend Engineering",
    "start_date": "2024-01-20 06:00:00",
    "end_date": "2024-01-20 07:00:00",
    "implementation_plan": "1. Deploy to staging\\n2. Run integration tests\\n3. Deploy to production\\n4. Monitor for 30 minutes",
    "backout_plan": "Roll back to v2.3.0 using deployment pipeline",
    "test_plan": "Run connection pool stress tests in staging environment"
  }
})
```

**Query pending changes:**
```javascript
usePower("servicenow", "servicenow", "query_table", {
  "table": "change_request",
  "query": "state=assess^ORstate=authorize^assignment_group.name=Backend Engineering",
  "fields": "number,short_description,type,risk,state,start_date,end_date",
  "limit": 10
})
```

### CMDB Queries

**Find servers:**
```javascript
usePower("servicenow", "servicenow", "query_cmdb", {
  "class": "cmdb_ci_server",
  "query": "operational_status=1^environment=production",
  "limit": 20
})
```

**Get CI with relationships:**
```javascript
usePower("servicenow", "servicenow", "get_cmdb_ci", {
  "sys_id": "ci_sys_id_here",
  "include_relations": true
})
```

### Knowledge Base

**Search for solutions:**
```javascript
usePower("servicenow", "servicenow", "search_knowledge", {
  "query": "connection pool exhaustion troubleshooting",
  "limit": 5
})
```

## Combining Tools (Workflows)

### Workflow 1: Incident Response with CMDB

```javascript
// Step 1: Find the incident
const incidents = usePower("servicenow", "servicenow", "query_table", {
  "table": "incident",
  "query": "state=1^priority=1",
  "fields": "number,short_description,cmdb_ci,assignment_group",
  "limit": 5
})

// Step 2: Get the affected CI details
const ci = usePower("servicenow", "servicenow", "get_cmdb_ci", {
  "sys_id": incidents[0].cmdb_ci.value,
  "include_relations": true
})

// Step 3: Search knowledge base for known solutions
const articles = usePower("servicenow", "servicenow", "search_knowledge", {
  "query": incidents[0].short_description
})

// Step 4: Add work note with findings
const note = usePower("servicenow", "servicenow", "add_work_note", {
  "table": "incident",
  "sys_id": incidents[0].sys_id,
  "note": "Affected CI: " + ci.name + ". Found KB article with resolution steps. Applying fix."
})

// Step 5: Resolve the incident
const resolved = usePower("servicenow", "servicenow", "update_record", {
  "table": "incident",
  "sys_id": incidents[0].sys_id,
  "data": {
    "state": "6",
    "close_code": "Solved (Permanently)",
    "close_notes": "Applied fix from KB article. Verified service restored."
  }
})
```

### Workflow 2: Change Request Lifecycle

```javascript
// Step 1: Create change request
const change = usePower("servicenow", "servicenow", "create_record", {
  "table": "change_request",
  "data": {
    "short_description": "Upgrade database to PostgreSQL 16",
    "type": "normal",
    "risk": "high",
    "impact": "2",
    "assignment_group": "Database Team"
  }
})

// Step 2: Link to related incident
const link = usePower("servicenow", "servicenow", "update_record", {
  "table": "change_request",
  "sys_id": change.sys_id,
  "data": {
    "justification": "Required to resolve recurring connection issues (INC0012345)"
  }
})

// Step 3: Check approval status
const status = usePower("servicenow", "servicenow", "get_record", {
  "table": "change_request",
  "sys_id": change.sys_id,
  "fields": "number,state,approval,risk"
})

// Step 4: After implementation, close the change
const closed = usePower("servicenow", "servicenow", "update_record", {
  "table": "change_request",
  "sys_id": change.sys_id,
  "data": {
    "state": "3",
    "close_code": "successful",
    "close_notes": "Database upgraded successfully. All services verified operational."
  }
})
```

### Workflow 3: Problem Management

```javascript
// Step 1: Find recurring incidents
const incidents = usePower("servicenow", "servicenow", "query_table", {
  "table": "incident",
  "query": "short_descriptionLIKEconnection pool^state=7^sys_created_on>=javascript:gs.beginningOfLast30Days()",
  "fields": "number,short_description,cmdb_ci,resolved_at",
  "limit": 50
})

// Step 2: Create a problem record
const problem = usePower("servicenow", "servicenow", "create_record", {
  "table": "problem",
  "data": {
    "short_description": "Recurring connection pool exhaustion in payment-service",
    "description": "15 incidents in the last 30 days related to connection pool exhaustion. Root cause investigation needed.",
    "urgency": "2",
    "impact": "2",
    "assignment_group": "Backend Engineering",
    "category": "Software"
  }
})

// Step 3: Add root cause analysis
const rca = usePower("servicenow", "servicenow", "add_work_note", {
  "table": "problem",
  "sys_id": problem.sys_id,
  "note": "Root cause identified: Connection leak when database queries timeout. Fix: Add connection validation and timeout handling. Change request CHG0001234 created for the fix."
})
```

## Query Syntax Reference

### Encoded Query Format
ServiceNow uses encoded query strings with operators:

**Operators:**
- `=` - Equals
- `!=` - Not equals
- `LIKE` - Contains
- `STARTSWITH` - Starts with
- `ENDSWITH` - Ends with
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `IN` - In list (comma-separated)
- `ISEMPTY` - Field is empty
- `ISNOTEMPTY` - Field is not empty

**Logical operators:**
- `^` - AND
- `^OR` - OR
- `^NQ` - New query (OR group)

**Examples:**
```
# High priority open incidents
state!=7^priority<=2

# Incidents for specific group, created today
assignment_group.name=Backend Team^sys_created_on>=javascript:gs.beginningOfToday()

# Changes in assess or authorize state
state=assess^ORstate=authorize

# CIs in production that are operational
environment=production^operational_status=1

# Incidents containing "timeout" in description
short_descriptionLIKEtimeout^ORdescriptionLIKEtimeout
```

### Common Table Names
| Table | Description |
|-------|-------------|
| `incident` | Incidents |
| `change_request` | Change requests |
| `problem` | Problems |
| `sc_request` | Service catalog requests |
| `sc_req_item` | Requested items |
| `cmdb_ci` | Configuration items (base) |
| `cmdb_ci_server` | Servers |
| `cmdb_ci_app_server` | Application servers |
| `cmdb_ci_service` | Business services |
| `kb_knowledge` | Knowledge articles |
| `sys_user` | Users |
| `sys_user_group` | Groups |
| `task` | Tasks (parent of incident, change, etc.) |

### Incident States
| Value | State |
|-------|-------|
| 1 | New |
| 2 | In Progress |
| 3 | On Hold |
| 6 | Resolved |
| 7 | Closed |

### Change Request States
| Value | State |
|-------|-------|
| -5 | New |
| -4 | Assess |
| -3 | Authorize |
| -2 | Scheduled |
| -1 | Implement |
| 0 | Review |
| 3 | Closed |
| 4 | Cancelled |

## Best Practices

### ✅ Do:
- **Use encoded queries** for efficient filtering
- **Specify fields** to reduce response size
- **Link incidents to CIs** for impact analysis
- **Search knowledge base** before creating new incidents
- **Add work notes** to document investigation progress
- **Use proper close codes** when resolving incidents
- **Create change requests** for all production changes
- **Include implementation and backout plans** in changes

### ❌ Don't:
- **Query without filters** - Always use encoded query
- **Skip the CMDB** - Link incidents to affected CIs
- **Resolve without documentation** - Always add close notes
- **Create changes without plans** - Include implementation, test, and backout plans
- **Ignore SLA timers** - Monitor and respond before breach

## Configuration

**Authentication Required**: ServiceNow instance URL and credentials

**Setup Steps:**

1. **Get ServiceNow Credentials:**
  - Obtain your instance URL (e.g., `https://yourinstance.service-now.com`)
  - Create a service account or use existing credentials
  - Ensure the account has appropriate roles (itil, admin, or custom)

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "servicenow": {
         "command": "npx",
         "args": ["-y", "@servicenow/mcp-server"],
         "env": {
           "SERVICENOW_INSTANCE_URL": "https://yourinstance.service-now.com",
           "SERVICENOW_USERNAME": "your-username",
           "SERVICENOW_PASSWORD": "your-password"
         }
       }
     }
   }
   ```

3. **For OAuth authentication:**
   ```json
   "env": {
     "SERVICENOW_INSTANCE_URL": "https://yourinstance.service-now.com",
     "SERVICENOW_CLIENT_ID": "your-client-id",
     "SERVICENOW_CLIENT_SECRET": "your-client-secret"
   }
   ```

## Tips

1. **Use encoded queries** - More efficient than client-side filtering
2. **Specify fields** - Only request fields you need
3. **Search KB first** - Known solutions save time
4. **Link to CMDB** - Enables impact analysis and reporting
5. **Document everything** - Work notes create audit trail
6. **Use proper states** - Follow ITIL lifecycle
7. **Include plans in changes** - Implementation, test, and backout
8. **Monitor SLAs** - Respond before breach thresholds
9. **Create problems for patterns** - Recurring incidents need root cause analysis
10. **Use assignment groups** - Route to the right team

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@servicenow/mcp-server`
**Source:** ServiceNow
**License:** MIT-0
**Documentation:** https://docs.servicenow.com/
