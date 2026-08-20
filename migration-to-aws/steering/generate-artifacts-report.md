# Generate Phase: HTML Migration Report

> Loaded by generate.md AFTER generate-artifacts-docs.md completes.

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Generate a single self-contained HTML report (`migration-report.html`) combining an executive summary with detailed appendix. The HTML file uses inline CSS — no external dependencies required. Users can open it in any browser and use "Print to PDF" if a PDF is needed.

**Output:**

- `migration-report.html` — Self-contained HTML report with executive summary and detailed appendix

**Non-blocking:** If report generation fails after `VALIDATE_OK` (HTML build error only), log a warning and continue. Validation `GATE_FAIL` is **not** a silent skip — always surface to the user. Do NOT fail the Generate phase for report issues.

## Step 0: Validate Artifacts (Read Only)

Load and execute `validate-artifacts.md` **before** building report content.

- Run all **required** checks (field presence only — do not rewrite artifact prose).
- On any `GATE_FAIL`: output failure lines to the user, **do NOT write** `migration-report.html`, **do NOT patch artifacts**, return to parent `generate.md`.
- On `VALIDATE_OK`: proceed to Step 1.

## Prerequisites

At least one of these must exist in `$MIGRATION_DIR/`:

- Design artifact: `aws-design.json`, `aws-design-ai.json`, or `aws-design-billing.json`
- Estimation artifact: `estimation-infra.json`, `estimation-ai.json`, or `estimation-billing.json`
- Generation plan: `generation-infra.json`, `generation-ai.json`, or `generation-billing.json`

If **none** exist: skip report generation. Output: "Skipping HTML report — no migration artifacts found."

## Data Sources

Gather data from all available artifacts. Each section below notes which artifact provides the data.

| Data Point                              | Primary Source                                                                                                                                          | Fallback                                             |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| GCP services detected                   | `aws-design.json` clusters[].resources[]                                                                                                                | `aws-design-billing.json` services[]                 |
| AWS service mappings                    | `aws-design.json` resources[].aws_service                                                                                                               | `aws-design-billing.json` services[].aws_service     |
| Rationale per service                   | `aws-design.json` resources[].rationale                                                                                                                 | `aws-design-billing.json` services[].rationale       |
| Current GCP monthly cost                | `estimation-infra.json` current_costs.gcp_monthly                                                                                                       | `estimation-billing.json`                            |
| Projected AWS monthly cost              | `estimation-infra.json` projected_costs.aws_monthly_balanced                                                                                            | `estimation-billing.json`                            |
| Cost breakdown per service              | `estimation-infra.json` projected_costs.breakdown                                                                                                       | `estimation-billing.json`                            |
| Cost tiers (premium/balanced/optimized) | `estimation-infra.json` cost_comparison                                                                                                                 | —                                                    |
| Optimization opportunities              | `estimation-infra.json` optimization_opportunities                                                                                                      | —                                                    |
| Migration timeline                      | `generation-infra.json` migration_plan.total_weeks                                                                                                      | `generation-billing.json`                            |
| Top risks                               | `generation-infra.json` risk_assessment                                                                                                                 | `generation-billing.json`                            |
| Human expertise flags                   | Design artifact resources[].human_expertise_required                                                                                                    | —                                                    |
| AI model mappings                       | `aws-design-ai.json`                                                                                                                                    | —                                                    |
| AI cost estimates                       | `estimation-ai.json`                                                                                                                                    | —                                                    |
| Migration decision / recommendation     | `estimation-infra.json` → `recommendation`                                                                                                              | `financial_summary.recommendation` (string fallback) |
| Complexity and timeline hint            | `migration-preview.json` → `complexity_signal`, `timeline_hint`                                                                                         | —                                                    |
| Key decisions ahead                     | `migration-preview.json` → `key_decisions_ahead`                                                                                                        | —                                                    |
| User configuration choices              | `preferences.json` (read `.value` from wrapped fields)                                                                                                  | —                                                    |
| AI capabilities and integration         | `ai-workload-profile.json` → `models[]`, `integration`, `agentic_profile`                                                                               | —                                                    |
| Deferred services                       | Design artifact `resources[].aws_service == "Deferred — specialist engagement"`                                                                         | —                                                    |
| Observability cost callout              | `estimation-infra.json` → `projected_costs.breakdown` (array: `service` contains "Observability"; object: key contains `observability` or `cloudwatch`) | —                                                    |
| **Combined TCO (infra + AI)**           | Sum `estimation-infra.json` Balanced + `estimation-ai.json` → `cost_comparison.projected_bedrock_monthly` (or `recommended_model.monthly_cost`)         | —                                                    |
| **Security baseline component costs**   | `estimation-infra.json` → `projected_costs.breakdown.security_baseline.components` (GuardDuty, cloudtrail_s3, etc.)                                     | Static ranges in Appendix G when JSON absent         |
| **Engineering effort**                  | `generation-infra.json` + `generation-ai.json` → `recommendation.estimated_total_effort_hours`                                                          | —                                                    |
| **Terraform validation status**         | `validation-report.json` → `status`, `provider_version`                                                                                                 | —                                                    |
| **Pricing confidence / staleness**      | `estimation-infra.json` → `pricing_source`, `accuracy_confidence`                                                                                       | `estimation-ai.json` accuracy fields                 |
| **AI optimization opportunities**       | `estimation-ai.json` → `optimization_opportunities`, `optimized_projection`                                                                             | —                                                    |
| **What-if workshop scenarios**          | `scenarios/index.json` + each `scenarios/scenario-NNN.json` manifest (`estimation_summary`, `preferences_subset`, optional `graviton_note`)             | — (omit section when workshop unused)                |

## Step 1: Build Executive Summary Section

The executive summary is the first thing visible when opening the report. Design it to fit approximately 1–2 printed pages.

### Executive Summary Content

**Header:** "GCP to AWS Migration Assessment" with subtitle "Executive Summary" and generation date.

**Table of contents (required):** Linked `<nav class="toc">` listing all executive sections and appendix sections present in this report. **Every `href="#section-id"` MUST match a `<section id="section-id">` on the page exactly** (same string, including hyphens). Omit TOC links only for sections not rendered.

**Target length:** approximately 2–4 printed pages for executive summary. **Do NOT truncate appendices** to fit page count — appendices may be long.

**Anti-stub rule (mandatory):** The appendix MUST render artifact data as HTML tables and prose. **Forbidden:** appendix sections that only say "see `estimation-infra.json`" or list JSON filenames without numeric costs, service mappings, or migration phases. Reference fixture: `awslabs/startups:migrate/plugins/migration-to-aws/fixtures/migration-report-reference.html`.

**Section 0 — Migration Decision Summary (REQUIRED):**

Pull from `estimation-infra.json` → `recommendation` block. Fallback chain if `recommendation` is absent:

1. `estimation-infra.json` → `financial_summary.recommendation` (string) — use as `path_label`; synthesize `migrate_if` / `stay_if` from Part 7 prose defaults in `estimate-infra.md`
2. `migration-preview.json` — show complexity + timeline only; label: "Full recommendation requires Estimate phase — run Phase 4"

Content when `recommendation` block exists:

1. **Verdict (typography-first — the verdict is the thesis of this section):** When `recommendation.outcome` exists (v2 artifacts), render `outcome_label` as the section's **headline statement** in large display type (e.g. `<p class="verdict-headline">Go, with conditions</p>`), followed by one labeled metadata line in body type: "Execution shape: [path_label] · Complexity: [complexity_signal]". The hierarchy encodes the real relationship — the decision is the headline; how and how-hard are attributes of it. Do **not** render the verdict as a row of colored pill badges: structure should carry the information, and meaning must never depend on color alone (a muted color accent on the headline is fine; the words carry the verdict). When `outcome` is absent (pre-extension artifacts), the same treatment applies with `path_label` as the headline. When `conditional_go`: render `conditions[]` as a short checklist directly under the metadata line. When `defer_for_evidence`: lead with what IS established ("AWS can host this stack; AWS-side estimate $X–$Y/mo" + the designed-slice mapping), then the named missing evidence and how to obtain it — do not show a savings headline as if the decision were made, and do not present defer as "no answer."
   1b. **Confidence pointer:** one line under the verdict block — `Confidence: [confidence] — full basis in <a href="#exec-assumptions">What This Assessment Rests On</a>.` The full assumptions panel lives at the **end** of the executive summary (see Section 8 below), not here.
2. **Complexity:** from `migration-preview.json` → `complexity_signal` ("Simple", "Moderate", "Complex") — colored badge
3. **Cost headline:** from `estimation-infra.json` → `cost_comparison.option_b_balanced` vs GCP baseline, OR legacy `comparison.aws_balanced_monthly_usd` vs `comparison.gcp_monthly_usd`. Do NOT use `migration-preview.json` → `cost_preview` when estimation artifact exists (preview is superseded). If only preview exists: show labeled "Early estimate (±30%) — full analysis not yet run."
4. **Timeline:** from `generation-infra.json` → `migration_plan.total_weeks` (preferred), OR `migration-preview.json` → `timeline_hint`. Do NOT use `recommendation.next_steps` as timeline — those are action items, not duration.
5. **Migrate if / Stay if:** from `recommendation.migrate_if` and `recommendation.stay_if`. Render as two compact lists. For BigQuery/deferred analytics: **do not** frame specialist engagement as a reason to stay on GCP unless the user must cut over analytics in the **same window** as app infra. Prefer migrate-if bullets that mention parallel specialist planning.
6. **Key decisions ahead:** from `migration-preview.json` → `key_decisions_ahead` — **ordered list** (`<ol class="compact">`), not bullets. Each item is one concrete decision the reader must make next.
   6b. **What would flip this (v2 artifacts):** from `recommendation.would_flip_if[]` when present — short unordered list immediately after Migrate if / Stay if. Skip silently when absent.
7. **Next steps (optional):** from `recommendation.next_steps` — **ordered list** (`<ol class="compact">`) of actionable steps separate from timeline. Numbered sequence implies priority order; keep `Migrate if` / `Stay if` as unordered lists.

**Deferred services flag:** If ANY resource in the design artifact has `aws_service == "Deferred — specialist engagement"`, add a prominent callout:

> ⚠️ **Specialist engagement required:** [service name] does not have an automated AWS mapping from this plugin. Engage your AWS account team and/or a data analytics migration partner to evaluate the best AWS analytics path. This does **not** block phased migration of other services; exclude [service name] from combined TCO until the target architecture is defined.

**Startup credits callout (decision summary / verdict):**

| `startup_program_status.value` | Verdict / metric copy                                                                                                                                                                                                                                |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `eligible_founders`            | May state "Eligible for up to $5K AWS Activate Founders credits" and link `STARTUP_PROGRAMS.md`                                                                                                                                                      |
| `eligible_portfolio`           | May state Portfolio credits (up to $200K) and Org ID requirement                                                                                                                                                                                     |
| `has_credits`                  | Note existing credits; no "apply for" language                                                                                                                                                                                                       |
| `unknown`                      | **Neutral only:** e.g. "Review AWS Activate tiers in `STARTUP_PROGRAMS.md` — funding stage not confirmed in Clarify." **Do not** write "Eligible Founders tier", "your status: eligible_*", or dollar amounts tied to a specific tier in the verdict |

**Sidebar callout box:** Show the 💡 Activate callout when `startup_program_status.value` is **not** `unknown`, **or** when `unknown` but you use the neutral wording above (optional). When `unknown`, do **not** imply a confirmed tier.

Do **not** infer Activate tier from `gcp_monthly_spend` or `ai_monthly_spend` in the report or `estimation-*.json` ROI bullets.

**Apply link (required):** Whenever the report or `STARTUP_PROGRAMS.md` mentions AWS Activate credits, include at least one clickable link to the official apply page: `<a href="https://aws.amazon.com/startups/credits/">AWS Activate credits</a>` (HTML report) or `[AWS Activate credits](https://aws.amazon.com/startups/credits/)` (Markdown). Place it in the decision-summary verdict, a callout, and/or the Next steps ordered list — not only in the appendix artifact catalog.

After Generate, run `validate-startup-program-artifacts.py --migration-dir $MIGRATION_DIR`.

Source: estimation artifact `recommendation`, `migration-preview.json`, design artifact

- Source: estimation artifact

**Section 1b — Total Cost of Ownership (`exec-tco`, REQUIRED when both `estimation-infra.json` AND `estimation-ai.json` exist):**

Combined monthly and annual view **excluding** deferred services (e.g. BigQuery):

| Row            | GCP                                                      | AWS Balanced                                | Notes                       |
| -------------- | -------------------------------------------------------- | ------------------------------------------- | --------------------------- |
| Infrastructure | `current_costs.gcp_monthly`                              | `projected_costs.aws_monthly_balanced`      | From infra estimate         |
| AI / ML        | `current_costs.gcp_monthly_ai_spend` or AI band midpoint | `cost_comparison.projected_bedrock_monthly` | From AI estimate            |
| **Total**      | sum                                                      | sum                                         | Show monthly Δ and % change |

If `estimation-ai.json` → `optimized_projection` exists, footnote the optimized AI path separately.

Source: `estimation-infra.json`, `estimation-ai.json`

**Section 1 — Current Stack Overview:**

- Count of PRIMARY GCP services detected (from design artifact — filter to primary classification only; exclude secondary/supporting resources like default VPC firewalls)
- List each PRIMARY GCP service with its type (e.g., "Cloud Run (compute)", "Cloud SQL (database)")
- Source: design artifact (filtered)

**Section 2 — Recommended AWS Architecture:**

- Table with columns: GCP Service, AWS Service, **How we chose this**
- **How we chose this** values: use `design-ref-fast-path.md` → **User-facing vocabulary** — **Standard pairing** (`deterministic`), **Tailored to your setup** (`inferred`), **Estimated from billing only** (`billing_inferred`). Show the **bold phrase** in the table; JSON value optional in a tooltip or footnote for technical readers only.
- One row per mapped service
- If any service has `human_expertise_required: true`, mark it with a warning indicator and footnote: "Specialist guidance recommended — contact your AWS account team"
- Source: design artifact

**Section 2b — Architecture diagram (`exec-architecture`, REQUIRED when `aws-design.json` clusters exist):**

ASCII or structured diagram showing: users → ALB → compute → database/storage/AI; security baseline box; deferred services called out.

Include **migration cluster order** from `generation-infra.json` → `migration_plan.cluster_order`.

Source: `aws-design.json`, `generation-infra.json`

**Section 3 — Cost Comparison:**

- Side-by-side display: Current GCP Monthly vs Estimated AWS Monthly (**Balanced** tier — the default scenario for comparing to GCP)
- **Baseline-quality badge (required):** label the GCP figure using `current_costs.source` and the display-label table in `estimate-infra.md` Part 1 — "Measured from your GCP billing (±5%)" / "Estimated from resource configs (±20–30%, standing charges only)" / "Your stated spend band from Clarify" / "Your stated figure (unverified)". **Never** place an inventory-only GCP figure beside a user spend band without the explicit not-comparable line from `estimate-infra.md` Part 1 — they measure different things.
- Percent change (savings or increase)
- **Cost labeling rule:** All dollar figures in cost tables and metrics MUST be labeled as estimated monthly costs. Use column headers like "Est. Monthly AWS" or "Estimated Monthly" — never present figures as exact amounts.
- **How to read cost tiers (callout box — required when infra estimation with three tiers exists):** The three AWS monthly figures are **estimated monthly costs** for the **same** mapped architecture (same services in `aws-design.json`), not three different generated Terraform stacks. **Order = highest → middle → lowest** monthly estimate in this model. Use **Balanced** as the **primary** row vs GCP; **Premium** and **Optimized** are **bounds** (higher HA / newer skew vs cost-optimization skew). When `terraform/` is present, it implements **one** infrastructure baseline aligned with the **Balanced** cost scenario (see `terraform/README.md` and `migration_summary` output).
- If 3 tiers available: show **Premium**, **Balanced**, and **Optimized** with **short subtitles** (second line or subtext under each label):
  - **Premium** — _Highest resilience / highest monthly estimate in this model_
  - **Balanced** — _Default scenario; compare GCP to this row first_
  - **Optimized** — _Lower monthly estimate; reservations, Spot, or storage trade-offs assumed_
- **Footnote (required):** _All figures are estimated monthly costs based on AWS pricing data at time of analysis. Only one Terraform configuration is generated (Balanced-aligned baseline). Premium and Optimized are what-if cost models in `estimation-infra.json` — adjust IaC yourself if you want those postures in production._
- **Only include "GCP data transfer egress (est.)" when the infra estimation artifact has `migration_cost_considerations.billing_data_available === true`.** Never present human one-time migration costs. If `false` or only non-infra estimates exist, footnote: "GCP data transfer egress estimates require billing data and the infra estimate path."
- If observability entry exists in `projected_costs.breakdown` (tolerant lookup: array where `service` contains "Observability" OR object where key contains `observability` or `cloudwatch`) AND the entry's `note` field mentions GCP free tiers:

> **Observability cost note:** [Pull the `note` field verbatim]

- Source: estimation artifact

**Section 3b — What-if scenarios (`what-if-scenarios`, OPTIONAL):**

Render **only when** `$MIGRATION_DIR/scenarios/index.json` exists and
`scenarios[]` has **≥ 2** entries (baseline + at least one workshop variant).
Omit entirely when workshop was declined or never entered.

1. Load `scenarios/index.json`. For each entry (baseline first, then by
   `created_at`), read the manifest at `entry.manifest`.
2. HTML table matching `workshop-compare.md` columns:

| Scenario | Region | HA | Compute | Arch | Premium $/mo | Balanced $/mo | Optimized $/mo | Complexity |
| -------- | ------ | -- | ------- | ---- | ------------ | ------------- | -------------- | ---------- |

Resolve knobs from each scenario's preferences copy (or
`preferences_subset` / `estimation_summary` on the manifest): Region ←
`design_constraints.target_region.value`; HA ←
`design_constraints.availability.value`; Compute ←
`design_constraints.kubernetes.value` when present; Arch ←
`design_constraints.cpu_architecture.value`. Costs and complexity ←
`estimation_summary`.
3. Mark the active row (`scenario_id == index.active_scenario_id`) with
`class="active-scenario"` or an "(active)" label.
4. Under the table: active vs baseline knob deltas (plain language); any
`graviton_note` / `region_note`; for each scenario with a non-null
`estimation_summary.calculator_url`, an "open in AWS Pricing Calculator" link
(stakeholders can open and edit; AWS computes regional prices server-side);
remind that discovery inventory is frozen
and generated Terraform matches the **active** scenario only.
5. TOC: link `#what-if-scenarios` only when rendered. Place this section in the
executive flow immediately after `exec-costs` (before security teaser /
timeline).

**Section 4 — Security & Cost Guardrails (teaser — full table in Appendix G):**

Show top controls as a compact teaser:

| Control                        | What it does for you                                               | Monthly cost                         |
| ------------------------------ | ------------------------------------------------------------------ | ------------------------------------ |
| GuardDuty                      | Detects compromised credentials and crypto mining within minutes   | ~$2–25/mo                            |
| CloudTrail                     | Immutable audit log of every API call — required for SOC 2         | ~$0.50–3/mo                          |
| Budget alerts                  | Email when spend exceeds threshold — catches runaway resources     | $0                                   |
| Bedrock cost anomaly detection | Alerts within ~24h if AI spend spikes unexpectedly (AI track only) | $0 (Cost Explorer anomaly detection) |

The fourth row is **conditional** — only render when `$MIGRATION_DIR/ai-migration/bedrock_monitoring.tf` exists on disk. Do NOT render based on `generation-ai.json` alone.

> See Appendix G for full security and cost guardrails table with GCP equivalents.

If `preferences.json` contains compliance values (`soc2`, `pci`, `hipaa`, `fedramp`):

> **Compliance note:** Your declared compliance requirement ([standard]) triggers additional controls (AWS Config + Security Hub) at ~$3–25/mo. See Appendix G.

**Do NOT include step-by-step enablement** — that belongs in `terraform/README.md` and `MIGRATION_GUIDE.md`.

Source: static content + `preferences.json` compliance values

**Section 5 — Operational Changes (conditional rows only):**

Only render rows for service types PRESENT in the design artifact. Do not show rows for services not in the migration.

| GCP Service        | AWS Service | What stays the same                                 | What's new                                                                           |
| ------------------ | ----------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Cloud Run          | Fargate     | Fully managed containers, auto-scaling, pay-per-use | Task definitions replace service.yaml; ALB for HTTP routing; ECR replaces GCR        |
| Cloud SQL          | RDS/Aurora  | Managed DB, automated backups, PITR                 | Parameter groups replace database flags; Security Groups replace authorized networks |
| Cloud Storage      | S3          | Object storage, lifecycle policies, versioning      | Bucket policies replace IAM conditions; CloudFront needed for public CDN             |
| Vertex AI / Gemini | Bedrock     | Managed API, pay-per-token                          | IAM-based access (no API keys); SDKs differ                                          |

**Conditional rendering:** Check design artifact for each `gcp_type` / `aws_service` pair. Only include rows where the GCP source type exists in the design. If a service category has no match, skip that row entirely.

Source: static template filtered by design artifact service types

**Section 6 — Timeline:**

- Total migration weeks (infra + note parallel AI weeks if applicable)
- Migration approach (phased/fast-track/conservative)
- **Engineering effort:** sum `generation-infra.json` and `generation-ai.json` → `recommendation.estimated_total_effort_hours` when both exist
- Source: generation plan

**Section 7 — Top Risks:**

- Up to 3 highest-severity risks
- Each with: risk name, severity, one-line mitigation
- Source: generation plan risk_assessment

**Section 8 — What this assessment rests on (`exec-assumptions`, REQUIRED):**

> Rendered heading is a plain title — e.g. `<h2>What This Assessment Rests On</h2>` with `<section id="exec-assumptions">`. Never render a literal "Section 8" heading (validator readability rule).

Placed at the **end of the executive summary** — after Top Risks, immediately before the appendices — where assumption and validation sections conventionally sit in a migration report. The decision summary links here via the confidence pointer (item 1b). Three parts, all read from existing artifacts — invent nothing:

1. **Assumptions applied by default** — table of every constraint in `preferences.json` with `chosen_by: "default"`: Setting (plain name), Assumed value, and the constraint's `design_consequence` verbatim. When no constraint was defaulted, render one line: "All inputs were confirmed by you or extracted from your Terraform/billing — nothing was assumed."
2. **Confidence** — one line from `recommendation.confidence` with a plain-language gloss: high — "inputs measured or confirmed"; medium — "some material inputs assumed"; low — "key inputs missing or stale". When v2 `decision_basis` exists, render its three lists (measured / assumed / unknown) as compact columns instead of the single line.
3. **Pricing provenance** — from the estimation artifact: `pricing_source` + cache date + `accuracy_confidence` band, matching the wording the Estimate chat summary already uses (e.g. "Estimates based on cached AWS pricing (2026-03-07), accuracy ±5–10%").

TOC: link `#exec-assumptions` in the executive list. The anti-stub rule applies: this section must render actual settings and consequences, never "see preferences.json".

Source: `preferences.json`, `estimation-infra.json` (falls back to `estimation-ai.json` accuracy fields for AI-only runs)

## Step 2: Build Detailed Appendix

The appendix follows the executive summary, clearly separated with an "Appendix: Detailed Migration Analysis" header.

### Appendix Section A — Service Recommendations

For each mapped service, include:

- GCP service name and type
- AWS service recommendation
- **How the mapping was chosen** — use **Standard pairing**, **Tailored to your setup**, or **Estimated from billing only** (`design-ref-fast-path.md` → User-facing vocabulary); JSON `confidence` may appear in parentheses for support
- Full rationale text from design artifact
- If the mapping was **Tailored to your setup** (`inferred`) and `rubric_applied` is present: list the 6 criteria evaluations (appendix detail — optional in executive summary)
- If `human_expertise_required: true`: include the specialist guidance callout

Source: design artifact (aws-design.json or aws-design-billing.json)

### Appendix Section B — Cost Estimates

**Per-service cost breakdown table** with columns: Service Category, AWS Service, Monthly Cost (Balanced), Calculation/Notes.

**Mandatory rows when present in `projected_costs.breakdown`:**

- compute, database, storage, networking
- **security_baseline** — include `mid` cost AND component sub-rows from `components` (e.g. GuardDuty, cloudtrail_s3, budgets)
- **observability** — include `mid` and `note` (GCP free-tier comparison)
- supporting (Secrets Manager, ECR, etc.)

Do NOT collapse security_baseline into "other". Surface GuardDuty explicitly.

**GCP baseline breakdown** (when `current_costs.breakdown` exists): table of compute/database/storage/networking/other vs infra total.

Source: estimation artifact projected_costs.breakdown, current_costs.breakdown

**Three-tier comparison table** with columns: **Tier** (name + subtitle as in Section 3), Monthly Cost, vs GCP Monthly, Annual Difference.

Repeat the **How to read cost tiers** callout from Section 3 here or include a one-line pointer: _See executive summary — three tiers are scenario $ only; generated Terraform matches **Balanced** baseline._

Source: estimation artifact cost_comparison

**Optimization opportunities table** with columns: Optimization, Target Services, Monthly Savings, Commitment, Effort.

Merge infra (`estimation-infra.json`) and AI (`estimation-ai.json`) optimization rows when both exist.

Source: estimation artifact optimization_opportunities

> **Security baseline costs** are included as a line item in the breakdown above. For Terraform resource names and GCP equivalents, see Appendix G.

### Appendix Section C — Migration Steps

Numbered migration phases from the generation plan, each with:

- Phase name and description
- Services included
- Estimated duration
- Dependencies and prerequisites

Source: generation plan

**Rollback procedure** — triggers, steps, and RTO from generation plan.

### Appendix Section D — AI Migration (conditional)

**Only include if `aws-design-ai.json` or `estimation-ai.json` exists.**

**D.1 — AI Stack Detected:**

Pull from `ai-workload-profile.json` when present:

| Aspect              | Detected                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| AI source           | `summary.ai_source`                                                                                        |
| Models              | `models[].model_id` — comma-separated list                                                                 |
| Capabilities in use | `integration.capabilities_summary` — keys where value is `true`                                            |
| Integration pattern | `integration.pattern`                                                                                      |
| Gateway/router      | `integration.gateway_type` or "None (direct SDK)"                                                          |
| Frameworks          | `integration.frameworks` or "None"                                                                         |
| Agentic             | If `agentic_profile` exists: "Yes — [framework], [orchestration_pattern], [agent_count] agents"; else "No" |

**D.2 — Why Bedrock (conditional):**

Show this section when `aws-design-ai.json` → `ai_architecture.honest_assessment` contains ANY of: `"recommend_stay"`, `"weak_migrate"`, or `"moderate_migrate"` where any model's Bedrock price exceeds the source provider price.

> **Why migrate to Bedrock when [source] may be cheaper per token?**
>
> - **Single-vendor billing:** One AWS bill instead of separate provider invoices
> - **VPC-private inference:** Model calls stay in your VPC — no data over public internet
> - **IAM access control:** No API keys to rotate; permissions follow your AWS IAM model
> - **Model evaluation:** A/B test models with Bedrock's built-in evaluation framework
> - **Guardrails:** Content filtering and PII detection at the platform level
> - **Commitment pricing:** Provisioned Throughput for predictable costs at scale
>
> These benefits matter most when: you handle sensitive data, need AI call audit trails, or want to consolidate vendors.

**D.3 — Model Mappings:**

- Model mappings (GCP model to AWS Bedrock model)
- AI cost estimates

**D.4 — Migration approach:**

- Migration approach (adapter pattern, A/B testing)

**D.5 — Post-migration AI cost optimization (conditional):**

**Only include if `generation-ai.json` exists in `$MIGRATION_DIR/` (AI track ran).**

After migration is validated and stable, three optimization levers are available (typical ranges from plugin guidance — validate against your traffic):

| Optimization               | Estimated savings        | When to apply                                    | Prerequisite                                                             |
| -------------------------- | ------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------ |
| Intelligent Prompt Routing | 10–30%                   | After 2+ weeks of production traffic             | Same model family in multiple tiers (e.g., Claude Sonnet + Haiku)        |
| Prompt caching             | 20–50% on eligible calls | When prompts have long repeated context          | Minimum ~1K–4K tokens cacheable prefix; per-model minimums and TTL apply |
| Model distillation         | Up to ~75%               | After 30+ days of stable, high-volume production | Stable prompts, evaluation dataset, sufficient call volume               |

These are not migration steps — they are post-migration optimizations. Do not block migration on these. Surface as a "Month 2–3" roadmap item.

**Prompt caching caveat:** Caching only helps for long, repeated context windows. Evaluate actual prompt patterns before assuming savings.

**Full detail:** Open `ai-workload-profile.json` in this directory.

Source: `ai-workload-profile.json`, `aws-design-ai.json`, `estimation-ai.json`

### Appendix Section E — Generated Artifacts Catalog

List all files and directories generated during the Generate phase:

- `terraform/` — list .tf files and **`README.md`**
- `scripts/` — list migration scripts
- `ai-migration/` — list adapter files (if applicable)
- `MIGRATION_GUIDE.md`, `README.md`

Check for actual file/directory existence before listing.

**Data artifacts (for detailed review):**

| Artifact                      | Contents                                                   |
| ----------------------------- | ---------------------------------------------------------- |
| `preferences.json`            | All migration configuration choices and their sources      |
| `ai-workload-profile.json`    | Full AI model inventory, capabilities, evidence            |
| `gcp-resource-inventory.json` | Complete GCP resource inventory with classifications       |
| `estimation-infra.json`       | Detailed cost model, recommendation, per-service breakdown |
| `aws-design.json`             | Full architecture design with rationale per service        |

Open any JSON file with a text editor or `cat <filename> | python3 -m json.tool` for formatted output.

**AI migration artifacts (conditional — only list if they exist on disk):**

| Artifact                                                    | Description                                                                       |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `ai-migration/bedrock_monitoring.tf`                        | Bedrock budget alerts, anomaly detection, inference profiles for cost attribution |
| `ai-migration/STARTUP_PROGRAMS.md` or `STARTUP_PROGRAMS.md` | AWS Activate credit tiers, application URLs, eligibility guidance                 |
| `ai-migration/setup_bedrock.sh`                             | Bedrock model access setup script                                                 |
| `ai-migration/test_comparison.py`                           | A/B comparison harness for source vs Bedrock quality                              |

Do not list files that were not generated.

### Appendix Section F — Your Configuration (`appendix-config`, conditional)

**Only include if `preferences.json` exists in `$MIGRATION_DIR/`.**

Key decisions that shaped this migration plan. Read every object in `design_constraints`, `ai_constraints`, and `startup_constraints` (when present). Schema: `schema-preferences.md`.

Render an HTML table with **five columns**, one row per constraint object (iterate every key in `design_constraints`, `ai_constraints`, and `startup_constraints` when present — do not hardcode a subset):

| Column                    | Source                                                                                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Question / assumption** | `prompt` on each constraint object                                                                                                              |
| **Your choice**           | formatted `value` (human-readable; expand arrays)                                                                                               |
| **Source**                | `chosen_by` → "User answer", "Extracted from infrastructure", "Default applied", or "Derived"                                                   |
| **Source signal**         | the `source` field when present (shows provenance like `terraform:availability_type=ZONAL` or `default:Q16`); leave blank for user/derived rows |
| **Design consequence**    | `design_consequence` on each constraint object                                                                                                  |

**Assumption flag:** Rows where `source` starts with `"default:"` are unverified assumptions — render in a visually distinct style (e.g., lighter text or italic) so the reader can spot which values were not explicitly verified from infrastructure.

**Critical-default caveats (required when present):** If any of the following constraints have `chosen_by: "default"` AND the corresponding question ID appears in `metadata.questions_defaulted`:

- `compliance` (Q2): render a warning callout: _"⚠️ Compliance was not explicitly confirmed. The security baseline assumes no regulatory requirements. If SOC 2, PCI, HIPAA, or FedRAMP applies, re-run Clarify or manually add controls."_ **Also fire this callout whenever `compliance.value` contains `"unknown"`** (regardless of `chosen_by` — covers both "I don't know" answers and defaulted runs). `"unknown"` never triggers the Section 4 compliance-controls note or any compliance-specific architecture.
- `gcp_monthly_spend` (Q3): render a warning callout: _"⚠️ GCP spend was not confirmed by the user. Cost comparison uses the default band ($1K–$5K). Actual spend may differ — verify against your GCP billing console."_
- `availability` (Q6): render a warning callout: _"⚠️ Database availability was assumed (Multi-AZ) — the user never confirmed it. This assumption roughly doubles the database line vs single-AZ. Confirm the availability requirement (or compare a single-AZ scenario in the what-if workshop) before treating the database estimate as final."_

Place these callouts at the top of Appendix F, before the table, so they're immediately visible.

**Sort order:** user-answered rows first, then extracted, then default, then derived.

**Legacy fallback:** If a constraint object lacks `prompt` or `design_consequence` (pre-extension runs), use the catalog in `schema-preferences.md` keyed by constraint name — never omit the appendix or leave cells empty.

**Do not** reduce this section to a key/value dump without question text and consequences.

Source: `preferences.json`

### Appendix Section G — Security Capabilities

Full security baseline capabilities. Executive summary shows a teaser; this appendix provides the complete picture.

| Control                | What it does for you                                                                | Threat mitigated                      | GCP equivalent                             | Monthly cost |
| ---------------------- | ----------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------ | ------------ |
| GuardDuty              | Detects compromised credentials, crypto mining, unusual API patterns within minutes | Credential theft, resource hijacking  | Security Command Center (paid Premium)     | ~$2–25/mo    |
| CloudTrail             | Immutable audit log of every API call — who did what, when                          | Unauthorized changes, compliance gaps | Cloud Audit Logs (free for admin activity) | ~$0.50–3/mo  |
| IMDSv2 enforcement     | Blocks SSRF attacks from stealing instance/container credentials                    | Server-side request forgery           | N/A (GCP uses different metadata model)    | $0           |
| Access Analyzer        | Alerts when IAM policies or S3 buckets become publicly accessible                   | Accidental public exposure            | IAM Recommender (partial)                  | $0           |
| EBS default encryption | All storage volumes encrypted at rest by default                                    | Data exposure from stolen disks       | Default encryption (GCP default)           | $0           |
| Budget alerts          | Email when spend exceeds threshold                                                  | Bill shock from runaway resources     | GCP Budgets (free)                         | $0           |
| S3 Block Public Access | Account-wide prevention of any bucket being made public                             | Accidental data leaks                 | Uniform bucket-level access (opt-in)       | $0           |
| IAM password policy    | 14-char min, rotation, complexity for console users                                 | Weak password compromise              | Cloud Identity policies                    | $0           |

**Compliance-conditional (only when SOC 2/PCI/HIPAA/FedRAMP declared in preferences):**

| Control             | What it adds                                           | Compliance gap covered             | Monthly cost |
| ------------------- | ------------------------------------------------------ | ---------------------------------- | ------------ |
| AWS Config          | Continuous recording of resource configuration changes | Change audit trail for SOC 2 / PCI | ~$2–10/mo    |
| Security Hub + FSBP | Automated security checks against AWS best practices   | Baseline posture scoring           | ~$1–15/mo    |

**Cost guardrails (when `$MIGRATION_DIR/ai-migration/bedrock_monitoring.tf` exists):**

| Control                         | What it does for you                                                    | Threat mitigated                                   | GCP equivalent                                 | Monthly cost |
| ------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------- | ------------ |
| Bedrock budget (1.5× projected) | Hard spend alert at 150% of estimated AI costs — fires before month-end | Runaway token spend from buggy retry loops         | GCP Budgets (free, but no per-service scoping) | $0           |
| Cost anomaly detection          | Daily digest when AI spend deviates from baseline (~24h data lag)       | Gradual cost creep, unexpected model-price changes | None (no GCP per-service anomaly equivalent)   | $0           |
| Inference profiles (tagged)     | Per-model cost attribution in Cost Explorer                             | Invisible cost distribution across models          | None                                           | $0           |

These are detective controls, not spend caps. You will know within ~24 hours if something goes wrong — not at invoice time.

**What the baseline does NOT cover (you still need):**

- SOC 2: Qualified auditor, formal policies, employee training, vendor management
- HIPAA: BAA with AWS, qualified HIPAA auditor, data handling policies
- PCI: QSA assessment, network segmentation validation, pen testing
- FedRAMP: Agency-level NIST 800-53 controls, ATO process

**For detailed cost breakdown:** See Appendix B (cost estimates include security baseline as a line item).

**To enable:** Run `terraform apply` on `baseline.tf`. To skip: delete `baseline.tf` before applying. See `terraform/README.md` for details.

Source: static content + `preferences.json` compliance values

### Appendix Section H — Security Gap Analysis (`appendix-security-gap`, REQUIRED when infra track ran)

Table: Capability | GCP (detected) | AWS (generated) | Gap / action

Minimum rows:

- Network perimeter (firewall rules → security groups)
- Identity & access (service accounts → IAM roles)
- Audit logging (Cloud Audit Logs → CloudTrail)
- Threat detection (SCC optional → GuardDuty in baseline.tf)
- Public data exposure (if public GCS/S3 detected in design)
- Observability cost shift (GCP larger free tier vs CloudWatch always-free tier; pull gap text from `estimation-infra.json` observability `note` — do **not** say CloudWatch has no free tier)

Source: `aws-design.json`, `terraform/baseline.tf`, `estimation-infra.json` observability note. Gap/action column should compare tier sizes (e.g. 50 GB GCP logging vs 5 GB CloudWatch always-free) and note the estimate assumes usage above free-tier limits — never "no free logging tier on AWS."

### Appendix Section I — Assumptions & Validation (`appendix-assumptions`, REQUIRED)

**Pricing confidence table:** domain, source, accuracy band, last updated (from `pricing_source` / `accuracy_confidence`).

**Exclusions list:**

- Deferred services (`deferred_services[]`, `excluded_from_totals`)
- GCP egress when `migration_cost_considerations.billing_data_available === false`
- Professional services / dual-run period (not modeled)

**Terraform validation:** from `validation-report.json` when present (`status`, provider version).

Source: estimation artifacts, `validation-report.json`, design warnings

## Step 3: Generate HTML

### Pre-Write Sanity Check (mandatory)

Immediately before writing the file, **re-read from disk**:

1. `estimation-infra.json` → `recommendation.path_label` present OR Step 1 fallback documented.
2. `migration-preview.json` → `complexity_signal` present (if file exists).
3. Assembled HTML string contains `<section id="decision-summary">`.

If any check fails: emit `GATE_FAIL | phase=generate | field=<path> | reason=missing`, do **not** write the file, return to parent.

Write the complete HTML to `$MIGRATION_DIR/migration-report.html`.

### HTML Structure (required section IDs)

The output MUST include these `id` attributes (content from Steps 1–2; gates check **presence only**):

| Section ID           | Content                                |
| -------------------- | -------------------------------------- |
| `decision-summary`   | Section 0 — Migration Decision Summary |
| `exec-services`      | Primary services summary               |
| `exec-costs`         | Cost comparison headline / tier table  |
| `exec-timeline`      | Timeline + effort                      |
| `exec-risks`         | Top risks                              |
| `appendix-services`  | Appendix A                             |
| `appendix-costs`     | Appendix B                             |
| `appendix-steps`     | Appendix C                             |
| `appendix-artifacts` | Appendix E                             |

Optional IDs (include when data exists): `exec-tco`, `exec-architecture`, `exec-security-teaser`, `what-if-scenarios`, `appendix-ai`, `appendix-config`, `appendix-security`, `appendix-security-gap`, `appendix-assumptions`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GCP to AWS Migration Assessment</title>
  <style>
    /* All CSS inline — see CSS specification below */
  </style>
</head>
<body>
  <div class="report">
    <div class="executive-summary">
      <section id="decision-summary"><!-- Section 0 --></section>
      <section id="exec-services"><!-- Primary services --></section>
      <section id="exec-costs"><!-- Cost headline --></section>
      <!-- <section id="what-if-scenarios"> when scenarios/index.json has ≥2 entries -->
      <section id="exec-timeline"><!-- Timeline --></section>
      <section id="exec-risks"><!-- Top risks --></section>
    </div>
    <div class="appendix">
      <section id="appendix-services"><!-- Appendix A --></section>
      <section id="appendix-costs"><!-- Appendix B --></section>
      <section id="appendix-steps"><!-- Appendix C --></section>
      <!-- <section id="appendix-ai"> when AI artifacts exist -->
      <section id="appendix-artifacts"><!-- Appendix E --></section>
      <!-- <section id="appendix-config"> when preferences.json exists -->
      <!-- <section id="appendix-security"> Appendix G -->
    </div>
    <footer>
      Generated by GCP to AWS Migration Advisor — draft for review; verify figures against source JSON artifacts before executive sign-off.
    </footer>
  </div>
</body>
</html>
```

### CSS Specification

The inline CSS must include:

**Layout:**

- `body`: font-family system-ui, -apple-system, sans-serif; max-width 900px; margin 0 auto; padding 40px 20px; color #1a1a2e; background #ffffff; line-height 1.6
- `.report`: single container

**Typography:**

- `h1`: font-size 1.8rem; color #1a1a2e; border-bottom 3px solid #ff9900; padding-bottom 8px
- `h2`: font-size 1.4rem; color #232f3e; margin-top 2rem
- `h3`: font-size 1.1rem; color #545b64

**Tables:**

- `table`: width 100%; border-collapse collapse; margin 1rem 0
- `th`: background #232f3e; color white; padding 10px 12px; text-align left; font-size 0.85rem
- `td`: padding 8px 12px; border-bottom 1px solid #e8e8e8; font-size 0.85rem
- `tr:hover`: background #f5f5f5

**Cards (for executive summary metrics):**

- `.metric-card`: display inline-block; background #f8f9fa; border 1px solid #e8e8e8; border-radius 8px; padding 16px 24px; margin 8px; text-align center; min-width 160px
- `.metric-value`: font-size 1.6rem; font-weight bold; color #232f3e
- `.metric-label`: font-size 0.8rem; color #687078; text-transform uppercase

**Cost comparison highlight:**

- `.cost-savings`: color #067d68 (green for savings)
- `.cost-increase`: color #d13212 (red for increase)

**Warning callout (for human_expertise_required):**

- `.callout-warning`: background #fff8e1; border-left 4px solid #ff9900; padding 12px 16px; margin 1rem 0; border-radius 0 4px 4px 0

**Confidence badges (visible text = user-facing vocabulary, not JSON):**

- `.badge`: display inline-block; padding 2px 8px; border-radius 12px; font-size 0.75rem; font-weight 600
- `.badge-deterministic`: background #e6f4ea; color #137333 — label **Standard pairing**
- `.badge-inferred`: background #fef7e0; color #b05a00 — label **Tailored to your setup**
- `.badge-billing`: background #fce8e6; color #c5221f — label **Estimated from billing only**

**Verdict badges (Section 0):**

- `.badge-verdict-migrate`: background #e6f4ea; color #137333 — `migrate_optimized`
- `.badge-verdict-phased`: background #e8f0fe; color #1a73e8 — `migrate_phased`
- `.badge-verdict-stay`: background #fef7e0; color #b05a00 — `stay`
- `.badge-complexity`: background #f1f3f4; color #545b64 — complexity signal

**Print styles:**

- `@media print`: hide nothing, adjust margins, ensure page breaks before `.appendix`

**Footer:**

- `footer`: margin-top 3rem; padding-top 1rem; border-top 1px solid #e8e8e8; text-align center; color #687078; font-size 0.8rem

### Content Rules

1. **All data must come from artifacts** — do not invent numbers or services. If an artifact field is missing, omit that section.
2. **Currency formatting**: Monthly figures as whole dollars with thousands separators (`$1,415`, `$118`). Use cents only where sub-dollar precision is meaningful (`$1.50`, `$0.40`). Be consistent within the report — do not mix `$118.00` and `$118`.
3. **Percentage formatting**: Include `+` or `-` prefix. Use green styling for savings, red for increases.
4. **No external resources**: No CDN links, no external fonts, no images. Everything inline.
5. **Valid HTML5**: Output must be valid, well-formed HTML5.

### Readability Conventions (enforced by `validate-migration-report.py`)

These move from "example in the fixture" to enforced gate. See `validate-migration-report.md` and `awslabs/startups:migrate/plugins/migration-to-aws/fixtures/migration-report-reference.html`.

1. **No numbered headings.** Rendered `<h2>`/`<h3>` headings use plain titles ("Total Cost of Ownership"), never `Section N — …`. The "Section N" labels used elsewhere in _this spec_ are authoring references only and must not appear in output. The table of contents carries structure: executive sections in an ordered `<ol>`, appendices in a separate lettered list (avoids "11. Appendix A" double-numbering). The validator fails on a literal `Section 0` or any `<hN>Section N — …` heading. **Genuine sequences keep their numbers.** This ban targets _decorative_ heading labels only. Real sequences — the migration cluster order, phased timeline weeks, migration phases, and rollback steps — MUST stay ordered (`<ol>` or a numbered table column) because the order carries information the reader needs. Do not flatten them to bullets to satisfy this rule.
2. **No internal scoring trace.** Per-cluster mapping rationale goes in a collapsible `<details class="why">` ("Why this mapping?") block — never a bare `Rubric:` line. The validator fails on a literal `Rubric:` in the body.
3. **Security teaser up top, full detail in the appendix.** `exec-security-teaser` carries a 2–3 line summary that links down to `appendix-security` (full control table) and `appendix-security-gap`. Do not render the full control table in the executive flow.
4. **Expand acronyms** on first use and include a glossary (TCO, DMS, OAI, RTO, CUD, SCC, IMDSv2, P95, RAG) in the assumptions section — the audience is startup founders, not AWS specialists.
5. **Accessible tables and diagrams.** Every table has a `<caption>` and `scope="col"` on header cells. The architecture diagram is wrapped in `<figure role="img" aria-label="…">` with a `<figcaption>` text alternative.
6. **State the verdict.** The decision summary includes a one-sentence recommendation banner (e.g. "Recommendation: Migrate, phased over 10 weeks — ~$497/mo savings, BigQuery deferred") in addition to the `path_label` badges.
7. **Reader vocabulary in the executive flow.** Artifact filenames (`estimation-infra.json`) and Terraform resource IDs (`aws_guardduty_detector.baseline`) are internal build vocabulary. Use them only in the technical appendices (`appendix-services`, `appendix-costs`, `appendix-security`, `appendix-artifacts`, etc.). In the executive flow (`decision-summary`, `exec-tco`, `exec-costs`, `exec-services`, `exec-architecture`, `exec-security-teaser`, `what-if-scenarios`, `exec-timeline`, `exec-risks`), name things by what the reader controls — "the generated security baseline", "the infrastructure cost estimate", "workshop scenario comparison" — not by the file or resource that produced them. Rewrite tooling-availability notes (e.g. "awsknowledge MCP not invoked") to reader-facing impact, or drop them. The validator fails on a `*.json` artifact filename or an `aws_<resource>.<name>` Terraform ID inside any `exec-*`, `what-if-scenarios`, or `decision-summary` section.
8. **One name per concept.** Use a single consistent label for each recommended choice across the whole report. The recommended Bedrock model and the chosen cost tier keep the same name in the verdict, tables, and appendices (always "Claude Sonnet 4.6 (recommended)", always "Balanced"). Do not alternate "recommended / selected target / design target / projected" for the same item — one label is how the reader keeps their bearings.
9. **Ordered action lists.** In `decision-summary`, `Key decisions ahead` and `Next steps` MUST use `<ol class="compact">`, not `<ul>`. The validator fails when either heading is followed by a bullet list. `Migrate if` / `Stay if` remain unordered lists.

> **Section IDs are stable anchors, not placement hints.** Some `appendix-*` IDs render in the executive flow on purpose (notably `appendix-assumptions`). Do not rename IDs to match position — the validator and TOC key on them.

## Step 4: Self-Check and Post-Write Validation

After generating the HTML file, verify:

1. **Required section IDs**: Each required ID appears **exactly once** on `<section id="...">` (not on `<div>` or other elements). See validator script.
2. **TOC integrity**: Every `<nav class="toc">` link `href="#id"` resolves to a `<section id="id">`; all required sections are linked.
3. **Appendix not a stub**: Appendix B contains ≥3 cost line items with dollar amounts; Appendix A contains per-cluster or per-service mappings (not only JSON file links).
4. **Security baseline surfaced**: When `projected_costs.breakdown.security_baseline` exists, GuardDuty or dollar-formatted component costs appear in `appendix-security` / `appendix-costs`.
5. **Combined TCO**: When **both** `estimation-infra.json` and `estimation-ai.json` exist, exactly one `exec-tco` section with summed totals.
6. **Data accuracy**: Cost figures in HTML match the estimation artifact values exactly — **manual / agent self-check**; the automated validator does not verify numerics (see `validate-migration-report.md` scope).
7. **Conditional sections**: AI appendix only present if AI artifacts exist; billing caveats shown when billing_data_available is false; Bedrock monitoring row only when `bedrock_monitoring.tf` exists; startup credits callout only when `STARTUP_PROGRAMS.md` or preference indicates eligibility
8. **Decision summary**: Migration Decision Summary present when estimation or preview artifacts exist; uses `recommendation.path_label` when block present, plus a one-sentence recommendation banner
9. **Human expertise flags**: Warning callouts appear for all services with `human_expertise_required: true`
10. **Valid HTML**: Opening and closing tags match, no broken table structures
11. **No placeholders**: No `[placeholder]` or `TODO` text in the report output
12. **Footer disclaimer**: Footer contains "draft for review"
13. **Readability**: No literal `Rubric:` and no numbered headings (`Section 0`, `Section 1b`, `<hN>Section N — …`); security teaser up top with full table in the appendix; tables have `<caption>`/`scope`; acronyms expanded; one-sentence recommendation banner in decision summary
14. **Reader vocabulary**: No artifact filenames (`*.json`) or Terraform resource IDs (`aws_*.*`) inside `decision-summary` / `exec-*` sections — those names live only in the technical appendices.
15. **Consistent labels**: The recommended model and the chosen cost tier use one consistent name across verdict, tables, and appendices (no "recommended / selected / design target" drift for the same item).
16. **Configuration provenance**: When `preferences.json` exists, `appendix-config` table has Question/assumption, Your choice, Source, and Design consequence columns populated from `prompt` and `design_consequence` fields (see `schema-preferences.md`).
17. **Ordered next steps**: `Key decisions ahead` and `Next steps` in `decision-summary` use `<ol>`, not `<ul>`.

**Run automated validator (mandatory when HTML was written):**

Load `validate-migration-report.md`. Resolve script from `$STEERING`: `$STEERING/validate-migration-report.py`.

```bash
python3 "$STEERING/validate-migration-report.py" \
  "$MIGRATION_DIR/migration-report.html" \
  --estimation-infra "$MIGRATION_DIR/estimation-infra.json" \
  --estimation-ai "$MIGRATION_DIR/estimation-ai.json" \
  --migration-dir "$MIGRATION_DIR"
```

Pass `--estimation-infra` / `--estimation-ai` only when those files exist in `$MIGRATION_DIR`. Use `--no-readability` only for non-customer test fixtures — not for normal Generate runs.

- On `REPORT_OK`: proceed to Step 5.
- On `REPORT_FAIL`: **rename** to `migration-report.incomplete.html` (default; do not delete), emit all failure lines to the user, and report to parent: "Report generation incomplete — re-run report step or expand appendix per awslabs/startups:migrate/plugins/migration-to-aws/fixtures/migration-report-reference.html". Do **not** claim a complete report was delivered or present a stub/numbered/jargon report as complete.

## Step 5: Open Report in Browser

After writing the HTML file, open it in the user's default browser so they can view it immediately.

Run: `open "$MIGRATION_DIR/migration-report.html"` (macOS) or `xdg-open "$MIGRATION_DIR/migration-report.html"` (Linux).

If the open command fails, fall back to presenting the full file path to the user:

```
Migration report ready — open in your browser:
file://$MIGRATION_DIR/migration-report.html
```

## Completion

Report to the parent orchestrator. **Do NOT update `.phase-status.json`** — the parent `generate.md` handles phase completion.

Output:

```
Migration report saved to $MIGRATION_DIR/migration-report.html

Report sections:
- Executive Summary: Section 0 Migration Decision Summary, [services count] primary services, [cost comparison], [timeline]
- Appendix A: Service Recommendations
- Appendix B: Cost Estimates
- Appendix C: Migration Steps
- [Appendix D: AI Migration — if applicable]
- Appendix E: Artifacts Catalog
- [Appendix F: Your Configuration — if preferences.json exists]
- Appendix G: Security Capabilities
- [Appendix H: Security Gap Analysis — when infra track ran]
- [Appendix I: Assumptions & Validation — always recommended]
```
