---
_fragment: report
_of_phase: generate
_contributes:
  - migration-report.html
---

# Generate — Stakeholder HTML Report (Heroku)

> Thin shareable HTML for SAs / founders. Not a full GCP/Vercel assessment
> clone — decision + costs + optional what-if scenarios, then point at
> `MIGRATION_GUIDE.md` for procedure. Runs **after** docs so the guide exists
> when the report links to it.

**Execute ALL steps in order. Do not skip.**

---

## Inputs

| Artifact                                                                                                                       | Use                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `estimation-infra.json`                                                                                                        | Recommendation path, three cost tiers, complexity                                                                                                                               |
| `aws-design.json`                                                                                                              | Short service count / primary compute target                                                                                                                                    |
| `preferences.json`                                                                                                             | Region, HA, arch (active scenario = working tree)                                                                                                                               |
| `scenarios/index.json` + manifests **+ each scenario's `scenarios/scenario-NNN.preferences.json` / `.aws-design.json` copies** | What-if table when ≥2 scenarios — manifests carry the cost tiers/complexity; the per-scenario Region/HA/Compute/Arch columns come from the scenario's preferences/design copies |
| `MIGRATION_GUIDE.md`                                                                                                           | Must already exist (docs fragment ran first)                                                                                                                                    |

---

## Step 1: Gather figures

From `estimation-infra.json`:

- `recommendation.path_label` (or `financial_summary.recommendation`)
- `projected_costs.aws_monthly_premium` / `_balanced` / `_optimized`
- `complexity_tier`
- `pricing_source.status` (for a one-line pricing confidence note)

From design + preferences: region, primary compute (EB / Fargate / EKS),
service count.

---

## Step 2: Write `migration-report.html`

Write a **self-contained** HTML file to `$MIGRATION_DIR/migration-report.html`
(inline CSS only). Required section IDs:

| Section ID         | Content                                                                                                                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `decision-summary` | Verdict / path label, complexity, one-sentence next action                                                                                                                                                                             |
| `exec-costs`       | Heroku-vs-AWS side-by-side when a Heroku baseline exists (`current_costs.source != "unavailable"`); otherwise the AWS three-tier table with a one-line note that no Heroku baseline was available. Estimated monthly; Balanced primary |
| `next-steps`       | Ordered list pointing to `MIGRATION_GUIDE.md` phases (not a procedure dump)                                                                                                                                                            |

### Conditional — `what-if-scenarios`

When `scenarios/index.json` exists and `scenarios[]` has **≥ 2** entries,
render `<section id="what-if-scenarios">` **after** `exec-costs` and **before**
`next-steps`:

Render, in order:

- Table columns (must stay in sync with `heroku-workshop-compare.md`'s table):

| Scenario | Region | HA | Compute | Arch | Premium $/mo | Balanced $/mo | Optimized $/mo | Complexity |
| -------- | ------ | -- | ------- | ---- | ------------ | ------------- | -------------- | ---------- |

- Mark the active row (`index.active_scenario_id`).
- For each scenario with a non-null `estimation_summary.calculator_url`,
  render the scenario name as a link (or an adjacent "open in AWS Pricing
  Calculator" link) — stakeholders can open and edit the estimate there.
- Under the table: active vs baseline knob deltas; any `region_note`; remind
  inventory is frozen and Terraform matches the **active** scenario only.

Omit the section when workshop was declined or never entered.

### TOC + footer

- `<nav class="toc">` with links to every section present.
- Footer must include: `draft for review` and instruct readers to verify figures
  before sign-off.
- Title: `Heroku to AWS Migration Assessment`.
- Cost labeling: every dollar figure is an **estimated monthly** cost.
- Reader vocabulary: no `*.json` filenames or `aws_*.` resource IDs in
  `decision-summary` / `exec-costs` / `what-if-scenarios` (name things the
  reader controls).

### Minimal CSS

Use a short inline stylesheet: readable body font, `.report` max-width ~900px,
tables with borders, `.active-scenario` or bold active row, `.verdict` badge,
`.toc` list. Keep visual noise low — this is a one-pager for stakeholders, not
a design system.

### Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Heroku to AWS Migration Assessment</title>
  <style>/* inline */</style>
</head>
<body>
  <div class="report">
    <nav class="toc">…</nav>
    <section id="decision-summary">…</section>
    <section id="exec-costs">…</section>
    <!-- <section id="what-if-scenarios"> when ≥2 scenarios -->
    <section id="next-steps">…</section>
    <footer>Generated by Heroku to AWS Migration Advisor — draft for review; verify figures before executive sign-off.</footer>
  </div>
</body>
</html>
```

---

## Step 3: Soft gate

Before returning:

1. File exists and is non-empty.
2. Contains `decision-summary`, `exec-costs`, `next-steps`, and `draft for review`.
3. If `scenarios/index.json` has ≥2 scenarios, contains `what-if-scenarios`.

On failure: fix and rewrite — do **not** leave a stub. Report generation is
part of Generate for heroku-to-aws (stakeholder deliverable), but a report
failure should not delete Terraform/docs; repair the HTML and continue.

Optional (non-blocking): if
`$STEERING/heroku-validate-migration-report.py` exists, run:

```
python3 $STEERING/heroku-validate-migration-report.py \
  "$MIGRATION_DIR/migration-report.html" --migration-dir "$MIGRATION_DIR"
```

Exit 0 (`REPORT_OK`) → continue. Non-zero (`REPORT_FAIL | ...`) → repair the
named section(s) and re-run once; if it still fails, keep the best HTML, record
the failure line in `generation-warnings.json`, and continue (never a
generation halt).

---

## Scope Boundary

**This fragment writes `migration-report.html` ONLY.**

FORBIDDEN:

- Re-running Design / Estimate / workshop
- Duplicating the full `MIGRATION_GUIDE.md` procedure into HTML
- Inventing cost figures not present in `estimation-infra.json` / scenario
  manifests
