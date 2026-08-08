# AWS Serverless Development Kiro Power

A comprehensive Kiro Power for building production-ready serverless applications on AWS using SAM (Serverless Application Model).

## What This Power Provides

This power gives Kiro instant expertise in:

- **AWS SAM** - Initialize, build, and deploy serverless applications
- **Lambda Functions** - Best practices for handlers, performance, and error handling
- **API Gateway** - REST and HTTP APIs with authentication and authorization
- **Event-Driven Architecture** - EventBridge, SQS, SNS, S3 events, DynamoDB Streams
- **DynamoDB** - Single-table design, access patterns, and optimization
- **Local Testing** - SAM local invoke and API testing
- **Security & IAM** - Least privilege policies, secrets management, encryption
- **Performance Optimization** - Cold start reduction, memory tuning, cost optimization

## Installation

### From Local Path (Development)

1. Clone or download this repository
2. Open Kiro IDE
3. Go to Powers panel
4. Click "Add power from Local Path"
5. Select the `serverless-dev` directory

### From GitHub (Once Published)

1. Open Kiro IDE
2. Go to Powers panel
3. Click "Add power from GitHub"
4. Enter the repository URL

## Prerequisites

This power requires:

- **AWS SAM CLI** - Install from https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
- **AWS CLI** - Configured with credentials
- **Docker** (optional but recommended) - For local testing and container builds

The power will validate these dependencies on first use.

## Usage

Once installed, the power activates automatically when you mention serverless-related keywords:

- "Create a Lambda function"
- "Build a serverless API"
- "Set up DynamoDB table"
- "Deploy with SAM"
- "Add EventBridge rule"

## Example Prompts

**Initialize a new project:**
```
Create a new serverless API with Python Lambda functions and DynamoDB
```

**Add functionality:**
```
Add an EventBridge rule that triggers a Lambda function when orders are placed
```

**Optimize performance:**
```
Optimize this Lambda function for better cold start performance
```

**Deploy:**
```
Build and deploy this application using SAM
```

## Steering Files

The power includes specialized guidance for:

- `sam-init-workflow.md` - Project initialization
- `sam-build-deploy.md` - Build and deployment
- `lambda-best-practices.md` - Lambda function patterns
- `api-gateway-patterns.md` - API Gateway configuration
- `event-driven-patterns.md` - Event-driven architectures
- `dynamodb-patterns.md` - DynamoDB integration
- `local-testing.md` - Local development and testing
- `security-iam.md` - Security and IAM best practices
- `performance-optimization.md` - Performance tuning

## Best Practices Included

- SAM policy templates for least privilege
- Arm64 architecture for better price-performance
- X-Ray tracing enabled by default
- Structured logging patterns
- Error handling and retry strategies
- Cold start optimization techniques
- Cost optimization recommendations

## Contributing

To improve this power:

1. Add or update steering files in the `steering/` directory
2. Update `POWER.md` with new keywords or workflows
3. Test locally before sharing

## License

This power is provided as-is for use with Kiro IDE.
