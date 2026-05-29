# .phase-status.json

Lightweight phase tracking. This is the SINGLE source of truth for the `.phase-status.json` schema. All steering files reference this definition.

```json
{
  "migration_id": "0226-1430",
  "last_updated": "2026-02-26T15:35:22Z",
  "phases": {
    "discover": "completed",
    "clarify": "completed",
    "design": "in_progress",
    "estimate": "pending",
    "generate": "pending",
    "feedback": "pending"
  }
}
```

**Field Definitions:**

| Field           | Type     | Set When                                                         |
| --------------- | -------- | ---------------------------------------------------------------- |
| `migration_id`  | string   | Created (matches folder name, never changes)                     |
| `last_updated`  | ISO 8601 | After each phase update                                          |
| `phases.<name>` | string   | Phase transitions: `"pending"` → `"in_progress"` → `"completed"` |

**Rules:**

- Phase status progresses: `"pending"` → `"in_progress"` → `"completed"`. Never goes backward.
- Valid phase names: discover, clarify, design, estimate, generate, feedback.
- `migration_id` matches the `$MIGRATION_DIR` folder name (e.g., `0226-1430`).
