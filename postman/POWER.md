---
name: "postman"
displayName: "API Testing with Postman"
description: "Automate API testing and collection management with Postman - create workspaces, collections, environments, and run tests programmatically"
keywords: ["postman", "api", "testing", "collections", "rest", "http", "automation"]
author: "Postman"
---

# Onboarding

Before proceeding, validate that the user has completed the following steps before using this power.

## Step 1

Confirm the user has a Postman API key available to the MCP server as `POSTMAN_API_KEY`.

This power runs the Postman MCP server **locally over stdio**, which authenticates with a Postman API key (the local server does not support OAuth). Ask the user in chat to confirm they have set it — do not probe the value from the terminal.

- Generate a key at https://postman.postman.co/settings/me/api-keys
- Export it in the environment Kiro launches from, e.g. `export POSTMAN_API_KEY=...`. `mcp.json` forwards it to the server via `"POSTMAN_API_KEY": "${POSTMAN_API_KEY}"`.
- Node.js 20 or later must be installed, since the server is started with `npx`.

To verify the connection, call the `getAuthenticatedUser` MCP tool. A successful response is the auth check — if it fails, the key is missing, expired, or invalid.

## Step 2

Create a hook that runs anytime the source code or configuration file has been changed. Save the hook in .kiro/hooks/hookname.kiro.hook. Example hook format. Please update the patterns to match the project's file structure.

```json
{
  "enabled": true,
  "name": "API Postman Testing",
  "description": "Monitors API source code changes across multiple programming languages and automatically runs Postman collection tests to validate functionality",
  "version": "1",
  "when": {
    "type": "fileEdited",
    "patterns": [
      "*.js",
      "*.ts",
      "*.py",
      "*.java",
      "*.cs",
      "*.go", 
      "*.rs",
      "*.php",
      "*.rb",
      "*.kt",
      "*.swift",
      "*.scala",
      "package.json",
      "requirements.txt",
      "Pipfile",
      "pom.xml",
      "build.gradle",
      "*.csproj",
      "go.mod",
      "Cargo.toml",
      "composer.json",
      "Gemfile",
      "build.sbt",
      "openapi.yaml",
      "openapi.yml",
      "swagger.yaml",
      "swagger.yml",
      "api.yaml",
      "api.yml"
    ]
  },
  "then": {
    "type": "askAgent",
    "prompt": "API source code or configuration has been modified. Please retrieve the contents of the .postman.json file. If the file does not exist or is empty, create a Postman collection for the API. If it exists, get the collection ID and run the collection, showing me the results and propose fixes for any errors found."
  }
}
```
# Overview

Automate API testing and collection management with Postman. Create workspaces, collections, environments, and run tests programmatically.

**Authentication**: Postman API key, supplied to the local server as `POSTMAN_API_KEY`.

## Available MCP Servers

### postman
**Package:** `@postman/postman-mcp-server`
**Connection:** Local server over stdio, started with `npx`
**Authentication:** Postman API key via the `POSTMAN_API_KEY` environment variable
**Mode:** Minimal (42 essential tools) - Default configuration

**Why the local server:** `runCollection` — the tool that actually executes a collection and returns test results — is only exposed by the local server. Postman's hosted remote endpoints (`https://mcp.postman.com/minimal` and `/mcp`) do not include it. Because collection runs are the core of this power (the hook in Step 2 asks the agent to run the collection and propose fixes), the local server is required.

The local server also executes requests from the developer's own machine, so collections that target `http://localhost:3000` and other private hosts are reachable. The remote server has no network access to the user's workstation.

To enable Full mode (125 tools) for advanced collaboration and enterprise features, add `--full` to `args`.

**Available Tools (42 in Minimal Mode):**

**Workspace Management:**
- `createWorkspace` - Create a new workspace
- `getWorkspace` - Get workspace details
- `getWorkspaces` - List all accessible workspaces
- `updateWorkspace` - Update workspace properties

**Collection Management:**
- `createCollection` - Create a new API collection
- `getCollection` - Get detailed collection information
- `getCollections` - List all collections in a workspace
- `putCollection` - Replace/update entire collection
- `duplicateCollection` - Create a copy of a collection
- `createCollectionRequest` - Add a request to a collection
- `updateCollectionRequest` - Update an existing request in a collection
- `createCollectionResponse` - Add a response example to a request

**Environment Management:**
- `createEnvironment` - Create a new environment
- `getEnvironment` - Get environment details
- `getEnvironments` - List all environments
- `putEnvironment` - Replace/update entire environment

**Mock Server Management:**
- `createMock` - Create a mock server
- `getMock` - Get mock server details
- `getMocks` - List all mock servers
- `updateMock` - Update mock server configuration
- `publishMock` - Make mock server public

**API Specification Management:**
- `createSpec` - Create a new API specification
- `getSpec` - Get specification details
- `getAllSpecs` - List all specifications
- `getSpecDefinition` - Get complete spec definition
- `updateSpecProperties` - Update spec metadata
- `createSpecFile` - Add a file to a spec
- `getSpecFile` - Get a specific spec file
- `getSpecFiles` - List all files in a spec
- `updateSpecFile` - Update a spec file

**Code Generation & Sync:**
- `generateCollection` - Generate collection from API spec
- `generateSpecFromCollection` - Generate spec from collection
- `getGeneratedCollectionSpecs` - Get specs generated from a collection
- `getSpecCollections` - Get collections generated from a spec
- `syncCollectionWithSpec` - Sync collection with its spec
- `syncSpecWithCollection` - Sync spec with its collection

**Testing & Execution:**
- `runCollection` - Execute a collection with automated tests (**local server only**)

**Search & Discovery:**
- `searchPostmanElements` - Search Postman elements across networks

**User & Metadata:**
- `getAuthenticatedUser` - Get current user information
- `getTaggedEntities` - Get entities by tag
- `getDuplicateCollectionTaskStatus` - Check the status of a collection duplication task
- `getEnabledTools` - List available tools by mode

## Tool Usage Examples

```javascript
// Create workspace
mcp_postman_createWorkspace({
  "workspace": { "name": "My API Project", "type": "personal" }
})

// Create collection
mcp_postman_createCollection({
  "workspace": "workspace-id",
  "collection": {
    "info": {
      "name": "User API",
      "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    }
  }
})

// Create environment
mcp_postman_createEnvironment({
  "workspace": "workspace-id",
  "environment": {
    "name": "Local",
    "values": [
      { "key": "base_url", "value": "http://localhost:3000", "enabled": true }
    ]
  }
})

// Run collection
mcp_postman_runCollection({
  "collectionId": "collection-id",
  "environmentId": "environment-id"
})
```

## Workflows

**Project Setup:**
```javascript
const { workspace } = await mcp_postman_createWorkspace({ "workspace": { "name": "Project", "type": "personal" }})
const { collection } = await mcp_postman_createCollection({ "workspace": workspace.id, "collection": { "info": { "name": "API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json" }}})
const { environment } = await mcp_postman_createEnvironment({ "workspace": workspace.id, "environment": { "name": "Local", "values": [{ "key": "base_url", "value": "http://localhost:3000", "enabled": true }]}})
// Save IDs to .postman.json
```

**Generate from OpenAPI:**
```javascript
const { spec } = await mcp_postman_createSpec({ "workspaceId": "workspace-id", "name": "API Spec", "type": "OPENAPI:3.0", "files": [{ "path": "openapi.yaml", "content": "..." }]})
const result = await mcp_postman_generateCollection({ "specId": spec.id, "elementType": "collection", "name": "Generated Collection" })
```

**Automated Testing:**
```javascript
const { workspaces } = await mcp_postman_getWorkspaces()
const { collections } = await mcp_postman_getCollections({ "workspace": workspaces[0].id })
const { environments } = await mcp_postman_getEnvironments({ "workspace": workspaces[0].id })
for (const collection of collections) {
  await mcp_postman_runCollection({ "collectionId": collection.uid, "environmentId": environments[0]?.id })
}
```

## Best Practices

- Store workspace/collection/environment IDs in `.postman.json`
- Use environment variables for different contexts (local/staging/production)
- Add post-request test scripts for validation
- Organize requests in folders
- Run collections before deployment
- Ensure API server is running before tests

## Troubleshooting

**"Collection not found"**: Call `getCollections` to verify ID and permissions

**"Environment not found"**: Call `getEnvironments` with correct workspace ID

**Test failures**: Verify API server running, check environment variables (base_url), review test scripts

**Authentication issues**: Confirm `POSTMAN_API_KEY` is exported in the environment Kiro was launched from, then restart the MCP server so it picks up the value. Call `getAuthenticatedUser` to verify. Keys can be regenerated at https://postman.postman.co/settings/me/api-keys

**Server fails to start**: Ensure Node.js 20 or later is installed and `npx` is on `PATH`. The first run downloads the package, which may take a moment.

**`runCollection` not available**: The tool is only exposed by the local server. Confirm `mcp.json` uses `command`/`args` rather than a `url` pointing at `https://mcp.postman.com/...`.

## Configuration

**MCP Configuration (Minimal mode - 42 tools):**
```json
{
  "mcpServers": {
    "postman": {
      "command": "npx",
      "args": ["-y", "@postman/postman-mcp-server@latest"],
      "env": {
        "POSTMAN_API_KEY": "${POSTMAN_API_KEY}"
      },
      "disabled": false
    }
  }
}
```

**Full mode (125 tools):** Add `--full` to `args`:
```json
"args": ["-y", "@postman/postman-mcp-server@latest", "--full"]
```

**EU region:** Add `--region eu` to `args`.
