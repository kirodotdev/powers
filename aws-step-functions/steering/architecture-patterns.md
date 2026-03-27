# Architecture Patterns (JSONata Mode)

## Polling Loop (Wait → Check → Choice)

Many AWS operations are asynchronous — you start them and then poll until they complete. The pattern is: initial wait → call describe/status API → check result → short wait → loop back.

```json
"SubmitOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/FulfillmentQueue",
    "MessageBody": "{% $string({'orderId': $orderId, 'items': $states.input.items}) %}"
  },
  "Assign": { "fulfillmentOrderId": "{% $orderId %}" },
  "Next": "InitialWaitForFulfillment"
},
"InitialWaitForFulfillment": {
  "Type": "Wait",
  "Seconds": 300,
  "Next": "CheckFulfillmentStatus"
},
"CheckFulfillmentStatus": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:getItem",
  "Arguments": {
    "TableName": "OrdersTable",
    "Key": { "orderId": { "S": "{% $fulfillmentOrderId %}" } }
  },
  "Assign": { "orderStatus": "{% $states.result.Item.status.S %}" },
  "Next": "EvaluateFulfillment",
  "Retry": [
    { "ErrorEquals": ["States.TaskFailed", "ThrottlingException"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2 }
  ]
},
"EvaluateFulfillment": {
  "Type": "Choice",
  "Choices": [
    { "Condition": "{% $orderStatus = 'fulfilled' %}", "Next": "FulfillmentComplete" },
    { "Condition": "{% $orderStatus in ['failed', 'cancelled'] %}", "Next": "FulfillmentFailed" }
  ],
  "Default": "WaitBeforeNextPoll"
},
"WaitBeforeNextPoll": {
  "Type": "Wait",
  "Seconds": 60,
  "Next": "CheckFulfillmentStatus"
}
```

Key elements:
- Initial longer wait gives the operation time to start. Shorter poll interval for subsequent checks.
- Choice state routes to success, failure, or back to the wait loop.
- Always add Retry on the status-check Task to handle transient API errors.
- Consider adding `TimeoutSeconds` on the state machine or a counter variable to prevent infinite polling.

---

## Compensation / Saga Pattern

Step Functions has no built-in rollback. The saga pattern chains compensating actions in reverse order. Each forward step has a Catch that records which step failed, then routes to the appropriate compensation entry point.

```json
"ReserveInventory": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:updateItem",
  "Arguments": {
    "TableName": "InventoryTable",
    "Key": { "productId": { "S": "{% $states.input.productId %}" } },
    "UpdateExpression": "SET reserved = reserved + :qty",
    "ExpressionAttributeValues": { ":qty": { "N": "{% $string($states.input.quantity) %}" } }
  },
  "Assign": { "reservedQty": "{% $states.input.quantity %}" },
  "Catch": [
    { "ErrorEquals": ["States.ALL"], "Assign": { "failedStep": "ReserveInventory", "errorInfo": "{% $states.errorOutput %}" }, "Next": "OrderFailed" }
  ],
  "Next": "ChargePayment"
},
"ChargePayment": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargeCard:$LATEST",
    "Payload": { "orderId": "{% $orderId %}", "amount": "{% $states.input.total %}" }
  },
  "Assign": { "chargeId": "{% $states.result.Payload.chargeId %}" },
  "Output": "{% $states.result.Payload %}",
  "Catch": [
    { "ErrorEquals": ["States.ALL"], "Assign": { "failedStep": "ChargePayment", "errorInfo": "{% $states.errorOutput %}" }, "Next": "ReleaseInventory" }
  ],
  "Next": "ShipOrder"
},
"ShipOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ShipOrder:$LATEST",
    "Payload": { "orderId": "{% $orderId %}" }
  },
  "Catch": [
    { "ErrorEquals": ["States.ALL"], "Assign": { "failedStep": "ShipOrder", "errorInfo": "{% $states.errorOutput %}" }, "Next": "RefundPayment" }
  ],
  "Next": "OrderComplete"
},
"RefundPayment": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:RefundCharge:$LATEST",
    "Payload": { "chargeId": "{% $chargeId %}", "reason": "{% $errorInfo.Cause %}" }
  },
  "Next": "ReleaseInventory"
},
"ReleaseInventory": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:updateItem",
  "Arguments": {
    "TableName": "InventoryTable",
    "Key": { "productId": { "S": "{% $states.input.productId %}" } },
    "UpdateExpression": "SET reserved = reserved - :qty",
    "ExpressionAttributeValues": { ":qty": { "N": "{% $string($reservedQty) %}" } }
  },
  "Next": "OrderFailed"
},
"OrderFailed": {
  "Type": "Fail",
  "Error": "{% $failedStep & 'Error' %}",
  "Cause": "{% 'Order ' & $orderId & ' failed at ' & $failedStep & ': ' & ($exists($errorInfo.Cause) ? $errorInfo.Cause : 'Unknown') %}"
}
```

Compensation chain: `ReserveInventory` fails → `OrderFailed`. `ChargePayment` fails → `ReleaseInventory` → `OrderFailed`. `ShipOrder` fails → `RefundPayment` → `ReleaseInventory` → `OrderFailed`. Each Catch records `$failedStep` and `$errorInfo`. Compensation states use variables from forward steps (`$chargeId`, `$reservedQty`) to know what to undo.

---

## Nested Map / Parallel Structures

Map, Parallel, and Task states nest in any combination. The key constraint is understanding variable scope and data flow at each nesting boundary.

```json
"ProcessAllOrders": {
  "Type": "Map",
  "Items": "{% $states.input.orders %}",
  "MaxConcurrency": 5,
  "ItemProcessor": {
    "ProcessorConfig": { "Mode": "INLINE" },
    "StartAt": "ProcessSingleOrder",
    "States": {
      "ProcessSingleOrder": {
        "Type": "Parallel",
        "Branches": [
          {
            "StartAt": "ValidatePayment",
            "States": {
              "ValidatePayment": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Arguments": {
                  "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ValidatePayment:$LATEST",
                  "Payload": "{% $states.input %}"
                },
                "Output": "{% $states.result.Payload %}",
                "End": true
              }
            }
          },
          {
            "StartAt": "CheckInventory",
            "States": {
              "CheckInventory": {
                "Type": "Task",
                "Resource": "arn:aws:states:::dynamodb:getItem",
                "Arguments": {
                  "TableName": "InventoryTable",
                  "Key": { "productId": { "S": "{% $states.input.productId %}" } }
                },
                "Output": "{% $states.result.Item %}",
                "End": true
              }
            }
          }
        ],
        "Output": { "payment": "{% $states.result[0] %}", "inventory": "{% $states.result[1] %}" },
        "End": true
      }
    }
  },
  "Assign": { "orderResults": "{% $states.result %}" },
  "Next": "Summarize"
}
```

### Variable Scoping Across Nesting Levels

Each nesting level creates a new scope. Inner scopes can READ outer variables but CANNOT ASSIGN to them — use `Output` on terminal states to pass data back up. Parallel branches and Map iterations are isolated from each other. Variable names must be unique across all nesting levels (no shadowing). Exception: Distributed Map (`"Mode": "DISTRIBUTED"`) cannot read outer scope variables at all.

Data flows down via state input (use `ItemSelector` for Map, `Arguments` for Parallel) and up via `Output` on terminal states. Parallel result is an array per branch; Map result is an array per iteration.

---

## Scatter-Gather with Partial Results

When calling unreliable external APIs per-item, use `ToleratedFailurePercentage` on a Map to continue with whatever succeeded, then post-process the results to separate successes from failures. Failed iterations return objects with `Error` and `Cause` fields.

```json
"CallExternalAPIs": {
  "Type": "Map",
  "Items": "{% $states.input.records %}",
  "MaxConcurrency": 10,
  "ToleratedFailurePercentage": 100,
  "ItemProcessor": {
    "ProcessorConfig": { "Mode": "INLINE" },
    "StartAt": "CallAPI",
    "States": {
      "CallAPI": {
        "Type": "Task",
        "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": {
          "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:CallExternalAPI:$LATEST",
          "Payload": "{% $states.input %}"
        },
        "Output": "{% $states.result.Payload %}",
        "Retry": [
          { "ErrorEquals": ["States.TaskFailed"], "IntervalSeconds": 2, "MaxAttempts": 2, "BackoffRate": 2.0, "JitterStrategy": "FULL" }
        ],
        "End": true
      }
    }
  },
  "Next": "SplitResults"
},
"SplitResults": {
  "Type": "Pass",
  "Assign": {
    "successes": "{% ( $s := $states.input[$not($exists(Error))]; $type($s) = 'array' ? $s : $exists($s) ? [$s] : [] ) %}",
    "failures": "{% ( $f := $states.input[$exists(Error)]; $type($f) = 'array' ? $f : $exists($f) ? [$f] : [] ) %}"
  },
  "Output": {
    "successes": "{% ( $s := $states.input[$not($exists(Error))]; $type($s) = 'array' ? $s : $exists($s) ? [$s] : [] ) %}",
    "failures": "{% ( $f := $states.input[$exists(Error)]; $type($f) = 'array' ? $f : $exists($f) ? [$f] : [] ) %}",
    "totalProcessed": "{% $count($states.input) %}"
  },
  "Next": "EvaluateResults"
},
"EvaluateResults": {
  "Type": "Choice",
  "Choices": [
    { "Condition": "{% $count($successes) = 0 %}", "Next": "AllFailed" }
  ],
  "Default": "ProcessSuccesses"
}
```

Key elements:
- `ToleratedFailurePercentage: 100` lets the Map complete even if every item fails. Lower the threshold to bail out early.
- Filter on `$exists(Error)` to separate failed from successful iterations.
- Guard filtered results with the `$type`/`$exists`/`[]` pattern — JSONata returns a single object (not a 1-element array) when exactly one item matches, and undefined when nothing matches.

---

## Semaphore / Concurrency Lock

Step Functions has no native mutual exclusion. Use DynamoDB conditional writes as a distributed lock when only one execution should process a given resource at a time. Pattern: acquire lock → do work → release lock, with Catch ensuring release on failure.

```json
"AcquireLock": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:putItem",
  "Arguments": {
    "TableName": "LocksTable",
    "Item": {
      "lockId": { "S": "{% $states.input.customerId %}" },
      "executionId": { "S": "{% $states.context.Execution.Id %}" },
      "expiresAt": { "N": "{% $string($toMillis($now()) + 900000) %}" }
    },
    "ConditionExpression": "attribute_not_exists(lockId) OR expiresAt < :now",
    "ExpressionAttributeValues": {
      ":now": { "N": "{% $string($toMillis($now())) %}" }
    }
  },
  "Retry": [
    { "ErrorEquals": ["DynamoDB.ConditionalCheckFailedException"], "IntervalSeconds": 5, "MaxAttempts": 12, "BackoffRate": 1.5, "JitterStrategy": "FULL" }
  ],
  "Catch": [
    { "ErrorEquals": ["DynamoDB.ConditionalCheckFailedException"], "Assign": { "lockError": "{% $states.errorOutput %}" }, "Next": "LockUnavailable" }
  ],
  "Next": "DoProtectedWork"
},
"DoProtectedWork": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessCustomer:$LATEST",
    "Payload": "{% $states.input %}"
  },
  "Output": "{% $states.result.Payload %}",
  "Catch": [
    { "ErrorEquals": ["States.ALL"], "Assign": { "workError": "{% $states.errorOutput %}" }, "Next": "ReleaseLock" }
  ],
  "Next": "ReleaseLock"
},
"ReleaseLock": {
  "Type": "Task",
  "Resource": "arn:aws:states:::dynamodb:deleteItem",
  "Arguments": {
    "TableName": "LocksTable",
    "Key": { "lockId": { "S": "{% $states.input.customerId %}" } },
    "ConditionExpression": "executionId = :execId",
    "ExpressionAttributeValues": { ":execId": { "S": "{% $states.context.Execution.Id %}" } }
  },
  "Retry": [
    { "ErrorEquals": ["States.ALL"], "IntervalSeconds": 1, "MaxAttempts": 3, "BackoffRate": 2.0 }
  ],
  "Next": "CheckWorkResult"
},
"CheckWorkResult": {
  "Type": "Choice",
  "Choices": [
    { "Condition": "{% $exists($workError) %}", "Next": "WorkFailed" }
  ],
  "Default": "Done"
},
"LockUnavailable": {
  "Type": "Fail",
  "Error": "LockContention",
  "Cause": "{% 'Could not acquire lock for ' & $states.input.customerId & ' after retries' %}"
}
```

Key elements:
- `ConditionExpression` with `attribute_not_exists` ensures only one writer wins. The `expiresAt` check provides stale-lock recovery if an execution crashes without releasing.
- `executionId` on the lock item lets `ReleaseLock` conditionally delete only its own lock.
- Retry on `ConditionalCheckFailedException` acts as a spin-wait. Tune `MaxAttempts` and `IntervalSeconds` based on expected hold time.
- Catch on `DoProtectedWork` routes to `ReleaseLock` so the lock is always released. After releasing, `CheckWorkResult` re-raises the error path.
- Set `expiresAt` to a reasonable TTL (here 15 min). Use a DynamoDB TTL attribute to auto-clean expired locks.

---

## Human-in-the-Loop with Timeout Escalation

Chain multiple `.waitForTaskToken` states with `States.Timeout` catches to build escalation: primary approver → manager → auto-reject.

```json
"RequestApproval": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
    "MessageBody": "{% $string({'taskToken': $states.context.Task.Token, 'orderId': $orderId, 'approver': $states.input.primaryApprover, 'amount': $states.input.amount}) %}"
  },
  "TimeoutSeconds": 86400,
  "Assign": { "approvalResult": "{% $states.result %}" },
  "Catch": [
    { "ErrorEquals": ["States.Timeout"], "Assign": { "escalationReason": "Primary approver did not respond within 24 hours" }, "Next": "EscalateToManager" },
    { "ErrorEquals": ["States.ALL"], "Assign": { "approvalError": "{% $states.errorOutput %}" }, "Next": "ApprovalFailed" }
  ],
  "Next": "EvaluateApproval"
},
"EscalateToManager": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Arguments": {
    "TopicArn": "arn:aws:sns:us-east-1:123456789012:EscalationNotifications",
    "Subject": "Approval Escalation",
    "Message": "{% 'Order ' & $orderId & ' requires manager approval. ' & $escalationReason %}"
  },
  "Next": "WaitForManagerApproval"
},
"WaitForManagerApproval": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
  "Arguments": {
    "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
    "MessageBody": "{% $string({'taskToken': $states.context.Task.Token, 'orderId': $orderId, 'approver': $states.input.managerApprover, 'amount': $states.input.amount, 'escalated': true}) %}"
  },
  "TimeoutSeconds": 43200,
  "Assign": { "approvalResult": "{% $states.result %}" },
  "Catch": [
    {
      "ErrorEquals": ["States.Timeout"],
      "Assign": { "approvalResult": { "decision": "rejected", "reason": "No response from manager within 12 hours — auto-rejected" } },
      "Next": "EvaluateApproval"
    },
    { "ErrorEquals": ["States.ALL"], "Assign": { "approvalError": "{% $states.errorOutput %}" }, "Next": "ApprovalFailed" }
  ],
  "Next": "EvaluateApproval"
},
"EvaluateApproval": {
  "Type": "Choice",
  "Choices": [
    { "Condition": "{% $approvalResult.decision = 'approved' %}", "Next": "ProcessApprovedOrder" }
  ],
  "Default": "OrderRejected"
}
```

Key elements:
- Each callback stage has its own `TimeoutSeconds` — shorter for escalation stages since urgency increases.
- `States.Timeout` in Catch distinguishes "no response" from actual errors, routing to the next escalation tier.
- The final tier auto-rejects by assigning a synthetic result in Catch `Assign` and routing to the same `EvaluateApproval` Choice. This avoids duplicating decision logic.
- External system calls `SendTaskSuccess` with `{"decision": "approved"}` or `{"decision": "rejected", "reason": "..."}`.
- Use Standard (not Express) workflows — Express doesn't support `.waitForTaskToken`.

---

## Express → Standard Handoff

Express workflows are more cost-effective for high volume State Machine Invocations, but don't support callbacks or long waits. Standard workflows handle those but cost per state transition. Use Express for fast, high-volume ingest and kick off a Standard execution for the long-running tail.

```json
{
  "Comment": "Express workflow — fast ingest and validation",
  "QueryLanguage": "JSONata",
  "StartAt": "ValidateInput",
  "States": {
    "ValidateInput": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": {
        "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ValidateOrder:$LATEST",
        "Payload": "{% $states.input %}"
      },
      "Output": "{% $states.result.Payload %}",
      "Next": "EnrichData"
    },
    "EnrichData": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "LookupCustomer",
          "States": {
            "LookupCustomer": {
              "Type": "Task",
              "Resource": "arn:aws:states:::dynamodb:getItem",
              "Arguments": {
                "TableName": "CustomersTable",
                "Key": { "customerId": { "S": "{% $states.input.customerId %}" } }
              },
              "Output": "{% $states.result.Item %}",
              "End": true
            }
          }
        },
        {
          "StartAt": "LookupPricing",
          "States": {
            "LookupPricing": {
              "Type": "Task",
              "Resource": "arn:aws:states:::lambda:invoke",
              "Arguments": {
                "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:GetPricing:$LATEST",
                "Payload": "{% $states.input %}"
              },
              "Output": "{% $states.result.Payload %}",
              "End": true
            }
          }
        }
      ],
      "Output": {
        "order": "{% $states.input %}",
        "customer": "{% $states.result[0] %}",
        "pricing": "{% $states.result[1] %}"
      },
      "Next": "HandOffToStandard"
    },
    "HandOffToStandard": {
      "Type": "Task",
      "Resource": "arn:aws:states:::states:startExecution",
      "Arguments": {
        "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:OrderFulfillment-Standard",
        "Input": "{% $string($states.input) %}"
      },
      "Output": {
        "status": "handed_off",
        "childExecutionArn": "{% $states.result.ExecutionArn %}"
      },
      "End": true
    }
  }
}
```

Key elements:
- Express does validation, enrichment, fan-out — fast, stateless work that benefits from per-request pricing.
- `HandOffToStandard` uses fire-and-forget (no `.sync` suffix) so the Express execution completes immediately. Use `.sync:2` if you need to wait, but watch the 5-minute Express limit.
- Use `$string($states.input)` to serialize — `startExecution` expects a JSON string for `Input`.
- Ideal for event-driven architectures: API Gateway or EventBridge triggers Express at high volume, only orders needing long-running processing incur Standard costs.
