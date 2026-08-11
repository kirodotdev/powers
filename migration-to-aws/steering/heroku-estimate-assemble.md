---
_assemble: assemble-estimation
_of_phase: estimate
_reads:
  - cost-engine (fragment contribution)
_produces:
  - estimation-infra.json
---

# Estimate — Assemble and Validate estimation-infra.json

> **Assembler unit.** Runs after the cost-engine fragment (`heroku-estimate-cost-engine.md`)
> has computed the full financial picture. It assembles the final
> `estimation-infra.json`, enforces the completion handoff gate (including the
> Property-16 total invariant + every-service-priced check), updates
> `.phase-status.json`, and presents the summary. It owns the artifact-level
> contract for this phase.

---

## Output: Write `estimation-infra.json`

Assemble the full artifact conforming to `estimation-infra.schema.json`
(that schema is the field contract — do not re-enumerate it here). Each section is the
corresponding output the cost-engine fragment computed: `pricing_source` +
`current_costs` (Part 1), `projected_costs` (Parts 2/2B), `cost_comparison` (Part 3),
`migration_cost_considerations` (Part 4), `roi_analysis` (Part 5),
`optimization_opportunities` (Part 6), `complexity_tier` + `complexity_inputs`
(Part 7), and `recommendation` (Part 8).

The assembler additionally DERIVES the `financial_summary` roll-up (not produced by
any single cost-engine Part; the schema leaves its shape open):

```json
{
  "financial_summary": {
    "current_heroku_monthly": "<N or null>",
    "projected_aws_balanced_monthly": "<N>",
    "projected_aws_optimized_monthly": "<N>",
    "monthly_savings_balanced": "<heroku - balanced, negative = AWS more expensive>",
    "monthly_savings_optimized": "<heroku - optimized>",
    "annual_savings_optimized": "<× 12>",
    "recommendation": "<summary sentence>"
  }
}
```

Sign convention: savings = Heroku minus AWS (positive = you save by migrating).
This is deliberately the OPPOSITE sign of
`roi_analysis.recurring_savings.monthly_difference_*` (difference = AWS minus
Heroku) — same fact, savings-vs-difference framing. When presenting either,
always label the direction in words; never print a bare signed value.

Also attach optional workshop metadata when present (does not affect Property-16):

```json
{
  "workshop": {
    "scenario_id": "<preferences.workshop.active_scenario_id or null>",
    "region_note": "<from cost-engine, or null>"
  }
}
```

Write to `$MIGRATION_DIR/estimation-infra.json`.

---

## Completion Handoff Gate (Fail Closed)

The completion checks are declared in this phase's `_postconditions` frontmatter
and enforced per `INTERPRETER.md` § Gate protocol: **re-read `estimation-infra.json`
from disk**, run the mechanical checks (`_check_file_exists` / `_validate_json`) and
the `_assert` judgment checks (recommendation shape, the Property-16 total-invariant,
every-service-priced, complexity tier), then emit `GATE_FAIL` (do NOT patch artifacts;
STOP) or `HANDOFF_OK | phase=estimate | artifacts=estimation-infra.json`.

One check needs this fragment's context: `estimation-infra.json` must also pass
`estimation-infra.schema.json` validation (the schema shape) — verify that as part
of the `_validate_json` postcondition.

### Inner workshop reprice — skip this gate's state transition

When invoked from `heroku-workshop-refresh.md` (inner reprice): write
`estimation-infra.json`, optionally soft-check Property-16, present a brief
summary, then **return to the workshop loop**. Do **not** emit `HANDOFF_OK`, do
**not** update `.phase-status.json`, do **not** offer the what-if workshop below.

---

## Present Summary

After writing `estimation-infra.json`, present a concise summary to the user:

1. **Pricing source and accuracy** — State cache age and accuracy range
2. **Heroku baseline vs AWS projected** (balanced tier) — one-line comparison (if a baseline was determined, labeled with its source; include the derived-baseline caveat when the source is not billing data)
3. **Three-tier table**: Premium, Balanced, Optimized with monthly totals
   - Premium: _Highest resilience / highest monthly estimate_
   - Balanced: _Default scenario; compare Heroku to this first_
   - Optimized: _Lower estimate; reservations / Spot trade-offs assumed_
   - One-line note: Three figures are pricing scenarios for the same architecture (not three Terraform stacks). Generated Terraform aligns with Balanced.
4. **Per-service cost breakdown** (balanced tier, 1 line per service)
5. **Migration complexity**: tier + timeline range
6. **Monthly and annual savings** (or increase) vs Heroku per tier (if a baseline was determined)
7. **Top 2-3 optimization opportunities** with savings potential
8. **Recommendation**: `path_label` with one-line justification

Keep under 25 lines. The user can ask for details or re-read `estimation-infra.json`.

---

## Phase status after outer Estimate (deferred Generate advance)

After outer-run `HANDOFF_OK` (not an inner workshop reprice):

1. Mark `phases.estimate` → `"completed"`.
2. Ensure `phases.workshop` exists (seed `"pending"` if the key is missing).
3. **Do not** set `current_phase` to `"generate"` yet — leave `current_phase` at
   `"estimate"` until the workshop sidebar is resolved (entered then exited, or
   declined). This matches sidebar semantics: workshop never owns
   `current_phase`, and mid-workshop fixtures correctly stay on `estimate`.
4. Offer the what-if workshop below.

---

## Post-Estimate: What-If Workshop Offer

After outer-run `HANDOFF_OK`, the summary above, and the deferred phase-status
update — offer:

```
Estimate complete. Before Generate, you can run a what-if workshop:
change region, HA, compute target, or CPU architecture (x86 vs Graviton)
and compare priced scenarios without re-discovering inventory.

[A] Enter what-if workshop
[B] Proceed toward Generate
```

- **A** → Load `heroku-workshop.md` (sidebar) and follow it
  (baseline capture if `scenarios/` missing, then the sheet). Keep
  `current_phase: estimate`; set `phases.workshop` → `"in_progress"`.
- **B** → Mark `phases.workshop` → `"completed"` (resolved/declined — no
  `scenarios/` required). Set `current_phase` → `"generate"`. Continue with the
  Feedback/Generate sidebars in `heroku-orchestrator.md`.

On first workshop entry after this Estimate, `heroku-workshop-refresh.md` baseline
capture snapshots the current artifacts as `scenario-001` before any edits.
