# VMware Containerization

> **Last Updated:** 2026-05-10

## Capabilities

Containerize applications from VMware environments for deployment on Amazon ECS or Amazon EKS using AWS Transform's AI-powered agent. Analyzes source code, generates Docker artifacts, builds and publishes container images, and generates Infrastructure as Code for container orchestration platforms.

- Source code analysis → Dockerfiles + configuration files (AI-generated)
- Container image building → Amazon ECR (with automated vulnerability scanning)
- Infrastructure as Code generation → Amazon EKS (Helm charts) or Amazon ECS (Terraform modules)
- Private dependency support → AWS CodeArtifact (Maven, PyPI, npm) + private ECR base images
- Iterative test deployment → validate before production cutover
- Standalone containerization or end-to-end VMware migration with containerize strategy

### Access Path

Containerization is accessed through a VMware migration job. Two modes:

| Mode | When to Use |
|------|-------------|
| **Standalone containerization** | Containerize source code without a full VMware migration |
| **End-to-end migration with containerization** | Full VMware migration with `containerize` strategy assigned to one or more waves |

### Prerequisites

| Prerequisite | Required | Notes |
|-------------|----------|-------|
| AWS Transform workspace | Yes | See Getting Started |
| Application source code | Yes | Git repo via AWS CodeConnections, or zip upload. Individual files ≤ 1 GB, total ≤ 8 GB. |
| Amazon ECR repository | Optional | Can configure later in workflow when ready to publish |
| Amazon EKS cluster | For EKS deployments | Existing cluster or permissions to create infrastructure |
| Amazon ECS permissions | For ECS deployments | Permissions to create ECS clusters, services, and related resources |

---

## Workflow

The containerization workflow is a 9-step sequence. The AWS Transform agent guides the user through each step in the chat interface.

**When presenting the workflow to the user, show it as a sequential numbered list:**

```
1. Review security disclaimer
2. Clone source code
3. Containerize (AI analysis → Docker artifacts)
4. Review Docker artifacts and code changes
5. Publish images to Amazon ECR
6. Generate Infrastructure as Code (EKS Helm charts or ECS Terraform)
7. Deploy test infrastructure
8. Clean up test infrastructure
9. Deploy cutover infrastructure (production)
```

### Step 1: Review Security Disclaimer

- Agent presents security disclaimer
- User must review and accept before proceeding

### Step 2: Clone Source Code

- User provides application source code
- Accepted formats: Git repository (via AWS CodeConnections) or zip file upload
- Individual files must not exceed 1 GB; total source code must not exceed 8 GB
- **Git flow:** Create connector via API (see Connector Setup), complete the HITL task with connector ID, then provide repo name. The agent will ask for the CodeBuild execution role deployment before cloning.
- **Zip flow:** Upload via `upload_artifact` with `categoryType: "CUSTOMER_INPUT"`

### Step 3: Containerize

- AI agent analyzes source code
- Generates Docker artifacts (Dockerfiles, related configuration files)
- This is the core AI-driven analysis step
- **Before starting analysis, the agent asks about preferences. Present them clearly:**
  - Show the defaults that will be used if the user just proceeds:
    1. Base image: Amazon Linux 2023
    2. Scope: Process all applications in the repository
    3. Dockerfiles: Reuse existing if present (with minor modifications if needed)
  - Show the optional customizations available:
    - Enable private CodeArtifact dependencies (Maven, PyPI, npm)
    - Enable private ECR base images
    - Always generate a new Dockerfile (ignore existing ones)
  - Ask: "Would you like to proceed with defaults, or customize any of these?"

### Step 4: Review Docker Artifacts and Code Changes

- Agent presents generated Dockerfiles and configuration
- User reviews and approves code changes before proceeding
- **GATE:** User must approve artifacts before continuing

### Step 5: Publish Images

- Builds container images using AI-driven Docker builds
- Publishes images to Amazon ECR
- Automated vulnerability scanning runs on published images
- Private dependencies (CodeArtifact, private ECR base images) resolved if configured

### Step 6: Generate Infrastructure as Code

- **MANDATORY GATE:** You MUST ask the user which deployment target they want BEFORE proceeding. NEVER assume or infer from earlier context. ECS and EKS are completely different target platforms — do not guess.
- Ask: "Where do you want to deploy your containerized application? Amazon ECS (Terraform modules) or Amazon EKS (Helm charts)?"
- Wait for explicit user response before telling the agent which platform to generate IaC for.
- **EKS:** Generates Helm charts with automated validation and security scanning
- **ECS:** Generates Terraform modules with automated validation and security scanning

### Step 7: Deploy Test Infrastructure

- The agent creates a HITL task with an infrastructure configuration form
- The form contains fields with dropdown options (VPCs, subnets, security groups, IAM roles) pulled from the user's AWS account
- **MANDATORY PRESENTATION FORMAT:** When presenting the infrastructure configuration form:
  1. First show a **summary table** listing ALL fields, whether each is required or optional, the input type (text, select, multiselect), and a brief description
  2. Then show each field as a **separate section** with its complete list of ALL available options — never truncate, summarize, or say "see list below"
  3. For IAM roles: show recognizable/relevant roles in full, then note the count of remaining generic roles grouped by prefix (e.g., "plus 16 StackSet-aws-open-ports roles, 20 migration-factory-test roles")
  4. If two fields share the same options list (e.g., task_security_group_ids and alb_security_group_ids), you may say "Same options as [field name] above" ONLY after showing the full list for the first field
  5. **After presenting all options, ask the user for their choice ONE FIELD AT A TIME.** Do not ask for all values at once. Start with the first required field, wait for the answer, then ask for the next.
- After the user provides all values, submit the form via `complete_task`
- Deploys test infrastructure for validation
- User validates the deployment before production cutover

### Step 8: Clean Up Test Infrastructure

- Tears down test resources after validation
- Ensures no lingering test infrastructure remains

### Step 9: Deploy Cutover Infrastructure

- Deploys finalized production infrastructure
- Completes the containerization workflow
- **IMPORTANT: After the agent confirms deployment success, it will show a "Proceed" button. You MUST send "Proceed" to finalize the job.** The job remains in `EXECUTING` status until this acknowledgment is sent. Without it, the job never transitions to `COMPLETE` in the console.
- After sending "Proceed", verify the agent responds with a completion message (e.g., "The migration job has been marked as complete")
- Only then is the workflow truly finished

---

## Agents & Transforms

| Agent | How to Discover | Purpose |
|-------|----------------|---------|
| VMware Migration Agent (orchestrator) | `list_resources` with `resource: "agents"` | Orchestrates containerization workflow within a VMware migration job |
| Containerization sub-agent | _(invoked by orchestrator)_ | Source code analysis, Docker artifact generation, image building, IaC generation |

**Discover the agent dynamically:**

```python
list_resources(resource="agents")
# Find the VMware migration orchestrator from results
# Then create job with discovered orchestratorAgent
create_job(
  workspaceId="<workspace-id>",
  jobName="VMware Containerization <timestamp>",
  objective="Containerize application source code for deployment on ECS/EKS",
  orchestratorAgent="<discovered>"
)
```

**Selection criteria:** Choose the agent whose description mentions "VMware migration" — containerization runs within the VMware migration job context. The orchestrator invokes the containerization sub-agent as needed.

### Job Creation

To start a containerization job:

1. Create a VMware migration job in the workspace
2. Choose standalone containerization or end-to-end migration with containerize strategy
3. The agent guides through the 9-step workflow

---

## Connector Setup (Reference)

When the user chooses Git repository in Step 2, the agent creates a HITL task (`GeneralConnector` component, title "Set up Containerization Connector") requesting connector configuration. To complete it programmatically instead of directing the user to the web UI:

### 1. Check for Existing Connector

```python
list_resources(resource="connectors", workspaceId="<workspace-id>")
# Filter for connectorType="vmware_migration|containerization|2"
```

- **If an ACTIVE containerization connector exists** — ask the user: "There's already a containerization connector configured (`<name>`, region `<region>`). Would you like to use it, or create a new one?"
- **If no containerization connector exists** — proceed to create one.

### 2. Resolve CodeConnections ARN (if user doesn't have it)

```bash
aws codeconnections list-connections --region <target-region> --query 'Connections[?ConnectionStatus==`AVAILABLE`].[ConnectionName,ConnectionArn]' --output table
```

- **One connection** — use it.
- **Multiple connections** — ask the user which one to use.
- **No connections** — tell the user to create one in the AWS Console: [Developer Tools → Settings → Connections](https://console.aws.amazon.com/codesuite/settings/connections). They must install the GitHub App and grant access to the target repositories.

### 3. Create the Connector (if needed)

```python
create_connector(
  workspaceId="<workspace-id>",
  connectorName="containerization-<region>",
  connectorType="vmware_migration|containerization|2",
  configuration={"codeConnectionArn": "<codeconnections-arn>"},
  awsAccountId="<account-id>",
  targetRegions=["<target-region>"]
)
```

**Key rules:**

- `targetRegions` — **top-level parameter**, NOT inside `configuration`
- `encryptionKeyArn` — NOT supported for this connector type. Do not pass it.
- `configuration` cannot be empty — at least `codeConnectionArn` or `mapAgreementId` is required.

### 4. Approve the Connector

Connector approval is human-gated. Present the verification link to the user. Do NOT auto-poll. When user confirms → verify status once via `get_resource(resource="connector")`. Must be ACTIVE before proceeding.

### 5. Complete the HITL Task

Submit the connector ID to bind it to the job:

```python
complete_task(
  workspaceId="<workspace-id>",
  jobId="<job-id>",
  taskId="<connector-task-id>",
  content={"connectorId": "<connector-id>"}
)
```

Get the task ID from `list_resources(resource="tasks")` — look for title "Set up Containerization Connector".

### After Connector is Accepted

The agent may ask the user to deploy a **CodeBuild execution role** via a CloudFormation stack (skipped if already deployed from a previous job). This is human-gated — present the link and wait for confirmation.

Then the agent asks for the repository name:

- Format: `owner/repo-name` (e.g., `evgenyka/classDemo`)
- **Do NOT specify a branch** unless certain it exists. Omitting the branch uses the repository's default branch.
- Repository names are case-sensitive.

### Known Limitations (Connector)

- `targetRegions` must be a top-level parameter — passing `targetRegion` inside `configuration` returns `400: unsupported connector properties`
- `encryptionKeyArn` is NOT supported for this connector type
- `configuration` cannot be empty — API rejects it without at least one valid property
- Agent does not auto-detect existing connectors in a fresh job — must complete the HITL task with the connector ID
- CodeConnections must have the GitHub App installed with access to the target repositories — a connection in AVAILABLE status without the app installed will fail at clone time

---

## Decision Points

| Step | Question to Ask User | Options |
|------|---------------------|---------|
| Mode | "Do you want standalone containerization or end-to-end migration with containerization?" | Standalone / End-to-end migration |
| Source code | "How would you like to provide your source code?" | Git repository (CodeConnections) / Zip upload |
| Artifact review | "Do the generated Docker artifacts look correct?" | Approve / Request changes |
| Private dependencies | "Does your application use private dependencies?" | Configure CodeArtifact / Configure private ECR base images / No private dependencies |
| Deployment target | "Where do you want to deploy your containerized application?" | Amazon EKS (Helm charts) / Amazon ECS (Terraform modules) |
| Test validation | "Has the test deployment been validated successfully?" | Proceed to cutover / Re-deploy test / Modify configuration |
| Cutover | "Ready to deploy production infrastructure?" | Deploy cutover / Go back to test |

---

## Assessment Signals

| File Pattern | What to Look For | Indicates |
|-------------|-----------------|-----------|
| `Dockerfile`, `docker-compose.yml` | Existing container configuration | Already partially containerized |
| `pom.xml`, `build.gradle` | Java build files | Java application — Maven/Gradle build |
| `package.json` | Node.js project | Node.js application — npm/yarn build |
| `requirements.txt`, `pyproject.toml`, `setup.py` | Python dependencies | Python application — pip build |
| `*.csproj`, `*.sln` | .NET project files | .NET application |
| `.mvn/`, `mvnw` | Maven wrapper | Self-contained Maven build |
| `Procfile` | Process declarations | Application entry points defined |
| `application.yml`, `application.properties` | Spring Boot config | Spring Boot application |
| `web.xml`, `WEB-INF/` | Java EE/Servlet config | Traditional Java web application |

---

## Example Requirements

```
## Requirement 1: Source Code Containerization
**User Story:** As a platform engineer, I want my VMware-hosted application containerized
so that it can run on Amazon EKS or Amazon ECS.
**Acceptance Criteria:**
1. WHEN containerization completes, a Dockerfile SHALL be generated for each application component
2. WHEN containerization completes, container images SHALL be published to Amazon ECR
3. WHEN containerization completes, vulnerability scanning SHALL report no critical findings
**Handled by:** AWS Transform VMware Migration Agent (Containerization sub-agent)

## Requirement 2: Infrastructure as Code Generation
**User Story:** As a DevOps engineer, I want deployment infrastructure generated
so that I can deploy containerized applications to my target platform.
**Acceptance Criteria:**
1. WHEN IaC generation completes for EKS, Helm charts SHALL be generated with security scanning passed
2. WHEN IaC generation completes for ECS, Terraform modules SHALL be generated with validation passed
3. WHEN IaC generation completes, deployment templates SHALL include all required service configurations
**Handled by:** AWS Transform VMware Migration Agent (Containerization sub-agent)

## Requirement 3: Test and Cutover Deployment
**User Story:** As an operations engineer, I want to validate containerized deployments
before production cutover so that I can confirm application behavior.
**Acceptance Criteria:**
1. WHEN test deployment completes, application SHALL be accessible and functional
2. WHEN test infrastructure is cleaned up, no orphaned resources SHALL remain
3. WHEN cutover deployment completes, production infrastructure SHALL match validated test configuration
**Handled by:** AWS Transform VMware Migration Agent (Containerization sub-agent) + User validation
```

---

## Example Tasks

```
- [ ] 1. Setup (AWS Transform)
  - [ ] 1.1 Create VMware migration job
  - [ ] 1.2 Select containerization mode (standalone or end-to-end)
  - [ ] 1.3 Review and accept security disclaimer
- [ ] 2. Source code provisioning
  - [ ] 2.1 Provide source code (Git repo or zip upload)
  - [ ] 2.2 Configure private dependencies (if applicable)
- [ ] 3. Containerization (AWS Transform)
  - [ ] 3.1 AI agent analyzes source code
  - [ ] 3.2 Review generated Docker artifacts
  - [ ] 3.3 Approve code changes
- [ ] 4. Image publishing
  - [ ] 4.1 Build container images
  - [ ] 4.2 Publish to Amazon ECR
  - [ ] 4.3 Review vulnerability scan results
- [ ] 5. Infrastructure as Code generation
  - [ ] 5.1 Select deployment target (EKS or ECS)
  - [ ] 5.2 Generate IaC (Helm charts or Terraform modules)
  - [ ] 5.3 Review generated infrastructure templates
- [ ] 6. Test deployment
  - [ ] 6.1 Deploy test infrastructure
  - [ ] 6.2 Validate application behavior
  - [ ] 6.3 Clean up test infrastructure
- [ ] 7. Production cutover
  - [ ] 7.1 Deploy cutover infrastructure
  - [ ] 7.2 Verify production deployment
  - [ ] 7.3 Confirm migration complete
```

---

## Approvals (Web UI Required)

Certain steps require manual approval through the AWS Transform web console. These are `TOOL_APPROVAL` category tasks that cannot be completed via the MCP API.

**Steps that require web UI approval:**

- Step 5: Publish images to ECR
- Step 7: Deploy test infrastructure
- Step 8: Clean up test infrastructure
- Step 9: Deploy cutover infrastructure

**How to construct the approval URL:**

The console approval URL follows this pattern:

```
<origin>/workspaces/<workspaceId>/jobs/<jobId>/approvals
```

Where:

- `<origin>` is the Transform application URL from the auth configuration (get via `get_status().fes.origin`)
- `<workspaceId>` is the current workspace ID
- `<jobId>` is the current job ID

Example:

```
https://7223639b0ed85fd08.transform.us-east-1.on.aws/workspaces/285f85b9-b109-459a-9aeb-f83542addc0b/jobs/d1800414-458b-4016-9d11-9881319a9954/approvals
```

**When presenting an approval to the user:**

1. **NEVER preemptively tell the user an approval is needed.** Only present the approval link AFTER you have confirmed the agent has actually requested it (by seeing a message containing "approval" or "approve" from the agent).
2. Call `get_status()` to get the `origin` URL
3. Construct the full URL: `<origin>/workspaces/<workspaceId>/jobs/<jobId>/approvals`
4. Present the direct link to the user
5. Tell the user which specific approval is pending (e.g., "Publish 2 images to Amazon ECR")
6. Wait for the user to confirm they've approved, or check messages to verify
7. Then check for new messages to confirm the agent has proceeded

---

## Known Limitations

- Containerization is accessed through a VMware migration job — cannot be started independently outside that context
- Individual source files must not exceed 1 GB; total source code must not exceed 8 GB
- Private dependencies require pre-configured AWS CodeArtifact repositories or private ECR base images
- EKS deployments require an existing cluster or permissions to create one
- Vulnerability scanning may flag issues that require Dockerfile modifications before proceeding
- AI-generated Dockerfiles may need manual tuning for complex multi-stage builds or non-standard application structures
- The agent handles Docker artifact generation — do not attempt manual Dockerfile creation within this workflow
- **TOOL_APPROVAL tasks cannot be approved via the MCP API.** Steps that require `TOOL_APPROVAL` (image publishing, infrastructure deployment, cleanup) must be approved in the web UI. The `complete_task` API returns `HTTP 400: TOOL_APPROVAL tasks cannot submit human artifacts` for these tasks.
