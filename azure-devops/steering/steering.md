# Azure DevOps MCP Server Steering Guide

This steering file covers the Azure DevOps MCP server to manage work items, pull requests, pipelines, and repositories.

## When to Use the Azure DevOps MCP Server

Use Azure DevOps MCP tools when you need to:
- **Manage work items**: Create, update, and query bugs, tasks, user stories, and epics
- **Handle pull requests**: Create, review, comment on, and complete PRs
- **Run pipelines**: Trigger builds, check status, and monitor deployments
- **Search code**: Find patterns across repositories
- **Plan sprints**: Query backlogs, manage iterations, and track progress

## Core Principles

### 1. Link Everything
Always link PRs to work items and work items to each other. This enables traceability, auto-transitions, and reporting.

### 2. Use Branch Policies
Enforce code review, build validation, and work item linking through branch policies on main/release branches.

### 3. Automate State Transitions
Configure PR completion to automatically transition linked work items to the next state.

---

## WIQL (Work Item Query Language) Reference

### Basic Syntax
```sql
SELECT [Field1], [Field2], ...
FROM WorkItems
WHERE [Condition1] AND [Condition2]
ORDER BY [Field] ASC|DESC
```

### Field Reference

**System fields:**
| Field | Description | Example Values |
|-------|-------------|----------------|
| `[System.Id]` | Work item ID | 12345 |
| `[System.Title]` | Title text | "Fix login bug" |
| `[System.State]` | Current state | New, Active, Resolved, Closed |
| `[System.WorkItemType]` | Item type | Bug, Task, User Story, Epic, Feature |
| `[System.AssignedTo]` | Assignee | "user@company.com" |
| `[System.CreatedDate]` | Created date | 2024-01-15 |
| `[System.ChangedDate]` | Last modified | 2024-01-20 |
| `[System.CreatedBy]` | Creator | "user@company.com" |
| `[System.AreaPath]` | Area path | "Project\\Backend" |
| `[System.IterationPath]` | Sprint | "Project\\Sprint 15" |
| `[System.Tags]` | Tags | "api, urgent" |
| `[System.Description]` | Description | HTML content |
| `[System.Reason]` | State change reason | "Fixed" |

**VSTS fields:**
| Field | Description | Example Values |
|-------|-------------|----------------|
| `[Microsoft.VSTS.Common.Priority]` | Priority | 1, 2, 3, 4 |
| `[Microsoft.VSTS.Common.Severity]` | Bug severity | 1-Critical, 2-High, 3-Medium, 4-Low |
| `[Microsoft.VSTS.Scheduling.StoryPoints]` | Story points | 1, 2, 3, 5, 8, 13 |
| `[Microsoft.VSTS.Scheduling.RemainingWork]` | Remaining hours | 4.0 |
| `[Microsoft.VSTS.Scheduling.OriginalEstimate]` | Original estimate | 8.0 |
| `[Microsoft.VSTS.Scheduling.CompletedWork]` | Completed hours | 4.0 |
| `[Microsoft.VSTS.Common.AcceptanceCriteria]` | Acceptance criteria | HTML content |
| `[Microsoft.VSTS.TCM.ReproSteps]` | Repro steps (bugs) | HTML content |

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `[System.State] = 'Active'` |
| `<>` | Not equals | `[System.State] <> 'Closed'` |
| `>`, `<`, `>=`, `<=` | Comparison | `[Microsoft.VSTS.Common.Priority] <= 2` |
| `IN` | In list | `[System.State] IN ('Active', 'New')` |
| `NOT IN` | Not in list | `[System.WorkItemType] NOT IN ('Task')` |
| `CONTAINS` | Text contains | `[System.Title] CONTAINS 'checkout'` |
| `NOT CONTAINS` | Text doesn't contain | `[System.Title] NOT CONTAINS 'test'` |
| `UNDER` | Path hierarchy | `[System.AreaPath] UNDER 'Project\\Backend'` |
| `NOT UNDER` | Not in path | `[System.IterationPath] NOT UNDER 'Project\\Archive'` |
| `WAS EVER` | Historical | `[System.AssignedTo] WAS EVER @Me` |

### Macros

| Macro | Description |
|-------|-------------|
| `@Me` | Current user |
| `@Today` | Today's date |
| `@Today - N` | N days ago |
| `@Today + N` | N days from now |
| `@CurrentIteration` | Current sprint |
| `@CurrentIteration + 1` | Next sprint |
| `@CurrentIteration - 1` | Previous sprint |
| `@Project` | Current project |
| `@TeamAreas` | Current team's area paths |

### Common Query Patterns

**My active work:**
```sql
SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.State] NOT IN ('Closed', 'Resolved', 'Removed')
ORDER BY [Microsoft.VSTS.Common.Priority] ASC, [System.ChangedDate] DESC
```

**Sprint backlog:**
```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo],
       [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration
  AND [System.WorkItemType] IN ('User Story', 'Bug')
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

**Unresolved bugs by severity:**
```sql
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Severity],
       [System.AssignedTo], [System.CreatedDate]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug'
  AND [System.State] NOT IN ('Closed', 'Resolved')
ORDER BY [Microsoft.VSTS.Common.Severity] ASC, [System.CreatedDate] ASC
```

**Items changed this week:**
```sql
SELECT [System.Id], [System.Title], [System.State], [System.ChangedDate]
FROM WorkItems
WHERE [System.ChangedDate] >= @Today - 7
  AND [System.WorkItemType] <> 'Task'
ORDER BY [System.ChangedDate] DESC
```

**Blocked items:**
```sql
SELECT [System.Id], [System.Title], [System.State], [System.Tags]
FROM WorkItems
WHERE [System.Tags] CONTAINS 'blocked'
  AND [System.State] NOT IN ('Closed', 'Resolved')
```

**Items without estimates:**
```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration
  AND [System.WorkItemType] = 'User Story'
  AND [Microsoft.VSTS.Scheduling.StoryPoints] = ''
```

**Carry-over from last sprint:**
```sql
SELECT [System.Id], [System.Title], [System.State],
       [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration - 1
  AND [System.State] NOT IN ('Closed', 'Resolved', 'Removed')
  AND [System.WorkItemType] IN ('User Story', 'Bug')
```

---

## Pull Request Best Practices

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `hotfix/description` - Production hotfixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### PR Title Format
Follow conventional commits:
- `feat: add password reset flow`
- `fix: handle null pointer in checkout`
- `refactor: extract payment validation`
- `docs: update API documentation`

### PR Description Template
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Related Work Items
Closes #12345
```

### Merge Strategies

| Strategy | When to Use |
|----------|-------------|
| Squash | Default for feature branches - clean history |
| Rebase | When you want linear history without merge commits |
| No Fast-Forward | When you want to preserve branch history |

---

## Pipeline Patterns

### Triggering Pipelines

**Standard build:**
```javascript
run_pipeline({
  "pipeline_id": 42,
  "branch": "refs/heads/main"
})
```

**With variables:**
```javascript
run_pipeline({
  "pipeline_id": 42,
  "branch": "refs/heads/release/v2.0",
  "variables": {
    "environment": "production",
    "skipTests": "false",
    "deployRegion": "us-east-1"
  }
})
```

### Monitoring Pipeline Runs

1. Trigger the pipeline
2. Get the run ID from the response
3. Poll `get_pipeline_run` for status
4. Check for failed stages/jobs
5. If failed, investigate logs

### Common Pipeline States
- `notStarted` - Queued
- `inProgress` - Running
- `completed` - Finished (check result)
- `canceling` / `canceled` - Cancelled

### Pipeline Results
- `succeeded` - All stages passed
- `failed` - One or more stages failed
- `canceled` - Run was cancelled
- `partiallySucceeded` - Some stages failed but run continued

---

## Work Item State Transitions

### User Story
```
New → Active → Resolved → Closed
         ↓         ↑
       Removed    Active (reactivated)
```

### Bug
```
New → Active → Resolved → Closed
  ↓      ↓         ↑
  ↓    Removed    Active (reactivated)
  └→ Resolved (by design / cannot reproduce)
```

### Task
```
New → Active → Closed
         ↓
       Removed
```

---

## Sprint Planning Workflow

### 1. Review Previous Sprint
```sql
-- Completed items
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration - 1
  AND [System.State] IN ('Closed', 'Resolved')
  AND [System.WorkItemType] IN ('User Story', 'Bug')

-- Carry-over items
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration - 1
  AND [System.State] NOT IN ('Closed', 'Resolved', 'Removed')
```

### 2. Plan Current Sprint
```sql
-- Backlog items ready for sprint
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Priority],
       [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @Project
  AND [System.State] = 'New'
  AND [System.WorkItemType] IN ('User Story', 'Bug')
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

### 3. Track Progress
```sql
-- Sprint burndown data
SELECT [System.Id], [System.State], [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration
  AND [System.WorkItemType] IN ('User Story', 'Bug')
```

---

## Troubleshooting

### WIQL Query Errors
1. Check field names are correct (case-sensitive)
2. Verify string values are in single quotes
3. Ensure dates use correct format
4. Check that macros are supported in your context
5. Verify area/iteration paths exist

### PR Creation Fails
1. Verify branch names include `refs/heads/` prefix
2. Check source branch exists and has commits ahead of target
3. Verify repository name or ID is correct
4. Check branch policies aren't blocking creation

### Pipeline Not Triggering
1. Verify pipeline ID is correct
2. Check branch name format
3. Verify PAT has Build (Execute) permission
4. Check pipeline isn't disabled or paused

---

## Summary Checklist

For effective Azure DevOps usage:
- ✅ Link PRs to work items for traceability
- ✅ Use WIQL for complex work item queries
- ✅ Follow conventional commit format for PR titles
- ✅ Use squash merge for clean history
- ✅ Delete source branches after merge
- ✅ Include `refs/heads/` prefix for branch names
- ✅ Set up branch policies for quality gates
- ✅ Use iteration paths for sprint planning
- ✅ Monitor pipeline status after triggering
- ✅ Auto-transition work items on PR completion

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `AZURE_DEVOPS_PAT` values in responses
- When referencing tokens, use placeholder names (e.g., "your PAT") not actual values
- Do not include PATs in work item descriptions, PR comments, or pipeline variables

### Repository and Code Safety
- **Never push secrets to repositories** - if file content contains API keys, passwords, or tokens, refuse and warn the user
- **Never push directly to `main` or protected branches** - always use feature branches and PRs
- **Do not modify pipeline YAML** (`azure-pipelines.yml`) without explicit user approval - CI/CD changes can have security implications
- **Do not set pipeline variables containing secrets** without explicit user confirmation
- When using `push_files` or `create_or_update_file`, verify content does not contain hardcoded credentials

### Data Sensitivity
- Work items may contain sensitive information - customer details, security vulnerabilities, internal architecture
- Code search results may contain sensitive patterns - do not reproduce large blocks that appear to contain secrets
- Pipeline logs may contain secrets - summarize errors rather than reproducing full logs verbatim
- Do not expose internal project names, organization URLs, or infrastructure details to unauthorized contexts
- WIQL query results may contain PII in work item fields - summarize rather than reproduce verbatim

### Access Control
- Only access projects and repositories the configured PAT has permissions for
- Do not attempt to enumerate organizations, projects, or teams beyond what's needed
- If an operation returns 403/401, report the error without retrying with different credentials
- Do not attempt to bypass branch policies, required reviewers, or build validation
- Do not attempt to modify project-level settings, policies, or permissions
- Respect area path and iteration path security - some paths may be restricted

## Anti-Hallucination Guardrails

### Query Accuracy
- **Only use valid WIQL syntax** - do not invent field names, operators, or clauses
- **Only use documented field references** - valid system fields start with `[System.]`, VSTS fields with `[Microsoft.VSTS.]`
- **Do not fabricate work item IDs, PR IDs, or pipeline IDs** - always query first to confirm they exist
- **Do not assume branch names** - verify branches exist before creating PRs (use `refs/heads/` prefix)
- **Do not invent WIQL macros** - valid macros: `@Me`, `@Today`, `@Today - N`, `@CurrentIteration`, `@Project`, `@TeamAreas`
- **Do not assume work item types** - valid types vary by process template (Agile, Scrum, CMMI); common types: Bug, Task, User Story, Epic, Feature

### Result Interpretation
- **Never invent API responses** - if a tool hasn't been called, say "I need to check this" rather than guessing
- **Do not assume PR status** - always check current state before suggesting merge or review actions
- **Do not assume pipeline status** - verify before claiming a pipeline passed or failed
- **Do not assume work item states** - states vary by work item type and process template
- **If a query returns no results**, report that clearly rather than speculating
- **Do not fabricate iteration paths, area paths, or team names** - these are organization-specific

### Tool Capability Boundaries
- Do not claim ability to approve PRs on behalf of other users
- Do not claim ability to modify branch policies or project settings
- Do not claim ability to manage build agents, service connections, or variable groups
- Do not claim ability to create or modify pipeline definitions (only trigger existing ones)
- Clearly state when an action requires the user to perform it in the Azure DevOps UI

## Operational Optimization Guardrails

### API Rate Limiting
- **Azure DevOps has rate limits** (varies by plan, typically 200 requests/minute) - be mindful of call volume
- **Use WIQL for bulk queries** - a single WIQL query is more efficient than multiple individual work item fetches
- **Cache work item IDs and PR IDs** - once found, reuse without re-querying
- **Use `$top` / `limit` parameters** to control result sizes
- **Avoid paginating through all results** - use specific WIQL filters instead

### Request Efficiency
- **Use WIQL over list operations** - `query_work_items` with specific WHERE clauses is more efficient than listing and filtering
- **Minimize diff fetches** - PR diffs can be large; only fetch when reviewing
- **Don't repeatedly check pipeline status** - check once, wait, then check again if needed
- **Use `expand` parameter wisely** - only expand relations when you need them; it adds overhead
- **Batch work item updates** when possible - plan changes before executing

### Workflow Efficiency
- **Create branch + push + PR in sequence** - minimize intermediate operations
- **Link work items at PR creation** - use `work_item_ids` parameter rather than updating later
- **Use `transition_work_items: true`** on PR completion - automates state changes
- **Use `delete_source_branch: true`** on merge - keeps repository clean automatically
- **Use draft PRs** for work-in-progress - avoids triggering required reviewers prematurely

## Cost Optimization Guardrails

### API Usage
- **Minimize API calls** - plan the workflow before executing, determine minimum calls needed
- **Avoid redundant queries** - if you already have the information, don't query again
- **Use WIQL efficiently** - a well-crafted WIQL query replaces multiple API calls
- **Batch file operations** - push multiple files in one commit when possible

### Pipeline Cost Awareness
- **Every pipeline run consumes compute** - don't trigger pipelines unnecessarily
- **Use `variables` parameter wisely** - skip expensive test stages during development with variables like `skipTests=true`
- **Don't trigger pipelines on every push** - consider using draft PRs that may skip CI
- **Consider parallel pipeline costs** - multiple simultaneous runs multiply compute usage
- **Avoid force-pushing repeatedly** - each push to a PR branch may trigger a new pipeline run

### Work Item Efficiency
- **Use WIQL to find existing items** before creating duplicates
- **Proper categorization reduces rework** - correct area path and iteration path on creation
- **Link related items** - reduces duplicate investigation and improves traceability
- **Use tags for cross-cutting concerns** - more efficient than creating duplicate work items
- **Close completed items promptly** - reduces noise in queries and boards
