---
inclusion: auto
name: deploy-agent
description: Deploy AWS Transform agent using Docker/finch/CodeBuild pipeline (build, push, deploy, register)
---

# AWS Transform Agent Deployment Workflow

This workflow deploys an AWS Transform agent through the complete pipeline: build → push → deploy → register.

## When to Use

Invoke this workflow when the user wants to:
- Deploy an AWS Transform agent to production
- Build and register a new agent
- Update an existing agent with a new version
- Push agent changes to Bedrock AgentCore

## First-time setup: IAM roles

**If this is the first time you're deploying an AWS Transform agent in this AWS account, you likely need to create IAM roles first.** Skipping this step is the single most common cause of silent deployment failures: the runtime reaches READY but jobs fail ~8 minutes after creation with "Failed to start the job" in the AWS Transform webapp.

AWS Transform agent deployment requires two IAM roles:

- **`AgentCoreExecutionRole`** — runs your agent container. Needs `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, `transform-agents:*`, ECR pull, CloudWatch Logs, and X-Ray permissions. Trust principal: `bedrock-agentcore.amazonaws.com`.
- **`AWSTransformAgentInvokeRole`** — assumed by AWS Transform to invoke your runtime. Needs `bedrock-agentcore:InvokeAgentRuntime`, `bedrock-agentcore:GetAgentRuntime`, and `bedrock-agentcore:GetAgentRuntimeEndpoint`. Trust principal: `prod.us-east-1.compute.elastic-gumby.aws.internal`.

> **Regional scope:** The AWS Transform Compute principal format is `{stage}.{region}.compute.elastic-gumby.aws.internal`, and AWS Transform runs in several prod regions. This workflow, the CloudFormation template, and `deploy_agent_full_pipeline` assume us-east-1 only. For a non-us-east-1 AWS Transform region, swap the region segment in both principals, point the registry endpoint at the matching airport code, and pass `region` explicitly to the pipeline tool.

### Check if roles exist

```bash
aws iam get-role --role-name AgentCoreExecutionRole --query 'Role.Arn' --output text
aws iam get-role --role-name AWSTransformAgentInvokeRole --query 'Role.Arn' --output text
```

If either returns `NoSuchEntity`, create them using the CloudFormation template below.

### Create roles with CloudFormation

A complete, battle-tested CloudFormation template for both roles is documented in [deployment-pipeline-guide.md Section 2](./deployment-pipeline-guide.md#section-2-complete-cloudformation-template). Save it as `iam-roles.yaml` and deploy:

```bash
aws cloudformation deploy \
  --template-file iam-roles.yaml \
  --stack-name aws-transform-agent-iam-roles \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Using non-default role names

If you already have Bedrock AgentCore roles with different names (common when Bedrock AgentCore was set up via the AWS console or SDK, which creates roles like `AmazonBedrockAgentCoreSDKRuntime-us-east-1-d4f0bc5a29`):

- **`AgentCoreExecutionRole`** — `deploy_agent_full_pipeline` first tries the default name, then falls back to scanning trust policies for a role trusting `bedrock-agentcore.amazonaws.com`. If exactly one match is found it's used automatically; if zero or multiple candidates are found, the tool errors out and asks you to pass `execution_role_arn` explicitly.
- **`AWSTransformAgentInvokeRole`** — only the exact default name is auto-detected. There is no trust-policy fallback. If your invoke role has a non-default name, pass `access_role_arn` explicitly; otherwise registry registration is skipped with a warning and the pipeline continues without registering.

## Prerequisites Check

Before deploying, verify:
1. Agent directory contains Dockerfile
2. AWS credentials are configured (`aws sts get-caller-identity`)
3. IAM roles exist with correct permissions (see "First-time setup" above)
4. AWS account is allowlisted by AWS Transform team

## Deployment Steps

### Step 1: Gather Information

Ask the user these questions in order:

1. **Agent directory path**: "Where is the agent code?" (e.g., `eswar-test` or `./agents/modernization`)

2. **Agent name**: "What should this agent be called?" (e.g., `eswar-test` or `modernization-orchestrator`)
   - **CRITICAL:** `agent_name` is used as an ECR repository name. Must be lowercase and match `[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*`. No uppercase letters — `myOrchestrator` will fail with `InvalidParameterException` on `DescribeRepositories`.

3. **Agent version**: "What version?" (default: `1.0.0`)

4. **Owner contact** (required): "What email or CTI should receive notifications about this agent?" (e.g., `team@example.com`)
   - Passed as `owner_contact_info`. The registry requires a contact on every published agent, so this is required unless you deploy with `skip_registry=True`.

5. **IMPORTANT - Agent type**: "Will this agent be the main orchestrator that users interact with in the AWS Transform console?"
   - If user says **YES** → This is a job orchestrator (set `job_orchestrator=True`)
   - If user says **NO** → This is a subagent (set `job_orchestrator=False`)

6. **If YES to question 5**, also ask: "What should the display name be in the chat UI?" (e.g., "Eswar Test Orchestrator")

7. **Build method**: "Use CodeBuild?" (recommend yes for Windows, auto-detect otherwise)

### Step 2: Use deploy_agent_full_pipeline Tool

Call `deploy_agent_full_pipeline` with the gathered information:

```python
deploy_agent_full_pipeline(
    agent_path="<path from Step 1>",
    agent_name="<name from Step 1>",
    owner_contact_info="<owner email or CTI from Step 1>",  # Required
    agent_version="<version from Step 1>",
    job_orchestrator=<True if user answered YES to orchestrator question, False otherwise>,
    chat_ui_label="<display name if job_orchestrator=True>",  # Optional
    use_codebuild=<True if Windows or CI/CD, False to auto-detect>
)
```

**Key parameters:**
- `owner_contact_info` → Required. Email or CTI for the agent's owner contact and notifications (required unless `skip_registry=True`)
- `job_orchestrator=True` → Agent can be bound to workspaces (for orchestrators)
- `job_orchestrator=False` → Agent called by other agents only (for subagents)
- `chat_ui_label` → Only needed if job_orchestrator=True

The tool will automatically:
- Detect platform (Windows → CodeBuild, macOS → finch/docker)
- Build ARM64 Docker image
- Push to ECR
- Deploy to Bedrock AgentCore
- Register with AWS Transform registry

### Step 3: Report Results

After deployment completes, report to the user:

```
✓ Agent deployed successfully!

Build Phase:
  - Method: {build_method}
  - Image URI: {image_uri}

Deploy Phase:
  - Runtime ARN: {runtime_arn}
  - Status: READY

Register Phase:
  - Agent: {agent_name}
  - Version: {agent_version}
  - Registry: {registry_endpoint}

Your agent is ready to use!
```

## Platform-Specific Guidance

**Windows Users**:
- Tool automatically uses CodeBuild (finch not available on Windows)
- Requires AWS credentials with CodeBuild permissions
- Build takes 2-3 minutes (CodeBuild startup overhead)

**macOS/Linux Users**:
- Tool uses local finch (fastest)
- Falls back to docker if finch not installed
- Can force CodeBuild with `use_codebuild=True`

## Error Handling

Common errors and solutions:

1. **"Dockerfile not found"**
   - Verify agent_path is correct
   - Check that Dockerfile exists in the directory

2. **"No container runtime available"**
   - Windows: Tool should auto-use CodeBuild
   - macOS/Linux: Install finch or docker, or use `use_codebuild=True`

3. **"Bedrock AgentCore runtime stuck in CREATING"**
   - Check CloudWatch logs: `/aws/bedrock-agentcore/agent-runtime/{runtime-id}`
   - Common causes: ECR permissions, health check failure, container crash

4. **"Agent registration failed"**
   - Verify AWS account is allowlisted by AWS Transform team
   - Check IAM role permissions (AWSTransformAgentInvokeRole)

## Advanced Usage

### Deploy Without Registry Registration

If you want to deploy to Bedrock AgentCore but skip registry registration:

```python
deploy_agent_full_pipeline(
    agent_path="./agents/modernization",
    agent_name="modernization-orchestrator",
    owner_contact_info="",  # not required when skip_registry=True
    skip_registry=True
)
```

### Force CodeBuild (Windows or CI/CD)

For Windows users or CI/CD pipelines without local Docker:

```python
deploy_agent_full_pipeline(
    agent_path="./agents/modernization",
    agent_name="modernization-orchestrator",
    owner_contact_info="team@example.com",
    use_codebuild=True
)
```

### Custom IAM Roles

If your IAM roles have different names:

```python
deploy_agent_full_pipeline(
    agent_path="./agents/modernization",
    agent_name="modernization-orchestrator",
    owner_contact_info="team@example.com",
    execution_role_arn="arn:aws:iam::123456:role/CustomExecutionRole",
    access_role_arn="arn:aws:iam::123456:role/CustomAccessRole"
)
```

### Individual Phase Tools

For more control, use individual tools:

**Build only:**
```python
build_agent_image(
    agent_path="./agents/modernization",
    agent_name="modernization-orchestrator",
    use_codebuild=False
)
```

**Deploy only (after building manually):**
```python
deploy_agent_to_agentcore(
    image_uri="123456.dkr.ecr.us-east-1.amazonaws.com/aws-transform-agents/agent:latest",
    agent_name="modernization-orchestrator",
    execution_role_arn="arn:aws:iam::123456:role/AgentCoreExecutionRole"
)
```

## Related Documentation

- [Deployment Pipeline Guide](deployment-pipeline-guide.md) - Detailed pipeline patterns and IAM setup
- [Agent Registration](agent-registration.md) - Registry API details and manual registration
- [Orchestrator Patterns](orchestrator-patterns.md) - Agent architecture patterns

## Troubleshooting

### Build Issues

**Image build fails with "permission denied":**
- Check that Dockerfile exists and is readable
- Verify finch/docker is running
- Try `finch system prune` to clean up space

**ECR push fails:**
- Verify AWS credentials: `aws sts get-caller-identity`
- Check ECR permissions in your IAM policy
- Ensure ECR repository exists or can be created

### Deployment Issues

**Bedrock AgentCore runtime stuck in CREATING:**
- Wait up to 2 minutes for provisioning
- Check CloudWatch logs: `/aws/bedrock-agentcore/agent-runtime/{runtime-id}`
- Common causes:
  - Container health check failing (must expose port 8080 with /health endpoint)
  - Container crashes on startup (check application logs)
  - ECR image not accessible (verify execution role permissions)

**Bedrock AgentCore runtime fails with "FAILED" status:**
- Check CloudWatch logs for detailed error messages
- Verify container image is ARM64 architecture
- Ensure health check endpoint returns 200 OK

### Registry Issues

**"Account not allowlisted":**
- Contact AWS Transform team to allowlist your AWS account ID
- Provide account ID from `aws sts get-caller-identity`

**"Agent already registered":**
- Agent names must be unique across all publishers
- Try a different agent name
- Or update existing agent with `publish_agent_version` tool

**Registration succeeds but agent not visible:**
- Check agent visibility setting (PRIVATE vs PUBLIC)
- Verify your registry endpoint points to prod (`iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev`)
- Allow a few minutes for registry propagation

---

**Note**: This workflow requires:
- AWS Transform Agent Toolkit MCP server with deployment tools
- AWS credentials configured
- IAM roles: AgentCoreExecutionRole, AWSTransformAgentInvokeRole
- AWS account allowlisted by AWS Transform team
