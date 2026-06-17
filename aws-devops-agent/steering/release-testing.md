---
name: release-testing
description: Guide for running release testing jobs (UI or API) via the aws-devops-agent remote MCP server (typed tools). Use when the user wants to run automated tests, check job status, view test progress, or download test reports.
---

## Overview

This skill uses the typed tools from the `aws-devops-agent` remote MCP server to run release testing in the cloud via the Release Testing Agent. It handles the full job lifecycle — creating jobs, polling for progress, streaming journal output, and retrieving the final test report.

**Input is a test profile** — the test profile already contains the target URL, agent type (UI or API), test personas, and credentials. Do NOT ask the user for a URL directly; the URL is defined in the test profile.

## Usage

Use this skill when:
- You need to validate multi-step user workflows end-to-end
- You developed a feature and want to validate its functionality and usability from an end-user perspective
- You made code changes and want to ensure there are no regressions
- You need to verify visual aspects of your web application after code changes
- You want to surface unexpected behavior, UI issues, or accessibility problems
- You want to test API endpoints against an OpenAPI specification
- You want to surface unexpected behavior, UI issues, or contract violations
- You want to create code fixes based on the test result

## Prerequisites

- A pre-existing test profile (Knowledge Item ID like `ki-12345`) created from the AWS DevOps Agent operator app console.

## Instructions

### Gathering test parameters

Before starting any workflow, you MUST gather the following parameters. Do NOT proceed to job creation until answered.

#### Step 1 — Test profile (required)
Ask the user which test profile to use. The test profile already contains the target URL, agent type (UI or API), test personas, and credentials configuration — these do NOT need to be gathered separately.

**Note:** A pre-existing test profile is a prerequisite for running this agent. Test profiles are created using the AWS DevOps Agent console or API, not through this tool. If the user asks whether they need a test profile or whether one can be created here, inform them that a test profile must already exist before starting a release testing job.

#### Step 2 — Test requirement (optional)
If the user has not already mentioned a test focus, ask:
> "Do you have a specific test requirement or focus area? If not, I'll run a full exploratory test."

Wait for the user's response. If they provide one, use it as the `test_requirement`. If they say no or skip, proceed without it.

IMPORTANT: You MUST wait for the user to respond before proceeding to job creation.

### Core workflow

#### 1. Check tool availability

Verify that the `create_release_testing_job` tool is available. If it is not present, use the Fallback (aws-mcp) path described at the bottom of this document instead of continuing with the steps below.

#### 2. Start the Job

Call `create_release_testing_job` with:
- `test_profile_id`: the Knowledge Item ID (e.g., `ki-12345`)
- `webhook_event_message`: (optional) if the user provided a test requirement, pass it here

Record the **taskId** and **executionId** from the response.

#### 3. Poll for Status

Call `get_task(task_id=TASK_ID)` every **30 seconds** until the status transitions to `IN_PROGRESS` or a terminal state.

#### 4. Monitor Until Completion

Once `IN_PROGRESS`, poll for progress in a loop:

1. Call `list_journal_records(execution_id=EXEC_ID, order="ASC")` to fetch new findings.
2. Present each record to the user with a friendly progress update and progress emojis (e.g. 🔍 searching, 🔬 analyzing, 🎯 finding, 📊 summarizing), without mentioning the phrase journal records.
3. Use `next_token` from the response to fetch only new records on subsequent polls.
4. **Wait 20 seconds** (run `sleep 20` in bash) between each poll iteration.
5. Check `get_task(task_id=TASK_ID)` periodically — stop when terminal status (`COMPLETED`, `FAILED`, `CANCELED`, `TIMED_OUT`).

#### 5. Present Results

Once the job reaches a terminal status:
- If `COMPLETED`:
  1. Determine the report type from the test profile's agent type (UI or API) captured during job creation. Call `get_release_ui_testing_report(execution_id=EXEC_ID)` for UI profiles or `get_release_api_testing_report(execution_id=EXEC_ID)` for API profiles.
  2. Write the report contents to a markdown file:
     ```
     release-testing-report-<YYYY-MM-DD-HHmmss>.md
     ```
  3. Inform the user that the report was saved, including the file path.
- If `FAILED` or `TIMED_OUT`: Present the error information and suggest next steps.
- If `CANCELED`: Inform the user the job was canceled and no report is available.

### Cancelling a job

Call `cancel_release_testing_job(task_id=TASK_ID)`.

### Error handling

1. If the task status changes to `FAILED`, stop the workflow and report the error.
2. If the task does not reach `IN_PROGRESS` within 5 minutes, cancel it using `cancel_release_testing_job(task_id=TASK_ID)`.
3. If any output contains "NoCredentialsError", "ExpiredTokenException", or auth failures, suggest the user refresh their credentials or check the bearer token.
4. If throttled (`429` or `ThrottlingException`), wait 30 seconds before retrying. After 3 retries, inform the user.

---

## Fallback (aws-mcp)

If `create_release_testing_job` is not available, use `aws-mcp` with `call_aws`. All workflow logic, sequencing, and behavior from the core workflow apply identically — only the tool invocations differ.

#### Step 1 — Agent Space ID (required)

```
aws___call_aws(cli_command="aws devops-agent list-agent-spaces --region us-east-1")
```

Display all spaces and ask the user to select one. **Do NOT proceed until the user has selected one.** Use the selected `agentSpaceId` as `SPACE_ID` in all subsequent calls.

#### 2. Start the Job

```
aws___call_aws(cli_command="aws devops-agent create-backlog-task \
  --agent-space-id SPACE_ID \
  --task-type RELEASE_TESTING \
  --title 'Release Testing Job' \
  --priority MEDIUM \
  --description '{\"testProfileId\": \"ki-12345\", \"webhookEventMessage\": \"<REQUIREMENT>\"}' \
  --region us-east-1")
```

If the user provided a test requirement, include it as `webhookEventMessage`. If not, omit the field or leave it empty.

Record the **taskId** and **executionId** from the response.

#### 3. Poll for Status

Call every **30 seconds** until the status transitions to `IN_PROGRESS` or a terminal state (`COMPLETED`, `FAILED`, `CANCELED`, `TIMED_OUT`):

```
aws___call_aws(cli_command="aws devops-agent get-backlog-task \
  --agent-space-id SPACE_ID \
  --task-id TASK_ID \
  --region us-east-1")
```

#### 4. Monitor Until Completion

Once `IN_PROGRESS`, poll for progress in a loop:

1. Call `list-journal-records` to fetch new findings:
   ```
   aws___call_aws(cli_command="aws devops-agent list-journal-records \
     --agent-space-id SPACE_ID \
     --execution-id EXEC_ID \
     --order ASC \
     --region us-east-1")
   ```
2. Present each record to the user with a friendly progress update and progress emojis (e.g. 🔍 searching, 🔬 analyzing, 🎯 finding, 📊 summarizing), without mentioning the phrase journal records.
3. Use `--next-token` from the response to fetch only new records on subsequent polls.
4. **Wait 20 seconds** (run `sleep 20` in bash) between each poll iteration.
5. Check `get-backlog-task` periodically — stop when terminal status (`COMPLETED`, `FAILED`, `CANCELED`, `TIMED_OUT`).

#### 5. Present Results

Once the job reaches a terminal status:
- If `COMPLETED`:
  1. Determine the report type from the test profile's agent type (UI or API). For UI profiles:
     ```
     aws___call_aws(cli_command="aws devops-agent list-journal-records \
       --agent-space-id SPACE_ID \
       --execution-id EXEC_ID \
       --record-type qa_ui_testing_report \
       --region us-east-1")
     ```
     For API profiles, use `--record-type qa_api_testing_report` instead.
  2. Write the report contents to a markdown file:
     ```
     release-testing-report-<YYYY-MM-DD-HHmmss>.md
     ```
  3. Inform the user that the report was saved, including the file path.
- If `FAILED` or `TIMED_OUT`: Present the error information and suggest next steps.
- If `CANCELED`: Inform the user the job was canceled and no report is available.

#### Cancelling (fallback)

```
aws___call_aws(cli_command="aws devops-agent update-backlog-task \
  --agent-space-id SPACE_ID \
  --task-id TASK_ID \
  --task-status CANCELED \
  --region us-east-1")
```

#### Error handling (fallback)

1. If the task status changes to `FAILED`, stop the workflow and report the error.
2. If the task does not reach `IN_PROGRESS` within 5 minutes, cancel with `update-backlog-task` (set `--task-status CANCELED`).
3. If any output contains "NoCredentialsError", "ExpiredTokenException", or auth failures, suggest the user refresh their credentials or check the bearer token.
4. If throttled (`429` or `ThrottlingException`), wait 30 seconds before retrying. After 3 retries, inform the user.
