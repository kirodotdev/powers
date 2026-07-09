# Generate Phase: HTML Migration Report

> Loaded by generate.md AFTER generate-artifacts-docs.md completes.

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Generate a single self-contained HTML report (`migration-report.html`) combining an executive summary with detailed appendix. The HTML file uses inline CSS — no external dependencies required. Users can open it in any browser and use "Print to PDF" if a PDF is needed.

**Output:**

- `migration-report.html` — Self-contained HTML report with executive summary and detailed appendix

**Non-blocking:** If report generation fails after `VALIDATE_OK` (HTML build error only), log a warning and continue. Validation `GATE_FAIL` is **not** a silent skip — always surface to the user. Do NOT fail the Generate phase for report issues.

## Step 0: Validate Artifacts (Read Only)

Load and execute `steering/validate-artifacts.md` **before** building report content.

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

## Step 1: Build Executive Summary Section

The executive summary is the first thing visible when opening the report. Design it to fit approximately 1–2 printed pages.

### Executive Summary Content

**Header:** "GCP to AWS Migration Assessment" with subtitle "Executive Summary" and generation date.

**Target length:** approximately 1–2 printed pages. If content exceeds 2 pages, move the Security Capabilities table to Appendix G and keep only the teaser in the exec summary.

**Section 0 — Migration Decision Summary (REQUIRED):**

Pull from `estimation-infra.json` → `recommendation` block. Fallback chain if `recommendation` is absent:

1. `estimation-infra.json` → `financial_summary.recommendation` (string) — use as `path_label`; synthesize `migrate_if` / `stay_if` from Part 7 prose defaults in `estimate-infra.md`
2. `migration-preview.json` — show complexity + timeline only; label: "Full recommendation requires Estimate phase — run Phase 4"

Content when `recommendation` block exists:

1. **Verdict badge:** `recommendation.path_label` — render as colored badge (green for `migrate_optimized`, blue for `migrate_phased`, amber for `stay`)
2. **Complexity:** from `migration-preview.json` → `complexity_signal` ("Simple", "Moderate", "Complex") — colored badge
3. **Cost headline:** from `estimation-infra.json` → `cost_comparison.option_b_balanced` vs GCP baseline, OR legacy `comparison.aws_balanced_monthly_usd` vs `comparison.gcp_monthly_usd`. Do NOT use `migration-preview.json` → `cost_preview` when estimation artifact exists (preview is superseded). If only preview exists: show labeled "Early estimate (±30%) — full analysis not yet run."
4. **Timeline:** from `generation-infra.json` → `migration_plan.total_weeks` (preferred), OR `migration-preview.json` → `timeline_hint`. Do NOT use `recommendation.next_steps` as timeline — those are action items, not duration.
5. **Migrate if / Stay if:** from `recommendation.migrate_if` and `recommendation.stay_if`. Render as two compact lists.
6. **Key decisions ahead:** from `migration-preview.json` → `key_decisions_ahead` — bullet list
7. **Next steps (optional):** from `recommendation.next_steps` — compact bullet list separate from timeline

**Deferred services flag:** If ANY resource in the design artifact has `aws_service == "Deferred — specialist engagement"`, add a prominent callout:

> ⚠️ **Specialist engagement required:** [service name] does not have an automated AWS mapping. Engage your AWS account team before including this in cost projections or migration timelines.

**Startup credits callout:** If `STARTUP_PROGRAMS.md` exists in `$MIGRATION_DIR/` OR `$MIGRATION_DIR/ai-migration/STARTUP_PROGRAMS.md` OR `preferences.json` contains `startup_program_status.value` other than `"unknown"`:

> 💡 **AWS Activate credits:** You may be eligible for $1K–$100K in AWS credits that apply to Bedrock, Fargate, RDS, and other services used in this migration. See `STARTUP_PROGRAMS.md` for program tiers and application links.

Do not show this callout if none of the conditions are met.

Source: estimation artifact `recommendation`, `migration-preview.json`, design artifact

**Section 1 — Current Stack Overview:**

- Count of PRIMARY GCP services detected (from design artifact — filter to primary classification only; exclude secondary/supporting resources like default VPC firewalls)
- List each PRIMARY GCP service with its type (e.g., "Cloud Run (compute)", "Cloud SQL (database)")
- Source: design artifact (filtered)

**Section 2 — Recommended AWS Architecture:**

- Table with columns: GCP Service, AWS Service, **How we chose this**
- **How we chose this** values: use `steering/design-ref-fast-path.md` → **User-facing vocabulary** — **Standard pairing** (`deterministic`), **Tailored to your setup** (`inferred`), **Estimated from billing only** (`billing_inferred`). Show the **bold phrase** in the table; JSON value optional in a tooltip or footnote for technical readers only.
- One row per mapped service
- If any service has `human_expertise_required: true`, mark it with a warning indicator and footnote: "Specialist guidance recommended — contact your AWS account team"
- Source: design artifact

**Section 3 — Cost Comparison:**

- Side-by-side display: Current GCP Monthly vs Projected AWS Monthly (**Balanced** tier — the default scenario for comparing to GCP)
- Percent change (savings or increase)
- **How to read cost tiers (callout box — required when infra estimation with three tiers exists):** The three AWS monthly figures are **pricing scenarios** for the **same** mapped architecture (same services in `aws-design.json`), not three different generated Terraform stacks. **Order = highest → middle → lowest** monthly estimate in this model. Use **Balanced** as the **primary** row vs GCP; **Premium** and **Optimized** are **bounds** (higher HA / newer skew vs cost-optimization skew). When `terraform/` is present, it implements **one** infrastructure baseline aligned with the **Balanced** cost scenario (see `terraform/README.md` and `migration_summary` output).
- If 3 tiers available: show **Premium**, **Balanced**, and **Optimized** with **short subtitles** (second line or subtext under each label):
  - **Premium** — _Highest resilience / highest monthly estimate in this model_
  - **Balanced** — _Default scenario; compare GCP to this row first_
  - **Optimized** — _Lower monthly estimate; reservations, Spot, or storage trade-offs assumed_
- **Footnote (required):** _Only one Terraform configuration is generated (Balanced-aligned baseline). Premium and Optimized are what-if cost models in `estimation-infra.json` — adjust IaC yourself if you want those postures in production._
- **Only include "GCP data transfer egress (est.)" when the infra estimation artifact has `migration_cost_considerations.billing_data_available === true`.** Never present human one-time migration costs. If `false` or only non-infra estimates exist, footnote: "GCP data transfer egress estimates require billing data and the infra estimate path."
- If observability entry exists in `projected_costs.breakdown` (tolerant lookup: array where `service` contains "Observability" OR object where key contains `observability` or `cloudwatch`) AND the entry's `note` field mentions GCP free tiers:

> **Observability cost note:** [Pull the `note` field verbatim]

- Source: estimation artifact

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

- Total migration weeks
- Migration approach (phased/fast-track/conservative)
- Source: generation plan

**Section 7 — Top Risks:**

- Up to 3 highest-severity risks
- Each with: risk name, severity, one-line mitigation
- Source: generation plan risk_assessment

## Step 2: Build Detailed Appendix

The appendix follows the executive summary, clearly separated with an "Appendix: Detailed Migration Analysis" header.

### Appendix Section A — Service Recommendations

For each mapped service, include:

- GCP service name and type
- AWS service recommendation
- **How the mapping was chosen** — use **Standard pairing**, **Tailored to your setup**, or **Estimated from billing only** (`steering/design-ref-fast-path.md` → User-facing vocabulary); JSON `confidence` may appear in parentheses for support
- Full rationale text from design artifact
- If the mapping was **Tailored to your setup** (`inferred`) and `rubric_applied` is present: list the 6 criteria evaluations (appendix detail — optional in executive summary)
- If `human_expertise_required: true`: include the specialist guidance callout

Source: design artifact (aws-design.json or aws-design-billing.json)

### Appendix Section B — Cost Estimates

**Per-service cost breakdown table** with columns: Service Category, AWS Service, Monthly Cost (Balanced), Alternative, Alternative Cost, Potential Savings.

Source: estimation artifact projected_costs.breakdown

**Three-tier comparison table** with columns: **Tier** (name + subtitle as in Section 3), Monthly Cost, vs GCP Monthly, Annual Difference.

Repeat the **How to read cost tiers** callout from Section 3 here or include a one-line pointer: _See executive summary — three tiers are scenario $ only; generated Terraform matches **Balanced** baseline._

Source: estimation artifact cost_comparison

**Optimization opportunities table** with columns: Optimization, Target Services, Monthly Savings, Commitment, Effort.

Source: estimation artifact optimization_opportunities

> **Security baseline costs** are included as a line item in the breakdown above. For what each control does and GCP equivalents, see Section 4 (exec summary teaser) or Appendix G (full capabilities table).

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

### Appendix Section F — Your Configuration (conditional)

**Only include if `preferences.json` exists in `$MIGRATION_DIR/`.**

Key decisions that shaped this migration plan. Each value is read from `preferences.json` using the `.value` field of wrapped preference objects (e.g., `availability.value`, not `availability` directly).

| Decision                 | Your choice                                            | Impact on plan                                                  |
| ------------------------ | ------------------------------------------------------ | --------------------------------------------------------------- |
| Target AWS region        | `design_constraints.target_region.value` or equivalent | All resources deployed here; Bedrock model availability checked |
| Availability requirement | `availability.value`                                   | Drives RDS single-AZ vs Multi-AZ vs Aurora selection            |
| Monthly GCP spend        | From estimation source or `gcp_monthly_spend.value`    | Cost comparison baseline                                        |
| Framework                | `ai_framework.value` (if AI track ran)                 | Determines migration effort for AI workloads                    |
| AI priority              | `ai_priority.value` (if present)                       | Drives Bedrock model selection                                  |
| Compliance               | `compliance.value` (if present)                        | Triggers Config + Security Hub in baseline.tf                   |

**Source indicators:** Each preference shows `chosen_by`: `"user"` (explicitly answered), `"extracted"` (inferred from IaC/code), or `"default"` (plugin default applied).

**Full detail:** Open `preferences.json` in this directory.

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
| `exec-costs`         | Cost comparison headline               |
| `exec-timeline`      | Timeline                               |
| `exec-risks`         | Top risks                              |
| `appendix-services`  | Appendix A                             |
| `appendix-costs`     | Appendix B                             |
| `appendix-steps`     | Appendix C                             |
| `appendix-artifacts` | Appendix E                             |

Optional IDs (include when data exists): `appendix-ai`, `appendix-config`, `appendix-security`.

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
2. **Currency formatting**: All cost values displayed as `$X,XXX.XX` with dollar sign and commas.
3. **Percentage formatting**: Include `+` or `-` prefix. Use green styling for savings, red for increases.
4. **No external resources**: No CDN links, no external fonts, no images. Everything inline.
5. **Valid HTML5**: Output must be valid, well-formed HTML5.

## Step 4: Self-Check

After generating the HTML file, verify:

1. **Required section IDs**: `decision-summary`, `exec-services`, `exec-costs`, `exec-timeline`, `exec-risks`, `appendix-services`, `appendix-costs`, `appendix-steps`, `appendix-artifacts` each appear exactly once as `<section id="...">`. If any missing: treat as build failure (warn user; do not fail Generate phase).
2. **Data accuracy**: Cost figures in HTML match the estimation artifact values exactly
3. **Conditional sections**: AI appendix only present if AI artifacts exist; billing caveats shown when billing_data_available is false; Bedrock monitoring row only when `bedrock_monitoring.tf` exists; startup credits callout only when `STARTUP_PROGRAMS.md` or preference indicates eligibility
4. **Section 0**: Migration Decision Summary present when estimation or preview artifacts exist; uses `recommendation.path_label` when block present
5. **Human expertise flags**: Warning callouts appear for all services with `human_expertise_required: true`
6. **Valid HTML**: Opening and closing tags match, no broken table structures
7. **No placeholders**: No `[placeholder]` or `TODO` text in the report output
8. **Footer disclaimer**: Footer contains "draft for review"

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
```
