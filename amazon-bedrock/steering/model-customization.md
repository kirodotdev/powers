# Bedrock Model Customization

## Overview

Three approaches to customize models on Bedrock:

| Method | How It Works | Best For |
|--------|-------------|----------|
| **Supervised Fine-Tuning** | Train on labeled input/output pairs | Domain-specific style, format, or knowledge |
| **Reinforcement Fine-Tuning** | Train with reward functions (no labels needed) | Complex reasoning, subjective quality |
| **Distillation** | Transfer knowledge from large to small model | Cost optimization with maintained quality |

## Supervised Fine-Tuning

### Supported Models

Not all models support fine-tuning. Check current support:

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")
models = bedrock.list_foundation_models(
    byCustomizationType="FINE_TUNING"
)["modelSummaries"]
for m in models:
    print(f"{m['modelId']} — {m['modelName']}")
```

Common fine-tunable models: Amazon Titan, Meta Llama, Cohere Command R, Anthropic Claude (select models).

### Training Data Format

JSONL file in S3, one example per line:

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Summarize this contract."}, {"role": "assistant", "content": "The contract states..."}]}
{"messages": [{"role": "user", "content": "Draft a response to this email."}, {"role": "assistant", "content": "Dear Customer, thank you for..."}]}
```

Requirements:
- Minimum examples vary by model (typically 32-10,000)
- Messages must alternate user/assistant (system optional)
- JSONL format, UTF-8 encoded
- Stored in S3

### Create Fine-Tuning Job

```python
job = bedrock.create_model_customization_job(
    jobName="my-finetune-job",
    customModelName="my-custom-model",
    roleArn="arn:aws:iam::ACCOUNT:role/BedrockCustomizationRole",
    baseModelIdentifier="amazon.titan-text-lite-v1:0:4k",
    customizationType="FINE_TUNING",
    trainingDataConfig={
        "s3Uri": "s3://my-bucket/training-data/train.jsonl",
    },
    validationDataConfig={
        "validators": [{
            "s3Uri": "s3://my-bucket/training-data/validation.jsonl",
        }]
    },
    outputDataConfig={
        "s3Uri": "s3://my-bucket/output/",
    },
    hyperParameters={
        "epochCount": "3",
        "batchSize": "8",
        "learningRate": "0.00001",
    },
)
job_arn = job["jobArn"]
```

### Monitor Job

```python
status = bedrock.get_model_customization_job(jobIdentifier=job_arn)
print(f"Status: {status['status']}")
# IN_PROGRESS, COMPLETED, FAILED, STOPPING, STOPPED
```

### Use Custom Model

After job completes, create a Provisioned Throughput to use it:

```python
# Create provisioned throughput
pt = bedrock.create_provisioned_model_throughput(
    modelUnits=1,
    provisionedModelName="my-custom-model-pt",
    modelId=status["outputModelArn"],
)

# Invoke via Converse
response = bedrock_runtime.converse(
    modelId=pt["provisionedModelArn"],
    messages=[{"role": "user", "content": [{"text": "Hello"}]}],
)
```

**Important**: Custom models require Provisioned Throughput — they cannot use on-demand pricing or CRIS.

## Reinforcement Fine-Tuning

Uses reward functions instead of labeled data. A Lambda function scores model outputs at training time.

```python
job = bedrock.create_model_customization_job(
    jobName="my-rlft-job",
    customModelName="my-rl-model",
    roleArn="arn:aws:iam::ACCOUNT:role/BedrockCustomizationRole",
    baseModelIdentifier="anthropic.claude-3-haiku-20240307-v1:0",
    customizationType="REINFORCEMENT_FINE_TUNING",
    trainingDataConfig={
        "s3Uri": "s3://my-bucket/training-data/prompts.jsonl",
    },
    # Reward function is a Lambda
    customizationConfig={
        "reinforcementFineTuningConfig": {
            "evaluatorModelConfig": {
                "bedrockEvaluatorModels": [{
                    "evaluatorLambdaArn": "arn:aws:lambda:us-east-1:ACCOUNT:function:reward-function",
                }]
            }
        }
    },
    outputDataConfig={"s3Uri": "s3://my-bucket/output/"},
)
```

## Distillation

Transfer knowledge from a teacher (large, expensive) model to a student (small, fast) model:

```python
job = bedrock.create_model_customization_job(
    jobName="my-distillation-job",
    customModelName="my-distilled-model",
    roleArn="arn:aws:iam::ACCOUNT:role/BedrockCustomizationRole",
    baseModelIdentifier="anthropic.claude-3-haiku-20240307-v1:0",  # student
    customizationType="DISTILLATION",
    trainingDataConfig={
        "s3Uri": "s3://my-bucket/training-data/prompts.jsonl",
    },
    customizationConfig={
        "distillationConfig": {
            "teacherModelConfig": {
                "teacherModelIdentifier": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            }
        }
    },
    outputDataConfig={"s3Uri": "s3://my-bucket/output/"},
)
```

## Custom Model Import

Import models trained outside Bedrock (Hugging Face, SageMaker, etc.) using the MCP server:

```
# List imported models
list_imported_models()

# Import a model from S3
create_model_import_job(
    jobName="my-import",
    importedModelName="my-external-model",
    modelDataSource={"s3DataSource": {"s3Uri": "s3://bucket/model/"}}
)

# Check import status
get_model_import_job(job_identifier="job-id")
```

Or via boto3:

```python
job = bedrock.create_model_import_job(
    jobName="my-import",
    importedModelName="my-external-model",
    roleArn="arn:aws:iam::ACCOUNT:role/BedrockImportRole",
    modelDataSource={
        "s3DataSource": {
            "s3Uri": "s3://my-bucket/model-artifacts/",
        }
    },
)
```

## IAM Role for Customization

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::my-bucket/output/*"
        }
    ]
}
```

## Pricing

| Component | Charged For |
|-----------|------------|
| Fine-tuning | Tokens processed (training data tokens x epochs) |
| Storage | Per month per custom model |
| Inference | Provisioned Throughput (model units/hour) |

## Best Practices

- **Start with prompt engineering** — fine-tuning is expensive; make sure prompting can't solve it first
- **Minimum training examples** — more data generally means better quality; aim for 1000+ examples
- **Use validation data** — always include a validation set to detect overfitting
- **Low learning rates** — start with 1e-5 and adjust
- **Clean your data** — garbage in, garbage out; review training examples for quality
- **Custom models need Provisioned Throughput** — budget for always-on inference costs
- **Distillation for cost optimization** — if you have a working large-model solution, distill to a smaller model

## Troubleshooting

### Job fails immediately
- Check IAM role has correct S3 permissions
- Verify training data format matches expected JSONL schema
- Ensure base model supports the customization type

### Poor quality after fine-tuning
- Increase training examples (more diverse data)
- Reduce learning rate
- Add more epochs (but watch for overfitting on validation set)
- Review training data quality — remove noisy examples

### Can't invoke custom model
- Custom models require Provisioned Throughput — create one first
- CRIS inference profiles don't work with custom models
- Verify the Provisioned Throughput is in ACTIVE state
