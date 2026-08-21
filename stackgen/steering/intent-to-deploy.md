# Intent to Deploy — End-to-End Flow

User sees MAX 4 messages: (1) setup confirm, (2) plan summary, (3) approval, (4) final result.

## Cross-Platform Awareness

Before executing ANY command in this flow, check the user's OS from the Kiro system prompt (`Operating System`, `Platform`, `Shell` fields). Apply the correct variant:

| Operation | macOS | Linux | Windows |
|---|---|---|---|
| Install stackgen | `brew install stackgenhq/stackgen/stackgen` | Prefer `brew install`; or `download-stackgen.sh <version> <arch>` (no `latest`) | WSL/Docker, or versioned `.exe` zip from docs/releases |
| Check command exists | `command -v stackgen` | `command -v stackgen` | `Get-Command stackgen -EA 0` |
| Read config file | `grep '^token:' ~/.stackgen/config.yaml` | Same | `Select-String '^token:' "$env:USERPROFILE\.stackgen\config.yaml"` |
| sed in-place | `sed -i '' 's/…/…/'` | `sed -i 's/…/…/'` | `(Get-Content file) -replace '…','…' \| Set-Content file` |
| Unix timestamp | `date +%s` | `date +%s` | `[DateTimeOffset]::Now.ToUnixTimeSeconds()` |
| Heredoc + curl | `bash << 'SCRIPT' ... curl -d @- << 'JSON'` | Same | PowerShell here-string: `$body = @'…'@; Invoke-RestMethod …` |
| Cleanup temp files | `rm -rf /tmp/env_config*` | Same | `Remove-Item "$env:TEMP\env_config*" -Recurse -Force` |

## Step 1: Understand App
Read Dockerfile + package.json. Map: Dockerfile → ECS+ECR, pg/prisma → RDS, HTTP → ALB, Lambda → Lambda+FunctionURL.

## Step 2: Auth
1. `stackgen version` → upgrade if needed (use OS-appropriate install method)
2. MCP `me` → if works, skip to Step 3
3. If fails: `stackgen login --url="{STACKGEN_URL}"` (NO timeout) → create PAT → set in `~/.kiro/settings/mcp.json` (or `$env:USERPROFILE\.kiro\settings\mcp.json` on Windows) → wait 5s → retry
4. `aws sts get-caller-identity` → if no creds: `aws sso login`
5. **Do NOT proceed until MCP + AWS both confirmed**

## Step 3: Confirm
> Ready to deploy. Project **X**, region **us-east-1**, env **dev**. Say "go".

## Step 4: Create AppStack
`create_appstack: name="<app>-infra-<timestamp>", cloud_provider="aws", project_name="<project>"`

## Step 5: Create Custom Modules (bash+curl, parallel)
See `module-authoring` steering. All modules created in one `execute_bash` with `&` + `wait`.
On Windows without WSL/Git Bash, use sequential PowerShell with `Invoke-RestMethod` instead of heredocs.
If 403 on publish → catalog fallback within 5s.

## Step 6: Add + Configure Resources
```
get_supported_resource_types → get template IDs
bulk_add_resources_to_appstack → all in ONE call
update_resource × N → configure silently
get_possible_resource_connections → if empty, skip
```

## Step 7: Deploy Prerequisites (silent)
1. `create_env_profile` + `update_env_profile` (state backend + variables)
2. `list-available-secrets` → find/create AWS secret
3. Attach secret + region to runner (API)
4. Create state bucket

## Step 8: Plan
`create_appstack_action_run: action_type="Plan"` — save the run ID from response.

**Polling (same as UI — every 5s):**
After triggering Plan/Apply, poll `get_action_run` every 5 seconds until terminal state:
```
Loop:
  sleep 5s
  get_action_run(action_run_id=<id>, project_name=<project>)
  Check status field:
    "pending" or "running" → continue polling
    "completed" → SUCCESS — stop polling
    "failed" → FAILED — call get_action_run_logs to get error
    "cancelled" → CANCELLED — stop polling
```
- Never poll more frequently than 5s
- On "failed": `get_action_run_logs(action_run_id, log_type="plan_stderr")` or `"init_stderr"`
- Fix once, retry once. MCP 400 → API fallback with `{"operationType":"Plan"}`

## Step 9: Plan Summary (to user)
> **Plan ready.** Will create: Network, Container service, Load balancer, Database. **Apply?**

## Step 10: Apply
`create_appstack_action_run: action_type="Apply"` — pass planRunId if via API.

## Step 11: Health Check (before telling user)
Wait 60s → `aws ecs describe-services` → `runningCount > 0`.
If 0: check events. Common: CannotPullContainer (no route), Essential container exited (bad env vars).
Fix via StackGen only.

## Step 11b: Change Record (optional)
Only if the health check passed. Resolve the script path first (workspace may be the
repo root or an app subfolder), then check setup silently:
resolve `SG_SCRIPT` with the glob-free loop in the `change-record` steering (zsh aborts on unmatched globs).
Not found, or `check-change-record-setup.sh` exits 1 → skip, no message mid-flow.
If READY: run `"$SG_SCRIPT"` with the Apply run data (`correlation_id` = Apply run ID,
`plan_stdout` = plan log). See `change-record` steering.
Never blocks: any failure here → deploy still reported as successful.

## Step 12: Result
> **Done!** App live at: `http://<alb-dns>` | [View topology]({url})
> Change record: `CHG0030002`   ← only if created; omit the line if skipped

## Step 13: Docker (if needed)
Build → `ecr get-login-password` → push → `ecs update-service --force-new-deployment` → wait healthy.

## Step 14: Cleanup
- macOS/Linux: `rm -rf /tmp/env_config* ./{uuid-dirs}/`
- Windows: `Remove-Item "$env:TEMP\env_config*" -Recurse -Force -EA 0; Get-ChildItem -Directory | Where-Object { $_.Name -match '^[0-9a-f]{8}-' } | Remove-Item -Recurse -Force`
