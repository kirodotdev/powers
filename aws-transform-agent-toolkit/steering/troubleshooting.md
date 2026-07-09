---
inclusion: auto
name: troubleshooting
description: "Field-tested troubleshooting guide for common AWS Transform agent issues"
---

# AWS Transform Agent Troubleshooting Guide

## Quick Reference

| # | Issue | Symptom | Fix |
|---|-------|---------|-----|
| 1 | Wrong agent type registered | Shows as ORCHESTRATOR instead of SUB_AGENT | Manual 3-step registration via MCP |
| 2 | MCP credentials not inherited | Auth errors in MCP tools | Add creds to `~/.kiro/settings/mcp.json` env block |
| 3 | MCP server slow startup | `MCP error -32001: Request timed out` | Retry 2-3 times after config changes |
| 4 | Relative agent_path | `FileNotFoundError` in `build_agent_image` | Use absolute path |
| 5 | Workspace MCP overrides power | Power servers disabled | Only use `~/.kiro/settings/mcp.json` for power servers |
| 6 | Python version mismatch | SDK install fails | Use `/opt/homebrew/bin/python3.11 -m venv .venv` |
| 7 | Publish config gaps | Agent missing resiliency/schemas | Include all required fields (see agent-registration.md) |
| 8 | agentCard field | A2A Agent Card — required by PublishAgentVersion | Empty `{}` rejected by boto3 — see Minimal agentCard Example in agent-registration.md |
| 9 | Large publish payload | "tool does not exist" error | Publish minimal config first, add fields in later versions |
| 10 | Orchestrator not in webapp | Agent registered but not visible | Set `jobOrchestrator: true` + `jobOrchestratorMetadata` at registration |
| 11 | customerConfigurationRequired trade-off | Can't have compute config + dependencies | Choose based on priority (see details) |
| 12 | Bare model ID fails | `ValidationException: Invocation of model ID...` | Use `us.` prefix (cross-region inference profile) |
| 13 | agent_factory signature | `takes 1 positional argument but 2 were given` | Add `storage_dir=None` param |
| 14 | publish_agent_version includes compute | Rejected for `customerConfigurationRequired: true` | Use `publish-agent-version` from `agent-builder-mcp-aws-transform` |
| 15 | Stale registration after redeploy | New runtime gets zero invocations | Publish new version or re-register with `customerConfigurationRequired: false` |
| 16 | computeConfiguration schema change | Flat `agentRuntimeArn` rejected | Use nested `provisionedComputeConfiguration.agentCoreConfiguration.runtimeArn` |
| 17 | Expired STS tokens | `get_caller_identity()` fails | Use `TARGET_ACCOUNT_ID` from `.env` |
| 18 | Symlinked SDK dir | Build fails or SDK missing | `cp -r` not `ln -s` |
| 19 | Wrong role in agent registration | Chat never enables, zero invocations | Use `AWSTransformAgentInvokeRole` not `AgentCoreExecutionRole` |
| 20 | StatelessAgentRuntimeServer timeout | HITL polling killed after 28s | Use `AgentRuntimeServer` with `delayed_timeout=3600` |
| 21 | Container reuse stale instance | Subagent COMPLETED without doing work | Re-run job (AWS Transform bug) |
| 22 | HITL description too long | display_report fails | Truncate to < 1024 chars |
| 23 | Post-COMPLETED operations fail | `TerminalResourceException` after second message | Design one message per subagent instance |
| 24 | SendMessage -32603 timeout | Orchestrator thinks subagent failed | Poll `get_agent_instance` until COMPLETED |
| 25 | PutJobPlan stepId mismatch | 404 on UpdateJobPlanStep | Call `list_job_plan_steps()` to get real stepIds |
| 26 | JobManager auto-transitions status | Job goes EXECUTING→PLANNING→PLANNED→EXECUTING | Harmless; SDK auto-transitions during init |
| 27 | ATX_CHAT messaging undocumented | Chat messages don't appear | Use A2A format with `extensions` + `userSelection: "jobCreator"` (see orchestrator-patterns.md) |
| 28 | Background execution undocumented | Orchestrator exceeds delayed_timeout | Spawn daemon thread from LLM tool |
| 29 | S3 connector auth denied | `Partner not authorized to access this type of connector` | Fall back to direct S3 tools; request connector access from AWS Transform team |
| 30 | Stale SDK install or `uvx` cache | `Models OK` check raises `UnknownServiceError`, MCP server reports placeholder v0.0.1, or `pip` reports `Package(s) not found` | Re-run upgrade install + `aws configure add-model`; for the MCP server, bust the `uvx` cache once |

## Detailed Issues

### 1. Agent Registered as Wrong Type

**Symptom:** `deploy_agent_full_pipeline` registers as ORCHESTRATOR_AGENT instead of SUB_AGENT, sets `customerConfigurationRequired: false`.
**Fix:** Split into 3 steps: (1) `build_agent_image` + `deploy_agent_to_agentcore`, (2) `register_agent` MCP tool with correct metadata, (3) `publish_agent_version` MCP tool.
**Gotcha:** `agentCard`, `inputPayloadSchema`, `outputPayloadSchema` cannot be empty `{}` — must contain at least one property.

### 2. MCP Server Credentials Not Inherited

**Symptom:** Auth errors from `agent-builder-mcp-aws-transform` MCP server.
**Fix:** Add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` to the `env` block in `~/.kiro/settings/mcp.json`. Tokens expire — update when credentials refresh.

### 3. MCP Server Slow Startup

**Symptom:** `MCP error -32001: Request timed out` on connect.
**Fix:** Retry 2-3 times. The MCP server may be slower on first connect.

### 4. Relative Path in deploy_agent_full_pipeline

**Symptom:** `FileNotFoundError` when using relative `agent_path`.
**Fix:** Use absolute path: `/Users/username/projects/my-agent/`.

### 5. Workspace MCP Overrides Power Config

**Symptom:** Power servers disabled after creating `.kiro/settings/mcp.json` in workspace.
**Fix:** Don't duplicate power server entries in workspace-level MCP config. Use only `~/.kiro/settings/mcp.json`.

### 6. SDK Requires Python 3.11+

**Symptom:** `agent-builder-sdk-aws-transform` fails to install.
**Fix:** Create venv with correct Python: `/opt/homebrew/bin/python3.11 -m venv .venv`.

### 7. Publish Configuration Gaps

**Symptom:** Agent missing `objectiveNegotiationPrompt`, `agentResiliencyConfiguration`, proper schemas.
**Fix:** Include all required publish configuration fields. Add `partnerControllerRetryWindowMinutes: 6`, `recoveryWaitTimeSeconds: 60`. See `agent-registration.md` for the complete configuration structure.

### 8. agentCard Field

Forward-looking field for A2A agent discovery. Required by `PublishAgentVersion` — boto3 client-side validation rejects empty `{}`. Must contain at least the required fields (id, name, description, version, capabilities with extensions). See the Minimal agentCard Example in `agent-registration.md`.

### 9. Large Publish Payload Fails

**Symptom:** `publish_agent_version` via MCP returns "tool does not exist".
**Fix:** Publish v1.0.0 with minimal config, add fields in v1.0.1, v1.0.2, etc.

### 10. Orchestrator Not Visible in Webapp

**Symptom:** Registered orchestrator doesn't appear in workspace agent list.
**Fix:** Must set `jobOrchestrator: true` AND `jobOrchestratorMetadata` (chatUILabel, chatAgentIdentifier, a2aSupported) at registration time. These fields cannot be updated after registration.

### 11. customerConfigurationRequired Trade-Off

`true` blocks `computeConfiguration` in publish but allows `customerConfiguredAgentDependencies`. `false` allows compute config but blocks dependencies. See `agent-registration.md` for the full trade-off matrix.

### 12. Cross-Region Inference Profile Required

**Symptom:** `ValidationException: Invocation of model ID ... with on-demand throughput isn't supported`.
**Fix:** Use `us.anthropic.claude-3-7-sonnet-20250219-v1:0` (cross-region inference profile).

### 13. agent_factory Signature Mismatch

**Symptom:** `agent_factory() takes 1 positional argument but 2 were given`.
**Fix:** `def agent_factory(mcp_client, storage_dir=None):` — server now passes 2 args.

### 14. publish_agent_version Includes Compute for customerConfigurationRequired

**Symptom:** `publish_agent_version` always includes `computeConfiguration`.
**Fix:** Use `publish_agent_version` MCP tool with appropriate overrides, manually omitting `computeConfiguration`.

### 15. Stale Registration After Redeploy

**Symptom:** New runtime is READY but gets zero invocations; old runtime still receives traffic.
**Fix:** Publish a new agent version pointing to the new runtime ARN, or re-register under a new name with `customerConfigurationRequired: false` to embed runtime ARN directly.

### 16. computeConfiguration Schema Change

**Symptom:** Flat `agentRuntimeArn` rejected.
**Fix:** Use nested structure: `computeConfiguration.provisionedComputeConfiguration.agentCoreConfiguration.runtimeArn`.

### 17. Expired STS Tokens in Scripts

**Symptom:** `boto3.client("sts").get_caller_identity()` fails.
**Fix:** Read account ID from environment: `os.environ.get("TARGET_ACCOUNT_ID")`. Set in `.env` file.

### 18. Symlinked SDK Directory

**Symptom:** Docker/finch build fails — build context doesn't follow symlinks.
**Fix:** Copy the SDK into the project directory (don't symlink): `pip install agent-builder-sdk-aws-transform --target <your-project>/sdk/`.

### 19. Wrong Role in Agent Registration

**Symptom:** Chat input never enables, zero invocations, no error.
**Cause:** Used `AgentCoreExecutionRole` instead of `AWSTransformAgentInvokeRole` in the `atxAccessRoleArn` field during registration.
**Fix:** Use `AWSTransformAgentInvokeRole` (trusted by `prod.us-east-1.compute.elastic-gumby.aws.internal`).

### 20. StatelessAgentRuntimeServer 28s Timeout

**Symptom:** Subagent processing killed after 28 seconds; HITL polling never completes.
**Cause:** `StatelessAgentRuntimeServer` uses `asyncio.timeout(28)` on entire `process_message`.
**Fix:** Use `AgentRuntimeServer` with `delayed_timeout=3600`. Must also override `process_message_async` to set COMPLETED/FAILED. See `subagent-patterns.md` for the override pattern.

### 21. Container Reuse Stale Instance (AWS Transform Bug)

**Symptom:** `TerminalResourceException: Agent instance status is not valid: COMPLETED` on first invocation.
**Cause:** AWS Transform reuses container from previous job without resetting instance state.
**Fix:** Re-run the job. Service-level issue — no code workaround.

### 22. HITL Description Exceeds 1024 Characters

**Symptom:** `display_report` HITL task creation fails.
**Fix:** Truncate: `description = description[:1000] + "\n\n[Truncated]"` before passing.

### 23. Post-COMPLETED Operations Fail

**Symptom:** After COMPLETED, all API calls on that instance return `TerminalResourceException`.
**Fix:** Subagents are single-use. Design orchestrators to send all work in a single message per invocation.

### 24. SendMessage -32603 Internal Timeout

**Symptom:** SendMessage returns `error.code: "-32603"` with HTTP 200 after ~25s.
**Cause:** Internal API timeout. Subagent is still processing.
**Fix:** Fire-and-forget pattern — send message, immediately poll `get_agent_instance` until COMPLETED. See `orchestrator-patterns.md` for the polling pattern.

### 25. PutJobPlan Assigns Its Own Step IDs

**Symptom:** `ResourceNotFoundException` when calling `UpdateJobPlanStep` with `stepLabel`.
**Fix:** After `put_job_plan`, call `list_job_plan_steps()` and build `stepLabel → stepId` mapping.

### 26. JobManager Auto-Transitions Status

**Symptom:** Job status goes EXECUTING→PLANNING→PLANNED→EXECUTING during startup.
**Cause:** SDK's `JobManager` auto-transitions to EXECUTING during init. Your tool then sets PLANNING.
**Impact:** Harmless. Status settles to correct value.

### 27. ATX_CHAT Messaging Format Undocumented

**Symptom:** Chat messages don't appear in webapp.
**Fix:** Use the exact A2A format with `extensions` containing `{"userSelection": "jobCreator"}` metadata. See `orchestrator-patterns.md` for the working code pattern.

### 28. Background Thread Execution Pattern

**Symptom:** Orchestrator exceeds `delayed_timeout` during multi-step execution.
**Fix:** Spawn a `threading.Thread(daemon=True)` from the LLM tool, return immediately. The thread handles step execution, polling, status updates, and ATX_CHAT progress. See `orchestrator-patterns.md` for the background execution architecture.

### 29. S3 Connector Authorization Denied

**Symptom:** `ValidationException: Partner 'X' is not authorized to access this type of connector`.
**Cause:** Publisher not authorized for S3 connector type at AWS Transform level. `list_s3_connectors()` succeeds but data plane calls fail.
**Fix:** Fall back to direct S3 tools (`download_s3_file`/`upload_s3_file`). Contact AWS Transform team to request S3 connector authorization. Always register both connector and direct S3 tools.

### 30. Stale SDK Install or `uvx` Cache

**Symptom:** Any of the following:
- The `Models OK` verification command in onboarding raises `botocore.exceptions.UnknownServiceError: Unknown service: 'transformagenticservice'` (or `'atxagentregistryexternal'`).
- `python3 -c "from importlib.metadata import version; print(version('agent-builder-sdk-aws-transform'))"` prints `0.0.1`.
- The MCP server reports the placeholder version, or `pip` reports `Package(s) not found: agent-builder-mcp-aws-transform`.

**Cause:** The pinned floors and `--upgrade` flag in onboarding prevent this on a clean machine. You'll only hit it if the SDK was installed before May 13 (when the v0.0.1 name-reservation placeholder was the only release on PyPI), or if a previous `uvx` invocation cached an old resolution.

**Fix:**

1. Re-run the upgrade install from `POWER.md` Step 2:
   ```bash
   pip install --upgrade \
       'agent-builder-sdk-aws-transform>=1.0.0' \
       'agent-builder-agentic-mcp-aws-transform>=1.0.0' \
       'agent-builder-types-aws-transform>=1.0.0' \
       'agent-builder-mcp-client-aws-transform>=1.0.0'
   ```
2. Re-run `aws configure add-model` for both services. The model JSONs only exist in the real release, so registration done against v0.0.1 was a no-op.
3. Re-run the `Models OK` boto3 sanity check.
4. For the MCP server, evict the cached resolution and restart Kiro:
   ```bash
   uv cache clean --force agent-builder-mcp-aws-transform
   ```
   Then quit and relaunch Kiro — the new `mcp.json` args trigger a fresh `uvx` resolution on startup.

   *Optional:* If you'd prefer not to use `--force`, quit Kiro first, then run `uv cache clean agent-builder-mcp-aws-transform` (without `--force`).

**Note:** `uvx` runs the MCP server in its own environment, but boto3 in that environment still reads service models from `~/.aws/models/`. Host-level `aws configure add-model` is sufficient — there is no need to register models inside the `uvx` environment.

## Debugging Techniques

### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-name>-DEFAULT --follow --region us-east-1

# Filter for errors
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-name>-DEFAULT --filter-pattern "ERROR"
```

Also use `fetch_logs` and `list_log_streams` MCP tools from `agent-builder-mcp-aws-transform`.

### Local Docker Testing

```bash
docker build -t my-agent .
docker run -p 8080:8080 \
  -e WORKSPACE_ID=test -e JOB_ID=test -e AGENT_INSTANCE_ID=test \
  -e LOG_LEVEL=DEBUG my-agent
curl http://localhost:8080/ping
```
