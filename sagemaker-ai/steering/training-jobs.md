# Training on SageMaker AI

## Reference Repository

For production-ready fine-tuning recipes (QLoRA, Spectrum, Full FT, DPO, GRPO/RLVR) with pre-configured YAML configs for Llama, Qwen, DeepSeek, Phi, Gemma, and GPT-OSS models, see:
`https://github.com/aws-samples/amazon-sagemaker-generativeai/tree/main/0_model_customization_recipes`

Includes one-command training pipeline, multi-node/multi-GPU support, Flash Attention, Liger Kernel, 4-bit quantization, and built-in evaluation with vLLM.

## Three Approaches to Model Customization

| Approach | Best For | Complexity | Cost Model |
|----------|----------|------------|------------|
| **Serverless Model Customization** | Quick fine-tuning, no infra management | Low | Pay-per-token |
| **SageMaker Training Jobs** | Flexible training with cost control | Medium | Pay-per-hour |
| **SageMaker HyperPod** | Large-scale, long-running FM training | High | Persistent cluster |

### Decision Guide

| Scenario | Recommended |
|----------|-------------|
| Fine-tune < 7B, quick iteration | Serverless Model Customization |
| Fine-tune 7B-70B, cost-sensitive | Training Jobs (with Spot/Trainium) |
| Fine-tune 70B+ | Training Jobs or HyperPod |
| Pre-train foundation model | HyperPod |
| Multi-week continuous training | HyperPod |
| Teams without MLOps expertise | Serverless Model Customization |

## Serverless Model Customization

Fully managed capability (launched December 2025) — fine-tune foundation models without infrastructure management. The service automatically provisions and optimizes GPU instances.

### Supported Models
- Amazon Nova: Micro, Lite, Pro, Lite 2.0
- Meta Llama: 3.1 8B, 3.1 70B, 2 7B/13B
- Qwen, DeepSeek, GPT-OSS (region-dependent)

### Supported Techniques
- SFT (Supervised Fine-Tuning)
- DPO (Direct Preference Optimization)
- RLVR (RL with Verifiable Rewards)
- RLAIF (RL from AI Feedback)
- LoRA/QLoRA
- Full-Rank fine-tuning
- CPT (Continued Pre-Training)

### Key Characteristics
- Data format: JSONL, CSV, Parquet
- Dataset size: 1,000-10,000 rows (model-dependent)
- Deployment: SageMaker Inference or Amazon Bedrock
- Pricing: Pay-per-token
- Regions: us-east-1, us-west-2, eu-west-1, ap-northeast-1

### Limitations
- No SSH access to training instances
- TensorBoard only (no MLFlow/WandB)
- No model merging or multi-LoRA adapter support
- Limited model selection (supported models only)

---

## SageMaker Training Jobs

### When to Use Training Jobs vs HyperPod

| Criteria | SageMaker Training Jobs | SageMaker HyperPod |
|----------|------------------------|-------------------|
| Best for | Single experiments, LoRA/QLoRA, models ≤70B | Large-scale, full fine-tuning, multi-node, 70B+ |
| Infrastructure | Ephemeral (spins up/down per job) | Persistent cluster (Slurm/EKS) |
| Cost model | Pay per job duration | Pay for cluster uptime |
| Setup complexity | Low (SDK + script) | Higher (cluster config, EKS, operators) |
| Iteration speed | Fast (no cluster to manage) | Slower setup, faster for many sequential jobs |

## Instance Selection for Training

### GPU Memory per Technique

| Technique | Memory per Billion Params | Notes |
|-----------|--------------------------|-------|
| Full Fine-Tuning (BF16) | ~16-18 GB/B | Model + optimizer + gradients |
| LoRA (FP16) | ~4-6 GB/B | Frozen base + adapters |
| QLoRA (4-bit) | ~1-1.5 GB/B | Quantized base + adapters |

### Instance Matrix for QLoRA (Most Common)

| Model Size | Recommended Instance | GPUs | Total VRAM |
|------------|---------------------|------|------------|
| 7-8B | ml.g5.2xlarge | 1x A10G | 24 GB |
| 13B | ml.g5.4xlarge | 1x A10G | 24 GB |

Note: g5.2xlarge → g5.4xlarge adds CPU/RAM only, same 1x A10G 24GB. For 13B QLoRA with seq_len > 1024, consider ml.g5.12xlarge (4x A10G, 96GB).
| 34B | ml.g5.12xlarge | 4x A10G | 96 GB |
| 70B | ml.g5.48xlarge or ml.p4d.24xlarge | 8x A10G / 8x A100 | 192 / 320 GB |

### Trainium Instances

| Instance | Chips | HBM | Best For |
|----------|-------|-----|----------|
| ml.trn1.2xlarge | 1 chip (2 cores) | 32 GB | Testing, small models |
| ml.trn1.32xlarge | 16 chips (32 cores) | 512 GB | Production training |

Trainium has limited architecture support. Verified: `llama`, `qwen3`, `granite`. Always check `model_type` in config.json and the Neuron SDK compatibility matrix for the latest supported list. Variants like `qwen3_vl`, `mllama` are NOT supported.

## SDK v3 Training Job Launcher Pattern

```python
from sagemaker.train import ModelTrainer
from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.core import image_uris
from sagemaker.core.training.configs import (
    Compute, SourceCode, OutputDataConfig,
    CheckpointConfig, StoppingCondition,
)

sess = Session()
region = sess.boto_region_name
role = get_execution_role()
bucket = sess.default_bucket()

# Get training container image
# ALWAYS check https://aws.github.io/deep-learning-containers/reference/available_images/
# for the latest version. The SDK may auto-select an older image.
training_image = image_uris.retrieve(
    framework="pytorch",
    region=region,
    version="2.5.1",
    py_version="py311",
    image_scope="training",
    instance_type="ml.g5.2xlarge",
)

model_trainer = ModelTrainer(
    training_image=training_image,
    source_code=SourceCode(
        source_dir="./scripts",
        command="pip install -r requirements.txt && python train_lora.py",
    ),
    base_job_name="my-training-job",
    compute=Compute(
        instance_type="ml.g5.2xlarge",
        instance_count=1,
        volume_size_in_gb=300,
        keep_alive_period_in_seconds=1800,  # Warm pool for faster restarts
    ),
    role=role,
    environment={
        "MODEL_ID": "meta-llama/Llama-3.1-8B-Instruct",
        "NUM_EPOCHS": "3",
        "BATCH_SIZE": "2",
        "GRADIENT_ACCUMULATION": "4",
        "LEARNING_RATE": "2e-4",
        "MAX_SEQ_LENGTH": "2048",
        "LORA_R": "16",
        "LORA_ALPHA": "32",
        "SM_CHANNEL_TRAIN": "/opt/ml/input/data/train",
    },
    input_data_config=[{
        "channel_name": "train",
        "data_source": {
            "s3_data_source": {
                "s3_uri": f"s3://{bucket}/datasets/train/",
                "s3_data_type": "S3Prefix",
            }
        },
    }],
    output_data_config=OutputDataConfig(
        s3_output_path=f"s3://{bucket}/training-outputs",
    ),
    checkpoint_config=CheckpointConfig(
        s3_uri=f"s3://{bucket}/checkpoints",
        local_path="/opt/ml/checkpoints",
    ),
    stopping_condition=StoppingCondition(
        max_runtime_in_seconds=86400,  # 24 hours
    ),
)

model_trainer.train(wait=True, logs=True)
```

## Training Script Patterns

### QLoRA Training Script (GPU)

Key components for `scripts/train_lora.py`:

```python
import os, torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# Config from env vars (set in ModelTrainer.environment)
model_id = os.environ.get("MODEL_ID")
train_data = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
output_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

# 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id, quantization_config=bnb_config,
    device_map="auto", torch_dtype=torch.bfloat16,
)
model = prepare_model_for_kbit_training(model)

# LoRA config — SFTTrainer applies this automatically
peft_config = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    bias="none", task_type="CAUSAL_LM",
)

# Dataset: expects {"messages": [...]} format
dataset = load_dataset("json", data_files={"train": f"{train_data}/train.jsonl"})

tokenizer = AutoTokenizer.from_pretrained(model_id)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def formatting_func(example):
    return tokenizer.apply_chat_template(
        example["messages"], tokenize=False, add_generation_prompt=False
    )

sft_config = SFTConfig(
    output_dir=output_dir,
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    bf16=True,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    optim="paged_adamw_8bit",
)

trainer = SFTTrainer(
    model=model, args=sft_config,
    train_dataset=dataset["train"],
    processing_class=tokenizer,  # renamed from tokenizer in trl 0.12+
    formatting_func=formatting_func,
    peft_config=peft_config,
)
trainer.train()
trainer.save_model()
tokenizer.save_pretrained(output_dir)
```

### Trainium LoRA Training Script

Key differences from GPU:
- Uses `optimum-neuron` instead of `bitsandbytes`
- BF16 training (no 4-bit quantization on Trainium)
- `attn_implementation="eager"` (no flash attention)
- No `device_map="auto"` — Neuron handles placement

```python
from optimum.neuron import NeuronSFTConfig, NeuronSFTTrainer
from optimum.neuron.models.training.config import TrainingNeuronConfig
from peft import LoraConfig

trn_config = TrainingNeuronConfig(
    tensor_parallel_size=tp_degree,
    sequence_parallel_enabled=False,
)

# NeuronSFTTrainer handles model loading and Neuron compilation
trainer = NeuronSFTTrainer(
    model=model_id,
    args=NeuronSFTConfig(
        output_dir=output_dir,
        bf16=True,
        tensor_parallel_size=tp_degree,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        gradient_checkpointing=True,
    ),
    train_dataset=dataset["train"],
    processing_class=tokenizer,
    formatting_func=formatting_func,
    peft_config=peft_config,
)
```

Container for Trainium:
```
763104351884.dkr.ecr.<region>.amazonaws.com/pytorch-training-neuronx:2.8.0-neuronx-py311-sdk2.26.1-ubuntu22.04
```

Launch command for Trainium:
```python
SourceCode(
    source_dir="./scripts",
    command="pip install -r requirements_trainium.txt && torchrun --nproc_per_node=2 train_lora_trainium.py",
)
```

## AWS Recipe-Based Training

For supported models, use the official AWS SFT recipes from:
`https://github.com/aws-samples/amazon-sagemaker-generativeai/tree/main/0_model_customization_recipes`

These provide pre-configured YAML recipes for QLoRA, Spectrum, and full fine-tuning with Accelerate + DeepSpeed. Supported models include Llama 3.x, Qwen 2.5/3, DeepSeek R1, Phi-3/4, Gemma 3, and GPT-OSS 20B/120B.

### Quick Instance Reference (from recipes repo)

| Model Size | QLoRA | Spectrum | Full FT |
|------------|-------|----------|---------|
| 1-4B | ml.g5.2xlarge | ml.g6e.2xlarge | ml.g6e.2xlarge |
| 7-14B | ml.g6e.2xlarge | ml.g6e.2xlarge / g6e.4xlarge | ml.g6e.2xlarge / g6e.12xlarge |
| 17-32B | ml.p4de.24xlarge | ml.p4de.24xlarge | ml.p4de.24xlarge / p5e.48xlarge |
| 70-120B | ml.p5e.48xlarge | ml.p5e.48xlarge | ml.p5e.48xlarge |
| 600B+ | ml.p5en.48xlarge | ml.p5en.48xlarge | ml.p5en.48xlarge |

Launch pattern:
```python
SourceCode(
    source_dir="./sagemaker_code",
    command="./sm_accelerate_train.sh --config recipes/model_recipe.yaml",
)
```

## Data Format

SageMaker training scripts expect data in the SageMaker input channel:

```
/opt/ml/input/data/train/train.jsonl
/opt/ml/input/data/train/val.jsonl  (optional)
```

Standard chat format (recommended):
```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

## HyperPod

For HyperPod cluster setup, Training Operator, Task Governance, and resiliency features, load the dedicated steering file:

```
Call action "readSteering" with powerName="sagemaker-ai", steeringFile="hyperpod.md"
```

For deploying trained models as inference endpoints on HyperPod (JumpStart, custom models from S3/FSx, autoscaling):

```
Call action "readSteering" with powerName="sagemaker-ai", steeringFile="hyperpod-inference.md"
```

## Troubleshooting

### CUDA OOM during training
- Reduce `BATCH_SIZE` to 1
- Increase `GRADIENT_ACCUMULATION` to maintain effective batch size
- Reduce `MAX_SEQ_LENGTH`
- Use QLoRA instead of LoRA/full fine-tuning
- Use a larger instance type

### Neuron compilation timeout
- First run on Trainium compiles the model graph (10-20 min)
- Subsequent runs use cached compilation
- Set `NEURON_CC_FLAGS="--model-type transformer"` for faster compilation

### Training job fails immediately
- Check the CloudWatch logs: `/aws/sagemaker/TrainingJobs`
- Verify the container image exists in your region
- Verify the IAM role has S3 and ECR access
- Check instance quota: `aws service-quotas list-service-quotas --service-code sagemaker`
