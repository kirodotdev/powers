# Regional Capabilities and Limitations

## Purpose

This document describes region-specific capabilities and limitations for AWS HealthOmics. Not all HealthOmics features are available in all regions.

## Authoritative Source

For the most up-to-date information on supported regions, instance types, and features, refer to the [AWS HealthOmics public documentation](https://docs.aws.amazon.com/omics/latest/dev/memory-and-compute-tasks.html) and the [HealthOmics endpoints and quotas page](https://docs.aws.amazon.com/general/latest/gr/healthomics-quotas.html). IF the information in this document appears inconsistent with what public documentation states, defer to the public documentation.

## When to Reference This Document

Reference this document when:
- The user asks about feature availability in a specific region
- The user encounters errors related to Storage (sequence/reference stores) or Analytics (variant/annotation stores)
- The user is choosing which region to deploy workflows in
- The user asks about GPU instance type availability

## Regional Feature Availability

### Full-Feature Regions

The following regions support **all** HealthOmics capabilities (Workflows, Storage, and Analytics):

| Region | Region Code | Workflows | Storage | Analytics |
|---|---|---|---|---|
| US West (Oregon) | us-west-2 | Yes | Yes | Yes |
| US East (N. Virginia) | us-east-1 | Yes | Yes | Yes |
| Europe (Ireland) | eu-west-1 | Yes | Yes | Yes |
| Europe (London) | eu-west-2 | Yes | Yes | Yes |
| Europe (Frankfurt) | eu-central-1 | Yes | Yes | Yes |
| Israel (Tel Aviv) | il-central-1 | Yes | Yes | Yes |
| Asia Pacific (Singapore) | ap-southeast-1 | Yes | Yes | Yes |

**All features include**:
- Private workflows (custom WDL, Nextflow, CWL)
- Ready2Run workflows (pre-built sample workflows)
- Sequence stores and Reference stores (HealthOmics Storage)
- Variant stores and Annotation stores (HealthOmics Analytics)
- ECR Pull-Through Cache support

### Workflows-Only Regions

The following regions support **Workflows only** (no Storage or Analytics):

| Region | Region Code | Workflows | Storage | Analytics |
|---|---|---|---|---|
| US East (Ohio) | us-east-2 | Yes | No | No |
| Asia Pacific (Tokyo) | ap-northeast-1 | Yes | No | No |
| Asia Pacific (Seoul) | ap-northeast-2 | Yes | No | No |

**Supported features**:
- Private workflows (custom WDL, Nextflow, CWL)
- All standard CPU instance types
- GPU instance types (availability varies — see below)
- VPC networking and Configurations
- ECR Pull-Through Cache

**Not available in these regions**:
- Ready2Run workflows
- Sequence stores (HealthOmics Storage)
- Reference stores (HealthOmics Storage)
- Variant stores (HealthOmics Analytics)
- Annotation stores (HealthOmics Analytics)

## GPU Instance Type Availability

HealthOmics supports the following GPU instance families: g4dn, g5, and g6. Not all GPU families are available in every region.

Notable regional GPU limitations:
- **il-central-1 (Tel Aviv)** — g5 only
- **ap-southeast-1 (Singapore)** — g4dn only
- **eu-west-1 (Ireland), eu-west-2 (London), and eu-central-1 (Frankfurt)** — g4dn and g5 only
- **ap-northeast-2 (Seoul), ap-northeast-1 (Tokyo), and us-east-2 (Ohio)** — g4dn, g5, and g6 available. g5.12xlarge and larger sizes not currently available.

## When to Use Each Region Type

### Use Full-Feature Regions When:
- You need to store genomic data in HealthOmics Storage (sequence stores, reference stores)
- You need to query variant or annotation data using HealthOmics Analytics
- You want to use Ready2Run sample workflows
- You need all HealthOmics capabilities in one location

### Use Workflows-Only Regions When:
- You have custom workflows and manage data in S3
- You want to keep compute close to other AWS resources in that region
- You only need workflow execution without integrated storage or analytics

## Related Documentation
- For VPC subnet configuration and Availability Zone information, see [VPC Setup SOP](./vpc-setup.md)
- For running workflows, see [Running a Workflow SOP](./running-a-workflow.md)
- For workflow development, see [Workflow Development SOP](./workflow-development.md)
- For ECR Pull-Through Cache setup, see [ECR Pull-Through Cache SOP](./ecr-pull-through-cache.md)
