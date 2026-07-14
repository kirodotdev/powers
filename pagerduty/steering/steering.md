# PagerDuty MCP Server Steering Guide

This steering file covers the PagerDuty MCP server to manage incidents, on-call schedules, services, and incident response workflows.

## When to Use the PagerDuty MCP Server

Use PagerDuty MCP tools when you need to:
- **Respond to incidents**: Acknowledge, investigate, escalate, or resolve incidents
- **Check on-call**: Find who's currently on-call for a service or schedule
- **Manage services**: Review service health, integrations, and dependencies
- **Track metrics**: Analyze MTTA, MTTR, and incident frequency trends
- **Coordinate response**: Add notes, merge incidents, run response plays
- **Review escalation**: Understand escalation chains and routing rules

## Core Principles

### 1. Acknowledge First, Investigate Second
When an incident is triggered, acknowledge it immediately to signal you're responding. Then investigate.

### 2. Document as You Go
Add notes to incidents during investigation. This creates a timeline for postmortems and helps other responders.

### 3. Merge Related Incidents
Multiple alerts from the same root cause should be merged into a single incident to reduce noise and focus response.

---

## Incident Lifecycle

### States
1. **Triggered** - New incident, awaiting response
2. **Acknowledged** - Responder is investigating
3. **Resolved** - Issue is fixed

### Urgency Levels
- **High** - Customer-impacting, pages immediately, follows escalation policy
- **Low** - Informational, may not page, lower priority

### Priority Levels (if configured)
- P1 - Critical (service down, data loss)
- P2 - High (degraded service, partial outage)
- P3 - Medium (non-critical feature affected)
- P4 - Low (cosmetic, minor impact)
- P5 - Informational (no customer impact)

---

## Incident Response Workflow

### Phase 1: Detection & Triage

```javascript
// Check what's firing
const incidents = list_incidents({
  "statuses": ["triggered"],
  "urgencies": ["high"]
})

// Get details on the most critical
const incident = get_incident({ "id": incidents[0].id })

// Check the affected service
const service = get_service({ "id": incident.service.id })
```

### Phase 2: Response

```javascript
// Acknowledge to stop escalation
update_incident({ "id": incident.id, "status": "acknowledged" })

// Document initial findings
add_incident_note({
  "id": incident.id,
  "content": "Investigating. Error rate spike in checkout-service. Checking recent deployments and dependencies."
})

// If you need help, check who else is on-call
const onCall = list_on_calls({
  "escalation_policy_ids": [service.escalation_policy.id]
})
```

### Phase 3: Escalation (if needed)

```javascript
// Escalate to next level
update_incident({
  "id": incident.id,
  "escalation_level": 2
})

// Or reassign to specific person
update_incident({
  "id": incident.id,
  "assignments": [{"assignee": {"id": "PUSER123", "type": "user_reference"}}]
})

// Add context for the next responder
add_incident_note({
  "id": incident.id,
  "content": "Escalating. Root cause appears to be database connection pool exhaustion. Need DBA assistance. Relevant dashboard: https://grafana.example.com/d/db-pool"
})
```

### Phase 4: Resolution

```javascript
// Document the fix
add_incident_note({
  "id": incident.id,
  "content": "Root cause: Connection leak in payment-service v2.3.1. Fix: Rolled back to v2.3.0. Connection pool recovered within 5 minutes. Will deploy fix in v2.3.2."
})

// Resolve the incident
update_incident({ "id": incident.id, "status": "resolved" })
```

---

## On-Call Management

### Finding Who's On-Call

**Current on-call for all schedules:**
```javascript
list_on_calls({})
```

**On-call for specific escalation policy:**
```javascript
list_on_calls({
  "escalation_policy_ids": ["PPOLICY1"]
})
```

**On-call for a specific time range (planning):**
```javascript
list_on_calls({
  "since": "2024-01-22T00:00:00Z",
  "until": "2024-01-29T00:00:00Z"
})
```

### Schedule Details

**View schedule with rendered entries:**
```javascript
get_schedule({
  "id": "PSCHED1",
  "since": "2024-01-15T00:00:00Z",
  "until": "2024-01-22T00:00:00Z"
})
```

---

## Service Health Analysis

### Quick Health Check

```javascript
// List all services
const services = list_services({})

// Check incidents per service in last 7 days
const incidents = list_incidents({
  "since": "2024-01-08T00:00:00Z",
  "until": "2024-01-15T00:00:00Z"
})

// Get analytics for trending
const analytics = get_analytics({
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-01-31T23:59:59Z"
})
```

### Identifying Noisy Services

Look for services with:
- High incident count relative to others
- Many auto-resolved incidents (flapping)
- Low MTTA (incidents not being acknowledged)
- Repeated similar incidents (needs automation)

---

## Analytics & Metrics

### Key Metrics

- **MTTA** (Mean Time to Acknowledge) - How quickly incidents are acknowledged
- **MTTR** (Mean Time to Resolve) - How quickly incidents are resolved
- **Incident Count** - Total incidents in period
- **Escalation Rate** - Percentage of incidents that escalate

### Querying Analytics

**Monthly service report:**
```javascript
get_analytics({
  "service_ids": ["PSERVICE1", "PSERVICE2"],
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-01-31T23:59:59Z"
})
```

**Compare periods for improvement:**
```javascript
// This month
const current = get_analytics({
  "since": "2024-02-01T00:00:00Z",
  "until": "2024-02-29T23:59:59Z"
})

// Last month
const previous = get_analytics({
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-01-31T23:59:59Z"
})
```

---

## Incident Note Best Practices

### What to Include in Notes

**Initial triage:**
```
Investigating. Symptoms: [what's broken]. Impact: [who's affected].
Checking: [what you're looking at next].
```

**Progress updates:**
```
Update: Found [root cause indicator]. [Action taken].
Next steps: [what you're doing next].
```

**Escalation context:**
```
Escalating to [team/person]. Need [specific expertise].
Current findings: [summary]. Relevant links: [dashboards, logs, docs].
```

**Resolution:**
```
Resolved. Root cause: [what broke and why].
Fix: [what was done]. Prevention: [follow-up actions].
Duration: [how long customers were impacted].
```

---

## Common Patterns

### Incident Deduplication
When multiple alerts fire for the same root cause:
1. Identify the primary incident (first triggered, most descriptive)
2. Merge related incidents into the primary
3. Add a note explaining the merge

### Scheduled Maintenance
Before planned maintenance:
1. Create a low-urgency incident documenting the maintenance
2. Add notes with the maintenance plan
3. Suppress alerts for affected services during the window
4. Resolve when maintenance is complete

### Postmortem Preparation
After resolving a significant incident:
1. Review the incident timeline (notes, acknowledgments, escalations)
2. Note MTTA and MTTR
3. Identify what went well and what could improve
4. Document action items for prevention

---

## Troubleshooting

### Incident Not Routing Correctly
1. Check the service's escalation policy
2. Verify on-call schedule has coverage for current time
3. Check if the service has the correct integration
4. Verify urgency rules on the service

### On-Call Shows No One
1. Check schedule has entries for the current time
2. Verify schedule layers don't have gaps
3. Check if overrides are in place
4. Verify user accounts are active

### Analytics Showing Unexpected Numbers
1. Verify time range includes the expected incidents
2. Check if incidents were merged (reduces count)
3. Verify service_ids filter is correct
4. Check if incidents were created via API vs integration

---

## Summary Checklist

For effective incident management:
- ✅ Acknowledge incidents promptly (reduces MTTA)
- ✅ Add notes during investigation (creates timeline)
- ✅ Include context when escalating (helps next responder)
- ✅ Merge related incidents (reduces noise)
- ✅ Document resolution (enables postmortems)
- ✅ Review analytics monthly (track improvements)
- ✅ Check on-call before escalating (know who you're paging)
- ✅ Use appropriate urgency (reserve high for customer impact)
- ✅ Resolve incidents when fixed (don't leave in acknowledged)

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `PAGERDUTY_API_KEY` values in responses
- When referencing API keys, use placeholder names only
- Do not include API keys in incident notes, descriptions, or any created content

### Incident Data Sensitivity
- **Incident details may contain sensitive information** - customer names, internal URLs, infrastructure details
- Do not reproduce full incident timelines verbatim if they contain PII or security-sensitive details
- When summarizing incidents, redact customer-identifying information unless explicitly needed
- Incident notes may contain root cause details that reveal vulnerabilities - summarize rather than reproduce

### Operational Safety
- **Do not resolve incidents without explicit user confirmation** - resolving prematurely can mask ongoing issues
- **Do not create high-urgency incidents without explicit user request** - this pages people and interrupts their work
- **Do not escalate without explicit user approval** - escalation pages additional responders
- **Do not merge incidents without understanding the relationship** - merging unrelated incidents loses context
- **Be cautious with response plays** - they can trigger automated actions including paging and communication

### Access Control
- Only access services and incidents the configured API key has permissions for
- Do not attempt to enumerate users, teams, or organization structure beyond what's needed
- If an operation returns 403/401, report the error without retrying
- Do not attempt to modify escalation policies, schedules, or service configurations without explicit approval
- Respect on-call boundaries - do not page people outside their scheduled hours without explicit request

## Anti-Hallucination Guardrails

### API Accuracy
- **Do not fabricate incident IDs, service IDs, or user IDs** - always list or search first to confirm they exist
- **Do not assume incident states** - always check current state before suggesting actions
- **Do not invent PagerDuty-specific terminology** - use correct terms: triggered, acknowledged, resolved (not "open", "in-progress", "closed")
- **Do not fabricate on-call schedules** - always query current on-call before stating who's available
- **Do not assume escalation policy structure** - query the policy to understand levels and targets

### Result Interpretation
- **Never invent incident details** - if you haven't queried an incident, say "I need to check this"
- **Do not assume incident severity or impact** - read the actual incident data
- **Do not assume who acknowledged or resolved an incident** - check the timeline
- **If a query returns no incidents**, report that clearly rather than speculating
- **Do not extrapolate MTTA/MTTR trends** without sufficient data points

### Tool Capability Boundaries
- Do not claim ability to modify escalation policies or schedules
- Do not claim ability to create or modify services or integrations
- Do not claim ability to manage users or teams
- Do not claim ability to configure event rules or alert grouping
- Clearly state when an action requires the user to perform it in the PagerDuty UI

## Operational Optimization Guardrails

### API Rate Limiting
- **PagerDuty has rate limits** (varies by plan, typically 900 requests/minute) - be mindful of call volume
- **Use filters** - always filter by status, urgency, or service rather than listing all incidents
- **Cache service IDs and policy IDs** - don't re-list them for every operation
- **Avoid paginating through all historical incidents** - use time filters to scope results

### Request Efficiency
- **Filter at the API level** - use `statuses`, `service_ids`, and `urgencies` parameters rather than client-side filtering
- **Use `since` and `until`** to bound incident queries - don't fetch all-time history
- **Minimize redundant calls** - if you just created/updated an incident, use the response rather than re-fetching
- **Batch awareness** - some operations (like merging) affect multiple incidents; plan accordingly

### Incident Response Efficiency
- **Acknowledge immediately** - this stops escalation timers and signals you're responding
- **Add notes as you investigate** - creates timeline without additional API calls later
- **Merge related incidents early** - reduces noise and duplicate notifications
- **Resolve promptly when fixed** - don't leave incidents in acknowledged state indefinitely

## Cost Optimization Guardrails

### API Usage
- **Minimize API calls** - plan the workflow before executing
- **Avoid redundant queries** - if you already have incident details, don't re-fetch
- **Use appropriate time ranges** - don't query 90 days of history when 7 days suffices
- **Limit analytics queries** - they can be expensive on large datasets

### Notification Cost Awareness
- **Every incident creation triggers notifications** - don't create test incidents on production services
- **Escalation triggers additional notifications** - only escalate when genuinely needed
- **Response plays trigger automated actions** - understand what a play does before running it
- **High-urgency incidents page immediately** - use low urgency for non-critical issues

### Operational Efficiency
- **Reduce alert noise** - when reviewing services, identify candidates for alert consolidation
- **Suggest event rules** - help users configure intelligent alert grouping to reduce incident volume
- **Recommend maintenance windows** - for planned work, suggest suppressing alerts
- **Track MTTA/MTTR** - use analytics to identify services that need attention
