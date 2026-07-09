# Phase 2: Clarify Requirements

**Phase 2 of 6** — Ask adaptive questions before design begins, then interpret answers into ready-to-apply design constraints.

> **HARD GATE — Clarify before Design:** Do not load `steering/design.md` (or any later phase) until this phase finishes **and** `$MIGRATION_DIR/.phase-status.json` records `phases.clarify` as `"completed"`. Writing `preferences.json` without updating phase status is a protocol violation. If the user asks to skip questions, use documented defaults and still complete this phase (including phase status).

The output — `preferences.json` — is consumed directly by Design and Estimate without any further interpretation.

Questions are organized into **six named categories (A–F)** with documented firing rules. Up to 22 questions across categories, depending on which discovery artifacts exist and which GCP services are detected. Questions are presented in **progressive batches** (up to 3 batches) with intermediate saves between each — partial answers persist across sessions. A standalone **AI-Only** flow exists for migrations that only move AI/LLM calls to Bedrock.

## Category Reference Files

| File                  | Category                     | Questions | Loaded When                                     |
| --------------------- | ---------------------------- | --------- | ----------------------------------------------- |
| `clarify-global.md`   | A — Global/Strategic         | Q1–Q7     | Always                                          |
| `clarify-compute.md`  | B — Config Gaps, C — Compute | Q8–Q11    | Compute or billing-source resources present     |
| `clarify-database.md` | D — Database                 | Q12–Q13b  | Database resources present                      |
| `clarify-ai.md`       | F — AI/Bedrock               | Q14–Q26   | `ai-workload-profile.json` exists               |
| `clarify-ai-only.md`  | _(standalone)_               | Q1–Q10    | AI-only migration (no infrastructure artifacts) |

---

## Step 0: Prior Run Check

Check `$MIGRATION_DIR/` for existing state:

**Case 1 — Completed preferences exist** (`preferences.json` present):

> "I found existing migration preferences from a previous run. Would you like to:"
>
> A) Re-use these preferences and skip questions
> B) Start fresh and re-answer all questions

- If A: Run Step 2 item 6 only (BigQuery detection) on current discovery artifacts. If `bigquery_present` is **true**, output the Step 4 **BigQuery / deferred analytics** advisory block once (even though questions are skipped), then skip to Validation Checklist with the existing `preferences.json`.
- If B: delete `preferences.json`, continue to Step 1.

**Case 2 — Draft preferences exist** (`preferences-draft.json` present, no `preferences.json`):

> "I found a partial set of answers from a previous session ([N] of [total] batches completed). Would you like to:"
>
> A) Resume from where you left off — I'll pick up the remaining questions
> B) Start fresh and re-answer all questions

- If A: load the draft, read `metadata.batches_completed` to determine which batches are done, skip completed batches when entering Step 4.
- If B: delete `preferences-draft.json`, continue to Step 1.

**Case 3 — No prior state**: Continue to Step 1.

---

## Step 1: Read Inventory and Determine Migration Type

Read `$MIGRATION_DIR/` and check which discovery outputs exist:

- `gcp-resource-inventory.json` + `gcp-resource-clusters.json` — infrastructure discovered
- `ai-workload-profile.json` — AI workloads detected
- `billing-profile.json` — billing data parsed

At least one discovery artifact must exist to proceed.

### Migration Type Detection

- **Full migration**: `gcp-resource-inventory.json` or `billing-profile.json` exists (may also have `ai-workload-profile.json`)
- **AI-only migration**: ONLY `ai-workload-profile.json` exists (no infrastructure or billing artifacts)

**If AI-only**: Read `clarify-ai-only.md` NOW and follow that flow. Skip all remaining steps below.

> **HARD GATE — AI-Only Path:** You MUST read `clarify-ai-only.md` before presenting any questions. The question text, answer options, and interpretation rules are ONLY in that file — they are NOT in this file. Do NOT fabricate questions from the summaries above.

### Discovery Summary

Present a discovery summary:

**If `gcp-resource-inventory.json` exists:**

> **Infrastructure discovered:** [total resources] GCP resources across [cluster count] clusters
> **Top resource types:** [list top 3–5 types]

**If `ai-workload-profile.json` exists:**

> **AI workloads detected:** [from `models[].model_id`]
> **Capabilities in use:** [from `integration.capabilities_summary` where true]
> **Integration pattern:** [from `integration.pattern`] via [from `integration.primary_sdk`]

**If `billing-profile.json` exists:**

> **Monthly GCP spend:** $[total_monthly_spend]
> **Top services by cost:** [top 3–5 from billing data]

---

## Step 1.5: Fast-Path Gate (Simple Stacks)

**After presenting the Discovery Summary**, check `$MIGRATION_DIR/migration-preview.json` for fast-path eligibility:

```
IF migration-preview.json exists
   AND eligible_for_clarify_fast_path == true
THEN offer infra fast-path (3 questions)
ELSE IF eligible_for_clarify_simple_path == true
THEN offer simple hybrid path (~6 questions)
ELSE skip to Step 2 (full Clarify)
```

### Infra fast-path (no AI)

**If `eligible_for_clarify_fast_path`**, present this offer before any questions:

> "Your stack looks straightforward — [primary_resource_count] resource(s), no database, no AI detected.
>
> Want to use smart defaults and answer just 3 questions instead of up to 22?
>
> **[Yes — 3 questions]** / **[No — ask me everything]**"

**If user chooses Yes:**

1. Ask only: **Q1** (region), **Q2** (compliance), **Q7** (maintenance window) — from `clarify-global.md`.
2. Apply documented defaults for ALL other questions. Record each in `metadata.questions_defaulted`.
3. Still run the BigQuery advisory if `bigquery_present` is true.
4. Write `preferences.json` with `metadata.clarify_mode: "fast_path"`. Skip Steps 2–4.

### Simple hybrid path (simple infra + lightweight AI)

**If `eligible_for_clarify_simple_path`**, present:

> "Your stack looks straightforward with lightweight AI ([model IDs from profile]) — no agentic framework detected.
>
> Want a short question set (~6 questions) instead of the full flow? I'll use discovery for region, database sizing, and model detection.
>
> **[Yes — short path]** / **[No — ask me everything]**"

**If user chooses Yes:**

1. Run **Step 2 extraction** (mandatory — do not skip).
2. Run **Step 2.5 Detected Settings Confirmation** (mandatory — wait for user response).
3. Ask only questions **not** resolved by extraction (after any user corrections):
   - **Q2** (compliance) — always ask
   - **Q7** (maintenance window) — always ask
   - **Q16** (AI priority) — from `clarify-ai.md`
   - **Q21** (AI latency) — from `clarify-ai.md`
   - **Q3** (GCP spend) — only if billing did not extract it
   - **Q1** (region) — only if region extraction ambiguous (multiple GCP regions)
4. Apply documented defaults for all other unanswered questions. Record in `metadata.questions_defaulted`.
5. Write `preferences.json` with `metadata.clarify_mode: "simple_hybrid"`. Skip Step 4 batch loop — go to Category E opt-in (if applicable) then Step 5.

**Agentic hard block:** If `agentic_profile.is_agentic == true`, **never offer** infra fast-path or simple hybrid path. Agentic workloads require Q23–Q26.

**If user chooses No, or neither path is eligible:** Continue to Step 2 (full Clarify).

---

## Step 2: Extract Known Information

Before generating questions, scan the inventory to extract values that are already known:

1. **GCP regions** — Extract all GCP regions from the inventory. Map to the closest AWS region as a suggested default for Q1.
2. **Resource types present** — Build a set of resource types: compute (Cloud Run, Cloud Functions, GKE, GCE), database (Cloud SQL, Spanner, Memorystore), storage (Cloud Storage), messaging (Pub/Sub).
3. **Billing SKUs** — If `billing-profile.json` exists, check if any SKU reveals storage class, HA configuration, or other answerable questions.
4. **Billing-only mode** — If `billing-profile.json` exists and `gcp-resource-inventory.json` does NOT exist, check `billing-profile.json → services[]` for Category B question matching.
5. **AI framework detection** — If `ai-workload-profile.json` exists, check `integration.gateway_type` and `integration.frameworks` for auto-detection of Q14 answer.
6. **BigQuery / analytics warehouse** — Set `bigquery_present` to **true** if **any** of: (a) a resource in `gcp-resource-inventory.json` has `gcp_type` (or equivalent type field) starting with `google_bigquery_`; (b) `billing-profile.json` lists a service/SKU that clearly indicates **BigQuery** (e.g., service name or SKU contains `BigQuery`). Otherwise `bigquery_present` is **false**.
7. **Database size auto-detect (Q13b)** — For each `google_sql_database_instance`, read `config.disk_size`, `config.disk_size_gb`, or `gcp_config.disk_size_gb`. Map to Q13b band and **skip Q13b** when unambiguous:

| Disk size (GB) | `db_size` value | Skip Q13b?                     |
| -------------- | --------------- | ------------------------------ |
| < 10           | `"<10GB"`       | Yes — `chosen_by: "extracted"` |
| 10 – 99        | `"10-100GB"`    | Yes — `chosen_by: "extracted"` |
| 100 – 499      | `"100-500GB"`   | Yes — `chosen_by: "extracted"` |
| ≥ 500          | `">500GB"`      | Yes — `chosen_by: "extracted"` |

If multiple instances disagree, ask Q13b. Record in `metadata.inventory_clarifications.db_size_gb` when extracted.

1. **Q6 from Cloud SQL HA** — For each `google_sql_database_instance`, read `availability_type` (or `config.availability_type`):

| GCP value  | `availability` extracted |
| ---------- | ------------------------ |
| `ZONAL`    | `"single-az"`            |
| `REGIONAL` | `"multi-az"`             |

Skip Q6 only when **all** Cloud SQL PostgreSQL/MySQL instances agree on the same mapped value. **`multi-az-ha` and `multi-region` are never auto-extracted** — those require Q6 user answers (Mission-Critical / Catastrophic). Cloud SQL `REGIONAL` maps to `multi-az` (RDS Multi-AZ), not `multi-az-ha` (Aurora). Record in `metadata.inventory_clarifications.cloud_sql_ha`. When `availability_type` is missing on any instance, or instances disagree, ask Q6.

1. **Q12/Q13 dev-tier defaults** — When **all** Cloud SQL instances match dev pattern (`db-f1-micro`, `db-g1-small`, or `tier` contains `micro`/`small` with `availability_type: ZONAL`), extract and **skip Q12 and Q13**. When instances mix dev and prod tiers, do not extract — ask Q12 and Q13.

```
database_traffic: "steady" — chosen_by: "extracted"
db_io_workload: "low" — chosen_by: "extracted"
```

1. **Q3 GCP spend from billing** — If `billing-profile.json` exists, map `summary.total_monthly_spend` to spend band and **skip Q3** when unambiguous:

| Monthly USD   | `gcp_monthly_spend` |
| ------------- | ------------------- |
| < 1,000       | `"<$1K"`            |
| 1,000–4,999   | `"$1K-$5K"`         |
| 5,000–19,999  | `"$5K-$20K"`        |
| 20,000–99,999 | `"$20K-$100K"`      |
| ≥ 100,000     | `">$100K"`          |

1. **Q1 region extraction** — When inventory has a **single** GCP region among PRIMARY compute/database resources, map to closest AWS region and **skip Q1** with `target_region` `chosen_by: "extracted"`. When multiple regions, suggest default but still ask Q1.

1. **Q19 primary model** — If `ai-workload-profile.json` exists and `models[0].model_id` is set with confidence ≥ 0.8, map to Q19 answer and **skip Q19**. Set `ai_model_baseline` with `chosen_by: "extracted"`.

1. **Q20 input modalities** — If `integration.capabilities_summary` exists:

| Signal                               | Extract                                                                           | Skip Q20?                                                |
| ------------------------------------ | --------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `vision: true`                       | `ai_vision: "vision-required"`                                                    | Yes                                                      |
| `image_generation: true` (no vision) | note in `ai_capabilities_required`; Q20 may still ask unless text-only path clear | Partial — skip if only text + image gen via separate API |
| all false / text only                | `ai_vision: "text-only"`                                                          | Yes                                                      |

When `image_generation: true` and `vision: false`, set `ai_capabilities_required` derived from profile and skip Q20 (image output is not vision _input_).

1. **Q9 WebSocket scan** — Only when application code was **actually analyzed**. Treat code as analyzed when **any** of: (a) `discover-app-code.md` ran and found source files; (b) `ai-workload-profile.json` → `metadata.sources_analyzed.application_code == true`; (c) a companion app directory was scanned. Scan for WebSocket usage: `websocket`, `WebSocket`, `socket.io`, `@nestjs/websockets`, FastAPI WebSocket, `ws` package imports. If code was analyzed and **no matches**, extract `websocket: false` and **skip Q9**. If matches found, ask Q9 to confirm.
   **If no application code was available** (Terraform-only workspace, no code discovery), do **NOT** extract Q9 — leave Q9 in the question flow. Absence of a code scan is not evidence of no WebSockets.

1. **Q10 Cloud Run traffic** — If Cloud Run `min_instance_count` / `min_instances` > 0 in Terraform config, extract `cloud_run_traffic_pattern: "constant-24-7"` and skip Q10. Otherwise ask Q10.

1. **Multi-instance Cloud SQL conflicts** — When multiple `google_sql_database_instance` resources **disagree** on values used for Q6, Q12/Q13, or Q13b (e.g. one ZONAL and one REGIONAL; mixed dev/prod tiers; different disk sizes):
   - Do **not** extract a single global value or skip the affected question(s)
   - Record per-instance values in `metadata.inventory_clarifications.cloud_sql_instances[]` (address, `availability_type`, `tier`, `disk_size_gb`)
   - In Step 2.5, show a **per-instance breakdown** (see below) instead of a single summary row
   - Ask the affected question(s), or let the user pick a global posture during Step 2.5 confirmation

Record all extracted values in `metadata.inventory_clarifications` where applicable. Questions fully resolved by extraction are **skipped** (not asked) with `chosen_by: "extracted"` and listed in `metadata.questions_skipped_extracted`.

**After Step 2 completes, proceed to Step 2.5 before Step 3 or any questions.**

---

## Step 2.5: Confirm Detected Settings (Mandatory Gate)

**When to run:** After Step 2 whenever any setting was extracted (i.e., `questions_skipped_extracted` would be non-empty, or any constraint was populated with `chosen_by: "extracted"` in working memory).

**Skip Step 2.5 only when** Step 2 produced zero extractions — nothing inferred from IaC, billing, or code. Proceed directly to Step 3.

**HARD GATE — do NOT present question batches or ask individual questions until the user responds to this summary.**

Present a structured table (omit rows for settings not extracted):

```
### What we detected from your Terraform, billing, and code

| Setting | Detected value | Source | Question skipped |
| ------- | -------------- | ------ | ---------------- |
| Region | us-west-2 (GCP us-west1) | gcp-resource-inventory.json | Q1 |
| GCP monthly spend | $1K–$5K (~$2,400/mo) | billing-profile.json | Q3 |
| Database availability | Single-AZ (Cloud SQL `ZONAL`) | Terraform `availability_type` | Q6 |
| Database size | 10–100 GB (allocated disk: 10 GB) | Terraform `disk_size` | Q13b |
| DB traffic / I/O | Steady / Low (dev-tier `db-f1-micro`) | Terraform tier + ZONAL | Q12, Q13 |
| Cloud Run traffic | Constant 24/7 (`min_instances > 0`) | Terraform | Q10 |
| WebSockets | None detected (code scanned) | application code scan | Q9 |
| AI framework | Direct SDK (no gateway) | ai-workload-profile.json | Q14 |
| AI model | gemini-2.5-flash | ai-workload-profile.json | Q19 |
| Input modalities | Text only | ai-workload-profile.json | Q20 |

Does this look correct?

- Reply **"looks good"** or **"correct"** to proceed — I'll only ask about what we couldn't infer.
- To fix something, name the setting and the correct value, e.g. **"availability: mission-critical"**, **"db size: 100-500GB"**, **"region: eu-central-1"**, **"model: gpt-4o"**. I'll update that setting; if the correction is ambiguous I'll ask the full question for that item.
- Reply **"ask me everything"** to discard all extractions and run the full question flow (clear `questions_skipped_extracted`; set all previously extracted constraints to pending).
```

**Multi-instance Cloud SQL conflicts:** When instances disagree, replace the single-row summary with a per-instance table and do **not** skip the conflicting question until resolved:

```
| Instance | availability_type | tier | disk_size (GB) |
| -------- | ----------------- | ---- | -------------- |
| google_sql_database_instance.main | ZONAL | db-f1-micro | 10 |
| google_sql_database_instance.analytics | REGIONAL | db-n1-standard-4 | 100 |

These instances disagree on availability. Which posture should we use for the migration design?
A) Most conservative (highest HA) | B) Use [instance name] as primary | C) Ask me the full Q6 question
```

**Override handling** — when the user corrects a detected value:

| User correction (examples)                       | Update constraint                                  | Re-ask?                   |
| ------------------------------------------------ | -------------------------------------------------- | ------------------------- |
| `availability: mission-critical` / `multi-az-ha` | `availability: "multi-az-ha"`, `chosen_by: "user"` | No — value is explicit    |
| `availability: significant` / `multi-az`         | `availability: "multi-az"`, `chosen_by: "user"`    | No                        |
| `availability: dev` / `single-az`                | `availability: "single-az"`, `chosen_by: "user"`   | No                        |
| `db size: <10GB` / `10-100GB` / etc.             | Set `db_size` to stated band, `chosen_by: "user"`  | No if band is explicit    |
| `region: [AWS region]`                           | Set `target_region`, `chosen_by: "user"`           | No                        |
| `model: [model name]`                            | Set `ai_model_baseline`, `chosen_by: "user"`       | No if maps cleanly to Q19 |
| `websockets: yes`                                | Set `websocket: "required"`, `chosen_by: "user"`   | No                        |
| `spend: $5K-$20K`                                | Set `gcp_monthly_spend`, `chosen_by: "user"`       | No if band is explicit    |
| Vague correction ("that's wrong")                | Remove that item from skipped list                 | Yes — ask full question   |

For each override: remove the associated question ID(s) from `metadata.questions_skipped_extracted`, set `chosen_by: "user"`, and record in `metadata.detected_settings` with `"confirmed": false` and `"corrected_by_user": true`.

When user confirms: mark all rows `"confirmed": true` in `metadata.detected_settings`.

**`metadata.detected_settings` schema** (write to `preferences.json` at Step 5):

```json
"detected_settings": [
  {
    "key": "availability",
    "value": "single-az",
    "source": "terraform:availability_type=ZONAL",
    "questions_skipped": ["Q6"],
    "confirmed": true,
    "corrected_by_user": false
  }
]
```

---

## Step 3: Generate Questions by Category

### Category Definitions and Firing Rules

| Category | Name               | Firing Rule                                                                    | Reference File        | Questions                                                                                                           |
| -------- | ------------------ | ------------------------------------------------------------------------------ | --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **A**    | Global/Strategic   | **Always fires**                                                               | `clarify-global.md`   | Q1 (location), Q2 (compliance), Q3 (GCP spend), Q4 (funding stage), Q5 (multi-cloud), Q6 (uptime), Q7 (maintenance) |
| **B**    | Configuration Gaps | `billing-profile.json` exists AND `gcp-resource-inventory.json` does NOT exist | `clarify-compute.md`  | Cloud SQL HA, Cloud Run count, Memorystore memory, Functions gen                                                    |
| **C**    | Compute Model      | Compute resources present (Cloud Run, Cloud Functions, GKE, GCE)               | `clarify-compute.md`  | Q8 (K8s sentiment), Q9 (WebSocket), Q10 (Cloud Run traffic), Q11 (Cloud Run spend)                                  |
| **D**    | Database Model     | Database resources present (Cloud SQL, Spanner, Memorystore)                   | `clarify-database.md` | Q12 (DB traffic pattern), Q13 (DB I/O), Q13b (DB size)                                                              |
| **E**    | Migration Posture  | **Disabled by default** — requires explicit user opt-in                        | _(inline below)_      | HA upgrades, right-sizing                                                                                           |
| **F**    | AI/Bedrock         | `ai-workload-profile.json` exists                                              | `clarify-ai.md`       | Q14–Q26 (Q14–Q22 always; Q23–Q26 only when `agentic_profile.is_agentic == true`)                                    |

**Apply firing rules to determine which categories are active:**

1. Category A is always active.
2. Check for billing-only mode — if `billing-profile.json` exists and `gcp-resource-inventory.json` does NOT, Category B is active.
3. Check for compute resources — if present, Category C is active. Within C, skip Q8 if no GKE present. Skip Q10/Q11 if no Cloud Run present.
4. Check for database resources — if present, Category D is active.
5. Category E is disabled by default. Offered after the last batch completes in Step 4 (see **Category E Opt-In** in Step 4). If user declines or does not respond, apply Category E defaults (no HA upgrades, no right-sizing).
6. Check for `ai-workload-profile.json` — if present, Category F is active.

**If no IaC, billing data, or code is available** (empty discovery): only Category A is active. All service-specific categories are skipped.

### HARD GATE — Read Category Files Before Proceeding

> **STOP. You MUST read each active category's file NOW, before moving to Step 4.**
>
> The exact question wording, answer options, context rationale, and interpretation rules exist ONLY in the category files listed below. They are NOT in this file. The table above is a summary index only — do NOT use it to fabricate questions.
>
> **Read these files based on which categories are active:**
>
> | Active Category | File to Read          |
> | --------------- | --------------------- |
> | A (always)      | `clarify-global.md`   |
> | B or C          | `clarify-compute.md`  |
> | D               | `clarify-database.md` |
> | F               | `clarify-ai.md`       |
>
> **Do NOT proceed to Step 4 until you have read every applicable file above.**

### Early-Exit Rules

Apply these before presenting questions:

- **Q5 = "Yes, multi-cloud required"** — Immediately record `compute: "eks"`. Skip Q8 (Kubernetes sentiment) — all container workloads resolve to EKS.
- **Q6 extracted** — When Step 2 mapped Cloud SQL `availability_type` → skip Q6.
- **Q10/Q11 N/A** — Cloud Run not present, auto-skip.
- **Q10 extracted** — When min_instances > 0, skip Q10.
- **Q12/Q13 N/A** — Cloud SQL (PostgreSQL or MySQL) not present in inventory, auto-skip.
- **Q12/Q13 extracted** — Dev-tier Cloud SQL (Step 2 item 9), skip Q12 and Q13.
- **Q13b extracted** — Unambiguous disk size from inventory (Step 2 item 7), skip Q13b.
- **Q3 extracted** — Billing band mapped (Step 2 item 10), skip Q3.
- **Q1 extracted** — Single-region inventory (Step 2 item 11), skip Q1.
- **Q9 extracted** — No WebSocket signals in a completed code scan (Step 2 item 14), skip Q9. **Do not extract** when no code was analyzed.
- **Q14 auto-detected** — If `integration.gateway_type` is non-null OR `integration.frameworks` is non-empty in `ai-workload-profile.json`, skip Q14. Set `ai_framework` with `chosen_by: "extracted"`.
- **Q19 auto-detected** — Primary model from `ai-workload-profile.json` (Step 2 item 12), skip Q19.
- **Q20 auto-detected** — Modalities from `capabilities_summary` (Step 2 item 13), skip Q20.

### Batch Planning

After determining active categories, organize questions into **up to three batches** presented sequentially with intermediate saves:

| Batch | Name                   | Categories                                 | Questions                         | Fires When                                |
| ----- | ---------------------- | ------------------------------------------ | --------------------------------- | ----------------------------------------- |
| **1** | Strategic Requirements | A (Global/Strategic)                       | Q1–Q7 (minus Q4)                  | Always                                    |
| **2** | Infrastructure         | B (Config Gaps), C (Compute), D (Database) | Q8–Q13b + Category B prompts      | Any compute or database resources present |
| **3** | AI Workloads           | F (AI/Bedrock)                             | Q14–Q26 (Q23–Q26 only if agentic) | `ai-workload-profile.json` exists         |

**Determine active batches:**

1. Batch 1 is always active.
2. Batch 2 is active if Category B, C, or D fired.
3. Batch 3 is active if Category F fired.

Record the ordered list of active batches and count the questions per batch (after extraction and early-exit filtering). These counts are used for per-batch progress messaging — not shown as a grand total upfront.

**Category E** (Migration Posture) is offered after the last substantive batch completes, before writing final `preferences.json`.

---

## Category E — Migration Posture (Disabled by Default)

_Fire when:_ User explicitly opts in.
_Default behavior when disabled:_ Apply conservative defaults — no HA upgrades, no right-sizing.

If the user opts in, present after all other categories:

### Q-E1 — Should we recommend upgrading Single-AZ to Multi-AZ where possible?

> A) Yes — upgrade to Multi-AZ for higher availability | B) No — keep current topology

Interpret → `ha_upgrade`: A → `true`, B → `false`. Default: B → `false`.

### Q-E2 — Should we use billing utilization data to right-size instance types?

> A) Yes — right-size based on utilization | B) No — match current capacity

Interpret → `right_sizing`: A → `true`, B → `false`. Default: B → `false`.

---

## Step 4: Present Questions in Progressive Batches

**Prerequisite:** Step 2.5 confirmation must be complete (user said "looks good" or finished correcting) before presenting Batch 1. Do not re-show the full detected-settings table here unless the user asks for a recap.

**BigQuery / deferred analytics (mandatory callout):** If Step 2 set `bigquery_present` to **true**, output this block **once**, **before** any questions (same turn as Batch 1), then continue with the question flow:

> **BigQuery / analytics warehouse:** Your discovery inputs include BigQuery. This skill **does not** select an AWS analytics or data-warehouse target (no Athena, Redshift, Glue, or EMR recommendation from the plugin). **Before** warehouse, data lake, SQL analytics, or BI cutover planning, engage your **AWS account team** and/or a **data analytics migration partner** to assess query patterns, data volumes, ETL/ELT, and downstream consumers. Design will mark these resources as **`Deferred — specialist engagement`**.

Questions are presented in sequential batches with a save after each. After each batch the user can skip individual questions (defaults applied), say **"use defaults for the rest"** to apply defaults for all remaining batches and proceed immediately, or answer normally.

### Batch Loop

For each active batch (determined in Batch Planning above), execute steps 4a–4d:

#### 4a. Present Batch

Use a conversational tone with brief context explaining why each question matters. Number questions within each batch starting from 1.

**Batch 1 — Strategic Requirements (always first):**

```
Before mapping your infrastructure to AWS, I have a few sections of questions
to tailor the migration plan. You can answer each, skip individual ones
(I'll use sensible defaults), or say "use defaults for the rest" at any point.

Let's start with your strategic requirements.

--- Strategic Requirements ---

Question 1: [Q1 text with context]
Question 2: [Q2 text with context]
...
Question [N]: [Q7 text with context]
```

**Batch 2 — Infrastructure (if active):**

After Batch 1 answers are saved, present:

```
Got it — your strategic preferences are saved.

Next up: [N] questions about your compute and database setup.
You can answer each, skip individual ones, or say "use defaults for the rest."

--- Infrastructure ---

Question 1: [first active question text with context]
...
```

**Batch 3 — AI Workloads (if active):**

After prior batch answers are saved, present. Adapt the intro based on whether this is the second or third batch:

```
[Infrastructure preferences saved. / Strategic preferences saved.]

Last section — [N] questions about your AI workloads, then we're ready to design.
You can answer each, skip individual ones, or say "use defaults for the rest."

--- AI Workloads ---

Question 1: [first active question text with context]
...
```

If Batch 3 is the second batch (Batch 2 was skipped because no infra resources), use "Next up" instead of "Last section" if appropriate.

**Single-batch shortcut:** If only Batch 1 is active (no infrastructure or AI categories fired), skip the multi-batch framing. Present Batch 1 questions with a simpler intro and proceed directly to Category E opt-in then Step 5 after answers — no draft file needed.

#### 4b. Wait for Response

Wait for the user's response to the current batch. Do NOT present the next batch or proceed to Design without a response or an explicit "use defaults for the rest."

**"Use defaults for the rest" handling:** If the user says this at any point:

1. Apply documented defaults for all unanswered questions in the current batch.
2. Apply documented defaults for all questions in remaining batches.
3. Skip directly to Category E opt-in, then Step 5 (write final `preferences.json`).

#### 4c. Interpret Batch Answers

Apply the interpret rule (from the category reference files) for every answered question in the batch. For skipped questions within the batch, apply the documented default.

Apply early-exit rules triggered by this batch's answers. For example, if Batch 1 includes Q5 = "Yes, multi-cloud required", record `compute: "eks"` and mark Q8 as skipped (early-exit) for Batch 2.

#### 4d. Save Draft

**If more batches remain** after this one: Write (or update) `$MIGRATION_DIR/preferences-draft.json` with all answers collected so far. Use the same schema as `preferences.json` with these additional `metadata` fields:

```json
{
  "metadata": {
    "draft": true,
    "batches_completed": ["strategic"],
    "batches_remaining": ["infrastructure", "ai"],
    "migration_type": "full",
    "timestamp": "<ISO timestamp>",
    ...
  },
  "design_constraints": { ... },
  "ai_constraints": { ... }
}
```

Batch name values: `"strategic"`, `"infrastructure"`, `"ai"`.

Return to **4a** for the next batch.

**If this was the last active batch**: Do not write a draft — proceed to **Category E opt-in** then **Step 5**.

### Category E Opt-In

After the last substantive batch is answered (but before writing final `preferences.json`), offer Category E if `billing-profile.json` exists:

> "Would you also like HA upgrade and right-sizing recommendations based on your billing data? If not, I'll use conservative defaults (no upgrades, match current capacity)."

If user opts in, present Q-E1–Q-E2 (defined in **Category E — Migration Posture** above). Otherwise, apply Category E defaults (`ha_upgrade: false`, `right_sizing: false`).

---

## Answer Combination Triggers

| Scenario                                 | Key Answers                                                   | Recommendation                                                                                 |
| ---------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Early-stage funding path                 | Q3 = lower spend band                                         | Entry-tier migration funding program review                                                    |
| Growth-stage funding path                | Q3 = higher spend band                                        | Migration funding/support program review based on spend profile                                |
| Must stay portable                       | Q5 = Yes multi-cloud                                          | EKS only, no ECS Fargate                                                                       |
| Kubernetes-averse                        | Q5 = No + Q8 = Frustrated                                     | ECS Fargate strongly recommended                                                               |
| WebSocket app                            | Q9 = Yes                                                      | ALB WebSocket config required                                                                  |
| Low-traffic Cloud Run                    | Q10 = Business hours + Q11 < $100                             | Recommend staying on Cloud Run                                                                 |
| Cloud SQL Postgres — dev/low HA          | Q6 = Inconvenient + Cloud SQL in inventory                    | **RDS PostgreSQL** single-AZ                                                                   |
| Cloud SQL Postgres — prod HA (RDS)       | Q6 = Significant Issue + Cloud SQL in inventory               | **RDS PostgreSQL** Multi-AZ                                                                    |
| Cloud SQL Postgres — mission-critical    | Q6 = Mission-Critical + Cloud SQL in inventory                | **Aurora PostgreSQL** Multi-AZ; apply Q12/Q13                                                  |
| Cloud SQL Postgres — global catastrophic | Q6 = Catastrophic + Q1 = Global + Cloud SQL in inventory      | **Aurora PostgreSQL Global Database**                                                          |
| High I/O database (RDS path)             | Q6 = Inconvenient/Significant + Q13 = High                    | **RDS** io2 or Provisioned IOPS                                                                |
| High I/O database (Aurora path)          | Q6 = Mission-Critical/Catastrophic + Q13 = High               | Aurora I/O-Optimized                                                                           |
| Write-heavy global DB                    | Q6 = Mission-Critical/Catastrophic + Q12 = Write-heavy/global | Aurora DSQL architecture review (RDS path only: size writer; flag review)                      |
| Rapidly growing DB (RDS path)            | Q6 = Inconvenient/Significant + Q12 = Rapidly growing         | RDS with headroom on instance class                                                            |
| Rapidly growing DB (Aurora path)         | Q6 = Mission-Critical/Catastrophic + Q12 = Rapidly growing    | Aurora Serverless v2                                                                           |
| Zero downtime required                   | Q7 = No downtime                                              | Blue/green + AWS DMS required (RDS or Aurora blue/green per Q6)                                |
| HIPAA compliance                         | Q2 = HIPAA                                                    | BAA services only, specific regions                                                            |
| FedRAMP required                         | Q2 = FedRAMP                                                  | GovCloud regions only                                                                          |
| CCPA / CPRA                              | Q2 = G (CCPA / CPRA)                                          | Consumer privacy, logging/retention, data-inventory posture; confirm regions with legal review |
| Gateway-only AI                          | Q14 = B only (LLM router/gateway)                             | Config change only; skip SDK migration                                                         |
| LangChain/LangGraph AI                   | Q14 includes C                                                | Provider swap via ChatBedrock; 1–3 days                                                        |
| OpenAI Agents SDK                        | Q14 includes E                                                | Highest AI effort; Bedrock Agents; 2–4 weeks                                                   |
| Multi-agent + MCP                        | Q14 = D + F                                                   | Bedrock Agents to unify orchestration + MCP                                                    |
| Voice platform AI                        | Q14 includes G                                                | Check native Bedrock support; Nova 2 Sonic if needed                                           |
| GPT-5.5 migration                        | Q19 = GPT-5.5                                                 | Claude Opus 4.6 — Bedrock 17% cheaper on output; or Sonnet 4.6 for 53% savings                 |
| GPT-5.5 Pro migration                    | Q19 = GPT-5.5 Pro                                             | Nova 2 Pro — 95% cheaper on Bedrock                                                            |
| GPT-5.4 migration                        | Q19 = GPT-5.4                                                 | Claude Sonnet 4.6 — near price parity; AWS consolidation                                       |
| GPT-5.4 Mini/Nano migration              | Q19 = GPT-5.4 Mini or Nano                                    | Nova Lite/Micro — 87-94% cheaper on Bedrock                                                    |
| GPT-4 Turbo migration                    | Q19 = GPT-4 Turbo                                             | Claude Sonnet 4.6 — 70% cheaper on input                                                       |
| o-series migration                       | Q19 = o-series                                                | Claude Sonnet 4.6 with extended thinking                                                       |
| High-volume cost-critical AI             | Q18 = High + cost critical                                    | Nova Micro or Haiku 4.5 + provisioned throughput                                               |
| Reasoning/agent workload                 | Q17 = Extended thinking                                       | Claude Sonnet 4.6 extended thinking; Opus 4.6 for hardest                                      |
| Speech-to-speech AI                      | Q17 = Real-time speech                                        | Nova 2 Sonic                                                                                   |
| RAG workload                             | Q17 = RAG optimization                                        | Bedrock Knowledge Bases + Titan Embeddings                                                     |
| Vision workload                          | Q20 = Vision required                                         | Claude Sonnet 4.6 (multimodal)                                                                 |
| Latency-critical AI                      | Q21 = Critical                                                | Haiku 4.5 or Nova Micro + streaming                                                            |
| Complex reasoning tasks                  | Q22 = Complex                                                 | Claude Sonnet 4.6; Opus 4.6 for hardest                                                        |

---

## Step 5: Assemble and Write preferences.json

Assemble all interpreted answers from the completed batches into the final `$MIGRATION_DIR/preferences.json`. If `preferences-draft.json` exists, use it as the base — merge in the final batch's answers, remove the draft-specific metadata fields (`draft`, `batches_completed`, `batches_remaining`), and set `metadata.timestamp` to the current time. Write `$MIGRATION_DIR/preferences.json`:

```json
{
  "metadata": {
    "migration_type": "full",
    "timestamp": "<ISO timestamp>",
    "discovery_artifacts": ["gcp-resource-inventory.json", "ai-workload-profile.json"],
    "questions_asked": [
      "Q1",
      "Q2",
      "Q3",
      "Q5",
      "Q6",
      "Q7",
      "Q16",
      "Q17",
      "Q19",
      "Q21",
      "Q22"
    ],
    "questions_defaulted": ["Q9"],
    "questions_skipped_extracted": ["Q14"],
    "questions_skipped_early_exit": ["Q8"],
    "questions_skipped_not_applicable": ["Q4", "Q10", "Q11", "Q12", "Q13", "Q13b"],
    "detected_settings": [
      {
        "key": "availability",
        "value": "multi-az",
        "source": "terraform:availability_type=REGIONAL",
        "questions_skipped": ["Q6"],
        "confirmed": true,
        "corrected_by_user": false
      }
    ],
    "category_e_enabled": false,
    "clarify_mode": "full",
    "inventory_clarifications": {}
  },
  "design_constraints": {
    "target_region": { "value": "us-east-1", "chosen_by": "user" },
    "compliance": { "value": ["hipaa"], "chosen_by": "user" },
    "gcp_monthly_spend": { "value": "$5K-$20K", "chosen_by": "user" },
    "funding_stage": { "value": "series-a", "chosen_by": "user" },
    "availability": { "value": "multi-az", "chosen_by": "default" },
    "cutover_strategy": { "value": "maintenance-window-weekly", "chosen_by": "user" },
    "kubernetes": { "value": "eks-or-ecs", "chosen_by": "user" },
    "database_traffic": { "value": "steady", "chosen_by": "user" },
    "db_io_workload": { "value": "medium", "chosen_by": "user" },
    "db_size": { "value": "10-100GB", "chosen_by": "user" }
  },
  "ai_constraints": {
    "ai_framework": { "value": ["direct"], "chosen_by": "extracted" },
    "ai_monthly_spend": { "value": "$500-$2K", "chosen_by": "user" },
    "ai_priority": { "value": "balanced", "chosen_by": "user" },
    "ai_critical_feature": { "value": "function-calling", "chosen_by": "user" },
    "ai_token_volume": { "value": "low", "chosen_by": "user" },
    "ai_model_baseline": { "value": "claude-sonnet-4-6", "chosen_by": "user" },
    "ai_vision": { "value": "text-only", "chosen_by": "user" },
    "ai_latency": { "value": "important", "chosen_by": "user" },
    "ai_complexity": { "value": "moderate", "chosen_by": "user" },
    "ai_capabilities_required": {
      "value": ["text_generation", "streaming", "function_calling"],
      "chosen_by": "extracted"
    }
  }
}
```

### Schema Rules

1. Every entry in `design_constraints` and `ai_constraints` is an object with `value` and `chosen_by` fields.
2. `chosen_by` values: `"user"` (explicitly answered), `"default"` (system default applied — includes "I don't know" answers), `"extracted"` (inferred from inventory), `"derived"` (computed from combination of answers + detected capabilities).
3. Only write a key to `design_constraints` / `ai_constraints` if the answer produces a constraint. Absent keys mean "no constraint — Design decides."
4. Do not write null values.
5. For billing-source inventories, `metadata.inventory_clarifications` records Category B answers.
6. `metadata.questions_skipped_early_exit` records questions skipped due to early-exit logic (e.g., Q8 skipped because Q5=multi-cloud).
7. `metadata.questions_skipped_extracted` records questions skipped because inventory already provided the answer.
8. `metadata.detected_settings` records each auto-detected setting with source, confirmation status, and whether the user corrected it in Step 2.5.
9. `metadata.questions_skipped_not_applicable` records questions skipped because the relevant service wasn't in the inventory.
10. `ai_constraints` section is present ONLY if Category F fired. Omit entirely if no AI artifacts exist.
11. `ai_constraints.ai_capabilities_required` is the UNION of detected capabilities from `ai-workload-profile.json` + critical feature from Q17 + vision from Q20. `chosen_by` is `"derived"`.
12. `ai_constraints.ai_framework` is an array (Q14 is select-all-that-apply). If auto-detected, `chosen_by` is `"extracted"`.

After writing `preferences.json`, delete `$MIGRATION_DIR/preferences-draft.json` if it exists.

---

## Defaults Table

| Question                | Default              | Constraint                                        |
| ----------------------- | -------------------- | ------------------------------------------------- |
| Q1 — Location           | A (single region)    | `target_region`: closest AWS region to GCP region |
| Q2 — Compliance         | A (none)             | no constraint                                     |
| Q3 — GCP spend          | B ($1K–$5K)          | `gcp_monthly_spend: "$1K-$5K"`                    |
| Q4 — Funding stage      | _(skip in IDE mode)_ | no constraint                                     |
| Q5 — Multi-cloud        | B (AWS-only)         | no constraint                                     |
| Q6 — Uptime             | B (significant)      | `availability: "multi-az"`                        |
| Q7 — Maintenance        | D (flexible)         | `cutover_strategy: "flexible"`                    |
| Q8 — K8s sentiment      | B (neutral)          | `kubernetes: "eks-or-ecs"`                        |
| Q9 — WebSocket          | B (no)               | no constraint                                     |
| Q10 — Cloud Run traffic | C (24/7)             | `cloud_run_traffic_pattern: "constant-24-7"`      |
| Q11 — Cloud Run spend   | B ($100–$500)        | `cloud_run_monthly_spend: "$100-$500"`            |
| Q12 — DB traffic        | A (steady)           | `database_traffic: "steady"`                      |
| Q13 — DB I/O            | B (medium)           | `db_io_workload: "medium"`                        |
| Q13b — DB size          | E (unknown)          | `db_size: "unknown"` → default to pgcopydb        |
| Q14 — AI framework      | _(auto-detect)_      | `ai_framework` from code detection                |
| Q15 — AI spend          | B ($500–$2K)         | `ai_monthly_spend: "$500-$2K"`                    |
| Q16 — AI priority       | E (balanced)         | `ai_priority: "balanced"`                         |
| Q17 — Critical feature  | J (none)             | no additional override                            |
| Q18 — Volume + cost     | A (low + quality)    | `ai_token_volume: "low"`                          |
| Q19 — Current model     | _(auto-detect)_      | `ai_model_baseline` from code detection           |
| Q20 — Input types       | A (text only)        | no constraint                                     |
| Q21 — AI latency        | B (important)        | `ai_latency: "important"`                         |
| Q22 — Task complexity   | B (moderate)         | `ai_complexity: "moderate"`                       |

---

## Validation Checklist

Before handing off to Design:

- [ ] If extractions were made, Step 2.5 detected-settings confirmation was shown and user responded before questions
- [ ] If extractions were made, `metadata.detected_settings` records each inferred value with `confirmed` status
- [ ] If `bigquery_present` was **true**, the Step 4 BigQuery specialist advisory was shown before questions — **or**, if Step 0 option A (reuse preferences), the same advisory was shown after BigQuery detection
- [ ] `preferences.json` written to `$MIGRATION_DIR/`
- [ ] `design_constraints.target_region` is populated with `value` and `chosen_by`
- [ ] `design_constraints.availability` is populated when Cloud SQL PostgreSQL/MySQL is in inventory (asked, extracted, or defaulted — Design must not run with absent/null availability)
- [ ] Only keys with non-null values are present in `design_constraints`
- [ ] Every entry in `design_constraints` and `ai_constraints` has `value` and `chosen_by` fields
- [ ] Config gap answers recorded in `metadata.inventory_clarifications` (billing mode only)
- [ ] Early-exit skips recorded in `metadata.questions_skipped_early_exit`
- [ ] `ai_constraints` section present ONLY if Category F fired
- [ ] If Category F fired, `ai_constraints.ai_framework` is populated (from detection or Q14)
- [ ] If Category F fired, `ai_capabilities_required` is derived from detection + Q17 + Q20
- [ ] `ai_constraints.ai_framework` is an array (Q14 is multi-select)
- [ ] Output is valid JSON
- [ ] `preferences-draft.json` has been deleted (if it existed)
- [ ] `metadata.clarify_mode` is set to `"fast_path"`, `"simple_hybrid"`, or `"full"`

---

## Completion Handoff Gate (Fail Closed)

Load `steering/handoff-gates.md`. **Re-read from disk** before checking.

**Re-entry guard:** If `aws-design.json` (or `aws-design-ai.json` / `aws-design-billing.json`) exists and `phases.design` is `"completed"`: STOP unless the user explicitly confirms re-running Clarify. Emit `GATE_FAIL | phase=clarify | field=aws-design.json | reason=stale_downstream`.

**Checks (all must PASS):**

1. `preferences.json` exists and parses as JSON.
2. Step 5 validation checklist items all pass (including `metadata.clarify_mode`).
3. If `gcp-resource-inventory.json` contains `google_sql_database_instance` → `design_constraints.availability.value` is set (non-null, non-empty).

**On any FAIL:** Emit `GATE_FAIL | phase=clarify | field=<path> | reason=missing`. **Do NOT modify artifacts to pass the gate.** **Do NOT update `.phase-status.json`.** Tell the user to answer the missing question or re-run Clarify.

**On PASS:** Emit `HANDOFF_OK | phase=clarify | artifacts=preferences.json`.

## Step 6: Update Phase Status

Only after `HANDOFF_OK`. In the **same turn** as the output message below, use the Phase Status Update Protocol (Write tool) to write `.phase-status.json` with `phases.clarify` set to `"completed"`.

Output to user: "Clarification complete. Proceeding to Phase 3: Design AWS Architecture."

---

## Scope Boundary

**This phase covers requirements gathering ONLY.**

FORBIDDEN — Do NOT include ANY of:

- Detailed AWS architecture or service configurations
- Code migration examples or SDK snippets
- Detailed cost calculations
- Migration timelines or execution plans
- Terraform generation

**Your ONLY job: Understand what the user needs. Nothing else.**
