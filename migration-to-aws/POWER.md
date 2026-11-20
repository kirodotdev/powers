---
name: "migration-to-aws"
displayName: "Migrate to AWS"
description: "Migrate workloads to AWS from Google Cloud Platform or Heroku, migrate AI/LLM code to Amazon Bedrock, and decide how to run AI agents on AWS. Triggers on: migrate from GCP, GCP to AWS, move off Google Cloud, migrate Terraform to AWS, migrate Cloud SQL to RDS, migrate GKE to EKS, migrate Cloud Run to Fargate, migrate Vertex AI to SageMaker, migrate Cloud Spanner to Aurora, migrate Firestore to DynamoDB, migrate Pub/Sub to SNS or SQS, migrate BigQuery off Google Cloud, Google Cloud migration, migrate from Heroku, Heroku to AWS, move off Heroku, migrate dynos to Elastic Beanstalk, migrate dynos to Fargate, migrate Heroku Postgres to RDS, migrate Heroku Redis to ElastiCache, migrate Heroku Kafka to MSK, leave Heroku, migrate from OpenAI to Bedrock, move off OpenAI, switch from ChatGPT API to AWS, migrate from Gemini to Bedrock, migrate from Anthropic API to Bedrock, migrate LangChain to Bedrock, migrate LangGraph to AWS, migrate CrewAI or AutoGen agents to AWS, migrate my AI app to AWS, which runtime for my agent, AgentCore vs ECS vs EKS vs Lambda, AgentCore vs Lambda MicroVMs, deploy an AI agent on AWS, agent architecture on AWS, move my agents to AWS, agent migration plan, add AgentCore services, add memory or gateway or identity to my agent, migrate Temporal workers to AWS, Temporal to AWS, Temporal Cloud to AWS, what-if workshop, reprice migration scenarios, compare GCP and AWS pricing. Routes to one of four migration engines and runs a phased process with fail-closed handoff gates: discover the source workload, clarify requirements, design the AWS target, estimate cost, and generate migration artifacts (Terraform, scripts, adapters, documentation, and reports). Cost estimates use a cached pricing table as the primary source with the AWS Pricing MCP server as a secondary lookup. AI model mapping is compatibility-guided, not 1:1 parity; validate prompts, tool-calling behavior, and eval metrics before cutover. Do not use for: Azure or on-premises migrations to AWS, AWS-to-GCP or AWS-to-Heroku reverse migration, general AWS architecture advice without migration intent, same-cloud refactoring, or multi-cloud deployments that do not involve migrating onto AWS."
keywords:
  [
    "gcp",
    "google cloud",
    "aws",
    "heroku",
    "migration",
    "cloud migration",
    "terraform",
    "re-platform",
    "cost estimation",
    "cost comparison",
    "architecture",
    "vertex ai",
    "bigquery",
    "cloud sql",
    "cloud run",
    "spanner",
    "firestore",
    "pub/sub",
    "gke",
    "aurora",
    "elasticache",
    "msk",
    "dynos",
    "add-ons",
    "bedrock",
    "openai",
    "gemini",
    "anthropic",
    "langchain",
    "langgraph",
    "crewai",
    "autogen",
    "agentcore",
    "ai agents",
    "agent runtime",
    "lambda microvms",
    "llm migration",
    "temporal",
    "temporal cloud",
  ]
author: "AWS"
---

# Migrate to AWS

A router over four migration engines plus one shared authoring guide. This file selects the
engine and holds the conventions every engine shares. **The engine's own orchestrator owns
its phase flow** — load it and follow it.

## Engines

| Engine                | Orchestrator                            | Source → target                                                        | Run directory     |
| --------------------- | --------------------------------------- | ---------------------------------------------------------------------- | ----------------- |
| **gcp-to-aws**        | `steering/gcp-orchestrator.md`           | Google Cloud → AWS (infrastructure, AI workloads, billing-only)        | `.migration/`     |
| **heroku-to-aws**     | `steering/heroku-orchestrator.md`        | Heroku → AWS (dynos, Postgres, Redis, Kafka, add-ons)                  | `.migration/`     |
| **llm-to-bedrock**    | `steering/llm-orchestrator.md`           | OpenAI / Gemini / Anthropic SDK code → Amazon Bedrock                   | `.llm-migration/` |
| **agent-advisor**     | `steering/agent-advisor-orchestrator.md` | AI agent workloads → an AWS runtime (AgentCore, ECS, EKS, Lambda)      | `.agent-advisor/` |
| **tf-best-practices** | `steering/tf-best-practices.md`          | _Not standalone._ Shared Terraform posture rules + read-only policy gate | n/a               |

---

## Engine Selection

Evaluate in order and stop at the first match. State which engine you selected and why
before loading its orchestrator.

1. **Resuming a run?** If a run directory already exists with a `.phase-status.json`, resume
   that engine. Do not re-route mid-migration. See **Resuming** below.

2. **Agentic workload with a runtime question** → **agent-advisor**.
   The user is asking *where or how to run an AI agent*: runtime choice (AgentCore vs ECS vs
   EKS vs Lambda vs Lambda MicroVMs), agent architecture, an agent migration plan, a
   deployable POC, adding AgentCore capabilities (memory, gateway, identity, policy,
   observability) to agents already on AWS, or moving Temporal-orchestrated workers.
   Requires at least one genuinely agentic component — a system of only plain services,
   batch jobs, or HTTP endpoints is out of scope and its Clarify phase halts on a scope gate.

3. **AI/LLM SDK rewrite with no agent-architecture question** → **llm-to-bedrock**.
   The user wants provider code (OpenAI, Gemini, Anthropic) rewritten to Bedrock and handed
   back as a ready-to-merge branch, including output-quality evaluation. Not for runtime
   selection or agent architecture.

4. **Source cloud is Heroku** → **heroku-to-aws**.

5. **Source cloud is Google Cloud** → **gcp-to-aws**. This is also the engine for
   AI-provider migration guidance that arrives alongside infrastructure, and for AI-only
   runs that need design/estimate/artifact phases rather than a code rewrite.

**Ambiguous or mixed signals:** ask. Do not guess between engines. A stack that is both a
GCP infrastructure migration *and* an LLM rewrite is two passes, not one — see the hybrid
budget warning in `steering/gcp-orchestrator.md`.

**Cross-engine handoffs are explicit, never implicit:**

- agent-advisor's Migration Plan stage reuses the gcp-to-aws engine with the advisor's
  decisions carried over (`steering/agent-advisor-handoff-migration.md`,
  `steering/agent-advisor-migration-plan.md`).
- Any engine that writes a `terraform/` directory loads `steering/tf-best-practices.md`
  twice: once for posture rules before authoring, once for the read-only policy verdict
  after.

---

## Definitions

- **"Load"** = Read the file with the Read tool and follow its instructions. Do not
  summarize or skip sections.
- **`$STEERING`** = the **absolute** path of this power's `steering/` directory — the
  directory these reference files were loaded from. Resolve it once, before running any
  shell command that touches a shipped file. A power is installed outside the user's
  workspace (typically `~/.kiro/powers/installed/migration-to-aws/steering/`) while run
  directories are created inside it, so a workspace-relative path — a bare `steering/`
  prefix, or a `./scripts/` prefix — will **not** reach these files. The llm-to-bedrock engine also calls
  this `$SCRIPTS`, `$HELPERS`, and `<scriptsDir>`; agent-advisor's `$GCP_BASE` is the same
  directory too. All are the one flat directory.
- **`$MIGRATION_DIR`** = the run-specific directory for the gcp-to-aws and heroku-to-aws
  engines, e.g. `.migration/0226-1430/`. Set during Discover.
- **`$RUN_DIR`** = the run-specific directory for agent-advisor, e.g.
  `.agent-advisor/0630-1430/`. Set during Intake.
- **Engine** = one of the four migration workflows above. Each owns its own phase list,
  run directory, and state file.

Steering files reference each other by **bare filename** (`clarify.md`, not
`steering/clarify.md`) because Kiro loads `steering/` as a flat namespace. This file uses
the `steering/` prefix for clarity.

---

## Prerequisites

| Requirement            | Needed by                                          | Check                                                                 |
| ---------------------- | -------------------------------------------------- | --------------------------------------------------------------------- |
| `uv`                   | agent-advisor (scoring), llm-to-bedrock (all steps) | `uv --version`. If missing: `curl -LsSf https://astral.sh/uv/install.sh \| sh`, then stop. |
| AWS credentials (read) | Estimate phases, via the awspricing MCP server     | `aws sts get-caller-identity`                                         |
| `terraform`            | Generate phases that emit `terraform/`             | `terraform version`                                                   |
| `heroku` CLI (authed)  | heroku-to-aws live discovery (consent-gated)       | `heroku auth:whoami`                                                  |
| `gcloud` (authed)      | gcp-to-aws live discovery (consent-gated)          | `gcloud auth list`                                                    |

Live discovery for both cloud engines is **read-only and consent-gated**: an exact-command
allowlist of list/describe calls, no config-var values, no credential extraction. Ask before
running it.

---

## Context Loading Rules

These apply to every engine.

- **Budget:** a phase should load no more than ~800 lines of instructions, excluding user
  artifacts (JSON profiles) and MCP tool results.
- **Conditional loading:** a reference file with a trigger condition MUST NOT be loaded
  unless the condition holds. Do not speculatively load.
- **No duplication:** model-mapping tables, pricing data, and shared warnings live in one
  canonical file. Other files point at them.
- **Progressive depth:** phase orchestrators hold short routing logic; load a sub-file only
  once its path is selected.

Each engine's orchestrator carries its own conditional-load table. Honour it.

---

## Shared Conventions

### Handoff gates (fail closed)

Every phase ends by emitting `HANDOFF_OK` or `GATE_FAIL` per `steering/handoff-gates.md`.
On `GATE_FAIL`: **stop**. Do not update phase status, do not load the next phase, and report
the exact check that failed.

### Phase status

Run state lives in `.phase-status.json` inside the engine's run directory
(`steering/schema-phase-status.md`, and `steering/phase-status.schema.json` for the machine
form). Update it **only** after `HANDOFF_OK`, using read-merge-write in the same turn as the
phase's final output message. Never blind-write the whole file.

### Frontmatter DSL

The heroku-to-aws and agent-advisor engines compose phases from fragments declared in YAML
frontmatter. The execution contract is `steering/INTERPRETER.md` — load it once at the start
of a run, before executing any phase body.

### Phase dispatch (`_exec`)

Three phases — `heroku-discover`, `heroku-generate`, `agent-advisor-estimate` — declare
`_exec: {_agent: rw}`, meaning their work runs in an isolated sub-agent while the main
window keeps the gates, `_init`, and the state transition.

Dispatch to the generic `general-task-execution` sub-agent and hand it
`steering/generic-phase-worker-rw.md` as its contract, following the labeled context block
in `steering/INTERPRETER.md` § `_exec`. There is no per-tier registered agent to target, so
the `rw` capability tier is **advisory** here, not enforced — INTERPRETER.md's
platform-asymmetry note covers this: the tier is least-privilege intent, never a security
boundary. `rw` is the only tier this power ships a worker for.

The sub-agent returns `WORKER_DONE` or `WORKER_BLOCKED`. Neither is a handoff — re-read the
artifacts from disk and run the completion gate in the main window. The sub-agent must never
emit `HANDOFF_OK` or touch `.phase-status.json`. If dispatch is unavailable, run the phase
inline instead; behaviour is identical, only the context isolation is lost.

### File writing protocol

Many outputs (JSON artifacts, Terraform, scripts) exceed 50 lines.

1. **≤50 lines:** write in a single operation.
2. **>50 lines:** write the first ~50 lines, then append until complete.
3. **Always verify:** confirm the result is valid (e.g. parseable JSON) and that nothing was
   lost or duplicated at a chunk boundary.

### Cost estimation

`steering/cached-prices.md` is the **primary** pricing source (±5–10% infrastructure,
±15–25% AI models). The awspricing MCP server is **secondary**, for services absent from the
cache. On MCP failure, fall back per `steering/pricing-fallback.md` and record
`pricing_source: "cached_fallback"` in the applicable `estimation-*.json`.

Do not present human labour, professional services, or people-time as dollar estimates or a
"one-time migration cost". Vendor charges grounded in discovered data (e.g. GCP egress) are
allowed.

### Resuming

1. Look for existing run directories: `.migration/*/`, `.agent-advisor/*/`,
   `.llm-migration/*/`.
2. If exactly one exists, resume its engine from `current_phase`, or from the first
   non-completed phase when `current_phase` is absent.
3. If several exist, list them and ask which to resume.
4. Never re-route to a different engine mid-run.

---

## MCP Servers

| Server            | Used by                             | Purpose                                                                    |
| ----------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| **awsknowledge**  | all engines                         | AWS documentation and service guidance                                     |
| **awspricing**    | Estimate phases                     | Live pricing lookups for services missing from `steering/cached-prices.md`  |
| **temporal-docs** | agent-advisor (Temporal paths only) | Temporal documentation when the workload is Temporal-orchestrated           |

**awspricing setup** (improves accuracy):

- Any valid AWS account with read-only access — the Pricing API is public and does not need
  to be the target migration account.
- IAM: `pricing:DescribeServices`, `pricing:GetAttributeValues`, `pricing:GetProducts`.
- Credentials must be unexpired (`aws sso login` / `aws configure`).

Only the Estimate phases need awspricing. Discover, Clarify, and Design do not.

---

## Files in This Power

Kiro loads `steering/` as a **flat** directory — nested subdirectories are not read. Every
reference file therefore lives directly under `steering/`, namespaced by engine:

| Prefix                                                        | Engine                                       | Files |
| ------------------------------------------------------------- | -------------------------------------------- | ----- |
| _(unprefixed)_                                                | gcp-to-aws, plus the shared/canonical assets | 87    |
| `agent-advisor-`                                              | agent-advisor                                | 52    |
| `heroku-`                                                     | heroku-to-aws                                | 43    |
| `llm-`                                                        | llm-to-bedrock                               | 28    |
| `tf-`, `security-posture-rules.md`, `terraform-validation.md` | tf-best-practices                            | 4     |

214 files total: 178 `.md`, 24 `.json`, 11 `.py`, 1 `.template`.

The upstream plugin vendors copies of `skills/shared/**` into individual skills. Those copies
are byte-identical, so they collapse here onto one unprefixed canonical name each —
`INTERPRETER.md`, `workshop-invariants.md`, `pricing-mode.md`, `complexity-tiers.json`,
`estimation-infra.schema.json`, `aws-infra-pricing.json`, `phase-status.schema.json` — and
every engine points at the same file.

Naming rules, so a reference resolves predictably:

- **Phase orchestrator:** `<engine->discover.md`, `-clarify.md`, `-design.md`,
  `-estimate.md`, `-generate.md`, `-feedback.md` (gcp-to-aws is unprefixed).
- **Phase fragment / assembler:** `<phase>-<fragment>.md`, `<phase>-assemble.md`.
- **Design reference (gcp):** `design-ref-*.md`, indexed by `design-ref-index.md`.
- **Decision reference (agent-advisor):** `agent-advisor-<topic>.md`.
- **Schema (prose):** `schema-*.md`. **Schema (machine):** `*.schema.json`.
- **Sizing / pricing data:** `*.json`.
- **Executable helper:** `*.py`, invoked with `uv run`.

```
POWER.md          ← you are here (engine router + shared conventions)
mcp.json          MCP server configuration
steering/         214 flat reference files (see prefixes above)
tooling/          parity sync scripts (maintainers only, not loaded at runtime)
```

**Executable helpers.** 11 `.py` files ship in `steering/` and are invoked with `uv run
$STEERING/<name>.py` — an absolute path, per the `$STEERING` definition above. Three need
third-party packages — `llm-validate-result.py`
(`jsonschema`), `llm-preflight-bedrock.py` and `llm-bedrock-pricing.py` (`boto3`,
`botocore`) — and each declares them with PEP 723 inline metadata, so `uv run` resolves them
with no virtualenv setup. The rest are standard-library only.

`agent-advisor-scoring.py` is the one helper loaded as a **module** rather than run as a
script (agent-advisor's Clarify phase calls `scoring.score()` per unit). Its flat filename
contains hyphens, so it is not importable by name; the phase loads it by path with
`importlib.util.spec_from_file_location`. Do not rewrite that to a plain `import`.

`steering/design-ref-index.md` is the lookup table from a GCP resource type to its design
reference. Start there rather than guessing a filename.

---

## Error Conditions

| Condition                                              | Action                                                                                                                       |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| Cannot tell which engine applies                       | Ask. Present the engine table and let the user choose. Do not guess.                                                         |
| No source found for the selected engine                | Stop. Name the input types that engine accepts and ask for at least one.                                                      |
| Several run directories exist                          | List them and ask which to resume. Do not pick one silently.                                                                  |
| `.phase-status.json` shows an unmet phase gate         | Stop. Output: "Cannot enter Phase X: Phase X-1 not completed. Start from Phase X-1 or resume it."                             |
| `GATE_FAIL` from a handoff gate                        | Stop. Do not advance or update status. Report the failed check.                                                               |
| `uv` missing, and the engine needs it                  | Stop. Give the install command. agent-advisor and llm-to-bedrock cannot run without it.                                       |
| awspricing unavailable after 3 attempts                | Warn about ±5–25% accuracy, use `steering/cached-prices.md`, set `pricing_source: "cached_fallback"`.                         |
| agent-advisor finds no agentic component               | Halt on the scope gate and redirect to gcp-to-aws, heroku-to-aws, or llm-to-bedrock.                                          |
| User says "use defaults for the rest" during Clarify   | Apply documented defaults for the remaining questions in this and all later batches. The phase still completes.               |

---

## Defaults

- **Region:** `us-east-1`, unless the user specifies one or the source region maps elsewhere.
- **Sizing:** development tier (`db.t4g.micro`, single AZ, 0.5 vCPU Fargate). Upgrade only on
  user direction.
- **Posture:** re-platform to the closest managed AWS service rather than redesigning.
- **IaC output:** Terraform, plus migration scripts, adapters, and documentation.
- **Currency:** USD.
- **CPU architecture:** Graviton/arm64 for gcp-to-aws (`steering/graviton.md`); x86_64 for
  heroku-to-aws, whose sizing tables are x86-first.
- **Timeline:** 2–18 weeks by complexity tier — see `steering/migration-complexity.md`.

---

# Telemetry Disclosure

This power includes an **optional** feedback phase that collects anonymized usage data.
Telemetry is **off by default** and runs only if the user explicitly opts in at a feedback
checkpoint (after Discover, or after Estimate).

**Collected:** anonymous responses to 5 optional survey questions, plus aggregated migration
metadata (resource counts, migration path type, phases completed). Full schema in
`steering/feedback-trace.md`.

**Never collected:** resource names, file paths, account IDs, IP addresses, credentials, or
any personally identifiable information.

**To disable:** decline the prompt (option **[B]**) at either checkpoint. Nothing is
collected or transmitted without an explicit **[A]**. No response at either checkpoint means
feedback is skipped after Generate.

# Integrations

- [AWS Knowledge MCP Server](https://knowledge-mcp.global.api.aws) — AWS documentation and
  service guidance
- [AWS Pricing MCP Server](https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server)
  (Apache-2.0) — live AWS cost estimation
- [Temporal docs MCP server](https://temporal.mcp.kapa.ai) — Temporal documentation for
  agent-advisor's Temporal paths

Upstream source of the engine content:
[awslabs/startups → migrate](https://github.com/awslabs/startups/tree/main/migrate).

# License

```
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```
