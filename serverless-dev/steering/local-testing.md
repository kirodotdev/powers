# Local Testing with SAM

## Local Function Invocation

### Invoke with Event File
```bash
sam local invoke MyFunction -e events/event.json
```

### Invoke with Inline Event
```bash
echo '{"key": "value"}' | sam local invoke MyFunction
```

### Invoke Specific Function
```bash
sam local invoke MyFunction --parameter-overrides Environment=dev
```

## Local API Gateway

### Start Local API
```bash
sam local start-api
```

Access at: http://localhost:3000

### Custom Port
```bash
sam local start-api --port 8080
```

### With Environment Variables
```bash
sam local start-api --env-vars env.json
```

env.json:
```json
{
  "MyFunction": {
    "TABLE_NAME": "local-table",
    "LOG_LEVEL": "DEBUG"
  }
}
```

## Debugging

### Python with Debugger
```bash
sam local invoke -d 5858 MyFunction
```

Then attach debugger to port 5858.

### Node.js with Debugger
```bash
sam local invoke -d 9229 MyFunction
```

## Generate Sample Events

```bash
sam local generate-event apigateway aws-proxy > events/api-event.json
sam local generate-event s3 put > events/s3-event.json
sam local generate-event dynamodb update > events/dynamodb-event.json
```

## Testing with Docker

### Use Container for Build
```bash
sam build --use-container
```

### Specify Docker Network
```bash
sam local start-api --docker-network my-network
```

Useful for connecting to local databases.

## Logs

### View Function Logs
```bash
sam logs -n MyFunction --stack-name my-stack --tail
```

### Filter Logs
```bash
sam logs -n MyFunction --filter "ERROR"
```

### Logs from Specific Time
```bash
sam logs -n MyFunction --start-time "10min ago"
```

## Testing Best Practices

### Create Test Events
Store test events in `events/` directory:
```
events/
├── api-get-request.json
├── api-post-request.json
├── sqs-event.json
└── s3-event.json
```

### Environment Variables
- Use `env.json` for local environment variables
- Never commit secrets to version control
- Use AWS Secrets Manager for sensitive data

### Unit Tests
```python
import pytest
from src import app

def test_lambda_handler():
    event = {
        'httpMethod': 'GET',
        'path': '/items'
    }
    response = app.lambda_handler(event, None)
    assert response['statusCode'] == 200
```

### Integration Tests
Test with `sam local invoke` in CI/CD pipeline:
```bash
sam build
sam local invoke MyFunction -e tests/integration/event.json
```

## Troubleshooting

### Function Timeout
Increase timeout in template.yaml:
```yaml
Timeout: 60
```

### Memory Issues
Increase memory:
```yaml
MemorySize: 1024
```

### Docker Issues
- Ensure Docker is running
- Check Docker has enough resources
- Use `--skip-pull-image` to use cached images

### Permission Issues
Test IAM policies locally by setting AWS credentials:
```bash
export AWS_PROFILE=dev
sam local invoke MyFunction
```
