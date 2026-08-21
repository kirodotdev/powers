# Filing and Tracking Support Cases

Workflow for filing, tracking, replying to, and resolving cases. For backend/IAM/setup, see
[setup](setup.md). For diagnostics/secrets, see
[case-safety-and-diagnostics](case-safety-and-diagnostics.md).

## Routing

| Intent | Action |
| --- | --- |
| Raise a case | [File a Case](#file-a-case) |
| Track / status | `describe_support_cases` |
| Read history | `describe_communications` |
| Reply | `add_communication_to_case` |
| Resolve | `resolve_support_case` (confirm first) |
| Check access | Step 1 probe; if denied → [Admin Setup](setup.md#admin-setup) |

## MCP Tools

Server: `awslabs.aws-support-mcp-server`. All arguments use **`snake_case`** (not camelCase).

| Tool | Purpose |
| --- | --- |
| `describe_support_cases` | List/search cases — also the read-only access probe |
| `describe_services` | List services + category codes |
| `describe_create_case_options` | Valid categories/severities for a service |
| `describe_severity_levels` | List severity levels + SLAs |
| `create_support_case` | File a case |
| `describe_communications` | Case communication history |
| `add_communication_to_case` | Reply to a case |
| `resolve_support_case` | Close a case |
| `add_attachments_to_set` | Upload files → returns `attachmentSetId` |

### `create_support_case` arguments

| Arg | Required | Notes |
| --- | --- | --- |
| `subject` | Yes | Short, specific |
| `service_code` | Yes | From `describe_services` |
| `category_code` | Yes | From `describe_create_case_options` |
| `severity_code` | Yes | `low`/`normal`/`high`/`urgent`/`critical` |
| `communication_body` | Yes | Structured body (template below) |
| `issue_type` | No | `technical` (default) or `customer-service` |
| `attachment_set_id` | No | From `add_attachments_to_set` |

### Toolkit fallback (CLI)

When using `aws-mcp`, issue `aws support <command> --region us-east-1`. Use `kebab-case` flags.

| Dedicated tool | CLI equivalent |
| --- | --- |
| `describe_severity_levels` | `aws support describe-severity-levels --region us-east-1` |
| `describe_services` | `aws support describe-services --region us-east-1` |
| `create_support_case` | `aws support create-case --subject .. --service-code .. --category-code .. --severity-code .. --communication-body .. --region us-east-1` |
| `describe_support_cases` | `aws support describe-cases --region us-east-1` |
| `describe_communications` | `aws support describe-communications --case-id .. --region us-east-1` |
| `add_communication_to_case` | `aws support add-communication-to-case --case-id .. --communication-body .. --region us-east-1` |
| `resolve_support_case` | `aws support resolve-case --case-id .. --region us-east-1` |

---

## File a Case

**Target: 3 turns max** (user describes → agent asks one follow-up → user confirms → filed).

### Step 1 — Verify access (silent, fast)

1. Check `mcp.json` has a real `AWS_PROFILE` (not the placeholder). If missing, ask user to set it.
2. Call `describe_support_cases` as a probe (same read-only probe used on activation).
   - Succeeds → continue.
   - Server unavailable → fall back to toolkit (see [setup](setup.md)).
   - `AccessDenied` → route to [Admin Setup](setup.md#admin-setup). Stop.
   - `SubscriptionRequiredException` → tell user account needs Business+ plan. Stop.

### Step 2 — Gather info (ONE batched message)

From the user's initial description, identify what you already have and what's missing. Ask for everything missing in **one message**, and close with the capture shortcut:

> I need a few things to file this:
> 1. **Conversation ID** — the session where the issue happened
> 2. **Kiro version** — Help → About
> 3. **Severity** — Low (24h) / Normal (12h) / High (4h) / Urgent (1h)?
> 4. **Steps to reproduce** — and the exact error text if you have it
> 5. **Debug logs** *(optional)* — path to `.kiro/debug/debug.log` or a zip
>
> Or just say **`capture these`** and I'll collect them from your machine.

Skip any item the user already provided. Don't ask for OS (you know it).

If they mention "crash"/"freeze"/"hang" — clarify which type in the same message (IDE crash vs freeze vs agent hang).

### Step 3 — Discover codes + build case (no user interaction needed)

1. Call `describe_services` → find the Kiro service code.
2. Call `describe_create_case_options` → get valid category/severity.
3. Map issue to category:

   | Issue type | Category |
   | --- | --- |
   | Completions, chat, inline suggestions | Chat / IDE |
   | Install, auth, login, config | Setup |
   | CLI issues | CLI |
   | Steering not loading | Steering |
   | Powers / MCP in a power | Powers |
   | Hooks | Hooks / Extensions |
   | MCP connections/tools | MCP |
   | Specs / task execution | Specs |
   | Feature requests | Feature Request |
   | Other | General Guidance |

   This table is a mapping *hint* only. The valid codes returned by `describe_create_case_options`
   are authoritative — if they conflict with this table, use the API's codes.

4. If user's stated severity doesn't match their described impact, flag it in one line and let them decide.
5. If captured logs surfaced **more than one distinct error**, confirm which one the case is about
   before building the body — see [multiple errors found](case-safety-and-diagnostics.md#multiple-errors-found--confirm-which-one-dont-guess).
   One issue per case.

### Step 4 — Confirm and file (one message)

Present the case summary for approval:

> **Subject:** `<subject>`
> **Severity:** `<severity>` (SLA: Xh)
> **Category:** `<service/category>`
>
> **Body:**
> ```
> <formatted body>
> ```
>
> File this? (If you have a debug zip, remind me of the path.)

On "yes":
- **With attachment:** `add_attachments_to_set` → get `attachmentSetId` → immediately `create_support_case` with that ID. No other calls between.
- **Without attachment:** `create_support_case` directly.

Return the case ID. Done.

### Attachment rules (non-negotiable)

- Upload → file in one uninterrupted sequence.
- Encode the file inside `add_attachments_to_set` — never pre-encode in a separate step.
- Never file first intending to attach later.
- If user said "done" without a path, search `.kiro/debug/` for a recent zip before asking.
- Remind user once to strip secrets from logs before shipping.

---

## Severity mapping

| Impact | Code | SLA (Business) |
| --- | --- | --- |
| General question / feature request | `low` | 24h |
| Non-critical, workaround exists | `normal` | 12h |
| Something isn't working right | `high` | 4h |
| Blocked / production impact | `urgent` | 1h |
| Critical system down (Enterprise only) | `critical` | 15 min |

---

## Case body template

```
## Issue Description
<what happened, what was expected>

## Environment
- Kiro Version: <version>
- OS: <platform>
- Session Type: <Vibe/Spec>
- Conversation ID: <id>

## Steps to Reproduce
1. <step>
2. <step>

Expected: <expected>
Actual: <actual>
Frequency: <always / intermittent / one-time>

## Error Messages
<exact text>

## Diagnostics Attached
- Debug Log Zip: <attached / not attached>

## Additional Context
<patterns, recent changes, workarounds tried; "None." if none>
```

## Tracking and follow-up

- **List cases:** `describe_support_cases`
- **Read history:** `describe_communications` — show chronologically.
- **Reply:** `add_communication_to_case` — remind to strip secrets from new logs. Attach with same two-step flow.
- **Resolve:** `resolve_support_case` — confirm with user first. Cases can be reopened within 7 days.
