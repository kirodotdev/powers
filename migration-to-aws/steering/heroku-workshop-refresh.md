---
_fragment: refresh
_of_phase: workshop
---

# Workshop — Refresh (patch → Design → Estimate → snapshot)

> Runs after the user confirms **Apply & reprice**, or for one-time **baseline
> capture** when `scenarios/index.json` is missing.

## Inner runs (artifact-only) — mandatory

Follow `workshop-invariants.md` § 3 (canonical
allowed/forbidden contract) for every inner Design/Estimate run. Heroku
specifics: leave `phases.design` and `phases.estimate` as `"completed"`;
the inner Estimate skips the post-Estimate workshop offer; `current_phase`
stays `"estimate"` until `heroku-workshop-assemble.md`.

## Baseline capture (no Design yet)

When `scenarios/` or `scenarios/index.json` is absent:

1. Compute `inventory_fingerprint` = SHA-256 hex of
   `$MIGRATION_DIR/heroku-resource-inventory.json` bytes.
2. Create `scenarios/`.
3. Copy working-tree artifacts to:
   - `scenarios/scenario-001.preferences.json`
   - `scenarios/scenario-001.aws-design.json`
   - `scenarios/scenario-001.estimation-infra.json`
4. Write `scenarios/scenario-001.json` manifest with
   `source: "baseline"`, `label: "baseline"`, fingerprints, and
   `estimation_summary` from current `estimation-infra.json`
   (`projected_costs.*`, `complexity_tier`, `pricing_source.status`,
   `workshop.region_note` or `null`).
5. Write `scenarios/index.json` with `baseline_scenario_id` /
   `active_scenario_id` = `scenario-001`, `max_scenarios: 5`.
6. Ensure `preferences.workshop` exists:
   `{ "active": true, "cpu_architecture": "<existing or x86_64>",
     "last_sheet_at": "<now>", "active_scenario_id": "scenario-001" }`
   Write preferences back if created/updated.
7. If this invocation was baseline-only (no sheet apply), **stop** and return to
   `heroku-workshop.md` to present the sheet.

## Apply & reprice

### 1. Inventory guard

Recompute inventory fingerprint. If it differs from
`scenarios/index.json.inventory_fingerprint`, **STOP**:

> Inventory changed since baseline. Re-run Discover before workshop reprice.

### 2. Stale Generate guard

If `.phase-status.json` has `phases.generate` (or later) `completed`, require
Estimate `_re_entry_guard` confirm and reset those phases to `pending` before
continuing.

### 3. Patch preferences

Apply sheet edits to `$MIGRATION_DIR/preferences.json`:

- Update knob paths from the sheet.
- Set `metadata.timestamp` to now.
- Set `workshop.active: true`, `workshop.last_sheet_at` to now,
  `workshop.cpu_architecture` from the sheet.
- Leave non-knob fields untouched.

### 4. Re-run Design (inner)

Execute Design per **Inner runs** above against the frozen inventory + patched
preferences. Overwrite `$MIGRATION_DIR/aws-design.json`. Do not touch inventory.

### 5. Re-run Estimate (inner)

Execute Estimate per **Inner runs** above. Overwrite
`$MIGRATION_DIR/estimation-infra.json`. Chat note only:
"Workshop reprice Estimate complete; returning to workshop loop."

### 6. Snapshot new scenario

1. Allocate next id: `scenario-00N` where N = max existing + 1 (zero-pad 3).
2. If `index.json.scenarios.length` would exceed 5, **before deleting**: warn the
   user with the scenario id and label that will be evicted (oldest non-baseline),
   then delete that scenario's manifest + three artifact copies and drop it from
   `index.json.scenarios[]`. Never delete `baseline_scenario_id` unless the user
   explicitly resets the workshop.
3. Copy working-tree preferences / aws-design / estimation-infra into
   `scenarios/{id}.*`.
4. Build `preferences_subset`: dot-paths whose values differ from
   `scenario-001.preferences.json` (workshop knobs only — region, availability,
   database_ha, redis_ha, compute_target.default, cost_optimization,
   workshop.cpu_architecture).
5. Write `scenarios/{id}.json` with `source: "workshop"`, label summarizing the
   subset (e.g. `arm64 + multi-az`), fingerprints, estimation_summary
   (include all three monthly tiers + `region_note` from estimation-infra if
   present).
6. Update `index.json`: append scenario, set `active_scenario_id`, set
   `preferences.workshop.active_scenario_id` to match; write preferences.

### 6b. Shareable calculator link (best-effort, never blocks)

Follow `workshop-invariants.md` § 6 with
`{SKILL_LABEL}` = "Heroku" — probe once, prefer `build_estimate` on the
scenario's Balanced-tier services, store the URL as
`estimation_summary.calculator_url`, null + one chat note on any failure.

### 7. Hand back

Return to `heroku-workshop.md` → run `heroku-workshop-compare.md`.
