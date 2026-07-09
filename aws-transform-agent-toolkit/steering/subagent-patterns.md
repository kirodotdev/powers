---
inclusion: auto
name: subagent-patterns
description: "Guidance for building or updating subagents"
---

# Building Subagents

## What is a Subagent?

A subagent performs specialized, focused tasks within an orchestrator's workflow. It responds to A2A messages from orchestrators, collects user input via HITL AutoForms, processes data with domain-specific tools, and reports results back. Each subagent instance processes exactly one message.

## How to Build a Subagent

### Step 1: Understand the Subagent Base Class

Your subagent will extend `AsyncBaseSubagent`. Key points:
- Use `AsyncBaseSubagent` (not the synchronous version)
- Provide a focused `system_prompt` for the specific task
- Keep implementation simple and stateless
- **CRITICAL**: The subagent class MUST be defined inside `agent_factory()` — module-level subclasses hang in production containers. See Step 4 for the full pattern.

### Step 2: Configure System Prompt

The system prompt defines your subagent's specific task:

```python
system_prompt = """You are a specialized subagent for analyzing AWS infrastructure configurations.

Your specific task:
- Parse infrastructure configuration files (JSON, YAML, Terraform)
- Identify security vulnerabilities and misconfigurations
- Return structured analysis results

Constraints:
- Process one configuration at a time
- Return results in JSON format
- Do not maintain conversation history
"""
```

**Best Practices**:
- Be very specific about the single task
- Define input/output formats clearly
- Emphasize stateless operation
- Keep scope narrow and focused

### Step 3: Create Custom Tools (Optional)

Define specialized tools for your subagent's task:

```python
# custom_subagent_tools.py
from strands.tools import tool


@tool
def parse_terraform_config(config: str) -> dict:
    """Parse Terraform configuration and extract resource definitions.
    
    Args:
        config: Terraform configuration as string
        
    Returns:
        Dictionary with parsed resources and their properties
    """
    # Your parsing logic here
    return {
        "resources": ["aws_instance", "aws_s3_bucket"],
        "count": 2
    }


@tool
def validate_security_rules(rules: list) -> dict:
    """Validate security group rules against best practices.
    
    Args:
        rules: List of security group rules
        
    Returns:
        Validation results with issues found
    """
    return {
        "valid": True,
        "issues": [],
        "recommendations": ["Restrict SSH to specific IPs"]
    }
```

**Tool Guidelines**:
- Keep tools focused on the subagent's specific domain
- Ensure tools are stateless (no side effects)
- Return structured data for easy processing
- Include comprehensive docstrings

### Step 4: Create Your Entry Point

Use `AgentRuntimeServer` with `delayed_timeout=3600` (NOT `StatelessAgentRuntimeServer` — it has a hard 28s timeout that kills HITL polling and long-running tools):

```python
# my_subagent_cli.py
import argparse
import logging
from agent_builder_sdk.server.agent_runtime_server import AgentRuntimeServer

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
        from agent_builder_sdk.base_subagent.base_subagent import AsyncBaseSubagent

        # Define subagent class INSIDE agent_factory (module-level hangs in containers)
        class MySubagent(AsyncBaseSubagent):
            pass

        return MySubagent(
            system_prompt="You are a specialized subagent for infrastructure analysis...",
            mcp_clients=[mcp_client] if mcp_client is not None else None,
            region_name="us-east-1",
            model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        )

    logger.info("Starting Agent Runtime Server...")
    server = AgentRuntimeServer(
        agent_factory=agent_factory,
        host=args.host,
        port=args.port,
        binary_location=args.binary_location,
        delayed_timeout=3600,
    )
    
    # This will set up everything and run the server
    server.start()


if __name__ == "__main__":
    main()
```

**Key Features**:
- **Queue-based server**: Acks after 28s, continues processing in background for up to `delayed_timeout`
- **Class inside factory**: Avoids module-level subclass hang in production containers
- **Agent factory pattern**: Pluggable agent creation
- **Compatible protocols**: Supports both Bedrock AgentCore and AWS Transform compute service endpoints

#### Custom Agent Factory

For more control, create a custom agent factory with custom tools:

```python
from my_custom_subagent.custom_tools import parse_terraform_config, validate_security_rules


def agent_factory(mcp_client, storage_dir=None):
    """Create custom subagent with specific tools and configuration."""
    from agent_builder_sdk.base_subagent.base_subagent import AsyncBaseSubagent
    
    class MySubagent(AsyncBaseSubagent):
        pass

    return MySubagent(
        system_prompt="You are a specialized infrastructure analysis subagent...",
        mcp_clients=[mcp_client] if mcp_client is not None else None,
        region_name="us-east-1",
        custom_tools=[parse_terraform_config, validate_security_rules],
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    )
```

### Step 5: Local Testing

Set up environment variables and test your subagent:

```bash
# Required environment variables
export WORKSPACE_ID=your-workspace-id
export JOB_ID=your-job-id
export AGENT_INSTANCE_ID=your-agent-instance-id
export AUTHORIZATION_TOKEN=your-token
export QT_AGENTIC_API_ENDPOINT=https://iad.prod.agenticapi.elastic-gumby.ai.aws.dev
export AWS_REGION=us-east-1

# Start local server for API testing
python src/my_custom_subagent/my_subagent_cli.py \
  --binary-location agent-builder-agentic-mcp
```

## Orchestrator vs Subagent Decision Guide

| Feature | Orchestrator | Subagent |
|---------|-------------|----------|
| **Base Class** | `AsyncBaseOrchestrator` | `AsyncBaseSubagent` |
| **Server** | AgentRuntimeServer + delayed_timeout | AgentRuntimeServer + delayed_timeout |
| **Visibility** | PUBLIC (in webapp chat) | RESTRICTED (orchestrator-invoked) |
| **Status Management** | Automatic (queue manages) | Manual (must set COMPLETED/FAILED) |
| **State** | Stateful (episodic memory) | Stateless (no memory between requests) |
| **MCP Client** | Optional (disable if A2A-only) | Optional (disable if using @tool functions) |

**Use Orchestrator when:** coordinating multiple agents, maintaining conversation context, building user-facing agents.
**Use Subagent when:** performing focused tasks, responding only to orchestrator requests, no conversation history needed.

## Project Structure

```
my-subagent/
├── __init__.py
├── subagent_cli.py          # Entry point + subagent class (INSIDE agent_factory)
├── agent_client.py          # HITL + artifact client (AgenticApiHelper subclass)
├── tools/
│   ├── __init__.py
│   ├── custom_tools.py      # CUSTOMIZE: domain-specific tools
│   ├── hitl_tools.py        # HITL AutoForm tools
│   ├── s3_tools.py          # Direct S3 upload/download
│   └── connector_s3_tools.py # Connector-aware S3 tools (optional)
├── prompts/
│   └── subagent_prompt.md   # CUSTOMIZE: domain-specific system prompt
├── requirements.txt
├── Dockerfile
└── .bedrock_agentcore.yaml
```

## Dockerfile (REQUIRED — do NOT scaffold from scratch)

**You MUST use the canonical Dockerfile template from [dockerfile-subagent.md](./dockerfile-subagent.md).** Copy its contents verbatim as your `Dockerfile`. Adapt the `COPY` source lines and `ENTRYPOINT` to match your source layout.

A minimal Dockerfile will fail on first invocation — see [orchestrator-patterns.md](./orchestrator-patterns.md#dockerfile-required--do-not-scaffold-from-scratch) for the full explanation of the two bugs this prevents.

## Architecture Decisions (must-know)

### CRITICAL: AgentRuntimeServer, NOT StatelessAgentRuntimeServer

`StatelessAgentRuntimeServer` has a hard 28s `asyncio.timeout` around the entire `process_message` call. Any tool blocking longer (like `poll_hitl_response` waiting for user input) gets killed silently. Use `AgentRuntimeServer` with `delayed_timeout=3600` — it acks after 28s and continues processing in the background.

### Subagent Class Defined INSIDE agent_factory

Module-level subclasses of `AsyncBaseSubagent` hang in production containers. Always define the subagent class inside the `agent_factory()` function:

```python
def agent_factory(mcp_client, storage_dir=None):
    class MySubagent(AsyncBaseSubagent):
        async def process_message_async(self, request):
            # ... handle message
            pass
    return MySubagent(mcp_clients=[mcp_client] if mcp_client else None)
```

### process_message_async Override

The SDK queue handler passes `ProcessMessageRequest` objects, but the base class expects `str`. The override must:
1. Handle `ProcessMessageRequest` type (extract `.message`)
2. Extract text from A2A dict format (`parts[0].text`)
3. Call `self._process_message(message)` with the extracted string
4. Manually set COMPLETED or FAILED via `get_agent_instance_manager().update_status()` with `agentOutput={"serializedPayload": json.dumps(...)}`

The override must extract the text and set final status:

```python
async def process_message_async(self, request):
    if hasattr(request, 'message'):
        msg = request.message
    else:
        msg = request
    if isinstance(msg, dict):
        text = msg.get("parts", [{}])[0].get("text", str(msg))
    else:
        text = str(msg)
    try:
        result = await self._process_message(text)
        self.get_agent_instance_manager().update_status(
            "COMPLETED", agentOutput={"serializedPayload": json.dumps({"response": result})}
        )
    except Exception as e:
        self.get_agent_instance_manager().update_status("FAILED", statusReason=str(e))
```

### HITL AutoForm Pattern

The orchestrator passes `step_id` in the A2A message. The subagent:
1. Extracts `step_id` from the message text
2. Calls `create_hitl_autoform(step_id, title, description, fields)` — uploads form schema, creates task, starts it, sets step to `PENDING_HUMAN_INPUT`
3. Calls `poll_hitl_response(hitl_task_id)` — polls until SUBMITTED, downloads response artifact, closes task
4. Processes the user's input with domain-specific tools

The `description` field in HITL tasks has a max length of 1024 characters — truncate before passing.

### S3 Access: Connector First, Direct Fallback

Always register both `connector_s3_tools` AND `s3_tools`. The system prompt must instruct the LLM to:
1. Call `list_s3_connectors()` first
2. Use `download_from_connector`/`upload_to_connector` if connectors available
3. Fall back to `download_s3_file`/`upload_s3_file` if connector fails (auth error) or none available

See troubleshooting #29 for known connector auth issues.

### mcp_clients Must Be Plural (List) or None

```python
# WRONG
MySubagent(mcp_client=mcp_client)
# CORRECT
MySubagent(mcp_clients=[mcp_client] if mcp_client else None)
```

### Cross-Region Inference Profile Required

Use `model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"` — bare model IDs fail with `ValidationException`.

## Common Errors Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `Agent processing timed out after 28 seconds` | Using `StatelessAgentRuntimeServer` | Switch to `AgentRuntimeServer` with `delayed_timeout=3600` |
| Never reaches COMPLETED | Missing `update_status()` | Set COMPLETED with `agentOutput` in `process_message_async` |
| Orchestrator can't get response | Bad `agentOutput` format | Include `serializedPayload` as JSON string |
| Message processing fails | A2A format not extracted | Handle `ProcessMessageRequest` + dict in override |
| Constructor hangs in container | Module-level subclass | Define class inside `agent_factory()` |
| `unexpected keyword argument 'mcp_client'` | Singular not plural | Use `mcp_clients=[client]` or `None` |
| HITL display_report fails | Description exceeds 1024 chars | Truncate to < 1024 chars |
| `TerminalResourceException: status is not valid: COMPLETED` | Container reuse (AWS Transform bug) | Re-run job for fresh container |

## Next Steps

- Build orchestrator: see `orchestrator-patterns.md`
- Deploy: see `deploy-agent-workflow.md`
- Register: see `agent-registration.md`
- Troubleshoot: see `troubleshooting.md`
