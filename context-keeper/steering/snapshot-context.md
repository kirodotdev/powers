---
inclusion: manual
---

# Snapshot Context — Manual Context Capture Guide

When the user triggers a manual snapshot, generate a session summary and save it with a `-manual` suffix.

## Steps

1. Detect the current git branch using `git rev-parse --abbrev-ref HEAD`. If detection fails, use `unknown`.
2. Sanitize the branch name (same rules as capture: replace unsafe chars with hyphens).
3. Generate a summary using the exact same 7-section format defined in `steering/capture-context.md`.
4. Write the summary to `.kiro/context-keeper/sessions/{timestamp}-{sanitized-branch}-manual.md`
   - Timestamp format: `YYYY-MM-DDTHH-mm-ss` (hyphens instead of colons)
   - Create the `.kiro/context-keeper/sessions/` directory if it doesn't exist.
5. Confirm the save to the user by displaying the file path.

## Rules

- Follow the same 150-line cap and "None captured" rules as automatic capture.
- Manual snapshots count toward the 20-file limit in the session store.
- The `-manual` suffix goes after the branch name: `{timestamp}-{branch}-manual.md`
