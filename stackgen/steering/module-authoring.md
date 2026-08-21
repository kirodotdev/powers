# Module Authoring — Custom Modules at AppStack Scope

## When to Create

Always. Default path — create appstack-scoped custom modules. Fall back to catalog only if user requests or publish returns 403.

## Philosophy

1. **Hide complexity, expose intent.** 3-8 variables max.
2. **Bake best practices inside.** Encryption, IAM, tagging hardcoded — not exposed.
3. **Side panel friendly.** >15 variables = too complex.
4. **Plan all upfront.** Decide all modules BEFORE creating any. Then parallel.

## Quality Rules

From `config/module-rules.yaml`:
- **V01–V09:** Variables (types, descriptions, sensitivity, count, naming)
- **O01–O03:** Outputs (descriptions, sensitive, connectable)
- **S01–S08:** stackgen.yaml (representation, variable_groups, connections)
- **T01–T10:** Structure (no providers, for_each>count, tags, formatting)
- **SEC01–SEC07:** Security (encryption default, no public access, least privilege)
- **X01–X04:** Cross-cutting (abstraction, no dead code)

## Required Files

`main.tf`, `variables.tf`, `outputs.tf`, `.stackgen/stackgen.yaml`

## Creation Flow (single execute_bash, no file writes)

**Problem:** HCL has `${...}` which zsh expands. `jq --arg` mishandles `\n` as literal chars. File writes need approvals.

**Solution:** `curl -d @- << 'JSON'` — pipe pre-formatted JSON body directly into curl via heredoc. No jq, no variables, no escaping issues. Single-quoted heredoc delimiter prevents all shell expansion.

**Cross-platform note:** This heredoc pattern requires bash (available on macOS and Linux natively). On Windows, Kiro executes commands via the system shell. If the user is on Windows:
- **Git Bash** (bundled with Git for Windows): heredocs work as-is
- **WSL**: heredocs work as-is
- **PowerShell fallback**: Use `Invoke-RestMethod` with splatting instead of curl heredocs. The JSON body should be stored in a PowerShell variable and passed with `-Body`

The agent MUST detect the user's OS (from the Kiro system prompt `Operating System` field) and use the appropriate shell syntax. On Windows without WSL/Git Bash, convert the curl heredoc pattern to:
```powershell
$body = @'
{"files":{"main.tf":"...","variables.tf":"...","outputs.tf":"...",".stackgen/stackgen.yaml":"..."}}
'@
Invoke-RestMethod -Method Put -Uri "$URL/tf-module/v1/modules/$MOD_ID/files" -Headers @{Authorization="Bearer $TOKEN";"Content-Type"="application/json"} -Body $body
```

```bash
bash << 'SCRIPT'
TOKEN=$(grep '^token:' ~/.stackgen/config.yaml | sed 's/^token: *//')
URL="https://cloud.stackgen.com"
APPSTACK_ID="<uuid>"
PID="<project-id>"

# Step 1: Create module (~1s)
MOD_ID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$URL/tf-module/v1/modules" \
  -d "{\"name\":\"<name>\",\"cloudProvider\":\"aws\",\"resourceType\":\"<type>\"}" \
  | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Step 2: Upload files via stdin heredoc (~1s) — NO jq needed
curl -s -o /dev/null -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$URL/tf-module/v1/modules/$MOD_ID/files" \
  -d @- << 'JSON'
{"files":{"main.tf":"resource \"aws_vpc\" \"main\" {\n  cidr_block = var.cidr\n  tags = { Name = \"${var.name}-vpc\" }\n}","variables.tf":"variable \"name\" {\n  type = string\n}","outputs.tf":"output \"vpc_id\" {\n  value = aws_vpc.main.id\n}",".stackgen/stackgen.yaml":"version: \"1.0\"\nrepresentation:\n  icon: aws-vpc"}}
JSON

# Step 3: Publish (~1s)
curl -s -o /dev/null -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$URL/tf-module/v1/modules/$MOD_ID/publish?overwriteVersion=true&orgId=$PID" \
  -d '{"version":"0.0.1","scope":{"type":"appstack","appstackId":"'"$APPSTACK_ID"'"}}'

echo "DONE:$MOD_ID"
SCRIPT
```

**Rules:**
- `curl -d @- << 'JSON'` — body is the heredoc itself, piped to stdin. Zero overhead.
- In the JSON heredoc: `\n` = literal two chars (what JSON wants for newlines). `\"` = escaped quote.
- Single-quoted delimiter `'JSON'` prevents bash from touching `${var.name}` inside.
- **Total time per module: ~3s** (create 1s + upload 1s + publish 1s). If slower → something is wrong.
- For multiple modules: repeat the 3-step block for each module within the same `bash << 'SCRIPT'`.
- **NO jq, NO printf, NO intermediate variables for file content.**

## API Reference

| Step | Method | Path | Body |
|---|---|---|---|
| Create | POST | `/tf-module/v1/modules` | `{"name":"..","cloudProvider":"aws","resourceType":".."}` |
| Upload | PUT | `/tf-module/v1/modules/{id}/files` | `{"files":{"main.tf":"..","variables.tf":"..","outputs.tf":"..",".stackgen/stackgen.yaml":".."}}` |
| Publish | POST | `/tf-module/v1/modules/{id}/publish?overwriteVersion=true&orgId={PID}` | `{"version":"0.0.1","scope":{"type":"appstack","appstackId":"<id>"}}` |

- Files body is MAP (not array). All 4 required. Non-empty content.
- `scope.type` = `"appstack"` (lowercase). `overwriteVersion=true` for re-publish.
- After publish: `get_supported_resource_types` (retry 3x, 500ms) → get `templateId` → `bulk_add_resources_to_appstack`

## stackgen.yaml Template

```yaml
version: "1.0"
representation:
  description: "Brief description"
  icon: aws-<resource>
  side_panel:
    label: Human Name
    icon: aws-<resource>
  node:
    label:
      static: Default Label
      template: Label - ${name}
    label_attribute: name
variables:
  name:
    label: Name
    type: string
    validation:
      required: true
variable_groups:
  - label: Basic
    variables: [name]
```

## Self-Contained Module Rule

Each module includes ALL its resources internally:
- **VPC:** VPC + subnets + IGW + NAT + route tables + associations + routes
- **ECS:** cluster + task def + service + ALB + target group + listener + SGs + IAM roles
- **RDS:** DB instance + subnet group + security group

Cross-module deps → accept as variable. Never dynamic `count` from module refs.

## Troubleshooting

| Error | Fix |
|---|---|
| 403 on publish | Catalog fallback immediately (<5s) |
| Files 400 | MAP format `{"files":{"main.tf":"..."}}` not array |
| Not in catalog after publish | `get_supported_resource_types` retry 3x/500ms |
| 409 name conflict | Append timestamp |
| resourceType empty | Ensure name is valid terraform slug |

## Pre-Module Validation

Before writing HCL:
- **RDS versions:** `aws rds describe-db-engine-versions --engine postgres` — never guess
- **Instance types:** confirm exists in target region
- **CIDR:** don't overlap existing VPCs
- **SG rules:** ALB allows 80/443 in. ECS allows from ALB SG only.
- **Routes:** Public RT → IGW. Private RT → NAT.

## Registries (research)

Use web search: `terraform {provider} {resource_type} module best practice`
URLs in `config/module-rules.yaml` → `registries` section.
