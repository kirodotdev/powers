# Compute Services Design Rubric

**Applies to:** Cloud Run (v1/v2), Cloud Functions (Gen 1/Gen 2), Compute Engine, GKE, App Engine

**Table lookup first:** Check `design-ref-fast-path.md` **Direct Mappings** for this Terraform type.

- `google_cloud_run_service`, `google_cloud_run_v2_service`, `google_cloudfunctions_function`, and `google_cloudfunctions2_function` are currently in Direct Mappings and usually resolve with `confidence: "deterministic"` when row conditions are met.
- `google_compute_instance`, `google_container_cluster`, and `google_app_engine_application` are not direct-mapped in `design-ref-fast-path.md`; use the rubric below (typically `confidence: "inferred"`).
- If a resource is not eligible for Direct Mappings (or row conditions are not met), use the rubric below.

## Eliminators (Hard Blockers)

| GCP Service     | AWS        | Blocker                                                                                                                                                        |
| --------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cloud Run       | Lambda     | Execution time >15 min → use Fargate                                                                                                                           |
| Cloud Run       | Fargate    | GPU workload or >16 vCPU or >120 GB memory → use EC2                                                                                                           |
| Cloud Functions | Lambda     | Python version not supported (e.g., Python 2.7) → use custom runtime on Fargate                                                                                |
| GKE             | EKS        | Custom CRI incompatible → manual workaround or ECS                                                                                                             |
| Any             | App Runner | **Closed to new customers (April 30 2026).** Do not target App Runner for new migrations. Use Fargate (default), Lambda (event-driven), or EKS (K8s required). |

## Signals (Decision Criteria)

### Cloud Run / App Engine

- **Always-on** or **cold-start sensitive** → Fargate (not Lambda)
- **Stateless microservice** + **<15 min execution** → Lambda
- **HTTP-only** + **container-native** → Fargate preferred (better dev/prod parity)

### Cloud Functions

- **Event-driven** + **<15 min** + **Python/Node/Go** → Lambda
- **Always-on or long** → run as Container on Fargate or ECS

### Compute Engine (VMs)

- **Always-on workload** → EC2 (reserved or on-demand based on cost sensitivity)
- **Batch/periodic jobs** → EC2 with Auto Scaling (scale to 0 in dev)
- **Windows-only workload** → EC2 (Lambda/Fargate support limited)

### GKE

- **Kubernetes orchestration explicitly required** (`kubernetes = "eks-managed"` or `"eks-or-ecs"` in `preferences.json`) → EKS
- **Default / no explicit K8s preference** (`kubernetes = "ecs-fargate"` or absent):
  - → **Fargate** (absent kubernetes preference resolves to Fargate, not EKS — teams that want EKS answer A or B in Clarify)

## 6-Criteria Rubric

Apply in order; first match wins:

1. **Eliminators**: Does GCP config violate AWS constraints? If yes: switch to alternative
2. **Operational Model**: Managed (Lambda, Fargate) vs Self-Hosted (EC2, EKS)?
   - Prefer managed unless: Always-on + high baseline cost → EC2
3. **User Preference**: From `preferences.json`: `design_constraints.kubernetes`, `design_constraints.cost_sensitivity`?
   - If `kubernetes = "eks-managed"` → EKS (preserves K8s investment)
   - If `kubernetes = "eks-or-ecs"` → EKS with managed node groups (user is competent with K8s)
   - If `kubernetes = "ecs-fargate"` → Fargate (simpler managed containers)
   - If `kubernetes` is **absent** → Fargate (treat same as `"ecs-fargate"` — do not default to EKS)
   - If `cost_sensitivity` present and high → prefer Fargate (lower operational cost)
4. **Feature Parity**: Does GCP config require AWS-unsupported features?
   - Example: GCP auto-scaling to zero + cold-start-sensitive → Fargate (not Lambda)
5. **Cluster Context**: Are other resources in this cluster using EKS/EC2/Fargate?
   - Prefer same platform (affinity)
6. **Simplicity**: Fewer resources = higher score
   - Fargate (1 service) > EC2 (N services for ASG + monitoring)

## Examples

### Example 1: Cloud Run (stateless API)

- GCP: `google_cloud_run_service` (memory=512MB, timeout=60s, min_instances=1)
- Signals: HTTP, stateless, always-on
- Criterion 1 (Eliminators): PASS (60s < 15min doesn't apply; stateless OK)
- Criterion 2 (Operational Model): FARGATE preferred
- → **AWS: Fargate (0.5 CPU, 1 GB memory)**
- Confidence: `inferred` (rubric-based — Cloud Run is not in fast-path)

### Example 2a: Cloud Functions (event processor, short-running)

- GCP: `google_cloudfunctions_function` (runtime=python39, timeout=540s)
- Signals: Event-driven, 540s = 9 minutes (< 15min limit)
- Criterion 1 (Eliminators): PASS on timeout (540s < 900s)
- Criterion 2 (Operational Model): Lambda preferred for event-driven + short-running
- → **AWS: Lambda with EventBridge trigger**
- Confidence: `inferred`

### Example 2b: Cloud Functions (long-running batch processor)

- GCP: `google_cloudfunctions_function` (runtime=python39, timeout=1200s)
- Signals: Event-driven but 1200s = 20 minutes (> 15min limit)
- Criterion 1 (Eliminators): FAIL on timeout (1200s > 900s) → **cannot use Lambda**
- Criterion 2 (Operational Model): Fargate (managed + can handle longer execution)
- → **AWS: Fargate (0.5 CPU, 1 GB memory) with EventBridge trigger**
- Confidence: `inferred`

### Example 3: Compute Engine (background job)

- GCP: `google_compute_instance` (machine_type=e2-medium, region=us-central1, startup_script=...)
- Signals: Periodic batch job (inferred from startup script), always-on
- Criterion 1 (Eliminators): PASS
- Criterion 2 (Operational Model): EC2 (explicit compute control)
- Criterion 3 (User Preference): If `design_constraints.gcp_monthly_spend` indicates cost sensitivity, prefer auto-scaling → EC2 + ASG (scale to 0)
- → **AWS: EC2 t3.medium + Auto Scaling Group (min=0 in dev)**
- Confidence: `inferred`

## Output Schema

```json
{
  "gcp_type": "google_cloud_run_service",
  "gcp_address": "example-service",
  "gcp_config": {
    "memory_mb": 512,
    "timeout_seconds": 60
  },
  "aws_service": "Fargate",
  "aws_config": {
    "cpu": "0.5",
    "memory_mb": 1024,
    "region": "us-east-1"
  },
  "confidence": "inferred",
  "rationale": "Rubric: Cloud Run (stateless, <15min) → Fargate (always-on, managed)",
  "rubric_applied": [
    "Eliminators: PASS",
    "Operational Model: Managed preferred",
    "User Preference: N/A",
    "Feature Parity: Full",
    "Cluster Context: Fargate affinity",
    "Simplicity: Fargate (1 service)"
  ]
}
```
