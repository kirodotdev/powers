---
_phase: generate
_title: "Generate Migration Artifacts"
_requires_phase: estimate
_input:
  - aws-design.json
  - estimation-infra.json
  - preferences.json
  - heroku-resource-inventory.json
_fragments:
  - _id: terraform
    _trigger: { _always: true }
    _file: heroku-generate-terraform.md
  - _id: docs
    _trigger: { _always: true }
    _file: heroku-generate-docs.md
  - _id: report
    _trigger: { _always: true }
    _file: heroku-generate-report.md
  - _id: eks-generate
    _trigger: { _when: "aws-design.json has an eks_cluster entry OR a service with aws_service == 'EKS'" }
    _file: heroku-generate-eks.md
_assemble:
  _file: heroku-generate-assemble.md
_produces:
  - terraform/main.tf
  - terraform/variables.tf
  - terraform/outputs.tf
  - terraform/security.tf
  - terraform/.gitignore
  - terraform/terraform.tfvars.example
  - MIGRATION_GUIDE.md
  - README.md
  - migration-report.html
  - generation-warnings.json
_advances_to: complete
_interactive: false
_exec:
  _agent: rw
_preconditions:
  - _check_phase_completed: estimate
    _on_failure: _halt_and_inform
  - _check_single_active_phase: true
    _on_failure: _halt_and_inform
  - _check_file_exists: [aws-design.json, estimation-infra.json, preferences.json, heroku-resource-inventory.json]
    _on_failure: _unrecoverable
  - _validate_json: [aws-design.json, estimation-infra.json, preferences.json, heroku-resource-inventory.json]
    _on_failure: _unrecoverable
_postconditions:
  - _check_file_exists: [terraform/main.tf, terraform/variables.tf, terraform/outputs.tf, terraform/security.tf, terraform/.gitignore, terraform/terraform.tfvars.example, MIGRATION_GUIDE.md, README.md, migration-report.html, generation-warnings.json]
    _on_failure: _halt_and_inform
  - _assert: "terraform/main.tf has valid provider configuration; terraform/variables.tf declares at least an aws_region variable"
    _on_failure: _halt_and_inform
  - _assert: "at least one domain .tf file exists beyond the core files"
    _on_failure: _halt_and_inform
  - _assert: "MIGRATION_GUIDE.md has Prerequisites and Verification sections; README.md lists the artifacts"
    _on_failure: _halt_and_inform
  - _assert: "migration-report.html has decision-summary, exec-costs, next-steps, and draft-for-review footer; if scenarios/index.json has ≥2 scenarios, also what-if-scenarios"
    _on_failure: _halt_and_inform
  - _assert: "if Postgres is in the design, scripts/migrate-postgres.sh exists; if Redis is in the design, scripts/migrate-redis.sh exists"
    _on_failure: _halt_and_inform
  - _assert: "if EKS is in the design, terraform/eks.tf exists WITH cluster + node group resources, AND a kubernetes/ directory has namespace + deployment manifests"
    _on_failure: _halt_and_inform
  - _assert: "if Elastic Beanstalk is in the design, terraform/beanstalk.tf exists; if preferences.design_constraints.eb_deploy_method.value is github_actions or absent, .github/workflows/deploy-eb.yml exists; if codepipeline, terraform/pipeline.tf exists; if manual, no automated deploy artifact is required"
    _on_failure: _halt_and_inform
  - _assert: "every designed service is accounted for (generated or listed in generation-warnings.json)"
    _on_failure: _halt_and_inform
  - _assert: "no placeholder {{VARIABLE}} tokens remain in Terraform .tf files (those belong in variables.tf as var.* references)"
    _on_failure: _halt_and_inform
_forbids_files:
  - heroku-resource-inventory.json
  - preferences.json
  - aws-design.json
  - estimation-infra.json
---

# Phase 5: Generate Migration Artifacts

## Orientation

Transform the design + estimate into deployable artifacts in `$MIGRATION_DIR/`: a
`terraform/` directory, `MIGRATION_GUIDE.md`, `README.md`, `migration-report.html`
(stakeholder summary + optional what-if scenarios), database migration scripts,
and `generation-warnings.json`. This is the multi-artifact phase.

Composed of the terraform + docs + report fragments + an EKS-generate fragment + one
cross-artifact validator assembler (declared in the frontmatter
`_fragments`/`_assemble`); the interpreter runs each fragment whose `_trigger` is
true, then the assembler. The `eks-generate` fragment is an ALTERNATIVE compute
path — it fires only when the design has an `eks_cluster` (its `_when` trigger),
emitting `eks.tf` + `kubernetes/` manifests. Templates are output skeletons
(`templates/generate/...`); the fragments are the routing algorithm. Read each unit
file for its own contract; the assembler owns the cross-artifact completion gate.

---

## Scope Boundary

**This phase covers artifact generation ONLY.**

FORBIDDEN — Do NOT include ANY of:

- Re-designing or changing AWS service selections (Phase 3 decisions are final)
- Re-estimating costs (Phase 4 estimates are final)
- Asking the user additional clarification questions (Phase 2 is done)
- Discovering new Heroku resources (Phase 1 is done)
- Feedback collection (Phase 6 handles this)

**Your ONLY job: Transform the design into deployable artifacts. Nothing else.**
