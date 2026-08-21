# Deploy Setup — Runner Config & Prerequisites

All agent-driven. User only approves browser for SSO.

## Cross-Platform Notes

Commands in this file default to bash (macOS/Linux). On Windows, use these substitutions:

| Unix Command | Windows (PowerShell) Equivalent |
|---|---|
| `grep '^token:' ~/.stackgen/config.yaml \| sed 's/^token: *//'` | `(Select-String -Pattern '^token: (.+)' "$env:USERPROFILE\.stackgen\config.yaml").Matches[0].Groups[1].Value.Trim()` |
| `curl -s -H "Authorization: Bearer $TOKEN" "$URL"` | `Invoke-RestMethod -Uri $URL -Headers @{Authorization="Bearer $TOKEN"}` |
| `curl -s -X POST -H "..." -d '...' "$URL"` | `Invoke-RestMethod -Method Post -Uri $URL -Headers @{...} -Body $json` |
| `echo "$VAR" \| grep -o '"id":"[^"]*"' \| head -1 \| cut -d'"' -f4` | `($resp.id)` (PowerShell auto-parses JSON from Invoke-RestMethod) |
| `aws sts get-caller-identity` | Same (AWS CLI is cross-platform) |
| `~/.stackgen/config.yaml` | `$env:USERPROFILE\.stackgen\config.yaml` |

**Shell requirement:** The bash blocks below require bash or a POSIX shell. On Windows, these run automatically via Git Bash (bundled with Git for Windows) or WSL. Kiro's execute_bash uses the system's configured shell.

## Runner Configuration (before Plan)

**The StackGen SaaS runner needs project-level environment config. If `GET /iac-gen/v1/environment-config?orgId={PID}` returns empty items, CREATE it first.**

### 0. Create Environment Config (if doesn't exist)
```bash
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$STACKGEN_URL/iac-gen/v1/environment-config?orgId=$PROJECT_ID")
# If items array is empty → create:
CONFIG=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$STACKGEN_URL/iac-gen/v1/environment-config?orgId=$PROJECT_ID" \
  -d '{"name":"default","environmentTemplates":[{"name":"dev","color":"green"}]}')
# Extract: CONFIG_ID and ENV_TEMPLATE_ID from response
```

### 1. AWS session
```bash
aws sts get-caller-identity || aws sso login
```

### 2. Integration config
```bash
curl -s -H "Authorization: Bearer $TOKEN" "$STACKGEN_URL/api/vault/v1/integration/aws/config?orgId=$PROJECT_ID"
```
Returns: `roleArn`, `externalId`, `trustPolicy`

### 3. IAM role (if not exists)

**CRITICAL: Trust policy MUST have TWO statements — AssumeRole AND TagSession (separate statements, NOT combined)**

```bash
# Get integration config first
INTEGRATION=$(curl -s -H "Authorization: Bearer $TOKEN" "$STACKGEN_URL/api/vault/v1/integration/aws/config?orgId=$PROJECT_ID")
BASTION_ROLE=$(echo "$INTEGRATION" | grep -o '"roleArn":"[^"]*"' | cut -d'"' -f4)
EXTERNAL_ID=$(echo "$INTEGRATION" | grep -o '"externalId":"[^"]*"' | cut -d'"' -f4)

# Create role with CORRECT trust policy (both AssumeRole + TagSession)
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "'$BASTION_ROLE'" },
      "Action": "sts:AssumeRole",
      "Condition": { "StringEquals": { "sts:ExternalId": "'$EXTERNAL_ID'" } }
    },
    {
      "Effect": "Allow",
      "Principal": { "AWS": "'$BASTION_ROLE'" },
      "Action": "sts:TagSession"
    }
  ]
}'

aws iam get-role --role-name stackgen-aws-integration 2>/dev/null || \
aws iam create-role --role-name stackgen-aws-integration --assume-role-policy-document "$TRUST_POLICY"

# NOTE: AdministratorAccess is used here for demo/dev simplicity.
# For production, scope down to only the permissions your infrastructure requires.
# At minimum: EC2, ECS, ECR, RDS, S3, VPC, ELB, IAM (for service roles), CloudWatch, Route53.
aws iam attach-role-policy --role-name stackgen-aws-integration --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
ROLE_ARN=$(aws iam get-role --role-name stackgen-aws-integration --query 'Role.Arn' --output text)
```

**If role already exists** → update trust policy: `aws iam update-assume-role-policy --role-name stackgen-aws-integration --policy-document "$TRUST_POLICY"`

### 4. Vault secret
```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$STACKGEN_URL/api/vault/v1/secrets?orgId=$PROJECT_ID" \
  -d '{"name":"aws-deploy-credentials","description":"AWS assume role","category":"Cloud","subcategory":"aws","value":[{"key":"auth_method","value":"assume_role"},{"key":"aws_role_arn","value":"'"$ROLE_ARN"'"}],"shareWithTenant":true}'
```

### 5. Env config + runner attach
```bash
# Get config ID
CONFIG_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$STACKGEN_URL/iac-gen/v1/environment-config?orgId=$PROJECT_ID" \
  | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
ENV_TEMPLATE_ID=$(curl -s -H "Authorization: Bearer $TOKEN" "$STACKGEN_URL/iac-gen/v1/environment-config?orgId=$PROJECT_ID" \
  | grep -o '"environmentTemplates":\[{"id":"[^"]*"' | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Attach secret
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$STACKGEN_URL/iac-gen/v1/environment-config/$CONFIG_ID/runner/secrets?orgId=$PROJECT_ID" \
  -d '[{"provider":"aws","values":[{"environmentTemplateId":"'"$ENV_TEMPLATE_ID"'","value":"'"$SECRET_ID"'"}]}]'

# Add region
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$STACKGEN_URL/iac-gen/v1/environment-config/$CONFIG_ID/runner/variables?orgId=$PROJECT_ID" \
  -d '[{"key":"AWS_DEFAULT_REGION","values":[{"environmentTemplateId":"'"$ENV_TEMPLATE_ID"'","value":"us-east-1"}]}]'
```

### 6. State bucket
```bash
BUCKET="<appstack-name>-state"
aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null || {
  aws s3api create-bucket --bucket "$BUCKET" --region us-east-1
  aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
}
```

### 7. State backend (MCP)
```
update_env_profile: profile_name="dev"
  variables: {"region":"us-east-1","AWS_DEFAULT_REGION":"us-east-1"}
  state_backend_raw_hcl: terraform { backend "s3" { bucket="<bucket>" key="<appstack>/terraform.tfstate" region="us-east-1" encrypt=true } }
```

## CLI Fallback: stackgen provision

If SaaS runner fails 2+ times (credential/signing errors), use local CLI:
```bash
# MUST set project context first
stackgen login --url="{STACKGEN_URL}" --project="<PROJECT_ID>"
# Then provision (uses local AWS creds)
stackgen provision --appstack <APPSTACK_ID> -e dev
# For apply:
stackgen provision --appstack <APPSTACK_ID> -e dev --apply
```

## GitHub Module Access (if Plan fails: module not found)

Custom modules from private repos need a GitHub PAT as runner secret.

Ask user with clear explanation:
> **GitHub token needed for deployment.** StackGen's cloud runner pulls your Terraform modules from GitHub during Plan/Apply. Without a token, it can't access private module repositories and the plan will fail with "module not found".
>
> Please create a GitHub Personal Access Token:
> 1. Go to [https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)
> 2. Click **"Generate new token"**
> 3. Name it something like "stackgen-runner"
> 4. Under **Repository access**, select "All repositories" (or specific repos containing your Terraform modules)
> 5. Under **Permissions → Repository permissions**, grant **Contents: Read-only**
> 6. Click **Generate token** and paste it here
>
> This token is stored securely in StackGen's vault and only used by the runner during Plan/Apply.

Then:
1. Vault secret: `{"name":"github-modules","category":"SCM","subcategory":"github","value":[{"key":"token","value":"<PAT>"}],"shareWithTenant":true}`
2. Attach: `[{"provider":"github","values":[{"environmentTemplateId":"<id>","value":"<secret_id>"}]}]`
3. Retry Plan

## UI Deep Links

| Page | URL |
|---|---|
| AppStack | `{URL}/project/{name}/appstacks/{id}` |
| Secret Store | `{URL}/project/{name}/secret-store` |
| Env Config | `{URL}/project/{name}/project-settings?tab=environment-configuration` |
| Runner Secrets | `{URL}/project/{name}/project-settings?tab=environment-configuration&env-tab=secrets` |
| CLI Runs | `{URL}/project/{name}/cli-runs` |
| PAT Tokens | `{URL}/enterprise/account-settings/pat` |
