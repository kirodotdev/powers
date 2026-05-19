---
name: "databricks"
displayName: "Databricks AI Dev Kit"
description: "Comprehensive Databricks development toolkit with 44 MCP tools (180+ operations) and expert guidance for building data pipelines, ML workflows, dashboards, jobs, and applications on Databricks platform."
keywords: ["databricks", "spark", "delta", "mlflow", "unity catalog", "pipelines", "jobs", "sql", "data engineering", "machine learning"]
author: "Databricks Solutions"
---

# Databricks AI Dev Kit

## Overview

The Databricks AI Dev Kit provides comprehensive support for building on the Databricks platform:

- **44 MCP Tools (180+ operations)** - Execute Databricks operations directly (SQL queries, job management, pipeline creation, model serving, Unity Catalog, and more)
- **Expert Skills** - Best practices and patterns for every Databricks capability, loaded from the latest [ai-dev-kit GitHub repository](https://github.com/databricks-solutions/ai-dev-kit)

## What You Can Build

- Spark Declarative Pipelines (streaming tables, CDC, SCD Type 2, Auto Loader)
- Databricks Jobs (scheduled workflows, multi-task DAGs, serverless execution)
- AI/BI Dashboards (interactive visualizations, KPIs, analytics)
- Unity Catalog (tables, volumes, governance, system tables, metric views)
- Genie Spaces (natural language data exploration)
- Knowledge Assistants (RAG-based document Q&A with vector search)
- MLflow Experiments (model evaluation, scoring, traces)
- Model Serving (deploy ML models and AI agents to endpoints)
- Databricks Apps (full-stack web applications)
- Vector Search (semantic search and RAG applications)
- Lakebase (managed PostgreSQL for OLTP workloads)

## Available Skills

Steering files are downloaded from the latest [ai-dev-kit repository](https://github.com/databricks-solutions/ai-dev-kit/tree/main/databricks-skills) during setup using the official Databricks installer, then copied into this Power's steering directory. Skills are discovered dynamically — any new skills added to the repository will be included on next update.

## Onboarding

When you first activate this power, I will guide you through a one-time setup process using the **official Databricks AI Dev Kit installer**.

### Prerequisites

- **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **git** - Version control
- **Databricks workspace** - AWS, Azure, or GCP
- **Databricks CLI** (optional, needed for OAuth login) - [Install guide](https://docs.databricks.com/en/dev-tools/cli/install.html)

### What I Will Do During Setup

I will perform three tasks:

1. **Run the official installer** — downloads MCP server, creates venv, installs skills to `~/.kiro/skills/`
2. **Copy skills to Power steering directory** — moves skills from `~/.kiro/skills/` into this Power's steering folder so they are scoped to Power activation
3. **Configure Databricks authentication** — prompts for credentials

### Step 1: Run the Official Installer

I will execute the official unified installer in non-interactive (silent) mode targeting Kiro:

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --silent
```

**IMPORTANT:** The installer script may return a non-zero exit code even when it succeeds. Do NOT treat this as a failure. Instead, verify success by checking that the expected files exist:

```bash
ls ~/.ai-dev-kit/.venv/bin/python && ls ~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py && ls ~/.kiro/skills/ | head -5
```

If these files exist, the installation succeeded regardless of the exit code. Proceed to Step 2.

If the files do NOT exist, then the installation genuinely failed. Check prerequisites (uv, git) and retry.

**Installer options explained:**
- `--tools kiro` — Only configure for Kiro (skip Claude, Cursor, etc.)
- `--global` — Install skills to `~/.kiro/skills/` and MCP config to `~/.kiro/settings/mcp.json`
- `--silent` — Non-interactive mode (uses defaults: all skills, DEFAULT profile)

**Optional flags you can add:**
- `--profile PROFILE_NAME` — Use a specific Databricks CLI profile (default: DEFAULT)
- `--skills-profile data-engineer` — Install only data engineering skills (options: all, data-engineer, analyst, ai-ml-engineer, app-developer)
- `--force` — Force reinstall even if already up to date
- `--skills-only` — Skip MCP server setup (skills only)

If the user wants interactive mode (to pick tools, profiles, and skills interactively), run without `--silent`:

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global
```

### Step 2: Copy Skills to Power Steering Directory

After the installer completes, I will copy the downloaded skills into this Power's steering directory and clean up the global skills location to avoid duplication:

```bash
POWER_STEERING="$HOME/.kiro/powers/installed/databricks/steering"
rm -rf "$POWER_STEERING"
mkdir -p "$POWER_STEERING"
cp -r "$HOME/.kiro/skills/"* "$POWER_STEERING/" 2>/dev/null || true
rm -rf "$HOME/.kiro/skills/databricks-"* "$HOME/.kiro/skills/mlflow-"* "$HOME/.kiro/skills/spark-"* "$HOME/.kiro/skills/agent-"* "$HOME/.kiro/skills/analyze-"* "$HOME/.kiro/skills/instrumenting-"* "$HOME/.kiro/skills/querying-"* "$HOME/.kiro/skills/retrieving-"* "$HOME/.kiro/skills/searching-"*
```

This ensures:
- Skills are scoped to this Power (only loaded when the Power is activated)
- No duplicate skills polluting the global skills namespace
- Skills appear in the Power's `steeringFiles` list for on-demand loading

After copying, I will tell the user:

"Skills installed into the Databricks Power's steering directory. These provide expert guidance for every Databricks capability — pipelines, jobs, dashboards, ML workflows, and more. They load on-demand based on your task.

Please click 'Update' on the Databricks Power in Kiro to refresh the steering files list."

### Step 3: Configure Authentication

After the installer completes, the MCP server needs valid Databricks credentials. The installer uses `DATABRICKS_CONFIG_PROFILE` in the MCP config, which reads from `~/.databrickscfg`.

I will prompt the user:

"How would you like to authenticate with Databricks?

- **Option A** (recommended): Databricks CLI OAuth login — requires [Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/install.html) to be installed. A browser window will open for authentication.
- **Option B**: I already have a profile configured in `~/.databrickscfg`
- **Option C**: Use a Personal Access Token (PAT) — no Databricks CLI needed

Which option?"

**If Option A:**
- First check if Databricks CLI is installed: `databricks --version`
- If NOT installed, tell the user: "Databricks CLI is required for OAuth login. Install it with: `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh` — then re-run this step. Or choose Option C to authenticate with a PAT token instead (no CLI needed)."
- If installed, run: `databricks auth login --profile DEFAULT` (or the user's chosen profile name)
- This opens a browser for OAuth. Once complete, credentials are stored in `~/.databrickscfg`.
- The MCP server will use this profile automatically.

**If Option B:**
- Confirm the profile name matches what's in `~/.kiro/settings/mcp.json` under `env.DATABRICKS_CONFIG_PROFILE`
- If different, update the profile name in the MCP config.

**If Option C:**
- Ask: "What is your DATABRICKS_HOST? (e.g., https://your-workspace.cloud.databricks.com)"
- Ask: "What is your DATABRICKS_TOKEN? (Personal Access Token)"
- Update `~/.kiro/settings/mcp.json` to replace `DATABRICKS_CONFIG_PROFILE` with explicit `DATABRICKS_HOST` and `DATABRICKS_TOKEN` env vars:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "~/.ai-dev-kit/.venv/bin/python",
      "args": ["~/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "dapi..."
      }
    }
  }
}
```

After authentication is configured, Kiro will auto-reconnect the MCP server.

### Step 4: Update Power's MCP Config

After the installer runs, the MCP config at `~/.kiro/settings/mcp.json` will have a `databricks` entry under `mcpServers`. However, since this Power bundles its own `mcp.json`, I need to update the **Power's runtime MCP config** at `~/.kiro/settings/mcp.json` under `powers.mcpServers.power-databricks-databricks` to match the installed server path.

I will read the installer-generated config and mirror it into the Power's MCP entry:
- Set `command` to the venv python path (e.g., `$HOME/.ai-dev-kit/.venv/bin/python`)
- Set `args` to `["$HOME/.ai-dev-kit/repo/databricks-mcp-server/run_server.py"]`
- Set `env` to match the authentication method chosen
- Set `disabled` to `false`
- Remove any `_comment` fields

### Example Setup Flow

```
User: "Set up Databricks power"

Agent: "I'll set up the Databricks AI Dev Kit for Kiro using the official installer.

[Running: bash <(curl -sL .../install.sh) --tools kiro --global --silent]
  ✓ git
  ✓ uv
  ✓ Repository cloned
  ✓ MCP server ready
  ✓ Databricks skills (25) → .kiro/skills
  ✓ MLflow skills (8) → .kiro/skills
  ✓ Kiro MCP config
✓ Installation complete!

[Copying skills to Power steering directory...]
  ✓ 33 skills copied to Power steering
  ✓ Cleaned up global skills directory

Please click 'Update' on the Databricks Power to refresh steering files.

Now let's configure authentication.

How would you like to authenticate with Databricks?
- Option A (recommended): OAuth login via Databricks CLI
- Option B: I already have a profile in ~/.databrickscfg
- Option C: Use a Personal Access Token (no CLI needed)

Which option?"

User: "A"

Agent: "Checking for Databricks CLI...
✓ Databricks CLI v0.280.0 found.

Running OAuth login...
[Executing: databricks auth login --profile DEFAULT]
A browser window should open for authentication.

...

✓ Authentication complete!

Once connected, try:
- 'List my SQL warehouses'
- 'Execute: SELECT current_catalog()'
- 'Show me all jobs'"
```

### Update Skills

To refresh skills with the latest versions from the repository:

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --skills-only --force --silent
```

Then copy to Power steering:
```bash
POWER_STEERING="$HOME/.kiro/powers/installed/databricks/steering"
rm -rf "$POWER_STEERING"
mkdir -p "$POWER_STEERING"
cp -r "$HOME/.kiro/skills/"* "$POWER_STEERING/" 2>/dev/null || true
rm -rf "$HOME/.kiro/skills/databricks-"* "$HOME/.kiro/skills/mlflow-"* "$HOME/.kiro/skills/spark-"* "$HOME/.kiro/skills/agent-"* "$HOME/.kiro/skills/analyze-"* "$HOME/.kiro/skills/instrumenting-"* "$HOME/.kiro/skills/querying-"* "$HOME/.kiro/skills/retrieving-"* "$HOME/.kiro/skills/searching-"*
```

Or paste this into Kiro chat:
```
Update Databricks skills: run the official installer with --tools kiro --global --skills-only --force --silent, then copy skills from ~/.kiro/skills/ to the Power steering directory and clean up.
```

### Change Skill Profile

To switch to a different skill profile (e.g., only data engineering skills):

```bash
bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh) --tools kiro --global --skills-profile data-engineer --force --silent
```

Then re-copy to Power steering (same commands as Update Skills above).

Available profiles:
- `all` — All 34+ skills (default)
- `data-engineer` — Pipelines, Spark, Jobs, Streaming (14 skills)
- `analyst` — Dashboards, SQL, Genie, Metrics (8 skills)
- `ai-ml-engineer` — Agents, RAG, Vector Search, MLflow (17 skills)
- `app-developer` — Apps, Lakebase, Deployment (10 skills)

You can also combine profiles: `--skills-profile data-engineer,ai-ml-engineer`

## Available MCP Tools

44 tools covering 180+ operations:

| Category | Tools | Key Operations |
|----------|-------|---------------|
| SQL | 5 | execute_sql, execute_sql_multi, manage_warehouse, get_table_stats_and_schema |
| Compute | 4 | execute_code, manage_cluster, manage_sql_warehouse, list_compute |
| Jobs | 2 | manage_jobs (create/get/list/update/delete), manage_job_runs (run/wait/cancel) |
| Pipelines | 2 | manage_pipeline, manage_pipeline_run |
| Unity Catalog | 9 | manage_uc_objects, manage_uc_grants, manage_uc_storage, manage_uc_tags, manage_metric_views |
| Dashboards | 1 | manage_dashboard (create/get/list/delete/publish) |
| Genie | 2 | manage_genie, ask_genie |
| Agent Bricks | 2 | manage_ka, manage_mas |
| Model Serving | 1 | manage_serving_endpoint (get/list/query) |
| Vector Search | 4 | manage_vs_endpoint, manage_vs_index, query_vs_index, manage_vs_data |
| Lakebase | 4 | manage_lakebase_database, manage_lakebase_branch, manage_lakebase_sync |
| Apps | 1 | manage_app (create/get/list/delete/deploy) |
| Files | 2 | manage_workspace_files, manage_volume_files |
| Other | 5 | manage_workspace, get_current_user, generate_and_upload_pdf, list_tracked_resources, delete_tracked_resource |

## Resources

- **GitHub Repository**: https://github.com/databricks-solutions/ai-dev-kit
- **Official Installer**: `bash <(curl -sL https://raw.githubusercontent.com/databricks-solutions/ai-dev-kit/main/install.sh)`
- **Databricks CLI Install**: `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh`
- **Databricks Documentation**: https://docs.databricks.com
- **Kiro Documentation**: https://kiro.dev/docs

## Contributors

- [@antonyprasad-db](https://github.com/antonyprasad-db) — Senior Specialist Solutions Architect, Databricks (AWS Partnership) — Kiro IDE installer in [ai-dev-kit PR #511](https://github.com/databricks-solutions/ai-dev-kit/pull/511); primary maintainer of this Power
- [@venkatavaradhanv](https://github.com/venkatavaradhanv) — Solutions Architect, AWS — prototyped the catalog-ready Power packaging
