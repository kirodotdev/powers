# Inference on SageMaker HyperPod

## Reference Repository

For working deployment examples of popular open-source models on SageMaker (Llama, Mistral, Mixtral, Falcon, CodeLlama, etc.), see:
`https://github.com/aws-samples/sagemaker-genai-hosting-examples`

This repo covers DJL LMI, TGI, Inferentia2 integration, and performance tuning — the same container images and patterns apply to HyperPod inference deployments.

## Overview

HyperPod extends beyond training to provide a unified inference platform on the same persistent clusters. Deploy, scale, and optimize ML models with enterprise-grade reliability using Kubernetes-native workflows. Supports JumpStart foundation models, custom/fine-tuned models from S3 or FSx, autoscaling, KV caching, intelligent routing, and MIG GPU partitioning.

Use HyperPod inference when:
- Running production LLM inference on persistent GPU clusters
- Need autoscaling, KV caching, or intelligent routing for LLM workloads
- Deploying fine-tuned models directly from training artifacts on the same cluster
- Multiple teams sharing inference infrastructure with Task Governance
- Need unified training + inference on the same compute

## Architecture

```
HyperPod Cluster (Inference)
├── EKS Cluster (control plane)
│   ├── Inference Operator (deployment lifecycle)
│   ├── Task Governance (multi-team quotas via Kueue)
│   ├── KEDA (autoscaling)
│   └── Health Monitoring Agent
├── Worker Instance Groups
│   ├── GPU workers (P5, P4d, G5, G6)
│   └── Trainium workers (Trn1, Trn2)
├── Inference Features
│   ├── KV Cache (L1 CPU + L2 Redis/Tiered Storage)
│   ├── Intelligent Routing (prefix-aware, kv-aware, session, round-robin)
│   ├── MIG GPU Partitioning
│   └── SageMaker Endpoint Registration
└── Storage
    ├── S3 (model artifacts)
    ├── FSx for Lustre (large model weights, shared)
    └── EBS (local scratch)
```

## Prerequisites

Before deploying inference on HyperPod:

- [ ] HyperPod cluster created with EKS orchestration
- [ ] HyperPod inference operator installed (via helm or cluster creation)
- [ ] `kubectl` and `jq` installed and configured
- [ ] `sagemaker-hyperpod` CLI/SDK installed (`pip install sagemaker-hyperpod`)
- [ ] Cluster context set: `hyp set-cluster-context --cluster-name <cluster>`
- [ ] Namespace with `hyperpod-inference` service account created by admin
- [ ] IAM permissions for S3 access (model artifacts) and SageMaker endpoint creation

## Deployment Interfaces

| Interface | Best For | JumpStart | Custom Models |
|-----------|----------|-----------|---------------|
| SageMaker Studio UI | Visual one-click deployment | ✅ | ❌ |
| `kubectl` | Kubernetes-native, full YAML control | ✅ | ✅ |
| HyperPod CLI (`hyp`) | Quick CLI-based deployment | ✅ | ✅ |
| HyperPod Python SDK | Programmatic integration | ✅ | ✅ |

## Deploy JumpStart Models

TLS certificates are auto-generated for secure ALB endpoint communication and stored in the specified S3 bucket. The `--tls-certificate-output-s3-uri` parameter is optional — omit it if you only need the SageMaker endpoint (no ALB).

### Via HyperPod CLI

```bash
pip install sagemaker-hyperpod

# Set cluster context
hyp set-cluster-context --cluster-name my-cluster

# Deploy a JumpStart model
hyp create hyp-jumpstart-endpoint \
  --model-id deepseek-llm-r1-distill-qwen-1-5b \
  --instance-type ml.g5.8xlarge \
  --endpoint-name my-jumpstart-endpoint \
  --tls-certificate-output-s3-uri s3://my-tls-bucket/ \
  --namespace default
```

### Via HyperPod Python SDK

```python
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint, TlsConfig,
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

model = Model(model_id="deepseek-llm-r1-distill-qwen-1-5b")
server = Server(instance_type="ml.g5.8xlarge")
endpoint_name = SageMakerEndpoint(name="my-jumpstart-endpoint")
tls_config = TlsConfig(tls_certificate_output_s3_uri="s3://my-tls-bucket/")

js_endpoint = HPJumpStartEndpoint(
    model=model,
    server=server,
    sage_maker_endpoint=endpoint_name,
    tls_config=tls_config,
    namespace="default",
)
js_endpoint.create()
```

### Via kubectl (JumpStartModel CRD)

```bash
# Setup
export REGION=<region>
export HYPERPOD_CLUSTER_NAME="my-cluster"
export MODEL_ID="deepseek-llm-r1-distill-qwen-1-5b"
export MODEL_VERSION="2.0.4"
export INSTANCE_TYPE="ml.g5.8xlarge"
export CLUSTER_NAMESPACE="default"
export SAGEMAKER_ENDPOINT_NAME="my-jumpstart-endpoint"

# Get EKS cluster name and configure kubectl
export EKS_CLUSTER_NAME=$(aws --region $REGION sagemaker describe-cluster \
  --cluster-name $HYPERPOD_CLUSTER_NAME \
  --query 'Orchestrator.Eks.ClusterArn' --output text | cut -d'/' -f2)
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $REGION
```

```yaml
# jumpstart_model.yaml
apiVersion: inference.sagemaker.aws.amazon.com/v1
kind: JumpStartModel
metadata:
  name: my-jumpstart-endpoint
  namespace: default
spec:
  sageMakerEndpoint:
    name: my-jumpstart-endpoint
  model:
    modelHubName: SageMakerPublicHub
    modelId: deepseek-llm-r1-distill-qwen-1-5b
    modelVersion: "2.0.4"
  server:
    instanceType: ml.g5.8xlarge
    # acceleratorPartitionType: "1g.10gb"  # Optional: for MIG-enabled instances
  metrics:
    enabled: true
  maxDeployTimeInSeconds: 1800
  autoScalingSpec:
    minReplicaCount: 1
    maxReplicaCount: 5
    cloudWatchTrigger:
      name: "SageMaker-Invocations"
      namespace: "AWS/SageMaker"
      metricName: "Invocations"
      targetValue: 10
      minValue: 0.0
      metricCollectionPeriod: 30
      metricStat: "Sum"
      metricType: "Average"
      dimensions:
        - name: "EndpointName"
          value: "my-jumpstart-endpoint"
        - name: "VariantName"
          value: "AllTraffic"
```

```bash
kubectl apply -f jumpstart_model.yaml
```

### Discovering JumpStart Models

```bash
# List available models in SageMaker Public Hub
aws sagemaker list-hub-contents \
  --hub-name SageMakerPublicHub \
  --hub-content-type Model \
  --query '{Models: HubContentSummaries[].{ModelId:HubContentName,Version:HubContentVersion}}' \
  --output json

# Check supported instance types for a model
aws sagemaker describe-hub-content \
  --hub-name SageMakerPublicHub \
  --hub-content-type Model \
  --hub-content-name "deepseek-llm-r1-distill-qwen-1-5b" \
  --output json | jq -r '.HubContentDocument | fromjson | {Default: .DefaultInferenceInstanceType, Supported: .SupportedInferenceInstanceTypes}'
```

## Deploy Custom / Fine-Tuned Models

### Via HyperPod CLI (Model from S3)

```bash
# Upload model artifacts to S3 first
aws s3 cp ./my-model s3://my-model-bucket/models/my-model/ --recursive

# Deploy with DJL LMI container
hyp create hyp-custom-endpoint \
  --endpoint-name my-custom-endpoint \
  --model-name my-model \
  --model-source-type s3 \
  --model-location models/my-model/ \
  --s3-bucket-name my-model-bucket \
  --s3-region us-west-2 \
  --instance-type ml.g5.8xlarge \
  --image-uri 763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128 \
  --container-port 8080 \
  --model-volume-mount-name modelmount \
  --tls-certificate-output-s3-uri s3://my-tls-bucket/ \
  --namespace default
```

### Via HyperPod Python SDK (Model from S3)

```python
from sagemaker.hyperpod.inference.config.hp_custom_endpoint_config import (
    Model, Server, SageMakerEndpoint, TlsConfig, EnvironmentVariables,
)
from sagemaker.hyperpod.inference.hp_custom_endpoint import HPCustomEndpoint

model = Model(
    model_source_type="s3",
    model_location="models/my-model/",
    s3_bucket_name="my-model-bucket",
    s3_region="us-west-2",
    prefetch_enabled=True,
)

server = Server(
    instance_type="ml.g5.8xlarge",
    image_uri="763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128",
    container_port=8080,
    model_volume_mount_name="model-weights",
)

resources = {
    "requests": {"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
    "limits": {"nvidia.com/gpu": 1},
}

env = EnvironmentVariables(
    HF_MODEL_ID="/opt/ml/model",
)

endpoint_name = SageMakerEndpoint(name="my-custom-endpoint")
tls_config = TlsConfig(tls_certificate_output_s3_uri="s3://my-tls-bucket/")

custom_endpoint = HPCustomEndpoint(
    model=model,
    server=server,
    resources=resources,
    environment=env,
    sage_maker_endpoint=endpoint_name,
    tls_config=tls_config,
)
custom_endpoint.create()
```

### Via kubectl (InferenceEndpointConfig CRD)

#### Model from S3

```yaml
# custom_model_s3.yaml
apiVersion: inference.sagemaker.aws.amazon.com/v1
kind: InferenceEndpointConfig
metadata:
  name: my-custom-endpoint
  namespace: default
spec:
  sageMakerEndpoint:
    name: my-custom-endpoint
  modelSourceConfig:
    modelSourceType: s3
    modelLocation: "models/my-model/"
    s3Storage:
      bucketName: "my-model-bucket"
      region: "us-west-2"
  worker:
    image: "763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128"
    modelVolumeMountName: "model-weights"
    modelInvocationPort:
      containerPort: 8080
    resources:
      requests:
        cpu: "30000m"
        nvidia.com/gpu: 1
        memory: "100Gi"
      limits:
        nvidia.com/gpu: 1
    environmentVariables:
      - name: HF_MODEL_ID
        value: "/opt/ml/model"
      - name: OPTION_ROLLING_BATCH
        value: "vllm"
      - name: OPTION_DTYPE
        value: "fp16"
      - name: OPTION_MAX_MODEL_LEN
        value: "4096"
  server:
    instanceType: ml.g5.8xlarge
  metrics:
    enabled: true
  maxDeployTimeInSeconds: 1800
```

#### Model from FSx for Lustre

```yaml
# custom_model_fsx.yaml
apiVersion: inference.sagemaker.aws.amazon.com/v1
kind: InferenceEndpointConfig
metadata:
  name: my-fsx-endpoint
  namespace: default
spec:
  sageMakerEndpoint:
    name: my-fsx-endpoint
  modelSourceConfig:
    modelSourceType: fsx
    modelLocation: "/fsx/models/my-model"
    fsxStorage:
      claimName: "fsx-claim"
  worker:
    image: "763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128"
    modelVolumeMountName: "model-weights"
    modelInvocationPort:
      containerPort: 8080
    resources:
      requests:
        cpu: "30000m"
        nvidia.com/gpu: 1
        memory: "100Gi"
      limits:
        nvidia.com/gpu: 1
    environmentVariables:
      - name: HF_MODEL_ID
        value: "/opt/ml/model"
      - name: OPTION_ROLLING_BATCH
        value: "vllm"
      - name: OPTION_DTYPE
        value: "fp16"
  server:
    instanceType: ml.g5.8xlarge
  metrics:
    enabled: true
```

### Deploying HuggingFace Models (Custom from Hub)

To deploy a HuggingFace model not available in JumpStart, download artifacts to S3 first:

```bash
# Download model from HuggingFace Hub
pip install huggingface-hub
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir ./llama-3.1-8b

# Upload to S3
aws s3 cp ./llama-3.1-8b s3://my-model-bucket/models/llama-3.1-8b/ --recursive

# Deploy via CLI
hyp create hyp-custom-endpoint \
  --endpoint-name llama-31-8b-endpoint \
  --model-name llama-31-8b \
  --model-source-type s3 \
  --model-location models/llama-3.1-8b/ \
  --s3-bucket-name my-model-bucket \
  --s3-region us-west-2 \
  --instance-type ml.g5.8xlarge \
  --image-uri 763104351884.dkr.ecr.us-west-2.amazonaws.com/djl-inference:0.36.0-lmi20.0.0-cu128 \
  --container-port 8080 \
  --model-volume-mount-name modelmount \
  --env '{"HF_MODEL_ID":"/opt/ml/model","OPTION_ROLLING_BATCH":"vllm","OPTION_DTYPE":"fp16","OPTION_MAX_MODEL_LEN":"4096"}' \
  --namespace default
```

## Invocation

### Via HyperPod CLI

```bash
# JumpStart endpoint
hyp invoke hyp-jumpstart-endpoint \
  --endpoint-name my-jumpstart-endpoint \
  --body '{"inputs": "What is machine learning?"}'

# Custom endpoint
hyp invoke hyp-custom-endpoint \
  --endpoint-name my-custom-endpoint \
  --body '{"inputs": "What is machine learning?", "parameters": {"max_new_tokens": 256}}'
```

### Via HyperPod Python SDK

```python
# JumpStart
data = '{"inputs": "What is machine learning?"}'
response = js_endpoint.invoke(body=data).body.read()
print(response)

# Custom
data = '{"inputs": "What is machine learning?", "parameters": {"max_new_tokens": 256}}'
response = custom_endpoint.invoke(body=data).body.read()
print(response)
```

### Via AWS CLI (SageMaker Runtime)

```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name my-endpoint \
  --content-type "application/json" \
  --body '{"inputs": "What is machine learning?"}' \
  --region us-west-2 \
  --cli-binary-format raw-in-base64-out \
  /dev/stdout
```

### Via boto3

```python
import boto3, json
from botocore.config import Config

runtime = boto3.client("sagemaker-runtime", config=Config(read_timeout=600))
response = runtime.invoke_endpoint(
    EndpointName="my-endpoint",
    ContentType="application/json",
    Body=json.dumps({
        "inputs": "What is machine learning?",
        "parameters": {"max_new_tokens": 256, "temperature": 0.7},
    }),
)
result = json.loads(response["Body"].read())
```

## KV Caching and Intelligent Routing

### KV Cache Configuration

Two-tier caching architecture for LLM inference performance:
- L1 Cache: CPU memory for low-latency local reuse (enabled by default)
- L2 Cache: Redis or managed tiered storage for node-level cache sharing

```yaml
# Add to your deployment YAML spec
kvCacheSpec:
  enableL1Cache: true
  enableL2Cache: true
  l2CacheSpec:
    l2CacheBackend: tieredstorage  # or "redis"
    # l2CacheLocalUrl: <redis-url>  # Required only for redis backend
```

Security notes:
- KV cache data is stored unencrypted at rest for performance
- When using tiered storage, multiple deployments share cache with no isolation
- For strict encryption or multi-tenant isolation, use dedicated Redis instances or separate clusters

### Intelligent Routing

Routes requests to the inference instance most likely to have relevant cached KV pairs:

| Strategy | Behavior |
|----------|----------|
| `prefixaware` | Same prompt prefix → same instance (default) |
| `kvaware` | Routes to instance with highest KV cache hit rate |
| `session` | Same user session → same instance |
| `roundrobin` | Even distribution, no cache consideration |

```yaml
intelligentRoutingSpec:
  enabled: true
  routingStrategy: prefixaware  # or kvaware, session, roundrobin
```

## Autoscaling

### Built-in autoScalingSpec (in deployment YAML)

```yaml
autoScalingSpec:
  minReplicaCount: 1      # 0 enables scale-to-zero
  maxReplicaCount: 5
  pollingInterval: 15
  cooldownPeriod: 120
  scaleDownStabilizationTime: 60
  scaleUpStabilizationTime: 0
  cloudWatchTrigger:
    name: "SageMaker-Invocations"
    namespace: "AWS/SageMaker"
    metricName: "Invocations"
    targetValue: 10
    minValue: 0.0
    metricCollectionPeriod: 30
    metricStat: "Sum"
    metricType: "Average"
    dimensions:
      - name: "EndpointName"
        value: "my-endpoint"
      - name: "VariantName"
        value: "AllTraffic"
```

### Standalone KEDA ScaledObject (via kubectl)

For advanced scenarios — CloudWatch, SQS, Prometheus, CPU/memory triggers:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: my-scaledobject
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-endpoint
  minReplicaCount: 1
  maxReplicaCount: 4
  pollingInterval: 10
  triggers:
  - type: aws-cloudwatch
    metadata:
      namespace: AWS/SageMaker
      metricName: Invocations
      targetMetricValue: "1"
      minMetricValue: "1"
      awsRegion: "us-west-2"
      dimensionName: EndpointName;VariantName
      dimensionValue: my-endpoint;AllTraffic
      metricStatPeriod: "30"
      metricStat: "Sum"
      identityOwner: operator
```

### Scale-to-Zero

Set `minReplicaCount: 0` with an activation threshold. Ensure the activation metric does not depend on the pods themselves (they won't be running to generate it).

## GPU Partitioning (MIG)

Multi-Instance GPU (MIG) allows running multiple inference workloads on a single GPU for better utilization:

```yaml
# In JumpStartModel or InferenceEndpointConfig spec
server:
  instanceType: ml.p5.48xlarge
  acceleratorPartitionType: "1g.10gb"  # MIG profile
```

## Multi-Instance Type Deployment

Specify a prioritized list of instance types for automatic failover when preferred capacity is unavailable:

```yaml
# Uses preferredDuringSchedulingIgnoredDuringExecution node affinity
# System evaluates instance types in priority order
server:
  instanceType: ml.g5.8xlarge  # Primary preference
  # Additional instance types configured via nodeAffinity
```

## Container Selection for Custom Models

| Model Type | Recommended Container | Notes |
|------------|----------------------|-------|
| Standard LLM (Llama, Mistral, Qwen, DeepSeek) | DJL LMI with vLLM | `djl-inference:0.36.0-lmi20.0.0-cu128` |
| Multimodal/Vision (Qwen-VL, LLaVA) | DJL LMI with vLLM | Same container, vLLM supports vision models |
| Custom inference handler | HuggingFace Inference DLC | Requires `code/inference.py` in model.tar.gz |
| PyTorch custom model | PyTorch Inference DLC | For non-LLM custom models |

Always check latest images at: `https://aws.github.io/deep-learning-containers/reference/available_images/`

### CUDA Compatibility (Same as SageMaker Endpoints)

| CUDA Version | Works On | Fails On |
|---|---|---|
| cu124 | g5, g6, p5 | — |
| cu128 | g5, g6, p5 | — |
| cu129 | g6, p5 | g5 (driver version mismatch → CannotStartContainerError) |

Note: cu129 failure on g5 is due to the DLC requiring a newer GPU driver than what's installed on g5 instances. Inferentia2 (inf2) instances do not use CUDA — use Neuron SDK containers instead.

## Monitoring and Observability

### Check Deployment Status

```bash
# JumpStart
kubectl describe JumpStartModel my-endpoint -n default
hyp list hyp-jumpstart-endpoint
hyp describe hyp-jumpstart-endpoint --name my-endpoint

# Custom
kubectl describe InferenceEndpointConfig my-endpoint -n default
hyp list hyp-custom-endpoint
hyp describe hyp-custom-endpoint --name my-endpoint

# SageMaker endpoint status
aws sagemaker describe-endpoint --endpoint-name my-endpoint --output table

# All resources in namespace
kubectl get pods,svc,deployment,JumpStartModel,InferenceEndpointConfig,sagemakerendpointregistration -n default
```

### View Logs

```bash
# Via CLI
hyp list-pods hyp-jumpstart-endpoint --namespace default
hyp get-logs hyp-jumpstart-endpoint --namespace default --pod-name <pod-name>

# Via kubectl
kubectl logs <pod-name> -n default

# Operator logs
hyp get-operator-logs hyp-jumpstart-endpoint --since-hours 0.5

# Grafana / Prometheus (if observability stack deployed)
hyp get-monitoring --grafana
hyp get-monitoring --prometheus
```

### Key Metrics

HyperPod inference tracks: time-to-first-token (TTFT), latency, GPU utilization, invocations, and error rates. Enable metrics in deployment YAML:

```yaml
metrics:
  enabled: true
  modelMetrics:
    port: 8080
```

## Cleanup

```bash
# Delete JumpStart deployment
hyp delete hyp-jumpstart-endpoint --name my-endpoint
# or
kubectl delete JumpStartModel my-endpoint -n default

# Delete custom deployment
hyp delete hyp-custom-endpoint --name my-endpoint
# or
kubectl delete InferenceEndpointConfig my-endpoint -n default

# Verify cleanup
kubectl get pods,svc,deployment -n default
aws sagemaker describe-endpoint --endpoint-name my-endpoint --region us-west-2
```

## Troubleshooting

### Deployment stuck in DeploymentInProgress
- Check pod status: `kubectl get pods -n <namespace>`
- Check operator logs: `hyp get-operator-logs hyp-custom-endpoint --since-hours 1`
- Verify instance type is available in cluster: `aws sagemaker describe-cluster --cluster-name <cluster> --query "InstanceGroups"`
- Verify namespace has `hyperpod-inference` service account

### Pod CrashLoopBackOff
- Check container logs: `kubectl logs <pod-name> -n <namespace>`
- CUDA version mismatch: use cu128 for g5, cu129 only for g6/p5
- OOM: model too large for instance — use larger instance or reduce `OPTION_MAX_MODEL_LEN`
- Image pull failure: verify ECR image URI and region

### SageMaker endpoint not created
- Check SageMakerEndpointRegistration: `kubectl describe sagemakerendpointregistration <name> -n <namespace>`
- Verify IAM role has `sagemaker:CreateEndpoint` permissions
- Ensure endpoint name is unique across the account

### Model loading timeout
- Increase `maxDeployTimeInSeconds` in YAML (default 1800)
- For large models from S3, ensure S3 VPC endpoint exists for faster downloads
- For FSx, verify PVC is mounted and model path is correct

### Autoscaling not working
- Verify KEDA operator is installed: `kubectl get pods -n keda`
- Check ScaledObject status: `kubectl describe scaledobject <name> -n <namespace>`
- Verify CloudWatch metrics are being emitted (endpoint must receive traffic first)
- Ensure KEDA operator IAM role has CloudWatch read permissions

### Cannot invoke endpoint
- Wait for deployment status to be `DeploymentComplete` / endpoint `InService`
- First invocation may be slow (model loading) — use `Config(read_timeout=600)` in boto3
- Check security groups allow inbound traffic on the container port
