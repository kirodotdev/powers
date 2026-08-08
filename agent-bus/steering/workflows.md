# Cooperation Workflows

## Oncall Triage Pattern

When handling multiple sev-2 tickets simultaneously:

1. **Coordinator agent** reads the ticket queue and prioritizes
2. Coordinator posts assignments to investigator inboxes via `agent_post_message`
3. Each **investigator agent** reads its assignment, investigates, and posts findings back
4. Investigators signal completion via `agent_signal`
5. Coordinator collects findings, synthesizes, and decides next actions

### Setup

```
Coordinator: "You are the oncall coordinator. Read the ticket queue, prioritize sev-2s, and delegate to investigators."
Investigator 1: "You are investigating ticket V123. Read your inbox for instructions."
Investigator 2: "You are investigating ticket V456. Read your inbox for instructions."
```

### Message Protocol

Investigators should structure findings as:
```
TICKET: V2147427488
STATUS: investigated | blocked | needs-escalation
ROOT CAUSE: [one-line summary]
DETAILS: [full findings]
NEXT STEPS: [what needs to happen]
BLOCKER: [if any]
```

## Parallel Development Pattern

When splitting a large feature across agents:

1. **Architect agent** designs the approach and creates task breakdown
2. Posts task assignments to builder inboxes
3. **Builder agents** implement in parallel, sharing progress via signals
4. Builders post "ready for review" signals when done
5. **Reviewer agent** picks up completed work

### Avoiding Conflicts

Use the claims pattern to prevent two agents from editing the same file:
```javascript
// Before editing a file, claim it
agent_post_message({ from: "builder-1", to: "file-claims", body: "CLAIM: src/agent/cooperation/mod.rs" })

// Check if someone else claimed it first
const claims = agent_read_messages({ agent_id: "file-claims", clear: false })
// If another agent claimed it, work on something else
```

## Pipeline Pattern

Sequential handoff between specialized agents:

```
Research → Design → Implement → Test → Review
```

Each stage signals completion and passes context to the next:
```javascript
agent_signal({ name: "stage-research-done", payload: "RFC at path/to/rfc.md" })
agent_signal({ name: "stage-design-done", payload: "Architecture doc at path/to/design.md" })
agent_signal({ name: "stage-implement-done", payload: "Code at crates/cooperation/" })
```

## Status Dashboard Pattern

All agents periodically post status updates to a shared inbox:

```javascript
// Every agent posts status every few minutes
agent_post_message({
  from: "investigator-1",
  to: "status-board",
  body: JSON.stringify({
    agent: "investigator-1",
    task: "V2147427488",
    status: "in-progress",
    progress: "Found root cause, checking DLQ depth",
    updated: new Date().toISOString()
  })
})
```

The coordinator (or human) reads the status board:
```javascript
agent_read_messages({ agent_id: "status-board", clear: false })
```
