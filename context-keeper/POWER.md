---
name: "context-keeper"
displayName: "Context Keeper"
description: "Preserves session context across chat windows — automatically captures summaries when sessions end, restores them when new sessions begin, and maintains a persistent project memory file for long-term knowledge."
keywords: ["context", "session", "summary", "memory", "history", "continuity", "branch", "project-memory"]
author: "Logesh"
---

# Context Keeper

## Onboarding

This power preserves your session context across Kiro chat windows. It works automatically — no configuration needed.

### What gets installed

- **4 hooks** that automate context capture and restore
- **5 steering files** that guide the agent through each workflow

### How it works

1. **Auto-capture** (`agentStop`): When a session ends, the agent summarizes key decisions, files modified, patterns, preferences, and next steps into a structured markdown file in `.kiro/context-keeper/sessions/`.
2. **Auto-restore** (`promptSubmit`): When a new session starts, the agent loads the most recent summary (preferring the current git branch) plus the project memory and any compressed history.
3. **Manual snapshot** (`userTriggered`): Trigger anytime to save a point-in-time snapshot of the current session context.
4. **Compress** (`userTriggered`): Consolidate older session summaries into a single compressed file to keep the store lean.

### Session store location

- Session summaries: `.kiro/context-keeper/sessions/`
- Project memory: `.kiro/context-keeper/project-memory.md`

## Steering

### Capture context
- workflow: capture-context
- description: Guides the agent to generate a structured session summary with 7 sections, write it to the session store, update project memory, and clean up old files.
- file: steering/capture-context.md

### Restore context
- workflow: restore-context
- description: Guides the agent to find the most recent branch-scoped summary, load project memory and compressed history, and present all as labeled context.
- file: steering/restore-context.md

### Snapshot context
- workflow: snapshot-context
- description: Guides the agent to create a manual point-in-time snapshot using the same structured format.
- file: steering/snapshot-context.md

### Update project memory
- workflow: project-memory-update
- description: Guides the agent to append new learnings to the persistent project memory file without duplicating existing content.
- file: steering/project-memory-update.md

### Compress context
- workflow: compress-context
- description: Guides the agent to merge older session summaries into a single compressed file, deduplicating content and discarding resolved questions.
- file: steering/compress-context.md

## License and support

This power is open source (MIT). No data is collected or transmitted — all context is stored locally in your workspace.

- [License](https://github.com/logesh4v/context-keeper/blob/main/LICENSE)
- [Privacy Policy](https://github.com/logesh4v/context-keeper/blob/main/README.md#license) — No data collection; all files stay in your local `.kiro/` directory
- [Support / Issues](https://github.com/logesh4v/context-keeper/issues)
