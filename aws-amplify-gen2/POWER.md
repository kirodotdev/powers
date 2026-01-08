---
name: "aws-amplify-gen2"
displayName: "AWS Amplify Gen 2"
description: "Complete guide for building full-stack applications with AWS Amplify Gen 2, including backend implementation, frontend integration, and deployment workflows using AWS MCP Agent SOPs"
keywords: ["amplify", "gen2", "aws", "fullstack", "backend", "frontend", "deployment"]
author: "Davide De Sio"
---

# AWS Amplify Gen 2

## Overview

This power provides comprehensive guidance for building full-stack applications with AWS Amplify Gen 2 using pre-built Agent SOPs (Standard Operating Procedures). It leverages the AWS MCP server to execute structured workflows that follow Amplify best practices for backend implementation, frontend integration, and deployment.

AWS Amplify Gen 2 represents the next generation of full-stack development on AWS, providing type-safe, Git-based workflows with enhanced developer experience. This power specifically focuses on Gen 2 capabilities and never uses legacy Gen 1 approaches.

The power includes three core Agent SOPs that guide you through the complete application lifecycle:
- **Backend Implementation**: Authentication, data models, storage, serverless functions, and AI features
- **Frontend Integration**: Connecting modern JavaScript/TypeScript frameworks to Amplify backend services  
- **Deployment Guide**: Sandbox environments, production deployments, and CI/CD pipelines

**CRITICAL for AI Agents**: 
1. **NEVER use Amplify Gen 1 commands** - This power is exclusively for Amplify Gen 2. Gen 1 commands are deprecated and incompatible.
2. **Always ask which SOP to execute** - When a user requests Amplify help, present the three available SOPs and let them choose the appropriate workflow.
3. **Only use AWS MCP Agent SOPs** - All Amplify guidance must come from the retrieved SOPs, never from general knowledge about older Amplify versions.

## Amplify Gen 2 vs Gen 1: Critical Differences

**⚠️ IMPORTANT: This power is ONLY for Amplify Gen 2. Never use Gen 1 commands or approaches.**

### Prohibited Gen 1 Commands (NEVER USE):
```bash
# ❌ NEVER use these Gen 1 commands:
amplify init
amplify add auth
amplify add api
amplify add storage
amplify add function
amplify push
amplify pull
amplify publish
amplify configure
amplify status
amplify env
```

### Required Gen 2 Approach:
- **Use AWS MCP Agent SOPs exclusively** - All guidance comes from the three SOPs
- **Code-first configuration** - Define resources in TypeScript/JavaScript files
- **Git-based workflows** - No CLI commands for resource management
- **Type-safe development** - Generated types for all resources

### Gen 2 Project Structure:
```
my-amplify-app/
├── amplify/
│   ├── auth/
│   ├── data/
│   ├── storage/
│   └── backend.ts
├── src/
└── package.json
```

**If you encounter Gen 1 references:**
1. Stop immediately
2. Retrieve the appropriate Gen 2 SOP using `aws___retrieve_agent_sop`
3. Follow only the SOP guidance for Gen 2 implementation

## Available Agent SOPs

This power provides access to three specialized Agent SOPs through the AWS MCP server:

### amplify-backend-implementation
Guides implementation of well-structured backend applications using Amplify Gen 2 capabilities including Auth, Data, Storage, and Functions. Promotes recommended patterns, secure defaults, and idiomatic use of Amplify's backend abstractions.

### amplify-frontend-integration  
Provides guidance for integrating Amplify backend with modern JavaScript and TypeScript frameworks. Covers state management recommendations, data binding patterns, and configuration best practices using Amplify libraries.

### amplify-deployment-guide
Walks through deploying applications using Amplify Gen 2. Covers branch-based workflows, CI/CD configuration, environment setup, and operational guardrails for production-ready deployments.

## Onboarding

### Prerequisites

**Core Requirements:**
- Python 3.10+ installed on your machine
- uv package manager installed  
- AWS credentials configured locally (via `aws configure`, SSO, or environment variables)

**AWS Permissions:**
Your AWS credentials must include the following permissions:

**For AWS MCP Server Operations:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aws-mcp:InvokeMCP",
                "aws-mcp:CallReadOnlyTool", 
                "aws-mcp:CallReadWriteTool"
            ],
            "Resource": "*"
        }
    ]
}
```

**For Amplify Gen 2 Sandbox Deployment:**
- Permissions equivalent to `AmplifyBackendDeployFullAccess` AWS-managed policy

**For Amplify Application Management:**
- `AdministratorAccess-Amplify` AWS-managed policy (recommended for full functionality)

### Installation

**Install uv package manager:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Configure AWS credentials:**
```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-west-2
```

**Verify setup:**
```bash
# Check uv installation
uv --version

# Check AWS credentials
aws sts get-caller-identity

# Test AWS MCP server
uvx mcp-proxy-for-aws@latest --help
```

## Common Workflows

### Agent Workflow: SOP Selection Process

**When a user requests Amplify Gen 2 help, follow this process:**

1. **Assess the user's current stage:**
   - Do they need to set up backend infrastructure? → `amplify-backend-implementation`
   - Do they have a backend and need frontend integration? → `amplify-frontend-integration`
   - Do they need to deploy their application? → `amplify-deployment-guide`
   - Are they unsure what they need? → Present all options

2. **Present available SOPs:**
   ```
   I can help you with Amplify Gen 2 development using these specialized workflows:
   
   🏗️ **Backend Implementation** - Set up authentication, data models, storage, and functions
   🎨 **Frontend Integration** - Connect your frontend framework to Amplify backend services
   🚀 **Deployment Guide** - Deploy to sandbox or production environments
   
   Which workflow would be most helpful for your current task?
   ```

3. **Execute the chosen SOP:**
   Use `aws___retrieve_agent_sop` tool with the selected SOP name

### Workflow 1: Backend Implementation

**When to use:** Setting up new backend infrastructure or adding backend services

**User scenarios:**
- "I need to add authentication to my app"
- "Help me set up a data layer with GraphQL"
- "I want to add file storage to my application"
- "I need to create serverless functions"

**Agent process:**
1. Confirm this is the right SOP: "I'll help you implement backend services using the amplify-backend-implementation SOP."
2. Execute: `aws___retrieve_agent_sop` with `sop_name: "amplify-backend-implementation"`
3. Follow the retrieved SOP guidance for backend setup

**Expected outcome:** Fully configured Amplify Gen 2 backend with type-safe schema

### Workflow 2: Frontend Integration

**When to use:** Connecting frontend applications to existing Amplify backend

**User scenarios:**
- "I have a backend set up, now I need to connect my React app"
- "How do I integrate authentication in my Vue.js app?"
- "I need to fetch data from my GraphQL API in Next.js"
- "Help me set up state management for my Amplify app"

**Agent process:**
1. Confirm this is the right SOP: "I'll help you integrate your frontend with the Amplify backend using the amplify-frontend-integration SOP."
2. Execute: `aws___retrieve_agent_sop` with `sop_name: "amplify-frontend-integration"`
3. Follow the retrieved SOP guidance for frontend integration

**Expected outcome:** Fully integrated frontend with type-safe Amplify operations

### Workflow 3: Deployment Guide

**When to use:** Deploying applications to sandbox or production environments

**User scenarios:**
- "I want to deploy my app to a sandbox for testing"
- "How do I set up CI/CD for my Amplify app?"
- "I need to deploy to production"
- "Help me configure different environments"

**Agent process:**
1. Confirm this is the right SOP: "I'll help you deploy your Amplify application using the amplify-deployment-guide SOP."
2. Execute: `aws___retrieve_agent_sop` with `sop_name: "amplify-deployment-guide"`
3. Follow the retrieved SOP guidance for deployment

**Expected outcome:** Live environment ready for testing or production use

### Workflow 4: Full Application Development

**When to use:** Building a complete application from scratch

**User scenarios:**
- "I want to build a full-stack app with Amplify Gen 2"
- "Help me create a complete application from start to finish"
- "I need guidance on the entire development process"

**Agent process:**
1. Explain the complete workflow: "I'll guide you through building a complete Amplify Gen 2 application. We'll work through three phases: backend implementation, frontend integration, and deployment."
2. Start with backend: Execute `amplify-backend-implementation` SOP
3. Move to frontend: Execute `amplify-frontend-integration` SOP  
4. Finish with deployment: Execute `amplify-deployment-guide` SOP
5. Provide guidance between each phase

**Expected outcome:** Complete, deployed full-stack application

## Tool Usage Examples

### Retrieving Agent SOPs

The AWS MCP server provides the `aws___retrieve_agent_sop` tool to access pre-built workflows:

**Tool:** `aws___retrieve_agent_sop`
**Parameters:**
- `sop_name`: Name of the SOP to retrieve
- `context`: Optional context for the workflow

**Example usage:**
```
Tool: aws___retrieve_agent_sop
Parameters: {
  "sop_name": "amplify-backend-implementation",
  "context": "Building a todo app with user authentication"
}
```

### Available SOP Names

- `amplify-backend-implementation` - Backend setup and configuration
- `amplify-frontend-integration` - Frontend framework integration  
- `amplify-deployment-guide` - Deployment and CI/CD workflows

## Best Practices

### Amplify Gen 2 Specific

- **NEVER use Gen 1 commands** - Amplify CLI commands like `amplify init`, `amplify add`, `amplify push` are Gen 1 only and incompatible with Gen 2
- **Always use Gen 2 syntax** - Code-first configuration in TypeScript/JavaScript files
- **Leverage type safety** - Use generated TypeScript types throughout
- **Follow Git-based workflows** - Use branch-based development and deployment
- **Use secure defaults** - Let Amplify configure security best practices
- **Implement proper error handling** - Handle authentication and API errors gracefully
- **Only follow SOP guidance** - All implementation must follow the retrieved Agent SOPs, never general Amplify knowledge

### Development Workflow

- **Start with backend** - Define your data schema and authentication first
- **Use sandbox environments** - Test changes in isolated environments before production
- **Follow SOP guidance** - Let the Agent SOPs guide implementation decisions
- **Validate permissions** - Ensure AWS credentials have required permissions
- **Monitor deployments** - Use Amplify console to track deployment status

### Security Considerations

- **Use least privilege** - Grant only necessary AWS permissions
- **Secure API endpoints** - Implement proper authentication on all GraphQL operations
- **Validate user input** - Use Amplify's built-in validation features
- **Monitor access patterns** - Use CloudWatch to monitor API usage
- **Regular credential rotation** - Rotate AWS credentials regularly

## Troubleshooting

### MCP Server Connection Issues

**Problem:** AWS MCP server won't start or connect
**Symptoms:**
- Error: "Connection refused"
- Timeout errors during tool execution

**Solutions:**
1. Verify uv installation: `uv --version`
2. Test MCP server directly: `uvx mcp-proxy-for-aws@latest --help`
3. Check AWS credentials: `aws sts get-caller-identity`
4. Verify network connectivity to AWS MCP endpoint
5. Restart Kiro and try again

### Permission Errors

**Problem:** AWS operations fail with permission denied
**Symptoms:**
- Error: "User is not authorized to perform action"
- Access denied messages

**Solutions:**
1. Verify AWS credentials are configured: `aws configure list`
2. Check IAM permissions include required policies:
   - `aws-mcp:InvokeMCP`
   - `AmplifyBackendDeployFullAccess`
   - `AdministratorAccess-Amplify`
3. Test permissions: `aws amplify list-apps`
4. Contact AWS administrator if using organizational account

### Amplify Deployment Failures

**Problem:** Sandbox deployment fails or times out
**Symptoms:**
- Deployment stuck in "IN_PROGRESS" status
- CloudFormation stack errors
- Resource creation failures

**Solutions:**
1. Check AWS region configuration matches Amplify app region
2. Verify sufficient AWS service limits (Lambda functions, S3 buckets, etc.)
3. Review CloudFormation events in AWS console
4. Clean up failed resources: `amplify delete`
5. Retry deployment with fresh environment

### Agent SOP Retrieval Issues

**Problem:** Cannot retrieve or execute Agent SOPs
**Symptoms:**
- Error: "SOP not found"
- Tool execution timeouts

**Solutions:**
1. Verify SOP name spelling:
   - `amplify-backend-implementation`
   - `amplify-frontend-integration`
   - `amplify-deployment-guide`
2. Check AWS MCP server status
3. Verify network connectivity
4. Try retrieving SOP manually to test connection

## Configuration

### Environment Variables

The AWS MCP server supports these environment variables:

- `AWS_REGION`: AWS region for operations (default: us-west-2)
- `AWS_PROFILE`: AWS CLI profile to use
- `AWS_ACCESS_KEY_ID`: AWS access key (if not using profiles)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (if not using profiles)

### MCP Server Configuration

The power uses this MCP server configuration:

```json
{
  "mcpServers": {
    "aws-mcp": {
      "command": "uvx",
      "timeout": 100000,
      "transport": "stdio", 
      "args": [
        "mcp-proxy-for-aws@latest",
        "https://aws-mcp.us-east-1.api.aws/mcp",
        "--metadata", "AWS_REGION=us-west-2"
      ]
    }
  }
}
```

**Configuration Notes:**
- High timeout (100s) accommodates complex AWS operations
- Region can be customized via metadata parameter
- Uses latest version of mcp-proxy-for-aws for newest features

---

**MCP Server:** aws-mcp  
**Package:** mcp-proxy-for-aws@latest  
**Agent SOPs:** amplify-backend-implementation, amplify-frontend-integration, amplify-deployment-guide