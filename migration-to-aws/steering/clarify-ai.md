# Category F — AI/Bedrock (If `ai-workload-profile.json` Exists)

_Fire when:_ `ai-workload-profile.json` exists in `$MIGRATION_DIR/`.

These questions refine the AI migration approach — framework/orchestration layer, model selection, cost projections, and performance requirements.

---

## AI Context Summary

Before presenting questions, show the AI detection context:

> **AI Context Summary:**
> **AI source:** [from `summary.ai_source`: "Gemini", "OpenAI", "Both", or "Other"]
> **Models detected:** [from `models[].model_id`]
> **Capabilities in use:** [from `integration.capabilities_summary` where true]
> **Integration pattern:** [from `integration.pattern`] via [from `integration.primary_sdk`]
> **Gateway/router:** [from `integration.gateway_type`, or "None (direct SDK)"]
> **Frameworks:** [from `integration.frameworks`, or "None"]

---

## Q14 — What AI framework or orchestration layer are you using? (select all that apply)

**Rationale:** The orchestration layer determines the migration surface area more than the model choice. A LangGraph app with multi-agent tool-calling has a fundamentally different migration path than raw API calls routed through a gateway. Understanding the full AI stack upfront determines whether to migrate orchestration to Bedrock Agents, keep the existing framework with a Bedrock provider swap, adopt a hybrid approach, or simply change a gateway config.

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
- Nova Sonic or Whisper integration in code → G

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

| Answer                                   | Recommendation Impact                                                                                                                                                                                                        | Migration Effort  | Timeline                                           |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | -------------------------------------------------- |
| A) No framework — direct API calls       | Swap OpenAI/Gemini SDK calls to Bedrock SDK; recommend evaluating Bedrock Agents if planning agentic capabilities                                                                                                            | Low               | 1–3 weeks depending on call sites                  |
| B) LLM router/gateway                    | Add Bedrock as provider in gateway config, swap model IDs; no app code changes; verify gateway supports AWS SigV4 auth                                                                                                       | Minimal           | Hours to 1–3 days                                  |
| C) LangChain / LangGraph                 | Provider swap to Bedrock via `ChatBedrock` class; existing chains/graphs/tools preserved; validate tool schemas with Bedrock tool-use format                                                                                 | Low               | 1–3 days; 1 week if complex agent graphs           |
| D) Multi-agent framework                 | Two paths: 1) Keep framework, swap to Bedrock as LLM provider — lower effort, 2) Migrate to Bedrock multi-agent orchestration — higher effort, deeper AWS integration; recommend path 1 unless managed infrastructure wanted | Medium            | Path 1: 3–5 days; Path 2: 2–4 weeks                |
| E) OpenAI Agents SDK / custom agent loop | Highest effort; OpenAI Agents SDK is tightly coupled to OpenAI API with no provider swap; recommend Bedrock Agents as replacement or LangGraph as portable intermediate step; tool-calling schema translation required       | High              | 2–4 weeks                                          |
| F) MCP servers or A2A protocol           | Bedrock Agents supports MCP tool use natively; A2A interop available; recommend Bedrock Agents as orchestration layer to preserve MCP/A2A investments                                                                        | Low–Medium        | 3–5 days for MCP; 1–2 weeks if A2A refactoring     |
| G) Voice/conversational agent platform   | Check if platform supports Bedrock natively — if yes, config change only; if no, evaluate Nova Sonic as replacement for voice layer                                                                                          | Minimal to Medium | Hours if native; 2–3 weeks if Nova Sonic migration |

### Combination Logic

| Combination                          | Approach                                                                                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| A only                               | Simplest path — direct SDK migration                                                                                                     |
| B only                               | Quick win — gateway config change, skip SDK migration steps                                                                              |
| B + any other                        | Gateway swap is the quick win; assess framework migration as separate workstream                                                         |
| C + A                                | Two workstreams: LangChain provider swap (fast) + direct call migration (slower)                                                         |
| D + F                                | Complex — multi-agent with MCP tooling; recommend Bedrock Agents to unify orchestration and tool access                                  |
| E + anything                         | E is the long pole; plan timeline around the Agents SDK migration; other layers may be quick wins                                        |
| Multiple frameworks (C+D, C+E, etc.) | Assess each independently; prioritize by traffic volume or business criticality; recommend consolidating to one framework post-migration |

**Key principle:** When a framework is detected, lead with "here's how your orchestration layer maps to AWS" rather than "here's which model replaces yours." Model recommendation from subsequent questions becomes a sub-decision within the framework migration.

_Note: If answer includes B and no other selections, skip or abbreviate SDK migration steps. If answer is A only, proceed with standard model migration flow._

Interpret:

```
A -> ai_framework: ["direct"] — Full SDK migration required
B -> ai_framework: ["llm-router"] — Config change only (1-3 days)
C -> ai_framework: ["langchain"] — Provider swap via ChatBedrock
D -> ai_framework: ["multi-agent"] — Two migration paths available
E -> ai_framework: ["openai-agents"] — Highest effort; Bedrock Agents recommended
F -> ai_framework: ["mcp-a2a"] — Bedrock Agents for orchestration
G -> ai_framework: ["voice-platform"] — Check native Bedrock support
Multiple -> ai_framework: [array of all selected values]
```

Default: _(auto-detect from code)_ — fall back to `["direct"]` if detection fails.

---

## Q15 — Approximately how much are you spending on OpenAI or Gemini per month?

**Rationale:** AI spend drives the IW Migrate credits calculation at the 35% rate (vs 25% for infrastructure-only). Also provides the cost engine with a baseline for Bedrock cost comparison when detailed billing CSV is not uploaded.

**Pricing context:** GPT-5 ($1.25/$10 per 1M tokens) is actually cheaper than GPT-4o ($2.50/$10) and significantly cheaper than GPT-4 Turbo ($10/$30). Users on GPT-4 Turbo have the strongest cost savings case for migrating to Bedrock — Claude Sonnet 4.6 at $3/$15 is 70% cheaper on input tokens. Users on GPT-5 will see more modest savings since GPT-5 is already competitively priced.

> AI spend helps me calculate your migration credits eligibility (35% rate for AI workloads) and establish a cost baseline for Bedrock comparison.
>
> A) < $500/month
> B) $500–$2,000/month
> C) $2,000–$10,000/month
> D) > $10,000/month
> E) I don't know

| Answer               | Recommendation Impact                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| < $500/month         | AWS Activate or low-tier IW Migrate credits; Bedrock cost comparison shows modest savings         |
| $500–$2,000/month    | IW Migrate credits at 35% of ARR; Bedrock cost comparison highlighted                             |
| $2,000–$10,000/month | Significant IW Migrate credits; Bedrock cost savings prominently featured; Savings Plans analysis |
| > $10,000/month      | MAP eligibility likely; dedicated AI migration support; Bedrock provisioned throughput analysis   |

Interpret:

```
A -> ai_monthly_spend: "<$500" — Activate or low-tier IW Migrate
B -> ai_monthly_spend: "$500-$2K" — IW Migrate at 35% of ARR
C -> ai_monthly_spend: "$2K-$10K" — Significant IW Migrate; Savings Plans analysis
D -> ai_monthly_spend: ">$10K" — MAP eligibility; provisioned throughput analysis
E -> same as default (B)
```

Default: B — `ai_monthly_spend: "$500-$2K"`.

---

## Q16 — What matters most for your AI workloads?

**Rationale:** The primary priority is the top-level filter for Bedrock model selection. Quality, speed, and cost point to different model families.

**Context for user:** When asking, help the user think about their actual priority rather than defaulting to "best quality":

- **Best quality/reasoning** — accuracy and depth matter most; you'd pay more or wait longer for better answers (e.g., legal analysis, complex code generation, medical summarization)
- **Fastest speed** — response time is the primary constraint; users are waiting in real-time (e.g., chat UI, autocomplete, live suggestions)
- **Lowest cost** — volume is high and budget is tight; good-enough quality at scale (e.g., classification, tagging, bulk summarization)
- **Specialized capability** — you rely on a specific feature like vision, function calling, or extended thinking (covered in Q17)
- **Balanced** — no single dimension dominates; you want a solid all-rounder

> This determines our model selection strategy and optimization approach.
>
> A) Best quality/reasoning — accuracy matters most, willing to pay more
> B) Fastest speed — response time is the primary constraint
> C) Lowest cost — high volume, budget tight, good-enough quality at scale
> D) Specialized capability — rely on a specific feature (covered in Q17)
> E) Balanced — no single dimension dominates
> F) I don't know

| Answer                 | Recommendation Impact                                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Best quality/reasoning | Claude Sonnet 4.6 (latest, highest reasoning in Sonnet family) — primary; Claude Opus 4.6 for most demanding reasoning tasks |
| Fastest speed          | Claude Haiku 4.5 — lowest latency in Claude family; also consider Amazon Nova Micro/Lite for cost-optimized speed            |
| Lowest cost            | Claude Haiku 4.5 or Amazon Nova Micro — lowest cost per token                                                                |
| Specialized capability | Deferred to Q17 to determine which model                                                                                     |
| Balanced               | Claude Sonnet 4.6 as default balanced recommendation                                                                         |

Interpret:

```
A -> ai_priority: "quality" — Claude Sonnet 4.6; Opus 4.6 for hardest tasks
B -> ai_priority: "speed" — Haiku 4.5 or Nova Micro
C -> ai_priority: "cost" — Haiku 4.5 or Nova Micro
D -> ai_priority: "specialized" — deferred to Q17
E -> ai_priority: "balanced" — Claude Sonnet 4.6
F -> same as default (E)
```

Default: E — `ai_priority: "balanced"`.

---

## Q17 — What is your MOST CRITICAL specialized AI feature?

**Rationale:** Specialized features can override the priority-based model selection from Q16. Some features are only available in specific models.

> Some features are only available in specific models. This helps me ensure the recommended model supports your critical requirement.
>
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

| Answer                               | Recommendation Impact                                                                                                                        |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Function calling / Tool use          | Claude Sonnet 4.6 — best-in-class tool use on Bedrock via structured JSON tool schemas; supports parallel tool calls and multi-turn tool use |
| Ultra-long context (> 300K tokens)   | Claude Sonnet 4.6 — supports 1M token context window (beta); no chunking strategy required for most use cases                                |
| Extended thinking / Chain-of-thought | Claude Sonnet 4.6 with extended thinking mode; Claude Opus 4.6 for most complex reasoning                                                    |
| Prompt caching                       | Claude Sonnet 4.6 with prompt caching enabled; cost savings analysis included                                                                |
| RAG optimization                     | Amazon Bedrock Knowledge Bases recommended alongside model; Titan Embeddings for vector store                                                |
| Agentic workflows                    | Claude Sonnet 4.6 with Bedrock Agents; multi-agent orchestration guidance included                                                           |
| Real-time speed (< 500ms)            | Claude Haiku 4.5 or Nova Micro; streaming response guidance included                                                                         |
| Multimodal with image generation     | Claude Sonnet 4.6 (vision) + Amazon Nova Canvas or Titan Image Generator for generation                                                      |
| Real-time conversational speech      | Amazon Nova Sonic recommended for speech-to-speech; latency guidance included                                                                |
| None                                 | Default recommendation from Q16 priority stands                                                                                              |

Interpret:

```
A -> ai_critical_feature: "function-calling" — Claude Sonnet 4.6
B -> ai_critical_feature: "long-context" — Claude Sonnet 4.6 (1M context)
C -> ai_critical_feature: "extended-thinking" — Claude Sonnet 4.6 extended thinking; Opus 4.6
D -> ai_critical_feature: "prompt-caching" — Claude Sonnet 4.6 with caching
E -> ai_critical_feature: "rag" — Bedrock Knowledge Bases + Titan Embeddings
F -> ai_critical_feature: "agentic" — Claude Sonnet 4.6 + Bedrock Agents
G -> ai_critical_feature: "real-time-speed" — Haiku 4.5 or Nova Micro
H -> ai_critical_feature: "multimodal-generation" — Sonnet 4.6 + Nova Canvas/Titan Image
I -> ai_critical_feature: "speech" — Nova Sonic (hard override — Claude has no speech)
J -> (no constraint written — Q16 priority stands)
```

Default: J — no additional override.

---

## Q18 — What's your AI usage volume and cost tolerance?

**Rationale:** Volume at scale changes the economics significantly. High-volume workloads should use provisioned throughput or cheaper models even if quality is slightly lower.

> Volume determines whether on-demand or provisioned throughput is more cost-effective, and whether we should optimize for cost over quality.
>
> A) Low volume + quality priority — small-scale, quality matters most
> B) Medium volume + balanced — moderate production use, balanced approach
> C) High volume + cost critical — high scale, budget is tight, need cost control

| Answer                        | Recommendation Impact                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Low volume + quality priority | On-demand Claude Sonnet; no provisioned throughput needed                                                     |
| Medium volume + balanced      | On-demand Claude Sonnet or Haiku depending on Q16; Savings Plans analysis                                     |
| High volume + cost critical   | **Provisioned throughput strongly recommended**; Claude Haiku or Nova Micro; prompt caching analysis included |

Interpret:

```
A -> ai_volume_cost: "low-quality" — On-demand; quality model
B -> ai_volume_cost: "medium-balanced" — On-demand; Savings Plans analysis
C -> ai_volume_cost: "high-cost-critical" — Provisioned throughput; cheaper models; prompt caching
```

Default: A — `ai_volume_cost: "low-quality"`.

---

## Q19 — Which Gemini or OpenAI model are you currently using?

**Rationale:** The source model establishes the baseline Bedrock recommendation — a like-for-like capability match. This is a starting point only; answers to Q16 (priority), Q17 (features), Q18 (volume), Q21 (latency), and Q22 (complexity) can all override this baseline.

**Override hierarchy:**

1. Q17 special features — hard overrides (e.g., speech-to-speech forces Nova Sonic regardless of source model)
2. Q16 priority — adjusts up or down within the Claude family
3. Q18/Q21 volume and latency — may further adjust toward provisioned throughput or faster models
4. Q19 source model — baseline only, used when no overrides apply

> The model you're currently using helps me recommend the closest Bedrock equivalent as a starting point.
>
> A) Gemini Flash (1.5/2.0/2.5 Flash)
> B) Gemini Pro (1.5/2.5/3 Pro)
> C) GPT-3.5 Turbo
> D) GPT-4 / GPT-4 Turbo
> E) GPT-4o
> F) GPT-5 / GPT-5.x
> G) o-series (o1, o3)
> H) Other / Multiple models
> I) I don't know

| Source Model              | Baseline Bedrock Recommendation                                       | Pricing Context                                                  |
| ------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Gemini Flash variants     | Claude Haiku 4.5 ($1/$5) — speed and cost optimized                   | Strong savings vs Gemini Flash pricing                           |
| Gemini Pro variants       | Claude Sonnet 4.6 ($3/$15) — quality match                            | Comparable pricing tier                                          |
| GPT-3.5 Turbo             | Claude Haiku 4.5 ($1/$5) — cost-equivalent                            | Haiku is faster and cheaper                                      |
| GPT-4 / GPT-4 Turbo       | Claude Sonnet 4.6 ($3/$15) — quality equivalent                       | Major savings: GPT-4 Turbo is $10/$30 vs Sonnet $3/$15           |
| GPT-4o                    | Claude Sonnet 4.6 ($3/$15) — performance equivalent                   | Modest savings on output; input slightly higher on Bedrock       |
| GPT-5 / GPT-5.x           | Claude Sonnet 4.6 ($3/$15) — performance equivalent                   | GPT-5 is $1.25/$10 — savings story is quality/features, not cost |
| GPT-5 (flagship use case) | Claude Opus 4.6 ($5/$25) — flagship-to-flagship                       | Opus still cheaper than GPT-5 Pro ($15/$120)                     |
| o-series (o1, o3)         | Claude Sonnet 4.6 with extended thinking; Opus 4.6 for most demanding | o1 is $15/$60 — significant savings with Sonnet 4.6 at $3/$15    |

**Example overrides:**

- GPT-4 user (baseline: Sonnet 4.6) + Q16=lowest cost → **Haiku 4.5**
- Gemini Flash user (baseline: Haiku 4.5) + Q17=extended thinking → **Sonnet 4.6 with extended thinking**
- GPT-4o user (baseline: Sonnet 4.6) + Q17=real-time speech → **Nova Sonic** (Claude has no speech)
- GPT-3.5 user (baseline: Haiku 4.5) + Q22=complex reasoning → **Sonnet 4.6** (complexity overrides cost mapping)
- GPT-5 user (baseline: Opus 4.6) + Q16=balanced → **Sonnet 4.6** (priority overrides flagship mapping)

Interpret:

```
A -> ai_model_baseline: "claude-haiku-4-5" — speed/cost optimized
B -> ai_model_baseline: "claude-sonnet-4-6" — quality match
C -> ai_model_baseline: "claude-haiku-4-5" — cost equivalent
D -> ai_model_baseline: "claude-sonnet-4-6" — quality equivalent; major savings
E -> ai_model_baseline: "claude-sonnet-4-6" — performance equivalent
F -> ai_model_baseline: "claude-sonnet-4-6" — default; "claude-opus-4-6" for flagship use cases
G -> ai_model_baseline: "claude-sonnet-4-6-extended-thinking" — reasoning equivalent
H -> ai_model_baseline: "claude-sonnet-4-6" — safe default for multiple models
I -> same as default (use Q16 priority to determine)
```

Default: _(auto-detect from code)_ — fall back to Q16 priority-based selection.

---

## Q20 — Do you need vision (image understanding) or just text?

**Rationale:** Vision capability narrows the model selection to multimodal-capable models only.

> Vision capability limits which models are available. This ensures the recommendation supports your input types.
>
> A) Text only
> B) Vision required — model must process images
> C) Audio/Video inputs needed

| Answer             | Recommendation Impact                                                                 |
| ------------------ | ------------------------------------------------------------------------------------- |
| Text only          | Full model catalog available; cheapest/fastest text model per Q16 priority            |
| Vision required    | Claude Sonnet family (multimodal) required; Haiku excluded for vision tasks           |
| Audio/Video inputs | Amazon Nova Reel (video) or Nova Sonic (audio); Claude excluded for audio/video input |

Interpret:

```
A -> (no constraint written — full model catalog)
B -> ai_vision: "required" — Claude Sonnet family required; Haiku excluded for vision
C -> ai_vision: "audio-video" — Nova Reel (video) or Nova Sonic (audio); Claude excluded
```

Default: A — no constraint (text only).

---

## Q21 — How important is AI response speed?

**Rationale:** Latency requirements can override cost and quality preferences from Q16.

**Context for user:** When asking, anchor each option in a real scenario:

- **Critical (< 500ms)** — users are staring at a loading spinner; every millisecond matters (e.g., autocomplete, live chat, real-time transcription)
- **Important (< 2s)** — users expect a quick response but a brief pause is acceptable (e.g., chat assistant, search augmentation, inline suggestions)
- **Flexible (2–10s)** — users submit a request and can wait; background or async is fine (e.g., report generation, batch analysis, email drafting)

> Latency requirements can override cost and quality preferences from your earlier answers.
>
> A) Critical (< 500ms) — users staring at a loading spinner
> B) Important (< 2s) — quick response expected, brief pause acceptable
> C) Flexible (2–10s) — users can wait, background/async acceptable

| Answer             | Recommendation Impact                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------- |
| Critical (< 500ms) | Claude Haiku 4.5 or Nova Micro; streaming required; provisioned throughput for consistent latency |
| Important (< 2s)   | Claude Sonnet 4.6 with streaming; standard on-demand acceptable                                   |
| Flexible (2–10s)   | Any model; batch inference considered for cost savings at high volume                             |

Interpret:

```
A -> ai_latency: "critical" — Haiku 4.5 or Nova Micro; streaming; provisioned throughput
B -> ai_latency: "important" — Sonnet 4.6 with streaming; on-demand
C -> ai_latency: "flexible" — Any model; batch inference for cost savings
```

Default: B — `ai_latency: "important"`.

---

## Q22 — How complex are your AI tasks?

**Rationale:** Task complexity determines whether a cheaper/faster model can handle the workload or whether a more capable model is required.

**Context for user:** When asking, give concrete examples so the user doesn't over- or under-estimate:

- **Simple** — single-step tasks with short prompts: classify this text, extract these fields, summarize this paragraph
- **Moderate** — multi-step prompts with examples or structured output: analyze this document and return JSON, generate content following a template, few-shot classification
- **Complex** — multi-turn reasoning, tool use, or long chain-of-thought: agentic workflows, code generation with debugging loops, research tasks that require planning and iteration

> Task complexity determines whether a cheaper/faster model can handle the workload or whether a more capable model is required.
>
> A) Simple (classification, short summaries, extraction)
> B) Moderate (analysis, structured content, few-shot)
> C) Complex (multi-step reasoning, tool use, agentic workflows)

| Answer   | Recommendation Impact                                                                       |
| -------- | ------------------------------------------------------------------------------------------- |
| Simple   | Claude Haiku 4.5 or Nova Micro sufficient; significant cost savings vs larger models        |
| Moderate | Claude Sonnet 4.6 recommended; Haiku may suffice with prompt engineering                    |
| Complex  | Claude Sonnet 4.6 required; extended thinking considered; Claude Opus 4.6 for hardest tasks |

Interpret:

```
A -> ai_complexity: "simple" — Haiku 4.5 or Nova Micro sufficient
B -> ai_complexity: "moderate" — Sonnet 4.6 recommended; Haiku may suffice
C -> ai_complexity: "complex" — Sonnet 4.6 required; Opus 4.6 for hardest tasks
```

Default: B — `ai_complexity: "moderate"`.
