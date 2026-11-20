# Workshop — Assemble (sidebar resolve)

> Marks the workshop sidebar resolved and returns control to the backbone.
> Does **not** set `current_phase` to `workshop`.

## When exiting to Generate

1. Set `preferences.workshop.active` to `false` (keep `active_scenario_id`).
2. Ensure `scenarios/index.json` exists (baseline-only is enough).
3. Update `.phase-status.json` (read-merge-write):
   - `phases.workshop` → `"completed"`
   - `current_phase` → `"generate"`
   - `last_updated` → now
4. Emit:

   ```
   HANDOFF_OK | phase=workshop | artifacts=scenarios/index.json | return_to=generate
   ```

5. Output: "Workshop paused. Active scenario: `{id}`. Proceeding toward Generate."

## Soft postcondition

If scenarios are missing after an empty entry, warn and still mark workshop
`"completed"` + advance to generate — do not block Generate.
