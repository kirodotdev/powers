---
_phase: estimate
_title: "Estimate AWS Costs"
_requires_phase: design
_input:
  - aws-design.json
  - preferences.json
  - heroku-resource-inventory.json
_knowledge:
  - { file: heroku-estimate-defaults.json }
  - { file: aws-infra-pricing.json }
  - { file: complexity-tiers.json }
  - { file: estimation-infra.schema.json }
_fragments:
  - _id: cost-engine
    _trigger: { _always: true }
    _file: heroku-estimate-cost-engine.md
_assemble:
  _file: heroku-estimate-assemble.md
_produces:
  - estimation-infra.json
_advances_to: generate
_re_entry_guard:
  _stale_if_completed: generate
  _stale_artifact: MIGRATION_GUIDE.md
  _on_reentry: stop_unless_confirmed
  _on_confirm: reset_downstream_to_pending
_preconditions:
  - _check_phase_completed: design
    _on_failure: _halt_and_inform
  - _check_single_active_phase: true
    _on_failure: _halt_and_inform
  - _check_file_exists: [aws-design.json, preferences.json, heroku-resource-inventory.json]
    _on_failure: _unrecoverable
  - _validate_json: [aws-design.json, preferences.json]
    _on_failure: _unrecoverable
  - _assert: "aws-design.json services[] exists and is non-empty, and every entry has aws_service and aws_config"
    _on_failure: _unrecoverable
_postconditions:
  - _check_file_exists: estimation-infra.json
    _on_failure: _halt_and_inform
  - _validate_json: estimation-infra.json
    _on_failure: _halt_and_inform
  - _assert: "recommendation.path is one of {migrate_optimized, migrate_phased, stay} and recommendation.path_label is a non-empty string"
    _on_failure: _halt_and_inform
  - _assert: "recommendation.migrate_if and recommendation.stay_if are non-empty arrays"
    _on_failure: _halt_and_inform
  - _assert: "projected_costs.aws_monthly_balanced is a positive number"
    _on_failure: _halt_and_inform
  - _assert: "every service in aws-design.json services[] appears in the cost breakdown, or is listed as 'unpriced' in warnings"
    _on_failure: _halt_and_inform
  - _assert: "the balanced total equals the arithmetic sum of the per-service costs, excluding unpriced (Property-16 invariant)"
    _on_failure: _halt_and_inform
  - _assert: "complexity_tier is one of {small, medium, large}"
    _on_failure: _halt_and_inform
_forbids_files:
  - README.md
  - "*.txt"
  - "terraform/**"
  - "kubernetes/**"
  - MIGRATION_GUIDE.md
---

# Phase 4: Estimate AWS Costs

## Orientation

Calculate projected monthly AWS costs for the designed Heroku-to-AWS architecture,
producing `estimation-infra.json` (conforming to
`estimation-infra.schema.json`) and classifying
migration complexity using the tier thresholds in
`complexity-tiers.json`.

Composed of a cost-engine fragment + one assembler (declared in the frontmatter
`_fragments`/`_assemble`); the interpreter runs the fragment, then the assembler,
and evaluates the `_knowledge` guards to load the pricing/defaults/tier data. The
fragment selects the pricing mode and computes the financial picture; the assembler
writes the final artifact, runs the completion gate, presents the summary, and
**offers the optional what-if workshop sidebar**
(`heroku-workshop.md`, `_kind: sidebar`) before Generate —
read each unit file for its own contract. Outer Estimate defers
`current_phase → generate` until workshop is resolved (see `heroku-estimate-assemble.md`).

---

## Scope Boundary

**This phase covers financial analysis ONLY.**

FORBIDDEN — Do NOT include ANY of:

- Changes to architecture mappings from Phase 3 (Design)
- Execution timelines or migration schedules (beyond tier classification)
- Terraform or IaC code generation
- Detailed migration procedures or runbooks
- Team staffing, human labor costs, or professional services fees
- AI workload estimation (not applicable to Heroku migrations)

**Your ONLY job: Show the financial picture of moving from Heroku to AWS. Nothing else.**
