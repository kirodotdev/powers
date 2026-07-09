---
name: "aws-step-functions"
displayName: "AWS Step Functions"
description: "Build workflows with AWS Step Functions state machines using the JSONata query language. Covers Amazon States Language (ASL) structure, state types, variables, data transformation, error handling, AWS service integration, and migrating from the JSONPath to the JSONata query language."
keywords: ["step functions", "state machine", "serverless", "jsonata", "asl", "amazon states language", "workflow", "orchestration"]
author: "AWS"
---

# AWS Step Functions

## Overview

AWS Step Functions uses Amazon States Language (ASL) to define state machines as JSON. With AWS Step Functions, you can create workflows, also called State machines, to build distributed applications, automate processes, orchestrate microservices, and create data and machine learning pipelines.

This power provides comprehensive guidance for writing state machines in ASL, covering:
- ASL structure and JSONata expression syntax
- Details on the eight available workflow states
- The `$states` reserved variable
- Workflow variables with `Assign`
- Error handling
- AWS Service integration patterns
- Example code for data transformation and architecture 
- Validation and testing of state machines
- How to migrate from JSONPath to JSONata

## When to Load Steering Files

Load the appropriate steering file based on what the user is working on:

- **ASL structure**, **state types**, **Task**, **Pass**, **Choice**, **Wait**, **Succeed**, **Fail**, **Parallel**, **Map** → see `asl-state-types.md`
- **Variables**, **Assign**, **data passing**, **scope**, **$states**, **input**, **output**, **Arguments**, **Output**, **data transformation**, **QueryEvaluationError** → see `variables-and-data.md`
- **Error handling**, **troubleshooting**, **Retry**, **Catch**, **fallback**, **error codes**, **States.Timeout**, **States.ALL** → see `error-handling.md`
- **Service integrations**, **Lambda invoke**, **DynamoDB**, **SNS**, **SQS**, **SDK integrations**, **Resource ARN**, **sync**, **async** → see `service-integrations.md`
- **Migrating from JSONPath to JSONata**, **migration**, **JSONPath to JSONata**, **InputPath**, **Parameters**, **ResultSelector**, **ResultPath**, **OutputPath**, **intrinsic functions**, **Iterator**, **payload template** → see `migrating-from-jsonpath-to-jsonata.md`
- **Validation**, **linting**, **testing**, **TestState**, **test state**, **mock**, **mocking**, **unit test**, **inspection level**, **DEBUG**, **TRACE**, **validate state**, **test in isolation** → see `validation-and-testing.md`
- **Architecture patterns**, **examples**, **polling**, **saga**, **compensation**, **scatter-gather**, **semaphore**, **lock**, **human-in-the-loop**, **escalation**, **Express to Standard** → see `architecture-patterns.md`
- **Data transformation**, **JSONata expressions**, **filtering**, **aggregation**, **string operations**, **$reduce**, **$lookup**, **$toMillis**, **$partition**, **$parse**, **$hash**, **$uuid** → see `transforming-data.md`
- **State input/output**, **$states**, **Assign**, **Output**, **Arguments**, **variable scope**, **variable limits**, **evaluation order**, **passing data between states** → see `processing-state-inputs-and-outputs.md`

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

**JSONPath is still supported** and is the default if `QueryLanguage` is omitted — existing state machines do not need to be migrated.

## Best Practices

- Set `"QueryLanguage": "JSONata"` at the top level for new state machines unless the user wants to use JSONPath
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
- Reference validation-and-testing.md and error-handling.md for detailed troubleshooting information.

## Resources

- [ASL Specification](https://states-language.net/spec.html)
- [JSONata documentation](https://docs.jsonata.org/overview.html)
- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)

## License
Apache-2.0 license.