---
inclusion: auto
name: getting-started
description: "Getting started with AWS Transform or building your first agent"
---

# Getting Started with AWS Transform Agent Development

This guide helps you build your first AWS Transform agent.

## Prerequisites

Before starting, ensure you've completed the onboarding steps:

1. **Tools validated**: Python 3.11+, AWS CLI, finch/Docker
2. **SDK installed**: `pip install agent-builder-sdk-aws-transform`
3. **Hooks added**: Workspace validation hooks set up

**If you haven't done this yet**: The AWS Transform Agent Toolkit onboarding walks you through all installation steps. Kiro will guide you through tool validation, SDK installation, and hook setup when you first activate the power.

## What You Can Build

With AWS Transform, you create two types of agents:

- **Orchestrator Agents**: Coordinate complex workflows and manage multiple subagents
- **Subagents**: Handle specific, focused tasks within a workflow

## How to Use This Power

### Search → Read → Generate Workflow

MCP search tools are a **discovery layer** — they find what exists and where.
For code generation, always follow this workflow:

1. **Discover**: `keyword_search("BaseOrchestrator")` → find the class, get the `file` field from results
2. **Find** the installed package location:
   ```bash
   python3 -c "import agent_builder_sdk; print(agent_builder_sdk.__file__)"
   ```
3. **Grep** for the class or function:
   ```bash
   grep -r "class BaseOrchestrator" $(python3 -c "import agent_builder_sdk, os; print(os.path.dirname(agent_builder_sdk.__file__))")
   ```
4. **Read** the matched file for full signatures and docstrings
5. **Generate** code using the complete source — not the truncated preview

**NEVER generate code from search result snippets alone** — they are truncated previews.
Key classes like AsyncBaseOrchestrator and AsyncBaseSubagent are heavily truncated in
search results. Always read the full source via grep.

### Search AWS Transform Documentation

Ask Kiro to search the indexed documentation:
- "How do I create an orchestrator agent?"
- "What's the difference between orchestrator and subagent?"
- "How do I invoke a subagent?"

### Generate Agent Code

Ask Kiro to generate code from descriptions:
- "Create an orchestrator agent called CustomerSupportAgent that handles support tickets"
- "Create a subagent that analyzes code quality"

### Get Guidance on Specific Topics

Reference other steering files for detailed patterns:
- Creating orchestrators → See orchestrator-patterns.md
- Building subagents → See subagent-patterns.md
- Working with APIs → See api-reference.md
- Deploying agents → See deployment-pipeline-guide.md

## Key Concepts

### Agent Types

| Type | Purpose | Base Class |
|------|---------|------------|
| **Orchestrator** | Coordinate workflows, manage subagents | `AsyncBaseOrchestrator` |
| **Subagent** | Handle specific focused tasks | `AsyncBaseSubagent` |

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Transform                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │  Orchestrator Agent  │
              │  (Your Main Logic)   │
              └──────────────────────┘
                     │       │
            ┌────────┴───────┴────────┐
            ▼                          ▼
    ┌──────────────┐         ┌──────────────┐
    │  Subagent A  │         │  Subagent B  │
    │ (Specialized)│         │ (Specialized)│
    └──────────────┘         └──────────────┘
```

- **Orchestrator**: Receives requests from AWS Transform, coordinates workflow
- **Subagents**: Perform specialized tasks (code analysis, data processing, etc.)
- **Communication**: Via Agentic API (InvokeAgent operation)

## Quick Start Examples

### Example 1: Simple Orchestrator

Ask Kiro:
```
"Create an orchestrator that receives a customer question and returns an answer"
```

Kiro will generate:
- Flask app with `/invoke` endpoint
- AsyncBaseOrchestrator subclass
- Request/response handling
- Error handling patterns

### Example 2: Multi-Agent System

Ask Kiro:
```
"Create a code modernization orchestrator with two subagents:
one for code analysis and one for generating recommendations"
```

Kiro will generate:
- Orchestrator that coordinates both subagents
- Subagent invocation using Agentic API
- Job status polling
- Result aggregation

## Next Steps

1. **Learn patterns**: Review orchestrator-patterns.md or subagent-patterns.md
2. **Generate code**: Ask Kiro to create your first agent
3. **Test locally**: Run Flask app and test `/invoke` endpoint
4. **Deploy**: Follow deployment-pipeline-guide.md to deploy to Bedrock AgentCore

## Common Questions

**Q: Where do I start?**
A: Ask Kiro "Create an orchestrator called X that does Y" - it will generate a working scaffold.

**Q: How do I test my agent locally?**
A: Run the Flask app and POST to `http://localhost:8080/invoke` with test payloads.

**Q: How do I invoke a subagent from my orchestrator?**
A: Use the Agentic API's InvokeAgent operation. See orchestrator-patterns.md for examples.

**Q: What APIs are available?**
A: See api-reference.md for complete API documentation.

**Q: How do I deploy my agent?**
A: See deployment-pipeline-guide.md for Docker, ECR, and Bedrock AgentCore deployment steps.
