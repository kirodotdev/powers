---
name: "atlassian"
displayName: "Atlassian Admin"
description: "Manage Jira projects, issues, and sprints alongside Confluence spaces and pages - plan work, track bugs, and document everything using the official Atlassian MCP server"
keywords: ["atlassian", "jira", "confluence", "project-management", "issues", "sprints", "documentation", "wiki", "tickets", "agile"]
author: "Steven J Miklovic"
---

# Atlassian Admin Power

## Overview

Manage your Atlassian ecosystem directly from Kiro. This power connects to the official Atlassian Remote MCP server to give you full access to **Jira** for project and issue management and **Confluence** for documentation and knowledge management.

Use Jira to create and track issues, manage sprints, query with JQL, and update workflows. Use Confluence to create and edit pages, manage spaces, and keep your team's knowledge base up to date.

**Key capabilities:**

- **Jira Issues**: Create, read, update, and transition issues across any project
- **JQL Search**: Run precise Jira Query Language queries to find issues
- **Sprints & Boards**: Inspect active sprints and board configurations
- **Epics & Links**: Link issues to epics and create issue relationships
- **Confluence Pages**: Create, read, and update pages within any space
- **Space Management**: List and inspect Confluence spaces
- **Comments**: Add comments to Jira issues and Confluence pages
- **Attachments**: Retrieve attachments from issues and pages

**Authentication**: Requires an Atlassian account. The Atlassian Remote MCP server uses OAuth 2.0 (3LO) — you will be prompted to authorize Kiro in your browser on first use.

## Available MCP Servers

### atlassian

**Connection:** SSE endpoint at `https://mcp.atlassian.com/v1/sse`
**Authorization:** OAuth 2.0 (3LO) — browser-based sign-in to your Atlassian account

## Best Practices

### Jira

- **Search before creating** — use JQL to check for existing issues before filing duplicates.
- **Use JQL** for all issue queries: `project = MYPROJ AND status = "In Progress" AND assignee = currentUser()`.
- **Set required fields** — always provide `summary`, `issuetype`, and `project` when creating issues.
- **Transition, don't force** — use issue transitions to move status rather than setting the field directly.
- **Link to epics** — associate stories and tasks with their parent epic to maintain hierarchy.

### Confluence

- **Search first** — look for an existing page before creating one to avoid duplicates.
- **Match space conventions** — follow the naming and structure conventions already used in the target space.
- **Use labels** — add labels to pages for better discoverability and filtering.
- **Structure content** — use headings, bullet lists, and code blocks (with language tags) to keep pages readable.

## Common Workflows

### Workflow 1: Create and Assign a Jira Issue

```
1. Identify the project key (e.g., "PROJ")
2. Create an issue with summary, type (Story/Bug/Task), and description
3. Assign the issue to the appropriate team member
4. Link the issue to its parent epic if applicable
5. Set the priority and any relevant labels or components
```

### Workflow 2: Query Issues with JQL

```
// Find all open bugs assigned to me in a project
project = "PROJ" AND issuetype = Bug AND status != Done AND assignee = currentUser() ORDER BY priority DESC

// Find issues in the current sprint
project = "PROJ" AND sprint in openSprints() ORDER BY rank ASC

// Find recently updated issues
project = "PROJ" AND updated >= -7d ORDER BY updated DESC
```

### Workflow 3: Create a Confluence Page

```
1. Identify the target space key (e.g., "TEAM")
2. Search for a suitable parent page
3. Create the page with a descriptive title and structured content
4. Add labels to improve discoverability
5. Share the page link with relevant stakeholders
```

### Workflow 4: Update a Jira Issue Status

```
1. Retrieve the issue by key (e.g., "PROJ-123")
2. List available transitions for the issue
3. Apply the appropriate transition (e.g., "In Progress" → "In Review")
4. Add a comment explaining the status change if needed
```

### Workflow 5: Document a Sprint Retrospective in Confluence

```
1. Retrieve completed sprint details from Jira
2. Find or create a "Retrospectives" page in the relevant Confluence space
3. Create a child page titled "<Sprint Name> Retrospective"
4. Populate with sections: What went well, What to improve, Action items
5. Link Jira issues for any action items created
```

## Configuration

**Authentication Required**: Atlassian account (OAuth 2.0)

**Setup Steps:**

1. Install this power in Kiro
2. On first use, Kiro will open a browser window to authorize with your Atlassian account
3. Grant the requested permissions for Jira and Confluence access
4. The MCP server will use your account's permissions — you can only access projects and spaces you have permission to view or edit

**MCP Configuration:**

```json
{
  "mcpServers": {
    "atlassian": {
      "url": "https://mcp.atlassian.com/v1/sse"
    }
  }
}
```

## Troubleshooting

### Error: "Unauthorized" or "401"

**Cause:** OAuth token missing, expired, or revoked
**Solution:**

1. Re-authorize by triggering the OAuth flow again
2. Ensure your Atlassian account has access to the relevant sites
3. Check that the MCP server URL is correct: `https://mcp.atlassian.com/v1/sse`

### Error: "Project not found" or "Space not found"

**Cause:** Incorrect project key or space key, or insufficient permissions
**Solution:**

1. List available projects/spaces to confirm the correct key
2. Verify your account has at least Browse permission for the project or space
3. Check that the project/space exists in your Atlassian site

### Error: "Issue does not exist" or "404"

**Cause:** Invalid issue key or the issue was deleted
**Solution:**

1. Verify the issue key format (e.g., `PROJ-123`)
2. Search for the issue using JQL to confirm it exists
3. Ensure you have permission to view the issue

### JQL query returns no results

**Cause:** Query syntax error or no matching issues
**Solution:**

1. Validate JQL syntax in Jira's issue search UI first
2. Simplify the query and add conditions incrementally
3. Check field names are correct (e.g., `issuetype` not `issue_type`)
4. Verify the project key is correct and issues exist in that project

### Confluence page creation fails

**Cause:** Missing required fields or duplicate title in the same space
**Solution:**

1. Ensure both `title` and `spaceKey` are provided
2. Search for an existing page with the same title in the space
3. Verify your account has Create Page permission in the target space

## Resources

- [Atlassian Remote MCP Server](https://www.atlassian.com/blog/announcements/remote-mcp-server)
- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/v2/)
- [JQL Reference](https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [Atlassian OAuth 2.0](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)

---

**License:** MIT
