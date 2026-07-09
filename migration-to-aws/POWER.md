---
name: "migration-to-aws"
displayName: "GCP to AWS Migration Advisor"
description: "Migrate workloads from Google Cloud Platform to AWS — including AI and agentic workloads regardless of cloud provider. Triggers on: migrate from GCP, GCP to AWS, move off Google Cloud, migrate Terraform to AWS, migrate Cloud SQL to RDS, migrate GKE to EKS, migrate Cloud Run to Fargate, Google Cloud migration, migrate from OpenAI to Bedrock, move off OpenAI, switch from ChatGPT API to AWS, migrate from Gemini to Bedrock, migrate LangChain to Bedrock, migrate LangGraph to AWS, migrate agentic workloads to AWS, move AI workloads to AWS, migrate my AI app to AWS. Runs a 6-phase process: discover GCP resources from Terraform files, app code, or billing exports, clarify migration requirements, design AWS architecture, estimate costs, generate migration artifacts, and collect optional feedback. Clarify must finish before Design, Estimate, or Generate. Includes AI provider migration guidance (for example, OpenAI to Amazon Bedrock) by selecting closest-fit Bedrock model families for required modality, latency/quality targets, context windows, and cost constraints. Model mapping is compatibility-guided, not 1:1 parity; validate prompts, tool-calling behavior, and eval metrics before cutover. Do not use for: Azure or on-premises migrations to AWS, AWS-to-GCP reverse migration, general AWS architecture advice without migration intent, GCP-to-GCP refactoring, or multi-cloud deployments that do not involve migrating off GCP."
keywords: ["gcp", "aws", "migration", "cloud migration", "terraform", "re-platform", "cost estimation", "architecture", "bedrock", "openai", "gemini", "anthropic"]
author: "AWS"
---

# GCP-to-AWS Migration Advisor

## Philosophy

- **Re-platform by default**: Select AWS services that match GCP workload types (e.g., Cloud Run → Fargate, Cloud SQL → RDS).
- **Dev sizing unless specified**: Default to development-tier capacity (e.g., db.t4g.micro, single AZ). Upgrade only on user direction.
- **No human one-time migration costs**: Do not present human labor, professional services, or people-time work as dollar estimates or "one-time migration cost" budget categories. Vendor charges grounded in data (for example GCP data transfer egress in the infra estimate when billing exists) are allowed.
- **Multi-signal approach**: Design phase adapts based on available inputs — Terraform IaC for infrastructure, billing data for service mapping, and app code for AI workload detection.
- **BigQuery / `google_bigquery_*`**: The power **does not** recommend a specific AWS analytics or warehouse service. During **Clarify**, if discovery shows BigQuery (IaC `google_bigquery_*` and/or billing rows for BigQuery), you **must** surface the specialist advisory **before** Design (see `steering/clarify.md`). Design output uses **`Deferred — specialist engagement`**; keep directing the user to their **AWS account team** and/or a **data analytics migration partner** through Design, Estimate, and docs (see `steering/design-infra.md` BigQuery specialist gate).

---

## Definitions

- **"Load"** = Read the file using the Read tool and follow its instructions. Do not summarize or skip sections.
- **`$MIGRATION_DIR`** = The run-specific directory under `.migration/` (e.g., `.migration/0226-1430/`). Set during Phase 1 (Discover).

---

## Context Loading Rules

Each phase loads reference files on demand. To keep per-turn context manageable and prevent instruction-following degradation:

- **Budget:** Each phase should load no more than ~800 lines of instructions (excluding user artifacts like JSON profiles and MCP tool results).
- **Conditional loading:** Reference files with trigger conditions (e.g., `agentic_profile.is_agentic == true`) MUST NOT be loaded unless the condition is met. Do not speculatively load files.
- **No duplication:** Model mapping tables, pricing data, and shared warnings exist in one canonical file. Other files reference them; they do not copy them inline.
- **Progressive depth:** Phase orchestrators (`design.md`, `generate.md`) contain short routing logic that points to detailed sub-files. Load the sub-file only when its path is selected.

**Conditional reference files (load ONLY when condition is true):**

| File                                             | Condition                                                                                          |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `steering/design-ref-ai-gemini-to-bedrock.md`            | `ai-workload-profile.json` exists AND `summary.ai_source` = `"gemini"` or `"both"`                 |
| `steering/design-ref-ai-openai-to-bedrock.md`            | `ai-workload-profile.json` exists AND `summary.ai_source` = `"openai"` or `"both"`                 |
| `steering/design-ref-ai-anthropic-to-bedrock.md`         | `ai-workload-profile.json` exists AND `summary.ai_source` = `"anthropic"`                          |
| `steering/design-ref-ai.md`                              | `ai-workload-profile.json` exists AND `summary.ai_source` = `"other"`                              |
| `steering/design-ref-harness.md`              | `agentic_profile.is_agentic == true` AND `ai_constraints.agentic.migration_approach == "harness"`  |
| `steering/design-ref-agentic-to-agentcore.md` | `agentic_profile.is_agentic == true` AND `ai_constraints.agentic.migration_approach == "strands"`  |
| `steering/retarget-gotchas.md`                     | `agentic_profile.is_agentic == true` AND `ai_constraints.agentic.migration_approach == "retarget"` |

When adding new reference files, verify the phase's total loaded instructions remain under budget. If a new file would exceed ~800 lines when combined with other loaded refs, split it or make it conditional.

**Hybrid stack budget warning:**

When both `gcp-resource-inventory.json` AND `ai-workload-profile.json` exist, the combined design refs will approach the ~800-line budget. Output this warning to the user **before** loading the AI design refs:

> "⚠️ This is a large hybrid stack (infrastructure + AI workloads). To ensure complete and accurate recommendations, consider running the migration in two separate passes:
>
> **Pass 1 — Infrastructure:** Run with only your Terraform files to get infra mapping, Terraform generation, and cost estimates.
>
> **Pass 2 — AI workloads:** Run with only your application code to get Bedrock model recommendations, provider adapters, and AI migration artifacts.
>
> Continue with the combined run? (Y/N)"

If the user chooses to continue, proceed with the combined run. Load AI refs **after** infra refs to preserve infra instruction fidelity. If the user declines, stop and instruct them to re-run with a single input source type.

**This warning is advisory only** — it does not block the run.

---

## Prerequisites

User must provide at least one GCP source:

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

| Current State | Condition                                                             | Next Action                                                                            |
| ------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `discover`    | `phases.discover != "completed"`                                      | Load `steering/discover.md`                                          |
| `clarify`     | `phases.discover == "completed"` AND `phases.clarify != "completed"`  | Load `steering/clarify.md`                                            |
| `design`      | `phases.clarify == "completed"` AND `phases.design != "completed"`    | Load `steering/design.md`                                              |
| `estimate`    | `phases.design == "completed"` AND `phases.estimate != "completed"`   | Load `steering/estimate.md`                                          |
| `generate`    | `phases.estimate == "completed"` AND `phases.generate != "completed"` | Load `steering/generate.md`                                          |
| `complete`    | `phases.generate == "completed"` AND `phases.feedback == "pending"`   | Set `phases.feedback` to `"completed"` (user had two chances), then migration complete |
| `complete`    | `phases.generate == "completed"` AND `phases.feedback == "completed"` | Migration planning complete                                                            |

**How to determine current state (deterministic):**

1. Read `$MIGRATION_DIR/.phase-status.json`
2. If `current_phase` exists, use it (must match one of: discover, clarify, design, estimate, generate, complete)
3. Otherwise use ordered phase evaluation: `discover` → `clarify` → `design` → `estimate` → `generate`
4. Pick the **first** phase in that order where `phases.<phase> != "completed"`; if none, state is `complete`

**Phase gate checks**: If prior phase incomplete, do not advance (e.g., cannot enter estimate without completed design).

**Clarify is mandatory:** Do not load `steering/design.md`, `steering/estimate.md`, or `steering/generate.md` unless `$MIGRATION_DIR/.phase-status.json` exists and `phases.clarify` is exactly `"completed"`. A `preferences.json` file alone is **not** sufficient proof that Clarify ran. If the user asks to skip Clarify or jump straight to Design, cost estimate, or artifact generation, refuse briefly, then load `steering/clarify.md` and run Phase 2. There is no exception for "quick" or "obvious" migrations.

**Feedback checkpoints**: Feedback is not a sequential phase — it is offered at two interleaved checkpoints (after Discover and after Estimate). See step 8 of **Workflow Execution** below for details.

### Handoff Gate Orchestration (Fail Closed)

Load `steering/handoff-gates.md` when executing any phase completion step.

1. **Single `$MIGRATION_DIR`**: Use one run directory for the entire migration. Do not mix artifacts across `.migration/*/` sessions.
2. **Re-read from disk**: Before each phase (and before each handoff gate), Read required artifacts from `$MIGRATION_DIR/`. Do not rely on chat memory.
3. **Advance only on `HANDOFF_OK`**: A phase is complete only when its orchestrator emits `HANDOFF_OK | phase=<name> | artifacts=...`. Do not load the next phase without it.
4. **On `GATE_FAIL`**: Output the failure line(s) to the user in plain language. **Do NOT modify artifacts** to pass the gate. **Do NOT continue** to the next phase. Tell the user which phase to re-run.
5. **Re-entry**: Re-running an earlier phase after downstream phases completed requires explicit user confirmation; downstream phases must be reset to `"pending"`. See `handoff-gates.md` re-entry table.

Generate phase additionally loads `steering/validate-artifacts.md` before writing `migration-report.html`.

---

## State Validation

When reading `$MIGRATION_DIR/.phase-status.json`, validate before proceeding:

1. **Multiple sessions**: If multiple directories exist under `.migration/`, list them with their phase status and ask: [A] Resume latest, [B] Start fresh, [C] Cancel.
2. **Invalid JSON**: If `.phase-status.json` fails to parse, STOP. Output: "State file corrupted (invalid JSON). Delete the file and restart the current phase."
3. **Unrecognized phase**: If `phases` object contains a phase not in {discover, clarify, design, estimate, generate, feedback}, STOP. Output: "Unrecognized phase: [value]. Valid phases: discover, clarify, design, estimate, generate, feedback."
4. **Unrecognized status**: If any `phases.*` value is not in {pending, in_progress, completed}, STOP. Output: "Unrecognized status: [value]. Valid values: pending, in_progress, completed."
5. **Invalid `current_phase`** (if present): If `current_phase` is not in {discover, clarify, design, estimate, generate, complete}, STOP. Output: "Unrecognized current_phase: [value]. Valid values: discover, clarify, design, estimate, generate, complete."
6. **Out-of-order completion**: For ordered phases [discover, clarify, design, estimate, generate], if any later phase is `"completed"` while an earlier phase is not `"completed"`, STOP. Output: "Inconsistent phase ordering detected. Reconcile `.phase-status.json` before resuming."
7. **Multiple active phases**: Across core phases {discover, clarify, design, estimate, generate}, at most one phase may be `"in_progress"`. If >1, STOP. Output: "Multiple phases are in_progress. Keep only one active phase before resuming."

---

## State Management

Migration state lives in `$MIGRATION_DIR` (`.migration/[MMDD-HHMM]/`), created by Phase 1 and persisted across invocations.

**.phase-status.json schema:**

```json
{
  "migration_id": "0226-1430",
  "last_updated": "2026-02-26T15:35:22Z",
  "current_phase": "design",
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
For core phases (discover, clarify, design, estimate, generate), at most one phase may be `"in_progress"` at any time.
`current_phase` is optional but recommended; when present it is authoritative.

The `.migration/` directory is automatically protected by a `.gitignore` file created in Phase 1.

### Phase Status Update Protocol

Use **read-merge-write** updates for `.phase-status.json`:

1. Read the current file before every update.
2. Change only the phase keys being advanced and `last_updated`.
3. Keep prior completed phases unchanged.
4. Set `current_phase` to the next deterministic phase (or `complete` after generate).
5. Write the full file in the same turn as your final phase work message.

Example — after completing the Clarify phase, write `$MIGRATION_DIR/.phase-status.json` with:

```json
{
  "migration_id": "MMDD-HHMM",
  "last_updated": "2026-02-26T15:35:22Z",
  "current_phase": "design",
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

Replace `MMDD-HHMM` with the actual migration ID, generate the `last_updated` ISO 8601 UTC timestamp yourself, and set each phase to its correct status at that point.

---

## File Writing Protocol

Many output files (JSON artifacts, Terraform configs, migration scripts) exceed 50 lines. When writing a file:

1. **If the content is 50 lines or fewer**: Write the entire file in a single operation.
2. **If the content exceeds 50 lines**: Write the first portion of the file (up to 50 lines), then append the remaining content in subsequent operations until the file is complete.
3. **Always verify**: After writing, confirm the file is valid (e.g., valid JSON for `.json` files). If the file was written in multiple parts, ensure no content was lost or duplicated at chunk boundaries.

This applies to all files written during any phase, including JSON artifacts, Terraform `.tf` files, migration scripts, and documentation.

---

## Phase Summary Table

| Phase        | Inputs                                                                                                                                                                   | Outputs                                                                                                                                                                                                                                       | Reference                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **Discover** | `.tf` files, app source code, and/or billing exports (at least one required)                                                                                             | `gcp-resource-inventory.json`, `gcp-resource-clusters.json`, `ai-workload-profile.json`, `billing-profile.json`, `.phase-status.json` updated (outputs vary by input)                                                                         | `steering/discover.md` |
| **Clarify**  | Discovery artifacts (`gcp-resource-inventory.json`, `gcp-resource-clusters.json`, `ai-workload-profile.json`, `billing-profile.json` — whichever exist)                  | `preferences.json`, `.phase-status.json` updated                                                                                                                                                                                              | `steering/clarify.md`   |
| **Design**   | `preferences.json` + discovery artifacts                                                                                                                                 | `aws-design.json` (infra), `aws-design-ai.json` (AI), `aws-design-billing.json` (billing-only)                                                                                                                                                | `steering/design.md`     |
| **Estimate** | `aws-design.json` or `aws-design-billing.json` or `aws-design-ai.json`, `preferences.json`                                                                               | `estimation-infra.json` or `estimation-ai.json` or `estimation-billing.json`, `.phase-status.json` updated                                                                                                                                    | `steering/estimate.md` |
| **Generate** | `estimation-infra.json` or `estimation-ai.json` or `estimation-billing.json`, `aws-design.json` or `aws-design-billing.json` or `aws-design-ai.json`, `preferences.json` | `generation-infra.json` or `generation-ai.json` or `generation-billing.json` + `terraform/`, `scripts/`, `ai-migration/`, `validation-report.json` (when infra route active), `MIGRATION_GUIDE.md`, `README.md`, `.phase-status.json` updated | `steering/generate.md` |
| **Feedback** | `.phase-status.json` (discover completed minimum), all existing migration artifacts                                                                                      | `feedback.json`, `trace.json`, `.phase-status.json` updated                                                                                                                                                                                   | `steering/feedback.md` |

---

## MCP Servers

**awspricing** (for cost estimation):

- Provides `get_pricing`, `get_pricing_service_codes`, `get_pricing_service_attributes` tools
- Only needed during Estimate phase. Discover and Design do not require it.
- Primary pricing source: `steering/cached-prices.md` (cached 2026 rates, ±5-10% for infrastructure, ±15-25% for AI models). MCP is secondary — used only for services not found in the cache.

**Recommended setup** (better accuracy):

- AWS credentials configured locally (any valid AWS account with read-only access)
- Required IAM permissions: `pricing:DescribeServices`, `pricing:GetAttributeValues`, `pricing:GetProducts`
- The AWS Pricing API is a public, read-only API — any AWS account works, it does not need to be the target migration account
- Credentials must be active and not expired (refresh via `aws sso login` or `aws configure` as needed)

---

## Files in This Power

Kiro powers require a **flat** `steering/` directory — nested subdirectories are not loaded. All reference files live directly under `steering/`.

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
    ├── discover-iac.md                         # Terraform/IaC discovery
    ├── discover-app-code.md                    # App code discovery (SDK imports, AI detection)
    ├── discover-billing.md                     # Billing data discovery
    ├── discover-preview.md                     # Discovery preview for user review
    │
    ├── # Clarify sub-files
    ├── clarify-global.md                       # Category A: Global/Strategic (Q1-Q7)
    ├── clarify-compute.md                      # Categories B+C: Config Gaps + Compute (Q8-Q11)
    ├── clarify-database.md                     # Category D: Database (Q12–Q13b)
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
    ├── generate-artifacts-report.md            # migration-report.html
    │
    ├── # Feedback sub-files
    ├── feedback-trace.md                       # Anonymized trace builder
    │
    ├── # Design reference files
    ├── design-ref-index.md                     # Lookup table: GCP type → design-ref file
    ├── design-ref-fast-path.md                 # Deterministic 1:1 mappings (Pass 1)
    ├── design-ref-compute.md                   # Compute mappings (Cloud Run, GCE, GKE, App Engine)
    ├── design-ref-database.md                  # Database mappings (Cloud SQL, Spanner, Firestore, Redis)
    ├── design-ref-storage.md                   # Storage mappings (GCS, Filestore)
    ├── design-ref-networking.md                # Networking mappings (VPC, LB, DNS, Interconnect)
    ├── design-ref-messaging.md                 # Messaging mappings (Pub/Sub, Cloud Tasks)
    ├── design-ref-security.md                  # Security baseline (GuardDuty, CloudTrail, IMDSv2)
    ├── design-ref-ai.md                        # AI/ML mappings (Vertex AI → Bedrock)
    ├── design-ref-ai-gemini-to-bedrock.md      # Gemini → Bedrock model selection guide
    ├── design-ref-ai-openai-to-bedrock.md      # OpenAI → Bedrock model selection guide
    ├── design-ref-ai-anthropic-to-bedrock.md   # Anthropic → Bedrock model selection guide
    ├── design-ref-harness.md                   # AgentCore Harness migration path
    ├── design-ref-agentic-to-agentcore.md      # Agentic → AgentCore / Strands path
    │
    ├── # Clustering algorithm files
    ├── clustering-classification-rules.md      # Primary/secondary classification rules
    ├── clustering-algorithm.md                 # Cluster formation rules
    ├── depth-calculation.md                    # Topological depth (Kahn's algorithm)
    ├── typed-edges-strategy.md                 # Edge type assignment (HCL reference parsing)
    │
    ├── # Shared / cross-phase
    ├── schema-phase-status.md                  # .phase-status.json schema
    ├── schema-discover-iac.md                  # gcp-resource-inventory + clusters schemas
    ├── schema-discover-ai.md                   # ai-workload-profile schema
    ├── schema-discover-billing.md              # billing-profile schema
    ├── schema-estimate-infra.md                # estimation-infra.json schema
    ├── handoff-gates.md                        # Fail-closed handoff protocol (GATE_FAIL / HANDOFF_OK)
    ├── validate-artifacts.md                   # Pre-report validation (Generate Step 0; read-only)
    ├── terraform-validation.md                 # Terraform artifact validation rules
    ├── migration-complexity.md                 # Complexity tier definitions (small/medium/large)
    ├── cached-prices.md                        # Cached AWS + source provider pricing (±5-25%, primary)
    ├── pricing-fallback.md                     # MCP fallback rules when cache missing
    ├── bedrock-quotas.md                       # Bedrock TPM/RPM quota awareness
    ├── ai-migration-guardrails.md              # AI migration safety rails
    ├── ai-model-lifecycle.md                   # Bedrock model lifecycle & deprecation policy
    ├── retarget-gotchas.md                     # Retarget path pitfalls (agentic)
    │
    ├── # Data
    └── sdk-capability-map.json                 # Deterministic SDK method → AI capability map
```

---

## Error Conditions

| Condition                                                     | Action                                                                                                                                                  |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No GCP sources found (no `.tf`, no app code, no billing data) | Stop. Output: "No GCP sources detected. Provide at least one source type (Terraform files, application code, or billing exports) and try again."        |
| `.phase-status.json` missing phase gate                       | Stop. Output: "Cannot enter Phase X: Phase Y-1 not completed. Start from Phase Y or resume Phase Y-1."                                                  |
| awspricing unavailable after 3 attempts                       | Display user warning about ±5-25% accuracy. Use `cached-prices.md`. Add `pricing_source: "cached_fallback"` to the applicable `estimation-*.json` file. |
| User skips questions or says "use defaults for the rest"      | Apply documented defaults for remaining questions in the current batch and all subsequent batches. Phase 2 completes either way.                        |
| `aws-design.json` missing required clusters                   | Stop Phase 4. Output: "Re-run Phase 3 to generate missing cluster designs."                                                                             |

---

## Defaults

- **IaC output**: Terraform configurations, migration scripts, AI migration code, and documentation
- **Region**: `us-east-1` (unless user specifies, or GCP region → AWS region mapping suggests otherwise)
- **Sizing**: Development tier (e.g., `db.t4g.micro` for databases, 0.5 CPU for Fargate)
- **Migration mode**: Adapts based on available inputs (infrastructure, AI, or billing-only)
- **Cost currency**: USD
- **Timeline assumption**: 2-16 weeks depending on migration complexity — small (2-6 weeks), medium (6-12 weeks), large (12-18 weeks). See `steering/migration-complexity.md` for tier definitions.

---

## Workflow Execution

When invoked, the agent **MUST follow this exact sequence**:

1. **Load phase status**: Read `.phase-status.json` from `.migration/*/`.
   - If missing: Initialize for Phase 1 (Discover)
   - If exists: Determine current phase using deterministic rules in **State Machine**

2. **Determine phase to execute**:
   - If `current_phase` exists: execute that phase.
   - Otherwise execute the first non-completed phase in ordered list: discover → clarify → design → estimate → generate.
   - If all ordered phases are completed: migration is complete (with feedback finalization rule).

3. **Read phase reference**: Load the full reference file for the target phase.

4. **Execute ALL steps in order**: Follow every numbered step in the reference file. **Do not skip, optimize, or deviate.**

5. **Validate outputs**: Confirm all required output files exist with correct schema before proceeding. Phase orchestrators run **Completion Handoff Gate** checks per `steering/handoff-gates.md`.

6. **Handoff gate**: Emit `HANDOFF_OK` or `GATE_FAIL` per `steering/handoff-gates.md`. On `GATE_FAIL`, stop — do not update phase status or load the next phase.

7. **Update phase status**: Only after `HANDOFF_OK`. Use the Phase Status Update Protocol (read-merge-write) in the same turn as the phase's final output message.

8. **Feedback checkpoint**: After a phase completes, check if feedback is due (see rules below). This runs **before** advancing to the next phase.

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
     - If user picks **B** → Use the Phase Status Update Protocol to set `phases.feedback` to `"completed"`. Continue to Generate.

   - **After Generate**: No feedback offer. If `phases.feedback` is still `"pending"`, use the Phase Status Update Protocol to set it to `"completed"` (user had two chances and chose to defer/skip).

9. **Display summary**: Show user what was accomplished, highlight next phase, or confirm migration completion.

**Critical constraint**: Agent must strictly adhere to the reference file's workflow. If unable to complete a step, stop and report the exact step that failed.

User can invoke the power again to resume from `current_phase` (or deterministic ordered evaluation when `current_phase` is absent).

---

## Scope Notes

**v1.0 includes:**

- Terraform infrastructure discovery
- App code scanning (AI workload detection — Gemini, OpenAI, Anthropic, and other providers)
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
