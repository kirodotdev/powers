---
name: "appwrite"
displayName: "Appwrite Backend Platform"
description: "Build and manage Appwrite Cloud or self-hosted backends with authentication, databases, storage, functions, messaging, sites, and current Appwrite documentation."
keywords: ["appwrite", "backend", "database", "auth", "authentication", "storage", "functions", "serverless", "baas", "api", "users", "sites", "messaging", "cloud", "self-hosted"]
author: "Appwrite"
---

# Appwrite Backend Platform

This power includes both officially supported Appwrite MCP deployment methods. Appwrite Cloud is enabled by default; the self-hosted server is included but disabled until the user supplies credentials and selects it.

## Deployment support

| Deployment | MCP transport | Authentication | Default state |
|---|---|---|---|
| Appwrite Cloud | Hosted HTTP at `https://mcp.appwrite.io/` | Browser-based OAuth | Enabled |
| Self-hosted Appwrite | Local stdio through `uvx mcp-server-appwrite` | Project ID, API key, and instance endpoint | Disabled |

Keep only the server for the intended project enabled. This prevents similarly named tools from operating against the wrong Appwrite deployment.

## Onboarding

### 1. Choose a deployment

- **Appwrite Cloud:** Create or select a project at [cloud.appwrite.io](https://cloud.appwrite.io). No local installation, environment variables, or API key are required.
- **Self-hosted Appwrite:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/), create a scoped API key in the target instance, and set `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, and `APPWRITE_ENDPOINT` in the environment that launches Kiro.

### 2. Select the MCP server in Kiro

Open **Kiro panel → MCP servers** and use one of these configurations:

- **Cloud:** Leave `appwrite-cloud` enabled and `appwrite-self-hosted` disabled. On first connection, complete Appwrite OAuth in the browser.
- **Self-hosted:** Disable `appwrite-cloud`, approve the three Appwrite environment-variable names if Kiro prompts, and enable `appwrite-self-hosted`.

The bundled configuration is:

```json
{
  "mcpServers": {
    "appwrite-cloud": {
      "url": "https://mcp.appwrite.io/",
      "disabled": false
    },
    "appwrite-self-hosted": {
      "command": "uvx",
      "args": ["mcp-server-appwrite", "--all"],
      "env": {
        "APPWRITE_PROJECT_ID": "${APPWRITE_PROJECT_ID}",
        "APPWRITE_API_KEY": "${APPWRITE_API_KEY}",
        "APPWRITE_ENDPOINT": "${APPWRITE_ENDPOINT}"
      },
      "disabled": true
    }
  }
}
```

### 3. Confirm the target before changes

For Cloud, ask for workspace context and identify the intended organization and project. For self-hosted Appwrite, verify that the three environment variables point to the intended instance and project. Confirm the target again before destructive or production operations.

## Available MCP Servers

### appwrite-cloud

The hosted Cloud server combines project operations, workspace context, and current Appwrite documentation search. It exposes a compact discovery workflow:

- `appwrite_get_context` — summarize the connected account, organization, and projects.
- `appwrite_search_tools` — find an Appwrite operation and its parameter schema.
- `appwrite_call_tool` — execute the selected operation.
- `appwrite_search_docs` — search Appwrite documentation semantically.

No API key, endpoint variable, local package, or separate documentation server belongs in this configuration.

### appwrite-self-hosted

The local stdio server connects directly to one self-hosted project using the configured endpoint and API key. The bundled `--all` flag enables all supported Appwrite APIs. To reduce tool-context use, customize the local power before installation and replace `--all` with only the needed flags, such as `--tablesdb`, `--users`, `--teams`, `--storage`, `--functions`, or `--messaging`. Database tools are enabled by default when no service flags are supplied.

Do not commit actual credentials to `mcp.json`; keep them in approved environment variables. The self-hosted server does not provide the hosted Cloud server's OAuth flow or integrated semantic documentation search.

## Tool usage

Use natural-language requests and name the intended deployment when both servers are active. Prefer mutually exclusive enablement; if both must remain active, explicitly select the server in Kiro before invoking a tool.

Examples:

- “Using `appwrite-cloud`, list projects in my workspace.”
- “Using `appwrite-cloud`, create a database named `main` in project `PROJECT_ID`.”
- “Using `appwrite-self-hosted`, list users in the configured project.”
- “Search the Appwrite documentation for real-time user creation events.”

Follow the tool schema returned by the selected server exactly.

## Available Steering Files

- `steering/steering.md` — Load on demand for detailed Appwrite guidance covering database schemas and indexes, permissions, user management, storage, functions, real-time subscriptions, error handling, performance, testing, monitoring, and production-readiness practices.

## Safety and implementation guidance

- Keep only the server for the current target enabled whenever possible.
- Confirm deployment, organization, project, and resource identifiers before mutations.
- Use least-privilege OAuth authorization and API-key scopes.
- Do not use public read/write access for sensitive data.
- Keep application and MCP credentials in server-side or approved environment variables.
- Test permission changes, deployments, data migrations, and destructive operations in a non-production project first.

## Troubleshooting

### Cloud authorization does not complete

Reconnect `appwrite-cloud`, complete sign-in and consent in the browser, and verify that the signed-in account can access the intended Appwrite Cloud project.

### Self-hosted server does not start

Verify that `uv` is installed, the three environment variables are set in Kiro's environment, their names are approved when prompted, and `APPWRITE_ENDPOINT` ends with the instance API path such as `/v1`. Check the MCP server logs from the Kiro panel.

### The wrong project or deployment appears

Disable both Appwrite servers, then enable only the intended one. For Cloud, request workspace context and specify the project. For self-hosted, verify `APPWRITE_PROJECT_ID` and `APPWRITE_ENDPOINT` before reconnecting.

### Too many self-hosted tools are loaded

Replace `--all` in the locally installed power configuration with only the service flags needed for that workflow, then reconnect the server.

## Resources

- [Appwrite MCP overview](https://appwrite.io/docs/tooling/ai/mcp-servers/)
- [Hosted Appwrite Cloud MCP server](https://appwrite.io/docs/tooling/ai/mcp-servers/api)
- [Self-hosted MCP server](https://appwrite.io/docs/advanced/self-hosting/mcp)
- [Appwrite documentation](https://appwrite.io/docs)
- [Appwrite Cloud console](https://cloud.appwrite.io)
