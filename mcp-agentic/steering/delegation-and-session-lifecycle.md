# Delegation and Session Lifecycle

## Preferred delegation sequence

Follow this sequence for reliable delegation:

1. **Verify bridge readiness** — `bridge_health` if uncertain
2. **Discover agents** — `agents_discover` to find available agents and their providers
3. **Select provider** — if the agent supports multiple providers, choose one based on the `providers` field in the discovery response
4. **Create a session** — `sessions_create` with `agentId` and optional `metadata.provider` (returns `sessionId`)
5. **Submit the prompt** — `sessions_prompt` with `sessionId`, `prompt`, and optional `runtimeParams`
6. **Check status** — `sessions_status` if the task is long-running
7. **Continue session** — `sessions_prompt` again for follow-up requests (with optional `runtimeParams` overrides)
8. **Close session** — `sessions_close` when work is complete

For one-shot tasks, use `tasks_delegate` (with optional `runtimeParams`) instead of steps 3–8.

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

## Provider-aware sessions

When using `MultiProviderCompanionAgent`, sessions can be bound to a specific AI provider at creation time.

### Creating a session with a specific provider:

Pass `metadata.provider` to `sessions_create` to select the AI provider for the session:

```
sessions_create({
  agentId: "multi-provider-agent",
  metadata: {
    provider: "anthropic",
    runtimeParams: { model: "claude-sonnet-4-20250514", temperature: 0.7 }
  }
})
→ { sessionId: "abc-123", agentId: "multi-provider-agent", status: "active" }
```

- `metadata.provider` — selects the AI provider for all prompts in this session
- `metadata.runtimeParams` — sets session-level default parameters (model, temperature, etc.)
- If `metadata.provider` is omitted, the agent uses its configured `defaultProviderId`
- If `metadata.provider` specifies an unregistered provider, `sessions_create` fails with `BridgeError` CONFIG

### Provider affinity:

Once a session is created with a specific provider, all prompts in that session use that provider. The provider cannot be changed mid-session — create a new session to switch providers.

## Runtime parameter overrides

`RuntimeParams` allow dynamic control of AI generation parameters at each request, without restarting the server.

### Available parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `string` | Model identifier (e.g., `"gpt-4o"`, `"claude-sonnet-4-20250514"`) |
| `temperature` | `number` (0–2) | Sampling temperature; higher = more random |
| `maxTokens` | `number` (positive int) | Maximum tokens to generate |
| `topP` | `number` (0–1) | Nucleus sampling probability |
| `topK` | `number` (positive int) | Top-K sampling parameter |
| `stopSequences` | `string[]` | Sequences that stop generation |
| `systemPrompt` | `string` | System prompt override for this request |
| `providerSpecific` | `Record<string, unknown>` | Provider-native parameters not covered by common fields |

### Merge priority (ascending):

```
ProviderConfig.defaults  <  session metadata.runtimeParams  <  prompt-level runtimeParams
```

Only defined fields override lower-priority values. `undefined` fields are ignored during merge. `providerSpecific` is shallow-merged across all layers.

### Per-prompt overrides via `sessions_prompt`:

```
sessions_prompt({
  sessionId: "abc-123",
  prompt: "Explain quantum computing",
  runtimeParams: {
    temperature: 0.2,
    maxTokens: 500,
    systemPrompt: "You are a physics professor. Explain concepts simply."
  }
})
→ { text: "Quantum computing uses...", stopReason: "end_turn", usage: { inputTokens: 45, outputTokens: 120 } }
```

### One-shot delegation with `runtimeParams`:

```
tasks_delegate({
  agentId: "multi-provider-agent",
  prompt: "Summarize this document",
  metadata: { provider: "openai" },
  runtimeParams: { temperature: 0, maxTokens: 200 }
})
→ { sessionId: "xyz-789", text: "The document covers...", stopReason: "end_turn", usage: { inputTokens: 80, outputTokens: 50 } }
```

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

The `usage` field is present when the AI provider reports token consumption. It contains `inputTokens` (tokens consumed by the prompt) and `outputTokens` (tokens generated in the response). Not all providers or configurations guarantee usage data.

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
