# AutoML with AutoGluon on SageMaker AI

## Overview

AutoGluon is an open-source AutoML framework that automates model selection, hyperparameter tuning, and ensembling. On SageMaker, it runs via the AutoGluon DLC (Deep Learning Container) with SDK v3 `ModelTrainer`.

Supports three task types:
- Tabular classification/regression
- Time series forecasting
- Multimodal (text + tabular fusion)

## DLC Image Retrieval

```python
from sagemaker.core import image_uris

image_uri = image_uris.retrieve(
    "autogluon",
    region=region,
    version="1.5",          # Check latest at DLC images page
    py_version="py312",
    image_scope="training",  # or "inference"
    instance_type="ml.m5.2xlarge",
)
```

## Training Pattern

```python
from sagemaker.train import ModelTrainer
from sagemaker.core.training.configs import (
    Compute, SourceCode, OutputDataConfig, StoppingCondition,
)

trainer = ModelTrainer(
    training_image=image_uri,
    role=role_arn,
    source_code=SourceCode(
        source_dir=".",
        entry_script="train.py",
    ),
    compute=Compute(
        instance_type="ml.m5.2xlarge",
        instance_count=1,
        volume_size_in_gb=100,
    ),
    output_data_config=OutputDataConfig(
        s3_output_path=f"s3://{bucket}/output",
    ),
    base_job_name="autogluon-tabular",
    hyperparameters={
        "config": "config.yaml",
        "train-dir": "/opt/ml/input/data/train",
    },
    stopping_condition=StoppingCondition(
        max_runtime_in_seconds=7200,
    ),
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


## Training Scripts

### Tabular Classification

```python
"""train.py — AutoGluon tabular training on SageMaker"""
import os
import yaml
from autogluon.tabular import TabularPredictor
import pandas as pd

train_dir = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Load data
df = pd.read_csv(os.path.join(train_dir, "train.csv"))

# Train
predictor = TabularPredictor(
    label=config["label_column"],
    path=model_dir,
    eval_metric=config.get("eval_metric", "roc_auc"),
).fit(
    train_data=df,
    time_limit=config.get("time_limit", 3600),
    presets=config.get("presets", "best_quality"),
)

# Save leaderboard
leaderboard = predictor.leaderboard(silent=True)
leaderboard.to_csv(os.path.join(model_dir, "leaderboard.csv"), index=False)
print(f"Best model: {predictor.model_best}")
```

### Time Series Forecasting

```python
"""train.py — AutoGluon time series training on SageMaker"""
import os
from autogluon.timeseries import TimeSeriesPredictor, TimeSeriesDataFrame
import pandas as pd

train_dir = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

df = pd.read_csv(os.path.join(train_dir, "train.csv"), parse_dates=["timestamp"])
ts_df = TimeSeriesDataFrame.from_data_frame(
    df, id_column="item_id", timestamp_column="timestamp",
)

predictor = TimeSeriesPredictor(
    target="target",
    prediction_length=24,
    path=model_dir,
    eval_metric="MASE",
).fit(
    train_data=ts_df,
    time_limit=3600,
    presets="best_quality",
)
```

### Multimodal (Text + Tabular)

Requires GPU instance (`ml.g4dn.xlarge` or larger).

```python
"""train.py — AutoGluon multimodal training on SageMaker"""
import os
from autogluon.multimodal import MultiModalPredictor
import pandas as pd

train_dir = os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train")
model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

df = pd.read_csv(os.path.join(train_dir, "train.csv"))

predictor = MultiModalPredictor(
    label="label",
    path=model_dir,
    eval_metric="roc_auc",
).fit(
    train_data=df,
    time_limit=3600,
    presets="best_quality",
)
```

## Inference (Real-Time Endpoint)

AutoGluon DLC uses TorchServe and requires `code/inference.py` inside `model.tar.gz`.

### Repackaging Model Artifacts

Pipeline training outputs only contain model artifacts. You must repackage with the inference script:

```python
import tarfile, os, shutil

# Download original model.tar.gz from S3
# Extract, add code/inference.py, repackage
os.makedirs("repackaged/code", exist_ok=True)
with tarfile.open("model.tar.gz", "r:gz") as tar:
    tar.extractall("repackaged")
shutil.copy("serve.py", "repackaged/code/inference.py")
with tarfile.open("model-repackaged.tar.gz", "w:gz") as tar:
    tar.add("repackaged", arcname=".")
# Upload repackaged model to S3
```

### Inference Handler (serve.py → code/inference.py)

```python
"""Inference handler for AutoGluon on SageMaker"""
import os, json, io
import pandas as pd

def model_fn(model_dir):
    from autogluon.tabular import TabularPredictor
    return TabularPredictor.load(model_dir)

def input_fn(request_body, content_type):
    if content_type == "text/csv":
        return pd.read_csv(io.StringIO(request_body))
    elif content_type == "application/json":
        return pd.DataFrame(json.loads(request_body))
    raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(data, model):
    predictions = model.predict(data)
    probabilities = model.predict_proba(data)
    return {"predictions": predictions.tolist(), "probabilities": probabilities.values.tolist()}

def output_fn(prediction, accept):
    return json.dumps(prediction), "application/json"
```

### Deploy with SDK v3 Core API

```python
from sagemaker.core.resources import Model, EndpointConfig, Endpoint
from sagemaker.core.shapes.shapes import ContainerDefinition, ProductionVariant
from sagemaker.core import image_uris

inference_image = image_uris.retrieve(
    "autogluon", region=region, version="1.5",
    py_version="py312", image_scope="inference",
    instance_type="ml.m5.xlarge",
)

Model.create(
    model_name="autogluon-model",
    primary_container=ContainerDefinition(
        image=inference_image,
        model_data_url=f"s3://{bucket}/output/model-repackaged.tar.gz",
    ),
    execution_role_arn=role_arn,
)

EndpointConfig.create(
    endpoint_config_name="autogluon-endpoint",
    production_variants=[ProductionVariant(
        variant_name="AllTraffic",
        model_name="autogluon-model",
        initial_instance_count=1,
        instance_type="ml.m5.xlarge",
        initial_variant_weight=1.0,
    )],
)

Endpoint.create(
    endpoint_name="autogluon-endpoint",
    endpoint_config_name="autogluon-endpoint",
)
```

## SageMaker Pipelines with AutoGluon

### Correct Imports (SDK v3)

```python
from sagemaker.core.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.core.workflow.parameters import ParameterString
from sagemaker.core.workflow.pipeline_context import PipelineSession
from sagemaker.mlops.workflow.pipeline import Pipeline
from sagemaker.mlops.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.train import ModelTrainer
```

### Pipeline Pattern

```python
# Processing step
processor = ScriptProcessor(
    image_uri=image_uri, role=role_arn,
    instance_type="ml.m5.xlarge", instance_count=1,
)
processing_step = ProcessingStep(
    name="Preprocess",
    step_args=processor.run(
        code="preprocess.py",
        inputs=[ProcessingInput(source=raw_s3, destination="/opt/ml/processing/input")],
        outputs=[ProcessingOutput(source="/opt/ml/processing/output", destination=processed_s3)],
    ),
)

# Training step
training_step = TrainingStep(
    name="Train",
    step_args=trainer.train(
        input_data_config=[{
            "channel_name": "train",
            "data_source": {"s3_data_source": {
                "s3_uri": processing_step.properties.ProcessingOutputConfig
                    .Outputs["output"].S3Output.S3Uri,
                "s3_data_type": "S3Prefix",
            }},
        }],
    ),
)

# Create pipeline
pipeline = Pipeline(
    name="AutoGluonPipeline",
    steps=[processing_step, training_step],
    sagemaker_session=PipelineSession(),
)
pipeline.upsert(role_arn=role_arn)
```

## Troubleshooting

### OOM during multimodal training
- Multimodal uses a text transformer — requires GPU instances
- Reduce `time_limit` or use `presets="medium_quality"` to limit ensemble size
- Use `ml.g4dn.xlarge` minimum, `ml.g5.2xlarge` for larger datasets

### TorchServe startup failure on inference endpoint
- AutoGluon DLC uses TorchServe — requires `code/inference.py` inside `model.tar.gz`
- If you trained via Pipeline, the output model.tar.gz won't have the inference script — repackage it

### model.tar.gz packaging errors
- The archive must have `code/inference.py` at the root level (not nested under extra directories)
- Use `tar.add("repackaged", arcname=".")` to avoid extra directory nesting

### Time series prediction returns empty or errors
- Requires 48+ historical timestamps per item for reliable predictions
- Ensure `item_id` and `timestamp` columns match training format exactly

## Key Considerations

- Use `ParameterString` for all hyperparameters (SageMaker passes them as strings)
- Multimodal tasks require GPU instances (`ml.g4dn.xlarge`+)
- Time series inference requires 48+ historical timestamps per item
- Name evaluation scripts `run_evaluation.py` (not `evaluate.py`) to avoid conflicts with the HuggingFace `evaluate` package
- AutoGluon DLC version 1.5 uses Python 3.12

## Instance Recommendations

| Task | Training | Inference |
|------|----------|-----------|
| Tabular | ml.m5.2xlarge | ml.m5.xlarge |
| Time Series | ml.m5.2xlarge | ml.m5.xlarge |
| Multimodal | ml.g4dn.xlarge | ml.g4dn.xlarge |
