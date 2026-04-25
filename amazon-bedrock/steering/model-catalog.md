# Bedrock Model Catalog and CRIS Inference Profiles

## How to Choose a Model

1. **Determine your modality**: text-only, multimodal (image/video/document), embeddings, image generation, speech
2. **Pick quality tier**: best quality (Opus), balanced (Sonnet/Pro), fast+cheap (Haiku/Lite/Micro)
3. **Always use CRIS inference profiles** for invocation — better throughput and automatic failover

## Cross-Region Inference (CRIS)

CRIS routes requests across multiple AWS regions transparently. Use inference profile IDs instead of base model IDs.

### CRIS Prefix Types

| Prefix | Regions Included | Pricing | Use When |
|--------|-----------------|---------|----------|
| `us.` | us-east-1, us-west-2, us-east-2, etc. | Standard | Data must stay in US |
| `eu.` | eu-west-1, eu-central-1, etc. | Standard | Data must stay in EU |
| `apac.` | ap-northeast-1, ap-southeast-1, etc. | Standard | Data must stay in APAC |
| `global.` | All commercial regions worldwide | ~10% savings | Maximum throughput, no data residency constraints |

### How to Use CRIS

Pass the inference profile ID as the `modelId` parameter — no other code changes needed:

```python
# Single-region (lower throughput, no failover)
response = client.converse(modelId="anthropic.claude-sonnet-4-6", ...)

# CRIS US (automatic failover across US regions)
response = client.converse(modelId="us.anthropic.claude-sonnet-4-6", ...)

# CRIS Global (maximum throughput, ~10% savings)
response = client.converse(modelId="global.anthropic.claude-sonnet-4-6", ...)
```

### Monitoring CRIS

Track which region served each request via CloudTrail:
- Field: `additionalEventData.inferenceRegion`

### CRIS Limitations

- Provisioned Throughput is NOT supported with inference profiles
- Model Customization outputs (fine-tuned models) cannot use CRIS
- Not all models have CRIS profiles — check the tables below

## Anthropic Claude Models

| Model | Base Model ID | US CRIS | Global CRIS |
|-------|--------------|---------|-------------|
| Claude Opus 4.6 | `anthropic.claude-opus-4-6-v1` | `us.anthropic.claude-opus-4-6-v1` | `global.anthropic.claude-opus-4-6-v1` |
| Claude Sonnet 4.6 | `anthropic.claude-sonnet-4-6` | `us.anthropic.claude-sonnet-4-6` | `global.anthropic.claude-sonnet-4-6` |
| Claude Opus 4.5 | `anthropic.claude-opus-4-5-20251101-v1:0` | `us.anthropic.claude-opus-4-5-20251101-v1:0` | `global.anthropic.claude-opus-4-5-20251101-v1:0` |
| Claude Sonnet 4.5 | `anthropic.claude-sonnet-4-5-20250929-v1:0` | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| Claude Opus 4.1 | `anthropic.claude-opus-4-1-20250805-v1:0` | `us.anthropic.claude-opus-4-1-20250805-v1:0` | — |
| Claude Opus 4 | `anthropic.claude-opus-4-20250514-v1:0` | `us.anthropic.claude-opus-4-20250514-v1:0` | — |
| Claude Sonnet 4 | `anthropic.claude-sonnet-4-20250514-v1:0` | `us.anthropic.claude-sonnet-4-20250514-v1:0` | `global.anthropic.claude-sonnet-4-20250514-v1:0` |
| Claude Haiku 4.5 | `anthropic.claude-haiku-4-5-20251001-v1:0` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Claude 3.7 Sonnet | `anthropic.claude-3-7-sonnet-20250219-v1:0` | `us.anthropic.claude-3-7-sonnet-20250219-v1:0` | — |
| Claude 3.5 Sonnet v2 | `anthropic.claude-3-5-sonnet-20241022-v2:0` | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` | — |
| Claude 3.5 Haiku | `anthropic.claude-3-5-haiku-20241022-v1:0` | `us.anthropic.claude-3-5-haiku-20241022-v1:0` | — |
| Claude 3 Haiku | `anthropic.claude-3-haiku-20240307-v1:0` | `us.anthropic.claude-3-haiku-20240307-v1:0` | — |
| Claude 3 Opus | `anthropic.claude-3-opus-20240229-v1:0` | `us.anthropic.claude-3-opus-20240229-v1:0` | — |

**Recommendation**: Use Claude Opus 4.6 for best quality, Sonnet 4.6 for balanced quality/speed, Haiku 4.5 for fast/cheap.

## Amazon Nova Models

| Model | Base Model ID | US CRIS | Global CRIS | Modality |
|-------|--------------|---------|-------------|----------|
| Nova Premier | `amazon.nova-premier-v1:0` | `us.amazon.nova-premier-v1:0` | — | TEXT,IMAGE,VIDEO->TEXT |
| Nova Pro | `amazon.nova-pro-v1:0` | `us.amazon.nova-pro-v1:0` | — | TEXT,IMAGE,VIDEO->TEXT |
| Nova Lite | `amazon.nova-lite-v1:0` | `us.amazon.nova-lite-v1:0` | — | TEXT,IMAGE,VIDEO->TEXT |
| Nova Micro | `amazon.nova-micro-v1:0` | `us.amazon.nova-micro-v1:0` | — | TEXT->TEXT |
| Nova 2 Lite | `amazon.nova-2-lite-v1:0` | `us.amazon.nova-2-lite-v1:0` | `global.amazon.nova-2-lite-v1:0` | TEXT,IMAGE,VIDEO->TEXT |
| Nova Canvas | `amazon.nova-canvas-v1:0` | — | — | TEXT,IMAGE->IMAGE |
| Nova Reel v1.1 | `amazon.nova-reel-v1:1` | — | — | TEXT,IMAGE->VIDEO |
| Nova Sonic | `amazon.nova-sonic-v1:0` | — | — | SPEECH->SPEECH,TEXT |
| Nova 2 Sonic | `amazon.nova-2-sonic-v1:0` | — | — | SPEECH->SPEECH,TEXT |

## Meta Llama Models

| Model | Base Model ID | US CRIS |
|-------|--------------|---------|
| Llama 4 Maverick 17B | `meta.llama4-maverick-17b-instruct-v1:0` | `us.meta.llama4-maverick-17b-instruct-v1:0` |
| Llama 4 Scout 17B | `meta.llama4-scout-17b-instruct-v1:0` | `us.meta.llama4-scout-17b-instruct-v1:0` |
| Llama 3.3 70B | `meta.llama3-3-70b-instruct-v1:0` | `us.meta.llama3-3-70b-instruct-v1:0` |
| Llama 3.2 90B (vision) | `meta.llama3-2-90b-instruct-v1:0` | `us.meta.llama3-2-90b-instruct-v1:0` |
| Llama 3.2 11B (vision) | `meta.llama3-2-11b-instruct-v1:0` | `us.meta.llama3-2-11b-instruct-v1:0` |
| Llama 3.2 3B | `meta.llama3-2-3b-instruct-v1:0` | `us.meta.llama3-2-3b-instruct-v1:0` |
| Llama 3.2 1B | `meta.llama3-2-1b-instruct-v1:0` | `us.meta.llama3-2-1b-instruct-v1:0` |
| Llama 3.1 70B | `meta.llama3-1-70b-instruct-v1:0` | `us.meta.llama3-1-70b-instruct-v1:0` |
| Llama 3.1 8B | `meta.llama3-1-8b-instruct-v1:0` | `us.meta.llama3-1-8b-instruct-v1:0` |

## Mistral AI Models

| Model | Base Model ID | US CRIS |
|-------|--------------|---------|
| Mistral Large 3 675B | `mistral.mistral-large-3-675b-instruct` | — |
| Devstral 2 123B | `mistral.devstral-2-123b` | — |
| Pixtral Large (vision) | `mistral.pixtral-large-2502-v1:0` | `us.mistral.pixtral-large-2502-v1:0` |
| Magistral Small | `mistral.magistral-small-2509` | — |
| Voxtral Small 24B (speech) | `mistral.voxtral-small-24b-2507` | — |
| Voxtral Mini 3B (speech) | `mistral.voxtral-mini-3b-2507` | — |

## DeepSeek Models

| Model | Base Model ID | US CRIS |
|-------|--------------|---------|
| DeepSeek-R1 | `deepseek.r1-v1:0` | `us.deepseek.r1-v1:0` |
| DeepSeek V3.2 | `deepseek.v3.2` | — |

## Other Notable Models

| Model | Base Model ID | Type |
|-------|--------------|------|
| Cohere Embed v4 | `cohere.embed-v4:0` | TEXT,IMAGE->EMBEDDING |
| Cohere Rerank 3.5 | `cohere.rerank-v3-5:0` | Reranking |
| Titan Text Embeddings V2 | `amazon.titan-embed-text-v2:0` | TEXT->EMBEDDING |
| Titan Multimodal Embeddings | `amazon.titan-embed-image-v1:0` | TEXT,IMAGE->EMBEDDING |
| Qwen3 32B | `qwen.qwen3-32b-v1:0` | TEXT->TEXT |
| Qwen3 Coder 30B | `qwen.qwen3-coder-30b-a3b-v1:0` | TEXT->TEXT |
| Qwen3 VL 235B (vision) | `qwen.qwen3-vl-235b-a22b` | TEXT,IMAGE->TEXT |
| NVIDIA Nemotron Super 120B | `nvidia.nemotron-super-3-120b` | TEXT->TEXT |
| MiniMax M2.5 | `minimax.minimax-m2.5` | TEXT,IMAGE->TEXT |
| Google Gemma 3 27B | `google.gemma-3-27b-it` | TEXT,IMAGE->TEXT |
| Kimi K2.5 | `moonshotai.kimi-k2.5` | TEXT->TEXT |
| GLM 5 | `zai.glm-5` | TEXT->TEXT |
| AI21 Jamba 1.5 Large | `ai21.jamba-1-5-large-v1:0` | TEXT->TEXT |
| Writer Palmyra X5 | `writer.palmyra-x5-v1:0` | TEXT->TEXT |

## Embedding Models for Knowledge Bases

| Model | Dimensions | Modality | Use Case |
|-------|-----------|----------|----------|
| Titan Text Embeddings V2 | 256/512/1024 | Text | Default for text-only KB |
| Titan Multimodal Embeddings | 256/384/1024 | Text+Image | KB with images |
| Cohere Embed v4 | 256/384/512/1024 | Text+Image | High-quality semantic search |
| Nova Multimodal Embeddings | 256/512/1024 | Text+Image+Audio+Video | Multimodal KB |

## Listing Models Programmatically

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")

# List all foundation models
models = bedrock.list_foundation_models()["modelSummaries"]
for m in models:
    print(f"{m['modelId']} — {m['modelName']} ({m['providerName']})")

# List CRIS inference profiles
profiles = bedrock.list_inference_profiles(typeEquals="SYSTEM_DEFINED")["inferenceProfileSummaries"]
for p in profiles:
    print(f"{p['inferenceProfileId']} — {p['inferenceProfileName']}")
```

## Important Notes

- **Model access must be enabled** in the Bedrock console before use. Go to Model Access -> Manage model access.
- **Some models require EULA acceptance** (e.g., Meta Llama, Mistral).
- **Not all models support all features** — check Converse API compatibility per model.
- **Model IDs with version suffixes** (`:0`, `:0:24k`) indicate context window variants.
- **This catalog reflects models available as of 2025-03-25** — use `aws bedrock list-foundation-models` for the latest.
