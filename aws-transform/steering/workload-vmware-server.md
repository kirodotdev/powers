# Server Migration

> **Last Updated:** 2026-05-10

## Capabilities

Rehost VMware servers to Amazon EC2 using AWS Application Migration Service (MGN). AWS Transform orchestrates the full wave-based migration lifecycle — wave setup, inventory validation, replication agent deployment, data replication monitoring, test instance launch, and production cutover. This workload covers VMware-sourced servers only; for VMware infrastructure (vSphere networking, vSAN storage, vCenter) see `workload-vmware.md`.

- VMware servers → Amazon EC2 instances (rehost/lift-and-shift via MGN)
- Continuous block-level data replication via AWS Replication Agent
- Automated replication agent installation via MGN connector (SSH/WinRM) — reusable across waves and target accounts
- Multi-wave migration with per-wave configuration
- Single-account and multi-account migration support
- Test instance launch and validation before production cutover
- Selective or full-wave cutover with finalization

## Starting Workflow

1. **Confirm prerequisites** — target AWS accounts ready, VPCs/subnets/security groups deployed and tagged, inventory file prepared with wave assignments
2. **Configure execution defaults** — EC2 recommendation preferences and default launch settings (apply to all target accounts)
3. **Set up migration wave** — configure target account, migration mode (single vs multi-account), IP assignment strategy, verify resource tags. If the target account and migration mode were already provided earlier in the conversation, use that data without asking again.
4. **Validate inventory** — review and confirm server-to-EC2 mapping, licensing options, and network configuration before loading into MGN
5. **Deploy replication agents** — choose installation method (organization tools, MGN connector, or manual), deploy to all servers in the wave
6. **Monitor replication** — track initial sync and continuous replication until all servers reach Ready for testing. Individual servers that reach Ready for testing can be progressed to test or cutover independently, without waiting for the rest of the wave.
7. **Test** — obtain approval before launching test instances, then launch, validate, mark applications ready for cutover. Can be done per-server or for the full wave.
8. **Cutover** — obtain approval before launching cutover instances, then launch, verify, finalize (stops replication), optionally archive source servers. Can be done per-server or for the full wave — a server that has completed testing can be cut over even while other servers in the wave are still replicating.

---

## Agent Monitoring Behavior

Throughout the entire migration flow, the agent MUST proactively pull status and report progress to the user after every significant action. Do not wait for the user to ask.

**Rules:**

- **After triggering any operation** (wave setup, inventory import, agent deployment, replication start, test launch, cutover launch) — immediately begin polling and report status updates as they arrive
- **After each poll** — present a concise status summary: what completed, what is in progress, what is blocked, and what the next step is
- **During long-running phases** (initial sync, agent deployment across many servers) — poll on a regular cadence and proactively surface progress (e.g., "12 of 20 servers have completed initial sync")
- **When a server changes state** — surface it immediately without waiting for the user to ask (e.g., "Server web-01 has reached Ready for testing — do you want to proceed with testing now?")
- **When a HITL task appears** — surface it immediately, do not wait for the user to notice
- **When an error or failure occurs** — surface it immediately with the failure reason and suggested resolution

**Per-step monitoring expectations:**

| Step | What to Poll | What to Report |
|------|-------------|----------------|
| Wave setup | Connector status, MGN initialization | Connector ACTIVE, MGN initialized per account |
| Inventory import | Import job status | Import complete, source server records created in MGN |
| Agent deployment | Per-server deployment status | Servers connected, INITIATING/INITIAL_SYNC state confirmed |
| Data replication | Per-server replication state and lag | Progress count, servers reaching Ready for testing |
| Test launch | Per-server test instance status | Instance IDs, test instance running |
| Cutover launch | Per-server cutover instance status | Instance IDs, cutover instance running |
| Finalization | Per-server lifecycle state | Replication stopped, lifecycle locked |

---

## Prerequisites

Before starting rehost migration, the following must be in place:

- **Target accounts** — AWS account IDs where servers will be migrated. Use AWS Transform landing zone or other tools to set up infrastructure.
- **Network infrastructure** — VPCs, subnets, and security groups deployed and configured. Use AWS Transform network migration or other tools.
- **Inventory file** — Prepared with server details, wave assignments, target account information, and EC2 instance type preferences. Use AWS Transform migration planning to generate this file.

> VPCs and subnets created by the AWS Transform network migration agent are automatically tagged. If you set up your own VPCs and subnets, you must manually apply these tags to the **replication staging area VPC and subnet** — this is the minimum required for migration to proceed:
>
> - `CreatedFor: AWSTransform`
> - `ATWorkspace: <workspace_id>`

### Migration Execution Defaults

Before starting wave execution, configure default settings that apply to all target accounts. These define how EC2 instances are launched and how the general migration is configured. Defaults can be overridden at the wave level during wave setup.

**EC2 recommendation preferences** — AWS Transform provides EC2 instance type recommendations based on source VM utilization. Recommendations can also incorporate input from Migration Evaluator, AWS OLA, or an AWS Transform assessment job.

**Default launch settings** — Configured via the Application Migration Service console.

---

## Workflow

### Step 1: Set Up Migration Wave

AWS Transform prepares the migration wave by:

- Configuring the target account
- Verifying service permissions
- Setting up resource tags
- Adding networking data to inventory
- Configuring replication and launch settings

**Migration modes:**

| Mode | Description |
|------|-------------|
| Single-account | All servers in the wave migrate to the same target account configured in the connector |
| Multi-account | Servers migrate to different target accounts specified in the inventory file — requires `mgn:account-id` column |

AWS Transform confirms the target account and verifies that Application Migration Service is initialized in each target account. This check runs for every wave. If not yet initialized, AWS Transform provides initialization instructions. During initialization, MGN creates required IAM service roles for replication and launch operations, including cross-account roles for multi-account migrations.

**Resource tagging verification** — AWS Transform verifies all required resources are properly tagged:

- **Source servers:** `CreatedBy: AWSTransform` and `ATWorkspace: <workspace_id>` — required only if the user started replication on source servers prior to working with AWS Transform and wants to bring those servers into the current migration. Not required for new servers.
- **VPCs and subnets:** `CreatedFor: AWSTransform` and `ATWorkspace: <workspace_id>` — the replication staging area VPC and subnet are mandatory and must be tagged. For the remaining network resources (target subnets, security groups), the user has two options:
  - **Auto-tag** — use the tagging link provided by AWS Transform to tag all resources automatically
  - **Provide in inventory** — specify the target subnet and security group per server directly in the inventory file during the Validate and Confirm Inventory step (Step 2)

**Add networking data to inventory** — AWS Transform maps servers to target subnets and security groups based on the network configuration from the migrate network phase.

**IP assignment strategy:**

| Strategy | Description |
|----------|-------------|
| Static IP | Source server IP is maintained; CIDR transformation applied automatically if needed |
| Dynamic IP (DHCP) | Each server is assigned a new IP from the subnet's pool |

> IP assignment options depend on the security group mapping strategy chosen during network migration:
>
> - **MAP** — static IP only. MAP translates source firewall rules to IP-based SG rules, so IPs must remain stable.
> - **MAP_DHCP** — static IP or DHCP. MAP_DHCP generates broader SG rules that accommodate IP changes.
> - **SKIP** — static IP or DHCP. SGs are configured manually post-migration, so no IP constraint applies.

---

### Step 2: Validate and Confirm Inventory

AWS Transform prepares the inventory file for review before loading into MGN. Available in CSV or XLSX format.

**Required inventory fields:**

| Field | Description |
|-------|-------------|
| Server information | Server name, VMID, source specifications |
| Wave assignment | Migration wave grouping |
| Application grouping | Logical application associations |
| Target configuration | Target account, Region, EC2 instance type |
| Network configuration | Target subnet and security groups |

The inventory file can be modified to adjust EC2 configurations, change OS licensing options (`BYOL` or `License Included` via `mgn:launch:placement:operating-system-licensing`), and update tenancy settings (`mgn:launch:placement:tenancy`).

After review, accept as-is or upload a modified version. AWS Transform then loads the data into MGN, which creates source server records for each server in the wave.

> Do not remove columns or change column headers — AWS Transform requires the original file structure.
> AWS Transform allows one import to a given target AWS account and Region at a time. If working on more than one wave simultaneously, wait for an import to finish before starting another in a different wave or job.

---

### Step 3: Deploy Replication Agents

Install the AWS Replication Agent on each source server. Three installation methods:

| Method | Description |
|--------|-------------|
| Organization tools | Use existing deployment tools (SCCM, Ansible, Chef) with silent install flags: `--no-prompt`, `--aws-access-key-id`, `--aws-secret-access-key`, `--aws-session-token` |
| MGN connector | Automates agent installation over SSH (Linux) or WinRM (Windows). Reusable across waves and target accounts |
| Manual installation | Direct installation on each server — full control, requires direct access |

#### MGN Connector Setup

The AWS Transform MGN connector is a lightweight client deployed on a dedicated Linux machine in the on-premises environment. It connects to source servers over SSH/WinRM to install replication agents.

**Connector machine requirements:**

| Requirement | Details |
|-------------|---------|
| OS | Supported Linux OS (see MGN connector prerequisites) |
| Network access | Must reach all source servers (SSH for Linux, WinRM for Windows) |
| Internet connectivity | Outbound HTTPS (443) to AWS endpoints (SSM, Secrets Manager, MGN) |
| Disk space | Minimum 200 MB free |
| Permissions | Root or sudo access |

> The connector must be installed on a Linux machine, but can deploy agents to both Linux and Windows source servers.

**Setup process:**

1. **Connector configuration** — Provide a name (or use auto-generated). Can be installed on management account or delegated administrator account.
2. **AWS resource setup** — AWS Transform opens a setup page in the browser using your AWS credentials. Automatically creates:
   - `AWSApplicationMigrationConnectorManagementRole`
   - `AWSApplicationMigrationConnectorSharingRole_<ACCOUNT-ID>`
   - SSM Hybrid Activation (30-day expiration)

   > Keep the setup page open until installation is complete. Closing it requires restarting the process. All credentials exist only in the browser and are not stored by AWS Transform.

3. **Connector installation** — Copy the installation link, SSH into the Linux machine, paste and execute. Typically takes 2–3 minutes.
4. **Attach source servers** — AWS Transform automatically attaches all source servers in the current wave to the connector.
5. **Configure credentials** — Provide AWS Secrets Manager ARNs for source server credentials:

| Option | Description |
|--------|-------------|
| Single secret for Linux | One shared secret (SSH keys or username/password) for all Linux servers |
| Single secret for Windows | One shared secret (username/password) for all Windows servers |
| Multiple per-server secrets | Different secrets per server or group — AWS Transform generates a pre-populated CSV to fill in `secret_arn` per server |

> Linux and Windows single-secret options can be combined. Per-server secrets option is mutually exclusive with single-secret options.

**Credential secret format:**

```json
{
  "WinConnectionProtocol": "HTTPS",
  "WinUserName": "windows_username",
  "WinPassword": "windows_password",
  "LinuxUserName": "linux_username",
  "LinuxPrivateKey": "linux_private_key",
  "LinuxHostKeyValidation": false
}
```

**Agent deployment process per server:**

1. AWS Transform sends deployment commands to the connector via SSM
2. Connector retrieves credentials from Secrets Manager
3. Connector connects to source server
4. Connector validates prerequisites
5. Connector installs and configures the replication agent
6. Connector verifies successful installation and connectivity

Deployment progress is tracked in real-time with per-server status, current step, elapsed time, and estimated time remaining. Failed servers can be retried individually while successful servers proceed independently.

**Connector reuse:**

| State | Behavior |
|-------|----------|
| Active | Hybrid Activation still valid — AWS Transform verifies IAM roles and proceeds to credential configuration |
| Expired | Activation cannot be renewed — must select a different connector or create a new one |

> SSM Hybrid Activations expire after 30 days. Once the connector is installed, it can continue deploying agents even after activation expires. A new connector is only needed if installing on a new machine.

#### Manual Agent Installation

**Credential options:**

- **Temporary credentials (recommended)** — Create IAM role with `AWSApplicationMigrationAgentInstallationPolicy`, use `aws sts assume-role`
- **Permanent credentials** — Create IAM user with `AWSApplicationMigrationAgentInstallationPolicy` and generate access key

**Linux installation:**

```bash
wget -O ./aws-replication-installer-init \
  https://aws-application-migration-service-{region}.s3.{region}.amazonaws.com/latest/linux/aws-replication-installer-init
sudo chmod +x aws-replication-installer-init
sudo ./aws-replication-installer-init --region {region} --user-provided-id {server-identifier}
```

**Windows installation (PowerShell as Administrator):**

```powershell
Invoke-WebRequest -Uri "https://aws-application-migration-service-{region}.s3.{region}.amazonaws.com/latest/windows/AwsReplicationWindowsInstaller.exe" `
  -OutFile "C:\AwsReplicationWindowsInstaller.exe"
C:\AwsReplicationWindowsInstaller.exe --region {region} --user-provided-id {server-identifier}
```

> `--user-provided-id` is required. Use the exact value from the `mgn:server:user-provided-id` column in the inventory file. This links the physical server to its MGN source server record.

After installation, AWS Transform verifies all agents are connected by checking that servers show replication state `INITIATING` or `INITIAL_SYNC`.

> AWS Transform does not support MGN agentless replication.
> All servers in a wave must have the replication agent installed. Servers without an agent can be removed from the wave, or disconnected (`disconnect-from-service`) and archived (`mark-as-archived`). The archive command only works for servers in `DISCONNECTED` lifecycle state.

---

### Step 4: Data Replication

After replication agents are installed, data replication begins automatically using continuous block-level replication.

**Replication phases:**

| Phase | Description |
|-------|-------------|
| Initial sync | Complete copy of source server data to AWS, stored as EBS snapshots in the target account. Duration depends on data volume and network bandwidth |
| Continuous replication | Ongoing synchronization of changed blocks with minimal impact on source server performance |

Replication servers are temporary EC2 instances in the staging area subnet, automatically managed by MGN.

**AWS Transform monitors and provides:**

- Replication status per server
- Replication lag (time difference between source and replicated data)
- Bandwidth usage

**Server replication states:**

| State | Meaning |
|-------|---------|
| Not ready | Undergoing initial sync — not yet ready for testing |
| Ready for testing | Data replication started — test or cutover instances can be launched |

Once all servers in the wave have progressed beyond `NOT_READY`, the data replication phase is complete.

**Replication controls:**

- **Pause** — Temporarily pause replication for specific servers or the entire wave
- **Resume** — Resume previously paused replication
- **Stop** — Permanently stop replication (can be restarted, but begins from initial sync)

---

### Step 5: Testing

After servers reach the Ready for testing state, obtain approval before launching test instances. Once approved, launch test instances to validate migrated servers before final cutover.

**Testing options:**

| Option | Description |
|--------|-------------|
| Full wave testing | Launch test instances for all servers in the wave |
| Selective testing | Launch test instances for specific servers by user-provided IDs from the inventory file |

> Servers do not need to be at the same replication stage. A server that has reached Ready for testing can be tested immediately while others in the wave are still in initial sync.

AWS Transform launches EC2 instances from replicated data and provides instance IDs for connection and validation.

**After testing:**

- Proceed to cutover if testing is successful
- Launch new test instances to retest
- Terminate test instances and address issues before retesting

#### Step 5b: Mark Applications as Ready for Cutover

After testing is complete, mark applications as ready for cutover. AWS Transform reviews replication status of each application and resolves any replication alerts before allowing progression. Only applications with a clean replication status can be marked for cutover.

---

### Step 6: Cutover

Final migration step where production workloads move to AWS. Approval is required before launching cutover instances.

**Cutover options:**

| Option | Description |
|--------|-------------|
| Full wave cutover | Cutover all servers in the wave |
| Selective cutover | Cutover specific servers by user-provided IDs |

> Per-server cutover is independent of wave progress. A server that has completed testing can be cut over while other servers in the same wave are still replicating or in test.

**Cutover process:**

1. **Launch cutover instances** — AWS Transform launches EC2 instances from the latest replicated data and provides instance IDs
2. **Verify cutover instances** — Connect to launched instances and verify they are functioning correctly
3. **Finalize cutover** — Confirm cutover to stop source machine replication. Can finalize all servers or select specific ones. Finalization:
   - Stops replication agents from sending data
   - Removes replication agents from source servers
   - Locks the server lifecycle state

   > This action cannot be easily undone. Verify cutover instances before finalizing.

4. **Archive source servers (optional)** — Mark source servers as archived after finalization to free up source server quota

> Downtime occurs between source shutdown and cutover instance availability. Plan the cutover window accordingly.

---

## Server Lifecycle States

| State | Description |
|-------|-------------|
| Not ready | Undergoing initial sync — not ready for testing |
| Ready for testing | Data replication started — test or cutover instances can be launched |
| Test in progress | A test instance is currently being launched |
| Ready for cutover | Server has been tested and is ready for cutover |
| Cutover in progress | A cutover instance is currently being launched |
| Cutover complete | Server has been cutover — all data migrated to AWS cutover instance |
| Disconnected | Server has been disconnected from MGN |

---

## Status Queries

At any point during the migration, the user can request a status summary of their wave. When asked, the agent SHALL immediately fetch the latest state and present a summary table showing each server's migration lifecycle state, replication status, and recommended next step.

**Example natural language queries:**

- "What is the status of my servers?"
- "What's the status of my wave?"
- "What's the status of the step that I'm currently in?"
- "Give me a summary of the wave"

During wave migration, users can instruct AWS Transform to advance a specific server to the next stage independently of the rest of the wave. For example, if a single server has reached Ready for testing while others are still in initial sync, the user can instruct the agent to launch a test instance for that server immediately, then proceed to cutover once validated — all while the remaining servers continue replicating. The agent handles per-server progression without requiring the full wave to be at the same stage.

---

## Connector Setup

Before deploying replication agents via the MGN connector method, the connector must be created and activated via the MCP API.

**Important:** `create_connector` accepts invalid KMS key ARNs without validation — it fails silently at agent deployment time. Always resolve a real KMS key ARN before creating the connector:

```bash
aws kms describe-key --key-id alias/aws/s3 --region us-east-1 --query 'KeyMetadata.Arn' --output text
```

```python
create_connector(
  workspaceId="<workspace-id>",
  connectorName="server-migration-connector",
  connectorType="vmware_migration|server_migration|2",
  configuration={"encryptionKeyArn": "<real-kms-key-arn>"},
  awsAccountId="<account-id>",
  targetRegions=["<target-region>"]
)
# → Present verification link to user for approval via AWS Console
# → Connector approval is human-gated — do NOT auto-poll
# → When user confirms approval, verify status once via get_resource(resource="connector")
```

Always use the verification link to approve — this creates a fresh IAM role with the correct KMS and MGN permissions. Reusing a role from a deleted connector may have KMS permissions on the wrong key — always use the verification link for a fresh role.

> `encryptionKeyArn` is required by MCP validation even though the webapp does not require it. Always resolve and pass a real ARN.

**Connector reuse across waves:** An active connector can be reused for multiple waves and target accounts. Check connector status before each wave:

| State | Action |
|-------|--------|
| ACTIVE | Reuse — verify IAM roles and proceed to credential configuration |
| PENDING | Present verification link again — user has not yet approved |
| EXPIRED | SSM Hybrid Activation expired — create a new connector on a new machine |

> SSM Hybrid Activations expire after 30 days. Once installed, the connector continues deploying agents even after activation expires. A new connector is only needed when installing on a new machine.

---

## Multi-Account Considerations

| Aspect | What the Power Needs to Know |
|--------|------------------------------|
| **Migration mode selection** | Decision point at Step 1: Single-account or Multi-account. Present via AskUserQuestion. |
| **Inventory file** | Multi-account requires `mgn:account-id` column in the inventory file — one row per server with its target account ID |
| **Cross-account IAM roles** | MGN creates cross-account roles during initialization. Verify MGN is initialized in each target account before starting the wave. |
| **AWS Organizations** | Required for multi-account migrations. Each target account must be part of the same AWS Organization as the source account. |
| **MGN initialization per account** | If MGN is not yet initialized in a target account, AWS Transform provides initialization instructions. MGN creates `AWSServiceRoleForApplicationMigrationService` in each account. |
| **Connector scope** | A single connector can deploy agents to servers targeting different accounts — account routing is handled via the inventory file, not the connector. |
| **Parallel wave imports** | Only one inventory import to a given target account and Region is allowed at a time. Sequence imports across accounts if running multiple waves simultaneously. |

---

## Deployment Approvals

Some migration operations require explicit approval before execution. AWS Transform routes these requests to authorized approvers through the Approvals tab.

1. **Submission** — Power confirms the operation (e.g., cutover launch), agent submits the request for review
2. **Routing** — Request routes automatically to authorized approvers via the AWS Transform Approvals tab
3. **Review** — Approvers validate the operation against migration plan and security standards
4. **Decision** — Approver approves or denies:
   - **Approved** → operation proceeds automatically
   - **Denied** → inform user, suggest contacting approver for required modifications
5. **Audit** — All approval decisions are tracked for audit purposes

Only users with the **Admin** or **Approver** role in AWS Transform can approve deployment requests. Deployments proceed only after receiving confirmation.

**Power behavior during approval:**

- After submission, inform user that the operation requires approval
- Deployment approval is human-gated — do NOT auto-poll. Present the pending status and wait for the user to confirm approval has been granted, then verify once.
- If denied, present the denial to the user and offer to address the blocker and resubmit

---

## Agents & Transforms

| Agent | How to Discover | Purpose |
|-------|----------------|---------|
| Server Migration Agent | `list_resources` with `resource: "agents"` | Wave setup, inventory validation, agent deployment, replication monitoring, testing, cutover |
| AWS Application Migration Service (MGN) | External | Actual server replication, testing, and cutover execution |
| AWS Migration Hub | External | Migration tracking and orchestration |

**Discover the agent dynamically:**

```python
list_resources(resource="agents")
# Or ask the chat agent
send_message(workspaceId="...", text="What agents are available for server migration?")
# Then create job with discovered orchestratorAgent
create_job(workspaceId="...", jobName="Server Migration",
  objective="Migrate VMware servers to EC2 using MGN", orchestratorAgent="<discovered>")
```

---

## Decision Points

| Decision | Options | When to Ask |
|----------|---------|-------------|
| Migration mode | Single-account / Multi-account | Step 1 — wave setup. Skip if already known from earlier in the conversation. |
| IP assignment strategy | Static IP / Dynamic IP (DHCP) | Step 1 — wave setup |
| Agent installation method | Organization tools / MGN connector / Manual | Step 3 — before agent deployment |
| Credential configuration | Single secret (Linux) / Single secret (Windows) / Per-server secrets | Step 3 — connector setup |
| Testing scope | Full wave / Selective | Step 5 — before launching test instances |
| Cutover scope | Full wave / Selective | Step 6 — before launching cutover instances |

---

## Example Requirements

```
## Requirement 1: Wave Setup and Inventory Validation
**User Story:** As an infrastructure engineer, I want each migration wave configured and validated
so that servers are correctly mapped to target accounts, subnets, and EC2 instance types.
**Acceptance Criteria:**
1. WHEN wave setup completes, EACH server SHALL have a target account, subnet, security group, and EC2 instance type assigned
2. WHEN inventory is validated, required resource tags SHALL be verified (CreatedBy: AWSTransform, ATWorkspace: <id>)
3. WHEN inventory is loaded, MGN SHALL create source server records for each server in the wave
**Handled by:** AWS Transform Server Migration Agent

## Requirement 2: Replication Agent Deployment
**User Story:** As an operations engineer, I want replication agents deployed to all source servers
so that continuous block-level replication to AWS begins automatically.
**Acceptance Criteria:**
1. WHEN agents are deployed, ALL servers in the wave SHALL show replication state INITIATING or INITIAL_SYNC
2. WHEN initial sync completes, ALL servers SHALL reach Ready for testing state
3. WHEN a server fails agent installation, the failure reason SHALL be displayed and retry SHALL be available
**Handled by:** AWS Transform Server Migration Agent

## Requirement 3: Testing and Cutover
**User Story:** As an operations engineer, I want to validate migrated servers before cutover
so that production workloads are moved to AWS with verified functionality.
**Acceptance Criteria:**
1. WHEN test instances are launched, instance IDs SHALL be provided for each server
2. WHEN test instances are launched, the EC2 launch template ID SHALL be taken from the default version of the specific EC2 launch template ID configured in the target account launch settings
3. WHEN all applications are marked ready for cutover, replication alerts SHALL be resolved
4. WHEN cutover is finalized, source machine replication SHALL stop and lifecycle state SHALL be locked
5. WHEN cutover completes, downtime SHALL be limited to the window between source shutdown and cutover instance availability
**Handled by:** AWS Transform Server Migration Agent
```

---

## Example Tasks

```
- [ ] 1. Prerequisites verification
  - [ ] 1.1 Confirm target AWS accounts are ready
  - [ ] 1.2 Verify VPC, subnets, and security groups are deployed and tagged
  - [ ] 1.3 Confirm inventory file is prepared with wave assignments and EC2 preferences
  - [ ] 1.4 Configure migration execution defaults (EC2 recommendation preferences, launch settings)
- [ ] 2. Wave setup (Step 1)
  - [ ] 2.1 Configure migration mode (single-account or multi-account)
  - [ ] 2.2 Verify MGN is initialized in target accounts
  - [ ] 2.3 Verify resource tagging
  - [ ] 2.4 Add networking data to inventory
  - [ ] 2.5 Configure IP assignment strategy
- [ ] 3. Inventory validation (Step 2)
  - [ ] 3.1 Download and review inventory file (CSV/XLSX)
  - [ ] 3.2 Adjust EC2 instance types, licensing options, tenancy if needed
  - [ ] 3.3 Upload modified inventory or accept as-is
  - [ ] 3.4 Confirm MGN source server records created
- [ ] 4. Deploy replication agents (Step 3)
  - [ ] 4.1 Choose installation method (organization tools / MGN connector / manual)
  - [ ] 4.2 Set up MGN connector if selected (configure, install, attach servers, configure credentials)
  - [ ] 4.3 Deploy agents to all servers in the wave
  - [ ] 4.4 Verify all agents show INITIATING or INITIAL_SYNC state
- [ ] 5. Data replication (Step 4)
  - [ ] 5.1 Monitor initial sync progress per server
  - [ ] 5.2 Confirm all servers reach Ready for testing state
- [ ] 6. Testing (Step 5)
  - [ ] 6.1 Launch test instances (full wave or selective)
  - [ ] 6.2 Validate test instances — connectivity, application health
  - [ ] 6.3 Terminate test instances after validation
  - [ ] 6.4 Mark applications as ready for cutover
- [ ] 7. Cutover (Step 6)
  - [ ] 7.1 Launch cutover instances within maintenance window
  - [ ] 7.2 Verify cutover instances are functioning correctly
  - [ ] 7.3 Finalize cutover (stops replication, locks lifecycle state)
  - [ ] 7.4 Archive source servers (optional)
```

---

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Connector status stuck on PENDING | User hasn't approved via verification link | Present verification link again — approval creates IAM role with correct MGN and KMS permissions |
| Agent installation fails on all servers | Connector can't reach source servers | Verify network access: SSH (port 22) for Linux, WinRM (port 5985/5986) for Windows |
| Agent installation fails on specific servers | Wrong credentials or per-server secret ARN incorrect | Check Secrets Manager ARN for the affected server; verify secret format matches expected JSON structure |
| Servers stuck in NOT_READY after agent install | Initial sync still in progress | Monitor replication lag — large disks or low bandwidth extend initial sync duration |
| MGN not initialized in target account | First-time use of MGN in that account | Follow AWS Transform initialization instructions — MGN creates required IAM service roles automatically |
| Inventory import fails | Duplicate import in progress for same account/Region | Wait for the active import to finish before starting another in the same target account and Region |
| Inventory import fails | Column headers modified or columns removed | Restore original file structure — AWS Transform requires unmodified column headers |
| Test instance launch fails | Server not in Ready for testing state | Verify replication state is not NOT_READY; check for replication alerts |
| Cutover finalization blocked | Replication alerts on one or more servers | Resolve replication alerts before marking applications ready for cutover |
| Source server not found in MGN after import | `mgn:server:user-provided-id` mismatch | Ensure the value passed to `--user-provided-id` during agent install exactly matches the inventory file value |
| Dynamic IP (DHCP) assignment unavailable | MAP security groups strategy used during network migration | MAP supports static IP only — to enable DHCP, redo network migration with MAP_DHCP or SKIP strategy |

---

## Known Limitations

- Agentless replication is not supported — the AWS Replication Agent must be installed on all servers in a wave
- Servers without a replication agent can be removed from the wave, or disconnected and archived to free up source server quota
- SSM Hybrid Activations for the MGN connector expire after 30 days — a new connector is required if installing on a new machine after expiration
- Only one inventory import to a given target account and Region is allowed at a time — parallel wave imports to the same account must be sequenced
- IP assignment is constrained by the security group mapping strategy: MAP supports static IP only; MAP_DHCP and SKIP support both static and DHCP
- Only the replication staging area VPC and subnet must be tagged with `CreatedFor: AWSTransform` and `ATWorkspace: <workspace_id>` if not created by AWS Transform network migration — other network resources can be tagged via the tagging link or specified per-server in the inventory file
- Deployment approvals require Admin or Approver role in AWS Transform — non-admin/non-approver users cannot approve cutover operations
- Downtime is unavoidable between source shutdown and cutover instance availability — plan maintenance windows accordingly
