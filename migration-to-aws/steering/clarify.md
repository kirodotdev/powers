# Phase 2: Clarify Requirements

**Phase 2 of 5** — Ask adaptive questions before design begins, then interpret answers into ready-to-apply design constraints.

The output — `preferences.json` — is consumed directly by Design and Estimate without any further interpretation.

Questions are organized into **six named categories (A–F)** with documented firing rules. Up to 22 questions across categories, depending on which discovery artifacts exist and which GCP services are detected. A standalone **AI-Only** flow exists for migrations that only move AI/LLM calls to Bedrock.

## Category Reference Files

| File                  | Category                     | Questions | Loaded When                                     |
| --------------------- | ---------------------------- | --------- | ----------------------------------------------- |
| `clarify-global.md`   | A — Global/Strategic         | Q1–Q7     | Always                                          |
| `clarify-compute.md`  | B — Config Gaps, C — Compute | Q8–Q11    | Compute or billing-source resources present     |
| `clarify-database.md` | D — Database                 | Q12–Q13   | Database resources present                      |
| `clarify-ai.md`       | F — AI/Bedrock               | Q14–Q22   | `ai-workload-profile.json` exists               |
| `clarify-ai-only.md`  | _(standalone)_               | Q1–Q10    | AI-only migration (no infrastructure artifacts) |

---

## Step 0: Prior Run Check

If `$MIGRATION_DIR/preferences.json` already exists:

> "I found existing migration preferences from a previous run. Would you like to:"
>
> A) Re-use these preferences and skip questions
> B) Start fresh and re-answer all questions

- If A: skip to Validation Checklist, proceed with existing file.
- If B: continue to Step 1.

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

**If AI-only**: Read `steering/clarify-ai-only.md` NOW and follow that flow. Skip all remaining steps below.

> **HARD GATE — AI-Only Path:** You MUST read `steering/clarify-ai-only.md` before presenting any questions. The question text, answer options, and interpretation rules are ONLY in that file — they are NOT in this file. Do NOT fabricate questions from the summaries above.

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

## Step 2: Extract Known Information

Before generating questions, scan the inventory to extract values that are already known:

1. **GCP regions** — Extract all GCP regions from the inventory. Map to the closest AWS region as a suggested default for Q1.
2. **Resource types present** — Build a set of resource types: compute (Cloud Run, Cloud Functions, GKE, GCE), database (Cloud SQL, Spanner, Memorystore), storage (Cloud Storage), messaging (Pub/Sub).
3. **Billing SKUs** — If `billing-profile.json` exists, check if any SKU reveals storage class, HA configuration, or other answerable questions.
4. **GCP spend baseline** — If `billing-profile.json` exists, read `summary.total_monthly_spend` and map it to the Q3 bucket (`<1000` → A, `1000-5000` → B, `5000-20000` → C, `20000-100000` → D, `>100000` → E). Use this as the **billing-informed default for Q3** instead of the hardcoded B. Still ask Q3 (the user may know about spend beyond this billing export), but if they answer "I don't know" or "use all defaults", apply the billing-derived bucket.
5. **Config confidence** — If inventory `metadata.source = "billing"`, identify resources with `config_confidence = "assumed"` for Category B questions.
6. **AI framework detection** — If `ai-workload-profile.json` exists, check `integration.gateway_type` and `integration.frameworks` for auto-detection of Q14 answer.

Record extracted values. Questions whose answers are fully determined by extraction will be skipped and the extracted value used directly with `chosen_by: "extracted"`.

---

## Step 3: Generate Questions by Category

### Category Definitions and Firing Rules

| Category | Name               | Firing Rule                                                                                     | Reference File        | Questions                                                                                                           |
| -------- | ------------------ | ----------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **A**    | Global/Strategic   | **Always fires**                                                                                | `clarify-global.md`   | Q1 (location), Q2 (compliance), Q3 (GCP spend), Q4 (funding stage), Q5 (multi-cloud), Q6 (uptime), Q7 (maintenance) |
| **B**    | Configuration Gaps | Inventory with `metadata.source == "billing"` AND at least one `config_confidence == "assumed"` | `clarify-compute.md`  | Cloud SQL HA, Cloud Run count, Memorystore memory, Functions gen                                                    |
| **C**    | Compute Model      | Compute resources present (Cloud Run, Cloud Functions, GKE, GCE)                                | `clarify-compute.md`  | Q8 (K8s sentiment), Q9 (WebSocket), Q10 (Cloud Run traffic), Q11 (Cloud Run spend)                                  |
| **D**    | Database Model     | Database resources present (Cloud SQL, Spanner, Memorystore)                                    | `clarify-database.md` | Q12 (DB traffic pattern), Q13 (DB I/O)                                                                              |
| **E**    | Migration Posture  | **Disabled by default** — requires explicit user opt-in                                         | _(inline below)_      | HA upgrades, right-sizing                                                                                           |
| **F**    | AI/Bedrock         | `ai-workload-profile.json` exists                                                               | `clarify-ai.md`       | Q14–Q22                                                                                                             |

**Apply firing rules to determine which categories are active:**

1. Category A is always active.
2. Check inventory `metadata.source` — if `"billing"` with assumed configs, Category B is active.
3. Check for compute resources — if present, Category C is active. Within C, skip Q8 if no GKE present. Skip Q10/Q11 if no Cloud Run present.
4. Check for database resources — if present, Category D is active.
5. Category E is disabled by default. Do not activate unless user opts in.
6. Check for `ai-workload-profile.json` — if present, Category F is active.

**If no IaC, billing data, or code is available** (empty discovery): only Category A is active. All service-specific categories are skipped.

### HARD GATE — Read Category Files Before Proceeding

> **STOP. You MUST read each active category's file NOW, before moving to Step 4.**
>
> The exact question wording, answer options, context rationale, and interpretation rules exist ONLY in the category files listed below. They are NOT in this file. The table above is a summary index only — do NOT use it to fabricate questions.
>
> **Read these files based on which categories are active:**
>
> | Active Category | File to Read                    |
> | --------------- | ------------------------------- |
> | A (always)      | `steering/clarify-global.md`    |
> | B or C          | `steering/clarify-compute.md`   |
> | D               | `steering/clarify-database.md`  |
> | F               | `steering/clarify-ai.md`        |
>
> **Do NOT proceed to Step 4 until you have read every applicable file above.**

### Early-Exit Rules

Apply these before presenting questions:

- **Q5 = "Yes, multi-cloud required"** — Immediately record `compute: "eks"`. Skip Q8 (Kubernetes sentiment) — all container workloads resolve to EKS.
- **Q10/Q11 N/A** — Cloud Run not present, auto-skip.
- **Q12/Q13 N/A** — Cloud SQL not present, auto-skip.
- **Q14 auto-detected** — If `integration.gateway_type` and `integration.frameworks` fully resolve the framework, skip Q14 and use extracted value.

---

## Category E — Migration Posture (Disabled by Default)

_Fire when:_ User explicitly opts in.
_Default behavior when disabled:_ Apply conservative defaults — no HA upgrades, no right-sizing.

If the user opts in, present after all other categories:

- **HA upgrade preference**: Should we recommend upgrading Single-AZ to Multi-AZ where possible?
  > Default: No — keep current topology.
- **Right-sizing from billing**: Should we use billing utilization data to right-size instance types?
  > Default: No — match current capacity.

---

## Step 4: Present Questions Interactively

Present questions **one at a time** in conversational order. Wait for the user's response to each question before presenting the next one. This creates a natural dialogue rather than an overwhelming form.

**Formatting rule:** When presenting answer options, put each option on its own line with a blank line between options so they are visually separated and easy to scan. Never run options together on consecutive lines without spacing.

### Flow

1. **Calculate question set**: Before starting, determine which questions will be asked. Remove all **pre-excluded** questions first — these are never counted in M and never mentioned to the user:
   - Category firing rules (which categories are active based on inventory artifacts)
   - N/A skips (Cloud Run not present → remove Q10/Q11; Cloud SQL not present → remove Q12/Q13; no GKE → remove Q8)
   - Auto-detection skips (Q14 framework auto-detected from code)
   - IDE/CLI mode skips (Q4 in non-web mode)

   Pre-excluded questions do not exist from the user's perspective — do NOT announce them as "skipped" during the flow.

   Calculate `M` = total questions remaining after removing pre-excluded questions. **Do NOT factor in answer-dependent early-exit skips** (e.g., Q5→Q8) — those are the only skips communicated to the user mid-flow.

   **Double-check:** List out the specific question numbers that will be asked. Verify the count matches M.

2. **Opening message**: Present a brief introduction before the first question:

   > Before mapping your infrastructure to AWS, I have **M questions** to tailor the migration plan. I'll ask them one at a time.
   >
   > You can answer each, or say **"use all defaults"** to accept defaults for all remaining questions.

3. **Ask one question at a time**: For each question in order:
   - Show the progress indicator: **"Question N of M"**
   - When entering a new section for the first time, show the section header
   - Present the question with its context and answer options
   - **Wait for the user's response before presenting the next question**
   - Apply the interpret rule immediately after receiving the answer
   - Check inline early-exit rules: if Q5 = "Yes, multi-cloud required", record `compute: "eks"`, remove Q8 from remaining questions, add Q8 to `questions_skipped_early_exit`, and reduce `M` by the number of questions skipped.

   **Communicating skipped questions:** When an answer causes later questions to be skipped, reduce `M` by the number of skipped questions and show a one-line note before the next question:
   > *(Skipping [count] question(s) based on your previous answer — [M] questions total now.)*

   Then continue the progress indicator using the updated `M`. For example, if the original M was 8 and 1 question is skipped after Question 4, M becomes 7. The next question shown is "Question 5 of 7", then "Question 6 of 7", then "Question 7 of 7".

   Keep it short and general. Never reference internal question IDs (Q8, Q14, etc.) or technical constraint details (compute: "eks") in user-facing messages. The user doesn't need to know which specific question was removed or why — just that the total changed.

4. **Handle user shortcuts at any point during the conversation**:
   - **"use all defaults"** or **"defaults for the rest"** → Before applying defaults, present a plain-language summary of what the defaults mean for the remaining unanswered questions so the customer knows exactly what they're getting. Use a bulleted list where each item is a self-contained sentence — no option codes, no table columns. Example:

     > Here's what I'll assume for the remaining questions:
     >
     > - **Uptime**: Your app needs high availability — we'll deploy across multiple availability zones (Multi-AZ)
     > - **Maintenance window**: Flexible — we can schedule a maintenance window when you're ready for cutover
     > - **Kubernetes**: Neutral stance — we'll evaluate both EKS and ECS and recommend the best fit
     > - **Database I/O**: Medium workload — Aurora standard pricing (we can switch to I/O-Optimized later if needed)
     > - *(... list all remaining unanswered questions ...)*
     >
     > These are conservative, middle-of-the-road choices. Does this work for you, or would you prefer to go through them one by one?

     - If the customer **accepts** → Apply all defaults, skip to Step 5
     - If the customer **rejects** or wants to go through them → Continue presenting questions one at a time as normal from where they left off

5. **Handle "I don't know" or "idk" answers**: When the user selects "I don't know" (or says "idk", "not sure", etc.) for any question, do NOT silently apply the default. Instead, explain the default and confirm:

     > The default for this question is **[default option label]** — [plain-language explanation of what this means for their migration].
     >
     > Is that acceptable, or would you like to reconsider?
     >
     > **Exception — Q3 (GCP spend):** Do not explain downstream implications (credits, pricing tiers, savings programs). Just state the default bucket and, if billing data exists, note it matches their billing data. Nothing more.

     - If the customer **accepts** → Apply the default, record `chosen_by: "default"`, move to the next question
     - If the customer **wants to reconsider** → Re-present the same question's options (excluding "I don't know") and let them choose

6. **Section transitions**: When moving between categories, briefly introduce the new section:
   > *Now let's talk about your infrastructure...*
   >
   > *(or)* *Now let's discuss your AI workloads...*

7. **Completion**: After the last question is answered, confirm:
   > That's all my questions. Let me generate your migration preferences.

   **If questions were skipped**, acknowledge it briefly so the user isn't surprised by the gap between the announced total and the number actually asked:
   > That's all my questions — the rest didn't apply to your setup. Let me generate your migration preferences.

### Question Order

Present in this order (skipping any that don't apply):

```
--- Section 1: About Your Users & Requirements ---
Q1 → Q2 → Q3 → Q4 → Q5 → Q6 → Q7

--- Section 2: Your Infrastructure ---
[Category B questions, if applicable]
Q8 → Q9 → Q10 → Q11 → Q12 → Q13

--- Section 3: AI Workloads ---
Q14 → Q15 → Q16 → Q17 → Q18 → Q19 → Q20 → Q21 → Q22
```

Wait for the user's response to EVERY question. Do NOT batch questions. Do NOT proceed to Design without completing all questions or receiving an explicit "use all defaults".

---

## Answer Combination Triggers

| Scenario                     | Key Answers                                  | Recommendation                                            |
| ---------------------------- | -------------------------------------------- | --------------------------------------------------------- |
| Early-stage credits          | Q4 = Pre-seed/Seed                           | AWS Activate Founders or Portfolio credits                |
| Growth-stage credits         | Q4 = Series B+ and Q3 spend                  | IW Migrate or MAP credits based on ARR                    |
| Must stay portable           | Q5 = Yes multi-cloud                         | EKS only, no ECS Fargate                                  |
| Kubernetes-averse            | Q5 = No + Q8 = Frustrated                    | ECS Fargate strongly recommended                          |
| WebSocket app                | Q9 = Yes                                     | ALB WebSocket config required                             |
| Low-traffic Cloud Run        | Q10 = Business hours + Q11 < $100            | Recommend staying on Cloud Run                            |
| High I/O database            | Q13 = High IOPS                              | Aurora I/O-Optimized                                      |
| Write-heavy global DB        | Q6 = Catastrophic + Q12 = Write-heavy/global | Aurora DSQL                                               |
| Rapidly growing DB           | Q12 = Rapidly growing                        | Aurora Serverless v2                                      |
| Zero downtime required       | Q7 = No downtime                             | Blue/green + AWS DMS required                             |
| HIPAA compliance             | Q2 = HIPAA                                   | BAA services only, specific regions                       |
| FedRAMP required             | Q2 = FedRAMP                                 | GovCloud regions only                                     |
| Gateway-only AI              | Q14 = B only (LLM router/gateway)            | Config change only; skip SDK migration                    |
| LangChain/LangGraph AI       | Q14 includes C                               | Provider swap via ChatBedrock; 1–3 days                   |
| OpenAI Agents SDK            | Q14 includes E                               | Highest AI effort; Bedrock Agents; 2–4 weeks              |
| Multi-agent + MCP            | Q14 = D + F                                  | Bedrock Agents to unify orchestration + MCP               |
| Voice platform AI            | Q14 includes G                               | Check native Bedrock support; Nova Sonic if needed        |
| GPT-4 Turbo migration        | Q19 = GPT-4 Turbo                            | Claude Sonnet 4.6 — 70% cheaper on input                  |
| o-series migration           | Q19 = o-series                               | Claude Sonnet 4.6 with extended thinking                  |
| High-volume cost-critical AI | Q18 = High + cost critical                   | Nova Micro or Haiku 4.5 + provisioned throughput          |
| Reasoning/agent workload     | Q17 = Extended thinking                      | Claude Sonnet 4.6 extended thinking; Opus 4.6 for hardest |
| Speech-to-speech AI          | Q17 = Real-time speech                       | Nova Sonic                                                |
| RAG workload                 | Q17 = RAG optimization                       | Bedrock Knowledge Bases + Titan Embeddings                |
| Vision workload              | Q20 = Vision required                        | Claude Sonnet 4.6 (multimodal)                            |
| Latency-critical AI          | Q21 = Critical                               | Haiku 4.5 or Nova Micro + streaming                       |
| Complex reasoning tasks      | Q22 = Complex                                | Claude Sonnet 4.6; Opus 4.6 for hardest                   |

---

## Step 5: Interpret and Write preferences.json

Apply the interpret rule for every answered question (defined in each category file). For skipped questions, apply the documented default.

**Before writing the file**, verify that every question Q1–Q22 appears in exactly one of: `questions_asked`, `questions_defaulted`, `questions_skipped_extracted`, `questions_skipped_early_exit`, or `questions_skipped_not_applicable`. If any question is missing, fix it before writing the file.

Write `$MIGRATION_DIR/preferences.json`:

```json
{
  "metadata": {
    "timestamp": "<ISO timestamp>",
    "discovery_artifacts": ["gcp-resource-inventory.json", "ai-workload-profile.json"],
    "questions_asked": [
      "Q1",
      "Q2",
      "Q3",
      "Q5",
      "Q6",
      "Q7",
      "Q14",
      "Q16",
      "Q17",
      "Q19",
      "Q21",
      "Q22"
    ],
    "questions_defaulted": ["Q9"],
    "questions_skipped_extracted": ["Q14"],
    "questions_skipped_early_exit": ["Q8"],
    "questions_skipped_not_applicable": ["Q4", "Q10", "Q11", "Q12", "Q13"],
    "category_e_enabled": false,
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
    "db_io_workload": { "value": "medium", "chosen_by": "user" }
  },
  "ai_constraints": {
    "ai_framework": { "value": ["direct"], "chosen_by": "extracted" },
    "ai_monthly_spend": { "value": "$500-$2K", "chosen_by": "user" },
    "ai_priority": { "value": "balanced", "chosen_by": "user" },
    "ai_critical_feature": { "value": "function-calling", "chosen_by": "user" },
    "ai_volume_cost": { "value": "low-quality", "chosen_by": "user" },
    "ai_model_baseline": { "value": "claude-sonnet-4-6", "chosen_by": "derived" },
    "ai_vision": { "value": "text-only", "chosen_by": "user" },
    "ai_latency": { "value": "important", "chosen_by": "user" },
    "ai_complexity": { "value": "moderate", "chosen_by": "user" },
    "ai_capabilities_required": {
      "value": ["text_generation", "streaming", "function_calling"],
      "chosen_by": "derived"
    }
  },
  "question_details": {
    "Q1": { "question": "Where are your users located?", "answer": "A) Single region", "interpreted_as": { "target_region": "us-east-1" } },
    "Q8": { "question": "How does your team feel about managing Kubernetes?", "answer": null, "skipped_reason": "early_exit", "note": "Q5=multi-cloud → EKS only" },
    "Q9": { "question": "Do any services need WebSocket support?", "answer": "I don't know", "interpreted_as": {}, "note": "Default: no constraint" }
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
8. `metadata.questions_skipped_not_applicable` records questions skipped because the relevant service wasn't in the inventory.
9. `ai_constraints` section is present ONLY if Category F fired. Omit entirely if no AI artifacts exist.
10. `ai_constraints.ai_capabilities_required` is the UNION of detected capabilities from `ai-workload-profile.json` + critical feature from Q17 + vision from Q20. `chosen_by` is `"derived"`.
11. `ai_constraints.ai_framework` is an array (Q14 is select-all-that-apply). If auto-detected, `chosen_by` is `"extracted"`.
12. `question_details` — audit log of Q&A. One entry per question in `questions_asked` + `questions_defaulted` + `questions_skipped_early_exit`. Fields: `question`, `answer` (verbatim or `null` if skipped), `interpreted_as`, optional `skipped_reason`/`note`. Omit `questions_skipped_not_applicable`. Informational only — downstream phases ignore it.

---

## Defaults Table

| Question                | Default              | Constraint                                        |
| ----------------------- | -------------------- | ------------------------------------------------- |
| Q1 — Location           | A (single region)    | `target_region`: closest AWS region to GCP region |
| Q2 — Compliance         | A (none)             | no constraint                                     |
| Q3 — GCP spend          | Billing-informed bucket if `billing-profile.json` exists, otherwise B ($1K–$5K) | `gcp_monthly_spend` mapped from billing data or `"$1K-$5K"` |
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
| Q14 — AI framework      | _(auto-detect)_      | `ai_framework` from code detection                |
| Q15 — AI spend          | B ($500–$2K)         | `ai_monthly_spend: "$500-$2K"`                    |
| Q16 — AI priority       | E (balanced)         | `ai_priority: "balanced"`                         |
| Q17 — Critical feature  | J (none)             | no additional override                            |
| Q18 — Volume + cost     | A (low + quality)    | `ai_volume_cost: "low-quality"`                   |
| Q19 — Current model     | _(auto-detect)_      | `ai_model_baseline` from code detection           |
| Q20 — Vision            | A (text only)        | no constraint                                     |
| Q21 — AI latency        | B (important)        | `ai_latency: "important"`                         |
| Q22 — Task complexity   | B (moderate)         | `ai_complexity: "moderate"`                       |

---

## Validation Checklist

Before handing off to Design:

- [ ] `preferences.json` written to `$MIGRATION_DIR/`
- [ ] `design_constraints.target_region` is populated with `value` and `chosen_by`
- [ ] `design_constraints.availability` is populated (if Q6 was asked or defaulted)
- [ ] Only keys with non-null values are present in `design_constraints`
- [ ] Every entry in `design_constraints` and `ai_constraints` has `value` and `chosen_by` fields
- [ ] Config gap answers recorded in `metadata.inventory_clarifications` (billing mode only)
- [ ] Early-exit skips recorded in `metadata.questions_skipped_early_exit`
- [ ] `ai_constraints` section present ONLY if Category F fired
- [ ] If Category F fired, `ai_constraints.ai_framework` is populated (from detection or Q14)
- [ ] If Category F fired, `ai_capabilities_required` is derived from detection + Q17 + Q20
- [ ] `ai_constraints.ai_framework` is an array (Q14 is multi-select)
- [ ] `question_details` includes an entry for every question in `questions_asked`, `questions_defaulted`, and `questions_skipped_early_exit`
- [ ] Output is valid JSON

---

## Step 6: Update Phase Status

Update `$MIGRATION_DIR/.phase-status.json`:

- Set `phases.clarify` to `"completed"`
- Update `last_updated` to current timestamp

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
