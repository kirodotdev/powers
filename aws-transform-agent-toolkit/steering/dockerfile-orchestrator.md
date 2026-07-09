# Orchestrator Dockerfile Template

**MANDATORY** — use this Dockerfile verbatim when scaffolding an orchestrator agent. Do NOT generate a Dockerfile from scratch. A minimal Dockerfile will fail on first invocation with two separate bugs:

1. **Missing botocore service models** — agent init fails with `Unknown service: 'transformagenticservice'`. The SDK registers these models on the host during install, but they must also be registered inside the container.

2. **Missing MCP server shim** — `AgentRuntimeServer` spawns the Agentic MCP server from the hardcoded path `/home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp`. Without the shim, the runtime fails with `FileNotFoundError` and the agent is stuck in STARTING.

Adapt the `COPY src/orchestrator/ .` line and `ENTRYPOINT` to match your source layout. Everything else must remain as-is.

**Note on the base image**: `public.ecr.aws/docker/library/python` is the AWS-operated public mirror of Docker Hub's official Python image — equivalent bits, no AWS account required to pull.

```dockerfile
FROM --platform=linux/arm64 public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install AWS Transform SDK from PyPI
RUN pip install --no-cache-dir \
    agent-builder-sdk-aws-transform \
    agent-builder-agentic-mcp-aws-transform \
    agent-builder-types-aws-transform \
    agent-builder-mcp-client-aws-transform

# Register botocore service models (REQUIRED for Agentic API and Agent Registry API)
RUN pip install --no-cache-dir awscli && \
    SDK_MODELS=$(python -c "from importlib.resources import files; print(files('agent_builder_sdk').joinpath('botocore_models'))") && \
    aws configure add-model --service-name atxagentregistryexternal \
      --service-model "file://${SDK_MODELS}/atxagentregistryexternal/2022-07-26/service-2.json" && \
    aws configure add-model --service-name transformagenticservice \
      --service-model "file://${SDK_MODELS}/transformagenticservice/2018-05-10/service-2.json"

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create MCP server wrapper binary
RUN mkdir -p /home/amazon/AgentBuilderAgenticMCP/bin && \
    printf '#!/bin/bash\npython -m agent_builder_agentic_mcp "$@"\n' > /home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp && \
    chmod +x /home/amazon/AgentBuilderAgenticMCP/bin/agent-builder-agentic-mcp

# Copy orchestrator source
COPY src/orchestrator/ .

# Create storage directories
RUN mkdir -p /tmp/agent_queue /tmp/orchestrator_agent

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

ENTRYPOINT ["python", "app.py"]
```
