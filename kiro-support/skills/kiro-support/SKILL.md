---
name: "kiro-support"
description: "File and track AWS Support cases for Kiro issues without leaving the IDE. Use when creating, tracking, replying to, or resolving AWS Support cases, or when checking Support API access."
license: "Apache-2.0"
metadata:
  author: "Kiro AWS team"
  version: "1.0.0"
---

# Kiro Support Cases

File and track AWS Support cases for Kiro without leaving the IDE. Two backends:
[AWS Support MCP Server](https://awslabs.github.io/mcp/servers/aws-support-mcp-server) (primary) and
[Agent Toolkit](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/) (`aws-mcp`, fallback).

## On activation

If intent is clear (e.g. "file a case for X"), go straight to the matching workflow.
Otherwise reply with just this menu — no preamble, no capability tour:

> What do you need?
> 1. Raise a case  2. Track a case  3. Read history  4. Reply  5. Resolve  6. Check access / setup

For "get started" / "check access" / "setup": run the read-only `describe_support_cases`
probe and report the result in one line (e.g. "Access confirmed — no open cases. What next?").
Do not explain what the power does, list its features, or show example code unless asked.

## First-run onboarding

Before the first case in a session, confirm the environment is ready — silently, in this order.
Surface a step only if it fails; if all pass, continue to the task without narrating the checks.

1. **`uvx` present** — the MCP server launches via `uvx`. If `uvx --version` fails, point to the
   [install guide](https://docs.astral.sh/uv/getting-started/installation/).
2. **`AWS_PROFILE` set** — confirm `mcp.json` has a real profile, not the `<your-aws-profile>`
   placeholder. If it's still the placeholder, ask the user to set it and reconnect the server.
3. **Access probe** — run `describe_support_cases` once. Success → proceed. `AccessDenied` or
   `SubscriptionRequiredException` → [setup](references/setup.md). Server won't start → fall back to `aws-mcp`.

## Available MCP servers

Configured in [`mcp.json`](../../mcp.json). Both backends reach the same AWS Support API with the same
IAM permissions (`support:*`) and require a Business+ support plan.

**Primary — `awslabs.aws-support-mcp-server`** (typed tools; all arguments use `snake_case`):

| Tool | Purpose |
| --- | --- |
| `describe_support_cases` | List/search cases — also the read-only access probe |
| `describe_communications` | Full communication history for a case |
| `add_communication_to_case` | Reply to a case (optional attachments) |
| `create_support_case` | File a new case |
| `resolve_support_case` | Close a case (reopenable within 7 days) |
| `describe_services` | List services + category codes |
| `describe_severity_levels` | List severity levels + SLAs |
| `describe_create_case_options` | Valid categories/severities for a service |
| `describe_supported_languages` | List supported languages |
| `add_attachments_to_set` | Upload files → returns `attachmentSetId` |
| `describe_attachment` | Download an attachment by ID |

**Fallback — `aws-mcp`** (Agent Toolkit): runs `aws support …` CLI commands (kebab-case flags,
`--region us-east-1`) when the primary server can't start. CLI equivalents for each tool above are
in [filing-and-tracking-cases](references/filing-and-tracking-cases.md#toolkit-fallback-cli).

## Output contract (applies to EVERY response)

- **No narration.** Never write "Let me…", "Now I understand…", "Now I'll…". Just act, then report.
- **No unsolicited overviews.** Don't explain what the power does, list capabilities, or show
  example workflows/code unless the user asks. They activated it; they know what it's for.
- **No multi-section essays.** No "1. What this does / 2. Setup / 3. Example" structures.
- **No behind-the-scenes.** Don't narrate which tools run internally, IAM/plan requirements, or
  fallback servers unless the user asks or something fails.
- **Lead with the result.** Tool ran → one-line outcome → at most one short next-step question.
- **Batch questions.** All missing info in one message. Never drip questions across turns.
- **Skip what you know.** OS is in system context. Don't re-ask for anything already provided.
- **Confirm once.** Show the case body a single time for approval, then file. No recaps after.

### Formatting

Brevity and polish aren't opposites — format for scannability, not length.

- **Bold the lead.** Start with the outcome in bold (e.g. **Access confirmed**), then a short clause.
- **Bullets for capabilities.** When listing what the power does, use a tight bulleted list with
  the verb bolded (**Raise**, **Track**, …) — one line each, no sentences.
- **Inline code for examples.** Put example prompts and identifiers in backticks
  (`file a normal case: Kiro chat keeps disconnecting on macOS`), not fenced code blocks.
- **Label the closer.** End with a bolded lead-in for the next step (e.g. **Next up:** …).
- **No headers, no tables, no emojis** in chat replies — they add height without adding signal.
- Keep the whole thing scannable in one glance: bold anchors, short lines, ≤10 lines total.

### When asked for an overview / walkthrough / example (e.g. the install "try it out" prompt)

Comply, but stay bounded — a request for an overview is not license for an essay:

- **Overview:** one short sentence, or one line per capability. No section headers.
- **Setup/verify:** run `describe_support_cases`, report the one-line result. Don't recount the
  guide's steps or explain what you're about to do.
- **Example:** one sentence describing the most common flow (filing a case). No code block, no
  step-by-step internals, unless the user asks.
- **Total:** aim for ≤10 lines. End with one next-step question.

<example>
<scenario>User: "help me get started"</scenario>
<bad>A three-part essay: what the power does, a walkthrough of the setup guide, a code
example, and a menu of six next steps.</bad>
<good>[runs describe_support_cases] "Access confirmed — no open cases yet. Want to file one,
or check something else?"</good>
</example>

<example>
<scenario>Overview + example, formatted for scannability (still ≤10 lines).</scenario>
<good>
**Access confirmed** — no open cases, you're set up.

**kiro-support** files and tracks AWS Support cases without leaving Kiro:

- **Raise** a new case
- **Track** case status
- **Read** a case's history
- **Reply** to support
- **Resolve** a case

**Typical flow:** tell me an issue — e.g. `file a normal case: Kiro chat keeps disconnecting on
macOS` — and I'll draft it, show you the body once for approval, then file on your OK.

**Next up:** file one, or check something else?
</good>
</example>

<example>
<scenario>Prompt asks for a brief overview + step-by-step setup + a simple example.</scenario>
<bad>Runs the probe, then writes "1. What this power does" (capability list), "2. Setup status"
(recaps the guide + IAM/plan notes), "3. A simple example" (code block + behind-the-scenes
tool sequence), then a six-option menu.</bad>
<good>[runs describe_support_cases] "Access confirmed — no open cases, you're set up.
This power files and tracks AWS Support cases from Kiro: raise, track, reply to, or resolve
cases. Typical use: tell me an issue like 'file a normal case: Kiro chat keeps disconnecting on
macOS' and I'll draft it, show you the body, and file on your OK. Want to try one?"</good>
</example>

## Steering guides — MUST read before acting

These files contain the detailed workflows, templates, and procedures for this skill. They are
located in the `references/` directory alongside this SKILL.md file.

**You MUST use `read_file` to load the matching file from this skill's `references/` directory
BEFORE executing any intent.** The files are located at:
`skills/kiro-support/references/<filename>` relative to the power root.

Do not attempt to file, track, reply, resolve, or troubleshoot without first reading the relevant
guide. Load only what the current intent requires; don't read them all up front.

| Intent | File to read | When to load |
| --- | --- | --- |
| Filing, tracking, replying, resolving a case | `references/filing-and-tracking-cases.md` | **Always** before filing, replying, tracking, or resolving. Contains the required 4-step workflow, case body template, severity mapping, tool arguments, and attachment rules. |
| Backend selection, onboarding, IAM/permissions, troubleshooting | `references/setup.md` | **Always** before handling access errors, `AccessDenied`, `SubscriptionRequiredException`, server connection failures, or when user asks about setup/configuration. Contains backend fallback logic and the admin email template. |
| Capturing diagnostics, secrets reminder, attaching logs | `references/case-safety-and-diagnostics.md` | **Always** when filing a case. Contains the auto-capture workflow, session lookup, debug log location, attachment size rules, and secrets reminder. |

**Filing a case requires reading TWO files:**
1. Read `references/filing-and-tracking-cases.md` for the workflow and template.
2. Read `references/case-safety-and-diagnostics.md` for diagnostics collection.

Follow both fully. In particular: always offer `capture these` to auto-gather session data and
debug logs before drafting the case body. Do not skip diagnostics gathering.

---

## Licenses

This power integrates with the [AWS Support MCP Server](https://github.com/awslabs/mcp) (`awslabs.aws-support-mcp-server`, Apache-2.0 license).

This power integrates with [MCP Proxy for AWS](https://github.com/aws/mcp-proxy-for-aws) (`mcp-proxy-for-aws`, the `aws-mcp` / Agent Toolkit backend, Apache-2.0 license).

The reference files and `SKILL.md` are original content authored by the power author and are distributed as part of this power.

## Telemetry

- **Primary backend** (`awslabs.aws-support-mcp-server`): no client-side telemetry is documented or collected by the server.
- **Fallback backend** (`mcp-proxy-for-aws`): collects telemetry by default. This power ships with
  `--disable-telemetry` set in [`mcp.json`](../../mcp.json), so telemetry is off out of the box. To re-enable it,
  remove that flag from the `aws-mcp` args and reconnect the server.
- This power itself adds no additional telemetry, analytics, or usage tracking.

## Privacy

- **What leaves your machine:** only the AWS Support case content you approve — subject, severity,
  category, body, and any attachment you explicitly add — sent to the AWS Support API using your own
  AWS credentials. Nothing is filed, replied to, or resolved without your confirmation.
- **Local reads are opt-in:** the power reads local Kiro session data (`~/.kiro/sessions/…`) and
  workspace debug logs (`.kiro/debug/`) only when you say `capture these`. It announces the read
  before touching the filesystem.
- **Secrets:** the power reminds you to strip secrets (passwords, tokens, keys) from logs before
  they're included in a case. Review case content before approving.
- **No third parties:** the power sends data only to the AWS Support API via your credentials; it
  does not transmit your code, logs, or session data to any other endpoint.
