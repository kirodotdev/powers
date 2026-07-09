# Generate Phase: Billing-Only Migration Plan

> Loaded by generate.md when estimation-billing.json exists.

**Execute ALL steps in order. Do not skip or optimize.**

**Known limitations:** Partial IaC discovery (mixed Terraform + billing-only services) is not yet supported. Confidence scoring per service based on billing SKU specificity is not yet implemented.

## Overview

This file produces a **conservative migration plan** with wider timelines and lower confidence thresholds than the infrastructure path. Billing-only data provides service-level spend but lacks configuration details (instance sizes, replication settings, networking topology). The plan accounts for this uncertainty with:

- Longer discovery refinement phase upfront
- Wider success criteria thresholds
- Explicit recommendation to run IaC discovery before executing the plan

## Prerequisites

Read the following artifacts from `$MIGRATION_DIR/`:

- `aws-design-billing.json` (REQUIRED) — Billing-based service mapping from Phase 3
- `estimation-billing.json` (REQUIRED) — Billing-only cost estimates from Phase 4
- `billing-profile.json` (REQUIRED) — GCP billing breakdown from Phase 1
- `preferences.json` (REQUIRED) — User migration preferences from Phase 2

If any required file is missing: **STOP**. Output: "Missing required artifact: [filename]. Complete the prior phase that produces it."

## Part 1: Context and Limitations

### What Billing Data Provides

- Service-level monthly spend (which GCP services are in use)
- Relative cost distribution (which services are most expensive)
- AI signal detection (whether AI/ML services appear in billing)
- SKU-level hints about usage patterns

### What Billing Data Does NOT Provide

- Instance sizes and configurations (CPU, memory, storage)
- Networking topology (VPC, subnets, firewall rules)
- Database engines and versions
- Replication and high-availability settings
- Inter-service dependencies
- Scaling configurations (min/max instances, autoscaling policies)
- Security configurations (IAM roles, encryption settings)

### Recommendation

> **For a more accurate migration plan, provide Terraform files and re-run discovery.**
> This billing-only plan is suitable for initial budgeting and stakeholder discussions,
> but must be refined with IaC discovery before executing the actual migration.

## Part 2: Conservative Timeline

A 15-week timeline with extended discovery and parallel-run phases to account for billing-only uncertainty.

### Stage 1: Discovery Refinement (Weeks 1-4)

- **Week 1-2**: Audit current GCP infrastructure manually
  - Document instance sizes, database configs, networking topology
  - Map dependencies between services
  - Identify stateful vs stateless services
  - Catalog secrets, environment variables, API keys
- **Week 3-4**: Refine AWS design based on discovered configurations
  - Update `aws-design-billing.json` unknowns with actual values
  - Re-estimate costs with refined configuration data
  - Identify any services that need different AWS targets
  - Consider running IaC discovery if Terraform files become available

### Stage 2: Service Migration (Weeks 5-9)

- **Week 5-6**: Provision AWS infrastructure
  - Set up VPC, subnets, security groups (based on discovery findings)
  - Provision compute, database, and storage resources
  - Configure IAM roles and policies
- **Week 7-8**: Deploy applications
  - Migrate application code and configurations
  - Set up CI/CD pipelines
  - Deploy to AWS staging environment
- **Week 9**: Integration testing
  - End-to-end testing on AWS
  - Performance baseline measurement
  - Data migration dry run

### Stage 3: Parallel Run (Weeks 10-12)

- Run both GCP and AWS simultaneously
- Compare performance, reliability, and costs
- Validate data consistency between environments
- Build confidence in AWS deployment
- Monitor for 2+ weeks before cutover decision

### Stage 4: Cutover and Validation (Weeks 13-15)

- **Week 13**: Execute cutover (DNS switch, traffic migration)
- **Week 14**: Intensive monitoring (48-hour watch period)
- **Week 15**: Stabilization and GCP teardown planning

## Part 3: Risk Assessment

Risks are higher for billing-only migrations due to configuration uncertainty.

| Risk                                         | Probability | Impact | Mitigation                                                          |
| -------------------------------------------- | ----------- | ------ | ------------------------------------------------------------------- |
| Incorrect service sizing                     | high        | high   | Extended discovery phase (Weeks 1-4); right-size after parallel run |
| Missing dependencies discovered late         | high        | medium | Manual dependency mapping in Week 1-2; extra buffer in timeline     |
| Data migration complexity underestimated     | medium      | high   | Dry run in Week 9; parallel run (Weeks 10-12) as safety net         |
| Cost overrun due to unknown configurations   | high        | medium | Set billing alerts at 80% of high estimate; weekly cost reviews     |
| Performance regression from incorrect sizing | medium      | high   | Parallel run comparison; resize before cutover                      |
| Longer timeline than planned                 | high        | medium | Build 3-week buffer into schedule; communicate 15-week plan upfront |
| Unmapped services block migration            | medium      | high   | Address unknowns in discovery refinement (Weeks 1-4)                |

## Part 4: Per-Service Migration Steps

For each service in `aws-design-billing.json.services[]`, generate a migration step template.

### Migration Step Template

```
Service: [gcp_service] → [aws_service]
Monthly Cost: $[monthly_cost] (GCP) → $[aws_mid] estimated (AWS)
Confidence: billing_inferred

Steps:
1. [ ] Determine actual configuration (instance size, storage, etc.)
   - TODO: Check GCP console or Terraform for [gcp_service] configuration
2. [ ] Provision AWS [aws_service] with discovered configuration
3. [ ] Migrate data (if applicable)
4. [ ] Test functionality and performance
5. [ ] Validate cost aligns with estimate

Unknowns:
- Instance sizing: TODO — verify in GCP console
- Scaling configuration: TODO — verify current autoscaling policies
- Dependencies: TODO — map which services depend on this one
```

### Example: Cloud Run to Fargate

```
Service: Cloud Run → Fargate
Monthly Cost: $450.00 (GCP) → $270-$630 estimated (AWS)
Confidence: billing_inferred
SKU Hints: CPU Allocation Time, Memory Allocation Time

Steps:
1. [ ] Determine actual configuration
   - TODO: Check CPU/memory allocation per Cloud Run service
   - TODO: Check concurrency and scaling settings
   - TODO: Check number of Cloud Run services
2. [ ] Create Fargate task definitions with matching CPU/memory
3. [ ] Set up ALB and target groups
4. [ ] Deploy container images to ECR
5. [ ] Configure autoscaling to match Cloud Run behavior
6. [ ] Test endpoint connectivity and performance

Unknowns:
- CPU allocation: TODO — check Cloud Run service configurations
- Memory allocation: TODO — check Cloud Run service configurations
- Number of services: TODO — count from GCP console or gcloud CLI
- Concurrency settings: TODO — check Cloud Run concurrency limits
```

### Unmapped Services

For each entry in `aws-design-billing.json.unknowns[]`:

```
Service: [gcp_service] — UNMAPPED
Monthly Cost: $[monthly_cost] (GCP)
Reason: [reason]
Suggestion: [suggestion]

Action Required:
- [ ] TODO: Manually identify the AWS equivalent for [gcp_service]
- [ ] TODO: Determine configuration and sizing
- [ ] TODO: Add to migration plan once mapped
```

## Part 5: Success Criteria

Relaxed thresholds reflecting billing-only uncertainty.

| Criteria                    | Target                     | Note                                                          |
| --------------------------- | -------------------------- | ------------------------------------------------------------- |
| Performance within baseline | Within 20% of GCP          | Wider than infra path (10%) due to sizing uncertainty         |
| Monitoring stability        | 48-hour watch period       | Longer than infra path (24 hours)                             |
| Post-migration stability    | 45-day observation         | Longer than infra path (30 days)                              |
| Cost variance               | Within 40% of mid estimate | Wider than infra path (15%) due to billing-only confidence    |
| Data integrity              | 100%                       | Same as infra path — no compromise on data                    |
| Service availability        | 99%                        | Lower than infra path (99.9%) initially, improve after tuning |

## Part 6: Output Format

Generate `generation-billing.json` in `$MIGRATION_DIR/` with the following schema:

```json
{
  "phase": "generate",
  "generation_source": "billing_only",
  "confidence": "low",
  "timestamp": "2026-02-26T14:30:00Z",
  "migration_plan": {
    "total_weeks": 15,
    "approach": "conservative_with_discovery",
    "phases": [
      {
        "name": "Discovery Refinement",
        "weeks": "1-4",
        "key_activities": [
          "Manual infrastructure audit",
          "Dependency mapping",
          "Configuration documentation",
          "Design refinement"
        ],
        "note": "Extended discovery to compensate for missing IaC data"
      },
      {
        "name": "Service Migration",
        "weeks": "5-9",
        "key_activities": [
          "AWS infrastructure provisioning",
          "Application deployment",
          "Integration testing",
          "Data migration dry run"
        ]
      },
      {
        "name": "Parallel Run",
        "weeks": "10-12",
        "key_activities": [
          "Dual environment operation",
          "Performance comparison",
          "Cost validation",
          "Confidence building"
        ]
      },
      {
        "name": "Cutover and Validation",
        "weeks": "13-15",
        "key_activities": [
          "DNS switch",
          "48-hour intensive monitoring",
          "Stabilization"
        ]
      }
    ],
    "services": [
      {
        "gcp_service": "Cloud Run",
        "aws_service": "Fargate",
        "monthly_cost_gcp": 450.00,
        "estimated_cost_aws_mid": 450.00,
        "confidence": "billing_inferred",
        "unknowns": ["instance sizing", "scaling config"]
      }
    ]
  },
  "risks": [
    {
      "category": "incorrect_sizing",
      "probability": "high",
      "impact": "high",
      "mitigation": "Extended discovery phase; right-size after parallel run",
      "phase_affected": "Discovery Refinement"
    }
  ],
  "success_metrics": {
    "performance_threshold": "within 20% of GCP baseline",
    "monitoring_period_hours": 48,
    "stability_period_days": 45,
    "cost_variance_threshold": "within 40% of mid estimate",
    "data_integrity": "100%",
    "availability_target": "99%"
  },
  "recommendation": {
    "approach": "Conservative migration with extended discovery",
    "confidence": "low",
    "iac_discovery_offered": true,
    "note": "For tighter estimates and a shorter timeline, provide Terraform files and re-run discovery.",
    "key_risks": [
      "Configuration uncertainty",
      "Missing dependency information",
      "Cost variance due to unknown sizing"
    ],
    "estimated_total_effort_hours": 720
  }
}
```

## Output Validation Checklist

- `phase` is `"generate"`
- `generation_source` is `"billing_only"`
- `confidence` is `"low"`
- `migration_plan.total_weeks` is 12-18 (conservative range)
- `migration_plan.phases` includes Discovery Refinement as first phase
- `migration_plan.services` covers every service from `aws-design-billing.json`
- `risks` array has at least 4 entries (more than infra path, reflecting higher uncertainty)
- Each risk `probability` is appropriately elevated (most are "medium" or "high")
- `success_metrics` has relaxed thresholds compared to infrastructure path
- `recommendation.iac_discovery_offered` is `true`
- `recommendation.confidence` is `"low"`
- Output is valid JSON

## Generate Phase Integration

The parent orchestrator (`generate.md`) uses `generation-billing.json` to:

1. Gate Stage 2 artifact generation — `generate-artifacts-billing.md` requires this file
2. Provide billing context to `generate-artifacts-docs.md` for MIGRATION_GUIDE.md
3. Set phase completion status in `.phase-status.json`
