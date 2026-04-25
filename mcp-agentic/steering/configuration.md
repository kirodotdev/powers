# Configuration

## McpAgenticServerConfig

`McpAgenticServer` is configured via a `McpAgenticServerConfig` object passed to the constructor. There is no external config file or `AGENT_CONFIG_PATH` environment variable.

```typescript
interface McpAgenticServerConfig {
  agents?: AgentHandler[];         // Pre-register in-process agents
  defaultAgentId?: string;         // Default agent when none specified
  maxConcurrentRequests?: number;  // Backpressure limit (default: 50)
  maxPromptBytes?: number;         // Max prompt size (default: 1 MiB)
  maxMetadataBytes?: number;       // Max metadata size (default: 64 KiB)
  silent?: boolean;                // Suppress executor stderr logging (default: false)
}
```

## In-process agents

Register agents programmatically using the fluent API:

```typescript
import { McpAgenticServer } from '@stdiobus/mcp-agentic';

const server = new McpAgenticServer({ defaultAgentId: 'my-agent' })
  .register({
    id: 'my-agent',
    capabilities: ['code-analysis', 'debugging'],
    async prompt(sessionId, input) {
      return { text: `Response: ${input}`, stopReason: 'end_turn' };
    },
  });
```

### AgentHandler interface

Agents implement the `AgentHandler` interface:

```typescript
interface AgentHandler {
  readonly id: string;
  readonly capabilities?: string[];
  prompt?(sessionId: string, input: string, opts?: PromptOpts): Promise<AgentResult>;
  stream?(sessionId: string, input: string, opts?: StreamOpts): AsyncIterable<AgentEvent>;
  onSessionCreate?(sessionId: string, metadata?: Record<string, unknown>): Promise<void>;
  onSessionClose?(sessionId: string, reason?: string): Promise<void>;
  cancel?(sessionId: string, requestId?: string): Promise<void>;
}
```

At minimum, implement `id` and either `prompt` or `stream`.

## Worker configuration

Register external worker processes via `registerWorker()`:

```typescript
server.registerWorker({
  id: 'py-agent',
  command: 'python',
  args: ['agent.py'],
  env: { OPENAI_API_KEY: process.env.OPENAI_API_KEY ?? '' },
  capabilities: ['data-analysis'],
});
```

### WorkerConfig

```typescript
interface WorkerConfig {
  id: string;                       // Unique worker/agent ID
  command: string;                  // Executable to spawn
  args: string[];                   // Command-line arguments
  env?: Record<string, string>;     // Additional environment variables
  capabilities?: string[];          // Advertised capabilities
}
```

The `WorkerExecutor` creates a `StdioBus` instance on `start()` with pool configurations derived from registered `WorkerConfig` entries. The `env` field is passed through to the StdioBus pool so worker processes receive the specified environment variables.

## Backpressure

`maxConcurrentRequests` (default: 50) limits the number of in-flight tool handler calls. When the limit is reached, new requests are rejected with a retryable `BridgeError.transport('Server overloaded')`.

## Input size validation

- `maxPromptBytes` (default: 1,048,576 / 1 MiB) — maximum prompt size in bytes
- `maxMetadataBytes` (default: 65,536 / 64 KiB) — maximum metadata size in bytes (JSON-serialized)

Prompts and metadata are validated before being forwarded to the executor. Oversized inputs are rejected with `BridgeError.upstream`.

## Session limits

The `InProcessExecutor` enforces a configurable `maxSessions` limit (default: 100). Sessions also have:

- **Session TTL** (`sessionTtlMs`, default: 3,600,000 / 1 hour) — maximum session lifetime
- **Idle timeout** (`sessionIdleMs`, default: 600,000 / 10 minutes) — maximum idle time before expiry

Expired sessions are reaped automatically and the agent's `onSessionClose` hook is called with reason `'expired'`.

## Logging

Executors log lifecycle events (start, close, errors) to stderr via `process.stderr.write`. This logging is controlled by the `silent` flag in `McpAgenticServerConfig`:

- `silent: false` (default) — executors write lifecycle messages to stderr
- `silent: true` — all executor logging is suppressed (useful for tests)

stdout is reserved for MCP protocol messages — never write non-protocol data there.

> **Note:** The `Logger` class and `LoggingConfig` type exist internally but are not exposed through `McpAgenticServerConfig`. They are used by `RemoteAgenticBridge` (SaaS mode) and may be integrated into the public API in a future version.

## CLI entry point

The CLI entry point (`out/dist/cli/server.js`) is a **reference/diagnostics server** with no agents registered. It starts the MCP server and warns on stderr:

```typescript
import { McpAgenticServer } from '@stdiobus/mcp-agentic';

const server = new McpAgenticServer();
await server.startStdio();

// Warns: "No agents registered. This CLI is a reference server for diagnostics only."
```

`bridge_health` and `agents_discover` will respond (healthy: false / empty list), but `tasks_delegate` and `sessions_create` will fail because there are no agents.

For actual agent delegation, create your own entry point that calls `server.register()` before `server.startStdio()`.

## Best practices

1. **Use in-process agents for development** — simpler setup, faster iteration
2. **Use workers for production isolation** — separate processes for reliability
3. **Set appropriate limits** — tune `maxConcurrentRequests`, `maxPromptBytes`, and session limits for your workload
4. **Pass credentials via `env`** — use `WorkerConfig.env` for worker process secrets
5. **Handle signals** — always wire up `SIGINT`/`SIGTERM` to `server.close()`
6. **Monitor health** — use `bridge_health` to check readiness before delegating
