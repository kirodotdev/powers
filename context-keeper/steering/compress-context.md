---
inclusion: manual
---

# Compress Context — Session Summary Compression Guide

When the user triggers compression, consolidate older session summaries into a single compressed file.

## Steps

1. List all files in `.kiro/context-keeper/sessions/`.
2. Count session summary files (exclude `compressed-*.md` files from the count).
3. If fewer than **4 session files** exist, inform the user: "Not enough session summaries to compress (need at least 4, found {count})." and stop.
4. Sort session files lexicographically (chronological order due to ISO 8601 prefix).
5. Identify the **3 most recent** session files — these are preserved unchanged.
6. All remaining session files (and any existing `compressed-*.md` files) are candidates for merging.
7. Read each candidate file and extract:
   - **Key Decisions** — bullet points from the Key Decisions section
   - **Architectural Patterns** — bullet points from the Architectural Patterns section
   - **User Preferences** — bullet points from the User Preferences section
8. **Discard** from candidates: Session Metadata, Files Modified, Unresolved Questions, and Next Steps (these are session-specific).
9. **Deduplicate** extracted content across all candidate files (case-insensitive comparison, ignoring bullet markers).
10. Write the compressed summary to `.kiro/context-keeper/sessions/compressed-{timestamp}.md`
    - Timestamp format: `YYYY-MM-DDTHH-mm-ss`
11. Delete all candidate files (the ones that were merged).
12. Confirm to the user: "Compressed {count} session summaries into {filename}. {kept} most recent summaries preserved."

## Compressed Summary Format

```markdown
# Compressed Summary
- **Compressed At**: {ISO 8601 timestamp}
- **Source Sessions**: {count} sessions from {earliest date} to {latest date}

## Key Decisions
- {Deduplicated decision}

## Architectural Patterns
- {Deduplicated pattern}

## User Preferences
- {Deduplicated preference}
```

## Rules

- The compressed summary must be **150 lines or fewer**. If content exceeds this, truncate proportionally across sections.
- Always preserve the 3 most recent session files untouched.
- Delete originals only after the compressed file is successfully written.
- The minimum threshold is 4 session files. Below that, compression is skipped.
