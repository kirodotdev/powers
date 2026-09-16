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

1. Check executor cache (populated on `start()`)
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

When an agent supports multiple AI providers (e.g., `MultiProviderCompanionAgent`), the discovery response includes an optional `providers` field with enriched metadata:

```json
{
  "id": "multi-provider-agent",
  "capabilities": ["general"],
  "status": "ready",
  "providers": [
    {
      "id": "openai",
      "models": ["gpt-4o", "gpt-4o-mini"],
      "kind": "llm",
      "capabilities": { "streaming": true, "tools": true, "vision": true, "jsonMode": true },
      "displayName": "OpenAI"
    },
    {
      "id": "anthropic",
      "models": ["claude-sonnet-4-20250514"],
      "kind": "llm",
      "capabilities": { "streaming": true, "tools": true, "vision": true, "jsonMode": false },
      "displayName": "Anthropic"
    },
    {
      "id": "google-gemini",
      "models": ["gemini-2.0-flash"],
      "kind": "llm",
      "capabilities": { "streaming": false, "tools": false, "vision": true, "jsonMode": true },
      "displayName": "Google Gemini"
    }
  ]
}
```

Each provider entry may include:
- `kind` — provider type (`'llm'`, `'embedding'`, `'reranker'`). Defaults to `'llm'` if not set.
- `capabilities` — self-reported capabilities (`streaming`, `tools`, `vision`, `jsonMode`). Omitted if the provider has no capabilities metadata.
- `displayName` — human-readable name (e.g., `"OpenAI"`, `"Google Gemini"`)
- `description` — provider description

The `providers` field is only present when the agent has a `ProviderRegistry` with registered providers. Agents without multi-provider support omit this field entirely.

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

## Provider discovery

When agents support multiple AI providers, use `agents_discover` to find available providers and their models before creating a session.

### Discovery sequence:

1. **Call `agents_discover`** — retrieve agent list including provider information
2. **Inspect `providers` field** — check which AI providers are available and their supported models
3. **Select provider** — choose the appropriate provider based on task requirements
4. **Create session with provider** — pass `metadata.provider` to `sessions_create`

### Provider selection rules:

- **By model availability** — choose the provider that supports the model you need (e.g., `gpt-4o` → `openai`, `claude-sonnet-4-20250514` → `anthropic`)
- **By capability match** — some providers may be better suited for specific tasks (e.g., code generation, creative writing)
- **By cost/latency tradeoff** — different providers have different pricing and response times
- **Default provider** — when no provider is specified, the agent uses its configured `defaultProviderId`

### Example: discover providers and select one

```
agents_discover({})
→ [{
    id: "multi-provider-agent",
    capabilities: ["general"],
    status: "ready",
    providers: [
      { id: "openai", models: ["gpt-4o", "gpt-4o-mini"] },
      { id: "anthropic", models: ["claude-sonnet-4-20250514"] }
    ]
  }]

sessions_create({
  agentId: "multi-provider-agent",
  metadata: { provider: "anthropic" }
})
→ { sessionId: "abc-123", agentId: "multi-provider-agent", status: "active" }
```

### Provider not found:

If `metadata.provider` specifies an unregistered provider id, `sessions_create` fails with `BridgeError.config('Provider "{id}" is not registered in the ProviderRegistry')`.

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
