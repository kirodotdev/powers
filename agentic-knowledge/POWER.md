---
name: "agentic-knowledge"
displayName: "Agentic Knowledge"
description: "Architectural guidance for building agentic AI systems using AWS prescriptive guidance and patterns"
keywords: ["agentic ai",  "agentic architecture", "agent patterns", "agentic workflows", "aws architecture", "multi-agent systems",  "autonomous systems",  "intelligent agents", "prescriptive guidance", "architectural patterns"]
author: "AWS"
---

# Agentic Knowledge Power

This power provides architectural guidance for building agentic AI systems on AWS. It leverages MCP servers to access AWS prescriptive guidance and combines it with intelligent steering to provide contextual architectural recommendations.

## Prerequisites

Before using this power, ensure you have:
- **AWS Account**: Access to AWS services for implementation
- **AWS Credentials**: Properly configured AWS credentials if deploying resources
- **Internet Connection**: Required for MCP server communication
- **Python/uv**: Required for running MCP servers (uvx command)

## MCP Servers:
  - strands-agents
  - agentcore-mcp-server
  - aws-knowledge

## Foundational Concepts

### Definitions and Core Terminology

**Agentic AI**: A paradigm of intelligent systems consisting of software agents capable of adaptive behavior, complex coordination, and delegated decision-making. These systems can perceive their environment, reason about goals, and take autonomous actions to achieve objectives.

**Software Agents**: Autonomous digital entities that perceive their environment through sensors, reason about goals using internal models, and act through effectors to achieve desired outcomes. They exhibit characteristics of autonomy, reactivity, proactivity, and social ability.

**Agent Patterns**: Reusable design templates that describe the structure and behavior of individual agents, including reasoning agents, tool-based agents, coding agents, and multi-agent collaborative patterns.

**Agentic Workflows**: Complex orchestrations of multiple agents, tools, and environments that interact to form autonomous systems capable of handling sophisticated tasks through coordination, delegation, and collaborative problem-solving.

### Evolution from Traditional Systems to Agentic Systems

Traditional event-driven systems operate through reactive patterns where components respond to specific triggers and events. These systems follow predetermined workflows and require explicit programming for each scenario.

Modern agentic systems represent a paradigm shift toward autonomous, goal-oriented behavior. Instead of following rigid event-response patterns, agentic systems can:
- Perceive and interpret complex environments
- Reason about goals and constraints
- Plan and execute multi-step strategies
- Adapt to changing conditions
- Collaborate with other agents and humans

This evolution enables systems that can handle ambiguous requirements, learn from experience, and operate effectively in dynamic environments.

### Core Principles of Agentic Behavior

#### 1. Autonomy
Agents operate independently without constant human intervention, making decisions based on their goals, knowledge, and environmental conditions.

#### 2. Reactivity
Agents perceive their environment and respond appropriately to changes, maintaining awareness of their operational context.

#### 3. Proactivity
Agents take initiative to achieve their goals, planning ahead and anticipating future needs rather than merely reacting to events.

#### 4. Social Ability
Agents can interact and collaborate with other agents and humans through communication protocols and shared understanding.

#### 5. Goal-Oriented Behavior
Agents work toward specific objectives, making decisions that advance their goals while considering constraints and trade-offs.

#### 6. Temporal Continuity
Agents maintain persistent state and memory, learning from past experiences and maintaining context across interactions.

### Characteristics of Effective Agentic Systems

Effective agentic systems demonstrate three core capability dimensions:

**Perception Capabilities**: The ability to sense, interpret, and understand environmental conditions, user inputs, and system states through various input modalities.

**Reasoning Capabilities**: The capacity to process information, make decisions, plan actions, and solve problems using logical inference, pattern recognition, and learned knowledge.

**Action Capabilities**: The power to execute decisions through tool usage, API calls, system modifications, and interactions with other agents or humans.

## Business Value and Benefits

### Accelerated Time to Value
Agentic AI systems enable rapid deployment and faster decision-making through autonomous operation and intelligent automation. Organizations can achieve faster time-to-market for new capabilities and reduce the time required for complex decision-making processes.

### Improved Customer Engagement
Through personalized experiences and enhanced responsiveness, agentic systems can provide 24/7 availability, contextual understanding, and adaptive interactions that improve customer satisfaction and engagement metrics.

### Reduced Operational Costs
Automation benefits and efficiency gains from agentic systems reduce manual intervention requirements, optimize resource utilization, and streamline operational workflows, leading to significant cost reductions.

### Innovation and Differentiation Benefits
Agentic AI provides competitive advantages through organizational transformation, enabling new business models, enhanced service offerings, and innovative approaches to traditional challenges.

### Modernization of Legacy Workflows
Digital Transformation through Workflow Evolution allows organizations to modernize existing processes, integrate with modern systems, and adapt to changing business requirements more effectively.

### Quantifiable Business Outcomes
Organizations implementing agentic AI systems typically see measurable improvements in Operational Metrics, including reduced response times, increased throughput, improved accuracy rates, and enhanced customer satisfaction scores. Financial Impact includes cost savings from automation, revenue growth from improved services, and Strategic Benefits from competitive differentiation.

## How This Power Works

This power combines:
- **AWS Prescriptive Guidance Priority**: Starts with official AWS foundational documents on agentic AI
- **Documentation Access**: Retrieval of AWS guidance through MCP servers
- **Grounded Recommendations**: Architectural advice based on official AWS prescriptive guidance
- **Modern Implementation**: Combines AWS best practices with current frameworks (Strands, AgentCore)

## Core Capabilities

### 🔍 **AWS Prescriptive Guidance Foundation**
Starts with official AWS prescriptive guidance documents:
- **Foundations of agentic AI on AWS** - Core principles and architectural foundations
- **Agentic AI patterns and workflows on AWS** - Specific implementation patterns
- **Agentic AI frameworks, protocols, and tools on AWS** - Framework selection guidance
- **Serverless and multi-tenant architectures** - Deployment and scaling strategies

### 🏗️ **Architecture Design Assistance**
Get contextual recommendations for:
- **AWS Service Selection**: Compute (Lambda, ECS, EKS), Storage (S3, DynamoDB), Database (RDS, Aurora), Networking (VPC, API Gateway), Analytics (Kinesis, Glue)
- **Strands Agent SDK implementation patterns**: Multi-agent coordination and framework integration
- **AgentCore platform service selection and configuration**: Runtime, Memory, Gateway, and Observability services
- **Multi-agent patterns**: A2A, Graph, Swarm, Workflow coordination patterns
- **Memory and tool integration strategies**: Persistent context and tool ecosystem development
- **Scalability considerations**: Auto-scaling, load balancing, performance optimization, and high availability design
- **Security best practices**: Authentication, authorization, encryption, compliance, and access control patterns

### 📋 **Implementation Guidance**
Receive practical guidance on:
- **Strands Agent SDK setup and configuration**: Getting started with multi-provider agent development
- **AgentCore deployment and scaling strategies**: Serverless deployment, container orchestration, and performance tuning
- **Memory integration and tool development**: Persistent context management and custom tool creation
- **Observability and monitoring**: AgentCore platform monitoring, logging, and performance metrics
- **Security implementation**: Authentication patterns, secure communication, and compliance frameworks
- **Scalable architecture patterns**: Microservices deployment, event-driven architectures, and distributed systems design

---

*This power leverages MCP servers to access AWS prescriptive guidance and architectural patterns for agentic AI systems.*

## Getting Started

### 1. **Describe Your Use Case**
Start by describing what you want to build:
- "I need to build a customer service agent that can handle complex inquiries"
- "I want to create a multi-agent system for data processing workflows"
- "I need an agentic architecture for automated code review and deployment"

### 2. **Get Grounded Recommendations**
The power will:
- **First search AWS prescriptive guidance** on agentic AI foundations and patterns
- **Reference specific sections** from official AWS architectural guidance
- **Identify appropriate patterns** based on prescriptive guidance recommendations
- **Supplement with modern frameworks** (Strands, AgentCore) that align with AWS best practices

### 3. **Refine Your Architecture**
Through interactive dialogue and iterative refinement:
- **Clarify requirements and constraints** through targeted questions
- **Explore alternative architectural approaches** and evaluate trade-offs
- **Address scalability, security, and operational concerns** with specific recommendations
- **Iteratively improve and optimize** the architecture based on feedback
- **Develop a concrete implementation roadmap** with step-by-step guidance

## Modern Agentic Frameworks

### Strands Agent SDK
- **Multi-Provider Support**: Bedrock, Anthropic, OpenAI, Gemini, Llama models
- **Agent Patterns**: Reasoning, tool-based, coding, and collaborative agents
- **Multi-Agent Coordination**: A2A, Graph, Swarm, and Workflow patterns
- **Tool Integration**: MCP tools, Python tools, and community ecosystem

### AgentCore Platform
- **AgentCore Runtime**: Serverless deployment and auto-scaling
- **AgentCore Memory**: Event and semantic memory for persistent context
- **AgentCore Gateway**: Transform APIs into agent-compatible tools
- **AgentCore Observability**: Real-time monitoring and tracing

### Integration Patterns
- **Memory Integration**: Persistent context and learning capabilities
- **Tool Ecosystem**: MCP protocol and custom tool development
- **Multi-Agent Workflows**: Complex agent coordination and collaboration
- **Deployment Strategies**: Serverless scaling and management

## Example Interactions

**"I need to build a customer service agent"**
→ The power will first search AWS prescriptive guidance on "agentic AI patterns" and "customer service agents", reference specific architectural principles, then recommend Strands and AgentCore implementations that align with AWS best practices.

**"How do I implement multi-agent collaboration?"**
→ The power will search "agentic AI patterns and workflows" prescriptive guidance for multi-agent coordination principles, then provide implementation details using Strands multi-agent patterns (A2A, Graph, Swarm) and AgentCore services.

**"What's the best architecture for agentic workflows?"**
→ The power will reference AWS prescriptive guidance on "agentic workflows" and "serverless architectures", then recommend specific implementation approaches using modern frameworks that follow AWS architectural principles.

## Troubleshooting

### Common Issues and Solutions

#### MCP Server Connection Issues
**Problem**: MCP servers not responding or timing out
**Solution**: 
- Check your internet connection and AWS credentials
- Verify MCP server configurations in mcp.json
- Try restarting the MCP servers from the Kiro MCP panel
- Check the MCP server logs for specific error messages

#### Incomplete or Generic Responses
**Problem**: Receiving generic advice instead of AWS-specific guidance
**Solution**:
- Be more specific in your architectural requirements
- Mention specific AWS services or constraints you're working with
- Ask follow-up questions to refine the recommendations
- Request specific implementation examples or code snippets

#### Framework Selection Confusion
**Problem**: Unclear which framework (Strands vs AgentCore) to use
**Solution**:
- Strands Agent SDK: Use for multi-provider agent development and complex multi-agent patterns
- AgentCore: Use for serverless deployment, memory management, and production scaling
- Both can be used together: Strands for development, AgentCore for deployment

#### Outdated Information
**Problem**: Recommendations seem outdated or don't match current AWS services
**Solution**:
- The power uses live MCP servers to access current documentation
- If information seems outdated, try rephrasing your question
- Ask specifically for "current" or "latest" guidance
- Report persistent issues to ensure MCP servers are functioning correctly

### Getting Better Results

#### Be Specific About Your Context
- Mention your industry, use case, and scale requirements
- Include any existing AWS services or constraints
- Specify performance, security, or compliance requirements
- Describe your team's technical expertise level

#### Ask Progressive Questions
- Start with high-level architecture questions
- Drill down into specific implementation details
- Ask about trade-offs between different approaches
- Request specific examples or code snippets when needed

#### Leverage Interactive Refinement
- Respond to clarifying questions with detailed information
- Ask for alternatives if the first recommendation doesn't fit
- Request implementation roadmaps for complex architectures
- Ask about operational considerations (monitoring, scaling, security)

## Best Practices

### Effective Usage Patterns

#### 1. **Start with Requirements Gathering**
- Clearly describe your business use case and technical requirements
- Mention any existing AWS infrastructure or constraints
- Specify performance, security, and compliance needs
- Include information about expected scale and growth

#### 2. **Follow the Guidance Hierarchy**
- AWS Prescriptive Guidance provides the architectural foundation
- Strands Agent SDK offers implementation flexibility and multi-agent patterns
- AgentCore provides production-ready deployment and scaling
- Use all three layers for comprehensive solutions

#### 3. **Iterate and Refine**
- Start with high-level architecture discussions
- Progressively drill down into implementation details
- Ask about trade-offs and alternative approaches
- Request specific examples and code snippets

#### 4. **Consider the Full Lifecycle**
- Development: Use Strands for rapid prototyping and testing
- Deployment: Leverage AgentCore for serverless scaling
- Operations: Implement comprehensive monitoring and observability
- Maintenance: Plan for updates and continuous improvement

### Architecture Decision Guidelines

#### When to Use Strands Agent SDK
- ✅ Multi-provider model support needed
- ✅ Complex multi-agent coordination required
- ✅ Rapid prototyping and development
- ✅ Custom tool integration needed
- ✅ A2A, Graph, Swarm, or Workflow patterns

#### When to Use AgentCore Platform
- ✅ Production deployment and scaling
- ✅ Serverless architecture preferred
- ✅ Persistent memory and context needed
- ✅ API transformation and gateway functionality
- ✅ Enterprise security and compliance requirements

#### When to Combine Both
- ✅ Full development-to-production lifecycle
- ✅ Complex multi-agent systems at scale
- ✅ Need both flexibility and production reliability
- ✅ Enterprise-grade agentic applications

### Security and Compliance Best Practices

#### Authentication and Authorization
- Use AgentCore Identity for secure authentication
- Implement proper access controls for agent interactions
- Follow AWS IAM best practices for service permissions
- Use VPC and security groups for network isolation

#### Data Protection
- Encrypt data in transit and at rest
- Use AWS KMS for key management
- Implement proper data retention policies
- Follow compliance requirements (GDPR, HIPAA, etc.)

#### Monitoring and Auditing
- Implement comprehensive logging with AgentCore Observability
- Monitor agent behavior and performance metrics
- Set up alerts for anomalous behavior
- Maintain audit trails for compliance

### Performance Optimization

#### Cost Management
- Use appropriate model sizes for each task
- Implement caching for frequently accessed data
- Leverage AgentCore's pay-per-use pricing model
- Monitor and optimize resource usage

#### Scalability Planning
- Design for horizontal scaling from the start
- Use AgentCore Runtime for automatic scaling
- Implement proper load balancing strategies
- Plan for peak usage scenarios

#### Latency Optimization
- Choose models based on latency requirements
- Implement efficient memory and context management
- Use appropriate AWS regions for your users
- Optimize tool and API integrations

---

## License Information

This power integrates with the following MCP servers:

- **strands-agents-mcp-server**: Apache-2.0 License
- **amazon-bedrock-agentcore-mcp-server**: Apache-2.0 License  
- **AWS Knowledge MCP Server**: Proprietary AWS service

For complete license details, refer to each MCP server's repository or documentation.

## Telemetry and Privacy

**Telemetry Collection**: This power does not collect or transmit telemetry data. However, the integrated MCP servers may collect usage data according to their respective privacy policies:

- **AWS Knowledge MCP Server**: Subject to AWS Privacy Notice and service terms
- **Strands and AgentCore MCP Servers**: May collect usage metrics as documented in their respective repositories

**Data Handling**: When using this power:
- Architectural queries and responses are processed through MCP servers
- No user data is stored by the power itself
- AWS service usage follows standard AWS data handling practices
- Review individual MCP server privacy policies for specific data handling details

**Disabling Telemetry**: To disable telemetry collection:
- For AWS services: Configure according to AWS service documentation
- For third-party MCP servers: Refer to their respective documentation for opt-out procedures
- MCP server connections can be disabled in the mcp.json configuration file

For questions about data handling or privacy, consult the AWS Privacy Notice at https://aws.amazon.com/privacy/ and individual MCP server documentation.