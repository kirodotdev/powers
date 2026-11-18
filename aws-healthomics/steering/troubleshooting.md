# SOP: Troubleshooting HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, diagnose and resolve common HealthOmics workflow failures.

## Workflow Creation Failure

Workflow creation is asynchronous. `CreateAHOWorkflow` returns HTTP 200 with status `CREATING`; the workflow then transitions to `ACTIVE` or `FAILED`. A 200 response is NOT evidence of a valid workflow — you MUST poll `GetAHOWorkflow` until the status leaves `CREATING`. Invalid definitions are accepted at submission time and reported only as the later `FAILED` status, with the parser error in `statusMessage`.

ALSO read `statusMessage` on an `ACTIVE` workflow. It carries warnings that do not block creation but change how the workflow is interpreted — for example `MissingVersion, document should declare WDL version; draft-2 assumed`, or a report that no input parameters were found.

IF a workflow fails to reach `ACTIVE` status, check these causes in order:

1. The workflow zip package is corrupted or missing.
2. The workflow zip package has multiple workflow definition files at the top level. There MUST be only one `main.wdl`, `main.nf`, etc. at the top level — dependencies MUST be in sub-directories.
3. The workflow zip package is missing a dependency required by the workflow definition, or the dependency location is inconsistent with the import path.
4. The workflow has invalid syntax. Call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to verify.
5. After identifying and fixing the cause, redeploy the workflow by calling `CreateAHOWorkflow` (for a new workflow) or `CreateAHOWorkflowVersion` (for a new version of an existing workflow).

## Run Failures

- IF a run fails with a service error (5xx): a transient error occurred in the HealthOmics service. 
    1. Re-start the run with identical inputs.
    2. IF the previous run used a run cache you MUST also use that run cache for the re-run.
- IF a run fails with a customer error (4xx): 
    1. Call `DiagnoseAHORunFailure` to access important logs and run information. 
    2. Use the diagnosis to fix the workflow, service role permissions or input parameters as appropriate. 
    3. IF you modify the workflow definition you MUST create a new version via `CreateAHOWorkflowVersion`.
    4. IF the previous run used a Run Cache you MUST reference that when starting the new run. Otherwise, you MAY create a Run Cache for this run.
    5. Start a new run of the workflow/ workflow version using identical or modified inputs and Run Cache as appropriate.

## Nextflow Version-Specific Issues

IF a Nextflow run fails or behaves unexpectedly, match the symptom before deeper diagnosis:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Unknown process directive: echo` or `Unrecognized process directive echo`, before any task starts | The `echo` directive was removed in v26.10 | Replace `echo true` with `debug true`. `engineSettings.syntaxVersion = "v1"` does NOT help |
| `NoClassDefFoundError: io/seqera/serde/gson/GsonEncodingStrategy` | A registry-style module include (`include { X } from 'nf-core/foo'`) | Vendor the module into the workflow zip and include it by relative path (`'./modules/nf-core/foo/main.nf'`) |
| `Missing workflow parameters: ...` for typed `params` that have defaults | Typed params with defaults are treated as required | Pass every typed param in the run parameters |
| Execution reports (report, timeline, trace, DAG) missing from the run output | A relative `file` without `directory` is not exported | On v26.10+, set a relative `directory`. On any version, use an absolute `file` under `/mnt/workflow/output/` |
| The run used an unexpected engine version (the engine log states the version used) | `manifest.nextflowVersion` is missing or is a range | Pin the version exactly (e.g. `'=26.10.0'`) — see [Pinning the Nextflow Version](./running-a-workflow.md#pinning-the-nextflow-version) |
| Tasks with `eval(...)` outputs re-ran on a run cache after moving to v26.10 | The `eval` output hash changed in v26.10 | Expected, once per run cache. Later v26.10 runs cache normally |
| Every task missed the run cache | A container referenced by a mutable tag (e.g. `:latest`) was republished; the image digest is part of the task hash | Reference containers by digest when using run caches |

## VPC Connected Workflow Run Failures

IF a workflow run using VPC networking fails with connectivity-related errors:

- **Run fails to access public internet:**
    1. Verify the configuration is using private subnets (not public subnets).
    2. Verify the private subnets' route tables have a route to a NAT Gateway for `0.0.0.0/0`.
    3. Verify the NAT Gateway is in a public subnet with a route to an Internet Gateway, and is in AVAILABLE state with an Elastic IP.
    4. Verify security groups allow outbound traffic to the required destinations and ports.
    5. Call `DiagnoseAHORunFailure` to get detailed failure information.
    6. Fix the VPC configuration and retry the run.
- **Run fails to access AWS services in other Regions:**
    1. Verify the VPC has internet access via NAT Gateway or appropriate VPC endpoints configured.
    2. Verify the IAM service role has permissions to access the cross-Region resources.
- **Run fails to access private VPC resources:**
    1. Verify the security groups allow traffic to the target resource's IP and port.
    2. Verify network ACLs on the subnets allow the required traffic (network ACLs are stateless — they need explicit rules for both directions, including ephemeral ports 1024-65535 for return traffic).
    3. Verify the target resource's security group allows inbound traffic from the HealthOmics ENIs.
- **Run fails with non-connectivity errors:**
    - IF 5xx, a transient error occurred — re-start the run without changes.
    - IF 4xx, call `DiagnoseAHORunFailure` to diagnose and fix the workflow. See the [Running a Workflow SOP](./running-a-workflow.md) for handling run failures.
- **Cause is unclear:**
    1. Enable VPC Flow Logs on the VPC or on specific HealthOmics ENIs (tagged `Service: HealthOmics`, `eniType: CUSTOMER`).
    2. Query flow logs in CloudWatch Logs Insights filtering for `action = "REJECT"` to identify rejected traffic.
    3. Use the results to identify the failing network component (security group, network ACL, NAT Gateway, or route table) and fix it.
    4. Retry the run.

For VPC infrastructure setup, see the [VPC Setup SOP](./vpc-setup.md). For configuration management, see the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).
