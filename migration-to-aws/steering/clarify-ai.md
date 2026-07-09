# Category F — AI/Bedrock (If `ai-workload-profile.json` Exists)

_Fire when:_ `ai-workload-profile.json` exists in `$MIGRATION_DIR/`.

---

## AI Context Summary

Before presenting questions, show:

> **AI Context Summary:**
> **AI source:** [from `summary.ai_source`: "Gemini", "OpenAI", "Both", or "Other"]
> **Profile origin:** [from `metadata.profile_source`: if `iac_vertex` or `summary.inferred_from_iac` is true, state that Terraform was the primary signal and application code did not fully characterize the workload]
> **Models detected:** [from `models[].model_id`; if empty, say **None inferred from code or IaC** — the following questions will pin down models and frameworks]
> **Capabilities in use:** [from `integration.capabilities_summary` where true; if all false or pattern is `unknown`, say **Not inferred — confirm below**]
> **Integration pattern:** [from `integration.pattern`; if `unknown`, say **Unknown (IaC-only)**] via [from `integration.primary_sdk`, or **not determined**]
> **Gateway/router:** [from `integration.gateway_type`, or "None (direct SDK)"]
> **Frameworks:** [from `integration.frameworks`, or "None"]

---

## Q14 — Framework auto-detection signals

**Auto-detect signals** — scan IaC and application code before asking:

---

## Multi-Workload Confirmation Table (if `workloads[]` has ≥ 2 entries)

**Fire when:** `ai-workload-profile.json` contains a non-empty `workloads[]` array with 2 or more entries. This replaces the per-workload Q16–Q22 loop with a single confirmation table.

Before presenting Q16–Q22, show the detected workloads and proposed Bedrock targets:

> **Detected AI Workloads:**
>
> | # | Model                   | SDK Method                   | Capability        | Confidence | Proposed Bedrock Target       |
> | - | ----------------------- | ---------------------------- | ----------------- | ---------- | ----------------------------- |
> | 1 | gemini-2.5-flash        | generateContent              | text_generation   | medium     | [text-class per Q16 priority] |
> | 2 | gemini-2.5-flash        | generateContent (structured) | structured_output | high       | [same text-class as row 1]    |
> | 3 | imagen-3.0-generate-001 | generateImages               | image_generation  | high       | [image-class model]           |
>
> **For each row, you can:**
>
> - **Accept** — keep the proposed mapping
> - **Edit** — change the capability or Bedrock target
> - **Drop** — this isn't an AI workload (false positive)
>
> _(v1: merge and split actions are planned for v2)_
>
> _Do you accept all mappings? Or type the row number to edit._

**Timing:** This table fires AFTER existing global/infra questions complete (Q1–Q15 and Q14–Q15 AI globals). It does not replace or conflict with the master Clarify orchestrator or PR #57 auto-extraction — those run first, and their answers feed into the capability confirmation.

**Behavior:**

1. **High-confidence rows (confidence = `high`):** Pre-fill Bedrock target from `capability → Bedrock model` mapping. Do NOT ask Q16–Q22 for these rows unless the user edits.

2. **Medium/low-confidence rows:** Ask at most 2 questions per row:
   - "Is the detected capability correct?" (confirm or select from: text_generation, structured_output, image_generation, embedding, speech_to_text, text_to_speech, unknown)
   - "What matters most for this workload?" (Q16 priority: quality/speed/cost/balanced)

3. **Target mapping** (default, overridden by user edits — look up actual model IDs from design-refs tables, not hardcoded names):

   | Capability        | Target Class                                   | Notes                                                                                                                              |
   | ----------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
   | text_generation   | Text/reasoning class                           | Apply Q16–Q19 override hierarchy                                                                                                   |
   | structured_output | Text/reasoning class (same as text_generation) | Uses same Bedrock target as text_generation for that workload's priority tier — structured output is a mode, not a different model |
   | image_generation  | Image generation class                         | e.g., Nova Canvas                                                                                                                  |
   | embedding         | Embedding class                                | e.g., Titan Embed Text v2                                                                                                          |
   | speech_to_text    | Speech-to-text class                           | e.g., Transcribe                                                                                                                   |
   | text_to_speech    | Text-to-speech class                           | e.g., Polly                                                                                                                        |
   | unknown           | Ask Q16–Q22 for this workload                  | Falls back to full questionnaire                                                                                                   |

4. **After confirmation — persist workloads[] to preferences.json (REQUIRED):**

   Immediately after the user confirms (accepts all, or finishes editing individual rows), write the final `workloads[]` array to `preferences.json`. This is the **single source of truth** for all downstream phases (Design, Estimate, Generate). Do NOT rely on `ai-workload-profile.json` downstream — it contains the raw Discover output before user edits/drops.

   **Write rules:**
   - Read existing `preferences.json` (preserving all non-AI fields written by earlier Clarify categories)
   - Add or overwrite the top-level `workloads` key with the confirmed array
   - Each entry MUST include: `workload_id`, `model_id`, `sdk_method`, `capability`, `capability_confidence`, `structured_output`, `call_sites`, `target_bedrock_model`, and the user's `priority`/`latency_tier` selections (use defaults `"balanced"`/`"standard"` for high-confidence rows that were auto-accepted)
   - Dropped rows are excluded from `workloads[]` — they do not appear
   - Write the file atomically (write to `.tmp`, then rename) to prevent partial writes on failure
   - If write fails: STOP. Output: "Failed to persist workloads to preferences.json — do not proceed to Design."

   **Single-workload case:** If only 1 workload exists (confirmation table skipped), persist it to `workloads[]` after Q16–Q22 completes, using the same schema. Design always reads `workloads[]` regardless of count.

   **Zero-workload case:** If no AI workloads detected and user doesn't report any, write `"workloads": []` to preferences.json. Design emits empty `design_blocks[]` for this case.

5. **Question budget:** 4 global questions (Q14, Q15, framework, spend) + at most 2 per medium/low workload. For an app with 3 high-confidence workloads: 4 questions total, 0 per-workload. For an app with 2 high + 1 medium: 4 + 2 = 6 questions max.

**Single-workload fallback:** If `workloads[]` has exactly 1 entry or is empty, skip the confirmation table and proceed with the existing Q16–Q22 flow below.

**Known limitations (v1):**

- Gateway calls (LiteLLM, OpenRouter) and custom HTTP calls to AI endpoints are not yet detected as separate workloads — they may be miscategorized or missed. Planned for v2.
- Merge and split actions are not supported in v1. Users who need to combine or split workloads should edit individual rows.

---

## Q14 — What AI framework or orchestration layer are you using? (select all that apply)

**Auto-detect signals** — scan IaC and application code before asking:

- No AI framework imports, raw HTTP calls to OpenAI/Gemini endpoints → A
- LiteLLM imports or config files → B
- OpenRouter base URL in code/config → B
- PortKey, Helicone, Martian SDK imports → B
- Kong AI Gateway, Apigee AI config files → B
- Custom proxy class wrapping the AI client → B
- LangChain/LangGraph imports → C
- LangChain/LlamaIndex with provider-agnostic model config → C
- CrewAI imports, `Crew` and `Agent` class definitions → D
- AutoGen imports, `ConversableAgent` patterns → D
- Custom multi-agent loop with dispatcher logic → D
- OpenAI Agents SDK / Swarm imports → E
- Custom while-loop agent with tool-call parsing → E
- `mcp.server` / `mcp.client` imports, MCP config JSON files → F
- A2A protocol config or SDK imports → F
- Vapi, Bland.ai, Retell SDK imports → G
- Nova Sonic / Nova 2 Sonic or Whisper integration in code → G

_Skip when:_ Auto-detection fully resolves the framework(s). Use detected value(s) with `chosen_by: "extracted"`.

> How your AI calls reach the model determines migration effort. Gateway users can often migrate by changing a single config line.
>
> A) No framework — direct API calls to OpenAI/Gemini
> B) LLM router/gateway (LiteLLM, OpenRouter, PortKey, Kong, Apigee)
> C) LangChain / LangGraph
> D) Multi-agent framework (CrewAI, AutoGen, custom)
> E) OpenAI Agents SDK / custom agent loop
> F) MCP servers or A2A protocol
> G) Voice/conversational agent platform (Vapi, Retell, Bland.ai)
>
> _(Multiple selections allowed)_

| Answer                             | Recommendation Impact                                                                                     | Migration Effort  | Timeline                                             |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------------------------------- |
| A) No framework — direct API calls | Swap SDK calls to Bedrock SDK; evaluate Bedrock Agents if planning agentic                                | Low               | 1–3 weeks depending on call sites                    |
| B) LLM router/gateway              | Add Bedrock as provider in gateway config; no app code changes; verify SigV4 auth                         | Minimal           | Hours to 1–3 days                                    |
| C) LangChain / LangGraph           | Provider swap via `ChatBedrock`; chains/graphs/tools preserved; validate tool schemas                     | Low               | 1–3 days; 1 week if complex graphs                   |
| D) Multi-agent framework           | Path 1: Keep framework, swap LLM provider (lower effort). Path 2: Migrate to Bedrock multi-agent (deeper) | Medium            | Path 1: 3–5 days; Path 2: 2–4 weeks                  |
| E) OpenAI Agents SDK               | Highest effort; tightly coupled to OpenAI API; recommend Bedrock Agents or LangGraph as portable step     | High              | 2–4 weeks                                            |
| F) MCP / A2A                       | Bedrock Agents supports MCP natively; A2A interop available; recommend Bedrock Agents as orchestration    | Low–Medium        | 3–5 days MCP; 1–2 weeks A2A                          |
| G) Voice platform                  | If platform supports Bedrock natively → config change; otherwise evaluate Nova 2 Sonic                    | Minimal to Medium | Hours if native; 2–3 weeks if Nova 2 Sonic migration |

### Combination Logic

| Combination                          | Approach                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| A only                               | Simplest path — direct SDK migration                                                                   |
| B only                               | Quick win — gateway config change, skip SDK migration steps                                            |
| B + any other                        | Gateway swap is the quick win; assess framework migration as separate workstream                       |
| C + A                                | Two workstreams: LangChain provider swap (fast) + direct call migration (slower)                       |
| D + F                                | Complex — multi-agent with MCP tooling; recommend Bedrock Agents to unify orchestration and tools      |
| E + anything                         | E is the long pole; plan timeline around Agents SDK migration; other layers may be quick wins          |
| Multiple frameworks (C+D, C+E, etc.) | Assess independently; prioritize by traffic volume or business criticality; consolidate post-migration |

If answer includes B and no other selections, skip or abbreviate SDK migration steps. If answer is A only, proceed with standard model migration flow.

Interpret → `ai_framework` array (multiple selections → array of all selected values). Default: auto-detect from code, fallback `["direct"]`.

---

## Q15 — Approximately how much are you spending on OpenAI or Gemini per month?

> A) < $500/month
> B) $500–$2,000/month
> C) $2,000–$10,000/month
> D) > $10,000/month
> E) I don't know

| Answer               | Recommendation Impact                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| < $500/month         | **AWS Activate Founders** (up to $5,000 credits, self-service, no VC needed — apply at aws.amazon.com/startups/credits); Bedrock free tier covers initial testing; Bedrock cost comparison shows modest savings                                                                                                                                                                                                                  |
| $500–$2,000/month    | **AWS Activate Portfolio** (up to $200,000 credits for VC/accelerator-backed startups — requires Activate Provider Org ID); Bedrock cost comparison highlighted; credits apply to Bedrock third-party models including Claude                                                                                                                                                                                                    |
| $2,000–$10,000/month | **AWS Activate Portfolio** (up to $200,000); Bedrock cost savings prominently featured; Savings Plans analysis; if agentic workload detected → flag **AWS Generative AI Accelerator** (up to $1M credits, cohort-based, adjacent to the credits-hub funnel)                                                                                                                                                                      |
| > $10,000/month      | **AWS Credits for AI Startups** ($200,000+, invite-only for startups ready to scale post-Activate-Portfolio — contact your AWS Account Manager; see aws.amazon.com/startups/credits); dedicated AI migration support; Bedrock provisioned throughput analysis; if agentic workload detected → also flag **AWS Generative AI Accelerator** (up to $1M credits, 8-week cohort — aws.amazon.com/startups/generative-ai/accelerator) |

**Activate eligibility (Founders & Portfolio):** Pre-Series B, founded in the last 10 years, AWS Account on Paid Tier Plan, and either new to Activate Credits or requesting more credits than previously received.

Interpret → `ai_monthly_spend`. Default: B → `"$500-$2K"`.

---

## Q16 — What matters most for your AI workloads?

Present with concrete anchors: Quality = legal analysis/code gen; Speed = autocomplete/live chat; Cost = classification/tagging at scale; Specialized = specific feature (→ Q17); Balanced = all-rounder.

> A) Best quality/reasoning — accuracy matters most, willing to pay more
> B) Fastest speed — response time is the primary constraint
> C) Lowest cost — high volume, budget tight, good-enough quality at scale
> D) Specialized capability — rely on a specific feature (covered in Q17)
> E) Balanced — no single dimension dominates
> F) I don't know

| Answer                 | Recommendation Impact                                                                                                                                                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Best quality/reasoning | Claude Sonnet 4.6 (latest, highest reasoning in Sonnet family) — primary; Claude Opus 4.7 for the most demanding reasoning tasks (same headline on-demand $5/$25 as Opus 4.6 on standard Bedrock pricing); Claude Opus 4.6 remains a valid alternative |
| Fastest speed          | Claude Haiku 4.5 — lowest latency in Claude family; also consider Amazon Nova Micro/Lite for cost-optimized speed                                                                                                                                      |
| Lowest cost            | Claude Haiku 4.5 or Amazon Nova Micro — lowest cost per token                                                                                                                                                                                          |
| Specialized capability | Deferred to Q17 to determine which model                                                                                                                                                                                                               |
| Balanced               | Claude Sonnet 4.6 as default balanced recommendation                                                                                                                                                                                                   |

Interpret → `ai_priority`. Default: E → `"balanced"`.

---

## Q17 — What is your MOST CRITICAL specialized AI feature?

> A) Function calling / Tool use
> B) Ultra-long context (> 300K tokens)
> C) Extended thinking / Chain-of-thought
> D) Prompt caching
> E) RAG optimization
> F) Agentic workflows
> G) Real-time speed (< 500ms)
> H) Multimodal with image generation
> I) Real-time conversational speech
> J) None — standard features are sufficient

| Answer                               | Recommendation Impact                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Function calling / Tool use          | Claude Sonnet 4.6 — best-in-class tool use on Bedrock via structured JSON tool schemas; supports parallel tool calls and multi-turn tool use                                                                                                                                                                                                                                         |
| Ultra-long context (> 300K tokens)   | Claude Sonnet/Opus 4.6 long-context SKUs where available (standard on-demand for 4.6 matches base tier in US East N. Virginia per [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)); or Llama 4 Scout (10M), Llama 4 Maverick (1M), Nova 2 Pro/Lite (1M) for very large native context windows                                                                      |
| Extended thinking / Chain-of-thought | Claude Sonnet 4.6 with extended thinking mode; Claude Opus 4.6 for most complex reasoning                                                                                                                                                                                                                                                                                            |
| Prompt caching                       | Claude Sonnet 4.6 with prompt caching enabled; cost savings analysis included. **Caveat:** caching only helps for long, repeated context (system prompts, documents). Per-model minimum token thresholds (~1K–4K tokens) and TTL apply — short prompts won't cache. Verify current minimums at docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html before recommending. |
| RAG optimization                     | Amazon Bedrock Knowledge Bases recommended alongside model; Titan Embeddings for vector store                                                                                                                                                                                                                                                                                        |
| Agentic workflows                    | Claude Sonnet 4.6 with Bedrock Agents; multi-agent orchestration guidance included                                                                                                                                                                                                                                                                                                   |
| Real-time speed (< 500ms)            | Claude Haiku 4.5 or Nova Micro; streaming response guidance included                                                                                                                                                                                                                                                                                                                 |
| Multimodal with image generation     | Claude Sonnet 4.6 (vision) + Amazon Nova Canvas for generation                                                                                                                                                                                                                                                                                                                       |
| Real-time conversational speech      | Amazon Nova 2 Sonic recommended for speech-to-speech; latency guidance included                                                                                                                                                                                                                                                                                                      |
| None                                 | Default recommendation from Q16 priority stands                                                                                                                                                                                                                                                                                                                                      |

Interpret → `ai_critical_feature`. Default: J → no override.

---

## Q18 — What's your AI usage volume and cost tolerance?

> A) Low volume + quality priority — small-scale, quality matters most
> B) Medium volume + balanced — moderate production use, balanced approach
> C) High volume + cost critical — high scale, budget is tight, need cost control

| Answer                        | Recommendation Impact                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Low volume + quality priority | On-demand Claude Sonnet; no provisioned throughput needed                                                     |
| Medium volume + balanced      | On-demand Claude Sonnet or Haiku depending on Q16; Savings Plans analysis                                     |
| High volume + cost critical   | **Provisioned throughput strongly recommended**; Claude Haiku or Nova Micro; prompt caching analysis included |

Interpret → `ai_token_volume`: A → `"low"`, B → `"medium"`, C → `"high"`. Default: A → `"low"`.

---

## Q19 — Which Gemini or OpenAI model are you currently using?

**Auto-detect signal:** If `ai-workload-profile.json` exists and `models[0].model_id` is set with detection confidence ≥ 0.8, map to the matching Q19 answer and **skip Q19**. Set `ai_model_baseline` with `chosen_by: "extracted"`. If multiple models detected with similar confidence, ask Q19.

_Skip when:_ Primary model fully resolved from discovery. Use detected value with `chosen_by: "extracted"`.

Establishes baseline Bedrock recommendation. **Override hierarchy:** Q17 special features (hard override) > Q16 priority > Q18/Q21 volume and latency > Q19 source model (baseline only).

> A) Gemini 3.5 Flash (GA — current flagship Flash model)
> B) Gemini 3.5 Flash Thinking (thinking budget enabled)
> C) Gemini 3.1 Pro
> D) Gemini 3.1 Flash-Lite (high-volume, low-cost)
> E) Gemini 2.5 Flash (standard, no thinking budget)
> F) Gemini 2.5 Flash Thinking (thinking budget enabled — variable output pricing)
> G) Gemini 2.5 Pro
> H) Gemini 3 Pro / 3.1 Pro Preview
> I) Gemini Flash (2.0 Flash) or Gemini Flash 1.5 _(EOL Sep 2025 — flag for source model upgrade)_
> J) Gemini Pro 1.5 _(EOL Sep 2025 — flag for source model upgrade)_
> K) GPT-3.5 Turbo
> L) GPT-4 / GPT-4 Turbo
> M) GPT-4o
> N) GPT-5.4 / GPT-5.4 Mini / GPT-5.4 Nano
> O) GPT-5 / GPT-5.x (older)
> P) GPT-5.5 / GPT-5.5 Pro
> Q) o-series (o1, o3)
> R) Other / Multiple models
> S) I don't know

| Source Model                   | Baseline Bedrock Recommendation                                                                                                                                                 | Pricing Context                                                                                                                                                                                                                                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gemini 3.5 Flash (GA)          | Nova Lite ($0.06/$0.24) — 94% cheaper                                                                                                                                           | Gemini 3.5 Flash is $1.50/$9.00 — 5x more expensive than old 2.5 Flash; Nova Lite is the cost-equivalent; very strong migration case                                                                                                                                         |
| Gemini 3.5 Flash Thinking      | Claude Sonnet 4.6 with extended thinking ($3/$15)                                                                                                                               | At $1.50/$9.00 base + thinking tokens, Sonnet 4.6 is comparable or cheaper at full thinking; profile actual thinking usage before committing                                                                                                                                 |
| Gemini 3.1 Flash-Lite          | Nova Micro ($0.035/$0.14) — 88% cheaper; or Nova Lite ($0.06/$0.24) — 76% cheaper                                                                                               | Gemini 3.1 Flash-Lite is $0.25/$1.50; strong Bedrock cost case                                                                                                                                                                                                               |
| Gemini 2.5 Flash (standard)    | Nova Lite ($0.06/$0.24) — 88% cheaper                                                                                                                                           | Gemini 2.5 Flash is $0.30/$2.50; Nova Lite is the cost-equivalent; strong migration case                                                                                                                                                                                     |
| Gemini 2.5 Flash Thinking      | Claude Sonnet 4.6 with extended thinking ($3/$15)                                                                                                                               | Thinking output pricing on Gemini 2.5 Flash ranges $0.60–$3.50/M depending on thinking budget; at full thinking budget Sonnet 4.6 is comparable or cheaper; flag that thinking token costs vary and user should profile their actual thinking budget usage before committing |
| Gemini 2.5 Pro                 | Nova 2 Pro ($1.38/$11) — 9% cheaper; or Nova Pro ($0.80/$3.20) — 62% cheaper                                                                                                    | Gemini 2.5 Pro is $1.25/$10; migration case is cost + AWS consolidation                                                                                                                                                                                                      |
| Gemini 3 Pro / 3.1 Pro         | Claude Sonnet 4.6 ($3/$15) — agentic reliability; or Nova 2 Pro ($1.38/$11) — cost                                                                                              | Gemini 3.1 Pro is $2/$12 — cheaper than Sonnet 4.6; migration case is agentic reliability and AWS ecosystem, NOT cost. Be honest: Gemini 3.1 Pro leads on general benchmarks.                                                                                                |
| Gemini Flash 1.5 / 2.0 (older) | Nova Lite ($0.06/$0.24) or Nova Micro ($0.035/$0.14) — **flag Gemini 1.5 Flash as EOL (Sep 2025); recommend upgrading source model to 3.5 Flash before or alongside migration** | Strong Bedrock cost savings; 1.5 Flash is past EOL so migration is doubly urgent                                                                                                                                                                                             |
| Gemini Pro 1.5 (older)         | Claude Sonnet 4.6 ($3/$15) — **flag Gemini 1.5 Pro as EOL (Sep 2025); recommend upgrading source model to 3.1 Pro before or alongside migration**                               | 1.5 Pro is past EOL; migration to Bedrock and source model upgrade should be planned together                                                                                                                                                                                |
| GPT-3.5 Turbo                  | Claude Haiku 4.5 ($1/$5) — cost-equivalent                                                                                                                                      | Haiku is faster and cheaper                                                                                                                                                                                                                                                  |
| GPT-4 / GPT-4 Turbo            | Claude Sonnet 4.6 ($3/$15) — quality equivalent                                                                                                                                 | Major savings: GPT-4 Turbo is $10/$30 vs Sonnet $3/$15                                                                                                                                                                                                                       |
| GPT-4o                         | Claude Sonnet 4.6 ($3/$15) — performance equivalent                                                                                                                             | Modest savings on output; input slightly higher on Bedrock                                                                                                                                                                                                                   |
| GPT-5.4                        | Claude Sonnet 4.6 ($3/$15) — near price parity                                                                                                                                  | GPT-5.4 is $2.50/$15 — ~5% cheaper; migration case is AWS consolidation, not cost                                                                                                                                                                                            |
| GPT-5.4 Mini                   | Nova Lite ($0.06/$0.24) — massive cost savings                                                                                                                                  | 94% cheaper on Bedrock; strong migration case                                                                                                                                                                                                                                |
| GPT-5.4 Nano                   | Nova Micro ($0.035/$0.14) — massive cost savings                                                                                                                                | 87% cheaper on Bedrock; strong migration case                                                                                                                                                                                                                                |
| GPT-5.4 Pro                    | Nova 2 Pro ($1.38/$11) — flagship reasoning on AWS                                                                                                                              | 94% cheaper on Bedrock; strongest migration case                                                                                                                                                                                                                             |
| GPT-5 / GPT-5.x (older)        | Claude Sonnet 4.6 ($3/$15) — performance equivalent                                                                                                                             | GPT-5 is $1.25/$10 — savings story is quality/features, not cost                                                                                                                                                                                                             |
| GPT-5 (flagship use case)      | Claude Opus 4.6 ($5/$25) — flagship-to-flagship                                                                                                                                 | Opus still cheaper than GPT-5 Pro ($15/$120)                                                                                                                                                                                                                                 |
| GPT-5.5                        | Claude Opus 4.6 ($5/$25) — flagship-to-flagship                                                                                                                                 | Bedrock 17% cheaper on output ($25 vs $30); same input price                                                                                                                                                                                                                 |
| GPT-5.5 (cost-sensitive)       | Claude Sonnet 4.6 ($3/$15) — 53% cheaper                                                                                                                                        | Strong cost case; Sonnet leads on agentic reliability                                                                                                                                                                                                                        |
| GPT-5.5 Pro                    | Nova 2 Pro ($1.38/$11) — flagship reasoning on AWS                                                                                                                              | 95% cheaper on Bedrock; strongest migration case                                                                                                                                                                                                                             |
| o-series (o1, o3)              | Claude Sonnet 4.6 with extended thinking; Opus 4.6 for most demanding                                                                                                           | o1 is $15/$60 — significant savings with Sonnet 4.6 at $3/$15                                                                                                                                                                                                                |

**Override examples:** GPT-4 + Q16=cost → Haiku; Flash + Q17=extended thinking → Sonnet; GPT-4o + Q17=speech → Nova 2 Sonic; GPT-3.5 + Q22=complex → Sonnet; GPT-5 + Q16=balanced → Sonnet; GPT-5.5 + Q16=cost → Sonnet 4.6; Gemini 2.5 Flash Thinking + Q16=cost → Nova Lite (if thinking budget is low) or Sonnet 4.6 (if full thinking mode).

Interpret → `ai_model_baseline`. Default: auto-detect from code, fallback Q16 priority-based.

---

## Q20 — What input types must the model accept: text only, images (vision), or audio/video?

**Auto-detect signal:** Read `integration.capabilities_summary`:

| Signal                                           | Extract                                                                    | Skip Q20?                      |
| ------------------------------------------------ | -------------------------------------------------------------------------- | ------------------------------ |
| `vision: true`                                   | `ai_vision: "vision-required"`                                             | Yes — `chosen_by: "extracted"` |
| `speech_to_text: true` or `text_to_speech: true` | `ai_vision: "audio-video"`                                                 | Yes                            |
| all false / text only                            | `ai_vision: "text-only"`                                                   | Yes                            |
| `image_generation: true` and `vision: false`     | note in `ai_capabilities_required`; skip Q20 (image output ≠ vision input) | Yes                            |

_Skip when:_ Modalities fully resolved from `capabilities_summary`. Use detected value with `chosen_by: "extracted"`.

> A) Text only
> B) Vision required — model must process images
> C) Audio/Video inputs needed

| Answer             | Recommendation Impact                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Text only          | Full model catalog available; cheapest/fastest text model per Q16 priority                                             |
| Vision required    | Claude Sonnet or Haiku (both support multimodal vision); Nova Micro excluded (text-only)                               |
| Audio/Video inputs | Amazon Nova 2 Sonic (audio); Nova Reel v1 for video (Legacy — EOL Sep 30, 2026); Claude excluded for audio/video input |

Interpret → `ai_vision`. Default: A → no constraint.

---

## Q21 — How important is AI response speed?

Present with concrete anchors: Critical = autocomplete/live chat/real-time transcription; Important = chat assistant/search augmentation; Flexible = report generation/batch analysis.

> A) Critical (< 500ms) — users staring at a loading spinner
> B) Important (< 2s) — quick response expected, brief pause acceptable
> C) Flexible (2–10s) — users can wait, background/async acceptable

| Answer             | Recommendation Impact                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| Critical (< 500ms) | Claude Haiku 4.5 or Nova Micro; streaming required; provisioned throughput for consistent latency |
| Important (< 2s)   | Claude Sonnet 4.6 with streaming; standard on-demand acceptable                                   |
| Flexible (2–10s)   | Any model; batch inference considered for cost savings at high volume                             |

Interpret → `ai_latency`. Default: B → `"important"`.

---

## Q22 — How complex are your AI tasks?

Present with concrete examples: Simple = classify/extract/summarize; Moderate = analyze+JSON/few-shot; Complex = multi-turn reasoning/tool use/agentic.

> A) Simple (classification, short summaries, extraction)
> B) Moderate (analysis, structured content, few-shot)
> C) Complex (multi-step reasoning, tool use, agentic workflows)

| Answer   | Recommendation Impact                                                                             |
| -------- | ------------------------------------------------------------------------------------------------- |
| Simple   | Claude Haiku 4.5 or Nova Micro sufficient; significant cost savings vs larger models              |
| Moderate | Claude Sonnet 4.6 recommended; Haiku may suffice with prompt engineering                          |
| Complex  | Claude Sonnet 4.6 required; extended thinking considered; Claude Opus 4.7 / 4.6 for hardest tasks |

Interpret → `ai_complexity`. Default: B → `"moderate"`.

---

## Category G — Agentic Workflows (If `agentic_profile` exists in `ai-workload-profile.json`)

_Fire when:_ `ai-workload-profile.json` contains `agentic_profile` with `is_agentic: true`.

_Skip entirely when:_ `agentic_profile` is absent from `ai-workload-profile.json`.

---

## Agentic Context Summary

Before presenting Category G questions, show:

> **Agentic Context Summary:**
> **Framework:** [from `agentic_profile.framework`]
> **Agents detected:** [from `agentic_profile.agent_count`] ([list `agents[].agent_id`])
> **Orchestration pattern:** [from `agentic_profile.orchestration_pattern`]
> **Tools:** [from `agentic_profile.tool_count`] tools detected
> **Memory:** [from `agentic_profile.has_memory`; if true, backend: `agentic_profile.memory_backend`]
> **Human-in-the-loop:** [from `agentic_profile.has_human_in_loop`]

---

## Q23 — How do you want to migrate your agent system?

**Auto-detect signals** — recommend default based on `agentic_profile.framework`:

- `gateway_type` is `"llm_router"` (LiteLLM or OpenRouter detected) → Default to **A (retarget)**. These users are already abstracted from the model provider — migration is a config change (swap model IDs), not a code rewrite. Set `migration_approach: "retarget"` automatically and skip Q23 unless the user explicitly asks to evaluate Harness or Strands.
- `langgraph`, `crewai`, `autogen` → Default to A (retarget). These frameworks support Bedrock as a model provider with minimal code changes.
- `openai_agents` → Surface all options. OpenAI Agents SDK is tightly coupled to OpenAI API; retarget is harder. Note partial retarget (HTTP-compatible routing to Bedrock) as a bridge.
- `strands` → Already AWS-native. Recommend B (Harness) for managed deployment or note "already on target framework."
- `custom` → Surface all options. Custom loops vary widely in complexity.

_Skip when:_ Auto-detection fully resolves AND user has no preference signal. Use detected default with `chosen_by: "extracted"`.

> Your agent system can migrate to AWS in different ways, each with different effort and risk:
>
> A) **Retarget** — Keep your current framework ([framework name]), swap the model layer to Bedrock. Fastest path, lowest risk. Your orchestration code stays the same.
> B) **AgentCore Harness** — Declare your agent as configuration (model + tools + prompt). Get managed runtime, memory, identity, and observability. Good for simpler agents or incremental migration. _(Preview — 4 regions: us-east-1, us-west-2, eu-central-1, ap-southeast-2)_
> C) **Strands native** — Rewrite orchestration using AWS Strands SDK on AgentCore. Most AWS-integrated, highest effort. Best for teams wanting full AWS-native multi-agent capabilities.
> D) **I'm not sure** — Help me decide based on my workload.

| Answer               | When it fits                                                                                                                               | Effort range                                                     | Risk                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | ------------------------------ |
| A) Retarget          | Working system, team knows the framework, need to ship fast. LangGraph/CrewAI/AutoGen with Bedrock model provider support.                 | 1–3 weeks depending on agent count, tool count, test coverage    | Low — orchestration unchanged  |
| B) AgentCore Harness | Simple single-agent, OpenAI Assistants migration, want managed runtime, or incremental migration (run existing models on AWS infra first). | 3–10 days depending on tool complexity and memory requirements   | Low — config-based, reversible |
| C) Strands native    | OpenAI Agents SDK or custom loops where retarget doesn't work well, multi-agent systems, team willing to refactor for AWS-native benefits. | 2–6 weeks depending on agent count, graph complexity, tool count | Medium — orchestration rewrite |
| D) Undecided         | —                                                                                                                                          | —                                                                | —                              |

**For OpenAI Agents SDK users:** Note that a partial retarget (HTTP-compatible routing to Bedrock while keeping OpenAI SDK orchestration) is a valid short-lived bridge before committing to B or C. This is not a fourth path — it's a Phase 0 step within B or C.

**If answer is D:** Recommend A (retarget) as default for LangGraph/CrewAI/AutoGen users. Recommend B (Harness) for OpenAI Assistants or simple single-agent patterns. Recommend C (Strands) only if user explicitly wants AWS-native multi-agent and accepts refactor cost.

Interpret → `ai_constraints.agentic.migration_approach`: A → `"retarget"`, B → `"harness"`, C → `"strands"`, D → `"undecided"` (treated as `"retarget"` in Design unless overridden). Default: auto-detect based on framework.

---

## Q24 — Do your agents need to remember context across sessions?

> A) No — each request is independent, no memory needed
> B) Within a session — conversation history during a single interaction, but fresh start each time
> C) Across sessions — remember user preferences, past interactions, accumulated knowledge between separate conversations

| Answer          | Recommendation Impact                                                                                                                                                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No memory       | Standard stateless invocation. No AgentCore Memory needed.                                                                                                                                                                                                      |
| Within session  | AgentCore Harness sessions are stateful by default (microVM per session). No additional config needed for Harness path. For retarget path: existing framework memory (e.g., LangGraph checkpointer) continues to work.                                          |
| Across sessions | AgentCore Memory service recommended. Persists knowledge, user preferences, and interaction history across sessions. For retarget path: evaluate existing memory backend migration (Redis → ElastiCache, Postgres → RDS, vector store → OpenSearch Serverless). |

Interpret → `ai_constraints.agentic.memory_requirement`: A → `"none"`, B → `"session"`, C → `"cross_session"`. Default: B → `"session"`.

---

## Q25 — How long do your agent tasks typically run?

> A) Quick (< 30 seconds) — simple tool calls, single-turn responses
> B) Medium (30 seconds – 5 minutes) — multi-step reasoning, several tool calls
> C) Long (5 minutes – 1 hour) — complex research, multi-agent collaboration, iterative refinement
> D) Very long (1+ hours) — extended autonomous work, large-scale data processing

| Answer    | Recommendation Impact                                                                                                                                                    |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Quick     | Standard invocation. Any deployment model works.                                                                                                                         |
| Medium    | AgentCore Runtime recommended for managed scaling. Harness sessions handle this natively.                                                                                |
| Long      | AgentCore Runtime strongly recommended (supports up to 8-hour sessions). Serverless alternatives (Lambda) will timeout.                                                  |
| Very long | AgentCore Runtime required (8-hour max session). If tasks exceed 8 hours: recommend breaking into sub-tasks with session chaining, or evaluate custom compute (ECS/EKS). |

Interpret → `ai_constraints.agentic.task_duration`: A → `"quick"`, B → `"medium"`, C → `"long"`, D → `"very_long"`. Default: B → `"medium"`.

---

## Q26 — Do you want to migrate incrementally?

> A) Yes — run my existing models (OpenAI/Gemini) on AWS infrastructure first, then swap to Bedrock models later when I'm confident
> B) No — do a full model swap to Bedrock in one go
> C) I'm not sure

| Answer            | Recommendation Impact                                                                                                                                                                                                                                                |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Yes (incremental) | AgentCore Harness multi-model switching: deploy on Harness with existing OpenAI/Gemini model (API key in AgentCore Identity), then override `--model-id` per invocation to A/B test Bedrock. Swap default when confident. Works for both Harness and retarget paths. |
| No (full swap)    | Standard migration: swap model layer directly to Bedrock. Faster to complete but higher risk per deployment.                                                                                                                                                         |
| Not sure          | Default to incremental if using Harness path (it's free — multi-model switching is built in). Default to full swap if retarget path with LangChain/LangGraph (simpler to test with framework's built-in model switching).                                            |

Interpret → `ai_constraints.agentic.incremental_migration`: A → `true`, B → `false`, C → auto-select based on `migration_approach`. Default: `true` for Harness path, `false` for retarget path.

---

## Category G Combination Logic

| Combination                             | Design Impact                                                                    |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| A (retarget) + C (cross-session memory) | Retarget model layer + migrate memory backend to AWS (Redis → ElastiCache, etc.) |
| B (harness) + A (no memory)             | Simplest Harness config — model + tools + prompt, no memory setup                |
| B (harness) + C (cross-session memory)  | Harness + AgentCore Memory service                                               |
| B (harness) + D (very long tasks)       | Flag: 8-hour session limit. Recommend task decomposition or session chaining.    |
| C (strands) + C (cross-session memory)  | Strands SessionManager + AgentCore Memory                                        |
| Any + A (incremental)                   | Include incremental migration script in Generate artifacts                       |

---

## Category H — Startup Programs (Always fires when Category F fires)

_Fire when:_ `ai-workload-profile.json` exists (same trigger as Category F). Ask once, after Q26 if agentic, or after Q22 if non-agentic.

---

## Q27 — Have you applied for AWS Activate credits?

**Rationale:** AWS Activate credits apply directly to Bedrock usage (including Claude, Llama, Nova, and other third-party models). Surfacing eligibility at the migration decision moment helps startups reduce the cost of the migration itself. This takes 30 seconds to answer and can unlock $5K–$200K in credits.

**Activate eligibility:** Pre-Series B, founded in the last 10 years, AWS Account on Paid Tier Plan, and either new to Activate Credits or requesting more credits than previously received.

> AWS Activate credits offset Bedrock costs during and after migration — including Claude, Llama, and Nova models. Eligible startups can get $5K–$200K depending on funding stage.
>
> A) Yes — already have AWS Activate credits
> B) No — haven't applied yet (self-funded or pre-VC)
> C) No — VC/accelerator-backed but haven't applied
> D) I don't know

| Answer                     | Recommendation Impact                                                                                                                                          |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Already have credits       | Note credit balance in migration plan; flag Bedrock usage as credit-eligible                                                                                   |
| No — self-funded           | Flag **AWS Activate Founders** (up to $5,000, self-service): aws.amazon.com/startups/credits — apply before starting migration to offset Bedrock testing costs |
| No — VC/accelerator-backed | Flag **AWS Activate Portfolio** (up to $200,000): requires Activate Provider Org ID from your VC/accelerator — contact them for the Org ID before applying     |
| Don't know                 | Surface both tiers; recommend checking with investors/accelerator for Org ID                                                                                   |

If `ai_monthly_spend` is `">$10K"`: also flag **AWS Credits for AI Startups** ($200,000+, invite-only for startups ready to scale post-Activate-Portfolio — contact your AWS Account Manager; aws.amazon.com/startups/credits).

If `ai_monthly_spend` is `"$2K-$10K"` or `">$10K"` AND `agentic_profile.is_agentic == true`: also flag **AWS Generative AI Accelerator** (up to $1M credits, 8-week cohort — adjacent cohort program, distinct from the credits-hub funnel): aws.amazon.com/startups/generative-ai/accelerator

Interpret → `startup_program_status`: A → `"has_credits"`, B → `"eligible_founders"`, C → `"eligible_portfolio"`, D → `"unknown"`. Default: D → `"unknown"`.

---

## Preferences Output — `ai_constraints.agentic`

Category G answers are stored in `preferences.json` → `ai_constraints.agentic`:

```json
{
  "ai_constraints": {
    "agentic": {
      "migration_approach": "retarget|harness|strands|undecided",
      "memory_requirement": "none|session|cross_session",
      "task_duration": "quick|medium|long|very_long",
      "incremental_migration": true
    }
  }
}
```

**Field contract (consumed by Design phase):**

- `migration_approach` — Routes Design to the correct path: `"retarget"` uses existing model-swap flow, `"harness"` loads `design-ref-harness.md`, `"strands"` loads `design-ref-agentic-to-agentcore.md`
- `memory_requirement` — Determines whether AgentCore Memory is included in design
- `task_duration` — Determines AgentCore Runtime recommendation and session limit warnings
- `incremental_migration` — Determines whether incremental migration artifacts are generated
