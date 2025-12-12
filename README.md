# Kiro Powers Repository

Collection of Kiro Powers for enhanced AI agent capabilities. Each power provides specialized tools and workflows for specific development tasks.

Documentation is available at https://kiro.dev/docs/powers/

## Available Powers

### aurora-dsql
**Deploy a distributed SQL database on AWS** - PostgreSQL-compatible serverless distributed SQL database with Aurora DSQL-specific constraints and capabilities.

**MCP Servers:** aurora-dsql, aws-core (optional)

---

### aws-agentcore
**AWS Bedrock AgentCore** - Build, test, and deploy AI agents using AWS Bedrock AgentCore with local development workflow.

**MCP Servers:** agentcore-mcp-server, strands-mcp-server

---

### aws-infrastructure-as-code
**AWS Infrastructure as Code** - Generate well-architected AWS infrastructure with CDK and CloudFormation - access latest documentation, validate templates, and troubleshoot deployments

**MCP Servers:** aws-iac-mcp-server

---

### cloud-architect
**AWS CDK with Python** - Build AWS infrastructure as code following AWS Well-Architected framework best practices. Specialized for Python CDK development with comprehensive testing strategies.

**MCP Servers:** awspricing, awsknowledge, awsapi, context7, fetch

---

### datadog
**Datadog Observability** - Query logs, metrics, traces, RUM events, incidents, and monitors from Datadog for production debugging and performance analysis.

**MCP Servers:** datadog (HTTPS API)

---

### dynatrace
**Dynatrace Observability** - Query logs, metrics, traces, problems, and security vulnerabilities using DQL (Dynatrace Query Language) and Davis AI.

**MCP Servers:** dynatrace-mcp-server

---

### figma
**Design to Code** - Connect Figma designs to code components, automatically generate design system rules, and maintain design-code consistency.

**MCP Servers:** figma (HTTPS API)

---

### neon
**Neon Serverless Postgres** - Serverless Postgres with database branching, autoscaling, and scale-to-zero capabilities.

**MCP Servers:** neon (remote MCP)

---

### postman
**Postman API Testing** - Automate API testing and collection management with Postman - create workspaces, collections, environments, and run tests programmatically.

**MCP Servers:** postman (40 tools in minimal mode, 112 in full mode)

---

### requirements-analyst
**Requirements Analyst** - Complete requirements engineering power with 6-phase methodology: Discovery, Classification, Analysis, Prioritization, Validation, and Specification.

**MCP Servers:** None (standalone power)

---

### saas-builder
**SaaS Builder** - Build production-ready multi-tenant SaaS applications with serverless architecture, integrated billing, and enterprise-grade security.

**MCP Servers:** fetch, stripe, aws-knowledge-mcp-server, awslabs.dynamodb-mcp-server, awslabs.aws-serverless-mcp, playwright

---

### spec-kit
**Spec-Driven Development** - Complete SDD methodology with 8 workflows: Steering, Specify, Clarify, Plan, Tasks, Implement, Analyze, and Checklist. Transform specifications into executable code with multi-step refinement.

**MCP Servers:** None (standalone power)

---

### strands
**Strands Agents SDK** - Build AI agents with Strands SDK using Bedrock, Anthropic, OpenAI, Gemini, or Llama models.

**MCP Servers:** strands-agents

---

### stripe
**Stripe Payments** - Build payment integrations with Stripe - accept payments, manage subscriptions, handle billing, and process refunds.

**MCP Servers:** stripe (HTTPS API)

---

### terraform
**Terraform** - Build and manage infrastructure as code with Terraform - access registry providers, modules, policies, and HCP Terraform workspace management.

**MCP Servers:** terraform (Docker stdio)

---


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
