---
name: "mcp-agentic"
displayName: "MCP Agentic"
description: "Connect MCP clients to ACP-compatible agents through a local MCP bridge built on stdio Bus with embedded runtime and multi-provider AI support (OpenAI, Anthropic, Google Gemini)"
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
  - multi-provider
  - openai
  - anthropic
  - gemini
  - runtime-params
  - provider-discovery
author: "stdio Bus"
license: "Apache-2.0"
---

# MCP Agentic

This power enables MCP clients to communicate with ACP-compatible agents through a local MCP bridge. Agents can run in-process (via `AgentHandler` implementations) or as external worker processes (via `@stdiobus/node` StdioBus). The single entry point is `McpAgenticServer`, which owns the MCP server, tool registration, and executor lifecycle.

The power includes a **multi-provider AI layer** supporting OpenAI, Anthropic, and Google Gemini through their native SDKs. The **Factory API** (`openAI()`, `anthropic()`, `gemini()`, `createMultiProviderAgent()`) is the recommended way to configure providers with flat, typed options and Zod validation. Custom providers can be created via `defineProvider()`. Providers expose `kind` and `capabilities` metadata for enriched discovery via `agents_discover`.

## Use this power when

- **Discovering available agents** — find registered agents and their capabilities
- **Delegating work to external agents** — route tasks to specialized agents
- **Managing agent sessions** — create, prompt, check status, cancel, or close sessions
- **Multi-step delegated work** — preserve session continuity across multiple interactions
- **One-shot delegation** — delegate a task in a single call (create + prompt + close)
- **Selecting AI providers** — choose between OpenAI, Anthropic, or Google Gemini per session
- **Tuning AI parameters at runtime** — override model, temperature, systemPrompt, and other parameters per request

Do not use this power when the task can be completed fully without external delegation.

## Runtime model

> **Note:** The `mcp.json` config shipped with this power starts the default CLI reference server, which has no agents registered. It is useful for verifying MCP connectivity and inspecting the tool schema, but cannot delegate work. For actual agent delegation, create your own server script that calls `server.register()` before `server.start()` — see the Programmatic setup example below.

**Architecture:**
- The MCP client communicates with 8 MCP tools exposed by `McpAgenticServer`
- `McpAgenticServer` routes tool calls to an `AgentExecutor` backend
- Two executor backends:
  - **InProcessExecutor** — calls `AgentHandler` instances directly in-memory
  - **WorkerExecutor** — routes requests through `@stdiobus/node` StdioBus to ACP worker processes
- In-process agents take priority over workers when an agent ID exists in both
- Sessions are tracked per-executor with TTL and idle expiry
- **Provider Layer** — an extensible layer of AI providers (`src/provider/`) that normalizes requests and responses across different AI services through the `AIProvider` interface

**Key components:**
- **McpAgenticServer** — single public entry point; owns MCP server and executor lifecycle
- **AgentHandler** — public interface users implement for custom agent logic
- **AgentExecutor** — internal interface abstracting execution backends
- **InProcessExecutor** — direct in-memory agent calls, session management, lifecycle hooks
- **WorkerExecutor** — StdioBus transport to external ACP worker processes
- **Tool Handlers** — decoupled functions in `src/mcp/tools/*.ts` that depend only on `AgentExecutor`
- **ProviderRegistry** — registry of AI providers; supports registration, lookup, and discovery of available providers and their models
- **MultiProviderCompanionAgent** — agent implementing `AgentHandler` that delegates AI generation to any registered provider, with dynamic provider selection per session and runtime parameter overrides

## MCP tools (8 total)

| Tool | Description |
|------|-------------|
| `bridge_health` | Check bridge readiness |
| `agents_discover` | List available agents, optionally filter by capability. Response includes a `providers` field for agents that support multiple AI providers, listing each provider's `id`, `models`, `kind`, `capabilities`, `displayName`, and `description`. |
| `sessions_create` | Create a new agent session, returns a `sessionId`. Accepts `metadata.provider` to select a specific AI provider for the session, and `metadata.runtimeParams` for session-level parameter defaults. |
| `sessions_prompt` | Send a prompt to an existing session. Accepts an optional `runtimeParams` field to override provider parameters (model, temperature, systemPrompt, etc.) for this specific prompt. |
| `sessions_status` | Check the status of an existing session |
| `sessions_close` | Close a session when done |
| `sessions_cancel` | Cancel an in-flight prompt request |
| `tasks_delegate` | One-shot delegation (create session + prompt + close). Accepts an optional `runtimeParams` field to override provider parameters for this delegation. |

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
3. **Create a session** — `sessions_create` with `agentId` (and optionally `metadata.provider` to select a provider)
4. **Submit the task** — `sessions_prompt` with `sessionId` and `prompt` (and optionally `runtimeParams`)
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
- `stopReason` — why the agent stopped (`end_turn`, `max_tokens`, `content_filter`, `cancelled`)
- `usage` — token usage statistics (when available): `{ inputTokens, outputTokens }`

**Agent discovery (`agents_discover`) returns:**
- `id` — agent identifier
- `capabilities` — list of agent capabilities
- `status` — agent status (`ready`, `busy`, `unavailable`)
- `providers` — (optional) array of available AI providers when the agent supports multiple providers, each with `id`, `models`, and enriched metadata (`kind`, `capabilities`, `displayName`, `description`)

**`sessions_prompt` accepts:**
- `sessionId` — target session
- `prompt` — prompt text
- `timeout` — optional request timeout in milliseconds
- `runtimeParams` — optional runtime parameter overrides (see RuntimeParams below)

**`tasks_delegate` accepts:**
- `prompt` — prompt text
- `agentId` — optional target agent
- `timeout` — optional request timeout in milliseconds
- `metadata` — optional session metadata (including `provider` for provider selection)
- `runtimeParams` — optional runtime parameter overrides

**Failures return a `BridgeError` with:**
- `type` — error category (`CONFIG`, `AUTH`, `UPSTREAM`, `TRANSPORT`, `TIMEOUT`, `INTERNAL`)
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

### MultiProviderCompanionConfig

Configuration for constructing a `MultiProviderCompanionAgent`:

```typescript
interface MultiProviderCompanionConfig {
  /** Unique agent identifier. */
  id: string;
  /** Default provider id to use when no override is specified. */
  defaultProviderId: string;
  /** Registry of available AI providers. */
  registry: ProviderRegistry;
  /** Optional list of capabilities this agent supports. */
  capabilities?: string[];
  /** Default system prompt applied to all sessions unless overridden. */
  systemPrompt?: string;
  /** Provider-level default RuntimeParams. */
  defaults?: RuntimeParams;
}
```

### ProviderConfig

Configuration for constructing a provider instance:

```typescript
interface ProviderConfig {
  /** Credential key-value pairs (e.g., { apiKey: '...' }). Sourced from env by the caller. */
  credentials: Record<string, string>;
  /** Model identifiers available for this provider. */
  models: string[];
  /** Default RuntimeParams applied when no override is specified. */
  defaults?: RuntimeParams;
}
```

### RuntimeParams

Parameters for AI generation, passed dynamically at runtime:

```typescript
interface RuntimeParams {
  model?: string;            // Model identifier
  temperature?: number;      // Sampling temperature (0–2)
  maxTokens?: number;        // Maximum tokens to generate
  topP?: number;             // Nucleus sampling (0–1)
  topK?: number;             // Top-K sampling
  stopSequences?: string[];  // Stop sequences
  systemPrompt?: string;     // System prompt override
  providerSpecific?: Record<string, unknown>;  // Provider-native parameters
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

await server.start();
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

## Multi-provider configuration

The multi-provider layer allows using OpenAI, Anthropic, and Google Gemini through their native SDKs with a unified interface.

### Peer dependencies

Install only the provider SDKs you need:

```bash
# OpenAI
npm install openai

# Anthropic
npm install @anthropic-ai/sdk

# Google Gemini
npm install @google/generative-ai
```

### ProviderConfig and RuntimeParams

Each provider is constructed with a `ProviderConfig` containing credentials (sourced from environment variables by the caller), a list of available models, and optional default `RuntimeParams`. Providers never access `process.env` directly after construction.

### Three-level merge priority

RuntimeParams are merged in ascending priority:

```
ProviderConfig.defaults  <  session metadata.runtimeParams  <  prompt-level runtimeParams
```

- Only defined (non-`undefined`) fields from higher-priority layers override lower ones.
- `providerSpecific` is shallow-merged (spread) across all layers, not replaced.

### Programmatic setup with providers

```typescript
import {
  McpAgenticServer,
  openAI,
  anthropic,
  gemini,
  createMultiProviderAgent,
} from '@stdiobus/mcp-agentic';

// Create multi-provider agent using Factory API
const agent = createMultiProviderAgent({
  id: 'multi-ai',
  defaultProviderId: 'openai',
  providers: [
    openAI({
      apiKey: process.env.OPENAI_API_KEY!,
      models: ['gpt-4o', 'gpt-4o-mini'],
      defaults: { temperature: 0.7 },
    }),
    anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY!,
      models: ['claude-sonnet-4-20250514'],
    }),
    gemini({
      apiKey: process.env.GOOGLE_AI_API_KEY!,
      models: ['gemini-2.0-flash'],
    }),
  ],
  capabilities: ['chat', 'analysis'],
  systemPrompt: 'You are a helpful assistant.',
});

// Register and start server
const server = new McpAgenticServer({ defaultAgentId: 'multi-ai' })
  .register(agent);

await server.start();
```

## Steering references

Load the relevant guidance depending on the task:

- `steering/activation-and-scope.md` — when to use this power
- `steering/discovery-and-routing.md` — agent discovery and routing rules
- `steering/delegation-and-session-lifecycle.md` — session management patterns
- `steering/failure-handling.md` — error handling strategies
- `steering/configuration.md` — configuration options and best practices

## Examples

**Discover available agents and their providers:**
```
agents_discover({ capability: "chat" })
→ [{
    id: "multi-ai",
    capabilities: ["chat", "analysis"],
    status: "ready",
    providers: [
      { id: "openai", models: ["gpt-4o", "gpt-4o-mini"], kind: "llm", capabilities: { streaming: true, tools: true, vision: true, jsonMode: true }, displayName: "OpenAI" },
      { id: "anthropic", models: ["claude-sonnet-4-20250514"], kind: "llm", capabilities: { streaming: true, tools: true, vision: true, jsonMode: false }, displayName: "Anthropic" },
      { id: "google-gemini", models: ["gemini-2.0-flash"], kind: "llm", capabilities: { streaming: false, tools: false, vision: true, jsonMode: true }, displayName: "Google Gemini" }
    ]
  }]
```

**Create session with a specific provider:**
```
sessions_create({ agentId: "multi-ai", metadata: { provider: "anthropic" } })
→ { sessionId: "abc-123", agentId: "multi-ai", status: "active" }
```

**Prompt with runtimeParams override:**
```
sessions_prompt({
  sessionId: "abc-123",
  prompt: "Explain quantum computing",
  runtimeParams: { temperature: 0.3, model: "claude-sonnet-4-20250514", systemPrompt: "Explain concepts simply." }
})
→ { text: "Quantum computing uses...", stopReason: "end_turn", usage: { inputTokens: 42, outputTokens: 128 } }
```

**One-shot delegation with runtimeParams:**
```
tasks_delegate({
  agentId: "multi-ai",
  prompt: "Summarize this document",
  metadata: { provider: "openai" },
  runtimeParams: { temperature: 0, maxTokens: 200 }
})
→ { sessionId: "def-456", text: "The document covers...", stopReason: "end_turn" }
```

**Multi-provider switching in one server:**
```
// Session 1: Use OpenAI
sessions_create({ agentId: "multi-ai", metadata: { provider: "openai" } })
→ { sessionId: "s1", agentId: "multi-ai", status: "active" }

sessions_prompt({ sessionId: "s1", prompt: "Hello" })
→ { text: "Hi there! (from OpenAI)", stopReason: "end_turn" }

// Session 2: Use Anthropic
sessions_create({ agentId: "multi-ai", metadata: { provider: "anthropic" } })
→ { sessionId: "s2", agentId: "multi-ai", status: "active" }

sessions_prompt({ sessionId: "s2", prompt: "Hello" })
→ { text: "Hello! (from Anthropic)", stopReason: "end_turn" }
```

**Delegate a task (one-shot, basic):**
```
tasks_delegate({ agentId: "my-agent", prompt: "Analyze this codebase for security issues" })
→ { sessionId: "abc-123", text: "Found 3 issues...", stopReason: "end_turn" }
```

**Multi-turn session (basic):**
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
- The default CLI (`npx @stdiobus/mcp-agentic`) starts with no agents registered — this is expected. Create a custom entry point that calls `server.register()` before `server.start()`.
- If using a custom entry point, ensure agents are registered via `register()` or `registerWorker()` before starting the server.
- Check agent status — agents may be `unavailable`

**Provider SDK not installed:**
- Provider SDKs (`openai`, `@anthropic-ai/sdk`, `@google/generative-ai`) are peer dependencies — install only the ones you need
- If you see a module-not-found error for a provider SDK, run `npm install <package-name>`

**API key missing → BridgeError CONFIG:**
- Each provider validates that required credentials (e.g., `apiKey`) are present and non-empty at construction time
- If a credential is missing, the provider throws a `BridgeError` with category `CONFIG` specifying which credential is absent
- Ensure environment variables are set before constructing providers

**Invalid API key → BridgeError AUTH:**
- If the AI service rejects the API key at request time, the provider throws a `BridgeError` with category `AUTH`
- Verify the API key is valid and has the required permissions

**Rate limiting → BridgeError UPSTREAM (retryable):**
- When a provider receives a rate-limit response (HTTP 429), it throws a `BridgeError` with category `UPSTREAM` and `retryable: true`
- Wait and retry the request

**Unknown provider in metadata → BridgeError CONFIG:**
- If `metadata.provider` in `sessions_create` specifies a provider id not registered in the `ProviderRegistry`, a `BridgeError` with category `CONFIG` is thrown
- Use `agents_discover` to check available providers before creating a session

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
- **Provider credentials** — providers accept credentials via `ProviderConfig.credentials` at construction time and never access `process.env` directly after construction
