# ServiceNow ITSM Steering Guide

This steering file covers the ServiceNow MCP server to manage incidents, changes, problems, and CMDB queries.

## When to Use the ServiceNow MCP Server

Use ServiceNow MCP tools when you need to:
- **Manage incidents**: Create, update, resolve, and track IT incidents
- **Handle changes**: Create and track change requests through approval workflows
- **Investigate problems**: Track root causes and create known error records
- **Query CMDB**: Find configuration items and their relationships
- **Search knowledge**: Find existing solutions and documentation
- **Track SLAs**: Monitor compliance and approaching breaches

## Core Principles

### 1. Follow ITIL Lifecycle
Incidents, changes, and problems each have defined lifecycles. Follow the state transitions properly.

### 2. Always Link to CMDB
Every incident and change should reference the affected configuration item. This enables impact analysis and reporting.

### 3. Document as You Work
Add work notes at each step. This creates an audit trail and helps other team members.

---

## Encoded Query Syntax

### Basic Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `state=1` |
| `!=` | Not equals | `state!=7` |
| `LIKE` | Contains | `short_descriptionLIKEtimeout` |
| `STARTSWITH` | Starts with | `numberSTARTSWITHINC` |
| `ENDSWITH` | Ends with | `nameENDSWITHprod` |
| `>` | Greater than | `priority>2` |
| `<` | Less than | `priority<3` |
| `>=` | Greater or equal | `sys_created_on>=2024-01-01` |
| `<=` | Less or equal | `sys_updated_on<=2024-01-31` |
| `IN` | In list | `stateIN1,2,3` |
| `ISEMPTY` | Is empty | `assigned_toISEMPTY` |
| `ISNOTEMPTY` | Is not empty | `resolved_atISNOTEMPTY` |

### Logical Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `^` | AND | `state=1^priority=1` |
| `^OR` | OR | `state=1^ORstate=2` |
| `^NQ` | New query (OR group) | Complex grouping |

### Date/Time Functions

| Function | Meaning |
|----------|---------|
| `javascript:gs.beginningOfToday()` | Start of today |
| `javascript:gs.beginningOfYesterday()` | Start of yesterday |
| `javascript:gs.beginningOfLastWeek()` | Start of last week |
| `javascript:gs.beginningOfLast30Days()` | 30 days ago |
| `javascript:gs.daysAgo(7)` | 7 days ago |
| `javascript:gs.hoursAgo(4)` | 4 hours ago |
| `javascript:gs.minutesAgo(30)` | 30 minutes ago |

### Dot-Walking (Related Records)

Access fields on related records using dot notation:
```
# Incidents assigned to a specific group
assignment_group.name=Backend Engineering

# Incidents for a specific CI's business service
cmdb_ci.business_service.name=Payment Platform

# Changes owned by a specific user's manager
requested_by.manager.name=John Smith
```

---

## Common Query Patterns

### Incident Queries

**Open P1/P2 incidents:**
```
state!=7^priority<=2
```

**My assigned incidents:**
```
assigned_to=javascript:gs.getUserID()^state!=7
```

**Incidents created in last 4 hours:**
```
sys_created_on>=javascript:gs.hoursAgo(4)
```

**Unassigned incidents for my group:**
```
assignment_group.name=Backend Team^assigned_toISEMPTY^state=1
```

**Incidents with SLA breach risk:**
```
state!=7^sla_due<=javascript:gs.hoursAgo(-2)^sla_dueISNOTEMPTY
```

**Incidents related to a specific CI:**
```
cmdb_ci=CI_SYS_ID^state!=7
```

### Change Request Queries

**Pending approval changes:**
```
state=-3^assignment_group.name=Backend Engineering
```

**Changes scheduled for this week:**
```
start_date>=javascript:gs.beginningOfThisWeek()^start_date<=javascript:gs.endOfThisWeek()
```

**High-risk changes:**
```
risk=high^state!=-5^state!=4
```

**Emergency changes in last 7 days:**
```
type=emergency^sys_created_on>=javascript:gs.daysAgo(7)
```

### Problem Queries

**Open problems:**
```
state!=4^state!=7
```

**Problems with known errors:**
```
known_error=true^state!=4
```

**Problems linked to recurring incidents:**
```
related_incidents>3^state=2
```

### CMDB Queries

**Production servers:**
```
environment=production^operational_status=1
```

**Application servers for a service:**
```
business_service.name=Payment Platform^operational_status=1
```

**CIs with recent changes:**
```
sys_updated_on>=javascript:gs.daysAgo(7)^operational_status=1
```

---

## Incident Management Workflow

### Creating Effective Incidents

Include these fields:
- **short_description**: Clear, concise summary (what's broken)
- **description**: Detailed information (symptoms, impact, timeline)
- **urgency**: How quickly it needs resolution (1=High, 2=Medium, 3=Low)
- **impact**: How many users/services affected (1=High, 2=Medium, 3=Low)
- **category/subcategory**: Classification for routing and reporting
- **assignment_group**: Team responsible for resolution
- **cmdb_ci**: Affected configuration item

### Priority Matrix
Priority is calculated from Impact × Urgency:

| | Impact: High (1) | Impact: Medium (2) | Impact: Low (3) |
|---|---|---|---|
| **Urgency: High (1)** | P1 - Critical | P2 - High | P3 - Moderate |
| **Urgency: Medium (2)** | P2 - High | P3 - Moderate | P4 - Low |
| **Urgency: Low (3)** | P3 - Moderate | P4 - Low | P5 - Planning |

### State Transitions

```
New (1) → In Progress (2) → On Hold (3) → In Progress (2) → Resolved (6) → Closed (7)
                                                              ↑
New (1) → In Progress (2) ─────────────────────────────────────┘
```

---

## Change Management Workflow

### Change Types

| Type | Use When | Approval |
|------|----------|----------|
| Standard | Pre-approved, low-risk, routine | Auto-approved |
| Normal | Planned changes, needs review | CAB approval |
| Emergency | Urgent fix for P1/P2 incident | Expedited approval |

### Creating Effective Change Requests

Required information:
- **short_description**: What's being changed
- **description**: Detailed scope and rationale
- **type**: standard, normal, emergency
- **risk**: Assessment of risk level
- **impact**: Who/what is affected
- **implementation_plan**: Step-by-step procedure
- **backout_plan**: How to revert if it fails
- **test_plan**: How to verify success
- **start_date/end_date**: Maintenance window

### Change States

```
New (-5) → Assess (-4) → Authorize (-3) → Scheduled (-2) → Implement (-1) → Review (0) → Closed (3)
                                                                                            ↓
                                                                                      Cancelled (4)
```

---

## Problem Management Workflow

### When to Create a Problem

Create a problem record when:
- Same incident occurs 3+ times in 30 days
- Root cause is unknown for a significant incident
- A workaround exists but permanent fix is needed
- Pattern of related incidents across services

### Problem States

```
New (1) → Assess (2) → Root Cause Analysis (3) → Fix in Progress (4) → Resolved (5) → Closed (7)
                                                                                         ↓
                                                                                   Known Error (created)
```

---

## CMDB Best Practices

### CI Classes Hierarchy

```
cmdb_ci (base)
├── cmdb_ci_computer
│   ├── cmdb_ci_server
│   │   ├── cmdb_ci_win_server
│   │   └── cmdb_ci_linux_server
│   └── cmdb_ci_vm_instance
├── cmdb_ci_service
│   ├── cmdb_ci_service_auto
│   └── cmdb_ci_service_discovered
├── cmdb_ci_app_server
│   ├── cmdb_ci_app_server_java
│   └── cmdb_ci_app_server_nodejs
├── cmdb_ci_database
│   ├── cmdb_ci_db_mysql
│   └── cmdb_ci_db_postgresql
└── cmdb_ci_cloud_service_account
```

### Relationship Types
- **Runs on** - Application runs on server
- **Depends on** - Service depends on another service
- **Used by** - Infrastructure used by application
- **Hosted on** - VM hosted on hypervisor
- **Connected to** - Network connectivity

---

## Field Reference

### Incident Fields
| Field | Description | Values |
|-------|-------------|--------|
| state | Current state | 1-7 (see states above) |
| priority | Calculated priority | 1-5 |
| urgency | How quickly needed | 1=High, 2=Medium, 3=Low |
| impact | Scope of effect | 1=High, 2=Medium, 3=Low |
| category | Classification | Software, Hardware, Network, etc. |
| assignment_group | Responsible team | Group reference |
| assigned_to | Individual assignee | User reference |
| cmdb_ci | Affected CI | CI reference |
| caller_id | Who reported | User reference |
| close_code | Resolution type | Solved, Not Solved, etc. |

### Change Request Fields
| Field | Description | Values |
|-------|-------------|--------|
| type | Change type | standard, normal, emergency |
| risk | Risk level | high, moderate, low |
| state | Current state | -5 to 4 (see states above) |
| approval | Approval status | not yet requested, requested, approved, rejected |
| start_date | Planned start | DateTime |
| end_date | Planned end | DateTime |
| implementation_plan | Steps to implement | Text |
| backout_plan | Rollback procedure | Text |
| test_plan | Verification steps | Text |

---

## Troubleshooting

### Query Returns No Results
1. Check table name is correct
2. Verify field names (use sys_dictionary table to check)
3. Widen time range
4. Remove filters one at a time
5. Check if using correct field values (sys_id vs display value)

### Permission Denied
1. Verify account has required roles (itil, admin)
2. Check ACL rules on the table
3. Verify the record isn't restricted by domain separation
4. Check if the table requires elevated privileges

### Record Not Updating
1. Verify sys_id is correct
2. Check if record is in a read-only state
3. Verify field names match the table schema
4. Check for mandatory fields that are missing
5. Verify business rules aren't blocking the update

---

## Summary Checklist

For effective ServiceNow usage:
- ✅ Use encoded queries for efficient filtering
- ✅ Specify only needed fields to reduce response size
- ✅ Link incidents to CMDB configuration items
- ✅ Follow ITIL state transitions properly
- ✅ Add work notes to document progress
- ✅ Include implementation and backout plans in changes
- ✅ Search knowledge base before creating new incidents
- ✅ Use proper close codes when resolving
- ✅ Create problems for recurring incident patterns
- ✅ Use dot-walking for related record queries

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD`, or OAuth credentials in responses
- When referencing credentials, use placeholder names only
- Do not include credentials in work notes, descriptions, or any created content

### Data Sensitivity
- **Incident and change records may contain sensitive information** - customer data, internal URLs, infrastructure details, security vulnerabilities
- Do not reproduce full incident descriptions verbatim if they contain PII or security-sensitive details
- CMDB data reveals infrastructure topology - treat as sensitive; do not expose server names, IP addresses, or network architecture unless explicitly needed
- Knowledge base articles may contain internal procedures - summarize rather than reproduce in full
- Work notes may contain investigation details that reveal vulnerabilities - summarize patterns

### Operational Safety
- **Do not close or resolve incidents without explicit user confirmation** - premature closure can violate SLAs
- **Do not approve change requests** - approval workflows require authorized approvers
- **Do not modify CMDB records without explicit approval** - CMDB accuracy is critical for impact analysis
- **Do not create P1/Critical incidents without explicit user request** - this triggers major incident processes
- **Do not modify assignment groups or escalation** without understanding the organizational routing rules
- **Be cautious with state transitions** - some transitions are irreversible or trigger automated workflows

### Access Control
- Only access tables and records the configured credentials have permissions for
- Do not attempt to enumerate users, roles, or ACLs beyond what's needed
- If an operation returns 403 or "insufficient privileges", report the error without retrying
- Do not attempt to access `sys_security_acl`, `sys_user_has_role`, or other security tables
- Respect domain separation - do not attempt cross-domain queries
- Do not query `sys_audit` or `sys_journal_field` tables unless explicitly requested

## Anti-Hallucination Guardrails

### Query Accuracy
- **Only use valid encoded query operators** - valid operators: `=`, `!=`, `LIKE`, `STARTSWITH`, `ENDSWITH`, `>`, `<`, `>=`, `<=`, `IN`, `ISEMPTY`, `ISNOTEMPTY`, `BETWEEN`
- **Only use valid logical operators** - `^` (AND), `^OR` (OR), `^NQ` (new query)
- **Do not fabricate table names** - common valid tables: `incident`, `change_request`, `problem`, `sc_request`, `sc_req_item`, `cmdb_ci`, `cmdb_ci_server`, `kb_knowledge`, `sys_user`, `sys_user_group`, `task`
- **Do not fabricate field names** - if unsure, suggest querying with `fields=*` on a single record to discover available fields
- **Do not invent sys_id values** - always query first to find valid sys_ids
- **Do not assume state values** - incident states (1-7) differ from change states (-5 to 4); use the correct values for each table

### Result Interpretation
- **Never invent record details** - if you haven't queried a record, say "I need to look this up"
- **Do not assume record states** - always check current state before suggesting transitions
- **Do not assume SLA status** - query actual SLA data rather than guessing based on priority
- **If a query returns no results**, report that clearly and suggest broadening filters or checking field names
- **Do not fabricate sys_ids, record numbers, or timestamps**
- **Do not assume organizational structure** - assignment groups, categories, and area paths vary by organization

### Tool Capability Boundaries
- Do not claim ability to approve change requests or run workflows
- Do not claim ability to modify ACLs, business rules, or system properties
- Do not claim ability to manage users, roles, or groups
- Do not claim ability to configure SLA definitions or notification rules
- Clearly state when an action requires the user to perform it in the ServiceNow UI

## Operational Optimization Guardrails

### Query Performance
- **Always use encoded queries** - they're processed server-side and much faster than client-side filtering
- **Specify `fields` parameter** - only request fields you need; reduces response size significantly
- **Use `limit` parameter** - start with 10-20 results, increase only if needed
- **Use indexed fields for filtering** - `number`, `sys_id`, `state`, `priority`, `assignment_group` are typically indexed
- **Avoid `LIKE` on large text fields** - `descriptionLIKE` is expensive; use `short_descriptionLIKE` instead
- **Use dot-walking sparingly** - each dot-walked field requires a join; limit to 1-2 levels

### Rate Limiting
- **ServiceNow has API rate limits** - typically 10 requests/second per user; be mindful of call volume
- **Batch awareness** - plan queries to minimize round trips
- **Cache sys_ids** - once you have a record's sys_id, reuse it without re-querying
- **Avoid paginating through all records** - use specific filters to find what you need

### Request Efficiency
- **Use `order_by` and `limit`** together - get the most relevant records first
- **Combine related information** - use dot-walking to get related record fields in a single query rather than multiple queries
- **Use `sysparm_display_value=true`** awareness - display values are human-readable but require additional processing
- **Minimize work note additions** - each work note triggers notifications; batch updates when possible

## Cost Optimization Guardrails

### API Usage
- **Minimize API calls** - plan the workflow before executing
- **Avoid redundant queries** - if you already have record details, don't re-fetch
- **Use specific queries** - `number=INC0012345` is one record; `state!=7` could be thousands
- **Limit result sets** - always use `limit` parameter; default may return too many records

### License and Capacity Awareness
- **ServiceNow licenses are per-user** - API calls consume the same capacity as UI interactions
- **Large queries impact instance performance** - avoid unbounded queries on production instances
- **Attachment and journal queries are expensive** - only fetch when specifically needed
- **CMDB queries can be expensive** - CI tables can be very large; always filter by class and operational status

### Process Efficiency
- **Search knowledge base before creating incidents** - existing solutions save time and reduce ticket volume
- **Link incidents to problems** - reduces duplicate investigation effort
- **Use proper categorization** - correct routing on first assignment reduces reassignment overhead
- **Include sufficient detail in incidents** - reduces back-and-forth communication
- **Create change requests with complete plans** - reduces approval cycle time
