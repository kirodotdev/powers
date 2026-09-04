---
_fragment: migration-plan-gcp-constraints
_of_phase: migration-plan
---

# gcp-to-aws Global Constraints for Inline Execution

Loaded by `agent-advisor-migration-plan.md` Step 2.5. These constraints mirror gcp-to-aws's agent-advisor-orchestrator.md
and govern every phase that agent-advisor-migration-plan.md executes inline. Apply them exactly as if
gcp-to-aws's own state machine were running.

## Design principles (always active)

- **Dev sizing unless specified** — default to dev-tier capacity (db.t4g.micro, single AZ,
  0.5 vCPU Fargate). Only upgrade when the user explicitly requests it.
- **No human one-time migration costs** — do not present engineering labor or professional
  services as dollar estimates. Only vendor charges grounded in data are allowed.
- **Re-platform by default** — select AWS services that match GCP workload types.
- **BigQuery specialist gate** — if discovery finds BigQuery (`google_bigquery_*` in IaC or
  billing rows), STOP the migration and surface the specialist advisory before Design. Do
  not recommend a specific AWS analytics service; direct the user to their AWS account team.

## Context loading budget

Each phase should load no more than ~800 lines of instructions. Load conditional reference
files (the flat design-ref rubrics, sub-files) ONLY when their trigger condition is met — do not
speculatively load all sub-files.

**Always-load files in Generate (do not skip even when context is tight):**

- `generate-artifacts-docs.md` — produces MIGRATION_GUIDE.md + README.md (mandatory)
- `generate-artifacts-report.md` — produces migration-report.html and opens it in the
  browser. This is the final step of Generate and must NOT be skipped. It runs
  `open "$MIGRATION_DIR/migration-report.html"` (macOS) or
  `xdg-open "$MIGRATION_DIR/migration-report.html"` (Linux) after writing the file.

Conditional files (load ONLY when condition is true):

| File                                             | Condition                                                                          |
| ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `design-ref-ai-gemini-to-bedrock.md`            | `ai-workload-profile.json` exists AND `summary.ai_source` = `"gemini"` or `"both"` |
| `design-ref-ai-openai-to-bedrock.md`            | `ai-workload-profile.json` exists AND `summary.ai_source` = `"openai"` or `"both"` |
| `design-ref-ai-anthropic-to-bedrock.md`         | `ai-workload-profile.json` exists AND `summary.ai_source` = `"anthropic"`          |
| `design-ref-ai.md`                              | `ai-workload-profile.json` exists AND `summary.ai_source` = `"other"`              |
| `design-ref-harness.md`              | `agentic_profile.is_agentic == true` AND `migration_approach == "harness"`         |
| `design-ref-agentic-to-agentcore.md` | `agentic_profile.is_agentic == true` AND `migration_approach == "strands"`         |
| `retarget-gotchas.md`                     | `agentic_profile.is_agentic == true` AND `migration_approach == "retarget"`        |

All files above live directly in `$GCP_BASE` (= `$STEERING`, defined in migration-plan.md); there are no subdirectories.

## Feedback sidebar handling

gcp-to-aws's `agent-advisor-discover.md` and `agent-advisor-estimate.md` each offer a feedback prompt after their
`HANDOFF_OK`. Because this execution runs inside agent-advisor's session, automatically
choose "skip feedback" (option B) at both sidebars and continue to the next phase. Do
NOT load `feedback.md`.

## Hybrid stack warning

When both `gcp-resource-inventory.json` AND `ai-workload-profile.json` exist in
`$MIGRATION_DIR`, the combined design refs approach the ~800 line budget. Present the
user with the option to run infrastructure and AI workloads as two separate passes (as
specified in gcp-to-aws's agent-advisor-orchestrator.md hybrid stack warning), then continue based on their
answer.
