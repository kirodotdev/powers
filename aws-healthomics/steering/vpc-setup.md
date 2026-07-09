# SOP: VPC Setup for HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, help users set up a VPC for use with HealthOmics VPC Connected Workflow Runs. This covers VPC infrastructure requirements including subnets, NAT Gateways, security groups, route tables, and VPC endpoints.

## Trigger Conditions

Follow this SOP WHEN:
- User wants to set up a VPC for HealthOmics workflows.
- User wants to configure subnets, NAT Gateways, security groups, or route tables for HealthOmics.
- User wants to know which Regions and Availability Zones HealthOmics supports.
- User wants to add VPC endpoints to optimize costs or performance for HealthOmics.
- User asks about VPC requirements for running workflows with internet access.

DO NOT follow this SOP WHEN:
- User wants to start a workflow run with VPC networking — use the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md).
- User wants to create or manage a HealthOmics Configuration resource — use the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).

## Key Concepts

- **Networking Mode** — Controls network access for a workflow run. Two modes are available:
  - `RESTRICTED` (default) — Runs can only access S3 and ECR in the same Region. No internet or cross-Region access.
  - `VPC` — Run traffic is routed through ENIs in the customer's VPC. Enables internet, cross-Region, and private resource access.
- **ENI** — Elastic Network Interface. HealthOmics provisions ENIs in the customer's VPC to route run traffic. These are managed automatically by the HealthOmics service-linked role.
- **NAT Gateway** — Required in the customer's VPC for runs that need public internet access. Runs connected to a VPC do NOT automatically have internet access — the VPC must be configured with a NAT Gateway.
- **In-Region S3 Routing** — In-Region Amazon S3 traffic is routed through the HealthOmics service VPC by default. If you configure Amazon S3 interface endpoints in your VPC, traffic is routed through your VPC instead. Use S3 Gateway endpoints for best performance and cost optimization.

## Supported Regions and Availability Zones

HealthOmics Workflows operates in the following Regions and Availability Zones. When creating VPC subnets, ensure they are in one or more of these Availability Zones.

| Region | Availability Zone Name | Availability Zone ID |
|---|---|---|
| us-west-2 | us-west-2a | usw2-az2 |
| us-west-2 | us-west-2b | usw2-az1 |
| us-west-2 | us-west-2c | usw2-az3 |
| us-east-1 | us-east-1a | use1-az4 |
| us-east-1 | us-east-1b | use1-az6 |
| us-east-1 | us-east-1c | use1-az1 |
| us-east-1 | us-east-1d | use1-az2 |
| eu-west-1 | eu-west-1a | euw1-az2 |
| eu-west-1 | eu-west-1b | euw1-az3 |
| eu-west-1 | eu-west-1c | euw1-az1 |
| eu-central-1 | eu-central-1a | euc1-az2 |
| eu-central-1 | eu-central-1b | euc1-az3 |
| eu-central-1 | eu-central-1c | euc1-az1 |
| eu-west-2 | eu-west-2a | euw2-az2 |
| eu-west-2 | eu-west-2b | euw2-az3 |
| eu-west-2 | eu-west-2c | euw2-az1 |
| ap-southeast-1 | ap-southeast-1a | apse1-az2 |
| ap-southeast-1 | ap-southeast-1b | apse1-az1 |
| ap-southeast-1 | ap-southeast-1c | apse1-az3 |
| il-central-1 | il-central-1a | ilc1-az1 |
| il-central-1 | il-central-1b | ilc1-az2 |
| il-central-1 | il-central-1c | ilc1-az3 |
| ap-northeast-2 | ap-northeast-2a | apne2-az1 |
| ap-northeast-2 | ap-northeast-2b | apne2-az2 |
| ap-northeast-2 | ap-northeast-2c | apne2-az3 |

## Procedure

### Step 1: Assess VPC Requirements

1. Determine what external resources the workflow needs to access:
   - **Public internet** (datasets, APIs, license servers) → Requires NAT Gateway.
   - **AWS services in other Regions** (cross-Region S3) → Requires NAT Gateway or VPC endpoints.
   - **Private VPC resources** (databases, internal services) → Requires appropriate security group rules.
   - **On-premises resources** → Requires Site-to-Site VPN or Direct Connect.
2. IF the user only needs same-Region S3 and ECR access, inform them that `RESTRICTED` mode (the default) is sufficient and VPC networking is not needed.

### Step 2: Create or Verify VPC Infrastructure

1. Verify the user has a VPC with appropriate subnets:
   - Use **private subnets** for workflow runs. Connecting a run to a public subnet does NOT give it internet access or a public IP address.
   - Subnets must be in Availability Zones where HealthOmics operates in the Region (see the Supported Regions and AZs table above).
   - Recommend multiple subnets across different Availability Zones for better availability.
2. IF the workflow needs public internet access, verify a NAT Gateway is configured:
   - The NAT Gateway must be in a **public subnet**.
   - The private subnets' route tables must route `0.0.0.0/0` traffic to the NAT Gateway.
   - For production workloads, recommend one NAT Gateway per Availability Zone for resiliency.
3. Verify security groups allow outbound traffic to required destinations:

   | Type | Protocol | Port Range | Destination | Description |
   |---|---|---|---|---|
   | HTTPS | TCP | 443 | 0.0.0.0/0 | Allow HTTPS to internet |
   | HTTP | TCP | 80 | 0.0.0.0/0 | Allow HTTP to internet (if needed) |

   - Use specific destination CIDR blocks instead of `0.0.0.0/0` when possible (principle of least privilege).
   - For on-premises resources, allow traffic to the specific VPN or CIDR ranges.

4. Verify route tables on private subnets:

   | Destination | Target |
   |---|---|
   | 10.0.0.0/16 | local |
   | 0.0.0.0/0 | nat-xxxxxxxxx |

   - For on-premises resources, add routes to a virtual private gateway.

5. OPTIONALLY, recommend VPC endpoints for AWS services the workflow needs to access to reduce NAT Gateway costs and improve performance.

### Step 3: Create HealthOmics Configuration

Once the VPC infrastructure is ready, create a HealthOmics Configuration resource to store the VPC settings. Follow the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).

### Step 4: Validate Setup

1. Start a test workflow run with VPC networking to validate connectivity. See the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md).
2. IF connectivity issues occur, see the [Troubleshooting SOP](./troubleshooting.md) for VPC-specific troubleshooting including VPC Flow Logs analysis.

## Best Practices

### Security
- Use least-privilege security groups. Allow only the minimum required outbound traffic. Use specific destination CIDR blocks instead of `0.0.0.0/0` when possible. Document the purpose of each security group rule.
- Separate configurations by environment (dev, staging, production). Use different VPCs or subnets for each environment. Apply appropriate tags for organization.
- Enable VPC Flow Logs for security analysis. Set up CloudWatch alarms for unusual traffic patterns. Regularly review CloudTrail logs for configuration changes.
- Use VPC endpoints for AWS services the workflow accesses to keep traffic within the AWS network, reduce NAT Gateway costs, and improve performance.

### Performance
- Network throughput starts at 10 Gbps per ENI and scales to 100 Gbps over a 60-minute period with sustained traffic. For workflows with immediate high-throughput requirements, plan ahead and contact AWS Support for pre-warming.
- Deploy one NAT Gateway per Availability Zone for production workloads to improve resiliency and throughput, and reduce cross-AZ data transfer costs.
- Reuse configurations across multiple workflows to reduce management overhead and ensure consistent network settings.
- Test configurations with test workflows before production use. Validate network connectivity and verify security group rules allow required traffic.

### Cost Optimization
- Use VPC endpoints where possible to reduce NAT Gateway data processing charges.
- Monitor data transfer costs with AWS Cost Explorer. Data transfer in has no charge; data transfer out to internet incurs standard rates; cross-Region transfer has higher rates.
- Right-size NAT Gateway deployment — one for dev, one per AZ for production. Monitor NAT Gateway utilization to avoid over-provisioning.
- Delete unused configurations regularly. Use tags to identify configuration ownership and purpose.

### Operational
- Use descriptive configuration names (e.g., `prod-genomics-vpc`, `dev-clinical-trials-vpc`). Include environment, purpose, and team in the name.
- Tag all configurations with Environment, Owner, CostCenter, and Purpose.
- Document which external services each configuration accesses. Maintain a map of security group rules and their purposes.
- Share network architecture diagrams with your team.

## VPC Networking Quotas

| Resource | Default Limit | Quota ID | Adjustable |
|---|---|---|---|
| Maximum configurations per account | 10 | L-D91CDC5E | Yes |
| Maximum security groups per configuration | 5 | — | No |
| Maximum subnets per configuration | 16 | — | No |
| Maximum subnets per Availability Zone | 1 | — | No |
| Elastic network interfaces per Region | 5,000 | — | Yes |

To request a quota increase, open the [Service Quotas console](https://console.aws.amazon.com/servicequotas/home/services/omics/quotas/L-D91CDC5E), choose **AWS services**, search for **AWS HealthOmics**, select the quota, and choose **Request quota increase**.
