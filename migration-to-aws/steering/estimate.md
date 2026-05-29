# Phase 4: Estimate AWS Costs (Orchestrator)

**Execute ALL steps in order. Do not skip or optimize.**

## Step 0: Pricing Mode Selection

Before running any sub-estimate file, determine the pricing source.

### Step 0a: Load Pricing Cache

Read `steering/cached-prices.md`. Check the `Last updated` date in the header:

- If <= 90 days old: **Cached prices are the primary source.** No MCP calls needed for services listed in the cache. Proceed to Step 1.
- If > 90 days old: Cache is stale. Attempt MCP (Step 0b) for fresh prices; use stale cache as fallback.

### Step 0b: MCP Availability Check (only if cache stale or service not listed)

Attempt to reach awspricing with **up to 2 retries** (3 total attempts):

1. **Attempt 1**: Call `get_pricing_service_codes()`
2. **If timeout/error**: Wait 1 second, retry (Attempt 2)
3. **If still fails**: Wait 2 seconds, retry (Attempt 3)
4. **If all 3 attempts fail**: Use cached prices with staleness warning

### Pricing Hierarchy

Each sub-estimate file uses this lookup order per service:

1. **`steering/cached-prices.md`** (primary) — Cached prices (±5-25% accuracy). Set `pricing_source: "cached"`. Used first because it requires zero API calls and covers most common services.
2. **MCP API** (fallback) — Real-time pricing for services NOT in cached-prices.md (±5-10% accuracy, more precise). Set `pricing_source: "live"`. Only called when the cache lacks the needed service or model.

If cache is > 90 days old and MCP is unavailable:

- Add warning: "Cached pricing data is >90 days old; accuracy may be significantly degraded"
- **Display to user**: Add visible warning with staleness notice

## Step 1: Prerequisites

Read `$MIGRATION_DIR/preferences.json`. If missing: **STOP**. Output: "Phase 2 (Clarify) not completed. Run Phase 2 first."

Check which design artifacts exist in `$MIGRATION_DIR/`:

- `aws-design.json` (infrastructure design from IaC)
- `aws-design-ai.json` (AI workload design)
- `aws-design-billing.json` (billing-only design)

If **none** of these artifacts exist: **STOP**. Output: "No design artifacts found. Run Phase 3 (Design) first."

## Step 2: Routing Rules

### Infrastructure Estimate

IF `aws-design.json` exists:

> Load `estimate-infra.md`

Produces: `estimation-infra.json`

### Billing-Only Estimate

IF `aws-design-billing.json` exists AND `aws-design.json` does **NOT** exist:

> Load `estimate-billing.md`

Produces: `estimation-billing.json`

### AI Estimate

IF `aws-design-ai.json` exists:

> Load `estimate-ai.md`

Produces: `estimation-ai.json`

### Mutual Exclusion

- **estimate-infra** and **estimate-billing** never both run (billing-only is the fallback when no IaC exists).
- **estimate-ai** runs independently of either estimate-infra or estimate-billing (no shared state). Run it after the infra/billing estimate completes.

## Phase Completion

After all applicable sub-estimates finish, use the Phase Status Update Protocol (Write tool) to write `.phase-status.json` with `phases.estimate` set to `"completed"` — **in the same turn** as the output message below.

Output to user: "Cost estimation complete. Proceeding to Phase 5: Generate Migration Artifacts."

## Reference Files

- `steering/cached-prices.md` — Cached AWS + source provider pricing (±5-25%, primary source)

## Scope Boundary

**This phase covers financial analysis ONLY.**

FORBIDDEN — Do NOT include ANY of:

- Changes to architecture mappings from the Design phase
- Execution timelines or migration schedules
- Terraform or IaC code generation
- Detailed migration procedures or runbooks
- Team staffing or resource allocation

**Your ONLY job: Show the financial picture of moving to AWS. Nothing else.**
