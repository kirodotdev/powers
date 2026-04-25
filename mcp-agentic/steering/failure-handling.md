# Failure Handling

## BridgeError categories

All errors in the system are represented as `BridgeError` instances with a `type` field indicating the category:

| Category | When Used | Retryable | MCP Error Code |
|----------|-----------|-----------|----------------|
| `CONFIG` | Invalid configuration, no agents registered | No | `-32004` |
| `UPSTREAM` | Agent errors, session not found, agent not found, invalid worker response | No | `-32002` |
| `TRANSPORT` | StdioBus communication failures, worker timeouts, server overloaded (backpressure) | Yes | `-32000` |
| `INTERNAL` | Executor not started, unexpected internal errors | No | `-32603` |

> **Note:** The `BridgeError` class also defines `AUTH`, `TIMEOUT`, and `PROTOCOL` types for future use, but no current code path produces them. Worker timeouts are mapped to `TRANSPORT` with `retryable: true`.

## Error sources by executor

### InProcessExecutor errors:

| Scenario | Error |
|----------|-------|
| `prompt()` called before `start()` | `BridgeError.internal('Executor not started')` |
| `createSession()` with non-existent `agentId` | `BridgeError.upstream('Agent not found: {agentId}')` |
| `createSession()` at capacity | `BridgeError.upstream('Session capacity reached')` |
| `getSession()` / `prompt()` with unknown `sessionId` | `BridgeError.upstream('Session not found: {sessionId}')` |
| Agent's `prompt()` throws unexpected error | `BridgeError.upstream('Agent {agentId} failed', {}, cause)` |
| No agents registered | `BridgeError.config('No agents registered')` |

### WorkerExecutor errors:

| Scenario | Error |
|----------|-------|
| `start()` fails to create StdioBus | `BridgeError.transport('Failed to start StdioBus')` |
| `bus.request()` throws error | `BridgeError.upstream('Worker {workerId} failed: {operation}', {}, cause)` |
| `bus.request()` times out | `BridgeError.transport('Worker {workerId} timed out', { retryable: true })` |
| `prompt()` called before `start()` | `BridgeError.internal('Executor not started')` |
| Invalid worker response (missing `sessionId`) | `BridgeError.upstream('Invalid worker response: missing sessionId')` |
| Malformed prompt result | `BridgeError.upstream('Invalid worker response: malformed prompt result')` |

### McpAgenticServer errors:

| Scenario | Error |
|----------|-------|
| Concurrent request limit reached | `BridgeError.transport('Server overloaded', { retryable: true })` |
| Prompt exceeds `maxPromptBytes` | `BridgeError.upstream('Prompt exceeds maximum size')` |
| Metadata exceeds `maxMetadataBytes` | `BridgeError.upstream('Metadata exceeds maximum size')` |

## Failure reporting principles

When a tool call fails, **always report**:

1. **Error category** — the `BridgeError` type (CONFIG, UPSTREAM, TRANSPORT, INTERNAL)
2. **Error message** — human-readable description
3. **Retryability** — whether the operation can be retried (`details.retryable`)
4. **Session validity** — whether the session remains valid (`details.sessionValid`)
5. **Recovery options** — what the user can do next

> **Note:** Tool handlers may also produce non-BridgeError exceptions (e.g., Zod validation errors for malformed input). These are caught by `mapErrorToMCP()` and mapped to `INTERNAL` with `retryable: false`.

## Error classification

### Transient errors (retryable):

- Server overloaded (backpressure) — `TRANSPORT`
- Worker timeout — `TRANSPORT` with `retryable: true`
- StdioBus transport failures — `TRANSPORT`

**Strategy:** Wait and retry.

### Permanent errors (not retryable):

- Invalid configuration
- Agent not found
- Session not found
- Session capacity reached
- Input size exceeded

**Strategy:** Report to user, fix the issue, don't retry.

### Internal errors (not retryable):

- Executor not started
- Unexpected internal failures

**Strategy:** Report to user, check bridge health, restart if needed.

## MCP error mapping

`BridgeError` instances are mapped to MCP JSON-RPC error codes via `mapErrorToMCP()`:

```
CONFIG    → -32004 (Config Error)
UPSTREAM  → -32002 (Upstream Error)
TRANSPORT → -32000 (Server Error)
INTERNAL  → -32603 (Internal Error)
Unknown   → -32603 (Internal Error)
```

> `AUTH` → `-32003`, `TIMEOUT` → `-32001`, `PROTOCOL` → `-32000` are defined in the error mapper but not currently produced by any runtime code path.

The MCP error response includes:
- `code` — numeric MCP error code
- `message` — original error message
- `data` — error details including `type`, `retryable`, `sessionValid`

## Failure handling rules

### Do NOT:

- **Claim success on failure** — be explicit about errors
- **Hide bridge errors** — don't wrap in generic messages
- **Silently discard warnings** — report all warnings
- **Retry indefinitely** — respect the `retryable` flag
- **Ignore session state** — check if session is still valid after errors

### DO:

- **Report exact error category** — use the `BridgeError` type
- **Distinguish retryable from permanent** — check `details.retryable`
- **Preserve `sessionId`** — keep session identifier even on failure
- **Include raw error details** — provide underlying error context
- **Suggest recovery** — offer actionable next steps
- **Use `bridge_health`** — check readiness after failures

## Idempotent operations (safe to retry):

- `bridge_health`
- `agents_discover`
- `sessions_status`
- `sessions_close` (returns silently if session already closed or doesn't exist)

## Non-idempotent operations (retry with caution):

- `sessions_create`
- `sessions_prompt`
- `sessions_cancel`
- `tasks_delegate`

Only retry these if the error is marked `retryable: true`.

## User communication

### Error messages for users:

- **Be specific** — explain exactly what failed and which error category
- **Be actionable** — suggest what the user can do
- **Be honest** — don't hide or minimize failures
- **Be concise** — include the error type and message, not full stack traces

### Example user message:

```
Failed to submit prompt to agent 'my-agent':
Session not found: abc-123 (UPSTREAM, not retryable)

The session may have expired. You can:
1. Create a new session with sessions_create
2. Check available agents with agents_discover
```
