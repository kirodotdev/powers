---
inclusion: auto
name: agent-registration
description: "Guidance for registering agents, publishing versions, and understanding agentCard schema for composability"
---

# Agent Registration Guide

## Related Guides

- For full deployment automation (build → ECR → Bedrock AgentCore → registry), see [deployment-pipeline-guide.md](./deployment-pipeline-guide.md)
- For IAM role setup and permissions, see [IAM Roles Overview](./deployment-pipeline-guide.md#section-1-iam-roles-overview)

## Important Distinctions

- **Bedrock AgentCore CLI**: `aws bedrock-agentcore-control` (NOT `aws bedrock-agent`)
- **Agentic API** (`transformagenticservice`): Runtime operations (InvokeAgent, GetJob) - for running agents
- **Agent Registry API** (`atxagentregistryexternal`): Registration operations (RegisterAgent, PublishAgentVersion) - for registering agents

To explore available operations:
```bash
aws atxagentregistryexternal help
aws transformagenticservice help
aws bedrock-agentcore-control help
```

## Endpoint Configuration (CRITICAL)

The Agent Registry API requires an explicit endpoint URL and region:

| Service | Endpoint URL | Region |
|---------|-------------|--------|
| Agent Registry API (`atxagentregistryexternal`) | `https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev` | `us-east-1` |

**Every AWS CLI call to the Agent Registry MUST include `--endpoint-url` and `--region`:**

```bash
aws atxagentregistryexternal list-agents-by-publisher \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

**Every boto3 call MUST include `endpoint_url` and `region_name`:**

```python
import boto3
client = boto3.client(
    'atxagentregistryexternal',
    region_name='us-east-1',
    endpoint_url='https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev'
)
```

**NEVER omit the endpoint URL** — without it, the CLI/SDK will attempt to resolve a non-existent endpoint and fail.

## Registration Flow

1. **Build & containerize** your agent
2. **Deploy to Bedrock AgentCore** via `aws bedrock-agentcore-control create-agent-runtime`
3. **Register, publish, and enable access** — use the `register_agent` MCP tool to perform steps 3–5 in a single call (RegisterAgent → PublishAgentVersion → UpdatePublisherAccessControl)

> **Tip:** The `register_agent` tool automates the RegisterAgent, PublishAgentVersion, and UpdatePublisherAccessControl API calls. For manual CLI registration, see the detailed API sections below.

## Bedrock AgentCore Deployment Requirements

### Runtime Naming Constraints

Bedrock AgentCore runtime names MUST match the pattern: `[a-zA-Z][a-zA-Z0-9_]{0,47}`

**CRITICAL RULES:**
- First character MUST be a letter (a-z, A-Z)
- Remaining characters can be letters, digits, or underscores
- **NO HYPHENS ALLOWED** - `my-agent` is INVALID, use `my_agent`
- Maximum 48 characters total
- Deleted runtime names have a cooldown period and cannot be reused immediately

**Good names:** `code_analysis_agent`, `myAgent_v1`, `atx_ws_agent_20240224`
**Bad names:** `code-analysis-agent` (hyphens), `123agent` (starts with digit), `my.agent` (dots)

### Runtime Status

After creating a Bedrock AgentCore runtime, poll for status. The success state is **`READY`** (not `ACTIVE`).

**Status values:**
- `CREATING` - Runtime is being provisioned
- `READY` - **Runtime is ready to serve requests (SUCCESS STATE)**
- `ACTIVE` - Legacy alias for READY (some API versions return this instead of READY)
- `FAILED` - Creation failed
- `STOPPED` - Runtime stopped
- `DELETE_FAILED` - Deletion failed

**Polling example:**
```bash
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id <runtime-id> \
  --region us-east-1 \
  --query 'status'
```

## IAM Role Trust Policy Requirements

The AWS Transform Agent Invoke Role (role assumed by AWS Transform to invoke your agent) MUST trust the correct service principal.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "prod.us-east-1.compute.elastic-gumby.aws.internal"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Common Error:** If you get `AccessDeniedException: AWS Transform is unable to assume the Access Role` during `publish-agent-version`, the trust policy principal doesn't match your registry endpoint.

## IAM Role Permissions (Beyond Trust Policy)

The `AgentCoreExecutionRole` needs these key permissions:
- **Bedrock**: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` on `arn:aws:bedrock:*::foundation-model/*`
- **Bedrock AgentCore**: `bedrock-agentcore:GetWorkloadAccessToken*`
- **AWS Transform Agentic API**: `transform-agents:*` — required for the agent to call GetAgentInstance, UpdateJobStatus, SendMessage, etc.
- **ECR**: Image pull permissions (ecr:GetAuthorizationToken, ecr:BatchCheckLayerAvailability, ecr:GetDownloadUrlForLayer, ecr:BatchGetImage)
- **CloudWatch Logs**: CreateLogGroup, CreateLogStream, PutLogEvents
- **X-Ray**: PutTraceSegments, PutTelemetryRecords

For complete CloudFormation template, see [deployment-pipeline-guide.md](./deployment-pipeline-guide.md).

## RegisterAgent API

Registers a new agent with the AWS Transform registry. Use this once per agent (not per version).

### API Signature

```bash
aws atxagentregistryexternal register-agent \
  --name <agent-name> \
  --metadata <json-string> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Metadata Structure

The `--metadata` parameter is a JSON object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Agent type: `SUB_AGENT` or `ORCHESTRATOR_AGENT` |
| `description` | string | Yes | Human-readable description of the agent |
| `ownerName` | string | Yes | Agent owner/publisher name |
| `ownerContactInfo` | string | Yes | Contact email or information |
| `ownerType` | string | Yes | One of: `DIRECT_AGENT`, `MARKETPLACE_AGENT` |
| `customerConfigurationRequired` | boolean | Yes | `true` if customer must configure; `false` for same-account deployment |
| `jobOrchestrator` | boolean | **Orchestrators only** | MUST be `true` for orchestrator agents |
| `jobOrchestratorMetadata` | object | **Orchestrators only** | Chat UI configuration (see below) |
| `customerConfiguredAgentDependencies` | array | Optional | List of subagent names (only for customer-account deployments) |

### ownerType Values

- **`DIRECT_AGENT`**: Use this for your own agents deployed in your AWS account
- **`MARKETPLACE_AGENT`**: Agents published to AWS Marketplace (future)

**Default:** Use `DIRECT_AGENT`.

### customerConfigurationRequired

- **`false`**: Agent and dependencies are deployed in the same AWS account as the registry (typical for demos/development)
- **`true`**: Agent will be deployed in customer's AWS account and requires customer configuration

**Trade-off matrix:**

| `customerConfigurationRequired` | `computeConfiguration` in publish | `customerConfiguredAgentDependencies` via update |
|---|---|---|
| `true` | Blocked — customer provides compute at deployment time | Allowed — declare subagent dependencies |
| `false` | Allowed — embed runtime ARN in published version | Blocked — no dependency declaration |

An orchestrator needing webapp visibility + compute config + subagent dependencies cannot satisfy all three. Choose based on priority:
- Register with `false` — webapp + compute config, but no declared dependencies (orchestrator still invokes subagents at runtime)
- Register with `true` — dependencies declared, but compute config provided by customer at deployment time

### customerConfiguredAgentDependencies

When `customerConfigurationRequired: true`, declare the orchestrator's subagent dependencies so AWS Transform knows which agents must be available:

```python
metadata = {
    "type": "ORCHESTRATOR_AGENT",
    "customerConfigurationRequired": True,
    "customerConfiguredAgentDependencies": [
        "my-analysis-agent",
        "my-transformation-agent"
    ]
}
```

These MUST be kept in sync with the `discover_subagents()` tool in `tools/orchestrator_tools.py`.

### Orchestrator-Specific Fields

**CRITICAL:** If `type` is `ORCHESTRATOR_AGENT`, you MUST set `jobOrchestrator: true` and provide `jobOrchestratorMetadata`.

#### jobOrchestratorMetadata Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chatUILabel` | string | Yes | Display name shown in AWS Transform chat UI |
| `chatAgentIdentifier` | string | Yes | Unique identifier for chat routing (use agent name) |
| `a2aSupported` | boolean | Yes | Whether agent supports Agent-to-Agent protocol |

> **Note:** `UpdateAgent` now supports updating: `description`, `ownerName`, `customerConfiguredAgentDependencies`, `workloadTypes`, `marketplaceMetadata`, `jobOrchestrator`, `jobOrchestratorMetadata`, `deprecated`, `ownerContactInfo`, and `resourceDeletionNotificationEnabled`.

### Complete Examples

#### Registering a Subagent

```bash
aws atxagentregistryexternal register-agent \
  --name code-analysis-agent \
  --metadata '{
    "type": "SUB_AGENT",
    "description": "Analyzes code structure and dependencies",
    "ownerName": "my-team",
    "ownerContactInfo": "team@example.com",
    "ownerType": "DIRECT_AGENT",
    "customerConfigurationRequired": false
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

#### Registering an Orchestrator

```bash
aws atxagentregistryexternal register-agent \
  --name modernization-orchestrator \
  --metadata '{
    "type": "ORCHESTRATOR_AGENT",
    "description": "Coordinates code modernization workflow",
    "ownerName": "my-team",
    "ownerContactInfo": "team@example.com",
    "ownerType": "DIRECT_AGENT",
    "customerConfigurationRequired": false,
    "jobOrchestrator": true,
    "jobOrchestratorMetadata": {
      "chatUILabel": "Code Modernization Orchestrator",
      "chatAgentIdentifier": "modernization-orchestrator",
      "a2aSupported": true
    }
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Python Example

```python
import boto3
import json

client = boto3.client(
    'atxagentregistryexternal',
    region_name='us-east-1',
    endpoint_url='https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev'
)

# Subagent
client.register_agent(
    name='code-analysis-agent',
    metadata={
        'type': 'SUB_AGENT',
        'description': 'Analyzes code structure and dependencies',
        'ownerName': 'my-team',
        'ownerContactInfo': 'team@example.com',
        'ownerType': 'DIRECT_AGENT',
        'customerConfigurationRequired': False
    }
)

# Orchestrator
client.register_agent(
    name='modernization-orchestrator',
    metadata={
        'type': 'ORCHESTRATOR_AGENT',
        'description': 'Coordinates code modernization workflow',
        'ownerName': 'my-team',
        'ownerContactInfo': 'team@example.com',
        'ownerType': 'DIRECT_AGENT',
        'customerConfigurationRequired': False,
        'jobOrchestrator': True,
        'jobOrchestratorMetadata': {
            'chatUILabel': 'Code Modernization Orchestrator',
            'chatAgentIdentifier': 'modernization-orchestrator',
            'a2aSupported': True
        }
    }
)
```

## PublishAgentVersion API

Publishes a new version of an agent, linking it to a Bedrock AgentCore runtime.

> **Tip:** To publish a new version without manual CLI commands, use the `publish_agent_version` MCP tool. It fetches the existing version's config, applies optional overrides (runtimeArn, atxAccessRoleArn), and publishes in a single call. Requires only the agent name and new version number.

### API Signature

```bash
aws atxagentregistryexternal publish-agent-version \
  --name <agent-name> \
  --version <version-string> \
  --configuration <json-string> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Configuration Structure

The `--configuration` parameter is a JSON object with nested structures. **All fields below are required unless marked optional.**

#### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `shortDescription` | string | Yes | Brief description (can be same as registration description) |
| `computeConfiguration` | object | Yes | Bedrock AgentCore runtime configuration (see below) |
| `agentCard` | object | Yes | Agent metadata card (see [agentCard Structure](#agentcard-structure) below) |
| `inputPayloadSchema` | object | Yes | JSON schema for input (use `{"type": "object"}` minimal — empty `{}` is rejected) |
| `outputPayloadSchema` | object | Yes | JSON schema for output (use `{"type": "object"}` minimal — empty `{}` is rejected) |
| `monitoringType` | string | Yes | Must be `HEALTHCHECK` or `HEARTBEAT` |
| `notificationsEnabled` | string | Yes | `ENABLED` or `DISABLED` |
| `objectiveNegotiationPrompt` | string | Yes | Prompt for objective validation (can be empty string) |
| `agentResiliencyConfiguration` | object | Optional | Retry and recovery settings (see below) |

**CRITICAL:** Use `"monitoringType": "HEALTHCHECK"` (not `"DEFAULT"`)

#### computeConfiguration Structure

```json
{
  "computeConfiguration": {
    "provisionedComputeConfiguration": {
      "agentCoreConfiguration": {
        "atxAccessRoleArn": "arn:aws:iam::<account>:role/AWSTransformAgentInvokeRole",
        "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:<account>:runtime/<runtime-id>",
        "qualifier": "DEFAULT"
      }
    }
  }
}
```

**IMPORTANT:**
- Use `runtimeArn` (NOT `agentCoreRuntimeArn`)
- The `qualifier` field is optional but recommended (use `"DEFAULT"`)
- Get the runtime ARN from `aws bedrock-agentcore-control get-agent-runtime`

#### agentResiliencyConfiguration Structure (Optional but Recommended)

```json
{
  "agentResiliencyConfiguration": {
    "partnerControllerRetryWindowMinutes": 6,
    "agentRecoveryConfiguration": {
      "recoveryWaitTimeSeconds": 60
    }
  }
}
```

#### agentCard Structure

The `agentCard` field describes the agent's identity, capabilities, skills, and provider metadata. It is required by `PublishAgentVersion` (not by `RegisterAgent`). An empty `{}` is rejected by boto3 client-side validation — you must provide at least the required fields. The same validation applies to both orchestrator and subagent cards.

##### Top-Level agentCard Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Agent identifier (pattern: `^[a-zA-Z0-9_-]+$`) |
| `name` | string | Yes | Human-readable agent name |
| `description` | string | Yes | Agent description |
| `version` | string | Yes | Semantic version: `major.minor.patch` (e.g., `1.0.0`) |
| `url` | string | No | Agent URL |
| `defaultInputModes` | string[] | No | Input modes (e.g., `["text"]`) |
| `defaultOutputModes` | string[] | No | Output modes (e.g., `["text"]`) |
| `capabilities` | object | Yes | Capability flags and extensions (see below) |
| `tags` | string[] | No | Freeform tags |

##### capabilities Structure

The `capabilities` object contains boolean flags and a required `extensions` array:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `restartable` | boolean | Yes | Whether the agent can be restarted |
| `a2aSupported` | boolean | Yes | Whether agent supports Agent-to-Agent protocol |
| `legacyDashboard` | boolean | Yes | Legacy dashboard support flag |
| `legacyTaskLink` | boolean | Yes | Legacy task link support flag |
| `webAppV2` | boolean | Yes | Web app v2 support flag |
| `legacyRestartable` | boolean | Yes | Legacy restartable support flag |
| `extensions` | array | Yes | Required extensions (see below) |

##### Required Extensions

Three extensions are **required** in `capabilities.extensions`:

**1. Agent Provider** — Publisher/owner details

```json
{
  "name": "Agent Provider",
  "description": "Agent publisher details",
  "params": {
    "name": "My Team Name",
    "accountId": "123456789012",
    "ownerType": "DIRECT_AGENT",
    "organization": "AWS",
    "contactInfo": [
      { "type": "email", "value": "team@example.com" }
    ]
  }
}
```

Provider params:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Publisher display name |
| `accountId` | string | Yes | 12-digit AWS account ID (pattern: `^[0-9]{12}$`) |
| `ownerType` | string | Yes | `DIRECT_AGENT` or `MARKETPLACE_AGENT` |
| `contactInfo` | array | Yes | List of contact entries (at least one required) |

Contact entry types: `email`, `phone`, `slack`, `other`

**Contact validation rules:**
- `type` — Required. Must be non-null, non-blank, and one of the valid types above. Throws `ValidationException` if missing or invalid.

**2. Agent Dependencies** — Runtime dependencies

```json
{
  "name": "Agent Dependencies",
  "description": "Runtime dependencies",
  "params": {
    "agentDependencies": [],
    "requiredConnectorTypes": []
  }
}
```

**3. Agent Connectors** — Connector types used by the agent

```json
{
  "name": "Agent Connectors",
  "description": "Connector types used by this agent",
  "params": {
    "connectors": [
      {
        "connectorTypeId": "platform|s3|1",
        "displayName": "Platform S3 Managed Policy Connector",
        "required": true,
        "description": "S3 bucket for storing transformation artifacts"
      }
    ]
  }
}
```

Connector entry fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connectorTypeId` | string | Yes | Format: `{owner}\|{shortName}\|{version}` |
| `displayName` | string | Yes | Human-readable connector name |
| `required` | boolean | Yes | Whether the connector is required |
| `description` | string | Yes | Connector description |


##### Minimal agentCard Example

The minimum structure that passes boto3 and server-side validation (works for both orchestrators and subagents):

```json
{
  "agentCard": {
    "id": "my-orchestrator-agent",
    "name": "My Orchestrator Agent",
    "description": "Orchestrates sub-agents to complete tasks",
    "version": "1.0.0",
    "capabilities": {
      "restartable": true,
      "a2aSupported": true,
      "legacyDashboard": false,
      "legacyTaskLink": false,
      "webAppV2": true,
      "legacyRestartable": false,
      "extensions": [
        {
          "name": "Agent Provider",
          "description": "Agent publisher details",
          "params": {
            "name": "MyTeam",
            "accountId": "123456789012",
            "ownerType": "DIRECT_AGENT",
            "contactInfo": [
              {
                "type": "email",
                "value": "team@example.com"
              }
            ]
          }
        },
        {
          "name": "Agent Dependencies",
          "description": "Agent runtime dependencies",
          "params": {
            "agentDependencies": [],
            "requiredConnectorTypes": []
          }
        },
        {
          "name": "Agent Connectors",
          "description": "Connector types used by this agent",
          "params": {
            "connectors": []
          }
        }
      ]
    }
  }
}
```

##### Complete agentCard Example

```json
{
  "agentCard": {
    "id": "code-analysis-agent",
    "name": "Code Analysis Agent",
    "description": "Analyzes code structure, dependencies, and quality",
    "version": "1.0.0",
    "url": "https://example.com/agent",
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "tags": ["analysis", "assessment"],
    "capabilities": {
      "restartable": true,
      "a2aSupported": true,
      "legacyDashboard": false,
      "legacyTaskLink": false,
      "webAppV2": true,
      "legacyRestartable": false,
      "extensions": [
        {
          "name": "Agent Provider",
          "description": "Agent publisher details",
          "params": {
            "name": "My Team",
            "accountId": "111122223333",
            "ownerType": "DIRECT_AGENT",
            "organization": "AWS",
            "contactInfo": [
              { "type": "email", "value": "team@example.com" }
            ]
          }
        },
        {
          "name": "Agent Dependencies",
          "description": "Runtime dependencies",
          "params": {
            "agentDependencies": [],
            "requiredConnectorTypes": []
          }
        },
        {
          "name": "Agent Connectors",
          "description": "Connector types used by this agent",
          "params": {
            "connectors": []
          }
        }
      ]
    }
  }
}
```

##### Orchestrator agentCard Example

An orchestrator card showing subagent dependencies, connectors, and owner metadata:

```json
{
  "agentCard": {
    "id": "my-orchestrator-agent",
    "name": "My Orchestrator Agent",
    "description": "Orchestrator agent that coordinates analysis and transformation tasks",
    "version": "1.0.0",
    "capabilities": {
      "restartable": true,
      "a2aSupported": true,
      "legacyDashboard": true,
      "legacyTaskLink": false,
      "webAppV2": true,
      "legacyRestartable": false,
      "extensions": [
        {
          "name": "Agent Provider",
          "description": "Agent publisher details",
          "params": {
            "name": "My Team",
            "accountId": "123456789012",
            "ownerType": "DIRECT_AGENT",
            "contactInfo": [
              {
                "type": "email",
                "value": "team@example.com"
              }
            ]
          }
        },
        {
          "name": "Agent Dependencies",
          "description": "Runtime dependencies",
          "params": {
            "agentDependencies": [
              {
                "agentName": "my-analysis-agent",
                "role": "Analyzes source artifacts",
                "required": false
              },
              {
                "agentName": "my-assessment-agent",
                "role": "Runs assessment checks",
                "required": false
              },
              {
                "agentName": "my-transformation-agent",
                "role": "Performs transformation tasks",
                "required": false
              }
            ]
          }
        },
        {
          "name": "Agent Connectors",
          "description": "Agent connector configurations",
          "params": {
            "connectors": [
              {
                "connectorTypeId": "my_service|s3|1",
                "displayName": "Amazon S3",
                "required": false,
                "description": "S3 bucket for storing artifacts"
              }
            ]
          }
        }
      ]
    },
    "skills": []
  }
}
```

Key differences from the minimal subagent card:
- **Agent Dependencies** lists all subagents the orchestrator invokes at runtime
- **Agent Connectors** declares connector types customers need to configure
- **`legacyDashboard: true`** enables the legacy dashboard view for this orchestrator

#### JSON Schema Examples

For minimal setup, use a basic type declaration (empty `{}` is rejected by boto3):
```json
{
  "inputPayloadSchema": {"type": "object"},
  "outputPayloadSchema": {"type": "object"}
}
```

For proper schemas (recommended for production):
```json
{
  "inputPayloadSchema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "sourceCode": {"type": "string"},
      "language": {"type": "string"}
    },
    "required": ["sourceCode"]
  },
  "outputPayloadSchema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "analysis": {"type": "object"},
      "recommendations": {"type": "array"}
    }
  }
}
```

### Complete Example

```bash
aws atxagentregistryexternal publish-agent-version \
  --name code-analysis-agent \
  --version 1.0.0 \
  --configuration '{
    "shortDescription": "Analyzes code structure and dependencies",
    "computeConfiguration": {
      "provisionedComputeConfiguration": {
        "agentCoreConfiguration": {
          "atxAccessRoleArn": "arn:aws:iam::111122223333:role/AWSTransformAgentInvokeRole",
          "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/code_analysis_agent-ABC123",
          "qualifier": "DEFAULT"
        }
      }
    },
    "agentCard": { "...see Minimal agentCard Example above..." },
    "inputPayloadSchema": {"type": "object"},
    "outputPayloadSchema": {"type": "object"},
    "monitoringType": "HEALTHCHECK",
    "notificationsEnabled": "ENABLED",
    "objectiveNegotiationPrompt": "",
    "agentResiliencyConfiguration": {
      "partnerControllerRetryWindowMinutes": 6,
      "agentRecoveryConfiguration": {
        "recoveryWaitTimeSeconds": 60
      }
    }
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Python Example

```python
configuration = {
    "shortDescription": "Analyzes code structure and dependencies",
    "computeConfiguration": {
        "provisionedComputeConfiguration": {
            "agentCoreConfiguration": {
                "atxAccessRoleArn": f"arn:aws:iam::{account_id}:role/AWSTransformAgentInvokeRole",
                "runtimeArn": runtime_arn,
                "qualifier": "DEFAULT"
            }
        }
    },
    "agentCard": { "...see Minimal agentCard Example above..." },
    "inputPayloadSchema": {"type": "object"},
    "outputPayloadSchema": {"type": "object"},
    "monitoringType": "HEALTHCHECK",
    "notificationsEnabled": "ENABLED",
    "objectiveNegotiationPrompt": "",
    "agentResiliencyConfiguration": {
        "partnerControllerRetryWindowMinutes": 6,
        "agentRecoveryConfiguration": {
            "recoveryWaitTimeSeconds": 60
        }
    }
}

client.publish_agent_version(
    name='code-analysis-agent',
    version='1.0.0',
    configuration=configuration
)
```

## Agent Visibility Levels

Agents have three visibility levels that control who can access them:

| Visibility | Access Model | Transition |
|-----------|-------------|-----------|
| `RESTRICTED` (default) | Only explicitly allowlisted accounts | Starting state for all agents |
| `AWS_PUBLIC` | All internal AWS accounts get automatic access; external accounts must be allowlisted | `RESTRICTED → AWS_PUBLIC` (self-service, one-way) |
| `PUBLIC` | All accounts have access (requires Marketplace productId) | `AWS_PUBLIC → PUBLIC` or `RESTRICTED → PUBLIC` (one-way) |

Transitions are **one-way toward broader access** — you cannot narrow visibility once promoted.

### Promoting to AWS_PUBLIC

Only agents with `ownerType: INTERNAL_AGENT` can be promoted to `AWS_PUBLIC`. Use the `update_agent` MCP tool:

```python
update_agent(name="my-agent", visibility="AWS_PUBLIC")
```

Or via CLI:

```bash
aws atxagentregistryexternal update-agent \
  --name my-agent \
  --visibility AWS_PUBLIC \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

After promotion:
- All internal AWS accounts automatically have access — no `update-publisher-access-control` needed for them
- External (non-AWS) accounts can still be explicitly allowlisted via `update-publisher-access-control`
- Attempting to allowlist an internal account on an AWS_PUBLIC agent is a no-op (returns success)

## UpdatePublisherAccessControl API

Controls which AWS accounts can access your agent. For `RESTRICTED` agents, this is **REQUIRED** to make agents visible, even in same-account scenarios. For `AWS_PUBLIC` agents, this is only needed to grant access to external (non-AWS) accounts.

### API Signature

```bash
aws atxagentregistryexternal update-publisher-access-control \
  --agent-name <agent-name> \
  --customer-account-id <12-digit-account-id> \
  --access-control <ENABLED|DISABLED> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--agent-name` | string | Yes | Name of the agent |
| `--customer-account-id` | string | Yes | 12-digit AWS account ID to grant/revoke access |
| `--access-control` | enum | Yes | `ENABLED` or `DISABLED` |

### Example

```bash
# Grant access to the same account (same account as publisher)
aws atxagentregistryexternal update-publisher-access-control \
  --agent-name code-analysis-agent \
  --customer-account-id 111122223333 \
  --access-control ENABLED \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# Grant access to a different customer account
aws atxagentregistryexternal update-publisher-access-control \
  --agent-name code-analysis-agent \
  --customer-account-id 999888777666 \
  --access-control ENABLED \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

**CRITICAL:** Even if you're using the same AWS account for both publishing and consuming agents, you MUST run this command to make agents visible in the AWS Transform console.

## Complete Registration Workflow

### For Subagents

```bash
# 1. Create Bedrock AgentCore runtime
RUNTIME_ARN=$(aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name code_analysis_agent_v1 \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"<ecr-uri>"}}' \
  --role-arn arn:aws:iam::<account>:role/AgentCoreExecutionRole \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --region us-east-1 \
  --query 'agentRuntimeArn' \
  --output text)

# 2. Poll until READY
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id <runtime-id> \
  --region us-east-1 \
  --query 'status'

# 3. Register agent
aws atxagentregistryexternal register-agent \
  --name code-analysis-agent \
  --metadata '{
    "type": "SUB_AGENT",
    "description": "Analyzes code structure",
    "ownerName": "my-team",
    "ownerContactInfo": "team@example.com",
    "ownerType": "DIRECT_AGENT",
    "customerConfigurationRequired": false
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# 4. Publish version
aws atxagentregistryexternal publish-agent-version \
  --name code-analysis-agent \
  --version 1.0.0 \
  --configuration '{
    "shortDescription": "Analyzes code structure",
    "computeConfiguration": {
      "provisionedComputeConfiguration": {
        "agentCoreConfiguration": {
          "atxAccessRoleArn": "arn:aws:iam::<account>:role/AWSTransformAgentInvokeRole",
          "runtimeArn": "'$RUNTIME_ARN'",
          "qualifier": "DEFAULT"
        }
      }
    },
    "monitoringType": "HEALTHCHECK",
    "notificationsEnabled": "ENABLED",
    "objectiveNegotiationPrompt": "",
    "agentCard": { "...see Minimal agentCard Example above..." },
    "inputPayloadSchema": {"type": "object"},
    "outputPayloadSchema": {"type": "object"}
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# 5. Enable access
aws atxagentregistryexternal update-publisher-access-control \
  --agent-name code-analysis-agent \
  --customer-account-id <account-id> \
  --access-control ENABLED \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### For Orchestrators

Same workflow as subagents, but with different metadata in step 3:

```bash
# 3. Register orchestrator (note the additional fields)
aws atxagentregistryexternal register-agent \
  --name modernization-orchestrator \
  --metadata '{
    "type": "ORCHESTRATOR_AGENT",
    "description": "Coordinates code modernization",
    "ownerName": "my-team",
    "ownerContactInfo": "team@example.com",
    "ownerType": "DIRECT_AGENT",
    "customerConfigurationRequired": false,
    "jobOrchestrator": true,
    "jobOrchestratorMetadata": {
      "chatUILabel": "Code Modernization Orchestrator",
      "chatAgentIdentifier": "modernization-orchestrator",
      "a2aSupported": true
    }
  }' \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# ... continue with publish-agent-version and update-publisher-access-control
```

## DeregisterAgent API

Deregisters an agent from the AWS Transform registry. Synchronous when no active instances exist; asynchronous (via `force=true`) when there are.

> **Use the `deregister_agent` MCP tool.** Do NOT auto-approve it — the two-click Run flow below is the safety acknowledgment.

### Two-step safety flow (REQUIRED)

The registry enforces a two-step confirmation when the agent has active instances in running jobs:

1. **First call — always without force.** Call `deregister_agent(name=<agent>)`. Do NOT set `force=True` on the first call, ever.
2. **If no active instances:** returns `{"deregistrationStatus": "DEREGISTERED"}`. Done.
3. **If active instances exist:** the service returns a `ValidationException` with this exact message:

   > Cannot deregister agent '<name>' because it has active instances in running jobs. Use force=true to proceed with async deregistration, which will stop all running instances and fail associated jobs.

   The MCP tool returns this message verbatim in its `error` field. **Surface it to the user verbatim** and ask for explicit confirmation before retrying.

   **Clarification on "fail associated jobs":** jobs are failed only when the agent being deregistered is the **orchestrator** of those jobs. If the agent is a **subagent**, its running instances are stopped but the parent job continues.

4. **Second call — with force, after user confirmation.** Once the user acknowledges, call `deregister_agent(name=<agent>, force=True)`. Returns `{"deregistrationStatus": "DEREGISTRATION_IN_PROGRESS"}`. Async teardown is queued.
5. **Retry safety:** if deregistration is already in progress, subsequent calls are idempotent and return `{"deregistrationStatus": "DEREGISTRATION_IN_PROGRESS"}`.

### Why two Run clicks matter

Each MCP tool invocation shown to the user in Kiro requires a "Run" / "Accept command" click. Calling `deregister_agent` twice — first without force, then with force after the user reads the ValidationException message — means the user clicks Run twice, with the service's own guidance text in between as the acknowledgment. Never collapse this into a single `force=True` call.

### API Signature (CLI, for reference)

```bash
aws atxagentregistryexternal deregister-agent \
  --name <agent-name> \
  [--force] \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Agent name to deregister. |
| `force` | boolean | No (default `false`) | Acknowledge that active instances may exist and proceed with async deregistration. Only set `true` after explicit user confirmation. |

### DeregistrationStatus values

| Value | Meaning |
|-------|---------|
| `DEREGISTERED` | Synchronous deregistration completed. No active instances existed. |
| `DEREGISTRATION_IN_PROGRESS` | Async teardown queued. Running instances are being stopped; orchestrator jobs (if any) are being failed. |

### Python example

```python
# Step 1 — always without force.
result = deregister_agent(name="code-analysis-agent")
# result is JSON. Inspect for 'error' vs 'deregistrationStatus'.

# Step 2 — only after the user confirms the ValidationException message.
result = deregister_agent(name="code-analysis-agent", force=True)
```

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationException: agentRuntimeName must match [a-zA-Z][a-zA-Z0-9_]{0,47}` | Runtime name contains hyphens or invalid characters | Use underscores instead of hyphens: `my_agent` not `my-agent` |
| `AccessDeniedException: unable to assume the Access Role` | IAM role trust policy doesn't match registry endpoint | Update trust policy to include correct service principal (`prod.us-east-1.compute.elastic-gumby.aws.internal` for prod) |
| `ConflictException: Agent already exists` | Agent name already registered | Use `publish-agent-version` to publish a new version instead of `register-agent` |
| `Cannot start job without orchestrator agent` | Orchestrator not registered or access not enabled | Re-register with `jobOrchestrator: true` and run `update-publisher-access-control` |
| Runtime status stuck in `CREATING` | Container image issues or role permissions | Check CloudWatch logs for the runtime, verify execution role permissions |
| `Invalid parameter: monitoringType DEFAULT` | Wrong monitoringType value | Use `HEALTHCHECK` or `HEARTBEAT`, not `DEFAULT` |
| `Agent marked as customer configurable, compute configuration cannot be provided` | `customerConfigurationRequired: true` with `computeConfiguration` in publish | Omit `computeConfiguration`; use `publish-agent-version` from `agent-builder-mcp-aws-transform` |
| Chat input never enables / zero invocations | Wrong role used in registration | Use `AWSTransformAgentInvokeRole`, not `AgentCoreExecutionRole` |

## Verification Commands

```bash
# List your registered agents
aws atxagentregistryexternal list-agents-by-publisher \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# Get agent details
aws atxagentregistryexternal get-agent \
  --name <agent-name> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# Get specific agent version
aws atxagentregistryexternal get-agent-version \
  --name <agent-name> \
  --version <version> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# Check Bedrock AgentCore runtime status
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id <runtime-id> \
  --region us-east-1

# List all Bedrock AgentCore runtimes
aws bedrock-agentcore-control list-agent-runtimes \
  --region us-east-1

# Deregister an agent (synchronous — no active instances)
aws atxagentregistryexternal deregister-agent \
  --name <agent-name> \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1

# Deregister with force (async — only after ValidationException confirmation)
aws atxagentregistryexternal deregister-agent \
  --name <agent-name> \
  --force \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

## Additional Resources

For API-specific details, always use the MCP search tools:
- `keyword_search("register agent")` - General registration guidance
- `search_by_source("RegisterAgent", "api")` - RegisterAgent API reference
- `search_by_source("PublishAgentVersion", "api")` - PublishAgentVersion API reference
- `search_by_source("UpdatePublisherAccessControl", "api")` - Access control API reference

**Grounding requirement:** Only answer based on search results. If specific information isn't found, refer users to the AWS Transform Developer Guide or their Solutions Architect.
