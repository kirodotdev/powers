# Discovery and Routing

## Discovery workflow

Discovery **must happen before delegation** when the target agent is not explicitly known.

### Discovery sequence:

1. **Check bridge health** — verify the bridge is operational via `bridge_health`
2. **Call `agents_discover`** — retrieve list of available agents
3. **Filter by capability** — pass `capability` parameter to narrow results
4. **Select agent** — choose the most appropriate agent by ID
5. **Create session** — use the selected `agentId` in `sessions_create` or `tasks_delegate`

### Discovery timing:

- **On first use** — always discover on initial power activation
- **On explicit request** — when user asks to see available agents
- **On routing failure** — when selected agent is unavailable
- **Never speculatively** — don't discover without a concrete need

## Agent resolution

`McpAgenticServer` resolves agents across two executor backends:

1. **InProcessExecutor** — agents registered via `register()`
2. **WorkerExecutor** — agents registered via `registerWorker()`

### Resolution priority:

In-process agents **always take priority** over workers. When an `agentId` exists in both executors, the in-process agent handles the request.

### Resolution flow:

1. Check executor cache (populated on `startStdio()`)
2. On cache miss, call `discover()` on `InProcessExecutor` first
3. If not found, call `discover()` on `WorkerExecutor`
4. Cache the result for subsequent lookups
5. Cache is invalidated on `register()` or `registerWorker()`

### Default agent:

- If `defaultAgentId` is set in `McpAgenticServerConfig`, it is used when no `agentId` is specified
- If no `defaultAgentId` and no `agentId`, the `InProcessExecutor` uses the first registered agent
- If no in-process agents exist, the `WorkerExecutor` is used

## Agent info

Agents expose their identity and capabilities through discovery:

```json
{
  "id": "my-agent",
  "capabilities": ["code-analysis", "debugging"],
  "status": "ready"
}
```

### Agent statuses:

- **ready** — agent is available for new sessions

> **Note:** The `AgentInfo` type also defines `'busy'` and `'unavailable'` statuses, but the current executor implementations always return `'ready'`. Dynamic status tracking (e.g., marking agents as busy when all sessions are in use) may be added in a future version.

### Capability filtering:

Pass `capability` to `agents_discover` to filter results:

```
agents_discover({ capability: "code-analysis" })
→ [{ id: "my-agent", capabilities: ["code-analysis", "debugging"], status: "ready" }]
```

Only agents whose `capabilities` array includes the specified capability are returned.

## Routing constraints

- **Use discovery results as source of truth** — never invent agents
- **Preserve session affinity** — all requests in a session go to the same executor
- **Never silently reroute** — report any routing changes explicitly
- **Validate before routing** — ensure agent is available and capable

## Session-to-executor binding

Once a session is created:

- The session is bound to the executor that created it
- `McpAgenticServer` resolves the executor for session-based operations (`sessions_prompt`, `sessions_status`, `sessions_close`, `sessions_cancel`) by checking which executor owns the `sessionId`
- In-process executor is checked first, then worker executor

## Routing failures

When routing fails:

1. **Report the error** — include `BridgeError` type and message
2. **Explain reason** — agent not found, no agents registered, etc.
3. **Suggest alternatives** — use `agents_discover` to find available agents
4. **Preserve session** — keep session valid if possible

### Common routing failures:

- **Agent not found** — `BridgeError.upstream('Agent not found: {agentId}')`
- **No agents registered** — `BridgeError.config('No agents registered')`
- **Session not found** — `BridgeError.upstream('Session not found: {sessionId}')`
- **Executor not started** — `BridgeError.internal('Executor not started')`
