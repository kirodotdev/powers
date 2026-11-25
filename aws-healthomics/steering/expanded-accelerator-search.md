# SOP: Expanded Accelerator Search (several GPU accelerator types and sizes for one task)

## Purpose

This SOP defines how you, the agent, configure a HealthOmics WDL or Nextflow task to accept several GPU
accelerator types and a range of vCPUs and memory, so HealthOmics searches every matching instance type in the
Region at the same time and runs the task on one that has capacity. This is *expanded accelerator search*. For
general task resource directives, see the [Workflow Development SOP](./workflow-development.md#task-parameters).
For an ordered list of resource profiles, see the [Resource Fallback SOP](./resource-fallback.md).

## Terms

- **Expanded accelerator search** (expanded search): the task lists several accelerator types, or sets
  `omicsMaxCpu` or `omicsMaxMemory`. HealthOmics searches every matching type and size at the same time.
- **Predefined accelerator bundle**: a fixed accelerator value that covers more than one instance family
  (`nvidia-tesla-t4-a10g`, `nvidia-l4-a10g`, `nvidia-t4-a10g-l4`). HealthOmics searches its families one at a
  time. A predefined bundle can be one entry of an expanded search list.
- USE these two names when you talk to the user. DO NOT call expanded search a "bundle".

## When to Use This

- RECOMMEND expanded accelerator search WHEN a GPU task can run on several accelerator types or sizes without
  changes to its command, and the user sees long waits or capacity failures (`INSTANCE_RESERVATION_FAILED`)
  with a single accelerator type or a predefined accelerator bundle. The more instance types a task can accept,
  the more likely HealthOmics is to find capacity for it.
- KEEP a single `acceleratorType` WHEN the task needs one specific GPU.
- USE `omicsResourceFallbackOrder` WHEN the user wants a fixed order of preference, or a fall back to CPU. A
  profile in that order can itself use expanded search (see
  [Use Expanded Search in a Fallback Profile](#use-expanded-search-in-a-fallback-profile)).
- Expanded accelerator search is available for WDL and Nextflow. CWL is not supported: DO NOT write a
  comma-separated `acceleratorType` in a CWL workflow.

## Choose a Placement Method

| Method | Task configuration | How HealthOmics searches | Instance type selected |
|---|---|---|---|
| Single accelerator type | `acceleratorType: "nvidia-l4"` | One accelerator type | The smallest size that fits the request |
| Predefined accelerator bundle | `acceleratorType: "nvidia-l4-a10g"` | One instance family at a time | First available matching instance |
| Expanded accelerator search | A comma-separated `acceleratorType`, or `omicsMaxCpu` / `omicsMaxMemory` | Every matching type and size at the same time | First available matching instance |
| Resource fallback | `omicsResourceFallbackOrder` | One profile at a time, each up to its wait timeout | The first profile that gets capacity, including an optional final CPU profile |

## What Makes a Task Use Expanded Search

A GPU request uses expanded accelerator search WHEN `acceleratorType` is a comma-separated list of accelerator
types or predefined accelerator bundles, OR WHEN an `acceleratorType` is combined with `omicsMaxCpu` or
`omicsMaxMemory` (every size of that accelerator type in the range).

## How It Works

1. The user lists the accelerator types, the number of GPUs, and the minimum and maximum vCPUs and memory.
2. HealthOmics finds every instance type of the listed accelerator types that is offered in the Region and has
   vCPUs and memory in the range. IF no instance type has exactly the requested number of GPUs, HealthOmics
   uses the instance types with the next larger number of GPUs. THEN, IF the task sets `disks` (WDL) or `disk`
   (Nextflow), it keeps only the instance types whose local NVMe storage is at least that size. It does not
   move to a larger number of GPUs to find more storage.
3. HealthOmics requests capacity across all matching instance types in a single search. The search repeats until
   an instance launches or the wait timeout ends.
4. The task runs on the instance type that launched, and HealthOmics does not move it to a different type
   later. The order of the list does not set a preference (see
   [Choose the Accelerator Types](#choose-the-accelerator-types)).
5. IF no capacity is found within the wait timeout, the task fails with reason `INSTANCE_RESERVATION_FAILED`.

## Choose the Accelerator Types

- LIST only the accelerator types that meet the task's performance needs. HealthOmics runs the task on the first
  matching instance type that launches, not the fastest, so a list that includes `nvidia-tesla-t4` can run on T4
  even when a faster GPU is free.
- DO NOT tell the user that expanded search picks the cheapest or lowest-priced instance type. Say that the task
  runs on a matching instance type that has capacity.
- IF the task needs a specific GPU when it is available, and can wait for it, USE `omicsResourceFallbackOrder`
  with that GPU in the first profile and an expanded search or CPU profile after it.
- Each task of a scatter searches for capacity on its own, so tasks of one scatter can run on different
  instance types. IF the task's output or runtime must not depend on the GPU type, TELL the user.
- MORE accelerator types and a WIDER vCPU and memory range give HealthOmics more instance types to search,
  which shortens capacity waits. A task can match at most 40 instance types; a request above that is rejected
  with `INVALID_TASK_RESOURCE_VALUE`.
- Cost: HealthOmics bills the instance type the task runs on (`instanceType` in GetRunTask), so the cost of the
  same task can differ between runs and between the tasks of one scatter.

## Field Reference

Set these fields in the task's `runtime` section in WDL, or as process directives in Nextflow. In Nextflow,
set the accelerator types and number of GPUs with the `accelerator` directive, for example
`accelerator 1, type: 'nvidia-l4,nvidia-tesla-a10g'`.

| Field | Type | Default when omitted | Notes |
|---|---|---|---|
| `acceleratorType` | String | Required | A comma-separated list of accelerator types, for example `"nvidia-l4,nvidia-tesla-a10g"`. Each entry MUST be a supported accelerator type: `nvidia-tesla-t4`, `nvidia-tesla-a10g`, `nvidia-l4`, `nvidia-l40s`. A predefined accelerator bundle (`nvidia-tesla-t4-a10g`, `nvidia-t4-a10g-l4`, `nvidia-l4-a10g`) adds each of its accelerator types to the list. |
| `acceleratorCount` | Integer | Required | The number of GPUs. MUST be at least 1. |
| `cpu` (WDL), `cpus` (Nextflow) | Integer | — | The minimum number of vCPUs. You SHOULD set it. |
| `memory` | String, for example `"32 GiB"` (WDL) or `'32 GB'` (Nextflow) | — | The minimum memory. You SHOULD set it. |
| `omicsMaxCpu` | Integer | No upper limit | The maximum number of vCPUs. MUST be at least `cpu` (WDL) or `cpus` (Nextflow). |
| `omicsMaxMemory` | String, in the same format as `memory` | No upper limit | The maximum memory. MUST be at least `memory`. |
| `omicsResourceWaitTimeoutInMin` | Integer | 20 minutes | How long HealthOmics searches for capacity before the task fails. The allowed range is 20–10080 minutes (7 days). A negative value is rejected. A positive value below 20 or above 10080 is set to the nearest bound, with a run log warning. |
| `disks` (WDL), `disk` (Nextflow) | WDL: `"400 GiB"`; Nextflow: `'400 GB'` | No minimum | The minimum local NVMe storage. See [Local Scratch Storage](#local-scratch-storage). |

- WHEN a comma-separated `acceleratorType` is set with no `omicsMaxCpu`/`omicsMaxMemory`, every larger size of the
  listed accelerator types can be used. A single `acceleratorType` with neither field is not expanded search: it
  runs on the smallest size that fits the request.
- Write Nextflow memory and disk values the way the directives accept them (`'32 GB'`); `GiB` is not accepted
  in Nextflow.
- A task that sets expanded search fields at the top level MUST NOT also use `omicsResourceFallbackOrder`. WDL
  rejects the workflow at CreateWorkflow. Nextflow only warns, and the process's `omicsMaxCpu`,
  `omicsMaxMemory` and `omicsResourceWaitTimeoutInMin` are never applied. Put the fields in a profile instead.
- Retries above the maximums: WDL doubles `memory` on an out-of-memory retry, and a Nextflow process can raise
  it on each attempt (for example `memory { 32.GB * task.attempt }`). HealthOmics rejects a retry that requests
  more memory than `omicsMaxMemory`, or more vCPUs than `omicsMaxCpu`, with `INVALID_TASK_RESOURCE_VALUE`, and
  the run fails. Each retry searches all matching instance types again, so it can run on a different instance
  type than the first attempt. SET `omicsMaxCpu` and `omicsMaxMemory` to the largest values any attempt can
  request.

## Examples

The following task can run on any instance type with one `nvidia-l4` or `nvidia-tesla-a10g` GPU, 8–16 vCPUs,
and 32–64 GiB of memory: `omics.g6.2xlarge`, `omics.g6.4xlarge`, `omics.g5.2xlarge` and `omics.g5.4xlarge`.
HealthOmics searches for capacity for up to 30 minutes.

### WDL

```wdl
task align {
  command <<<
    echo "Running on ${AWS_HEALTHOMICS_RESOURCE_TYPE}"
  >>>
  runtime {
    docker: "my-registry/align-gpu:latest"
    acceleratorType: "nvidia-l4,nvidia-tesla-a10g"
    acceleratorCount: 1
    cpu: 8
    memory: "32 GiB"
    omicsMaxCpu: 16
    omicsMaxMemory: "64 GiB"
    omicsResourceWaitTimeoutInMin: 30
  }
}
```

### Nextflow

```groovy
process ALIGN {
    container 'my-registry/align-gpu:latest'
    accelerator 1, type: 'nvidia-l4,nvidia-tesla-a10g'
    cpus 8
    memory '32 GB'
    omicsMaxCpu 16
    omicsMaxMemory '64 GB'
    omicsResourceWaitTimeoutInMin 30

    script:
    """
    echo "Running on \$AWS_HEALTHOMICS_RESOURCE_TYPE"
    """
}
```

### Several Sizes of One Accelerator Type

To search every size of one accelerator type in a range, list a single accelerator type and set a maximum. For
example, `acceleratorType: "nvidia-l4"` with `acceleratorCount: 1`, `cpu: 8` and `omicsMaxCpu: 64` searches
the four one-GPU `nvidia-l4` sizes `omics.g6.2xlarge`, `omics.g6.4xlarge`, `omics.g6.8xlarge` and
`omics.g6.16xlarge`. The 4-GPU sizes are excluded because the task requests one GPU.

## Use Expanded Search in a Fallback Profile

A profile in `omicsResourceFallbackOrder` can use expanded search: give it a comma-separated `acceleratorType`,
and add `omicsMaxCpu` and `omicsMaxMemory` as needed. HealthOmics searches all accelerator types of the profile
at the same time for the profile's `omicsResourceWaitTimeoutInMin`, then moves to the next profile. The
following order searches `nvidia-l40s` for up to 45 minutes, then `nvidia-l4` and `nvidia-tesla-a10g` together
with 8–16 vCPUs, and then falls back to CPU.

```wdl
runtime {
  omicsResourceFallbackOrder: [
    {"acceleratorType": "nvidia-l40s", "acceleratorCount": 1,
     "cpu": 8, "memory": "32 GiB", "omicsResourceWaitTimeoutInMin": 45},
    {"acceleratorType": "nvidia-l4,nvidia-tesla-a10g", "acceleratorCount": 1,
     "cpu": 8, "memory": "32 GiB", "omicsMaxCpu": 16, "omicsMaxMemory": "64 GiB"},
    {"cpu": 32, "memory": "128 GiB"}
  ]
}
```

```groovy
omicsResourceFallbackOrder([
    [acceleratorType: 'nvidia-l40s', acceleratorCount: 1, cpus: 8, memory: '32 GB',
     omicsResourceWaitTimeoutInMin: 45],
    [acceleratorType: 'nvidia-l4,nvidia-tesla-a10g', acceleratorCount: 1, cpus: 8, memory: '32 GB',
     omicsMaxCpu: 16, omicsMaxMemory: '64 GB'],
    [cpus: 32, memory: '128 GB']
])
```

- `omicsMaxCpu` and `omicsMaxMemory` are allowed only in a profile that sets `acceleratorType`, and MUST be at
  least the profile's minimum vCPUs and memory. They are rejected in a CPU profile.
- An expanded search profile with no matching instance type in the Region is skipped, with a warning in the run
  log, and the next profile runs. The task is rejected only when no profile can run.

## Find the Instance Type a Task Ran On

Use `aws omics get-run-task --id <run-id> --task-id <task-id>` (GetRunTask), or for every task of a run
`aws omics list-run-tasks --id <run-id> --query 'items[].{task: taskId, name: name, instance: instanceType}'`:

- `instanceType` is the instance type the task ran on, and the type HealthOmics bills. It is empty until the
  task gets an instance.
- `cpus`, `memory`, and `gpus` show the minimum values the user requested, not the size of the instance type.
- In the task container, the `AWS_HEALTHOMICS_RESOURCE_TYPE` environment variable holds the accelerator type of
  the instance the task runs on, for example `nvidia-l4`, so a command can branch on the GPU it received.

## Local Scratch Storage

GPU tasks use the local NVMe storage of the instance they land on (see the
[Ephemeral Storage SOP](./ephemeral-storage.md)). Because expanded search can land on different instance types,
the storage can vary from task to task.

- IF the task needs a minimum amount of scratch storage, SET `disks` (WDL, in GiB) or `disk` (Nextflow) to that
  minimum. HealthOmics then only matches instance types whose local NVMe storage is at least that size. SET
  only the true minimum: a higher value removes instance types from the search and lengthens capacity waits.
- The run log names the instance types left out for storage.
- IF no listed instance type has that much storage, the task fails when HealthOmics creates it, with reason
  `INVALID_TASK_RESOURCE_VALUE`. RECOMMEND a lower minimum, or accelerator types and sizes with more NVMe
  storage. In a fallback profile, an expanded search that no instance type satisfies is skipped.
- Instance storage is published in decimal GB, and `disks` is in GiB: 900 GB is about 838 GiB. A larger size
  does not always have more storage (the `g5`, `g6` and `g6e` 16xlarge sizes have half the storage of the
  12xlarge). Check the exact sizes in the Ephemeral Storage SOP before you set a minimum.

```wdl
runtime {
  acceleratorType: "nvidia-l4,nvidia-tesla-a10g"
  acceleratorCount: 1
  cpu: 8
  memory: "32 GiB"
  disks: "400 GiB"
}
```

```groovy
process ALIGN {
    accelerator 1, type: 'nvidia-l4,nvidia-tesla-a10g'
    cpus 8
    memory '32 GB'
    disk '400 GB'
    ...
}
```

## Troubleshooting

Find the failure reason with `aws omics get-run --id <run-id>` (`failureReason`, `statusMessage`) or
`aws omics get-run-task` for the task. Use the reason to choose the fix; read the status message for the
details (the message text can change).

| Failure reason | When | Cause | Fix |
|---|---|---|---|
| `UNSUPPORTED_GPU_INSTANCE_TYPE` | Task creation | None of the listed accelerator types is offered in the Region, or the run uses the ARM64 runtime platform | USE an accelerator type offered in the Region (see the [Regional Capabilities SOP](./regional-capabilities.md)), or run the task on x86 |
| `INVALID_TASK_RESOURCE_VALUE` | Task creation | No instance type in the Region matches the number of GPUs, the vCPU and memory range and the `disks` minimum; a maximum is below its minimum; `acceleratorCount` is missing; more than 40 instance types match; or expanded search fields are set both at the top level and with `omicsResourceFallbackOrder` | WIDEN the vCPU and memory range, lower the `disks` minimum, set `acceleratorCount`, narrow a very broad request, or MOVE the fields into a profile. MAKE `omicsMaxCpu` at least `cpu`/`cpus` and `omicsMaxMemory` at least `memory` |
| `INSTANCE_RESERVATION_FAILED` | Run failure | No matching instance type had capacity within the wait timeout | RECOMMEND a longer `omicsResourceWaitTimeoutInMin`, more accelerator types, or a wider vCPU and memory range. To fall back to CPU, use `omicsResourceFallbackOrder` with a final CPU profile |

- A run log warning that an accelerator type was ignored (unsupported, not offered in the Region, or no size in
  the range) names the type and the types searched instead. The run fails only when no listed type is left.
- A run log warning that an accelerator type is listed more than once is harmless: REMOVE the duplicate.
- **WDL workflow fails to create:** WDL checks expanded search values at CreateWorkflow and rejects an
  unsupported accelerator type, an empty entry in `acceleratorType` (a doubled or trailing comma), a maximum
  below its minimum, or a negative wait timeout. The workflow status message names the value.
- **Nextflow run fails with `WORKFLOW_RUN_FAILED`:** Nextflow reports invalid expanded search values in the workflow's
  `statusMessage` at CreateWorkflow, but the workflow still becomes `ACTIVE`. The run then fails when the task
  starts, even with `errorStrategy 'retry'`, and the reason is in the engine log. IF a user creates a Nextflow
  workflow that uses expanded search, CHECK `statusMessage` with GetWorkflow before starting a run.
- IF the task ran on a different GPU than the user expected, CHECK `instanceType` with GetRunTask and the run
  log for ignored types, then REMOVE the types that don't meet the task's needs or use a fallback order.

## Related Documentation

- [Resource Fallback SOP](./resource-fallback.md) for `omicsResourceFallbackOrder`.
- [Regional Capabilities SOP](./regional-capabilities.md) for GPU instance families per Region.
- [Ephemeral Storage SOP](./ephemeral-storage.md) for GPU local NVMe capacity.
