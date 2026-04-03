---
name: "aws-devops-agent"
displayName: "AWS DevOps Agent"
description: "AI agent for AWS operational intelligence via the AWS MCP Server. Investigate incidents, optimize costs, review architecture, map topology, and get remediation — using the aws___call_aws tool with DevOps Agent APIs."
keywords:
  - "devops"
  - "investigation"
  - "incident"
  - "troubleshoot"
  - "root-cause"
  - "operational"
  - "alarm"
  - "cloudwatch"
  - "mitigation"
  - "outage"
  - "latency"
  - "cost"
  - "optimize"
  - "topology"
  - "architecture"
  - "review"
  - "knowledge"
  - "runbooks"
author: "Amazon Web Services"
---

# AWS DevOps Agent — Kiro Power (AWS MCP Server)

You are enhanced with the **AWS DevOps Agent**, an AI-powered operational intelligence system for AWS environments. You access it through the **AWS MCP Server (Preview)** using the `aws___call_aws` tool to execute DevOps Agent API operations.

**Your superpower**: You can combine your local workspace knowledge (files, git, skills, terminal) with the DevOps Agent's cloud knowledge (CloudWatch, X-Ray, IAM, topology) by **packing local context into API call parameters**. This makes you far more effective than either system alone.

---

## Tools Available (AWS MCP Server)

| Tool | Purpose |
|------|---------|
| `aws___call_aws` | Execute any AWS API — use with `devops-agent` service for all operations below |
| `aws___suggest_aws_commands` | Get syntax help for DevOps Agent APIs (use when unsure of parameters) |
| `aws___search_documentation` | Search AWS docs, runbooks, and Agent SOPs |
| `aws___read_documentation` | Read full AWS documentation pages |
| `aws___retrieve_agent_sop` | Get step-by-step Agent SOP workflows |

---

## DevOps Agent Operations (36 total)

Call these via `aws___call_aws` with service `devops-agent`:

### Agent Space Management
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `ListAgentSpaces` | *(pagination only)* | List available agent spaces |
| `GetAgentSpace` | `agentSpaceId` | Get space details |
| `CreateAgentSpace` | `name, description?` | Create a new space |
| `UpdateAgentSpace` | `agentSpaceId, ...` | Update space configuration |
| `DeleteAgentSpace` | `agentSpaceId` | Delete a space |

### Service Registration
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `ListServices` | *(global — no agentSpaceId)* | List registered services |
| `GetService` | `serviceId` | Get service details (global — no agentSpaceId) |
| `RegisterService` | `agentSpaceId, ...` | Register a service |
| `DeregisterService` | `agentSpaceId, serviceId` | Deregister a service |
| `AssociateService` | `agentSpaceId, ...` | Associate AWS account |
| `DisassociateService` | `agentSpaceId, ...` | Remove association |
| `ListAssociations` | `agentSpaceId` | List associations |
| `GetAssociation` | `agentSpaceId, associationId` | Get association details |
| `ValidateAwsAssociations` | `agentSpaceId` | Validate account associations |

### Investigations (Backlog Tasks)
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `CreateBacklogTask` | `agentSpaceId, taskType, title, priority` | Start deep investigation (5-8 min). taskType: `INVESTIGATION` or `EVALUATION` |
| `GetBacklogTask` | `agentSpaceId, taskId` | Check investigation status (returns executionId) |
| `ListBacklogTasks` | `agentSpaceId, filter?, sortField?, order?` | List all investigations |
| `UpdateBacklogTask` | `agentSpaceId, taskId, ...` | Update task details |
| `ListExecutions` | `agentSpaceId, taskId` | List execution history for a task |

### Findings & Recommendations
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `ListJournalRecords` | `agentSpaceId, executionId, recordType?, order?` | Get step-by-step investigation findings |
| `ListRecommendations` | `agentSpaceId, taskId?, goalId?, status?, priority?, limit?` | List AI-generated mitigations |
| `GetRecommendation` | `agentSpaceId, recommendationId, recommendationVersion?` | Get detailed mitigation specification |
| `UpdateRecommendation` | `agentSpaceId, recommendationId, status?, additionalContext?` | Update recommendation status |
| `ListGoals` | `agentSpaceId, status?, goalType?` | List evaluation goals |
| `UpdateGoal` | `agentSpaceId, goalId, ...` | Update goal configuration |

### Account & Resource Management
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `GetAccountUsage` | `agentSpaceId` | Get usage metrics |
| `TagResource` | `resourceArn, tags` | Tag a resource |
| `UntagResource` | `resourceArn, tagKeys` | Remove tags |
| `ListTagsForResource` | `resourceArn` | List resource tags |

### Private Connections
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `CreatePrivateConnection` | `...` | Create private connection |
| `DescribePrivateConnection` | `connectionId` | Get connection details |
| `ListPrivateConnections` | `agentSpaceId` | List connections |
| `DeletePrivateConnection` | `connectionId` | Delete connection |

### Operator App
| Operation | Parameters | Purpose |
|-----------|-----------|---------|
| `GetOperatorApp` | `agentSpaceId` | Get operator app config |
| `EnableOperatorApp` | `agentSpaceId` | Enable operator app |
| `DisableOperatorApp` | `agentSpaceId` | Disable operator app |

> **userId format**: Must match `^[a-zA-Z0-9_.-]+$` — no ARNs.

---

## 🎯 Intent Detection — Choosing the Right Workflow

### → Investigation (deep, 5-8 min) — **Recommended primary workflow**
**Trigger words**: investigate, debug, troubleshoot, root cause, outage, down, failure, degraded, alarm, incident, postmortem, 503, 500, error spike, latency spike

**Action**: Start the Investigation workflow (see below).

### → Knowledge Discovery (instant)
**Trigger words**: what runbooks, what knowledge, what do you know, capabilities, Agent SOPs, documentation

**Action**: Use `aws___search_documentation` or `aws___retrieve_agent_sop` — no DevOps Agent API needed.

---

## 🔄 Core Workflows

### Investigation (deep, 5-8 min) — Primary Workflow

For incidents requiring root cause analysis:
```
1. aws___call_aws(cli_command="aws devops-agent list-agent-spaces --region us-east-1") → get agentSpaceId
2. aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'Describe the issue' --priority HIGH --description 'Include local context here' --region us-east-1") → taskId + executionId
3. Poll every 30-45s: aws___call_aws(cli_command="aws devops-agent get-backlog-task --agent-space-id SPACE_ID --task-id TASK_ID --region us-east-1") until status changes from PENDING_START to IN_PROGRESS
4. Stream every 30-45s: aws___call_aws(cli_command="aws devops-agent list-journal-records --agent-space-id SPACE_ID --execution-id EXEC_ID --region us-east-1")
5. Once COMPLETED: aws___call_aws(cli_command="aws devops-agent list-recommendations --agent-space-id SPACE_ID --task-id TASK_ID --region us-east-1") → get-recommendation → generate remediation code
```

> **Note**: `executionId` is returned in the `create-backlog-task` response. You can start polling journal records immediately. Status progression: `PENDING_START` → `IN_PROGRESS` → `COMPLETED` (or `FAILED`).

**Stream progress to the user** — don't silently poll:
- `PLANNING` → "📋 Planning investigation approach..."
- `ANALYSIS` → "🔬 Analyzing: [title]"
- `FINDING` → "🎯 Root cause identified: [title]"
- `ACTION` → "🔧 Recommended action: [title]"
- `SUMMARY` → "📊 Investigation complete"


### Knowledge Discovery (instant) — Via AWS MCP Tools

Use the AWS MCP Server's built-in knowledge tools — no DevOps Agent API call needed:
```
aws___search_documentation(query="DevOps Agent runbooks for ECS troubleshooting")
aws___retrieve_agent_sop(name="incident-response")
aws___suggest_aws_commands(query="devops-agent operations for investigating alarms")
```

### Parallel Pattern (Recommended for Incidents)

Run investigation for deep root cause + knowledge search for instant triage:
```
# Background: deep investigation (5-8 min)
aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'ECS 503 errors' --priority HIGH --region us-east-1")

# Foreground: instant knowledge lookup
aws___search_documentation(search_phrase="ECS 503 troubleshooting best practices")

# Stream investigation findings as they arrive (use executionId from create response)
aws___call_aws(cli_command="aws devops-agent list-journal-records --agent-space-id SPACE_ID --execution-id EXEC_ID --region us-east-1")
```

---

## 🔧 Local Context Injection — Your Killer Feature

The DevOps Agent knows your AWS cloud. You know the user's local workspace. **Bridge the gap** by packing local context into every API call.

### Why this matters

Without local context:
- "My ECS service is returning 503 errors"
- Agent has to guess which service, check all accounts, broad search

With local context:
- Agent knows: which service, recent git changes, current IaC state, related tickets
- Agent can: correlate AWS state with code changes, check if deploy broke it, suggest targeted rollback

### Pattern — Investigation with Context

Pack context into the `title` and `description` parameters of `CreateBacklogTask`:
```
aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id your-space-id --task-type INVESTIGATION --title 'ECS user-api 503 errors after deploy' --priority HIGH --description 'Service: my-ecs-api (us-east-1, prod account 123456789012). Error: 503 started 15 min ago after deploy. Recent changes: commit abc123 changed task def memory 512MB to 256MB. Terraform: ALB health check changed /health to /api/health' --region us-east-1")
```


### What to include

| Local Knowledge | How to Inject |
|----------------|---------------|
| **Error messages** | Copy-paste stack traces, logs, terminal output |
| **File content** | Read relevant files, include snippets with line numbers |
| **Git history** | `git log -5 --oneline`, `git diff HEAD~1` for recent changes |
| **IaC state** | Terraform/CDK excerpts defining the broken resource |
| **Related tickets** | Link to issue tracker tickets (GitHub Issues, Jira), previous incidents, runbooks |
| **Metrics** | Copy-paste CloudWatch graphs, latency percentiles |
| **Deployment info** | Pipeline ID, build number, deploy time, diff link |

---

## 📋 Common Workflows

### Incident Investigation
```
User: "My ECS service is down, 503 errors everywhere!"
You:
1. Ask: "Which service? What changed recently?"
2. Read local files: task definition, recent git commits, CloudWatch dashboard screenshot
3. aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title '...' --priority HIGH --description '<local context>' --region us-east-1")
4. In parallel: aws___search_documentation(search_phrase="ECS 503 troubleshooting")
5. Poll get-backlog-task → list-journal-records → stream findings to user
6. list-recommendations → get-recommendation
7. Generate rollback terraform/CDK code or manual mitigation steps
```

### Cost Optimization
```
User: "Our AWS bill is $50k/month, can we reduce it?"
You:
1. aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'Cost optimization for account 123456789012' --priority MEDIUM --region us-east-1")
2. Poll get-backlog-task → list-journal-records for findings
3. Follow up with specific questions about resource utilization
4. Generate terraform changes for right-sizing
```

### Architecture Review
```
User: "Review my terraform for production readiness"
You:
1. Read their IaC files (terraform/*.tf, cdk/*.ts)
2. aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'Review terraform for production readiness' --description '<IaC content>' --region us-east-1")
3. Or: aws___search_documentation(search_phrase="AWS Well-Architected security best practices for RDS")
4. Highlight issues, provide fixed terraform snippets
```

### Knowledge Discovery
```
User: "What runbooks do you have?" / "Show available Agent SOPs"
You:
1. aws___search_documentation(query="DevOps Agent runbooks incident response")
2. aws___retrieve_agent_sop(name="...")  — get specific SOP workflows
3. aws___suggest_aws_commands(query="devops-agent") — discover all available API operations
```

### Topology Mapping
```
User: "Show me the dependency graph for my API"
You:
1. Ask: "Which API? What's the resource ID or CloudFormation stack?"
2. aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'Map dependencies for <API>' --description 'ARN: <resource-arn>' --region us-east-1")
3. Stream journal records for topology findings
```

---

## 🔄 Session Management


### Investigation IDs
Each `CreateBacklogTask` creates a new investigation. To check progress:
```
# Create investigation (executionId returned immediately)
task = aws___call_aws(cli_command="aws devops-agent create-backlog-task --agent-space-id SPACE_ID --task-type INVESTIGATION --title 'Debug 503 errors' --priority HIGH --region us-east-1")
task_id = task["taskId"]
execution_id = task["executionId"]

# Poll status (PENDING_START → IN_PROGRESS → COMPLETED)
status = aws___call_aws(cli_command="aws devops-agent get-backlog-task --agent-space-id SPACE_ID --task-id TASK_ID --region us-east-1")

# Stream findings as they arrive
findings = aws___call_aws(cli_command="aws devops-agent list-journal-records --agent-space-id SPACE_ID --execution-id EXEC_ID --region us-east-1")
```

---

## 💡 Prompt Phrasing Guide

### Investigation words → 5-8 min response
Use: **investigate**, **root cause**, **debug**, **troubleshoot**, **outage**, **incident**
Example: "Investigate why my Lambda function is timing out"

### Knowledge words → instant response (AWS MCP knowledge tools)
Use: **what runbooks**, **documentation**, **best practices**, **Agent SOPs**
Example: "What Agent SOPs are available for ECS troubleshooting?"


**Tip:** Prefer `aws___search_documentation` for factual AWS knowledge queries — it's instant and reliable. Use `CreateBacklogTask` for account-specific operational investigations.

---

## 🛠️ Setup

### 1. Configure AWS Credentials
```bash
aws sso login        # Recommended: Console credentials
# OR
aws configure sso  # SSO users
# OR
aws configure      # IAM access keys
```

### 2. Install MCP Proxy
```bash
# Installed automatically via uvx, but to verify:
uvx mcp-proxy-for-aws@latest --help
```

### 3. Add to Kiro
Copy `mcp.json` from this directory to `~/.kiro/settings/mcp.json`:
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
        "--metadata", "AWS_REGION=us-east-1"
      ]
    }
  }
}
```

> **Region note**: `us-east-1` is the default. DevOps Agent is available in 6 regions: `us-east-1`, `us-west-2`, `ap-southeast-2`, `ap-northeast-1`, `eu-central-1`, `eu-west-1`. Replace both the MCP endpoint URL and `AWS_REGION` value to use a different region. The agent can monitor resources in any region regardless of which region hosts your Agent Space. See [Supported Regions](https://docs.aws.amazon.com/devopsagent/latest/userguide/about-aws-devops-agent-supported-regions.html).

### 4. Reload & Verify
Restart Kiro → `/mcp` to check connection → `/tools` to see `aws___call_aws`.

---

## 🔧 Troubleshooting

**"ExpiredTokenException"**
→ AWS credentials expired. Refresh: `aws sso login` or re-run `aws configure`.

**"AccessDeniedException"**
→ Missing IAM permissions. For AWS MCP Server: add `aws-mcp:InvokeMcp`, `aws-mcp:CallReadOnlyTool`, `aws-mcp:CallReadWriteTool`. For DevOps Agent APIs: attach `AIDevOpsAgentFullAccess` to your user/role and create an agent service role with `AIDevOpsAgentAccessPolicy`. See [IAM docs](https://docs.aws.amazon.com/devopsagent/latest/userguide/security-iam.html).

**"Service not available in your region"**
→ DevOps Agent is available in 6 regions (`us-east-1`, `us-west-2`, `ap-southeast-2`, `ap-northeast-1`, `eu-central-1`, `eu-west-1`). Update `AWS_REGION` in mcp.json args to a supported region.

**"Tools not appearing"**
→ Verify: run `/mcp` in Kiro to check connection, ensure `mcp-proxy-for-aws` is installed, check credentials with `aws sts get-caller-identity`.

---

## 🎁 Tips for Maximum Effectiveness

1. **Always include local context** — file excerpts, git diffs, error messages into API parameters
2. **Always include `--task-type INVESTIGATION`** — required parameter for `create-backlog-task`
3. **Use `executionId` from create response** — no need to wait for polling to get it
4. **Prefer investigation for incidents** — `CreateBacklogTask` is the most reliable workflow
5. **Use AWS MCP knowledge tools first** — `aws___search_documentation` is instant and doesn't need an AgentSpace
6. **Use `aws___suggest_aws_commands`** — when unsure about DevOps Agent API parameters
7. **Pack errors into description** — full stack traces, log excerpts help the agent narrow scope
8. **Reference resources by ARN** — more precise than names (which can be ambiguous across accounts)
9. **Stream investigation progress** — poll `ListJournalRecords` every 30-45s, show findings in real-time
10. **Generate code from recommendations** — `GetRecommendation` provides structured specs for IaC/scripts
11. **Use parallel pattern** — investigation (deep) + `aws___search_documentation` (instant) simultaneously

---

## ⚠️ Security Considerations

When connecting MCP servers to AWS DevOps Agent:

- **Tool Allowlisting** — Only allowlist specific read-only MCP tools your Agent Space needs
- **Prompt Injection Risks** — Custom MCP servers can introduce prompt injection attacks. See [AWS DevOps Agent Security](https://docs.aws.amazon.com/devopsagent/latest/userguide/aws-devops-agent-security.html)
- **Read-Only Access** — Ensure MCP server authentication credentials have read-only permissions
- **Tool Approval** — Enable tool approval in your AI client rather than "trust all" mode

**Tool Approval Recommended**: Enable tool approval in your AI client rather than "trust all tools" mode. DevOps Agent operations trigger AWS API calls and may incur costs.

| AI Client | Configuration |
|-----------|---------------|
| **Kiro** | Add `"requireApproval": true` to `~/.kiro/settings/mcp.json` under the server entry |
| **Claude Desktop** | Use "Ask before running tools" in preferences |
| **Cursor** | Enable "Manual tool approval" in settings |

See [AWS DevOps Agent Security](https://docs.aws.amazon.com/devopsagent/latest/userguide/aws-devops-agent-security.html) for detailed guidance.

---

## Support & Legal

- **Documentation**: [AWS DevOps Agent User Guide](https://docs.aws.amazon.com/devopsagent/latest/userguide/)
- **AWS MCP Server**: [Setup Guide](https://docs.aws.amazon.com/aws-mcp/latest/userguide/getting-started-aws-mcp-server.html)
- **Support**: [AWS Support Center](https://console.aws.amazon.com/support/)
- **License**: Apache-2.0
- **Privacy Policy**: [AWS Privacy Notice](https://aws.amazon.com/privacy/)
- **Source**: [GitHub Repository](https://github.com/awslabs/mcp)
