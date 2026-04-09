# SageMaker Model Monitor (SDK v3)

## Overview

SageMaker Model Monitor continuously monitors the quality of ML models in production by detecting data drift, model quality degradation, bias drift, and feature attribution changes. All 4 monitor types use the same workflow: baseline → schedule → detect violations.

| Monitor Type | What It Detects | Requires Ground Truth |
|---|---|---|
| Data Quality | Feature drift, missing values, distribution shifts, schema violations | No |
| Model Quality | Degradation in accuracy, precision, recall, F1, AUC | Yes |
| Model Bias | Demographic parity difference (DPL), disparate impact (DI) | Yes |
| Model Explainability | SHAP feature attribution drift | No |

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  Training    │───>│  Model       │───>│  Endpoint         │
│  (XGBoost)   │    │  (S3 .tar.gz)│    │  (ml.m5.xlarge)   │
└─────────────┘    └──────────────┘    └────────┬──────────┘
                                                │
                                     DataCapture (100%)
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │  S3 Capture  │
                                        │  (JSONL)     │
                                        └──────┬───────┘
                                               │
                    ┌──────────────┬────────────┴──────────────┐
                    │              │                           │
              ┌─────▼──────┐ ┌────▼───────────┐  ┌────────────▼──────┐
              │ DQ Monitor │ │ MQ Monitor     │  │ Clarify Monitors  │
              │ (hourly)   │ │ (hourly +      │  │ (Bias + SHAP,     │
              │            │ │  ground truth) │  │  hourly)          │
              └────────────┘ └────────────────┘  └───────────────────┘
```

## SDK v3 Imports

All monitoring classes live under `sagemaker.core` (verified with `sagemaker==3.5.0`):

```python
from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.core.model_monitor import (
    DefaultModelMonitor,
    ModelQualityMonitor,
    DataCaptureConfig,
    CronExpressionGenerator,
    DatasetFormat,
    EndpointInput,
)
from sagemaker.core.model_monitor.clarify_model_monitoring import (
    ModelBiasMonitor,
    ModelExplainabilityMonitor,
)
from sagemaker.core.model_monitor.model_monitoring import Constraints
from sagemaker.core.clarify import (
    BiasConfig, DataConfig, ModelConfig,
    ModelPredictedLabelConfig, SHAPConfig,
)
```

## Prerequisites

- `sagemaker>=3.5.0` (SDK v3 — v2 will NOT work)
- An endpoint deployed with DataCapture enabled
- IAM role with `AmazonSageMakerFullAccess` and S3 read/write

## Step 1: Deploy Endpoint with Data Capture

Data capture must be enabled on the endpoint before any monitor can work.

```python
from sagemaker.serve.model_builder import ModelBuilder
from sagemaker.serve.builder.schema_builder import SchemaBuilder
from sagemaker.core.model_monitor import DataCaptureConfig

data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,
    destination_s3_uri=f"s3://{bucket}/datacapture/{endpoint_name}",
    capture_options=["Input", "Output"],
    csv_content_types=["text/csv"],
)

builder = ModelBuilder(
    image_uri=image_uri,
    s3_model_data_url=repacked_model_uri,
    role_arn=role,
    sagemaker_session=sm_session,
    schema_builder=SchemaBuilder(
        sample_input="39,77516,13,2174,0,40,State-gov,Bachelors,Never-married,Adm-clerical,Not-in-family,White,Male,United-States",
        sample_output="0,0.123456",
    ),
    env_vars={
        "SAGEMAKER_PROGRAM": "inference.py",
        "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",  # Local path inside container, NOT S3
    },
)
builder.build()

# Known SDK v3 bug: deploy() may raise ValidationError on kms_key_id
# The endpoint IS deployed successfully — catch and continue
try:
    endpoint = builder.deploy(
        endpoint_name=endpoint_name,
        instance_type="ml.m5.xlarge",
        initial_instance_count=1,
        data_capture_config=data_capture_config,
    )
except Exception as e:
    if "kms_key_id" in str(e).lower() or "validation error" in str(e).lower():
        print(f"Known SDK v3 bug (endpoint IS deployed): {type(e).__name__}")
    else:
        raise
```

Data capture latency: 2-5 minutes before capture files appear in S3.

## Step 2: Data Quality Monitor

Detects feature drift, missing values, and distribution shifts. No ground truth needed.

### Baseline

```python
data_quality_monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800,  # Must be < schedule cadence (3600s for hourly)
    sagemaker_session=sm_session,
)

data_quality_monitor.suggest_baseline(
    baseline_dataset=baseline_s3_uri,  # CSV with header, features only (no target)
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri=f"s3://{bucket}/data-quality/baseline-results",
    wait=True,
    logs=False,
)

# Get baseline artifacts
statistics = data_quality_monitor.latest_baselining_job.baseline_statistics()
constraints = data_quality_monitor.latest_baselining_job.suggested_constraints()
```

### Schedule

```python
data_quality_monitor.create_monitoring_schedule(
    monitor_schedule_name="dq-monitor-schedule",
    endpoint_input=endpoint_name,
    output_s3_uri=f"s3://{bucket}/data-quality/reports",
    statistics=statistics,
    constraints=constraints,
    schedule_cron_expression=CronExpressionGenerator.hourly(),
    enable_cloudwatch_metrics=True,
)
```

### Trigger Violations (Testing)

Send drifted data to the endpoint to trigger violations:

```python
import numpy as np

def generate_drifted_data(df, numerical_features, categorical_features):
    """Shift numericals by 3σ, flip 30% of categoricals, inject 15% missing."""
    df = df.copy()
    # Numerical shift
    n_shift = int(len(df) * 0.5)
    idx = np.random.choice(df.index, size=n_shift, replace=False)
    for col in numerical_features:
        df.loc[idx, col] = df.loc[idx, col] + 3 * df[col].std()
    # Categorical flip
    n_flip = int(len(df) * 0.3)
    idx = np.random.choice(df.index, size=n_flip, replace=False)
    for col in categorical_features:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) > 1:
            df.loc[idx, col] = np.random.choice(unique_vals, size=n_flip)
    # Missing values
    n_missing = int(len(df) * 0.15)
    for col in df.columns:
        idx = np.random.choice(df.index, size=n_missing, replace=False)
        df.loc[idx, col] = np.nan
    return df
```

## Step 3: Model Quality Monitor

Detects degradation in classification/regression metrics. Requires ground truth labels.

### Baseline

```python
model_quality_monitor = ModelQualityMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800,
    sagemaker_session=sm_session,
)

# Baseline CSV must have: prediction, probability, label columns
model_quality_monitor.suggest_baseline(
    baseline_dataset=mq_baseline_s3_uri,
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri=f"s3://{bucket}/model-quality/baseline-results",
    problem_type="BinaryClassification",
    inference_attribute="prediction",
    probability_attribute="probability",
    ground_truth_attribute="label",
    wait=True,
    logs=False,
)

mq_constraints = model_quality_monitor.latest_baselining_job.suggested_constraints()
```

### Ground Truth Format

Ground truth must be uploaded as JSONL with event IDs matching data capture records:

```json
{"groundTruthData": {"data": "0", "encoding": "CSV"}, "eventMetadata": {"eventId": "<must-match-capture-event-id>"}}
{"groundTruthData": {"data": "1", "encoding": "CSV"}, "eventMetadata": {"eventId": "<must-match-capture-event-id>"}}
```

Upload to S3 with time-partitioned path: `s3://bucket/ground-truth/YYYY/MM/DD/HH/`

### Schedule

```python
endpoint_input = EndpointInput(
    endpoint_name=endpoint_name,
    destination="/opt/ml/processing/input/endpoint",
    inference_attribute="0",   # Column index for predicted label
    probability_attribute="1", # Column index for probability
)

model_quality_monitor.create_monitoring_schedule(
    monitor_schedule_name="mq-monitor-schedule",
    endpoint_input=endpoint_input,
    output_s3_uri=f"s3://{bucket}/model-quality/reports",
    constraints=mq_constraints,
    ground_truth_input=f"s3://{bucket}/ground-truth",
    problem_type="BinaryClassification",
    schedule_cron_expression=CronExpressionGenerator.hourly(),
    enable_cloudwatch_metrics=True,
)
```

## Step 4: Model Bias Monitor (Clarify)

Detects bias drift on protected attributes. Uses SageMaker Clarify under the hood.

### Baseline

```python
from sagemaker.core.clarify import BiasConfig, DataConfig, ModelConfig, ModelPredictedLabelConfig

bias_data_config = DataConfig(
    s3_data_input_path=analysis_s3_uri,  # CSV with features + label
    s3_output_path=f"s3://{bucket}/clarify/bias-results",
    label="income",
    headers=ALL_FEATURES + ["income"],
    dataset_type="text/csv",
)

bias_config = BiasConfig(
    label_values_or_threshold=[1],       # Favorable outcome
    facet_name="sex",                    # Protected attribute
    facet_values_or_threshold=["Male"],  # Reference group
)

model_config = ModelConfig(
    model_name=model_name,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    content_type="text/csv",
    accept_type="text/csv",
)

predicted_label_config = ModelPredictedLabelConfig(
    label=0,              # Column index for predicted label
    probability=1,        # Column index for probability
    probability_threshold=0.5,
)

model_bias_monitor = ModelBiasMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800,
    sagemaker_session=sm_session,
)

# Known SDK v3 bug: suggest_baseline may raise AttributeError on sagemaker_session
# The baseline job DOES complete — catch and load constraints from S3
try:
    model_bias_monitor.suggest_baseline(
        data_config=bias_data_config,
        bias_config=bias_config,
        model_config=model_config,
        model_predicted_label_config=predicted_label_config,
        wait=True,
        logs=False,
    )
    bias_constraints = model_bias_monitor.latest_baselining_job.suggested_constraints()
except AttributeError as e:
    if "sagemaker_session" in str(e):
        bias_constraints = Constraints.from_s3_uri(
            constraints_file_s3_uri=f"s3://{bucket}/clarify/bias-results/analysis.json",
            sagemaker_session=sm_session,
        )
    else:
        raise
```

### Schedule

```python
bias_endpoint_input = EndpointInput(
    endpoint_name=endpoint_name,
    destination="/opt/ml/processing/input/endpoint",
    inference_attribute="0",
    probability_attribute="1",
)

model_bias_monitor.create_monitoring_schedule(
    monitor_schedule_name="bias-monitor-schedule",
    endpoint_input=bias_endpoint_input,
    output_s3_uri=f"s3://{bucket}/bias/reports",
    constraints=bias_constraints,
    ground_truth_input=f"s3://{bucket}/ground-truth",
    schedule_cron_expression=CronExpressionGenerator.hourly(),
    enable_cloudwatch_metrics=True,
)
```

## Step 5: Model Explainability Monitor (SHAP)

Detects drift in feature attributions using SHAP values.

### SHAP Baseline for Mixed Data

When building the SHAP baseline row for datasets with both numerical and categorical features, use median for numeric and mode for categorical:

```python
baseline_row = [
    float(df[c].median()) if c in NUMERICAL_FEATURES else df[c].mode().iloc[0]
    for c in ALL_FEATURES
]

shap_config = SHAPConfig(
    baseline=[baseline_row],
    num_samples=100,
    agg_method="mean_abs",
)
```

Do NOT use `.median()` on all columns — it raises `TypeError` on categorical columns.

### Baseline

```python
explainability_data_config = DataConfig(
    s3_data_input_path=analysis_s3_uri,
    s3_output_path=f"s3://{bucket}/clarify/explainability-results",
    label="income",
    headers=ALL_FEATURES + ["income"],
    dataset_type="text/csv",
)

model_explainability_monitor = ModelExplainabilityMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800,
    sagemaker_session=sm_session,
)

# Same SDK v3 bug as bias monitor — catch and load from S3
try:
    model_explainability_monitor.suggest_baseline(
        data_config=explainability_data_config,
        model_config=model_config,
        explainability_config=shap_config,
        wait=True,
        logs=False,
    )
    explain_constraints = model_explainability_monitor.latest_baselining_job.suggested_constraints()
except AttributeError as e:
    if "sagemaker_session" in str(e):
        explain_constraints = Constraints.from_s3_uri(
            constraints_file_s3_uri=f"s3://{bucket}/clarify/explainability-results/analysis.json",
            sagemaker_session=sm_session,
        )
    else:
        raise
```

### Schedule

```python
explain_endpoint_input = EndpointInput(
    endpoint_name=endpoint_name,
    destination="/opt/ml/processing/input/endpoint",
)

model_explainability_monitor.create_monitoring_schedule(
    monitor_schedule_name="explain-monitor-schedule",
    endpoint_input=explain_endpoint_input,
    output_s3_uri=f"s3://{bucket}/explainability/reports",
    constraints=explain_constraints,
    schedule_cron_expression=CronExpressionGenerator.hourly(),
    enable_cloudwatch_metrics=True,
)
```

## Inference Handler for Model Monitor

The endpoint's inference handler must output CSV with `predicted_label,probability` per row. This format is required for all 4 monitor types:

```python
def model_fn(model_dir):
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    encoder = joblib.load(os.path.join(model_dir, "encoder.joblib"))
    with open(os.path.join(model_dir, "feature_names.json")) as f:
        feature_names = json.load(f)
    return {"model": model, "encoder": encoder, "feature_names": feature_names}

def input_fn(request_body, request_content_type):
    if request_content_type == "text/csv":
        return pd.read_csv(io.StringIO(request_body), header=None)
    raise ValueError(f"Unsupported: {request_content_type}")

def predict_fn(input_data, model_dict):
    model, encoder = model_dict["model"], model_dict["encoder"]
    feature_names = model_dict["feature_names"]
    if list(input_data.columns) == list(range(len(input_data.columns))):
        input_data.columns = feature_names[:len(input_data.columns)]
    X_enc = encoder.transform(input_data[feature_names])
    predictions = model.predict(X_enc)
    probabilities = model.predict_proba(X_enc)[:, 1]
    return np.column_stack([predictions, probabilities])

def output_fn(prediction, accept):
    out = io.StringIO()
    for row in prediction:
        out.write(f"{int(row[0])},{row[1]:.6f}\n")
    return out.getvalue(), "text/csv"
```

Package as `code/inference.py` inside `model.tar.gz`.

## Invocation

Always use boto3 `sagemaker-runtime` for invocation — the SDK v3 `Endpoint.get().invoke()` hits the same Pydantic `kms_key_id` bug:

```python
smr_client = boto3.client("sagemaker-runtime")
response = smr_client.invoke_endpoint(
    EndpointName=endpoint_name,
    Body=payload,
    ContentType="text/csv",
    Accept="text/csv",
)
result = response["Body"].read().decode("utf-8")
```

## Cleanup

Delete in this order: schedules → endpoint → endpoint config → model.

```python
sm_client = boto3.client("sagemaker")

# Delete all monitoring schedules
for schedule_name in [dq_schedule, mq_schedule, bias_schedule, explain_schedule]:
    try:
        sm_client.delete_monitoring_schedule(MonitoringScheduleName=schedule_name)
    except Exception:
        pass

# Delete endpoint, config, model
sm_client.delete_endpoint(EndpointName=endpoint_name)
sm_client.delete_endpoint_config(EndpointConfigName=endpoint_name)
sm_client.delete_model(ModelName=model_name)
```

## Known SDK v3 Bugs (sagemaker==3.5.0)

| Bug | Impact | Workaround |
|-----|--------|------------|
| `ModelBuilder.deploy()` raises `ValidationError` on `kms_key_id` | Endpoint IS deployed; error in return value deserialization | Catch exception and continue |
| `ClarifyBaseliningJob` raises `AttributeError: 'ProcessingJob' has no attribute 'sagemaker_session'` | Clarify job completes; error in wrapping result | Catch error, load constraints from S3 via `Constraints.from_s3_uri()` |
| `max_runtime_in_seconds >= schedule cadence` raises `ValidationException` | Schedule creation fails | Use 1800s for hourly schedules (cadence = 3600s) |
| `Endpoint.get().invoke()` hits Pydantic `kms_key_id` bug | Cannot use SDK invoke | Use `boto3.client('sagemaker-runtime').invoke_endpoint()` |

## Operational Notes

- Data capture latency: 2-5 minutes before files appear in S3
- Monitoring schedule: runs hourly; first execution may take up to 1 hour after creation
- Clarify containers: 10-20 minutes each for bias and explainability baselining
- Ground truth format: JSONL with `groundTruthData.data` (CSV-encoded label) and `eventMetadata.eventId` (must match capture event IDs exactly)
- Cleanup order: delete monitoring schedules first, then endpoint, then config, then model
- `max_runtime_in_seconds` must be strictly less than the schedule cadence (use 1800 for hourly)

## Troubleshooting

### No violations detected
- Ensure enough drifted traffic was sent during the monitoring window
- Data capture has 2-5 min latency — wait before checking
- Check that the monitoring execution completed: `monitor.list_executions()`

### Schedule creation fails with ValidationException
- `max_runtime_in_seconds` must be < schedule cadence (3600s for hourly)
- Use 1800s as the max runtime

### Clarify baseline fails with AttributeError
- Known SDK v3 bug — the job DID complete
- Load constraints directly: `Constraints.from_s3_uri(f'{output_uri}/analysis.json', sagemaker_session=sm_session)`

### Ground truth not matched
- Event IDs in ground truth JSONL must exactly match event IDs from data capture files
- Parse capture files to extract event IDs before generating ground truth
- Upload ground truth to time-partitioned S3 path: `YYYY/MM/DD/HH/`

### CloudWatch metrics not appearing
- Metrics are published after monitoring execution completes
- Namespace: `/aws/sagemaker/Endpoints/data-metrics`
- Check dimensions: `Endpoint` and `MonitoringSchedule`
