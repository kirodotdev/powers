---
name: ecs-incident-walkthrough
description: Worked example of the full ECS incident workflow — chat triage, deep investigation with streamed progress, mitigation retrieval, and local IaC fix. Use when investigating ECS 503 errors, service outages, or deployment failures.
---

# Walkthrough: ECS 503 Incident — Chat Triage → Investigation → Mitigation

Full worked example showing: instant chat triage, deep investigation with progress streaming, and local fix generation.

## Scenario

Your `checkout-service` (ECS Fargate behind ALB) started returning 503s at 14:32 UTC. You're in a Kiro workspace with the CDK stack open.

---

## Step 1 — Gather Local Context

Before calling any tool, read what you already know locally:

```bash
git log --oneline -10
# abc1234 fix: increase timeout (2h ago)
# def5678 feat: add /api/v2 endpoint (4h ago)

cat lib/checkout-stack.ts   # CDK: ECS Fargate, 256MB memory, ALB target group
cat package.json            # name: checkout-service
```

---

## Step 2 — Instant Chat Triage (2-10s)

Use the `chat` tool for immediate analysis:

```
chat(message="""[Local Context]
Service: checkout-service (ECS Fargate, 256MB, ALB)
Last deploy: commit abc1234 — 2h ago (increased timeout)
CDK Stack: lib/checkout-stack.ts

[Question]
Our checkout-service started returning 503s at 14:32 UTC. Quick triage — what could cause this?""")
```

→ Response (5s): "Based on the 256MB memory configuration and the recent deploy, this could be an OOM issue. The timeout increase in abc1234 may have increased memory pressure. I'd recommend a deep investigation to check CloudWatch metrics and X-Ray traces."

Show this to the user immediately. The agent suggests deeper analysis — escalate.

---

## Step 3 — Start Deep Investigation (5-8 min)

```
investigate(title="ECS 503 errors on checkout-service — OOM suspected after timeout increase deploy", priority="HIGH")
```

→ `{ "taskId": "task-inv-001", "executionId": "exe-001", "status": "investigation_started" }`

Tell the user: "🔬 Starting deep investigation — this takes 5-8 minutes. I'll stream findings as they come in."

---

## Step 4 — Stream Progress

Poll every 30-45 seconds:

```
get_task(task_id="task-inv-001")
→ { "taskStatus": "IN_PROGRESS", "executionId": "exe-001" }
```

Fetch findings:

```
list_journal_records(execution_id="exe-001")
```

Update the user after every poll:

> 📋 **30s:** Planning investigation — checking CloudWatch metrics, ECS task health, ALB target group.

> 🔍 **1:30:** Querying CloudWatch — error rate spiked to 23% at 14:32 UTC. Checking memory utilization.

> 🔬 **3:00:** Analyzing ECS task metrics — memory utilization hit 100% on 3/4 tasks starting at 14:30.

> 🎯 **5:00:** Root cause identified — task memory at 256MB is insufficient after timeout increase caused longer-lived connections that pushed memory over the limit, triggering OOM kills.

> 📊 **6:00:** Investigation complete.

---

## Step 5 — Get Mitigations

```
list_recommendations(task_id="task-inv-001")
→ { "recommendations": [{ "recommendationId": "rec-001", "title": "Increase ECS task memory to 512MB" }] }

get_recommendation(recommendation_id="rec-001")
→ { "specification": "Update task definition memory from 256 to 512..." }
```

---

## Step 6 — Generate Local Fix (require user approval)

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

---

## Fallback Path

If the remote server is unreachable at any step, switch to `aws-mcp`:

- **Step 2 fallback**: `aws___call_aws("aws devops-agent create-chat ...")` + `aws___run_script` with `call_boto3(SendMessage)`
- **Step 3 fallback**: `aws___call_aws("aws devops-agent create-backlog-task --task-type INVESTIGATION ...")`
- **Steps 4-5 fallback**: `aws___call_aws("aws devops-agent get-backlog-task ...")` + `aws___call_aws("aws devops-agent list-journal-records ...")`

See `steering/steering.md` for full fallback code patterns.
