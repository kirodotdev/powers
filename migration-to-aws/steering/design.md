# Phase 3: Design AWS Architecture (Orchestrator)

**Execute ALL steps in order. Do not skip or optimize.**

## Prerequisites

Read `$MIGRATION_DIR/preferences.json`. If missing: **STOP**. Output: "Phase 2 (Clarify) not completed. Run Phase 2 first."

Check which discovery artifacts exist in `$MIGRATION_DIR/`:

- `gcp-resource-inventory.json` (IaC discovery ran)
- `gcp-resource-clusters.json` (IaC discovery ran)
- `billing-profile.json` (billing discovery ran)
- `ai-workload-profile.json` (AI workloads detected)

If **none** of these artifacts exist: **STOP**. Output: "No discovery artifacts found. Run Phase 1 (Discover) first."

## Routing Rules

### Infrastructure Design (IaC-based)

IF `gcp-resource-inventory.json` AND `gcp-resource-clusters.json` both exist:

→ Load `design-infra.md`

Produces: `aws-design.json`

### Billing-Only Design (fallback)

IF `billing-profile.json` exists AND `gcp-resource-inventory.json` does **NOT** exist:

→ Load `design-billing.md`

Produces: `aws-design-billing.json`

### AI Workload Design

IF `ai-workload-profile.json` exists:

→ Load `design-ai.md`

Produces: `aws-design-ai.json`

### Mutual Exclusion

- **design-infra** and **design-billing** never both run (billing-only is the fallback when no IaC exists).
- **design-ai** runs independently of either design-infra or design-billing (no shared state). Run it after the infra/billing design completes.

## Phase Completion

After all applicable sub-designs finish, use the Phase Status Update Protocol (Write tool) to write `.phase-status.json` with `phases.design` set to `"completed"` — **in the same turn** as the output message below.

Output to user: "AWS Architecture designed. Proceeding to Phase 4: Estimate Costs."

## Reference Files

Sub-design files may reference rubrics in `steering/`:

- `steering/design-ref-index.md` — GCP type → rubric file lookup
- `steering/design-ref-fast-path.md` — Deterministic 1:1 GCP→AWS mappings
- `steering/design-ref-compute.md` — Compute service rubric
- `steering/design-ref-database.md` — Database service rubric
- `steering/design-ref-storage.md` — Storage service rubric
- `steering/design-ref-networking.md` — Networking service rubric
- `steering/design-ref-messaging.md` — Messaging service rubric
- `steering/design-ref-ai.md` — AI/ML service rubric

## Scope Boundary

**This phase covers architecture mapping ONLY.**

FORBIDDEN — Do NOT include ANY of:

- Cost calculations or pricing estimates
- Execution timelines or migration schedules
- Terraform or IaC code generation
- Risk assessments or rollback procedures
- Team staffing or resource allocation

**Your ONLY job: Map GCP resources to AWS services. Nothing else.**
