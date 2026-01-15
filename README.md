# Kiro powers repository

Collection of Kiro powers for enhanced AI agent capabilities. Each power provides specialized tools and workflows for specific development tasks.

Documentation is available at https://kiro.dev/docs/powers/

## Available powers

### aws-agentcore
**Build an agent with Amazon Bedrock AgentCore** - Build, test, and deploy AI agents using AWS Bedrock AgentCore with local development workflow. Amazon Bedrock AgentCore is an agentic platform for building, deploying, and operating effective agents.

**MCP Servers:** agentcore-mcp-server

---

### aws-infrastructure-as-code
**Build AWS infrastructure with CDK and CloudFormation** - Generate well-architected AWS infrastructure with CDK and CloudFormation - access latest documentation, validate templates, and troubleshoot deployments.

**MCP Servers:** awslabs.aws-iac-mcp-server

---

### cloud-architect
**Build infrastructure on AWS** - Build AWS infrastructure with CDK in Python following AWS Well-Architected framework best practices.

**MCP Servers:** awspricing, awsknowledge, awsapi, context7, fetch

---

### cloudwatch
**AWS CloudWatch Observability** - Query and analyze metrics, logs and alarms from AWS CloudWatch for troubleshooting and root cause analysis.

**MCP Servers:** awslabs.cloudwatch-mcp-server

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
**Design to Code with Figma** - Connect Figma designs to code components - automatically generate design system rules, map UI components to Figma designs, and maintain design-code consistency.

**MCP Servers:** figma

---

### neon
**Build a database with Neon** - Serverless Postgres with database branching, autoscaling, and scale-to-zero - perfect for modern development workflows.

**MCP Servers:** neon

---

### postman
**API Testing with Postman** - Automate API testing and collection management with Postman - create workspaces, collections, environments, and run tests programmatically.

**MCP Servers:** postman

---

### power-builder
**Power Builder** - Complete guide for building and testing new Kiro powers with templates, best practices, and validation.

**MCP Servers:** None (Knowledge Base Power)

---

### saas-builder
**SaaS Builder** - Build production-ready multi-tenant SaaS applications with serverless architecture, integrated billing, and enterprise-grade security.

**MCP Servers:** fetch, stripe, aws-knowledge-mcp-server, awslabs.dynamodb-mcp-server, awslabs.aws-serverless-mcp, playwright

---

### strands
**Build an agent with Strands SDK** - Build AI agents with Strands SDK using Bedrock, Anthropic, OpenAI, Gemini, or Llama models.

**MCP Servers:** strands-agents

---

### stripe
**Stripe Payments** - Build payment integrations with Stripe - accept payments, manage subscriptions, handle billing, and process refunds.

**MCP Servers:** stripe

---

### terraform
**Deploy infrastructure with Terraform** - Build and manage Infrastructure as Code with Terraform - access registry providers, modules, policies, and HCP Terraform workflow management.

**MCP Servers:** terraform (Docker stdio)

---

## Vercel Powers

Powers ported from [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills).

### vercel/react-best-practices
**React Best Practices** - React and Next.js performance optimization guidelines from Vercel Engineering. Contains 45+ rules across 8 categories, prioritized by impact to guide code review, refactoring, and optimization.

**MCP Servers:** None (Knowledge Base Power)

**Categories:** Eliminating Waterfalls (CRITICAL), Bundle Size Optimization (CRITICAL), Server-Side Performance (HIGH), Client-Side Data Fetching (MEDIUM-HIGH), Re-render Optimization (MEDIUM), Rendering Performance (MEDIUM), JavaScript Performance (LOW-MEDIUM), Advanced Patterns (LOW)

---

### vercel/web-design-guidelines
**Web Design Guidelines** - Review UI code for compliance with web interface best practices. Audits code for 100+ rules covering accessibility, performance, UX, forms, animations, typography, images, navigation, dark mode, touch interactions, and internationalization.

**MCP Servers:** None (Knowledge Base Power)

**Categories:** Accessibility, Focus States, Forms, Animation, Typography, Images, Performance, Navigation & State, Dark Mode & Theming, Touch & Interaction, Locale & i18n

**Guidelines Source:** https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md

---


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
