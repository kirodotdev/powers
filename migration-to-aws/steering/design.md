# Phase 3: Design AWS Architecture (Orchestrator)

**Execute ALL steps in order. Do not skip or optimize.**

## Prerequisites

1. Read `$MIGRATION_DIR/.phase-status.json`. If missing, invalid, or `phases.clarify` is not exactly `"completed"`: **STOP**. Output: "Phase 2 (Clarify) not completed or phase state is missing/invalid. Run `steering/clarify.md` until Clarify finishes and `.phase-status.json` shows `phases.clarify`: `completed`."
2. Read `$MIGRATION_DIR/preferences.json`. If missing: **STOP**. Output: "Phase 2 (Clarify) not completed. Run Phase 2 first."

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

Before marking Design complete, enforce route output gates (fail closed):

1. Determine which design routes ran:
   - IaC route: `gcp-resource-inventory.json` AND `gcp-resource-clusters.json` exist
   - Billing-only route: `billing-profile.json` exists AND `gcp-resource-inventory.json` does NOT exist
   - AI route: `ai-workload-profile.json` exists
2. Require at least one route to be active. If none active: STOP.
3. For each active route, require its expected artifact:
   - IaC route -> `aws-design.json`
   - Billing-only route -> `aws-design-billing.json`
   - AI route -> `aws-design-ai.json`
4. If any active route is missing its expected output: STOP and output: "Design route [name] did not produce required artifact(s). Re-run the failed sub-design before completing Phase 3."

## Completion Handoff Gate (Fail Closed)

Load `steering/handoff-gates.md`. **Re-read from disk** each active route artifact before checking.

**Re-entry guard:** If `estimation-infra.json` (or sibling estimate artifacts) exists and `phases.estimate` is `"completed"`: STOP unless the user explicitly confirms re-running Design. Emit `GATE_FAIL | phase=design | field=estimation-infra.json | reason=stale_downstream`.

**On any route gate FAIL:** Emit `GATE_FAIL | phase=design | field=<artifact> | reason=missing`. **Do NOT modify artifacts to pass the gate.** **Do NOT update `.phase-status.json`.**

**On PASS:** Emit `HANDOFF_OK | phase=design | artifacts=<comma-separated active design files>`.

After `HANDOFF_OK`, use the Phase Status Update Protocol (read-merge-write) to update `.phase-status.json` — **in the same turn** as the output message below:

- Set `phases.design` to `"completed"`
- Set `current_phase` to `"estimate"`

Output to user: "AWS Architecture designed. Proceeding to Phase 4: Estimate Costs."

## Reference Files

Sub-design files may reference rubrics in the `steering/design-ref-*.md` files:

- `steering/design-ref-index.md` — GCP type → rubric file lookup
- `steering/design-ref-fast-path.md` — Direct (table) mappings vs rubric path; **User-facing vocabulary** for presenting `confidence` to users (**Standard pairing** / **Tailored to your setup** / **Estimated from billing only**)
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
