# Performance Optimization

## Lambda Configuration

### Memory and CPU
- Memory range: 128 MB to 10,240 MB
- CPU scales proportionally with memory
- Use Lambda Power Tuning to find optimal configuration

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    MemorySize: 1024  # Start here, tune based on metrics
    Timeout: 30
```

### Architecture
```yaml
Architectures:
  - arm64  # Graviton2: 20% better price-performance
```

## Cold Start Optimization

### Keep Package Size Small
- Remove unnecessary dependencies
- Use Lambda Layers for shared code
- Minimize deployment package size

### Provisioned Concurrency
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    ProvisionedConcurrencyConfig:
      ProvisionedConcurrentExecutions: 5
```

Use for latency-sensitive functions only (adds cost).

### Lambda SnapStart (Java)
```yaml
MyJavaFunction:
  Type: AWS::Serverless::Function
  Properties:
    Runtime: java21
    SnapStart:
      ApplyOn: PublishedVersions
```

## Code Optimization

### Initialize Outside Handler
```python
# Good: Initialize once
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    # Use initialized resources
    table.get_item(Key={'id': '123'})
```

```python
# Bad: Initialize on every invocation
def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    table.get_item(Key={'id': '123'})
```

### Connection Pooling
```python
import urllib3

# Reuse connection pool
http = urllib3.PoolManager(maxsize=10)

def lambda_handler(event, context):
    response = http.request('GET', 'https://api.example.com')
```

### Use /tmp for Caching
```python
import os
import json

CACHE_FILE = '/tmp/cache.json'

def lambda_handler(event, context):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    else:
        cache = fetch_data()
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
```

## DynamoDB Optimization

### Use BatchGetItem
```python
# Good: Batch operation
response = dynamodb.batch_get_item(
    RequestItems={
        'MyTable': {
            'Keys': [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        }
    }
)
```

### Use Projection Expressions
```python
# Only fetch needed attributes
response = table.get_item(
    Key={'id': '123'},
    ProjectionExpression='name,email'
)
```

### Enable DAX for Read-Heavy Workloads
```yaml
DAXCluster:
  Type: AWS::DAX::Cluster
  Properties:
    NodeType: dax.t3.small
    ReplicationFactor: 3
```

## API Gateway Optimization

### Enable Caching
```yaml
ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    CacheClusterEnabled: true
    CacheClusterSize: '0.5'
    MethodSettings:
      - ResourcePath: "/*"
        HttpMethod: "GET"
        CachingEnabled: true
        CacheTtlInSeconds: 300
```

### Use HTTP API for Lower Latency
HTTP APIs have lower latency and cost than REST APIs.

## Async Processing

### Use SQS for Decoupling
```yaml
ProcessQueue:
  Type: AWS::SQS::Queue

ApiFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: api.handler
    Environment:
      Variables:
        QUEUE_URL: !Ref ProcessQueue
```

Send to queue instead of processing synchronously:
```python
sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl=os.environ['QUEUE_URL'],
    MessageBody=json.dumps(data)
)
```

## Monitoring and Tuning

### Key Metrics to Monitor
- Duration
- Memory utilization
- Cold start frequency
- Throttles
- Errors

### CloudWatch Insights Query
```
filter @type = "REPORT"
| stats avg(@duration), max(@duration), avg(@maxMemoryUsed/1024/1024) as avgMemoryUsedMB
```

### Lambda Insights
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Layers:
      - !Sub 'arn:aws:lambda:${AWS::Region}:580247275435:layer:LambdaInsightsExtension:21'
```

## Cost Optimization

### Right-Size Memory
- Monitor actual memory usage
- Reduce memory if consistently under 50% utilization
- Increase if approaching limit

### Use Arm64 Architecture
20% better price-performance than x86_64.

### Optimize Execution Time
- Reduce cold starts
- Optimize code efficiency
- Use async processing where possible

### Set Appropriate Timeouts
Don't use default 3 seconds if function needs more time, but don't set unnecessarily high timeouts.

## Performance Testing

### Load Testing with Artillery
```yaml
config:
  target: 'https://api.example.com'
  phases:
    - duration: 60
      arrivalRate: 10

scenarios:
  - flow:
      - get:
          url: "/items"
```

### Monitor During Load Tests
- Watch CloudWatch metrics
- Check for throttling
- Monitor error rates
- Observe cold start impact
