---
name: "azure-devops"
displayName: "Azure DevOps"
description: "Manage repositories, pipelines, work items, pull requests, and boards in Azure DevOps for end-to-end software delivery"
keywords: ["azure-devops", "ado", "wiql", "azure-pipelines", "azure-boards", "azure-repos", "work-items"]
author: "Community"
---

# Azure DevOps Power

## Overview

The Azure DevOps Power connects to Azure DevOps Services for managing repositories, CI/CD pipelines, work items, pull requests, boards, and sprints. Work with Azure DevOps directly from your IDE.

**Key capabilities:**
- **Repositories**: Create, manage, and search Git repositories
- **Pull Requests**: Create, review, approve, and complete PRs
- **Pipelines**: Trigger, monitor, and manage CI/CD pipelines
- **Work Items**: Create, update, query, and manage work items (bugs, tasks, user stories)
- **Boards**: View and manage sprint boards and backlogs
- **Build & Release**: Monitor builds, releases, and deployment status
- **Wiki**: Search and manage project wikis
- **Artifacts**: Manage package feeds and artifacts

**Authentication**: Requires Azure DevOps organization URL and Personal Access Token (PAT).

## Onboarding

### Prerequisites

1. **Azure DevOps organization** - Azure DevOps Services or Azure DevOps Server
2. **Personal Access Token (PAT)** - With appropriate scopes for your workflows
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your organization URL and PAT
3. Test with: *"List my active work items"* or *"Show open pull requests"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_ORGANIZATION`**: Your Azure DevOps organization name.
 - **How to get it:** This is the organization name in your Azure DevOps URL: `https://dev.azure.com/YOUR_ORGANIZATION`. You can find it in Organization Settings.

- **`YOUR_PERSONAL_ACCESS_TOKEN`**: An Azure DevOps Personal Access Token.
 - **How to get it:**
    1. Log in to Azure DevOps
    2. Click your profile icon → Personal Access Tokens
    3. Click "New Token"
    4. Set scopes: Code (Read & Write), Work Items (Read & Write), Build (Read & Execute), Project (Read)
    5. Set expiration (recommend 90 days max)
    6. Copy the generated token (you won't see it again)

## Available Steering Files

- **steering/steering.md** - WIQL query syntax, pipeline patterns, and PR workflows

## Available MCP Servers

### azure-devops
**Package:** `@microsoft/azure-devops-mcp-server`
**Connection:** stdio via npx

**Tools:**

1. **get_work_item** - Get work item details
  - Required: `id` (number) - Work item ID
  - Optional: `expand` (string) - relations, fields, all
  - Returns: Work item with fields and relations

2. **create_work_item** - Create a new work item
  - Required: `project` (string) - Project name
  - Required: `type` (string) - Work item type (Bug, Task, User Story, Epic, Feature)
  - Required: `title` (string) - Work item title
  - Optional: `description` (string) - HTML description
  - Optional: `assigned_to` (string) - Assignee email
  - Optional: `area_path` (string) - Area path
  - Optional: `iteration_path` (string) - Sprint/iteration
  - Optional: `priority` (number) - 1-4
  - Optional: `parent_id` (number) - Parent work item ID
  - Returns: Created work item

3. **update_work_item** - Update a work item
  - Required: `id` (number) - Work item ID
  - Optional: `title` (string), `state` (string), `assigned_to` (string), `priority` (number), `description` (string)
  - Returns: Updated work item

4. **query_work_items** - Execute a WIQL query
  - Required: `query` (string) - WIQL query
  - Optional: `project` (string) - Project scope
  - Returns: Matching work items

5. **create_pull_request** - Create a pull request
  - Required: `repository_id` (string) - Repository name or ID
  - Required: `source_branch` (string) - Source branch (refs/heads/...)
  - Required: `target_branch` (string) - Target branch
  - Required: `title` (string) - PR title
  - Optional: `description` (string) - PR description
  - Optional: `reviewers` (array) - Reviewer IDs or emails
  - Optional: `work_item_ids` (array) - Linked work items
  - Optional: `is_draft` (boolean) - Create as draft
  - Returns: Created PR details

6. **get_pull_request** - Get PR details
  - Required: `repository_id` (string) - Repository name or ID
  - Required: `pull_request_id` (number) - PR ID
  - Returns: Full PR with reviewers, status, and threads

7. **list_pull_requests** - List pull requests
  - Required: `repository_id` (string) - Repository name or ID
  - Optional: `status` (string) - active, completed, abandoned
  - Optional: `creator_id` (string) - Filter by creator
  - Optional: `reviewer_id` (string) - Filter by reviewer
  - Returns: List of PRs

8. **complete_pull_request** - Complete (merge) a PR
  - Required: `repository_id` (string) - Repository name or ID
  - Required: `pull_request_id` (number) - PR ID
  - Optional: `merge_strategy` (string) - squash, rebase, noFastForward
  - Optional: `delete_source_branch` (boolean) - Delete branch after merge
  - Optional: `transition_work_items` (boolean) - Move linked work items
  - Returns: Completed PR

9. **get_pipeline** - Get pipeline details
  - Required: `pipeline_id` (number) - Pipeline ID
  - Returns: Pipeline configuration and recent runs

10. **list_pipelines** - List pipelines
   - Optional: `project` (string) - Project name
   - Returns: Pipelines with status

11. **run_pipeline** - Trigger a pipeline run
   - Required: `pipeline_id` (number) - Pipeline ID
   - Optional: `branch` (string) - Branch to build
   - Optional: `variables` (object) - Pipeline variables
   - Returns: Pipeline run details

12. **get_pipeline_run** - Get pipeline run status
   - Required: `pipeline_id` (number) - Pipeline ID
   - Required: `run_id` (number) - Run ID
   - Returns: Run status, stages, and logs

13. **list_repositories** - List repositories
   - Optional: `project` (string) - Project name
   - Returns: Repositories with metadata

14. **get_file_contents** - Get file from repository
   - Required: `repository_id` (string) - Repository name or ID
   - Required: `path` (string) - File path
   - Optional: `branch` (string) - Branch name
   - Returns: File content

15. **search_code** - Search code across repositories
   - Required: `search_text` (string) - Search query
   - Optional: `project` (string) - Project scope
   - Optional: `repository` (string) - Repository filter
   - Returns: Matching code with file paths

16. **add_pr_comment** - Add comment to a PR
   - Required: `repository_id` (string), `pull_request_id` (number), `content` (string)
   - Optional: `file_path` (string), `line` (number) - For inline comments
   - Returns: Created comment thread

17. **get_iterations** - List sprint iterations
   - Required: `project` (string) - Project name
   - Optional: `timeframe` (string) - current, past, future
   - Returns: Iterations with dates and paths

## Tool Usage Examples

### Work Item Management

**Query open bugs:**
```javascript
usePower("azure-devops", "azure-devops", "query_work_items", {
  "query": "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Common.Priority] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' AND [System.State] <> 'Closed' AND [System.State] <> 'Resolved' ORDER BY [Microsoft.VSTS.Common.Priority] ASC",
  "project": "MyProject"
})
```

**Create a user story:**
```javascript
usePower("azure-devops", "azure-devops", "create_work_item", {
  "project": "MyProject",
  "type": "User Story",
  "title": "As a user, I want to reset my password via email",
  "description": "<h3>Acceptance Criteria</h3><ul><li>User receives reset email within 1 minute</li><li>Reset link expires after 24 hours</li><li>Password must meet complexity requirements</li></ul>",
  "assigned_to": "developer@company.com",
  "iteration_path": "MyProject\\Sprint 15",
  "priority": 2
})
```

**Create a bug:**
```javascript
usePower("azure-devops", "azure-devops", "create_work_item", {
  "project": "MyProject",
  "type": "Bug",
  "title": "Checkout fails with 500 error when cart has more than 50 items",
  "description": "<h3>Steps to Reproduce</h3><ol><li>Add 51 items to cart</li><li>Click checkout</li><li>Observe 500 error</li></ol><h3>Expected</h3><p>Checkout succeeds</p><h3>Actual</h3><p>HTTP 500 Internal Server Error</p>",
  "priority": 1,
  "area_path": "MyProject\\Backend"
})
```

**Update work item state:**
```javascript
usePower("azure-devops", "azure-devops", "update_work_item", {
  "id": 12345,
  "state": "Active",
  "assigned_to": "developer@company.com"
})
```

### Pull Request Workflow

**Create a PR:**
```javascript
usePower("azure-devops", "azure-devops", "create_pull_request", {
  "repository_id": "my-repo",
  "source_branch": "refs/heads/feature/password-reset",
  "target_branch": "refs/heads/main",
  "title": "feat: add password reset via email",
  "description": "## Summary\nImplements password reset flow.\n\n## Changes\n- Reset endpoint\n- Email service integration\n- Token generation and validation\n\n## Testing\n- Unit tests added\n- Integration tests pass\n\nCloses #12345",
  "work_item_ids": [12345],
  "reviewers": ["reviewer@company.com"],
  "is_draft": false
})
```

**Complete a PR:**
```javascript
usePower("azure-devops", "azure-devops", "complete_pull_request", {
  "repository_id": "my-repo",
  "pull_request_id": 99,
  "merge_strategy": "squash",
  "delete_source_branch": true,
  "transition_work_items": true
})
```

### Pipeline Management

**Trigger a build:**
```javascript
usePower("azure-devops", "azure-devops", "run_pipeline", {
  "pipeline_id": 42,
  "branch": "refs/heads/main",
  "variables": {
    "environment": "staging",
    "skipTests": "false"
  }
})
```

**Check pipeline status:**
```javascript
usePower("azure-devops", "azure-devops", "get_pipeline_run", {
  "pipeline_id": 42,
  "run_id": 1001
})
```

## Combining Tools (Workflows)

### Workflow 1: Feature Development

```javascript
// Step 1: Create user story
const story = usePower("azure-devops", "azure-devops", "create_work_item", {
  "project": "MyProject",
  "type": "User Story",
  "title": "Implement order history page",
  "iteration_path": "MyProject\\Sprint 15",
  "priority": 2
})

// Step 2: Create tasks under the story
const task = usePower("azure-devops", "azure-devops", "create_work_item", {
  "project": "MyProject",
  "type": "Task",
  "title": "Create order history API endpoint",
  "parent_id": story.id,
  "assigned_to": "developer@company.com"
})

// Step 3: After implementation, create PR
const pr = usePower("azure-devops", "azure-devops", "create_pull_request", {
  "repository_id": "backend-api",
  "source_branch": "refs/heads/feature/order-history",
  "target_branch": "refs/heads/main",
  "title": "feat: add order history endpoint",
  "work_item_ids": [story.id, task.id]
})

// Step 4: After review, complete PR
const completed = usePower("azure-devops", "azure-devops", "complete_pull_request", {
  "repository_id": "backend-api",
  "pull_request_id": pr.pullRequestId,
  "merge_strategy": "squash",
  "delete_source_branch": true,
  "transition_work_items": true
})
```

### Workflow 2: Bug Fix Pipeline

```javascript
// Step 1: Get bug details
const bug = usePower("azure-devops", "azure-devops", "get_work_item", {
  "id": 54321,
  "expand": "relations"
})

// Step 2: Search for related code
const code = usePower("azure-devops", "azure-devops", "search_code", {
  "search_text": "checkout cart limit",
  "repository": "backend-api"
})

// Step 3: Update bug to Active
const updated = usePower("azure-devops", "azure-devops", "update_work_item", {
  "id": 54321,
  "state": "Active",
  "assigned_to": "developer@company.com"
})

// Step 4: Create PR with fix
const pr = usePower("azure-devops", "azure-devops", "create_pull_request", {
  "repository_id": "backend-api",
  "source_branch": "refs/heads/fix/checkout-cart-limit",
  "target_branch": "refs/heads/main",
  "title": "fix: handle large cart sizes in checkout",
  "description": "Fixes #54321. Increases cart item limit and adds pagination for large carts.",
  "work_item_ids": [54321]
})

// Step 5: Trigger pipeline
const run = usePower("azure-devops", "azure-devops", "run_pipeline", {
  "pipeline_id": 42,
  "branch": "refs/heads/fix/checkout-cart-limit"
})

// Step 6: Check pipeline result
const status = usePower("azure-devops", "azure-devops", "get_pipeline_run", {
  "pipeline_id": 42,
  "run_id": run.id
})
```

### Workflow 3: Sprint Planning

```javascript
// Step 1: Get current sprint
const iterations = usePower("azure-devops", "azure-devops", "get_iterations", {
  "project": "MyProject",
  "timeframe": "current"
})

// Step 2: Query sprint backlog
const backlog = usePower("azure-devops", "azure-devops", "query_work_items", {
  "query": "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Scheduling.StoryPoints] FROM WorkItems WHERE [System.IterationPath] = 'MyProject\\Sprint 15' AND [System.WorkItemType] IN ('User Story', 'Bug') ORDER BY [Microsoft.VSTS.Common.Priority] ASC",
  "project": "MyProject"
})

// Step 3: Check unfinished items from last sprint
const carryover = usePower("azure-devops", "azure-devops", "query_work_items", {
  "query": "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.IterationPath] = 'MyProject\\Sprint 14' AND [System.State] <> 'Closed' AND [System.State] <> 'Resolved' AND [System.WorkItemType] IN ('User Story', 'Bug')",
  "project": "MyProject"
})
```

## WIQL Query Syntax

### Basic Structure
```sql
SELECT [Field1], [Field2]
FROM WorkItems
WHERE [Condition]
ORDER BY [Field] ASC|DESC
```

### Common Fields
| Field | Description |
|-------|-------------|
| `[System.Id]` | Work item ID |
| `[System.Title]` | Title |
| `[System.State]` | State (New, Active, Resolved, Closed) |
| `[System.WorkItemType]` | Type (Bug, Task, User Story, Epic, Feature) |
| `[System.AssignedTo]` | Assignee |
| `[System.CreatedDate]` | Creation date |
| `[System.ChangedDate]` | Last modified date |
| `[System.AreaPath]` | Area path |
| `[System.IterationPath]` | Sprint/iteration |
| `[System.Tags]` | Tags |
| `[Microsoft.VSTS.Common.Priority]` | Priority (1-4) |
| `[Microsoft.VSTS.Scheduling.StoryPoints]` | Story points |
| `[Microsoft.VSTS.Common.Severity]` | Bug severity |

### Operators
- `=`, `<>`, `>`, `<`, `>=`, `<=`
- `IN ('value1', 'value2')`
- `NOT IN ('value1')`
- `CONTAINS 'text'`
- `UNDER 'path'` (for area/iteration paths)
- `= @Me` (current user)
- `= @Today` (today's date)
- `>= @Today - 7` (7 days ago)

### Example Queries

**Active bugs by priority:**
```sql
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Priority]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug'
  AND [System.State] = 'Active'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

**My work items:**
```sql
SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.State] <> 'Closed'
ORDER BY [System.ChangedDate] DESC
```

**Sprint burndown:**
```sql
SELECT [System.Id], [System.Title], [System.State], [Microsoft.VSTS.Scheduling.StoryPoints]
FROM WorkItems
WHERE [System.IterationPath] UNDER 'MyProject\Sprint 15'
  AND [System.WorkItemType] IN ('User Story', 'Bug')
```

**Recently created items:**
```sql
SELECT [System.Id], [System.Title], [System.CreatedDate]
FROM WorkItems
WHERE [System.CreatedDate] >= @Today - 7
  AND [System.WorkItemType] <> 'Task'
ORDER BY [System.CreatedDate] DESC
```

## Best Practices

### ✅ Do:
- **Link PRs to work items** - Enables traceability and auto-transitions
- **Use squash merge** - Keeps main branch history clean
- **Write descriptive PR descriptions** - Include summary, changes, and testing
- **Use WIQL for complex queries** - More powerful than UI filters
- **Delete source branches** - Keep repository clean after merge
- **Use draft PRs** - Signal work-in-progress
- **Transition work items** - Let PR completion move items to Done
- **Use branch policies** - Enforce reviews and build validation

### ❌ Don't:
- **Push directly to main** - Always use PRs with branch policies
- **Create PRs without linked work items** - Breaks traceability
- **Skip pipeline checks** - Wait for green builds before merging
- **Leave stale branches** - Delete after merge
- **Use vague work item titles** - Be specific about what and why
- **Ignore failed pipelines** - Investigate and fix before merging

## Configuration

**Authentication Required**: Azure DevOps organization URL and PAT

**Setup Steps:**

1. **Create a Personal Access Token:**
  - Go to Azure DevOps → User Settings → Personal Access Tokens
  - Create token with scopes: Code (Read & Write), Work Items (Read & Write), Build (Read & Execute), Project (Read)

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "azure-devops": {
         "command": "npx",
         "args": ["-y", "@microsoft/azure-devops-mcp-server"],
         "env": {
           "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/YOUR_ORGANIZATION",
           "AZURE_DEVOPS_PAT": "your-personal-access-token"
         }
       }
     }
   }
   ```

3. **For Azure DevOps Server (on-prem):**
   ```json
   "env": {
     "AZURE_DEVOPS_ORG_URL": "https://tfs.yourcompany.com/tfs/DefaultCollection",
     "AZURE_DEVOPS_PAT": "your-pat"
   }
   ```

## Tips

1. **Link everything** - PRs to work items, work items to each other
2. **Use WIQL** - More powerful than basic search for complex queries
3. **Squash merge** - Clean history, easy to revert
4. **Branch policies** - Enforce quality gates automatically
5. **Pipeline variables** - Parameterize builds for flexibility
6. **Sprint iterations** - Use iteration paths for sprint planning
7. **Area paths** - Organize by team or component
8. **Draft PRs** - Get early feedback before code is complete
9. **Auto-transition** - Let PR completion move work items
10. **Code search** - Find patterns across all repositories

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@microsoft/azure-devops-mcp-server`
**Source:** Microsoft
**License:** MIT-0
**Documentation:** https://learn.microsoft.com/en-us/azure/devops/
