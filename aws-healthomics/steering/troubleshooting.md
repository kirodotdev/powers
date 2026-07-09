# SOP: Troubleshooting HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, diagnose and resolve common HealthOmics workflow failures.

## Workflow Creation Failure

IF a workflow fails to reach `CREATED` status, check these causes in order:

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
