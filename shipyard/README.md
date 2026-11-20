# Shipyard (hosted)

Put your repo on [Shipyard](https://shipyard.build) and check its preview environments from your coding agent, with
nothing to install. Sign in with Shipyard, and the agent adds your GitHub repo as an app, writes a Docker Compose file
if the repo has none, and gives you a live preview environment for each branch.

## Overview

This plugin connects your agent to Shipyard's hosted MCP server and adds one skill that tells the agent how to use it
safely. There's no CLI and no token to copy: you sign in from your client, and the client keeps the token. The skill
loads its Compose-writing guide only when the repo needs one.

## Skills

| Skill | When to use | References |
|---|---|---|
| `shipyard` | "try the Shipyard power", "put this repo on Shipyard", "get a preview environment for this branch", "write a docker-compose file", "did my change deploy?", "why did the build fail?" | compose |

## Routing guide

The skill has one section per task:

- **Just installed it, or not connected yet?** → On activation, then Connecting
- **Putting a repo on Shipyard?** → Adding an app (with `references/compose.md` when the repo has no Compose file)
- **Changing an app's services, routes, branches or repos?** → Changing an app
- **Checking that a push or change is live, or why a build failed?** → Checking a change

## MCP servers

| Server | URL | Sign-in |
|---|---|---|
| `shipyard` | `https://mcp.shipyard.build/mcp` | Shipyard OAuth in your browser |

Tools:

- `plan_application`: preview adding a pushed GitHub branch as an app. Changes nothing.
- `create_application`: create the app from a plan you confirmed.
- `update_application`: change an app's branches, services, routes or repos.
- `get_environments`, `get_environment`, `get_build_history`, `get_failure_details`, `get_build_logs`: check
  environments, builds and failures.

There's no tool to set env vars after creating an app, stop or restart an environment, rebuild on request, read
service logs or run commands. Use the Shipyard dashboard, or the
[CLI plugin](https://github.com/shipyard/shipyard-plugins#readme), for those.

## Installation

### Kiro

In the Powers panel, choose **Add Custom Power**, then **Import power from GitHub**, and enter:

```
https://github.com/shipyard/shipyard-plugins/tree/main/hosted
```

Then click **Try power**, or ask "put this repo on Shipyard".

### Claude Code

```
claude plugin marketplace add shipyard/shipyard-plugins
claude plugin install shipyard-hosted@shipyard
```

Then run `/mcp` and connect the Shipyard server.

### Codex

```
codex plugin marketplace add shipyard/shipyard-plugins
codex plugin add shipyard-hosted@shipyard
codex mcp login shipyard
```

Connecting opens Shipyard in your browser. Sign in and allow access. If you're in more than one organization, pick the
one the agent works in. Install this plugin or the CLI plugin, not both: each defines a server named `shipyard`.

## Prerequisites

- A Shipyard account. You can sign up with GitHub on the sign-in page, or at https://shipyard.build/signup.
- A GitHub repo. If yours has no remote yet, the agent offers to create a private one with the GitHub CLI, or points
  you to github.com/new.
- Shipyard's GitHub app with access to the repo. If it doesn't have access yet, the agent gives you the link.
- Optional: Docker, so the agent can check a Compose file it writes, and the GitHub CLI (`gh`), so it can create the
  repo for you.

## Examples

- "Put this repo on Shipyard"
- "My repo has no docker-compose file. Can you write one for Shipyard?"
- "Give me a preview environment for this branch"
- "Did my last push deploy?"
- "Why did the build fail?"
- "Show me the build logs for the api service"
- "Add the worker service and route /api to the api service"
- "List my Shipyard environments"

## Safety

- The agent asks before it commits, pushes, creates a repo or changes an app. Adding an app takes two yeses: one for
  everything before the plan, and one before the app is created.
- It lists the files it wrote apart from yours, and commits only your files the build needs. It leaves `.env` files,
  keys and Terraform state out, screens the commits it would push for secrets and asks you about any hit, and never
  force-pushes or asks you to paste a token.
- Your client decides whether a tool can run without asking. Keep approval on for `create_application` and
  `update_application`.

## Support

- Docs: [Shipyard MCP guide](https://github.com/shipyard/shipyard-cli/blob/main/docs/mcp.md#the-hosted-server)
- Support: support@shipyard.build
- Security reports: security@shipyard.build, see https://shipyard.build/security/
- [Privacy policy](https://shipyard.build/privacy/) and [terms](https://shipyard.build/terms/)

## License

Apache-2.0
