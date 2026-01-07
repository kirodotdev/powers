---
name: "serverless-dev"
displayName: "AWS Serverless Development"
description: "Build production-ready serverless applications on AWS using AWS SAM, Lambda, API Gateway, EventBridge, and other serverless services following AWS best practices"
keywords: ["serverless", "lambda", "sam", "api gateway", "eventbridge", "dynamodb", "s3", "step functions", "sqs", "sns", "cloudformation", "lambda durable functions", "workflow"]
mcpServers: ["awslabs.aws-serverless-mcp-server", "aws-knowledge-mcp-server"]
---

# Onboarding

## Step 1: Validate AWS SAM CLI
Before building serverless applications, ensure AWS SAM CLI is installed:
- **AWS SAM CLI**: Required for building and deploying serverless applications
  - Verify with: `sam --version`
  - Install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
  - **CRITICAL**: If SAM CLI is not installed, guide the user to install it before proceeding

## Step 2: Validate AWS CLI
- **AWS CLI**: Required for AWS operations
  - Verify with: `aws --version`
  - Check credentials: `aws sts get-caller-identity`
  - If not configured, guide user to run: `aws configure`

## Step 3: Validate Docker (Optional but Recommended)
- **Docker**: Required for local testing and building container-based Lambda functions
  - Verify with: `docker --version`
  - Note: Docker is optional but highly recommended for `sam build --use-container` and `sam local` commands

# When to Load Steering Files

- Initializing new serverless projects → `sam-init-workflow.md`
- Building and deploying applications → `sam-build-deploy.md`
- Creating Lambda functions → `lambda-best-practices.md`
- Building long-running workflows with Lambda Durable Functions → `lambda-durable-functions.md`
- Working with API Gateway → `api-gateway-patterns.md`
- Event-driven architectures with EventBridge, SQS, SNS → `event-driven-patterns.md`
- DynamoDB integration → `dynamodb-patterns.md`
- Local testing and debugging → `local-testing.md`
- Security and IAM → `security-iam.md`
- Performance optimization → `performance-optimization.md`

# Core Principles

## Always Use SAM for Serverless Development
- Prefer AWS SAM over raw CloudFormation for Lambda and API Gateway
- Use SAM CLI commands: `sam init`, `sam build`, `sam deploy`, `sam local invoke`
- Leverage SAM's simplified syntax for serverless resources

## Infrastructure as Code
- All infrastructure defined in `template.yaml` (SAM template)
- Use SAM policy templates for common IAM patterns
- Version control all infrastructure code

## Security First
- Apply least privilege IAM permissions
- Use SAM policy templates when possible
- Enable AWS X-Ray tracing for observability
- Use environment variables for configuration, AWS Secrets Manager for secrets

## Performance and Cost Optimization
- Right-size Lambda memory and timeout
- Use Lambda Layers for shared dependencies
- Implement proper error handling and retries
- Consider Lambda SnapStart for Java functions
- Use provisioned concurrency only when needed

## Testing Strategy
- Test locally with `sam local invoke` and `sam local start-api`
- Use `sam build` before deployment
- Implement unit tests for Lambda handlers
- Use `sam logs` for debugging deployed functions
