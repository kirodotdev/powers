# cmux Integration

Agent Bus works seamlessly with [cmux](https://cmux.dev), the terminal multiplexer built for AI coding agents.

## Spawning Agents with Bus Access

When launching kiro sessions in cmux panes, each session automatically has access to the Agent Bus MCP tools (if the power is installed).

```bash
# Create splits for parallel agents
cmux new-split right
cmux new-split down

# Launch kiro in each pane
cmux send --surface surface:2 'kiro-cli chat --trust-all-tools "You are investigator-1. Use agent_post_message to register with the registry inbox, then read your assignment from agent_read_messages."
'
```

## Monitoring from Coordinator Pane

The coordinator agent can use cmux's `read-screen` alongside Agent Bus messages:

```bash
# Read agent bus messages (via MCP tools in kiro)
# Plus read raw terminal output for additional context
cmux read-screen --surface surface:2 --lines 20
```

## Combining cmux Notifications with Signals

When an agent completes a task, it can both:
1. Set an Agent Bus signal (for other agents)
2. Trigger a cmux notification (for the human)

```bash
# In the agent's workflow:
# 1. Signal other agents
agent_signal({ name: "task-done", payload: "findings summary" })

# 2. Notify the human via cmux
# (agent runs this via execute_bash)
cmux notify --title "Investigation Complete" --body "V2147427488 root cause found"
cmux log --level success "Ticket V2147427488 investigated"
```

## Sidebar Status Integration

Agents can update cmux sidebar status to show at-a-glance progress:

```bash
# Agent updates its workspace sidebar
cmux set-status oncall "investigating V2147427488" --icon hammer --color "#ff9500"
cmux set-progress 0.5 --label "Checking DLQ depth..."

# When done
cmux set-status oncall "complete" --icon checkmark --color "#34c759"
cmux set-progress 1.0 --label "Done"
```

## Full Example: Oncall with 3 Investigators

```bash
#!/bin/bash
# oncall-parallel.sh — Launch parallel oncall investigation

KIRO="kiro-cli chat --model claude-opus-4.6-1m --trust-all-tools"

# Pane 1: Coordinator (current pane)
# Pane 2: Investigator 1
cmux new-split right
sleep 0.3
cmux send --surface surface:2 "${KIRO}
"
sleep 10
cmux send --surface surface:2 "You are investigator-1. Register yourself: agent_post_message(from='inv-1', to='registry', body='Investigating V2147427488'). Then investigate the ticket and post findings to coordinator inbox.
"

# Pane 3: Investigator 2
cmux new-split down --surface surface:2
sleep 0.3
cmux send --surface surface:3 "${KIRO}
"
sleep 10
cmux send --surface surface:3 "You are investigator-2. Register yourself: agent_post_message(from='inv-2', to='registry', body='Investigating V2145073654'). Then investigate and post findings to coordinator inbox.
"

echo "Investigators launched. Use agent_read_messages to check their findings."
```
