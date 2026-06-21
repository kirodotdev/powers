---
name: "appwrite"
displayName: "Appwrite Backend Platform"
description: "Build backend services with Appwrite - databases, authentication, storage, functions, and messaging for web and mobile apps"
keywords: ["appwrite", "backend", "database", "auth", "authentication", "storage", "functions", "serverless", "baas", "api", "users", "sites", "messaging"]
author: "Appwrite"
version: "2.0.0"
---

# Onboarding

Before using Appwrite MCP, ensure you have completed the following steps.

## Step 1: Validate Prerequisites

Check that the required tools are installed:

**For API Server:**
- **uv**: Required to run the Appwrite API MCP server (version 0.4.1+)
  - Verify with: `uv --version`
  - Install if missing: Follow instructions at https://docs.astral.sh/uv/getting-started/installation/
  - **CRITICAL**: If uv is not installed, DO NOT proceed with API server setup

**For Docs Server:**
- **No prerequisites required** - HTTP-based server, works out of the box

## Step 2: Configure Appwrite Credentials

You need an Appwrite project with API credentials:

1. **Create or access your Appwrite project** at https://cloud.appwrite.io
2. **Get your Project ID** from the Settings page
3. **Create an API Key** with necessary scopes:
   - Navigate to Settings → API Keys
   - Click "Create API Key"
   - Enable required scopes (databases, users, storage, functions, etc.)
   - Copy the generated API key
4. **Note your region and endpoint**:
   - Format: `https://<REGION>.cloud.appwrite.io/v1`
   - Common regions: `nyc`, `fra`, `sfo`, `blr`, `sgp`, `syd`

**Environment Variables:**

Set these environment variables on your system or add them to your MCP configuration:

- `APPWRITE_PROJECT_ID` - Your project ID
- `APPWRITE_API_KEY` - Your API key (keep secure!)
- `APPWRITE_ENDPOINT` - Your endpoint URL (e.g., `https://nyc.cloud.appwrite.io/v1`)

## Step 3: Understand MCP Server 2.0 Architecture

This power provides two MCP servers:

- **appwrite-api**: Interact with Appwrite services using the new 2-tool architecture
- **appwrite-docs**: Query Appwrite documentation for guidance and examples

**What's New in MCP Server 2.0:**
- **Zero Configuration**: No more service flags (`--users`, `--storage`, etc.) - all services are automatically available
- **Compact Architecture**: Only 2 tools exposed to the model (`appwrite_search_tools` and `appwrite_call_tool`)
- **Reduced Context Usage**: Full Appwrite tool catalog stays internal and is searched at runtime
- **Automatic Service Discovery**: All supported Appwrite services are automatically registered

You can enable one or both servers depending on your needs. The API server is essential for building applications, while the docs server helps with learning and troubleshooting.

## Step 4: Add Development Hooks (Optional)

Create a hook to validate database operations. Save to `.kiro/hooks/appwrite-db-check.kiro.hook`:

```json
{
  "enabled": true,
  "name": "Appwrite Database Validation",
  "description": "Validates database schema and queries when database files are modified",
  "version": "1",
  "when": {
    "type": "fileEdited",
    "patterns": [
      "**/appwrite/**/*.ts",
      "**/appwrite/**/*.js",
      "**/lib/appwrite/**",
      "**/src/appwrite/**"
    ]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Review the Appwrite database code for best practices: proper error handling, type safety, query optimization, and security permissions"
  }
}
```

# Overview

Appwrite is an open-source backend-as-a-service platform that provides authentication, databases, storage, functions, and messaging. This power gives you access to both the Appwrite API and comprehensive documentation through MCP servers.

**Key capabilities:**

- **Databases**: Create collections, manage documents, query data with powerful filters
- **Authentication**: User management, OAuth providers, sessions, teams
- **Storage**: File uploads, downloads, image transformations, permissions
- **Functions**: Serverless functions with multiple runtimes
- **Messaging**: Email, SMS, and push notifications
- **Real-time**: WebSocket subscriptions for live data updates
- **Sites**: Deploy static sites and SSR applications

**Perfect for:**
- Building full-stack web and mobile applications
- Creating serverless backends
- Managing user authentication and authorization
- Storing and serving files with CDN
- Implementing real-time features
- Deploying static sites and server-side rendered apps

## Available MCP Servers

### appwrite-api

**Package:** `mcp-server-appwrite` (version 0.4.1+, via uvx)
**Connection:** Python-based MCP server
**Authentication:** API key with project ID and endpoint
**Architecture:** MCP Server 2.0 with compact two-tool design

**Revolutionary Two-Tool Architecture:**

Instead of exposing dozens of tools directly to the model, MCP Server 2.0 uses only **two MCP tools**:

- `appwrite_search_tools` - Searches the full Appwrite tool catalog based on natural language intent
- `appwrite_call_tool` - Executes a specific Appwrite operation by name

**Key Benefits:**
- **Zero Configuration**: No service flags needed - all Appwrite services work automatically
- **Minimal Context Usage**: Full tool catalog stays internal, freeing up context for your code
- **Automatic Discovery**: All services (databases, users, storage, functions, messaging, sites, teams) are available by default
- **Smart Search**: AI searches for the right tool based on your intent
- **Validation on Startup**: Credentials and scopes are validated when the server starts, not on first tool call

**No More Service Flags!**

Previous versions required flags like `--users`, `--storage`, `--functions`, etc. These are **completely removed** in version 2.0. Simply run:

```json
{
  "command": "uvx",
  "args": ["mcp-server-appwrite"]
}
```

All services are automatically available without any configuration.

**Available Tools (via search and call pattern):**

The server provides access to all Appwrite services through the two-tool architecture:

**Core Services** (automatically available):
- **Databases**: Collections, documents, queries, indexes, attributes, transactions
- **Users**: User management, sessions, preferences, MFA, OAuth
- **Storage**: Buckets, file operations, image transformations, previews
- **Functions**: Serverless deployment, executions, variables, multiple runtimes
- **Messaging**: Email, SMS, push notifications, topics, subscribers
- **Sites**: Static sites, SSR applications, deployments, frameworks
- **Teams**: Team management, memberships, roles, invitations
- **Locale**: Country, language, currency, timezone data
- **Avatars**: Generate avatars, QR codes, favicons

**How It Works:**

1. **Search**: AI uses `appwrite_search_tools` with natural language (e.g., "create a user", "list databases")
2. **Discover**: Server searches internal catalog and returns matching tool definitions
3. **Execute**: AI calls `appwrite_call_tool` with the specific tool name and parameters
4. **Result**: Server executes the operation and returns the result

**Example Flow:**
```
User: "Create a new database called 'production'"
↓
AI: appwrite_search_tools(query="create database")
↓
Server: Returns tool definition for "databases_create"
↓
AI: appwrite_call_tool(tool_name="databases_create", arguments={...})
↓
Server: Executes and returns database creation result
```

### appwrite-docs

**Connection:** HTTPS API endpoint at `https://mcp-for-docs.appwrite.io`
**Authentication:** None required
**Type:** HTTP-based MCP server

**Available Tools:**

- `search_documentation` - Search Appwrite documentation with natural language
- `get_documentation_page` - Get specific documentation page content
- `list_documentation_sections` - List available documentation sections
- `get_api_reference` - Get API reference for specific endpoint
- `get_code_examples` - Get code examples for specific features

**Perfect for:**
- Learning Appwrite APIs and best practices
- Finding code examples and implementation patterns
- Troubleshooting errors and issues
- Understanding service capabilities
- Getting up-to-date documentation

## Tool Usage Examples

### Using the Two-Tool Architecture

**Example 1: Create a Database**

```javascript
// Step 1: Search for the right tool
appwrite_search_tools({
  "query": "create a new database"
})

// Returns: Tool definition for "databases_create"

// Step 2: Call the tool
appwrite_call_tool({
  "tool_name": "databases_create",
  "arguments": {
    "database_id": "main",
    "name": "Main Database",
    "enabled": true
  }
})
```

**Example 2: Create a User**

```javascript
// Search
appwrite_search_tools({
  "query": "create user with email and password"
})

// Call
appwrite_call_tool({
  "tool_name": "users_create",
  "arguments": {
    "user_id": "unique()",
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }
})
```

**Example 3: Upload a File**

```javascript
// Search
appwrite_search_tools({
  "query": "upload file to storage bucket"
})

// Call
appwrite_call_tool({
  "tool_name": "storage_create_file",
  "arguments": {
    "bucket_id": "avatars",
    "file_id": "unique()",
    "file": "/path/to/avatar.jpg",
    "permissions": ["read(\"any\")"]
  }
})
```

### Natural Language Queries

The search tool understands natural language, so you can ask in various ways:

- "How do I create a collection?"
- "List all users in my project"
- "Upload an image to storage"
- "Deploy a serverless function"
- "Send an email notification"

The AI will automatically search for the right tool and execute it.

## Common Workflows

### Workflow 1: Complete Database Setup

```javascript
// The AI will automatically search and call the right tools

// Step 1: Create database
"Create a database called 'main'"
// AI searches for and calls: databases_create

// Step 2: Create collection
"Create a collection called 'posts' in the main database with public read access"
// AI searches for and calls: databases_create_collection

// Step 3: Add attributes
"Add a string attribute 'title' (max 255 chars, required) to the posts collection"
"Add a string attribute 'content' (max 10000 chars, required) to the posts collection"
"Add a datetime attribute 'published_at' (optional) to the posts collection"
// AI searches for and calls: databases_create_string_attribute (x2), databases_create_datetime_attribute

// Step 4: Create index
"Create an index on the title field for the posts collection"
// AI searches for and calls: databases_create_index

// Step 5: Create first document
"Create a post with title 'Getting Started with Appwrite' and content '...'"
// AI searches for and calls: databases_create_document
```

### Workflow 2: User Authentication Setup

```javascript
// Natural language workflow

"Create an admin user with email admin@example.com"
// AI: searches for users_create, executes with proper parameters

"Create a team called 'Engineering Team'"
// AI: searches for teams_create, executes

"Add the admin user to the Engineering Team as owner"
// AI: searches for teams_create_membership, executes

"Set user preferences for dark theme and email notifications"
// AI: searches for users_update_prefs, executes
```

### Workflow 3: File Upload and Management

```javascript
// Conversational approach

"Create a storage bucket for user documents with 10MB limit, allowing PDF and DOCX files"
// AI: searches for storage_create_bucket, configures properly

"Upload document.pdf to the documents bucket"
// AI: searches for storage_create_file, handles upload

"Get the download URL for the uploaded file"
// AI: searches for storage_get_file_download, returns URL

"List all files in the documents bucket"
// AI: searches for storage_list_files, returns list
```

### Workflow 4: Serverless Function Deployment

```javascript
// Simple natural language commands

"Create a function called 'Process Payment' using Node.js 18 runtime"
// AI: searches for functions_create, sets up function

"Deploy the function code from /path/to/function.tar.gz"
// AI: searches for functions_create_deployment, handles deployment

"Set environment variable STRIPE_API_KEY for the function"
// AI: searches for functions_create_variable, adds variable

"Execute the function with payment data"
// AI: searches for functions_create_execution, runs function
```

## Best Practices

### ✅ Do:

- **Use document-level permissions** for fine-grained access control
- **Enable document security** on collections with sensitive data
- **Create indexes** for frequently queried attributes
- **Use `unique()` for IDs** to auto-generate unique identifiers
- **Validate data** before creating documents
- **Handle errors gracefully** with try-catch blocks
- **Use queries efficiently** with proper filters and limits
- **Store sensitive data** in environment variables
- **Enable file security** on storage buckets
- **Set appropriate file size limits** on buckets
- **Use transactions** for atomic multi-document operations
- **Test with sandbox** before production deployment
- **Monitor function executions** for errors and performance
- **Use webhooks** for real-time event handling
- **Keep API keys secure** - never commit to version control

### ❌ Don't:

- **Expose API keys** in client-side code
- **Skip permission configuration** - always set appropriate permissions
- **Create collections without attributes** - define schema first
- **Use weak passwords** for user accounts
- **Ignore query limits** - always paginate large result sets
- **Store large files** without compression
- **Hardcode credentials** in function code
- **Skip error handling** in production code
- **Use `read("any")` for sensitive data** - restrict access properly
- **Forget to enable collections** - disabled collections are inaccessible
- **Mix test and production data** - use separate projects
- **Skip backup strategy** - export data regularly
- **Ignore rate limits** - implement proper throttling
- **Use synchronous functions** for long operations - use async

## Troubleshooting

### Error: "Invalid API key"
**Cause:** Incorrect or missing API key
**Solution:**
1. Verify API key in Appwrite console
2. Check environment variable is set correctly
3. Ensure API key has required scopes
4. Regenerate key if compromised

### Error: "Database not found"
**Cause:** Invalid database ID or database doesn't exist
**Solution:**
1. Call `list_databases` to verify database exists
2. Check database ID spelling
3. Ensure database is enabled
4. Create database if it doesn't exist

### Error: "Collection not found"
**Cause:** Invalid collection ID or collection doesn't exist
**Solution:**
1. Call `list_collections` to verify collection exists
2. Check collection ID spelling
3. Ensure collection is enabled
4. Create collection if it doesn't exist

### Error: "Document not found"
**Cause:** Invalid document ID or document was deleted
**Solution:**
1. Verify document ID is correct
2. Check if document was deleted
3. Ensure user has read permissions
4. Query collection to find document

### Error: "Attribute not found"
**Cause:** Trying to query or set non-existent attribute
**Solution:**
1. Call `list_attributes` to see available attributes
2. Create attribute before using it
3. Check attribute key spelling
4. Wait for attribute creation to complete (async operation)

### Error: "Permission denied"
**Cause:** User doesn't have required permissions
**Solution:**
1. Check document/collection permissions
2. Verify user is authenticated
3. Update permissions to grant access
4. Use `read("any")` for public data

### Error: "File too large"
**Cause:** File exceeds bucket's maximum file size
**Solution:**
1. Check bucket's `maximum_file_size` setting
2. Compress file before upload
3. Update bucket settings to allow larger files
4. Split large files into chunks

### Error: "Invalid file extension"
**Cause:** File type not allowed in bucket
**Solution:**
1. Check bucket's `allowed_file_extensions`
2. Convert file to allowed format
3. Update bucket to allow file type
4. Remove extension restriction if appropriate

### Error: "Function execution failed"
**Cause:** Error in function code or timeout
**Solution:**
1. Check function logs in Appwrite console
2. Verify function has required environment variables
3. Increase timeout if needed
4. Test function locally before deployment
5. Check function runtime is correct

### Error: "Rate limit exceeded"
**Cause:** Too many requests in short time
**Solution:**
1. Implement exponential backoff
2. Cache frequently accessed data
3. Batch operations when possible
4. Upgrade plan for higher limits
5. Optimize query patterns

## Configuration

**Authentication Required:** Appwrite API key, Project ID, and Endpoint URL

**Setup Steps:**

1. Create Appwrite account at https://cloud.appwrite.io
2. Create a new project or select existing one
3. Navigate to Settings → API Keys
4. Create API key with required scopes:
   - `databases.read`, `databases.write` for database operations
   - `users.read`, `users.write` for user management
   - `files.read`, `files.write` for storage operations
   - `functions.read`, `functions.write` for serverless functions
   - Or select "All" for full access
5. Copy Project ID from Settings page
6. Note your region (e.g., `nyc`, `fra`, `sfo`)
7. Set environment variables:
   ```bash
   export APPWRITE_PROJECT_ID="your-project-id"
   export APPWRITE_API_KEY="your-api-key"
   export APPWRITE_ENDPOINT="https://nyc.cloud.appwrite.io/v1"
   ```

**MCP Configuration:**

**Minimal Configuration (MCP Server 2.0):**
```json
{
  "mcpServers": {
    "appwrite-api": {
      "command": "uvx",
      "args": ["mcp-server-appwrite"],
      "env": {
        "APPWRITE_PROJECT_ID": "${APPWRITE_PROJECT_ID}",
        "APPWRITE_API_KEY": "${APPWRITE_API_KEY}",
        "APPWRITE_ENDPOINT": "${APPWRITE_ENDPOINT}"
      }
    }
  }
}
```

**With Documentation Server:**
```json
{
  "mcpServers": {
    "appwrite-api": {
      "command": "uvx",
      "args": ["mcp-server-appwrite"],
      "env": {
        "APPWRITE_PROJECT_ID": "${APPWRITE_PROJECT_ID}",
        "APPWRITE_API_KEY": "${APPWRITE_API_KEY}",
        "APPWRITE_ENDPOINT": "${APPWRITE_ENDPOINT}"
      }
    },
    "appwrite-docs": {
      "url": "https://mcp-for-docs.appwrite.io",
      "type": "http"
    }
  }
}
```

**Important Notes:**
- **No service flags needed** - All services are automatically available
- **Remove old flags** - If upgrading from v1.x, remove `--users`, `--storage`, `--functions`, etc.
- **Validation on startup** - Server validates credentials when it starts, not on first tool call
- **Using uvx** - Automatically fetches the latest version (0.4.1+)

## Tips

1. **Use natural language** - The search tool understands conversational queries
2. **All services available** - No need to enable specific services, everything works out of the box
3. **Minimal context usage** - MCP 2.0 architecture uses less context, leaving more room for your code
4. **Start with databases** - Most apps need data storage first
5. **Use document security** - Enable for collections with user-specific data
6. **Create indexes early** - Add indexes before large datasets
7. **Test permissions** - Verify access control works as expected
8. **Monitor usage** - Check Appwrite console for metrics
9. **Enable real-time** - Use subscriptions for live updates
10. **Batch operations** - Use transactions for related changes
11. **Cache strategically** - Reduce API calls with smart caching
12. **Read the docs** - Use the docs MCP server for guidance
13. **Use TypeScript** - Type safety prevents many errors
14. **Version your schema** - Track database structure changes
15. **Backup regularly** - Export data periodically
16. **Monitor logs** - Check function and API logs for issues
17. **Upgrade from v1.x** - Remove all service flags from your configuration

## Resources

- [Appwrite Documentation](https://appwrite.io/docs)
- [MCP Server 2.0 Announcement](https://appwrite.io/blog/post/announcing-appwrite-mcp-server-2)
- [MCP Server GitHub Repository](https://github.com/appwrite/mcp-for-api)
- [MCP Server on PyPI](https://pypi.org/project/mcp-server-appwrite/)
- [API Reference](https://appwrite.io/docs/references)
- [Quick Starts](https://appwrite.io/docs/quick-starts)
- [Database Guide](https://appwrite.io/docs/products/databases)
- [Authentication Guide](https://appwrite.io/docs/products/auth)
- [Storage Guide](https://appwrite.io/docs/products/storage)
- [Functions Guide](https://appwrite.io/docs/products/functions)
- [Sites Guide](https://appwrite.io/docs/products/sites)
- [Community Discord](https://appwrite.io/discord)
- [GitHub Repository](https://github.com/appwrite/appwrite)

---

**Package:** `mcp-server-appwrite` (Python via uvx)  
**Version:** 0.4.1+  
**Source:** Official Appwrite  
**License:** MIT  
**Connection:** Python MCP server with API key authentication  
**Architecture:** MCP Server 2.0 with two-tool design
