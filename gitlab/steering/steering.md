# GitLab MCP Server Steering Guide

This steering file covers the GitLab MCP server to manage projects, merge requests, issues, CI/CD pipelines, and code collaboration.

## When to Use the GitLab MCP Server

Use GitLab MCP tools when you need to:
- **Manage merge requests**: Create, review, approve, and merge MRs
- **Track issues**: Create, search, update, and manage issues with boards
- **Monitor pipelines**: Trigger, check status, and debug CI/CD jobs
- **Search code**: Find patterns across projects and groups
- **Manage branches**: Create branches and push code
- **Collaborate**: Add comments, manage labels, and track milestones

## Core Principles

### 1. Follow GitLab Flow
Use feature branches → merge requests → main → deploy. Never push directly to protected branches.

### 2. Pipeline First
Always check pipeline status before merging. Failed pipelines indicate problems that need fixing.

### 3. Use Scoped Labels
GitLab's scoped labels (e.g., `priority::high`) ensure mutual exclusivity within a scope.

---

## Merge Request Best Practices

### MR Title Format
Follow conventional commits:
```
feat: add user authentication with OAuth2
fix: handle race condition in order processing
docs: update deployment guide for Kubernetes
refactor: extract payment validation into service
test: add integration tests for notification system
chore: upgrade Rails to 7.1
```

### MR Description Template
```markdown
## Summary
Brief description of what this MR does and why.

## Changes
- Implemented OAuth2 login flow
- Added token refresh mechanism
- Created auth middleware

## Testing
- [x] Unit tests pass (`bundle exec rspec`)
- [x] Integration tests pass
- [x] Manual testing completed

## Screenshots (if applicable)
Before: ...
After: ...

## Related Issues
Closes #123
Related to #456

## Checklist
- [x] Code follows project style guidelines
- [x] Tests added for new functionality
- [x] Documentation updated
- [ ] Migration included (if DB changes)
```

### MR Workflow

```javascript
// Step 1: Create branch
create_branch({
  "project_id": "mygroup/myproject",
  "branch": "feature/oauth-login",
  "ref": "main"
})

// Step 2: Push code
create_or_update_file({
  "project_id": "mygroup/myproject",
  "file_path": "app/controllers/auth_controller.rb",
  "content": "...",
  "commit_message": "feat: add OAuth2 authentication controller",
  "branch": "feature/oauth-login"
})

// Step 3: Create MR
create_merge_request({
  "project_id": "mygroup/myproject",
  "title": "feat: add OAuth2 authentication",
  "source_branch": "feature/oauth-login",
  "target_branch": "main",
  "description": "## Summary\nAdds OAuth2 login flow...",
  "reviewer_ids": [42, 43],
  "labels": "feature,auth,priority::high"
})

// Step 4: Check pipeline
list_pipelines({
  "project_id": "mygroup/myproject",
  "ref": "feature/oauth-login"
})

// Step 5: Merge when ready
merge_merge_request({
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99,
  "squash": true,
  "should_remove_source_branch": true
})
```

---

## CI/CD Pipeline Management

### Checking Pipeline Status

```javascript
// List recent pipelines
list_pipelines({
  "project_id": "mygroup/myproject",
  "status": "failed"
})

// Get pipeline details
get_pipeline({
  "project_id": "mygroup/myproject",
  "pipeline_id": 12345
})

// List jobs in a pipeline
list_pipeline_jobs({
  "project_id": "mygroup/myproject",
  "pipeline_id": 12345
})

// Get failed job log
get_job_log({
  "project_id": "mygroup/myproject",
  "job_id": 67890
})
```

### Pipeline States
| Status | Description |
|--------|-------------|
| `created` | Pipeline created, not yet started |
| `waiting_for_resource` | Waiting for runner |
| `preparing` | Being prepared |
| `pending` | Waiting to run |
| `running` | Currently executing |
| `success` | All jobs passed |
| `failed` | One or more jobs failed |
| `canceled` | Manually cancelled |
| `skipped` | Skipped due to rules |
| `manual` | Waiting for manual trigger |
| `scheduled` | Scheduled for later |

### Debugging Failed Pipelines

1. **List pipelines for the branch:**
```javascript
list_pipelines({
  "project_id": "mygroup/myproject",
  "ref": "feature/my-branch",
  "status": "failed"
})
```

2. **Get pipeline jobs:**
```javascript
list_pipeline_jobs({
  "project_id": "mygroup/myproject",
  "pipeline_id": 12345
})
```

3. **Find the failed job:**
Look for jobs with `status: "failed"` in the response.

4. **Get job log:**
```javascript
get_job_log({
  "project_id": "mygroup/myproject",
  "job_id": failedJobId
})
```

5. **Common failure patterns:**
- Test failures → Check test output in log
- Lint errors → Look for style violations
- Build errors → Check compilation output
- Docker errors → Check Dockerfile and registry access
- Deploy errors → Check credentials and permissions

---

## Issue Management

### Creating Issues

**Bug report:**
```javascript
create_issue({
  "project_id": "mygroup/myproject",
  "title": "Bug: API returns 500 on concurrent checkout requests",
  "description": "## Environment\n- Production (v2.3.1)\n- Affects: checkout-service\n\n## Steps to Reproduce\n1. Send 10 concurrent POST /checkout requests\n2. Observe intermittent 500 errors\n\n## Expected\nAll requests succeed (or graceful 429)\n\n## Actual\n3-4 requests fail with 500 Internal Server Error\n\n## Logs\n```\nActiveRecord::Deadlock: Mysql2::Error: Deadlock found\n```",
  "labels": "bug,priority::critical,service::checkout",
  "weight": 8
})
```

**Feature request:**
```javascript
create_issue({
  "project_id": "mygroup/myproject",
  "title": "Feature: Add bulk order import via CSV",
  "description": "## Problem\nCustomers with large orders must add items individually.\n\n## Proposal\nAdd CSV upload endpoint for bulk order creation.\n\n## Acceptance Criteria\n- [ ] CSV parsing with validation\n- [ ] Error reporting per row\n- [ ] Max 1000 items per upload\n- [ ] Background processing for large files",
  "labels": "feature,priority::medium,service::orders",
  "weight": 13
})
```

### Scoped Labels

GitLab scoped labels use `::` separator. Only one label per scope can be applied:

```
priority::critical    # Only one priority at a time
priority::high
priority::medium
priority::low

workflow::backlog     # Only one workflow state
workflow::ready
workflow::in-progress
workflow::review
workflow::done

service::checkout    # Can have multiple service labels
service::payment
service::inventory

type::bug
type::feature
type::tech-debt
type::documentation
```

### Issue Boards

Issues move through board columns based on scoped labels:
```
Backlog → Ready → In Progress → Review → Done
(workflow::backlog → workflow::ready → workflow::in-progress → workflow::review → workflow::done)
```

---

## Code Search

### Search Patterns

```javascript
// Find function definitions
search_repositories({ "search": "def authenticate" })

// Find configuration
search_repositories({ "search": "DATABASE_URL" })

// Find specific file types
search_repositories({ "search": "Dockerfile" })
```

### File Operations

```javascript
// Read a file
get_file_contents({
  "project_id": "mygroup/myproject",
  "file_path": "config/database.yml",
  "ref": "main"
})

// Create/update a file
create_or_update_file({
  "project_id": "mygroup/myproject",
  "file_path": "docs/API.md",
  "content": "# API Documentation\n...",
  "commit_message": "docs: add API documentation",
  "branch": "docs/api-docs"
})
```

---

## Project Organization

### Group Structure
```
mycompany/
├── platform/
│   ├── api-gateway
│   ├── auth-service
│   └── shared-libs
├── services/
│   ├── checkout
│   ├── payment
│   └── inventory
└── infrastructure/
    ├── terraform
    ├── helm-charts
    └── monitoring
```

### Branch Protection
Protected branches (main, release/*) should require:
- Merge request approval (1-2 reviewers)
- Passing CI pipeline
- No force push
- Code owner approval (for critical paths)

---

## Merge Strategies

| Strategy | When to Use | Command |
|----------|-------------|---------|
| Merge commit | Preserve full history | `squash: false` |
| Squash | Clean up WIP commits | `squash: true` |
| Fast-forward | Linear history (if possible) | Configured in project settings |

### Recommended: Squash Merge
```javascript
merge_merge_request({
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99,
  "squash": true,
  "should_remove_source_branch": true,
  "merge_commit_message": "feat: add OAuth2 authentication (#99)"
})
```

---

## Common Workflows

### Workflow 1: Bug Fix

```javascript
// 1. Create branch from main
create_branch({
  "project_id": "mygroup/myproject",
  "branch": "fix/checkout-deadlock",
  "ref": "main"
})

// 2. Push fix
create_or_update_file({
  "project_id": "mygroup/myproject",
  "file_path": "app/services/checkout_service.rb",
  "content": "...",
  "commit_message": "fix: add row-level locking to prevent checkout deadlock",
  "branch": "fix/checkout-deadlock"
})

// 3. Create MR linked to issue
create_merge_request({
  "project_id": "mygroup/myproject",
  "title": "fix: add row-level locking to prevent checkout deadlock",
  "source_branch": "fix/checkout-deadlock",
  "target_branch": "main",
  "description": "Closes #456\n\nAdds `FOR UPDATE` lock on inventory rows during checkout to prevent deadlocks under concurrent load.",
  "labels": "bug,priority::critical"
})

// 4. Monitor pipeline
list_pipelines({
  "project_id": "mygroup/myproject",
  "ref": "fix/checkout-deadlock"
})

// 5. After approval and green pipeline, merge
merge_merge_request({
  "project_id": "mygroup/myproject",
  "merge_request_iid": 100,
  "squash": true,
  "should_remove_source_branch": true
})
```

### Workflow 2: MR Review

```javascript
// 1. Get MR details
get_merge_request({
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99
})

// 2. Review the diff
get_merge_request_diffs({
  "project_id": "mygroup/myproject",
  "merge_request_iid": 99
})

// 3. Check pipeline status
list_pipelines({
  "project_id": "mygroup/myproject",
  "ref": "feature/oauth-login"
})

// 4. If pipeline failed, check logs
list_pipeline_jobs({
  "project_id": "mygroup/myproject",
  "pipeline_id": 12345
})

// 5. Add review comment
create_note({
  "project_id": "mygroup/myproject",
  "noteable_type": "MergeRequest",
  "noteable_iid": 99,
  "body": "Looks good! One suggestion: consider adding rate limiting to the token endpoint."
})
```

---

## Troubleshooting

### Pipeline Keeps Failing
1. Check job logs for specific error messages
2. Verify CI/CD variables are set correctly
3. Check if runner is available and has correct tags
4. Verify Docker images are accessible
5. Check for flaky tests (retry the pipeline)

### MR Cannot Be Merged
1. Check for merge conflicts (rebase or merge main into branch)
2. Verify pipeline is passing
3. Check if required approvals are met
4. Verify branch protection rules
5. Check if there are unresolved threads

### Permission Denied
1. Verify PAT has `api` scope
2. Check project membership and role
3. Verify group-level permissions
4. Check if project is archived

---

## Summary Checklist

For effective GitLab usage:
- ✅ Follow GitLab Flow (feature branch → MR → main)
- ✅ Use conventional commit format for MR titles
- ✅ Include descriptive MR descriptions
- ✅ Use scoped labels for structured categorization
- ✅ Check pipeline status before merging
- ✅ Use squash merge for clean history
- ✅ Delete source branches after merge
- ✅ Link MRs to issues with "Closes #N"
- ✅ Set reviewers for accountability
- ✅ Use weights for sprint planning
- ✅ Monitor pipeline jobs for failures
- ✅ Use draft MRs for work-in-progress

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `GITLAB_PERSONAL_ACCESS_TOKEN` values in responses
- When referencing tokens, use placeholder names (e.g., "your GitLab token") not actual values
- Do not include tokens in commit messages, file contents, or MR descriptions

### Repository and Code Safety
- **Never push secrets to repositories** - if file content contains API keys, passwords, or tokens, refuse and warn the user
- **Never push directly to protected branches** - always use feature branches and MRs
- **Do not create public projects** unless the user explicitly requests and confirms
- **Do not delete projects or branches** without explicit user confirmation
- When using `create_or_update_file`, verify content does not contain hardcoded credentials or private keys
- Do not modify `.gitlab-ci.yml` without explicit user approval - CI/CD changes can have security implications

### Data Sensitivity
- Code search results may contain sensitive patterns - summarize rather than reproduce large blocks
- Do not expose private project names, internal URLs, or infrastructure details
- Treat group membership and project structure as potentially sensitive
- Pipeline job logs may contain secrets - summarize errors rather than reproducing full logs verbatim

### Access Control
- Only access projects the configured token has permissions for
- Do not attempt to enumerate groups, members, or permissions beyond what's needed
- If an operation returns 403/404, report the error without retrying
- Do not attempt to bypass merge request approval rules or protected branch settings
- Respect CODEOWNERS - suggest appropriate reviewers

## Anti-Hallucination Guardrails

### API Accuracy
- **Only use documented tool parameters** - do not invent parameter names or values
- **Do not fabricate project IDs, MR IIDs, or issue IIDs** - always search or list first to confirm they exist
- **Do not assume branch names** - verify branches exist before creating MRs
- **Do not invent pipeline IDs or job IDs** - always list pipelines first
- **Project IDs can be numeric or path-based** (e.g., "mygroup/myproject") - use the format the user provides

### Result Interpretation
- **Never invent API responses** - if a tool hasn't been called, say "I need to check this" rather than guessing
- **Do not assume MR status** - always check current state before suggesting merge actions
- **Do not assume pipeline status** - verify before claiming a pipeline passed or failed
- **If a search returns no results**, report that clearly rather than speculating
- **Do not fabricate commit SHAs, usernames, or timestamps**

### Tool Capability Boundaries
- Do not claim ability to approve MRs on behalf of other users
- Do not claim ability to retry or cancel pipelines unless the tool supports it
- Do not claim ability to manage CI/CD variables, runners, or project settings
- Clearly state when an action requires the user to perform it in the GitLab UI

## Operational Optimization Guardrails

### API Rate Limiting
- **GitLab has rate limits** (varies by plan) - be mindful of call volume
- **Use pagination wisely** - start with small `per_page` values (10-20), increase only if needed
- **Cache references** - once you have a project ID, MR IID, or pipeline ID, reuse it
- **Avoid listing all items** when a specific query would suffice

### Request Efficiency
- **Use specific filters** - filter by state, labels, or branch rather than listing everything
- **Minimize diff fetches** - `get_merge_request_diffs` can return large payloads; only fetch when reviewing
- **Don't repeatedly check pipeline status** - check once, wait, then check again if needed
- **Use `ref` parameter** when listing pipelines to scope to a specific branch

### Workflow Efficiency
- **Create branch + push + MR in sequence** - minimize intermediate operations
- **Link issues at MR creation** - use "Closes #N" in description rather than updating later
- **Use draft MRs** for work-in-progress - avoids triggering unnecessary reviews and notifications
- **Squash on merge** - reduces the need for clean commit history on feature branches

## Cost Optimization Guardrails

### API Usage
- **Minimize API calls** - plan the workflow before executing
- **Avoid redundant operations** - if you already have the information, don't query again
- **Batch awareness** - creating MRs and issues triggers notifications; be intentional

### CI/CD Cost Awareness
- **Draft MRs may skip CI** in some configurations - use drafts for WIP to avoid unnecessary pipeline costs
- **Don't create throwaway MRs** - each MR may trigger CI pipelines that consume runner minutes
- **Consider pipeline costs** - GitLab CI/CD minutes are limited on SaaS plans
- **Avoid force-pushing repeatedly** - each push triggers a new pipeline run
- **Use `rules:` and `only:`/`except:`** awareness - suggest efficient pipeline configurations

### Project Hygiene
- **Delete source branches after merge** - reduces clutter
- **Close stale issues and MRs** - reduces noise
- **Use scoped labels** - enables efficient board management and filtering
