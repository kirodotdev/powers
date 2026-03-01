# Lambda Function Best Practices

## Function Definition in SAM

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/
    Handler: app.lambda_handler
    Runtime: python3.13
    Architectures:
      - arm64  # Graviton2 for better price-performance
    MemorySize: 512
    Timeout: 30
    Tracing: Active
    Environment:
      Variables:
        TABLE_NAME: !Ref MyTable
        LOG_LEVEL: INFO
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref MyTable
    Events:
      ApiEvent:
        Type: Api
        Properties:
          Path: /items
          Method: get
```

## Handler Code Structure

### Python Handler Pattern
```python
import json
import os
import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize clients outside handler (reused across invocations)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

@tracer.capture_lambda_handler
@metrics.log_metrics
@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    try:
        # Business logic here
        result = process_request(event)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        logger.exception("Error processing request")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Node.js Handler Pattern
```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand } = require('@aws-sdk/lib-dynamodb');

// Initialize outside handler
const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

exports.handler = async (event, context) => {
    try {
        // Business logic
        const result = await processRequest(event);
        
        return {
            statusCode: 200,
            body: JSON.stringify(result)
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};
```

## Performance Optimization

### Memory Configuration
- Start with 512 MB, adjust based on CloudWatch metrics
- More memory = more CPU power
- Use Lambda Power Tuning tool to find optimal configuration

### Cold Start Reduction
- Keep deployment package small
- Use Lambda Layers for dependencies
- Consider Lambda SnapStart (Java)
- Use Provisioned Concurrency for latency-sensitive functions

### Initialization Best Practices
- Initialize SDK clients outside handler
- Reuse database connections
- Cache static data in global scope
- Use /tmp for temporary file storage (512 MB - 10 GB)

## Error Handling

### Implement Retries
```yaml
EventInvokeConfig:
  MaximumRetryAttempts: 2
  MaximumEventAgeInSeconds: 3600
  DestinationConfig:
    OnFailure:
      Type: SQS
      Destination: !GetAtt DeadLetterQueue.Arn
```

### Use Dead Letter Queues
```yaml
DeadLetterQueue:
  Type: AWS::SQS::Queue
  Properties:
    MessageRetentionPeriod: 1209600  # 14 days
```

## Environment Variables

- Use for configuration, not secrets
- For secrets, use AWS Secrets Manager or Parameter Store
- Reference other resources using !Ref or !GetAtt

## Lambda Layers

```yaml
MyLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: shared-dependencies
    ContentUri: layers/
    CompatibleRuntimes:
      - python3.13
    RetentionPolicy: Retain

MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Layers:
      - !Ref MyLayer
```

## Monitoring

- Enable X-Ray tracing
- Use structured logging
- Set CloudWatch alarms for errors and throttles
- Use Lambda Insights for enhanced metrics
