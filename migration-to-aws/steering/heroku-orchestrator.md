---
name: heroku-to-aws
description: "Migrate workloads from Heroku to AWS. Triggers on: migrate from Heroku, Heroku to AWS, move off Heroku, migrate Heroku app, migrate Heroku Postgres to RDS, migrate Heroku Redis to ElastiCache, migrate Heroku Kafka to MSK, migrate dynos to Elastic Beanstalk, migrate dynos to Fargate, Heroku migration, move from Heroku to AWS, migrate Heroku Private Space, Heroku to Elastic Beanstalk, Heroku to ECS, Heroku to Fargate, leave Heroku, migrate off Heroku platform, what-if workshop, reprice Heroku migration, compare migration scenarios, workshop mode. Runs a 6-phase process: discover Heroku resources live via the authenticated Heroku CLI (read-only, consent-gated) and/or from Terraform files, Procfile/app.json, and optional billing exports, clarify migration requirements, design AWS architecture, estimate costs, generate migration artifacts, and collect optional feedback. After Estimate, an optional what-if workshop can reprice region/HA/compute/Graviton scenarios without re-discovery. Clarify must finish before Design, Estimate, or Generate. Uses a flat resource model (no clustering or dependency graphs) with deterministic mapping tables for core services (Dynos → Elastic Beanstalk by default, Postgres → RDS/Aurora, Redis → ElastiCache, Kafka → MSK) and a fast-path table for 13+ common add-ons. Cedar/Fir generation detection is detect-only in v1. Pipeline/Review Apps are detect-only. Do not use for: GCP or Azure migrations to AWS, AWS-to-Heroku reverse migration, general AWS architecture advice without migration intent, Heroku-to-Heroku refactoring, or multi-cloud deployments that do not involve migrating off Heroku."
---

# Heroku-to-AWS Migration Skill

## Philosophy

- **Full platform exit by default**: Heroku is in sustaining engineering (KTLO) — stability and support only, no new investment. Enterprise contracts are no longer sold to new customers. This skill assumes complete departure from Heroku (compute, data, and add-ons) within a user-defined window. Do not recommend indefinite continued use of Heroku.
- **PaaS-to-PaaS by default, recommendation-shaped**: Elastic Beanstalk (Docker platform, AL2023) is the default compute target because it preserves Heroku's managed platform model (source deployment, platform-managed environments, and lower operational burden than direct container orchestration). Clarify presents a per-formation compute recommendation before asking for confirmation. Fargate remains the override for direct container control and is used automatically for horizontally scaled non-web processes that EB SingleInstance cannot preserve; EKS remains the override for teams with Kubernetes expertise. ECS Express Mode may be mentioned only as a forward-look for the Fargate override path, not as a replacement for the EB default. Do not recommend AWS App Runner (no longer accepting new customers as of April 2026).
- **Interim cutover is bounded**: If a user chooses data-first migration (database on AWS, app temporarily on Heroku), treat this as a bounded phase (weeks, not quarters). Require a target exit date and surface KTLO platform risk warnings.
- **Re-platform by default**: Select AWS services that match Heroku workload types (e.g., Dynos → Elastic Beanstalk, Heroku Postgres → RDS/Aurora, Heroku Redis → ElastiCache, Kafka → MSK).
- **Dev sizing unless specified**: Default to development-tier capacity (e.g., db.t4g.micro, single AZ). Upgrade only on user direction.
- **No human one-time migration costs**: Do not present human labor, professional services, or people-time work as dollar estimates or "one-time migration cost" budget categories. Vendor charges grounded in data (for example Heroku invoice line items in the infra estimate when billing exists) are allowed.
- **Live-first discovery, read-only and consent-gated**: The user's authenticated Heroku CLI is a first-class discovery source — most startups have no `heroku_*` Terraform, and the account is authoritative for what actually runs. Live capture is strictly read-only (an exact-command whitelist of list/info commands), requires explicit consent, never captures config var values (key names only), and never extracts the API token. Terraform files (`.tf` with `heroku_*` resources) and repo artifacts (Procfile, app.json) remain fully supported; when both live and Terraform data exist, live wins for current state, Terraform supplements structure and provenance, and disagreements are surfaced as drift — never silently resolved.
- **Flat resource model**: Heroku resources are organized per-app without dependency graphs or clustering. No topological sorting, typed edges, or cluster formation logic. Resources are processed as a flat list in input order.
- **Deterministic mappings**: Core services use fixed lookup tables (Dyno Type Table, Postgres Plan Table, Redis Plan Table, Kafka Plan Table). Common add-ons use the Fast-Path Table. Unknown add-ons hit the specialist gate.
- **DMS has Heroku constraints**: AWS DMS cannot perform continuous replication (CDC) with Heroku Postgres because Heroku does not grant the REPLICATION role. DMS is for one-time bulk migration with a cutover window only. The skill must surface this constraint when DMS is selected.
- **What-if after Estimate**: After costs are computed, SAs can enter an optional what-if workshop sidebar (`heroku-workshop.md`) to change region, HA, compute target, or CPU architecture (x86 vs Graviton), refresh Design + Estimate, and compare up to 5 priced scenarios — without re-running Discover. Region dollar deltas need awspricing MCP; without it, rates stay us-east-1-cache-based. Workshop arch defaults to **x86_64** here (EB tables historically x86-first).

---

## Definitions

- **"Load"** = Read the file using the Read tool and follow its instructions. Do not summarize or skip sections.
- **`$MIGRATION_DIR`** = The run-specific directory under `.migration/` (e.g., `.migration/0315-1030/`). Set during Phase 1 (Discover).

---

## Phase Structure (frontmatter)

Phase and unit files carry a YAML frontmatter block that declares how the phase is
composed — its inputs, the fragments it runs, the assembler that combines them,
what it produces, its gates, and what it requires/advances-to. The DSL interpreter
contract is the vendored `INTERPRETER.md`: it defines every
frontmatter key, the fragment/assembler model, and the interpreter loop. **Load it
first** (once, at the start of a migration), then execute a phase file's prose
body. Elsewhere in this skill, `INTERPRETER.md` (without a path) refers to this
same loaded contract.

Frontmatter is being introduced phase-by-phase; a phase file without it runs from
its prose as before.

---

## Context Loading Rules

Each phase loads reference files on demand. To keep per-turn context manageable and prevent instruction-following degradation:

- **Budget:** Each phase should load no more than ~800 lines of instructions (excluding user artifacts like JSON profiles and MCP tool results).
- **Conditional loading:** Reference files with trigger conditions MUST NOT be loaded unless the condition is met. Do not speculatively load files.
- **No duplication:** Mapping tables, pricing data, and shared warnings exist in one canonical file. Other files reference them; they do not copy them inline.
- **Progressive depth:** Phase orchestrators (`heroku-design.md`, `heroku-generate.md`) contain short routing logic that points to detailed sub-files. Load the sub-file only when its path is selected.

Each phase declares its own conditional reference/knowledge loads in frontmatter (a fragment `_trigger` or a `_knowledge` entry's `_when`); do not maintain a separate load-condition table here.

When adding new reference files, verify the phase's total loaded instructions remain under budget. If a new file would exceed ~800 lines when combined with other loaded refs, split it or make it conditional.

---

## Execution

This skill is driven by the interpreter loop in `INTERPRETER.md` (§ The interpreter
loop): it reads `.phase-status.json`, determines the current phase, runs each
phase's `_preconditions` / fragments / `_assemble` / `_postconditions`, advances on
`HANDOFF_OK` via `_advances_to`, and validates state. The phase set, ordering, and
gates are all derived from the phase files' frontmatter and `INTERPRETER.md` — they
are not restated here.

**Cold start (entry phase).** On a cold start — no `.migration/` run with a
`.phase-status.json` yet — begin at `heroku-discover.md`, this
skill's entry phase (the one carrying `_init: true`). The interpreter loads THIS
phase directly; it does not scan every phase's frontmatter to discover the root.
All subsequent phases are reached by following each phase's `_advances_to`. On a
warm start, `current_phase` in `.phase-status.json` is authoritative **except**
when deferred-advance sidebar resume applies (`INTERPRETER.md` § The
interpreter loop step 2 — Estimate completed + `workshop` pending/in_progress
must not re-run Estimate).

**Clarify is mandatory (heroku policy).** Do not skip Clarify or jump straight to
Design, Estimate, or Generate even if the user asks — there is no exception for
"quick" or "obvious" migrations. A `preferences.json` that was not produced by an
actual Clarify run does not count. If asked to skip, refuse briefly and run
Clarify.

---

## State Management

Migration state lives in `$MIGRATION_DIR` (`.migration/[MMDD-HHMM]/`), created on
the first phase and persisted across invocations. The state file is
`.phase-status.json`; its shape is defined by
`phase-status.schema.json`, and how it is created, validated, and
updated across the lifecycle is defined in `INTERPRETER.md` § The interpreter loop.
The `.migration/` directory is protected by a `.gitignore` created at init.

---

## MCP Servers

**awspricing** (for cost estimation):

- Provides `get_pricing`, `get_pricing_service_codes`, `get_pricing_service_attributes` tools
- Only needed during Estimate phase. Discover and Design do not require it.
- Primary pricing source: `aws-infra-pricing.json` (cached AWS infrastructure rates, ±5-10% for infrastructure). MCP is secondary — used only for services not found in the pricing file.

---

## Files in This Power

Every file below is a flat file in `steering/`. This power has no subdirectories;
steering files reference each other by bare filename.

```
steering/
├── heroku-orchestrator.md                # You are here (orchestrator + state machine)
├── heroku-discover.md                    # Phase 1: Discover orchestrator
├── heroku-discover-terraform.md          # Terraform discovery
├── heroku-discover-live-capture.md       # Live CLI capture (main-window pre-work, consent-gated)
├── heroku-discover-live.md               # Live discovery fragment (parses live-capture/)
├── heroku-discover-billing.md            # Billing data parsing
├── heroku-clarify.md                     # Phase 2: Adaptive questions (12–15, batched ≤5)
├── heroku-design.md                      # Phase 3: Design orchestrator (flat single-pass mapping)
├── heroku-estimate.md                    # Phase 4: Cost projection
├── heroku-workshop.md                    # Sidebar: optional post-Estimate what-if
├── heroku-workshop-sheet.md              # Assumption sheet knobs
├── heroku-workshop-refresh.md            # Patch prefs → Design → Estimate → snapshot
├── heroku-workshop-compare.md            # Side-by-side scenarios
├── heroku-workshop-assemble.md           # Resolve sidebar → return to Generate
├── heroku-generate.md                    # Phase 5: Generate orchestrator
├── heroku-generate-terraform.md          # Terraform configurations
├── heroku-generate-docs.md               # MIGRATION_GUIDE.md + README.md
├── heroku-generate-report.md             # migration-report.html (stakeholder + scenarios)
├── heroku-generate-eks.md                # EKS manifests when design has EKS
├── heroku-feedback.md                    # Phase 6: Feedback collection (reuses shared)
├── heroku-pricing-cache.md               # Heroku plan pricing (source-side baseline)
├── heroku-schema-discover-heroku.md      # heroku-resource-inventory.json schema
├── heroku-schema-workshop-scenarios.md   # scenarios/ + preferences.workshop contract
├── heroku-dyno-eb-sizing.json            # Dyno type → Elastic Beanstalk EC2 instance type
├── heroku-dyno-fargate-sizing.json       # Dyno type → Fargate CPU/memory
├── heroku-eks-pod-sizing.json            # Dyno type → EKS pod sizing + node selection
├── heroku-postgres-rds-sizing.json       # Postgres plan → RDS/Aurora sizing
├── heroku-redis-elasticache-sizing.json  # Redis plan → ElastiCache sizing
├── heroku-kafka-msk-sizing.json          # Kafka plan → MSK sizing
└── heroku-fast-path-addons.json          # Add-on → AWS deterministic mappings (13+ entries)
```

| Condition                                                | Action                                                                                                                                                                    |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.phase-status.json` missing phase gate                  | Stop. Output: "Cannot enter Phase X: Phase Y-1 not completed. Start from Phase Y or resume Phase Y-1."                                                                    |
| awspricing unavailable after 3 attempts                  | Display user warning about ±5-10% accuracy. Use `aws-infra-pricing.json`. Add `pricing_source: "cached_fallback"` to `estimation-infra.json`. |
| User skips questions or says "use defaults for the rest" | Apply documented defaults for remaining questions. Phase 2 completes either way.                                                                                          |
| Dyno type not in selected compute sizing table           | Reject mapping for that formation. Output: "Unsupported dyno type: {type}. Cannot map to target compute service."                                                         |
| Add-on not in Fast-Path Table                            | Mark as "Deferred — specialist engagement". No automated mapping produced.                                                                                                |

## Defaults

- **IaC output**: Terraform configurations, migration scripts, and documentation
- **Region**: `us-east-1` (unless user specifies otherwise)
- **Sizing**: Development tier (e.g., `db.t4g.micro` for databases, 0.5 CPU for Fargate)
- **Migration mode**: Adapts based on available inputs (live CLI discovery recommended, Terraform supported, Procfile/app.json supplementary, billing optional)
- **Cost currency**: USD
- **Timeline assumption**: 2-16 weeks depending on migration complexity — small (2-6 weeks), medium (6-12 weeks), large (12-18 weeks). Complexity tiers are classified per `complexity-tiers.json`.

## Feedback & Sharing Sidebars

The interpreter loop (`INTERPRETER.md` § The interpreter loop) drives phase
sequencing, gates, and state. This section defines only the heroku-specific
sidebar orchestration: WHERE the optional `workshop` and `feedback`
sidebars are offered (placement is orchestration prose, not part of the phase
contract). Both are `_kind: sidebar` — off-backbone, trigger-entered, never
`current_phase`.

> **Plan-share links are GATED OFF.** The share landing page
> (`https://aws.amazon.com/startups/migrate/connect`) is not yet live (404). Do
> NOT offer, generate, or present a share link at any sidebar. The share-link
> spec is preserved in `heroku-feedback-collect.md` Step 3
> (itself gated) for when the page ships; restoring the share prompts here is the
> un-gating change.

- **After Discover**: No prompt. Proceed directly to Clarify.

- **After Estimate**: First offer the what-if workshop sidebar per
  `heroku-estimate-assemble.md` (Enter workshop / Proceed toward Generate). Outer
  Estimate keeps `current_phase: estimate` until workshop is resolved (entered
  then exited via `heroku-workshop-assemble.md`, or declined). If the user enters
  workshop, follow `heroku-workshop.md`. Then, if
  `phases.feedback` is `"pending"`:

  ```
  Would you like to share quick feedback? (5 optional questions +
  anonymized usage data — never resource names, file paths, or
  account IDs)

  [A] Yes, share feedback
  [B] No thanks, continue to Generate
  ```

  - If user picks **A** → Load `heroku-feedback.md`, execute it. Set `phases.feedback` to `"completed"`. Continue to Generate.
  - If user picks **B** → Set `phases.feedback` to `"completed"`. Continue to Generate.

- **Workshop resume (mandatory):** If `current_phase == "estimate"` AND
  `phases.estimate == "completed"` AND `phases.workshop` is `"pending"` or
  `"in_progress"`, **do not recompute Estimate**. If `"pending"`, re-present the
  post-Estimate workshop offer from `heroku-estimate-assemble.md`. If `"in_progress"`,
  load `heroku-workshop.md`. Generate must wait until
  `phases.workshop == "completed"` (entered+exited or declined).

- **Warm start / explicit what-if**: If the user says "what if", "reprice",
  "workshop mode", or "compare scenarios" and Estimate artifacts already exist,
  load `heroku-workshop.md` directly (respect Generate
  `_re_entry_guard` when Terraform was already produced). Knobs on the pilot
  sheet: region, HA, compute target, cost optimization, CPU architecture
  (x86 vs Graviton). There is no traffic-multiplier knob in v1.

- **After Generate**: No prompt. If `phases.feedback` is still `"pending"`, set it to `"completed"` and mark the migration complete.

**Critical constraint**: Follow each phase reference file's workflow exactly. If unable to complete a step, stop and report the specific issue. Do not fabricate or infer data.
