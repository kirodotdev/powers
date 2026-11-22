# Getting Started with AgentCore

This guide uses the AgentCore CLI (`@aws/agentcore`). Check it is installed with `agentcore --version`; install it with `npm install -g @aws/agentcore` (Node.js 20.12 or later). Python agents also need `uv`.

If `agentcore` rejects the commands below, the old Python starter toolkit may be on the PATH. Uninstall it with `pip uninstall bedrock-agentcore-starter-toolkit`.

## Choose a Path

- **New agent:** create a project from a template (Path 1).
- **Existing agent code:** create an empty project, add a runtime, and move the code into it (Path 2). Do not scaffold a template over existing code.
- **No code, managed agent:** add a harness (Path 3).

## Path 1: New Agent from a Template

```bash
agentcore create --name MyAgent --template agent-python-strands
cd MyAgent
```

Project names must start with a letter, contain only letters and digits (no dashes or underscores), and be at most 23 characters.

`agentcore create --help` lists the templates. The common ones:

| Template | Agent |
| --- | --- |
| `agent-python-strands` | Strands agent with AgentCore Memory (default choice) |
| `agent-python-strands-container` | Same, deployed as a container |
| `agent-python-langchain` | LangChain agent on Amazon Bedrock |
| `agent-python-minimal` | Python, no agent framework |
| `agent-typescript-strands` | Strands agent in TypeScript with AgentCore Memory |
| `agent-typescript-vercel` | Vercel AI SDK agent in TypeScript |
| `a2a-python-strands` | Strands agent serving the A2A protocol |
| `agui-python-strands` | Strands agent serving AG-UI |
| `mcp-python-fastmcp` | MCP server built with FastMCP |
| `empty` | No runtime (the default when `--template` is omitted) |

With `--template`, the project uses the template's default model provider (Amazon Bedrock for the model-backed templates). To use Anthropic, OpenAI, Gemini, an OpenAI-compatible endpoint, or LiteLLM, the user runs `agentcore create` without flags and picks the provider in the interactive flow; the API key is stored in `agentcore/.env.local` and provisioned as an AgentCore Identity credential on deploy.

`create` installs the dependencies (`uv sync` for Python, `npm install` for the CDK app) and initializes a git repository. Use `--skip-install` or `--skip-git` to skip either.

For `agent-python-strands`, the project contains:

```
MyAgent/
├── agentcore/
│   ├── agentcore.json      # runtime "agent" and memory "agentMemory"
│   ├── aws-targets.json    # deployment targets, filled on first deploy
│   ├── .env.local          # local-only variables, gitignored
│   └── cdk/                # CDK app used by deploy
└── app/agent/
    ├── main.py             # entrypoint (BedrockAgentCoreApp)
    ├── model/load.py       # model provider
    ├── memory/session.py   # AgentCore Memory session manager
    ├── parse.py            # payload parsing
    └── pyproject.toml
```

The runtime is named `agent`. The payload is `{"prompt": "..."}`, with an optional `actorId` for memory scoping.

## Path 2: Existing Agent Code

```bash
agentcore create --name MyProject
cd MyProject
agentcore add runtime --name support --language python
```

`add runtime` registers the runtime in `agentcore.json` and creates `app/support/` with a `README.md` and an `AGENTS.md`. Read `app/support/AGENTS.md` before changing the code: it lists what the CLI needs. In short, for an HTTP runtime in Python:

- The entrypoint is `app/support/main.py`, with a module-level `app = BedrockAgentCoreApp()` (from `bedrock_agentcore.runtime`), an `@app.entrypoint` function, and `if __name__ == "__main__": app.run()` at the end.
- Dependencies go in `[project].dependencies` in `app/support/pyproject.toml`, not `requirements.txt`. Include `bedrock-agentcore` and `aws-opentelemetry-distro` (the deployed runtime starts the code with `opentelemetry-instrument` and fails without it).
- Packages must publish `aarch64` manylinux wheels; AgentCore runs on ARM64 Linux.
- To use an entrypoint other than `main.py`, set it in `pyproject.toml`:

  ```toml
  [tool.agentcore]
  entrypoint = "server.py"
  ```

- Adding a `Dockerfile` to `app/support/` switches the runtime to a container build. Only add one if the user wants that.

A minimal entrypoint:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context):
    agent = Agent(system_prompt="You are a helpful assistant.")
    result = agent(payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
```

`--protocol` selects `HTTP` (default), `MCP`, `A2A`, or `AGUI`; the generated `AGENTS.md` describes the contract for each. For TypeScript, use `--language typescript`.

Projects made with the starter toolkit (`.bedrock_agentcore.yaml`) are not converted automatically. Follow Path 2 and move the agent code and dependencies into `app/<name>/`.

## Path 3: Managed Harness

```bash
agentcore add harness --name MyAssistant
agentcore deploy
agentcore invoke --harness MyAssistant --prompt "What can you do?"
```

`agentcore add harness --help` lists the model, system prompt, tool, skill, and memory options. Harnesses are not available in the China regions.

## Run and Test Locally

```bash
agentcore dev
```

`agentcore dev` runs the project's runtime with hot reload on port 8080 (8000 for MCP, 9000 for A2A). With several agents, choose one with `--agent <name>`. `--port` changes the port, and `--mode browser` opens the Agent Inspector web UI.

In a second terminal:

```bash
agentcore invoke --runtime agent --local --payload '{"prompt": "Hello"}'
```

`--runtime` and `--local` are both required for a local call. Stop the server with Ctrl+C.

Notes:

- Local runs use the developer's AWS credentials, so a Bedrock-backed agent needs credentials even locally.
- `dev` sets `LOCAL_DEV=1`, `PORT`, and `AWS_REGION`, and loads `agentcore/.env.local`. Put local-only variables and secrets there, never in `app/<name>/` (everything in that folder is uploaded on deploy).
- Memory and gateway IDs are only injected into the deployed runtime. See the memory and gateway steering files for testing those locally.
- For a harness, `agentcore dev` deploys it and prints how to invoke it; `--skip-deploy` reuses the deployed harness.

After each code change, invoke the agent again locally and check the response before moving on.

## Deploy

Confirm with the user first; deploying creates AWS resources.

```bash
agentcore deploy
```

On the first run, `deploy` creates the `default` target in `agentcore/aws-targets.json` from the current AWS account and region, bootstraps CDK if needed, builds the code, and deploys one CloudFormation stack. Use `--region` or `AWS_REGION` to pick the region, and `--target <name>` for another entry in `aws-targets.json`.

To build and synthesize without deploying (no AWS calls needed): `agentcore build`.

## Invoke and Inspect the Deployed Agent

```bash
agentcore invoke --runtime agent --payload '{"prompt": "Hello"}'
agentcore invoke --runtime agent --session-id <session-id> --payload '{"prompt": "And then?"}'
agentcore status
agentcore logs runtime --name agent --since 15m
agentcore logs runtime --name agent --tail
agentcore traces runtime list
```

When `--session-id` is omitted, `invoke` generates one and prints it as `runtime-session-id`; pass it back with `--session-id` to continue the conversation. `agentcore runtime list` and `agentcore runtime get` read deployed runtimes without a project.

## Tear Down

```bash
agentcore remove all --yes
agentcore deploy --yes
```

`remove all` empties every resource collection in `agentcore.json` and leaves the code in `app/`. The following `deploy --yes` deletes the stack. To remove a single resource instead, use `agentcore remove <type> --name <name>` (for example `agentcore remove memory --name agentMemory`) and deploy again.

## Quick Reference

```bash
npm install -g @aws/agentcore                                  # install the CLI
agentcore create --name MyAgent --template agent-python-strands
cd MyAgent
agentcore dev                                                  # terminal 1
agentcore invoke --runtime agent --local --payload '{"prompt": "Hi"}'   # terminal 2
agentcore deploy
agentcore invoke --runtime agent --payload '{"prompt": "Hi"}'
agentcore status
agentcore logs runtime --name agent --since 15m
agentcore remove all --yes && agentcore deploy --yes           # tear down
```
