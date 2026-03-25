# SageMaker Python SDK v3 — API Reference

## Correct Imports

```python
# Core session and role
from sagemaker.core.helper.session_helper import Session, get_execution_role

# Image URI lookup
from sagemaker.core import image_uris

# Training
from sagemaker.train import ModelTrainer
from sagemaker.core.training.configs import (
    Compute, SourceCode, OutputDataConfig,
    CheckpointConfig, StoppingCondition,
)

# Deployment — ModelBuilder (simple HF / JumpStart models)
from sagemaker.serve import ModelBuilder, InferenceSpec, ModelServer
from sagemaker.serve.builder.schema_builder import SchemaBuilder

# Deployment — Core API (DJL LMI / vLLM / full control)
from sagemaker.core.resources import Model, EndpointConfig, Endpoint
from sagemaker.core.shapes.shapes import ContainerDefinition, ProductionVariant

# Hyperparameter tuning
from sagemaker.train.tuner import (
    HyperparameterTuner, ContinuousParameter,
    IntegerParameter, CategoricalParameter,
)

# Processing
from sagemaker.core.processing import ScriptProcessor, ProcessingInput, ProcessingOutput

# Batch transform
from sagemaker.core.transformer import Transformer

# JumpStart
from sagemaker.core.jumpstart.notebook_utils import list_jumpstart_models
```

NEVER import from: `sagemaker.model`, `sagemaker.processing`, `sagemaker.transformer`,
`sagemaker.workflow`, `sagemaker.xgboost`, `sagemaker.sklearn`, `sagemaker.pytorch`.
These are all SDK v2 and removed in v3.


## image_uris.retrieve() — Per Framework

```python
# XGBoost (no py_version or instance_type needed)
image_uri = image_uris.retrieve(framework="xgboost", region=region, version="1.7-1")

# SKLearn (no py_version or instance_type needed)
image_uri = image_uris.retrieve(framework="sklearn", region=region, version="1.2-1")

# PyTorch (REQUIRES py_version and instance_type)
image_uri = image_uris.retrieve(
    framework="pytorch", region=region, version="2.1",
    py_version="py310", instance_type="ml.m5.xlarge",
)

# AutoGluon (REQUIRES py_version, image_scope, instance_type)
image_uri = image_uris.retrieve(
    "autogluon", region=region, version="1.5",
    py_version="py312", image_scope="training",
    instance_type="ml.m5.2xlarge",
)
```

## Training Pattern — Classical ML (XGBoost/SKLearn)

Complete pattern for training XGBoost or SKLearn models with SDK v3:

```python
from sagemaker.train import ModelTrainer
from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.core import image_uris
from sagemaker.core.training.configs import (
    Compute, SourceCode, OutputDataConfig,
)

session = Session()
region = session.boto_region_name
role = get_execution_role()
bucket = session.default_bucket()

# Use SKLearn container with XGBoost in requirements.txt
sklearn_image = image_uris.retrieve(
    framework="sklearn", region=region, version="1.2-1",
)

trainer = ModelTrainer(
    training_image=sklearn_image,
    role=role,
    source_code=SourceCode(
        source_dir="./training",
        entry_script="train.py",
        requirements="requirements.txt",
    ),
    compute=Compute(
        instance_type="ml.m5.large",
        instance_count=1,
        volume_size_in_gb=30,
    ),
    hyperparameters={
        "n-estimators": "100",
        "max-depth": "6",
        "learning-rate": "0.1",
        "target-column": "target",
    },
    output_data_config=OutputDataConfig(
        s3_output_path=f"s3://{bucket}/output",
    ),
    base_job_name="xgboost-training",
    sagemaker_session=session,
)

trainer.train(
    input_data_config=[{
        "channel_name": "train",
        "data_source": {
            "s3_data_source": {
                "s3_uri": f"s3://{bucket}/data/train/",
                "s3_data_type": "S3Prefix",
            }
        },
    }],
    wait=True,
    logs=True,
)
```

Key rules for classical ML training scripts:
- Save model to `/opt/ml/model/` (use `SM_MODEL_DIR` env var)
- Read data from `/opt/ml/input/data/<channel>/` (use `SM_CHANNEL_TRAIN` env var)
- All argparse numeric args must have `type=int` or `type=float`
- Include `model_fn()` in train.py for inference compatibility

## Deployment Patterns

### Pattern 1: Core API — DJL LMI / vLLM (LLMs, multimodal)

Use when you need full control over the container and env vars.

```python
from sagemaker.core.resources import Model, EndpointConfig, Endpoint
from sagemaker.core.shapes.shapes import ContainerDefinition, ProductionVariant
from sagemaker.core.helper.session_helper import get_execution_role

role_arn = get_execution_role()

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

EndpointConfig.create(
    endpoint_config_name="my-endpoint",
    production_variants=[ProductionVariant(
        variant_name="AllTraffic",
        model_name="my-model",
        initial_instance_count=1,
        instance_type="ml.g5.2xlarge",
        initial_variant_weight=1.0,
        container_startup_health_check_timeout_in_seconds=900,
        model_data_download_timeout_in_seconds=900,
    )],
)

Endpoint.create(endpoint_name="my-endpoint", endpoint_config_name="my-endpoint")

# Wait
import boto3
sm = boto3.client("sagemaker")
sm.get_waiter("endpoint_in_service").wait(
    EndpointName="my-endpoint", WaiterConfig={"Delay": 30, "MaxAttempts": 60}
)
```

### Pattern 2: ModelBuilder — JumpStart / Simple HF Models

```python
from sagemaker.serve import ModelBuilder
from sagemaker.serve.builder.schema_builder import SchemaBuilder

builder = ModelBuilder(
    model="meta-textgeneration-llama-3-1-8b",  # JumpStart model ID
    schema_builder=SchemaBuilder(
        {"inputs": "Hello", "parameters": {"max_new_tokens": 32}},
        [{"generated_text": "sample"}],
    ),
    instance_type="ml.g5.2xlarge",
)
builder.build()
endpoint = builder.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge",
    endpoint_name="my-endpoint",
)
```

### Pattern 3: Classical ML Inference Hooks

The four hooks called in sequence for every prediction:

```
Request → input_fn → predict_fn → output_fn → Response
                        ↑
              model_fn (called once at startup)
```

Package as `code/inference.py` inside `model.tar.gz`:

```python
import os, json, joblib, numpy as np

def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "model.joblib"))

def input_fn(body, content_type):
    if content_type == "application/json":
        return np.array(json.loads(body)["instances"])
    raise ValueError(f"Unsupported: {content_type}")

def predict_fn(data, model):
    return model.predict(data)

def output_fn(prediction, accept):
    return json.dumps({"predictions": prediction.tolist()}), "application/json"
```

## Invocation

### Via boto3 (recommended for DJL LMI endpoints)

```python
import boto3, json
from botocore.config import Config

runtime = boto3.client("sagemaker-runtime", config=Config(read_timeout=600))
response = runtime.invoke_endpoint(
    EndpointName="my-endpoint",
    ContentType="application/json",
    Body=json.dumps({"inputs": "Hello", "parameters": {"max_new_tokens": 128}}),
)
result = json.loads(response["Body"].read())
```

### Via SDK v3 Endpoint.invoke

```python
from sagemaker.core.resources import Endpoint
endpoint = Endpoint.get("my-endpoint")
response = endpoint.invoke(
    body=json.dumps(payload),
    content_type="application/json",
    accept="application/json",
)
```

## Cleanup

```python
# Delete endpoint + config + model
import boto3
sm = boto3.client("sagemaker")
sm.delete_endpoint(EndpointName="my-endpoint")
sm.delete_endpoint_config(EndpointConfigName="my-endpoint")
sm.delete_model(ModelName="my-model")
```
