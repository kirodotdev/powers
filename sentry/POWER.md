---
name: "Sentry"
displayName: "Sentry Issue Triage"
description: "View and triage Sentry issues and errors for your current project. Automatically identifies the relevant Sentry project based on your repository."
keywords: ["sentry", "errors", "issues", "debugging", "triage", "monitoring"]
author: "ahanoff (Akhan Zhakiyanov)"
---

# Sentry Issue Triage

## Overview

This power connects Kiro to Sentry's MCP server, giving you direct access to issues, errors, and debugging data from your Sentry projects. It's designed for quick issue triage workflows - view recent errors, investigate stack traces, and get AI-powered analysis through Sentry's Seer integration.

The power automatically works with your current repository context, making it easy to find and fix errors in the code you're actively working on.

## Onboarding

### Prerequisites
- A Sentry account with access to your organization
- Projects configured in Sentry that match your repositories

### Authentication
When you first use the Sentry MCP server, you'll be prompted to:
1. Log in with your Sentry organization
2. Accept the OAuth authorization
3. Grant access to the necessary permissions

Once authenticated, all Sentry tools become available.

### No Installation Required
Sentry hosts and manages the remote MCP server with OAuth authentication - there's nothing to install locally.

## Common Workflows

### Workflow 1: View Recent Issues for Current Project

**Goal:** See what errors are happening in your project right now.

**Prompts to try:**
```
Tell me about the issues in my [project-name]
```

```
Show me recent errors in this project
```

```
What are the most critical unresolved issues?
```

### Workflow 2: Investigate Specific Errors

**Goal:** Deep dive into a specific error or file.

**Prompts to try:**
```
Check Sentry for errors in src/components/UserProfile.tsx and propose solutions
```

```
Diagnose issue PROJECT-123 and propose solutions
```

```
Find all errors related to authentication in my project
```

### Workflow 3: AI-Powered Analysis with Seer

**Goal:** Get AI-generated root cause analysis and fix recommendations.

**Prompts to try:**
```
Use Sentry's Seer to analyze and propose a solution for issue PROJECT-456
```

```
Get Seer analysis for the most recent crash
```

### Workflow 4: Release Management

**Goal:** Track releases and their associated issues.

**Prompts to try:**
```
Show me the most recent releases for my organization
```

```
What issues were introduced in the latest release?
```

## Available Tools

The Sentry MCP Server provides 16+ tools:

**Core Tools:**
- Organizations, Projects, Teams management
- Issues and DSN management
- Project creation and configuration

**Analysis Tools:**
- Error searching across files and projects
- Detailed issue investigation
- Seer integration for AI-powered root cause analysis

**Advanced Features:**
- Release management
- Performance monitoring
- Custom queries

## Best Practices

- Reference your project name or let the agent identify it from your repository context
- Use specific file paths when investigating errors (e.g., `src/api/handler.ts`)
- Leverage Seer for complex debugging - it provides AI-generated fix recommendations
- Check recent releases when investigating new issues to correlate changes

## Troubleshooting

### OAuth Authentication Problems
- Ensure you have the necessary permissions in your Sentry organization
- Try logging out of the MCP integration and logging back in
- Check that your browser allows popups for the OAuth flow

### Connection Issues
- Verify the MCP server URL is correct: `https://mcp.sentry.dev/mcp`
- Check your network connection
- Restart Kiro if the connection seems stuck

### Missing Projects or Issues
- Verify your Sentry organization access
- Ensure the project exists and you have permissions to view it
- Check that issues aren't filtered or resolved

### Seer Analysis Not Available
- Seer may not be enabled for all organizations
- Check your Sentry plan includes Seer features
- Some issue types may not support Seer analysis

## Configuration

**No additional configuration required** - works after OAuth authentication with Sentry.

The MCP server URL is: `https://mcp.sentry.dev/mcp`

---

**MCP Server:** Sentry (Remote OAuth)
**Server URL:** https://mcp.sentry.dev/mcp
