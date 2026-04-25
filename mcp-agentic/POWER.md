---
name: "mcp-agentic"
displayName: "MCP Agentic"
description: "Connect MCP clients to ACP-compatible agents through a local MCP bridge built on stdio Bus with embedded runtime"
keywords:
  - acp
  - agent client protocol
  - mcp
  - stdio bus
  - delegation
  - multi-agent
  - codex acp
  - external agent
  - agent discovery
  - session routing
  - continue session
  - route task to agent
  - embedded runtime
  - worker orchestration
author: "stdio Bus"
license: "Apache-2.0"
---

# MCP Agentic

This power enables MCP clients to communicate with ACP-compatible agents through a local MCP bridge. Agents can run in-process (via `AgentHandler` implementations) or as external worker processes (via `@stdiobus/node` StdioBus). The single entry point is `McpAgenticServer`, which owns the MCP server, tool registration, and executor lifecycle.

## Use this power when

- **Discovering available agents** — find registered agents and their capabilities
- **Delegating work to external agents** — route tasks to specialized agents
- **Managing agent sessions** — create, prompt, check status, cancel, or close sessions
- **Multi-step delegated work** — preserve session continuity across multiple interactions
- **One-shot delegation** — delegate a task in a single call (create + prompt + close)

Do not use this power when the task can be completed fully without external delegation.

## Runtime model

> **Note:** The `mcp.json` config shipped with this power starts the default CLI reference server, which has no agents registered. It is useful for verifying MCP connectivity and inspecting the tool schema, but cannot delegate work. For actual agent delegation, create your own server script that calls `server.register()` before `server.startStdio()` — see the Programmatic setup example below.

**Architecture:**
- The MCP client communicates with 8 MCP tools exposed by `McpAgenticServer`
- `McpAgenticServer` routes tool calls to an `AgentExecutor` backend
- Two executor backends:
  - **InProcessExecutor** — calls `AgentHandler` instances directly in-memory
  - **WorkerExecutor** — routes requests through `@stdiobus/node` StdioBus to ACP worker processes
- In-process agents take priority over workers when an agent ID exists in both
- Sessions are tracked per-executor with TTL and idle expiry

**Key components:**
- **McpAgenticServer** — single public entry point; owns MCP server and executor lifecycle
- **AgentHandler** — public interface users implement for custom agent logic
- **AgentExecutor** — internal interface abstracting execution backends
- **InProcessExecutor** — direct in-memory agent calls, session management, lifecycle hooks
- **WorkerExecutor** — StdioBus transport to external ACP worker processes
- **Tool Handlers** — decoupled functions in `src/mcp/tools/*.ts` that depend only on `AgentExecutor`

## MCP tools (8 total)

| Tool | Description |
|------|-------------|
| `bridge_health` | Check bridge readiness |
| `agents_discover` | List available agents, optionally filter by capability |
| `sessions_create` | Create a new agent session, returns a `sessionId` |
| `sessions_prompt` | Send a prompt to an existing session |
| `sessions_status` | Check the status of an existing session |
| `sessions_close` | Close a session when done |
| `sessions_cancel` | Cancel an in-flight prompt request |
| `tasks_delegate` | One-shot delegation (create session + prompt + close) |

## Mandatory rules

- **Never invent agents, capabilities, or statuses** — always use actual discovery results
- **Never claim delegation succeeded unless the bridge confirms it** — wait for explicit confirmation
- **Never silently switch sessions** — report session changes explicitly
- **Preserve structured tool outputs exactly** — do not transform or summarize results
- **Surface failures explicitly** — report errors with full context and `BridgeError` category
- **Prefer `tasks_delegate` for one-shot work** — use `sessions_*` tools only for multi-turn conversations

## Preferred tool sequence

1. **Check bridge readiness** — `bridge_health`
2. **Discover agents** — `agents_discover` (filter by capability if needed)
3. **Create a session** — `sessions_create` with `agentId`
4. **Submit the task** — `sessions_prompt` with `sessionId` and `prompt`
5. **Check status** — `sessions_status` if the task is long-running
6. **Close session** — `sessions_close` when work is complete
7. **Cancel if needed** — `sessions_cancel` to abort an in-flight prompt

For one-shot tasks, use `tasks_delegate` instead of steps 3–6.

## Output expectations

**Successful delegation returns:**
- `sessionId` — session identifier for continuity
- `agentId` — identifier of the agent handling the request
- `status` — current session status (`active`, `idle`, `busy`, `closed`, `failed`)
- `text` — agent response text (from prompt)
- `stopReason` — why the agent stopped (`end_turn`, `max_turns`, `cancelled`)

**Failures return a `BridgeError` with:**
- `type` — error category (`CONFIG`, `UPSTREAM`, `TRANSPORT`, `TIMEOUT`, `INTERNAL`)
- `message` — human-readable error description
- `details.retryable` — whether the operation can be retried
- `details.sessionValid` — whether the session remains valid after failure

## Configuration

`McpAgenticServer` accepts a `McpAgenticServerConfig` object:

```typescript
interface McpAgenticServerConfig {
  /** Pre-register in-process agents at construction time. */
  agents?: AgentHandler[];
  /** Default agent ID when none is specified in session creation. */
  defaultAgentId?: string;
  /** Maximum concurrent in-flight tool requests. Default: 50. */
  maxConcurrentRequests?: number;
  /** Maximum prompt size in bytes. Default: 1048576 (1 MiB). */
  maxPromptBytes?: number;
  /** Maximum metadata size in bytes (JSON-serialized). Default: 65536 (64 KiB). */
  maxMetadataBytes?: number;
}
```

### Programmatic setup

```typescript
import { McpAgenticServer } from '@stdiobus/mcp-agentic';

const server = new McpAgenticServer({ defaultAgentId: 'my-agent' })
  .register({
    id: 'my-agent',
    capabilities: ['code-analysis'],
    async prompt(sessionId, input) {
      return { text: `Analyzed: ${input}`, stopReason: 'end_turn' };
    },
  })
  .registerWorker({
    id: 'py-agent',
    command: 'python',
    args: ['agent.py'],
    capabilities: ['data-analysis'],
  });

await server.startStdio();
```

### Worker configuration

Workers are registered via `registerWorker()` with a `WorkerConfig`:

```typescript
interface WorkerConfig {
  id: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  capabilities?: string[];
}
```

## Steering references

Load the relevant guidance depending on the task:

- `steering/activation-and-scope.md` — when to use this power
- `steering/discovery-and-routing.md` — agent discovery and routing rules
- `steering/delegation-and-session-lifecycle.md` — session management patterns
- `steering/failure-handling.md` — error handling strategies
- `steering/configuration.md` — configuration options and best practices

## Examples

**Discover available agents:**
```
agents_discover({ capability: "code-analysis" })
→ [{ id: "my-agent", capabilities: ["code-analysis"], status: "ready" }]
```

**Delegate a task (one-shot):**
```
tasks_delegate({ agentId: "my-agent", prompt: "Analyze this codebase for security issues" })
→ { sessionId: "abc-123", text: "Found 3 issues...", stopReason: "end_turn" }
```

**Multi-turn session:**
```
sessions_create({ agentId: "my-agent" })
→ { sessionId: "abc-123", agentId: "my-agent", status: "active" }

sessions_prompt({ sessionId: "abc-123", prompt: "Analyze this codebase" })
→ { text: "Found 3 issues...", stopReason: "end_turn" }

sessions_prompt({ sessionId: "abc-123", prompt: "Now suggest fixes" })
→ { text: "Here are the fixes...", stopReason: "end_turn" }

sessions_close({ sessionId: "abc-123" })
→ { success: true }
```

## Troubleshooting

**Bridge not starting:**
- Check that Node.js >= 20.0.0 is installed
- Verify `@stdiobus/node` is available (for worker mode)
- Review bridge logs in stderr

**Agent discovery returns empty:**
- The default CLI (`npx @stdiobus/mcp-agentic`) starts with no agents registered — this is expected. Create a custom entry point that calls `server.register()` before `server.startStdio()`.
- If using a custom entry point, ensure agents are registered via `register()` or `registerWorker()` before starting the server.
- Check agent status — agents may be `unavailable`

**Session errors:**
- Verify session IDs are preserved across calls
- Check session TTL and idle expiry settings
- Sessions expire after configurable TTL (default: 1 hour) or idle timeout (default: 10 minutes)

**Backpressure errors:**
- `Server overloaded` means `maxConcurrentRequests` limit is reached
- This error is retryable — wait and retry

**Input size errors:**
- `Prompt exceeds maximum size` — reduce prompt size or increase `maxPromptBytes`
- `Metadata exceeds maximum size` — reduce metadata or increase `maxMetadataBytes`

## Security

- **Input validation** — prompt and metadata sizes are validated before forwarding
- **Session isolation** — sessions are isolated per executor
- **Backpressure** — concurrent request limiting prevents resource exhaustion
- **Credential handling** — never hardcode credentials; use environment variables for worker processes via `WorkerConfig.env`
