---
inclusion: manual
---

# Project Memory Update Guide

After each session capture, update the persistent project memory file with new learnings.

## File Location

`.kiro/context-keeper/project-memory.md`

## Steps

1. Read the existing project memory file. If it doesn't exist, create it with the 5 section headings below (empty sections).
2. Review the session that just ended. Identify any new learnings about:
   - **Project Architecture** — directory structure, service boundaries, deployment topology
   - **Tech Stack** — languages, frameworks, databases, tools, versions
   - **Coding Conventions** — style preferences, naming conventions, import patterns
   - **Key Patterns** — design patterns, architectural patterns, data access patterns
   - **Team Preferences** — workflow preferences, review processes, commit conventions
3. For each new learning, check if it already exists in the project memory (case-insensitive comparison, ignoring bullet markers).
4. Append only genuinely new information under the appropriate section heading.
5. If the file exceeds **200 lines** after the update, consolidate: trim proportionally across sections, keeping the most recent entries (entries at the end of each section are more recent).

## Format

```markdown
# Project Memory

## Project Architecture
- {Learning about project structure}

## Tech Stack
- {Learning about technologies used}

## Coding Conventions
- {Learning about coding style}

## Key Patterns
- {Learning about design patterns}

## Team Preferences
- {Learning about team workflow}
```

## Rules

- Never rewrite the entire file. Only append new learnings.
- Never duplicate information that already exists.
- Keep entries as concise bullet points.
- The 200-line cap is enforced after every update.
