# AgentCore Memory Integration Guide

## Overview

AgentCore Memory stores conversation events (short-term memory) and, with strategies, extracts long-term records such as facts, summaries, and preferences. With the AgentCore CLI, a memory is a project resource: `agentcore add memory` declares it in `agentcore.json`, `agentcore deploy` creates it, and the deployed runtimes receive its ID in an environment variable.

Projects created from `agent-python-strands`, `agent-typescript-strands`, `a2a-python-strands`, or `agui-python-strands` already include a memory named `agentMemory` with semantic and episodic strategies, wired into `memory/session.py`. For those projects, skip to Step 4 (deploy) unless the user wants a different memory.

## Step 1: Add the Memory

```bash
# Short-term memory only (events, no extraction)
agentcore add memory --name supportMemory

# With long-term strategies
agentcore add memory --name supportMemory --strategies SEMANTIC,SUMMARIZATION
```

Options:

- `--strategies`: comma-separated strategy types: `SEMANTIC`, `SUMMARIZATION`, `USER_PREFERENCE`, `EPISODIC`. A JSON `strategies[]` array (as stored in `agentcore.json`) is also accepted for custom namespaces.
- `--event-expiry-duration`: days to keep raw events, 3 to 365 (default 30).
- `--description`, `--encryption-key-arn`, `--execution-role-arn`, `--tags`: see `agentcore add memory --help`.

Each strategy type gets a default namespace:

| Strategy | Default namespace |
| --- | --- |
| `SEMANTIC` | `/users/{actorId}/facts` |
| `SUMMARIZATION` | `/summaries/{actorId}/{sessionId}` |
| `USER_PREFERENCE` | `/users/{actorId}/preferences` |
| `EPISODIC` | `/episodes/{actorId}/{sessionId}` (reflections in `/episodes/{actorId}`) |

Memory is not available in the China regions.

## Step 2: Add the Dependency

The Strands integration ships with the AgentCore SDK. In the runtime's `pyproject.toml`:

```toml
dependencies = [
    "aws-opentelemetry-distro ~= 0.21.0",
    "bedrock-agentcore[strands-agents] >= 1.18.1, < 2.0.0",
    "strands-agents >= 1.62.0, < 2.0.0",
]
```

Run `uv sync` in the runtime folder after editing it.

## Step 3: Use the Memory in the Agent

On deploy, every runtime in the project receives `MEMORY_<NAME>_ID` and `MEMORY_<NAME>_ARN`, where `<NAME>` is the memory name in upper case. A memory named `supportMemory` arrives as `MEMORY_SUPPORTMEMORY_ID`. Read it from the environment and run without memory when it is missing, so the agent still works locally and before the first deploy.

```python
import os

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

MEMORY_ID = os.environ.get("MEMORY_SUPPORTMEMORY_ID")
REGION = os.environ.get("AWS_REGION")

app = BedrockAgentCoreApp()


def memory_session_manager(session_id: str, actor_id: str):
    if not MEMORY_ID:
        return None
    return AgentCoreMemorySessionManager(
        AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            # Keys are the strategy namespaces with the actor and session filled in.
            retrieval_config={
                f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.0),
                f"/summaries/{actor_id}/{session_id}": RetrievalConfig(top_k=1, relevance_score=0.0),
            },
        ),
        REGION,
    )


@app.entrypoint
def invoke(payload, context):
    session_id = context.session_id or "default-session"
    actor_id = payload.get("actorId", "default")
    agent = Agent(
        system_prompt="You are a helpful assistant.",
        session_manager=memory_session_manager(session_id, actor_id),
    )
    result = agent(payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
```

Points to keep:

- The session ID comes from the runtime request (`context.session_id`, set from the `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` header), not from the payload.
- The actor ID identifies the end user. Take it from the payload or the caller's identity, and use a stable value per user.
- Leave out `retrieval_config` for short-term memory only. Only list namespaces of strategies the memory has.
- `relevance_score=0.0` returns the `top_k` records without score filtering. Raise it to filter out weak matches.

## Step 4: Deploy and Test

Confirm with the user before deploying.

```bash
agentcore deploy
agentcore invoke --runtime agent --payload '{"prompt": "My name is Alice and I like pizza", "actorId": "alice"}'
```

`invoke` prints the `runtime-session-id` it used. Pass it back to continue the same session:

```bash
agentcore invoke --runtime agent --session-id <runtime-session-id> \
  --payload '{"prompt": "What is my name?", "actorId": "alice"}'
```

To check long-term memory, ask from a new session (omit `--session-id`) with the same `actorId`. Extraction runs in the background, so long-term records can take a short while to appear.

## Testing Memory Locally

`agentcore dev` does not inject `MEMORY_<NAME>_ID`, so a local run has no memory by default. After the first deploy, get the memory ID and add it to `agentcore/.env.local`, which `agentcore dev` loads:

```bash
agentcore memory list
echo 'MEMORY_SUPPORTMEMORY_ID=<memory-id>' >> agentcore/.env.local
```

The local agent then reads and writes the deployed memory with the developer's AWS credentials.

## Inspect Memory Contents

These commands call the AgentCore APIs directly and work with or without a project:

```bash
agentcore memory list
agentcore memory get --id <memory-id>
agentcore memory actor list --id <memory-id>
agentcore memory session list --id <memory-id> --actor-id alice
agentcore memory event list --id <memory-id> --actor-id alice --session-id <session-id> --include-payloads
agentcore memory record list --id <memory-id> --namespace /users/alice/facts
```

The MCP server offers the same reads (`memory_list`, `memory_list_events`, `memory_list_records`, `memory_retrieve_records`) and a reference guide (`get_memory_guide`).

## Change or Remove a Memory

`agentcore add memory` does not change an existing memory. To change its strategies or expiry, edit that memory's entry in `agentcore/agentcore.json` (only with the user's agreement) and deploy.

Removing a memory from the project and deploying deletes the memory with all its events and records. Confirm with the user first.

```bash
agentcore remove memory --name supportMemory
agentcore deploy
```

## Troubleshooting

**Nothing is remembered between calls:** check that the calls share the same `--session-id` (short-term) or `actorId` (long-term), that the code reads the right `MEMORY_<NAME>_ID`, and that the project was deployed after the memory was added. Locally, check `agentcore/.env.local`.

**No long-term records:** the memory needs at least one strategy, and extraction is asynchronous. Check `agentcore memory record list` after a short wait, and make sure `retrieval_config` uses the same namespaces as the strategies.

**`unrecognized memory strategy`:** use one of `SEMANTIC`, `SUMMARIZATION`, `USER_PREFERENCE`, `EPISODIC`.

**Errors in the deployed agent:** read them with `agentcore logs runtime --name <runtime> --since 15m`.

## Resources

- [AgentCore Memory documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Strands session management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/session-management/)
