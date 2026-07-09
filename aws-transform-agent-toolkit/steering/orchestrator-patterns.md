---
inclusion: auto
name: orchestrator-patterns
description: "Guidance for creating or modifying orchestrator agents"
---

# Building Orchestrator Agents

## What is an Orchestrator Agent?

An orchestrator coordinates multiple subagents to accomplish complex workflows. It creates job plans visible in the AWS Transform webapp, executes steps in background threads (no timeout ceiling), sends progress messages via ATX_CHAT, and handles ad-hoc queries during execution. Orchestrators follow a 3-phase workflow: Negotiate, Confirm, Execute.

## How to Build an Orchestrator

### Step 1: Create Your Orchestrator Class

```python
# In your agent package (e.g., MyCustomAgent)
from agent_builder_sdk.orchestrator_strands.base_orchestrator import AsyncBaseOrchestrator


class MyCustomOrchestrator(AsyncBaseOrchestrator):
    """Your custom orchestrator implementation."""

    def __init__(self, **kwargs):
        super().__init__(
            system_prompt="You are a specialized orchestrator for...",
            **kwargs
        )
        # Add your custom tools, hooks, conversation implementation
```

**Key Points**:
- Extend `AsyncBaseOrchestrator` (not the synchronous version)
- Provide a clear `system_prompt` that defines the agent's role
- Use `**kwargs` to pass through configuration options

### Step 2: Configure System Prompt

The system prompt defines your agent's behavior and capabilities:

```python
system_prompt = """You are a specialized orchestrator for AWS infrastructure transformation.

Your responsibilities:
- Analyze customer infrastructure requirements
- Create detailed transformation plans
- Coordinate with subagents for specific tasks
- Provide progress updates to customers

Available capabilities:
- Access to AWS Transform APIs via MCP
- Memory management for conversation context
- Job plan creation and management
"""
```

**Best Practices**:
- Be specific about the agent's domain and responsibilities
- List available capabilities and tools
- Define expected behavior and constraints

### Step 3: Create Custom Tools (Optional)

Define domain-specific tools using Strands decorators:

```python
# custom_tools.py
from strands.tools import tool


@tool
def analyze_infrastructure(config: str) -> dict:
    """Analyze infrastructure configuration and return recommendations.
    
    Args:
        config: Infrastructure configuration in JSON or YAML format
        
    Returns:
        Dictionary with analysis results and recommendations
    """
    # Your analysis logic here
    return {
        "status": "analyzed",
        "recommendations": ["Use t3.medium instances", "Enable auto-scaling"]
    }


@tool
def create_migration_plan(source: str, target: str) -> str:
    """Create a migration plan from source to target infrastructure.
    
    Args:
        source: Source infrastructure identifier
        target: Target infrastructure identifier
        
    Returns:
        Migration plan as formatted string
    """
    return f"Migration plan from {source} to {target}:\n1. Assess current state\n2. Plan migration\n3. Execute migration"
```

**Tool Guidelines**:
- Use clear, descriptive function names
- Include comprehensive docstrings (LLM reads these)
- Specify parameter types and return types
- Keep tools focused on single responsibilities

### Step 4: Create Your Entry Point

#### Option A: Using AgentRuntimeServer (Recommended)

Use the simplified `AgentRuntimeServer` with a custom agent factory:

```python
# my_agent_cli.py
import argparse
import logging
from agent_builder_sdk.server.agent_runtime_server import AgentRuntimeServer
from agent_builder_sdk.agent_factory import create_default_orchestrator
from agent_builder_sdk.utils import get_prompt_with_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(description="Run Agent Runtime Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind server to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind server to")
    parser.add_argument(
        "--storage-dir", 
        default="/tmp/orchestrator_agent", 
        help="Storage directory for agent data (queue, responses, checkpoints)"
    )
    parser.add_argument(
        "--binary-location",
        default="/home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp",
        help="Path to the agentic MCP server binary",
    )
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Create agent factory with default configuration
    def agent_factory(mcp_client, storage_dir=None):
        return create_default_orchestrator(
            mcp_client=mcp_client,
            storage_dir=storage_dir,
            system_prompt=get_prompt_with_name("test_orchestrator_prompt"),
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

    logger.info("Starting Agent Runtime Server...")
    server = AgentRuntimeServer(
        agent_factory=agent_factory,
        host=args.host,
        port=args.port,
        binary_location=args.binary_location,
        storage_dir=args.storage_dir,
        delayed_timeout=3600,
    )
    
    # This will set up everything and run the server
    server.start()


if __name__ == "__main__":
    main()
```

**Key Features**:
- **Simplified interface**: Single unified server
- **Agent factory pattern**: Pluggable agent creation
- **Compatible protocols**: Supports both Bedrock AgentCore and AWS Transform compute service endpoints
- **Automatic handling**: JSON-RPC 2.0 protocol, context initialization, session management

#### Option B: Custom Agent Factory

For more control, create a custom agent factory:

```python
from my_custom_agent.custom_tools import analyze_infrastructure, create_migration_plan


def agent_factory(mcp_client, storage_dir=None):
    """Create custom orchestrator with specific tools and configuration."""
    from agent_builder_sdk.orchestrator_strands.base_orchestrator import AsyncBaseOrchestrator
    
    # Create orchestrator with custom tools
    orchestrator = AsyncBaseOrchestrator(
        system_prompt="You are a specialized AWS infrastructure transformation orchestrator...",
        mcp_clients=[mcp_client] if mcp_client is not None else None,
        region_name="us-east-1",
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        custom_tools=[analyze_infrastructure, create_migration_plan],
    )
    
    return orchestrator
```

### Step 5: Local Testing

Set up environment variables and test your agent:

```bash
# Required environment variables
export WORKSPACE_ID=your-workspace-id
export JOB_ID=your-job-id
export AGENT_INSTANCE_ID=your-agent-instance-id
export AUTHORIZATION_TOKEN=your-token
export QT_AGENTIC_API_ENDPOINT=https://iad.prod.agenticapi.elastic-gumby.ai.aws.dev
export AWS_REGION=us-east-1

# Console mode: Talk directly to the agent
python src/my_custom_agent/my_agent_cli.py \
  --storage-dir . \
  --binary-location agent-builder-agentic-mcp

# Server mode: Start local server for API testing
python src/my_custom_agent/my_agent_cli.py \
  --storage-dir . \
  --binary-location agent-builder-agentic-mcp \
  --queue-storage-path .
```

## Project Structure

```
my-orchestrator/
├── __init__.py
├── orchestrator_cli.py        # Entry point (argparse + AgentRuntimeServer)
├── orchestrator.py            # Main class (all tools defined here)
├── agent_client.py            # API client (AgenticApiHelper subclass)
├── tools/
│   └── orchestrator_tools.py  # CUSTOMIZE: discover_subagents tool
├── prompts/
│   └── orchestrator_prompt.md # CUSTOMIZE: 3-phase workflow prompt
├── requirements.txt
├── Dockerfile
└── .bedrock_agentcore.yaml
```

## Dockerfile (REQUIRED — do NOT scaffold from scratch)

**You MUST use the canonical Dockerfile template from [dockerfile-orchestrator.md](./dockerfile-orchestrator.md).** Copy its contents verbatim as your `Dockerfile`. Adapt the `COPY src/orchestrator/ .` line and `ENTRYPOINT` to match your source layout.

A minimal Dockerfile will fail on first invocation with two separate bugs that are extremely hard to debug:

1. **Missing botocore service models** → `Unknown service: 'transformagenticservice'` at agent init. Job stuck in STARTING.
2. **Missing MCP server shim** → `FileNotFoundError: '/home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp'`. Job stuck in STARTING.

Both require a full rebuild → new runtime → new version → re-register cycle to fix. The template already handles both correctly.

## Architecture Decisions (must-know)

### AgentRuntimeServer with delayed_timeout=3600

Orchestrators MUST use `AgentRuntimeServer` (NOT `StatelessAgentRuntimeServer`) with `delayed_timeout=3600`. The stateless server has a hard 28s asyncio timeout that kills long-running subagent coordination. `AgentRuntimeServer` has queue support built-in — it acks after 28s and continues processing in the background for up to `delayed_timeout` seconds.

```python
from agent_builder_sdk import AgentRuntimeServer

server = AgentRuntimeServer(agent_factory=agent_factory, delayed_timeout=3600)
server.start()
```

> **WARNING:** Do NOT pass `queue=True` — that parameter does not exist and will crash with `TypeError: __init__() got an unexpected keyword argument 'queue'`. Queue behavior is always enabled internally.

### mcp_clients Must Be Plural (List)

```python
# WRONG — will crash
MyOrchestrator(mcp_client=mcp_client)
# CORRECT — wrap in list, or None if A2A-only
MyOrchestrator(mcp_clients=[mcp_client] if mcp_client is not None else None)
```

### Background Execution via Daemon Thread

Running the full workflow synchronously exceeds `delayed_timeout`. The solution: `execute_plan()` spawns a `threading.Thread(daemon=True)` and returns immediately. The thread executes each step, polls with no timeout ceiling (exponential backoff), updates step statuses, and sends progress via ATX_CHAT. Python's GIL makes dict reads/writes atomic — no locks needed for shared `_execution_state`.

```
User Chat --> LLM (negotiate plan) --> create_job_plan --> user confirms
                                                              |
                                                        execute_plan()
                                                              |
                                              returns immediately: "Plan started"
                                                              |
                                                  +-----------v-----------+
                                                  |   Background Thread   |
                                                  |  for step in plan:    |
                                                  |    invoke subagent    |
                                                  |    send message       |
                                                  |    poll (no timeout)  |
                                                  |    update step status |
                                                  |    send ATX_CHAT msg  |
                                                  +-----------------------+
```

### execution_groups: Parallel + Sequential

Use `execution_groups` (list of dicts) for grouped parallel/sequential execution. Each dict in the list is a group — steps within the same dict run in parallel, groups run sequentially.

- Sequential: `[{"step-a": "agent-a"}, {"step-b": "agent-b"}]`
- Parallel: `[{"step-a": "agent-a", "step-b": "agent-b"}]`
- Mixed: `[{"step-a": "agent-a"}, {"step-b": "agent-b", "step-c": "agent-c"}]`

**NOTE:** Use `execution_groups` (list of dicts), NOT `step_agent_mapping` (flat dict). Do NOT simplify to a flat dict — that loses the parallel execution capability.

### Fire-and-Forget + Polling (A2A Communication)

The A2A `SendMessage` API has a ~25s internal timeout. If the subagent takes longer, the API returns error code `-32603` with HTTP 200. This is expected — the subagent is still processing. The pattern: send the message (fire-and-forget), immediately poll `get_agent_instance` until COMPLETED, then extract the response from `agentOutput.serializedPayload`.

### stepId vs stepLabel

`PutJobPlan` assigns its own step IDs. The `stepLabel` you send (e.g., `"analysis"`) is NOT the `stepId` the API uses. After calling `put_job_plan`, immediately call `list_job_plan_steps()` to get the real `stepId` values. Build a `stepLabel → stepId` mapping dict and use it for all subsequent `UpdateJobPlanStep` calls.

### Subagents Are Single-Use

Each subagent instance processes exactly one message then sets COMPLETED. Track completed instances via a `_completed_instances` set and block re-sends with a clear error.

### ATX_CHAT Messaging

`send_chat_message` sends progress messages to the webapp chat using `agent_instance_id="ATX_CHAT"` (special target, not a real instance). The required A2A format with `extensions` and `metadata` for `userSelection: "jobCreator"` is undocumented. The working format:

```python
message = {
    "role": "agent",
    "parts": [{"type": "TextPart", "text": progress_text}],
    "extensions": [json.dumps({"userSelection": "jobCreator"})],
    "metadata": {}
}
self.send_message(agent_instance_id="ATX_CHAT", params={"message": message})
```

### Cross-Region Inference Profile Required

Use `model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"` — bare model IDs fail with `ValidationException`.

## Common Errors Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `Package requires Python >=3.11` | Wrong Python in Dockerfile | Use `python:3.11-slim` base image |
| `ModuleNotFoundError: mypy_boto3_transformagenticservice` | Missing type stubs | `pip install agent-builder-types-aws-transform` |
| `Agent.__init__() got unexpected keyword argument 'mcp_client'` | Singular `mcp_client` | Use `mcp_clients=[client]` (plural, list) |
| `Missing required parameter: requestContext` | Using raw boto3 | Extend `AgenticApiHelper` |
| `SendMessage returned error code=-32603` | Normal — subagent took >25s | Expected; poll `get_agent_instance` |
| `ResourceNotFoundException` on `update_job_plan_step` | Using `stepLabel` not `stepId` | Use `stepId` from `list_job_plan_steps()` |
| `I was not able to generate a response on time` | Missing `delayed_timeout` | Set `delayed_timeout=3600` |
| `Distribution not found at: file:///app/...` | Deps not copied before pip | Fix Dockerfile copy order |
| `Unknown service: 'transformagenticservice'` | Missing botocore models in container | Use canonical Dockerfile from [dockerfile-orchestrator.md](./dockerfile-orchestrator.md) |
| `FileNotFoundError: '..agent-builder-agentic-mcp'` | Missing MCP shim in container | Use canonical Dockerfile from [dockerfile-orchestrator.md](./dockerfile-orchestrator.md) |
| `ValidationException: Invocation of model ID ...` | Bare model ID | Use `us.` prefix (cross-region profile) |
| `AttributeError: 'ClientSession' object has no attribute 'get_server_capabilities'` | MCP client issue | Use `mcp_clients=None` if A2A-only |

## Next Steps

- Build subagents: see `subagent-patterns.md`
- Deploy: see `deploy-agent-workflow.md`
- Register: see `agent-registration.md`
- Troubleshoot: see `troubleshooting.md`
