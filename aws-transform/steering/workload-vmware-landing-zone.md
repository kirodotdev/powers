# Landing Zone

> **Last Updated:** 2026-05-10

## Capabilities

Build an AWS landing zone as the foundation for your migration project. AWS Transform analyzes your migration inventory and business requirements to recommend an Organizational Unit (OU) and account structure, apply Service Control Policies (SCPs), and generate or deploy the infrastructure as code (IaC).

The landing zone agent operates in two phases:

1. **Foundation setup** — Establish the core landing zone: AWS Control Tower, foundational OUs (Security, Infrastructure, Sandbox, Workloads), and core accounts (Log Archive, Audit).
2. **Workload account design** — Design and create workload OUs and accounts based on migration waves, business units, and environment separation requirements.

AWS Transform supports both **greenfield** (no existing landing zone) and **brownfield** (existing OUs and accounts already deployed) environments. In brownfield scenarios, AWS Transform detects the existing organization structure and recommends only the changes needed to fill gaps against AWS best practices.

## Starting Workflow

1. **Connector setup** — Create a target AWS account connector pointing to the organization management account in the Control Tower home Region
2. **Confirm organization context** — AWS Transform retrieves the connector configuration and presents the management account ID and target Region for confirmation
3. **Foundation setup** — Design and deploy (or generate IaC for) the core OU structure, Control Tower initialization, and SCPs
4. **Workload account design** — Answer discovery questions; AWS Transform proposes OU and account structure based on migration waves and business requirements
5. **Workload deployment** — Deploy workload OUs, accounts, and SCPs, or download IaC artifacts

**Key questions to ask user:**

- "Do you already have AWS Control Tower or AWS Organizations set up (brownfield), or are we starting from scratch (greenfield)?"
- "What is your Control Tower home Region? This must match your IAM Identity Center Region."
- "What email prefix and domain should AWS Transform use to generate account email addresses (for example, `aws-admin` and `acme.com`)?"
- "How many business units or teams will use AWS, and do they need separate accounts?"
- "Do you have compliance requirements (HIPAA, PCI-DSS, SOC2, FedRAMP) that affect account isolation?"
- "Do you have migration planning data (wave plans, server-to-application mappings) already in AWS Transform?"

---

## Agent Monitoring Behavior

Throughout the entire landing zone flow, the agent MUST proactively pull status and report progress to the user after every significant action. Do not wait for the user to ask.

**Rules:**

- **After triggering any operation** (connector creation, Control Tower initialization, OU/account creation, SCP application, deployment submission) — immediately begin polling and report status updates as they arrive
- **After each poll** — present a concise status summary: what completed, what is in progress, what is blocked, and what the next step is
- **During long-running operations** (Control Tower initialization, CloudFormation stack deployment, account creation) — poll on a regular cadence and proactively surface progress
- **When a deployment approval is required** — surface it immediately, inform the user it is pending, and wait for the user to confirm approval has been granted. Then verify once.
- **When a HITL task appears** — surface it immediately, do not wait for the user to notice
- **When an error or failure occurs** — surface it immediately with the failure reason and suggested resolution

**Per-step monitoring expectations:**

| Step | What to Poll | What to Report |
|------|-------------|----------------|
| Connector setup | Connector status | Connector ACTIVE, management account ID and Region confirmed |
| Control Tower initialization | CloudFormation stack status | Stack creation complete, Control Tower initialized |
| Foundation OU/account creation | Deployment job status | OUs created, Log Archive and Audit accounts provisioned |
| SCP application | SCP assignment status | SCPs applied, updated organization tree |
| Workload OU/account creation | Deployment job status | OUs and accounts created in correct locations |
| IaC generation | Artifact availability | Artifacts ready for download, checksum provided |
| Deployment approval | Approval task status | Approved → deployment proceeds; Denied → surface reason and offer to resubmit |

---

## Prerequisites

Before starting landing zone setup, the following must be in place:

- **Target AWS account connector** — A connector configured for the organization management account. The connector Region must match the Control Tower home Region and the IAM Identity Center Region.
- **Management account** — The AWS Organizations root account. All OUs and accounts are created under this account.
- **Email convention** — A prefix and domain for plus-addressed account emails (for example, `aws-admin+<account-name>@acme.com`). AWS Transform derives all account emails automatically from this convention.

> **IAM Identity Center Region dependency** — The connector Region must match both the Control Tower home Region and the IAM Identity Center Region. If IAM Identity Center is already configured in your organization, Control Tower initialization will fail if the connector targets a different Region.

> In brownfield scenarios, AWS Transform inspects existing account emails to infer the plus-addressing convention already in use and offers to continue with the same pattern.

---

## Connector Setup

The landing zone agent requires a target AWS account connector to provision resources in the organization management account.

The connector has permissions to:

- Set up AWS Control Tower
- Create organizational units and accounts
- Configure Service Control Policies (SCPs)

Permissions are scoped to resources tagged with `CreatedBy: AWSTransform` and `ATWorkspace: {workspace-id}` where applicable, and cover:

- S3 bucket operations for buckets starting with `transform-vmware-landing-zone-`
- CloudFormation stack deployments and change set management
- AWS Control Tower operations (managing landing zones, enabling baselines and controls)
- AWS Organizations management (creating and managing OUs, creating accounts, moving accounts)
- SCP management via AWS Control Tower
- AWS Service Catalog provisioning artifact management

The connector requires a real KMS key ARN — resolve it before creating:

```bash
aws kms describe-key --key-id alias/aws/s3 --region <control-tower-home-region> --query 'KeyMetadata.Arn' --output text
```

```python
create_connector(
  workspaceId="<workspace-id>",
  connectorName="landing-zone-connector",
  connectorType="<landing-zone-connector-type>",   # discover via list_resources
  configuration={"encryptionKeyArn": "<real-kms-key-arn>"},
  awsAccountId="<management-account-id>",
  targetRegions=["<control-tower-home-region>"]
)
# → Present verification link to user for approval via AWS Console
# → Connector approval is human-gated — do NOT auto-poll
# → When user confirms approval, verify status once via get_resource(resource="connector")
```

Always use the verification link to approve — this creates a fresh IAM role with the correct permissions. Reusing a role from a deleted connector may have permissions on the wrong key.

---

## Workflow

### Phase 1: Foundation Setup

#### Step 1: Design Foundation Structure

AWS Transform recommends the following foundation OU structure based on AWS best practices. The user can customize it before creation.

**Recommended foundation OUs:**

| OU | Purpose | Accounts |
|----|---------|----------|
| Security | Centralized audit logging and monitoring. Isolates audit trail from workload teams. | Audit, Log Archive |
| Infrastructure | Shared networking (Transit Gateway, VPN), DNS, and common services. | None (created empty) |
| Sandbox | Developer experimentation with spending limits and restricted access. | Sandbox |
| Workloads | Contains Production, Non-Production, and optionally Regulated sub-OUs. Populated in Phase 2. | None (created empty) |

> The Security OU with Audit and Log Archive accounts is created as part of the Control Tower foundation setup. Infrastructure, Sandbox, and Workloads OUs are created separately after the user confirms the structure.

> **The Security OU is managed by Control Tower.** You cannot add accounts, SCPs, or any resources to it through the landing zone agent.

**In brownfield scenarios:** AWS Transform compares the existing foundation against this recommended structure and reports only the gaps. For example: "Your foundation has Security and Infrastructure OUs but no Sandbox OU."

#### Step 2: Control Tower Initialization

AWS Transform checks whether AWS Control Tower is already initialized.

**If Control Tower is not yet initialized:**

- AWS Transform provides a link to the AWS Transform console page
- Generating the operation in the link creates a CloudFormation stack to bootstrap Control Tower in the target Region
- After the stack creation completes, AWS Transform continues with the deployment

**What Control Tower provisions automatically:**

- Root — top-level parent containing all OUs
- Security OU — with Log Archive account (centralized, immutable logging) and Audit account (read-only access for security and compliance review)
- Mandatory guardrails — preventive and detective controls applied across the organization; cannot be disabled
- IAM Identity Center directory — cloud-native directory with preconfigured groups and SSO access

> Control Tower uses CloudFormation StackSets to deploy and manage resources consistently across all accounts and Regions. Do not modify or delete Control Tower managed resources outside of supported methods.

#### Step 3: Account Email Convention

AWS Transform uses plus addressing to generate unique account emails from a single mailbox.

**Format:** `prefix+account-name@domain`

The user provides a prefix (for example, `aws-admin`) and a domain (for example, `acme.com`). AWS Transform derives all account emails automatically:

- Audit account: `aws-admin+audit@acme.com`
- Log Archive account: `aws-admin+log-archive@acme.com`
- Sandbox account: `aws-admin+sandbox@acme.com`

#### Step 4: Service Control Policies (SCPs) — Foundation

SCPs set the maximum permissions for all accounts in an OU. They don't grant access — they define boundaries that no one in the account can exceed, even account administrators.

Control Tower applies baseline guardrails automatically. AWS Transform also recommends additional SCPs based on AWS best practices for a minimum viable landing zone.

SCPs can be applied to the Infrastructure, Sandbox, and Workloads OUs. **The Security OU cannot be targeted by SCPs through this tool.**

**In brownfield scenarios:** AWS Transform checks which SCPs are already applied and only recommends ones that fill gaps.

#### Step 5: Foundation Deployment

After the foundation design is confirmed, the user chooses how to deploy:

| Option | Description |
|--------|-------------|
| Deploy for me | AWS Transform deploys the foundation OUs, accounts, and SCPs to the AWS Organization |
| I'll deploy on my own | AWS Transform generates IaC artifacts for download (CDK or LZA — see IaC Formats) |
| Design workload accounts first | Skip deployment and continue to Phase 2; deploy everything together later |

> All deployment requests require explicit approval. See Deployment Approvals below.

---

### Phase 2: Workload Account Design

#### Step 6: Migration Planning Context

Before asking discovery questions, check the artifact store for migration planning outputs from a prior job in the same workspace. Migration planning artifacts contain wave plans and server-to-application mappings that drive the workload account structure.

```python
# 1. List artifacts scoped to migration planning outputs
list_resources(resource="artifacts",
  workspaceId="<workspace-id>",
  pathPrefix="migration-planning/")

# 2. If artifacts are found, download the relevant ones
get_resource(resource="artifact",
  workspaceId="<workspace-id>",
  artifactId="<artifact-id>",
  savePath="/tmp/migration-plan.json"   # or .csv/.zip depending on artifact type
)
```

**If migration planning artifacts are found:** Display a summary of the wave plan and server-to-application mappings, then ask the user to confirm or adjust before proceeding to workload structure design.

**If no migration planning artifacts are found:** Proceed directly to Step 7 (Discovery) and ask the discovery questions to gather the same information manually.

> Migration planning artifacts are produced by the VMware migration planning phase. If the user ran discovery and wave planning in a separate job or workspace, ask them to confirm the workspace ID so the correct artifacts can be retrieved.

#### Step 7: Discovery

AWS Transform asks questions to understand workload requirements. Any question can be skipped. Topics include:

- Number of business units or teams using AWS
- Industry and applicable compliance frameworks (HIPAA, PCI-DSS, SOC2, FedRAMP)
- Whether workloads handle sensitive data (PII, PHI, financial)
- Environment separation preferences (dev/test/staging/prod as separate accounts or shared)
- Workload isolation requirements
- Business applications and their purposes
- Server grouping into applications
- Cost tracking and allocation needs (by business unit, project, environment)
- Expected growth in the next 12–24 months
- Account strategy preference (single app per account, grouped, or environment-based)

#### Step 8: Proposed Workload Structure

Based on discovery answers and migration planning data, AWS Transform proposes an OU and account structure under the Workloads OU, including the reasoning behind each design decision.

**Design principles AWS Transform follows:**

| Principle | Detail |
|-----------|--------|
| Wave integrity | All servers in a migration wave go to the same account — waves cannot be split across accounts (rehost limitation during wave execution) |
| Environment isolation | If isolated environments are requested, AWS Transform creates `Workloads/Production` and `Workloads/Non-Production` sub-OUs |
| Compliance isolation | If applicable frameworks are identified, AWS Transform creates `Workloads/Regulated` and `Workloads/Standard` sub-OUs |
| Business unit separation | If multiple business units require different governance, AWS Transform creates business-unit-specific OUs under Workloads |
| Sensitive data isolation | Critical or sensitive-data applications get a single app per account — may require iterating on the wave plan |
| Dependency grouping | Tightly coupled applications with shared dependencies are grouped in one account |

Each proposed account includes: name, purpose, target OU, and business unit. AWS Transform shows the naming convention in use (for example, `<business-unit>-<environment>-<workload>`).

The user can review and modify the proposed structure before AWS Transform applies changes. After applying, the user can iterate — making additional changes until satisfied.

#### Step 9: Workload SCPs

After the workload structure is created, AWS Transform presents available SCPs and asks if any should be applied to workload OUs. The user selects which SCPs to apply and to which OUs. AWS Transform applies the SCPs and shows the updated organization tree with an SCP summary table.

#### Step 10: Workload Deployment

After the workload design is confirmed, the user chooses how to deploy:

| Option | Description |
|--------|-------------|
| Deploy for me | AWS Transform deploys the workload OUs, accounts, and SCPs to the AWS Organization |
| I'll deploy on my own | AWS Transform generates IaC artifacts for download (CDK or LZA — see IaC Formats) |

> All deployment requests require explicit approval. See Deployment Approvals below.

---

## IaC Formats

When the user chooses self-deployment, AWS Transform generates IaC artifacts in the following formats:

| Format | Description |
|--------|-------------|
| AWS CDK | TypeScript project for programmatic infrastructure deployment |
| Landing Zone Accelerator (LZA) | Configuration YAML files based on LZA Universal Configuration version 1.1.0. Works with the Landing Zone Accelerator on AWS to establish multi-account environments with pre-configured governance, organization structure, and networking aligned to AWS best practices |

> When deploying via the LZA pipeline, the AWS Transform account and LZA installation must be in the same AWS Organization. Deployment will fail if there is a mismatch between the Organizations IDs used in AWS Transform and LZA.

**Verifying downloaded artifacts:**

```bash
openssl dgst -sha256 -binary <file.zip> | base64
```

Compare the output to the checksum provided by AWS Transform to verify the file hasn't been corrupted or tampered with.

---

## Deployment Approvals

When the user selects AWS Transform-managed deployment:

1. **Submission** — Power confirms deployment intent; AWS Transform submits CloudFormation templates for review
2. **Routing** — Request routes automatically to authorized approvers via the AWS Transform Approvals tab
3. **Review** — Approvers validate CloudFormation templates and landing zone configurations against security standards
4. **Decision** — Approver approves or denies:
   - **Approved** → deployment proceeds automatically
   - **Denied** → inform user, suggest contacting approver for required modifications
5. **Audit** — All approval decisions are tracked for audit purposes

Only users with the **Admin** or **Approver** role in AWS Transform can approve deployment requests. Each submission triggers a new review cycle.

**Power behavior during approval:**

- After submission, inform the user that the deployment requires approval
- Deployment approval is human-gated — do NOT auto-poll. Present the pending status and wait for the user to confirm approval has been granted, then verify once.
- If denied, present the denial to the user and offer to modify the landing zone design and resubmit

**Rollback:** Once OUs and accounts are deployed, they cannot be removed through the landing zone agent. Account structure decisions are difficult to reverse — validate in non-production environments first. Manual deletion via the AWS Console or CLI is required if changes need to be undone.

---

## Reversing Changes

Only non-deployed elements can be removed. Once an OU or account is deployed, it cannot be removed through the landing zone agent.

When removing elements, order matters:

1. Remove accounts first (by email)
2. Remove SCPs from OUs
3. Remove child OUs — an OU cannot be removed if it still has accounts or nested OUs

---

## Resource Tagging

AWS Transform automatically tags all generated resources:

| Tag | Value |
|-----|-------|
| `CreatedBy` | `AWSTransform` |
| `ATWorkspace` | Workspace identifier |

> If the migration is part of the AWS Migration Acceleration Program (MAP 2.0), the MAP tag (`map-migrated: migMPE_ID`) can be included. It is requested during connector setup and applied during landing zone deployment.

---

## Agents & Transforms

| Agent | How to Discover | Purpose |
|-------|----------------|---------|
| Landing zone agent | `list_resources` with `resource: "agents"` | Foundation setup, workload account design, SCP configuration, IaC generation |

**Discover the agent dynamically:**

```python
list_resources(resource="agents")
# Or ask the chat agent
send_message(workspaceId="...", text="What agents are available for landing zone setup?")
# Then create job with discovered orchestratorAgent
create_job(workspaceId="...", jobName="Landing Zone Setup",
  objective="Build AWS landing zone foundation and workload account structure",
  orchestratorAgent="<discovered>")
```

---

## Decision Points

| Decision | Options | When to Ask |
|----------|---------|-------------|
| Greenfield vs brownfield | Greenfield (new) / Brownfield (existing OUs/accounts) | Start — determines what gaps to fill |
| Deployment method | Deploy for me / I'll deploy on my own / Design workload accounts first | Phase 1 Step 5 |
| Deployment method (workload) | Deploy for me / I'll deploy on my own | Phase 2 Step 10 |
| IaC format (if self-deploying) | AWS CDK / Landing Zone Accelerator (LZA) | When user selects "I'll deploy on my own" |
| Foundation OU customization | Accept recommended structure / Customize OUs and accounts | Phase 1 Step 1 |
| SCP selection | Which SCPs to apply and to which OUs | Phase 1 Step 4 and Phase 2 Step 9 |
| Account strategy | Single app per account / Grouped / Environment-based | Phase 2 Step 7 discovery |
| Environment separation | Separate accounts per env / Shared accounts | Phase 2 Step 7 discovery |
| Compliance sub-OUs | Regulated / Standard separation | Phase 2 Step 8 — if frameworks identified |

---

## Example Requirements

```
## Requirement 1: Foundation Setup
**User Story:** As a cloud platform engineer, I want the core landing zone foundation deployed
so that governance controls, centralized logging, and account isolation are in place before any workloads arrive.
**Acceptance Criteria:**
1. WHEN foundation setup completes, Control Tower SHALL be initialized with Security OU, Log Archive account, and Audit account
2. WHEN foundation setup completes, Infrastructure, Sandbox, and Workloads OUs SHALL exist in the organization
3. WHEN SCPs are applied, member accounts SHALL be unable to exceed the boundaries defined by the SCPs
**Handled by:** AWS Transform Landing Zone Agent

## Requirement 2: Workload Account Structure
**User Story:** As a cloud platform engineer, I want workload OUs and accounts designed around my migration waves
so that servers can be migrated into correctly isolated accounts without splitting waves.
**Acceptance Criteria:**
1. WHEN workload structure is proposed, ALL servers in a migration wave SHALL map to the same target account
2. WHEN environment isolation is required, Workloads/Production and Workloads/Non-Production sub-OUs SHALL be created
3. WHEN sensitive-data applications are identified, they SHALL each receive a dedicated account
**Handled by:** AWS Transform Landing Zone Agent

## Requirement 3: IaC Generation
**User Story:** As a platform engineer, I want IaC artifacts generated for the landing zone
so that I can review, version-control, and deploy the infrastructure through my own pipeline.
**Acceptance Criteria:**
1. WHEN IaC generation completes, artifacts SHALL be available in CDK (TypeScript) or LZA (YAML) format
2. WHEN artifacts are downloaded, a checksum SHALL be provided to verify file integrity
3. WHEN LZA format is selected, the generated YAML SHALL be compatible with LZA Universal Configuration version 1.1.0
**Handled by:** AWS Transform Landing Zone Agent
```

---

## Example Tasks

```
- [ ] 1. Connector setup
  - [ ] 1.1 Create target AWS account connector for the management account
  - [ ] 1.2 Confirm connector Region matches Control Tower home Region and IAM Identity Center Region
  - [ ] 1.3 Approve connector via AWS Console verification link
  - [ ] 1.4 Confirm management account ID and target Region presented by AWS Transform
- [ ] 2. Foundation design (Phase 1, Steps 1–4)
  - [ ] 2.1 Review recommended foundation OU structure (Security, Infrastructure, Sandbox, Workloads)
  - [ ] 2.2 Customize OU structure if needed
  - [ ] 2.3 Confirm email prefix and domain for plus-addressed account emails
  - [ ] 2.4 Review and select SCPs to apply to foundation OUs
- [ ] 3. Foundation deployment (Phase 1, Step 5)
  - [ ] 3.1 Choose deployment method (deploy / self-deploy / design workload accounts first)
  - [ ] 3.2 If Control Tower not initialized: follow link to create bootstrap CloudFormation stack
  - [ ] 3.3 Submit deployment for approval; wait for Admin approval
  - [ ] 3.4 Confirm Log Archive and Audit accounts created in Security OU
  - [ ] 3.5 Confirm Infrastructure, Sandbox, and Workloads OUs created
- [ ] 4. Workload account design (Phase 2, Steps 6–9)
  - [ ] 4.1 Check artifact store for migration planning artifacts (`pathPrefix="migration-planning/"`)
  - [ ] 4.2 If found: display wave plan summary and confirm or adjust with user; if not found: proceed to discovery questions
  - [ ] 4.3 Answer discovery questions (business units, compliance, environment separation, account strategy)
  - [ ] 4.4 Review proposed workload OU and account structure
  - [ ] 4.5 Iterate on structure until satisfied
  - [ ] 4.6 Review and select SCPs to apply to workload OUs
- [ ] 5. Workload deployment (Phase 2, Step 10)
  - [ ] 5.1 Choose deployment method (deploy / self-deploy)
  - [ ] 5.2 If self-deploying: select IaC format (CDK or LZA), download artifacts, verify checksum
  - [ ] 5.3 If deploying via AWS Transform: submit for approval; wait for Admin approval
  - [ ] 5.4 Confirm all workload OUs and accounts created in correct locations
```

---

## Known Limitations

- Once an OU or account is deployed, it cannot be removed through the landing zone agent — account structure decisions are difficult to reverse
- The Security OU is managed by Control Tower — accounts, SCPs, and resources cannot be added to it through the landing zone agent
- All servers in a migration wave must go to the same account — waves cannot be split across accounts during rehost execution
- The connector Region must match the Control Tower home Region and the IAM Identity Center Region — mismatches cause Control Tower initialization to fail
- LZA deployment requires the AWS Transform account and LZA installation to be in the same AWS Organization
- SCPs cannot grant permissions — they only restrict what IAM policies allow
- Brownfield environments may require remediation before Control Tower can be initialized — AWS Transform reports gaps but does not automatically fix pre-existing misconfigurations
