---
name: "sagemaker-ai"
displayName: "Amazon SageMaker AI"
description: "Deploy and train ML models on Amazon SageMaker AI — inference endpoints, LLM fine-tuning, HyperPod clusters, Model Monitor, AutoML with AutoGluon, and SageMaker Python SDK v3 patterns."
keywords: ["sagemaker", "inference", "training", "hyperpod", "model-monitor", "autogluon", "sdk-v3"]
author: "AWS"
---

# When to use this power

When you want to deploy ML models to SageMaker inference endpoints, fine-tune or train models (serverless, Training Jobs, or HyperPod), set up model monitoring, run AutoML with AutoGluon, or write correct SageMaker Python SDK v3 code.

# When to Load Steering Files

Whenever you are asked to perform a task related to any of the following scenarios - ensure you load and read the appropriate markdown file mentioned

- Deploying models to SageMaker real-time endpoints (container selection, DJL LMI/vLLM, DLC configuration, multimodal models) -> use `./steering/inference-endpoints.md`
- Fine-tuning or training models (serverless customization, QLoRA/LoRA, GPU vs Trainium, instance sizing) -> use `./steering/training-jobs.md`
- Setting up or managing HyperPod clusters for training (EKS orchestration, Training Operator, Task Governance, resiliency) -> use `./steering/hyperpod.md` — also use MCP tools `manage_hyperpod_stacks` and `manage_hyperpod_cluster_nodes` for cluster operations
- Deploying inference on HyperPod clusters (JumpStart models, custom models from S3/FSx, kubectl CRDs, autoscaling) -> use `./steering/hyperpod-inference.md`
- Setting up model monitoring (Data Quality, Model Quality, Bias, Explainability, baselines, schedules) -> use `./steering/model-monitor.md`
- Using AutoGluon for AutoML (tabular, time series, multimodal, SageMaker Pipelines) -> use `./steering/automl-autogluon.md`
- Writing SageMaker SDK v3 code (correct imports, image_uris, deployment patterns, invocation) -> use `./steering/sdk-v3-reference.md`

# Available MCP Tools

This power integrates with the [Amazon SageMaker AI MCP Server](https://github.com/awslabs/mcp/tree/main/src/sagemaker-ai-mcp-server) (Apache-2.0 license) for HyperPod cluster management.

## manage_hyperpod_stacks

Orchestrates HyperPod cluster infrastructure via CloudFormation.

- `operation="describe"` — Describe existing HyperPod CloudFormation stacks (read-only)
- `operation="deploy"` — Deploy a new HyperPod cluster via managed CloudFormation templates (requires `--allow-write`)
- `operation="delete"` — Delete a HyperPod CloudFormation stack and its resources (requires `--allow-write`)

Parameters: `operation`, `stack_name`, `region_name`, `profile_name`, `params_file` (for deploy)

**Safety**: Only modifies/deletes stacks originally created by this tool.

## manage_hyperpod_cluster_nodes

Manages cluster nodes within HyperPod deployments.

- `operation="list_clusters"` — List HyperPod clusters with filtering by name, creation time, training plan ARN
- `operation="list_nodes"` — List nodes in a cluster with filtering by instance group
- `operation="describe_node"` — Get detailed info about a specific node
- `operation="update_software"` — Update AMIs for all nodes or specific instance groups (requires `--allow-write`)
- `operation="batch_delete"` — Delete multiple nodes in a single operation (requires `--allow-write`)

Parameters: `operation`, `cluster_name`, `node_id` (for describe_node), `node_ids` (for batch_delete)

# Onboarding

1. **Ensure the user has valid AWS Credentials** These are used to interact with SageMaker and related AWS services.
2. **Verify AWS CLI access** Using `aws sts get-caller-identity`
3. **Check Python and SDK version** SageMaker Python SDK v3 requires Python <= 3.13. Install with `pip install 'sagemaker>=3'`
4. **Execution role** In SageMaker Studio, always use `get_execution_role()`. Outside Studio, ensure an IAM role with SageMaker permissions is available.
5. **MCP server dependencies** The SageMaker AI MCP server requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (for `uvx` command)

# SDK v3 Guardrails (Always-On)

These rules apply to EVERY piece of SageMaker code. Check each one before generating output.

| Rule | CORRECT | WRONG |
|------|---------|-------|
| Model class import | `from sagemaker.core.resources import Model` | `from sagemaker.model import Model` |
| Session import | `from sagemaker.core.helper.session_helper import Session, get_execution_role` | `from sagemaker import get_execution_role` |
| Deployment (LLMs) | Core API: `Model.create` + `EndpointConfig.create` + `Endpoint.create` | `ModelBuilder` with DJL/vLLM containers |
| Deployment (simple) | `ModelBuilder` + `SchemaBuilder` | V2 `Model.deploy()` |
| JumpStart deploy | `ModelBuilder(model="<model-id>")` | `JumpStartModel` (removed in V3) |
| Processing imports | `from sagemaker.core.processing import ...` | `from sagemaker.processing import ...` |
| Transformer import | `from sagemaker.core.transformer import Transformer` | `from sagemaker.transformer import Transformer` |
| Pipeline imports | `sagemaker.mlops.workflow.*` + `sagemaker.core.workflow.*` | `sagemaker.workflow.*` (V2, removed) |
| Python version | <= 3.13 | 3.14+ (SDK v3 incompatible) |
| DLC images source | `https://aws.github.io/deep-learning-containers/reference/available_images/` | HuggingFace docs (outdated) |

# Quick Reference

## SDK v3 Core API (Recommended for DJL/vLLM)

```python
from sagemaker.core.resources import Model, EndpointConfig, Endpoint
from sagemaker.core.shapes.shapes import ContainerDefinition, ProductionVariant
```

## SDK v3 ModelBuilder (For JumpStart / simple HF models)

```python
from sagemaker.serve import ModelBuilder
from sagemaker.serve.builder.schema_builder import SchemaBuilder
```

## Container Decision Tree

1. Standard text LLM (Llama, Mistral, Qwen) -> DJL LMI with vLLM backend
2. Multimodal/Vision model (Idefics3, LLaVA, Qwen-VL) -> DJL LMI with vLLM backend
3. Simple HF pipeline model (classification, NER) -> HuggingFace Inference DLC
4. Custom model with custom handler -> HuggingFace Inference DLC + custom inference.py in model.tar.gz

## CUDA Compatibility

| Instance Family | GPU | Max CUDA | Recommended DLC |
|---|---|---|---|
| ml.g5.* | A10G (24GB) | cu128 | `djl-inference:0.36.0-lmi20.0.0-cu128` |
| ml.g6.* | L4 (24GB) | cu129 | `djl-inference:0.36.0-lmi22.0.0-cu129` |
| ml.p5.* | H100 (80GB) | cu129 | `djl-inference:0.36.0-lmi22.0.0-cu129` |

Note: cu129 fails on g5 due to driver version mismatch, not CUDA compute capability. Always check the DLC images page for the latest versions — the versions above are examples.

## Reference Repositories

- Inference hosting examples (Llama, Mistral, Mixtral, Falcon, CodeLlama): `https://github.com/aws-samples/sagemaker-genai-hosting-examples`
- Model customization recipes (QLoRA, Spectrum, Full FT, DPO, GRPO): `https://github.com/aws-samples/amazon-sagemaker-generativeai/tree/main/0_model_customization_recipes`

## Latest DLC Images

Always check the latest images at:
`https://aws.github.io/deep-learning-containers/reference/available_images/`

Do NOT rely on the HuggingFace docs page — it is outdated.

# Best Practices

- Always use `get_execution_role()` in SageMaker Studio — don't hardcode role ARNs
- Set `ContainerStartupHealthCheckTimeoutInSeconds=900` for models that download from HuggingFace Hub at startup
- Clean up endpoints after testing — they cost money even when idle
- Use `dependencies={"auto": False}` with ModelBuilder to avoid capturing local packages that break the DLC
- For first invocation after deploy, add retry logic or a warm-up wait — models load lazily on first request

# Troubleshooting

## SDK v3 Import Errors

**Error**: `ImportError: cannot import name 'Model' from 'sagemaker.model'`
**Cause**: Using SDK v2 import paths
**Solution**: Use `from sagemaker.core.resources import Model` — see SDK v3 Guardrails table above

## Endpoint Creation Timeout

**Error**: Endpoint stays in `Creating` status and eventually fails
**Cause**: Model too large for instance, or container startup timeout too low
**Solution**:
1. Check model memory requirements against instance GPU memory
2. Set `ContainerStartupHealthCheckTimeoutInSeconds=900` (or higher for very large models)
3. Verify CUDA compatibility — see CUDA Compatibility table

## ModelBuilder Issues

**Error**: `ModelBuilder.build()` fails with dependency errors
**Cause**: Local packages captured by auto-dependency detection
**Solution**: Use `dependencies={"auto": False}` and manage dependencies explicitly

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
