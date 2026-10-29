---
name: "pagerduty"
displayName: "PagerDuty Incident Management"
description: "Manage incidents, on-call schedules, services, escalation policies, and alert routing in PagerDuty for incident response and operational reliability"
keywords: ["pagerduty", "pagerduty-incidents", "on-call", "escalation-policy", "incident-response", "pagerduty-schedule"]
author: "Community"
---

# PagerDuty Incident Management Power

## Overview

The PagerDuty Incident Management Power connects to PagerDuty's incident management platform for managing incidents, on-call schedules, services, escalation policies, and alert routing. Handle incident response directly from your IDE.

**Key capabilities:**
- **Incident Management**: Create, acknowledge, resolve, and escalate incidents
- **On-Call Schedules**: Query who's on-call, view schedules, and manage overrides
- **Service Management**: List services, check health, and manage integrations
- **Escalation Policies**: View and manage escalation chains
- **Alert Routing**: Understand how alerts flow to responders
- **Analytics**: Query incident metrics, MTTA, MTTR, and trends
- **Status Updates**: Post status updates and communicate during incidents

**Authentication**: Requires PagerDuty API key (v2 REST API token).

## Onboarding

### Prerequisites

1. **PagerDuty account** - Any PagerDuty plan with API access
2. **REST API v2 key** - Account-level or user-level API key
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace the placeholder in `mcp.json` with your PagerDuty API key
3. Test with: *"List active incidents"* or *"Who's on-call?"*

### MCP Config Placeholders

Before using this power, replace the following placeholder in `mcp.json`:

- **`YOUR_PAGERDUTY_API_KEY`**: Your PagerDuty REST API v2 key.
 - **How to get it:**
    1. Log in to PagerDuty
    2. Go to Integrations → API Access Keys
    3. Click "Create New API Key"
    4. Give it a description (e.g., "Kiro MCP")
    5. Copy the generated key
 - **Alternative (user token):** Go to My Profile → User Settings → Create API User Token

## Available Steering Files

- **steering/steering.md** - Incident response workflows, on-call patterns, and best practices

## Available MCP Servers

### pagerduty
**Package:** `@pagerduty/mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **list_incidents** - List incidents with filters
  - Optional: `statuses` (array) - triggered, acknowledged, resolved
  - Optional: `service_ids` (array) - Filter by service
  - Optional: `urgencies` (array) - high, low
  - Optional: `since` (string) - Start date (ISO 8601)
  - Optional: `until` (string) - End date (ISO 8601)
  - Optional: `sort_by` (string) - incident_number, created_at, resolved_at
  - Returns: Incidents with details and assignments

2. **get_incident** - Get incident details
  - Required: `id` (string) - Incident ID
  - Returns: Full incident with timeline, notes, and alerts

3. **create_incident** - Create a new incident
  - Required: `title` (string) - Incident title
  - Required: `service_id` (string) - Service to create incident on
  - Optional: `urgency` (string) - high, low
  - Optional: `body` (string) - Incident description
  - Optional: `escalation_policy_id` (string) - Override default escalation
  - Returns: Created incident details

4. **update_incident** - Update incident status
  - Required: `id` (string) - Incident ID
  - Optional: `status` (string) - acknowledged, resolved
  - Optional: `escalation_level` (number) - Escalate to level
  - Optional: `assignments` (array) - Reassign to users
  - Optional: `priority` (string) - Priority ID
  - Returns: Updated incident

5. **add_incident_note** - Add a note to an incident
  - Required: `id` (string) - Incident ID
  - Required: `content` (string) - Note content
  - Returns: Created note

6. **list_services** - List services
  - Optional: `query` (string) - Search filter
  - Optional: `team_ids` (array) - Filter by team
  - Returns: Services with status and integrations

7. **get_service** - Get service details
  - Required: `id` (string) - Service ID
  - Returns: Service with integrations, escalation policy, and dependencies

8. **list_on_calls** - List current on-call users
  - Optional: `schedule_ids` (array) - Filter by schedule
  - Optional: `escalation_policy_ids` (array) - Filter by policy
  - Optional: `since` (string) - Start time
  - Optional: `until` (string) - End time
  - Returns: On-call entries with users and schedules

9. **get_schedule** - Get schedule details
  - Required: `id` (string) - Schedule ID
  - Optional: `since` (string) - Start time
  - Optional: `until` (string) - End time
  - Returns: Schedule with layers and rendered entries

10. **list_escalation_policies** - List escalation policies
   - Optional: `query` (string) - Search filter
   - Returns: Policies with rules and targets

11. **get_escalation_policy** - Get escalation policy details
   - Required: `id` (string) - Policy ID
   - Returns: Full policy with escalation rules

12. **list_users** - List users
   - Optional: `query` (string) - Search filter
   - Optional: `team_ids` (array) - Filter by team
   - Returns: Users with contact methods and roles

13. **get_analytics** - Get incident analytics
   - Optional: `service_ids` (array) - Filter by service
   - Optional: `since` (string) - Start date
   - Optional: `until` (string) - End date
   - Returns: MTTA, MTTR, incident counts, and trends

14. **merge_incidents** - Merge incidents together
   - Required: `target_id` (string) - Target incident
   - Required: `source_ids` (array) - Incidents to merge into target
   - Returns: Merged incident

15. **run_response_play** - Run a response play
   - Required: `incident_id` (string) - Incident to run play on
   - Required: `response_play_id` (string) - Response play ID
   - Returns: Play execution result

## Tool Usage Examples

### Incident Management

**List active incidents:**
```javascript
usePower("pagerduty", "pagerduty", "list_incidents", {
  "statuses": ["triggered", "acknowledged"],
  "urgencies": ["high"]
})
```

**Create an incident:**
```javascript
usePower("pagerduty", "pagerduty", "create_incident", {
  "title": "Production database connection pool exhausted",
  "service_id": "PSERVICE1",
  "urgency": "high",
  "body": "Connection pool at 100% capacity. New requests failing with timeout errors. Affecting checkout and payment services."
})
```

**Acknowledge and add note:**
```javascript
usePower("pagerduty", "pagerduty", "update_incident", {
  "id": "PINC123",
  "status": "acknowledged"
})

usePower("pagerduty", "pagerduty", "add_incident_note", {
  "id": "PINC123",
  "content": "Investigating. Initial analysis shows connection leak in payment-service v2.3.1 deployed 30 minutes ago. Rolling back."
})
```

**Resolve an incident:**
```javascript
usePower("pagerduty", "pagerduty", "update_incident", {
  "id": "PINC123",
  "status": "resolved"
})
```

### On-Call Management

**Who's on-call now:**
```javascript
usePower("pagerduty", "pagerduty", "list_on_calls", {})
```

**On-call for specific schedule:**
```javascript
usePower("pagerduty", "pagerduty", "get_schedule", {
  "id": "PSCHED1",
  "since": "2024-01-15T00:00:00Z",
  "until": "2024-01-22T00:00:00Z"
})
```

### Service Health

**List all services:**
```javascript
usePower("pagerduty", "pagerduty", "list_services", {
  "query": "payment"
})
```

**Get service details:**
```javascript
usePower("pagerduty", "pagerduty", "get_service", {
  "id": "PSERVICE1"
})
```

### Analytics

**Incident metrics for last 30 days:**
```javascript
usePower("pagerduty", "pagerduty", "get_analytics", {
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-01-31T23:59:59Z",
  "service_ids": ["PSERVICE1", "PSERVICE2"]
})
```

## Combining Tools (Workflows)

### Workflow 1: Incident Response

```javascript
// Step 1: Check active incidents
const incidents = usePower("pagerduty", "pagerduty", "list_incidents", {
  "statuses": ["triggered", "acknowledged"],
  "urgencies": ["high"]
})

// Step 2: Get incident details
const incident = usePower("pagerduty", "pagerduty", "get_incident", {
  "id": incidents[0].id
})

// Step 3: Check who's on-call for the affected service
const onCall = usePower("pagerduty", "pagerduty", "list_on_calls", {
  "escalation_policy_ids": [incident.escalation_policy.id]
})

// Step 4: Acknowledge the incident
const updated = usePower("pagerduty", "pagerduty", "update_incident", {
  "id": incident.id,
  "status": "acknowledged"
})

// Step 5: Add investigation note
const note = usePower("pagerduty", "pagerduty", "add_incident_note", {
  "id": incident.id,
  "content": "Investigating. Checking application logs and metrics for root cause."
})

// Step 6: After resolution
const resolved = usePower("pagerduty", "pagerduty", "update_incident", {
  "id": incident.id,
  "status": "resolved"
})
```

### Workflow 2: Service Health Review

```javascript
// Step 1: List all services
const services = usePower("pagerduty", "pagerduty", "list_services", {})

// Step 2: Get analytics for each service
const analytics = usePower("pagerduty", "pagerduty", "get_analytics", {
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-01-31T23:59:59Z"
})

// Step 3: Check recent incidents for noisy services
const recentIncidents = usePower("pagerduty", "pagerduty", "list_incidents", {
  "service_ids": ["PNOISY_SERVICE"],
  "since": "2024-01-01T00:00:00Z"
})

// Step 4: Review escalation policies
const policies = usePower("pagerduty", "pagerduty", "list_escalation_policies", {})
```

### Workflow 3: Incident Deduplication

```javascript
// Step 1: Find related incidents
const incidents = usePower("pagerduty", "pagerduty", "list_incidents", {
  "statuses": ["triggered"],
  "service_ids": ["PSERVICE1"]
})

// Step 2: Identify duplicates (same root cause)
// Analyze titles and descriptions for similarity

// Step 3: Merge related incidents
const merged = usePower("pagerduty", "pagerduty", "merge_incidents", {
  "target_id": incidents[0].id,
  "source_ids": [incidents[1].id, incidents[2].id]
})

// Step 4: Add context note
const note = usePower("pagerduty", "pagerduty", "add_incident_note", {
  "id": incidents[0].id,
  "content": "Merged 3 related incidents. All caused by database connection pool exhaustion."
})
```

## Best Practices

### ✅ Do:
- **Acknowledge quickly** - Reduces MTTA and signals you're working on it
- **Add notes during investigation** - Creates timeline for postmortem
- **Use urgency levels** - High for customer-impacting, low for informational
- **Merge related incidents** - Reduces noise and focuses response
- **Check on-call before escalating** - Know who you're paging
- **Use analytics** - Track MTTA/MTTR trends for improvement
- **Resolve with notes** - Document what fixed the issue

### ❌ Don't:
- **Let incidents sit triggered** - Acknowledge or escalate promptly
- **Create incidents without context** - Always include description
- **Escalate without investigating** - Check if you can resolve first
- **Ignore low-urgency incidents** - They may indicate growing problems
- **Skip postmortem notes** - Future you will thank present you

## Configuration

**Authentication Required**: PagerDuty REST API v2 token

**Setup Steps:**

1. **Create an API Key:**
  - Go to PagerDuty → Integrations → API Access Keys
  - Create a new REST API Key (v2)
  - Or use a user token from My Profile → User Settings → API Access

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "pagerduty": {
         "command": "npx",
         "args": ["-y", "@pagerduty/mcp-server"],
         "env": {
           "PAGERDUTY_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

3. **For EU region:**
   ```json
   "env": {
     "PAGERDUTY_API_KEY": "your-api-key",
     "PAGERDUTY_API_URL": "https://api.eu.pagerduty.com"
   }
   ```

## Tips

1. **Check active incidents first** - Start every investigation with current state
2. **Use notes as a timeline** - Document findings as you investigate
3. **Merge duplicates** - Reduce noise by combining related incidents
4. **Review analytics monthly** - Track MTTA/MTTR improvements
5. **Know your on-call** - Check schedules before escalating
6. **Use urgency wisely** - Reserve high urgency for customer impact
7. **Add context to incidents** - Include affected services, error messages, links
8. **Resolve promptly** - Don't leave resolved incidents in acknowledged state
9. **Check escalation policies** - Understand the escalation chain
10. **Use response plays** - Automate common response patterns

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@pagerduty/mcp-server`
**Source:** PagerDuty
**License:** MIT-0
**Documentation:** https://developer.pagerduty.com/docs/
