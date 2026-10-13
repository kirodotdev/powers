---
name: "databricks-kiro-setup"
description: "Sets up the official Databricks agent skills in Kiro with the Databricks CLI, and shows how to add a governed Databricks MCP such as Genie One. Use when starting Databricks work in Kiro before the Databricks skills (such as databricks-core) are installed, when installing, updating, or removing them, when signing in the Databricks CLI, when adding a Databricks MCP to Kiro, when migrating from the Databricks AI Dev Kit Power, or when troubleshooting any of these."
metadata:
  author: "Databricks"
---

# Databricks in Kiro

## Overview

This Power sets up the official [Databricks agent skills](https://github.com/databricks/databricks-agent-skills) in Kiro. The skills teach Kiro how to build on the Databricks Platform: Lakeflow pipelines, jobs, AI/BI dashboards, Databricks Apps, Unity Catalog governance, Lakebase, Model Serving, MLflow and Agent Bricks.

The Databricks CLI installs the skills (`databricks aitools install --agents kiro`, CLI v1.20.0 and above) into `~/.kiro/skills/` and records the install, so `databricks aitools update` can refresh them. The Power also adds the MLflow skills from [mlflow/skills](https://github.com/mlflow/skills), which the CLI does not carry.

This Power ships no MCP server. Databricks-provided MCPs run on your own workspace and need your credentials, so you add them to your Kiro MCP config yourself; see [Optional: governed data access](#optional-governed-data-access).

> **Upgrading from the "Databricks AI Dev Kit" Power?** That version ran the ai-dev-kit installer, copied skills into the Power's `steering/` directory, and shipped a local MCP server that upstream has deprecated. See [Migrating from the AI Dev Kit Power](#migrating-from-the-ai-dev-kit-power) before you install.

## On activation

> **Run these checks on the first turn of a new conversation that uses this skill, before giving Databricks guidance.** The commands assume a POSIX shell (macOS, Linux, or WSL or Git Bash on Windows). Run each command on its own line, without trailing `#` comments: Kiro's terminal can be an interactive zsh, which passes `#` through as an argument.
>
> 1. **CLI version.** Run `databricks --version`. The skills need **v1.20.0 or later**, the first release with Kiro support in `databricks aitools`. If the CLI is missing or older, walk the user through [Step 1](#step-1-install-or-upgrade-the-databricks-cli).
> 2. **Skills installed.** Check locally, which works offline: `ls "$HOME/.databricks/aitools/skills/.state.json" "$HOME/.kiro/skills/databricks-core/SKILL.md"` (for a project install, `.databricks/aitools/skills/.state.json` and `.kiro/skills/databricks-core/SKILL.md`). If either file is missing, walk the user through [Step 3](#step-3-install-the-databricks-skills).
> 3. **Authentication.** The skills run Databricks CLI commands, which need a configured profile. List existing profiles with `databricks auth profiles --skip-validate`, which shows names and hosts and never a secret. Ignore its `Valid` column: with `--skip-validate` it always reads `NO`. If there are no profiles, walk the user through [Step 2](#step-2-authenticate-the-databricks-cli).
> 4. **Leftovers from the old Power.** If `grep -l 'databricks-mcp-server/run_server.py' "$HOME/.kiro/settings/mcp.json" .kiro/settings/mcp.json 2>/dev/null` prints a file name, the old ai-dev-kit MCP server is still configured. Mention it once and point to [Migrating from the AI Dev Kit Power](#migrating-from-the-ai-dev-kit-power); if the user declines, don't raise it again in this conversation. Never delete anything without explicit approval.
> 5. **No MCP tools by default.** This Power ships no MCP server. Do not describe Databricks MCP tools as available unless the user has added a Databricks MCP and Kiro shows it connected.

## Setup

### Prerequisites

- **Kiro IDE 1.0.288 or later**, the first release that installs Powers in the Agent Plugins format
- **Databricks workspace** on AWS, Azure, or GCP
- **Databricks CLI v1.20.0 or later** ([install](https://docs.databricks.com/aws/en/dev-tools/cli/install))
- **git**, for the MLflow skills in Step 4

### Step 1: Install or upgrade the Databricks CLI

Check the version. It needs to be v1.20.0 or later:

```bash
databricks --version
```

If the command is missing or reports an older version, install or upgrade it with the method for your platform from the [CLI install guide](https://docs.databricks.com/aws/en/dev-tools/cli/install). On macOS with Homebrew, install with:

```bash
brew tap databricks/tap
brew install databricks
```

or upgrade an existing install with `brew upgrade databricks`. Older CLIs reject the Kiro target with `Error: unknown agent "kiro"`.

### Step 2: Authenticate the Databricks CLI

> **⚠️ Agent behavior (REQUIRED):** before configuring credentials, check for existing profiles with a command that cannot print a secret. **Do not `cat ~/.databrickscfg`**: that prints every `token` and `client_secret` into the chat transcript. This lists profile names and hosts only, and honors `DATABRICKS_CONFIG_FILE`:
>
> ```bash
> databricks auth profiles --skip-validate
> ```
>
> Show the user the profile names and hosts (ignore the `Valid` column), then ask whether to reuse one or create a new one. Never reuse or copy credentials without explicit approval.

For interactive use, sign in with OAuth (user-to-machine). The CLI opens a browser, and the access token refreshes automatically:

```bash
databricks auth login --host https://<your-workspace-url> --profile <profile-name>
```

For other methods (service principal OAuth for automation, personal access tokens), see [Databricks CLI authentication](https://docs.databricks.com/aws/en/dev-tools/cli/authentication).

### Step 3: Install the Databricks skills

```bash
databricks aitools install --agents kiro --scope global
```

This installs the Databricks agent skills into `~/.kiro/skills/`. `--agents kiro` works even when the `kiro` command is not on your `PATH`. If `~/.kiro/skills/` already has a folder with the same name as a Databricks skill, for example a copy from the ai-dev-kit installer, the CLI moves it to a backup in the system temp directory, which the OS may clear; copy out any local edits first. Add `--experimental` to also install the experimental skills, such as `spark-python-data-source` (custom Spark data sources).

To install for one workspace only, use `--scope project`. The CLI then stores the skills under `.databricks/aitools/skills/` in that workspace and links them from `.kiro/skills/`. Bundle projects usually gitignore `.databricks/`, so don't commit `.kiro/skills/`; each teammate runs the install in their own checkout.

Check the result with `databricks aitools list`, which shows the installed version of each skill.

### Step 4: Add the MLflow skills

The CLI does not carry the MLflow skills (tracing, evaluation, trace analysis, metrics), so install them from [mlflow/skills](https://github.com/mlflow/skills). The block replaces any existing folders with these eight names; if any exist and the user didn't install them from `mlflow/skills`, this Power, or ai-dev-kit, ask before running it.

```bash
tmp="$(mktemp -d)"
ok=0
if git clone --depth 1 --quiet https://github.com/mlflow/skills.git "$tmp/mlflow-skills"; then
  mkdir -p "$HOME/.kiro/skills"
  for s in agent-evaluation analyze-mlflow-chat-session analyze-mlflow-trace \
           instrumenting-with-mlflow-tracing mlflow-onboarding querying-mlflow-metrics \
           retrieving-mlflow-traces searching-mlflow-docs; do
    dest="$HOME/.kiro/skills/$s"
    if [ -e "$dest.old" ] && [ ! -e "$dest" ]; then mv "$dest.old" "$dest"; fi
    rm -rf "$dest.new" "$dest.old"
    if [ -d "$tmp/mlflow-skills/$s" ] && cp -R "$tmp/mlflow-skills/$s" "$dest.new"; then
      if [ -e "$dest" ]; then mv "$dest" "$dest.old"; fi
      if mv "$dest.new" "$dest"; then
        rm -rf "$dest.old"; ok=$((ok + 1))
      else
        if [ -e "$dest.old" ]; then mv "$dest.old" "$dest"; fi
        rm -rf "$dest.new"; echo "Could not replace $s; kept the existing copy"
      fi
    else
      rm -rf "$dest.new"; echo "Skipped $s; any existing copy was left in place"
    fi
  done
else
  echo "Could not clone mlflow/skills; existing MLflow skills were left unchanged"
fi
rm -rf "$tmp"
echo "Installed $ok of 8 MLflow skills"
[ "$ok" -eq 8 ]
```

These are the same eight MLflow skills the ai-dev-kit installer used; `mlflow/skills` has more, which you can add to the list. The loop names the skills directly so it behaves the same in zsh (the macOS default) and bash. Each skill is copied to a temporary folder first and swapped in only after the copy succeeds; if the swap fails, the previous copy is put back, and a copy left over from an interrupted run is restored before the next attempt. The block exits non-zero unless all eight were installed. For a project install, replace `$HOME/.kiro/skills` with `.kiro/skills`. The CLI doesn't track these skills; re-run this step to refresh them from the `main` branch of `mlflow/skills`.

### Step 5: Start a new chat session

Kiro loads skills when a chat session starts, so open a new session to pick them up. Ask something like "Using the databricks-core skill, which workspace am I connected to?" to confirm.

## Optional: governed data access

To query your data from Kiro, add a [Databricks-provided MCP](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services) through Unity Gateway. For analytics, start with `system.ai.genie_one_mcp`, which answers natural-language questions with Genie One. `system.ai.dbsql` runs specific SQL on a SQL warehouse (Unity Gateway beta, which an account admin enables). Each is a Unity Catalog securable, so grants and policies govern who can call it and what each call can do.

For local use, these MCPs accept a Databricks personal access token in an `Authorization: Bearer` header. Open your MCP config with **Open User MCP Config (JSON)** (all workspaces) or **Open Workspace MCP Config (JSON)** (this workspace) in the command palette, add the server inside the existing `mcpServers` object, and reference the token through an environment variable rather than pasting it into the file:

```json
{
  "mcpServers": {
    "databricks-genie-one": {
      "url": "https://<workspace-hostname>/ai-gateway/mcp-services/system.ai.genie_one_mcp",
      "headers": { "Authorization": "Bearer ${DATABRICKS_MCP_TOKEN}" }
    }
  }
}
```

Kiro expands `${DATABRICKS_MCP_TOKEN}` from the environment it was launched with, so export the variable in the shell profile that starts Kiro, then quit Kiro fully (Cmd+Q on macOS) and reopen it. Kiro picks up `mcp.json` edits without a restart, but it reads environment variables only at launch. Treat that profile as a credential file: don't commit or sync it, and give the token a short lifetime.

Kiro expands the variable in workspace MCP configs too, so add the entry to the user config and review a workspace's `.kiro/settings/mcp.json` before trusting the workspace.

Use a name other than `DATABRICKS_TOKEN`: the Databricks CLI reads that variable for its own sign-in, so exporting it would change how the skills' CLI commands authenticate. For other sign-in options, see [MCP authentication and networking](https://docs.databricks.com/aws/en/agents/mcp-tools/authentication-networking).

> **Agent behavior:** never write a token value into `mcp.json`, a shell profile, or the chat; the user sets the variable themselves. After the user adds the entry, check that Kiro's MCP panel shows the server connected before describing its tools as available.

## Keeping skills current

To refresh the Databricks skills, run:

```bash
databricks aitools update --scope global
```

It updates the skills for every coding agent the CLI detects on this machine, not only Kiro, and it can switch Claude Code, Codex and Copilot from raw skill files to the Databricks plugin. If the user has other coding agents set up, tell them before running it. Use `--scope project` from the workspace folder for a project install.

If Kiro's skills stay on an older version after another agent's skills were updated, `--force` re-downloads them, but it does so for every detected agent and replaces any local edits to Databricks skills in all of them. Get the user's approval before using it.

To remove the Databricks skills from Kiro, get the user's approval first, then run:

```bash
databricks aitools uninstall --agents kiro --scope global
```

Use `--scope project` for a project install. In an interactive terminal the command asks for confirmation; when run without a terminal it proceeds without asking. The CLI only removes skill folders that still match what it installed, so edited copies and skills it didn't install stay in place; leave them unless the user asks to remove them.

Re-run [Step 4](#step-4-add-the-mlflow-skills) to refresh the MLflow skills, or delete their eight directories from `~/.kiro/skills/` to remove them.

## Migrating from the AI Dev Kit Power

Update this Power in Kiro (or uninstall and reinstall it). Kiro deletes a Power's installed folder and its `powers.mcpServers` entries when it reinstalls it, so the skill copies the old version placed in its `steering/` directory, including the MLflow skills, and its disabled MCP server entry are removed. Then run [Step 3](#step-3-install-the-databricks-skills) and [Step 4](#step-4-add-the-mlflow-skills).

A few things live outside the Power, so updating it doesn't remove them:

- **A top-level `databricks` MCP server.** If you installed the old optional MCP server, Kiro's `mcp.json` may still have an entry that runs `databricks-mcp-server/run_server.py`. Kiro has no command to delete a server, so open the file as described in [Optional: governed data access](#optional-governed-data-access) and delete the `databricks` entry.
- **Credential and profile exports in your shell profile.** The old Power's setup options had you export `DATABRICKS_CONFIG_PROFILE`, `DATABRICKS_HOST` with `DATABRICKS_TOKEN`, or `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`. These override the profile you choose for the skills, so commands can reach the wrong workspace or fail with "more than one authorization method configured". Remove those exports and use a profile from [Step 2](#step-2-authenticate-the-databricks-cli). If a token or client secret sat in the profile in plain text, revoke it.
- **The ai-dev-kit clone** (`~/.ai-dev-kit`, or the directory in `AIDEVKIT_HOME`). Kiro no longer needs it, but ai-dev-kit may still serve other coding agents or projects. Remove it only if you don't use ai-dev-kit anywhere else, and delete the directory rather than running ai-dev-kit's `install.sh --uninstall`: the uninstaller removes skill folders by name from `~/.kiro/skills/`, including ones the Databricks CLI installed in Step 3.

## Troubleshooting

### `Error: unknown agent "kiro"`

The Databricks CLI is older than v1.20.0. Upgrade it ([Step 1](#step-1-install-or-upgrade-the-databricks-cli)) and re-run Step 3.

### Kiro doesn't use the skills

Skills load when a chat session starts. Open a new session, and check that `databricks-core/SKILL.md` exists in `~/.kiro/skills/`, or in `.kiro/skills/` for a project install.

### A command fails with stray `#` arguments

Kiro's terminal can be an interactive zsh, which doesn't treat `#` as a comment. Run commands without trailing comments.

### A `${...}` reference in `mcp.json` stays literal

Kiro expands variables from the environment it was launched with. Export the variable in the shell profile that starts Kiro, then quit and reopen Kiro. Some earlier Kiro versions also required listing the name in the `kiroAgent.mcpApprovedEnvVars` setting.

### A Databricks MCP server doesn't connect

Check the server's status and error in Kiro's MCP panel. If the token reference stayed literal, see the previous entry. An authentication error (HTTP 401) usually means the token is missing, invalid, or expired: create a new one, update the variable, and relaunch Kiro. A permission error (HTTP 403) usually means the identity behind the token isn't allowed to use that MCP service; ask a workspace or account admin, using [Databricks-provided MCP services](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services). `system.ai.dbsql` also needs the Unity Gateway beta enabled on the account.

### A warning that a skill name doesn't match its directory

Two MLflow skills (`analyze-mlflow-chat-session`, `analyze-mlflow-trace`) declare a `name` that differs from their directory name. Kiro warns and still loads them.

### Authentication errors when a skill runs a CLI command

Run `databricks auth profiles` to check which profiles are valid, then sign in again with `databricks auth login --host https://<your-workspace-url> --profile <profile-name>`.

### Duplicate Databricks skills

Overlapping skills with older names (for example `databricks-genie` next to `databricks-genie-agents`) usually come from the ai-dev-kit installer, which copied its own skill set into `~/.kiro/skills/`. A skill can also appear twice if it's installed at both global and project scope. Show the user the overlapping folders and remove only the ones they choose.

## License, Trademarks, and Support

### Power packaging

This Power's packaging (`plugin.json`, `dev.kiro/INSTRUCTIONS.md` and this skill) is published under the same license terms as the [kirodotdev/powers](https://github.com/kirodotdev/powers) catalog.

### Skills

The Databricks agent skills come from [databricks/databricks-agent-skills](https://github.com/databricks/databricks-agent-skills) and are installed by the Databricks CLI, which is subject to the [Databricks License](https://github.com/databricks/cli?tab=License-1-ov-file#readme) and [Databricks Privacy Notice](https://www.databricks.com/legal/privacynotice). The MLflow skills come from [mlflow/skills](https://github.com/mlflow/skills) under that repository's license.

### Trademarks

"Databricks", "Unity Catalog", "Delta Lake", "Agent Bricks", "Genie", "Lakebase", "MLflow", "Databricks Apps", and other Databricks product names referenced in this Power are trademarks of Databricks, Inc.

"Amazon Web Services", "AWS", and "Kiro" are trademarks of Amazon.com, Inc. or its affiliates.

### Contributors

- **Antony Prasad Thevaraj** ([@antonyprasad-db](https://github.com/antonyprasad-db)), Senior Specialist Solutions Architect, Databricks (AWS Partnership). Co-authored Kiro support in `databricks aitools` ([databricks/cli#6908](https://github.com/databricks/cli/pull/6908)) and maintains this Power.
- **Venkatavaradhan Viswanathan** ([@venkatavaradhanv](https://github.com/venkatavaradhanv)), Senior Solutions Architect, AWS. Created the original wrapper Power at [venkatavaradhanv/databricks](https://github.com/venkatavaradhanv/databricks).

### Support

- **Power packaging or installation** — [github.com/kirodotdev/powers/issues](https://github.com/kirodotdev/powers/issues)
- **Databricks agent skills** — [github.com/databricks/databricks-agent-skills/issues](https://github.com/databricks/databricks-agent-skills/issues)
- **Databricks CLI and `databricks aitools`** — [github.com/databricks/cli/issues](https://github.com/databricks/cli/issues)
- **Databricks platform support** — [help.databricks.com](https://help.databricks.com)
