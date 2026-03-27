# Service Integrations in JSONata Mode

## Integration Types

Step Functions can integrate with AWS services in three patterns:

1. **Optimized integrations** — Purpose-built, recommended where available (e.g., Lambda, DynamoDB, SNS, SQS, ECS, Glue, SageMaker, etc.)
2. **AWS SDK integrations** — Call any AWS SDK API action directly
3. **HTTP Task** — Call HTTPS APIs (e.g., Stripe, Salesforce)

### Resource ARN Patterns

```
# Optimized integration
"Resource": "arn:aws:states:::servicename:apiAction"

# Optimized integration (synchronous — wait for completion)
"Resource": "arn:aws:states:::servicename:apiAction.sync"

# Optimized integration (wait for callback token)
"Resource": "arn:aws:states:::servicename:apiAction.waitForTaskToken"

# AWS SDK integration
"Resource": "arn:aws:states:::aws-sdk:serviceName:apiAction"
```

---

## Lambda Function

### Optimized Integration (Recommended)

```json
"InvokeFunction": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction:$LATEST",
    "Payload": {
      "orderId": "{% $states.input.orderId %}",
      "customer": "{% $states.input.customer %}"
    }
  },
  "Output": "{% $states.result.Payload %}",
  "Next": "NextState"
}
```

Always include a version qualifier (`:$LATEST`, `:1`, or an alias like `:prod`) on the function ARN.

The result is wrapped in a `Payload` field, so use `$states.result.Payload` to access the Lambda return value.

### SDK Integration

```json
"InvokeViaSDK": {
  "Type": "Task",
  "Resource": "arn:aws:states:::aws-sdk:lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction",
    "Payload": "{% $string($states.input) %}"
  },
  "Next": "NextState"
}
```

---

## DynamoDB

### GetItem

```json
"GetUser": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:getItem",
  "Arguments": {
    "TableName": "UsersTable",
    "Key": {
      "userId": {
        "S": "{% $states.input.userId %}"
      }
    }
  },
  "Assign": {
    "user": "{% $states.result.Item %}"
  },
  "Output": "{% $states.result.Item %}",
  "Next": "ProcessUser"
}
```

### PutItem

```json
"SaveOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:putItem",
  "Arguments": {
    "TableName": "OrdersTable",
    "Item": {
      "orderId": {
        "S": "{% $orderId %}"
      },
      "status": {
        "S": "processing"
      },
      "total": {
        "N": "{% $string($states.input.total) %}"
      },
      "createdAt": {
        "S": "{% $now() %}"
      }
    }
  },
  "Next": "ProcessOrder"
}
```

### UpdateItem

```json
"UpdateStatus": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:updateItem",
  "Arguments": {
    "TableName": "OrdersTable",
    "Key": {
      "orderId": {
        "S": "{% $orderId %}"
      }
    },
    "UpdateExpression": "SET #s = :status, updatedAt = :time",
    "ExpressionAttributeNames": {
      "#s": "status"
    },
    "ExpressionAttributeValues": {
      ":status": {
        "S": "{% $states.input.newStatus %}"
      },
      ":time": {
        "S": "{% $now() %}"
      }
    }
  },
  "Next": "Done"
}
```

### Query

```json
"QueryOrders": {
  "Type": "Task",
  "Resource": "arn:aws:states:::aws-sdk:dynamodb:query",
  "Arguments": {
    "TableName": "OrdersTable",
    "KeyConditionExpression": "customerId = :cid",
    "ExpressionAttributeValues": {
      ":cid": {
        "S": "{% $states.input.customerId %}"
      }
    }
  },
  "Output": "{% $states.result.Items %}",
  "Next": "ProcessOrders"
}
```

---

## SNS (Simple Notification Service)

### Publish Message

```json
"SendNotification": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Arguments": {
    "TopicArn": "arn:aws:sns:us-east-1:123456789012:OrderNotifications",
    "Message": "{% 'Order ' & $orderId & ' has been processed successfully.' %}",
    "Subject": "Order Confirmation"
  },
  "Next": "Done"
}
```

### Publish with JSON Message

```json
"SendStructuredNotification": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Arguments": {
    "TopicArn": "arn:aws:sns:us-east-1:123456789012:Alerts",
    "Message": "{% $string({'orderId': $orderId, 'status': $states.input.status, 'timestamp': $now()}) %}"
  },
  "Next": "Done"
}
```

---

## SQS (Simple Queue Service)

### Send Message

```json
"QueueMessage": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ProcessingQueue",
    "MessageBody": "{% $string($states.input) %}"
  },
  "Next": "Done"
}
```

### Send Message with Wait for Task Token

```json
"WaitForApproval": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
    "MessageBody": "{% $string({'taskToken': $states.context.Task.Token, 'orderId': $orderId, 'amount': $states.input.amount}) %}"
  },
  "TimeoutSeconds": 86400,
  "Next": "ProcessApproval"
}
```

The execution pauses until an external system calls `SendTaskSuccess` or `SendTaskFailure` with the task token.

---

## Step Functions (Nested Execution)

### Start Execution (Synchronous)

```json
"RunSubWorkflow": {
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution.sync:2",
  "Arguments": {
    "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:ChildWorkflow",
    "Input": "{% $states.input %}"
  },
  "Output": "{% $parse($states.result.Output) %}",
  "Next": "ProcessSubResult"
}
```

Note: The `.sync:2` suffix waits for completion. The child output is a JSON string in `$states.result.Output`, so use `$parse()` to deserialize it.

### Start Execution (Async — Fire and Forget)

```json
"StartAsync": {
  "Type": "Task",
  "Resource": "arn:aws:states:::states:startExecution",
  "Arguments": {
    "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:AsyncWorkflow",
    "Input": "{% $string($states.input) %}"
  },
  "Next": "Continue"
}
```

---

## EventBridge

### Put Events

```json
"EmitEvent": {
  "Type": "Task",
  "Resource": "arn:aws:states:::events:putEvents",
  "Arguments": {
    "Entries": [
      {
        "Source": "my.application",
        "DetailType": "OrderProcessed",
        "Detail": "{% $string({'orderId': $orderId, 'status': 'completed'}) %}",
        "EventBusName": "default"
      }
    ]
  },
  "Next": "Done"
}
```

---

## ECS / Fargate

### Run Task (Synchronous)

```json
"RunContainer": {
  "Type": "Task",
  "Resource": "arn:aws:states:::ecs:runTask.sync",
  "Arguments": {
    "LaunchType": "FARGATE",
    "Cluster": "arn:aws:ecs:us-east-1:123456789012:cluster/MyCluster",
    "TaskDefinition": "arn:aws:ecs:us-east-1:123456789012:task-definition/MyTask:1",
    "NetworkConfiguration": {
      "AwsvpcConfiguration": {
        "Subnets": ["subnet-abc123"],
        "SecurityGroups": ["sg-abc123"],
        "AssignPublicIp": "ENABLED"
      }
    },
    "Overrides": {
      "ContainerOverrides": [
        {
          "Name": "my-container",
          "Environment": [
            {
              "Name": "ORDER_ID",
              "Value": "{% $orderId %}"
            }
          ]
        }
      ]
    }
  },
  "TimeoutSeconds": 600,
  "Next": "Done"
}
```

---

## AWS Glue

### Start Job Run (Synchronous)

```json
"RunGlueJob": {
  "Type": "Task",
  "Resource": "arn:aws:states:::glue:startJobRun.sync",
  "Arguments": {
    "JobName": "my-etl-job",
    "Arguments": {
      "--input_path": "{% $states.input.inputPath %}",
      "--output_path": "{% $states.input.outputPath %}"
    }
  },
  "TimeoutSeconds": 3600,
  "Next": "Done"
}
```

---

## Amazon Bedrock

### Invoke Model

```json
"InvokeModel": {
  "Type": "Task",
  "Resource": "arn:aws:states:::bedrock:invokeModel",
  "Arguments": {
    "ModelId": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
    "ContentType": "application/json",
    "Accept": "application/json",
    "Body": {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 1024,
      "messages": [
        {
          "role": "user",
          "content": "{% $states.input.prompt %}"
        }
      ]
    }
  },
  "Output": "{% $states.result.Body %}",
  "Next": "ProcessResponse"
}
```

---

## S3

### GetObject

```json
"ReadFile": {
  "Type": "Task",
  "Resource": "arn:aws:states:::aws-sdk:s3:getObject",
  "Arguments": {
    "Bucket": "my-bucket",
    "Key": "{% $states.input.filePath %}"
  },
  "Output": "{% $states.result.Body %}",
  "Next": "ProcessFile"
}
```

### PutObject

```json
"WriteFile": {
  "Type": "Task",
  "Resource": "arn:aws:states:::aws-sdk:s3:putObject",
  "Arguments": {
    "Bucket": "my-bucket",
    "Key": "{% 'results/' & $orderId & '.json' %}",
    "Body": "{% $string($states.input.results) %}"
  },
  "Next": "Done"
}
```

---

## Cross-Account Access

Use the `Credentials` field to assume a role in another account:

```json
"CrossAccountCall": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Credentials": {
    "RoleArn": "arn:aws:iam::111122223333:role/CrossAccountRole"
  },
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:111122223333:function:RemoteFunction:$LATEST",
    "Payload": "{% $states.input %}"
  },
  "Output": "{% $states.result.Payload %}",
  "Next": "Done"
}
```

---

## Synchronous vs Asynchronous Patterns

| Pattern | Resource Suffix | Behavior |
|---------|----------------|----------|
| Request-Response | (none) | Call API and continue immediately |
| Synchronous | `.sync` | Wait for task to complete |
| Wait for Callback | `.waitForTaskToken` | Pause until external callback |

### When to Use Each

- **Request-Response**: Fire-and-forget operations (start a process, send a message)
- **Synchronous (`.sync`)**: When you need the result before continuing (run ECS task, execute child workflow, run Glue job)
- **Wait for Callback (`.waitForTaskToken`)**: Human approval, external system processing, long-running async operations

### Callback Pattern Example

```json
"WaitForHumanApproval": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
    "MessageBody": "{% $string({'taskToken': $states.context.Task.Token, 'request': $states.input}) %}"
  },
  "TimeoutSeconds": 604800,
  "Catch": [
    {
      "ErrorEquals": ["States.Timeout"],
      "Output": {
        "status": "approval_timeout"
      },
      "Next": "HandleTimeout"
    }
  ],
  "Next": "ApprovalReceived"
}
```

The external system must call `SendTaskSuccess` or `SendTaskFailure` with the task token to resume execution.
