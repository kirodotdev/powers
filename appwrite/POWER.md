---
name: "appwrite"
displayName: "Appwrite Backend Platform"
description: "Build backend services with Appwrite - databases, authentication, storage, functions, and messaging for web and mobile apps"
keywords: ["appwrite", "backend", "database", "auth", "authentication", "storage", "functions", "serverless", "baas", "api", "users", "teams", "messaging"]
author: "Appwrite"
---

# Onboarding

Before using Appwrite MCP, ensure you have completed the following steps.

## Step 1: Validate Prerequisites

Check that the required tools are installed:

**For API Server:**
- **uv**: Required to run the Appwrite API MCP server
  - Verify with: `uv --version`
  - Install if missing: Follow instructions at https://docs.astral.sh/uv/getting-started/installation/
  - **CRITICAL**: If uv is not installed, DO NOT proceed with API server setup

**For Docs Server:**
- **Node.js and npm**: Required for the documentation MCP server
  - Verify with: `node --version` and `npm --version`
  - Install if missing: Download from https://nodejs.org/

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

## Step 3: Choose MCP Servers

This power provides two MCP servers:

- **appwrite-api**: Interact with Appwrite services (databases, users, storage, functions, etc.)
- **appwrite-docs**: Query Appwrite documentation for guidance and examples

You can enable one or both depending on your needs. The API server is essential for building applications, while the docs server helps with learning and troubleshooting.

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

**Package:** `mcp-server-appwrite` (via uvx)
**Connection:** Python-based MCP server
**Authentication:** API key with project ID and endpoint

**Command-line Arguments:**

By default, only Database tools are enabled. Use these flags to enable additional APIs:

- `--tables-db` - TablesDB API (relational database operations)
- `--users` - Users API (user management and authentication)
- `--teams` - Teams API (team and membership management)
- `--storage` - Storage API (file upload, download, management)
- `--functions` - Functions API (serverless function deployment)
- `--messaging` - Messaging API (email, SMS, push notifications)
- `--locale` - Locale API (country, language, currency data)
- `--avatars` - Avatars API (generate avatars and QR codes)
- `--sites` - Sites API (deploy static sites and SSR apps)
- `--databases` - Legacy Databases API
- `--all` - Enable all Appwrite APIs

**Important:** Only enable the APIs you need. Each enabled API adds tools to the LLM context, reducing available context window. Start with databases and add others as needed.

**Available Tools (varies by enabled APIs):**

**Databases API** (enabled by default):
- `mcp_appwrite_api_databases_create` - Create a new database
- `mcp_appwrite_api_databases_list` - List all databases
- `mcp_appwrite_api_databases_get` - Get database details
- `mcp_appwrite_api_databases_update` - Update database properties
- `mcp_appwrite_api_databases_delete` - Delete a database
- `mcp_appwrite_api_databases_create_collection` - Create a collection
- `mcp_appwrite_api_databases_list_collections` - List collections
- `mcp_appwrite_api_databases_get_collection` - Get collection details
- `mcp_appwrite_api_databases_update_collection` - Update collection
- `mcp_appwrite_api_databases_delete_collection` - Delete collection
- `mcp_appwrite_api_databases_create_document` - Create a document
- `mcp_appwrite_api_databases_list_documents` - Query documents
- `mcp_appwrite_api_databases_get_document` - Get document by ID
- `mcp_appwrite_api_databases_update_document` - Update document
- `mcp_appwrite_api_databases_delete_document` - Delete document
- Plus attribute, index, and transaction management tools

**Users API** (with `--users` flag):
- `mcp_appwrite_api_users_create` - Create a new user
- `mcp_appwrite_api_users_list` - List all users
- `mcp_appwrite_api_users_get` - Get user details
- `mcp_appwrite_api_users_update_email` - Update user email
- `mcp_appwrite_api_users_update_password` - Update user password
- `mcp_appwrite_api_users_delete` - Delete a user
- Plus session, preferences, and MFA management tools

**Storage API** (with `--storage` flag):
- `mcp_appwrite_api_storage_create_bucket` - Create storage bucket
- `mcp_appwrite_api_storage_list_buckets` - List all buckets
- `mcp_appwrite_api_storage_create_file` - Upload a file
- `mcp_appwrite_api_storage_list_files` - List files in bucket
- `mcp_appwrite_api_storage_get_file` - Get file metadata
- `mcp_appwrite_api_storage_get_file_download` - Download file
- `mcp_appwrite_api_storage_get_file_preview` - Get image preview
- `mcp_appwrite_api_storage_delete_file` - Delete a file

**Functions API** (with `--functions` flag):
- `mcp_appwrite_api_functions_create` - Create a function
- `mcp_appwrite_api_functions_list` - List all functions
- `mcp_appwrite_api_functions_create_deployment` - Deploy function code
- `mcp_appwrite_api_functions_create_execution` - Execute a function
- `mcp_appwrite_api_functions_list_executions` - List function executions
- Plus variable and runtime management tools

**Messaging API** (with `--messaging` flag):
- `mcp_appwrite_api_messaging_create_email` - Send email message
- `mcp_appwrite_api_messaging_create_sms` - Send SMS message
- `mcp_appwrite_api_messaging_create_push` - Send push notification
- `mcp_appwrite_api_messaging_create_topic` - Create messaging topic
- `mcp_appwrite_api_messaging_create_subscriber` - Add subscriber
- Plus provider and target management tools

**Sites API** (with `--sites` flag):
- `mcp_appwrite_api_sites_create` - Create a new site
- `mcp_appwrite_api_sites_list` - List all sites
- `mcp_appwrite_api_sites_create_deployment` - Deploy site code
- `mcp_appwrite_api_sites_list_deployments` - List deployments
- `mcp_appwrite_api_sites_update_site_deployment` - Activate deployment
- Plus variable and framework management tools

### appwrite-docs

**Connection:** HTTPS API endpoint at `https://mcp-for-docs.appwrite.io`
**Authentication:** None required
**Type:** HTTP-based MCP server

**Available Tools:**

- `search_documentation` - Search Appwrite documentation
- `get_documentation_page` - Get specific documentation page
- `list_documentation_sections` - List available doc sections
- `get_api_reference` - Get API reference for specific endpoint
- `get_code_examples` - Get code examples for specific feature

## Tool Usage Examples

### Database Operations

**Create a database:**
```javascript
mcp_appwrite_api_databases_create({
  "database_id": "main",
  "name": "Main Database",
  "enabled": true
})
```

**Create a collection:**
```javascript
mcp_appwrite_api_databases_create_collection({
  "database_id": "main",
  "collection_id": "users",
  "name": "Users",
  "permissions": ["read(\"any\")"],
  "document_security": true
})
```

**Add attributes to collection:**
```javascript
// String attribute
mcp_appwrite_api_databases_create_string_attribute({
  "database_id": "main",
  "collection_id": "users",
  "key": "name",
  "size": 255,
  "required": true
})

// Email attribute
mcp_appwrite_api_databases_create_email_attribute({
  "database_id": "main",
  "collection_id": "users",
  "key": "email",
  "required": true
})

// Boolean attribute
mcp_appwrite_api_databases_create_boolean_attribute({
  "database_id": "main",
  "collection_id": "users",
  "key": "is_active",
  "required": true,
  "default": true
})
```

**Create a document:**
```javascript
mcp_appwrite_api_databases_create_document({
  "database_id": "main",
  "collection_id": "users",
  "document_id": "unique()",
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "is_active": true
  },
  "permissions": ["read(\"user:USER_ID\")"]
})
```

**Query documents:**
```javascript
mcp_appwrite_api_databases_list_documents({
  "database_id": "main",
  "collection_id": "users",
  "queries": [
    "equal(\"is_active\", true)",
    "orderDesc(\"$createdAt\")",
    "limit(10)"
  ]
})
```

### User Management

**Create a user:**
```javascript
mcp_appwrite_api_users_create({
  "user_id": "unique()",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Jane Smith"
})
```

**List users:**
```javascript
mcp_appwrite_api_users_list({
  "queries": ["limit(25)"],
  "search": "john"
})
```

**Update user email:**
```javascript
mcp_appwrite_api_users_update_email({
  "user_id": "USER_ID",
  "email": "newemail@example.com"
})
```

### Storage Operations

**Create a storage bucket:**
```javascript
mcp_appwrite_api_storage_create_bucket({
  "bucket_id": "avatars",
  "name": "User Avatars",
  "permissions": ["read(\"any\")"],
  "file_security": true,
  "enabled": true,
  "maximum_file_size": 5000000, // 5MB
  "allowed_file_extensions": ["jpg", "jpeg", "png", "gif"]
})
```

**Upload a file:**
```javascript
mcp_appwrite_api_storage_create_file({
  "bucket_id": "avatars",
  "file_id": "unique()",
  "file": "/path/to/avatar.jpg",
  "permissions": ["read(\"any\")"]
})
```

### Documentation Queries

**Search documentation:**
```javascript
search_documentation({
  "query": "real-time subscriptions",
  "limit": 5
})
```

**Get API reference:**
```javascript
get_api_reference({
  "endpoint": "/databases/{databaseId}/collections/{collectionId}/documents",
  "method": "POST"
})
```

## Common Workflows

### Workflow 1: Complete Database Setup

```javascript
// Step 1: Create database
const db = await mcp_appwrite_api_databases_create({
  "database_id": "main",
  "name": "Main Database",
  "enabled": true
})

// Step 2: Create collection
const collection = await mcp_appwrite_api_databases_create_collection({
  "database_id": "main",
  "collection_id": "posts",
  "name": "Blog Posts",
  "permissions": ["read(\"any\")"],
  "document_security": true
})

// Step 3: Add attributes
await mcp_appwrite_api_databases_create_string_attribute({
  "database_id": "main",
  "collection_id": "posts",
  "key": "title",
  "size": 255,
  "required": true
})

await mcp_appwrite_api_databases_create_string_attribute({
  "database_id": "main",
  "collection_id": "posts",
  "key": "content",
  "size": 10000,
  "required": true
})

await mcp_appwrite_api_databases_create_datetime_attribute({
  "database_id": "main",
  "collection_id": "posts",
  "key": "published_at",
  "required": false
})

// Step 4: Create index for queries
await mcp_appwrite_api_databases_create_index({
  "database_id": "main",
  "collection_id": "posts",
  "key": "title_index",
  "type": "key",
  "attributes": ["title"]
})

// Step 5: Create first document
await mcp_appwrite_api_databases_create_document({
  "database_id": "main",
  "collection_id": "posts",
  "document_id": "unique()",
  "data": {
    "title": "Getting Started with Appwrite",
    "content": "Appwrite is an amazing backend platform...",
    "published_at": "2024-02-05T10:00:00.000Z"
  }
})
```

### Workflow 2: User Authentication Setup

```javascript
// Step 1: Create admin user
const admin = await mcp_appwrite_api_users_create({
  "user_id": "unique()",
  "email": "admin@example.com",
  "password": "SecureAdminPass123!",
  "name": "Admin User"
})

// Step 2: Create team for organization
const team = await mcp_appwrite_api_teams_create({
  "team_id": "unique()",
  "name": "Engineering Team"
})

// Step 3: Add user to team
await mcp_appwrite_api_teams_create_membership({
  "team_id": team.id,
  "email": "admin@example.com",
  "roles": ["owner"],
  "url": "https://example.com/join-team"
})

// Step 4: Set user preferences
await mcp_appwrite_api_users_update_prefs({
  "user_id": admin.id,
  "prefs": {
    "theme": "dark",
    "notifications": true
  }
})
```

### Workflow 3: File Upload and Management

```javascript
// Step 1: Create storage bucket
const bucket = await mcp_appwrite_api_storage_create_bucket({
  "bucket_id": "documents",
  "name": "User Documents",
  "permissions": ["read(\"any\")"],
  "file_security": true,
  "enabled": true,
  "maximum_file_size": 10000000, // 10MB
  "allowed_file_extensions": ["pdf", "doc", "docx", "txt"]
})

// Step 2: Upload file
const file = await mcp_appwrite_api_storage_create_file({
  "bucket_id": "documents",
  "file_id": "unique()",
  "file": "/path/to/document.pdf",
  "permissions": ["read(\"user:USER_ID\")"]
})

// Step 3: Get file download URL
const download = await mcp_appwrite_api_storage_get_file_download({
  "bucket_id": "documents",
  "file_id": file.id
})

// Step 4: List all files
const files = await mcp_appwrite_api_storage_list_files({
  "bucket_id": "documents",
  "queries": ["limit(25)"]
})
```

### Workflow 4: Serverless Function Deployment

```javascript
// Step 1: Create function
const func = await mcp_appwrite_api_functions_create({
  "function_id": "unique()",
  "name": "Process Payment",
  "runtime": "node-18.0",
  "execute": ["any"],
  "events": [],
  "schedule": "",
  "timeout": 15
})

// Step 2: Create deployment
const deployment = await mcp_appwrite_api_functions_create_deployment({
  "function_id": func.id,
  "code": "/path/to/function.tar.gz",
  "activate": true,
  "entrypoint": "index.js"
})

// Step 3: Set environment variables
await mcp_appwrite_api_functions_create_variable({
  "function_id": func.id,
  "key": "STRIPE_API_KEY",
  "value": "sk_test_...",
  "secret": true
})

// Step 4: Execute function
const execution = await mcp_appwrite_api_functions_create_execution({
  "function_id": func.id,
  "body": JSON.stringify({ amount: 1000, currency: "usd" }),
  "xasync": false
})
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

For API server (minimal - databases only):
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

For API server (with additional services):
```json
{
  "mcpServers": {
    "appwrite-api": {
      "command": "uvx",
      "args": [
        "mcp-server-appwrite",
        "--users",
        "--storage",
        "--functions",
        "--sites"
      ],
      "env": {
        "APPWRITE_PROJECT_ID": "${APPWRITE_PROJECT_ID}",
        "APPWRITE_API_KEY": "${APPWRITE_API_KEY}",
        "APPWRITE_ENDPOINT": "${APPWRITE_ENDPOINT}"
      }
    }
  }
}
```

For documentation server:
```json
{
  "mcpServers": {
    "appwrite-docs": {
      "url": "https://mcp-for-docs.appwrite.io",
      "type": "http"
    }
  }
}
```

**Permissions:** API key should have appropriate scopes for intended operations. Use least privilege principle - only grant necessary permissions.

## Tips

1. **Start with databases** - Most apps need data storage first
2. **Use document security** - Enable for collections with user-specific data
3. **Create indexes early** - Add indexes before large datasets
4. **Test permissions** - Verify access control works as expected
5. **Use query helpers** - Leverage Appwrite's query builder
6. **Monitor usage** - Check Appwrite console for metrics
7. **Enable real-time** - Use subscriptions for live updates
8. **Batch operations** - Use transactions for related changes
9. **Cache strategically** - Reduce API calls with smart caching
10. **Read the docs** - Use the docs MCP server for guidance
11. **Use TypeScript** - Type safety prevents many errors
12. **Version your schema** - Track database structure changes
13. **Test locally** - Use Appwrite CLI for local development
14. **Backup regularly** - Export data periodically
15. **Monitor logs** - Check function and API logs for issues

## Resources

- [Appwrite Documentation](https://appwrite.io/docs)
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
**Source:** Official Appwrite  
**License:** BSD-3-Clause  
**Connection:** Python MCP server with API key authentication
