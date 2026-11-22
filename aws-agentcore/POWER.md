---
name: "aws-agentcore"
displayName: "Build an agent with Amazon Bedrock AgentCore"
description: "Build, test, and deploy AI agents using Amazon Bedrock AgentCore with local development workflow. Amazon Bedrock AgentCore is an agentic platform for building, deploying, and operating effective agents."
keywords: ["agentcore", "bedrock", "aws", "agents", "ai", "development", "agent"]
author: "AWS"
---

# Amazon Bedrock AgentCore

## Overview

Build and deploy AI agents on Amazon Bedrock AgentCore with the AgentCore CLI (`agentcore`, npm package `@aws/agentcore`). The CLI creates a project, runs agents locally, deploys them with AWS CDK, and invokes them. This power adds the AgentCore MCP server for documentation search, reference guides, and direct access to AgentCore resources.

An AgentCore project is a directory with:

- `agentcore/agentcore.json`: the resources the project declares (runtimes, harnesses, memories, gateways, credentials).
- `agentcore/cdk/`: the CDK app that `agentcore deploy` uses.
- `agentcore/aws-targets.json`: deployment targets (account and region). The `default` target is created on the first deploy.
- `app/<name>/`: the code for each runtime.

A project can hold two kinds of agents:

- **Runtime**: agent code you own, scaffolded from a template (Strands, LangChain, Vercel AI SDK, A2A, AG-UI, MCP) or written yourself, in Python or TypeScript.
- **Harness**: a managed agent configured with a model, system prompt, tools, and skills, which AgentCore runs for you.

## When to Use This Power

- Creating a new agent project with `agentcore create`
- Bringing an existing agent into AgentCore Runtime
- Running an agent locally with `agentcore dev` and testing it with `agentcore invoke --local`
- Deploying with `agentcore deploy` and invoking the deployed agent
- Adding AgentCore Memory or Gateway to an agent
- Reading logs and checking deployed resources
- Searching AgentCore documentation

## Prerequisites

- Node.js 20.12 or later
- `uv` for Python agents
- AWS credentials configured as for the AWS CLI (for deploying, and for local runs of agents that call Amazon Bedrock)

```bash
npm install -g @aws/agentcore
agentcore --version
```

The older Python package `bedrock-agentcore-starter-toolkit` also installs an `agentcore` command, with different commands (`agentcore configure`, `agentcore launch`). If it is installed, uninstall it so the right `agentcore` is on the PATH: `pip uninstall bedrock-agentcore-starter-toolkit`.

## Steering Files

- **getting-started.md**: create a project or bring an existing agent, then the dev, deploy, and invoke workflow.
  Call action "readSteering" with powerName="aws-agentcore", steeringFile="getting-started.md"
- **agentcore-memory-integration.md**: add AgentCore Memory to a project and use it from a Strands agent.
  Call action "readSteering" with powerName="aws-agentcore", steeringFile="agentcore-memory-integration.md"
- **agentcore-gateway-integration.md**: add an AgentCore Gateway with MCP server, Lambda, or runtime targets, and call it from a Strands agent.
  Call action "readSteering" with powerName="aws-agentcore", steeringFile="agentcore-gateway-integration.md"

## Rules for Running the CLI

- Pass flags so commands run non-interactively. A command run without flags in a terminal opens an interactive flow. Add `--json` for machine-readable output.
- Run `agentcore <command> --help` when unsure of a flag. The installed CLI is the source of truth.
- Run `agentcore create` outside any existing project. Other project commands find the project by walking up from the current directory.
- Do not edit `agentcore/agentcore.json` by hand unless the user asks. Use `agentcore add` and `agentcore remove`.
- `agentcore deploy` creates AWS resources that cost money. Confirm with the user before deploying or tearing down.

## Available MCP Tools

The `agentcore-mcp-server` (`awslabs.amazon-bedrock-agentcore-mcp-server`) provides:

- `search_agentcore_docs`, `fetch_agentcore_doc`: search and read AgentCore documentation.
- `get_runtime_guide`, `get_memory_guide`, `get_gateway_guide`, `get_identity_guide`, `get_policy_guide`: reference guides for each service.
- Resource tools that call AgentCore APIs directly, for example `list_agent_runtimes`, `invoke_agent_runtime`, `memory_list`, `memory_retrieve_records`, `gateway_list`, `gateway_target_list`. Tools that create, update, or delete resources change the user's AWS account; prefer the CLI for resources the project owns, since `agentcore deploy` manages them.

The guides include CLI examples that can lag behind the installed CLI. When a guide and `agentcore --help` disagree, follow `--help`.

Search the documentation:

```
usePower("aws-agentcore", "agentcore-mcp-server", "search_agentcore_docs", {
  "query": "runtime session lifecycle"
})
```

Get the Memory reference guide:

```
usePower("aws-agentcore", "agentcore-mcp-server", "get_memory_guide", {})
```

## Troubleshooting

**`agentcore` rejects `configure`, `launch`, or `--non-interactive`:** those belong to the old starter toolkit. Use `agentcore deploy` and the commands in getting-started.md.

**`error: unknown option` on a documented flag:** an older `agentcore` (the starter toolkit, or an old `@aws/agentcore`) is first on the PATH. Check `agentcore --version` and `which agentcore`.

**`You cannot create a project inside an existing project`:** run `agentcore create` from a directory outside the project.

**`Could not reach local dev server on port 8080`:** start `agentcore dev` first, and pass `--runtime <name>` and `--local` to `agentcore invoke`.

**`Unable to locate credentials` or `NoCredentialsError`:** the agent or the CLI has no AWS credentials. Run `aws login`, or set `AWS_PROFILE` or the credential environment variables. Local runs need credentials too when the agent calls Amazon Bedrock.

**`Cannot create the default deployment target ... the AWS account could not be resolved`:** `agentcore deploy` could not find credentials or the region is not enabled. Sign in and set `--region` or `AWS_REGION`.

**Model access errors:** verify the AWS account has access to the model in Amazon Bedrock in the deployment region.

## Additional Resources

- [AgentCore CLI](https://github.com/aws/agentcore-cli) and its [command reference](https://github.com/aws/agentcore-cli/blob/main/command.md)
- [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [AgentCore SDK for Python](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
