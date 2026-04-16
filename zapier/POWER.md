---
name: "zapier"
displayName: "Zapier"
description: "Connect 9,000+ apps to your AI workflow — discover, enable, and execute Zapier actions directly from your AI assistant."
keywords: ["zapier", "automation", "integrations", "workflow", "ai-actions", "mcp", "no-code", "productivity", "slack", "gmail", "jira", "notion", "hubspot"]
author: "Zapier"
---

# Zapier Power

## Overview

Connect your AI assistant to 9,000+ apps — Slack, Gmail, Google Calendar, Jira, Notion, HubSpot, and thousands more. Once set up, you can search across your tools, take actions, and automate workflows through natural conversation. Zapier MCP is personalized to your workflow: you pick the apps and actions that matter to you, and your AI learns to use them.

**Key capabilities:**

- **Two server modes**: Agentic mode exposes 14 meta-tools for in-chat action management; Classic mode exposes each configured action as its own MCP tool
- **Cross-app workflows**: Chain reads and writes across Slack, Gmail, Jira, Notion, HubSpot, and 9,000+ other apps through natural conversation
- **Built-in safety model**: Read actions run without confirmation; write actions require explicit user approval
- **Personalized tool profiles**: Generate persistent AI instructions tailored to the specific set of actions you have enabled
- **OAuth authentication**: No API keys required — authenticate once via mcp.zapier.com and per-app OAuth flows

## Onboarding

### Step 1: Connect the Zapier MCP server

After installing this power, connect the Zapier MCP server:

Connection: HTTPS API endpoint at [https://mcp.zapier.com/api/v1/connect](https://mcp.zapier.com/api/v1/connect)
Authorization: Use OAuth to connect to the Zapier MCP server

### Step 2: Detect your server mode

Zapier MCP operates in one of two modes. Check which tools are available:

- **Agentic mode**: `list_enabled_zapier_actions` is present — actions are managed and executed via meta-tools in chat
- **Classic mode**: `get_configuration_url` + individual `app_action_name` tools (e.g., `gmail_send_email`) — each configured action is its own MCP tool
- **Not connected**: No Zapier tools available — the server needs authentication

### Step 3: Get started

- **Agentic mode**: Call `get_zapier_skill` with name `"zapier-mcp-onboarding"` and follow its instructions
- **Classic mode**: Say **"setup zapier"** to trigger the setup workflow
- **Not connected**: Attempt `mcp_auth` on the Zapier MCP server, or follow the manual connection steps above

## Available Steering Files

- **zapier-setup** — Setup, authentication, mode detection, and full onboarding flow for new and returning users
- **zapier-status** — Health check, audit, and diagnose modes for monitoring and maintaining the setup
- **create-my-tools-profile** — Generates a personalized AI tool profile from the user's enabled Zapier actions
- **zapier-lifecycle** — Tool lifecycle rules, safety model, and error handling that govern all Zapier MCP interactions

## When to Load Steering Files

- Setting up Zapier or troubleshooting connection issues → `zapier-setup.md`
- Checking tool health, auditing setup, or diagnosing broken tools → `zapier-status.md`
- Generating a personalized tools profile after setup → `create-my-tools-profile.md`
- Any interaction with Zapier MCP tools (reads, writes, error handling) → `zapier-lifecycle.md`

## Available MCP Servers

### zapier

**Connection:** HTTPS API endpoint at `https://mcp.zapier.com/api/v1/connect`
**Authorization:** OAuth via mcp.zapier.com (no API key required)

**Mode detection signals:**

- **Agentic mode**: `list_enabled_zapier_actions` is present as a tool — the server exposes a fixed set of meta-tools, and actions are managed and executed dynamically in chat
- **Classic mode**: `get_configuration_url` is present alongside individual `app_action_name` tools — each configured action is its own MCP tool
- **Not connected**: No Zapier tools are available — the server needs authentication

**Agentic mode tools (14 static meta-tools):**

| Tool | Purpose |
|------|---------|
| `list_enabled_zapier_actions` | List currently enabled actions |
| `discover_zapier_actions` | Search for apps and actions available to add |
| `enable_zapier_action` | Enable a specific action as a tool |
| `disable_zapier_action` | Disable an action no longer needed |
| `auto_provision_mcp` | Auto-setup tools from existing Zapier connections |
| `execute_zapier_read_action` | Run a read/search action (e.g., find an email) |
| `execute_zapier_write_action` | Run a write action (e.g., send a message) |
| `get_configuration_url` | Get the URL to the Zapier MCP config page |
| `list_zapier_skills` | List saved skills/workflows |
| `get_zapier_skill` | Retrieve a specific skill |
| `create_zapier_skill` | Create a new skill |
| `update_zapier_skill` | Update an existing skill |
| `delete_zapier_skill` | Delete a skill |
| `send_feedback` | Send feedback to Zapier |

**Classic mode tools:**

Each enabled action becomes its own MCP tool named `app_action_name` (e.g., `slack_send_channel_message`, `gmail_find_email`, `jira_find_issue_by_key`). Tool descriptions identify the associated app. The built-in `get_configuration_url` tool is always present and returns the URL where the user can add, remove, or manage actions in the web UI.

## MCP Configuration

```json
{
  "mcpServers": {
    "zapier": {
      "url": "https://mcp.zapier.com/api/v1/connect"
    }
  }
}
```

## License and support

This power integrates with [Zapier](https://zapier.com/mcp) (Apache-2.0).
- [Privacy Policy](https://zapier.com/privacy)
- [Support](https://zapier.com/support)