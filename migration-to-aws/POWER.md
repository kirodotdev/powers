---
name: "migration-to-aws"
displayName: "GCP to AWS Migration Advisor"
description: "Expert guidance for migrating workloads from Google Cloud Platform to AWS. This no-cost tool assesses your current cloud provider's usage, geography, and billing data to estimate and compare AWS services and pricing, and recommends migration or continued use of your current provider. AWS pricing is based on current published pricing and may vary over time. The tool may generate a .migration folder containing comparison and migration execution data, which you may delete upon completion or use to migrate to AWS."
keywords: ["gcp", "aws", "migration", "cloud migration", "terraform", "re-platform", "cost estimation", "architecture"]
author: "AWS"
---

# GCP-to-AWS Migration Advisor

Migrate workloads from Google Cloud Platform to AWS with a 5-phase guided process: Terraform infrastructure discovery, requirements clarification, AWS architecture design, cost estimation, and execution planning. This no-cost tool assesses your current cloud provider's usage, geography, and billing data to estimate and compare AWS services and pricing, and recommends migration or continued use of your current provider. AWS pricing is based on current published pricing and may vary over time. The tool may generate a .migration folder containing comparison and migration execution data, which you may delete upon completion or use to migrate to AWS.


## Philosophy

- **Re-platform by default**: Select AWS services that match GCP workload types (e.g., Cloud Run → Fargate, Cloud SQL → RDS).
- **Dev sizing unless specified**: Default to development-tier capacity (e.g., db.t4g.micro, single AZ). Upgrade only on user direction.
- **Multi-signal approach**: Design phase adapts based on available inputs — Terraform IaC for infrastructure, billing data for service mapping, and app code for AI workload detection.

---

## Definitions

- **"Load"** = Read the file using the Read tool and follow its instructions. Do not summarize or skip sections.
- **`$MIGRATION_DIR`** = The run-specific directory under `.migration/` (e.g., `.migration/0226-1430/`). Set during Phase 1 (Discover).

---

## Prerequisites

**GCP sources** — User must provide at least one:

- **Terraform IaC**: `.tf` files (with optional `.tfvars`, `.tfstate`)
- **Application code**: Source files with GCP SDK or AI framework imports
- **Billing data**: GCP billing/cost/usage export files (CSV or JSON)

If none of the above are found, stop and ask user to provide at least one source type.

**AWS credentials** — Optional, improves cost estimation accuracy:

- The power uses `steering/cached-prices.md` as the primary pricing source (±5-10% for infra, ±15-25% for AI)
- When cached pricing is unavailable or stale, the power falls back to the AWS Pricing MCP server for live rates
- To enable the MCP fallback: configure valid AWS credentials locally (`aws configure` or `aws sso login`)
- Any AWS account with read-only access works — the AWS Pricing API is a public, read-only API and does not need to be the target migration account
- Required IAM permissions: `pricing:DescribeServices`, `pricing:GetAttributeValues`, `pricing:GetProducts`
- If neither cached pricing nor MCP is available, the Estimate phase will warn about reduced accuracy

---

## State Machine

This is the execution controller. After completing each phase, consult this table to determine the next action.

| Current State   | Condition | Next Action                     |
| --------------- | --------- | ------------------------------- |
| `start`         | always    | Load `steering/discover.md`     |
| `discover_done` | always    | Load `steering/clarify.md`      |
| `clarify_done`  | always    | Load `steering/design.md`       |
| `design_done`   | always    | Load `steering/estimate.md`     |
| `estimate_done` | always    | Load `steering/generate.md`     |
| `generate_done` | always    | Migration planning complete     |

**How to determine current state:** Read `$MIGRATION_DIR/.phase-status.json` → check `phases` object → find the last phase with value `"completed"`.

**Phase gate checks**: If prior phase incomplete, do not advance (e.g., cannot enter estimate without completed design).

**Feedback checkpoints**: Feedback is not a sequential phase — it is offered at two interleaved checkpoints (after Discover and after Estimate). See step 7 of **Workflow Execution** below for details.

---

## State Validation

When reading `$MIGRATION_DIR/.phase-status.json`, validate before proceeding:

1. **Multiple sessions**: If multiple directories exist under `.migration/`, list them with their phase status and ask: [A] Resume latest, [B] Start fresh, [C] Cancel.
2. **Invalid JSON**: If `.phase-status.json` fails to parse, STOP. Output: "State file corrupted (invalid JSON). Delete the file and restart the current phase."
3. **Unrecognized phase**: If `phases` object contains a phase not in {discover, clarify, design, estimate, generate, feedback}, STOP. Output: "Unrecognized phase: [value]. Valid phases: discover, clarify, design, estimate, generate, feedback."
4. **Unrecognized status**: If any `phases.*` is not in {pending, in_progress, completed}, STOP. Output: "Unrecognized status: [value]. Valid values: pending, in_progress, completed."

---

## State Management

Migration state lives in `$MIGRATION_DIR` (`.migration/[MMDD-HHMM]/`), created by Phase 1 and persisted across invocations.

**.phase-status.json schema:**

```json
{
  "migration_id": "0226-1430",
  "last_updated": "2026-02-26T15:35:22-05:00",
  "phases": {
    "discover": "completed",
    "clarify": "completed",
    "design": "in_progress",
    "estimate": "pending",
    "generate": "pending",
    "feedback": "pending"
  }
}
```

**Status values:** `"pending"` → `"in_progress"` → `"completed"`. Never goes backward.

The `.migration/` directory is automatically protected by a `.gitignore` file created in Phase 1.

---

## Phase Status Update Protocol

**Do not Read `.phase-status.json` before updating it.** You already know the current state because you are executing phases sequentially. Use the Write tool to write the **complete file** in the same turn as your final phase work (e.g., the output message announcing phase completion).

Example — after completing the Clarify phase, write `$MIGRATION_DIR/.phase-status.json` with:

```json
{
  "migration_id": "MMDD-HHMM",
  "last_updated": "2026-02-26T15:35:22-05:00",
  "phases": {
    "discover": "completed",
    "clarify": "completed",
    "design": "pending",
    "estimate": "pending",
    "generate": "pending",
    "feedback": "pending"
  }
}
```

Replace `MMDD-HHMM` with the actual migration ID, generate the `last_updated` ISO 8601 timestamp with local timezone offset yourself, and set each phase to its correct status at that point.

**Read `.phase-status.json` ONLY during session resume** (Step 0 of discover.md when checking for existing runs) or the feedback prerequisite check.

---

## File Writing Protocol

Many output files (JSON artifacts, Terraform configs, migration scripts) exceed 50 lines. When writing a file:

1. **If the content is 50 lines or fewer**: Write the entire file in a single operation.
2. **If the content exceeds 50 lines**: Write the first portion of the file (up to 50 lines), then append the remaining content in subsequent operations until the file is complete.
3. **Always verify**: After writing, confirm the file is valid (e.g., valid JSON for `.json` files). If the file was written in multiple parts, ensure no content was lost or duplicated at chunk boundaries.

This applies to all files written during any phase, including JSON artifacts, Terraform `.tf` files, migration scripts, and documentation.

---

## Phase Summary Table

| Phase        | Inputs                                                                                                                                                                   | Outputs                                                                                                                                                                                   | Reference                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| **Discover** | `.tf` files, app source code, and/or billing exports (at least one required)                                                                                             | `gcp-resource-inventory.json`, `gcp-resource-clusters.json`, `ai-workload-profile.json`, `billing-profile.json`, `.phase-status.json` updated (outputs vary by input)                     | `steering/discover.md`     |
| **Clarify**  | Discovery artifacts (`gcp-resource-inventory.json`, `gcp-resource-clusters.json`, `ai-workload-profile.json`, `billing-profile.json` — whichever exist)                  | `preferences.json`, `.phase-status.json` updated                                                                                                                                          | `steering/clarify.md`      |
| **Design**   | `preferences.json` + discovery artifacts                                                                                                                                 | `aws-design.json` (infra), `aws-design-ai.json` (AI), `aws-design-billing.json` (billing-only)                                                                                            | `steering/design.md`       |
| **Estimate** | `aws-design.json` or `aws-design-billing.json` or `aws-design-ai.json`, `preferences.json`                                                                               | `estimation-infra.json` or `estimation-ai.json` or `estimation-billing.json`, `.phase-status.json` updated                                                                                | `steering/estimate.md`     |
| **Generate** | `estimation-infra.json` or `estimation-ai.json` or `estimation-billing.json`, `aws-design.json` or `aws-design-billing.json` or `aws-design-ai.json`, `preferences.json` | `generation-infra.json` or `generation-ai.json` or `generation-billing.json` + `terraform/`, `scripts/`, `ai-migration/`, `MIGRATION_GUIDE.md`, `README.md`, `.phase-status.json` updated | `steering/generate.md`     |
| **Feedback** | `.phase-status.json` (discover completed minimum), all existing migration artifacts                                                                                      | `feedback.json`, `trace.json`, `.phase-status.json` updated                                                                                                                               | `steering/feedback.md`     |

---

## Defaults

- **IaC output**: Terraform configurations, migration scripts, AI migration code, and documentation
- **Region**: `us-east-1` (unless user specifies, or GCP region → AWS region mapping suggests otherwise)
- **Sizing**: Development tier (e.g., `db.t4g.micro` for databases, 0.5 CPU for Fargate)
- **Migration mode**: Adapts based on available inputs (infrastructure, AI, or billing-only)
- **Cost currency**: USD
- **Timeline assumption**: 8-12 weeks total

---

## MCP Servers

**awspricing** (for cost estimation):

- Provides `get_pricing`, `get_pricing_service_codes`, `get_pricing_service_attributes` tools
- Only needed during Estimate phase. Discover and Design do not require it.
- Primary pricing source: `steering/cached-prices.md` (cached rates, ±5-10% for infra, ±15-25% for AI). MCP is secondary — used only for services not found in the cache.

**Recommended setup** (better accuracy):

- AWS credentials configured locally (any valid AWS account with read-only access)
- Required IAM permissions: `pricing:DescribeServices`, `pricing:GetAttributeValues`, `pricing:GetProducts`
- The AWS Pricing API is a public, read-only API — any AWS account works, it does not need to be the target migration account
- Credentials must be active and not expired (refresh via `aws sso login` or `aws configure` as needed)

---

## Workflow Execution

When invoked, the agent **MUST follow this exact sequence**:

1. **Load phase status**: Read `.phase-status.json` from `.migration/*/`.
   - If missing: Initialize for Phase 1 (Discover)
   - If exists: Determine current phase based on phase field and status value

2. **Determine phase to execute**:
   - If status is `in_progress`: Resume that phase (read corresponding steering file)
   - If status is `completed`: Advance to next phase (read next steering file)
   - Phase mapping for advancement:
     - discover (completed) → Execute clarify (read `steering/clarify.md`)
     - clarify (completed) → Execute design (read `steering/design.md`)
     - design (completed) → Execute estimate (read `steering/estimate.md`)
     - estimate (completed) → Execute generate (read `steering/generate.md`)
     - generate (completed) → Migration complete

3. **Read phase reference**: Load the full steering file for the target phase.

4. **Execute ALL steps in order**: Follow every numbered step in the steering file. **Do not skip, optimize, or deviate.**

5. **Validate outputs**: Confirm all required output files exist with correct schema before proceeding.

6. **Update phase status**: Use the Phase Status Update Protocol (Write tool, no Read) in the same turn as the phase's final output message.

7. **Feedback checkpoint**: After a phase completes, check if feedback should be offered. This runs **before** advancing to the next phase.

   - **After Discover** (if `phases.feedback` is `"pending"`): Output to user:
     "Would you like to share quick feedback (5 optional questions + anonymized usage data) to help improve this tool? Your data never includes resource names, file paths, or account IDs.
     [A] Send feedback now
     [B] Wait until after the Estimate phase"
     - If user picks **A** → Load `steering/feedback.md`, execute it, then continue to Clarify.
     - If user picks **B** → Continue to Clarify (feedback stays `"pending"`).

   - **After Estimate** (if `phases.feedback` is `"pending"`): Output to user:
     "Would you like to share quick feedback now? (5 optional questions + anonymized usage data)
     [A] Yes, share feedback
     [B] No thanks, continue to Generate"
     - If user picks **A** → Load `steering/feedback.md`, execute it, then continue to Generate.
     - If user picks **B** → Set `phases.feedback` to `"completed"`, update `last_updated`. Continue to Generate.

   - **After Generate**: No feedback offer. If `phases.feedback` is still `"pending"`, set it to `"completed"` and update `last_updated` (user had two chances and chose to defer/skip).

8. **Display summary**: Show user what was accomplished, highlight next phase, or confirm migration completion.

**Critical constraint**: Agent must strictly adhere to the steering file's workflow. If unable to complete a step, stop and report the exact step that failed.

User can invoke the power again to resume from last completed phase.

---

## Error Conditions

| Condition                                                     | Action                                                                                                                                           |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| No GCP sources found (no `.tf`, no app code, no billing data) | Stop. Output: "No GCP sources detected. Provide at least one source type (Terraform files, application code, or billing exports) and try again." |
| `.phase-status.json` missing phase gate                       | Stop. Output: "Cannot enter Phase X: Phase Y-1 not completed. Start from Phase Y or resume Phase Y-1."                                           |
| awspricing unavailable after 3 attempts                       | Display user warning about ±5-25% accuracy. Use `steering/cached-prices.md`. Add `pricing_source: "cached"` to estimation.json.                  |
| User skips questions or says "use all defaults"               | Apply documented defaults from each category file. Phase 2 completes either way.                                                                 |
| `aws-design.json` missing required clusters                   | Stop Phase 4. Output: "Re-run Phase 3 to generate missing cluster designs."                                                                      |

---

## Files in This Power

```
migration-to-aws/
├── POWER.md                                    ← You are here (orchestrator + state machine)
├── mcp.json                                    # MCP server configuration
│
└── steering/
    │
    ├── # Phase orchestrators (linear flow)
    ├── discover.md                             # Phase 1: Discover orchestrator
    ├── clarify.md                              # Phase 2: Clarify orchestrator
    ├── design.md                               # Phase 3: Design orchestrator
    ├── estimate.md                             # Phase 4: Estimate orchestrator
    ├── generate.md                             # Phase 5: Generate orchestrator
    ├── feedback.md                             # Phase 6: Feedback orchestrator
    │
    ├── # Discover sub-files
    ├── discover-iac.md                         # IaC discovery (Terraform/K8s/Docker)
    ├── discover-app-code.md                    # App code discovery (SDK imports, AI detection)
    ├── discover-billing.md                     # Billing data discovery
    │
    ├── # Clarify sub-files
    ├── clarify-global.md                       # Category A: Global/Strategic (Q1-Q7)
    ├── clarify-compute.md                      # Categories B+C: Config Gaps + Compute (Q8-Q11)
    ├── clarify-database.md                     # Category D: Database (Q12-Q13)
    ├── clarify-ai.md                           # Category F: AI/Bedrock (Q14-Q22)
    ├── clarify-ai-only.md                      # Standalone AI-only migration flow
    │
    ├── # Design sub-files
    ├── design-infra.md                         # Infrastructure design (cluster-based)
    ├── design-ai.md                            # AI workload design (Bedrock)
    ├── design-billing.md                       # Billing-only design (fallback)
    │
    ├── # Estimate sub-files
    ├── estimate-infra.md                       # Infrastructure cost analysis
    ├── estimate-ai.md                          # AI workload cost analysis
    ├── estimate-billing.md                     # Billing-only cost ranges
    │
    ├── # Generate sub-files
    ├── generate-infra.md                       # Infrastructure migration plan
    ├── generate-ai.md                          # AI migration plan
    ├── generate-billing.md                     # Billing-only migration plan
    ├── generate-artifacts-infra.md             # Terraform configurations
    ├── generate-artifacts-scripts.md           # Migration scripts
    ├── generate-artifacts-ai.md                # Provider adapter + test harness
    ├── generate-artifacts-billing.md           # Skeleton Terraform with TODO markers
    ├── generate-artifacts-docs.md              # MIGRATION_GUIDE.md + README.md
    │
    ├── # Feedback sub-files
    ├── feedback-trace.md                       # Anonymized trace builder
    │
    ├── # Design reference files
    ├── design-ref-index.md                     # Lookup table: GCP type → design-ref file
    ├── design-ref-fast-path.md                 # Deterministic 1:1 mappings (Pass 1)
    ├── design-ref-compute.md                   # Compute mappings (Cloud Run, GCE, GKE, App Engine)
    ├── design-ref-database.md                  # Database mappings (Cloud SQL, Firestore, BigQuery, Redis)
    ├── design-ref-storage.md                   # Storage mappings (GCS → S3)
    ├── design-ref-networking.md                # Networking mappings (VPC, LB, DNS, Interconnect)
    ├── design-ref-messaging.md                 # Messaging mappings (Pub/Sub, Cloud Tasks)
    ├── design-ref-ai.md                        # AI/ML mappings (traditional ML → SageMaker)
    ├── design-ref-ai-gemini-to-bedrock.md      # Gemini → Bedrock model selection guide
    ├── design-ref-ai-openai-to-bedrock.md      # OpenAI → Bedrock model selection guide
    │
    ├── # Clustering algorithm files
    ├── clustering-classification-rules.md      # Primary/secondary classification rules
    ├── clustering-algorithm.md                 # Cluster formation rules (6 priority rules)
    ├── depth-calculation.md                    # Topological depth (Kahn's algorithm)
    ├── typed-edges-strategy.md                 # Edge type assignment (HCL reference parsing)
    │
    ├── # Schema files
    ├── schema-phase-status.md                  # .phase-status.json schema
    ├── schema-discover-iac.md                  # gcp-resource-inventory + clusters schemas
    ├── schema-discover-ai.md                   # ai-workload-profile schema
    ├── schema-discover-billing.md              # billing-profile schema
    ├── schema-estimate-infra.md                # estimation-infra.json schema
    │
    ├── # Pricing files
    └── cached-prices.md                        # Pre-fetched live AWS pricing (±5-10%, primary)
```

---

## Scope Notes

**v1.0 includes:**

- Terraform infrastructure discovery
- App code scanning (AI workload detection — Gemini, OpenAI, and other providers)
- Billing data import from GCP
- User requirement clarification (adaptive questions by category)
- Multi-path Design (infrastructure, AI workloads, billing-only fallback)
- AWS cost estimation (two-tier pricing: cached primary, MCP secondary)
- Migration artifact generation (Terraform, scripts, AI adapters, documentation)
- Optional feedback collection with anonymized telemetry

# Telemetry Disclosure

This power includes an **optional** feedback phase that collects anonymized usage data to help improve the tool. Telemetry is **off by default** and only runs if the user explicitly opts in at one of two feedback checkpoints (after the Discover phase or after the Estimate phase).

**What is collected:** Anonymous responses to 5 optional survey questions and aggregated migration metadata (e.g., number of resources discovered, migration path type, phases completed). See `steering/feedback-trace.md` for the full trace schema.

**What is never collected:** Resource names, file paths, account IDs, IP addresses, credentials, or any personally identifiable information.

**How to disable:** Simply decline the feedback prompt when offered by selecting option **[B]** at either checkpoint. No telemetry data is collected or transmitted unless you explicitly choose option **[A]**. If you do not respond to either checkpoint, feedback is automatically skipped after the Generate phase.

# Integrations

This power integrates with:
- [AWS Knowledge MCP Server](https://knowledge-mcp.global.api.aws) — for AWS documentation and service guidance
- [AWS Pricing MCP Server](https://github.com/awslabs/mcp/tree/main/src/aws-pricing-mcp-server) (Apache-2.0 license) — for live AWS cost estimation

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
