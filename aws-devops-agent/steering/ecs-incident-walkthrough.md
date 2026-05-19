---
inclusion: auto
name: ecs-incident-walkthrough
description: Worked example of the full ECS incident workflow — chat triage, deep investigation with streamed progress, mitigation plan generation, and local IaC fix. Use when investigating ECS 503 errors, service outages, or deployment failures.
---
# Walkthrough: ECS 503 incident — chat triage → investigation → mitigation

This is a worked example showing the full power in action: instant chat triage, deep investigation with streamed progress, empty-recommendations recovery via `UpdateBacklogTask PENDING_START`, and local IaC fix generation.

## Scenario

Your `checkout-service` (ECS Fargate behind ALB) started returning 503s at 14:32 UTC. You're in a Kiro workspace with the CDK stack open.

## Step 1 — Gather local context

Before calling any DevOps Agent API, read what you already know locally:

```
git log --oneline -10
# abc1234 fix: increase timeout (2h ago)
# def5678 feat: add /api/v2 endpoint (4h ago)

cat lib/checkout-stack.ts   # CDK: ECS Fargate, 256MB memory, ALB target group
cat package.json            # name: checkout-service
```

## Step 2 — Pick the AgentSpace

```
aws___call_aws(cli_command="aws devops-agent list-agent-spaces --region us-east-1")
→ [{ "agentSpaceId": "as-abc123", "name": "production", ... }]
```

One space — use it.

## Step 3 — Instant chat triage (2-10s)

```
aws___call_aws(cli_command="aws devops-agent create-chat --agent-space-id as-abc123 --user-id jdoe --user-type IAM --region us-east-1")
→ { "executionId": "exec-chat-001" }

> **Note:** If `create-chat` fails with "User identity could not be resolved", your account may lack Operator App registration. Skip to Step 4 (investigation) — investigations don't require chat identity.
```

```python
aws___run_script(code="""
response = await call_boto3(
    service_name='devops-agent',
    operation_name='SendMessage',
    region_name='us-east-1',
    params={
        'agentSpaceId': 'as-abc123',
        'executionId': 'exec-chat-001',
        'userId': 'jdoe',
        'content': '''[Local Context]
Service: checkout-service (ECS Fargate, 256MB, ALB)
Last deploy: commit abc1234 — 2h ago (increased timeout)
CDK Stack: lib/checkout-stack.ts

[Question]
Our checkout-service started returning 503s at 14:32 UTC. Quick triage — what could cause this?'''
    }
)

full_response = []
current_block_type = None
for event in response['events']:
    if 'contentBlockStart' in event:
        current_block_type = event['contentBlockStart'].get('type')
    elif 'contentBlockDelta' in event:
        if current_block_type in (None, 'text'):
            delta = event['contentBlockDelta'].get('delta', {})
            if 'textDelta' in delta:
                full_response.append(delta['textDelta']['text'])
    elif 'contentBlockStop' in event:
        current_block_type = None

result = ''.join(full_response)
result
""")
```

> **Agent response** (5s): "Based on the 256MB memory configuration and the recent deploy, this could be an OOM issue. The timeout increase in abc1234 may have increased memory pressure. I'd recommend investigating with a deep analysis to check CloudWatch metrics and X-Ray traces."

Show this to the user immediately. The agent is suggesting deeper analysis — escalate.

## Step 4 — Start deep investigation (5-8 min)

```
aws___call_aws(cli_command="aws devops-agent create-backlog-task \
  --agent-space-id as-abc123 \
  --task-type INVESTIGATION \
  --title 'ECS 503 errors on checkout-service' \
  --priority HIGH \
  --description '[Local Context] Service: checkout-service (ECS Fargate, 256MB, ALB). Last deploy: commit abc1234 (increased timeout) 2h ago. CDK: lib/checkout-stack.ts. Error: 503s starting 14:32 UTC. Chat triage suggested OOM. [Question] Root cause of 503 errors and remediation.' \
  --region us-east-1")
→ { "taskId": "task-inv-001" }
```

Tell the user: "Starting deep investigation — this takes 5-8 minutes. I'll stream findings as they come in."

## Step 5 — Stream progress

Poll every 30-45 seconds:

```
aws___call_aws(cli_command="aws devops-agent get-backlog-task --agent-space-id as-abc123 --task-id task-inv-001 --region us-east-1")
→ { "taskStatus": "IN_PROGRESS", "executionId": "exe-ops1-abc123..." }

> **Important:** Investigation executionIds use `exe-ops1-*` format. Use `aws___call_aws` CLI (not `call_boto3`) for all investigation operations — `list-journal-records`, `get-backlog-task`, `list-recommendations`.
```

Fetch journal records with pagination:

```
aws___call_aws(cli_command="aws devops-agent list-journal-records --agent-space-id as-abc123 --execution-id exec-inv-001 --page-size 50 --region us-east-1")
```

Update the user after every poll:

> 📋 **30s:** Planning investigation — checking CloudWatch metrics, ECS task health, ALB target group.

> 🔍 **1:30:** Querying CloudWatch — error rate spiked to 23% at 14:32 UTC. Checking memory utilization.

> 🔬 **3:00:** Analyzing ECS task metrics — memory utilization hit 100% on 3/4 tasks starting at 14:30.

> 🎯 **5:00:** Root cause identified — task definition memory was reduced from 512MB to 256MB in a previous deploy. The timeout increase in abc1234 caused longer-lived connections that pushed memory over the limit, triggering OOM kills.

> 📊 **6:00:** Investigation complete.

## Step 6 — Fetch recommendations

```
aws___call_aws(cli_command="aws devops-agent list-recommendations --agent-space-id as-abc123 --task-id task-inv-001 --region us-east-1")
→ { "recommendations": [] }   # Empty!
```

Empty recommendations — trigger mitigation:

```
aws___call_aws(cli_command="aws devops-agent update-backlog-task --agent-space-id as-abc123 --task-id task-inv-001 --task-status PENDING_START --region us-east-1")
```

Re-poll `get-backlog-task` every 30-45s until `COMPLETED` again (2-5 min).

```
aws___call_aws(cli_command="aws devops-agent list-recommendations --agent-space-id as-abc123 --task-id task-inv-001 --region us-east-1")
→ { "recommendations": [{ "recommendationId": "rec-001", "title": "Increase ECS task memory to 512MB", ... }] }

aws___call_aws(cli_command="aws devops-agent get-recommendation --agent-space-id as-abc123 --recommendation-id rec-001 --region us-east-1")
→ { "specification": "Update task definition memory from 256 to 512..." }
```

## Step 7 — Generate local fix (require user approval)

Based on the recommendation, generate the CDK fix:

```diff
--- a/lib/checkout-stack.ts
+++ b/lib/checkout-stack.ts
@@ -15,7 +15,7 @@ export class CheckoutStack extends cdk.Stack {
     const taskDef = new ecs.FargateTaskDefinition(this, 'TaskDef', {
-      memoryLimitMiB: 256,
+      memoryLimitMiB: 512,
       cpu: 256,
     });
```

Show the diff. **Do not apply it.** Say: "Here's the recommended fix — increase memory from 256MB to 512MB. Want me to apply this change?"

Wait for explicit user approval before writing the file.
