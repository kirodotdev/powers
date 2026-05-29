# Phase 1: Discover GCP Resources

Lightweight orchestrator that delegates to domain-specific discoverers. Each sub-discovery file is self-contained — it scans for its own input, processes what it finds, and exits cleanly if nothing is relevant.
**Execute ALL steps in order. Do not skip or deviate.**

## Sub-Discovery Files

- **discover-iac.md** → `gcp-resource-inventory.json` + `gcp-resource-clusters.json` (if Terraform found)
- **discover-app-code.md** → `ai-workload-profile.json` (if source code with AI signals found)
- **discover-billing.md** → `billing-profile.json` (if billing data found)

Multiple artifacts can be produced in a single run — they are not mutually exclusive.

## Step 0: Initialize Migration State

1. Check for existing `.migration/` directory at the project root.
   - **If existing runs found:** List them with their phase status and ask:
     - `[A] Resume: Continue with [latest run]`
     - `[B] Fresh: Create new migration run`
     - `[C] Cancel`
   - **If resuming:** Set `$MIGRATION_DIR` to the selected run's directory. Read its `.phase-status.json` and skip to the appropriate phase per the State Machine in POWER.md.
   - **If fresh or no existing runs:** Continue to step 2.
2. **Resolve the current local timestamp FIRST** by running the shell command `date "+%m%d-%H%M"` in the user's project directory to get the actual `MMDD-HHMM` value in the user's local timezone. **Do NOT hardcode, guess, or infer the timestamp — always execute the command and use its output.** Then create `.migration/[MMDD-HHMM]/` directory using the resolved value (e.g., if the command returns `0226-1430`, create `.migration/0226-1430/`). Set `$MIGRATION_DIR` to this new directory.
3. Create `.migration/.gitignore` file (if not already present) with exact content:

   ```
   # Auto-generated migration state (temporary, should not be committed)
   *
   !.gitignore
   ```

   This prevents accidental commits of migration artifacts.

4. Write `.phase-status.json` with exact schema:

   ```json
   {
     "migration_id": "[MMDD-HHMM]",
     "last_updated": "[ISO 8601 timestamp with local timezone offset]",
     "phases": {
       "discover": "in_progress",
       "clarify": "pending",
       "design": "pending",
       "estimate": "pending",
       "generate": "pending",
       "feedback": "pending"
     }
   }
   ```

5. Confirm both `.migration/.gitignore` and `.phase-status.json` exist before proceeding to Step 1.

## Step 1: Load Phase Status Schema

Load `steering/schema-phase-status.md` now. Each sub-discovery file loads its own output schema — do not load them here.

## Step 2: Scan for Input Sources and Run Sub-Discoveries

Scan the project directory for each input type. Only load sub-discovery files when their input files are present.

**2a. Check for Terraform files:**
Glob for: `**/*.tf`, `**/*.tfvars`, `**/*.tfstate`, `**/.terraform.lock.hcl`

- If found → Load `discover-iac.md`
- If not found → Skip. Log: "No Terraform files found — skipping IaC discovery."

**2b. Check for source code / dependency manifests:**
Glob for: `**/*.py`, `**/*.js`, `**/*.ts`, `**/*.jsx`, `**/*.tsx`, `**/*.go`, `**/*.java`, `**/*.scala`, `**/*.kt`, `**/*.rs`, `**/requirements.txt`, `**/setup.py`, `**/pyproject.toml`, `**/Pipfile`, `**/package.json`, `**/go.mod`, `**/pom.xml`, `**/build.gradle`

- If found → Load `discover-app-code.md`
- If not found → Skip. Log: "No source code found — skipping app code discovery."

**2c. Check for billing data:**
Glob for: `**/*billing*.csv`, `**/*billing*.json`, `**/*cost*.csv`, `**/*cost*.json`, `**/*usage*.csv`, `**/*usage*.json`

- If not found → Skip. Log: "No billing files found — skipping billing discovery."
- If found AND **no** Terraform files from 2a → Load `discover-billing.md` (billing is the primary source — needs full processing for the billing-only design path).
- If found AND Terraform files **were** found in 2a → Use lightweight extraction below. Do **not** load `discover-billing.md`.

**Lightweight billing extraction (when IaC is the primary source):**

When Terraform is present, billing data is supplementary — only service-level costs and AI signal detection are needed. Extract via a script to avoid reading the raw file into context.

1. Use Bash to read only the **first line** of the billing file to identify column headers.
2. Write a script to `$MIGRATION_DIR/_extract_billing.py` (or `.js` / shell — use whatever runtime is available) that:
   - Reads the billing CSV/JSON file
   - Groups line items by service description, sums cost per service
   - Extracts top 3 SKU descriptions per service by cost
   - Scans service and SKU descriptions (case-insensitive) for AI keywords: `vertex ai`, `ai platform`, `bigquery ml`, `generative ai`, `gemini`, `document ai`, `vision ai`, `speech-to-text`, `natural language`, `dialogflow`, `translation`
   - Outputs JSON to stdout matching the schema in step 4
3. Run the script: try `python3 _extract_billing.py` first. If `python3` is not found, try `python _extract_billing.py`. If neither is available, delete the script and fall back to loading `discover-billing.md`.
4. Write the script's JSON output to `$MIGRATION_DIR/billing-profile.json` with this exact schema:

   ```json
   {
     "summary": { "total_monthly_spend": 0.00 },
     "services": [
       {
         "gcp_service": "Cloud Run",
         "monthly_cost": 450.00,
         "top_skus": [
           { "sku_description": "Cloud Run - CPU Allocation Time", "monthly_cost": 300.00 }
         ]
       }
     ],
     "ai_signals": { "detected": false }
   }
   ```

   Services sorted descending by `monthly_cost`. Only include services with cost > 0.

5. Delete the script file after successful execution.

**Critical:** Do **not** Read the billing file with the Read tool. Do **not** load `discover-billing.md` or `schema-discover-billing.md`.

**If NONE of the three checks found files**: STOP and output: "No GCP sources detected. Provide at least one source type (Terraform files, application code, or billing exports) and try again."

## Step 3: Check Outputs

After all loaded sub-discoveries complete, check what artifacts were produced in `$MIGRATION_DIR/`:

1. Check for output files:
   - `gcp-resource-inventory.json` — IaC discovery succeeded
   - `gcp-resource-clusters.json` — IaC discovery produced clusters
   - `ai-workload-profile.json` — App code discovery detected AI workloads
   - `billing-profile.json` — Billing data parsed
2. **If NO artifacts were produced** (sub-discoveries ran but produced no output): STOP and output: "Discovery ran but produced no artifacts. Check that your input files contain valid GCP resources and try again."

## Step 4: Update Phase Status

In the **same turn** as the output message below, use the Phase Status Update Protocol (Write tool) to write `.phase-status.json` with `phases.discover` set to `"completed"` and all other phases unchanged from their initial values.

Output to user — build message from whichever artifacts exist:

- If `gcp-resource-inventory.json` exists: "Discovered X total resources across Y clusters."
- If `ai-workload-profile.json` exists: "Detected AI workloads (source: [ai_source])."
- If `billing-profile.json` exists: "Parsed billing data ($Z/month across N services)."

Format: "Discover phase complete. [artifact summaries joined by space] Proceeding to Phase 2: Clarify."

## Output Files

**Discover phase writes files to `$MIGRATION_DIR/`. Possible outputs (depending on what sub-discoverers find):**

1. `gcp-resource-inventory.json` — from discover-iac.md
2. `gcp-resource-clusters.json` — from discover-iac.md
3. `ai-workload-profile.json` — from discover-app-code.md
4. `billing-profile.json` — from discover-billing.md

**No other files must be created:**

- No README.md
- No discovery-summary.md
- No EXECUTION_REPORT.txt
- No discovery-log.md
- No documentation or report files

All user communication via output messages only.

## Error Handling

- **Missing `.migration` directory**: Create it (Step 0)
- **Missing `.migration/.gitignore`**: Create it automatically (Step 0) — prevents accidental commits
- **No input files found for any sub-discoverer**: STOP with error message (Step 2)
- **Sub-discoveries ran but produced no artifacts**: STOP with error message (Step 3)
- **Sub-discoverer fails**: STOP and report exact failure point and which sub-discoverer failed
- **Output file validation fails**: STOP and report schema errors
- **Extra files created (README, reports, etc.)**: Failure. Discover must produce ONLY the JSON artifact files.

## Scope Boundary

**This phase covers Discover & Analysis ONLY.**

FORBIDDEN — Do NOT include ANY of:

- AWS service names, recommendations, or equivalents
- Migration strategies, phases, or timelines
- Terraform generation for AWS
- Cost estimates or comparisons
- Effort estimates

**Your ONLY job: Inventory what exists in GCP. Nothing else.**
