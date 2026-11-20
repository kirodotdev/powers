<!-- agent-advisor-recommendation-doc.md — fill all sections; business summary first, technical detail after -->

# AWS Agent Architecture Recommendation

## 1. Executive summary

<2–3 plain-language sentences: recommended runtime + why, for a non-technical reader.>

## 2. Your profile

`<bulleted summary of the answers that drove the decision; each answer carries provenance (wizard defaults vs user-stated).>`

## 3. Recommendation: `<Runtime>` <+ deployment model if AgentCore>

<rationale + the top scoring signals; business framing then technical specifics.>

## 3b. System topology (multi-unit systems only — omit entirely for one unit)

`<table: unit id | workload class | verdict | trigger | one-line rationale>`
<the platform decision: consolidated onto X / split, and why; the interconnect
(queue/gateway/none) in one sentence.>

## 3c. Temporal migration (temporal systems only — omit entirely otherwise)

<Worker deployment plan per task queue: Tier 1 choice + which rule fired + rationale (cite agent-advisor-temporal.md). Execution-tier plan per Activity class: Tier 2 targets (Light-IO in-process with hygiene reminders, agent-session scored, short-tool/heavy mapped). Commercials: selected by CURRENT server state — self-hosted → Way 1 gets Marketplace subscribe flow; already-on-Cloud gets billing-unchanged note (never re-pitch); Way 2 gets self-host stack. Cutover runbook: the selected runbook WITH its preconditions (runbook 1's graceful-drain/Activity-retry preconditions are not optional). Bedrock follow-up: if non-Bedrock LLM calls detected AND user said Yes → point to the llm-to-bedrock engine + replay safety per agent-advisor-temporal.md runbook 3 + shim caution if deeply-coupled; if user said No → "Later, optional: Bedrock" section with the same replay-safety pointer.>

## 4. Architecture diagram

<INSERT the Mermaid block + ASCII fallback produced by the Generate diagram step (Plan 3).>

## 5. Alternatives considered

<eliminated/lower-scored runtimes and why.>

## 6. Comparison

`<relevant rows from the runtime service cards.>`

## 7. Six dimensions

<Identity, Observability, Guardrails, Scaling, Tool/Gateway, Protocols — from the service card.>

## 8. AgentCore services to enable

<final service list from confirm.json, with why each; note which are free.>

## 9. Bedrock model

<model default + reasoning; for migrate, coarse family mapping + "see migration-to-aws for pricing".>

## 10. Cost magnitude

<Build paths (estimate.json exists): the band + assumptions + "order-of-magnitude" disclaimer; note that per-unit breakdown and cost drivers are detailed in estimate.json.
Migrate (estimate.json exists): present the per-unit target-state bands + breakdown from estimate.json. ALSO note that precise TCO comparison and current-spend delta are produced by the migration plugins. Do NOT invent a dollar band for anything estimate.json lacks (e.g., if Estimate failed, or for add_capabilities which bypasses Estimate).>

## 11. Next steps

<scaffolding pointers; handoff pointers if applicable. For AgentCore Build paths, point to the
deployment plan at `plan.md` (the staged idea → **plan** → deploy steps) and the generated POC at
`poc/` — agent code + deploy.sh + README — and note the user runs `./deploy.sh` themselves (it
creates real, billable AWS resources).>

## 12. Freshness footer

<from agent-advisor-freshness.md template: date, MCP-verified vs cached fields, verify disclaimer.>
