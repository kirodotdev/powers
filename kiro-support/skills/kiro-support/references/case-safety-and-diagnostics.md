# Case Safety and Diagnostics

What to gather, how to attach, and the one rule about secrets.

---

## Secrets reminder

When the user shares logs or a debug zip, remind them **once**:

> If there are secrets in the logs (passwords, tokens, API keys, private keys), remove them before shipping.

Safe to include: AWS Account IDs, ARNs, Conversation IDs, error messages, stack traces, Kiro version, OS, timestamps, regions.

---

## Diagnostics to collect

You know the OS from system context — don't ask. Batch all asks into one message.

| Item | How | Required |
| --- | --- | --- |
| Conversation ID | From local session data (see auto-capture) or user pastes it | Always |
| Kiro version | Help → About (not in session data) | Always |
| Debug logs | `.kiro/debug/debug.log` (plain text, preferred) or the zip (Cmd+Shift+P → "Create Debug Log Zip") | Recommended for crashes/errors |
| Repro steps | Steps → expected → actual → frequency | Always (if reproducible) |
| Error messages | Verbatim | If any |

When you list these for the user, always offer the shortcut: **"…or just say `capture these` and
I'll pull them from your local Kiro session data and debug logs."**

---

## Auto-capture (opt-in): "capture these"

When the user says `capture these` (or asks you to gather the diagnostics), **announce it first**,
then read the local filesystem — this is opt-in, so don't scan files until the user opts in:

> I'll read your local Kiro session data and debug logs to capture the conversation ID, session
> type, and version, and locate a debug zip. Nothing leaves your machine until you approve the case.

### Which session? (don't assume the current one)

The user may be filing from a **different conversation than the one the issue happened in**, so
never hard-code "the current session." Read session metadata and let the user pick:

1. List `~/.kiro/sessions/<workspace-hash>/sess_*/session.json`. Each file holds:
   - `id` — the **Conversation ID** (e.g. `sess_5cebf1c0-…`)
   - `title` — human-readable label
   - `agentMode` — `vibe` / `spec` → **Session Type** (Vibe/Spec)
   - `autopilot` — `true`/`false` → **Autonomy** (Autopilot/Supervised)
   - `modelId`, `workspacePaths`, `createdAt`, `lastModifiedAt`
2. Show the most recent few (title + last-modified + workspace) and ask which one the issue
   occurred in — unless the user already named it. Match by title/time/workspace.
3. Pull `id`, `agentMode`, `autopilot`, `modelId` from the chosen `session.json`.

### Locate debug logs

Search the chosen session's `workspacePaths` for `.kiro/debug/`. Two artifacts usually live there
(e.g. `<workspace>/.kiro/debug/debug.log`):

- **`debug.log`** (plain text) — **prefer this.** Read the relevant tail (~200 lines, or the lines
  around the error) and include it **inline** in the case body's Logs/Error section. No base64, no
  size-limit worries.
- **`kiroDebugLogs.zip`** — the full bundle. Only attach it when the plain log isn't enough, and
  check the 5 MB limit in the attachment flow below first.

On macOS, raw logs also live at `~/Library/Application Support/Kiro/logs/`. If neither exists, tell
the user how to make the zip (Cmd+Shift+P → "Create Debug Log Zip") or proceed without.

### Multiple errors found → confirm which one (don't guess)

A `debug.log` or zip often contains **several unrelated errors** from a long session. Never assume
which one the case is about. When you find more than one distinct error (different messages, stack
traces, or timeframes):

1. Show a short numbered list — one line each: timestamp + a one-line summary of the error.
2. Ask the user to confirm **which specific error** they want to report.
3. Put only the confirmed error's log lines in the case body. Ignore the rest.

> I found a few distinct errors in the log — which one is this case about?
> 1. `18:42` — MCP server `awslabs.aws-support-mcp-server` failed to connect (timeout)
> 2. `19:03` — Uncaught TypeError in chat renderer
> 3. `19:15` — Spec task execution aborted: tool call rejected
>
> Reply with the number, or tell me if it's something else.

If the errors are genuinely separate problems the user wants tracked, follow **one issue per
case** — file the confirmed one now and offer to file the others as their own cases.

### What you still can't auto-capture

- **Kiro version** — not in `session.json`; get it from the debug zip metadata or ask (Help → About).
- **Repro steps / error text / impact** — always from the user.

Report what you captured in a compact list, then continue to the remaining questions (version,
severity, repro) in one message.

### Crash type clarification (ask inline if user says "crash"/"freeze"/"hang")

| Type | Key diagnostic |
| --- | --- |
| IDE crash (process closes) | Debug Log Zip essential |
| Freeze/hang (IDE open, stuck) | Debug Log Zip + Conversation ID |
| Agent hang (IDE fine) | Output panel logs + Conversation ID |
| Feature broken | Conversation ID + repro steps |

### Debug zip handling

| User says | Action |
| --- | --- |
| Gives a path | Note it. Don't read/encode until filing time. |
| "Done" / "generated it" (no path) | Search `.kiro/debug/` for recent zip. Confirm with user. |
| "Skip" / "no zip" | Proceed without. Note in body: "Debug Log Zip: not attached." |

---

## Attachment flow

### Prefer inline logs over attachments

`add_attachments_to_set` only accepts files **under 5 MB** and requires base64 encoding — usually
overkill. **Default to pasting the relevant slice of `debug.log` inline** in the case body. Attach
a file only when it's genuinely needed (a binary, or a full zip support explicitly asks for) **and**
it's under 5 MB. If `kiroDebugLogs.zip` exceeds 5 MB, don't attach it — extract the relevant
`debug.log` lines inline instead, or wait for support to request specific logs.

**If attachment fails or is unavailable for any reason**, always fall back to reading the logs
directly and including the relevant lines inline. This is the primary diagnostic delivery method —
attachments are a convenience, not a requirement.

### Log extraction strategy (use this FIRST, before attempting full-file attachment)

Full debug zips and large log files are almost always too large for the `add_attachments_to_set`
tool argument limit (~30KB of base64 in a single tool call). **Do not attempt to attach full zips
or large files directly.** Instead:

1. **Extract relevant lines first.** Use `grep` with error-related patterns against the log file:
   ```
   grep -B2 -A2 "error\|abort\|failed\|ECONNRESET\|Stream error" <logfile> > /tmp/extract.log
   ```
2. **Check the extract size.** If `/tmp/extract.log` is under ~50KB, base64 it and attach as a
   small `.log` file via `add_attachments_to_set`. This usually succeeds.
3. **If still too large**, trim further (last 100 relevant lines) or paste the key lines directly
   into the case body's Error Messages section.
4. **Only attempt full zip attachment** if the extract is insufficient AND the zip is under 200KB
   AND the user explicitly requests attaching the full file.

This approach avoids the common failure mode where the agent tries to base64-encode a 275KB+ zip,
hits tool argument limits, gets stuck retrying, and wastes multiple turns.

### When you do attach (non-negotiable order)

**ATTACH FIRST, THEN FILE.** One uninterrupted sequence (file must be < 5 MB):

1. `add_attachments_to_set(attachments=[{"fileName": "kiroDebugLogs.zip", "data": "<base64>"}])` — encode inside this call.
2. Get `attachmentSetId` from response.
3. **Immediately** call `create_support_case(..., attachment_set_id=<id>)`.

### What NOT to do

- Pre-encode the file in an earlier step.
- Upload early, do other work, then file later (set expires ~1 hour).
- File first intending to attach later (impossible).

### Attachment failure or timeout fallback

If `add_attachments_to_set` fails, times out, or gets stuck (no response within ~30 seconds):

1. **Try the fallback server.** If using the primary (`awslabs.aws-support-mcp-server`), retry the
   upload via `aws-mcp` using the CLI equivalent:
   `aws support add-attachments-to-set --attachments fileName=kiroDebugLogs.zip,data=<base64> --region us-east-1`
2. **If fallback also fails or is unavailable**, abandon the attachment and collect logs inline:
   - Read the tail of `.kiro/debug/debug.log` (~200 lines) or `~/Library/Application Support/Kiro/logs/`
   - Search for lines matching the user's reported error (timestamps, stack traces, error messages)
   - If multiple errors exist, show a numbered list and confirm which one to include
   - Paste the relevant log lines directly into the case body's Diagnostics section
3. **File the case without the attachment.** Add a note in the body:
   `"Debug Log Zip: attachment upload failed — relevant log lines included inline below."`
4. **Tell the user.** Let them know the attachment didn't go through, the relevant logs were
   included inline, and they can manually attach the zip later via the AWS Support Console if needed.

Never block case filing on a stuck attachment. The inline log is always sufficient for initial triage.

---

## What NOT to include in cases

- Full log dumps (trim `debug.log` to ~200 relevant lines and paste inline)
- Entire workspace trees or source code
- `.env` files or secrets
- Other users' session data
