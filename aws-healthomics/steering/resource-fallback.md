# SOP: Custom Compute Fallback (`omicsResourceFallbackOrder`)

## Purpose

This SOP defines how you, the agent, configure a HealthOmics WDL task to automatically fall
back across an ordered list of resource profiles (for example GPU type A -> GPU type B -> CPU)
when the preferred resource isn't available, instead of the task failing outright. For general
task resource directives (`acceleratorType`, `cpu`, `memory`), see the
[Workflow Development SOP](./workflow-development.md#task-parameters).

## When to Use This

Use `omicsResourceFallbackOrder` when the user wants a task to:
- Try one GPU type, then fall back to a different GPU type if the first is out of capacity.
- Try a GPU, then fall back to a CPU-only profile if no GPU is available.
- Reduce `ALL_PROFILES_INSTANCE_RESERVATION_FAILED`/capacity-related task failures for
  GPU-dependent tasks without the customer polling and resubmitting manually.

Do NOT reach for this directive for OOM or transient 5xx retries — those are already handled
by the standard `maxRetries` directive and operate independently (see
[Interaction with Other Retries](#interaction-with-other-retries) below).

## Procedure: Adding `omicsResourceFallbackOrder` to a Task

### Step 1. Replace the individual resource directives

- `omicsResourceFallbackOrder` REPLACES the task's top-level `acceleratorType`,
  `acceleratorCount`, `cpu`, and `memory` directives. You MUST NOT set any of these at the
  top level in a task that also sets `omicsResourceFallbackOrder`.
- Task-level fields that are NOT resource-profile-specific (`docker`, `maxRetries`,
  `preemptible`, etc.) stay at the top level as usual and apply the same way regardless of
  which profile is active.

### Step 2. Write the profile list

- `omicsResourceFallbackOrder` is a WDL array of map literals in the `runtime {}` block. Each
  map is one profile to try, in order.
- You MUST use quoted (string) keys in every profile — e.g. `{"acceleratorType": "nvidia-l4"}`.
  Unquoted/bareword keys are invalid and fail workflow validation.
- Each profile MAY set any of these 5 fields; all are optional per profile, but a profile
  MUST NOT be empty (`{}`):

  | Field | Type | Default when omitted | Max |
  |---|---|---|---|
  | `acceleratorType` | String | Field absent -> CPU profile | n/a — must be one of the 7 supported values below, or absent |
  | `acceleratorCount` | Integer | Absent when `acceleratorType` is also absent | 4 |
  | `cpu` | Integer or Float | 1 vCPU, or a GPU-instance default if a GPU profile omits it | 192 |
  | `memory` | String (e.g. `"32 GiB"`) | 1 GiB, or a GPU-instance default if a GPU profile omits it | 1536 GiB |
  | `omicsResourceWaitTimeoutInMin` | Integer | System default wait window | none (recommend >= 20 min; lower produces a warning) |

- `acceleratorType`, when set, MUST be one of the 7 supported values: `nvidia-tesla-t4`,
  `nvidia-tesla-t4-a10g`, `nvidia-tesla-a10g`, `nvidia-t4-a10g-l4`, `nvidia-l4-a10g`,
  `nvidia-l4`, `nvidia-l40s`. Omit the field entirely to signal a CPU-only profile — do NOT
  set it to `""` or `"cpu"`; both are rejected.
- `acceleratorCount` and `acceleratorType` MUST be set together — a profile cannot have one
  without the other.
- The list MUST contain at least 1 and at most 10 profiles.
- At most one CPU profile (a profile that omits `acceleratorType`) is allowed, and if
  present it MUST be the last entry in the list — HealthOmics exhausts all GPU options
  before falling back to CPU.
- A field omitted from a profile takes its documented default, NOT a value copied from an
  earlier profile in the list — defaults do not carry over between profiles.

### Step 3. Handle the resource-type signal in the command

- HealthOmics sets the `AWS_HEALTHOMICS_RESOURCE_TYPE` environment variable in the container
  to the active profile's accelerator type (e.g. `nvidia-l40s`), or `cpu` for a CPU-only
  profile. Use it to branch the command when the GPU and CPU code paths differ.
- The container image (`docker` directive) MUST support every code path referenced across
  all profiles in the list, since the same image runs regardless of which profile is active.

### Step 4. Set `docker` and `maxRetries` normally

- `docker` and `maxRetries` are shared, not per-profile — set them once at the top level as
  you would for any other task. See the [Workflow Development SOP](./workflow-development.md#task-parameters).

## Example

```wdl
task align {
  command <<<
    if [ "$AWS_HEALTHOMICS_RESOURCE_TYPE" = "cpu" ]; then
      sentieon bwa mem -t 32 ~{reference} ~{fastq}
    else
      pbrun fq2bam --ref ~{reference} --in-fq ~{fastq}
    fi
  >>>

  runtime {
    docker: "my-registry/align-multi-arch:latest"  # must support both GPU and CPU code paths
    maxRetries: 2  # OOM retry with 2 attempts

    omicsResourceFallbackOrder: [
      {"acceleratorType": "nvidia-l40s", "acceleratorCount": 1, "cpu": 8, "memory": "32 GiB", "omicsResourceWaitTimeoutInMin": 45},
      {"acceleratorType": "nvidia-l4",   "acceleratorCount": 1, "cpu": 8, "memory": "32 GiB"},
      {"cpu": 32, "memory": "128 GiB"}
    ]
  }
}
```

This task tries `nvidia-l40s` first (waiting up to 45 minutes for capacity), then `nvidia-l4`
(default wait window), then falls back to a CPU-only profile (32 vCPUs, 128 GiB) if neither
GPU is available.

## Interaction with Other Retries

- OOM and service-error (5xx) retries via `maxRetries` are unaffected by
  `omicsResourceFallbackOrder` — they retry within the currently active profile and never
  advance to the next profile in the fallback order. A retry that exhausts `maxRetries` fails
  the task as usual.
- If every profile in the fallback list is exhausted with no instance reservation, the task
  fails with failure reason `ALL_PROFILES_INSTANCE_RESERVATION_FAILED`. This is terminal —
  HealthOmics does NOT retry for this failure reason even if `maxRetries` is configured. If a
  user hits this, suggest raising `omicsResourceWaitTimeoutInMin` on the relevant profile(s)
  rather than relying on `maxRetries`.

## Validation Rules Enforced at Workflow Creation and Task Run Time

Most rules below cause outright rejection. The exceptions — below-minimum wait time,
duplicate profiles, and an `acceleratorType` unsupported in the run's region — only produce a
warning (the profile is skipped at scheduling time for the region case).

1. Cannot mix `omicsResourceFallbackOrder` with the top-level `acceleratorType`,
   `acceleratorCount`, `cpu`, `memory`, or `omicsResourceWaitTimeoutInMin` directives.
2. Must be a list (array), not a single map.
3. Must contain at least 1 profile.
4. Must not contain more than 10 profiles.
5. Every profile key MUST be a quoted string.
6. No empty profiles (`{}`).
7. `acceleratorType` and `acceleratorCount` must be set together, or both omitted.
8. `acceleratorType`, if set, must be one of the 7 supported values (or omitted for CPU).
9. `omicsResourceWaitTimeoutInMin` below 20 minutes produces a warning, not a rejection.
10. Unrecognized fields in a profile are rejected.
11. Field values must be the correct type (e.g. `cpu` must be numeric, not a string).
12. At most one CPU profile is allowed in the list.
13. A CPU profile, if present, must be the last profile in the list.
14. Duplicate profiles are allowed but produce a warning (they typically provide no benefit).
15. `cpu` (max 192), `memory` (max 1536 GiB), and `acceleratorCount` (max 4) are each
    rejected above their maximum.
16. An `acceleratorType` unsupported in the workflow's AWS region produces a warning, not a
    rejection — that profile is skipped at task scheduling time, so confirm a later profile in
    the list doesn't also depend on an unsupported type.

## If Workflow Creation or a Run Fails

- IF the workflow fails to create with a validation error referencing
  `omicsResourceFallbackOrder`, check the profile list against the Validation Rules above —
  the most common causes are unquoted keys (rule 5), mixing with top-level resource directives
  (rule 1), or a CPU profile that isn't last (rule 13).
- IF a task fails with `ALL_PROFILES_INSTANCE_RESERVATION_FAILED`, this means every profile in
  the list ran out its wait window without securing capacity — see
  [Interaction with Other Retries](#interaction-with-other-retries). For other run failures,
  see the [Troubleshooting SOP](./troubleshooting.md).

## Observability

HealthOmics emits customer-facing CloudWatch log events while a task moves through the
fallback list. Point the user to these when they ask why a task took a while to start or which
profile it landed on:
- `RESOURCE_PROFILE_STARTED` — emitted when the task begins searching for capacity on a
  profile.
- `RESOURCE_PROFILE_ADVANCED` — emitted when a profile's wait window is exhausted and the task
  advances to the next profile; the message includes which profile was unavailable, how long
  it waited, and which profile it's advancing to.

## Timeout Best Practices

- The default wait window when `omicsResourceWaitTimeoutInMin` is omitted is 20 minutes.
- A value as low as 1 minute is accepted, but only allows roughly one capacity-search cycle
  before advancing — this is USUALLY too aggressive for anything but a deliberately fast
  first-choice profile.
- For scarce accelerator types (e.g. `nvidia-l40s`), RECOMMEND >= 20 minutes so the profile
  gets a fair chance before advancing (see rule 9 above).
- The sum of every profile's wait window SHOULD stay well under the run's overall timeout
  (maximum 7 days) — a long fallback list with generous per-profile timeouts can otherwise
  consume most of the run's time budget before a task even starts.

## Region Behavior

- IF a profile's `acceleratorType` has no capacity fleet in the workflow's AWS region, that
  profile is skipped almost immediately rather than waiting out its
  `omicsResourceWaitTimeoutInMin` window — HealthOmics only enters the timed capacity-search
  loop once it confirms the type is deployed in the region.
- This is NOT an error — it's expected behavior for a fallback list that includes an
  accelerator type unsupported in the current region (see validation rule 16). The task
  advances to the next profile in the list as usual.
- Tell the user to check [Regional Capabilities SOP](./regional-capabilities.md) if they see a
  profile skip unexpectedly fast — the accelerator type they listed may not be deployed in
  their run's region.

## Related Documentation
- For general task resource directives (`acceleratorType`, `cpu`, `memory` outside of a
  fallback list), see [Workflow Development SOP](./workflow-development.md#task-parameters).
- For the supported GPU accelerator types and per-region availability, see
  [Regional Capabilities SOP](./regional-capabilities.md).
- For diagnosing workflow creation issues and run failures generally, see the
  [Troubleshooting SOP](./troubleshooting.md).
