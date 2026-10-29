---
inclusion: auto
name: streaming
description: "Concurrent streaming for AWS Transform orchestrators and subagents: on by default for scaffolded agents, an SDK-level switch (StreamingConfig, the AG-UI/A2A stream, the subagent relay tools)"
---

# Streaming

AWS Transform agents answer in two ways. In a **buffered** turn the agent runs to completion and the
final answer is persisted and delivered. With **streaming** the agent's turn is emitted live as a
stream of events (reasoning, tool calls, text) while it runs, and several users of the same
orchestrator can have their turns run concurrently.

At the SDK level streaming is off until you pass a `StreamingConfig`; this power scaffolds new agents
with it on (below). It stays a switch: you can turn it off for a simple request/response agent, and
then nothing in this file applies and the agent behaves exactly as a buffered agent.

## When to turn it off

Keep streaming on (the default) when users should see the answer appear as it is produced, or when
one orchestrator serves several users at once. Turn it off only for a simple request/response agent
that wants neither — the buffered path needs none of the concurrency rules below. If you turn it
off, also set `capabilities.streaming: false` on the agent card (see the caveat below); the two must
agree.

## Enabling it

Pass a `StreamingConfig` to `AgentRuntimeServer`. With no `StreamingConfig` the server does not
stream, and a `message/stream` request returns HTTP 404 / JSON-RPC `-32601`, as before streaming
existed.

```python
from agent_builder_sdk.server.agent_runtime_server import AgentRuntimeServer
from agent_builder_sdk.streaming import StreamingConfig

server = AgentRuntimeServer(
    agent_factory=agent_factory,
    delayed_timeout=3600,
    streaming_config=StreamingConfig(),   # opt in
)
server.start()
```

A scaffolded agent enables streaming in its own entry point (the `StreamingConfig()` above), so the
Dockerfile `ENTRYPOINT` needs no change — do not add a `--concurrent-streaming` flag there. That
flag exists only on the SDK's sample `simple_cli_agent_core.py` (which also takes
`--emit-reasoning/--no-emit-reasoning` and `--emit-tool-calls/--no-emit-tool-calls`); it applies
only if your `ENTRYPOINT` runs that sample module directly instead of your own entry point.

**The agent card flag must match the server.** AWS Transform decides whether to stream to an agent
from its registered agent card's `capabilities.streaming`. Set it `true` only when the server
actually runs the streaming path (a `StreamingConfig` is passed, as above). The two must agree:

- card `true` + server has `StreamingConfig` → streaming works (the scaffolding default).
- card `false` (or absent) + no `StreamingConfig` → buffered, as before (a valid buffered-only agent).
- card `true` but server has **no** `StreamingConfig` → the platform streams to an agent that
  answers `message/stream` with HTTP 404, so the turn fails. Do not ship this combination.
- card `false` but server has `StreamingConfig` → the platform never streams; users only get
  buffered answers even though the server could stream.

See `agent-registration.md` for where this flag lives in the card.

## How it works

Strands runs one invocation at a time per `Agent`, so with streaming on the server keeps a pool with
one agent per source (a user, or another agent that streams to yours). Agents are built on first use
and evicted after an idle TTL.

- Each pooled agent builds its **own** model client from your factory. The MCP client, the
  conversation repository, and the memory manager are **shared**, so a user's buffered and streamed
  turns see the same history.
- A synchronous factory is run on a worker thread, one build at a time, so building a new user's
  agent does not stall live streams.

## Requirements for your factory

Your agent factory must accept and forward `conversation_repository` and `memory_manager`, so the
pooled agents share one history and memory store. The server checks this at startup.

```python
def agent_factory(mcp_client, storage_dir, **kwargs):
    return create_default_async_orchestrator(
        mcp_client=mcp_client,
        storage_dir=storage_dir,
        system_prompt=...,
        conversation_repository=kwargs.get("conversation_repository"),
        memory_manager=kwargs.get("memory_manager"),
    )
```

## Concurrency contract (important)

With streaming on, several users' turns run concurrently on one event loop. Tools and hooks MUST NOT
keep per-request state in module-level or class-level mutable globals — that state would leak between
users. Use a `contextvars.ContextVar`, or the per-request `ToolContext` / `invocation_state`,
instead.

## Subagents

A subagent can stream too, but only an async subagent is `StreamingCapable`: build it with
`create_default_async_subagent` (the sample `simple_subagent_cli.py` does this under
`--concurrent-streaming`). The subagent's own server must also be given a `StreamingConfig` and its
agent card must set `capabilities.streaming: true`; otherwise the agentic API's ConverseStream
rejects the relay with `ValidationException: Streaming is not supported for the requested agent`. An
orchestrator reaches a streaming subagent through one of two opt-in tools, added via `custom_tools`:

- `send_message_to_subagent_and_relay` — streams the subagent's answer to the user **as the
  orchestrator's own final answer**, and ends the orchestrator's turn. Use it when the subagent's
  answer is exactly what the user should get and the orchestrator has nothing to add.
- `stream_message_to_subagent` — returns the subagent's answer (its last model cycle) to the
  orchestrator without streaming it to the user, so the orchestrator can reason over it and keep
  working. Like `send_message_to_subagent`, but streamed under the hood.

## Interrupted turns

A streamed turn that is cut short (client disconnect, the turn's time budget, a crash) is closed out
when the conversation is next loaded: the unanswered user message gets a placeholder reply so the
next turn answers its own prompt, and a turn ended by a terminating tool keeps that tool's response
as the reply. You do not need to handle this yourself; it keeps the stored history valid for the
next turn.
