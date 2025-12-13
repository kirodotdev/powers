---
name: "defang"
displayName: "Defang with local MCP"
description: "Deploy Docker Compose apps to your own cloud account using Defang MCP."
keywords:
  [
    "deploy",
    "cloud",
    "deployment",
    "compose",
    "aws",
    "gcp",
    "digitalocean",
    "estimate",
  ]
mcpServers: ["defang"]
---

# Onboarding

## Validate tools work

Before using Defang Local MCP, ensure the following are installed and running:

- **Defang CLI**: Install via npm, Homebrew, Winget, or `eval "$(curl -fsSL s.defang.io/install)"`
  - Verify with: `defang --version`
  - Prefer using MCP tools

## First Steps:

**IMPORTANT**:
Ensure that the step above ## Validate tools work is completed before proceeding to the steps below.

- Ask the user which cloud provider they want to use (AWS, GCP)
  - If AWS:
    - Use the steering file `getting-started-aws`
  - If GCP:
    - Use the steering file `getting-started-gcp`

# Available Steering Files

- `getting-started-aws`: Guide on setting up and deploying to AWS using Defang MCP
- `getting-started-gcp`: Guide on setting up and deploying to GCP using Defang MCP

# Best Practices

## Compose File

- The Docker Compose file is typically named `compose.yaml`.
- Top-level `version:` is deprecated, omit it.
- Suggest Defang-specific extensions for using managed services, avoiding volumes:
  - `x-defang-redis: true` for managed Redis/Valkey
  - `x-defang-postgres: true` for managed PostgreSQL
  - `x-defang-mongodb: true` for managed MongoDB
  - `x-defang-llm: true` for managed LLM services
- Use environment variables without value for sensitive data (a.k.a "config").
- Avoid hardcoding secrets in the compose file. Suggest using config.
- Use `depends_on` to define service startup order.
- Use healthchecks to ensure services are ready before dependent services start.
- Avoid underscores in project or service names; use hyphens instead.
- Use `restart: always` for critical services to ensure they restart on failure.
- Add a `deploy:` section with resource reservations.
