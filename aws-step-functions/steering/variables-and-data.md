# Variables and Data Transformation (JSONata Mode)

## JSONata Expression Syntax

JSONata expressions are written inside `{% %}` delimiters in string values:

```json
"Output": "{% $states.input.customer.name %}"
"TimeoutSeconds": "{% $timeout %}"
"Condition": "{% $states.input.age >= 18 %}"
```

Rules:
- The string must start with `{%` (no leading spaces) and end with `%}` (no trailing spaces).
- Not all fields accept JSONata — `Type` and `Resource` must be constant strings.
- JSONata expressions can appear in string values within objects and arrays at any nesting depth.
- A string without `{% %}` is treated as a literal value.
- All string literals inside JSONata expressions must use single quotes (`'text'`), not double quotes. The expression is already inside a JSON double-quoted string, so double quotes would break the JSON.
- Use `:=` inside `( ... )` blocks to bind local variables within a single expression. These are expression-local only — they do NOT set state machine variables (use `Assign` for that).
- Complex logic is wrapped in `( expr1; expr2; ...; finalExpr )` where semicolons separate sequential expressions and the last expression is the return value.

### String Quoting

```json
"Output": "{% 'Hello ' & $states.input.name %}"
"Condition": "{% $states.input.status = 'active' %}"
```

Never use double quotes inside the expression:
```
❌  "Output": "{% "Hello" %}"
✓  "Output": "{% 'Hello' %}"
```

### Local Variable Binding with `:=`

Use `:=` inside `( ... )` blocks to bind intermediate values within a single JSONata expression. Semicolons separate each binding, and the last expression is the return value:

```json
"Output": "{% ( $subtotal := $sum($states.input.items.price); $tax := $subtotal * 0.1; $discount := $exists($couponValue) ? $couponValue : 0; {'subtotal': $subtotal, 'tax': $tax, 'discount': $discount, 'total': $subtotal + $tax - $discount} ) %}"
```

You can also define local helper functions:

```json
"Assign": {
  "summary": "{% ( $formatPrice := function($amt) { '$' & $formatNumber($amt, '#,##0.00') }; $subtotal := $sum($states.input.items.price); {'itemCount': $count($states.input.items), 'subtotal': $formatPrice($subtotal), 'total': $formatPrice($subtotal * 1.1)} ) %}"
}
```

Local variables bound with `:=` exist only within the `( ... )` block. They do not affect state machine variables. To persist values across states, use the `Assign` field.

## The `$states` Reserved Variable

Step Functions provides a reserved `$states` variable in every JSONata state:

```
$states = {
  "input":       // Original input to the state
  "result":      // Task/Parallel/Map result (if successful)
  "errorOutput": // Error Output (only available in Catch)
  "context":     // Context object (execution metadata)
}
```

### Where Each Field Is Accessible

| Field | Accessible In |
|-------|--------------|
| `$states.input` | All fields that accept JSONata, in any state |
| `$states.result` | Top-level `Output` and `Assign` in Task, Parallel, Map states |
| `$states.errorOutput` | `Output` and `Assign` inside a `Catch` block |
| `$states.context` | All fields that accept JSONata, in any state |

### Context Object

`$states.context` provides execution metadata:

```json
"executionId": "{% $states.context.Execution.Id %}",
"startTime": "{% $states.context.Execution.StartTime %}",
"stateName": "{% $states.context.State.Name %}",
"originalInput": "{% $states.context.Execution.Input %}"
```

Useful context fields:
- `$states.context.Execution.Id` — Execution ARN
- `$states.context.Execution.Input` — Original workflow input
- `$states.context.Execution.Name` — Execution name
- `$states.context.Execution.StartTime` — When execution started
- `$states.context.State.Name` — Current state name
- `$states.context.State.EnteredTime` — When current state was entered
- `$states.context.StateMachine.Id` — State machine ARN
- `$states.context.StateMachine.Name` — State machine name

Inside Map state `ItemSelector`:
- `$states.context.Map.Item.Value` — Current array element
- `$states.context.Map.Item.Index` — Zero-based index

## JSONata Restrictions in Step Functions

1. **No `$` or `$$` at top level**: You cannot use `$` or `$$` to reference an implicit input document. Use `$states.input` instead.
   - Invalid: `"Output": "{% $.name %}"` (top-level `$`)
   - Valid: `"Output": "{% $states.input.name %}"`
   - Valid inside expressions: `"Output": "{% $states.input.items[$.price > 10] %}"` (nested `$` is OK)

2. **No unqualified field names at top level**: Use variables or `$states.input`.
   - Invalid: `"Output": "{% name %}"` (unqualified)
   - Valid: `"Output": "{% $states.input.name %}"`

3. **No `$eval`**: Use `$parse()` instead for deserializing JSON strings.

4. **Expressions must produce a defined value**: `$data.nonExistentField` throws `States.QueryEvaluationError` because JSON cannot represent undefined.

---

## Workflow Variables with `Assign`

Variables let you store data in one state and reference it in any subsequent state, without threading data through Output/Input chains.

### Declaring Variables

```json
"StoreData": {
  "Type": "Pass",
  "Assign": {
    "productName": "product1",
    "count": 42,
    "available": true,
    "config": "{% $states.input.configuration %}"
  },
  "Next": "UseData"
}
```

### Referencing Variables

Prepend the variable name with `$`:

```json
"Arguments": {
  "product": "{% $productName %}",
  "quantity": "{% $count %}"
}
```

### Assigning from Task Results

```json
"FetchPrice": {
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Arguments": {
    "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:GetPrice:$LATEST",
    "Payload": {
      "product": "{% $states.input.product %}"
    }
  },
  "Assign": {
    "currentPrice": "{% $states.result.Payload.price %}"
  },
  "Output": "{% $states.result.Payload %}",
  "Next": "CheckPrice"
}
```

### States That Support Assign

Pass, Task, Map, Parallel, Choice, Wait — all support `Assign`.

Succeed and Fail do NOT support `Assign`.

### Assign in Choice Rules and Catch

Choice Rules and Catch blocks can each have their own `Assign`:

```json
"CheckValue": {
  "Type": "Choice",
  "Choices": [
    {
      "Condition": "{% $states.input.value > 100 %}",
      "Assign": {
        "tier": "premium"
      },
      "Next": "PremiumPath"
    }
  ],
  "Default": "StandardPath",
  "Assign": {
    "tier": "standard"
  }
}
```

If a Choice Rule matches, its `Assign` is used. If no rule matches, the state-level `Assign` is used.

---

## Variable Evaluation Order

All expressions in `Assign` are evaluated using variable values as they were on state entry. New values only take effect in the next state.

```json
"SwapExample": {
  "Type": "Pass",
  "Assign": {
    "x": "{% $y %}",
    "y": "{% $x %}"
  },
  "Next": "AfterSwap"
}
```

If `$x = 3` and `$y = 6` on entry, after this state: `$x = 6`, `$y = 3`. This works because all expressions are evaluated first, then assignments are made.

You cannot assign to a sub-path of a variable:
- Valid: `"Assign": {"x": 42}`
- Invalid: `"Assign": {"x.y": 42}` or `"Assign": {"x[2]": 42}`

---

## Variable Scope

Variables exist in a state-machine-local scope:

- **Outer scope**: All states in the top-level `States` field.
- **Inner scope**: States inside a Parallel branch or Map iteration.

### Scope Rules

1. Inner scopes can READ variables from outer scopes.
2. Inner scopes CANNOT ASSIGN to variables that exist in an outer scope.
3. Variable names must be unique across outer and inner scopes (no shadowing).
4. Variables in different Parallel branches or Map iterations are isolated from each other.
5. When a Parallel branch or Map iteration completes, its variables go out of scope.
6. Exception: Distributed Map states cannot reference variables in outer scopes.

### Passing Data Out of Inner Scopes

Use `Output` on terminal states within branches/iterations to return data to the outer scope:

```json
"ParallelWork": {
  "Type": "Parallel",
  "Branches": [
    {
      "StartAt": "BranchA",
      "States": {
        "BranchA": {
          "Type": "Task",
          "Resource": "...",
          "Output": "{% $states.result.Payload %}",
          "End": true
        }
      }
    }
  ],
  "Assign": {
    "branchAResult": "{% $states.result[0] %}"
  },
  "Next": "Continue"
}
```

### Catch Assign and Outer Scope

In a Catch block on a Parallel or Map state, `Assign` can assign values to variables in the outer scope (the scope where the Parallel/Map state exists):

```json
"Catch": [
  {
    "ErrorEquals": ["States.ALL"],
    "Assign": {
      "errorOccurred": true,
      "errorDetails": "{% $states.errorOutput %}"
    },
    "Next": "HandleError"
  }
]
```

---

## Arguments and Output Fields

### Arguments

Provides input to Task and Parallel states (replaces JSONPath `Parameters`):

```json
"Arguments": {
  "staticField": "hello",
  "dynamicField": "{% $states.input.name %}",
  "computed": "{% $count($states.input.items) %}"
}
```

Or as a single JSONata expression:

```json
"Arguments": "{% $states.input.payload %}"
```

`Arguments` can reference `$states.input` and `$states.context`, but NOT `$states.result` or `$states.errorOutput`.

### Output

Transforms the state output (replaces JSONPath `ResultSelector` + `ResultPath` + `OutputPath`):

```json
"Output": {
  "customerId": "{% $states.input.id %}",
  "result": "{% $states.result.Payload %}",
  "processedAt": "{% $now() %}"
}
```

Or as a single expression or literal value:

```json
"Output": "{% $states.result.Payload %}"
"Output": 42
"Output": { "status": "done" }
```

If `Output` is not provided:
- Task, Parallel, Map: state output = the result
- All other states: state output = the state input

### Assign and Output Are Parallel

`Assign` and `Output` are evaluated in parallel. Variable assignments in `Assign` are NOT available in `Output` of the same state — you must re-derive values in both if needed:

```json
"Assign": {
  "savedPrice": "{% $states.result.Payload.price %}"
},
"Output": {
  "price": "{% $states.result.Payload.price %}"
}
```

---

## Variable Limits

| Limit | Value |
|-------|-------|
| Max size of a single variable | 256 KiB |
| Max combined size in a single Assign | 256 KiB |
| Max total stored variables per execution | 10 MiB |
| Max variable name length | 80 Unicode characters |

---

## Data Transformation Patterns

### Filtering Arrays

```json
"Output": {
  "expensiveItems": "{% $states.input.items[price > 100] %}"
}
```

### Aggregation

```json
"Output": {
  "total": "{% $sum($states.input.items.price) %}",
  "average": "{% $average($states.input.items.price) %}",
  "count": "{% $count($states.input.items) %}"
}
```

### String Operations

```json
"Output": {
  "fullName": "{% $states.input.firstName & ' ' & $states.input.lastName %}",
  "upper": "{% $uppercase($states.input.name) %}",
  "trimmed": "{% $trim($states.input.rawInput) %}"
}
```

### Object Merging

```json
"Output": "{% $merge([$states.input, {'processedAt': $now(), 'status': 'complete'}]) %}"
```

### Building Lookup Maps with `$reduce`

Use `$reduce` to transform an array into a key-value object:

```json
"Assign": {
  "priceByProduct": "{% $reduce($states.input.items, function($acc, $item) { $merge([$acc, {$item.productId: $item.price}]) }, {}) %}"
}
```

Given `[{"productId": "A1", "price": 10}, {"productId": "B2", "price": 25}]`, this produces `{"A1": 10, "B2": 25}`.

### Dynamic Key Access with `$lookup`

Use `$lookup` to access an object property by a variable key:

```json
"Output": {
  "price": "{% $lookup($priceByProduct, $states.input.productId) %}"
}
```

This is essential when you've built a mapping object with `$reduce` and need to retrieve values dynamically. Standard dot notation (`$priceByProduct.someKey`) only works with literal key names.

### Conditional Values

```json
"Output": {
  "tier": "{% $states.input.total > 1000 ? 'gold' : 'standard' %}",
  "discount": "{% $exists($states.input.coupon) ? 0.1 : 0 %}"
}
```

### Array Membership with `in` and Concatenation with `$append`

Test if a value exists in an array with `in`:

```json
"Condition": "{% $states.input.status in ['pending', 'processing', 'shipped'] %}"
```

Concatenate arrays with `$append`:

```json
"Assign": {
  "allIds": "{% $append($states.input.orderIds, $states.input.returnIds) %}"
}
```

### Array Mapping

```json
"Output": {
  "names": "{% $states.input.users.(firstName & ' ' & lastName) %}"
}
```

### Generating UUIDs and Random Values

```json
"Assign": {
  "requestId": "{% $uuid() %}",
  "randomValue": "{% $random() %}"
}
```

### Partitioning Arrays

```json
"Assign": {
  "batches": "{% $partition($states.input.items, 10) %}"
}
```

### Parsing JSON Strings

```json
"Assign": {
  "parsed": "{% $parse($states.input.jsonString) %}"
}
```

### Hashing

```json
"Assign": {
  "hash": "{% $hash($states.input.content, 'SHA-256') %}"
}
```

### Timestamp Comparison with `$toMillis`

JSONata timestamps are strings, so you can't compare them directly with `<` or `>`. Use `$toMillis` to convert to numeric milliseconds:

```json
"Condition": "{% $toMillis($states.input.orderDate) > $toMillis($states.input.cutoffDate) %}"
```

Useful for sorting timestamps, calculating durations, or finding the most recent entry:

```json
"Assign": {
  "ageMinutes": "{% $round(($toMillis($now()) - $toMillis($states.input.createdAt)) / 60000, 2) %}",
  "mostRecent": "{% $sort($states.input.timestamps, function($a, $b) { $toMillis($a) < $toMillis($b) })[0] %}"
}
```
