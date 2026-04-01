---
name: "aws-step-functions"
displayName: "AWS Step Functions"
description: "Build workflows with AWS Step Functions state machines using the JSONata query language. Covers Amazon States Language (ASL) structure, all state types, variables, data transformation, error handling, and service integrations."
keywords: ["step functions", "state machine", "serverless", "jsonata", "asl", "amazon states language", "workflow", "orchestration"]
author: "AWS"
---

# AWS Step Functions

AWS Step Functions provides visual workflow orchestration with native integrations to 9,000+ API actions across 200+ AWS services. Define workflows as state machines in Amazon States Language using the JSONata query language instead of legacy JSONPath.

## Overview

AWS Step Functions uses Amazon States Language (ASL) to define state machines as JSON. With AWS Step Functions, you can create workflows, also called State machines, to build distributed applications, automate processes, orchestrate microservices, and create data and machine learning pipelines.

This power provides comprehensive guidance for writing state machines in ASL, covering:
- ASL structure and JSONata expression syntax
- Details on the eight available workflow states
- The `$states` reserved variable
- Workflow variables with `Assign`
- Error handling
- AWS Service integration patterns
- Data transformation and architecture examples
- Validation and testing of ASL structure
- How to migrate from JSONPath to JSONata

## When to Load Steering Files

Load the appropriate steering file based on what the user is working on:

- **ASL structure**, **state types**, **Task**, **Pass**, **Choice**, **Wait**, **Succeed**, **Fail**, **Parallel**, **Map** → see `asl-state-types.md`
- **Variables**, **Assign**, **data passing**, **scope**, **$states**, **input**, **output**, **Arguments**, **Output**, **data transformation** → see `variables-and-data.md`
- **Error handling**, **Retry**, **Catch**, **fallback**, **error codes**, **States.Timeout**, **States.ALL** → see `error-handling.md`
- **Service integrations**, **Lambda invoke**, **DynamoDB**, **SNS**, **SQS**, **SDK integrations**, **Resource ARN**, **sync**, **async** → see `service-integrations.md`
- **Converting from JSONPath**, **migration**, **JSONPath to JSONata**, **InputPath**, **Parameters**, **ResultSelector**, **ResultPath**, **OutputPath**, **intrinsic functions**, **Iterator**, **payload template** → see `converting-from-jsonpath-to-jsonata.md`
- **Validation**, **linting**, **testing**, **TestState**, **test state**, **mock**, **mocking**, **unit test**, **inspection level**, **DEBUG**, **TRACE**, **validate state**, **test in isolation** → see `validation-and-testing.md`

## Quick Reference

### Standard vs Express Workflows

|                                   | Standard                             | Express                                     |
| --------------------------------- | ------------------------------------ | ------------------------------------------- |
| **Max duration**                  | 1 year                               | 5 minutes                                   |
| **Execution semantics**           | Exactly-once                         | At-least-once (async) / At-most-once (sync) |
| **Execution history**             | Retained 90 days, queryable via API  | CloudWatch Logs only                        |
| **Max throughput**                | 2,000 exec/sec                       | 100,000 exec/sec                            |
| **Pricing model**                 | Per state transition                 | Per execution count + duration              |
| **`.sync` / `.waitForTaskToken`** | Supported                            | Not supported                               |
| **Best for**                      | Auditable, non-idempotent operations | High-volume, idempotent event processing    |

**Choose Standard** for: payment processing, order fulfillment, compliance workflows, anything that must never execute twice.

**Choose Express** for: IoT data ingestion, streaming transformations, mobile backends, high-throughput short-lived processing.

### Key State Types

| State              | Purpose                                                                              |
| ------------------ | ------------------------------------------------------------------------------------ |
| `Task`             | Execute work — invoke Lambda, call any AWS service via SDK integration               |
| `Choice`           | Branch based on input data conditions (no `Next` required on branches)               |
| `Parallel`         | Execute multiple branches concurrently; waits for all branches to complete           |
| `Map`              | Iterate over an array; use Distributed Map mode for up to 10M items from S3/DynamoDB |
| `Wait`             | Pause for a fixed duration or until a specific timestamp                             |
| `Pass`             | Pass input to output, optionally injecting or transforming data                      |
| `Succeed` / `Fail` | End execution successfully or with an error and cause                                |

### Setting the State Machine Query Language

JSONata is the modern, preferred way to reference and transform data in ASL. It replaces the five JSONPath I/O fields (`InputPath`, `Parameters`, `ResultSelector`, `ResultPath`, `OutputPath`) with just two: `Arguments` (inputs) and `Output`.

**Enable at the top level** to apply to all states:

```json
{ "QueryLanguage": "JSONata", "StartAt": "...", "States": {...} }
```

**Or per-state** to migrate from JSONPath incrementally:

```json
{ "Type": "Task", "QueryLanguage": "JSONata", ... }
```

**JSONata Expression syntax** 
ADD MORE COMPLEX EXAMPLE
Wrap expressions in `{% %}`:
```json
"Arguments": {
  "userId": "{% $states.input.user.id %}",
  "greeting": "{% 'Hello, ' & $states.input.user.name %}",
  "total": "{% $sum($states.input.items.price) %}"
}
```

**Built-in Step Functions JSONata functions:**

| Function | Purpose |
|----------|---------|
| `$partition(array, size)` | Partition array into chunks |
| `$range(start, end, step)` | Generate array of values |
| `$hash(data, algorithm)` | Calculate hash (MD5, SHA-1, SHA-256, SHA-384, SHA-512) |
| `$random([seed])` | Random number 0 ≤ n < 1, optional seed |
| `$uuid()` | Generate v4 UUID |
| `$parse(jsonString)` | Deserialize JSON string |

**JSONPath is still supported** and is the default if `QueryLanguage` is omitted — existing state machines do not need to be migrated.

### The `$states` Reserved Variable (JSONata only)

```
$states.input        → Original state input
$states.result       → Task/Parallel/Map result (on success)
$states.errorOutput  → Error output (only in Catch)
$states.context      → Execution context object
```

### Key Fields in Step Functions (JSONata only)

| Field | Purpose | Available In |
|-------|---------|-------------|
| `Arguments` | Input to task/branches | Task, Parallel |
| `Output` | Transform state output | All except Fail |
| `Assign` | Store workflow variables | All except Succeed, Fail |
| `Condition` | Boolean branching | Choice rules |
| `Items` | Array for iteration | Map |

### Functions Provided by Step Functions (JSONata only)

| Function | Purpose |
|----------|---------|
| `$partition(array, size)` | Partition array into chunks |
| `$range(start, end, step)` | Generate array of values |
| `$hash(data, algorithm)` | Calculate hash (MD5, SHA-1, SHA-256, SHA-384, SHA-512) |
| `$random([seed])` | Random number 0 ≤ n < 1, optional seed |
| `$uuid()` | Generate v4 UUID |
| `$parse(jsonString)` | Deserialize JSON string |

Plus all [built-in JSONata functions](https://github.com/jsonata-js/jsonata/tree/master/docs)

### Minimal Complete Example

```json
{
  "Comment": "Order processing workflow",
  "QueryLanguage": "JSONata",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:states:::dynamodb:getItem",
      "Arguments": {
        "TableName": "OrdersTable",
        "Key": {
          "orderId": {
            "S": "{% $states.input.orderId %}"
          }
        }
      },
      "Assign": {
        "orderId": "{% $states.input.orderId %}"
      },
      "Output": "{% $states.result.Item %}",
      "Next": "CheckStock"
    },
    "CheckStock": {
      "Type": "Choice",
      "Choices": [
        {
          "Condition": "{% $states.input.inStock = true %}",
          "Next": "ProcessPayment"
        }
      ],
      "Default": "OutOfStock"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sqs:sendMessage",
      "Arguments": {
        "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/PaymentQueue",
        "MessageBody": "{% $string({'orderId': $orderId, 'amount': $states.input.total.N}) %}"
      },
      "Output": {
        "orderId": "{% $orderId %}",
        "messageId": "{% $states.result.MessageId %}"
      },
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "End": true
    },
    "OutOfStock": {
      "Type": "Fail",
      "Error": "OutOfStockError",
      "Cause": "Requested item is out of stock"
    }
  }
}
```

## Best Practices

- Set `"QueryLanguage": "JSONata"` at the top level for new state machines unless JSONPath is mandatory
- Keep `Output` minimal — only include what the state immediately after the current state needs
- Use `Assign` to store variables needed in later states instead of threading it through Output
- Use `$states.input` to reference original state input
- Remember: `Assign` and `Output` are evaluated in parallel — variable assignments in `Assign` are NOT available in `Output` of the same state
- All JSONata expressions must produce a defined value — `$data.nonExistentField` throws `States.QueryEvaluationError`
- Use `$states.context.Execution.Input` to access the original workflow input from any state
- Save state machine definitions with `.asl.json` extension when working outside the console
- Prefer the optimized Lambda integration (`arn:aws:states:::lambda:invoke`) over the SDK integration

## Troubleshooting

### Common Errors

- `States.QueryEvaluationError` — JSONata expression failed. Check for type errors, undefined fields, or out-of-range values.
- Mixing JSONPath fields with JSONata fields in the same state.
- Using `$` or `$$` at the top level of a JSONata expression — use `$states.input` instead.
- Forgetting `{% %}` delimiters around JSONata expressions — the string will be treated as a literal.
- Assigning variables in `Assign` and expecting them in `Output` of the same state — new values only take effect in the next state.

## Resources

- [ASL Specification](https://states-language.net/spec.html)
- [Transforming data with JSONata in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/transforming-data.html)
- [Passing data between states with variables](https://docs.aws.amazon.com/step-functions/latest/dg/workflow-variables.html)
- [JSONata documentation](https://docs.jsonata.org/overview.html)
- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
