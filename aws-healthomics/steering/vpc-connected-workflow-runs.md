# SOP: VPC Connected Workflow Runs

## Purpose

This SOP defines how you, the agent, help users run HealthOmics workflows with VPC networking enabled. VPC Connected Workflow Runs allow workflows to access resources in the customer's VPC, the public internet, AWS services in other Regions, and on-premises resources.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to run a workflow that needs access to the public internet (e.g., downloading datasets from NIH, academic repositories).
- User wants to run a workflow that connects to third-party license servers or external APIs.
- User wants to run a workflow that reads or writes data from S3 buckets in other AWS Regions.
- User wants to run a workflow that accesses on-premises resources via VPN or Direct Connect.
- User wants to run a workflow that connects to AWS resources within their VPC.
- User mentions "VPC", "internet access", "public internet", "cross-region", "VPC networking", or "VPC connected" in the context of running workflows.

DO NOT follow this SOP WHEN:
- User only needs to access S3 and ECR in the same Region — the default `RESTRICTED` networking mode handles this.
- User wants to manage configurations without starting a run — use the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).
- User wants to set up a VPC, subnets, or NAT gateways from scratch — use the [VPC Setup SOP](./vpc-setup.md).

## Prerequisites

1. An `ACTIVE` HealthOmics Configuration with VPC networking settings. See [HealthOmics Configuration Management SOP](./healthomics-configuration.md) to create one, or [VPC Setup SOP](./vpc-setup.md) for full VPC infrastructure setup.
2. An IAM service role for HealthOmics with permissions to run workflows.
3. ALWAYS read and use preferences/defaults from `.healthomics/config.toml` if present.

## Procedure

### Step 1: Create or Verify Configuration

1. Call `ListAHOConfigurations` to check for existing configurations.
2. IF a suitable `ACTIVE` configuration exists, call `GetAHOConfiguration` to verify it has `runConfigurations.vpcConfig` with valid `securityGroupIds` and `subnetIds`. Configurations without VPC settings cannot be used for VPC Connected Workflow Runs.
3. IF no suitable configuration exists, follow the [HealthOmics Configuration Management SOP](./healthomics-configuration.md) to create one. For full VPC infrastructure setup, see the [VPC Setup SOP](./vpc-setup.md).
4. Verify the configuration status is `ACTIVE` before proceeding.

### Step 2: Start a Workflow Run with VPC Networking

1. Verify the workflow has been deployed successfully via `GetAHOWorkflow`.
2. Verify inputs and parameters are ready (see [Running a Workflow SOP](./running-a-workflow.md) for input validation steps).
3. Call `StartAHORun` with the following VPC-specific parameters in addition to standard run parameters:
   - `networking_mode` — Set to `VPC`.
   - `configuration_name` — The name of the `ACTIVE` configuration to use.
4. ALWAYS include standard run parameters from `.healthomics/config.toml`:
   - `role_arn` — IAM service role ARN.
   - `output_uri` — S3 output location.
   - `storage_type` — `DYNAMIC` recommended.

### Step 3: Verify Connectivity

1. Call `GetAHORun` to monitor the run status and verify VPC configuration details in the response:
   - `networkingMode` — Should show `VPC`.
   - `configuration` — Should show the configuration name, ARN, and UUID.
   - `vpcConfig` — Should show the security group IDs and VPC ID.
2. Check workflow logs in CloudWatch Logs for connection success or failure messages.
3. IF the run fails due to connectivity issues, see the [Troubleshooting SOP](./troubleshooting.md) for VPC-specific failure handling and VPC Flow Logs analysis.

## Examples

### StartAHORun request with VPC networking

```json
{
  "workflow_id": "1234567",
  "role_arn": "arn:aws:iam::123456789012:role/OmicsWorkflowRole",
  "output_uri": "s3://my-bucket/outputs/",
  "storage_type": "DYNAMIC",
  "networking_mode": "VPC",
  "configuration_name": "prod-genomics-vpc",
  "parameters": {
    "inputUri": "s3://my-bucket/input/sample.fastq",
    "referenceUri": "s3://my-bucket/reference/genome.fasta"
  }
}
```

### GetAHORun response (VPC-related fields)

```json
{
  "arn": "arn:aws:omics:us-west-2:123456789012:run/1234567",
  "id": "1234567",
  "status": "RUNNING",
  "workflowId": "7654321",
  "networkingMode": "VPC",
  "configuration": {
    "name": "prod-genomics-vpc",
    "arn": "arn:aws:omics:us-west-2:123456789012:configuration/prod-genomics-vpc",
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  "vpcConfig": {
    "securityGroupIds": ["sg-0123456789abcdef0"],
    "vpcId": "vpc-0abcdef1234567890"
  }
}
```

**Note:** If `networking_mode` is omitted, the default `RESTRICTED` mode is used. No configuration is required for `RESTRICTED` mode.

## Call Caching Considerations

When using VPC networking with call caching, ensure your workflow engine is configured appropriately:
- Consult the HealthOmics documentation on engine-specific caching features.
- When connecting to non-deterministic or dynamic resources (e.g., third-party databases on the public internet), use the cache task opt-out feature in your workflows to avoid caching dynamic datasets that could impact run outputs.

## Limitations and Considerations

- **VPC networking is per-run** — You specify the networking mode each time you start a run. Different runs of the same workflow can use different networking modes.
- **No public IP for runs** — Connecting a run to a public subnet does NOT give it internet access or a public IP address. Always use private subnets with NAT Gateway routes.
- **Configuration must be ACTIVE** — You cannot start a run with a configuration that is in `CREATING`, `UPDATING`, `DELETING`, `DELETED`, or `FAILED` status.
- **Configuration must have VPC settings** — Verify the configuration has `runConfigurations.vpcConfig` before using it for VPC Connected Workflow Runs.
- **Network throughput scaling** — Network throughput starts at 10 Gbps per ENI and scales to 100 Gbps over a 60-minute period with sustained traffic. Contact AWS Support for immediate high-throughput needs.
- **Data transfer responsibility** — When using VPC networking mode, you are responsible for determining whether it is safe and compliant to transfer or use data across AWS Regions.
- **ENI management** — Do not modify or delete ENIs created by HealthOmics (tagged with `Service: HealthOmics` and `eniType: CUSTOMER`). This can cause service delays or disruptions.
- **HealthOmics-managed VPC unchanged** — Every HealthOmics run executes inside a VPC owned by HealthOmics. Configuring your run to access your VPC has no effect on the HealthOmics-managed VPC.
- **In-Region S3 routing** — In-Region S3 traffic routes through the HealthOmics service VPC by default. Configuring S3 interface endpoints overrides this. Use S3 Gateway endpoints for best performance.
