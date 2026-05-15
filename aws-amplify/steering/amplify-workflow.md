# Amplify Workflow

Orchestrated workflow for AWS Amplify Gen 2 development.

## When to Use This Workflow

Use for any Amplify Gen 2 work:
- Building a new full-stack application
- Adding features to an existing backend
- Connecting frontend to backend
- Deploying to sandbox or production

The workflow determines which phases apply based on your request.

---

## Step 1: Validate Prerequisites

Run these checks before proceeding:

1. **Node.js 18.x or later**

   ```bash
   node --version
   ```

2. **npm available**

   ```bash
   npm --version
   ```

3. **AWS credentials configured** (CRITICAL)

   ```bash
   AWS_PAGER="" aws sts get-caller-identity
   ```

If the AWS credentials check fails, **STOP** and present this message to the user:

```
## AWS Credentials Required

I can't proceed without AWS credentials configured. Please set up your credentials first:

**Setup Guide:** https://docs.amplify.aws/react/start/account-setup/

**Quick options:**
- Run `aws configure` to set up access keys
- Run `aws sso login` if using AWS IAM Identity Center

Once your credentials are configured, **come back and start a new conversation** to continue building with Amplify.
```

**Do NOT proceed with Amplify work until credentials are configured.** The user must restart the conversation after setting up credentials.

---

## Step 2: Understand the Project

Once all prerequisites pass:

1. Read all necessary project files (e.g., `amplify/`, `package.json`, existing code) to understand the current state
2. If unsure about Amplify capabilities or best practices, use documentation tools to search and read AWS Amplify docs

Do this BEFORE proposing a plan.

---

## Step 3: Determine Applicable Phases

Based on the user's request and project state, determine which phases apply:

| Phase              | Applies when                                             | Steering file        |
| ------------------ | -------------------------------------------------------- | -------------------- |
| 1: Backend         | User needs to create or modify Amplify backend resources | `phase1-backend.md`  |
| 2: Sandbox         | Deploy to sandbox for testing                            | `phase2-sandbox.md`  |
| 3: Frontend & Test | Frontend needs to connect to Amplify backend             | `phase3-frontend.md` |
| 4: Production      | Deploy to production                                     | `phase4-production.md` |

Common patterns:
- **New full-stack app:** 1 -> 2 -> 3 -> 4
- **Backend only (no frontend):** 1 -> 2
- **Add feature to existing backend:** 1 -> 2
- **Redeploy after changes:** 2 only
- **Connect existing frontend:** 3 only
- **Deploy to production:** 4 only

**IMPORTANT: Only include phases that the user actually needs.** If the user asks for backend work only (e.g., "add auth", "create a data model", "add storage"), do NOT include Phase 3 (Frontend & Test). Frontend phases should only be included when the user explicitly asks for frontend work, a full-stack app, or to connect a frontend to Amplify.

---

## Step 4: Present Plan and Confirm

Present to the user:

```
## Plan

### What I understood
- [Brief summary of what the user wants]

### Features
[list features if applicable]

### Framework
[framework if known]

### Phases I'll execute
1. [Phase name] - [one-line description] -> SOP: [sop-name]
2. [Phase name] - [one-line description] -> SOP: [sop-name]
...
(Include SOP name for phases 1 and 3. Phases 2 and 4 use the amplify-deployment-guide SOP.)

Ready to get started?
```

**WAIT for user confirmation before proceeding.**

**Once the user approves the plan, you MUST stick to it. Do not deviate from the planned phases or SOPs unless the user explicitly asks for changes.**

---

## Step 5: Execute Phases

After the user confirms the plan, read **ONLY the first phase's steering file** using readSteering:

```
Call action "readSteering" with powerName="aws-amplify", steeringFile="<phase-file>"
```

Where `<phase-file>` is the steering file for the first phase in the plan (from the table in Step 3).

**Do NOT read any other phase steering files yet.**

### Resuming After a Phase Completes

When a phase completes, it will summarize what it did and stop. The orchestrator takes over:

1. Tell the user which phase just finished
2. If there are more phases in the plan, ask:

```
[Phase name] is complete. Ready to proceed to [next phase name]?
```

3. **WAIT for the user to confirm before proceeding.**
4. After the user confirms, read the next phase's steering file:

```
Call action "readSteering" with powerName="aws-amplify", steeringFile="<next-phase-file>"
```

**If there are no more phases in the plan, the workflow is complete.** Tell the user all phases are done.

Do NOT re-run prerequisites or re-present the plan. Simply dispatch the next phase.

---

## Critical Rules

1. **Always follow SOPs completely** - Do not improvise or skip steps
2. **Never use Gen 1 patterns** - This power is for Amplify Gen 2 only (TypeScript code-first, `defineAuth`/`defineData`/`defineStorage`/`defineFunction`)
3. **One phase at a time** - Read only one phase steering file at a time. Do not read ahead.
4. **Wait for confirmation between phases** - After each phase completes, ask the user to confirm before dispatching the next phase. Do not proceed until the user confirms.
5. **If you encounter an error or get sidetracked:**
   - Fix the immediate issue
   - Return to the SOP and continue from where you left off
   - Do NOT abandon the SOP or start improvising
6. **If you lose track of where you were in the SOP:**
   - Use the SOP retrieval tool to get the SOP again
   - Identify which step you completed last
   - Continue from the next step

---

## Troubleshooting

If issues occur during any phase:
1. Check the SOP's troubleshooting section first
2. Use documentation tools to search AWS Amplify docs for the error message
3. Read the relevant documentation page

**After resolving the issue, immediately return to the SOP and continue from where you left off. Do not abandon the workflow.**
