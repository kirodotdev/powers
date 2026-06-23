---
name: "github"
displayName: "GitHub"
description: "Manage repositories, issues, pull requests, workflows, code search, and collaboration on GitHub directly from your IDE"
keywords: ["github", "git", "repository", "pull-request", "issues", "actions", "ci", "cd", "code-review", "collaboration", "workflows"]
author: "Community"
---

# GitHub Power

## Overview

The GitHub Power connects to GitHub's platform for repository management, code collaboration, issue tracking, CI/CD workflows, and code search. Work with GitHub directly from your IDE.

**Key capabilities:**
- **Repository Management**: Create, fork, search, and manage repositories
- **Pull Requests**: Create, review, merge PRs with full diff and comment support
- **Issues**: Create, search, update, and manage issues with labels and assignees
- **Code Search**: Search code across repositories with advanced query syntax
- **Actions & Workflows**: Trigger and monitor CI/CD workflows
- **Branch Management**: Create, protect, and manage branches
- **File Operations**: Read, create, and update files directly in repositories
- **Collaboration**: Manage teams, reviews, and notifications

**Authentication**: Requires a GitHub Personal Access Token (PAT).

## Onboarding

### Prerequisites

1. **GitHub account** - GitHub.com or GitHub Enterprise
2. **Personal Access Token** - Fine-grained token with appropriate repository permissions
3. **Node.js 18+** - Required to run the MCP server via npx

### Quick Start

1. Install the power in Kiro
2. Replace the placeholder in `mcp.json` with your GitHub PAT
3. Test with: *"List my open pull requests"* or *"Search issues in my repo"*

### MCP Config Placeholders

Before using this power, replace the following placeholder in `mcp.json`:

- **`YOUR_GITHUB_TOKEN`**: A GitHub Personal Access Token.
 - **How to get it:**
    1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
    2. Click "Generate new token"
    3. Select the repositories you want to grant access to
    4. Set permissions: Contents (Read & Write), Issues (Read & Write), Pull requests (Read & Write), Metadata (Read)
    5. Click "Generate token" and copy the value (starts with `github_pat_`)

## Available Steering Files

- **steering/steering.md** - Search syntax, PR workflows, issue management, code search patterns, and branch conventions

## Available MCP Servers

### github
**Package:** `@modelcontextprotocol/server-github`
**Connection:** stdio via npx

**Tools:**

1. **create_or_update_file** - Create or update a file in a repository
  - Required: `owner` (string), `repo` (string), `path` (string), `content` (string), `message` (string), `branch` (string)
  - Optional: `sha` (string) - Required for updates
  - Returns: File commit details

2. **search_repositories** - Search GitHub repositories
  - Required: `query` (string) - Search query
  - Optional: `page` (number), `perPage` (number)
  - Returns: Matching repositories with metadata

3. **create_repository** - Create a new repository
  - Required: `name` (string)
  - Optional: `description` (string), `private` (boolean), `autoInit` (boolean)
  - Returns: Created repository details

4. **get_file_contents** - Get file or directory contents
  - Required: `owner` (string), `repo` (string), `path` (string)
  - Optional: `branch` (string)
  - Returns: File content (base64) or directory listing

5. **push_files** - Push multiple files in a single commit
  - Required: `owner` (string), `repo` (string), `branch` (string), `files` (array), `message` (string)
  - Returns: Commit details

6. **create_issue** - Create a new issue
  - Required: `owner` (string), `repo` (string), `title` (string)
  - Optional: `body` (string), `assignees` (array), `labels` (array), `milestone` (number)
  - Returns: Created issue details

7. **create_pull_request** - Create a pull request
  - Required: `owner` (string), `repo` (string), `title` (string), `head` (string), `base` (string)
  - Optional: `body` (string), `draft` (boolean), `maintainer_can_modify` (boolean)
  - Returns: Created PR details

8. **fork_repository** - Fork a repository
  - Required: `owner` (string), `repo` (string)
  - Optional: `organization` (string)
  - Returns: Forked repository details

9. **create_branch** - Create a new branch
  - Required: `owner` (string), `repo` (string), `branch` (string)
  - Optional: `from_branch` (string) - Source branch (default: repo default branch)
  - Returns: Branch reference details

10. **list_issues** - List issues in a repository
   - Required: `owner` (string), `repo` (string)
   - Optional: `state` (string), `labels` (string), `sort` (string), `direction` (string), `page` (number)
   - Returns: List of issues

11. **update_issue** - Update an existing issue
   - Required: `owner` (string), `repo` (string), `issue_number` (number)
   - Optional: `title` (string), `body` (string), `state` (string), `labels` (array), `assignees` (array)
   - Returns: Updated issue details

12. **add_issue_comment** - Add a comment to an issue or PR
   - Required: `owner` (string), `repo` (string), `issue_number` (number), `body` (string)
   - Returns: Created comment details

13. **search_code** - Search code across repositories
   - Required: `q` (string) - Search query
   - Optional: `page` (number), `perPage` (number)
   - Returns: Matching code with file paths and snippets

14. **search_issues** - Search issues and pull requests
   - Required: `q` (string) - Search query
   - Optional: `sort` (string), `order` (string), `page` (number), `perPage` (number)
   - Returns: Matching issues/PRs

15. **search_users** - Search GitHub users
   - Required: `q` (string) - Search query
   - Optional: `page` (number), `perPage` (number)
   - Returns: Matching users

16. **list_commits** - List commits in a repository
   - Required: `owner` (string), `repo` (string)
   - Optional: `sha` (string), `page` (number), `perPage` (number)
   - Returns: Commit history

17. **get_issue** - Get details of a specific issue
   - Required: `owner` (string), `repo` (string), `issue_number` (number)
   - Returns: Full issue details with comments

18. **get_pull_request** - Get details of a pull request
   - Required: `owner` (string), `repo` (string), `pull_number` (number)
   - Returns: Full PR details with diff stats

19. **list_pull_requests** - List pull requests
   - Required: `owner` (string), `repo` (string)
   - Optional: `state` (string), `head` (string), `base` (string), `sort` (string)
   - Returns: List of pull requests

20. **get_pull_request_diff** - Get the diff of a pull request
   - Required: `owner` (string), `repo` (string), `pull_number` (number)
   - Returns: PR diff content

21. **merge_pull_request** - Merge a pull request
   - Required: `owner` (string), `repo` (string), `pull_number` (number)
   - Optional: `commit_title` (string), `commit_message` (string), `merge_method` (string)
   - Returns: Merge result

22. **get_pull_request_reviews** - Get reviews for a PR
   - Required: `owner` (string), `repo` (string), `pull_number` (number)
   - Returns: List of reviews with status

23. **create_pull_request_review** - Submit a review on a PR
   - Required: `owner` (string), `repo` (string), `pull_number` (number), `event` (string)
   - Optional: `body` (string), `comments` (array)
   - Returns: Created review

## Tool Usage Examples

### Repository Management

**Search repositories:**
```javascript
usePower("github", "github", "search_repositories", {
  "query": "language:typescript stars:>1000 topic:react"
})
```

**Create a repository:**
```javascript
usePower("github", "github", "create_repository", {
  "name": "my-new-project",
  "description": "A new TypeScript project",
  "private": true,
  "autoInit": true
})
```

### Pull Request Workflow

**Create a PR:**
```javascript
usePower("github", "github", "create_pull_request", {
  "owner": "myorg",
  "repo": "myrepo",
  "title": "feat: add user authentication",
  "head": "feature/auth",
  "base": "main",
  "body": "## Summary\nAdds JWT-based authentication\n\n## Changes\n- Login endpoint\n- Token refresh\n- Middleware",
  "draft": false
})
```

**Review a PR:**
```javascript
usePower("github", "github", "get_pull_request_diff", {
  "owner": "myorg",
  "repo": "myrepo",
  "pull_number": 42
})
```

### Issue Management

**Create an issue:**
```javascript
usePower("github", "github", "create_issue", {
  "owner": "myorg",
  "repo": "myrepo",
  "title": "Bug: Login fails with special characters in password",
  "body": "## Steps to Reproduce\n1. Enter password with `&` character\n2. Click login\n\n## Expected\nSuccessful login\n\n## Actual\n400 Bad Request",
  "labels": ["bug", "priority:high"],
  "assignees": ["developer1"]
})
```

**Search issues:**
```javascript
usePower("github", "github", "search_issues", {
  "q": "repo:myorg/myrepo is:open label:bug sort:created-desc"
})
```

### Code Search

**Find usage patterns:**
```javascript
usePower("github", "github", "search_code", {
  "q": "org:myorg useAuth filename:*.ts"
})
```

## Combining Tools (Workflows)

### Workflow 1: Feature Development

```javascript
// Step 1: Create a branch
const branch = usePower("github", "github", "create_branch", {
  "owner": "myorg", "repo": "myrepo",
  "branch": "feature/new-api-endpoint"
})

// Step 2: Push implementation files
const commit = usePower("github", "github", "push_files", {
  "owner": "myorg", "repo": "myrepo",
  "branch": "feature/new-api-endpoint",
  "files": [
    {"path": "src/routes/users.ts", "content": "..."},
    {"path": "src/tests/users.test.ts", "content": "..."}
  ],
  "message": "feat: add users API endpoint"
})

// Step 3: Create PR
const pr = usePower("github", "github", "create_pull_request", {
  "owner": "myorg", "repo": "myrepo",
  "title": "feat: add users API endpoint",
  "head": "feature/new-api-endpoint",
  "base": "main",
  "body": "Adds CRUD operations for users"
})

// Step 4: Create tracking issue
const issue = usePower("github", "github", "create_issue", {
  "owner": "myorg", "repo": "myrepo",
  "title": "Track: Users API implementation",
  "body": `PR: #${pr.number}\n\n- [x] Create endpoint\n- [ ] Add pagination\n- [ ] Add filtering`,
  "labels": ["feature", "in-progress"]
})
```

### Workflow 2: Bug Investigation

```javascript
// Step 1: Search for related issues
const issues = usePower("github", "github", "search_issues", {
  "q": "repo:myorg/myrepo is:issue label:bug authentication"
})

// Step 2: Search code for the problematic area
const code = usePower("github", "github", "search_code", {
  "q": "repo:myorg/myrepo validatePassword filename:auth"
})

// Step 3: Check recent commits for changes
const commits = usePower("github", "github", "list_commits", {
  "owner": "myorg", "repo": "myrepo",
  "sha": "main"
})

// Step 4: Check open PRs that might be related
const prs = usePower("github", "github", "list_pull_requests", {
  "owner": "myorg", "repo": "myrepo",
  "state": "open"
})
```

## Search Query Syntax

### Repository Search
- `language:typescript` - Filter by language
- `stars:>1000` - Minimum stars
- `topic:react` - By topic
- `org:myorg` - Within organization
- `fork:true` - Include forks
- `archived:false` - Exclude archived

### Code Search
- `org:myorg` - Within organization
- `repo:owner/repo` - Specific repository
- `filename:*.ts` - File type
- `path:src/` - Directory path
- `language:python` - Language filter
- `"exact phrase"` - Exact match

### Issue/PR Search
- `is:open` / `is:closed` - State
- `is:issue` / `is:pr` - Type
- `label:bug` - By label
- `assignee:username` - By assignee
- `author:username` - By author
- `milestone:"v1.0"` - By milestone
- `created:>2024-01-01` - Date filter
- `sort:created-desc` - Sort order

## Best Practices

### ✅ Do:
- **Use descriptive PR titles** following conventional commits (feat:, fix:, docs:)
- **Include PR body** with summary, changes, and testing notes
- **Label issues** for easy filtering and prioritization
- **Search before creating** to avoid duplicate issues
- **Use draft PRs** for work-in-progress
- **Reference issues in PRs** with "Closes #123" syntax
- **Use branch naming conventions** (feature/, fix/, docs/)

### ❌ Don't:
- **Push directly to main** - always use branches and PRs
- **Create PRs without description** - reviewers need context
- **Leave issues without labels** - makes triage difficult
- **Merge without reviews** - enforce review requirements
- **Use vague commit messages** - be specific about changes

## Configuration

**Authentication Required**: GitHub Personal Access Token (PAT)

**Setup Steps:**

1. **Create a Personal Access Token:**
  - Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
  - Select repositories to grant access
  - Permissions needed: Contents (read/write), Issues (read/write), Pull requests (read/write), Metadata (read)

2. **Configure in mcp.json:**
   ```json
   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
         }
       }
     }
   }
   ```

3. **For GitHub Enterprise:**
   Add `GITHUB_API_URL` environment variable:
   ```json
   "env": {
     "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token",
     "GITHUB_API_URL": "https://github.yourcompany.com/api/v3"
   }
   ```

## Tips

1. **Use fine-grained tokens** - Scope access to specific repos for security
2. **Search before creating** - Check for existing issues/PRs first
3. **Use conventional commits** - Makes changelogs and releases easier
4. **Draft PRs for WIP** - Signal that code isn't ready for review
5. **Cross-reference** - Link issues to PRs with "Closes #N" or "Refs #N"
6. **Use labels consistently** - Establish a labeling taxonomy for your team
7. **Automate with Actions** - Trigger workflows on PR events
8. **Review diffs before merging** - Always check the full diff
9. **Keep PRs small** - Easier to review and less risky to merge
10. **Use code search** - Find patterns and usage across your org

## Disclaimer

This power is provided as a **base template** for reference and as a starting point only. Each organization must perform their own due diligence before using it in production environments. You may need additional customization, security review, and configuration specific to your infrastructure, compliance requirements, and operational standards.

---

**Package:** `@modelcontextprotocol/server-github`
**Source:** Anthropic (Model Context Protocol)
**License:** MIT-0
**Documentation:** https://github.com/modelcontextprotocol/servers/tree/main/src/github
