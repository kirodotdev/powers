---
name: 'localstack'
displayName: 'Develop AWS apps with LocalStack'
description: 'Build, test, and debug AWS applications locally and in CI/CD using LocalStack. Manage the local cloud environment, deploy infrastructure with CDK/Terraform/SAM, analyze logs, enforce IAM policies, inject chaos faults, and manage state snapshots.'
keywords:
  [
    'localstack',
    'aws',
    'local',
    'cloud',
    'emulation',
    'testing',
    'lambda',
    's3',
    'dynamodb',
    'terraform',
    'cdk',
    'cloudformation',
    'iam',
    'chaos',
    'cloud-pods',
    'ephemeral',
    'mocking',
    'local-dev',
  ]
author: 'LocalStack'
---

# LocalStack Power

## Overview

LocalStack is a fully functional local cloud stack that emulates AWS services on your machine. The LocalStack Power gives you intelligent tooling to manage your local cloud environment, deploy infrastructure, debug issues, and simulate real-world failure conditions — with no cloud waste.

Every developer must use a LocalStack auth token (including free Hobby accounts); your plan tier determines which product features and MCP tools you can use.

## Onboarding

**CRITICAL: You MUST complete every step below in order. Do NOT skip ahead. After each step, mark it done before proceeding to the next.**

### Onboarding Checklist

- [ ] **Step 1 — Validate prerequisites are installed**
- [ ] **Step 2 — Validate auth token is configured for MCP**
- [ ] **Step 3 — Validate auth token is configured for CLI**
- [ ] **Step 4 — Confirm MCP connectivity**
- [ ] **Step 5 — Start LocalStack**

---

### Step 1: Validate prerequisites are installed

Run each check command. If a tool is missing, show the user the install link and STOP. Do NOT attempt to install anything automatically.

| Tool | Check command | Install reference |
|------|--------------|-------------------|
| Docker | `docker --version` | https://docs.docker.com/get-docker/ |
| LocalStack CLI | `localstack --version` | `pip install localstack` or `brew install localstack/tap/localstack-cli` |
| Node.js v22+ | `node --version` | https://nodejs.org/ |
| awslocal | `which awslocal` | `pip install awscli-local` |

**IMPORTANT validation rules:**
- `which awslocal` is the correct check. `awslocal --version` is NOT a valid command and will fail even when awslocal is installed correctly.
- If ALL tools are present, mark Step 1 done and proceed.
- If ANY tool is missing, tell the user what to install and STOP. Do not proceed until the user confirms installation.

Optional IaC wrappers (only validate if user's project uses them):
- Terraform → `which tflocal` → `pip install terraform-local`
- CDK → `which cdklocal` → `npm install -g aws-cdk-local aws-cdk`
- SAM → `which samlocal` → `pip install aws-sam-cli-local`
- Pulumi → `which pulumilocal` → `pip install pulumi-local`

---

### Step 2: Validate auth token is configured for MCP

The MCP server receives its auth token from the `env.LOCALSTACK_AUTH_TOKEN` entry in `mcp.json`. Check that the user's MCP configuration has a real token value (not the placeholder `${LOCALSTACK_AUTH_TOKEN}` unless their IDE resolves secrets at launch).

**DO NOT:**
- Run `echo $LOCALSTACK_AUTH_TOKEN` or `printenv LOCALSTACK_AUTH_TOKEN` in the shell
- Ask the user to export the token in their shell profile
- Attempt to set the token yourself

**DO:**
- Ask the user: "Does your `mcp.json` have your real LocalStack auth token in `env.LOCALSTACK_AUTH_TOKEN`? You can get one at https://app.localstack.cloud/workspace/auth-token"
- If the user confirms yes → mark Step 2 done.
- If the user says no or is unsure → show them the expected `mcp.json` format and STOP until they confirm it's set:

```json
{
  "mcpServers": {
    "localstack": {
      "command": "npx",
      "args": ["-y", "@localstack/localstack-mcp-server"],
      "env": {
        "LOCALSTACK_AUTH_TOKEN": "ls-your-actual-token-here"
      }
    }
  }
}
```

---

### Step 3: Validate auth token is configured for CLI

The CLI stores its own token separately from MCP. Run:

```bash
localstack auth show-token
```

- If output shows `Valid: True` → mark Step 3 done.
- If output shows the token is not set or invalid → tell the user to run `localstack auth set-token <TOKEN>` and STOP until they confirm it's done.

**DO NOT** run `localstack auth set-token` yourself or ask the user to paste their token into chat.

---

### Step 4: Confirm MCP connectivity

Call the **`localstack-docs`** MCP tool with a simple query (e.g., `"LocalStack overview"`).

- If the tool responds successfully → mark Step 4 done. This confirms the MCP server is running and the token is accepted.
- If the tool fails → the MCP server is not connected. Tell the user to check their `mcp.json` configuration and restart the MCP server. STOP until resolved.

**DO NOT** use `localstack-management` for this check — it requires Docker/LocalStack to be running. `localstack-docs` works without a running instance.

---

### Step 5: Start LocalStack

```bash
localstack start -d
```

Verify it's running:

```bash
localstack status
```

- If status shows "running" → mark Step 5 done. Onboarding is complete.
- If it fails → check Docker is running (`docker info`) and port 4566 is free (`lsof -i :4566`).

---

## Available Steering Files

This power ships with focused steering files. Load only what the current task needs — do NOT read them all upfront.

| Steering file | Load when the user is… |
|---------------|------------------------|
| `localstack-best-practices.md` | Doing day-to-day LocalStack development, running health checks, choosing between MCP tools and CLI, setting environment variables, or calling AWS services with `awslocal` |
| `iac-deployment.md` | Deploying infrastructure with Terraform, CDK, SAM, CloudFormation, or Pulumi (including `tflocal`, `cdklocal`, `samlocal`, `pulumilocal` workflows) |
| `state-management.md` | Working with Cloud Pods, `localstack state export/import`, or `PERSISTENCE=1` |
| `mcp-tools-reference.md` | Looking up an MCP tool signature, or working with chaos injection, IAM policy analysis, extensions, or ephemeral instances |
| `troubleshooting.md` | Debugging: LocalStack won't start, MCP server won't connect, services unhealthy, `awslocal` missing, Lambda/SQS misbehaving |

Use the `readSteering` action to load a file on demand. If a task spans multiple areas, load the files in order of relevance rather than loading everything.

## Quick Start (post-onboarding)

Once onboarding is complete, try:

```
"Create an S3 bucket called my-test-bucket"
"Deploy my Terraform configuration to LocalStack"
"Show me any errors in the LocalStack logs"
"Save the current state as a Cloud Pod"
```

## Learn More

- LocalStack Documentation: https://docs.localstack.cloud
- LocalStack GitHub: https://github.com/localstack/localstack
- LocalStack MCP Server: https://github.com/localstack/localstack-mcp-server
- Community Slack: https://localstack.cloud/slack
- LocalStack Extensions: https://docs.localstack.cloud/user-guide/extensions/
- Cloud Pods Guide: https://docs.localstack.cloud/user-guide/state-management/cloud-pods/
