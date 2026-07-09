# VMware Migration

> **Last Updated:** 2026-05-10

## Capabilities

Migrate VMware environments to AWS using generative AI-driven planning and execution. AWS Transform orchestrates the full migration lifecycle — discovery, migration planning, landing zone setup, network migration, and server rehosting to EC2. Supports Windows and Linux servers on supported operating systems (see [MGN supported OS list](https://docs.aws.amazon.com/mgn/latest/ug/Supported-Operating-Systems.html)).

- VMware VMs → Amazon EC2 instances (rehost/lift-and-shift via MGN)
- AI-driven conversion of VMware network configuration → AWS VPC architecture (VPCs, subnets, security groups, Transit Gateway)
- AI-driven migration plan generation — application grouping and wave planning
- Three discovery options: AWS Application Discovery Service collectors, Export for vCenter tool, or independently collected data import
- Landing zone setup for target AWS accounts
- Multi-wave migration with per-wave configuration
- Single-account and multi-account migration support

For detailed execution guidance see:

- `workload-vmware-server.md` — replication agent deployment, data replication, testing, cutover
- `workload-vmware-network.md` — network mapping, topology, IaC generation, deployment
- `workload-vmware-landing-zone.md` — landing zone foundation and workload account design
- `workload-vmware-containerization.md` — source code containerization, Docker artifacts, ECR publishing, EKS/ECS IaC

---

## Job Types

AWS Transform offers the following VMware migration job types. Steps can be dynamically added or removed at any time to customize the workflow.

| Job Type                                        | Steps Included                                                                                                              |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **End-to-end migration**                        | Perform discovery → Build migration plan → Connect target accounts → Build landing zone → Migrate network → Migrate servers |
| **Discovery and migration planning**            | Perform discovery → Build migration plan                                                                                    |
| **Network migration**                           | Connect target accounts → Migrate network                                                                                   |
| **Landing zone**                                | Connect target accounts → Build landing zone                                                                                |
| **Landing zone, network, and server migration** | Connect target accounts → Build landing zone → Migrate network → Migrate servers                                            |
| **Migration planning and server migration**     | Perform discovery → Build migration plan → Connect target accounts → Migrate servers                                        |
| **Source code containerization**                | Connect target accounts → Containerize applications → Publish to ECR → Deploy to EKS/ECS                                    |

> One target AWS Region per VMware migration job. To migrate to different Regions, create multiple jobs.

---

## Starting Workflow

**Before starting:** Confirm job type — determine which steps are in scope based on what the user already has (existing network, existing landing zone, etc.)

1. **Perform discovery** — identify VM count, OS types, resource usage (CPU, memory, storage), and network dependencies using one of the three discovery options
2. **Build migration plan** — AI-driven application grouping, wave planning, and right-sizing recommendations
3. **Connect target accounts** — configure target AWS accounts and verify permissions
4. **Build landing zone** — set up AWS account structure, IAM roles, and baseline infrastructure in target accounts
5. **Migrate network** — translate VMware network configuration to AWS VPC architecture; deploy via CloudFormation
6. **Migrate servers** — deploy replication agents, replicate data, test, and cut over wave by wave

   **Separate job type (not part of end-to-end migration):**

7. **Containerize applications** — AI-driven Docker artifact generation, ECR publishing, EKS/ECS IaC and deployment (standalone or with containerize strategy assigned to waves)

**Key questions to ask user:**

- "Do you already have a landing zone and network set up in the target account(s), or do we need to build those?"
- "Which discovery method do you have available — ADS collectors, Export for vCenter, or an existing data export?"
- "Are any of your workloads candidates for containerization (EKS/ECS), or is this purely lift-and-shift to EC2?"

---

## Agent Monitoring Behavior

Throughout the entire VMware migration flow, the agent MUST proactively pull status and report progress to the user after every significant action. Do not wait for the user to ask.

**Rules:**

- **After triggering any operation** (discovery, migration plan generation, landing zone deployment, network deployment, wave setup, agent deployment, replication, test launch, cutover) — immediately begin polling and report status updates as they arrive
- **After EVERY job interaction** (send_message, complete_task, upload_artifact) — always read the latest messages back from the job and surface any agent response or question to the user immediately. Do not assume silence means the agent is still processing — it may have already responded.
- **After each poll** — present a concise status summary: what completed, what is in progress, what is blocked, and what the next step is
- **During long-running phases** (discovery, initial sync, CloudFormation deployment) — poll on a regular cadence and proactively surface progress
- **When a step completes** — surface it immediately and prompt the user for the next decision
- **When a HITL task appears** — surface it immediately, do not wait for the user to notice
- **When an error or failure occurs** — surface it immediately with the failure reason and suggested resolution

**Polling priority** — check in this order every poll cycle:

1. **Messages** (agent chat responses and questions) — check first, this is the primary communication channel
2. **Tasks** (formal HITL tasks awaiting human input)
3. **Worklogs** (agent activity and progress)

**Target account operations — always delegate to the agent:**

When the user asks about resources in the target AWS account (subnets, VPCs, security groups, instances, IAM roles, etc.), do NOT attempt to query the target account directly via AWS CLI or SDK. The Power does not have cross-account permissions. Instead, forward the request to the agent via `send_message` — the agent has connector-based access to the target account and can query and report back.

Examples:

- "What subnets are available?" → `send_message(text="List available subnets in the target account")`
- "Show me the security groups" → `send_message(text="List security groups in the target account")`
- "What VPCs are tagged?" → `send_message(text="Show tagged VPCs in the target account")`

Never run `aws ec2 describe-subnets` or similar CLI commands targeting the customer's account — they will fail with permissions errors or return results from the wrong account.

**Console link presentation — guided handoff:**

When a step requires the user to complete an action in the AWS Console (IAM role setup, CloudFormation deployment, connector approval, MGN initialization):

1. **Explain what needs to happen** — don't just present a link. State what the action does, why it's needed, and what the user should see when it's complete.
2. **Provide the direct link** — full URL, not a relative path or internal reference.
3. **State what to do after** — tell the user to confirm when done (e.g., "Let me know once you've approved the connector").
4. **Verify the result** — after user confirms, check the status once (connector ACTIVE, MGN initialized, stack deployed) and report back.
5. **Never leave the user hanging** — if verification fails, explain what went wrong and what to retry.
6. **Never construct console URLs yourself** — always use links provided by the agent in its messages or HITL tasks. Console URLs are dynamically generated and scoped to specific connectors, workspaces, and accounts. Constructing generic URLs will produce incorrect links. If the agent hasn't provided a link, ask it via `send_message` rather than guessing the URL format.

**Polling types:**

- **Machine-gated steps** (mapping, job processing, replication, deployments, IaC generation) — poll automatically and silently. Only surface results to the user (completion, error, or progress update). Do NOT ask permission to poll.
- **Human-gated steps** (connector approval, deployment approval, web UI approvals) — do NOT auto-poll. Present the action needed (link, instructions) and wait for the user to confirm when done. When user confirms → verify status once. If not yet complete → remind them what's needed.

**Per-step monitoring expectations:**

| Step                    | What to Poll                                                       | What to Report                                                                            |
| ----------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| Discovery               | Job status, messages                                               | Discovery complete, VM count, dependency map summary                                      |
| Migration plan          | Job status, messages                                               | Wave groupings, right-sizing recommendations ready for review                             |
| Connect target accounts | MGN initialization status per account                              | Accounts connected, MGN initialized                                                       |
| Landing zone            | Deployment job status                                              | OUs and accounts created, approval status                                                 |
| Network migration       | Deployment job status, connector status                            | Network deployed, VPCs/subnets ready                                                      |
| Server migration        | Per-server replication state, test/cutover status                  | Progress per wave — delegate to server migration monitoring rules                         |
| Containerization        | Artifact generation status, TOOL_APPROVAL tasks, deployment status | Docker artifacts ready for review, images published, IaC generated, test/cutover deployed |

---

## Prerequisites

- **Target AWS accounts** — account IDs where servers will be migrated
- **Discovery data** — VM inventory with OS types, CPU/memory/storage, and network dependencies
- **AWS Transform workspace** — determines the AWS Region for jobs and discovery data. Target Region can differ from workspace Region.

---

## Workflow

### Step 1: Perform Discovery

Three options for collecting VMware environment data:

| Method                                       | Description                                                           |
| -------------------------------------------- | --------------------------------------------------------------------- |
| AWS Application Discovery Service collectors | Automated discovery via ADS agents deployed in the VMware environment |
| Export for vCenter tool                      | Open-source tool that exports VM inventory directly from vCenter      |
| Independent data import                      | Import previously collected discovery data (CSV or supported format)  |

Discovery produces VM inventory with resource utilization, OS details, and network dependency mapping used for migration planning.

---

### Step 2: Build Migration Plan

AWS Transform analyzes discovery data and generates:

- **Application grouping** — logical grouping of VMs by application or workload
- **Migration waves** — prioritized wave assignments based on dependencies and risk
- **Right-sizing recommendations** — EC2 instance type recommendations per VM based on utilization data

The user reviews and adjusts groupings and wave assignments before proceeding.

---

### Step 3: Connect Target Accounts

Configure the target AWS account(s) where servers will be migrated. AWS Transform verifies permissions and initializes required services (MGN, IAM roles) in each target account.

For multi-account migrations, each target account must be part of the same AWS Organization.

---

### Step 4: Build Landing Zone

Set up the baseline AWS infrastructure in target accounts — account structure, IAM roles, VPCs for management, and baseline security controls. AWS Transform guides landing zone configuration and deployment.

---

### Step 5: Migrate Network

Translate VMware network configuration to AWS VPC architecture. See `workload-vmware-network.md` for full details including:

- Topology selection (Hub and Spoke or Isolated VPCs)
- Security group strategy (MAP / MAP_DHCP / SKIP)
- Network optimization and IaC generation
- CloudFormation deployment with approval workflow

> The security group mapping strategy chosen here determines IP assignment options in server migration: MAP = static IP only; MAP_DHCP and SKIP = static or DHCP.

---

### Step 6: Migrate Servers

Rehost VMware servers to EC2 using MGN. See `workload-vmware-server.md` for full details including:

- Wave setup and inventory validation
- Replication agent deployment (organization tools, MGN connector, or manual)
- Data replication monitoring
- Test instance launch (requires approval)
- Production cutover (requires approval)
- Per-server progression — servers can advance to test and cutover independently of the rest of the wave

---

### Step 7: Containerize Applications

Containerize applications for deployment on Amazon EKS or Amazon ECS. See `workload-vmware-containerization.md` for full details including:

- AI-driven source code analysis and Docker artifact generation
- Container image building and publishing to Amazon ECR (with vulnerability scanning)
- Infrastructure as Code generation (EKS Helm charts or ECS Terraform modules)
- Test deployment and production cutover
- TOOL_APPROVAL tasks require web UI approval

---

## Multi-Account Considerations

| Aspect                             | What the Power Needs to Know                                                                                                                                                       |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Job type selection**             | Confirm whether single-account or multi-account at job creation                                                                                                                    |
| **AWS Organizations**              | Required for multi-account migrations. Each target account must be in the same Organization.                                                                                       |
| **Cross-account IAM roles**        | MGN creates cross-account roles during initialization. Verify MGN is initialized in each target account.                                                                           |
| **MGN initialization per account** | If MGN is not yet initialized in a target account, AWS Transform provides initialization instructions. MGN creates `AWSServiceRoleForApplicationMigrationService` in each account. |
| **Connector scope**                | A single connector can deploy agents to servers targeting different accounts — account routing is handled via the inventory file, not the connector.                               |
| **Target Region**                  | One Region per job. Workspace Region and target Region can differ — data transfers across Regions if they differ.                                                                  |
| **Landing zone scope**             | Landing zone setup applies to all target accounts in the job                                                                                                                       |

---

## Deployment Approvals

Some migration operations require explicit approval before execution. AWS Transform routes these requests to authorized approvers through the Approvals tab.

1. **Submission** — Power confirms the operation, agent submits for review
2. **Routing** — Request routes automatically to authorized approvers via the Approvals tab
3. **Review** — Approvers validate against migration plan and security standards
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

| Agent                                                   | How to Discover                            | Purpose                                                                                              |
| ------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| VMware Migration Agent v2 (`vmware-migration-agent-v2`) | `list_resources` with `resource: "agents"` | End-to-end orchestration: discovery, planning, network migration, server migration, containerization |
| Server Migration Agent                                  | `list_resources` with `resource: "agents"` | Wave setup, replication agent deployment, replication monitoring, testing, cutover                   |
| Landing Zone Agent                                      | `list_resources` with `resource: "agents"` | Foundation setup, workload account design, SCP configuration, IaC generation                         |
| Network Migration Agent (NMA)                           | _(sub-agent, invoked by orchestrator)_     | Network mapping, optimization, and IaC generation                                                    |
| Containerization sub-agent                              | _(sub-agent, invoked by orchestrator)_     | Source code analysis, Docker artifact generation, image building, IaC generation                     |
| AWS Application Migration Service (MGN)                 | External                                   | Actual server replication, testing, and cutover execution                                            |
| AWS Migration Hub                                       | External                                   | Migration tracking and orchestration                                                                 |

**Discover agents dynamically:**

```python
list_resources(resource="agents")
# Or ask the chat agent
send_message(workspaceId="...", text="What agents are available for VMware migration?")
# Then create job with discovered orchestratorAgent
create_job(workspaceId="...", jobName="VMware Migration",
  objective="Migrate VMware workloads to EC2", orchestratorAgent="vmware-migration-agent-v2")
```

---

## Decision Points

| Decision                  | Options                                                                  | When to Ask                                                             |
| ------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Job type                  | End-to-end / Discovery and planning / Network only / Landing zone / etc. | Before starting — based on what the user already has                    |
| Discovery method          | ADS collectors / Export for vCenter / Independent import                 | Step 1 — before discovery                                               |
| Migration mode            | Single-account / Multi-account                                           | Step 3 — connecting target accounts                                     |
| Network topology          | Hub and Spoke / Isolated VPCs                                            | Step 5 — network migration                                              |
| Security group strategy   | MAP / MAP_DHCP / SKIP                                                    | Step 5 — network migration. Determines IP assignment options in Step 6. |
| IP assignment strategy    | Static IP / Dynamic IP (DHCP)                                            | Step 6 — wave setup. Constrained by SG strategy.                        |
| Agent installation method | Organization tools / MGN connector / Manual                              | Step 6 — before replication agent deployment                            |
| Testing scope             | Full wave / Selective                                                    | Step 6 — before launching test instances                                |
| Cutover scope             | Full wave / Selective                                                    | Step 6 — before launching cutover instances                             |
| Source code method        | Git repository (CodeConnections) / Zip upload                            | Step 7 — containerization                                               |
| Deployment target         | Amazon EKS (Helm charts) / Amazon ECS (Terraform modules)                | Step 7 — before IaC generation. MUST ask explicitly, never infer.       |

---

## Example Requirements

```
## Requirement 1: VM Discovery and Migration Planning

**User Story:** As an infrastructure engineer, I want all VMware VMs assessed and grouped into waves
so that I have a clear, prioritized migration plan with right-sized EC2 targets.
**Acceptance Criteria:**

1. WHEN discovery completes, EACH VM SHALL have a recommended EC2 instance type
2. WHEN discovery completes, network dependencies between VMs SHALL be documented
3. WHEN migration plan is built, VMs SHALL be grouped into migration waves with dependency ordering
   **Handled by:** AWS Transform VMware Migration Agent v2

## Requirement 2: Network Migration

**User Story:** As a network engineer, I want VMware network configuration translated to AWS VPC
so that VM communication patterns are preserved after migration.
**Acceptance Criteria:**

1. WHEN network mapping completes, EACH source network segment SHALL map to a distinct AWS VPC
2. WHEN network mapping completes, source firewall rules SHALL be translated to AWS Security Groups
3. WHEN deployment completes, ALL VPCs, subnets, and security groups SHALL exist in the target account
   **Handled by:** AWS Transform VMware Migration Agent v2 (NMA sub-agent)

## Requirement 3: Server Migration

**User Story:** As an operations engineer, I want VMware servers rehosted to EC2
so that production workloads run natively on AWS with verified functionality.
**Acceptance Criteria:**

1. WHEN replication agents are deployed, ALL servers SHALL show replication state INITIATING or INITIAL_SYNC
2. WHEN test instances are launched (after approval), instance IDs SHALL be provided for each server
3. WHEN cutover is finalized (after approval), source machine replication SHALL stop and lifecycle state SHALL be locked
   **Handled by:** AWS Transform Server Migration Agent

## Requirement 4: Landing Zone

**User Story:** As a cloud platform engineer, I want the core landing zone foundation deployed
so that governance controls, centralized logging, and account isolation are in place before workloads arrive.
**Acceptance Criteria:**

1. WHEN foundation setup completes, Control Tower SHALL be initialized with Security OU, Log Archive account, and Audit account
2. WHEN workload structure is proposed, ALL servers in a migration wave SHALL map to the same target account
3. WHEN SCPs are applied, member accounts SHALL be unable to exceed the boundaries defined by the SCPs
   **Handled by:** AWS Transform Landing Zone Agent

## Requirement 5: Containerization

**User Story:** As a platform engineer, I want selected applications containerized
so that they can run on Amazon EKS or Amazon ECS instead of bare EC2 instances.
**Acceptance Criteria:**

1. WHEN containerization completes, a Dockerfile SHALL be generated for each application component
2. WHEN images are published, vulnerability scanning SHALL report no critical findings
3. WHEN IaC generation completes, deployment templates SHALL be available in the selected format (Helm charts or Terraform)
   **Handled by:** AWS Transform VMware Migration Agent (Containerization sub-agent)
```

---

## Example Tasks

```
- [ ] 1. Job setup
  - [ ] 1.1 Confirm job type (end-to-end or subset of steps)
  - [ ] 1.2 Confirm single-account or multi-account migration
  - [ ] 1.3 Create and start VMware migration job
- [ ] 2. Discovery (Step 1)
  - [ ] 2.1 Choose discovery method (ADS / Export for vCenter / independent import)
  - [ ] 2.2 Run discovery and collect VM inventory
  - [ ] 2.3 Review discovery results
- [ ] 3. Migration planning (Step 2)
  - [ ] 3.1 Review AI-generated application groupings
  - [ ] 3.2 Review and adjust wave assignments
  - [ ] 3.3 Review right-sizing recommendations
  - [ ] 3.4 Approve migration plan
- [ ] 4. Connect target accounts (Step 3)
  - [ ] 4.1 Provide target AWS account IDs
  - [ ] 4.2 Verify MGN initialized in each target account
  - [ ] 4.3 Verify cross-account IAM roles
- [ ] 5. Build landing zone (Step 4)
  - [ ] 5.1 Configure landing zone settings
  - [ ] 5.2 Deploy landing zone (approval required)
  - [ ] 5.3 Verify baseline infrastructure in target accounts
- [ ] 6. Network migration (Step 5) — see workload-vmware-network.md
  - [ ] 6.1 Upload source network file
  - [ ] 6.2 Select topology and security group strategy
  - [ ] 6.3 Review and optimize network design
  - [ ] 6.4 Deploy network (approval required)
- [ ] 7. Server migration (Step 6) — see workload-vmware-server.md
  - [ ] 7.1 Set up migration wave per wave
  - [ ] 7.2 Validate and confirm inventory
  - [ ] 7.3 Deploy replication agents
  - [ ] 7.4 Monitor data replication
  - [ ] 7.5 Launch test instances (approval required)
  - [ ] 7.6 Mark applications ready for cutover
  - [ ] 7.7 Launch cutover instances (approval required)
  - [ ] 7.8 Finalize cutover and archive source servers
- [ ] 8. Containerization (Step 7, if applicable) — see workload-vmware-containerization.md
  - [ ] 8.1 Provide source code (Git or zip)
  - [ ] 8.2 Review AI-generated Docker artifacts
  - [ ] 8.3 Publish images to ECR (web UI approval)
  - [ ] 8.4 Select deployment target (EKS or ECS) and generate IaC
  - [ ] 8.5 Deploy test infrastructure (web UI approval)
  - [ ] 8.6 Deploy cutover infrastructure (web UI approval)
```

---

## Troubleshooting

| Symptom                                                | Likely Cause                                                | Resolution                                                                                                                                                                                                                |
| ------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Job cannot be resumed after stop                       | VMWARE_V2 jobs are non-restartable                          | Stopping is irreversible — create a new job to start over. Artifacts from the stopped job are preserved.                                                                                                                  |
| NSX import fails                                       | NSX imports only supported for end-to-end migration jobs    | Switch to end-to-end job type, or use a different source format (RVTools, ACI, etc.)                                                                                                                                      |
| Cannot create job in desired Region                    | Jobs execute in the workspace Region                        | The job always runs in the workspace Region. To target a different Region for migration, configure the target Region in the job settings. To run the job itself in a different Region, create a workspace in that Region. |
| Discovery data not recognized                          | Unsupported format or missing required fields               | Verify format matches one of the three supported discovery options; check required columns                                                                                                                                |
| Network deployment fails with Organization ID mismatch | LZA deployment account not in same AWS Organization         | Verify Organization membership or choose a different IaC format                                                                                                                                                           |
| Server replication issues                              | See `workload-vmware-server.md` Troubleshooting             | Covers agent install failures, stuck replication, MGN initialization, inventory import issues                                                                                                                             |
| Network mapping issues                                 | See `workload-vmware-network.md` Troubleshooting            | Covers connector KMS issues, file upload, topology and SG strategy problems                                                                                                                                               |
| Containerization issues                                | See `workload-vmware-containerization.md` Known Limitations | Covers TOOL_APPROVAL web UI requirement, connector targetRegion, source code size limits                                                                                                                                  |

---

## Known Limitations

- One target AWS Region per VMware migration job — create multiple jobs to migrate to different Regions
- Stopping a running migration job is irreversible — VMWARE_V2 jobs cannot be restarted once stopped. A new job must be created to start over. Artifacts from the stopped job are preserved but job progress is lost.
- NSX imports are only supported for end-to-end migration jobs
- Physical servers (non-virtualized) are not in scope
- VMware-specific features (vMotion, DRS, HA) have no direct AWS equivalents — require architectural redesign
- License mapping (Windows Server, SQL Server on VMs) requires manual review
- AWS Transform generates network configurations and migration strategies based on environment assessment — review with stakeholders before proceeding to ensure security and compliance requirements are met
