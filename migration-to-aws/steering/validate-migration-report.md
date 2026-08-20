# Validate Migration Report (Post-Write)

> **Read-only validation.** Run immediately after writing `migration-report.html` in `generate-artifacts-report.md` Step 4. Do NOT modify JSON artifacts.

If validation fails: **rename** the incomplete HTML to `migration-report.incomplete.html` (default — preserves output for inspection), emit failures to the user, and retry report generation. Do **not** delete unless the user asks. The Generate phase still completes (report is optional), but the user MUST see `REPORT_FAIL` — never silently accept a stub report.

---

## How to run (deterministic script path)

The validator script ships with the plugin at:

`migrate/plugins/migration-to-aws/scripts/validate-migration-report.py`

```bash
python3 "$STEERING/validate-migration-report.py" \
  "$MIGRATION_DIR/migration-report.html" \
  --estimation-infra "$MIGRATION_DIR/estimation-infra.json" \
  --estimation-ai "$MIGRATION_DIR/estimation-ai.json"
```

Pass `--estimation-infra` / `--estimation-ai` only when those files exist. Flags:

- `--migration-dir "$MIGRATION_DIR"` — enables **fixture-bleed detection** on real runs (the reference canary ID must not appear, and the report's migration ID must match the run folder). Omit it when validating the reference fixture itself.
- `--no-require-toc` — skip the TOC requirement (for minimal test fixtures only).
- `--no-readability` — skip the customer-facing readability checks (escape hatch; not for normal Generate runs).

### Check the exit code — do not pattern-match on stdout text alone

The agent must branch on the shell **exit code** of the validator command, not just on whether `REPORT_OK` or `REPORT_FAIL` appears in the text. If `python3` is not on `$PATH` (or the script path is wrong), the shell returns exit code `127` ("command not found") with neither string in its output — parsing for `REPORT_OK`/`REPORT_FAIL` alone leaves that case undefined and produces unpredictable agent behavior.

Handle exactly three outcomes:

| Exit code                                                                                | Meaning                                                                   | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`                                                                                      | `REPORT_OK` — validation passed                                           | Proceed to Step 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `1`                                                                                      | `REPORT_FAIL` — validation ran and found issues                           | Rename to `migration-report.incomplete.html`, surface failure lines to the user, retry report generation                                                                                                                                                                                                                                                                                                                                                                                 |
| anything else (e.g. `127` command not found, `126` permission denied, `2` bad arguments) | **Validator did not run** — this is neither `REPORT_OK` nor `REPORT_FAIL` | Do **not** rename or delete the HTML file. Do **not** claim the report passed or failed validation. Tell the user: "Could not run the report validator (`<exit code and stderr>`) — install Python 3 (`python3 --version` to check) or verify `$STEERING` is correct, then re-run validation manually." The Generate phase may still complete with the unvalidated report, but the user must be told validation did not occur — never silently treat a missing interpreter as a pass. |

---

## Scope

This validator is a **structural + readability completeness gate**. It does **not** verify that every dollar figure in the HTML matches estimation JSON. Self-check item for numeric accuracy in `generate-artifacts-report.md` remains a manual step. `REPORT_OK | structure=complete` means the report is ready for human review, not financially audited.

---

## Required checks (REPORT_FAIL on any failure)

| #  | Check                              | PASS when                                                                                                                                                                                                                                                                                     |
| -- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | Section IDs                        | Each required ID appears **exactly once** on a `<section id="...">` element (not `<div>`)                                                                                                                                                                                                     |
| 2  | Table of contents                  | `<nav class="toc">` exists; every `href="#id"` matches a `<section id="id">`; every required section is linked                                                                                                                                                                                |
| 3  | Appendix content                   | `appendix-costs` ≥3 data rows; `appendix-services` ≥2 mappings; `appendix-steps` ≥2 phases/rows                                                                                                                                                                                               |
| 4  | No stubs                           | Appendix B is not only "see estimation-infra.json"; appendix must render numeric costs from artifacts                                                                                                                                                                                         |
| 5  | Security costs                     | If `security_baseline` in estimate: **GuardDuty** or dollar-formatted component costs appear in `appendix-security` / `appendix-costs` (bare `15` in CSS does not count)                                                                                                                      |
| 6  | Footer                             | Contains "draft for review"                                                                                                                                                                                                                                                                   |
| 7  | No placeholders                    | No `[placeholder]` or `TODO` in report body                                                                                                                                                                                                                                                   |
| 8  | Combined TCO                       | If **both** `estimation-infra.json` and `estimation-ai.json` are passed: exactly one `<section id="exec-tco">`                                                                                                                                                                                |
| 9  | Readability — no scoring trace     | No literal `Rubric:` in the body. Render per-cluster rationale in a `<details>` "Why this mapping?" block instead                                                                                                                                                                             |
| 10 | Readability — no numbered headings | No literal `Section 0`, and no `<hN>Section N — …` numbered headings. Use plain titles; let the TOC carry structure. **Genuine sequences keep their numbering** — cluster order, phased weeks, migration phases, and rollback steps stay ordered; only _decorative_ section labels are banned |
| 11 | Security teaser present            | If `security_baseline` is in the estimate: exactly the compact `exec-security-teaser` carries it in the exec flow (full table stays in `appendix-security`)                                                                                                                                   |
| 12 | Verdict banner                     | If `estimation-infra.json` has a `recommendation` block: `decision-summary` contains a `class="verdict"` element or a "Recommendation:" sentence — not only badges                                                                                                                            |
| 13 | No fixture bleed                   | With `--migration-dir`: the reference canary migration ID does not appear in a real run, and the report's migration ID matches the run folder                                                                                                                                                 |
| 14 | Readability — reader vocabulary    | No artifact filename (`*.json`) or Terraform resource ID (`aws_<resource>.<name>`) inside any `exec-*` / `decision-summary` section. The executive flow names what the reader controls; those identifiers live only in the appendices                                                         |
| 15 | Ordered action lists               | When `Key decisions ahead` or `Next steps` headings exist in `decision-summary`, the following list is `<ol>`, not `<ul>`                                                                                                                                                                     |
| 16 | Configuration provenance           | When `<section id="appendix-config">` exists: table includes Question/Assumption and Design consequence columns; ≥2 data rows                                                                                                                                                                 |
| 17 | What-if scenarios                  | With `--migration-dir`: if `scenarios/index.json` lists ≥2 scenarios, exactly one `<section id="what-if-scenarios">` (workshop compare table)                                                                                                                                                 |

Checks 9, 10, and 14 scan the `<body>` with `<style>` stripped, so CSS class names (e.g. `.rubric`) and selectors never trip them. Check 14 scopes to executive-flow sections only — appendices may carry artifact filenames and resource IDs by design. Disable checks 9, 10, and 14 with `--no-readability` only for non-customer fixtures. Check 13 is inert without `--migration-dir`, so validating the reference fixture (which legitimately contains the canary ID) never self-trips. Checks 15–16 apply whenever the corresponding sections/headings exist.

---

## Optional sections (recommended — include when data exists)

| Section ID              | Include when                                                                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| `exec-tco`              | Both `estimation-infra.json` and `estimation-ai.json` exist                                                    |
| `exec-architecture`     | `aws-design.json` with clusters exists                                                                         |
| `exec-security-teaser`  | `estimation-infra.json` has `security_baseline` breakdown (compact summary; full table in `appendix-security`) |
| `what-if-scenarios`     | `scenarios/index.json` has ≥2 scenarios (baseline + workshop variant) — **required** when that trigger holds   |
| `appendix-ai`           | `estimation-ai.json` or `aws-design-ai.json` exists                                                            |
| `appendix-config`       | `preferences.json` exists — question/answer/consequence table from `prompt` and `design_consequence` fields    |
| `appendix-security`     | Full security capabilities table (rendered in the appendix)                                                    |
| `appendix-security-gap` | Infra track ran (rendered in the appendix)                                                                     |
| `appendix-assumptions`  | Pricing confidence, exclusions, validation status, glossary (rendered in the executive flow by design)         |

---

## Section IDs are stable anchors, not placement hints

Some `appendix-*` IDs render in the executive flow on purpose — `appendix-assumptions` especially, since exclusions and pricing confidence are executive-relevant. **Do not rename IDs to match position**; the validator and TOC key on them. `appendix-security` and `appendix-security-gap` render in the appendix and so their IDs match placement; `exec-security-teaser` is the compact executive summary that links down to them.

---

## Output

**Pass:**

```
REPORT_OK | structure=complete | sections=9/9 | optional=exec-tco,exec-security-teaser,appendix-ai | note=verify dollar figures against estimation JSON before sign-off
```

**Fail:**

```
REPORT_FAIL | migration-report.html
  - readability: internal scoring trace ("Rubric:") — drop it or gate behind a <details> "Why this mapping?" block
  - readability: literal "Section 0" heading — drop numeric "Section N" prefixes from customer-facing headings; let the table of contents carry structure
  - TOC broken link href="#decision" — no matching <section id="decision">
```

---

## Reference fixture

`awslabs/startups:migrate/plugins/migration-to-aws/fixtures/migration-report-reference.html` — TOC `href` values match `section id` attributes exactly, security detail lives in the appendix behind a teaser, mapping rationale is in `<details>` blocks, and headings carry no numbers. Validate with the full-contract command above.
