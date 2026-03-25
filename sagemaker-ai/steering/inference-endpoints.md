# Inference Endpoints on SageMaker AI

## Reference Repository

For working deployment examples of popular open-source models on SageMaker (Llama, Mistral, Mixtral, Falcon, CodeLlama, etc.), see:
`https://github.com/aws-samples/sagemaker-genai-hosting-examples`

This repo covers DJL LMI, TGI, Inferentia2 integration, and performance tuning for real-time and async inference.

## Container Selection

### Where to Find Latest DLC Images

The canonical source for AWS Deep Learning Container images is:
`https://aws.github.io/deep-learning-containers/reference/available_images/`

The HuggingFace docs page (`huggingface.co/docs/sagemaker/en/reference`) is outdated and only lists images up to transformers 4.26. Do not use it.

### DJL LMI with vLLM Backend (Recommended for LLMs)

Best for: LLMs, multimodal models, any model supported by vLLM.

Image pattern: `763104351884.dkr.ecr.<region>.amazonaws.com/djl-inference:<version>-lmi<lmi_version>-cu<cuda>`

Key env vars:
- `HF_MODEL_ID` — HuggingFace model ID (e.g., `meta-llama/Llama-3.1-8B-Instruct`)
- `OPTION_ROLLING_BATCH=vllm` — Use vLLM as the inference backend
- `OPTION_DTYPE=fp16` or `bf16` — Model precision (critical for fitting on GPU)
- `OPTION_MAX_MODEL_LEN=4096` — Maximum sequence length
- `OPTION_TENSOR_PARALLEL_DEGREE=1` — Number of GPUs for tensor parallelism

Example:
```python
ContainerDefinition(
    image="763104351884.dkr.ecr.us-east-1.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128",
    environment={
        "HF_MODEL_ID": "meta-llama/Llama-3.1-8B-Instruct",
        "OPTION_ROLLING_BATCH": "vllm",
        "OPTION_DTYPE": "fp16",
        "OPTION_MAX_MODEL_LEN": "4096",
        "OPTION_TENSOR_PARALLEL_DEGREE": "1",
    },
)
```

### HuggingFace Inference DLC

Best for: Simple HF pipeline models (classification, NER, summarization) or models with custom inference.py handlers.

Image pattern: `763104351884.dkr.ecr.<region>.amazonaws.com/huggingface-pytorch-inference:<pt_version>-transformers<tf_version>-gpu-py<py>-cu<cuda>-ubuntu<os>`

Key env vars:
- `HF_MODEL_ID` — HuggingFace model ID
- `HF_MODEL_REVISION` — Git revision (branch, tag, commit)
- `HF_TASK` — Pipeline task (e.g., `text-classification`, `image-to-text`)

Limitations:
- Default handler loads models in FP32 — no env var to override dtype
- For 8B+ models on 24GB GPUs, this will OOM
- Custom `inference.py` must be packaged in `model.tar.gz` at `code/inference.py`
- The `SourceCode` parameter in ModelBuilder does NOT reliably place the handler where the DLC expects it

### HuggingFace vLLM DLC

Image pattern: `763104351884.dkr.ecr.<region>.amazonaws.com/huggingface-vllm:<vllm_version>-transformers<tf_version>-gpu-py<py>-cu<cuda>-ubuntu<os>`

Note: As of the latest release, this DLC only ships with cu129 which does not work on ml.g5 instances. Use the DJL LMI container with vLLM backend instead for g5 instances. Always check the DLC images page for current versions.

### CUDA Version Compatibility

This is critical and easy to get wrong:

| CUDA Version | Works On | Fails On |
|---|---|---|
| cu124 | g5, g6, p5 | — |
| cu128 | g5, g6, p5 | — |
| cu129 | g6, p5 | g5 (driver version mismatch → CannotStartContainerError) |

Note: cu129 failure on g5 is due to the DLC requiring a newer GPU driver than what's installed on g5 instances, not a fundamental CUDA compute capability issue. Inferentia2 (inf2) instances do not use CUDA — use Neuron SDK containers instead.

## SageMaker Python SDK v3

### When to Use ModelBuilder

Use `ModelBuilder` for:
- JumpStart models (pass model ID string like `meta-textgeneration-llama-3-1-8b`)
- Simple HuggingFace models that work with the default pipeline handler

Do NOT use `ModelBuilder` for:
- DJL LMI containers — it overrides the container behavior
- Models that need custom dtype or loading logic
- When you need full control over the container environment

### When to Use Core API Directly

Use `Model.create` + `EndpointConfig.create` + `Endpoint.create` for:
- DJL LMI deployments
- Any deployment where you need full control over the container image and env vars
- When ModelBuilder keeps overriding your settings

```python
from sagemaker.core.resources import Model, EndpointConfig, Endpoint
from sagemaker.core.shapes.shapes import ContainerDefinition, ProductionVariant

# Create model
Model.create(
    model_name="my-model",
    primary_container=ContainerDefinition(
        image=f"763104351884.dkr.ecr.{region}.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128",
        environment={
            "HF_MODEL_ID": "meta-llama/Llama-3.1-8B-Instruct",
            "OPTION_ROLLING_BATCH": "vllm",
            "OPTION_DTYPE": "fp16",
            "OPTION_MAX_MODEL_LEN": "4096",
            "OPTION_TENSOR_PARALLEL_DEGREE": "1",
        },
    ),
    execution_role_arn=role_arn,
)

# Create endpoint config
EndpointConfig.create(
    endpoint_config_name="my-endpoint",
    production_variants=[
        ProductionVariant(
            variant_name="AllTraffic",
            model_name="my-model",
            initial_instance_count=1,
            instance_type="ml.g5.2xlarge",
            initial_variant_weight=1.0,
            container_startup_health_check_timeout_in_seconds=900,
            model_data_download_timeout_in_seconds=900,
        )
    ],
)

# Create endpoint
Endpoint.create(
    endpoint_name="my-endpoint",
    endpoint_config_name="my-endpoint",
)

# Wait for InService
import boto3
sm = boto3.client("sagemaker", region_name=region)
waiter = sm.get_waiter("endpoint_in_service")
waiter.wait(EndpointName="my-endpoint", WaiterConfig={"Delay": 30, "MaxAttempts": 60})
```

### ModelBuilder Pitfalls

1. `dependencies={"auto": True}` scans your local Python environment and installs those exact versions in the container. If your local machine has `torch==2.10` but the DLC has `torch==2.6`, it will overwrite the DLC's torch and break CUDA/NCCL.

   Fix: Always use `dependencies={"auto": False}` or `dependencies={"auto": False, "custom": ["only-what-you-need"]}`.

2. `model=` string parameter makes ModelBuilder use the HF default handler regardless of `image_uri`. It ignores your DJL/vLLM container.

   Fix: Use the core API directly for DJL/vLLM containers.

3. `InferenceSpec` serializes your Python class via cloudpickle. The container needs `cloudpickle` and `sagemaker` installed to deserialize it.

   Fix: Avoid InferenceSpec for production. Use the core API with container-native env vars.

4. `deploy()` returns an `Endpoint` object (SDK v3), not a `Predictor` (SDK v2). Use `Endpoint.invoke()` or `boto3 sagemaker-runtime invoke_endpoint`.

5. `SchemaBuilder` must be a `SchemaBuilder(sample_input, sample_output)` object, not a plain dict.

## Endpoint Configuration

### Timeouts

For models that download from HuggingFace Hub at container startup:

```python
ProductionVariant(
    variant_name="AllTraffic",
    model_name="my-model",
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",
    initial_variant_weight=1.0,
    container_startup_health_check_timeout_in_seconds=900,  # 15 min
    model_data_download_timeout_in_seconds=900,             # 15 min
)
```

Default is 300s which is too short for large models.

### First Invocation

The first invocation after deploy may timeout because:
- The model loads lazily on first request (DJL LMI behavior)
- Model weights download from HuggingFace Hub

Solutions:
- Add a warm-up wait (120-180s) after endpoint goes InService
- Use `boto3` with `Config(read_timeout=600)` for the first call
- Implement retry logic in your client

### Invocation Format

DJL LMI with vLLM backend accepts:

```python
# Simple text generation
payload = {
    "inputs": "Your prompt here",
    "parameters": {"max_new_tokens": 256, "temperature": 0.4},
}

# Multimodal (image + text) — Idefics3 format
payload = {
    "inputs": "User: <image>Describe this image.\nAssistant:",
    "parameters": {"max_new_tokens": 256},
    "images": ["data:image/png;base64,<BASE64_DATA>"],
}
```

## Troubleshooting

### CannotStartContainerError

**Cause:** CUDA version incompatibility between container and instance.
**Fix:** Use cu128 for g5 instances, cu129 only for g6/p5.

### Worker died / Load model failed

**Cause:** Out of memory — model too large for GPU.
**Fix:**
- Use `OPTION_DTYPE=fp16` or `bf16` (DJL LMI)
- Use a larger instance type
- Reduce `OPTION_MAX_MODEL_LEN`
- For HF DLC: the default handler loads in FP32 with no override — switch to DJL LMI

### ncclCommShrink undefined symbol

**Cause:** `ModelBuilder` `auto:True` dependencies overwrote the DLC's PyTorch with an incompatible version.
**Fix:** Use `dependencies={"auto": False}`.

### bitsandbytes not found

**Cause:** Using a quantized model revision (e.g., `quantized8bit`) but the DLC doesn't include bitsandbytes.
**Fix:** Use the `main` revision with `OPTION_DTYPE=fp16` instead.

### No inference script implementation found

**Cause:** Custom `inference.py` not placed where the HF DLC expects it (`/opt/ml/model/code/inference.py`).
**Fix:** Package as `model.tar.gz` with `code/inference.py` inside, upload to S3, and set `model_data_url`. Or switch to DJL LMI which doesn't need custom handlers.

### Invocation timeout (server error 0)

**Cause:** Model still loading on first request.
**Fix:** Wait 120-180s after InService before first invocation. Use `Config(read_timeout=600)` in boto3.

### SSO session expired during long deployments

**Cause:** AWS SSO tokens expire (typically 1-8 hours).
**Fix:** Run `aws sso login` before long operations. For automated scripts, use IAM roles or long-lived credentials.

## Model Memory Sizing

Quick reference for GPU memory requirements:

| Model Size | FP32 | FP16/BF16 | INT8 | Fits On |
|---|---|---|---|---|
| 7-8B | ~32GB | ~16GB | ~8GB | g5.xlarge (FP16), g6.xlarge (FP16) |
| 13B | ~52GB | ~26GB | ~13GB | g5.12xlarge (4x A10G, TP=2+), g6.12xlarge, p5 (any) |
| 70B | ~280GB | ~140GB | ~70GB | p5.48xlarge (8x H100), g5.48xlarge (8x A10G, TP=8) |

Note: 13B FP16 (~26GB) exceeds single A10G capacity (24GB). Use multi-GPU instances with tensor parallelism.

Always use FP16 or BF16 for inference — FP32 is wasteful and often won't fit.

## HyperPod Inference

For deploying inference on HyperPod clusters (JumpStart models, custom models from S3/FSx, autoscaling, KV caching, intelligent routing), load the dedicated steering file:

```
Call action "readSteering" with powerName="sagemaker-ai", steeringFile="hyperpod-inference.md"
```
