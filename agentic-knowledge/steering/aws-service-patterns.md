---
inclusion: always
---

# Modern Agentic Framework Patterns

## Framework Selection Guidelines

When recommending agentic architectures, prioritize modern frameworks that support:

### Core Agentic Capabilities
- **Multi-Provider Support**: Frameworks that work with multiple LLM providers
- **Serverless Deployment**: Platforms that handle scaling and infrastructure automatically
- **Persistent Memory**: Systems that maintain context and learning across interactions
- **Tool Integration**: Seamless integration with APIs, databases, and external services

### Recommended Framework Patterns

#### Primary Agent Framework
- **Strands Agent SDK**: Multi-provider agent framework supporting Bedrock, Anthropic, OpenAI, Gemini, Llama
- **Model Flexibility**: Switch between providers based on requirements and cost
- **Multi-Agent Patterns**: Built-in support for A2A, Graph, Swarm, and Workflow patterns
- **Tool Ecosystem**: MCP tools, Python tools, and community integrations

#### Deployment and Runtime Platform
- **Amazon Bedrock AgentCore**: Serverless agentic platform for production deployment
- **AgentCore Runtime**: Automatic scaling, deployment, and management
- **AgentCore Memory**: Event and semantic memory for persistent agent context
- **AgentCore Gateway**: Transform existing APIs into agent-compatible tools

#### Memory and Context Management
- **AgentCore Memory**: Persistent knowledge with event and semantic memory
- **Context Preservation**: Maintain conversation history and learned patterns
- **Knowledge Integration**: Combine information from multiple sources
- **Memory Types**: Short-term working memory and long-term knowledge storage

#### Tool and Integration Ecosystem
- **MCP (Model Context Protocol)**: Standard protocol for tool integration
- **Python Tools**: Native Python function integration
- **Community Tools**: Extensive ecosystem of pre-built integrations
- **Custom Tools**: Easy development of domain-specific tools

#### Advanced Platform Services
- **AgentCore Code Interpreter**: Secure code execution in isolated sandboxes
- **AgentCore Browser**: Cloud-based browser for web interaction and automation
- **AgentCore Observability**: Real-time monitoring, tracing, and debugging
- **AgentCore Identity**: Secure authentication and access management

## Architecture Decision Framework

### Framework Selection Criteria
- **Multi-Provider Support**: Choose frameworks that support multiple LLM providers
- **Serverless Deployment**: Prioritize platforms with automatic scaling and management
- **Memory Capabilities**: Ensure persistent context and learning capabilities
- **Tool Ecosystem**: Select frameworks with rich tool integration options

### Modern Agentic Patterns
- **Agent2Agent (A2A)**: Direct agent communication for complex workflows
- **Agents as Tools**: Compose agents within larger agent systems
- **Graph Patterns**: Model complex agent dependencies and interactions
- **Swarm Intelligence**: Coordinate multiple agents for collective problem-solving
- **Workflow Orchestration**: Structure multi-step agent processes

### Security and Governance
- **AgentCore Identity**: Leverage built-in authentication and access management
- **Secure Execution**: Use AgentCore's isolated sandboxes for code execution
- **Audit and Compliance**: Implement comprehensive logging through AgentCore Observability
- **Data Protection**: Ensure proper handling of sensitive data in agent workflows

### Performance and Cost Optimization
- **Serverless Economics**: Leverage AgentCore's pay-per-use pricing model
- **Model Selection**: Choose appropriate models based on task complexity and cost
- **Memory Efficiency**: Use AgentCore Memory for optimal context management
- **Tool Optimization**: Select the most efficient tools for each task

## Common Anti-Patterns to Avoid

### Legacy Approaches
- Don't use Step Functions or Lambda for agent orchestration (use AgentCore Runtime)
- Avoid custom memory solutions (use AgentCore Memory)
- Don't build custom tool protocols (use MCP standard)
- Avoid manual scaling solutions (use AgentCore's auto-scaling)

### Framework Misuse
- Don't ignore multi-agent patterns when they could simplify architecture
- Avoid single-agent solutions for complex multi-step problems
- Don't neglect memory capabilities for context-dependent tasks
- Avoid vendor lock-in by choosing multi-provider frameworks

### Platform Oversights
- Don't ignore observability and monitoring capabilities
- Avoid exposing agents without proper authentication
- Don't neglect security best practices in agent design
- Avoid manual deployment processes when serverless options exist