# CloudFormation Guidelines for Serverless Applications

This guide provides best practices for base CloudFormation templates.

## Template Structure

- Use consistent parameter validation with `AllowedPattern` and `NoEcho` for sensitive values

## Modular Architecture

- **ALWAYS** break infrastructure into logical, reusable stacks
- Pass parameters between stacks using `!GetAtt` and `!Ref` functions
- Only use nested stacks for complex deployments. Create separate templates for logically separate areas of the application
  which could theoretically be standalone or reused with minimal rework

## Security by Default Principles

### Encryption Standards

- **ALWAYS** enable encryption at rest for all data stores
- **ALWAYS** use customer-managed KMS keys for sensitive resources
- Enable automatic key rotation: `EnableKeyRotation: true`
- Apply KMS encryption to:
  - DynamoDB tables: `SSESpecification` with `KMSMasterKeyId`
  - SQS queues: `KmsMasterKeyId` property
  - SNS topics: `KmsMasterKeyId` property
  - CloudWatch Log Groups: `KmsKeyId` property
  - EventBridge event buses: `KmsKeyIdentifier` property

### S3 Security Configuration

- **ALWAYS** enable S3 bucket encryption with `BucketEncryption`
- **ALWAYS** block public access with `PublicAccessBlockConfiguration`
- **ALWAYS** enforce HTTPS-only access with bucket policies
- **ALWAYS** configure access logging to dedicated logging bucket
- Use Origin Access Control (OAC) for CloudFront distributions, not legacy OAI

### Network Security

- **ALWAYS** use `ViewerProtocolPolicy: redirect-to-https` for CloudFront
- **ALWAYS** enforce minimum TLS version: `MinimumProtocolVersion: TLSv1.3_2025` when using custom domains

### API Gateway Security

- **ALWAYS** enable access logging with structured log format
- **ALWAYS** implement proper CORS and security headers

## Backup and Recovery

### Point-in-Time Recovery

- **ALWAYS** enable PITR for DynamoDB tables: `PointInTimeRecoverySpecification.PointInTimeRecoveryEnabled: true`
- **ALWAYS** enable versioning for S3 buckets
- **ALWAYS** configure appropriate retention policies for logs and backups

### Dead Letter Queues (DLQs)

- **ALWAYS** implement DLQs for all asynchronous processing
- **ALWAYS** encrypt DLQs with customer-managed KMS keys
- **ALWAYS** set appropriate message retention: `MessageRetentionPeriod: 1209600` (14 days)
- **ALWAYS** configure redrive policies with reasonable retry counts
- **ALWAYS** monitor DLQ depth with CloudWatch alarms

## Monitoring and Observability

### CloudWatch Integration

- **ALWAYS** enable X-Ray tracing for Lambda functions: `Tracing: Active`
- **ALWAYS** enable API Gateway tracing: `TracingEnabled: true`
- **ALWAYS** use AWS Lambda Powertools layer for structured logging
- **ALWAYS** set appropriate log retention periods: `RetentionInDays: 90`

### Comprehensive Alerting

- **ALWAYS** create CloudWatch alarms for:
  - Lambda function errors
  - DLQ message visibility
  - API Gateway 4XX/5XX errors
  - CloudFront error rates
- **ALWAYS** use SNS topics for alert distribution
- **ALWAYS** implement anomaly detection for error rates
- **ALWAYS** create composite alarms for related failure scenarios

### Dashboards and Queries

- **ALWAYS** create operational dashboards with:
  - Key performance indicators (KPIs)
  - System health metrics
  - Error tracking widgets
  - Service maps for distributed tracing
- **ALWAYS** define CloudWatch Logs Insights queries for common troubleshooting scenarios
- **ALWAYS** include log correlation fields (entrantId, requestId, etc.)

## Production-Ready Configuration

### Resource Sizing and Performance

- **ALWAYS** use `BillingMode: PAY_PER_REQUEST` for DynamoDB tables by default
- **ALWAYS** configure appropriate Lambda memory and timeout settings
- **ALWAYS** use Global Secondary Indexes (GSI) for query patterns
- **ALWAYS** enable DynamoDB streams for event-driven architectures

### Error Handling and Resilience

- **ALWAYS** implement retry policies with exponential backoff
- **ALWAYS** set `MaximumRetryAttempts` and `MaximumEventAgeInSeconds` for EventBridge rules
- **ALWAYS** use `FunctionResponseTypes: ReportBatchItemFailures` for batch processing
- **ALWAYS** configure appropriate batch sizes and batching windows

### Content Delivery and Caching

- **ALWAYS** use CloudFront for static content delivery
- **ALWAYS** implement appropriate caching policies:
  - `CachingOptimized` for static assets
  - by default use `CachingDisabled` for dynamic API calls but the author may want to change this on a case by case basis
- **ALWAYS** configure custom error pages for SPA applications
- **ALWAYS** enable CloudFront logging to dedicated S3 bucket

### Security Headers and CSP

- **ALWAYS** implement comprehensive security headers:
  - Content Security Policy (CSP)
  - Strict Transport Security (HSTS)
  - X-XSS-Protection
  - Referrer Policy
- **ALWAYS** configure CSP to allow necessary external resources while maintaining security

## Environment and Configuration Management

### Parameter Management

- **ALWAYS** use AWS Systems Manager Parameter Store for configuration
- **ALWAYS** use AWS Secrets Manager for sensitive values (API keys, passwords)
- **ALWAYS** implement proper IAM policies for parameter access
- **ALWAYS** use parameter hierarchies: `/<app_name>/*` for organized access where <app_name> is an
  appropriate name for the app under development

### Conditional Resource Creation

- **ALWAYS** use CloudFormation conditions for optional features
- **ALWAYS** implement feature flags through parameters and conditions
- **ALWAYS** handle optional integrations gracefully (email providers, monitoring)

### Multi-Environment Support

- **ALWAYS** parameterize environment-specific values
- **ALWAYS** use consistent naming conventions with stack name prefixes
- **ALWAYS** implement proper resource tagging for cost allocation and management

## IAM and Access Control

### Least Privilege Access

- **ALWAYS** use SAM policy templates when available
- **ALWAYS** scope IAM permissions to specific resources using ARNs
- **ALWAYS** implement resource-based policies where appropriate
- **ALWAYS** use service-linked roles and managed policies when possible

### Cross-Service Access

- **ALWAYS** implement proper trust relationships for cross-service access
- **ALWAYS** use condition keys for additional security (aws:SourceAccount, aws:SourceArn)
- **ALWAYS** validate service principals and source constraints

## Compliance and Governance

### Resource Tagging

- **ALWAYS** implement consistent tagging strategy
- **ALWAYS** use cost allocation tags for billing transparency
- **ALWAYS** tag resources with environment, project, and owner information

### Documentation and Metadata

- **ALWAYS** include appropriate descriptions for resources which support a description parameter
- **ALWAYS** document parameter purposes and constraints
- **ALWAYS** use meaningful resource names that indicate purpose
- **ALWAYS** include copyright and ownership information in templates
- **ALWAYS** update README deployment instructions as changes are made which impact deployment steps
- **ALWAYS** update relevant sections of the README which relate to the infrastructure for the application
  and notify the user when they have made changes which may require updates to external assets like threat models
  or architecture diagrams
