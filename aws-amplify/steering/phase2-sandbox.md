# Phase 2: Sandbox Deployment

Deploy the Amplify Gen 2 backend to a sandbox environment for testing.

---

## Prerequisites Confirmed

Prerequisites (Node.js, npm, AWS credentials) were already validated by the orchestrator workflow. Do not re-validate.

---

## Retrieve and Follow the SOP

Use the SOP retrieval tool to get **"amplify-deployment-guide"** and follow it completely.

### SOP Overrides

- **Skip the SOP's Step 1** ("Verify Dependencies") — prerequisites were already validated by the orchestrator.
- **deployment_type is `sandbox`** — do not ask the user for the deployment type. This phase is always a sandbox deployment.
- **app_name** — infer from the project's `package.json` or existing Amplify configuration. Only ask the user if it cannot be determined.

### SOP Parameter Mapping

The SOP uses `deployment_type` with values `sandbox` or `cicd`. For this phase:
- deployment_type: **sandbox**

Follow all applicable SOP steps for sandbox deployment. Do not improvise or skip them.

### Error Handling

1. If you encounter an error, fix the immediate issue
2. Return to the SOP and continue from where you left off
3. Do NOT abandon the SOP or start improvising
4. If you lose track, retrieve the SOP again, identify your last completed step, and continue

---

## Phase Complete

After the SOP is fully executed:

1. Confirm deployment succeeded
2. Verify `amplify_outputs.json` exists in the project root
3. Summarize the deployment results

**STOP HERE.** Do NOT read any other steering files. Do NOT proceed to the next phase. The orchestrator workflow will handle what comes next.
