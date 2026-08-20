# Bedrock Model Selection (mapping only — no pricing)

Distilled from the migration-to-aws plugin's Q16/Q17 tables and `ai-model-lifecycle.md`.
**Source:** `clarify-ai.md` (Q16/Q17)

- `ai-model-lifecycle.md`. Last aligned: 2026-06-30.

This is a **coarse, family-level** mapping. Exact model IDs, pricing, TCO, EOL dates, and
regional availability come from **migration-to-aws (the llm-to-bedrock skill)** — never quote dollar figures
here. The deterministic implementation lives in `agent-advisor-scoring.py::_select_model`; the drift
test in `awslabs/startups:migrate/plugins/migration-to-aws/skills/agent-advisor/scripts/test_scoring.py` locks this list against the source lifecycle file (a source
model going Legacy/EOL fails CI).

Model choice is **independent of runtime choice** — it never changes which runtime is selected.

## Priority baseline (Q16)

| priority           | model                                                         |
| ------------------ | ------------------------------------------------------------- |
| quality            | Claude Sonnet 4.6 (Opus 4.7 for the most demanding reasoning) |
| balanced / unknown | Claude Sonnet 4.6                                             |
| speed              | Claude Haiku 4.5 (Nova Micro/Lite for cost-optimized speed)   |
| cost               | Claude Haiku 4.5 or Nova Micro                                |

## Specialized-feature override (Q17 — HARD override, beats priority)

Ask for the ONE most critical feature. It overrides the priority baseline (and, on the migrate
path, the source-model family mapping).

| feature           | primary model                                             | notes / alternates                                                                          |
| ----------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| tool_use          | Claude Sonnet 4.6                                         | best-in-class tool use                                                                      |
| long_context      | Llama 4 Scout (10M native)                                | Claude Sonnet 4.6 for shorter long-context; Nova 2 Pro (1M) only if GA                      |
| extended_thinking | Claude Sonnet 4.6 (extended thinking)                     | Opus 4.7 for hardest                                                                        |
| rag               | Claude Sonnet 4.6 + Bedrock Knowledge Bases               | Titan Embeddings v2                                                                         |
| multimodal        | Claude Sonnet 4.6 (vision)                                | add Stability AI if also _generating_ images                                                |
| image_generation  | Stability AI — Stable Image Core (cost) / Ultra (quality) | separate capability, not a text-model swap; see llm-to-bedrock                              |
| speech            | Amazon Nova 2 Sonic (speech-to-speech)                    | Transcribe (STT) / Polly (TTS) for one-directional; separate capability, see llm-to-bedrock |
| embedding         | Amazon Titan Embeddings v2                                |                                                                                             |
| none / unknown    | (no override — priority baseline stands)                  |                                                                                             |

**Active models only** (per the source lifecycle file). Do NOT recommend Nova Sonic v1 (→ Nova 2
Sonic) or Nova Canvas v1 (→ Stability AI) — both are Legacy/excluded.

## Cost/speed conflict

If a feature override selects a specialized model that contradicts a `cost`/`speed` priority
(e.g. cost + speech → Nova 2 Sonic), note in the recommendation that the specialized model may
not be the cheapest/fastest option, and that detailed pricing is downstream. Informational only.

## Migrate path

Record the source model (`migration_from`). The feature override wins; only fall back to the
coarse source→family mapping (gpt4o → Claude Sonnet 4.6 family, gemini_flash → Nova Lite, etc.)
when there is no feature override. Detailed pricing/TCO → migration-to-aws (llm-to-bedrock skill).
