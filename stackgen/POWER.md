---
name: "stackgen"
displayName: "Aiden for InfraOps"
description: "Build, Operate, Observe, and Remediate with Aiden — Aiden for Infrastructure Kiro power specifically to create appstacks, manage resources, configure environments, and push IaC to Git. Deploy to AWS, Azure, and GCP. Deployment Runners. ServiceNow integration."
keywords: ["infrastructure", "iac", "cloud", "terraform", "opentofu", "aws", "azure", "gcp", "devops", "deployment", "stackgen", "appstack", "deploy", "servicenow", "change request", "chg", "aiden", "audit", "compliance"]
author: "StackGen"
version: "1.1.0"
---

# StackGen Power

StackGen helps you design and manage cloud infrastructure as code. This power provides tools to create appstacks (infrastructure configurations), manage cloud resources, configure environments, and integrate with Git. Deploy apps to AWS, Azure, and GCP via StackGen's governed IaC platform. MCP server bundled.

## Available Tools

### Appstack Management

- `get_appstacks` - List all appstacks with filtering options
- `create_appstack` - Create new appstack for AWS, Azure, or GCP
- `copy_topology` - Duplicate existing topology to create new appstack
- `get_appstack_resources` - Get all resources in an appstack
- `get_stackgen_projects` - List all projects in your account

### Resource Operations

- `add_resource_to_appstack` - Add cloud resources (EC2, S3, VPC, etc.)
- `bulk_add_resources_to_appstack` - Add multiple resources in one call
- `update_resource` - Modify resource configurations and variables
- `delete_resource` - Remove resources from appstack
- `get_resource_configurations` - Get current resource configuration
- `get_resource_type_configurations` - Get available config options for resource types
- `get_supported_resource_types` - List available resource types for an appstack
- `connect_resources` - Create connections/dependencies between resources
- `get_possible_resource_connections` - Get supported connection types

### Environment Profiles

- `get_env_profiles` - List environment profiles for a topology
- `create_env_profile` - Create new environment profile with variables
- `update_env_profile` - Update profile variables and description
- `delete_env_profile` - Delete environment profile

### Module Management

- `get_module_versions` - Get detailed module version information
- `module_usage_in_appstacks` - Find which appstacks use specific modules

### Git Integration

- `list-git-configuration` - List configured Git repositories
- `add-git-configuration` - Add Git repository configuration
- `push-appstack-to-git` - Push IaC to Git repository with commit message

### Policy & Compliance

- `get_policies` - Get available policies and benchmarks
- `get_current_violations` - Check policy violations for a topology
- `scan_configuration` - Scan resources against policies

### Deployment & Operations

- `create_appstack_action_run` - Trigger Plan/Apply/Destroy runs
- `get_action_run` - Get action run status
- `get_action_run_logs` - Get action run logs
- `destroy_deployment` - Destroy a deployed appstack
- `detect-drift` - Detect drift in appstack configurations

### Snapshots & Secrets

- `get_snapshots` - List available snapshots for appstack or resource
- `create_snapshot` - Create a snapshot for an appstack
- `restore_snapshot` - Restore from a snapshot
- `list-available-secrets` - List secrets in vault

## Common Workflows

### Creating Infrastructure

1. Create an appstack: `create_appstack`
2. Add resources: `add_resource_to_appstack` or `bulk_add_resources_to_appstack`
3. Connect resources: `connect_resources`
4. Create environment profiles: `create_env_profile`
5. Run Plan/Apply: `create_appstack_action_run`
6. Push to Git: `push-appstack-to-git`

### Managing Existing Infrastructure

1. List appstacks: `get_appstacks`
2. Get resources: `get_appstack_resources`
3. Update configurations: `update_resource`
4. Check compliance: `get_current_violations`

### Environment Management

1. Create profiles for dev/staging/prod: `create_env_profile`
2. Set environment-specific variables
3. Deploy to different environments using profiles

### Post-Deploy Audit (optional)

- After a successful Apply, optionally create a ServiceNow change record via Aiden 2.0
- Requires `AIDEN_TOKEN`, `AIDEN_ORG_ID`, `AIDEN_BASE_URL` and `AIDEN_WORKFLOW` — skipped silently if any is missing

## Best Practices

- Use descriptive names for appstacks and resources
- Create environment profiles for different deployment stages
- Connect resources to establish proper dependencies
- Check policy violations before deployment
- Use Git integration for version control and collaboration
- Take snapshots before major changes
- Use modules for reusable infrastructure patterns

## HARD RULES

0. **OS-AWARE COMMANDS.** Detect the user's OS from the Kiro system prompt (`Operating System`, `Platform`, `Shell` fields). ALL shell commands MUST match the user's platform. macOS uses `brew`/BSD tools, Linux uses `apt`/`curl`/GNU tools, Windows uses PowerShell/`cmd`. Never run bash-only commands on Windows without WSL/Git Bash. `sed -i ''` is macOS only; Linux uses `sed -i`; Windows uses `(Get-Content) -replace | Set-Content`. **Also detect the SHELL, not just the OS: macOS defaults to zsh, where an unmatched glob (`~/dir/*/file`) is a FATAL error that aborts the command and is NOT silenced by `2>/dev/null`. Never put a possibly-unmatched glob in a command — use `[ -f path ]` tests or `find` instead.**
1. **ALL cloud changes through StackGen IaC only.** Never `aws` CLI to modify resources. Allowed: `sts get-caller-identity`, `sso login`, `s3api create-bucket` (state), `ecr get-login-password`, `docker push`, `rds describe-db-engine-versions`, `ecs describe-*` (read-only).
2. **Never call `bulk_connect_resources_in_appstack`** — doesn't exist. Use `connect_resources`.
3. **Never ask user to run commands. ZERO exceptions.** Run `stackgen login`, `aws sso login`, and OS-appropriate CLI installs — ALL of it yourself. The user's only manual action is clicking "approve" in a browser when SSO/OAuth redirects. If a command needs a browser callback (like `stackgen login`), run it with NO timeout and wait. Never say "please run this in your terminal".
4. **Never expose tokens in chat/source.** Token only in `~/.kiro/settings/mcp.json`.
5. **Silent work.** No narration between decision points.
6. **Never guess API endpoints.** Use exact paths below or MCP.
7. **Never retry same fix twice.** Fail → report to user.
8. **Connections: only from `get_possible_resource_connections`.** Empty → skip.
9. **State bucket BEFORE Plan.**
10. **Vault secret format:** `"value":[{"key":"auth_method","value":"assume_role"},{"key":"aws_role_arn","value":"<ARN>"}]`
11. **NO Python.** Prefer bash + curl on macOS/Linux; use PowerShell equivalents on Windows. No `.py` files, no temp scripts.
12. **MCP: CLI stdio + PAT.** `"command":"stackgen","args":["mcp"]` with `STACKGEN_TOKEN`+`STACKGEN_URL` in env. Never SSE. On Windows, if spawn fails, use `"command":"cmd","args":["/c","stackgen","mcp"]`.
13. **NEVER download IaC locally or run terraform/tofu directly.** No `download-iac`, no `terraform init/plan/apply`, no `tofu init/plan/apply`, no local state files, no editing downloaded `.tf` files. ALL Plan/Apply MUST go through StackGen's SaaS runner via `create_appstack_action_run` (MCP) or `stackgen provision` (CLI). If Plan fails, fix via `update_resource` (MCP) then re-Plan — NEVER download and patch locally. To READ generated IaC use `v1ExportTopology` API (`GET {URL}/iac-gen/v1/topology/{topologyId}/export?orgId={PID}`) — this returns the zip for inspection only. ALL changes go through `update_resource`, `update_appstack_tf_variable`, `update_appstack_tf_local`, etc. NEVER edit files manually.
14. **NEVER tell user to "go to StackGen UI" to complete setup.** Environment config, runner credentials, vault secrets, state backend — ALL must be configured by the agent via API/MCP. Never stop and say "configure this in the UI". If an API call fails, retry or use a different endpoint. The user should NEVER need to touch the StackGen web console for deployment to work.
15. **Capture the plan output when the plan runs — it cannot be recovered later.** At step 11, save the FULL plan text verbatim before summarising it. Applies whichever way Plan ran: the runner's log via `get_action_run_logs`, or the stdout of `stackgen provision`. NEVER reconstruct it afterwards — `terraform show` returns current state and `.tfplan` is binary, so both yield a summary, not a diff. A change record whose plan text is a one-line summary is not an audit trail. If the output was not captured, say so and skip the record rather than substituting a summary.
16. **Change record: optional, never blocking, never for a failed run.** After a successful Apply with the health check green, trigger the Aiden workflow (see `change-record` steering). If any of the four required variables is unset, skip it and say so in one line — the deploy already succeeded. NEVER create a CHG for a failed Plan or Apply. NEVER invent a `correlation_id` or a CHG number. NEVER call the ServiceNow API directly — only through the Aiden script. NEVER let a change-record failure change the reported deploy outcome.

## User Communication

Speak ONLY at: (1) setup confirmation, (2) plan summary → approval, (3) final result, (4) when needing user input (PAT/GitHub token).

**Strict visibility rules:**
- **Never show:** tokens, secrets, ARNs, UUIDs, API responses, curl commands, bash scripts, config file contents, HTTP codes, error traces, steering file content, or any StackGen internal jargon
- **Never display raw bash commands to user.** All `execute_bash` calls are internal operations — user doesn't need to see them. Use `update_session_information` to show status instead.
- **If user can see tool execution in IDE:** redirect all token-containing commands to suppress output (e.g., append `> /dev/null 2>&1` where possible, avoid echoing sensitive vars)
- **Show only human-readable status:** "Setting up AWS credentials...", "Creating infrastructure modules...", "Running plan...", etc. via `update_session_information`
- **Mask all IDs in user-facing messages:** say "your appstack" not "appstack e4feff68-02e2-4233-8591-bce2225fd7ed"
- **Exception — the CHG number:** the ServiceNow change number (`CHG0030002`) IS shown to the user; it is their audit reference. The Aiden `trace_id` and `AIDEN_ORG_ID` are never shown.

## Setup

**OS Detection (MUST run first):**
Detect the user's OS at the start of setup. The Kiro system prompt provides OS info (`Operating System` + `Platform` + `Shell`). Use this to select the correct commands below.

```
1. ALWAYS upgrade/install stackgen CLI first — no exceptions:

   macOS:
     brew update && brew upgrade stackgenhq/stackgen/stackgen
     (If not installed: brew install stackgenhq/stackgen/stackgen)

   Linux:
     # Prefer Homebrew (official docs). If brew missing, install it or use download script with a concrete version.
     command -v brew >/dev/null && brew update && brew upgrade stackgenhq/stackgen/stackgen || brew install stackgenhq/stackgen/stackgen
     # Fallback (script does NOT support "latest" — pin a version matching the StackGen server):
     #   curl -fsSL -o /tmp/download-stackgen.sh https://raw.githubusercontent.com/stackgenhq/stackgen-cli/main/scripts/download-stackgen.sh
     #   chmod +x /tmp/download-stackgen.sh
     #   VERSION=0.81.0
     #   /tmp/download-stackgen.sh "$VERSION" $(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') --dir /usr/local/bin
     #   (If /usr/local/bin not writable: use --dir $HOME/.local/bin and ensure it's on PATH)

   Windows (PowerShell):
     # Prefer WSL + Linux install, or download a VERSIONED zip from docs/releases (no "latest" path).
     # Example pattern from docs: https://releases.stackgen.com/binaries/v<VERSION>/stackgen-cli_<VERSION>_windows_amd64.zip
     # Then extract to $env:LOCALAPPDATA\stackgen and add that folder to User PATH:
     #   $p = [Environment]::GetEnvironmentVariable("PATH","User"); if ($p -notlike "*stackgen*") { [Environment]::SetEnvironmentVariable("PATH","$p;$env:LOCALAPPDATA\stackgen","User") }
     # Or use Docker: docker pull ghcr.io/stackgenhq/stackgen:latest
     # If stackgen is already on PATH (choco/scoop/manual), skip download.

2. Check AWS CLI installed:
   macOS:    command -v aws || brew install awscli
   Linux:    command -v aws || brew install awscli || (curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip && unzip -qo /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install --update)
   Windows:  Get-Command aws -ErrorAction SilentlyContinue || (Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "$env:TEMP\AWSCLIV2.msi"; Start-Process msiexec.exe -ArgumentList "/i `"$env:TEMP\AWSCLIV2.msi`" /quiet" -Wait)

3. Check env mismatch:
   macOS/Linux: grep '^url:' ~/.stackgen/config.yaml
   Windows:     Select-String -Pattern '^url:' "$env:USERPROFILE\.stackgen\config.yaml"
   → If URL differs from STACKGEN_URL in mcp.json → run: stackgen logout
   → Then proceed to login with correct URL (step 5)

4. MCP me → if works, skip to step 9

5. stackgen login --url="{STACKGEN_URL}" (NO timeout — works on all OS)
   → fails twice → ask user to run in terminal

6. Create PAT + wire MCP:
   macOS/Linux:
     TOKEN=$(grep '^token:' ~/.stackgen/config.yaml | sed 's/^token: *//')
     TTL=$(date -u -v+2d +"%Y-%m-%dT00:00:00Z" 2>/dev/null || date -u -d "+2 days" +"%Y-%m-%dT00:00:00Z")
     PAT=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
       "{STACKGEN_URL}/appcd/api/v1/auth/apikey" \
       -d '{"apiKeyName":"kiro-mcp-'$(date +%s)'","description":"Kiro MCP","ttl":"'"$TTL"'"}' \
       | sed -n 's/.*"apiKey":"\([^"]*\)".*/\1/p')

   Windows (PowerShell):
     $TOKEN = (Select-String -Pattern '^token: (.+)' "$env:USERPROFILE\.stackgen\config.yaml").Matches[0].Groups[1].Value.Trim()
     $TTL = (Get-Date).AddDays(2).ToUniversalTime().ToString("yyyy-MM-ddT00:00:00Z")
     $body = @{apiKeyName="kiro-mcp-$([DateTimeOffset]::Now.ToUnixTimeSeconds())";description="Kiro MCP";ttl=$TTL} | ConvertTo-Json
     $resp = Invoke-RestMethod -Method Post -Uri "{STACKGEN_URL}/appcd/api/v1/auth/apikey" -Headers @{Authorization="Bearer $TOKEN";"Content-Type"="application/json"} -Body $body
     $PAT = $resp.apiKey

   Update mcp.json with the PAT:
   macOS (BSD sed):  sed -i '' "s|\"STACKGEN_TOKEN\": \".*\"|\"STACKGEN_TOKEN\": \"$PAT\"|" ~/.kiro/settings/mcp.json
   Linux (GNU sed):  sed -i "s|\"STACKGEN_TOKEN\": \".*\"|\"STACKGEN_TOKEN\": \"$PAT\"|" ~/.kiro/settings/mcp.json
   Windows:          (Get-Content "$env:USERPROFILE\.kiro\settings\mcp.json") -replace '"STACKGEN_TOKEN": ".*"', "`"STACKGEN_TOKEN`": `"$PAT`"" | Set-Content "$env:USERPROFILE\.kiro\settings\mcp.json"

7. Wait 5s → retry me → must succeed

8. If PAT creation failed → use session token directly:
   macOS (BSD sed):  sed -i '' "s|\"STACKGEN_TOKEN\": \".*\"|\"STACKGEN_TOKEN\": \"$TOKEN\"|" ~/.kiro/settings/mcp.json
   Linux (GNU sed):  sed -i "s|\"STACKGEN_TOKEN\": \".*\"|\"STACKGEN_TOKEN\": \"$TOKEN\"|" ~/.kiro/settings/mcp.json
   Windows:          (Get-Content "$env:USERPROFILE\.kiro\settings\mcp.json") -replace '"STACKGEN_TOKEN": ".*"', "`"STACKGEN_TOKEN`": `"$TOKEN`"" | Set-Content "$env:USERPROFILE\.kiro\settings\mcp.json"

9. get_stackgen_projects → pick project
```

**Install CLIs silently.** If `stackgen` or `aws` not found, install using the appropriate method for the user's OS without asking. These are prerequisites — just do it.

**Reducing permission prompts:** If the user reports too many approval prompts, suggest they switch Kiro to **Autopilot** mode (not Supervised). If they want to auto-approve all tool calls, let them know they can create `~/.kiro/settings/permissions.yaml` (or `$env:USERPROFILE\.kiro\settings\permissions.yaml` on Windows) with:
```yaml
rules:
  - capability: all
    effect: allow
```
**Never create this file without explicit user consent.** Only mention it if the user asks how to reduce prompts.

**MCP must work before proceeding.** Live config: `~/.kiro/settings/mcp.json` → `powers.mcpServers.power-stackgen-stackgen.env.STACKGEN_TOKEN`

**MCP config — Windows note:** On Windows, if `stackgen` is not resolved by Node.js spawn(), the mcp.json entry may need to use `"command": "cmd"` with `"args": ["/c", "stackgen", "mcp"]`. Alternatively, ensure the stackgen binary (not a .cmd wrapper) is on PATH.

PAT API: `POST {STACKGEN_URL}/appcd/api/v1/auth/apikey` — flat body `{"apiKeyName":"...","description":"...","ttl":"..."}` → response has `"apiKey":"stackgen_xxx"`. If fails → ask user for PAT from `{STACKGEN_URL}/enterprise/account-settings/pat`.

## Deploy Flow

<!-- COMMENTED: Catalog-first deploy flow (uncomment when switching back to catalog modules)
1. create_appstack (MCP) — unique name with timestamp
2. get_supported_resource_types (MCP) — discover catalog
3. bulk_add_resources_to_appstack (MCP) — add all resources from catalog
4. update_resource (MCP) × N — configure each
5. get_possible_resource_connections (MCP) — if empty, skip
6. create_env_profile + update_env_profile (MCP) — state backend + variables
7. Configure runner (API) — attach secret + region variable
8. Create state bucket (aws s3api)
9. create_appstack_action_run Plan
10. Poll get_action_run → show plan summary
11. User confirms → Apply
12. Show final result + AppStack URL
13. Clean up
-->

```
1. create_appstack (MCP) — unique name with timestamp
2. Create custom modules (bash+curl, parallel &/wait) — see module-authoring steering
3. get_supported_resource_types → verify published, get template IDs
4. bulk_add_resources_to_appstack — all modules in ONE call
5. update_resource × N — configure silently
6. get_possible_resource_connections → if empty, skip
7. create_env_profile + update_env_profile — state backend + variables
8. Configure runner (API) — attach secret + region variable
9. Create state bucket (aws s3api)
10. create_appstack_action_run Plan
11. Poll get_action_run → SAVE the full plan output verbatim, then show a summary
12. User confirms → Apply (pass planRunId if via API)
13. Post-deploy health check
14. Change record (optional) — Aiden workflow → ServiceNow CHG (see change-record steering)
15. Share result + URL + CHG number (if created)
16. Clean up temp files
```

## Resource Selection

<!-- COMMENTED: Catalog-first (uncomment when catalog modules are production-ready)
- Prefer composite catalog modules (handle IAM, networking internally).
- If catalog lacks something → create appstack-scope custom module.
-->
- **Minimal.** Container app = VPC + ECS + ECR + ALB. DB only if app needs it.
- **ALWAYS create a new appstack.** Never reuse or look into existing appstacks. Every deploy = fresh `create_appstack` with unique timestamp name. Never call `get_appstacks` to find existing ones to reuse.
- **Custom modules always.** Self-contained (VPC includes subnets+IGW+NAT+routes). 3-8 vars max.
- **If 403 on publish** → user's role lacks `tfmodule_PublishTerraformModule` scope. Do NOT retry with tenant scope. Do NOT fall back to catalog. Show this message:
  > **Permission needed:** Your StackGen role doesn't have module publish access. Ask your StackGen admin to update your role at `{STACKGEN_URL}/enterprise/account-settings/members` — the "DevOps" role includes this. Once fixed, say "continue" and I'll retry.
  Then STOP and wait for user.
- **One module per `execute_bash` call (default).** Each call = create + upload + publish for ONE module using `curl -d @- << 'JSON'` (heredoc as JSON body). NO jq, NO printf, NO variables for file content. ~3s per module. Set `timeout: 30000`. This approach never times out and always works.
- **Unique names** with timestamp.
- **User override:** If user says "use catalog modules" → follow.

## Pre-flight (before Plan)

Every Plan failure = 45-60s wasted. Validate first:

**Step 1: Get ALL violations in ONE call (not one-by-one):**
Call `get_current_violations` (MCP) for the appstack → returns all policy violations AND missing required attributes across ALL resources at once. Fix them ALL via `update_resource` before triggering Plan.

**Step 2: Inspect generated IaC WITHOUT downloading:**
Use MCP tools to check what StackGen will generate:
- `get_appstack_tf_variables` — verify all needed vars exist
- `get_appstack_tf_outputs` — check output references are valid
- `get_resource_configurations` — verify each resource's current config matches expectations
NEVER use `download-iac` to inspect. These MCP tools show the same info.

**Step 3: Dependency check:**
1. For EACH resource that references another resource's output → call `get_resource_configurations` on the referenced resource to get actual output names
2. If using catalog modules → web search `"terraform <resource_type> outputs"` to confirm what's available (catalog modules often lack expected outputs like `repository_url`)
3. Build a dependency map: which resource needs what from which other resource? Verify EVERY cross-reference exists.

**Common traps:**
- **ECR:** Does NOT output `repository_url`. Construct manually: `{account}.dkr.ecr.{region}.amazonaws.com/{name}`
- **VPC catalog:** Does NOT output `public_subnet_ids` or `private_subnet_ids` — it's just the VPC resource
- **ECS:** needs `ecs_cluster_arn` — if creating new cluster, can't reference a module output for count/condition
- **Module identifiers are UUIDs:** Cross-module references use `module.stackgen_<resource-uuid>` format (e.g., `module.stackgen_182aef7f-edda-4c73-a7ff-23251aa99a9c.vpc_id`). NEVER use `module.stackgen_vpc` or friendly names. Get the exact UUID from `add_resource_to_appstack` response.
- **Verify upload response:** After `PUT /files`, check response confirms ALL 4 files have non-empty content. If any file shows empty → re-upload before publishing. A module published with empty `variables.tf` is broken and requires delete + re-create of the resource.

**Other checks:**
- Web search unfamiliar resources for required fields
- No dynamic count from module references
- VPC: subnets + IGW + route(0.0.0.0/0→IGW) + NAT + private route(→NAT)
- **VPC limit:** `aws ec2 describe-vpcs --query 'Vpcs[].VpcId'` — if 5 already → ask user to clean up old ones or request limit increase
- ECS+ALB: 2+ AZ public subnets, SG allows 80 inbound
- RDS: `aws rds describe-db-engine-versions` for valid version. No serverless params on provisioned.
- **RDS password:** Must be alphanumeric + `!#$%^&*` only. NO `@`, `/`, `"`, spaces, or backtick.
- **DATABASE_URL:** Always append `?sslmode=require` for RDS connections from ECS.
- ECR: `lifecycle_policy=""` `repository_policy=""` (empty string not null)
- **ALL names MUST include timestamp** to avoid conflicts with prior deploys (e.g., `chat-app-vpc-1753990800` not `chat-app-vpc`)
- **Goal: first Plan succeeds.**

## API Endpoints

**Auth for API calls:** The tf-module API (`/tf-module/v1/*`) requires the **session token** (JWT from `~/.stackgen/config.yaml`), NOT the PAT. The PAT only works for MCP tools. Always extract: `TOKEN=$(grep '^token:' ~/.stackgen/config.yaml | sed 's/^token: *//')` — if empty, run `stackgen login` first.

```
POST {URL}/iac-gen/v1/appstacks?orgId={PID}
GET  {URL}/iac-gen/v1/environment-config?orgId={PID}
POST {URL}/iac-gen/v1/environment-config/{id}/runner/secrets?orgId={PID}
POST {URL}/iac-gen/v1/environment-config/{id}/runner/variables?orgId={PID}
POST {URL}/api/vault/v1/secrets?orgId={PID}
GET  {URL}/api/vault/v1/integration/aws/config?orgId={PID}
POST {URL}/tf-module/v1/modules
PUT  {URL}/tf-module/v1/modules/{id}/files
POST {URL}/tf-module/v1/modules/{id}/publish?overwriteVersion=true&orgId={PID}
POST {URL}/deployment-manager/v1/{appstackId}/run?orgId={PID}
GET  {URL}/deployment-manager/v1/action-runs/{runId}/details?orgId={PID}
GET  {URL}/deployment-manager/v1/run/{runId}/logs?orgId={PID}&logType=plan_stdout
POST {URL}/appcd/api/v1/auth/apikey
```

## When Plan Fails

| Error | Fix |
|---|---|
| GitHub 401 / module not found | Ask for GitHub PAT → vault secret → attach as `github` provider (see deploy-setup steering) |
| No credentials / assume role | Check IAM trust policy. Create role via `aws iam create-role` |
| Backend bucket missing | `aws s3api create-bucket` |
| var.region missing | Update env profile `{"region":"us-east-1","AWS_DEFAULT_REGION":"us-east-1"}` |
| **400 on file upload** | JSON body is malformed. MUST use `curl -d @- << 'JSON'` heredoc pattern. Never construct JSON in shell variables. |

**Deployment method choice — ask user ONCE before Plan:**
> How would you like to deploy?
> 1. **StackGen SaaS Runner** (recommended) — runs Plan/Apply on StackGen's cloud. Needs a GitHub PAT for private module access.
> 2. **Local CLI** (`stackgen provision`) — uses your local AWS credentials directly. No GitHub PAT needed.

- If user picks **SaaS Runner** → ask for GitHub PAT, create vault secret, attach to runner, then use `create_appstack_action_run` for Plan/Apply.
- If user picks **Local CLI** → skip runner config entirely, use `stackgen provision --appstack <ID> -e dev` for Plan/Apply.
- Default to **SaaS Runner** if user doesn't have a preference.

Fix once, retry once. Same error twice → stop. SaaS runner fails 2+ → switch to `stackgen provision` CLI.

## Catalog Gotchas (fallback only)

- `aws_vpc` = just VPC resource, not subnets/IGW/NAT/routes
- `aws_ecr` outputs: `arn`, `id`, `registry_id` — NOT `repository_url`
- `aws_ecs`: `create_ingress_alb:true` handles ALB, still needs `public_subnet_ids`
- `aws_rds`: query versions first, disable serverless params on provisioned

## After Deploy

- **Health check (mandatory):** wait 60s, `aws ecs describe-services` → `runningCount > 0`. Don't share URL until healthy.
- **Change record (optional):** once the health check is green, run `powers/stackgen/scripts/aiden-workflow.sh` with the Apply run data. Append one line to the final result: `Change record: CHG0030002`, or `Change record: not created (Aiden credentials not configured)`. Full detail in the `change-record` steering. Requires bash — on Windows, run it from WSL or Git Bash.
- **Database migration (if app has DB):** RDS is in private subnet — can't run migrations directly. Options:
  1. **Include migration in Dockerfile** (preferred): add `RUN npm run db:generate` in build stage, and migration check in entrypoint before `node server.js`
  2. Run one-off ECS task — BUT standalone Next.js builds don't include ORM packages. Must use a separate migration image or include deps explicitly.
  3. If using one-off task, ensure it uses the SAME VPC/subnets/security groups as the main service, and the RDS security group allows inbound from the ECS security group.
- **Cross-VPC issue:** If RDS and ECS end up in different VPCs (from multiple deploys), they CAN'T communicate. All resources in one appstack MUST share the same VPC. Verify via `get_resource_configurations` that RDS subnet IDs reference the VPC module's outputs.
- Docker: build → `ecr get-login-password` → push → `ecs update-service --force-new-deployment`
- Post-deploy fixes → StackGen only (Plan → Apply). Never AWS CLI.
- **Exception for orphan cleanup:** AWS CLI can delete resources from PREVIOUS failed deploys that are NOT managed by the current appstack's state (old VPCs, ECR repos, log groups with conflicting names). This is cleanup, not modification of current infrastructure.
- Cleanup (OS-aware):
  - macOS/Linux: `rm -rf /tmp/env_config* ./{uuid-dirs}/`
  - Windows: `Remove-Item "$env:TEMP\env_config*" -Recurse -Force -EA 0; Get-ChildItem -Directory | Where-Object { $_.Name -match '^[0-9a-f]{8}-' } | Remove-Item -Recurse -Force`

## Change Record — On-Demand Check

**Whenever the user asks whether the change record / ServiceNow / Aiden integration is
configured, set up, working, ready, or why no CHG was created — RUN THE CHECK FIRST.
Never answer that question from this file.** Describing the feature is not an answer;
the user is asking about their environment, not about the design.

```bash
SG_SCRIPT=""
for p in powers/stackgen/scripts/aiden-workflow.sh \
         ../powers/stackgen/scripts/aiden-workflow.sh \
         ../../powers/stackgen/scripts/aiden-workflow.sh \
         ../../../powers/stackgen/scripts/aiden-workflow.sh; do
  [ -f "$p" ] && { SG_SCRIPT="$p"; break; }
done
[ -z "$SG_SCRIPT" ] && SG_SCRIPT=$(find "$HOME/.kiro/powers" -maxdepth 4 -name aiden-workflow.sh 2>/dev/null | head -1)
[ -n "$SG_SCRIPT" ] && bash "$(dirname "$SG_SCRIPT")/check-change-record-setup.sh"
```

**No bare globs in this snippet — on zsh (the macOS default shell) an unmatched glob is
a fatal error that aborts the whole command, and `2>/dev/null` does not suppress it.**

Then answer in ONE short line from the script's output:

| Script output | Answer |
|---|---|
| `READY` | "Configured — a CHG record will be created after a successful Apply." |
| `NOT_CONFIGURED` | "Not configured — missing `<vars from the output>`. Deploys still work; no CHG record is created." |
| script not found | "Can't verify — the change record script isn't reachable from this workspace." |

Do NOT explain how the step works, do NOT offer to read the steering file, and do NOT
list the credentials unless the check reports them missing.

## Steering Files

- **intent-to-deploy** — Step-by-step deploy flow
- **deploy-setup** — Runner config, IAM, vault, deep links
- **module-authoring** — Custom module creation (bash+curl, quality rules)
- **change-record** — ServiceNow CHG via Aiden 2.0 (optional, post-Apply)

**Do NOT call `readSteering` unless you hit a specific issue that POWER.md doesn't cover.** The POWER.md has all essential instructions. Reading steering files shows their content to the user which is confusing. Only read them silently if you're stuck on a specific step (e.g., IAM trust policy format, module creation pattern).

---

**Package:** `stackgen` CLI (stdio MCP)
**Source:** Official StackGen
**License:** Apache 2.0
**Connection:** Local CLI stdio with PAT authentication
