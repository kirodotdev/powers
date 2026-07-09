---
inclusion: auto
name: skill-operations
description: "Guidance for managing AWS Transform skills — upload, download, access control, metadata"
---

# AWS Transform Skill Operations Guide

## Related Guides

- For agent registration and publishing, see [agent-registration.md](./agent-registration.md)
- For full deployment automation, see [deployment-pipeline-guide.md](./deployment-pipeline-guide.md)

## Overview

Skills expand an agent's capabilities on the AWS Transform. The **skill registry** is a central repository where developers can choose from or contribute to a bank of skills to plug and play with their agents.

These tools interact with the skill registry and come from the AWS Transform Agent Toolkit MCP server (`agent-builder-mcp-aws-transform`). Use them when a developer needs to:
- **Upload** a skill they've authored to the registry so other agents can use it
- **Download** an existing skill from the registry to inspect, iterate on, or plug into their agent
- **Share** skills across AWS accounts so other developers' agents can use them
- **Manage** skill metadata, visibility, and lifecycle (activate, deprecate)

## Skill Lifecycle

```
upload-skill → (auto-zip, auto-activate, auto-grant-access)
  → get-skill-metadata → update-skill-metadata
  → update-skill-access-control → list-skills
  → download-skill
```

## Tool Reference

### list-skills

List all skills visible to your account. Auto-paginates internally — returns all results in one call.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filter` | object | No | Filter criteria (see below) |
| `filter.accessFilter` | enum | No | `ACCESSIBLE_ONLY` or `ALL_SKILLS` |
| `filter.statusFilter` | enum | No | `ACTIVE`, `DELETED`, `DEPRECATED`, `PENDING_UPLOAD`, or `UPDATE_IN_PROGRESS` |

**Returns:** `{ skills: [SkillSummary[]] }`

### get-skill-metadata

Get metadata for a specific skill.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name of the skill |

**Returns:** Full skill metadata object (name, description, status, visibility, timestamps, etc.)

### update-skill-metadata

Update a skill's metadata. Uses idempotency tokens for safe retries.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name of the skill to update |
| `description` | string | No | Updated description |
| `status` | enum | No | `ACTIVE` only (use `deprecate` flag to deprecate) |
| `visibility` | enum | No | `PRIVATE` or `PUBLIC` |
| `deprecate` | boolean | No | Set to `true` to deprecate the skill |

### upload-skill

Upload a skill artifact. Handles zipping, activation, and access control automatically.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name for the skill |
| `description` | string | Yes | Description of the skill artifact |
| `filePath` | string | Yes | Local path to the skill directory or file |
| `visibility` | enum | No | `PRIVATE` (default) or `PUBLIC` |

**Returns:** `{ skillName, status: "ACTIVE", accessGrantedTo: <callerAccountId>, zipped: boolean, uploadedSize: <bytes> }`

**Key behaviors:**
- **Auto-zip:** Directories and non-zip files are automatically zipped before upload
- **Auto-activate:** Skill status is set to `ACTIVE` immediately after upload
- **Auto-grant access:** Caller's AWS account (via STS GetCallerIdentity) is automatically granted access

### download-skill

Download a skill artifact. Optionally extract the zip contents.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name of the skill to download |
| `filePath` | string | Yes | Local path to save the artifact |
| `unzip` | boolean | No | If `true`, extract to `<filePath>/<skillName>/` |

**Returns:**
- If `unzip=true`: `{ message: "Successfully extracted skill to...", files: [<extracted filenames>] }`
- If `unzip=false`: `{ message: "Successfully downloaded skill to..." }`

### list-skill-access-control

List AWS accounts that have access to a skill.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name of the skill |

**Returns:** List of account IDs and their access status.

### update-skill-access-control

Grant or revoke access to a skill for a specific AWS account. Uses idempotency tokens for safe retries.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skillName` | string | Yes | Name of the skill |
| `skillUserAccountId` | string | Yes | 12-digit AWS account ID |
| `accessStatus` | enum | Yes | `ENABLED` to grant, `DISABLED` to revoke |

**Note:** Account ID must be exactly 12 digits.

## Common Workflows

### Publishing a New Skill

```
1. Prepare skill directory (SKILL.md + templates/ + examples/)
2. upload-skill(skillName, description, filePath)
   → auto-zips, auto-activates, auto-grants your account access
3. get-skill-metadata(skillName) to verify
4. update-skill-access-control(skillName, targetAccountId, "ENABLED") to share
```

### Downloading and Inspecting a Skill

```
1. list-skills() to find available skills
2. download-skill(skillName, filePath, unzip=true)
   → extracts to <filePath>/<skillName>/
3. Review SKILL.md, templates/, examples/
```

### Sharing a Skill With Another Account

```
1. upload-skill(skillName, description, filePath) — your account gets access automatically
2. update-skill-access-control(skillName, "123456789012", "ENABLED")
3. list-skill-access-control(skillName) to verify
```

### Deprecating a Skill

```
1. update-skill-metadata(skillName, deprecate=true)
2. get-skill-metadata(skillName) to verify status is DEPRECATED
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Upload fails with S3 error | File path doesn't exist or permissions issue | Verify `filePath` exists and is readable |
| Skill not visible after upload | Access not granted to consuming account | Use `update-skill-access-control` to grant access (caller account is auto-granted) |
| Account ID validation error | `skillUserAccountId` is not 12 digits | Provide exactly 12 numeric digits |
| Status update rejected | Tried to set status to something other than `ACTIVE` | Use `deprecate=true` to deprecate; only `ACTIVE` is valid for `status` field |
