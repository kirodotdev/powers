---
inclusion: auto
name: api-reference
description: "Guidance for working with AWS Transform APIs (Agentic API, Registry API)"
---

# AWS Transform Agentic API Reference

## Overview

The AWS Transform Agentic API provides operations for agents to interact with AWS Transform. All operations use JSON-RPC protocol over HTTPS with AWS SigV4 authentication.

**Base Endpoint**: Configured via `QT_AGENTIC_API_ENDPOINT` environment variable

**Authentication**: AWS SigV4 signing with `transform-agents` signing name

**Protocol**: JSON 1.0

## Common Request Structure

All requests include a `requestContext` with job metadata and authorization:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "uuid",
      "jobId": "uuid"
    },
    "agentInstanceId": "uuid",
    "authorizationToken": "token"
  }
}
```

## Key Operations

### InvokeAgent

Invoke another agent (orchestrator or subagent) to perform a task.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |
| **Idempotent** | Yes (with idempotencyToken) |

**Input Shape** (`InvokeAgentRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `agentId` | String | Yes | Agent identifier (pattern: `^[a-z0-9-]+$`) |
| `inputPayload` | AgentInputPayload | No | Input data for the agent |
| `idempotencyToken` | UUID | No | Token for idempotent retries |
| `agentVersion` | String | No | Specific agent version (pattern: `^\d+\.\d+\.\d+(?:-dev-[a-zA-Z0-9]+)?$`) |
| `agentInstanceId` | UUID | No | Existing agent instance to resume |

**Output Shape** (`InvokeAgentResponse`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentInstanceId` | UUID | Yes | Unique identifier for the agent invocation |

**Example Request**:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "jobId": "12345678-1234-1234-1234-123456789012"
    },
    "agentInstanceId": "87654321-4321-4321-4321-210987654321",
    "authorizationToken": "eyJhbGc..."
  },
  "agentId": "infrastructure-analyzer",
  "agentVersion": "1.0.0",
  "inputPayload": {
    "task": "analyze",
    "config": "{...}"
  }
}
```

**Example Response**:

```json
{
  "agentInstanceId": "98765432-8765-8765-8765-987654321098"
}
```

---

### GetJob

Retrieve details about the current transformation job.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |
| **Read-only** | Yes |

**Input Shape** (`GetJobRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `includeObjective` | Boolean | No | Include job objective in response |

**Output Shape** (`GetJobResponse`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job` | JobInfo | No | Job details including ID, workspace, status |

**Example Request**:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "jobId": "12345678-1234-1234-1234-123456789012"
    },
    "agentInstanceId": "87654321-4321-4321-4321-210987654321",
    "authorizationToken": "eyJhbGc..."
  },
  "includeObjective": true
}
```

**Example Response**:

```json
{
  "job": {
    "jobId": "12345678-1234-1234-1234-123456789012",
    "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "IN_PROGRESS",
    "objective": "Migrate infrastructure to AWS",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### ListAgents

List available agents that can be invoked.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |
| **Paginated** | Yes |

**Input Shape** (`ListAgentsRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `agentFilter` | ListAgentsFilter | No | Filter criteria for agents |
| `nextToken` | String | No | Pagination token |
| `maxResults` | Integer | No | Max results per page (1-10) |

**Output Shape** (`ListAgentsResponse`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | Array | No | List of agent metadata summaries |
| `nextToken` | String | No | Token for next page |

**Example Request**:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "jobId": "12345678-1234-1234-1234-123456789012"
    },
    "agentInstanceId": "87654321-4321-4321-4321-210987654321",
    "authorizationToken": "eyJhbGc..."
  },
  "maxResults": 10
}
```

**Example Response**:

```json
{
  "items": [
    {
      "agentId": "infrastructure-analyzer",
      "agentName": "Infrastructure Analyzer",
      "agentType": "SUB_AGENT",
      "version": "1.0.0"
    },
    {
      "agentId": "cost-calculator",
      "agentName": "Cost Calculator",
      "agentType": "SUB_AGENT",
      "version": "2.1.0"
    }
  ],
  "nextToken": "eyJuZXh0VG9rZW4..."
}
```

---

### ListAgentInstances

List all agent invocations for the current job.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |
| **Read-only** | Yes |
| **Paginated** | Yes |

**Input Shape** (`ListAgentInstancesRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `nextToken` | String | No | Pagination token |
| `maxResults` | Integer | No | Max results per page (1-100) |

**Output Shape** (`ListAgentInstancesResponse`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentInstances` | Array | Yes | List of agent instances |
| `nextToken` | String | No | Token for next page |

**Example Request**:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "jobId": "12345678-1234-1234-1234-123456789012"
    },
    "agentInstanceId": "87654321-4321-4321-4321-210987654321",
    "authorizationToken": "eyJhbGc..."
  },
  "maxResults": 50
}
```

**Example Response**:

```json
{
  "agentInstances": [
    {
      "agentInstanceId": "98765432-8765-8765-8765-987654321098",
      "agentId": "infrastructure-analyzer",
      "status": "COMPLETED",
      "startedAt": "2024-01-15T10:35:00Z",
      "completedAt": "2024-01-15T10:40:00Z"
    }
  ]
}
```

---

### GetAgentInstance

Get details about a specific agent invocation.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |

**Input Shape** (`GetAgentInstanceRequest`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `agentInstanceId` | UUID | Yes | Agent instance identifier |

**Output Shape** (`GetAgentInstanceResponse`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agentInstanceId` | UUID | Yes | Instance identifier |
| `agentInstanceStatus` | String | Yes | INVOKING, INVOKED, RUNNING, COMPLETED, FAILED |
| `agentOutput` | Object | No | Present when COMPLETED |
| `agentOutput.serializedPayload` | String | No | JSON string with response data |
| `statusReason` | String | No | Failure reason (when FAILED) |

**Instance lifecycle:** INVOKING → INVOKED → RUNNING → COMPLETED or FAILED. Poll for RUNNING before sending messages; poll for COMPLETED to extract results.

**Extracting response:**
```python
output = instance.get("agentOutput", {})
payload = json.loads(output.get("serializedPayload", "{}"))
response_text = payload.get("response", "")
```

**Example Request**:

```json
{
  "requestContext": {
    "jobMetadata": {
      "workspaceId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "jobId": "12345678-1234-1234-1234-123456789012"
    },
    "agentInstanceId": "87654321-4321-4321-4321-210987654321",
    "authorizationToken": "eyJhbGc..."
  },
  "agentInstanceId": "98765432-8765-8765-8765-987654321098"
}
```

**Example Response**:

```json
{
  "agentInstance": {
    "agentInstanceId": "98765432-8765-8765-8765-987654321098",
    "agentId": "infrastructure-analyzer",
    "status": "COMPLETED",
    "startedAt": "2024-01-15T10:35:00Z",
    "completedAt": "2024-01-15T10:40:00Z",
    "outputPayload": {
      "result": "analysis_complete",
      "findings": [...]
    }
  }
}
```

---

### SendMessage

Send an A2A message to a running agent instance.

| Property | Value |
|----------|-------|
| **HTTP Method** | POST |
| **Path** | / |

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requestContext` | RequestContext | Yes | Job and authorization context |
| `agentInstanceId` | UUID | Yes | Target agent instance (or `"ATX_CHAT"` for webapp chat) |
| `params` | Object | Yes | Message payload with A2A `message` object |

**CRITICAL:** SendMessage has a ~25s internal timeout. If the subagent takes longer, returns error code `-32603` with HTTP 200. The subagent is still processing — use the fire-and-forget + polling pattern: send the message, then poll `GetAgentInstance` until COMPLETED.

**ATX_CHAT:** Use `agentInstanceId="ATX_CHAT"` to send messages to the webapp chat. The required A2A format uses `extensions` with `userSelection: "jobCreator"` metadata. See `orchestrator-patterns.md` for the working code pattern.

---

## Job Plan APIs

### PutJobPlan

Create or replace the job plan with steps visible in the AWS Transform webapp.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan.nodes` | Array | Yes | List of step objects with `stepLabel`, `stepName`, `description` |
| `mode` | Object | Yes | Use `{"override": {}}` to replace existing plan |
| `idempotencyToken` | UUID | Yes | Required for all mutating calls |

**CRITICAL:** `PutJobPlan` assigns its own `stepId` values. The response does NOT include them. Call `ListJobPlanSteps` immediately after to get the `stepLabel → stepId` mapping.

### ListJobPlanSteps

List all steps in the current job plan with their API-assigned stepIds and statuses.

### UpdateJobPlanStep

Update a plan step's status.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `planStep.stepId` | String | Yes | API-assigned stepId (NOT stepLabel) |
| `planStep.status` | String | Yes | NOT_STARTED, IN_PROGRESS, SUCCEEDED, FAILED, PENDING_HUMAN_INPUT |
| `planStep.description` | String | No | Error message for FAILED status |
| `idempotencyToken` | UUID | Yes | Required |

**CRITICAL:** The error message field is `description`, NOT `errorMessage`. Using `errorMessage` silently drops the error text.

### UpdateJobStatus

Update overall job status: PLANNING, PLANNED, EXECUTING, COMPLETED, FAILED.

---

## HITL APIs

HITL (Human-in-the-Loop) enables subagents to collect user input via AutoForms in the AWS Transform webapp. See `subagent-patterns.md` for the HITL AutoForm pattern.

### CreateHitlTask

Create a HITL task attached to a job plan step.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uxComponentId` | String | Yes | Use `"AutoForm"` |
| `title` | String | Yes | Form title |
| `description` | String | Yes | Form description (max 1024 chars) |
| `stepId` | String | No | Plan step to attach to |
| `blockingType` | String | Yes | `"BLOCKING"` (wait for input) or `"NON_BLOCKING"` (display only) |
| `hitlRequestArtifact.artifactId` | String | No | Uploaded form schema artifact |
| `idempotencyToken` | UUID | Yes | Required |

### StartHitlTask / GetHitlTask / CloseHitlTask

- **StartHitlTask**: Activates the form in the webapp. Status: CREATED → AWAITING.
- **GetHitlTask**: Poll for status. When SUBMITTED, download the response artifact.
- **CloseHitlTask**: Close with `closureType: "CLOSED"`. Always close after processing.

---

## Artifact APIs

### UploadArtifact (CreateArtifactUploadUrl + PUT + CompleteArtifactUpload)

Three-step process: get presigned URL, PUT content, mark complete. Used for HITL form schemas and reports.

### DownloadArtifact (CreateArtifactDownloadUrl + GET)

Get presigned URL, then GET the content. Used to retrieve HITL user responses.

Use `AgenticApiHelper.create_artifact_upload_url()`, PUT content, then `complete_artifact_upload()`. For download: `create_artifact_download_url()` then GET.

---

## AgenticApiHelper Pattern

The recommended pattern for calling the Agentic API is to extend `AgenticApiHelper` from the SDK. It provides `_inject_request_context()` which automatically adds `workspaceId`, `jobId`, `agentInstanceId`, and `authorizationToken` to every API call.

Create an `AgenticApiHelper` subclass that calls `_inject_request_context()` on every API request. Do NOT use raw `boto3` clients directly — you'll get `Missing required parameter: requestContext` errors. Search `keyword_search("AgenticApiHelper")` for the SDK class documentation.

---

## Common Error Responses

All operations may return these standard errors:

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `AccessDeniedException` | 403 | Access denied to the requested resource |
| `InternalServerException` | 500 | Internal server error occurred |
| `ResourceNotFoundException` | 404 | Requested resource not found |
| `ThrottlingException` | 429 | Request rate limit exceeded |
| `ValidationException` | 400 | Request validation failed |
| `ConflictException` | 409 | Request conflicts with current resource state |

## Next Steps

- Review orchestrator patterns: `orchestrator-patterns.md`
- Review subagent patterns: `subagent-patterns.md`
- Troubleshoot: `troubleshooting.md`
