# SageMaker HyperPod (Cluster Setup & Training)

## Overview

Purpose-built persistent compute clusters for foundation model training and inference. Reduces training time by up to 40% through automatic fault tolerance. Supports EKS and Slurm orchestration.

Use HyperPod when:
- Pre-training or full fine-tuning models 70B+
- Running multi-week/month training campaigns
- Multiple teams sharing GPU/Trainium infrastructure
- Need automatic fault recovery and node replacement
- Running production inference on persistent GPU clusters

For inference deployment on HyperPod (JumpStart models, custom models, autoscaling, KV caching), load the dedicated steering file:

```
Call action "readSteering" with powerName="sagemaker-ai", steeringFile="hyperpod-inference.md"
```

## Architecture

```
HyperPod Cluster
├── EKS Cluster (control plane)
│   ├── Training Operator (job lifecycle)
│   ├── Task Governance (multi-team quotas via Kueue)
│   └── Health Monitoring Agent
├── Worker Instance Groups
│   ├── GPU workers (P5, P4d, G5, G6)
│   └── Trainium workers (Trn1, Trn2)
└── Storage
    ├── FSx for Lustre (training data, checkpoints)
    ├── S3 via Mountpoint CSI
    └── EBS (local scratch)
```

## Quick Setup

### Option 1: MCP Server (Recommended when using Kiro)

Use the `manage_hyperpod_stacks` MCP tool for automated cluster deployment via managed CloudFormation templates (same templates as the HyperPod console UI):

```
manage_hyperpod_stacks(operation="deploy", stack_name="my-cluster-stack", region_name="us-east-1")
```

To check status:
```
manage_hyperpod_stacks(operation="describe", stack_name="my-cluster-stack")
```

To list and inspect cluster nodes:
```
manage_hyperpod_cluster_nodes(operation="list_clusters")
manage_hyperpod_cluster_nodes(operation="list_nodes", cluster_name="my-cluster")
manage_hyperpod_cluster_nodes(operation="describe_node", cluster_name="my-cluster", node_id="node-id")
```

**Note**: Cluster creation typically takes ~30 minutes.

### Option 2: hyp CLI

```bash
pip install sagemaker-hyperpod

# Initialize cluster config
hyp init cluster-stack
# Edit config.yaml with your settings
hyp configure --stack-name my-stack

# Validate and create
hyp validate
hyp create
```

### Key config.yaml Settings

```yaml
template: cluster-stack
resource_name_prefix: my-training
hyperpod_cluster_name: my-cluster
kubernetes_version: "1.31"  # Check EKS supported versions for your region
node_recovery: Automatic
node_provisioning_mode: Continuous

instance_group_settings:
  - InstanceCount: 4
    InstanceGroupName: gpu-workers
    InstanceType: ml.p5.48xlarge
    InstanceStorageConfigs:
      - EbsVolumeConfig:
          VolumeSizeInGB: 500

helm_operators: >-
  trainingOperators.enabled=true,
  mlflow.enabled=true,
  health-monitoring-agent.enabled=true,
  deep-health-check.enabled=true,
  job-auto-restart.enabled=true
```

## Instance Types

| Instance | Accelerator | Memory | Best For | $/hr (approx) |
|----------|------------|--------|----------|---------------|
| ml.p5.48xlarge | 8x H100 | 640 GB HBM3 | Large FM training | ~$55 |
| ml.p5e.48xlarge | 8x H200 | 1.1 TB HBM3e | Memory-bound models | Contact AWS |
| ml.p4d.24xlarge | 8x A100 | 320 GB HBM2 | Budget-conscious | ~$38 |
| ml.trn1.32xlarge | 16x Trainium v1 | 512 GB HBM | Cost-optimized | ~$25 |
| ml.trn2.48xlarge | 16x Trainium v2 | 1.5 TB HBM | Best price-perf | Contact AWS |
| ml.g5.48xlarge | 8x A10G | 192 GB | Fine-tuning, small models | ~$16 |

### Sizing Guidance

| Task | Recommended |
|------|-------------|
| Pre-training 70B | 16-32x ml.p5.48xlarge |
| Full fine-tuning 70B | 4-8x ml.p5.48xlarge |
| LoRA fine-tuning 70B | 1-2x ml.p5.48xlarge |
| Fine-tuning 7-13B | 1-4x ml.g5.48xlarge |

## Training Operator

Enables data scientists to submit jobs via `kubectl`. Install as EKS add-on.

### Job Submission (HyperPodPyTorchJob)

```yaml
apiVersion: sagemaker.amazonaws.com/v1
kind: HyperPodPyTorchJob
metadata:
  name: my-training-job
  namespace: team-a
  labels:
    kueue.x-k8s.io/queue-name: team-a-localqueue
    kueue.x-k8s.io/priority-class: high
spec:
  nprocPerNode: "8"
  runPolicy:
    jobMaxRetryCount: 50
    restartPolicy:
      numRestartBeforeFullJobRestart: 3
      evalPeriodSeconds: 21600
      maxFullJobRestarts: 1
    cleanPodPolicy: "All"
  replicaSpecs:
    - name: workers
      replicas: 2
      template:
        spec:
          nodeSelector:
            node.kubernetes.io/instance-type: ml.p5.48xlarge
          containers:
            - name: trainer
              image: 763104351884.dkr.ecr.<region>.amazonaws.com/pytorch-training:2.6.0-gpu-py312-cu126-ubuntu22.04-sagemaker
              command: ["hyperpodrun"]
              args: ["--nproc-per-node=8", "--nnodes=2", "train.py"]
              resources:
                limits:
                  nvidia.com/gpu: 8
                  hugepages-2Mi: 5120Mi
                requests:
                  nvidia.com/gpu: 8
                  hugepages-2Mi: 5120Mi
                  memory: 32000Mi
```

### Log Monitoring Rules

Add to job spec for automatic hang/fault detection:

```yaml
logMonitoringConfiguration:
  rules:
    - name: "JobStart"
      logPattern: ".*Training started.*"
      expectedStartCutOffInSeconds: 120
    - name: "HangDetection"
      logPattern: ".*step (\\d+).*"
      expectedRecurringFrequencyInSeconds: 300
      expectedStartCutOffInSeconds: 600
    - name: "OOMDetection"
      logPattern: ".*OutOfMemoryError.*"
      faultOnMatch: true
```

## Task Governance (Multi-Team)

Requires Kubernetes >= 1.30. Provides namespace isolation, compute quotas, priority scheduling, and idle resource borrowing.

### Team Quota Example

| Team | Namespace | GPUs | Priority |
|------|-----------|------|----------|
| Pre-training | team-pretrain | 48 (6 nodes × 8) | critical |
| Fine-tuning | team-finetune | 16 (2 nodes × 8) | high |
| Exploration | team-explore | 8 (1 node × 8) | low |

Idle GPUs from one team are automatically lent to others and preempted when reclaimed.

## Resiliency Features

| Feature | Details |
|---------|---------|
| Health monitoring | Continuous on all nodes |
| Deep health checks | GPU/Trainium diagnostics, adds NoSchedule taint during check |
| Auto node replacement | Faulty nodes replaced without manual intervention |
| Job auto-resume | Training Operator restarts from last checkpoint |
| Checkpointless training | Recovery in minutes without saving checkpoints (Dec 2025+) |
| Elastic training | Dynamic cluster scaling during training |

## Training Plans (Capacity Reservations)

For guaranteed GPU availability:

| Parameter | Options |
|-----------|---------|
| Advance booking | Up to 56 days ahead, or instant-start |
| Duration | 1-182 days |
| Instance quantities | 1, 2, 4, 8, 16, 32, or 64 |
| Cancellation | Cannot be cancelled once purchased |

Use Training Plans when:
- GPU capacity is scarce in your region
- Running predictable multi-day training
- Need guaranteed availability for deadlines

## HyperPod Recipes

Pre-configured distributed training stacks for popular models on HyperPod clusters. These are different from the Model Customization Recipes (which target Training Jobs with Accelerate + DeepSpeed). HyperPod Recipes auto-configure distributed training, checkpointing, and optimizers for the HyperPod Training Operator.

```bash
git clone https://github.com/aws/sagemaker-hyperpod-recipes
# Pick model + instance config from recipe table
# Launch — auto-configures distributed training, checkpointing, optimizers
```

## Prerequisites Checklist

Before creating a cluster:

- [ ] Service quotas requested (GPU instances, EBS volumes, network interfaces)
- [ ] IAM roles created (HyperPod service role, EKS node role, Training Operator role)
- [ ] VPC with private subnets (public subnets NOT supported)
- [ ] Security groups allowing all intra-group traffic (required for EFA)
- [ ] S3 VPC endpoint created
- [ ] EKS Pod Identity Agent add-on installed
- [ ] cert-manager installed on EKS cluster

## Troubleshooting

### Cluster stuck in Creating
- Use `manage_hyperpod_stacks(operation="describe", stack_name="...")` to check CloudFormation stack status and events
- Check CloudFormation console for detailed errors
- Verify service quotas are approved
- Ensure subnets are private (not public)

### Training job not starting
- Verify Training Operator is running: `kubectl get pods -n aws-hyperpod`
- Check Kueue queue status: `kubectl get clusterqueue`
- Verify namespace and queue labels in job YAML

### Node replacement taking too long
- Use `manage_hyperpod_cluster_nodes(operation="describe_node", cluster_name="...", node_id="...")` to check node status
- Deep health checks add NoSchedule taint — check: `kubectl get nodes -o wide`
- Verify instance availability in your AZ
- Check HyperPod cluster events in SageMaker console
- To update node software: `manage_hyperpod_cluster_nodes(operation="update_software", cluster_name="...")`

### Neuron compilation slow (Trainium)
- First run compiles model graph (10-20 min) — subsequent runs use cache
- Set `NEURON_CC_FLAGS="--model-type transformer"` for faster compilation
- Use compilation cache: mount persistent storage for `/var/tmp/neuron-compile-cache`
