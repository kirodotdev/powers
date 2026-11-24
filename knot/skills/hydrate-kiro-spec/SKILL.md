---
name: "hydrate-kiro-spec"
description: "Hydrate Kiro feature specs (.kiro/specs/requirements.md, design.md, tasks.md) and steering context from governed product requirements, architectural decisions, and superseded constraints saved in Knot across ChatGPT, Claude, Gemini, and Cursor. Use when starting a feature, generating or updating Kiro specs, resuming cross-AI work, or checking pending handoffs before writing code."
license: "MIT"
compatibility: "Works with Kiro IDE, Kiro CLI, and Agent Plugins v1.0.0 clients"
metadata:
  author: "ConnectKnot"
  version: "1.0.0"
---

# Hydrate Kiro Specs from Knot

## Overview

Developers rarely start new features inside the IDE. Product requirements often originate in ChatGPT, architectural reviews happen in Claude, and research lives in Gemini or Cursor before an engineer opens Kiro.

This skill connects Kiro to Knot over MCP so `.kiro/specs/<feature>/` files (`requirements.md`, `design.md`, `tasks.md`) and `.kiro/steering/` inherit the latest governed truth, supersession lineage (`v1 -> v2`), and active cross-AI handoffs on Turn 0.

## Prerequisites Checklist

- [ ] Kiro has the `knot` power installed (`plugin.json` and `mcp.json` pointing to `https://api.connectknot.com/mcp` or your self-hosted EnterpriseBrain `/mcp` URL).
- [ ] User has completed OAuth 2.1 browser sign-in with Knot (or configured Bearer token auth for headless CI).
- [ ] Target project or shared knot name is known, or can be discovered via `knot_list_scopes`.

## Step-by-Step Guide

### 1. Verify Connection and Active Scope

Always inspect what scope the current grant can read before fetching project records.

1. Call `get_knot_connection_status` to confirm authentication and whether project context reads (`projectContextRead`) are enabled.
2. Call `knot_list_scopes` to list the personal knot, shared knots (`sharedKnots`), and team workspaces (`scopes`).
3. If the target project belongs to a shared knot or workspace, either:
   - Pass `shared_knot_id` directly on read calls (recommended when scoping a single feature), or
   - Call `knot_set_active_scope` with `shared_knot_id`, `workspace_id`, or `personal: true` to switch the default scope for the session.

```json
// Example: inspect readable scopes first
// Tool: knot_list_scopes
{}
```

```json
// Example: focus a specific shared workspace or project
// Tool: knot_set_active_scope
{
  "shared_knot_id": "<shared-knot-uuid>"
}
```

### 2. Check Pending Handoffs Directed to Kiro

Before drafting specs or modifying files, check whether another AI assistant (such as ChatGPT, Claude, or Cursor) queued a task handoff for Kiro.

1. Call `check_pending_handoffs` (no parameters required).
2. Also call `list_handoffs` with `limit: 20` if the user wants visibility into handoffs sent to or completed by other AIs on the same project.
3. If a relevant handoff is `proposed` for Kiro, confirm scope with the user if needed, then accept it using `update_handoff_status`:

```json
// Tool: update_handoff_status
{
  "handoff_id": "<handoff-uuid>",
  "status": "accepted"
}
```

Move status to `"working"` once spec hydration or implementation begins.

### 3. Recover Current Decisions, Lineage, and Open Conflicts

Use Knot's three epistemic read tools according to the granularity needed:

| Need | Tool | Key Arguments |
| :--- | :--- | :--- |
| Full session kickoff + activity | `get_context_recovery` | `entity_hint`, `query`, `shared_knot_id`, `limit: 6`, `trigger: "skill"` |
| Current vs. historical `v1 -> v2` delta | `get_relevant_context` | `entity_hint`, `query`, `query_mode: "trajectory"`, `shared_knot_id` |
| Provenance + cross-tool agreement | `get_shared_understanding` | `entity_hint`, `query`, `shared_knot_id`, `limit: 30` |

#### Enforcing Current Truth Over Superseded History

When upstream specs evolve (for example, `v1` allowed 5 webhook retries, and `v2` later superseded that constraint with 3 retries and strict payload checks):

1. Query with `query_mode: "trajectory"` on `get_relevant_context` to inspect both the original baseline and the active head (`supersedes_id` chain).
2. Treat items returned in `current` (with no active superseder) as authoritative requirements for code generation.
3. Never implement rules marked `historical` or superseded (`superseded` status), even if they still appear in older chat snippets or local comments. Cite superseded items only as rationale in `design.md` so reviewers know why a stricter `v2` design was chosen.
4. Check `reconciliation.potential_conflicts` and `potential_conflicts` in the read response:
   - **Stop and ask the user** whenever two active claims under the same `subject_key` conflict before generating conflicting specs or code.
   - Do not silently pick a winner between unresolved conflicts.

```json
// Tool: get_context_recovery
{
  "entity_hint": "OrderStream Webhook Service",
  "limit": 6,
  "trigger": "skill"
}
```

```json
// Tool: get_relevant_context
{
  "entity_hint": "OrderStream Webhook Service",
  "query": "retry PCI security webhook",
  "query_mode": "trajectory",
  "trigger": "skill"
}
```

### 4. Compile `.kiro/specs/<feature>/` Artifacts

Map recovered Knot items directly into Kiro's spec-driven development files using clear traceability:

| Knot Item `kind` | Target Kiro Spec File | Role in Spec |
| :--- | :--- | :--- |
| `goal` | `.kiro/specs/<feature>/requirements.md` | Problem statement and user story goals |
| `constraint` | `.kiro/specs/<feature>/requirements.md` + `design.md` | Non-negotiable EARS acceptance criteria and guardrails |
| `decision` | `.kiro/specs/<feature>/design.md` | Architectural choices, rationale, and rejected `v1` alternatives |
| `fact` | `.kiro/specs/<feature>/design.md` | Verified endpoints, schemas, library versions, and environment limits |
| `project_state` + `handoff` | `.kiro/specs/<feature>/tasks.md` | Next concrete engineering tasks and verification checks |

#### Spec Formatting Rules

1. **requirements.md**: Write testable EARS statements (`WHEN <event>, THE <system> SHALL <behavior>`). Include a compact Provenance table noting the source AI (`ChatGPT`, `Claude`, `Gemini`, `Cursor`), author, and `subject_key` for every active requirement.
2. **design.md**: Document components, interfaces, error codes, and an explicit **Superseded Constraints & Rationale** section explaining any `v1 -> v2` transition so engineers do not accidentally re-introduce `v1` behavior.
3. **tasks.md**: Break work into verifiable implementation and test checkboxes, ending with a final task to sync verified changes back to Knot via the `sync-decisions-and-handoffs` skill.

#### Optional Steering File Hydration

When cross-AI constraints apply repo-wide (not only to one feature spec), propose creating or updating `.kiro/steering/knot-context.md` with only active project invariants, API contracts, and security rules. Keep steering files concise to avoid unnecessary prompt token overhead.

## Common Workflows

### Workflow 1: First-Time Feature Kickoff in Kiro

**Goal:** Turn an upstream ChatGPT or Claude planning thread into ready-to-build Kiro specs without manual copy-paste.

1. Run `knot_list_scopes` and confirm the right project scope.
2. Run `check_pending_handoffs` and `get_context_recovery` with `entity_hint`.
3. Inspect `get_relevant_context` with `query_mode: "trajectory"` for critical security, retry, auth, or schema rules.
4. Generate `.kiro/specs/<feature>/requirements.md`, `design.md`, and `tasks.md`.
5. Ask the user to confirm the hydrated spec (and resolve any `potential_conflicts`) before executing implementation tasks.

### Workflow 2: Refresh Specs After an External Stakeholder Update

**Goal:** Sync mid-sprint requirement changes made by a PM or architect in ChatGPT/Claude into an existing `.kiro/specs/` folder.

1. Run `get_shared_understanding` with `entity_hint` and `knot_list_shared_updates` if working in a shared knot.
2. Compare current Knot decisions against existing `.kiro/specs/<feature>/requirements.md` and `design.md`.
3. Update only the changed EARS clauses and design sections, noting the `v1 -> v2` supersession chain in `design.md`.
4. Add or adjust remaining unchecked items in `tasks.md` and run tests before coding further.

## Troubleshooting

### Error: `read_required` or Empty Results on `get_relevant_context`

**Cause:** The active scope is set to `personal` while the target project lives in a Shared Knot or Workspace, or `entity_hint` did not match the exact project name.
**Solution:**
1. Call `knot_list_scopes` to inspect available `sharedKnots` and `scopes`.
2. Call `search_context` with `scope: "all"` and a short keyword query to see which readable knot holds matches.
3. Pass `shared_knot_id` explicitly or call `knot_set_active_scope`, then retry `get_context_recovery`.

### Error: Unresolved `potential_conflicts` Returned

**Cause:** Two connected AIs or team members recorded competing claims under the same `subject_key`, and Knot intentionally refuses to auto-resolve them.
**Solution:**
1. Present both conflicting statements, their source AIs, and timestamps to the user.
2. Wait for the user to confirm which statement should stand.
3. Use the `sync-decisions-and-handoffs` skill to supersede the outdated claim with `supersedes_context_id` before writing code.

### Warning: OAuth Sign-In Prompt or Expired Grant

**Cause:** First connection to `https://api.connectknot.com/mcp`, or the user's OAuth 2.1 grant was revoked or expired.
**Solution:**
1. Complete the browser OAuth 2.1 PKCE login prompt when Kiro opens it (or reconnect the `knot` MCP server in Kiro Powers settings).
2. Re-run `get_knot_connection_status` to confirm `connected: true` before reading project context.

## Best Practices

- Never copy raw chat transcripts or secrets into `.kiro/specs/` or `.kiro/steering/`. Store only atomic, verified requirements, decisions, and constraints.
- Always use `query_mode: "trajectory"` for security, billing, or compliance constraints so `v1 -> v2` overrides are explicit in `design.md`.
- Keep active steering concise and feature-specific details inside `.kiro/specs/<feature>/`.
- Verify implementation against hydrated constraints with automated tests before syncing completion back to Knot.
