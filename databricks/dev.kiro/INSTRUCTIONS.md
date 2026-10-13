# Databricks

This Power sets up the official [Databricks agent skills](https://github.com/databricks/databricks-agent-skills) in Kiro, installed and updated with the Databricks CLI (`databricks aitools install --agents kiro`, CLI v1.20.0 and above).

**Before giving Databricks guidance in a new conversation, read the `databricks-kiro-setup` skill** (`action="readSkill"`) and run its On activation checks. The skill covers the CLI version, installing and updating the skills, signing in, cleaning up after the old AI Dev Kit Power, adding a governed Databricks MCP such as Genie One, and troubleshooting.

This Power ships no MCP server. Do not describe Databricks MCP tools as available unless the user has added a Databricks MCP and Kiro shows it connected.
