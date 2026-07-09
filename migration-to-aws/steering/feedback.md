# Phase 6: Feedback (Optional)

Builds an anonymized usage trace and directs the user to the Pulse survey form.

**Execute ALL steps in order. Do not skip or deviate.**

## Prerequisites

Read `$MIGRATION_DIR/.phase-status.json`. Verify `phases.discover == "completed"`. If not: **STOP**. Output: "Feedback requires at least the Discover phase to be completed."

## Step 1: Build Trace

Load `steering/feedback-trace.md` and execute it. This produces `$MIGRATION_DIR/trace.json`.

If trace building fails: log the error, set `trace_included` to `false`, and skip to Step 3.

## Step 2: Show Trace and Provide Instructions

Read `$MIGRATION_DIR/trace.json` and display it pretty-printed so the user can see exactly what data is included:

```
--- Anonymized Trace (what will be shared) ---

<pretty-printed trace.json>

--- End Trace ---

This trace contains only aggregate counts, enum values, and timing data.
No resource names, file paths, account IDs, or secrets are included.
```

Then output the single-line minified version for copy-paste:

```
--- Copy the line below and paste it into the "Migration trace (optional)" field ---

<trace.json as single-line minified JSON — no newlines, no extra whitespace>

--- End ---
```

Then provide the survey link:

```
Open the feedback form in your browser:
https://pulse.amazon/survey/JWX45QZH

Answer the 5 quick questions in the form, then paste the trace line above
into the "Migration trace (optional)" field and submit.
```

## Step 3: Write feedback.json

Write `$MIGRATION_DIR/feedback.json`:

```json
{
  "timestamp": "<ISO 8601>",
  "survey_url": "https://pulse.amazon/survey/JWX45QZH",
  "phases_completed_at_feedback": ["<list of completed phases>"],
  "trace_included": true
}
```

If trace building failed: set `"trace_included": false`.

## Step 4: Update Phase Status

Use the Phase Status Update Protocol (Write tool) to write `.phase-status.json` with `phases.feedback` set to `"completed"` — **in the same turn** as the output message below.

Output to user: "Thank you for helping improve this tool."

After feedback completes, return control to the workflow execution in POWER.md. The calling checkpoint determines whether to advance to the next phase or end the migration.
