---
inclusion: manual
---

# Capture Context — Session Summary Guide

When a session ends, generate a structured summary of the session and save it to the session store.

## Steps

1. Detect the current git branch using `git rev-parse --abbrev-ref HEAD`. If detection fails, use `unknown`.
2. Sanitize the branch name for use in filenames: replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|` with hyphens. Collapse consecutive hyphens. Trim leading/trailing hyphens.
3. Generate the summary following the format below.
4. Write the summary to `.kiro/context-keeper/sessions/{timestamp}-{sanitized-branch}.md`
   - Timestamp format: `YYYY-MM-DDTHH-mm-ss` (hyphens instead of colons)
   - Create the `.kiro/context-keeper/sessions/` directory if it doesn't exist.
5. After writing, follow the `steering/project-memory-update.md` guide to update the project memory file.
6. Run cleanup: if more than 20 files exist in the sessions directory, delete the oldest files (sorted lexicographically) to bring the count back to 20.

## Summary Format

The summary must contain exactly these 7 sections in this order:

```markdown
# Session Summary

## Session Metadata
- **Session Start**: {ISO 8601 timestamp}
- **Session End**: {ISO 8601 timestamp}
- **Workspace**: {absolute path to workspace root}
- **Branch**: {original branch name, not sanitized}

## Key Decisions
- {Decision with one-sentence rationale}

## Files Modified
- `{relative/path/to/file}` — {one-line description of change}

## Architectural Patterns
- {Pattern observed or discussed}

## User Preferences
- {Preference expressed by the user}

## Unresolved Questions
- {Question that was raised but not resolved}

## Next Steps
- {Action item for the next session}
```

## Rules

- If no content exists for a section, include the heading with the text `None captured`. Never omit a section.
- Keep the summary to **150 lines or fewer**. If content exceeds this, truncate proportionally across sections.
- Both automatic and manual summaries count toward the 20-file limit.
