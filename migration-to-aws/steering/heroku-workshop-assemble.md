---
_assemble: assemble-workshop
_of_phase: workshop
_reads:
  - sheet
  - refresh
  - compare
_produces:
  - scenarios/index.json
---

# Workshop — Assemble (sidebar resolve)

> Marks the workshop sidebar resolved and returns control to the backbone.
> Does **not** set `current_phase` to `workshop` (forbidden for sidebars).

## When exiting to Generate

1. Set `preferences.workshop.active` to `false` (keep `active_scenario_id`).
2. Ensure `scenarios/index.json` exists (baseline-only is enough if user entered
   then exited without Apply).
3. Update `.phase-status.json`:
   - `phases.workshop` → `"completed"` (sidebar resolved — participated)
   - `current_phase` → `"generate"`
   - `last_updated` → now
4. Emit:

   ```
   HANDOFF_OK | phase=workshop | artifacts=scenarios/index.json | return_to=generate
   ```

5. Output: "Workshop paused. Active scenario: `{id}`. Proceeding toward Generate."

## When declining at Estimate offer (no entry)

Handled in `heroku-estimate-assemble.md` / `heroku-orchestrator.md` — set `phases.workshop` to
`"completed"` without requiring `scenarios/`. Participation signal = presence of
`scenarios/index.json`.

## Soft postcondition

If the user exits without any scenario directory (edge case), emit
`_warn_and_skip` for the scenarios postcondition and still mark workshop
`"completed"` + advance to generate — do not block Generate on an empty workshop.
