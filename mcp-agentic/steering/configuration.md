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

## Quick start with Factory API (recommended)

The Factory API is the recommended way to create providers and multi-provider agents:

```typescript
import {
  McpAgenticServer,
  openAI,
  anthropic,
  gemini,
  createMultiProviderAgent,
} from '@stdiobus/mcp-agentic';

const agent = createMultiProviderAgent({
  id: 'companion',
  defaultProviderId: 'openai',
  providers: [
    openAI({ apiKey: process.env.OPENAI_API_KEY ?? '', models: ['gpt-4o'] }),
    anthropic({ apiKey: process.env.ANTHROPIC_API_KEY ?? '', models: ['claude-sonnet-4-20250514'] }),
    gemini({ apiKey: process.env.GOOGLE_AI_API_KEY ?? '', models: ['gemini-2.0-flash'] }),
  ],
  capabilities: ['general'],
  systemPrompt: 'You are a helpful assistant.',
  defaults: { temperature: 0.7 },
});

const server = new McpAgenticServer({ defaultAgentId: 'companion' })
  .register(agent);

await server.start();
```

### Factory options

Each factory accepts flat, typed options with Zod validation at call time:

| Factory | Options | Required | Optional |
|---------|---------|----------|----------|
| `openAI()` | `OpenAIOptions` | `apiKey: string`, `models: string[]` | `defaults?: RuntimeParams` |
| `anthropic()` | `AnthropicOptions` | `apiKey: string`, `models: string[]` | `defaults?: RuntimeParams` |
| `gemini()` | `GeminiOptions` | `apiKey: string`, `models: string[]` | `defaults?: RuntimeParams` |

Invalid options (empty `apiKey`, empty `models`) throw `BridgeError.config` immediately.

If the provider SDK is not installed, the factory throws `BridgeError.config` with an installation instruction.

### createMultiProviderAgent

`createMultiProviderAgent()` replaces manual `ProviderRegistry` + `MultiProviderCompanionAgent` wiring:

```typescript
interface CreateMultiProviderAgentConfig {
  id: string;                    // Unique agent identifier
  providers: AIProvider[];       // Array of provider instances
  defaultProviderId: string;     // Must match one provider's id
  capabilities?: string[];       // Agent capabilities for discovery
  systemPrompt?: string;         // Default system prompt
  defaults?: RuntimeParams;      // Agent-level default parameters
}
```

Validation: empty `providers`, duplicate provider ids, or unknown `defaultProviderId` throw `BridgeError.config`.

### Custom providers with defineProvider

Use `defineProvider()` to create custom providers with Zod validation and discoverable metadata:

```typescript
import { defineProvider } from '@stdiobus/mcp-agentic';
import { z } from 'zod';

const myProvider = defineProvider({
  id: 'my-llm',
  kind: 'llm',
  displayName: 'My LLM',
  description: 'Custom LLM integration',
  capabilities: { streaming: true, tools: false, vision: false, jsonMode: false },
  schema: z.object({
    apiKey: z.string().min(1),
    models: z.array(z.string()).nonempty(),
  }),
  create: (options) => ({
    id: 'my-llm',
    models: options.models,
    async complete(messages, params) {
      // Your implementation here
      return { text: '...', stopReason: 'end_turn' };
    },
  }),
});

// Use alongside built-in factories
const agent = createMultiProviderAgent({
  id: 'companion',
  defaultProviderId: 'openai',
  providers: [
    openAI({ apiKey: '...', models: ['gpt-4o'] }),
    myProvider({ apiKey: '...', models: ['my-model'] }),
  ],
});
```

Static metadata (`factory.id`, `factory.kind`, `factory.schema`, `factory.capabilities`) is accessible without calling the factory. `agents_discover` automatically includes `displayName`, `description`, and `capabilities` for custom providers.

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

## Backpressure

`maxConcurrentRequests` (default: 50) limits the number of in-flight tool handler calls. When the limit is reached, new requests are rejected with a retryable `BridgeError.transport('Server overloaded')`.

## Input size validation

- `maxPromptBytes` (default: 1,048,576 / 1 MiB) — maximum prompt size in bytes
- `maxMetadataBytes` (default: 65,536 / 64 KiB) — maximum metadata size in bytes (JSON-serialized)

## Session limits

The `InProcessExecutor` enforces a configurable `maxSessions` limit (default: 100). Sessions also have:

- **Session TTL** (`sessionTtlMs`, default: 3,600,000 / 1 hour) — maximum session lifetime
- **Idle timeout** (`sessionIdleMs`, default: 600,000 / 10 minutes) — maximum idle time before expiry

## RuntimeParams

### Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `model` | `string` | — | Model identifier |
| `temperature` | `number` | 0–2 | Sampling temperature |
| `maxTokens` | `number` | positive int | Max tokens to generate |
| `topP` | `number` | 0–1 | Nucleus sampling |
| `topK` | `number` | positive int | Top-K sampling |
| `stopSequences` | `string[]` | — | Stop sequences |
| `systemPrompt` | `string` | — | System prompt override |
| `providerSpecific` | `Record<string, unknown>` | — | Provider-native parameters |

### Merge priority

```
ProviderConfig.defaults  <  session metadata.runtimeParams  <  prompt-level runtimeParams
```

Only defined (non-`undefined`) fields from higher-priority layers override lower ones. `providerSpecific` is shallow-merged across all layers.

## Peer dependencies

Provider SDKs are peer/optional dependencies. Install only the SDKs you need:

```bash
npm install openai              # OpenAI
npm install @anthropic-ai/sdk   # Anthropic
npm install @google/generative-ai  # Google Gemini
```

If a provider SDK is not installed, the factory throws `BridgeError.config` with an installation instruction.

## CLI entry point

The CLI (`src/cli/server.ts`) is a reference/diagnostics server with no agents. It starts the MCP server and warns on stderr. Use `bridge_health` and `agents_discover` for diagnostics. For actual delegation, create your own entry point with `server.register()` before `server.start()`.

## Low-level API (class-based, deprecated)

The class-based API (`new OpenAIProvider(config)`, `new ProviderRegistry()`, manual wiring) still works but is deprecated. Use the Factory API above instead.

```typescript
// ⚠️ Deprecated — use openAI(), anthropic(), gemini() factories instead
import { OpenAIProvider, ProviderRegistry, MultiProviderCompanionAgent } from '@stdiobus/mcp-agentic';

const registry = new ProviderRegistry();
registry.register(new OpenAIProvider({
  credentials: { apiKey: process.env.OPENAI_API_KEY ?? '' },
  models: ['gpt-4o'],
}));

const agent = new MultiProviderCompanionAgent({
  id: 'companion',
  defaultProviderId: 'openai',
  registry,
});
```
