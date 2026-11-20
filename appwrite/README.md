# Appwrite Power for Kiro

Build and manage Appwrite Cloud or self-hosted backends from Kiro. The power includes both official MCP deployment methods and keeps them separately selectable.

## Included servers

| Server | Use case | Authentication | Default |
|---|---|---|---|
| `appwrite-cloud` | Appwrite Cloud projects through `https://mcp.appwrite.io/` | Browser-based OAuth | Enabled |
| `appwrite-self-hosted` | A project on your own Appwrite instance through local `uvx` | Project ID, API key, and endpoint environment variables | Disabled |

Keep only the server for the current project enabled to avoid operating against the wrong deployment.

## Appwrite Cloud quick start

1. Create or select a project at [cloud.appwrite.io](https://cloud.appwrite.io).
2. Install this power in Kiro.
3. Leave `appwrite-cloud` enabled and `appwrite-self-hosted` disabled.
4. Connect `appwrite-cloud`, sign in through the browser, and approve the OAuth request.
5. Ask Kiro to retrieve workspace context before selecting a project for changes.

Cloud requires no `uv` installation, MCP API key, endpoint variable, or separate documentation server.

## Self-hosted quick start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Create a scoped API key for the target self-hosted project.
3. Set `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY`, and `APPWRITE_ENDPOINT` in the environment that launches Kiro.
4. In **Kiro panel → MCP servers**, disable `appwrite-cloud`, approve the environment-variable names if prompted, and enable `appwrite-self-hosted`.
5. Confirm the endpoint and project before making changes.

The bundled self-hosted server uses `--all` for broad API coverage. For a smaller tool surface, replace `--all` in a local copy of the power with only the required service flags before installation.

## Included configuration

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

Never put actual API keys in the power configuration or repository.

## Capabilities

- Create and manage databases, users, teams, storage, functions, messaging, and sites.
- Inspect Cloud account, organization, and project context.
- Search current Appwrite documentation through the hosted Cloud MCP server.
- Use natural-language requests while retaining explicit control over the target deployment.

## Safe usage

- Prefer mutually exclusive server enablement.
- Verify the deployment and project before every mutation.
- Apply least-privilege OAuth authorization, API-key scopes, and Appwrite permissions.
- Test production-impacting changes in a non-production project first.

## Documentation

- [POWER.md](POWER.md) — server selection, capabilities, safety, and troubleshooting.
- [QUICK_START.md](QUICK_START.md) — concise setup for both deployments.
- [steering/steering.md](steering/steering.md) — implementation and security best practices.
- [Appwrite Cloud MCP documentation](https://appwrite.io/docs/tooling/ai/mcp-servers/api)
- [Self-hosted MCP documentation](https://appwrite.io/docs/advanced/self-hosting/mcp)

## License

See [LICENSE](LICENSE).
