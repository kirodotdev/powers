---
_assemble: assemble-generation
_of_phase: generate
_reads:
  - terraform (fragment contribution)
  - docs (fragment contribution)
  - report (fragment contribution)
  - eks-generate (fragment contribution, when EKS in design)
_produces:
  - generation-warnings.json
---

# Generate — Validate and Assemble

> **Assembler unit.** Runs after the generation fragments (`heroku-generate-terraform.md`,
> `heroku-generate-docs.md`, `heroku-generate-report.md`, and `heroku-generate-eks.md` when EKS is in
> the design) have written their artifacts. It runs the cross-artifact validation
> (every-service-generated-or-warned, reference integrity, no `{{VAR}}` leak),
> enforces the completion handoff gate, and updates `.phase-status.json`. It owns
> the phase's final artifact-level contract.

---

## Step 3: Validate Complete Artifact Set

The full generated artifact set (core terraform files + MIGRATION_GUIDE.md +
README.md + migration-report.html + generation-warnings.json) is gate-checked by
this phase's `_postconditions` (see the Completion Handoff Gate below). This
assembler adds the cross-artifact checks that span multiple fragment outputs:

**Cross-reference checks:**

- Every service in `aws-design.json.services[]` is either generated in Terraform OR listed in `generation-warnings.json`
- If any service has `aws_service: "EKS"` → `terraform/eks.tf` must exist AND `kubernetes/` directory must contain at least one Deployment manifest
- If any service has `aws_service: "Elastic Beanstalk"` → `terraform/beanstalk.tf` must exist, plus the selected EB deploy artifact (`.github/workflows/deploy-eb.yml` for `github_actions`, `terraform/pipeline.tf` for `codepipeline`, none for `manual`)
- `README.md` references all files that actually exist
- `MIGRATION_GUIDE.md` data migration sections match design content (no empty sections)

---

## Completion Handoff Gate (Fail Closed)

The completion checks are declared in this phase's `_postconditions` frontmatter and
enforced per `INTERPRETER.md` § Gate protocol: re-read the generated artifacts from
disk, run the mechanical checks (`_check_file_exists` for the core terraform files +
MIGRATION_GUIDE.md + README.md + migration-report.html) and the `_assert` judgment
checks (valid provider / aws_region variable, a domain .tf beyond core, guide
sections, report sections, conditional Postgres/ Redis migration scripts, conditional
EKS terraform + kubernetes manifests, every service accounted for, no `{{VARIABLE}}`
placeholders), then emit `GATE_FAIL` (STOP) or
`HANDOFF_OK | phase=generate | artifacts=terraform/,MIGRATION_GUIDE.md,README.md,migration-report.html`.

Optionally run
`python3 "$STEERING/heroku-validate-migration-report.py" \
  "$MIGRATION_DIR/migration-report.html" --migration-dir "$MIGRATION_DIR"`
and treat exit `1` as `GATE_FAIL` for the report (repair HTML; do not delete
Terraform/docs).

---

## Step 4: Update Phase Status and Hand Off

Only after `HANDOFF_OK`, apply the phase-status update protocol (`INTERPRETER.md` § The interpreter loop) — mark `phases.generate` completed and advance per `_advances_to` (the `complete` terminal) — in the **same turn** as the output message below.

Output to user:

```
Generate phase complete.

Artifacts produced:
• terraform/ — [N] Terraform files for AWS infrastructure
• MIGRATION_GUIDE.md — Step-by-step migration procedure
• README.md — Artifact listing and quick start
• migration-report.html — Stakeholder summary (costs + what-if scenarios when present)
• scripts/ — Database migration scripts
[• generation-warnings.json — N service(s) require manual setup]   (show this line only when warnings is non-empty; the file is always written)

Migration planning is complete. All artifacts are in $MIGRATION_DIR/.
Share migration-report.html with stakeholders; use MIGRATION_GUIDE.md for cutover.
```

After this output, heroku-orchestrator.md handles the post-Generate share prompt and feedback finalization.

---

## Output Files

This phase's artifacts are declared in `_produces` (the terraform floor + MIGRATION_GUIDE.md + README.md + generation-warnings.json; `.phase-status.json` is updated per Step 4). Conditional outputs (`scripts/migrate-postgres.sh` when Postgres in design, `scripts/migrate-redis.sh` when Redis in design) are governed by the docs fragment's Step 0/Step 3; `generation-warnings.json` is always written (empty `warnings` array when nothing was skipped).

---

## Error Handling

Non-fatal generation errors and their handling (fatal predecessor/input/gate failures are handled by `_preconditions`/`_postconditions` + `INTERPRETER.md` § `_on_error`):

| Error Category                       | Behavior                                  |
| ------------------------------------ | ----------------------------------------- |
| Terraform generation partial failure | Log to generation-warnings.json, continue |
| Documentation generation failure     | GATE_FAIL at the completion gate          |
| Handoff gate check fails             | Halt pipeline, surface diagnostic         |
