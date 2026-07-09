---
inclusion: auto
name: deployment-pipeline-guide
description: "Guidance for deploying AWS Transform agents (Docker, ECR, Bedrock AgentCore, pipeline automation)"
---

# AWS Transform Agent Deployment Pipeline Guide

This guide covers the complete deployment pipeline for AWS Transform agents, including IAM role setup, container builds, Bedrock AgentCore runtime deployment, and registry integration. This is based on the battle-tested patterns from the AWS Transform modernization workshop demo project.

> **💡 Recommended Approach**: For the easiest deployment experience, use the MCP deployment tools instead of manual scripts. See [Deploy Agent Workflow Guide](deploy-agent-workflow.md) for the recommended workflow that works cross-platform (Windows/macOS/Linux) and handles all phases automatically.
>
> This guide documents the manual shell script approach for reference and advanced customization.

---

## Section 1: IAM Roles Overview

The AWS Transform agent deployment model requires two IAM roles, each with specific trust relationships and permissions:

### 1. AgentCoreExecutionRole
- **Used by**: Bedrock AgentCore service (runtime execution environment)
- **Purpose**: Executes agent containers, accesses ECR images, writes logs, traces
- **Trust Policy**: Bedrock's `bedrock-agentcore` service principal
- **When it's used**: During agent runtime execution when Bedrock AgentCore pulls images and runs containers

### 2. AWSTransformAgentInvokeRole
- **Used by**: AWS Transform compute service
- **Purpose**: Invokes Bedrock AgentCore runtimes on behalf of AWS Transform
- **Trust Policy**: AWS Transform compute service principal (`prod.us-east-1.compute.elastic-gumby.aws.internal`)
- **When it's used**: When AWS Transform routes requests to your agent

---

## Section 2: Complete CloudFormation Template

**IMPORTANT PREREQUISITES:**
1. **AWS Account Allowlisting**: Your AWS account ID must be allowlisted by the AWS Transform team before you can register agents with the AWS Transform registry. Contact your Solutions Architect or AWS Transform team to request allowlisting for your account.

The following CloudFormation template defines all required IAM roles.

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: >
  IAM roles required for AWS Transform modernization agent deployment.
  - AgentCoreExecutionRole: Used by Bedrock AgentCore to run agent containers
  - AWSTransformAgentInvokeRole: Used by AWS Transform to invoke agents

Resources:

  # -----------------------------------------------------------------------
  # AgentCoreExecutionRole
  # Used by Bedrock AgentCore to run your agent container
  # -----------------------------------------------------------------------
  AgentCoreExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: AgentCoreExecutionRole
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: bedrock-agentcore.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: AgentCoreExecutionPolicy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Sid: BedrockInvoke
                Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                  - bedrock-runtime:Converse
                  - bedrock-runtime:InvokeModel
                Resource: "*"
              - Sid: TransformAgentsApiPolicy
                Effect: Allow
                Action:
                  - transform-agents:*
                Resource: "*"
              - Sid: ECRImageAccess
                Effect: Allow
                Action:
                  - ecr:GetAuthorizationToken
                  - ecr:BatchCheckLayerAvailability
                  - ecr:GetDownloadUrlForLayer
                  - ecr:BatchGetImage
                Resource: "*"
              - Sid: CloudWatchLogs
                Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: "*"
              - Sid: XRayTracing
                Effect: Allow
                Action:
                  - xray:PutTraceSegments
                  - xray:PutTelemetryRecords
                Resource: "*"

  # -----------------------------------------------------------------------
  # AWSTransformAgentInvokeRole
  # Trust: AWS Transform compute service
  # Permissions: Invoke Bedrock AgentCore runtimes
  # -----------------------------------------------------------------------
  AWSTransformAgentInvokeRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: AWSTransformAgentInvokeRole
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - prod.us-east-1.compute.elastic-gumby.aws.internal
            Action: sts:AssumeRole
      Policies:
        - PolicyName: ATXAgentInvokePolicy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Sid: ATXAgentCoreRuntimePermissions
                Effect: Allow
                Action:
                  - bedrock-agentcore:GetAgentRuntime
                  - bedrock-agentcore:GetAgentRuntimeEndpoint
                  - bedrock-agentcore:InvokeAgentRuntime
                  - bedrock-agentcore:ListAgentRuntimeEndpoints
                  - bedrock-agentcore:ListAgentRuntimeVersions
                  - bedrock-agentcore:ListAgentRuntimes
                  - bedrock-agentcore:StopRuntimeSession
                Resource: "*"
              - Sid: TransformAgentsAPI
                Effect: Allow
                Action:
                  - "transform-agents:*"
                Resource: "*"


Outputs:
  AgentCoreExecutionRoleArn:
    Description: ARN of the Bedrock AgentCore execution role
    Value: !GetAtt AgentCoreExecutionRole.Arn
    Export:
      Name: AWSTransform-AgentCoreExecutionRoleArn

  AWSTransformAgentInvokeRoleArn:
    Description: ARN of the AWS Transform agent invoke role
    Value: !GetAtt AWSTransformAgentInvokeRole.Arn
    Export:
      Name: AWSTransform-AWSTransformAgentInvokeRoleArn
```

### Deploying the CloudFormation Stack

**Before deploying**, ensure your AWS account has been allowlisted by the AWS Transform team.

```bash
aws cloudformation deploy \
  --template-file pipeline/iam-roles.yaml \
  --stack-name aws-transform-agent-iam-roles \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

---

## Section 3: Deployment Pipeline Pattern

The deployment pipeline follows a **four-phase automation pattern**: Build → Push → Deploy → Register. This pattern is battle-tested and handles common failure modes gracefully.

### Four-Phase Pipeline Architecture

```
Phase 1: BUILD
  ├─ Docker build with platform=linux/arm64
  ├─ Install SDK wheels from local files
  ├─ Create MCP wrapper scripts
  └─ Save images as .tar for verification

Phase 2: PUSH
  ├─ ECR login using finch (not docker)
  ├─ Create ECR repos if needed
  ├─ Tag and push images
  └─ Verify images exist in ECR

Phase 3: DEPLOY
  ├─ Create Bedrock AgentCore runtimes with unique names (timestamp with seconds)
  ├─ Poll status until READY (or ACTIVE in older API versions)
  ├─ Detect terminal failure states (FAILED, STOPPED, DELETE_FAILED)
  └─ Capture runtime ARNs for registration

Phase 4: REGISTER
  ├─ Register agent with AWS Transform registry
  ├─ Publish version with compute configuration
  ├─ Grant access to account
  └─ Verify registration
```

### Key Implementation Details

#### 1. Container Runtime Selection (Platform-Specific)

**macOS/Linux**:
```python
# Recommended: Use finch to avoid Docker Desktop org auth issues
CONTAINER_CMD = "finch"  # or "docker" if finch not available
```

**Windows**:
```python
# Use Docker Desktop (finch is not available on Windows)
CONTAINER_CMD = "docker"
```

**Why finch on macOS/Linux**: Docker Desktop requires organization authentication which can cause silent failures in corporate environments. Finch is Amazon's open-source container runtime that works without licensing issues.

**Why docker on Windows**: Finch does not support Windows. Windows users must use Docker Desktop with proper authentication configured.

**Alternative: AWS CodeBuild** (Recommended for cross-platform teams)
- Offload container builds to AWS CodeBuild
- Handles ARM64 builds natively (using Amazon Linux 2 ARM64 instances)
- No local container runtime needed
- Works consistently across all developer platforms
- See Section 8 for CodeBuild setup

#### 2. Runtime Names with Seconds Precision

```python
# Lines 282-283 from deploy_agents.py
runtime_name = (
    f"atx_ws_{name.replace('-', '_')}_{datetime.now().strftime('%m%d%H%M%S')}"
)
```

**Why**: Bedrock AgentCore has a runtime name cooldown period. Using timestamp with seconds precision (not just minutes) prevents "runtime name already exists" errors during rapid redeployment cycles.

#### 3. Status Polling for READY

```python
# Lines 378-422 from deploy_agents.py
def _poll_runtime_status(runtime_id: str, region: str, name: str) -> str:
    """Poll Bedrock AgentCore runtime status until READY (or ACTIVE) or failure. Returns the ARN."""
    log.info(
        "  Polling runtime status for %s (timeout %ds)...", name, AGENTCORE_POLL_TIMEOUT
    )
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > AGENTCORE_POLL_TIMEOUT:
            log.error(
                "  ✗ Timeout waiting for %s to become READY (%.0fs)", name, elapsed
            )
            sys.exit(1)

        result = run_json(
            [
                "aws",
                "bedrock-agentcore-control",
                "get-agent-runtime",
                "--agent-runtime-id",
                runtime_id,
                "--region",
                region,
                "--output",
                "json",
            ]
        )

        status = result.get("status")
        arn = result.get("agentRuntimeArn", "")
        log.info("  [%3.0fs] %s status: %s", elapsed, name, status)

        if status == "ACTIVE" or status == "READY":
            log.info("  ✓ %s is %s (ARN: %s)", name, status, arn)
            return arn

        if status in AGENTCORE_TERMINAL_FAILURE_STATES:
            failure_reasons = result.get("statusReasons", [])
            log.error("  ✗ %s entered terminal state: %s", name, status)
            if failure_reasons:
                log.error("  Reasons: %s", json.dumps(failure_reasons, indent=2))
            sys.exit(1)

        time.sleep(AGENTCORE_POLL_INTERVAL)
```

**Why**: Bedrock AgentCore runtime deployment is asynchronous. The create call returns immediately, but the runtime isn't usable until status reaches READY or ACTIVE. This polling loop with timeout prevents premature registration.

#### 4. Error Handling with stderr Capture

```python
# Lines 72-86 from deploy_agents.py
def run_json(cmd: list[str]) -> dict:
    """Run a command and parse JSON output."""
    result = run(cmd, capture=True, check=False)
    if result.returncode != 0:
        log.error(
            "Command failed (exit %d): %s", result.returncode, result.stderr.strip()
        )
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        log.error("Failed to parse JSON from command output:\n%s", result.stdout)
        raise
```

**Why**: Many AWS CLI failures produce cryptic exit codes. Capturing and logging stderr provides actionable error messages for debugging.

#### 5. Using --cli-input-json for Complex Structures

```python
# Lines 313-331 from deploy_agents.py
result = run_json(
    [
        "aws",
        "bedrock-agentcore-control",
        "create-agent-runtime",
        "--agent-runtime-name",
        runtime_name,
        "--agent-runtime-artifact",
        json.dumps({"containerConfiguration": {"containerUri": image_uri}}),
        "--role-arn",
        execution_role_arn,
        "--network-configuration",
        json.dumps({"networkMode": "PUBLIC"}),
        "--region",
        region,
        "--output",
        "json",
    ]
)
```

**Why**: Passing JSON as string arguments avoids shell escaping issues and makes complex nested structures explicit.

#### 6. Phase Skip Flags for Iteration

```python
# Lines 659-674 from deploy_agents.py
parser.add_argument(
    "--skip-build",
    action="store_true",
    help="Skip Docker build phase (use existing images)",
)
parser.add_argument(
    "--skip-push",
    action="store_true",
    help="Skip ECR push phase (use already-pushed images)",
)
```

**Why**: During development, you often need to iterate on deploy/register logic without rebuilding images. Skip flags save 5-10 minutes per iteration.

### Complete Pipeline Script Pattern

```python
#!/usr/bin/env python3
"""Deployment pipeline for AWS Transform modernization agent system.

Phases (in order):
  1. Build   — Docker build each agent image, save as .tar
  2. Push    — Create ECR repos if needed, tag and push images
  3. Deploy  — Create Bedrock AgentCore runtimes, poll until READY
  4. Register — Register agents with AWS Transform registry, publish versions

Usage:
  python pipeline/deploy_agents.py                    # Full pipeline
  python pipeline/deploy_agents.py --skip-build       # Skip Docker build
  python pipeline/deploy_agents.py --skip-push        # Skip ECR push
  python pipeline/deploy_agents.py --skip-build --skip-push  # Deploy + register only
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

# Configuration
CONTAINER_CMD = "finch"  # Use finch, not docker
AGENTCORE_POLL_INTERVAL = 10  # seconds
AGENTCORE_POLL_TIMEOUT = 120  # seconds
AGENTCORE_TERMINAL_FAILURE_STATES = {"FAILED", "STOPPED", "DELETE_FAILED"}

def main():
    config = load_config()

    # Phase 1: Build
    if not args.skip_build:
        phase_build(config)

    # Phase 2: Push
    if not args.skip_push:
        phase_push(config)

    # Phase 3: Deploy to Bedrock AgentCore
    runtime_info = phase_deploy(config)

    # Phase 4: Register with AWS Transform
    phase_register(config, runtime_info)
```

---

## Section 4: Docker Build Context

### Platform Requirement

**CRITICAL**: All AWS Transform agents MUST be built for `linux/arm64`:

```dockerfile
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.11-slim
```

**Why**: Bedrock AgentCore runtimes run on AWS Graviton (ARM64) instances. x86_64 images will fail at runtime with "exec format error".

**Why ECR Public (not Docker Hub)**: `public.ecr.aws/docker/library/python` is the AWS-operated public mirror of Docker Hub's official Python image. Same bits, no AWS account required to pull.

### SDK Installation

Install the AWS Transform SDK packages from PyPI:

```dockerfile
# Install AWS Transform SDK from PyPI
RUN pip install --no-cache-dir \
    agent-builder-sdk-aws-transform \
    agent-builder-agentic-mcp-aws-transform
```

### Botocore Service Model Registration ⚠️ CRITICAL

**REQUIRED**: You MUST register the botocore service models for the Agentic API and Agent Registry API. Without these, boto3 clients will fail with "Unknown service" errors.

The service model JSON files ship with the `agent-builder-sdk-aws-transform` pip package. After installing the SDK, register them from the installed path:

```dockerfile
# Register botocore service models from the installed SDK package
RUN pip install --no-cache-dir awscli && \
    SDK_MODELS=$(python -c "from importlib.resources import files; print(files('agent_builder_sdk').joinpath('botocore_models'))") && \
    aws configure add-model --service-name atxagentregistryexternal \
      --service-model "file://${SDK_MODELS}/atxagentregistryexternal/2022-07-26/service-2.json" && \
    aws configure add-model --service-name transformagenticservice \
      --service-model "file://${SDK_MODELS}/transformagenticservice/2018-05-10/service-2.json"
```

**Why**: AWS Transform uses custom AWS service APIs not part of the standard boto3 distribution:
- `transformagenticservice` - Used by BaseAgent SDK to invoke other agents (InvokeAgent operation)
- `atxagentregistryexternal` - Used to register and publish agents to AWS Transform registry

Without registering these service models, your agent will fail at runtime when trying to:
- Invoke subagents from an orchestrator
- Register the agent with AWS Transform registry
- Use any BaseAgent SDK features that call Agentic API

**Common Error Without Service Models**:
```
botocore.exceptions.UnknownServiceError: Unknown service: 'transformagenticservice'
```

### MCP Runtime Wrapper

Bedrock AgentCore expects an MCP server binary at a specific path:

```dockerfile
# Create MCP server wrapper binary
RUN mkdir -p /home/amazon/AgentBuilderAgenticMCP/bin && \
    printf '#!/bin/bash\npython -m agent_builder_agentic_mcp "$@"\n' > /home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp && \
    chmod +x /home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp
```

**Why**: Bedrock AgentCore runtime looks for `agent-builder-agentic-mcp` binary in this exact path. The wrapper script delegates to the Python module installed from PyPI.

### Complete Dockerfile Templates

The canonical Dockerfile templates are maintained as standalone files for easy reference and single-source-of-truth maintenance:

- **Orchestrator**: [dockerfile-orchestrator.md](./dockerfile-orchestrator.md)
- **Subagent**: [dockerfile-subagent.md](./dockerfile-subagent.md)

These templates incorporate both the botocore service model registration and MCP wrapper script creation documented above. **Use them verbatim** — do not generate a Dockerfile from scratch.

### Docker Build Command

```bash
finch build \
  --platform linux/arm64 \
  -f src/orchestrator/Dockerfile \
  -t modernization-orchestrator:latest \
  .
```

---

## Section 5: Bedrock AgentCore CLI Commands

### Create Agent Runtime

```bash
aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name atx_ws_my_agent_02251430 \
  --agent-runtime-artifact '{
    "containerConfiguration": {
      "containerUri": "111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-transform-agents/my-agent:latest"
    }
  }' \
  --role-arn arn:aws:iam::111122223333:role/AgentCoreExecutionRole \
  --network-configuration '{"networkMode": "PUBLIC"}' \
  --region us-east-1 \
  --output json
```

**Returns**:
```json
{
  "agentRuntimeId": "abc123def456",
  "agentRuntimeName": "atx_ws_my_agent_02251430",
  "status": "CREATING"
}
```

### Get Agent Runtime Status

```bash
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id abc123def456 \
  --region us-east-1 \
  --output json
```

**Returns**:
```json
{
  "agentRuntimeId": "abc123def456",
  "agentRuntimeName": "atx_ws_my_agent_02251430",
  "agentRuntimeArn": "arn:aws:bedrock-agentcore:us-east-1:111122223333:agent-runtime/abc123def456",
  "status": "READY",
  "containerConfiguration": {
    "containerUri": "111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-transform-agents/my-agent:latest"
  },
  "roleArn": "arn:aws:iam::111122223333:role/AgentCoreExecutionRole",
  "networkConfiguration": {
    "networkMode": "PUBLIC"
  },
  "createdAt": "2026-02-25T14:30:00Z",
  "updatedAt": "2026-02-25T14:32:15Z"
}
```

### List Agent Runtimes

```bash
aws bedrock-agentcore-control list-agent-runtimes \
  --region us-east-1 \
  --output json
```

### Update Agent Runtime

```bash
aws bedrock-agentcore-control update-agent-runtime \
  --agent-runtime-id abc123def456 \
  --agent-runtime-artifact '{
    "containerConfiguration": {
      "containerUri": "111122223333.dkr.ecr.us-east-1.amazonaws.com/aws-transform-agents/my-agent:v2"
    }
  }' \
  --region us-east-1
```

### Delete Agent Runtime

```bash
aws bedrock-agentcore-control delete-agent-runtime \
  --agent-runtime-id abc123def456 \
  --region us-east-1
```

---

## Section 6: Common Pipeline Issues

### Issue 1: Docker Desktop Organization Authentication

**Symptom**:
```
Error response from daemon: Get https://111122223333.dkr.ecr.us-east-1.amazonaws.com/v2/: unauthorized
```

**Root Cause**: Docker Desktop on macOS requires organization authentication which may not be configured in CI/CD environments.

**Solution**: Use `finch` instead of `docker`:

```python
CONTAINER_CMD = "finch"
```

**Why It Works**: Finch is Amazon's open-source container runtime built on containerd and doesn't require Docker Desktop licensing or org authentication.

---

### Issue 2: Runtime Name Cooldown Period

**Symptom**:
```
ConflictException: An error occurred (ConflictException) when calling the CreateAgentRuntime operation:
Runtime name 'atx_ws_my_agent' already exists or was recently deleted
```

**Root Cause**: Bedrock AgentCore has a cooldown period for runtime names. Even after deleting a runtime, the name cannot be immediately reused.

**Solution**: Append timestamp with **seconds precision** to runtime names:

```python
runtime_name = (
    f"atx_ws_{name.replace('-', '_')}_{datetime.now().strftime('%m%d%H%M%S')}"
)
```

**Example**: `atx_ws_code_analysis_agent_02251430` (month, day, hour, minute, second)

**Why Seconds Matter**: Using only `%m%d%H%M` (without seconds) still causes collisions during rapid testing cycles. Adding seconds provides uniqueness within a 1-second window.

---

### Issue 3: Silent Publish Failures with Positional Arguments

**Symptom**: `publish-agent-version` command returns success but version doesn't appear in registry.

**Root Cause**: AWS CLI silently ignores malformed JSON when passed as positional arguments instead of named parameters.

**Bad**:
```bash
aws atxagentregistryexternal publish-agent-version \
  my-agent 1.0.0 '{"computeConfiguration": ...}'
```

**Good**:
```bash
aws atxagentregistryexternal publish-agent-version \
  --name my-agent \
  --version 1.0.0 \
  --configuration '{"computeConfiguration": ...}'
```

**Solution**: Always use `--cli-input-json` or named parameters:

```python
run_json([
    "aws",
    "atxagentregistryexternal",
    "publish-agent-version",
    "--name", name,
    "--version", version,
    "--configuration", json.dumps(configuration),
    "--endpoint-url", endpoint,
    "--region", region
])
```

---

### Issue 4: Trust Policy Mismatch (Prod vs Gamma)

**Symptom**:
```
AccessDeniedException: Cross-account pass role is not allowed
```

**Root Cause**: AWSTransformAgentInvokeRole trust policy doesn't include the correct AWS Transform compute service principal for your environment.

**Solution**: Trust policy must include the AWS Transform compute service principal:

```yaml
AssumeRolePolicyDocument:
  Version: "2012-10-17"
  Statement:
    - Effect: Allow
      Principal:
        Service:
          - prod.us-east-1.compute.elastic-gumby.aws.internal
      Action: sts:AssumeRole
```

**Verification**:
```bash
aws iam get-role --role-name AWSTransformAgentInvokeRole --query 'Role.AssumeRolePolicyDocument'
```

---

### Issue 5: Missing Bedrock and Agentic API Permissions in AgentCoreExecutionRole

**Symptom**:
```
AccessDeniedException: User: arn:aws:sts::111122223333:assumed-role/AgentCoreExecutionRole/...
is not authorized to perform: bedrock:InvokeModel / transform-agents:GetAgentInstance
```

**Root Cause**: AgentCoreExecutionRole missing Bedrock and AWS Transform Agentic API permissions.

**Solution**: Add required permissions to AgentCoreExecutionRole:

```yaml
- Sid: BedrockInvoke
  Effect: Allow
  Action:
    - bedrock:InvokeModel
    - bedrock:InvokeModelWithResponseStream
    - bedrock-runtime:Converse
    - bedrock-runtime:InvokeModel
  Resource: "*"
- Sid: TransformAgentsApiPolicy
  Effect: Allow
  Action:
    - transform-agents:*
  Resource: "*"
```

**Note**: Bedrock AgentCore needs broad access because:
- Agents may invoke different Bedrock models dynamically
- Agents need to call various AWS Transform Agentic API operations (GetAgentInstance, UpdateJobStatus, etc.)
Using `Resource: "*"` is intentional and recommended.

---

### Issue 6: Wrong Platform Architecture (x86_64 instead of arm64)

**Symptom**:
```
Container exited with code 1: exec /usr/local/bin/python: exec format error
```

**Root Cause**: Image was built for x86_64 but Bedrock AgentCore runtimes run on ARM64 (Graviton) instances.

**Solution**: Always specify `--platform linux/arm64` in Dockerfile FROM directive:

```dockerfile
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.11-slim
```

**Verification**:
```bash
finch inspect modernization-orchestrator:latest | grep Architecture
# Should output: "Architecture": "arm64"
```

**Build Command**:
```bash
finch build --platform linux/arm64 -f Dockerfile -t my-agent:latest .
```

---

### Issue 7: Bedrock AgentCore Runtime Stuck in CREATING State

**Symptom**: Runtime status stays "CREATING" for >5 minutes, never reaches READY.

**Root Cause**: Typically one of:
1. Image pull failure (ECR permissions)
2. Container health check failing
3. Container crashes immediately on startup

**Solution**: Check Bedrock AgentCore runtime failure reasons:

```bash
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id abc123def456 \
  --region us-east-1 \
  --query 'statusReasons'
```

**Common Failure Reasons**:
- `IMAGE_PULL_FAILED`: AgentCoreExecutionRole lacks ECR permissions
- `CONTAINER_UNHEALTHY`: Health check endpoint not responding
- `CONTAINER_EXITED`: Application crashed (check CloudWatch logs)

**Debugging**:
1. Verify ECR permissions in AgentCoreExecutionRole
2. Test health check locally: `curl http://localhost:8080/ping`
3. Check CloudWatch log group: `/aws/bedrock-agentcore/agent-runtime/<runtime-id>`

---

### Issue 8: Registry Endpoint Mismatch (Prod vs Gamma)

**Symptom**: Agent registration succeeds but agent doesn't appear in AWS Transform UI.

**Root Cause**: Registered to wrong registry endpoint.

**Solution**: Verify registry endpoint is the prod endpoint:

```json
{
  "atx_registry_endpoint": "https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev"
}
```

**Verification**:
```bash
aws atxagentregistryexternal get-agent \
  --name my-agent \
  --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
  --region us-east-1
```

---

## Section 7: End-to-End Example

### Reference Implementation

The complete working implementation is available in the AWS Transform modernization workshop demo project:

**Location**: `<your-project-root>/pipeline/`

**Key Files**:
```
pipeline/
├── deploy_agents.py       # Four-phase deployment automation
├── iam-roles.yaml         # CloudFormation IAM role definitions
├── config.json            # Agent configuration and AWS settings
└── README.md              # Setup and usage instructions

src/
├── orchestrator/
│   ├── Dockerfile         # Orchestrator container definition
│   ├── app.py             # Flask app with /invoke endpoint
│   ├── orchestrator.py    # Multi-agent orchestration logic
│   └── requirements.txt   # Python dependencies
└── subagents/
    ├── Dockerfile.analysis         # Analysis agent container
    ├── Dockerfile.transformation   # Transformation agent container
    ├── code_analysis_subagent.py
    ├── code_transformation_subagent.py
    └── requirements.txt

```

### Running the Example

1. **Clone the demo project**:
   ```bash
   cd <your-project-root>
   ```

2. **Configure AWS credentials**:
   ```bash
   export AWS_PROFILE=your-profile
   export AWS_REGION=us-east-1
   ```

3. **Deploy IAM roles** (one-time setup):
   ```bash
   aws cloudformation deploy \
     --template-file pipeline/iam-roles.yaml \
     --stack-name aws-transform-agent-iam-roles \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1
   ```

4. **Edit configuration**:
   ```bash
   # Edit pipeline/config.json with your account ID and registry endpoint
   vi pipeline/config.json
   ```

5. **Run full pipeline**:
   ```bash
   python pipeline/deploy_agents.py
   ```

   **Expected Output**:
   ```
   ============================================================
   PHASE 1: BUILD
   ============================================================
   Building code-analysis-agent from src/subagents/Dockerfile.analysis ...
     ✓ Image code-analysis-agent:latest built successfully
     ✓ Saved docker-images/code-analysis-agent.tar (156.3 MB)

   ============================================================
   PHASE 2: PUSH TO ECR
   ============================================================
   Logging in to ECR...
     ✓ ECR login successful
   Ensuring ECR repo aws-transform-agents/code-analysis-agent exists...
     ✓ Created aws-transform-agents/code-analysis-agent
     ✓ Image aws-transform-agents/code-analysis-agent:latest verified in ECR

   ============================================================
   PHASE 3: DEPLOY TO AGENTCORE
   ============================================================
   Creating Bedrock AgentCore runtime for code-analysis-agent ...
     ✓ Created runtime ID: abc123def456
     Polling runtime status for code-analysis-agent (timeout 120s)...
     [ 10s] code-analysis-agent status: CREATING
     [ 20s] code-analysis-agent status: CREATING
     [ 30s] code-analysis-agent status: READY
     ✓ code-analysis-agent is READY (ARN: arn:aws:bedrock-agentcore:...)

   ============================================================
   PHASE 4: REGISTER WITH AWS TRANSFORM
   ============================================================
   Registering code-analysis-agent with AWS Transform registry...
     ✓ Registered code-analysis-agent
     ✓ Published version 1.0.0 for code-analysis-agent
     ✓ Access granted for code-analysis-agent to account 111122223333

   ============================================================
   DEPLOYMENT COMPLETE
   ============================================================
     code-analysis-agent
       Runtime ID:  abc123def456
       Runtime ARN: arn:aws:bedrock-agentcore:us-east-1:111122223333:agent-runtime/abc123def456

   All 3 agents deployed and registered successfully.
   ```

6. **Iterate on deployment** (skip build/push to save time):
   ```bash
   python pipeline/deploy_agents.py --skip-build --skip-push
   ```

### Verification Steps

1. **Verify Bedrock AgentCore runtimes**:
   ```bash
   aws bedrock-agentcore-control list-agent-runtimes --region us-east-1
   ```

2. **Verify registry entries**:
   ```bash
   aws atxagentregistryexternal get-agent \
     --name code-analysis-agent \
     --endpoint-url https://iad.prod.agent-registry-external.elastic-gumby.ai.aws.dev \
     --region us-east-1
   ```

3. **Test agent invocation** (via AWS Transform):
   ```bash
   # This requires AWS Transform access
   curl -X POST https://your-atx-instance/api/v1/invoke \
     -H "Content-Type: application/json" \
     -d '{
       "agentName": "code-analysis-agent",
       "agentVersion": "1.0.0",
       "payload": {"request": "analyze this code"}
     }'
   ```

---

## Summary

This guide covers the complete AWS Transform agent deployment lifecycle:

1. **IAM Setup**: Two roles (AgentCoreExecutionRole, AWSTransformAgentInvokeRole) with precise trust policies
2. **Build Pipeline**: Four-phase automation (Build → Push → Deploy → Register) with error handling
3. **Docker Best Practices**: ARM64 platform, SDK wheel installation, MCP wrapper creation
4. **Bedrock AgentCore Operations**: Create, poll, verify runtimes with proper status checking
5. **Common Issues**: Solutions for Docker auth, runtime cooldown, trust policies, platform mismatches

**Key Takeaways**:
- Always use `finch` instead of `docker` on macOS/Linux (finch is not available on Windows — use Docker Desktop there)
- Include seconds in runtime name timestamps
- Specify `--platform linux/arm64` for all builds
- Poll Bedrock AgentCore status until READY/ACTIVE before registration
- Use `--cli-input-json` or named parameters to avoid silent failures
- Trust the prod principal in AWSTransformAgentInvokeRole

**Reference Implementation**: `<your-project-root>/pipeline/`

## Alternative: Using MCP Deployment Tools (Recommended)

Instead of manual shell scripts, you can deploy agents directly from Kiro using the new MCP deployment tools:

```python
# Full pipeline (build → push → deploy → register)
deploy_agent_full_pipeline(
    agent_path="./agents/modernization",
    agent_name="modernization-orchestrator",
    owner_contact_info="team@example.com",
    agent_version="1.0.0"
)
```

**Advantages of MCP Tools:**
- **Cross-platform**: Works on Windows (uses CodeBuild), macOS (uses finch), and Linux (uses docker)
- **Auto-detection**: Automatically detects best container runtime and IAM roles
- **Error handling**: Returns structured errors with helpful hints
- **No manual scripts**: No need to maintain separate shell scripts for each phase
- **Conversational**: Deploy agents through natural conversation with Kiro

**See**: [Deploy Agent Workflow Guide](deploy-agent-workflow.md) for detailed instructions on using MCP deployment tools.

For additional patterns, see:
- [Orchestrator Patterns](orchestrator-patterns.md)
- [Subagent Patterns](subagent-patterns.md)
- [Agent Registration](agent-registration.md)
- **[Deploy Agent Workflow](deploy-agent-workflow.md)** - Recommended deployment method using MCP tools
