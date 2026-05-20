# LocalStack Development Best Practices

Auto-loaded when working on LocalStack-related projects.

## MCP tools in Kiro (prefer these first)

The LocalStack Power wires the [LocalStack MCP Server](https://github.com/localstack/localstack-mcp-server). Use tools by name when they fit the task:

- **`localstack-docs`** — Coverage, configuration, and how-to questions (works without a running LocalStack instance; good sanity check after auth setup).
- **`localstack-management`** — Start, stop, restart, and status of the LocalStack container; health-style checks without scripting Docker by hand.
- **`localstack-logs-analysis`** — Structured summaries, errors-by-service, and metrics from logs instead of asking the user to paste raw `localstack logs`.
- **`localstack-aws-client`** — Safe `awslocal` execution inside the configured container context (sanitized; avoids accidental real-AWS calls).
- **`localstack-iam-policy-analyzer`** — IAM enforcement modes, violations from logs, and generated policies when your plan tier includes this capability.

Fall back to terminal commands when the user explicitly wants local scripts, CI logs, or the MCP server is unavailable — but default to MCP for interactive assistance.

## General Principles

- **ALWAYS** use `awslocal` instead of `aws` CLI when interacting with LocalStack. `awslocal` is a thin wrapper that automatically routes requests to `http://localhost:4566`.
- **ALWAYS** prefer LocalStack wrapper tools over vanilla IaC tools: `tflocal` over `terraform`, `cdklocal` over `cdk`, `samlocal` over `sam`, `pulumilocal` over `pulumi`.
- **NEVER** use real AWS credentials when working against LocalStack. Use dummy credentials:
  ```bash
  AWS_ACCESS_KEY_ID=test
  AWS_SECRET_ACCESS_KEY=test
  AWS_DEFAULT_REGION=us-east-1
  ```
- **ALWAYS** verify LocalStack is running before executing commands: `localstack status` or `curl http://localhost:4566/_localstack/health`.
- **Test against LocalStack before AWS**: Catch configuration errors, IAM issues, and logic bugs locally before running up cloud costs.

## Environment Configuration

### Recommended Development Settings

```bash
# Enable persistence so state survives restarts
PERSISTENCE=1 localstack start -d

# Enable debug logging when troubleshooting
DEBUG=1 localstack start -d

# Enable IAM soft enforcement to detect permission issues
ENFORCE_IAM=soft localstack start -d

# Combine multiple settings
DEBUG=1 PERSISTENCE=1 ENFORCE_IAM=soft localstack start -d
```

### Key Environment Variables

| Variable              | Description                            | Recommended Value                        |
| --------------------- | -------------------------------------- | ---------------------------------------- |
| `DEBUG`               | Enable verbose debug logging           | `1` when troubleshooting                 |
| `PERSISTENCE`         | Retain state across container restarts | `1` during development                   |
| `ENFORCE_IAM`         | IAM policy enforcement mode            | `soft` for discovery, `1` for validation |
| `GATEWAY_LISTEN`      | LocalStack port                        | `4566` (default)                         |
| `LS_LOG`              | Log level                              | `trace` for maximum verbosity            |
| `LAMBDA_DEBUG`        | Enable Lambda debug mode               | `1` when debugging functions             |
| `MAIN_CONTAINER_NAME` | Docker container name                  | `localstack-main` (default)              |

## AWS Service Interaction

### Using awslocal

```bash
# S3 operations
awslocal s3 mb s3://my-bucket
awslocal s3 cp file.txt s3://my-bucket/
awslocal s3 ls s3://my-bucket/

# DynamoDB operations
awslocal dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
awslocal dynamodb put-item --table-name Users --item '{"id": {"S": "123"}}'

# Lambda operations
awslocal lambda list-functions
awslocal lambda invoke \
  --function-name my-function \
  --payload '{"key": "value"}' \
  response.json

# SQS operations
awslocal sqs create-queue --queue-name my-queue
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/my-queue --message-body "hello"

# CloudFormation
awslocal cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml
```

### Resource Naming

- Use descriptive, consistent resource names that reflect their purpose
- Append environment suffixes where applicable: `my-table-dev`, `my-bucket-test`
- LocalStack uses account ID `000000000000` by default in resource ARNs

## Health & Monitoring

### Verifying Service Health

```bash
# Check all services
curl http://localhost:4566/_localstack/health | jq

# Check a specific service
curl http://localhost:4566/_localstack/health | jq '.services.s3'
curl http://localhost:4566/_localstack/health | jq '.services.lambda'

# View LocalStack version info
curl http://localhost:4566/_localstack/info | jq
```

### Viewing Logs

**In Kiro:** Prefer **`localstack-logs-analysis`** (modes such as errors, summary, or raw segments) before asking for full log dumps.

**In a terminal:**

```bash
# Follow logs in real time
localstack logs -f

# View last N lines
localstack logs --tail 100

# Filter for a specific service
localstack logs | grep -i lambda

# Filter for errors only
localstack logs | grep -i "error\|exception\|traceback"
```

## Container Lifecycle

```bash
# Start LocalStack (detached)
localstack start -d

# Check running status
localstack status

# Stop gracefully
localstack stop

# Restart (picks up new environment variables)
localstack restart

# Force restart via Docker
docker restart localstack-main
```

## Endpoint Configuration

All LocalStack services are available at `http://localhost:4566`. When manually configuring SDKs or clients:

```python
# Python (boto3)
import boto3
client = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)
```

```javascript
// JavaScript (AWS SDK v3)
import { S3Client } from '@aws-sdk/client-s3';
const client = new S3Client({
  endpoint: 'http://localhost:4566',
  region: 'us-east-1',
  credentials: { accessKeyId: 'test', secretAccessKey: 'test' },
  forcePathStyle: true, // Required for S3
});
```

## Troubleshooting Checklist

1. **Is LocalStack running?** → `localstack status`, or **`localstack-management`** with a status action in Kiro
2. **Are the services initialized?** → `curl http://localhost:4566/_localstack/health | jq`
3. **Are you using the right endpoint?** → `http://localhost:4566`
4. **Are you using awslocal/wrapper tools?** → Not bare `aws`, `terraform`, `cdk`
5. **Is your auth token configured (MCP and CLI)?** → **Do not** use `echo $LOCALSTACK_AUTH_TOKEN` — the MCP token lives in Power `mcp.json`. For CLI, run `localstack auth show-token` and expect `Valid: True`, or use **`localstack-docs`** in Kiro to confirm MCP auth. If the token is valid but a feature still fails, check whether your **plan tier** includes that capability.
6. **Are there errors in the logs?** → **`localstack-logs-analysis`** in Kiro, or `localstack logs | grep -i error` in a terminal
7. **Does the resource exist?** → **`localstack-aws-client`** or `awslocal <service> list-<resources>`
