# Appwrite MCP Quick Start for Kiro

This power includes two selectable servers. Use only the one that targets your current project.

## Appwrite Cloud

1. Create or choose a project in the [Appwrite Cloud console](https://cloud.appwrite.io).
2. In **Kiro panel → MCP servers**, leave `appwrite-cloud` enabled and `appwrite-self-hosted` disabled.
3. Connect `appwrite-cloud` and complete Appwrite OAuth in the browser.
4. Ask Kiro for workspace context, then name the intended project in your request.

No local installation, API key, project ID variable, or endpoint variable is needed.

```text
Using appwrite-cloud, list my Appwrite projects
Using appwrite-cloud, create a database named main in project PROJECT_ID
Search the Appwrite documentation for real-time subscriptions
```

## Self-hosted Appwrite

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Create an API key with only the scopes needed for the target project.
3. Set these variables in the environment that launches Kiro:

```powershell
$env:APPWRITE_PROJECT_ID="your-project-id"
$env:APPWRITE_API_KEY="your-api-key"
$env:APPWRITE_ENDPOINT="https://your-appwrite-domain/v1"
```

4. In **Kiro panel → MCP servers**, disable `appwrite-cloud`, approve the variable names if prompted, and enable `appwrite-self-hosted`.
5. Confirm the endpoint and project ID before issuing mutations.

```text
Using appwrite-self-hosted, list databases in the configured project
Using appwrite-self-hosted, list users in the configured project
```

The bundled server starts `uvx mcp-server-appwrite --all`. If this exposes more tools than needed, install a local copy of the power and replace `--all` with specific flags such as `--tablesdb`, `--users`, `--storage`, or `--functions`.

## Switching projects or deployments

1. Disable both Appwrite MCP servers.
2. For self-hosted Appwrite, update the three environment variables before reconnecting.
3. Enable only the server for the intended target.
4. Retrieve or verify project context before making changes.

## Troubleshooting

- **Cloud authorization does not finish:** reconnect `appwrite-cloud` and complete browser consent.
- **Self-hosted server does not start:** verify `uv`, environment variables, approved variable names, endpoint format, and API-key scopes.
- **Wrong project appears:** disable both servers, verify the target configuration, and reconnect only the intended server.
- **Too many tools:** replace self-hosted `--all` with specific service flags in a local copy of the power.

## Learn more

- [Appwrite Cloud MCP server](https://appwrite.io/docs/tooling/ai/mcp-servers/api)
- [Self-hosted MCP server](https://appwrite.io/docs/advanced/self-hosting/mcp)
