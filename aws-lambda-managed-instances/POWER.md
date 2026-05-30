---
name: "aws-lambda-managed-instances"
displayName: "AWS Lambda Managed Instances"
description: "Evaluate, configure, and migrate workloads to AWS Lambda Managed Instances (LMI). Run Lambda functions on EC2 instances in your account while AWS manages provisioning, patching, scaling, routing, and load balancing."
keywords: ["lambda", "lmi", "managed-instances", "ec2", "capacity-provider", "multi-concurrency", "cold-start", "graviton", "cost-optimization", "serverless", "lambda-pricing", "reserved-instances", "savings-plans"]
author: "AWS"
---

# AWS Lambda Managed Instances (LMI)

Run Lambda functions on current-generation EC2 instances in your account while AWS manages provisioning, patching, scaling, routing, and load balancing. Combines Lambda's developer experience with EC2's pricing and hardware options.

## Onboarding

### Step 1: Validate AWS CLI access

Before using this power, ensure AWS credentials are configured:

```bash
aws sts get-caller-identity
```

If this fails, configure credentials via `aws configure` or set `AWS_PROFILE`.

### Step 2: Check regional availability

Currently available: us-east-1, us-east-2, us-west-2, ap-northeast-1, eu-west-1. Expanding to all commercial regions soon. Verify the latest availability:

- [Lambda Managed Instances documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html)

## When to Load Steering Files

- **Cost comparison**, **pricing analysis**, **Lambda vs LMI cost**, **Savings Plans**, or **Reserved Instances** → `cost-comparison.md`
- **Instance types**, **memory sizing**, **vCPU ratios**, **scaling tuning**, or **capacity provider config** → `configuration-guide.md`
- **Thread safety**, **concurrency model**, **code review checklist**, **Powertools compatibility**, or **multi-concurrency readiness** → `thread-safety.md`
- **Before/after code examples**, **runtime-specific migration** (Node.js, Python, Java, .NET), or **connection pooling** → `migration-patterns.md`
- **IAM roles**, **VPC setup**, **CLI commands**, **SAM template**, or **CDK example** → `infrastructure-setup.md`
- **Errors**, **throttling**, **debugging**, or **stuck deployments** → `troubleshooting.md`

## Quick Decision: Is LMI Right for This Workload?

| Signal | LMI is a strong fit | Standard Lambda is better |
|--------|---------------------|---------------------------|
| Traffic | Steady, predictable, 50M+ req/mo | Bursty, unpredictable, long idle |
| Cost | Duration-heavy spend at scale | Low or sporadic invocations |
| Cold starts | Unacceptable (LMI eliminates for provisioned capacity) | Tolerable or mitigated by SnapStart |
| Compute | Latest CPUs, specific families, high network bandwidth | Standard Lambda memory/CPU sufficient |
| Isolation | Dedicated EC2 instances in your account, full VPC control | Shared Firecracker micro-VMs acceptable |
| Scale-to-zero | Not needed (execution environments always running) | Required (pay nothing when idle) |
| Code readiness | Thread-safe (Node.js/Java/.NET) or any Python code | Non-thread-safe code, expensive to change |

## Workflow

### Step 1: Assess the Workload

Gather these signals before recommending:

1. **Traffic pattern**: Steady vs bursty? Requests per second?
2. **Current costs**: Monthly Lambda spend? Existing Savings Plans?
3. **Runtime**: Node.js, Java, .NET, or Python?
4. **Memory/CPU**: How much memory? CPU-bound or I/O-bound?
5. **Execution duration**: Average and P99?
6. **Concurrency readiness**: Thread safety (Node.js/Java/.NET)? Shared `/tmp` paths? Per-invocation DB connections?
7. **VPC**: Already in a VPC? Private resource access needed?

### Step 2: Build the Cost Comparison

REQUIRED: Present a cost comparison before recommending LMI. Compare at minimum:

| Scenario | When it wins |
|----------|-------------|
| Lambda on-demand | Low volume, bursty traffic |
| LMI on-demand | High volume, steady traffic |

Rule of thumb: LMI becomes cost-competitive when your Lambda spend exceeds ~$1,000/month with steady traffic.

Use the [LMI Pricing Calculator](https://aws-samples.github.io/sample-aws-lambda-managed-instances/) for accurate comparisons.

### Step 3: Configure the Deployment

- **Instance families** (~450 types): C-series (compute, .xlarge+), M-series (general, .large+), R-series (memory, .large+). ARM (Graviton) for best price-performance.
- **Memory-to-vCPU ratios**: 2:1 (compute), 4:1 (general, default), 8:1 (memory). Min 2 GB, max 32 GB.
- **Multi-concurrency defaults/vCPU**: Node.js 64, Java 32, .NET 32, Python 16.
- **Scaling**: MinExecutionEnvironments (default 3), MaxVCpuCount (default 400), TargetResourceUtilization.

See `configuration-guide.md` for decision trees and detailed tuning.

### Step 4: Migrate the Code

Review code for concurrency safety. LMI runs multiple invocations concurrently per execution environment:

- **Python**: Process-based isolation — globals are NOT shared. No thread-safety changes needed. Focus on `/tmp` conflicts and memory sizing.
- **Node.js**: Worker threads — globals shared within a worker. Requires async safety.
- **Java/.NET**: OS threads/Tasks — handler shared across threads. Requires full thread safety.

See `thread-safety.md` for the review checklist and `migration-patterns.md` for before/after code.

### Step 5: Set Up Infrastructure

1. Create two IAM roles: execution role (for the function) and operator role (for capacity provider EC2 management)
2. Configure VPC with subnets across multiple AZs (recommended 3+ for resiliency)
3. Create capacity provider with VPC config and scaling limits
4. Create or update function with capacity provider attachment
5. Publish a version (triggers instance provisioning)

See `infrastructure-setup.md` for CLI commands and SAM templates.

### Step 6: Validate and Cut Over

1. Deploy to a non-production environment first
2. Monitor CloudWatch: CPU utilization, memory, concurrency, throttle rate
3. Gradual traffic shift with weighted aliases (10% → 50% → 100%)
4. Compare costs after 1-2 weeks of production data
5. Decommission standard Lambda once stable

## Best Practices

### Configuration

- Start with 4:1 ratio and runtime default concurrency
- Use ARM (Graviton) unless x86 dependencies exist
- Let Lambda choose instance types unless specific hardware needed
- Set MaxVCpuCount to control cost ceiling
- Never set MinExecutionEnvironments below 3 in production (reduces multi-AZ coverage); non-prod can use 1

### Migration

- Start with I/O-heavy functions (benefit most from multi-concurrency)
- Review code for concurrency safety before attaching to capacity provider
- Use weighted aliases for gradual traffic shift
- Include request IDs in all log statements
- Initialize DB pools and SDK clients outside the handler
- Estimate total `/tmp` usage under max concurrency

### Operations

- Set CloudWatch alarms on throttle rate > 1% and CPU > 80%
- Never manually terminate LMI EC2 instances (delete the capacity provider instead)
- Always publish a version — unpublished functions cannot run on LMI

## Limits Quick Reference

| Resource | Limit |
|----------|-------|
| Memory | 2 GB min, 32 GB max |
| Concurrency/vCPU | 64 (Node.js), 32 (Java/.NET), 16 (Python) |
| Instance lifespan | ~12 hours (auto-replaced by Lambda) |
| EE lifespan | ~4 hours (auto-replaced by Lambda) |
| Runtimes | Node.js, Java, .NET, Python |
| Instance families | C (.xlarge+), M (.large+), R (.large+) |
| Scaling | Doubles within 5 min without throttles |

## Resources

- [Lambda Managed Instances Docs](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances.html)
- [Introducing LMI (AWS Blog)](https://aws.amazon.com/blogs/aws/introducing-aws-lambda-managed-instances-serverless-simplicity-with-ec2-flexibility/)
- [Build High-Performance Apps with LMI](https://aws.amazon.com/blogs/compute/build-high-performance-apps-with-aws-lambda-managed-instances/)
- [Migrating Functions to LMI](https://aws.amazon.com/blogs/compute/migrating-your-functions-to-aws-lambda-managed-instances/)
- [LMI Pricing Calculator](https://aws-samples.github.io/sample-aws-lambda-managed-instances/)
- [LMI Samples Repository](https://github.com/aws-samples/sample-aws-lambda-managed-instances)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
