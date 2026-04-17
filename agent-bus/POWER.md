---
name: "agent-bus"
displayName: "Agent Bus — Multi-Agent Collaboration"
description: "Inter-agent message bus enabling multiple Kiro sessions to discover each other, exchange messages, share findings, and coordinate work via filesystem-backed MCP tools"
keywords: ["agent", "message bus", "multi-agent", "collaboration", "signal", "ipc", "cmux", "parallel", "oncall", "coordination"]
author: "webzane"
---

# Agent Bus — Multi-Agent Collaboration

## Overview

Agent Bus enables multiple Kiro agent sessions to work together. Whether you're running parallel oncall investigations, splitting a large refactor across agents, or coordinating research and implementation — Agent Bus provides the communication layer.

**Key capabilities:**
- **Discovery** — Find other active agent sessions in your workspace
- **Messaging** — Send messages between agents (findings, questions, instructions)
- **Signals** — Coordinate with named signals (e.g., "investigation-complete", "ready-to-merge")
- **Patterns** — Hub-and-spoke coordination, parallel investigation, pipeline workflows

**Transport:** All state is filesystem-based at `/tmp/kiro-agent-bus/`, making it inspectable, debuggable, and requiring no daemon process.

## Available Steering Files

This power has the following steering files:

- **workflows** — Cooperation patterns: oncall triage, parallel development, code review pipeline
- **cmux-integration** — Using Agent Bus with cmux terminal multiplexer for multi-pane agent orchestration

## Available MCP Servers

### agent-bus

**Package:** `kiro-power-agent-bus` (local Node.js MCP server)
**Connection:** Local stdio MCP server

**Tools:**

1. **agent_post_message** — Post a message to another agent's inbox
   - Required: `from` (string) — Sender agent ID
   - Required: `to` (string) — Recipient agent ID
   - Required: `body` (string) — Message content
   - Returns: Delivery confirmation with file path

2. **agent_read_messages** — Read messages from an agent's inbox
   - Required: `agent_id` (string) — Agent whose inbox to read
   - Optional: `from` (string) — Filter by sender
   - Optional: `clear` (boolean) — Clear messages after reading (default: false)
   - Returns: Array of messages with timestamps

3. **agent_signal** — Set a named signal that other agents can wait on
   - Required: `name` (string) — Signal name
   - Optional: `payload` (string) — Data attached to the signal
   - Returns: Confirmation

4. **agent_wait_signal** — Check if a named signal has been set
   - Required: `name` (string) — Signal name to check
   - Optional: `timeout_ms` (number) — Max wait time in ms (default: 0, non-blocking)
   - Returns: Signal data if found, or not-found status

5. **agent_list_agents** — List all agents registered on the bus
   - Returns: Array of registered agents with timestamps

## Tool Usage Examples

### Registering and Discovering Agents

When an agent starts working on a task, it should post a message to register its role:

```javascript
// Agent registers itself by posting to a well-known "registry" inbox
agent_post_message({
  from: "investigator-eu-west-1",
  to: "registry",
  body: "Investigating V2147427488 - ComplianceChecker DLQ in eu-west-1"
})

// Coordinator checks who's working
agent_read_messages({
  agent_id: "registry",
  clear: false
})
```

### Sharing Findings Between Agents

```javascript
// Investigator shares root cause
agent_post_message({
  from: "investigator-eu-west-1",
  to: "coordinator",
  body: "ROOT CAUSE: Firewalls not in READY state. 165 messages in DLQ. Blocker: need KMS perms on redrive role. Need 2PR from secondary oncall (charcyh)."
})

// Coordinator reads findings from all investigators
agent_read_messages({
  agent_id: "coordinator",
  clear: false
})
```

### Coordinating with Signals

```javascript
// Investigator signals completion
agent_signal({
  name: "investigation-V2147427488-complete",
  payload: "Root cause identified. DLQ redrive blocked on KMS perms."
})

// Coordinator checks if investigation is done
agent_wait_signal({
  name: "investigation-V2147427488-complete"
})
// Returns: { found: true, signal: { name: "...", payload: "...", timestamp: ... } }
```

### Preventing Duplicate Work

```javascript
// Before starting work, check if someone else claimed it
agent_read_messages({ agent_id: "claims", clear: false })
// If no claim exists, claim it
agent_post_message({
  from: "agent-3",
  to: "claims",
  body: "CLAIMED: V2145073654 - Wafv2 DLQ purge"
})
```

## Combining Tools (Workflows)

### Workflow 1: Parallel Oncall Investigation

A coordinator agent triages sev-2 tickets and delegates to investigators:

```javascript
// Step 1: Coordinator posts assignments
agent_post_message({
  from: "coordinator",
  to: "investigator-1",
  body: "Investigate V2147427488 - eu-west-1 ComplianceChecker DLQ. Read runbook at https://w.amazon.com/..."
})
agent_post_message({
  from: "coordinator",
  to: "investigator-2",
  body: "Investigate V2145073654 - us-east-1 Wafv2 DLQ. Check if purge was approved by charcyh."
})

// Step 2: Investigators read their assignments
agent_read_messages({ agent_id: "investigator-1", clear: true })

// Step 3: Investigators post findings
agent_post_message({
  from: "investigator-1",
  to: "coordinator",
  body: "FINDINGS: KMS perms needed. Consensus review a9a3091d already approved by abbishek. Secondary oncall is charcyh."
})

// Step 4: Investigators signal completion
agent_signal({ name: "inv-1-done", payload: "V2147427488 investigated" })

// Step 5: Coordinator collects all findings
agent_read_messages({ agent_id: "coordinator", clear: false })
agent_wait_signal({ name: "inv-1-done" })
agent_wait_signal({ name: "inv-2-done" })
```

### Workflow 2: Research → Implement Pipeline

```javascript
// Researcher shares findings
agent_post_message({
  from: "researcher",
  to: "implementer",
  body: "RFC complete at thoughts/shared/research/rfc.md. Key extension points: SessionManager (session_manager.rs), SubagentTool (subagent_tool.rs), BuiltInToolName enum."
})
agent_signal({ name: "research-complete" })

// Implementer waits for research, then reads findings
agent_wait_signal({ name: "research-complete" })
agent_read_messages({ agent_id: "implementer", clear: true })
// Now implements based on research findings
```

### Workflow 3: Code Review Coordination

```javascript
// Author signals PR is ready
agent_signal({ name: "pr-ready", payload: "CR-123456 - cooperation module" })

// Reviewer picks it up
agent_wait_signal({ name: "pr-ready" })
// Reviews code...
agent_post_message({
  from: "reviewer",
  to: "author",
  body: "REVIEW: 2 blocking issues. 1) Missing error handling in post_message. 2) Race condition in signal check."
})
agent_signal({ name: "review-complete" })
```

## Architecture

```
/tmp/kiro-agent-bus/
├── agents/           # Agent registration (one file per agent)
│   ├── coordinator.json
│   ├── investigator-1.json
│   └── investigator-2.json
├── messages/         # Per-agent inbox directories
│   ├── coordinator/
│   │   ├── 1710000001000-investigator-1.json
│   │   └── 1710000002000-investigator-2.json
│   ├── investigator-1/
│   │   └── 1710000000000-coordinator.json
│   └── registry/     # Well-known inbox for discovery
│       └── ...
└── signals/          # Named signal files
    ├── inv-1-done.json
    └── research-complete.json
```

## Best Practices

### ✅ Do:
- **Use descriptive agent IDs** — `investigator-eu-west-1` not `agent-1`
- **Include context in messages** — ticket IDs, file paths, account numbers
- **Signal completion** — always signal when a task is done
- **Claim work before starting** — prevent duplicate effort
- **Clear messages after processing** — keep inboxes clean
- **Use the registry pattern** — post to `registry` inbox for discovery

### ❌ Don't:
- **Don't poll in tight loops** — use `timeout_ms` on `agent_wait_signal`
- **Don't send huge payloads** — reference file paths instead of inline content
- **Don't forget to register** — other agents can't find you if you don't
- **Don't rely on message ordering across agents** — timestamps may differ slightly

## Troubleshooting

### Messages not appearing
**Cause:** Recipient agent ID doesn't match
**Solution:** Check `/tmp/kiro-agent-bus/messages/` for the exact inbox name

### Stale state from previous session
**Cause:** Old messages/signals from a previous run
**Solution:** Delete `/tmp/kiro-agent-bus/` to reset: `rm -rf /tmp/kiro-agent-bus`

### Signal never found
**Cause:** Signal name mismatch or signal not yet emitted
**Solution:** Check `/tmp/kiro-agent-bus/signals/` for existing signal files

### Permission errors
**Cause:** `/tmp/` not writable or different user
**Solution:** Set `KIRO_AGENT_BUS_DIR` env var to a writable directory

## Configuration

**Environment Variables:**
- `KIRO_AGENT_BUS_DIR` — Override the bus directory (default: `/tmp/kiro-agent-bus`)

**MCP Configuration:**
The power auto-configures via mcp.json. All 5 tools are auto-approved since inter-agent messaging should not require human confirmation.

---

**Package:** `kiro-power-agent-bus`
**Source:** Open source
**License:** MIT
**Connection:** Local stdio MCP server (Node.js)
