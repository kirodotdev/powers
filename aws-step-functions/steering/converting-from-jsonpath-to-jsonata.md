# Converting from JSONPath to JSONata

Systematic conversion guide for migrating existing JSONPath state machines to JSONata. Covers field mapping, state-type patterns, intrinsic function replacements, and common pitfalls.

## Migration Strategy

Convert incrementally by setting `QueryLanguage` per-state. JSONPath states and JSONata states can coexist:

```json
{
  "StartAt": "LegacyState",
  "States": {
    "LegacyState": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": { "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Legacy:$LATEST", "Payload.$": "$" },
      "ResultPath": "$.legacyResult",
      "Next": "MigratedState"
    },
    "MigratedState": {
      "Type": "Task",
      "QueryLanguage": "JSONata",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Arguments": { "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Modern:$LATEST", "Payload": "{% $states.input %}" },
      "Output": "{% $states.result.Payload %}",
      "End": true
    }
  }
}
```

When all states are converted, promote `QueryLanguage` to the top level and remove per-state declarations.

---

## Field Mapping Reference

### I/O Fields: Five Become Two

| JSONPath Field | JSONata Equivalent |
|---|---|
| `InputPath` | Not needed — use `$states.input.path` directly in `Arguments` |
| `Parameters` | `Arguments` |
| `ResultSelector` | `Output` (reference `$states.result`) |
| `ResultPath` | `Output` with `$merge`, or `Assign` (preferred) |
| `OutputPath` | `Output` (return only what you need) |

### Path Fields Eliminated

| JSONPath | JSONata |
|---|---|
| `TimeoutSecondsPath` | `TimeoutSeconds` with `{% %}` |
| `HeartbeatSecondsPath` | `HeartbeatSeconds` with `{% %}` |
| `ItemsPath` | `Items` with `{% %}` |

### Syntax Changes

| JSONPath | JSONata |
|---|---|
| `"key.$": "$.field"` | `"key": "{% $states.input.field %}"` |
| `$` or `$.field` (state input) | `$states.input` or `$states.input.field` |
| `$$` (context object) | `$states.context` |
| `$$.Execution.Input` | `$states.context.Execution.Input` |
| `$$.Task.Token` | `$states.context.Task.Token` |
| `$$.Map.Item.Value` | `$states.context.Map.Item.Value` |
| `$variable` (workflow var) | `$variable` (unchanged) |

---

## Converting Each State Type

### Task State

**Before (JSONPath):**
```json
"ProcessOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "InputPath": "$.order",
  "Parameters": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Process:$LATEST",
    "Payload": { "id.$": "$.orderId", "customer.$": "$.customerName" }
  },
  "ResultSelector": { "processedId.$": "$.Payload.id", "status.$": "$.Payload.status" },
  "ResultPath": "$.processingResult",
  "OutputPath": "$.processingResult",
  "Next": "Ship"
}
```

**After (JSONata):**
```json
"ProcessOrder": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Process:$LATEST",
    "Payload": { "id": "{% $states.input.order.orderId %}", "customer": "{% $states.input.order.customerName %}" }
  },
  "Output": { "processedId": "{% $states.result.Payload.id %}", "status": "{% $states.result.Payload.status %}" },
  "Next": "Ship"
}
```

Steps: (1) Fold `InputPath` path into `$states.input` references. (2) `Parameters` → `Arguments`, remove `.$` suffixes, wrap in `{% %}`. (3) Collapse `ResultSelector` + `ResultPath` + `OutputPath` into `Output`.

### ResultPath Patterns

**Merging result into input** (`ResultPath: "$.field"`):
```json
// Preferred: use Assign to store, pass input through
"Assign": { "priceResult": "{% $states.result.Payload %}" },
"Output": "{% $states.input %}"

// Alternative: explicit merge
"Output": "{% $merge([$states.input, {'priceResult': $states.result.Payload}]) %}"
```

**Discarding result** (`ResultPath: null`):
```json
"Output": "{% $states.input %}"
```

### Pass State

**Before:** `Result` + `ResultPath` → **After:** `Output` (or just `Assign` if downstream uses variables)

```json
// JSONPath
"InjectDefaults": { "Type": "Pass", "Result": { "region": "us-east-1" }, "ResultPath": "$.config", "Next": "Go" }

// JSONata — use Assign when possible
"InjectDefaults": { "Type": "Pass", "Assign": { "region": "us-east-1" }, "Next": "Go" }
```

### Choice State

JSONPath uses `Variable` + typed operators. JSONata uses a single `Condition` expression.

**Before (JSONPath):**
```json
"Choices": [
  { "Variable": "$.status", "StringEquals": "approved", "Next": "Approved" },
  { "And": [
    { "Variable": "$.priority", "StringEquals": "high" },
    { "Variable": "$.age", "NumericLessThanEquals": 30 }
  ], "Next": "FastTrack" },
  { "Not": { "Variable": "$.email", "IsPresent": true }, "Next": "RequestEmail" }
]
```

**After (JSONata):**
```json
"Choices": [
  { "Condition": "{% $states.input.status = 'approved' %}", "Next": "Approved" },
  { "Condition": "{% $states.input.priority = 'high' and $states.input.age <= 30 %}", "Next": "FastTrack" },
  { "Condition": "{% $not($exists($states.input.email)) %}", "Next": "RequestEmail" }
]
```

#### Choice Operator Mapping

| JSONPath Operator | JSONata |
|---|---|
| `StringEquals` / `StringEqualsPath` | `= 'value'` / `= $states.input.other` |
| `NumericGreaterThan` / `NumericLessThanEquals` | `> value` / `<= value` |
| `BooleanEquals` | `= true` / `= false` |
| `TimestampGreaterThan` | `$toMillis(field) > $toMillis('ISO-timestamp')` |
| `IsPresent: true` / `false` | `$exists(field)` / `$not($exists(field))` |
| `IsNull: true` | `field = null` |
| `IsNumeric` / `IsString` / `IsBoolean` | `$type(field) = 'number'` / `'string'` / `'boolean'` |
| `StringMatches` (wildcards) | `$contains(field, /regex/)` |
| `And` / `Or` / `Not` | `and` / `or` / `$not()` |

### Wait State

`SecondsPath` → `Seconds` with `{% %}`. `TimestampPath` → `Timestamp` with `{% %}`.

```json
// JSONPath
{ "Type": "Wait", "TimestampPath": "$.deliveryDate", "Next": "Check" }
// JSONata
{ "Type": "Wait", "Timestamp": "{% $states.input.deliveryDate %}", "Next": "Check" }
```

### Map State

| JSONPath | JSONata |
|---|---|
| `ItemsPath` | `Items` (fold `InputPath` into expression) |
| `Parameters` (with `$$.Map.*`) | `ItemSelector` (with `$states.context.Map.*`) |
| `Iterator` | `ItemProcessor` (add `ProcessorConfig`) |
| `ResultSelector` inside iterator | `Output` inside processor states |
| `ResultPath` on Map | `Assign` or `$merge` in `Output` |

```json
// JSONata Map
"ProcessItems": {
  "Type": "Map",
  "Items": "{% $states.input.orderData.items %}",
  "ItemSelector": {
    "item": "{% $states.context.Map.Item.Value %}",
    "index": "{% $states.context.Map.Item.Index %}"
  },
  "MaxConcurrency": 5,
  "ItemProcessor": {
    "ProcessorConfig": { "Mode": "INLINE" },
    "StartAt": "Process",
    "States": {
      "Process": {
        "Type": "Task",
        "Resource": "arn:aws:states:::lambda:invoke",
        "Arguments": { "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:Process:$LATEST", "Payload": "{% $states.input %}" },
        "Output": "{% $states.result.Payload %}",
        "End": true
      }
    }
  },
  "Assign": { "processedItems": "{% $states.result %}" },
  "Next": "Done"
}
```

---

## Converting Intrinsic Functions

| JSONPath Intrinsic | JSONata Equivalent |
|---|---|
| `States.Format('Order {}', $.id)` | `'Order ' & $states.input.id` |
| `States.StringToJson($.str)` | `$parse($states.input.str)` |
| `States.JsonToString($.obj)` | `$string($states.input.obj)` |
| `States.Array($.a, $.b)` | `[$states.input.a, $states.input.b]` |
| `States.ArrayPartition($.arr, 2)` | `$partition($states.input.arr, 2)` |
| `States.ArrayContains($.arr, $.v)` | `$states.input.v in $states.input.arr` |
| `States.ArrayRange(0, 10, 2)` | `$range(0, 10, 2)` |
| `States.ArrayGetItem($.arr, 0)` | `$states.input.arr[0]` |
| `States.ArrayLength($.arr)` | `$count($states.input.arr)` |
| `States.ArrayUnique($.arr)` | `$distinct($states.input.arr)` |
| `States.Base64Encode($.str)` | `$base64encode($states.input.str)` |
| `States.Base64Decode($.str)` | `$base64decode($states.input.str)` |
| `States.Hash($.data, 'SHA-256')` | `$hash($states.input.data, 'SHA-256')` |
| `States.JsonMerge($.a, $.b)` | `$merge([$states.input.a, $states.input.b])` |
| `States.MathRandom()` | `$random()` |
| `States.MathAdd($.a, $.b)` | `$states.input.a + $states.input.b` |
| `States.UUID()` | `$uuid()` |

---

## Converting Catch Blocks

JSONPath Catch uses `ResultPath`. JSONata Catch uses `Assign` and `Output` with `$states.errorOutput`.

```json
// JSONPath
"Catch": [{ "ErrorEquals": ["States.ALL"], "ResultPath": "$.error", "Next": "HandleError" }]

// JSONata — preferred: store in variable
"Catch": [{ "ErrorEquals": ["States.ALL"], "Assign": { "errorInfo": "{% $states.errorOutput %}" }, "Next": "HandleError" }]

// JSONata — if downstream expects merged object
"Catch": [{
  "ErrorEquals": ["States.ALL"],
  "Assign": { "errorInfo": "{% $states.errorOutput %}" },
  "Output": "{% $merge([$states.input, {'error': $states.errorOutput}]) %}",
  "Next": "HandleError"
}]
```

Retry syntax is identical between JSONPath and JSONata — no conversion needed.

---

## Context Object Reference Mapping

| JSONPath (`$$`) | JSONata (`$states.context`) |
|---|---|
| `$$.Execution.Id` | `$states.context.Execution.Id` |
| `$$.Execution.Input` | `$states.context.Execution.Input` |
| `$$.Execution.Name` | `$states.context.Execution.Name` |
| `$$.Execution.StartTime` | `$states.context.Execution.StartTime` |
| `$$.State.Name` | `$states.context.State.Name` |
| `$$.State.EnteredTime` | `$states.context.State.EnteredTime` |
| `$$.StateMachine.Id` | `$states.context.StateMachine.Id` |
| `$$.Task.Token` | `$states.context.Task.Token` |
| `$$.Map.Item.Value` | `$states.context.Map.Item.Value` |
| `$$.Map.Item.Index` | `$states.context.Map.Item.Index` |

---

## Common Conversion Pitfalls

### 1. Mixing JSONPath and JSONata fields in the same state
Invalid combinations: `Arguments` + `InputPath`, `Output` + `ResultSelector`, `Condition` + `Variable`. Remove all JSONPath fields from converted states.

### 2. Forgetting to remove `.$` suffixes
```json
❌  "orderId.$": "{% $states.input.orderId %}"
✓  "orderId": "{% $states.input.orderId %}"
```

### 3. Using `$` or `$$` instead of `$states`
```json
❌  "{% $.orderId %}"        ❌  "{% $$.Task.Token %}"
✓  "{% $states.input.orderId %}"   ✓  "{% $states.context.Task.Token %}"
```
Note: `$` is valid inside nested filter expressions (e.g., `$states.input.items[$.price > 10]`).

### 4. Double quotes inside JSONata expressions
```json
❌  "{% $states.input.status = "active" %}"
✓  "{% $states.input.status = 'active' %}"
```

### 5. Expecting Assign values in Output of the same state
`Assign` and `Output` evaluate in parallel — new variable values are not available in `Output`:
```json
❌  "Assign": { "total": "{% $states.result.Payload.total %}" },
    "Output": { "total": "{% $total %}" }
✓  "Assign": { "total": "{% $states.result.Payload.total %}" },
    "Output": { "total": "{% $states.result.Payload.total %}" }
```

### 6. Undefined field access
JSONPath silently returns null. JSONata throws `States.QueryEvaluationError`:
```json
❌  "{% $states.input.customer.middleName %}"
✓  "{% $exists($states.input.customer.middleName) ? $states.input.customer.middleName : '' %}"
```

### 7. Single-item filter results
JSONata returns a single object (not a 1-element array) when exactly one item matches a filter, and undefined when nothing matches. Both break Map state `Items` and functions like `$count`:
```json
❌  "Items": "{% $states.input.orders[status = 'pending'] %}"
✓  "Items": "{% ( $f := $states.input.orders[status = 'pending']; $type($f) = 'array' ? $f : $exists($f) ? [$f] : [] ) %}"
```

### 8. Iterator → ItemProcessor rename
`Iterator` was renamed to `ItemProcessor` and requires `ProcessorConfig`:
```json
❌  "Iterator": { "StartAt": "...", "States": {...} }
✓  "ItemProcessor": { "ProcessorConfig": { "Mode": "INLINE" }, "StartAt": "...", "States": {...} }
```

---

## Conversion Checklist

1. Add `"QueryLanguage": "JSONata"` (per-state or top-level)
2. Remove all five JSONPath I/O fields (`InputPath`, `Parameters`, `ResultSelector`, `ResultPath`, `OutputPath`)
3. `Parameters` → `Arguments` (remove `.$`, wrap in `{% %}`, `$` → `$states.input`)
4. Collapse `ResultSelector` + `ResultPath` + `OutputPath` into single `Output`
5. `ResultPath: null` → `Output: "{% $states.input %}"`
6. `ResultPath: "$.field"` → `Assign` (preferred) or `Output` with `$merge`
7. `*Path` fields → base field + `{% %}` expression
8. `$$` → `$states.context`
9. `States.*` intrinsic functions → JSONata equivalents (see table above)
10. Choice `Variable` + operators → `Condition` expression
11. `Iterator` → `ItemProcessor` with `ProcessorConfig`
12. Catch `ResultPath` → Catch `Assign`/`Output` with `$states.errorOutput`
13. Pass `Result` → `Output`
14. Refactor `ResultPath` merge chains to use `Assign` variables
15. Test each state individually via Workflow Studio Test State
16. Promote `QueryLanguage` to top level when all states are converted