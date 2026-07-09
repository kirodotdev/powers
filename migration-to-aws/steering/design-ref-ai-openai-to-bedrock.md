# OpenAI to Bedrock — Model Selection Guide

**Applies to:** OpenAI SDK usage detected in GCP-hosted applications → Amazon Bedrock

This file is loaded by `design-ai.md` when `ai-workload-profile.json` has `summary.ai_source` = `"openai"` or `"both"`. It provides model mapping tables with pricing and honest competitive analysis for OpenAI → Bedrock migration decisions.

Many GCP-hosted applications use OpenAI's API rather than Vertex AI. This guide covers that migration path.

Verify all pricing via AWS Pricing MCP or `steering/cached-prices.md`. Uses OpenAI Standard tier pricing.

**Model lifecycle:** Before recommending any Bedrock model, check `steering/ai-model-lifecycle.md`. Do not recommend Legacy models as primary selections for new migrations. Legacy models are annotated below where they appear.

---

## Key Insight: The Landscape Has Changed (April 2026)

**It is no longer "Bedrock is always cheaper."** It depends on the model.

- **Bedrock cheaper:** GPT-5.5 flagship (17% cheaper output via Opus 4.6), Nova Lite vs Mini models (85-94%), Nova Micro vs Nano (65-87%), Nova 2 Pro vs Pro models (90-95%), DeepSeek-R1 vs o3 (32%)
- **OpenAI cheaper:** GPT-5.4 (5%), GPT-5.2 (50%), GPT-5.1/5 (40%), GPT-4.1 (43%), GPT-4o (29%), o4-mini/o3-mini/o1-mini (69%)

> **GPT-5.5 note (April 23, 2026):** GPT-5.5 doubled pricing to $5/$30 per MTok vs GPT-5.4's $2.50/$15. Claude Opus 4.6 at $5/$25 now matches on input and is **17% cheaper on output**. This reverses the GPT-5.4 dynamic where OpenAI was cheaper — at the GPT-5.5 tier, Bedrock wins on cost. GPT-5.5 uses 40% fewer output tokens on coding tasks (per OpenAI), partially offsetting the price hike for Codex-style workloads.

---

## Model Mapping Tables

### GPT-5.5 Series (Latest — April 23, 2026)

GPT-5.5 is the first fully retrained base model since GPT-4.5. Natively omnimodal (text + image + audio + video), 88.7% SWE-Bench Verified, 256K context in ChatGPT / 1M in API. Two variants: standard and Pro. No Mini/Nano variants at launch (expected Q3 2026). Percentages below are blended savings using a 2:1 input-to-output token ratio.

| OpenAI Model | Price (in/out per 1M) | Best Bedrock Match   | Bedrock Price  | Winner              |
| ------------ | --------------------- | -------------------- | -------------- | ------------------- |
| GPT-5.5      | $5.00 / $30.00        | Claude Opus 4.6      | $5.00 / $25.00 | Bedrock 17% cheaper |
| GPT-5.5      | $5.00 / $30.00        | Claude Sonnet 4.6    | $3.00 / $15.00 | Bedrock 53% cheaper |
| GPT-5.5 Pro  | $30.00 / $180.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 95% cheaper |

> **Token efficiency caveat:** OpenAI reports GPT-5.5 uses ~40% fewer output tokens on Codex-style tasks vs GPT-5.4. Effective cost increase over GPT-5.4 is ~50% (not 100%) for coding workloads. For non-coding workloads, the full 2× price applies.

### GPT-5.4 Series

Percentages below are blended savings using a 2:1 input-to-output token ratio. GPT-5.4 uses breakpoint pricing at 272K input tokens; rates below assume <272K context.

| OpenAI Model | Price (in/out per 1M) | Best Bedrock Match   | Bedrock Price  | Winner              |
| ------------ | --------------------- | -------------------- | -------------- | ------------------- |
| GPT-5.4      | $2.50 / $15.00        | Claude Sonnet 4.6    | $3.00 / $15.00 | OpenAI 5% cheaper   |
| GPT-5.4 Mini | $0.75 / $4.50         | Nova Lite            | $0.06 / $0.24  | Bedrock 94% cheaper |
| GPT-5.4 Nano | $0.20 / $1.25         | Nova Micro           | $0.035 / $0.14 | Bedrock 87% cheaper |
| GPT-5.4 Pro  | $30.00 / $180.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 94% cheaper |

### Flagship (GPT-5/5.2 Series)

Percentages below are blended savings using a 2:1 input-to-output token ratio.

| OpenAI Model    | Price (in/out per 1M) | Best Bedrock Match    | Bedrock Price  | Winner              |
| --------------- | --------------------- | --------------------- | -------------- | ------------------- |
| GPT-5.2         | $1.75 / $14.00        | Claude Opus 4.7 / 4.6 | $5.00 / $25.00 | OpenAI 50% cheaper  |
| GPT-5.1 / GPT-5 | $1.25 / $10.00        | Claude Sonnet 4.6     | $3.00 / $15.00 | OpenAI 40% cheaper  |
| GPT-5 Mini      | $0.25 / $2.00         | Nova Lite             | $0.06 / $0.24  | Bedrock 86% cheaper |
| GPT-5 Nano      | $0.05 / $0.40         | Nova Micro            | $0.035 / $0.14 | Bedrock 58% cheaper |

### Pro Models (Extended Reasoning)

> **Lifecycle note:** Nova Premier v1 is **Legacy** (EOL Sep 14, 2026). Nova 2 Pro (Preview) is the Active successor for reasoning-heavy workloads. Pricing differs — see `cached-prices.md`.

| OpenAI Model | Price (in/out per 1M) | Best Bedrock Match   | Bedrock Price  | Winner              |
| ------------ | --------------------- | -------------------- | -------------- | ------------------- |
| GPT-5.5 Pro  | $30.00 / $180.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 95% cheaper |
| GPT-5.4 Pro  | $30.00 / $180.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 94% cheaper |
| GPT-5.2 Pro  | $21.00 / $168.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 93% cheaper |
| GPT-5 Pro    | $15.00 / $120.00      | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 90% cheaper |

### GPT-4.1 Series

| OpenAI Model | Price (in/out per 1M) | Best Bedrock Match | Bedrock Price  | Winner              |
| ------------ | --------------------- | ------------------ | -------------- | ------------------- |
| GPT-4.1      | $2.00 / $8.00         | Claude Sonnet 4.6  | $3.00 / $15.00 | OpenAI 43% cheaper  |
| GPT-4.1 Mini | $0.40 / $1.60         | Nova Lite          | $0.06 / $0.24  | Bedrock 85% cheaper |
| GPT-4.1 Nano | $0.10 / $0.40         | Nova Micro         | $0.035 / $0.14 | Bedrock 65% cheaper |

### GPT-4o Series

| OpenAI Model | Price (in/out per 1M) | Best Bedrock Match | Bedrock Price  | Winner              |
| ------------ | --------------------- | ------------------ | -------------- | ------------------- |
| GPT-4o       | $2.50 / $10.00        | Claude Sonnet 4.6  | $3.00 / $15.00 | OpenAI 29% cheaper  |
| GPT-4o Mini  | $0.15 / $0.60         | Nova Lite          | $0.06 / $0.24  | Bedrock 60% cheaper |

### Reasoning Models (o-series)

> **Lifecycle note:** Nova Premier v1 is **Legacy** (EOL Sep 14, 2026). Table below uses Nova 2 Pro (Preview) as the Active replacement.

| OpenAI Model                | Price (in/out per 1M) | Best Bedrock Match   | Bedrock Price  | Winner              |
| --------------------------- | --------------------- | -------------------- | -------------- | ------------------- |
| o1-pro                      | $150.00 / $600.00     | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 98% cheaper |
| o3-pro                      | $20.00 / $80.00       | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 87% cheaper |
| o1                          | $15.00 / $60.00       | Nova 2 Pro (Preview) | $1.38 / $11.00 | Bedrock 83% cheaper |
| o3                          | $2.00 / $8.00         | DeepSeek-R1          | $1.35 / $5.40  | Bedrock 32% cheaper |
| o4-mini / o3-mini / o1-mini | $1.10 / $4.40         | Claude Sonnet 4.6    | $3.00 / $15.00 | OpenAI 69% cheaper  |

### Legacy Models

| OpenAI Model  | Price (in/out per 1M) | Best Bedrock Match | Bedrock Price  | Winner                                    |
| ------------- | --------------------- | ------------------ | -------------- | ----------------------------------------- |
| GPT-4 Turbo   | $10.00 / $30.00       | Claude Sonnet 4.6  | $3.00 / $15.00 | Bedrock 58% cheaper                       |
| GPT-4         | $30.00 / $60.00       | Claude Sonnet 4.6  | $3.00 / $15.00 | Bedrock 82% cheaper                       |
| GPT-3.5 Turbo | $0.50 / $1.50         | Llama 4 Maverick   | $0.24 / $0.97  | Bedrock 42% cheaper + much better quality |

### OpenAI Models on Bedrock (gpt-oss)

OpenAI's open-source models are available directly on Bedrock, enabling migration without switching model families:

| OpenAI Model | Price (in/out per 1M) | Bedrock gpt-oss | Bedrock Price | Notes                                 |
| ------------ | --------------------- | --------------- | ------------- | ------------------------------------- |
| GPT-4o Mini  | $0.15 / $0.60         | gpt-oss-120b    | $0.15 / $0.60 | Same cost, runs on AWS infrastructure |
| GPT-5 Nano   | $0.05 / $0.40         | gpt-oss-20b     | $0.07 / $0.30 | Similar budget tier on AWS            |

This path avoids model-family risk: the application stays on OpenAI-architecture models while consolidating on AWS infrastructure.

_Percentages are blended savings using a 2:1 input-to-output token ratio. Actual savings depend on your input/output ratio._

---

## Migration Decision Framework

**Migrate to Bedrock if:**

- Using GPT-5.5 flagship → Bedrock 17% cheaper on output via Opus 4.6 ($5/$25 vs $5/$30); Sonnet 4.6 is 53% cheaper
- Using Pro/expensive models (GPT-5.5 Pro, GPT-5.4 Pro, o1-pro) → 87-98% savings via Nova 2 Pro
- Using Mini/Nano models at high volume → 87-94% savings via Nova Lite/Micro
- Using legacy GPT-4/3.5 → 42-82% savings
- Need AWS infrastructure integration
- Need prompt caching (Claude only, 90% savings on cached content)
- Using o3 for reasoning → DeepSeek-R1 on Bedrock is 32% cheaper
- Want to stay on OpenAI models → gpt-oss on Bedrock (same models, AWS infrastructure)

**Consider staying on OpenAI if:**

- Using GPT-5.5 for omnimodal (audio/video) → Claude is text+image only; GPT-5.5 has native audio/video
- Using GPT-5.4 flagship → only 5% cheaper than Sonnet 4.6; marginal either way
- Using mid-tier flagships (GPT-5, GPT-4.1, o3, o4-mini) → OpenAI 29-69% cheaper
- Low volume (<$500/mo) where absolute savings are small
- Heavily integrated with OpenAI ecosystem (Assistants API, gpt-image, Whisper, Realtime)
- Need Realtime API (no Bedrock equivalent)

**Analyze carefully:** Calculate actual token usage x model-specific pricing. Small % differences matter at scale.

---

## Feature Migration

| OpenAI Feature       | Bedrock Equivalent                       | Notes                                                                                                                          |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| OpenAI SDK (direct)  | Mantle OpenAI-compat endpoints           | Zero code changes — set `OPENAI_BASE_URL` + API key + model ID                                                                 |
| Function calling     | Claude tools (excellent, similar format) | Minimal changes (works via Mantle or Converse API)                                                                             |
| Streaming            | All major models                         | Verify gateway format                                                                                                          |
| Vision (GPT-4V)      | Claude Sonnet/Haiku, Llama 4 Maverick    | 70-95% cheaper                                                                                                                 |
| Embeddings (ada-002) | Titan Embeddings ($0.02/1M, 1536 dims)   | Must re-embed all docs                                                                                                         |
| DALL-E / gpt-image   | Nova Canvas ($0.04-$0.08/img)            | DALL-E EOL May 12, 2026; OpenAI replacement is gpt-image-1.5; Titan Image Gen v2 is Legacy (EOL Jun 30, 2026); use Nova Canvas |
| Whisper (STT)        | Amazon Transcribe ($0.024/min)           | 4x more expensive but more features                                                                                            |
| TTS                  | Amazon Polly                             | Different pricing model                                                                                                        |
| Assistants API       | See Assistants API decision tree below   | Path depends on which Assistants features are used — see decision tree                                                         |
| JSON mode            | Claude (excellent), Nova Pro (good)      | Most models via prompt                                                                                                         |
| Realtime API         | No equivalent                            | Stay on OpenAI for this                                                                                                        |

---

## Common Migration Paths

### OpenAI SDK → Mantle (minimal code changes)

If the application uses the OpenAI Python/JS SDK directly (`from openai import OpenAI` / `new OpenAI()`), Bedrock's [Mantle OpenAI-compatible endpoints](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html) allow migration with minimal code changes — primarily environment variables plus a model string swap:

1. Set `OPENAI_BASE_URL=https://bedrock-mantle.{region}.api.aws/v1`
2. Set `OPENAI_API_KEY=<bedrock-api-key>` — use a Bedrock API key, **not** your existing OpenAI API key
3. Change model string (e.g., `gpt-5.4` → `anthropic.claude-sonnet-4-6` or `openai.gpt-oss-120b`)

**Hard gates before recommending Mantle:**

- **Model compatibility:** Verify the selected Bedrock model supports the Responses API — [check API compatibility](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html). Not all models do. Do not recommend Mantle Responses API unless the target model is confirmed compatible.
- **Region availability:** Mantle is available in 13 regions (us-east-1, us-east-2, us-west-2, ap-northeast-1, ap-south-1, ap-southeast-2, ap-southeast-3, eu-central-1, eu-west-1, eu-west-2, eu-south-1, eu-north-1, sa-east-1). If the target region is outside this list, do not recommend Mantle — use the boto3 Converse API path instead.

Supports Chat Completions API, Responses API, streaming, and stateful conversations.

**Responses API capabilities (when stateful conversations matter):**

- **Stateful conversation management** — Bedrock rebuilds context automatically; no need to pass full conversation history on each request
- **Async / long-running inference** — background processing for workloads that exceed typical request timeouts (useful for complex agentic tasks)
- **Streaming + non-streaming** — both modes supported via the same endpoint

### Assistants API → Migration Decision Tree

Assistants API and Responses API are different surfaces. Do not treat all Assistants API usage as an env-var-only migration. Apply this decision tree:

**1. App already uses OpenAI Responses API** (`responses.create`)
→ Mantle is the cleanest path. Env var swap + model string change. Minimal code changes.

**2. App uses Assistants API only for stateful multi-turn conversation** (no hosted tools, no file search, no code interpreter, no persistent Assistant objects, no complex run lifecycle)
→ Mantle Responses API is viable. Requires migrating from `threads`/`runs` calls to `responses.create` — this is a small API migration (days), not a full redesign. Not a zero-code-change swap.

**3. App uses Assistants API with simple hosted tools** (function calling only, no file search or code interpreter)
→ Mantle Responses API with tool use is viable. Moderate code migration (1-2 weeks) to adapt tool definitions and run lifecycle.

**4. App uses Assistants API with file search, vector stores, code interpreter, persistent Assistant objects, or complex run lifecycle management**
→ Do not recommend Mantle. Evaluate: Bedrock Agents (sessions, action groups, knowledge bases) for full agentic replacement (2-4 week migration), or app-managed orchestration if the team prefers to own state.

**When to prefer Converse API over Mantle:** If you need Bedrock-specific features (Guardrails, Knowledge Bases, prompt caching, Bedrock Agents integration) or your target region doesn't have Mantle. Mantle is the fastest path; Converse API is the most feature-complete path.

### GPT-5.4 → Claude Sonnet 4.6

Near price parity (~5% difference). Migration case is driven by AWS consolidation, agentic reliability, or prompt caching — not cost. Both have ~200K+ context. Low risk.

### GPT-5.4 Mini/Nano → Nova Lite/Micro

87-94% savings. Strong cost case at any volume. Nova Lite (300K context) covers most GPT-5.4 Mini use cases.

### GPT-4/4 Turbo → Claude Sonnet 4.6

70-90% savings, similar or better quality, longer context (200K vs 128K). Low risk.

### GPT-3.5 Turbo → Llama 4 Maverick

Similar cost, dramatically better quality, 1M context (vs 16K).

### GPT-4 → Multi-Model (high spend)

Tier by complexity: simple → Nova Micro/Llama 4 Scout (60%), moderate → Llama 4 Maverick/Nova Pro (30%), complex → Claude Sonnet (10%). 85-95% savings.

### Pro models → Nova 2 Pro

83-98% savings. Strong migration case at any volume. (Nova Premier v1 is Legacy — use Nova 2 Pro instead.)

---

## Volume-Based Recommendations

**Low (<1M tokens/day):** Use best model for quality. Cost difference minimal.

**Medium (1-10M tokens/day):** Present cost comparison at volume. At 5M input + 2.5M output/day, evaluate per-model economics carefully.

**High (10-100M tokens/day):** Multi-model tiered approach recommended. Route by task complexity.

**Very high (>100M tokens/day):** Mandatory tiering:

- Simple tasks (60%) → Nova Micro or Llama 4 Scout
- Moderate tasks (30%) → Llama 4 Maverick or Nova Pro
- Complex tasks (10%) → Claude Sonnet 4.6

---

## OpenAI Pricing Tiers

OpenAI offers 4 tiers: Batch (50% off, 24hr), Flex (30-50% off, higher latency), Standard (baseline), Priority (2x, lowest latency). This guide uses Standard tier for comparison.
