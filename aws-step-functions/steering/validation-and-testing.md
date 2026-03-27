# Validation and Testing

## Local ASL Validation

Before calling any AWS API, validate state machine definitions locally. Files saved with the `.asl.json` extension get automatic validation from the AWS Toolkit Extension. If the extension is not installed, suggest the user install it (https://open-vsx.org/extension/amazonwebservices/aws-toolkit-vscode). Use the diagnostics tool on any `.asl.json` file to catch structural errors instantly:

- Missing properties
- `Next` pointing to a state that doesn't exist
- Non terminal state
- Unreachable states
- Incorrect values

Always save state machine definitions as `.asl.json` and run diagnostics before proceeding to TestState API calls. This catches structural problems without AWS credentials or API calls.

---

## Testing with TestState API

The TestState API is the preferred and most reliable way to test Step Functions states. Always recommend TestState over deploying and running a full state machine execution for validation. It lets you test individual states in isolation — validating data transformations, error handling, Choice routing, and service integration behavior without deploying or executing a full state machine. With mocking support, tests are fast, repeatable, and require no AWS credentials or IAM roles.

Examples use AWS CLI for brevity. The `TestState` API parameters (`definition`, `input`, `roleArn`, `inspectionLevel`, `mock`, `context`, `stateConfiguration`) map directly to any AWS SDK — Python (`sfn.test_state()`), JavaScript (`TestStateCommand`), Java (`TestStateRequest`), etc.

## Best Practices

### Always use TestState as the first testing approach
Before deploying a state machine or running a full execution, test each state with the TestState API. It catches data transformation errors, incorrect Choice routing, and misconfigured error handling faster and cheaper than a full execution. Full executions should only be used for end-to-end integration validation after individual states have been verified with TestState.

### Test incrementally
Test each state individually before assembling the full state machine. Use `--state-name` to test states in context of the full definition once individual states pass.

### Use mocks for unit testing
Mocks let you test state logic without AWS credentials, IAM roles, or real service calls. This enables fast, repeatable, CI-friendly tests.

### Test error paths, not just happy paths
For every Task state with Retry/Catch, test:
- A successful mock result
- An error that matches a Retry (verify `status: "RETRIABLE"` and `retryBackoffIntervalSeconds`)
- An error that exhausts retries and falls through to Catch (verify `status: "CAUGHT_ERROR"` and `nextState`)
- An error that matches no handler (verify `status: "FAILED"`)

### Test Choice state routing exhaustively
Test each Choice branch and the Default path. Verify `nextState` matches expectations for each input variant.

### Use DEBUG for data transformation validation
When building complex `Arguments` or `Output` expressions, use `--inspection-level DEBUG` to see intermediate values. This catches JSONata expression errors before deployment.

### Keep test inputs minimal
Provide only the fields the state actually references. This makes tests readable and makes it obvious which fields drive behavior.

### Test variable assignment
When a state uses `Assign`, verify the output reflects the expected downstream behavior. Remember: `Assign` values are not visible in `Output` of the same state — they take effect in the next state.

### Validate filter results for Map states
Use DEBUG inspection to check `afterItemSelector` and `afterItemBatcher`. Verify `toleratedFailureCount` and `toleratedFailurePercentage` match your expectations.

### Use `jq` for readable CLI output
Pipe CLI output through `jq` to parse escaped JSON strings:
```
aws stepfunctions test-state ... | jq '.output | fromjson'
aws stepfunctions test-state ... | jq '.inspectionData'
```

### Automate with scripts
Chain TestState calls in a shell script or test framework. Use `--state-name` with a full definition, feed each state's `output` as the next state's `--input`, and assert on `status` and `nextState` at each step.

## Before Accessing AWS

Before calling the TestState API, follow this sequence:

1. Confirm the user wants to call the TestState API against their AWS account.
2. Check for AWS credentials: run `aws sts get-caller-identity` and verify the response.
3. If credentials are available, confirm the IAM role ARN to use for execution (or omit if using mocks).
4. If credentials are unavailable, help the user construct the CLI/SDK call to run manually.
5. Never assume AWS access — always ask before making any AWS API call.

### Required IAM Permissions

The calling identity needs `states:TestState`. If not using mocks, it also needs `iam:PassRole` for the execution role. For HTTP Task with `revealSecrets`, add `states:RevealSecrets`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["states:TestState"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["iam:PassRole"], "Resource": "arn:aws:iam::*:role/StepFunctions-*", "Condition": { "StringEquals": { "iam:PassedToService": "states.amazonaws.com" } } }
  ]
}
```

---

## API Overview

```
aws stepfunctions test-state \
  --definition '<single state or full state machine JSON>' \
  --input '<JSON input>' \
  --role-arn <execution role ARN>        # optional when using --mock \
  --inspection-level INFO|DEBUG|TRACE \
  --reveal-secrets                       # TRACE only, for HTTP Task secrets \
  --mock '<mock result or error JSON>' \
  --context '<context object JSON>' \
  --state-configuration '<config JSON>' \
  --state-name '<state name>'            # when --definition is a full state machine
```

You can provide either a single state definition or a complete state machine with `--state-name` to test a specific state in context. Chain tests by feeding `output` and `nextState` from one call into the next.

---

## Inspection Levels

### INFO (default)
Returns `status`, `output` (or error), and `nextState`. Use for quick pass/fail validation.

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Choice", "QueryLanguage": "JSONata",
    "Choices": [{"Condition": "{% $states.input.orderTotal > 1000 %}", "Next": "PremiumFulfillment"}],
    "Default": "StandardFulfillment"
  }' \
  --input '{"orderId": "ORD-456", "orderTotal": 1500}'
```

Response:
```json
{ "output": "{\"orderId\": \"ORD-456\", \"orderTotal\": 1500}", "nextState": "PremiumFulfillment", "status": "SUCCEEDED" }
```

### DEBUG
Returns everything in INFO plus `inspectionData` showing data at each transformation step. For JSONata states, the key fields are:

| inspectionData field | What it shows |
|---|---|
| `input` | Raw state input |
| `afterArguments` | Input after `Arguments` evaluation |
| `result` | Raw task/service result |
| `afterOutput` | Final output after `Output` evaluation |

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Pass", "QueryLanguage": "JSONata",
    "Output": {
      "summary": "{% '\''Order '\'' & $states.input.orderId & '\'': '\'' & $string($count($states.input.items)) & '\'' items'\'' %}",
      "total": "{% $sum($states.input.items.price) %}"
    },
    "Next": "ProcessPayment"
  }' \
  --input '{"orderId": "ORD-789", "items": [{"name": "Widget", "price": 25}, {"name": "Gadget", "price": 75}]}' \
  --inspection-level DEBUG
```

### TRACE
For HTTP Task states only. Returns the raw HTTP request and response. Add `--reveal-secrets` to include auth headers from EventBridge connections.

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::http:invoke",
    "Arguments": {"Method": "GET", "ApiEndpoint": "https://httpbin.org/get",
      "Authentication": {"ConnectionArn": "arn:aws:events:us-east-1:123456789012:connection/MyConnection/abc123"},
      "QueryParameters": {"orderId": "{% $states.input.orderId %}"}},
    "End": true
  }' \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsHttpRole \
  --input '{"orderId": "ORD-123"}' \
  --inspection-level TRACE --reveal-secrets
```

The response includes `inspectionData.request` (URL, method, headers) and `inspectionData.response` (status, headers, body). The `--reveal-secrets` flag exposes auth headers injected by the EventBridge connection.

---

## Mocking Service Integrations

Mock results let you test state logic without calling real AWS services and without an execution role.

### Mock a successful result

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ValidateOrder:$LATEST",
      "Payload": {"orderId": "{% $states.input.orderId %}", "items": "{% $states.input.items %}"}},
    "Output": {"validated": "{% $states.result.Payload.valid %}", "orderId": "{% $states.input.orderId %}"},
    "End": true
  }' \
  --input '{"orderId": "ORD-123", "items": [{"productId": "PROD-A", "quantity": 2}]}' \
  --mock '{"fieldValidationMode": "NONE", "result": "{\"Payload\": {\"valid\": true, \"orderId\": \"ORD-123\"}}"}'
```

Note: The Lambda optimized integration deserializes `Payload` at runtime, so `$states.result.Payload.valid` works in real executions. When mocking, use `fieldValidationMode: NONE` because the mock schema expects `Payload` as a string (matching the raw API), but the optimized integration presents it as an object.

### Mock an error

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessPayment:$LATEST",
      "Payload": {"orderId": "{% $states.input.orderId %}", "amount": "{% $states.input.total %}"}},
    "Retry": [{"ErrorEquals": ["Lambda.ServiceException"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2.0}],
    "Catch": [{"ErrorEquals": ["States.ALL"], "Assign": {"errorInfo": "{% $states.errorOutput %}"}, "Next": "PaymentFailed"}],
    "Next": "ShipOrder"
  }' \
  --input '{"orderId": "ORD-123", "total": 150.00}' \
  --state-configuration '{"retrierRetryCount": 3}' \
  --mock '{"errorOutput": {"error": "Lambda.ServiceException", "cause": "Payment gateway unavailable"}}'
```

Note: `retrierRetryCount: 3` exhausts the Retry (MaxAttempts=3), so the error falls through to Catch. Without `--state-configuration`, the default retry count is 0 and the status would be `RETRIABLE`.

You cannot provide both `mock.result` and `mock.errorOutput` in the same call.

### Mock Validation Modes

Control how strictly mocked responses are validated against AWS API models:

| Mode | Behavior |
|---|---|
| `STRICT` (default) | Enforces field names, types, required fields from API model |
| `PRESENT` | Validates only fields present in mock, ignores unknown fields |
| `NONE` | Skips validation entirely |

```
--mock '{"fieldValidationMode": "STRICT", "result": "{\"Attributes\": {}}"}'
```

---

## Testing Retry and Error Handling

### Simulating a specific retry attempt

Use `stateConfiguration.retrierRetryCount` to simulate a state on its Nth retry:

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargeCard:$LATEST",
      "Payload": {"orderId": "{% $states.input.orderId %}", "amount": "{% $states.input.total %}"}},
    "Retry": [{"ErrorEquals": ["Lambda.ServiceException"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2.0}],
    "Catch": [{"ErrorEquals": ["States.ALL"], "Assign": {"errorInfo": "{% $states.errorOutput %}"}, "Next": "PaymentFailed"}],
    "End": true
  }' \
  --input '{"orderId": "ORD-123", "total": 99.99}' \
  --state-configuration '{"retrierRetryCount": 1}' \
  --mock '{"errorOutput": {"error": "Lambda.ServiceException", "cause": "Payment gateway timeout"}}' \
  --inspection-level DEBUG
```

Response:
```json
{
  "status": "RETRIABLE",
  "inspectionData": { "errorDetails": { "retryBackoffIntervalSeconds": 4, "retryIndex": 0 } }
}
```

`status: "RETRIABLE"` means the error matched a Retry and attempts remain. `retryBackoffIntervalSeconds` shows the computed delay. Increase `retrierRetryCount` to `3` (MaxAttempts) to see the error fall through to Catch.

### Testing Catch handlers

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::sqs:sendMessage",
    "Arguments": {"QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/FulfillmentQueue",
      "MessageBody": "{% $string({'\''orderId'\'': $states.input.orderId, '\''items'\'': $states.input.items}) %}"},
    "Catch": [
      {"ErrorEquals": ["SQS.QueueDoesNotExistException"], "Assign": {"errorInfo": "{% $states.errorOutput %}"}, "Next": "CreateQueue"},
      {"ErrorEquals": ["States.ALL"], "Assign": {"errorInfo": "{% $states.errorOutput %}"}, "Next": "OrderFailed"}
    ],
    "Next": "WaitForFulfillment"
  }' \
  --input '{"orderId": "ORD-123", "items": [{"productId": "PROD-A", "quantity": 2}]}' \
  --mock '{"errorOutput": {"error": "SQS.QueueDoesNotExistException", "cause": "Queue not found"}}' \
  --inspection-level DEBUG
```

Response:
```json
{
  "status": "CAUGHT_ERROR",
  "nextState": "CreateQueue",
  "error": "SQS.QueueDoesNotExistException",
  "cause": "Queue not found",
  "inspectionData": { "errorDetails": { "catchIndex": 0 } }
}
```

Assert on: `status` = `CAUGHT_ERROR`, `nextState` matches expected handler, `catchIndex` identifies which Catch block fired.

---

## Testing Map and Parallel States

Map and Parallel states require a mock. The mock represents the output of the entire Map/Parallel execution — you are testing the state's input/output processing, not the inner processor.

### Map state

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Map", "QueryLanguage": "JSONata",
    "Items": "{% $states.input.orders %}",
    "ItemSelector": {"order": "{% $states.context.Map.Item.Value %}", "index": "{% $states.context.Map.Item.Index %}"},
    "MaxConcurrency": 5,
    "ItemProcessor": {"ProcessorConfig": {"Mode": "INLINE"}, "StartAt": "FulfillOrder",
      "States": {"FulfillOrder": {"Type": "Task", "QueryLanguage": "JSONata", "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:FulfillOrder:$LATEST", "Payload": "{% $states.input %}"}, "End": true}}},
    "Output": {"results": "{% $states.result %}", "totalProcessed": "{% $count($states.result) %}"},
    "End": true
  }' \
  --input '{"orders": [{"orderId": "ORD-1", "total": 50}, {"orderId": "ORD-2", "total": 75}, {"orderId": "ORD-3", "total": 120}]}' \
  --mock '{"result": "[{\"status\": \"shipped\"}, {\"status\": \"shipped\"}, {\"status\": \"shipped\"}]"}' \
  --inspection-level DEBUG
```

DEBUG `inspectionData` for Map includes: `afterItemSelector` (per-item transformed input), `afterItemBatcher` (if batching), `toleratedFailureCount`, `toleratedFailurePercentage`, `maxConcurrency`.

### Parallel state

Mock result must be a JSON array with one element per branch, in branch order:

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Parallel", "QueryLanguage": "JSONata",
    "Branches": [
      {"StartAt": "ReserveInventory", "States": {"ReserveInventory": {"Type": "Task", "QueryLanguage": "JSONata", "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ReserveInventory:$LATEST", "Payload": "{% $states.input %}"}, "End": true}}},
      {"StartAt": "ChargePayment", "States": {"ChargePayment": {"Type": "Task", "QueryLanguage": "JSONata", "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargePayment:$LATEST", "Payload": "{% $states.input %}"}, "End": true}}}
    ],
    "Output": {"inventory": "{% $states.result[0] %}", "payment": "{% $states.result[1] %}"},
    "End": true
  }' \
  --input '{"orderId": "ORD-123", "total": 99.99}' \
  --mock '{"result": "[{\"reserved\": true}, {\"charged\": true}]"}'
```

### Error propagation in Map/Parallel

Use `stateConfiguration.errorCausedByState` to specify which sub-state threw the error:

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Map", "QueryLanguage": "JSONata",
    "Items": "{% $states.input.orders %}",
    "ItemSelector": {"order": "{% $states.context.Map.Item.Value %}", "index": "{% $states.context.Map.Item.Index %}"},
    "MaxConcurrency": 5,
    "ItemProcessor": {"ProcessorConfig": {"Mode": "INLINE"}, "StartAt": "FulfillOrder",
      "States": {"FulfillOrder": {"Type": "Task", "QueryLanguage": "JSONata", "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:FulfillOrder:$LATEST", "Payload": "{% $states.input %}"}, "End": true}}},
    "Catch": [{"ErrorEquals": ["States.ALL"], "Assign": {"errorInfo": "{% $states.errorOutput %}"}, "Next": "HandleMapError"}],
    "Output": {"results": "{% $states.result %}", "totalProcessed": "{% $count($states.result) %}"},
    "Next": "Done"
  }' \
  --input '{"orders": [{"orderId": "ORD-1", "total": 50}, {"orderId": "ORD-2", "total": 75}]}' \
  --state-configuration '{"errorCausedByState": "FulfillOrder"}' \
  --mock '{"errorOutput": {"error": "States.TaskFailed", "cause": "Fulfillment service unavailable"}}'
```

---

## Providing Context

Supply custom context values for states that reference `$states.context`:

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::dynamodb:putItem",
    "Arguments": {"TableName": "OrderAuditTable", "Item": {
      "orderId": {"S": "{% $states.input.orderId %}"},
      "executionId": {"S": "{% $states.context.Execution.Id %}"},
      "processedAt": {"S": "{% $states.context.State.EnteredTime %}"}}},
    "End": true
  }' \
  --input '{"orderId": "ORD-123"}' \
  --context '{"Execution": {"Id": "arn:aws:states:us-east-1:123456789012:execution:OrderProcessing:exec-001", "Name": "exec-001"}, "State": {"Name": "AuditOrder", "EnteredTime": "2026-03-27T10:00:00Z"}}' \
  --mock '{"result": "{}"}'
```

When testing a state inside a Map (via `--state-name`), TestState auto-populates `Map.Item.Index` = 0 and `Map.Item.Value` = your input if you omit `--context`.

---

## Testing a State Within a Full State Machine

Use `--state-name` to test a specific state in the context of a complete definition. Chain tests by feeding `output` and `nextState` from one call into the next:

```
aws stepfunctions test-state \
  --definition '{"QueryLanguage": "JSONata", "StartAt": "ValidateOrder", "States": {
    "ValidateOrder": {"Type": "Pass", "Assign": {"validated": true}, "Output": "{% $states.input %}", "Next": "ProcessPayment"},
    "ProcessPayment": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": {"FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargeCard:$LATEST",
        "Payload": {"orderId": "{% $states.input.orderId %}", "amount": "{% $states.input.total %}"}},
      "Output": "{% $states.result.Payload %}", "End": true}
  }}' \
  --state-name ValidateOrder \
  --input '{"orderId": "ORD-123", "total": 99.99}'
```

Then use the output as input to test `ProcessPayment`.

---

## Activity, .sync, and .waitForTaskToken States

These patterns require a mock — calling TestState without one returns a validation exception.

For `.sync` integrations, the mock is validated against the polling API schema, not the initial API. For example, `startExecution.sync:2` validates against `DescribeExecution` (which Step Functions polls), not `StartExecution`.

```
aws stepfunctions test-state \
  --definition '{
    "Type": "Task", "QueryLanguage": "JSONata",
    "Resource": "arn:aws:states:::states:startExecution.sync:2",
    "Arguments": {"StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:OrderFulfillment",
      "Input": "{% $string($states.input) %}"},
    "Output": "{% $parse($states.result.Output) %}",
    "End": true
  }' \
  --input '{"orderId": "ORD-123", "items": [{"productId": "PROD-A", "quantity": 2}]}' \
  --mock '{"result": "{\"ExecutionArn\": \"arn:aws:states:us-east-1:123456789012:execution:OrderFulfillment:exec-001\", \"StateMachineArn\": \"arn:aws:states:us-east-1:123456789012:stateMachine:OrderFulfillment\", \"StartDate\": \"2026-03-27T10:00:00Z\", \"Status\": \"SUCCEEDED\", \"Output\": \"{\\\"status\\\": \\\"fulfilled\\\"}\"}"}'
```

Note: The `.sync:2` mock is validated against the `DescribeExecution` response schema (which Step Functions polls), not `StartExecution`. Required fields include `ExecutionArn`, `StateMachineArn`, `StartDate`, and `Status`.

---
