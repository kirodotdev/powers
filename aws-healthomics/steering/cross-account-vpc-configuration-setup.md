# SOP: Cross-Account VPC Sharing for HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, help users/customers run HealthOmics workflows against a VPC that lives in a **different AWS account** from the one starting the run. It covers the two supported cross-account topologies — a VPC shared with AWS Resource Access Manager (RAM), and VPC peering — the setup each requires, how resource ownership is split across the accounts, and the operational consequences you MUST surface to the user.

## Trigger Conditions

Follow this SOP WHEN:
- User wants workflow runs to use a VPC and subnets owned by another AWS account (security groups may be owned by either the requester or the VPC owner).
- User wants to set up a RAM share, enable resource sharing with an AWS Organization, or share subnets/security groups to another account for HealthOmics.
- User mentions "RAM", "Resource Access Manager", "shared VPC", "shared subnet", "cross-account VPC", "centralized egress", "centralized networking", "network account", or "VPC owner account".
- User wants a run's ENIs to land in a VPC owned by a central/networking account (a common enterprise pattern).
- User asks what `vpcOwnerAccountId` on `CreateAHOConfiguration` is for, or how to set it.
- User asks whether VPC peering works with HealthOmics across accounts.

DO NOT follow this SOP WHEN:
- The VPC, subnets, and security groups are all in the **same account** that starts the run (if any resource — including security groups — comes from a different account, follow this SOP) — use the [VPC Setup SOP](./vpc-setup.md) and [HealthOmics Configuration Management SOP](./healthomics-configuration.md).
- User wants to build single-account VPC/subnet/NAT infrastructure — use the [VPC Setup SOP](./vpc-setup.md).
- User wants to start a run once a configuration already exists — use the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md).

## Key Concepts

- **Requester account** (the caller) — The account that calls `CreateAHOConfiguration` and `StartAHORun`. The run, its ENIs, and the HealthOmics service-linked role all live here.
- **VPC owner account** — The account that owns the VPC and its subnets and shares them to the requester.
- **RAM (Resource Access Manager)** — The AWS service used to share the owner's subnets (and optionally security groups) into the requester account. Requires both accounts to be in the same AWS Organization.
- **`vpcOwnerAccountId`** — The optional field on `CreateAHOConfiguration`'s `vpcConfig` that names the VPC owner account. Its presence is what tells HealthOmics the subnets are cross-account (RAM-shared) rather than local.
- **VPC peering** — An alternative topology where the run uses a VPC in its **own** account that has a peering connection to another account's VPC. This gives reachability into the peer VPC's resources; it does NOT place the run's ENIs in the other account's VPC.

## Supported Cross-Account Topologies

| Topology | Where the run's ENIs land | HealthOmics setup | Use when |
|---|---|---|---|
| **RAM-shared VPC** | Requester account, attached to the owner's shared subnets | `vpcOwnerAccountId` on the configuration | The run must operate *inside* a shared/central VPC (centralized egress, central network account). |
| **VPC peering** | Requester's own VPC | None (`vpcOwnerAccountId` not used) | The run only needs to *reach* resources in another account's VPC. |

Choose RAM sharing when the requirement is that the workflow's network interfaces belong to the shared VPC (for example, a centralized-egress model where the requester account has no VPC of its own to egress through). Choose peering when the requester keeps its own VPC and only needs a route to resources in a peer VPC.

## RAM-Shared VPC

### How ownership splits across the two accounts

The split is NOT uniform — do not assume every resource lives in the owner account:

- **Subnets** — ALWAYS owned by the VPC owner account and RAM-shared to the requester. `vpcOwnerAccountId` names this account, and HealthOmics resolves the shared subnet ARNs against it.
- **Security groups** — May be owned by EITHER the requester OR the VPC owner. Both are valid: a shared VPC can use a security group the requester created in that VPC, or one the owner created and shared.
- **ENIs** — ALWAYS created in the **requester account**, regardless of which account owns the security group. HealthOmics never creates ENIs in the owner account.
- **Service-linked role** — Both the requester account and the VPC owner account must have the `AWSServiceRoleForHealthOmics` service-linked role.

### Prerequisites

1. The VPC owner account and the requester account MUST be in the same AWS Organization.
2. Both the VPC owner account and the requester account must have the `AWSServiceRoleForHealthOmics` service-linked role. HealthOmics auto-creates the SLR in the requester account on first configuration creation, but the VPC owner account must create its own SLR manually (HealthOmics cannot create it cross-account).
3. The requester account meets the standard configuration prerequisites (IAM permissions to create configurations, ENI capacity, and — on its first configuration — `iam:CreateServiceLinkedRole`). See the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).
4. The owner's subnets are in Availability Zones where HealthOmics operates in the Region (see the Supported Regions and AZs table in the [VPC Setup SOP](./vpc-setup.md)), and the VPC is configured for the run's connectivity needs (e.g., NAT Gateway for internet access).

### Procedure

#### VPC Owner End

1. Follow the [VPC Setup SOP](./vpc-setup.md) to set up the VPC, subnets, security groups, and any required connectivity (e.g., NAT Gateway for internet access) in the VPC owner account.
2. Create an AWS Organization (if one does not already exist) and send an invitation to the requester account(s) that will share the VPC resources.
3. Enable resource sharing for the Organization (once per Organization, from the management account). If not enabled, shared resources will need to be manually accepted by each requester account in the RAM console. Via CLI:
   ```
   aws ram enable-sharing-with-aws-organization
   ```
4. Create a RAM resource share for the target **subnets**, shared with the requester — either the specific account principal or the whole Organization.
5. If a security group owned by the VPC owner will be used, create (or extend) a RAM resource share for that **security group** too. Skip this if the requester will supply its own security group in the shared VPC.

#### Requester End

1. Accept the AWS Organization invitation (if not already a member).
2. If the VPC owner enabled sharing with AWS Organizations (VPC Owner End step 3), the shared resources are automatically available — no acceptance is needed. If sharing is not enabled at the Organization level, accept the RAM resource share invitation manually in the RAM console.
3. Verify the shared subnets (and security groups, if shared) are visible in the requester account.
4. Follow the [HealthOmics Configuration Management SOP](./healthomics-configuration.md), and additionally set `vpcConfig.vpcOwnerAccountId` to the VPC owner's 12-digit account ID.
5. Provide the shared `subnetIds` and the `securityGroupIds` (requester-owned or owner-owned).
6. Poll `GetAHOConfiguration` until status is `ACTIVE`.
7. Start the run with `networking_mode = VPC` and the configuration name, as in the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md). The ENIs are created in the requester account and attached to the owner's shared subnets.

### ENI cleanup is the requester's responsibility

Because the ENIs live in the **requester account** but are attached to the **owner's** shared VPC, the VPC owner cannot manage or detach them and **cannot delete the VPC while they remain attached.** You MUST call this out to the user when helping with a RAM-shared configuration.

The VPC owner depends on the requester to clean up. To remove lingering ENIs, the owner can:
- Remove the RAM share, and/or
- Contact the requester directly to delete the ENIs, and/or
- Cut a ticket to the HealthOmics service team to clean up the ENIs.

Do NOT advise the VPC owner to delete these ENIs themselves — they cannot.

### Example: RAM-shared VPC configuration request

```json
{
  "name": "aho-shared-vpc-example",
  "description": "Configuration using a subnet RAM-shared from a central network account",
  "runConfigurations": {
    "vpcConfig": {
      "vpcOwnerAccountId": "111122223333",
      "securityGroupIds": ["sg-0123456789abcdef0"],
      "subnetIds": ["subnet-0a1b2c3d4e5f6g7h8"]
    }
  }
}
```

Here `111122223333` is the VPC owner account that shared `subnet-0a1b2c3d4e5f6g7h8`; the security group may belong to either that account or the requester. The configuration, the run, the ENIs, and the service-linked role all belong to the requester account that makes this call.

## VPC Peering (Alternative)

VPC peering is a cross-account workaround that requires **no HealthOmics-specific setup** and does NOT use `vpcOwnerAccountId`. The run uses a VPC in its own (requester) account; a peering connection provides a route to another account's VPC.

Use it only when the requester needs to *reach* resources in a peer VPC, not when the run's ENIs must live in a shared VPC. It does not satisfy a centralized-egress requirement, because the run still egresses through the requester's own VPC.

Setup shape (customer-managed, both accounts):
1. Create a VPC peering connection between the requester VPC and the peer VPC, and accept it.
2. Add routes in both accounts' route tables for the other VPC's CIDR via the peering connection.
3. Update security groups: the peer account allows inbound from the requester VPC CIDR (or SG); the requester allows the corresponding outbound.
4. Create the HealthOmics configuration and start the run normally, using the requester's own subnets. Leave `vpcOwnerAccountId` empty — it is not used for VPC peering.

## Limitations and Considerations

- **`vpcOwnerAccountId` marks RAM sharing only** — Set it exclusively for a cross-account RAM-shared VPC. Omit it for same-account VPCs and for peering.
- **Same AWS Organization required for RAM** — RAM sharing requires the owner and requester accounts to be in the same AWS Organization with resource sharing enabled.
- **ENIs always in the requester account** — Regardless of security group ownership. The VPC owner cannot delete the shared VPC while these ENIs are attached and depends on the requester (or the HealthOmics team) to remove them.
- **Peering does not place ENIs in the peer VPC** — It only provides reachability; it does not satisfy a requirement that the run operate inside a shared VPC.
- **VPC peering connections limit** — Each VPC supports a default of 50 active peering connections (increasable to 125). Each account pair requires its own peering connection, route table entries, and security group rules. RAM sharing avoids this per-pair overhead — a single RAM share can serve multiple accounts in the Organization.

## Related Documentation
- For building VPC infrastructure (subnets, NAT Gateway, security groups, endpoints), see the [VPC Setup SOP](./vpc-setup.md).
- For creating and managing configurations and the `vpcOwnerAccountId` parameter, see the [HealthOmics Configuration Management SOP](./healthomics-configuration.md).
- For starting a run with VPC networking, see the [VPC Connected Workflow Runs SOP](./vpc-connected-workflow-runs.md).
- For diagnosing VPC-connected run failures, see the [Troubleshooting SOP](./troubleshooting.md).
