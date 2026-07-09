---
inclusion: always
---

# Postman MCP Server Steering Guide

This steering file provides comprehensive guidance for using the Postman MCP (Model Context Protocol) server to manage API collections, workspaces, environments, and automated testing workflows.

## When to Use the Postman MCP Server

Use Postman MCP tools when you need to:
- **Create and manage API collections**: Build, update, and organize API request collections
- **Test API endpoints**: Run automated tests with assertions and validations
- **Manage environments**: Create and configure environment variables for different deployment stages
- **Generate collections from source code**: Define your API in Postman
- **Run collection tests**: Execute test suites and analyze results
- **Sync API with Postman**: Keep collections in sync with source code
- **Manage workspaces**: Organize collections and environments by project or team

## Core Principles

### 0. Always Validate Against Postman Collection Schema

**CRITICAL**: All collections MUST conform to the official Postman Collection Format schema.

**Schema Requirements**:
- **Schema URL**: `https://schema.getpostman.com/json/collection/v2.1.0/collection.json`
- **Version**: Use Collection Format v2.1.0 (current standard)
- **Validation**: Validate collection structure before creating or updating

**Required Fields in Collection**:

```json
{
  "info": {
    "name": "Collection Name",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    // Array of requests or folders
  ]
}
```

**Validation Steps**:

1. **Before Creating Collection**:
   - Verify `info.schema` field is present and correct
   - Validate `info.name` is provided
   - Ensure `item` array exists (can be empty)
   - Check all requests have required fields: `name`, `request.method`, `request.url`

2. **Before Updating Collection**:
   - Preserve existing collection structure
   - Validate new/modified requests against schema
   - Ensure no breaking changes to collection format
   - Maintain backward compatibility

3. **Schema Validation Checklist**:
   - ✅ `info.name` - Collection name (required)
   - ✅ `info.schema` - Schema URL (required)
   - ✅ `item` - Array of requests/folders (required)
   - ✅ Request `name` - Request name (required)
   - ✅ Request `method` - HTTP method (required)
   - ✅ Request `url` - URL object or string (required)
   - ✅ Event scripts - Valid JavaScript in `exec` array
   - ✅ Variables - Valid variable definitions

**Common Schema Violations to Avoid**:
- ❌ Missing `info.schema` field
- ❌ Invalid HTTP method (must be GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- ❌ Malformed URL object
- ❌ Invalid event listener (must be "test" or "prerequest")
- ❌ Non-array `exec` in script objects
- ❌ Invalid variable types

**Schema Reference**:
- Full schema documentation: https://schema.postman.com/
- Collection Format v2.1.0: https://schema.postman.com/json/collection/v2.1.0/draft-07/docs/index.html

**Example Valid Collection Structure**:

```json
{
  "info": {
    "name": "My API Collection",
    "description": "API testing collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{API_URL}}/users",
          "host": ["{{API_URL}}"],
          "path": ["users"]
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "type": "text/javascript",
            "exec": [
              "pm.test('Status code is 200', function () {",
              "    pm.response.to.have.status(200);",
              "});"
            ]
          }
        }
      ]
    }
  ],
  "variable": []
}
```

### 1. Check for Existing Resources First

**ALWAYS** check for existing workspaces and collections before creating new ones:

**Step 1: Check .postman.json**
- Read `.postman.json` if it exists in the project root
- If file exists and contains valid IDs, verify resources still exist
- Ask user: "Found existing Postman configuration. Would you like to use the existing workspace '{workspaceName}' and collection '{collectionName}'?"

**Step 2: Search User's Workspaces**
- Use `getWorkspaces` with `createdBy` parameter to list user's workspaces
- Look for workspaces with similar names to the project
- If found, ask user: "Found workspace '{name}'. Would you like to use this workspace or create a new one?"

**Step 3: Search Collections in Workspace**
- If workspace is selected, use `getCollections` to list existing collections
- Look for collections with similar names or matching API endpoints
- If found, ask user: "Found collection '{name}' in this workspace. Would you like to update this collection or create a new one?"

**Step 4: Get User Confirmation**
- Present options clearly:
  - Option A: Use existing workspace/collection (provide IDs and names)
  - Option B: Create new workspace/collection
  - Option C: Update existing collection with new endpoints
- Wait for explicit user confirmation before proceeding
- Never assume - always ask!

**Example Confirmation Flow**:
```
🔍 Checking for existing Postman resources...

Found existing configuration in .postman.json:
- Workspace: "CRUD API Demo" (ID: bcfb3f2f-7fdc-45b6-aa17-a21292148c6d)
- Collection: "CRUD API Demo" (ID: 89e5ec3f-66a3-48eb-804f-eb17926f4b9e)
- Environment: "CRUD API - Local" (ID: e719c6ad-cf2c-470e-8efa-71c14f3e20a4)

Would you like to:
A) Use existing resources
B) Create new workspace and collection
C) Use existing workspace but create new collection

Please confirm your choice (A/B/C):
```

### 2. Always Save Configuration
Store all Postman resource IDs in `.postman.json` for reusability:
- `workspaceId` - Workspace identifier
- `collectionId` - Collection identifier
- `collectionUid` - Full collection UID (format: `{userId}-{collectionId}`)
- `environmentId` - Environment identifier
- `environmentUid` - Full environment UID (format: `{userId}-{environmentId}`)
- Include metadata: `baseUrl`, `testResults`

### 3. Use Variables Everywhere - Best Practices

**CRITICAL**: Always use variables instead of hardcoded values for maximum flexibility and reusability.

**Sensitive Data**: Always use `type: "secret"` for sensitive data like API keys, passwords, and authentication tokens. This masks the values in the Postman UI and prevents accidental exposure.

**Variable Scopes** (from broadest to narrowest):
1. **Collection** - Available throughout a collection (configuration, default setup)
2. **Environment** - Scope work to different environments (auth, URLs)

**Variable Naming Conventions**:
- Use descriptive, UPPERCASE names: `API_URL`, `AUTH_TOKEN`, `USER_ID`
- Use underscores for multi-word names: `BASE_URL`, `API_KEY`, `TEST_ITEM_ID`
- Prefix by purpose: `TEST_`, `TEMP_`, `PROD_`, `DEV_`
- Be consistent across collections

**What to Store as Variables**:

**Environment Variables** (different per environment):
- ✅ API base URLs: `{{API_URL}}`, `{{BASE_URL}}`
- ✅ Authentication tokens: `{{API_KEY}}`, `{{AUTH_TOKEN}}`
- ✅ Environment-specific data sets: `{{COLLECTIONID}}`, `{{USERID}}`

**Collection Variables** (same across environments):
- ✅ API version: `{{API_VERSION}}`
- ✅ Timeout values: `{{REQUEST_TIMEOUT}}`
- ✅ Retry counts: `{{MAX_RETRIES}}`
- ✅ Common headers: `{{CONTENT_TYPE}}`

**Dynamic Variables** (set in test scripts):
- ✅ Test data IDs: `{{test_item_id}}`, `{{user_id}}`
- ✅ Temporary tokens: `{{temp_token}}`
- ✅ Response values: `{{created_resource_id}}`
- ✅ Timestamps: `{{test_timestamp}}`

**Variable Usage Syntax**:
```
URL: {{API_URL}}/items/{{item_id}}
Header: Authorization: Bearer {{AUTH_TOKEN}}
Body: {"userId": "{{user_id}}", "timestamp": "{{$timestamp}}"}
```

**Built-in Dynamic Variables** (Postman provides):
- `{{$guid}}` - UUID v4
- `{{$timestamp}}` - Current Unix timestamp
- `{{$randomInt}}` - Random integer (0-1000)
- `{{$randomUUID}}` - Random UUID
- `{{$randomEmail}}` - Random email
- `{{$randomFirstName}}`, `{{$randomLastName}}` - Random names

**Setting Variables in Scripts**:
```javascript
// Set collection variable
pm.collectionVariables.set('item_id', pm.response.json().id);

// Set environment variable
pm.environment.set('auth_token', pm.response.json().token);

// Get variable value
const apiUrl = pm.environment.get('API_URL');
const itemId = pm.collectionVariables.get('item_id');
```

**Variable Best Practices**:

1. **Never Hardcode Values**
   - ❌ Bad: `https://api.example.com/users`
   - ✅ Good: `{{API_URL}}/users`

2. **Use Appropriate Scope**
   - Environment-specific → Environment variables
   - Collection-wide → Collection variables
   - Temporary → Local variables in scripts

3. **Sensitive Data**
   - Always set `type: "secret"` for sensitive variables (passwords, tokens, API keys)
   - This masks values in the Postman UI and prevents accidental exposure
   - Never share sensitive values in shared collections or version control

4. **Chain Requests with Variables**
   ```javascript
   // Request 1: Create user
   pm.test('Save user ID', function() {
       pm.collectionVariables.set('user_id', pm.response.json().id);
   });
   
   // Request 2: Get user details
   // URL: {{API_URL}}/users/{{user_id}}
   ```

5. **Default Values**
   - Provide default values for optional variables
   - Document expected variable format
   - Include example values in descriptions

6. **Variable Documentation**
   - Add descriptions to all variables
   - Explain purpose and expected format
   - Include example values

**Example Environment Setup**:
```json
{
  "name": "Local Development",
  "values": [
    {
      "key": "API_URL",
      "value": "http://localhost:3000",
      "enabled": true,
      "description": "Base URL for API endpoints"
    },
    {
      "key": "AUTH_TOKEN",
      "value": "",
      "enabled": true,
      "type": "secret",
      "description": "Bearer token for authentication"
    }
  ]
}
```

**Variable Validation**:
```javascript
// Validate required variables exist
pm.test('Required variables are set', function() {
    pm.expect(pm.environment.get('API_URL')).to.not.be.undefined;
    pm.expect(pm.environment.get('AUTH_TOKEN')).to.not.be.undefined;
});
```

### 4. Use Environments for Configuration
Always create environments to manage different deployment stages:
- **Local Development**: `http://localhost:3000`
- **Staging**: `https://staging-api.example.com`
- **Production**: `https://api.example.com`

### 5. Add Comprehensive Tests
Include test scripts in all requests to validate:
- HTTP status codes
- Response schema structure
- Data integrity and correctness
- Performance (response time)
- Headers (Content-Type, CORS)

---

## Workflow Patterns

### Pattern 1: Create Workspace and Collection from API

**When to use**: Starting a new API testing project

**Steps**:

**STEP 0: Check for Existing Resources (REQUIRED)**
   
   a. **Check .postman.json file**
   ```
   - Read .postman.json from project root
   - If exists, extract workspaceId, collectionId, environmentId
   - Verify resources still exist using getWorkspace, getCollection
   - If valid, present to user and ask for confirmation
   ```

   b. **Search user's workspaces**
   ```
   Use: getAuthenticatedUser (to get user ID)
   Then: getWorkspaces with createdBy parameter
   - List all user's workspaces
   - Look for names matching project (fuzzy match)
   - Present matches to user for selection
   ```

   c. **Search collections in selected workspace**
   ```
   Use: getCollections with workspace parameter
   - List all collections in workspace
   - Look for names matching API/project
   - Present matches to user for selection
   ```

   d. **Get user confirmation**
   ```
   Present options:
   1. Use existing workspace + collection (if found)
   2. Use existing workspace + create new collection
   3. Create new workspace + new collection
   4. Update existing collection with new endpoints
   
   Wait for user response - DO NOT proceed without confirmation!
   ```

**STEP 1: Analyze the API code/specification**
   - Read API implementation or OpenAPI spec
   - Identify all endpoints, methods, and parameters
   - Note authentication requirements

**STEP 2: Create or use workspace**
   ```
   If user chose to create new:
     Use: createWorkspace
     Parameters: name, type (team/personal), description
   
   If user chose existing:
     Use workspaceId from selection
   ```

**STEP 3: Create or update collection (WITH SCHEMA VALIDATION)**
   ```
   CRITICAL: Validate collection against Postman Collection Format v2.1.0 schema
   
   Schema validation steps:
   1. Verify required fields:
      - info.name (string, required)
      - info.schema (must be "https://schema.getpostman.com/json/collection/v2.1.0/collection.json")
      - item (array, required)
   2. Validate each request:
      - name (string, required)
      - request.method (valid HTTP method, required)
      - request.url (string or object, required)
   3. Validate event scripts:
      - listen must be "test" or "prerequest"
      - script.exec must be array of strings
   4. Validate variables:
      - Must have key or id field
      - Type must be: string, boolean, any, or number
   
   If creating new:
     Use: createCollection
     Parameters: workspace ID, validated collection schema
     Include: All endpoints with request details
     Ensure: info.schema field is set correctly
   
   If updating existing:
     Use: putCollection
     Parameters: collectionId, validated updated collection schema
     Preserve: existing test scripts where applicable
     Maintain: collection IDs and structure
   
   Common validation errors to avoid:
   - Missing info.schema field
   - Invalid HTTP method (must be uppercase: GET, POST, PUT, DELETE, etc.)
   - Malformed URL object
   - Invalid event listener (not "test" or "prerequest")
   - Non-array exec in script
   - Missing required fields in requests
   ```

**STEP 4: Add test scripts**
   - Add as `event` objects with `listen: "test"`
   - Include assertions for status codes, response structure, data validation
   - Use `pm.test()` for each assertion
   - Save dynamic values with `pm.collectionVariables.set()`

**STEP 5: Create or update environment**
   ```
   If creating new:
     Use: createEnvironment
     Parameters: workspace ID, name, values array
     Include: API_URL, region, authentication tokens
   
   If updating existing:
     Use: putEnvironment
     Parameters: environmentId, updated values
   ```

**STEP 6: Save configuration**
   - Write all IDs to `.postman.json`
   - Include workspace name, collection name, environment name
   - Add timestamp and metadata
   - Preserve any existing metadata (testResults, etc.)

**Example .postman.json structure (Multi-Workspace Support)**:
```json
{
  "version": "0.1",
  "project": {
    "name": "My API Project",
    "baseUrl": "https://api.example.com",
    "region": "us-east-1",
    "deployedAt": "2025-11-20T19:03:04Z"
  },
  "default": {
    "workspace": "main-workspace",
    "collection": "api-tests",
    "environment": "local"
  },
  "workspaces": {
    "main-workspace": {
      "id": "workspace-uuid",
      "name": "My API Project",
      "type": "team",
      "description": "Main workspace for API testing",
      "createdAt": "2025-11-20T19:00:00Z"
    },
    "staging-workspace": {
      "id": "staging-workspace-uuid",
      "name": "My API Project - Staging",
      "type": "team",
      "description": "Staging environment testing",
      "createdAt": "2025-11-20T19:00:00Z"
    }
  },
  "collections": {
    "api-tests": {
      "id": "collection-uuid",
      "uid": "userId-collection-uuid",
      "name": "API Tests",
      "workspace": "main-workspace",
      "description": "Main API test suite",
      "requestCount": 10,
      "createdAt": "2025-11-20T19:02:00Z",
      "lastTestRun": "2025-11-20T19:10:00Z",
      "testResults": {
        "totalTests": 12,
        "passed": 11,
        "failed": 1,
        "successRate": "91.7%"
      }
    },
    "integration-tests": {
      "id": "integration-collection-uuid",
      "uid": "userId-integration-collection-uuid",
      "name": "Integration Tests",
      "workspace": "main-workspace",
      "description": "End-to-end integration tests",
      "requestCount": 5,
      "createdAt": "2025-11-20T19:03:00Z"
    }
  },
  "environments": {
    "local": {
      "id": "env-uuid",
      "uid": "userId-env-uuid",
      "name": "Local Development",
      "workspace": "main-workspace",
      "variables": {
        "API_URL": "http://localhost:3000",
        "API_KEY": "local-dev-key"
      },
      "createdAt": "2025-11-20T19:02:30Z"
    },
    "staging": {
      "id": "staging-env-uuid",
      "uid": "userId-staging-env-uuid",
      "name": "Staging Environment",
      "workspace": "staging-workspace",
      "variables": {
        "API_URL": "https://staging-api.example.com",
        "API_KEY": "staging-key"
      },
      "createdAt": "2025-11-20T19:02:45Z"
    },
    "production": {
      "id": "prod-env-uuid",
      "uid": "userId-prod-env-uuid",
      "name": "Production Environment",
      "workspace": "main-workspace",
      "variables": {
        "API_URL": "https://api.example.com",
        "API_KEY": "prod-key"
      },
      "createdAt": "2025-11-20T19:03:00Z"
    }
  }
}
```

**Structure Explanation**:
- `version`: Configuration file version
- `project`: Global project metadata
- `default`: Default workspace/collection/environment keys to use
- `workspaces`: Object with workspace keys mapping to workspace details
- `collections`: Object with collection keys mapping to collection details
- `environments`: Object with environment keys mapping to environment details

---

### Pattern 2: Run Collection Tests

**When to use**: Testing API endpoints, validating deployments, CI/CD integration

**Prerequisites**:
- Collection must exist with test scripts
- Environment must be configured with API URL
- API server must be running and accessible

**Steps**:

**STEP 0: Verify Resources Exist (REQUIRED)**
   
   a. **Check .postman.json**
   ```
   - Read .postman.json from project root
   - If missing, inform user and ask them to create workspace/collection first
   ```

   b. **Verify collection exists**
   ```
   Use: getCollection with collectionId
   - If not found, inform user collection was deleted
   - Ask if they want to recreate it or use a different collection
   - List available collections in workspace for selection
   ```

   c. **Verify environment exists**
   ```
   Use: getEnvironment with environmentId
   - If not found, inform user environment was deleted
   - Ask if they want to recreate it or use a different environment
   - List available environments in workspace for selection
   ```

   d. **Confirm with user**
   ```
   Display:
   - Collection name and ID
   - Environment name and ID
   - Number of requests in collection
   - API URL from environment
   
   Ask: "Ready to run tests with these resources? (Y/N)"
   Wait for confirmation before proceeding
   ```

**STEP 1: Read configuration**
   - Load `.postman.json` (already done in STEP 0)
   - Extract `collectionId` or `collectionUid`
   - Extract `environmentId` for variable substitution

**STEP 2: Verify API availability**
   - If the target API is a local server, ensure it is running before executing the collection
   - For remote APIs (e.g. staging, production, cloud endpoints), skip this check

**STEP 3: Run collection**
   ```
   Use: runCollection
   Parameters: 
     - collectionId (required)
     - environmentId (always pass if available — environment variables must be resolved for tests to work correctly)
     - iterationCount (default: 1)
     - requestTimeout (default: 60000ms)
   ```

**STEP 4: Analyze results**
   - Display summary: total tests, passed, failed, success rate
   - Show breakdown by endpoint/request
   - Highlight failed tests with error details
   - Calculate performance metrics (response times)

**STEP 5: Offer to fix failures**
   - If tests fail, analyze the error messages
   - Suggest fixes: API code changes, test adjustments, configuration updates
   - Offer to update collection or environment

**Result display format**:
```
📊 Overall Statistics
- Total Tests: 12
- Passed: 11 ✅
- Failed: 1 ❌
- Success Rate: 91.7%

🧪 Test Results by Endpoint
1. GET /items - ✅ All Passed (5/5)
2. POST /items - ✅ All Passed (3/3)
3. GET /items/{id} - ⚠️ Partial (1/2)
   - Failed: CORS headers check
```

---


### Pattern 3: Generate Collection from OpenAPI Specification

**When to use**: You have an OpenAPI/Swagger specification file

**Steps**:
1. **Read OpenAPI specification**
   - Parse YAML or JSON specification file
   - Extract endpoints, methods, parameters, schemas

2. **Create or get workspace**
   - Use existing workspace or create new one

3. **Create or get Postman specification**
    - Use existing specification or create new one

4. **Generate collection from specification**
   ```
   Use: generateCollection
   Parameters:
     - specId (if specification already in Postman)
     - elementType: "collection"
     - name: collection name
     - options: generation options
   ```

5. **Enhance with tests**
   - Auto-generated collections may lack comprehensive tests
   - Add custom test scripts for business logic validation
   - Include edge case testing

6. **Create environment**
   - Extract base URL from specification
   - Add authentication variables
   - Include any specification-defined variables

---

### Pattern 4: Sync Collection with API Changes

**When to use**: API code or specification has been updated

**Steps**:
1. **Detect changes**
   - Compare current API implementation with collection
   - Check for new endpoints, modified parameters, changed responses

2. **Update collection**
   ```
   Use: putCollection (replace entire collection)
   Or: Update individual requests
   ```

3. **Sync with specification** (if using OpenAPI)
   ```
   Use: syncCollectionWithSpec
   Parameters: collectionUid, specId
   ```

4. **Update tests**
   - Adjust assertions for changed response schemas
   - Add tests for new endpoints
   - Remove tests for deprecated endpoints

5. **Re-run tests**
   - Validate all changes work correctly
   - Update test results in `.postman.json`

---

## Test Script Best Practices

### Essential Test Patterns

**1. Status Code Validation**
```javascript
pm.test('Status code is 200', function () {
    pm.response.to.have.status(200);
});
```

**2. Response Schema Validation**
```javascript
pm.test('Response has required fields', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('name');
});
```

**3. Data Type Validation**
```javascript
pm.test('Price is a number', function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.price).to.be.a('number');
});
```

**4. Data Integrity Validation**
```javascript
pm.test('Response matches request', function () {
    const jsonData = pm.response.json();
    const requestBody = JSON.parse(pm.request.body.raw);
    pm.expect(jsonData.id).to.equal(requestBody.id);
});
```

**5. Performance Validation**
```javascript
pm.test('Response time is acceptable', function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});
```

**6. Header Validation**
```javascript
pm.test('Content-Type is correct', function () {
    pm.response.to.have.header('Content-Type');
    pm.expect(pm.response.headers.get('Content-Type'))
        .to.include('application/json');
});
```

**7. Save Variables for Chained Requests**
```javascript
// Save response data for use in subsequent requests
pm.collectionVariables.set('item_id', pm.response.json().id);
pm.collectionVariables.set('auth_token', pm.response.json().token);
```

### Error Handling Tests

**Test 404 Not Found**
```javascript
pm.test('Returns 404 for non-existent resource', function () {
    pm.response.to.have.status(404);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('error');
});
```

**Test 400 Bad Request**
```javascript
pm.test('Returns 400 for invalid data', function () {
    pm.response.to.have.status(400);
    const jsonData = pm.response.json();
    pm.expect(jsonData.error).to.exist;
});
```

---

## Configuration File Format

### Version 0.1 Format

**Structure**:
```json
{
  "version": "0.1",
  "project": { /* global metadata */ },
  "default": { /* default keys */ },
  "workspaces": { /* workspace objects */ },
  "collections": { /* collection objects */ },
  "environments": { /* environment objects */ }
}
```

---

## Resource Verification Best Practices

### Always Check Before Creating

**Rule**: Never create duplicate workspaces or collections without user confirmation

**Verification Checklist**:
1. ✅ Check `.postman.json` exists and is valid
2. ✅ Verify workspace still exists (not deleted)
3. ✅ Verify collection still exists (not deleted)
4. ✅ Verify environment still exists (not deleted)
5. ✅ Present findings to user with clear options
6. ✅ Wait for explicit user confirmation
7. ✅ Update `.postman.json` after any changes

### User Confirmation Templates

**Template 1: Found Existing Resources**
```
🔍 Found existing Postman configuration:

Workspace: "{workspaceName}"
  ID: {workspaceId}
  Type: {type}

Collection: "{collectionName}"
  ID: {collectionId}
  Requests: {requestCount}

Environment: "{environmentName}"
  ID: {environmentId}
  Variables: {variableCount}

Options:
  A) Use existing resources
  B) Create new workspace and collection
  C) Use existing workspace, create new collection
  D) Update existing collection

Your choice (A/B/C/D):
```

**Template 2: No Existing Resources**
```
🔍 No existing Postman configuration found.

Searched:
  ✓ .postman.json file (not found)
  ✓ Your workspaces (found {count} workspaces)
  ✓ Collections in workspaces (none match this project)

Would you like to create new resources? (Y/N):
```

**Template 3: Partial Match**
```
🔍 Found partial Postman configuration:

Found:
  ✓ Workspace: "{workspaceName}" (ID: {workspaceId})

Not Found:
  ✗ Collection for this API
  ✗ Environment configuration

Options:
  A) Use existing workspace, create collection and environment
  B) Create completely new workspace, collection, and environment

Your choice (A/B):
```

### Handling Deleted Resources

**If workspace was deleted**:
```
⚠️  Workspace "{workspaceName}" (ID: {workspaceId}) no longer exists.

Available workspaces:
  1. {workspace1Name} (ID: {id1})
  2. {workspace2Name} (ID: {id2})
  3. Create new workspace

Select option (1/2/3):
```

**If collection was deleted**:
```
⚠️  Collection "{collectionName}" (ID: {collectionId}) no longer exists.

Available collections in workspace "{workspaceName}":
  1. {collection1Name} (ID: {id1}) - {requestCount} requests
  2. {collection2Name} (ID: {id2}) - {requestCount} requests
  3. Create new collection

Select option (1/2/3):
```

### Fuzzy Matching for Discovery

When searching for existing resources, use fuzzy matching:

**Collection Name Matching**:
- API name: "E-Commerce API"
- Match: "E-Commerce API" (exact)
- Match: "ecommerce-api" (normalized)
- Match: "E-Commerce" (partial)
- Match: "Commerce API v2" (partial with version)

### Update vs Create Decision Tree

```
Does .postman.json exist?
├─ YES
│  ├─ Are IDs valid?
│  │  ├─ YES → Ask user: Use existing or create new?
│  │  └─ NO → Search for similar resources → Ask user
│  └─ Is file corrupted?
│     └─ YES → Delete and search for resources → Ask user
└─ NO
   └─ Search user's workspaces
      ├─ Found matches → Present options → Ask user
      └─ No matches → Confirm creation → Ask user
```

---

## Collection Structure Best Practices

### Organize by Resource
Group related endpoints together:
```
Collection: E-Commerce API
├── Products
│   ├── GET /products
│   ├── GET /products/{id}
│   ├── POST /products
│   └── DELETE /products/{id}
├── Orders
│   ├── GET /orders
│   ├── POST /orders
│   └── GET /orders/{id}
└── Users
    ├── GET /users
    └── POST /users
```

### Use Folders for Scenarios
Create folders for test scenarios:
```
Collection: API Tests
├── Happy Path Tests
│   ├── Create Item
│   ├── Get Item
│   └── Delete Item
├── Error Handling Tests
│   ├── Get Non-Existent Item (404)
│   └── Create Invalid Item (400)
└── Performance Tests
    └── Load Test - Get All Items
```

### Collection Variables
Use collection variables for:
- Test data IDs (set dynamically during test runs)
- Shared constants
- Temporary values between requests

### Environment Variables
Use environment variables for:
- API base URLs (different per environment)
- Authentication credentials
- Environment-specific configuration
- Region/deployment identifiers

---

## Common Pitfalls and Solutions

### ❌ Pitfall 1: Not Using Environments
**Problem**: Hardcoding URLs in requests
**Solution**: Always use `{{API_URL}}` variables and environments

### ❌ Pitfall 2: Missing Test Scripts
**Problem**: Running requests without validation
**Solution**: Add test scripts to every request

### ❌ Pitfall 3: Not Saving Configuration
**Problem**: Losing workspace/collection IDs
**Solution**: Always save to `.postman.json`

### ❌ Pitfall 4: Ignoring Failed Tests
**Problem**: Continuing with broken tests
**Solution**: Investigate and fix failures immediately

### ❌ Pitfall 5: Using curl Instead of Postman
**Problem**: Bypassing Postman's test framework
**Solution**: Always use Postman MCP tools for testing — never use curl or any other HTTP clients

---

## Integration with CI/CD

### Automated Testing Workflow
1. Deploy API to environment
2. Update environment variables in Postman
3. Run collection tests via MCP
4. Parse test results
5. Fail build if tests fail
6. Generate test report

### Example Test Report Structure
```markdown
# API Test Results

**Environment**: Production
**Collection**: E-Commerce API v2
**Date**: 2025-11-20 19:10:00 UTC

## Summary
- Total Tests: 45
- Passed: 43 ✅
- Failed: 2 ❌
- Success Rate: 95.6%

## Failed Tests
1. GET /products/{id} - Response time exceeded 2000ms
2. POST /orders - Missing CORS headers

## Recommendations
- Optimize product lookup query
- Configure API Gateway CORS settings
```

---

## Quick Reference

### Essential MCP Tools
- `getAuthenticatedUser` - Get current user info
- `getWorkspaces` - List available workspaces
- `createWorkspace` - Create new workspace
- `getCollections` - List collections in workspace
- `createCollection` - Create new collection
- `getCollection` - Get collection details
- `putCollection` - Update entire collection
- `runCollection` - Execute collection tests
- `createEnvironment` - Create environment
- `getEnvironment` - Get environment details
- `generateCollection` - Generate from OpenAPI specification
- `syncCollectionWithSpec` - Sync with specification changes

### Configuration File Location
Always use: `.postman.json` in project root

### Required Fields in .postman.json
- `version` - Configuration file version (use "0.1")
- `workspaceId` - Workspace UUID (or use default key structure)
- `collectionId` - Collection UUID (or use default key structure)
- `environmentId` - Environment UUID (or use default key structure)
- `baseUrl` - Base API URL (in project metadata)

### Test Execution Rules
1. ✅ Always use Postman MCP tools for testing
2. ❌ Never use curl or any other HTTP clients
3. ✅ If target API is local, verify server is running first; skip for remote APIs
4. ✅ Always pass environmentId to `runCollection` if available
5. ✅ Display comprehensive test results
6. ✅ Offer to fix failures

---

## Troubleshooting

### Issue: Collection Not Found
**Solution**: Check `.postman.json` for correct `collectionId` or `collectionUid`

### Issue: Environment Variables Not Substituted
**Solution**: Ensure `environmentId` is passed to `runCollection`

### Issue: Tests Failing Unexpectedly
**Solution**: 
1. Verify API server is running
2. Check environment variables are correct
3. Review test assertions for accuracy
4. Check for API changes that broke tests

### Issue: Authentication Errors
**Solution**: 
1. Verify API key in environment
2. Check token expiration
3. Confirm authentication headers in requests

---

## Summary

This steering guide ensures consistent, reliable API testing workflows using Postman MCP:
- Always save configuration to `.postman.json`
- Use environments for all variable data
- Add comprehensive test scripts to all requests
- Run tests through Postman MCP tools only (never curl or other HTTP clients)
- Always pass environmentId to `runCollection` when available
- Check if local server is running before testing local APIs; skip for remote
- Display detailed results and offer to fix failures
- Keep collections in sync with API changes
