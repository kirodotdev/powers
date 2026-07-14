# GitHub MCP Server Steering Guide

This steering file covers the GitHub MCP server to manage repositories, pull requests, issues, code search, and collaboration workflows.

## When to Use the GitHub MCP Server

Use GitHub MCP tools when you need to:
- **Manage pull requests**: Create, review, merge, and track PRs
- **Track issues**: Create, search, update, and manage issues
- **Search code**: Find patterns, usage, and implementations across repos
- **Manage repositories**: Create repos, branches, and push files
- **Collaborate**: Add comments, request reviews, and manage labels
- **Investigate bugs**: Search issues, code, and commit history

## Core Principles

### 1. Search Before Creating
Always search for existing issues or PRs before creating new ones to avoid duplicates.

### 2. Link Everything
Reference issues in PRs with "Closes #N" or "Refs #N". Link related issues together.

### 3. Use Conventional Commits
Structure PR titles and commit messages with prefixes: feat:, fix:, docs:, refactor:, test:, chore:

---

## Search Syntax Reference

### Code Search

**Qualifiers:**
| Qualifier | Description | Example |
|-----------|-------------|---------|
| `org:` | Organization | `org:myorg useAuth` |
| `repo:` | Specific repo | `repo:myorg/api-service` |
| `path:` | File path | `path:src/auth/` |
| `filename:` | File name | `filename:*.test.ts` |
| `extension:` | File extension | `extension:py` |
| `language:` | Language | `language:typescript` |
| `"exact"` | Exact phrase | `"function authenticate"` |
| `NOT` | Exclude | `useAuth NOT test` |

**Examples:**
```
# Find authentication usage in TypeScript files
org:myorg useAuth filename:*.ts NOT test

# Find API endpoint definitions
repo:myorg/backend "app.get(" path:src/routes/

# Find environment variable usage
org:myorg process.env.DATABASE_URL

# Find import patterns
repo:myorg/frontend "import { useAuth }" extension:tsx

# Find TODO comments
org:myorg TODO language:typescript
```

### Issue/PR Search

**Qualifiers:**
| Qualifier | Description | Example |
|-----------|-------------|---------|
| `is:open` / `is:closed` | State | `is:open` |
| `is:issue` / `is:pr` | Type | `is:pr` |
| `is:merged` / `is:unmerged` | Merge status | `is:merged` |
| `is:draft` | Draft PRs | `is:draft` |
| `label:` | Label filter | `label:bug` |
| `assignee:` | Assigned to | `assignee:username` |
| `author:` | Created by | `author:username` |
| `reviewer:` | PR reviewer | `reviewer:username` |
| `milestone:` | Milestone | `milestone:"v2.0"` |
| `created:` | Creation date | `created:>2024-01-01` |
| `updated:` | Last updated | `updated:>2024-01-15` |
| `closed:` | Close date | `closed:>2024-01-01` |
| `comments:` | Comment count | `comments:>5` |
| `sort:` | Sort order | `sort:created-desc` |
| `no:` | Missing field | `no:assignee` |
| `linked:pr` | Has linked PR | `linked:pr` |
| `review:` | Review status | `review:required` |

**Examples:**
```
# Open bugs in my repo
repo:myorg/api is:open is:issue label:bug

# My open PRs
is:open is:pr author:@me

# PRs awaiting my review
is:open is:pr reviewer:@me review:required

# High priority unassigned issues
repo:myorg/api is:open label:priority:high no:assignee

# Recently created issues
repo:myorg/api is:open is:issue sort:created-desc created:>2024-01-01

# Stale PRs (no updates in 7 days)
repo:myorg/api is:open is:pr updated:<2024-01-08

# Issues with many comments (potentially complex)
repo:myorg/api is:open is:issue comments:>10

# Merged PRs this week
repo:myorg/api is:merged merged:>2024-01-08
```

### Repository Search

**Qualifiers:**
| Qualifier | Description | Example |
|-----------|-------------|---------|
| `language:` | Primary language | `language:typescript` |
| `stars:` | Star count | `stars:>1000` |
| `forks:` | Fork count | `forks:>100` |
| `topic:` | Topic tag | `topic:react` |
| `org:` | Organization | `org:myorg` |
| `archived:` | Archive status | `archived:false` |
| `is:public` / `is:private` | Visibility | `is:public` |
| `created:` | Creation date | `created:>2024-01-01` |
| `pushed:` | Last push | `pushed:>2024-01-01` |
| `size:` | Repo size (KB) | `size:>1000` |

---

## Pull Request Workflows

### Creating Effective PRs

**Title format:**
```
feat: add user authentication with JWT
fix: handle null pointer in checkout flow
docs: update API documentation for v2
refactor: extract payment validation logic
test: add integration tests for order service
chore: upgrade dependencies to latest versions
```

**Description template:**
```markdown
## Summary
Brief description of what this PR does and why.

## Changes
- Added JWT token generation and validation
- Created auth middleware for protected routes
- Added refresh token rotation

## Testing
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual testing with Postman

## Screenshots (if UI changes)
Before: ...
After: ...

## Related Issues
Closes #123
Refs #456
```

### PR Review Workflow

```javascript
// Step 1: List PRs awaiting review
const prs = search_issues({
  "q": "repo:myorg/api is:open is:pr reviewer:@me review:required"
})

// Step 2: Get PR details
const pr = get_pull_request({
  "owner": "myorg", "repo": "api", "pull_number": 42
})

// Step 3: Review the diff
const diff = get_pull_request_diff({
  "owner": "myorg", "repo": "api", "pull_number": 42
})

// Step 4: Check existing reviews
const reviews = get_pull_request_reviews({
  "owner": "myorg", "repo": "api", "pull_number": 42
})

// Step 5: Submit review
const review = create_pull_request_review({
  "owner": "myorg", "repo": "api", "pull_number": 42,
  "event": "APPROVE",  // or "REQUEST_CHANGES" or "COMMENT"
  "body": "LGTM! Clean implementation."
})
```

### Merge Strategies

| Method | When to Use | Result |
|--------|-------------|--------|
| `merge` | Preserve full branch history | Merge commit |
| `squash` | Clean up messy commits | Single commit |
| `rebase` | Linear history, clean commits | No merge commit |

---

## Issue Management Workflows

### Bug Report Template
```javascript
create_issue({
  "owner": "myorg", "repo": "api",
  "title": "Bug: Checkout fails with special characters in address",
  "body": "## Environment\n- Production\n- API v2.3.1\n\n## Steps to Reproduce\n1. Add item to cart\n2. Enter address with `&` or `#` characters\n3. Submit checkout\n\n## Expected\nOrder is placed successfully\n\n## Actual\nHTTP 400 Bad Request\n\n## Additional Context\nStarted after deploy on Jan 15",
  "labels": ["bug", "priority:high", "checkout"],
  "assignees": ["developer1"]
})
```

### Feature Request Template
```javascript
create_issue({
  "owner": "myorg", "repo": "api",
  "title": "Feature: Add bulk order import via CSV",
  "body": "## Problem\nCustomers with large orders must add items one by one.\n\n## Proposed Solution\nAllow CSV upload with columns: SKU, quantity, notes\n\n## Acceptance Criteria\n- [ ] CSV parsing with validation\n- [ ] Error reporting for invalid rows\n- [ ] Maximum 1000 items per upload\n- [ ] Progress indicator for large files",
  "labels": ["enhancement", "priority:medium"]
})
```

### Issue Triage Workflow

```javascript
// Step 1: Find untriaged issues
const untriaged = search_issues({
  "q": "repo:myorg/api is:open is:issue no:label created:>2024-01-01"
})

// Step 2: Find unassigned high-priority issues
const unassigned = search_issues({
  "q": "repo:myorg/api is:open is:issue label:priority:high no:assignee"
})

// Step 3: Find stale issues (no updates in 30 days)
const stale = search_issues({
  "q": "repo:myorg/api is:open is:issue updated:<2023-12-15"
})
```

---

## Code Search Patterns

### Finding Usage Patterns
```javascript
// Find all uses of a function
search_code({ "q": "org:myorg validatePayment language:typescript" })

// Find configuration patterns
search_code({ "q": "repo:myorg/api DATABASE_URL filename:.env*" })

// Find test patterns
search_code({ "q": "repo:myorg/api describe( filename:*.test.ts path:src/" })

// Find API endpoint definitions
search_code({ "q": "repo:myorg/api router.post path:src/routes" })

// Find dependency usage
search_code({ "q": "org:myorg \"from 'lodash'\" extension:ts" })
```

### Finding Security Issues
```javascript
// Hardcoded secrets (should be in env vars)
search_code({ "q": "org:myorg password= NOT .env NOT test" })

// SQL injection risks
search_code({ "q": "org:myorg \"query(\" + language:javascript" })

// Unsafe eval usage
search_code({ "q": "org:myorg eval( language:javascript NOT test" })
```

---

## Branch Management

### Branch Naming Conventions
```
feature/TICKET-123-add-auth       # Feature branches
fix/TICKET-456-null-pointer       # Bug fix branches
hotfix/critical-security-patch    # Production hotfixes
release/v2.0.0                    # Release branches
docs/update-api-docs              # Documentation
refactor/extract-payment-logic    # Refactoring
```

### Branch Workflow
```javascript
// Step 1: Create feature branch
create_branch({
  "owner": "myorg", "repo": "api",
  "branch": "feature/add-order-history",
  "from_branch": "main"
})

// Step 2: Push implementation
push_files({
  "owner": "myorg", "repo": "api",
  "branch": "feature/add-order-history",
  "files": [
    {"path": "src/routes/orders.ts", "content": "..."},
    {"path": "src/tests/orders.test.ts", "content": "..."}
  ],
  "message": "feat: add order history endpoint"
})

// Step 3: Create PR
create_pull_request({
  "owner": "myorg", "repo": "api",
  "title": "feat: add order history endpoint",
  "head": "feature/add-order-history",
  "base": "main"
})
```

---

## Label Taxonomy

### Recommended Labels

**Type:**
- `bug` - Something isn't working
- `enhancement` - New feature request
- `documentation` - Documentation improvements
- `question` - Further information requested
- `tech-debt` - Technical debt cleanup

**Priority:**
- `priority:critical` - Production down
- `priority:high` - Major feature/bug
- `priority:medium` - Normal priority
- `priority:low` - Nice to have

**Status:**
- `needs-triage` - Needs initial review
- `in-progress` - Being worked on
- `blocked` - Blocked by dependency
- `needs-review` - Ready for review
- `wontfix` - Won't be addressed

**Area:**
- `frontend` - UI/UX related
- `backend` - Server-side
- `infrastructure` - DevOps/infra
- `security` - Security related
- `performance` - Performance related

---

## Automation Patterns

### Auto-close Issues from PRs
Use keywords in PR body or commit messages:
- `Closes #123` - Closes issue when PR is merged
- `Fixes #123` - Same as Closes
- `Resolves #123` - Same as Closes
- `Refs #123` - References without closing

### PR Templates
Create `.github/PULL_REQUEST_TEMPLATE.md` in your repo for consistent PR descriptions.

### Issue Templates
Create `.github/ISSUE_TEMPLATE/` directory with templates for bugs, features, etc.

---

## Troubleshooting

### Search Returns No Results
1. Check repository name and organization
2. Verify search syntax (quotes for exact phrases)
3. Try broader search terms
4. Check if repo is private (needs appropriate token scope)

### PR Creation Fails
1. Verify branch exists and has commits ahead of base
2. Check branch names are correct
3. Verify token has `repo` scope
4. Check if branch protection rules block creation

### Permission Denied
1. Verify PAT has required scopes
2. Check if repo requires specific team membership
3. Verify organization SSO is authorized for the token
4. Check if fine-grained token has access to the specific repo

---

## Summary Checklist

For effective GitHub usage:
- ✅ Search before creating (avoid duplicates)
- ✅ Use conventional commit format for PR titles
- ✅ Include descriptive PR body with context
- ✅ Link PRs to issues with "Closes #N"
- ✅ Use labels consistently for categorization
- ✅ Request reviews from appropriate team members
- ✅ Check CI status before merging
- ✅ Use draft PRs for work-in-progress
- ✅ Keep PRs small and focused
- ✅ Use code search to find patterns before implementing

---

## Security Guardrails

### Credential Protection
- **NEVER** log, echo, or expose `GITHUB_PERSONAL_ACCESS_TOKEN` values in responses
- When referencing tokens, use placeholder names (e.g., "your GitHub token") not actual values
- Do not include tokens in URLs, commit messages, or file contents

### Repository and Code Safety
- **Never push secrets to repositories** - if file content contains API keys, passwords, or tokens, refuse and warn the user
- **Never push directly to `main` or `master`** - always use feature branches and PRs
- **Do not create public repositories** unless the user explicitly requests it and confirms
- **Do not delete repositories or branches** without explicit user confirmation
- When using `push_files`, verify content does not contain hardcoded credentials, private keys, or connection strings
- Do not modify `.github/workflows/` files without explicit user approval - CI/CD changes can have security implications

### Data Sensitivity
- Code search results may contain sensitive patterns - do not reproduce large blocks of code that appear to contain secrets
- When presenting search results, summarize file paths and patterns rather than reproducing full file contents
- Do not expose private repository names, internal URLs, or infrastructure details to unauthorized contexts
- Treat organization membership and team structure as sensitive information

### Access Control
- Only access repositories the configured token has permissions for
- Do not attempt to enumerate organizations, teams, or members beyond what's needed
- If an operation returns 403/404, report the error without retrying with escalated permissions
- Do not attempt to bypass branch protection rules or required reviews
- Respect CODEOWNERS files - suggest appropriate reviewers based on changed paths

## Anti-Hallucination Guardrails

### API Accuracy
- **Only use documented tool parameters** - do not invent parameter names or values
- **Do not fabricate repository names, issue numbers, or PR numbers** - always search or list first to confirm they exist
- **Do not assume branch names** - verify branches exist before creating PRs or pushing files
- **Do not invent GitHub search qualifiers** - only use documented qualifiers (is:, label:, author:, repo:, org:, language:, etc.)

### Result Interpretation
- **Never invent API responses** - if a tool hasn't been called, say "I need to check this" rather than guessing
- **Do not assume PR status** - always check current state before suggesting merge or review actions
- **Do not assume issue state** - verify whether issues are open/closed before suggesting updates
- **If a search returns no results**, report that clearly rather than speculating about what might exist
- **Do not fabricate commit SHAs, user handles, or timestamps**

### Tool Capability Boundaries
- Do not claim ability to approve PRs on behalf of other users
- Do not claim ability to trigger GitHub Actions workflows directly (unless the tool supports it)
- Do not claim ability to manage GitHub Apps, webhooks, or organization settings
- Clearly state when an action requires the user to perform it in the GitHub UI

## Operational Optimization Guardrails

### API Rate Limiting
- **GitHub has strict rate limits** (5000 requests/hour for authenticated users) - be mindful of call volume
- **Batch operations when possible** - use `push_files` for multiple files instead of individual `create_or_update_file` calls
- **Use `perPage` parameter** to control result sizes - start with 10-20, increase only if needed
- **Cache entity references** - once you have a repo name, issue number, or PR number, reuse it without re-searching
- **Avoid paginating through all results** unless specifically needed - use search with specific filters instead

### Request Efficiency
- **Search before listing** - `search_issues` with specific qualifiers is more efficient than `list_issues` with client-side filtering
- **Use specific queries** - `repo:owner/repo is:open is:pr` is better than listing all PRs and filtering
- **Minimize diff fetches** - `get_pull_request_diff` can return large payloads; only fetch when reviewing
- **Don't repeatedly check PR status** - check once, take action, then verify if needed

### Workflow Efficiency
- **Create branch + push + PR in sequence** - don't create unnecessary intermediate operations
- **Link issues to PRs at creation time** - use `work_item_ids` or "Closes #N" in description rather than updating later
- **Use draft PRs** for work-in-progress - avoids triggering unnecessary CI runs and review notifications

## Cost Optimization Guardrails

### API Usage
- **Minimize API calls** - plan the workflow before executing, determine minimum calls needed
- **Avoid redundant searches** - if you already found the information, don't search again
- **Use webhooks awareness** - creating PRs, issues, and comments triggers notifications; be intentional about what you create
- **Batch file operations** - `push_files` with multiple files in one commit is one API call vs. N calls for individual files

### CI/CD Cost Awareness
- **Draft PRs don't trigger all CI** in many configurations - use drafts for WIP to avoid unnecessary build costs
- **Don't create throwaway PRs** - each PR may trigger CI pipelines that consume compute resources
- **Consider PR size** - smaller, focused PRs are cheaper to build and test than large ones
- **Avoid force-pushing repeatedly** - each push may trigger a new CI run

### Repository Hygiene
- **Delete branches after merge** - reduces clutter and potential confusion
- **Close stale issues and PRs** - reduces noise for the team
- **Use labels efficiently** - well-labeled issues reduce time spent searching and triaging
