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

## Common Run Failure Patterns

The table below maps error messages observed against the service to the causes worth investigating first. Treat a row as a starting point, not a diagnosis: the same message can arise from more than one cause, and the ordering reflects which is most common rather than which is certain. IF the first action does not resolve it, call `DiagnoseAHORunFailure` and work from the engine and task logs.

| Error message pattern | Investigate in this order | First action |
| --- | --- | --- |
| `couldn't construct <Type> from "..."` | 1. Struct passed as a JSON-encoded string rather than an object 2. Field name does not match the struct definition 3. Required field absent | Pass the value as a JSON object. See [Parameter Types](./running-a-workflow.md#parameter-types). |
| `IAM role is invalid or inaccessible` | 1. Role ARN wrong or role deleted 2. Trust policy does not allow `omics.amazonaws.com` 3. Role belongs to another account | `aws iam get-role --role-name <name>`, then read `AssumeRolePolicyDocument`. |
| `S3 bucket not located in <region>` | 1. Output bucket is in a different region than the run | `aws s3api get-bucket-location --bucket <name>`. A `null` LocationConstraint means `us-east-1`. Use a bucket in the run's region. |
| `S3 access denied for s3://...` | 1. Role lacks `s3:PutObject` on the output prefix 2. Bucket policy denies the role 3. Object is SSE-KMS encrypted and the role lacks key access | Check the role's policies for S3 write on that prefix, then the bucket policy, then the KMS key policy. |
| `has an invalid structure. Provide a valid ECR image URI` | 1. Task names a public registry and no container registry map was attached at workflow creation 2. Map attached but missing an entry for that registry | Re-create the workflow with `container_registry_map`, or replace the URI in the definition with a private ECR URI. The map is set at creation and cannot be added to an existing workflow. |
| `Container image ... not found` | 1. Tag does not exist in ECR 2. Pull-through cache not yet populated 3. Repository policy does not grant HealthOmics pull access | `CheckContainerAvailability` with `initiate_pull_through: true`, then `ListECRRepositories` to confirm accessibility. |
| `command not found` in a task log | 1. Image lacks a tool the command block invokes | The image exists but does not carry the tool. Use a multi-tool image — see Phase 1 of the [WDL migration SOP](./migration-guide-for-wdl.md). |
| `Invalid zip file` on the workflow, not the run | 1. Definition source was a bare `.wdl`/`.nf`/`.cwl` file rather than a ZIP 2. Archive is corrupt | Package with `PackageAHOWorkflow`. See [Deploying a Workflow](./workflow-development.md#step-1-packaging). |

Several of these are knowable before a run starts. `ValidateAHORunReadiness` checks the role, output location, input objects and container accessibility in one call — see [Pre-Run Validation](./running-a-workflow.md#pre-run-validation). PREFER it over discovering these one failed run at a time.

Two properties of run failures shape how to read them:

- **The message names where execution stopped, not what is misconfigured.** A missing container registry map surfaces as a task-level image URI error partway through the run, after earlier tasks have already consumed billed compute.
- **Input errors arrive after PENDING.** Parameters are validated by the engine, not by `StartRun`, so a mistyped parameter costs the same minutes as a real workflow defect before it reports.

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
