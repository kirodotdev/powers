# Single Transformation

Apply one TD to one repo. TD, config, and repo are already confirmed from the match report.

### 1. Verify ATX (once per session, skip if already verified)
```bash
atx --version
```

### 2. Verify Language Version
The active language runtime must match the transformation's target version so that builds and tests run correctly. For example, a Java 8 → 17 upgrade needs Java 17 available locally.

Check the installed version matches the target:
```bash
java -version    # Java transformations
python3 --version # Python transformations
node --version   # Node.js transformations
```
If there is a mismatch, resolve it before proceeding:
- Look for the correct version already installed (e.g., check `/usr/lib/jvm/`, `pyenv versions`, `nvm ls`)
- If found, switch to it (e.g., `sdk use java 17`, `pyenv shell 3.12`, `nvm use 22`)
- If not installed, ask the user for permission before installing. Suggest the appropriate version manager (e.g., `sdk install java 17`, `pyenv install 3.12`, `nvm install 22`)
- Verify the switch succeeded by re-checking the version before continuing

### 3. Prepare Source

If the user provided a git URL (HTTPS or SSH) instead of a local path, clone it
locally first. The user's local git config handles authentication for private repos
— no Secrets Manager setup needed in local mode.

```bash
CLONE_DIR=~/.aws/atx/custom/atx-agent-session/repos/<repo-name>-$SESSION_TS
git clone <git-url> "$CLONE_DIR"
```

If the user provided an S3 path to a zip, download and extract it locally:
```bash
aws s3 cp s3://user-bucket/repos/<project>.zip ~/.aws/atx/custom/atx-agent-session/<project>-$SESSION_TS.zip
mkdir -p ~/.aws/atx/custom/atx-agent-session/repos/<project>
unzip -qo ~/.aws/atx/custom/atx-agent-session/<project>-$SESSION_TS.zip -d ~/.aws/atx/custom/atx-agent-session/repos/<project>-$SESSION_TS/
```

Use the cloned/extracted path as `<repo-path>` for all subsequent steps. If the
user provided a local path, use it directly.

### 4. Validate Repository
```bash
ls -la <repo-path>
git -C <repo-path> status
```
If not a git repo: `cd <repo-path> && git init && git add . && git commit -m "Initial commit"`

### 5. Execute and Monitor

Launch the transformation in a way that returns control immediately. Some shell
tools block until all child processes exit, even with `&`. To avoid this, use bash to write
a launcher script and execute it:

```bash
mkdir -p ~/.aws/atx/custom/atx-agent-session
cat > ~/.aws/atx/custom/atx-agent-session/run.sh << 'RUNNER'
#!/bin/bash
atx custom def exec -n <td-name> -p <repo-path> -x -t \
  --configuration 'additionalPlanContext=<user-config>'
echo $? > ~/.aws/atx/custom/atx-agent-session/transform.exit
RUNNER
chmod +x ~/.aws/atx/custom/atx-agent-session/run.sh
nohup ~/.aws/atx/custom/atx-agent-session/run.sh > ~/.aws/atx/custom/atx-agent-session/transform.log 2>&1 &
echo $! > ~/.aws/atx/custom/atx-agent-session/transform.pid
cat ~/.aws/atx/custom/atx-agent-session/transform.pid
```
Omit `--configuration` if no config is needed.

This backgrounds the runner script (not ATX directly), so the exit code is
captured to `~/.aws/atx/custom/atx-agent-session/transform.exit` when ATX finishes. The PID file tracks
the runner process.

**As soon as you have the PID, immediately run the next command** — do NOT stop
and wait for the user. The ATX CLI outputs the conversation log path within
30-60 seconds of starting. Read it from the process log:
```bash
grep "Conversation log:" ~/.aws/atx/custom/atx-agent-session/transform.log 2>/dev/null
```
If it hasn't appeared yet, wait 15 seconds and retry (up to 4 attempts). The
output looks like:
```
Conversation log: /Users/<user>/.aws/atx/custom/20260319_063712_e3479843/logs/2026-03-19T06-37-26-conversation.log
```
Extract the full path from this line — this is the conversation log for THIS
specific run. Do NOT use `ls -t` to find the most recent log across all
conversations, as that may return a log from a previous run.

Then start a monitoring loop. On each cycle:
1. Check if the process is still running: `kill -0 $(cat ~/.aws/atx/custom/atx-agent-session/transform.pid) 2>/dev/null && echo "RUNNING" || echo "DONE"`
2. Read the latest lines from the conversation log and tell the user what's happening
3. Wait 60 seconds, then repeat

**You MUST continue polling without waiting for user input.** After each poll,
immediately schedule the next one. The user should see continuous progress updates
like "ATX is planning changes...", "Applying changes to 3 files...", "Running build...".

CRITICAL rules:

1. **Extract conversation ID and log path.** After launching the process, look for
   the conversation log line in stdout:
   ```
   📝 Conversation log: /Users/<user>/.aws/atx/custom/<conversation-id>/logs/<timestamp>-conversation.log
   ```
   Extract the `<conversation-id>` (e.g., `20260311_233325_21bb5ef0`) and the full
   log file path. Report the conversation ID to the user immediately. Example:
   "Transformation started — conversation ID: `20260311_233325_21bb5ef0`"

2. **Tail the conversation log.** Once the log path is known, read new lines from
   the conversation log on each polling cycle and relay meaningful progress to the
   user. This is the primary way to keep the user informed of what ATX is doing
   (e.g., planning steps, applying changes, running builds, encountering errors).

3. **Filter out noise.** When reading the conversation log or process stdout,
   silently IGNORE any lines containing "Thinking" — these are animated spinner
   indicators that repeat dozens of times and must NOT be echoed to the user.
   Surface everything else: planning output, file changes, build results, errors,
   and completion summaries.

4. **Completion = process exit only.** The transformation is done ONLY when the
   background process exits. Check the process exit code — do NOT parse terminal
   output or log content to determine completion. ATX prints progress messages
   and spinner animations throughout execution that do NOT indicate completion.

5. **Polling interval.** Check the background process status and tail the
   conversation log every 60 seconds. Do NOT use escalating backoff for local
   mode — a fixed 60-second interval is sufficient. Do NOT sleep in the foreground
   terminal.

6. **Exit code determines success.** Once `kill -0` confirms the process has
   exited, read the exit code: `cat ~/.aws/atx/custom/atx-agent-session/transform.exit`. Exit code 0 =
   success. Non-zero = failure. Only after reading the exit code should you
   report the transformation as complete or failed.

7. **Open artifacts in the IDE.** Using the conversation ID from rule #1, the
   artifacts directory is `~/.aws/atx/custom/<conversation-id>/artifacts/`.
   During each polling cycle, check whether each file exists and open it as
   soon as it appears. Open each file only once — track which ones you've
   already opened.

   Check and open during polling:
   ```bash
   ARTIFACTS_DIR=~/.aws/atx/custom/<conversation-id>/artifacts
   test -f "$ARTIFACTS_DIR/plan.json" && echo "PLAN_READY"
   test -f "$ARTIFACTS_DIR/worklog.log" && echo "WORKLOG_READY"
   ```
   When a file is ready, open it in the current Kiro window:
   ```bash
   kiro -r "$ARTIFACTS_DIR/plan.json"
   kiro -r "$ARTIFACTS_DIR/worklog.log"
   ```
   - `plan.json` — the transformation plan (appears after planning phase completes)
     IMMEDIATELY after opening plan.json — before doing anything else, before
     checking for worklog.log, before the next polling cycle — display this
     message to the user:
     
     > ### 💡 Open Source Control (Ctrl+Shift+G) to watch changes in real time
     > 
     > **ATX commits after each step — Source Control shows every file change with full diffs as they happen.**
     
     Do NOT defer this message. Do NOT batch it with other output. Send it
     right after the plan.json open command.
   - `worklog.log` — the execution log (appears shortly after plan.json)

   After the process exits, open:
   ```bash
   kiro -r "$ARTIFACTS_DIR/validation_summary.md"
   ```
   - `validation_summary.md` — the final validation report

### 6. Present Results
Show TD, repo path, key changes. Also tell the user:
"You can review all changes in the Source Control panel — it shows the full
commit history with diffs for each file ATX modified."

## Error Handling

| Issue | Resolution |
|-------|------------|
| Dependency incompatibility | Check package compatibility, may need manual update |
| ATX timeout | Set `ATX_SHELL_TIMEOUT=1800` or break into smaller transforms |

## Cleanup

After the transformation completes, clean up session files automatically:
```bash
[ -d ~/.aws/atx/custom/atx-agent-session ] && find ~/.aws/atx/custom/atx-agent-session -maxdepth 1 -type f \( -name "*.sh" -o -name "*.log" -o -name "*.pid" -o -name "*.exit" -o -name "*.zip" \) -delete 2>/dev/null || true
```