# Event-Driven Architecture Patterns

## EventBridge

### EventBridge Rule
```yaml
MyEventRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: default
    EventPattern:
      source:
        - my.application
      detail-type:
        - Order Placed
    Targets:
      - Arn: !GetAtt ProcessOrderFunction.Arn
        Id: ProcessOrderTarget

ProcessOrderFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      EventBridgeRule:
        Type: EventBridgeRule
        Properties:
          Pattern:
            source:
              - my.application
            detail-type:
              - Order Placed
```

### Publishing Events
```python
import boto3
import json

events = boto3.client('events')

events.put_events(
    Entries=[{
        'Source': 'my.application',
        'DetailType': 'Order Placed',
        'Detail': json.dumps({
            'orderId': '12345',
            'amount': 99.99
        })
    }]
)
```

## SQS Queue Integration

```yaml
MyQueue:
  Type: AWS::SQS::Queue
  Properties:
    VisibilityTimeout: 300
    MessageRetentionPeriod: 1209600
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt MyDLQ.Arn
      maxReceiveCount: 3

MyDLQ:
  Type: AWS::SQS::Queue

ProcessQueueFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      SQSEvent:
        Type: SQS
        Properties:
          Queue: !GetAtt MyQueue.Arn
          BatchSize: 10
          MaximumBatchingWindowInSeconds: 5
```

### SQS Handler Pattern
```python
def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        # Process message
        process_message(body)
```

## SNS Topic Integration

```yaml
MyTopic:
  Type: AWS::SNS::Topic

NotifyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      SNSEvent:
        Type: SNS
        Properties:
          Topic: !Ref MyTopic
```

### Publishing to SNS
```python
sns = boto3.client('sns')

sns.publish(
    TopicArn='arn:aws:sns:region:account:topic',
    Message=json.dumps({'event': 'data'}),
    Subject='Notification'
)
```

## S3 Event Notifications

```yaml
ProcessS3Function:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      S3Event:
        Type: S3
        Properties:
          Bucket: !Ref MyBucket
          Events: s3:ObjectCreated:*
          Filter:
            S3Key:
              Rules:
                - Name: prefix
                  Value: uploads/
                - Name: suffix
                  Value: .jpg

MyBucket:
  Type: AWS::S3::Bucket
```

### S3 Handler Pattern
```python
def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        # Process S3 object
```

## DynamoDB Streams

```yaml
MyTable:
  Type: AWS::DynamoDB::Table
  Properties:
    StreamSpecification:
      StreamViewType: NEW_AND_OLD_IMAGES

ProcessStreamFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      DynamoDBStream:
        Type: DynamoDB
        Properties:
          Stream: !GetAtt MyTable.StreamArn
          StartingPosition: LATEST
          BatchSize: 100
          MaximumBatchingWindowInSeconds: 10
```

## Step Functions

```yaml
MyStateMachine:
  Type: AWS::Serverless::StateMachine
  Properties:
    DefinitionUri: statemachine/workflow.asl.json
    Policies:
      - LambdaInvokePolicy:
          FunctionName: !Ref ProcessFunction
    Events:
      ApiEvent:
        Type: Api
        Properties:
          Path: /workflow
          Method: post
```

## Event-Driven Best Practices

### Idempotency
- Use idempotency tokens for duplicate prevention
- Store processed event IDs in DynamoDB

### Error Handling
- Configure DLQs for all async invocations
- Set appropriate retry policies
- Monitor DLQ depth with CloudWatch alarms

### Event Schema
- Use consistent event structure
- Include correlation IDs for tracing
- Version your event schemas

### Decoupling
- Use queues/topics between services
- Avoid direct service-to-service calls
- Design for eventual consistency
