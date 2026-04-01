# Multi-Transformation

Apply TDs to multiple repositories in parallel. TD-to-repo assignments and config
are already confirmed from the match report. Do NOT re-discover TDs or re-prompt.

## Input

From the match report: repo list, TD per repo, config per TD.

## Prerequisite Check (Once Only)

Verify AWS credentials ONCE. Do NOT repeat per repo.
```bash
aws sts get-caller-identity
```
Also: `atx --version`

If any repos were provided as git URLs (HTTPS or SSH), clone them locally first.
The user's local git config handles authentication — no Secrets Manager needed.
```bash
CLONE_DIR=~/.aws/atx/custom/atx-agent-session/repos/<repo-name>-$SESSION_TS
git clone <git-url> "$CLONE_DIR"
```

If repos were provided as an S3 bucket path with zips, download and extract locally:
```bash
mkdir -p ~/.aws/atx/custom/atx-agent-session/repos
aws s3 sync s3://user-bucket/repos/ ~/.aws/atx/custom/atx-agent-session/repos/ --exclude "*" --include "*.zip"
for zip in ~/.aws/atx/custom/atx-agent-session/repos/*.zip; do
  name=$(basename "$zip" .zip)
  unzip -qo "$zip" -d "$HOME/.aws/atx/custom/atx-agent-session/repos/${name}-$SESSION_TS/"
done
```

Use the cloned/extracted paths as `<repo-path>` for each repo.

For each repo, verify it's a git repo:
```bash
ls -la <repo-path>
git -C <repo-path> status
```
If not a git repo: `cd <repo-path> && git init && git add . && git commit -m "Initial commit"`

The active language runtime must match the transformation's target version so that
builds and tests run correctly. Check the current version, and if there is a
mismatch, first check whether the target version is already installed (e.g.,
`sdk list java | grep installed`, `pyenv versions`, `nvm ls`). If found, switch
to it (e.g., `sdk use java 23-amzn`, `pyenv shell 3.12`, `nvm use 22`). Only if
the target version is not installed at all, ask the user for permission before installing. Suggest:
- Java: `sdk install java 23-amzn` (SDKMAN), or `brew install --cask corretto23` (macOS)
- Python: `pyenv install 3.15.0 && pyenv shell 3.15.0`
- Node.js: `nvm install 23 && nvm use 23`

Do NOT proceed until the correct version is active. Verify the switch succeeded
before proceeding.

Run transformations in parallel — maximum 3 concurrent repos at a time (the user
can override this, but 3 is recommended to avoid overloading the machine). If there
are more than 3 repos, process them in batches of 3 (wait for a batch to finish
before starting the next).

For each repo, use bash to create a runner script that captures the exit code:
```bash
mkdir -p ~/.aws/atx/custom/atx-agent-session
cat > ~/.aws/atx/custom/atx-agent-session/run-<repo-name>.sh << 'RUNNER'
#!/bin/bash
atx custom def exec -n <td-name> -p <repo-path> -x -t \
  --configuration 'additionalPlanContext=<config>'
echo $? > ~/.aws/atx/custom/atx-agent-session/<repo-name>.exit
RUNNER
chmod +x ~/.aws/atx/custom/atx-agent-session/run-<repo-name>.sh
nohup ~/.aws/atx/custom/atx-agent-session/run-<repo-name>.sh > ~/.aws/atx/custom/atx-agent-session/<repo-name>.log 2>&1 &
echo $! > ~/.aws/atx/custom/atx-agent-session/<repo-name>.pid
```
Omit `--configuration` if no config needed. Launch each repo's script in rapid
succession — do NOT wait between launches. Each runner script is backgrounded
via nohup; the exit code is captured to `~/.aws/atx/custom/atx-agent-session/<repo-name>.exit` when ATX finishes.

After launching all repos, find each repo's conversation log by grepping its
process log (ATX outputs the path within 30-60 seconds of starting):
```bash
grep "Conversation log:" ~/.aws/atx/custom/atx-agent-session/<repo-name>.log 2>/dev/null
```
If it hasn't appeared yet, wait 15 seconds and retry. Extract the full path from
each — do NOT use `ls -t` across all conversations, as that may match a different run.

Then start monitoring. On each 60-second cycle:
1. Check each PID: `kill -0 $(cat ~/.aws/atx/custom/atx-agent-session/<repo-name>.pid) 2>/dev/null && echo "RUNNING" || echo "DONE"`
2. Tail each repo's conversation log and relay progress to the user
3. For each repo, check the artifacts directory (`~/.aws/atx/custom/<conversation-id>/artifacts/`)
   and open files with `kiro -r <filepath>` as they appear (open each file only once):
   - `plan.json` — the transformation plan (appears after planning phase completes)
   - `worklog.log` — the execution log (appears shortly after plan.json)
   - `validation_summary.md` — open after the repo's process exits
4. Report which repos are still running, which have completed

**You MUST continue polling without waiting for user input.** The user should see
continuous progress updates across all repos.

## Progress Reporting

```
[1/N] repo-name          TD-name                    Status
[2/N] repo-name          TD-name                    Status
```

## Result Collection

Collect per repo: success/failure, transformed code path, error details.
```
Succeeded:
- repo-name: TD-name (config)
Failed:
- repo-name: TD-name (error)
```

Hand off to [results-synthesis.md](results-synthesis.md) for consolidated reporting.

Tell the user: "To review changes in each repo, open it in Kiro (`kiro -r <repo-path>`)
and use the Source Control panel to see the full commit history with diffs for
each file ATX modified."

## Error Handling

| Scenario | Action |
|----------|--------|
| Git clone fails | Log error, continue with remaining repos |
| Transformation fails | Log repo and error, do not auto-retry |
| Partial results | Generate summary from successes, report failures |

## Cleanup

Clean up session files automatically:
```bash
[ -d ~/.aws/atx/custom/atx-agent-session ] && find ~/.aws/atx/custom/atx-agent-session -maxdepth 1 -type f \( -name "*.sh" -o -name "*.log" -o -name "*.pid" -o -name "*.exit" -o -name "*.zip" \) -delete 2>/dev/null || true
```

## Key Principles

1. Single prerequisite check — never repeat for parallel tasks
2. Trust the match report — do not re-discover TDs
3. Local parallel execution — maximum 3 concurrent repos (user-overridable)
4. Skip prerequisite checks in parallel task prompts
