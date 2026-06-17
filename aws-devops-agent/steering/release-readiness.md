---
name: release-readiness
description: Guide for running release readiness reviews via the aws-devops-agent remote MCP server (typed tools). Use when the user wants to trigger a release readiness review, check execution status, view execution journal, or cancel a review.
---

## Overview

This skill uses the typed tools from the `aws-devops-agent` remote MCP server to run release readiness reviews via the Release Readiness Review Agent. It handles the full execution lifecycle — starting reviews, polling for progress, streaming journal output, and retrieving the final release readiness report.

## Usage

Use this skill when:
- You want to trigger a release readiness review on a code change before merging
- You want to check the status of a release readiness review execution
- You want to view the journal/progress of a running release readiness review
- You want to cancel a release readiness review

## Instructions

### Pre-flight: Verify hook installation

Before proceeding, check if `.kiro/hooks/devops-agent-post-spec-completion.kiro.hook` exists by reading the file directly (e.g., `read_file` on `.kiro/hooks/devops-agent-post-spec-completion.kiro.hook`). If the file exists, skip hook installation silently. If it does NOT exist, follow the installation steps in the POWER.md Setup section — tell the user about the hook and install it (default: ON). Do NOT silently skip this. Once the hook check is resolved, continue below.

### Gathering execution parameters

Infer everything automatically from the user's request — do not ask for parameters that can be derived.

**Input source decision tree:**

```
Has the user provided a pull request/code review/merge request link or ID?
├── Yes: github.com PR URL               → use "GitHub PR" flow below
├── Yes: gitlab.com MR URL               → use "GitLab MR" flow below
└── No link provided — repo name only    → use "Local GitHub/GitLab repo" flow below
```

**Rules:**
- If a **PR/MR URL** is provided: Extract ALL fields from the URL. Do NOT inspect the local workspace or git state.
- **Only** use the local workspace flows when the user references a repository or package **without** a PR/MR link.

---

#### GitHub PR (github.com URL or PR reference)

- Parse the input to extract fields — do NOT attempt a web fetch unless fields cannot be determined from the input.
- `repository` (required): `owner/repo` from the PR URL
- At least one of the following is required: `headSha` (commit SHA), `headBranch` (branch name), `prNumber` (PR number as a **string**, e.g. `"8"` not `8`)
- `hostname`: Extract from the URL (e.g., `github.com` or a self-hosted hostname)
- Pass these fields to `create_release_readiness_review` under `content.githubPrContent` as an **array of objects** (even for a single PR).

**Example:**
```json
{
  "content": {
    "githubPrContent": [
      {
        "repository": "owner/repo",
        "prNumber": "8",
        "hostname": "github.com"
      }
    ]
  }
}
```

> ⚠️ **Critical format rules**: `githubPrContent` MUST be an array (not a single object). `prNumber` MUST be a string (not an integer).

---

#### GitLab MR (gitlab.com URL)

- Parse the input to extract fields — do NOT attempt a web fetch unless fields cannot be determined from the input.
- `repository` (required): `owner/repo` from the MR URL
- At least one of the following is required: `headSha` (commit SHA), `headBranch` (branch name), `mergeRequestIid` (MR number as a **string**, e.g. `"1"` not `1`)
- `hostname`: Extract from the URL (e.g., `gitlab.com` or a self-hosted hostname)
- Pass these fields to `create_release_readiness_review` under `content.gitlabMrContent` as an **array of objects** (even for a single MR).

**Example:**
```json
{
  "content": {
    "gitlabMrContent": [
      {
        "repository": "namespace/repo",
        "mergeRequestIid": "1",
        "hostname": "gitlab.com"
      }
    ]
  }
}
```

> ⚠️ **Critical format rules**: `gitlabMrContent` MUST be an array (not a single object). `mergeRequestIid` MUST be a string (not an integer). Violating either causes immediate task failure with no journal records.

---

#### Local GitHub/GitLab repo (no PR/MR URL provided — local workspace ONLY)

When the user references a repository without a PR/MR link, use this flow:

1. **Navigate to the repository directory**: `cd` to the repo root (e.g., `src/<RepoName>`, or wherever the clone lives, ask the user if needed).
2. **Determine the base branch**: Use `main` unless the user specifies a different branch. Verify the remote tracking branch exists:
   ```bash
   BASE_BRANCH="main"
   if ! git show-ref --verify --quiet refs/remotes/origin/$BASE_BRANCH; then
       git fetch origin $BASE_BRANCH
   fi
   ```
   If the fetch fails (e.g., "couldn't find remote ref"), ask the user to specify the base branch and stop.
3. **Check for local changes**: Run `git status --short` and `git rev-list --count origin/$BASE_BRANCH..HEAD` to determine the state and communicate accordingly:

   - **Clean AND not ahead**: Inform the user there's nothing new to analyze and stop.

   - **Has uncommitted changes (with or without unpushed commits)**:
     - If there are one or more unpushed commits (rev-list count >= 1), tell the user:
       > "You have uncommitted changes and N unpushed commits. I'll commit your uncommitted changes on top, then push all N+1 commits to a new branch for analysis. All changes will appear as a single diff against the base branch. Shall I proceed?"
     - If there are no other unpushed commits (rev-list count = 0), tell the user:
       > "I'll commit your uncommitted changes and push them to a new branch for release readiness review. Shall I proceed?"
     - If triggered by a hook/spec task, skip the confirmation and proceed directly.
     - **Do NOT proceed until the user approves.** If they decline, stop. If the user specifies a different scope, adjust accordingly.

   - **Clean but ahead of remote (rev-list count > 0, no uncommitted changes)**:
     - If ahead by more than 1 commit, tell the user:
       > "You have N unpushed commits. I'll push all of them to a new branch for analysis. All changes will appear as a single diff against the base branch. Shall I proceed?"
     - If ahead by exactly 1 commit, tell the user:
       > "I'll push your latest commit to a new branch for release readiness review. Shall I proceed?"
     - If triggered by a hook/spec task, skip the confirmation and proceed directly.
     - **Do NOT proceed until the user approves.** If they decline, stop.

4. **Stash uncommitted changes** (skip this step if working directory is clean):
   ```bash
   git stash push --include-untracked -m "release-analysis: preserve working changes"
   ```

5. **Create review branch** (do this BEFORE committing so the snapshot commit only lives on the disposable branch):
   ```bash
   ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   BRANCH_NAME="feat/release-readiness-review"
   git checkout -b $BRANCH_NAME 2>/dev/null || { BRANCH_NAME="feat/release-readiness-review-$(date +%Y%m%d-%H%M%S)"; git checkout -b $BRANCH_NAME; }
   ```

6. **Apply stashed changes and commit on the review branch** (skip this step if working directory was clean — go straight to step 7):
   ```bash
   git stash apply
   ```
   Before staging, check for sensitive files:
   ```bash
   git status --short | grep -iE '\.(env|pem|key|p12|pfx|credentials|secret)'
   ```
   If sensitive files are detected, warn the user and ask for confirmation before proceeding — even in hook mode. If the user declines, abort:
   ```bash
   git checkout $ORIGINAL_BRANCH && git branch -D $BRANCH_NAME && git stash drop
   ```

   Once confirmed (or no sensitive files found):
   ```bash
   git add -A
   git commit -m "chore: snapshot for release readiness review"
   ```

7. **Push all unpushed commits**:
   ```bash
   git push -u origin HEAD
   ```

8. **Determine the repository identifier and hostname**: Run `git remote get-url origin | sed 's|://[^@]*@|://|'` to extract the `owner/repo` and hostname. MANDATORY: Always use the sed command, we cannot expose PAT tokens in the context window!
   - GitHub URLs (github.com or self-hosted) → use `githubPrContent`, hostname from URL
   - GitLab URLs (gitlab.com or self-hosted) → use `gitlabMrContent`, hostname from URL

9. **Build the content**: Set `headBranch` to `$BRANCH_NAME`, `repository` to the extracted `owner/repo`, and `hostname` to the value from step 8. Wrap the object in an array:
   - GitHub: `{"githubPrContent": [{"repository": "owner/repo", "headBranch": "feat/release-readiness-review", "hostname": "github.com"}]}`
   - GitLab: `{"gitlabMrContent": [{"repository": "namespace/repo", "headBranch": "feat/release-readiness-review", "hostname": "gitlab.com"}]}`

10. **Inform the user**: Tell them which branch was created and pushed, then proceed with the standard workflow below.
11. **After analysis completes**: Clean up and restore working state:
    ```bash
    git checkout $ORIGINAL_BRANCH
    git push origin --delete $BRANCH_NAME 2>/dev/null || true
    git branch -D $BRANCH_NAME 2>/dev/null || true
    ```
    If step 4 was executed (uncommitted changes were stashed), also run:
    ```bash
    git stash pop
    ```

**Important**: Do NOT create a PR/MR — only push the branch. The release readiness review agent will read the branch directly.

### Core workflow

> ⚠️ **STRICT SEQUENCING**: Steps below are numbered. You MUST complete each step before moving to the next. In particular, step 1 (automated testing prompt) MUST NOT happen until the entire "Gathering execution parameters" flow above is fully complete — all git operations done, branch pushed (if local flow), content object built, and user informed of the branch. Only THEN proceed to step 1.

#### 1. Determine `skip_automated_testing` (ask ONLY after content is ready)

The `skip_automated_testing` parameter controls whether the agent runs automated testing (automated verification testing in a simulated environment) or only static analysis.

| Value | Behavior |
|-------|----------|
| `true` | Skip automated testing, run static analysis only (fast — code review, risk assessment, dependency checks) |
| `false` | Full analysis including automated testing (longer, spins up a testing environment, builds code, runs automated verification tests) |

**How to determine mode**: If triggered by a hook or spec task → spec mode. Otherwise → vibe mode (prompt the user).

**Spec mode (default)**: Always pass `skip_automated_testing=true`. Spec mode prioritizes speed — customers use this for a quick review before merging. Do NOT prompt the user; just run static analysis. Proceed directly to step 2.

**Vibe mode (interactive/user-driven)**: Present the choice and wait for a response:
> "Would you like a quick static analysis (code review, risk assessment, dependency checks), or a full analysis that also includes automated testing? Automated testing spins up a testing environment, builds your code, and runs automated verification tests — it's more thorough but takes longer."

**Do NOT move on to the next step until the user answers.**

- If the user says "yes" / "include testing" / "full analysis" / "run tests" → pass `skip_automated_testing=false`
- If the user says "no" / "static only" / "skip automated testing" / "quick" / "go ahead" / declines → pass `skip_automated_testing=true`

#### 2. Check tool availability

Verify that the `create_release_readiness_review` tool is available. If it is not present, use the Fallback (aws-mcp) path described at the bottom of this document instead of continuing with the steps below.

#### 3. Start the Job

Call `create_release_readiness_review` with:
- `content`: the content object built above (containing `githubPrContent` or `gitlabMrContent`)
- `skip_automated_testing`: `true` in spec mode (always). In vibe mode, `true` or `false` based on user's response to the prompt in step 1.

Record the **taskId** and **executionId** from the response.

#### 4. Poll for Status

Call `get_task(task_id=TASK_ID)` every **30 seconds** until the status transitions to `IN_PROGRESS` or a terminal state (`COMPLETED`, `FAILED`, `CANCELED`, `TIMED_OUT`).

#### 5. Monitor Until Completion

Once `IN_PROGRESS`, poll for progress in a loop:

1. Call `list_journal_records(execution_id=EXEC_ID, order="ASC")` to fetch new findings.
2. Present each record to the user with a friendly progress update and progress emojis (e.g. 🔍 searching, 🔬 analyzing, 🎯 finding, 📊 summarizing), without using the phrase journal record.
3. Use `next_token` from the response to fetch only new records on subsequent polls.
4. **Wait 15 seconds** (run `sleep 15` in bash) between each poll iteration.
5. Check `get_task(task_id=TASK_ID)` periodically — stop when terminal status.

#### 6. Present Results

Once the job reaches a terminal status:
- If `COMPLETED`:
  1. Call `get_release_readiness_report(execution_id=EXEC_ID)` to retrieve the full release readiness report.
  2. Write the report contents to a markdown file:
     ```
     release-readiness-review-<YYYY-MM-DD-HHmmss>.md
     ```
  3. Inform the user that the report was saved, including the file path.
  4. **Auto-fix flow (MANDATORY)**: After saving the report, you MUST attempt to generate and present fixes for all actionable risks — this is the primary value of the review workflow, not an optional step. Do NOT skip this step under any circumstances when risks are identified.
     - First, locate the analyzed repository in the current workspace:
       1. Run `ls src/` to list available directories.
       2. Match by repo name (the last segment of `owner/repo` or `namespace/repo`). For example, `testgroupadthiru/repo1updated` → look for `src/repo1updated`.
       3. If a single match is found and you're in vibe mode, confirm with the user: "I found `src/<match>` — is this the correct local copy of `<namespace/repo>`?"
       4. If multiple matches are found, ask the user which one is correct.
       5. If no obvious match exists and you're in vibe mode, ask the user: "I couldn't find a local directory matching `<repo-name>`. Is it available locally under a different name, or should I just show the suggested fixes?"
       6. In spec/hook mode, if no match is found, fall through to the "NOT found locally" path. If a single match is found, use it without asking.
     - If **found locally**:
       - **Verify branch**: Run `git -C <repo-directory> branch --show-current` to confirm you're on the expected branch (the branch that was analyzed). If not on the expected branch, check out the correct one before proceeding.
       - Scan the relevant code, interpret the risks/issues from the report. Then:
       - If triggered by a hook/spec task, skip the confirmation and proceed directly.
       - Otherwise, tell the user:
         > "The report identified N actionable issues. I can generate the fixes in your local repository, and can push them to a new branch `feat/release-readiness-fix`. Shall I proceed?"
       - **Do NOT proceed until the user approves.** If they decline, stop.
       - Once approved, generate the fixes. Then:
         ```bash
         cd <repo-directory>
         git checkout -b feat/release-readiness-fix 2>/dev/null || { git checkout -b "feat/release-readiness-fix-$(date +%Y%m%d-%H%M%S)"; }
         # Apply the fixes
         git add -A
         git commit -m "fix: Address issues identified by release readiness review"
         ```
       - **Before pushing, verify branch again**: Run `git branch --show-current` and confirm it shows `feat/release-readiness-fix*`. Do NOT push if you're on any other branch (e.g., `main`, the original feature branch).
         ```bash
         git push -u origin HEAD
         ```
         Inform the user: which issues were fixed, what branch was created, and that the fix has been pushed.
     - If **NOT found locally**: You MUST still present the suggested fixes from the report as concrete, ready-to-apply code patches. Use the `suggestedFix` field from each risk in the report. Format them as code blocks the user can copy-paste directly into their codebase. Walk through each actionable risk one by one: explain what the issue is, show the exact fix, and state which file/line it targets. Do NOT simply say "apply the fixes manually" without showing the actual code changes.
     - If the report finds **no risks or issues**: Inform the user the analysis completed with no actionable findings.
- If `FAILED` or `TIMED_OUT`: Present the error information and suggest next steps.
- If `CANCELED`: Inform the user the job was canceled and no report is available.

### Cancelling a job

Call `cancel_release_readiness_review(task_id=TASK_ID)`.

### Error handling

1. If `FAILED` or `TIMED_OUT` — stop and present the error. If the job failed quickly (within the first poll or two), call `list_associations` to check whether the target repository's hosting service (GitHub/GitLab hostname) is associated with the agent space. If no matching association exists, inform the user that the repository's source provider needs to be associated with their agent space before analysis can run.
2. If job does not reach `IN_PROGRESS` within 5 minutes — cancel with `cancel_release_readiness_review`.
3. If throttled (`429` or `ThrottlingException`) — wait 30 seconds, retry up to 3 times.
4. If the error does not match any known pattern above, present the raw error output to the user.

---

## Fallback (aws-mcp)

If `create_release_readiness_review` is not available, use `aws-mcp` with `call_aws`. All workflow logic, sequencing, and behavior from the core workflow steps 3–6 apply identically — only the tool invocations differ.

#### 3. Start the Job

```
aws___call_aws(cli_command="aws devops-agent create-backlog-task \
  --agent-space-id SPACE_ID \
  --task-type RELEASE_READINESS_REVIEW \
  --title 'Release Readiness Review' \
  --priority MEDIUM \
  --description '{\"agentInput\": {\"content\": <CONTENT_JSON>, \"metadata\": {\"skipAutomatedTesting\": true}}}' \
  --region us-east-1")
```

> **CRITICAL:** The `content` value must be a single object — NOT wrapped in a list. Correct: `"content": {"githubPrContent": [...]}`. Incorrect: `"content": [{"githubPrContent": [...]}]`. The values in the content should all be of string format e.g. the PR number should be a string.
- `"skipAutomatedTesting"`: `true` in spec mode (always). In vibe mode, `true` or `false` based on user's response to the prompt in step 1.

Record the **taskId** and **executionId** from the response.

#### 4. Poll for Status

Call every **30 seconds** until the status transitions to `IN_PROGRESS` or a terminal state (`COMPLETED`, `FAILED`, `CANCELED`, `TIMED_OUT`):

```
aws___call_aws(cli_command="aws devops-agent get-backlog-task \
  --agent-space-id SPACE_ID \
  --task-id TASK_ID \
  --region us-east-1")
```

#### 5. Monitor Until Completion

Once `IN_PROGRESS`, poll for progress in a loop:

1. Call `list-journal-records` to fetch new findings:
   ```
   aws___call_aws(cli_command="aws devops-agent list-journal-records \
     --agent-space-id SPACE_ID \
     --execution-id EXEC_ID \
     --order ASC \
     --region us-east-1")
   ```
2. Present each record to the user with a friendly progress update and progress emojis (e.g. 🔍 searching, 🔬 analyzing, 🎯 finding, 📊 summarizing), without using the phrase journal record.
3. Use `--next-token` from the response to fetch only new records on subsequent polls.
4. **Wait 15 seconds** (run `sleep 15` in bash) between each poll iteration.
5. Check `get-backlog-task` periodically — stop when terminal status.

#### 6. Present Results

Once the job reaches a terminal status:
- If `COMPLETED`:
  1. Call `list-journal-records` with `--record-type release_analysis_report` to retrieve the full release readiness report:
     ```
     aws___call_aws(cli_command="aws devops-agent list-journal-records \
       --agent-space-id SPACE_ID \
       --execution-id EXEC_ID \
       --order ASC \
       --record-type release_analysis_report \
       --region us-east-1")
     ```
  2. Write the report contents to a markdown file:
     ```
     release-readiness-review-<YYYY-MM-DD-HHmmss>.md
     ```
  3. Inform the user that the report was saved, including the file path.
  4. **Auto-fix flow (MANDATORY)**: After saving the report, you MUST attempt to generate and present fixes for all actionable risks — this is the primary value of the review workflow, not an optional step. Do NOT skip this step under any circumstances when risks are identified.
     - First, locate the analyzed repository in the current workspace:
       1. Run `ls src/` to list available directories.
       2. Match by repo name (the last segment of `owner/repo` or `namespace/repo`). For example, `testgroupadthiru/repo1updated` → look for `src/repo1updated`.
       3. If a single match is found and you're in vibe mode, confirm with the user: "I found `src/<match>` — is this the correct local copy of `<namespace/repo>`?"
       4. If multiple matches are found, ask the user which one is correct.
       5. If no obvious match exists and you're in vibe mode, ask the user: "I couldn't find a local directory matching `<repo-name>`. Is it available locally under a different name, or should I just show the suggested fixes?"
       6. In spec/hook mode, if no match is found, fall through to the "NOT found locally" path. If a single match is found, use it without asking.
     - If **found locally**:
       - **Verify branch**: Run `git -C <repo-directory> branch --show-current` to confirm you're on the expected branch (the branch that was analyzed). If not on the expected branch, check out the correct one before proceeding.
       - Scan the relevant code, interpret the risks/issues from the report. Then:
       - If triggered by a hook/spec task, skip the confirmation and proceed directly.
       - Otherwise, tell the user:
         > "The report identified N actionable issues. I can generate the fixes in your local repository, and can push them to a new branch `feat/release-readiness-fix`. Shall I proceed?"
       - **Do NOT proceed until the user approves.** If they decline, stop.
       - Once approved, generate the fixes. Then:
         ```bash
         cd <repo-directory>
         git checkout -b feat/release-readiness-fix 2>/dev/null || { git checkout -b "feat/release-readiness-fix-$(date +%Y%m%d-%H%M%S)"; }
         # Apply the fixes
         git add -A
         git commit -m "fix: Address issues identified by release readiness review"
         ```
       - **Before pushing, verify branch again**: Run `git branch --show-current` and confirm it shows `feat/release-readiness-fix*`. Do NOT push if you're on any other branch (e.g., `main`, the original feature branch).
         ```bash
         git push -u origin HEAD
         ```
         Inform the user: which issues were fixed, what branch was created, and that the fix has been pushed.
     - If **NOT found locally**: You MUST still present the suggested fixes from the report as concrete, ready-to-apply code patches. Use the `suggestedFix` field from each risk in the report. Format them as code blocks the user can copy-paste directly into their codebase. Walk through each actionable risk one by one: explain what the issue is, show the exact fix, and state which file/line it targets. Do NOT simply say "apply the fixes manually" without showing the actual code changes.
     - If the report finds **no risks or issues**: Inform the user the analysis completed with no actionable findings.
- If `FAILED` or `TIMED_OUT`: Present the error information and suggest next steps.
- If `CANCELED`: Inform the user the job was canceled and no report is available.

### Cancelling a job (fallback)

```
aws___call_aws(cli_command="aws devops-agent update-backlog-task \
  --agent-space-id SPACE_ID \
  --task-id TASK_ID \
  --task-status CANCELED \
  --region us-east-1")
```

### Error handling (fallback)

1. If `FAILED` or `TIMED_OUT` — stop and present the error. If the job failed quickly (within the first poll or two), call `list-associations` to check whether the target repository's hosting service (GitHub/GitLab hostname) is associated with the agent space:
   ```
   aws___call_aws(cli_command="aws devops-agent list-associations \
     --agent-space-id SPACE_ID \
     --region us-east-1")
   ```
   If no matching association exists, inform the user that the repository's source provider needs to be associated with their agent space before analysis can run.
2. If job does not reach `IN_PROGRESS` within 5 minutes — cancel with `update-backlog-task` (set `--task-status CANCELED`).
3. If throttled (`429` or `ThrottlingException`) — wait 30 seconds, retry up to 3 times.
4. If the error does not match any known pattern above, present the raw error output to the user.
