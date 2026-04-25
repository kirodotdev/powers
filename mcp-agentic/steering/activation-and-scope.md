# Activation and Scope

## When to use this power

Use the MCP Agentic power **only** when external agent delegation is actually required.

### Activate for:

- **External agent execution** — tasks that require specialized agents (in-process or worker-based)
- **Agent discovery** — finding available agents and their capabilities via `agents_discover`
- **Session-based delegation** — multi-step work that needs session continuity via `sessions_*` tools
- **One-shot delegation** — single tasks via `tasks_delegate`
- **Structured result collection** — retrieving formatted outputs from agents
- **Health checks** — verifying bridge readiness via `bridge_health`

### Do NOT activate for:

- **Purely local editing** — file modifications that the MCP client can handle directly
- **Direct reasoning** — analysis or planning that the MCP client can complete itself
- **Speculative orchestration** — multi-agent setups without a concrete task
- **Simple queries** — questions that don't require external agent capabilities
- **Configuration changes** — modifications to local settings or files

## Session continuity check

Before opening a new session, **always check** whether the user is continuing an existing delegated task:

1. **Review conversation history** — look for previous delegation operations
2. **Check for session references** — identify any active `sessionId` values
3. **Assess user intent** — determine if this is follow-up work
4. **Use existing session** — call `sessions_prompt` with the existing `sessionId` when continuity is intended

### Indicators of session continuity:

- User says "continue", "also", "now", "next", "then"
- Task is clearly related to previous delegation
- Same agent is referenced
- User expects context from previous interaction

### When to open a new session:

- User explicitly requests a new task
- Different agent or capability is needed
- Previous session was explicitly closed
- Task is unrelated to previous work
- Previous session has expired (TTL or idle timeout)

## Scope boundaries

This power handles **agent delegation and session management**. Specifically, it:

- Validates tool inputs via Zod schemas (prompt size, metadata size, required fields)
- Manages session lifecycle (create, prompt, status, close, cancel)
- Routes requests to the correct executor (in-process or worker)
- Enforces backpressure and input size limits
- Maps errors to MCP-compatible responses

It does NOT:

- Interpret prompt content or make decisions based on what the user asked
- Run inference, heuristics, or AI logic (that's the agent's job)
- Transform agent responses — results are passed through unchanged
- Implement ACP protocol logic — workers handle their own protocol

## Validation before activation

Before using this power, verify:

1. **Task requires external delegation** — cannot be completed by the MCP client alone
2. **Agent exists** — target capability is available (use `agents_discover`)
3. **Bridge is healthy** — use `bridge_health` if uncertain
4. **User intent is clear** — task requirements are well-defined

## Deactivation criteria

Stop using this power when:

- Task is complete and no follow-up is expected
- User explicitly requests to stop delegation
- All sessions have been closed
- Bridge becomes unavailable
- Task can be completed locally without delegation
