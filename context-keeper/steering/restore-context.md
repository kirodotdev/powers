---
inclusion: manual
---

# Restore Context — Session Context Loading Guide

When a new session starts, load prior context from the session store and present it to the agent.

## Steps

1. Detect the current git branch using `git rev-parse --abbrev-ref HEAD`. If detection fails, use `unknown`.
2. Sanitize the branch name (same rules as capture: replace unsafe chars with hyphens).
3. List all files in `.kiro/context-keeper/sessions/`.
4. **Select the most recent session summary:**
   - Filter for files whose filename contains the sanitized branch name (exclude `compressed-` files).
   - If matching files exist, select the most recent (lexicographically last).
   - If no files match the current branch, fall back to the most recent file from any branch.
5. **Load Project Memory:** If `.kiro/context-keeper/project-memory.md` exists, read it.
6. **Load Compressed Summary:** If any `compressed-*.md` file exists in the sessions directory, read the most recent one.
7. Present all loaded context in clearly labeled sections (see format below).

## Presentation Format

```
--- Prior Session Context ---
{Contents of the selected session summary}
--- End Prior Session Context ---

--- Project Memory ---
{Contents of project-memory.md}
--- End Project Memory ---

--- Historical Context (Compressed) ---
{Contents of the compressed summary}
--- End Historical Context ---
```

## Rules

- If the selected summary is from a **different branch** than the current branch, add a note: `(Source: {branch-name} branch)` after the "Prior Session Context" header.
- If **no session summaries exist**, proceed silently. Do not display an error or empty sections.
- If **Project Memory does not exist**, skip that section silently.
- If **no Compressed Summary exists**, skip that section silently.
- Only present sections that have content.
