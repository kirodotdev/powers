# AI Migration Guardrails

Shared warnings and constraints for all agentic migration paths. Loaded once by `design-ai.md` when `agentic_profile.is_agentic == true`. Path-specific design references (Harness, Strands, retarget) should NOT duplicate these — reference this file instead.

---

## AgentCore Regional Availability

AgentCore services have different regional footprints. Always validate via `get_regional_availability` from the `awsknowledge` MCP server before recommending.

**As of May 2026:**

| Service                     | Availability | Regions                                                                                                                                                                                         |
| --------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AgentCore Runtime (GA)      | 15 regions   | us-east-1, us-east-2, us-west-2, us-west-1, ap-southeast-1, ap-southeast-2, ap-northeast-1, ap-northeast-2, ap-south-1, eu-central-1, eu-west-1, eu-west-2, eu-north-1, sa-east-1, ca-central-1 |
| AgentCore Harness (Preview) | 4 regions    | us-west-2, us-east-1, ap-southeast-2, eu-central-1                                                                                                                                              |
| AgentCore Memory (GA)       | 15 regions   | Same as Runtime                                                                                                                                                                                 |
| AgentCore Gateway (GA)      | 15 regions   | Same as Runtime                                                                                                                                                                                 |

**IMPORTANT:** These lists go stale. The `get_regional_availability` MCP call is the source of truth. Use the table above only as a fallback if the MCP call fails.

**If target region is unavailable for a recommended service:**

1. Flag prominently in `aws-design-ai.json` → `regional_warnings[]`
2. Suggest nearest available region as alternative
3. Note in user summary: "[Service] is not yet available in [target region]. Nearest available: [alternative]."

---

## Bedrock Mantle Throughput Limits (Shared Account)

Bedrock Mantle provides OpenAI-compatible endpoints on Bedrock. It runs on a **shared account limit of 10,000 RPM** across all Mantle users in a region — this is not a per-customer quota.

**Risk table:**

| Workload Volume        | Risk Level | Guidance                                                                                 |
| ---------------------- | ---------- | ---------------------------------------------------------------------------------------- |
| Low (< 100 RPM)        | Low        | Mantle is a good fit; shared limit is not a concern                                      |
| Medium (100–1,000 RPM) | Medium     | Monitor for 429s at peak; have a fallback ready                                          |
| High (> 1,000 RPM)     | High       | Use `bedrock-runtime` (Converse API) directly — not subject to the shared Mantle RPM cap |

**When to use `bedrock-runtime` instead of Mantle:**

- Production workloads with sustained high request rates
- Latency-sensitive workloads where shared-limit throttling is unacceptable
- Workloads that need per-customer quota increases via Service Quotas

**Source:** [AWS Bedrock Mantle scaling throughput best practices](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html)

---

## Bedrock Mantle TPM Limits (Claude Models)

Claude models on Mantle have an additional **output TPM cap** that differs by model generation:

| Model Family            | Output TPM Cap                | Notes                             |
| ----------------------- | ----------------------------- | --------------------------------- |
| Claude 4.7+             | 2,000,000 output TPM          | Per-model cap applies             |
| All other Claude models | No per-model output TPM limit | Standard account TPM limits apply |

**Impact for migration decisions:**

- For Claude migrations at medium/high volume: the 2M output TPM cap on Claude 4.7+ is the binding constraint, not the 10K RPM limit
- For gpt-oss migrations (OpenAI model architecture on Bedrock): check whether the target model is Claude 4.7+ and flag the output TPM cap in the design
- When output-heavy workloads (long JSON, tool outputs, multi-step reasoning) are detected, flag this cap prominently and recommend `bedrock-runtime` for production

---

## AgentCore Harness Preview Caveats

- Harness is in **public preview** — not GA. Production workloads should evaluate stability.
- No separate Harness charge — pay only for underlying AgentCore capabilities (Runtime, Memory, Gateway).
- Harness is powered by Strands Agents internally. Custom orchestration can switch from config-based to code-defined harness without rearchitecting.
- Harness supports Bedrock, OpenAI, and Google Gemini models. Third-party API keys stored in AgentCore Identity token vault.

---

## Model Lifecycle Checks

Before recommending any Bedrock model in an agentic design:

1. Check `steering/ai-model-lifecycle.md` for model status
2. Do NOT recommend Legacy models as primary selections
3. If a model is approaching EOL, note the date and suggest the Active successor

---

## Pricing Source Rules

For agentic workload cost estimation:

1. **Primary:** `steering/cached-prices.md` (±5-10% accuracy)
2. **Secondary:** `awspricing` MCP server (±5-10%, real-time)
3. **Tertiary:** `steering/pricing-fallback.md` (±15-25%, broad coverage)

AgentCore Runtime and Harness pricing: consumption-based, no upfront cost. Include in estimate only if the user selects Harness or Strands path.

---

## Effort Estimation Rules

Do NOT output fixed week estimates for agentic migrations. Output ranges with drivers:

**Format:** "[low]–[high] weeks depending on [driver 1] ([value]), [driver 2] ([value]), [driver 3] ([value])"

**Drivers to include:**

- Agent count (from `agentic_profile.agent_count`)
- Tool count (from `agentic_profile.tool_count`)
- Orchestration complexity (from `agentic_profile.orchestration_pattern`)
- Framework familiarity (team's experience with target framework)
- Test coverage (existing tests reduce migration risk)

**Example:** "2–5 weeks depending on agent count (3), tool count (8), and graph complexity (hierarchical with conditional routing)"
