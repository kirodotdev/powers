# Phase 1: Backend

Create or modify Amplify Gen 2 backend resources.

---

## Prerequisites Confirmed

Prerequisites (Node.js, npm, AWS credentials) were already validated by the orchestrator workflow. Do not re-validate.

---

## Critical Constraints

- **Do NOT create frontend scaffolding or templates during this phase.** Do not run `create-next-app`, `create-react-app`, `create-vite`, `npm create`, or any frontend project generators. This phase is strictly for Amplify backend resources (the `amplify/` directory). If a frontend project already exists, leave it untouched. If no frontend project exists and the user only asked for backend work, do NOT create one.

- Before creating any files, ensure `.gitignore` exists in the project root and includes:
  `node_modules/`, `.env*`, `amplify_outputs.json`, `.amplify/`, `dist/`, `build/`.
  Create or update it if these entries are missing.

---

## Retrieve and Follow the SOP

**Do NOT write any code until you have retrieved and read the SOP.**

Use the SOP retrieval tool to get **"amplify-backend-implementation"** and follow it completely.

### SOP Overrides

- **Skip the SOP's Step 1** ("Verify Dependencies") — prerequisites were already validated by the orchestrator.
- **Skip the SOP's Step 12** ("Determine Next SOP Requirements") — phase sequencing is controlled by the orchestrator workflow, not the SOP.

Follow all other SOP steps (2 through 11) completely. Do not improvise or skip them.

### Error Handling

1. If you encounter an error, fix the immediate issue
2. Return to the SOP and continue from where you left off
3. Do NOT abandon the SOP or start improvising
4. If you lose track, retrieve the SOP again, identify your last completed step, and continue

---

## Phase Complete

After the SOP is fully executed, summarize what was created (which resources, files, configurations).

**STOP HERE.** Do NOT read any other steering files. Do NOT proceed to the next phase. The orchestrator workflow will handle what comes next.
