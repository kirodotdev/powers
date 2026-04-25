# Delegation and Session Lifecycle

## Preferred delegation sequence

Follow this sequence for reliable delegation:

1. **Verify bridge readiness** — `bridge_health` if uncertain
2. **Discover agents** — `agents_discover` to find available agents
3. **Create a session** — `sessions_create` with `agentId` (returns `sessionId`)
4. **Submit the prompt** — `sessions_prompt` with `sessionId` and `prompt`
5. **Check status** — `sessions_status` if the task is long-running
6. **Continue session** — `sessions_prompt` again for follow-up requests
7. **Close session** — `sessions_close` when work is complete

For one-shot tasks, use `tasks_delegate` instead of steps 3–7.

## Session lifecycle states

Sessions progress through these states:

- **active** — session created, ready for requests
- **busy** — session is processing a prompt
- **idle** — prompt completed, session ready for more requests
- **failed** — session encountered an unrecoverable error

> **Note:** When a session is closed (via `sessions_close` or automatic expiry), it is **deleted** from the executor — not transitioned to a "closed" state. You cannot query a closed session via `sessions_status`; it will return "Session not found".

### State transitions:

```
[create] → active → busy → idle → busy → ...
                                    ↓
                                  failed
         [close/expiry] → session deleted (not queryable)
```

Sessions also expire automatically (**in-process executor only**):
- **TTL expiry** — session exceeded maximum lifetime (default: 1 hour)
- **Idle expiry** — session idle beyond threshold (default: 10 minutes)

Expired sessions are reaped and the agent's `onSessionClose` hook is called with reason `'expired'`.

> **Note:** The `WorkerExecutor` does not have automatic session expiry. Worker sessions persist in the local session map until explicitly closed via `sessions_close`. Worker processes manage their own internal session lifecycle independently.

## Session management rules

### Always use `sessionId`:

- `sessions_create` returns a `sessionId` — use it for all subsequent calls
- Pass `sessionId` to `sessions_prompt`, `sessions_status`, `sessions_close`, `sessions_cancel`
- Report `sessionId` in all outputs for traceability

### One session per task:

- Don't split related work across sessions
- Only create parallel sessions when the user explicitly requests it
- Reuse sessions to reduce overhead

### Session invalidation:

If a session becomes invalid:

1. **Report explicitly** — tell the user the session is no longer valid
2. **Explain reason** — why the session was invalidated (expired, failed, closed)
3. **Offer recovery** — suggest creating a new session
4. **Preserve context** — maintain conversation context despite session loss

## Delegation patterns

### One-shot delegation:

For single tasks that don't need follow-up:

```
tasks_delegate({
  agentId: "my-agent",
  prompt: "Analyze this function for bugs"
})
→ { sessionId: "abc-123", text: "Found 2 issues...", stopReason: "end_turn" }
```

`tasks_delegate` creates a session, sends the prompt, and closes the session in one call.

### Multi-turn delegation:

For interactive work requiring multiple exchanges:

```
sessions_create({ agentId: "my-agent" })
→ { sessionId: "abc-123", agentId: "my-agent", status: "active" }

sessions_prompt({ sessionId: "abc-123", prompt: "Analyze this codebase" })
→ { text: "Found 3 issues...", stopReason: "end_turn" }

sessions_prompt({ sessionId: "abc-123", prompt: "Now suggest fixes" })
→ { text: "Here are the fixes...", stopReason: "end_turn" }

sessions_close({ sessionId: "abc-123" })
→ { closed: true, sessionId: "abc-123" }
```

### Cancellation:

To cancel an in-flight prompt:

```
sessions_cancel({ sessionId: "abc-123", requestId: "req-456" })
```

The agent's `cancel` hook is called if implemented.

## Structured payloads

### Preserve structured outputs:

- **Don't transform** — pass results through unchanged
- **Don't summarize** — keep full structured data
- **Don't flatten** — maintain nested structure
- **Don't filter** — include all fields unless explicitly requested

### Prompt result format:

```json
{
  "text": "Agent response text",
  "stopReason": "end_turn",
  "requestId": "req-456",
  "usage": {
    "inputTokens": 100,
    "outputTokens": 250
  }
}
```

### Session info format:

```json
{
  "sessionId": "abc-123",
  "agentId": "my-agent",
  "status": "idle",
  "createdAt": 1719000000000,
  "lastActivityAt": 1719000060000
}
```

## Session cleanup

### When to close sessions:

- Task is complete and no follow-up is expected
- User explicitly requests to stop
- Session has been idle too long (automatic via idle expiry)
- Unrecoverable error occurred

### Automatic cleanup (in-process executor only):

- **TTL expiry** — sessions expire after configured TTL (default: 1 hour)
- **Idle timeout** — sessions close after idle threshold (default: 10 minutes)
- **Max sessions** — new sessions are rejected when capacity is reached
- The `InProcessExecutor` runs a periodic reaper that cleans up expired sessions

> Worker sessions are not automatically reaped. They persist until explicitly closed or the server shuts down.
