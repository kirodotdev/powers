---
name: "gitlab"
displayName: "GitLab"
description: "Manage repositories, merge requests, issues, pipelines, and CI/CD on GitLab directly from your IDE"
keywords: ["gitlab", "git", "repository", "merge-request", "issues", "ci", "cd", "pipelines", "code-review", "devops"]
author: "Community"
---

# GitLab Power

## Overview

The GitLab Power connects to GitLab's DevOps platform for repository management, merge requests, issue tracking, CI/CD pipelines, and project management. Work with GitLab directly from your IDE.

**Key capabilities:**
- **Repository Management**: Create, fork, search, and manage projects
- **Merge Requests**: Create, review, approve, and merge MRs with full diff support
- **Issues**: Create, search, update, and manage issues with labels, milestones, and weights
- **CI/CD Pipelines**: Trigger, monitor, and manage pipeline runs and jobs
- **Code Search**: Search code across projects and groups
- **Branch Management**: Create, protect, and manage branches
- **File Operations**: Read, create, and update files directly in repositories
- **Wiki & Snippets**: Manage project wikis and code snippets

**Authentication**: Requires a GitLab Personal Access Token.

## Onboarding

### Prerequisites

1. **GitLab account** - GitLab.com or self-hosted GitLab instance
2. **Personal Access Token** - With `api`, `read_repository`, and `write_repository` scopes
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace placeholders in `mcp.json` with your GitLab token and API URL
3. Test with: *"List my open merge requests"* or *"Show project issues"*

### MCP Config Placeholders

Before using this power, replace the following placeholders in `mcp.json`:

- **`YOUR_GITLAB_TOKEN`**: A GitLab Personal Access Token.
 - **How to get it:**
    1. Go to GitLab → User Settings (click avatar) → Access Tokens
    2. Click "Add new token"
    3. Set scopes: `api`, `read_repository`, `write_repository`
    4. Set expiration date
    5. Click "Create personal access token" and copy the value (starts with `glpat-`)

- **`https://gitlab.com/api/v4`**: Your GitLab API URL.
 - **How to set it:** For GitLab.com, keep the default. For self-hosted GitLab, change to `https://your-gitlab-instance.com/api/v4`

## Available Steering Files

- **steering/steering.md** - GitLab flow, MR best practices, CI/CD pipeline management, and scoped label patterns

## Available MCP Servers

### gitlab
**Package:** `@modelcontextprotocol/server-gitlab`
**Connection:** stdio via npx

**Tools:**

1. **create_or_update_file** - Create or update a file in a project
  - Required: `project_id` (string), `file_path` (string), `content` (string), `commit_message` (string), `branch` (string)
  - Optional: `previous_path` (string) - For renames
  - Returns: File commit details

2. **search_repositories** - Search GitLab projects
  - Required: `search` (string) - Search query
  - Optional: `page` (number), `per_page` (number)
  - Returns: Matching projects with metadata

3. **create_repository** - Create a new project
  - Required: `name` (string)
  - Optional: `description` (string), `visibility` (string), `initialize_with_readme` (boolean), `namespace_id` (number)
  - Returns: Created project details

4. **get_file_contents** - Get file or directory contents
  - Required: `project_id` (string), `file_path` (string)
  - Optional: `ref` (string) - Branch or tag
  - Returns: File content or directory listing

5. **create_issue** - Create a new issue
  - Required: `project_id` (string), `title` (string)
  - Optional: `description` (string), `assignee_ids` (array), `labels` (string), `milestone_id` (number), `weight` (number)
  - Returns: Created issue details

6. **create_merge_request** - Create a merge request
  - Required: `project_id` (string), `title` (string), `source_branch` (string), `target_branch` (string)
  - Optional: `description` (string), `assignee_ids` (array), `reviewer_ids` (array), `labels` (string), `draft` (boolean)
  - Returns: Created MR details

7. **fork_repository** - Fork a project
  - Required: `project_id` (string)
  - Optional: `namespace` (string)
  - Returns: Forked project details

8. **create_branch** - Create a new branch
  - Required: `project_id` (string), `branch` (string), `ref` (string)
  - Returns: Branch details

9. **list_issues** - List issues in a project
  - Required: `project_id` (string)
  - Optional: `state` (string), `labels` (string), `milestone` (string), `assignee_id` (number), `page` (number)
  - Returns: List of issues

10. **update_issue** - Update an existing issue
   - Required: `project_id` (string), `issue_iid` (number)
   - Optional: `title` (string), `description` (string), `state_event` (string), `labels` (string), `assignee_ids` (array)
   - Returns: Updated issue details

11. **list_merge_requests** - List merge requests
   - Required: `project_id` (string)
   - Optional: `state` (string), `source_branch` (string), `target_branch` (string), `page` (number)
   - Returns: List of merge requests

12. **get_merge_request** - Get MR details
   - Required: `project_id` (string), `merge_request_iid` (number)
   - Returns: Full MR details with diff stats

13. **get_merge_request_diffs** - Get MR diff content
   - Required: `project_id` (string), `merge_request_iid` (number)
   - Returns: File diffs for the MR

14. **merge_merge_request** - Merge a merge request
   - Required: `project_id` (string), `merge_request_iid` (number)
   - Optional: `merge_commit_message` (string), `squash` (boolean), `should_remove_source_branch` (boolean)
   - Returns: Merge result

15. **list_pipelines** - List CI/CD pipelines
   - Required: `project_id` (string)
   - Optional: `status` (string), `ref` (string), `page` (number)
   - Returns: Pipeline list with status

16. **get_pipeline** - Get pipeline details
   - Required: `project_id` (string), `pipeline_id` (number)
   - Returns: Pipeline details with jobs

17. **list_pipeline_jobs** - List jobs in a pipeline
   - Required: `project_id` (string), `pipeline_id` (number)
   - Returns: Jobs with status and duration

18. **get_job_log** - Get job log output
   - Required: `project_id` (string), `job_id` (number)
   - Returns: Job log content

19. **create_note** - Add a comment to an issue or MR
   - Required: `project_id` (string), `noteable_type` (string), `noteable_iid` (number), `body` (string)
   - Returns: Created note details

## Tool Usage Examples

### Merge Request Workflow

**Create an MR:**
```javascript
usePower("gitlab", "gitlab", "create_merge_request", {
  "project_id": "mygroup/myproject",
  "title": "feat: add user authentication",
  "source_branch": "feature/auth",
  "target_branch": "main",
  "description": "## Summary\nAdds OAuth2 authentication\n\n## Changes\n- Login flow\n- Token management\n- Session handling",
  "reviewer_ids": [42],
  "labels": "feature,auth",
  "draft": false
})
```

**Check pipeline status:**
```javascript
usePower("gitlab", "gitlab", "list_pipelines", {
  "project_id": "mygroup/myproject",
  "ref": "feature/auth",
  "status": "failed"
})
```

**Get failed job logs:**
```javascript
usePower("gitlab", "gitlab", "get_job_log", {
  "project_id": "mygroup/myproject",
  "job_id": 12345
})
```

### Issue Management

**Create an issue:**
```javascript
usePower("gitlab", "gitlab", "create_issue", {
  "project_id": "mygroup/myproject",
  "title": "Bug: API returns 500 on concurrent requests",
  "description": "## Steps to Reproduce\n1. Send 10 concurrent POST requests\n2. Observe 500 errors\n\n## Expected\nAll requests succeed\n\n## Actual\n3/10 requests fail with 500",
  "labels": "bug,priority::high,backend",
  "weight": 5
})
```

## Combining Tools (Workflows)

### Workflow 1: MR Review and Pipeline Check

```javascript
// Step 1: Get MR details
const mr = usePower("gitlab", "gitlab", "get_merge_request", {
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99
})

// Step 2: Review the diff
const diffs = usePower("gitlab", "gitlab", "get_merge_request_diffs", {
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99
})

// Step 3: Check pipeline status
const pipelines = usePower("gitlab", "gitlab", "list_pipelines", {
  "project_id": "mygroup/myproject",
  "ref": mr.source_branch
})

// Step 4: If pipeline failed, check job logs
const jobs = usePower("gitlab", "gitlab", "list_pipeline_jobs", {
  "project_id": "mygroup/myproject",
  "pipeline_id": pipelines[0].id
})

// Step 5: Get failed job log
const failedJob = jobs.find(j => j.status === "failed")
const log = usePower("gitlab", "gitlab", "get_job_log", {
  "project_id": "mygroup/myproject",
  "job_id": failedJob.id
})
```

### Workflow 2: Feature Development

```javascript
// Step 1: Create branch
const branch = usePower("gitlab", "gitlab", "create_branch", {
  "project_id": "mygroup/myproject",
  "branch": "feature/new-endpoint",
  "ref": "main"
})

// Step 2: Push code
const file = usePower("gitlab", "gitlab", "create_or_update_file", {
  "project_id": "mygroup/myproject",
  "file_path": "src/routes/orders.ts",
  "content": "// Orders API implementation...",
  "commit_message": "feat: add orders endpoint",
  "branch": "feature/new-endpoint"
})

// Step 3: Create MR
const mr = usePower("gitlab", "gitlab", "create_merge_request", {
  "project_id": "mygroup/myproject",
  "title": "feat: add orders endpoint",
  "source_branch": "feature/new-endpoint",
  "target_branch": "main",
  "description": "Adds CRUD for orders"
})

// Step 4: Create tracking issue
const issue = usePower("gitlab", "gitlab", "create_issue", {
  "project_id": "mygroup/myproject",
  "title": "Implement orders API",
  "description": `MR: !${mr.iid}\n\nTasks:\n- [x] Create endpoint\n- [ ] Add tests\n- [ ] Update docs`,
  "labels": "feature,in-progress"
})
```

## Best Practices

### ✅ Do:
- **Use GitLab Flow** - feature branches → MR → main → deploy
- **Write descriptive MR descriptions** with context and testing notes
- **Use scoped labels** (priority::high, type::bug) for structured categorization
- **Set reviewers and assignees** on MRs for accountability
- **Check pipeline status** before merging
- **Use draft MRs** for work-in-progress
- **Reference issues** with "Closes #123" in MR descriptions
- **Use weights on issues** for sprint planning

### ❌ Don't:
- **Push directly to protected branches** - use MRs
- **Merge with failing pipelines** - fix CI first
- **Create MRs without description** - reviewers need context
- **Skip code review** - enforce approval rules
- **Ignore pipeline failures** - investigate and fix

## Configuration

**Authentication Required**: GitLab Personal Access Token

**Setup Steps:**

1. **Create a Personal Access Token:**
  - Go to GitLab → User Settings → Access Tokens
  - Create token with scopes: `api`, `read_repository`, `write_repository`

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "gitlab": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-gitlab"],
         "env": {
           "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat-your_token_here",
           "GITLAB_API_URL": "https://gitlab.com/api/v4"
         }
       }
     }
   }
   ```

3. **For Self-Hosted GitLab:**
   Change `GITLAB_API_URL` to your instance:
   ```json
   "GITLAB_API_URL": "https://gitlab.yourcompany.com/api/v4"
   ```

## Tips

1. **Use scoped labels** - `priority::high`, `type::bug`, `workflow::in-review`
2. **Use CI/CD** - Check pipeline status before merging
3. **Draft MRs early** - Get feedback before code is complete
4. **Use MR templates** - Standardize descriptions across your team
5. **Cross-reference** - Link issues and MRs with GitLab references
6. **Monitor pipelines** - Catch failures early with job logs
7. **Squash on merge** - Keep main branch history clean
8. **Use weights** - Plan sprints with issue weights
9. **Review diffs** - Always check the full diff before approving
10. **Automate** - Use pipeline triggers for deployment automation

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@modelcontextprotocol/server-gitlab`
**Source:** Anthropic (Model Context Protocol)
**License:** MIT-0
**Documentation:** https://github.com/modelcontextprotocol/servers/tree/main/src/gitlab
