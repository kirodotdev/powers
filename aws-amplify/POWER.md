---
name: "aws-amplify"
displayName: "AWS Amplify"
description: "Build full-stack applications with AWS Amplify Gen 2 using guided workflows for backend, frontend, and deployment"
keywords: ["amplify", "aws", "fullstack", "backend", "frontend", "auth", "graphql", "serverless", "gen2", "typescript", "react", "nextjs"]
author: "AWS"
---

# AWS Amplify

Build production-ready full-stack applications with AWS Amplify Gen 2. This power leverages AWS MCP Agent SOPs for backend implementation, frontend integration, and deployment workflows.

## Overview

AWS Amplify Gen 2 is a code-first, TypeScript-native framework for building full-stack applications on AWS. This power provides guided access to three specialized Agent SOPs:

| Workflow | SOP Name | Use When |
|----------|----------|----------|
| Backend Implementation | `amplify-backend-implementation` | Setting up Auth, Data, Storage, Functions, AI |
| Frontend Integration | `amplify-frontend-integration` | Connecting frontend framework to backend |
| Deployment Guide | `amplify-deployment-guide` | Sandbox, production, CI/CD setup |

## When to Load Steering Files

- Building backend services (Auth, Data, Storage, Functions) → `backend-implementation.md`
- Integrating frontend framework with Amplify → `frontend-integration.md`
- Deploying to sandbox or production → `deployment-guide.md`

## Amplify Gen 2 vs Gen 1

**This power is exclusively for Amplify Gen 2.** Gen 1 is deprecated.

| Approach | Gen 1 (Deprecated) | Gen 2 (Use This) |
|----------|-------------------|------------------|
| Configuration | CLI commands | Code-first TypeScript |
| Resource creation | `amplify add auth` | Define in `amplify/auth/resource.ts` |
| Deployment | `amplify push` | `npx ampx sandbox` or Git-based |
| Type safety | Manual | Auto-generated types |

**Never use:** `amplify init`, `amplify add`, `amplify push`, `amplify pull`

## Available MCP Server

**Server:** `aws-mcp`

### Tools

| Tool | Purpose |
|------|---------|
| `retrieve_agent_sop` | Get step-by-step Amplify workflows |
| `search_documentation` | Search Amplify Gen 2 documentation |
| `read_documentation` | Read specific documentation pages |
| `call_aws` | Execute AWS CLI commands |

### Agent SOPs

Retrieve workflows using `retrieve_agent_sop` with these SOP names:

- `amplify-backend-implementation` - Auth, Data, Storage, Functions setup
- `amplify-frontend-integration` - Framework integration patterns
- `amplify-deployment-guide` - Deployment and CI/CD workflows

## Onboarding

### Prerequisites

1. **Node.js 18+** - Required for Amplify Gen 2
2. **Python 3.10+** - Required for uv package manager
3. **uv package manager** - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
4. **AWS credentials** - Via `aws configure`, SSO, or environment variables

### Verify Setup

```bash
node --version    # Should be 18+
uv --version      # Should be installed
aws sts get-caller-identity  # Should show your identity
```

### Required AWS Permissions

For AWS MCP Server access:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "aws-mcp:InvokeMcp",
      "aws-mcp:CallReadOnlyTool",
      "aws-mcp:CallReadWriteTool"
    ],
    "Resource": "*"
  }]
}
```

For Amplify development, attach `AdministratorAccess-Amplify` AWS-managed policy.

## Quick Start

Ask your AI assistant:
- "Help me set up authentication for my app"
- "Create a data model for a todo application"
- "Connect my React app to Amplify"
- "Deploy my app to a sandbox environment"

## Project Structure

Amplify Gen 2 projects follow this structure:

```
my-app/
├── amplify/
│   ├── auth/
│   │   └── resource.ts      # Authentication config
│   ├── data/
│   │   └── resource.ts      # Data model schema
│   ├── storage/
│   │   └── resource.ts      # File storage config
│   ├── functions/
│   │   └── my-function/     # Lambda functions
│   └── backend.ts           # Backend entry point
├── src/                      # Frontend code
├── amplify_outputs.json      # Generated config
└── package.json
```

## Supported Frameworks

Amplify Gen 2 supports these frontend frameworks:

| Framework | Category |
|-----------|----------|
| React | Web |
| Next.js | Web (SSR) |
| Vue | Web |
| Angular | Web |
| JavaScript/TypeScript | Web |
| React Native | Mobile |
| Flutter | Mobile |
| Swift | iOS |
| Android (Kotlin) | Android |

## Troubleshooting

### MCP Connection Issues
1. Verify uv: `uv --version`
2. Check AWS credentials: `aws sts get-caller-identity`
3. Restart Kiro

### Permission Errors
1. Verify `aws-mcp:*` IAM permissions
2. Check `AdministratorAccess-Amplify` is attached
3. Test: `aws amplify list-apps`

### Sandbox Failures
1. Check CloudFormation events in AWS Console
2. Verify Node.js 18+ is installed
3. Clear cache: `rm -rf node_modules/.cache`

## Support

**CTI:** AWS/Amplify/JS

---

This power integrates with AWS MCP Server (Apache-2.0 license).
