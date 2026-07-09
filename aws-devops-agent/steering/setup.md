---
description: Setup diagnostics, onboarding, and troubleshooting for the AWS DevOps Agent power
alwaysApply: false
---

# AWS DevOps Agent — Setup & Diagnostics

Use this file when a user needs help setting up, diagnosing connection issues, or troubleshooting the DevOps Agent power.

---

## Step 1: Diagnose current setup

### 1a. Check environment variables

```bash
echo "DEVOPS_AGENT_TOKEN: $([ -n "$DEVOPS_AGENT_TOKEN" ] && echo 'set' || echo 'not set')"
echo "DEVOPS_AGENT_REGION: ${DEVOPS_AGENT_REGION:-not set}"
```

### 1b. If token and region are set, verify connectivity

Call `get_agent_space` to confirm the bearer path is live.

### 1c. Check SigV4 readiness

- `uvx --version` — proxy dependency present
- `aws sts get-caller-identity` — credentials valid

After checking, report which paths are configured and functional.

### Routing after diagnosis

- **Either path works** → Suggest next actions (chat, investigate). SigV4 takes priority if both are configured.
- **Prerequisites met but server not connected** → Ask user to check their MCP configuration for errors before falling back to `aws-mcp`.
- **Neither path configured** → Ask whether they want to connect via bearer token or AWS profile, then follow the relevant option below.

---

## Option A — Bearer Token Setup

### 1. Get a token
1. Open the AWS DevOps Agent **Operator Web App** for the desired AgentSpace
2. Navigate to **Settings → Access Keys**
3. Create an access token with scopes: **`agent:read` + `agent:operate`** (recommended)

> ⚠️ Without `agent:operate`, the headline tools (`chat`, `investigate`) will be **completely invisible** — not just fail, but absent from the tool list.

### 2. Set environment variables

Ask the user for their token and the region where their AgentSpace is deployed.

**macOS / Linux:**
```bash
export DEVOPS_AGENT_TOKEN="your-token-here"
export DEVOPS_AGENT_REGION="us-east-1"
```

**Windows (PowerShell):**
```powershell
setx DEVOPS_AGENT_TOKEN "your-token-here"
setx DEVOPS_AGENT_REGION "us-east-1"
$env:DEVOPS_AGENT_TOKEN = "your-token-here"
$env:DEVOPS_AGENT_REGION = "us-east-1"
```

> ⚠️ **Windows users:** After `setx`, restart Kiro for the env var to take effect.

> **Alternative:** Instead of `DEVOPS_AGENT_REGION`, hardcode the region in `.kiro/settings/mcp.json`:
> ```json
> { "mcpServers": { "aws-devops-agent": { "url": "https://connect.aidevops.us-east-1.api.aws/mcp" } } }
> ```

### 3. Approve environment variables in Kiro

Go to **Kiro → Settings → MCP Approved Env Vars** and ensure `DEVOPS_AGENT_REGION` and `DEVOPS_AGENT_TOKEN` are present. Without this, Kiro will not pass these variables to MCP servers.

### 4. Token lifecycle
- Tokens expire (default 90 days). HTTP 401 → create a new token.
- Rotate without downtime: create new token → update `DEVOPS_AGENT_TOKEN` → restart Kiro.

---

## Option B — SigV4 Setup

### 1. Install `uvx`
- macOS: `brew install uv`
- Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install astral-sh.uv` or `pip install uv`
- Verify: `uvx --version`

### 2. Set the region

Ask the user for the region where their DevOps Agent resource is deployed:

```bash
export DEVOPS_AGENT_REGION="us-east-1"  # replace with actual region
```

### 3. Ensure valid AWS credentials

```bash
aws sts get-caller-identity
```

The IAM role must have DevOps Agent permissions (e.g., `AIDevOpsAgentFullAccess`).

---

## Dependency Bootstrap

On first interaction (or when any `uvx`-based server fails), run:

```bash
uvx --version
```

If not found:
1. Install `uv` (see Option B step 1)
2. Verify: `uvx --version`
3. Tell user to restart Kiro so MCP servers can find `uvx` in PATH

If `uvx` is found but `mcp-proxy-for-aws` has never been fetched, it auto-downloads on first server launch (no manual install needed).

---

## Troubleshooting

### Option A: Remote server (`aws-devops-agent`) — no tools or errors

Run in order, stop at first failure:

1. **Is `DEVOPS_AGENT_TOKEN` set?**
   - Check: `[ -n "$DEVOPS_AGENT_TOKEN" ] && echo 'Token is set' || echo 'Token is NOT set'` (macOS/Linux) or `if ($env:DEVOPS_AGENT_TOKEN) { 'Token is set' } else { 'Token is NOT set' }` (PowerShell)
   - Fix: Set it (see Option A above) and **restart Kiro**

2. **Is the token valid?**
   - Symptom: HTTP 401 from remote server
   - Fix: Regenerate in the Operator Web App → Settings → Access Keys

3. **Does the token have the right scope?**
   - Symptom: `investigate` and `chat` tools are missing (not erroring — literally absent)
   - Cause: Token has `agent:read` scope only
   - Fix: Create a new token with `agent:read` + `agent:operate` scopes

4. **Are tools present but returning `AccessDeniedException`?**
   - Bearer token: Your token's scope doesn't cover this operation
   - This differs from "tools missing" — missing means scope filters them out; AccessDenied means scope covers the tool but server-side authorization failed (rare)

### Option B: SigV4 proxy (`aws-devops-agent-sigv4`) — no tools or errors

Run in order, stop at first failure:

1. **Is `uvx` installed?**
   - Check: `uvx --version`
   - Fix: `brew install uv` (macOS) or `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux)

2. **Can the proxy launch?**
   - Check: `uvx mcp-proxy-for-aws@latest --help`
   - Fix: If network error, check connectivity. If resolution fails: `uv tool install mcp-proxy-for-aws`

3. **Are AWS credentials valid?**
   - Check: `aws sts get-caller-identity`
   - `Unable to locate credentials` → `aws configure sso` or `aws configure`
   - `ExpiredToken` / `InvalidClientTokenId` → `aws sso login`

4. **Does the IAM role have DevOps Agent permissions?**
   - Check: `aws devops-agent list-agent-spaces --region $DEVOPS_AGENT_REGION`
   - `AccessDeniedException` → User needs a role with DevOps Agent permissions

### Fallback server (`aws-mcp`) — no tools

Same checks as Option B steps 1-3 (uvx → proxy launch → AWS creds).

### Quick reference

| Error | Cause | Fix |
|-------|-------|-----|
| No tools (remote) | Token not set or Kiro not restarted | Set `DEVOPS_AGENT_TOKEN`, restart Kiro |
| 401 from remote | Token invalid/expired | Regenerate in Operator Web App |
| Tools missing (`investigate`, `chat` absent) | Token scope is `agent:read` only | Create token with `agent:operate` scope |
| No tools (SigV4 proxy) | `uvx` not installed or creds missing | `uvx --version`, then `aws sts get-caller-identity` |
| Connection refused / timeout | Remote server down | Falls back to `aws-mcp` automatically |
| `ExpiredTokenException` | AWS credentials expired | `aws sso login` |
| `AccessDeniedException` (SigV4) | Missing IAM permissions | Use a role with `AIDevOpsAgentFullAccess` |
| `aws-mcp` shows no tools | `uvx` not installed OR creds missing | `uvx --version`, then `aws sts get-caller-identity` |
| Tool call times out | `chat` can take 5-30s normally | Ensure `timeout: 120000` in mcp.json |
| `MCP error -32000: Connection closed` | Proxy exited — missing creds or `uvx` not in PATH | Run ordered checks above |

---

## Connection Diagnosis (when tools show as unavailable)

When MCP tools aren't appearing, diagnose each configured path independently:

### Path A (`aws-devops-agent`) shows no tools:
1. Check `DEVOPS_AGENT_TOKEN` is set and non-empty
2. Check `DEVOPS_AGENT_REGION` is set (otherwise URL is invalid)
3. If neither is set → tell user: "Path A (bearer token) isn't configured. Set DEVOPS_AGENT_TOKEN + DEVOPS_AGENT_REGION, or use Path B (SigV4)."

### Path B (`aws-devops-agent-sigv4`) shows no tools but AWS creds exist:
1. Confirm `uvx --version` works
2. Confirm `aws sts get-caller-identity` succeeds
3. Check DevOps Agent access: `aws devops-agent list-agent-spaces --region $DEVOPS_AGENT_REGION`
4. If AccessDenied → user needs `AIDevOpsAgentFullAccess`
5. If creds valid but server still shows no tools → **restart Kiro** (MCP servers initialize at IDE launch)

### Always report to user:
- Which path(s) are configured vs not
- Which path would work given their current state
- Whether a restart is needed to pick up changes
