---
name: "amazon-bedrock"
displayName: "Amazon Bedrock"
description: "Build generative AI applications on Amazon Bedrock — model invocation via Converse API, cross-region inference (CRIS), agents, knowledge bases (RAG), guardrails, model customization, prompt management, and flows."
keywords: ["bedrock", "converse", "cris", "inference-profile", "knowledge-base", "guardrails", "agents", "fine-tuning"]
author: "AWS"
---

# When to use this power

When you want to invoke foundation models on Amazon Bedrock, build RAG applications with Knowledge Bases, create autonomous agents, apply content safeguards with Guardrails, fine-tune or distill models, manage reusable prompts, or orchestrate multi-step AI workflows with Flows.

# When to Load Steering Files

Whenever you are asked to perform a task related to any of the following scenarios - ensure you load and read the appropriate markdown file mentioned

- Looking up model IDs, CRIS inference profile IDs, or choosing which model to use -> use `./steering/model-catalog.md`
- Invoking models via Converse API, streaming, tool use, prompt caching, multimodal inputs -> use `./steering/converse-api.md`
- Building or configuring Bedrock Agents with action groups, Lambda functions, or return control -> use `./steering/agents.md`
- Setting up Knowledge Bases for RAG, vector stores, data sources, or querying indexed data -> use `./steering/knowledge-bases.md` — also use MCP tools `ListKnowledgeBases` and `QueryKnowledgeBases` for querying
- Configuring Guardrails for content filtering, PII protection, topic denial, or grounding checks -> use `./steering/guardrails.md`
- Fine-tuning, reinforcement fine-tuning, distilling, or importing custom models -> use `./steering/model-customization.md` — also use MCP tools for custom model import management
- Creating reusable prompts, prompt versions, or orchestrating multi-step Flows -> use `./steering/prompts-and-flows.md`

# Available MCP Tools

This power integrates with two MCP servers from [awslabs/mcp](https://github.com/awslabs/mcp) (Apache-2.0 license).

## Knowledge Base Retrieval (awslabs.bedrock-kb-retrieval-mcp-server)

- `ListKnowledgeBases()` — List all available knowledge bases and their data sources
- `QueryKnowledgeBases(query, knowledge_base_id, number_of_results, reranking, reranking_model_name, data_source_ids)` — Search a knowledge base with optional reranking (AMAZON or COHERE model)

**Prerequisites**: Knowledge bases must be tagged with key `mcp-multirag-kb=true` (configurable via `KB_INCLUSION_TAG_KEY` env var). IAM permissions: `bedrock-agent:Retrieve`, `bedrock-agent:ListKnowledgeBases`, `bedrock-agent:GetKnowledgeBase`.

## Custom Model Import (awslabs.aws-bedrock-custom-model-import-mcp-server)

- `create_model_import_job(jobName, importedModelName, roleArn, modelDataSource)` — Import a custom model into Bedrock (requires `--allow-write`)
- `list_model_import_jobs()` — List existing import jobs with filters
- `get_model_import_job(job_identifier)` — Get import job details
- `list_imported_models()` — List successfully imported models
- `get_imported_model(model_identifier)` — Get imported model details
- `delete_imported_model(model_identifier)` — Delete an imported model (requires `--allow-write`)

**Prerequisites**: S3 bucket with model files. Set `BEDROCK_MODEL_IMPORT_S3_BUCKET` env var.

# Onboarding

1. **Ensure the user has valid AWS Credentials** These are used to interact with Bedrock and related AWS services.
2. **Verify AWS CLI access** Using `aws sts get-caller-identity`
3. **Enable model access** In the Bedrock console, go to Model Access and request access to the models you need. Some models require acceptance of EULAs.
4. **MCP server dependencies** Both MCP servers require [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (for `uvx` command)
5. **For Knowledge Base MCP** Tag your knowledge bases with `mcp-multirag-kb=true` (or your custom tag key)

# Model Invocation Guardrails (Always-On)

These rules apply to EVERY Bedrock model invocation. Check each one before generating code.

| Rule | CORRECT | WRONG |
|------|---------|-------|
| API for conversations | `bedrock_runtime.converse()` or `converse_stream()` | `invoke_model()` with raw JSON payloads |
| Client for invocation | `boto3.client('bedrock-runtime')` | `boto3.client('bedrock')` (management only) |
| Client for agents/KB | `boto3.client('bedrock-agent')` (build) + `boto3.client('bedrock-agent-runtime')` (invoke) | Mixing build and runtime clients |
| CRIS model IDs | `us.anthropic.claude-sonnet-4-6` | `anthropic.claude-sonnet-4-6` (single-region, lower throughput) |
| Latest Claude models | Opus 4.6: `anthropic.claude-opus-4-6-v1`, Sonnet 4.6: `anthropic.claude-sonnet-4-6` | Old model IDs like `claude-v2`, `claude-instant` |
| Streaming | `converse_stream()` returns event stream, iterate with `for event in response['stream']` | Treating stream response as complete response |
| Tool use | Define in `toolConfig.tools`, handle `stopReason='tool_use'` | Ignoring tool_use stop reason |
| System prompts | Pass as `system=[{"text": "..."}]` parameter | Including system prompt in user message |
| Inference config | `inferenceConfig={"maxTokens": N, "temperature": T}` | Model-specific parameter names in wrong field |

# Quick Reference

## Recommended Models (2025)

| Use Case | Model | CRIS Profile ID |
|----------|-------|-----------------|
| Best quality (text) | Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1` |
| Best balance | Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` |
| Fast + cheap | Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Multimodal (text+image+video) | Nova Pro | `us.amazon.nova-pro-v1:0` |
| Best multimodal quality | Nova Premier | `us.amazon.nova-premier-v1:0` |
| Code generation | Claude Sonnet 4.6 or Devstral 2 | `us.anthropic.claude-sonnet-4-6` |
| Embeddings (text) | Titan Text Embeddings V2 | N/A (single-region) |
| Embeddings (multimodal) | Cohere Embed v4 | `us.cohere.embed-v4:0` |
| Image generation | Nova Canvas | N/A |
| Video generation | Nova Reel v1.1 | N/A |
| Speech-to-speech | Nova Sonic | N/A |

## CRIS Prefix Reference

| Prefix | Scope | Pricing |
|--------|-------|---------|
| `us.` | US regions only (us-east-1, us-west-2, etc.) | Standard |
| `eu.` | EU regions only | Standard |
| `apac.` | Asia Pacific regions | Standard |
| `global.` | All commercial regions worldwide | ~10% savings |
| (none) | Single region, no routing | Standard |

**Always use CRIS profiles** (`us.*` or `global.*`) for production workloads — they provide automatic failover and higher throughput at no extra cost (or savings for global).

## Minimal Converse Example

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[{"role": "user", "content": [{"text": "Hello!"}]}],
    inferenceConfig={"maxTokens": 1024, "temperature": 0.7},
)

print(response["output"]["message"]["content"][0]["text"])
```

# Best Practices

- **Always use CRIS inference profiles** for production — pass `us.` or `global.` prefixed model IDs as `modelId`
- **Use Converse API** instead of `invoke_model()` — unified interface, no model-specific payloads
- **Enable streaming** (`converse_stream()`) for user-facing applications — reduces time to first token
- **Include full conversation history** in each `converse()` call — Bedrock is stateless
- **Clean up resources** — delete endpoints, knowledge bases, and agents when no longer needed
- **Tag resources** for cost tracking and access control
- **Use Guardrails** for any user-facing application — content filtering + PII protection at minimum

# Troubleshooting

## AccessDeniedException on model invocation

**Error**: `You don't have access to the model with the specified model ID`
**Cause**: Model access not enabled in Bedrock console
**Solution**: Go to Bedrock console -> Model Access -> Request access for the model. Some models require EULA acceptance.

## ThrottlingException

**Error**: `Rate exceeded` or `Too many requests`
**Cause**: Hitting on-demand throughput limits in a single region
**Solution**: Switch to CRIS inference profiles (`us.*` or `global.*`) to distribute load across regions

## ValidationException with Converse API

**Error**: `Malformed input request`
**Cause**: Usually wrong content block format or missing required fields
**Solution**: Ensure messages follow `[{"role": "user", "content": [{"text": "..."}]}]` structure. System prompts go in `system` parameter, not in messages.

# Integrations

This power integrates with:
- [`awslabs.bedrock-kb-retrieval-mcp-server`](https://github.com/awslabs/mcp/tree/main/src/bedrock-kb-retrieval-mcp-server) | Apache-2.0 license
- [`awslabs.aws-bedrock-custom-model-import-mcp-server`](https://github.com/awslabs/mcp/tree/main/src/aws-bedrock-custom-model-import-mcp-server) | Apache-2.0 license

# License

```
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```
