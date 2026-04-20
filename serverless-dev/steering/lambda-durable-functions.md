# Lambda Durable Functions

Lambda Durable Functions enable long-running workflows that can span hours, days, or up to 1 year. They automatically checkpoint state and resume execution, allowing workflows to wait for callbacks, handle retries, and maintain execution history.

## Enabling Durable Functions

Add `DurableConfig` to your function:

```yaml
OrderProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/order-processor
    Handler: index.handler
    Runtime: nodejs22.x
    Architectures:
      - arm64
    Timeout: 900                # Function timeout: 15 minutes max
    DurableConfig:
      ExecutionTimeout: 3600    # Execution timeout: up to 1 year
      RetentionPeriodInDays: 7  # Keep execution history
```

## Understanding Timeouts

**Function Timeout** (`Timeout`):
- Controls each individual Lambda invocation
- Maximum: 15 minutes (900 seconds)
- Each checkpoint/resume is a new invocation with its own timeout

**Execution Timeout** (`ExecutionTimeout`):
- Controls the entire workflow duration
- Maximum: 1 year (31,536,000 seconds)
- Workflow can pause, wait, and resume many times

**Critical**: If execution timeout > function timeout, you MUST use asynchronous invocation.

## SDK Installation

### TypeScript/JavaScript
Add to `package.json`:
```json
{
  "dependencies": {
    "@aws/durable-execution-sdk-js": "^1.0.0",
    "@aws-sdk/client-lambda": "^3.0.0"
  }
}
```

### Python
Add to `requirements.txt`:
```
aws-durable-execution-sdk-python
boto3
```

## TypeScript Build Configuration

```yaml
OrderProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/order-processor
    Handler: index.handler
    Runtime: nodejs22.x
    DurableConfig:
      ExecutionTimeout: 3600
      RetentionPeriodInDays: 7
    Metadata:
      BuildMethod: esbuild
      BuildProperties:
        EntryPoints:
          - index.ts
```

## Durable Function Code Pattern

### TypeScript Example
```typescript
import { DurableExecution } from '@aws/durable-execution-sdk-js';

export const handler = async (event: any) => {
  const execution = new DurableExecution();
  
  // Step 1: Initial processing
  const orderId = event.orderId;
  await saveOrder(orderId);
  
  // Checkpoint and wait for callback (up to 5 minutes)
  const baristaResponse = await execution.waitForCallback({
    timeoutSeconds: 300
  });
  
  // Step 2: Process callback result
  if (baristaResponse.accepted) {
    await prepareOrder(orderId);
    
    // Wait for completion callback
    const completionResponse = await execution.waitForCallback({
      timeoutSeconds: 600
    });
    
    return { status: 'completed', orderId };
  }
  
  return { status: 'rejected', orderId };
};
```

### Python Example
```python
from aws_durable_execution_sdk_python import DurableExecution

def lambda_handler(event, context):
    execution = DurableExecution()
    
    # Step 1: Initial processing
    order_id = event['orderId']
    save_order(order_id)
    
    # Checkpoint and wait for callback
    barista_response = execution.wait_for_callback(
        timeout_seconds=300
    )
    
    # Step 2: Process callback result
    if barista_response['accepted']:
        prepare_order(order_id)
        
        completion_response = execution.wait_for_callback(
            timeout_seconds=600
        )
        
        return {'status': 'completed', 'orderId': order_id}
    
    return {'status': 'rejected', 'orderId': order_id}
```

## IAM Permissions for Client Functions

### Callback Functions
```yaml
BaristaCallbackFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: src/barista-callback
    Handler: index.handler
    Policies:
      - Statement:
          - Effect: Allow
            Action:
              - lambda:SendDurableExecutionCallbackSuccess
              - lambda:SendDurableExecutionCallbackFailure
              - lambda:SendDurableExecutionCallbackHeartbeat
            Resource: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:${OrderProcessorFunction}'
```

### Monitoring Functions
```yaml
MonitoringFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      - Statement:
          - Effect: Allow
            Action:
              - lambda:GetDurableExecution
              - lambda:GetDurableExecutionHistory
              - lambda:ListDurableExecutionsByFunction
              - lambda:StopDurableExecution
            Resource: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:${OrderProcessorFunction}'
```

## Sending Callbacks

### TypeScript
```typescript
import { LambdaClient, SendDurableExecutionCallbackSuccessCommand } from '@aws-sdk/client-lambda';

const lambda = new LambdaClient({});

await lambda.send(new SendDurableExecutionCallbackSuccessCommand({
  CallbackId: callbackId,
  Result: JSON.stringify({ accepted: true })
}));
```

### Python
```python
import boto3
import json

lambda_client = boto3.client('lambda')

lambda_client.send_durable_execution_callback_success(
    CallbackId=callback_id,
    Result=json.dumps({'accepted': True})
)
```

## Event-Driven Patterns

### API Gateway Trigger (Async for Long Workflows)
```yaml
OrderProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    Timeout: 900
    DurableConfig:
      ExecutionTimeout: 86400  # 24 hours
    Events:
      ApiEvent:
        Type: Api
        Properties:
          Path: /orders
          Method: post
```

### EventBridge Trigger
```yaml
OrderProcessorFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      EventBridgeRule:
        Type: EventBridgeRule
        Properties:
          Pattern:
            source:
              - order.system
            detail-type:
              - OrderPlaced
```

### Scheduled Workflows
```yaml
DailyReportFunction:
  Type: AWS::Serverless::Function
  Properties:
    DurableConfig:
      ExecutionTimeout: 7200  # 2 hours
    Events:
      DailySchedule:
        Type: Schedule
        Properties:
          Schedule: cron(0 9 * * ? *)
```

## Local Testing

### Invoke Locally
```bash
sam local invoke OrderProcessorFunction --event events/order.json
```

### With Environment Variables
```bash
sam local invoke OrderProcessorFunction \
  --event events/order.json \
  --env-vars locals.json
```

locals.json:
```json
{
  "OrderProcessorFunction": {
    "AWS_REGION": "us-east-1",
    "ORDERS_TABLE": "CoffeeOrders"
  }
}
```

### Track Execution State
```bash
# Get execution details
sam local execution get $EXECUTION_ARN

# View execution history
sam local execution history $EXECUTION_ARN

# Stop execution
sam local execution stop $EXECUTION_ARN
```

### Test Callbacks
```bash
# Success callback
sam local callback succeed $CALLBACK_ID --result '{"accepted": true}'

# Failure callback
sam local callback fail $CALLBACK_ID --error '{"message": "Rejected"}'

# Heartbeat
sam local callback heartbeat $CALLBACK_ID
```

## Remote Testing

```bash
# Invoke deployed function
sam remote invoke OrderProcessorFunction --event events/order.json

# Invoke specific version/alias
sam remote invoke OrderProcessorFunction:prod --event events/order.json

# Get execution details
sam remote execution get $EXECUTION_ARN

# View execution history
sam remote execution history $EXECUTION_ARN
```

## Configuration Best Practices

### Execution Timeout
- Short workflows (minutes): 600-3600 seconds
- Medium workflows (hours): 3600-86400 seconds
- Long workflows (days): 86400-2592000 seconds
- Maximum: 31,536,000 seconds (1 year)

### Function Timeout
- Quick operations: 30-60 seconds
- Standard processing: 60-300 seconds
- Heavy processing: 300-900 seconds
- Maximum: 900 seconds (15 minutes)

### Retention Period
- Development: 7 days
- Production: 30-90 days
- Compliance: 90+ days

### Memory Configuration
- Start with 512 MB
- Durable functions typically use less memory than non-durable
- Adjust based on CloudWatch metrics

## Monitoring

### Enable X-Ray Tracing
```yaml
Globals:
  Function:
    Tracing: Active
```

### CloudWatch Logs Insights Query
```
fields @timestamp, @message
| filter @message like /CHECKPOINT/
| sort @timestamp desc
| limit 100
```

### CloudWatch Alarms
```yaml
ExecutionFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: OrderProcessorFailures
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref OrderProcessorFunction
```

## Common Use Cases

### Approval Workflows
Wait for human approval with timeout:
```typescript
const approval = await execution.waitForCallback({
  timeoutSeconds: 86400  // 24 hours
});
```

### Multi-Step Processing
Chain operations with checkpoints:
```typescript
await step1();
await execution.checkpoint();

await step2();
await execution.checkpoint();

await step3();
```

### Retry with Backoff
Implement custom retry logic:
```typescript
for (let i = 0; i < 3; i++) {
  try {
    await processOrder();
    break;
  } catch (error) {
    if (i === 2) throw error;
    await execution.sleep(Math.pow(2, i) * 1000);
  }
}
```

## Troubleshooting

### Validation Error on Invoke
If execution timeout > function timeout, use async invocation.

### Individual Invocation Timeout
Increase `Timeout` property (max 900 seconds).

### Workflow Timeout
Increase `ExecutionTimeout` in `DurableConfig` (max 1 year).

### Permission Denied for Callbacks
Ensure client functions have `SendDurableExecutionCallback*` permissions.

### Execution History Not Available
Check `RetentionPeriodInDays` - history may have expired.
