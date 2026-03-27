# Error Handling in JSONata Mode

## Overview

When a state encounters an error, Step Functions defaults to failing the entire execution. You can override this with `Retry` (retry the failed state) and `Catch` (transition to a fallback state).

`Retry` and `Catch` are available on: Task, Parallel, and Map states.

## Error Names

Errors are identified by case-sensitive strings. Step Functions defines these built-in error codes:

| Error Code | Description |
|-----------|-------------|
| `States.ALL` | Wildcard — matches any error |
| `States.Timeout` | Task exceeded `TimeoutSeconds` or missed heartbeat |
| `States.HeartbeatTimeout` | Task missed heartbeat interval |
| `States.TaskFailed` | Task failed during execution |
| `States.Permissions` | Insufficient privileges |
| `States.ResultPathMatchFailure` | ResultPath cannot be applied (JSONPath only) |
| `States.ParameterPathFailure` | Parameter path resolution failed (JSONPath only) |
| `States.QueryEvaluationError` | JSONata expression evaluation failed |
| `States.BranchFailed` | A Parallel state branch failed |
| `States.NoChoiceMatched` | No Choice rule matched and no Default |
| `States.IntrinsicFailure` | Intrinsic function failed (JSONPath only) |
| `States.ExceedToleratedFailureThreshold` | Map state exceeded failure tolerance |
| `States.ItemReaderFailed` | Map state ItemReader failed |
| `States.ResultWriterFailed` | Map state ResultWriter failed |

Custom error names are allowed but must NOT start with `States.`.

---

## Retry

The `Retry` field is an array of Retrier objects. The interpreter scans retriers in order and uses the first one whose `ErrorEquals` matches.

### Retrier Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ErrorEquals` | string[] | Required | Error names to match |
| `IntervalSeconds` | integer | 1 | Seconds before first retry |
| `MaxAttempts` | integer | 3 | Maximum retry attempts (0 = never retry) |
| `BackoffRate` | number | 2.0 | Multiplier for retry interval (must be ≥ 1.0) |
| `MaxDelaySeconds` | integer | — | Cap on retry interval |
| `JitterStrategy` | string | — | Jitter strategy (e.g., `"FULL"`) |

### Basic Retry

```json
"ProcessPayment": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Pay:$LATEST",
    "Payload": "{% $states.input %}"
  },
  "Retry": [
    {
      "ErrorEquals": ["States.TaskFailed"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3,
      "BackoffRate": 2.0
    }
  ],
  "Next": "Confirm"
}
```

This retries after 2s, 4s, 8s (3 attempts with 2x backoff).

### Retry with Max Delay and Jitter

```json
"Retry": [
  {
    "ErrorEquals": ["States.TaskFailed"],
    "IntervalSeconds": 1,
    "MaxAttempts": 5,
    "BackoffRate": 2.0,
    "MaxDelaySeconds": 30,
    "JitterStrategy": "FULL"
  }
]
```

### Multiple Retriers

Retriers are evaluated in order. Each retrier tracks its own attempt count independently:

```json
"Retry": [
  {
    "ErrorEquals": ["ThrottlingException"],
    "IntervalSeconds": 1,
    "MaxAttempts": 5,
    "BackoffRate": 2.0,
    "JitterStrategy": "FULL"
  },
  {
    "ErrorEquals": ["States.Timeout"],
    "MaxAttempts": 0
  },
  {
    "ErrorEquals": ["States.ALL"],
    "IntervalSeconds": 3,
    "MaxAttempts": 2,
    "BackoffRate": 1.5
  }
]
```

Rules:
- `States.ALL` must appear alone in its `ErrorEquals` array.
- `States.ALL` must be in the last retrier.
- `MaxAttempts: 0` means "never retry this error."
- Retrier attempt counts reset when the interpreter transitions to another state.

---

## Catch

The `Catch` field is an array of Catcher objects. After retries are exhausted (or if no retrier matches), the interpreter scans catchers in order.

### Catcher Fields (JSONata)

| Field | Type | Description |
|-------|------|-------------|
| `ErrorEquals` | string[] | Required. Error names to match |
| `Next` | string | Required. State to transition to |
| `Output` | any | Optional. Transform the error output |
| `Assign` | object | Optional. Assign variables from error context |

### Basic Catch

```json
"ProcessOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Process:$LATEST",
    "Payload": "{% $states.input %}"
  },
  "Catch": [
    {
      "ErrorEquals": ["ValidationError"],
      "Output": {
        "error": "{% $states.errorOutput.Error %}",
        "cause": "{% $states.errorOutput.Cause %}",
        "originalInput": "{% $states.input %}"
      },
      "Next": "HandleValidationError"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "Output": "{% $states.errorOutput %}",
      "Next": "HandleGenericError"
    }
  ],
  "Next": "Success"
}
```

### Error Output Structure

When a state fails and matches a Catcher, the Error Output is a JSON object with:
- `Error` (string) — the error name
- `Cause` (string) — human-readable error description

```json
{
  "Error": "States.TaskFailed",
  "Cause": "Lambda function returned an error"
}
```

### Catch with Variable Assignment

```json
"Catch": [
  {
    "ErrorEquals": ["States.ALL"],
    "Assign": {
      "hasError": true,
      "errorType": "{% $states.errorOutput.Error %}",
      "errorMessage": "{% $states.errorOutput.Cause %}"
    },
    "Output": "{% $merge([$states.input, {'error': $states.errorOutput}]) %}",
    "Next": "ErrorHandler"
  }
]
```

In a Catch block, `Assign` and `Output` can reference:
- `$states.input` — the original state input
- `$states.errorOutput` — the error details
- `$states.context` — execution context

If a Catcher matches, the state's top-level `Assign` is NOT evaluated — only the Catcher's `Assign` runs.

### Catch Without Output

If no `Output` is provided in the Catcher, the state output is the raw Error Output object.

### Building Rich Error Context for Fail States

A user-friendly pattern is to capture error details into a variable via Catch `Assign`, then reference that variable in a Fail state's `Cause` with defensive fallbacks:

```json
"ChargePayment": {
  "Type": "Task",
  "Resource": "arn:aws:states:::sqs:sendMessage",
  "Arguments": { ... },
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Assign": {
        "error": "{% $states.errorOutput %}"
      },
      "Next": "PaymentFailed"
    }
  ],
  "Next": "ConfirmOrder"
},
"PaymentFailed": {
  "Type": "Fail",
  "Error": "PaymentError",
  "Cause": "{% 'Payment failed for order ' & ($exists($orderId) ? $orderId : 'unknown') & ': ' & ($exists($error.Error) ? $error.Error : 'Unknown') & ' - ' & ($exists($error.Cause) ? $error.Cause : 'No details') & '. Timestamp: ' & $now() %}"
}
```

Always guard with `$exists()` — if the variable was never assigned (e.g., the Catch didn't fire for that path), referencing it directly throws `States.QueryEvaluationError`.

---

## Combined Retry and Catch

When both are present, retries are attempted first. Only if retries are exhausted does the Catch apply:

```json
"CallExternalAPI": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:CallAPI:$LATEST",
    "Payload": "{% $states.input %}"
  },
  "Retry": [
    {
      "ErrorEquals": ["ThrottlingException", "ServiceUnavailable"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3,
      "BackoffRate": 2.0,
      "JitterStrategy": "FULL"
    },
    {
      "ErrorEquals": ["States.Timeout"],
      "IntervalSeconds": 5,
      "MaxAttempts": 2
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["ThrottlingException", "ServiceUnavailable"],
      "Assign": {
        "retryExhausted": true
      },
      "Output": {
        "error": "Service temporarily unavailable after retries",
        "details": "{% $states.errorOutput %}"
      },
      "Next": "NotifyAndRetryLater"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "Output": {
        "error": "{% $states.errorOutput %}",
        "input": "{% $states.input %}"
      },
      "Next": "FatalErrorHandler"
    }
  ],
  "Output": "{% $states.result.Payload %}",
  "Next": "ProcessResponse"
}
```

---

## Handling States.QueryEvaluationError

JSONata expressions can fail at runtime. Common causes:

1. **Type error**: `{% $x + $y %}` where `$x` or `$y` is not a number
2. **Type incompatibility**: `"TimeoutSeconds": "{% $name %}"` where `$name` is a string
3. **Value out of range**: Negative number for `TimeoutSeconds`
4. **Undefined result**: `{% $data.nonExistentField %}` — JSON cannot represent undefined

All of these throw `States.QueryEvaluationError`. Handle it like any other error:

```json
"Retry": [
  {
    "ErrorEquals": ["States.QueryEvaluationError"],
    "MaxAttempts": 0
  }
],
"Catch": [
  {
    "ErrorEquals": ["States.QueryEvaluationError"],
    "Output": {
      "error": "Data transformation failed",
      "details": "{% $states.errorOutput %}"
    },
    "Next": "HandleDataError"
  }
]
```

### Preventing QueryEvaluationError

Use defensive JSONata expressions:

```json
"Output": {
  "name": "{% $exists($states.input.name) ? $states.input.name : 'Unknown' %}",
  "total": "{% $type($states.input.amount) = 'number' ? $states.input.amount : 0 %}"
}
```

Watch out for single-value vs array results from filters. JSONata returns a single object (not a 1-element array) when a filter matches exactly one item, and undefined when nothing matches. Both cases will throw `States.QueryEvaluationError` if you pass the result to array-expecting functions like `$count`, `$map`, or a Map state `Items` field.

Guard filtered results before using them:

```json
"Assign": {
  "pendingOrders": "{% ($filtered := $states.input.orders[status = 'pending']; $type($filtered) = 'array' ? $filtered : $exists($filtered) ? [$filtered] : []) %}"
}
```

This ensures `$pendingOrders` is always an array regardless of how many items matched.

---

## Error Handling in Parallel States

If any branch fails, the entire Parallel state fails. Catch the error at the Parallel state level:

```json
"ParallelWork": {
  "Type": "Parallel",
  "Branches": [ ... ],
  "Retry": [
    {
      "ErrorEquals": ["States.BranchFailed"],
      "MaxAttempts": 1
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Output": {
        "error": "{% $states.errorOutput %}",
        "failedAt": "parallel execution"
      },
      "Next": "HandleParallelError"
    }
  ],
  "Next": "Continue"
}
```

---

## Error Handling in Map States

Individual iteration failures can be tolerated:

```json
"ProcessAll": {
  "Type": "Map",
  "Items": "{% $states.input.records %}",
  "ToleratedFailurePercentage": 10,
  "ItemProcessor": { ... },
  "Catch": [
    {
      "ErrorEquals": ["States.ExceedToleratedFailureThreshold"],
      "Output": {
        "error": "Too many items failed",
        "details": "{% $states.errorOutput %}"
      },
      "Next": "HandleBatchFailure"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "Next": "HandleMapError"
    }
  ],
  "Next": "Done"
}
```

---

## Common Error Handling Patterns

### Circuit Breaker with Variables

```json
"CheckRetryCount": {
  "Type": "Choice",
  "Choices": [
    {
      "Condition": "{% $retryCount >= $maxRetries %}",
      "Next": "MaxRetriesExceeded"
    }
  ],
  "Default": "AttemptOperation"
},
"AttemptOperation": {
  "Type": "Task",
  "Resource": "...",
  "Assign": {
    "retryCount": "{% $retryCount + 1 %}"
  },
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Assign": {
        "retryCount": "{% $retryCount + 1 %}",
        "lastError": "{% $states.errorOutput %}"
      },
      "Next": "WaitBeforeRetry"
    }
  ],
  "Next": "Success"
},
"WaitBeforeRetry": {
  "Type": "Wait",
  "Seconds": "{% $power(2, $retryCount) %}",
  "Next": "CheckRetryCount"
}
```

