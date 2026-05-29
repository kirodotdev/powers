# Compute Mappings

## google_cloud_run_service / google_cloud_run_v2_service

**Purpose:** Serverless container execution platform

**Default:** aws_ecs_service (ECS Fargate)

**Rationale for default:** Fargate is the recommended AWS equivalent to Cloud Run — fully managed containers, auto-scaling, better dev/prod parity than App Runner, broader feature set (service discovery, load balancer integration, capacity providers).

**Candidates:**
- aws_ecs_service (ECS Fargate)
- aws_apprunner_service (App Runner)
- aws_lambda_function (Lambda)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| timeout | > 900s | aws_ecs_service | strong | Exceeds Lambda maximum, App Runner max is 120s for request timeout |
| timeout | <= 120s | aws_apprunner_service | moderate | Within App Runner and Lambda limits, App Runner is simplest |
| timeout | 121s - 900s | aws_ecs_service | moderate | Exceeds App Runner, within Lambda, but long timeout suggests long-running work |
| memory | > 10240MB | aws_ecs_service | strong | Exceeds Lambda maximum (10GB) |
| memory | <= 3008MB | aws_lambda_function | weak | Within Lambda limits, but not a strong signal alone |
| min_instances | > 0 | aws_ecs_service | moderate | Always-on workload, Fargate more cost-effective than Lambda provisioned concurrency |
| min_instances | 0 or absent | aws_apprunner_service | weak | Scale-to-zero, all three support this |
| max_instances | > 100 | aws_ecs_service | moderate | High scale needs, Fargate has more predictable scaling |
| concurrency | 1 | aws_lambda_function | moderate | Single-request processing aligns with Lambda model |
| concurrency | > 80 | aws_ecs_service | moderate | High concurrency per instance suggests long-lived container |
| gpu | required | aws_ecs_service | strong | Only Fargate supports GPU tasks |
| allow_public | false | aws_ecs_service | moderate | Internal-only services are simpler on Fargate with private ALB |

**Eliminators:**
- timeout > 900s → eliminates aws_lambda_function (Lambda max 900s)
- timeout > 120s → eliminates aws_apprunner_service (App Runner request timeout max 120s)
- memory > 10240MB → eliminates aws_lambda_function (Lambda max 10GB)
- memory > 30720MB → eliminates aws_apprunner_service (App Runner max 30GB)
- gpu required → eliminates aws_lambda_function and aws_apprunner_service

**Peek at secondaries:** No

**1:Many Expansion:**

If App Runner:
- aws_apprunner_service — primary
- aws_apprunner_auto_scaling_configuration_version — if custom scaling needed
- aws_apprunner_vpc_connector — if VPC access needed
- aws_ecr_repository — for container image storage

If Lambda:
- aws_lambda_function — primary
- aws_lambda_function_url — if public HTTP endpoint needed (replaces Cloud Run URL)
- aws_cloudwatch_log_group — Lambda logging
- aws_ecr_repository — if using container image (vs zip deployment)

If ECS Fargate:
- aws_ecs_service — primary
- aws_ecs_task_definition — container configuration
- aws_ecs_cluster — if no cluster exists yet (shared across services)
- aws_lb — Application Load Balancer for HTTP traffic
- aws_lb_target_group — routing to ECS tasks
- aws_lb_listener — HTTP/HTTPS listener
- aws_ecr_repository — for container image storage
- aws_cloudwatch_log_group — ECS logging

**Source Config to Carry Forward:**
- container_image — determines image source (GCR/AR → ECR migration needed)
- memory — determines memory allocation
- cpu — determines CPU allocation
- timeout — determines timeout configuration
- min_instances — determines min capacity / desired count
- max_instances — determines max capacity / auto-scaling limits
- concurrency — determines target tracking scaling metric
- env_vars — determines environment variables (references may need updating)
- secret_env_vars — determines secrets references (Secret Manager ARNs)
- vpc_connector — determines VPC configuration
- allow_public — determines load balancer scheme (internet-facing vs internal)
- service_account — determines IAM role (resolved during secondary mapping)

---

## google_container_cluster

**Purpose:** Kubernetes container orchestration

**Default:** aws_ecs_service (ECS Fargate)

**Rationale for default:** ECS Fargate is the standard AWS migration target for GKE workloads — managed container execution, no node management, integrates natively with VPC, ALB, and IAM.

**Candidates:**
- ECS Fargate (via `aws_ecs_service` + `aws_ecs_task_definition`)
- ECS EC2 (same resources, different launch type)
- EKS (`aws_eks_cluster`)

**Preference shortcuts (check preferences.json first):**
- `compute: "eks"` → always EKS. Skip all other criteria.
- `kubernetes: "eks-managed"` → EKS.
- `kubernetes: "ecs-fargate"` → ECS Fargate.
- `kubernetes: "eks-or-ecs"` → continue rubric evaluation.

**Eliminators:**
- GPU node pools (any `google_container_node_pool` with accelerators configured) → eliminates ECS Fargate (limited GPU support), favor ECS EC2
- 10+ node pools of different machine families → eliminates ECS Fargate and ECS EC2, favor EKS (complex topology requires Kubernetes orchestration)

**Signals:**

| Signal | Favors | Weight | Reason |
|---|---|---|---|
| Single node pool, standard machine type (e2-standard, n1-standard) | ECS Fargate | strong | Straightforward workload, no need for node management |
| Multiple node pools | EKS | moderate | Complex topology is harder to replicate on ECS |
| Cluster description mentions "web service", "API", "backend" | ECS Fargate | moderate | Typical ECS Fargate workload |
| High node count (initial or max > 20) | EKS | moderate | Large fleets benefit from Kubernetes orchestration |
| Workload Insights or Dataplane V2 features used | EKS | weak | Advanced networking features map better to EKS |

**1:Many Expansion — ECS Fargate (most common case):**

**MANDATORY — always add ALL of the following to `new_aws_resources` when mapping a GKE cluster to ECS:**

| Resource | Always required? | Condition |
|---|---|---|
| `aws_ecs_cluster` | Yes, unless already created by a prior cluster | First ECS cluster in the migration |
| `aws_ecs_service` | Yes | One per node pool |
| `aws_ecs_task_definition` | Yes | One per node pool |
| `aws_ecr_repository` | **Always** | Container images must be re-pushed from GCR/Artifact Registry to ECR. Number of repos = number of distinct workloads. Cannot run on ECS without ECR. |
| `aws_lb` | **Always** (unless cluster is explicitly documented as internal-only with no external traffic) | GKE has implicit ingress. ECS has no external entry point without ALB. |
| `aws_lb_target_group` | Yes, with ALB | One per service family |
| `aws_lb_listener` | Yes, with ALB | HTTP port 80 and HTTPS port 443 |
| `aws_appautoscaling_target` | When node pool has `autoscaling` block | Registers ECS service as a scalable target |
| `aws_appautoscaling_policy` | When `aws_appautoscaling_target` is added | Defines scaling behavior (target tracking on CPU/memory) |

**PROHIBITED omissions:**
- Never omit `aws_ecr_repository`. Container images cannot be pulled from GCR on ECS.
- Never omit `aws_lb` unless the cluster is explicitly documented as internal-only. "I don't see an ingress resource" is not a sufficient reason to omit the ALB — GKE clusters with external workloads rely on the cluster's default ingress.
- Never omit `aws_appautoscaling_target` + `aws_appautoscaling_policy` when node pool autoscaling is configured.

**1:Many Expansion — EKS:**
- `aws_eks_cluster` — primary
- `aws_eks_node_group` — one per `google_container_node_pool`
- `aws_iam_role` — EKS cluster role
- `aws_iam_role` — EKS node group role
- `aws_ecr_repository` — always required (same reason as ECS)

**Source Config to Carry Forward:**
- name — cluster name
- location / region — determines AWS region and AZ placement
- network — determines VPC placement (resolved from google_compute_network mapping)
- subnetwork — determines subnet placement
- logging_service / monitoring_service — determines CloudWatch logging/monitoring config
- min_master_version — Kubernetes version reference
- workload_identity_config — determines IAM trust policy configuration (absorbed into task role)

---

## google_container_node_pool

**This is a secondary resource. Its target depends on what `google_container_cluster` mapped to.**

**CRITICAL: `google_container_node_pool` is NOT eligible for Pass 1. It must be evaluated in Pass 2 AFTER its parent cluster is resolved.**

**When cluster → ECS Fargate or ECS EC2:**
- **Target: `absorbed`**
- Node pool parameters translate into ECS task definition config and service scaling config — there are no nodes to manage on Fargate.
- Node pool does NOT become a 1:1 AWS resource.
- `aws_ecs_service` and `aws_ecs_task_definition` appear in `new_aws_resources` of the cluster, not as direct mapping targets of the node pool.

Carry forward these fields into the reason (they inform task definition and service config):
- `machine_type` — translates to vCPU/memory allocation for the task definition
- `disk_size_gb` — informs ephemeral storage config on the task
- `min_node_count` — becomes minimum task count / desired count baseline
- `max_node_count` — becomes maximum task count for auto-scaling policy
- `initial_node_count` — use as desired count if no billing data is available
- `autoscaling` block present → trigger `aws_appautoscaling_target` + `aws_appautoscaling_policy` in `new_aws_resources`

**When cluster → EKS:**
- **Target: `aws_eks_node_group`**
- One node pool → one EKS managed node group.
- Carry forward: `machine_type`, `min_node_count`, `max_node_count`, `disk_size_gb`, `node_count`

---

## google_compute_instance

**Purpose:** Virtual machines

**Default:** aws_instance (EC2)

**Candidates:**
- aws_instance (EC2)

**Signals:** None — direct 1:1 mapping. EC2 is the only candidate.

**Eliminators:** None

**Peek at secondaries:** No

**1:Many Expansion:**
- aws_instance — primary
- aws_ebs_volume — if additional disks attached (beyond root)
- aws_eip — if static external IP assigned

**Source Config to Carry Forward:**
- machine_type — determines instance_type (translation needed by Pillar 4)
- zone — determines availability_zone
- boot_disk.image — determines ami
- boot_disk.size — determines root volume size
- network_interface.network — determines VPC/subnet placement
- metadata.startup_script — determines user_data
- tags — determines instance tags
- service_account — determines IAM instance profile (resolved during secondary mapping)

---

## google_cloudfunctions_function / google_cloudfunctions2_function

**Purpose:** Serverless functions

**Default:** aws_lambda_function (Lambda)

**Candidates:**
- aws_lambda_function (Lambda)

**Signals:** None — direct 1:1 mapping. Cloud Functions and Lambda are equivalent models.

**Eliminators:**
- timeout > 900s (Cloud Functions 2nd gen supports up to 3600s) → Lambda cannot handle this, flag for user. Recommend ECS Fargate as alternative.
- memory > 10240MB → Lambda cannot handle this, flag for user.

**Peek at secondaries:** No

**1:Many Expansion:**
- aws_lambda_function — primary
- aws_cloudwatch_log_group — logging
- aws_lambda_event_source_mapping — if triggered by Pub/Sub (maps to SQS trigger)
- aws_lambda_permission — if triggered by HTTP (API Gateway or function URL)

**Source Config to Carry Forward:**
- runtime — determines runtime
- entry_point — determines handler
- memory_mb — determines memory_size
- timeout — determines timeout
- environment_variables — determines environment variables
- vpc_connector — determines VPC configuration
- source_archive_bucket / source_archive_object — determines deployment package source
- trigger_http — determines function URL or API Gateway need
- event_trigger — determines event source mapping

---

## Secondary: google_service_account

**Behavior:** Service accounts are identity secondaries that provide IAM credentials to compute resources. They map to AWS IAM roles based on what the primary compute resource became.

**Mapping Behavior:**

When google_cloud_run_service maps to:
- aws_apprunner_service → service account maps to aws_iam_role (execution role for App Runner)
- aws_lambda_function → service account maps to aws_iam_role (execution role for Lambda)
- aws_ecs_service → service account maps to aws_iam_role (task execution role for ECS)

When google_cloudfunctions_function maps to:
- aws_lambda_function → service account maps to aws_iam_role (execution role for Lambda)

When google_container_cluster maps to:
- aws_eks_cluster → service account maps to aws_iam_role (IRSA - IAM Roles for Service Accounts via OpenID Connect provider)
- aws_ecs_cluster → service account maps to aws_iam_role (cluster execution role)

When google_compute_instance maps to:
- aws_ec2_instance → service account maps to aws_iam_role (instance profile attached to EC2)

**Implementation Notes:**
1. Service account IAM bindings (google_project_iam_member, google_*_iam_member) become policy statements on the AWS role
2. Service account email becomes role assume role policy (who can assume this role)
3. Service account keys should be migrated to AWS Secrets Manager
4. For Kubernetes (EKS), uses IRSA to bind service accounts to IAM roles via OpenID Connect

**Skip Condition:**
If the primary compute resource is skipped or not mapped to AWS, skip this service account.

---

## google_app_engine_application

**Purpose:** Fully managed application hosting platform

**Default:** aws_ecs_service (ECS Fargate)

**Rationale for default:** App Engine applications are typically web apps or APIs. Fargate provides similar managed container hosting with auto-scaling, no server management, and better integration with the broader AWS ecosystem.

**Candidates:**
- aws_ecs_service (ECS Fargate) — general-purpose, best for most App Engine apps
- aws_amplify_app (Amplify Hosting) — for static/JAMstack apps with backend APIs
- aws_apprunner_service (App Runner) — simpler setup, fewer configuration options

**Signals:**

| Signal | Favors | Weight | Reason |
|---|---|---|---|
| Standard environment (Python, Java, Node.js, Go, PHP, Ruby) | Fargate | strong | Container-based deployment matches standard env |
| Flexible environment (custom runtime/Dockerfile) | Fargate | strong | Custom containers are Fargate's strength |
| Static site with API backend | Amplify | moderate | Amplify handles static hosting + API routes |
| Simple web service, minimal config | App Runner | weak | App Runner is simpler but less configurable |

**1:Many Expansion (Fargate):**
- aws_ecs_service
- aws_ecs_task_definition
- aws_lb (Application Load Balancer)
- aws_lb_target_group
- aws_lb_listener
