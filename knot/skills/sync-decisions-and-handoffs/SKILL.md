---
name: "sync-decisions-and-handoffs"
description: "Save verified architectural decisions, implementation state, superseding constraints, and cross-AI task handoffs from Kiro back to Knot so ChatGPT, Claude, Amazon Quick, and teammates read current truth. Use when completing a Kiro spec or implementation task, superseding an earlier design assumption, or handing work to another AI assistant."
license: "MIT"
compatibility: "Works with Kiro IDE, Kiro CLI, and Agent Plugins v1.0.0 clients"
metadata:
  author: "ConnectKnot"
  version: "1.0.0"
---

# Sync Kiro Decisions and Handoffs Back to Knot

## Overview

Context continuity only works when Kiro also writes verified engineering truth back upstream. When Kiro finishes implementing a feature, discovers a technical constraint, or updates an architectural assumption, other tools (ChatGPT, Claude, Gemini, Cursor, Amazon Quick, or Amazon Connect agents) remain stale until Knot records the updated state.

This skill guides Kiro through committing atomic decisions, cleanly superseding outdated `v1` claims (`v1 -> v2`), updating work threads, and passing structured task handoffs back through Knot.

## Prerequisites Checklist

- [ ] Changes or decisions have been verified locally (for example, specs approved or automated tests passed).
- [ ] Target scope (`personal` or specific `shared_knot_id`) is confirmed via `knot_list_scopes`.
- [ ] Statements contain zero raw API keys, passwords, tokens, or unredacted PII/PCI data.

## Step-by-Step Guide

### 1. Choose the Right Write Tool

| What Happened in Kiro | Knot Tool | Persistence Scope |
| :--- | :--- | :--- |
| One verified decision, fact, or constraint | `propose_context` | Durable context item (with lineage) |
| Multiple atomic items across one project | `batch_propose_context` | Multiple durable items in one call |
| Live progress update on a work thread | `report_active_state` | Time-bounded activity log |
| Accepting or finishing an incoming task | `update_handoff_status` | Handoff lifecycle update |
| Passing follow-up work to ChatGPT/Claude/Cursor | `create_handoff` | Structured cross-AI task |

### 2. Commit Durable Decisions and Supersede Outdated Rules

Always provide an `entity_hint`, `kind` (`fact`, `decision`, `constraint`, `goal`, or `project_state`), `idempotency_key`, and concise `rationale`.

#### Replacing a Superseded Rule (`v1 -> v2`)

Never leave an obsolete rule active alongside a newer decision. Always read the target item ID first via `get_relevant_context`, confirm with the user if changing shared team truth, and pass `supersedes_context_id` (or `updates_ref` such as `"K1"`):

```json
// Tool: propose_context
{
  "entity_hint": "OrderStream Webhook Service",
  "kind": "project_state",
  "statement": "Implemented OrderStream AWS EventBridge webhook handler in src/webhookHandler.ts enforcing v2 PCI guardrails (HTTP 422 PCI_CDE_PAYLOAD_REJECTED, max 3 exponential-backoff retries, AWS KMS metadata envelope) with passing node --test suite.",
  "subject_key": "orderstream-implementation-status",
  "rationale": "All unit tests pass locally after hydrating .kiro/specs/orderstream-webhooks/ from Knot.",
  "confidence": "high",
  "idempotency_key": "kiro-orderstream-impl-2026-11-24"
}
```

```json
// Tool: propose_context (superseding an existing context ID)
{
  "entity_hint": "OrderStream Webhook Service",
  "kind": "decision",
  "statement": "Use AWS SQS dead-letter queue with 14-day retention for retries exceeding 3 exponential-backoff attempts.",
  "supersedes_context_id": "<prior-context-uuid>",
  "subject_key": "orderstream-dlq-policy",
  "rationale": "Updated after EventBridge retry testing in Kiro.",
  "confidence": "high",
  "idempotency_key": "kiro-orderstream-dlq-v2"
}
```

#### Writing Into a Shared Knot

When writing into a team Shared Knot (`shared_knot_id` set or active):
1. Ask the user to confirm before overwriting or adding shared team decisions if the change impacts other teammates or downstream services.
2. If Knot holds a write for shared-scope confirmation (`personal_in_shared_scope` or similar confirmation prompt), re-submit with `confirm_shared: true` only after user confirmation.
3. If Knot returns `needs_clarification` with `related` item IDs, inspect each candidate:
   - Pass `supersedes_context_id` if the new item replaces an older item.
   - Pass `coexists_with_context_ids` (listing independent related IDs) if both facts remain true side-by-side.

#### Batch Writes (`batch_propose_context`)

Use `batch_propose_context` when recording 2 to 5 distinct atomic facts after completing a milestone (for example: one `decision`, one `constraint`, and one `project_state`). Keep one atomic fact per item.

```json
// Tool: batch_propose_context
{
  "shared_knot_id": "<optional-shared-knot-uuid>",
  "idempotency_key": "kiro-milestone-sync-2026-11-24",
  "items": [
    {
      "entity_hint": "OrderStream Webhook Service",
      "kind": "decision",
      "statement": "Validate incoming webhook signatures using HMAC-SHA256 before JSON parsing.",
      "subject_key": "orderstream-hmac-verification",
      "confidence": "high"
    },
    {
      "entity_hint": "OrderStream Webhook Service",
      "kind": "project_state",
      "statement": "Verified src/webhookHandler.ts against tests/webhookHandler.test.ts (6/6 tests passing).",
      "subject_key": "orderstream-test-verification",
      "confidence": "high"
    }
  ]
}
```

### 3. Record Active Work State and Close Handoffs

1. When finishing a Kiro task, record a concise work activity summary with `report_active_state`:

```json
// Tool: report_active_state
{
  "project_label": "OrderStream Webhook Service",
  "thread_key": "kiro-orderstream-implementation",
  "status": "completed",
  "end_reason": "completed",
  "task_summary": "Implement OrderStream webhook handler from hydrated Kiro specs",
  "activity_summary": "Hydrated requirements.md, design.md, and tasks.md from Knot v2 constraints, implemented src/webhookHandler.ts, and passed 6/6 automated tests."
}
```

2. If this work came from a Knot handoff, close the loop with `update_handoff_status`:

```json
// Tool: update_handoff_status
{
  "handoff_id": "<handoff-uuid>",
  "status": "completed",
  "resolution_summary": "Hydrated .kiro/specs/orderstream-webhooks/, implemented src/webhookHandler.ts enforcing HTTP 422 PCI_CDE_PAYLOAD_REJECTED and max 3 retries, verified all tests pass, and synced implementation state to Knot."
}
```

### 4. Pass Follow-Up Work to Another AI (`create_handoff`)

When Kiro completes engineering work that another tool needs to pick up (for example: asking ChatGPT to draft release notes or asking Claude to run an external security review), pass a clean handoff:

```json
// Tool: create_handoff
{
  "destination_client_id": "chatgpt",
  "context_refs": ["<new-project-state-uuid>"],
  "task": "Draft customer release notes and rollout checklist for OrderStream Webhook Service v2 based on the verified implementation synced in Knot."
}
```

## Enterprise VPC & AWS Integration Patterns

For teams deploying self-hosted **Knot EnterpriseBrain** inside an AWS VPC (Amazon EKS, Aurora/RDS PostgreSQL with `pgvector`, AWS KMS SigV4, EventBridge/SQS) or exposing Knot through **Amazon Bedrock AgentCore Gateway** to **Amazon Quick** and **Amazon Connect**, see [AWS EnterpriseBrain VPC & Gateway Reference](references/aws-enterprise-vpc.md).

## Troubleshooting

### Error: `needs_clarification` Returned on Write

**Cause:** Another active item in the same project has overlapping phrasing or shares the same `subject_key`.
**Solution:**
1. Read the `related` items returned in the tool response.
2. Ask the user whether the new item replaces one of the `related` IDs (`supersedes_context_id`) or stays alongside them (`coexists_with_context_ids`).
3. Retry `propose_context` with that explicit resolution field.

### Error: `422` or Secret/PII Hold-Back

**Cause:** The statement included raw secret patterns (for example API keys, tokens, private keys, or raw cardholder numbers) or personal kinds (`preference`, `person`, `relationship`) in a shared workspace.
**Solution:**
1. Strip all secrets, tokens, emails, and raw card data from the statement.
2. Keep project engineering updates in `fact`, `decision`, `constraint`, `goal`, or `project_state`.

## Best Practices

- Keep one atomic claim per item so future updates can supersede a single constraint cleanly without rewriting unrelated context.
- Always supply a deterministic `idempotency_key` on `propose_context` and `batch_propose_context` so retries never create duplicate records.
- Only report tests or builds as verified after running them following your final code edit.
- Confirm with the user before overwriting shared project decisions or creating external handoffs.
