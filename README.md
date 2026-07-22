# Kiro powers repository

Collection of Kiro powers for enhanced AI agent capabilities. Each power provides specialized tools and workflows for specific development tasks.

> This repository contains a subset of available Kiro powers. Additional powers are published and hosted independently by their respective authors. For the complete registry of all published powers, visit [kiro.dev/powers](https://kiro.dev/powers).

Documentation is available at https://kiro.dev/docs/powers/

## Available powers

### arm-soc-migration
**Perform Migration between Arm SoC** - Guides migration of code from one Arm SoC to another, with architecture-aware analysis and safe migration practices. Supports common scenarios like AWS Graviton to Raspberry Pi, NXP i.MX8 to NVIDIA Jetson Orin, and more.

**MCP Servers:** arm-mcp-server (Docker)

---

### aws-agentcore
**Build an agent with Amazon Bedrock AgentCore** - Build, test, and deploy AI agents using AWS Bedrock AgentCore with local development workflow. Amazon Bedrock AgentCore is an agentic platform for building, deploying, and operating effective agents.

**MCP Servers:** agentcore-mcp-server

---

### aws-amplify
**Build full-stack apps with AWS Amplify** - Build and extend full-stack applications with AWS Amplify Gen 2 using type-safe TypeScript, guided workflows, and best practices. Covers authentication, data models, storage, serverless functions, AI/ML integration, and deployment to sandbox and production.

**MCP Servers:** aws-mcp

---

### aws-devops-agent
**AWS DevOps Agent** - AI agent for AWS operational intelligence. Investigate incidents, optimize costs, review architecture, map topology, chat with the agent, get remediation, run automated release tests (UI and API), and trigger pre-merge release readiness reviews — all enhanced with your local workspace context.

**MCP Servers:** aws-devops-agent (remote MCP Server, supports Bearer token + SigV4 auth), aws-mcp

---

### aws-graviton-migration
**Plan and Migration to Graviton** - Analyzes source code to identify compatibilities with Graviton processors (Arm64 architecture). Generates reports with incompatibilities and provides suggestions for minimal required and recommended versions for language runtimes and dependency libraries.

**MCP Servers:** arm-mcp (Docker)

---

### aws-healthomics
**AWS HealthOmics** - Create, migrate, run, debug and optimize genomics workflows in AWS HealthOmics. Supports WDL, Nextflow, and CWL workflow languages.

**MCP Servers:** awslabs.aws-healthomics-mcp-server

---

### aws-infrastructure-as-code
**Build AWS infrastructure with CDK and CloudFormation** - Build well-architected AWS infrastructure with CDK using latest documentation, best practices, and code samples. Validate CloudFormation templates, check resource configuration security compliance, and troubleshoot deployments.

**MCP Servers:** awslabs.aws-iac-mcp-server

---

### aws-lambda-managed-instances
**AWS Lambda Managed Instances** - Evaluate, configure, and migrate workloads to AWS Lambda Managed Instances (LMI). Run Lambda functions on EC2 instances in your account while AWS manages provisioning, patching, scaling, routing, and load balancing.

**MCP Servers:** None (Knowledge Base Power)

---

### aws-mcp
**Work with AWS** - Perform complex, multi-step AWS tasks by combining real-time access to AWS documentation, syntactically correct API calls and executions, and pre-built workflows called Agent SOPs that follow AWS best practices.

**MCP Servers:** aws-mcp

---

### aws-observability
**AWS Observability** - Comprehensive AWS observability platform combining CloudWatch Logs, Metrics, Alarms, Application Signals (APM), CloudTrail security auditing, Amazon Managed Prometheus (AMP) metric querying, and automated codebase observability gap analysis.

**MCP Servers:** awslabs.cloudwatch-mcp-server, awslabs.cloudwatch-applicationsignals-mcp-server, awslabs.cloudtrail-mcp-server, awslabs.prometheus-mcp-server, awslabs.aws-documentation-mcp-server

---

### aws-sam
**AWS SAM** - An opinionated Kiro Power to aid development with AWS Serverless Application Model (SAM). Includes MCP tooling and common usage patterns for building, testing, and deploying serverless applications.

**MCP Servers:** awslabs.aws-serverless-mcp-server, fetch

---

### aws-step-functions
**AWS Step Functions** - Build workflows with AWS Step Functions state machines using the JSONata query language. Covers Amazon States Language (ASL) structure, state types, variables, data transformation, error handling, AWS service integration, and migrating from JSONPath to JSONata.

**MCP Servers:** None (Knowledge Base Power)

---

### aws-transform
**AWS Transform** - Migrate, modernize, and upgrade codebases: .NET Framework to .NET 8/10, mainframe COBOL to Java, VMware VMs to EC2, SQL Server/Oracle/MySQL to Aurora, and Java/Python/Node.js version upgrades or AWS SDK migrations. Assess, plan, and execute code transformations from your IDE.

**MCP Servers:** None

---

### aws-transform-agent-toolkit
**AWS Transform Agent Toolkit** - Build agents to run in AWS Transform. Provides a self-service agent lifecycle from inception to development to production. Build modernization and migration agents with citation-backed AWS Transform documentation search, package agents as containers, deploy to Bedrock AgentCore, and register with AWS Transform.

**MCP Servers:** aws-transform-agent-toolkit

---

### checkout
**Checkout.com Global Payments** - Access Checkout.com's comprehensive API documentation with intelligent search and detailed operation information for payments, customers, disputes, and more.

**MCP Servers:** checkout-dx (HTTPS)

---

### cloud-architect
**Build infrastructure on AWS** - Build AWS infrastructure with CDK in Python following AWS Well-Architected framework best practices.

**MCP Servers:** awspricing, awsknowledge, awsapi, context7, fetch

---

### cloudwatch-application-signals
**[DEPRECATED] Amazon CloudWatch Application Signals** - This power has been merged into the AWS Observability power. We recommend installing the AWS Observability power for a more comprehensive monitoring experience.

**MCP Servers:** awslabs.cloudwatch-applicationsignals-mcp-server

---

### databricks
**Databricks AI Dev Kit** - Comprehensive Databricks development toolkit with 44 MCP tools (180+ operations) and expert guidance for building data pipelines, ML workflows, dashboards, jobs, and applications on the Databricks platform across AWS, Azure, and GCP.

**MCP Servers:** databricks (ai-dev-kit local MCP server)

---

### datadog
**Datadog Observability** - Query logs, metrics, traces, RUM events, incidents, and monitors from Datadog for production debugging and performance analysis.

**MCP Servers:** datadog (HTTPS API)

---

### defang
**Deploy Anywhere with Defang** - Easily deploy any Docker Compose application to the cloud with Defang. Networking, compute, storage, databases, queues, LLMs - all deployed natively to the cloud of your choice - AWS, GCP, or DigitalOcean - in a secure, scalable, and cost-efficient way.

**MCP Servers:** defang

---

### dynatrace
**Dynatrace Observability** - Query logs, metrics, traces, problems, and Kubernetes events from Dynatrace using DQL (Dynatrace Query Language) and Davis AI.

**MCP Servers:** dynatrace-mcp-server

---

### localstack
**Develop AWS apps with LocalStack** - Build, test, and debug AWS applications locally and in CI/CD using LocalStack. Manage the local cloud environment, deploy infrastructure with CDK/Terraform/SAM, analyze logs, enforce IAM policies, inject chaos faults, and manage state snapshots.

**MCP Servers:** localstack

---

### migration-to-aws
**GCP to AWS Migration Advisor** - Migrate workloads from Google Cloud Platform to AWS — including AI and agentic workloads. Runs a 6-phase process: discover GCP resources, clarify requirements, design AWS architecture, estimate costs, generate migration artifacts, and collect feedback.

**MCP Servers:** awsknowledge, awspricing

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

### spark-troubleshooting-agent
**Troubleshoot Spark applications on AWS** - Troubleshoot Spark applications on AWS EMR, Glue, and SageMaker - analyze failures, identify bottlenecks, get code recommendations.

**MCP Servers:** sagemaker-unified-studio-mcp-troubleshooting, sagemaker-unified-studio-mcp-code-rec

---

### stackgen
**StackGen Infrastructure as Code** - Design, manage, and deploy cloud infrastructure with StackGen - create appstacks, manage resources, configure environments, and push IaC to Git. Supports AWS, Azure, and GCP.

**MCP Servers:** stackgen (HTTPS)

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

### zapier
**Zapier** - Connect 9,000+ apps to your AI workflow — discover, enable, and execute Zapier actions directly from your AI assistant. Supports Agentic and Classic server modes with OAuth authentication.

**MCP Servers:** zapier (HTTPS)

---


## License

Unless otherwise specified by the license in the individual power or the repository that hosts it, Kiro users have a non-exclusive license to access, download, and otherwise use the power for their personal or business purposes.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
