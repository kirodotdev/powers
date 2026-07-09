---
inclusion: auto
name: workflow-integration
description: "Guidelines for adding agents to an existing workflow from the AWS Transform console"
---

# Adding an Agent to an Existing Workflow

**IMPORTANT**: Do NOT look up the requested agent first. Understand the current workflow architecture before anything else.

## Step 1: Analyze the Current Codebase

### Check for architecture documents first

Search for `**/architecture*.md`, `**/design*.md`, `**/workflow*.md`, `**/ARCHITECTURE*`, `**/README.md`, `**/.kiro/specs/*`, `**/.kiro/steering/*`, `**/docs/agents*`. Look for: which agents exist, their roles, invocation flow, decision logic, and message formats.

### If no architecture document exists

Analyze the codebase:

1. **Find agents**: Search for classes extending `AsyncBaseOrchestrator`, `BaseOrchestrator`, `AsyncBaseSubagent`, or `BaseSubagent`. Also check for `AgentRuntimeServer` / `StatelessAgentRuntimeServer` setup.
2. **Read system prompts**: Look for `system_prompt=` in constructors, `get_prompt_with_name()` references, and prompt strings in config files.
3. **Find invocation patterns**: `InvokeAgent` calls, `agentId` references, A2A messages, tool definitions that invoke agents.
4. **Map the workflow**: Which agents exist, how they connect, invocation conditions, data passed between them. Don't assume a single-orchestrator-with-subagents pattern — there may be multiple orchestrators, chained agents, peer agents, or other topologies.

## Step 2: Confirm and Discuss with the User

1. **Confirm your understanding**: Share your mental model of the current workflow. Ask the user to confirm or correct it before proceeding.
2. **Suggest integration points**: The new agent could be any type. Consider: invoked by an existing agent, replacing an existing agent, an additional workflow step, a new orchestrator coordinating existing agents, or a peer agent.
3. **Ask the user to confirm**: Where it goes, when it's invoked, what data it needs.

## Step 3: Integrate the Agent

### Update system prompts

Add the new agent to the relevant agent's system prompt: its name/ID, when to invoke it, and what data to send. If it fits into a sequence with existing agents, update the workflow steps. Match the existing prompt style.

### Add invocation code (if applicable)

If agents use explicit code to invoke other agents, add the new invocation following the existing pattern in the codebase.

### Update architecture document (if it exists)

Add the agent to the agent list, update the workflow diagram/flow, and document invocation conditions and message format.

## Step 4: Verify

1. **Prompt coherence**: No contradictions or ambiguous invocation conditions.
2. **Code consistency**: New invocation code follows existing patterns.
3. **Document accuracy**: Architecture doc matches actual code changes.

## Guidelines

- Only modify what's necessary.
- Match existing style in prompts and code.
- Always specify: agent name/ID, when to invoke, what to send.
- Ask the user rather than guessing when unclear.
