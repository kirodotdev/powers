---
_assemble: assemble-poc
_of_phase: poc
_reads:
  - deployment plan + POC artifacts (written inline in agent-advisor-poc.md Steps 2.5–3)
  - HTML POC report (agent-advisor-poc-report.md contribution)
_produces:
  - plan.md
---

# POC — Assemble the deployment plan + POC

> **Assembler unit.** The POC phase writes the staged deployment plan
> (`plan.md`) and then the runtime-appropriate POC under `poc/` (Step 3 dispatch
> on the verdict — AgentCore Harness/Framework/hello-agent, or the ECS/EKS/Lambda
> shapes from agent-advisor-poc-shapes.md) inline within `agent-advisor-poc.md`; the `poc-report` fragment
> renders the HTML report. This unit records the artifact-level contract for the
> phase: it is the single creator of `plan.md` (the idea → **plan** → deploy
> bridge), and its postconditions (declared on the phase) are the phase's
> completion gate. See `agent-advisor-poc.md` § Steps 2.5–5 for the plan structure, the
> verify-don't-guess model-id rule, the deploy.sh guardrails, and the Mode B
> safety contract (identity gate, per-step confirmation, resource ledger,
> cleanup.sh).
