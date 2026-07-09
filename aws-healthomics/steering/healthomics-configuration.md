# SOP: HealthOmics Configuration Management

## Purpose

This SOP defines how you, the agent, create and manage HealthOmics Configuration resources. A Configuration stores reusable VPC networking settings (subnets and security groups) that can be shared across multiple workflow runs.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to create, view, or delete a HealthOmics Configuration.
- User wants to configure settings for workflow runs.
- User asks about managing configurations for HealthOmics.
- User wants to list existing configurations or check configuration status.

DO NOT follow this SOP WHEN:
- User wants to start a workflow run with VPC networking — use the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md).
- User wants to set up a VPC, subnets, or NAT gateways from scratch — use the [VPC Setup SOP](./vpc-setup.md).

## Key Concepts

- **Configuration** — A reusable HealthOmics resource that stores settings for workflow runs. Configurations can be shared across multiple workflow runs.
- **Configuration Name** — A unique name (maximum 128 characters) that identifies the configuration. Must start with an alphanumeric character and can contain letters, numbers, hyphens, dots, and underscores (pattern: `[A-Za-z0-9][A-Za-z0-9\-\._]*`). Used to reference the configuration when starting runs.
- **Configuration Description** — An optional description (maximum 256 characters) of the configuration's purpose.
- **Configuration Status** — The lifecycle state of a configuration: `CREATING`, `ACTIVE`, `UPDATING`, `DELETING`, `DELETED`, or `FAILED`.
- **Service-Linked Role** — An IAM role (`AWSServiceRoleForHealthOmics`) automatically created when you create your first configuration. It grants HealthOmics permission to manage elastic network interfaces (ENIs) in the customer's VPC.

### Configuration Lifecycle

`CREATING` → `ACTIVE` → `UPDATING` → `DELETING` → `DELETED`

A configuration may also reach `FAILED` status if provisioning encounters an error.

- **CREATING** — Resources are being provisioned. This can take up to 15 minutes.
- **ACTIVE** — The configuration is ready to use with workflow runs.
- **UPDATING** — The configuration is being modified.
- **DELETING** — Resources are being cleaned up.
- **DELETED** — The configuration has been fully removed.
- **FAILED** — Configuration provisioning or deletion encountered an error.

## VPC Configuration

A VPC configuration stores VPC networking settings (subnets and security groups) that enable workflows to connect to customer VPCs.

### VPC Configuration Settings

- **VPC Config** — The networking settings within a configuration, including security group IDs and subnet IDs. All subnets and security groups must belong to the same VPC.
- **Subnet IDs** — 1 to 16 subnets. Maximum one subnet per Availability Zone. All subnets must belong to the same VPC. Use private subnets with NAT Gateway routes for runs requiring internet access.
- **Security Group IDs** — 1 to 5 security groups. All must belong to the same VPC as the subnets.

## Prerequisites

1. An existing VPC in the same Region as HealthOmics workflows.
2. At least one subnet in an Availability Zone where HealthOmics operates in the Region.
3. Appropriate security groups controlling inbound and outbound traffic.
4. IAM permissions to create and manage HealthOmics configurations.
5. Sufficient ENI capacity in the AWS account (default limit: 5,000 ENIs per Region).
6. For the first configuration created in an account: `iam:CreateServiceLinkedRole` permission to allow automatic creation of the `AWSServiceRoleForHealthOmics` service-linked role.

## Procedure

### Step 1: Gather VPC Information

1. Verify the user has the following information:
   - **VPC** — An existing VPC in the same Region as their workflows.
   - **Subnet IDs** — 1 to 16 subnets. Maximum one subnet per Availability Zone. All subnets must belong to the same VPC. Use private subnets with NAT Gateway routes for runs requiring internet access.
   - **Security Group IDs** — 1 to 5 security groups. All must belong to the same VPC as the subnets.
   - **Configuration Name** — A descriptive, unique name (maximum 128 characters, pattern: `[A-Za-z0-9][A-Za-z0-9\-\._]*`). Must start with an alphanumeric character. Follow the naming convention: include environment, purpose, and team (e.g., `prod-genomics-vpc`, `dev-clinical-trials-vpc`).

### Step 2: Create the Configuration

1. Call `CreateAHOConfiguration` with:
   - `name` — The configuration name.
   - `description` — A description of the configuration's purpose (optional, maximum 256 characters).
   - `run_configurations` — Configuration settings containing:
     - `vpcConfig.securityGroupIds` — List of 1–5 security group IDs.
     - `vpcConfig.subnetIds` — List of 1–16 subnet IDs.
   - `tags` — Optional resource tags (recommended: Environment, Owner, CostCenter, Purpose).
   - `request_id` — Idempotency token (optional, auto-generated if not provided).
2. The configuration will initially have status `CREATING`. Inform the user that provisioning takes up to 15 minutes.
3. Call `GetAHOConfiguration` to poll the status until it becomes `ACTIVE`.
4. DO NOT proceed to start a workflow run until the configuration status is `ACTIVE`.

### Step 3: Verify the Configuration

1. Call `GetAHOConfiguration` with the configuration `name`.
2. Confirm the status is `ACTIVE`.
3. Confirm the VPC ID, subnet IDs, and security group IDs are correct.

### Step 4: Use the Configuration

Once the configuration is `ACTIVE`, it can be referenced when starting workflow runs with VPC networking. See the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md) for details on starting runs.

### Step 5: Handle Failures

IF the configuration creation fails or gets stuck in `CREATING`:
1. Wait up to 15 minutes — resource provisioning takes time. If the status doesn't change to `ACTIVE` after 15 minutes, continue with the checks below.
2. Verify subnets and security groups exist and belong to the same VPC.
3. Verify at least one subnet is in an Availability Zone where HealthOmics operates (see the Supported Regions and AZs table in the [VPC Setup SOP](./vpc-setup.md)).
4. Verify the user has the required IAM permissions.
5. Verify the service-linked role (`AWSServiceRoleForHealthOmics`) was created successfully. IF the creation fails due to a permissions error, advise the user to add the IAM permission shown in the Service-Linked Role section below.
6. Verify the account has not exceeded the maximum configurations quota (default: 10, quota ID: `L-D91CDC5E`).
7. Check that no two subnets are in the same Availability Zone.
8. After resolving the issue, call `DeleteAHOConfiguration` to clean up the failed configuration, then retry `CreateAHOConfiguration`.

IF a configuration deletion fails:
1. Check if active workflow runs are using the configuration. You cannot delete a configuration that is in use.
2. Wait for all runs using the configuration to complete, then retry `DeleteAHOConfiguration`.

IF deleting the service-linked role fails:
1. Verify ALL configurations in the account have been deleted first. Active configurations prevent role deletion.
2. Delete all remaining configurations using `DeleteAHOConfiguration`, then retry role deletion.

## Service-Linked Role

The first time a user creates a configuration, HealthOmics automatically creates a service-linked role (`AWSServiceRoleForHealthOmics`) in their account. This role grants HealthOmics the following permissions to manage ENIs in the user's VPC:

- `ec2:DescribeSubnets`, `ec2:DescribeTags`, `ec2:DescribeSecurityGroups`, `ec2:DescribeSecurityGroupRules`, `ec2:DescribeVpcs`, `ec2:DescribeNetworkInterfaces`, `ec2:DescribeAvailabilityZones`
- `ec2:GetSecurityGroupsForVpc`
- `ec2:CreateNetworkInterface` (tagged with `Service: HealthOmics`)
- `ec2:CreateTags` (on network interfaces created by HealthOmics)
- `ec2:DeleteNetworkInterface` (only for HealthOmics-tagged ENIs)
- `ec2:AssignPrivateIpAddresses`, `ec2:UnassignPrivateIpAddresses` (only for HealthOmics-tagged ENIs)

The user must have `iam:CreateServiceLinkedRole` permission for this to succeed. IF the creation fails due to a permissions error, advise the user to add the following IAM permission:

```json
{
  "Effect": "Allow",
  "Action": "iam:CreateServiceLinkedRole",
  "Resource": "arn:aws:iam::*:role/aws-service-role/omics.amazonaws.com/AWSServiceRoleForHealthOmics",
  "Condition": {
    "StringEquals": {
      "iam:AWSServiceName": "omics.amazonaws.com"
    }
  }
}
```

**Note on Service-Linked Role Deletion:** The service-linked role can only be deleted after ALL configurations in the account have been deleted. IF the user wants to delete the role:
1. First delete all configurations using `DeleteAHOConfiguration`.
2. Then delete the role through the IAM console or API.

## Managing Configurations

### Listing Configurations

1. Call `ListAHOConfigurations` to retrieve all configurations in the account.
2. Present the results showing name, description, status, and creation time.
3. IF the user is looking for a specific configuration, filter the results by name or status.

### Getting Configuration Details

1. Call `GetAHOConfiguration` with the configuration `name`.
2. Present the full details including:
   - Configuration ARN and UUID.
   - VPC ID, subnet IDs, and security group IDs.
   - Current status.
   - Creation time and tags.

### Deleting a Configuration

1. Verify the configuration is NOT currently in use by any active workflow runs.
2. Call `DeleteAHOConfiguration` with the configuration `name`.
3. The configuration status will change to `DELETING` while resources are cleaned up, then to `DELETED`.

## Examples

### Creating a configuration with multiple subnets (multi-AZ)

Request:

```json
{
  "name": "prod-genomics-vpc",
  "description": "Production VPC configuration for genomics workflows with internet access",
  "runConfigurations": {
    "vpcConfig": {
      "securityGroupIds": ["sg-0123456789abcdef0"],
      "subnetIds": [
        "subnet-0a1b2c3d4e5f6g7h8",
        "subnet-1a2b3c4d5e6f7g8h9"
      ]
    }
  },
  "tags": {
    "Environment": "production",
    "Team": "genomics"
  }
}
```

Response:

```json
{
  "arn": "arn:aws:omics:us-west-2:123456789012:configuration/prod-genomics-vpc",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "prod-genomics-vpc",
  "runConfigurations": {
    "vpcConfig": {
      "securityGroupIds": ["sg-0123456789abcdef0"],
      "subnetIds": [
        "subnet-0a1b2c3d4e5f6g7h8",
        "subnet-1a2b3c4d5e6f7g8h9"
      ],
      "vpcId": "vpc-0abcdef1234567890"
    }
  },
  "status": "CREATING",
  "creationTime": "2026-03-27T15:30:00Z",
  "tags": {
    "Environment": "production",
    "Team": "genomics"
  }
}
```

### Creating a minimal configuration (single subnet)

Request:

```json
{
  "name": "dev-testing-vpc",
  "description": "Development VPC for workflow testing",
  "runConfigurations": {
    "vpcConfig": {
      "securityGroupIds": ["sg-0987654321fedcba0"],
      "subnetIds": ["subnet-0a1b2c3d4e5f6g7h8"]
    }
  }
}
```

### Getting configuration details

Response:

```json
{
  "arn": "arn:aws:omics:us-west-2:123456789012:configuration/prod-genomics-vpc",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "prod-genomics-vpc",
  "runConfigurations": {
    "vpcConfig": {
      "securityGroupIds": ["sg-0123456789abcdef0"],
      "subnetIds": [
        "subnet-0a1b2c3d4e5f6g7h8",
        "subnet-1a2b3c4d5e6f7g8h9"
      ],
      "vpcId": "vpc-0abcdef1234567890"
    }
  },
  "status": "ACTIVE",
  "creationTime": "2026-03-27T15:30:00Z",
  "tags": {
    "Environment": "production",
    "Team": "genomics"
  }
}
```

### Listing configurations

Response:

```json
{
  "items": [
    {
      "arn": "arn:aws:omics:us-west-2:123456789012:configuration/prod-genomics-vpc",
      "name": "prod-genomics-vpc",
      "description": "Production VPC configuration for genomics workflows with internet access",
      "status": "ACTIVE",
      "creationTime": "2026-03-27T15:30:00Z"
    },
    {
      "arn": "arn:aws:omics:us-west-2:123456789012:configuration/dev-testing-vpc",
      "name": "dev-testing-vpc",
      "description": "Development VPC for workflow testing",
      "status": "ACTIVE",
      "creationTime": "2026-03-27T16:00:00Z"
    }
  ]
}
```

## Limitations and Considerations

- **Provisioning time** — Configuration creation takes up to 15 minutes while resources are provisioned. Do not attempt to start runs until the configuration status is `ACTIVE`.
- **Maximum configurations per account** — Default limit of 10 configurations (quota ID: `L-D91CDC5E`). Request a quota increase via the Service Quotas console if more are needed.
- **Single VPC per configuration** — All subnets and security groups in a configuration must belong to the same VPC. To use multiple VPCs, create separate configurations.
- **One subnet per Availability Zone** — A configuration can have at most one subnet in each Availability Zone.
- **Cannot delete in-use configurations** — A configuration that is referenced by active workflow runs cannot be deleted. Wait for all runs to complete first.
- **Configuration immutability during runs** — Workflow runs use a snapshot of the configuration at run start time. Modifying or deleting a configuration does not affect active runs.
- **Service-linked role required** — The first configuration creation in an account requires `iam:CreateServiceLinkedRole` permission. Subsequent creations do not need this.
- **ENI capacity** — HealthOmics provisions ENIs in your VPC. Monitor your ENI usage and request quota increases if needed (default: 5,000 per Region).
- **Do not modify HealthOmics ENIs** — ENIs tagged with `Service: HealthOmics` are managed by HealthOmics. Modifying or deleting them can cause service disruptions.
- **Configuration name constraints** — Must be 1-128 characters, start with an alphanumeric character, and contain only letters, numbers, hyphens, dots, and underscores.

## Configuration Limits

| Resource | Default Limit | Quota ID | Adjustable |
|---|---|---|---|
| Maximum configurations per account | 10 | L-D91CDC5E | Yes |
| Maximum security groups per configuration | 5 | — | No |
| Maximum subnets per configuration | 16 | — | No |
| Maximum subnets per Availability Zone | 1 | — | No |
| Elastic network interfaces per Region | 5,000 | — | Yes |

To request a quota increase, open the [Service Quotas console](https://console.aws.amazon.com/servicequotas/home/services/omics/quotas/L-D91CDC5E), choose **AWS services**, search for **AWS HealthOmics**, select the quota, and choose **Request quota increase**.
