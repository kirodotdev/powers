# Session Policies

## Purpose

This document describes how to scope down the IAM permissions of a HealthOmics
workflow run using an inline **session policy**, supplied via the `sessionPolicy`
parameter on `StartRun` (and `StartRunBatch`).

## When to Reference This Document

Reference this document when:
- The user wants to restrict what a run's tasks are allowed to access (for
  example, limit S3 access to specific buckets/prefixes) beyond what the run's
  IAM role already grants.
- The user asks about the `sessionPolicy` parameter on `StartRun` or `StartRunBatch`.
- The user encounters a `ValidationException` referencing `sessionPolicy`, or an
  `AccessDenied` / `403` at run time that may be caused by a restrictive session policy.

## What It Is

`sessionPolicy` is an **optional inline IAM policy, provided as a JSON string**,
that further scopes down the permissions of the IAM role passed in `roleArn` for
that run. The run's effective permissions are the **intersection** of the role's
identity-based policies and this session policy — a session policy can only
*restrict*, never *grant*, permissions.

This is the same concept as an AWS STS assume-role session policy: HealthOmics
assumes the run's role with the customer-provided policy attached, so every task
in the run operates under the intersected permissions.

## How to Specify It

- **Single run:** pass `sessionPolicy` on `StartRun`.
- **Batch run:** pass `sessionPolicy` inside `defaultRunSetting` on `StartRunBatch`;
  it applies to every run in the batch.

`GetRun` returns the `sessionPolicy` that was supplied for a run.

## Constraints

- Must be a valid JSON **object** (an IAM policy document).
- Length **1–2048 characters** (the AWS STS session-policy limit).
- A malformed (non-JSON / non-object) or oversized (>2048 character) policy is
  rejected synchronously at `StartRun` / `StartRunBatch` with a `ValidationException`.

## Runtime Behavior

Because the effective permissions are the intersection, a session policy that
denies (or fails to allow) a resource the run legitimately needs will cause the
run's tasks to fail at run time with an access error (for example, a `403` on an
S3 object). When helping a user debug a failed run that uses a session policy,
check whether the policy is too restrictive for the resources the workflow accesses.

## Example

A session policy that scopes the run's S3 access down to just its own output
bucket (the role's other permissions still apply only if this policy also allows
them, since the effective set is the intersection):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::<output-bucket>",
        "arn:aws:s3:::<output-bucket>/*"
      ]
    }
  ]
}
```

## Related Documentation
- For running a workflow, see [Running a Workflow SOP](./running-a-workflow.md)
- For batch runs, see [Batch Runs SOP](./batch-runs.md)
- For diagnosing run failures, see [Diagnose Run Failure SOP](./diagnose-run-failure.md)
