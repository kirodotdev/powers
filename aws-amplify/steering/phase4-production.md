# Phase 4: Production Deployment

Deploy the Amplify Gen 2 application to production.

---

## Prerequisites Confirmed

Prerequisites (Node.js, npm, AWS credentials) were already validated by the orchestrator workflow. Do not re-validate.

---

## Retrieve and Follow the SOP

Use the SOP retrieval tool to get **"amplify-deployment-guide"** and follow it completely.

### SOP Overrides

- **Skip the SOP's Step 1** ("Verify Dependencies") — prerequisites were already validated by the orchestrator.
- **deployment_type is `cicd`** — do not ask the user for the deployment type. This phase is always a production deployment.
- **app_name** — infer from the project's `package.json` or existing Amplify configuration. Only ask the user if it cannot be determined.

### SOP Parameter Mapping

The SOP uses `deployment_type` with values `sandbox` or `cicd`. For this phase:
- deployment_type: **cicd**

Follow all applicable SOP steps for CI/CD deployment. Do not improvise or skip them.

### Error Handling

1. If you encounter an error, fix the immediate issue
2. Return to the SOP and continue from where you left off
3. Do NOT abandon the SOP or start improvising
4. If you lose track, retrieve the SOP again, identify your last completed step, and continue

---

## Phase Complete

After the SOP is fully executed, present to the user:

```
## You're live!

### Production URL
[url from deployment output]

### Amplify Console
https://console.aws.amazon.com/amplify/home

Your app is now deployed! Future updates: just push to your repo and it auto-deploys.
```

This is the final phase. The workflow is complete.
