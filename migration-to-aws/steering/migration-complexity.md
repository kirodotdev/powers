# Migration Complexity Tiers

Shared classification loaded by `generate-billing.md` and `generate-infra.md` to right-size migration timelines. The AI path (`generate-ai.md`) self-sizes from workload profiles and does not use this file.

## Inputs

Collect these values from prior-phase artifacts before classifying:

| Input                | Source Artifact                                   | Key                                                                                     |
| -------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Service count        | `aws-design-billing.json` or `aws-design.json`    | `metadata.total_services`                                                               |
| Monthly spend        | `billing-profile.json` or `estimation-infra.json` | `summary.total_monthly_spend` or `current_costs.gcp_monthly`                            |
| Has databases        | Design artifact `services[]`                      | `aws_service` in {RDS, Aurora, DynamoDB, ElastiCache, DocumentDB, MemoryDB, OpenSearch} |
| Has stateful storage | Design artifact `services[]`                      | `aws_service` in {EFS, FSx, S3} with replication or versioning hints in `sku_hints`     |
| Has AI workloads     | `estimation-ai.json` exists                       | File presence                                                                           |
| Availability         | `preferences.json`                                | `design_constraints.availability`                                                       |
| Compliance           | `preferences.json`                                | `design_constraints.compliance`                                                         |
| Multi-region         | Design artifact `services[]`                      | More than one distinct `aws_config.region` value                                        |

## Tier Definitions

Evaluate from **Large down to Small**. The first tier whose condition matches is the result (highest-matching-tier wins).

### Large

ANY of the following:

- Service count >= 9
- Monthly spend > $10,000
- Multi-region deployment (services span 2+ AWS regions)
- AI workloads coexist with infrastructure (`estimation-ai.json` exists AND (`estimation-infra.json` OR `estimation-billing.json`) also exists)
- Compliance requirements present (`compliance` is not empty/none)

### Medium

NOT Large, and ANY of the following:

- Service count 4-8
- Monthly spend $1,000-$10,000
- Has databases
- Availability is `multi-az`

### Small

NOT Large, NOT Medium. Equivalently, ALL of:

- Service count <= 3
- Monthly spend < $1,000
- No databases or stateful storage with replication
- No AI workloads alongside infrastructure
- Availability is `single-az` or unspecified
- No compliance requirements

## Timeline Ranges

### Billing-Only Path

| Tier   | Weeks | Effort Hours | Approach                      |
| ------ | ----- | ------------ | ----------------------------- |
| Small  | 2-4   | 40-80        | `compressed`                  |
| Medium | 6-10  | 160-400      | `standard_with_discovery`     |
| Large  | 12-18 | 480-720      | `conservative_with_discovery` |

### Infrastructure Path

| Tier   | Weeks | Effort Hours | Approach                   |
| ------ | ----- | ------------ | -------------------------- |
| Small  | 3-6   | 80-160       | `compressed`               |
| Medium | 8-12  | 240-480      | `phased_cluster_migration` |
| Large  | 12-16 | 400-640      | `phased_cluster_migration` |

## Stage Templates

### Billing-Only Path

#### Small (2-4 weeks)

No parallel-run stage. Discovery and provisioning overlap. Cutover uses maintenance window.

- **Stage 1: Discovery + Provisioning (Week 1)**
  - Quick audit of GCP infrastructure (few services, low complexity)
  - Provision AWS VPC, compute, and supporting resources
  - Configure IAM roles and security groups
- **Stage 2: Deploy + Test (Week 2)**
  - Deploy applications to AWS
  - Run functional and integration tests
  - Validate cost tracking against estimates
- **Stage 3: Cutover + Validation (Weeks 3-4)**
  - Execute cutover during maintenance window (DNS switch)
  - 24-hour intensive monitoring
  - Stabilization and GCP teardown planning

#### Medium (6-10 weeks)

Shortened parallel run. Discovery takes 1-2 weeks instead of 4.

- **Stage 1: Discovery Refinement (Weeks 1-2)**
  - Audit current GCP infrastructure
  - Document instance sizes, database configs, networking topology
  - Map dependencies between services
  - Refine AWS design based on discovered configurations
- **Stage 2: Service Migration (Weeks 3-5)**
  - Provision AWS infrastructure
  - Deploy applications and configure CI/CD
  - Integration testing and data migration dry run
- **Stage 3: Parallel Run (Weeks 6-7)**
  - Run both environments simultaneously
  - Compare performance, reliability, and costs
  - Validate data consistency
- **Stage 4: Cutover and Validation (Weeks 8-10)**
  - Execute cutover (DNS switch, traffic migration)
  - 48-hour intensive monitoring
  - Stabilization and GCP teardown planning

#### Large (12-18 weeks)

Full conservative plan. Extended discovery, full parallel run.

- **Stage 1: Discovery Refinement (Weeks 1-4)**
  - Weeks 1-2: Manual infrastructure audit, dependency mapping, configuration documentation
  - Weeks 3-4: Refine AWS design, re-estimate costs, identify services needing different AWS targets
- **Stage 2: Service Migration (Weeks 5-9)**
  - Weeks 5-6: Provision AWS infrastructure (VPC, compute, databases, storage)
  - Weeks 7-8: Deploy applications, set up CI/CD, migrate to staging
  - Week 9: Integration testing, performance baseline, data migration dry run
- **Stage 3: Parallel Run (Weeks 10-12)**
  - Run both GCP and AWS simultaneously
  - Compare performance, reliability, and costs
  - Validate data consistency between environments
  - Monitor for 2+ weeks before cutover decision
- **Stage 4: Cutover and Validation (Weeks 13-15+)**
  - Execute cutover (DNS switch, traffic migration)
  - 48-hour intensive monitoring
  - Stabilization and GCP teardown planning

### Infrastructure Path

#### Small (3-6 weeks)

Compressed setup. PoC is a 2-day smoke test, not a 2-week phase. No data migration stage (small tier excludes databases by definition).

- **Stage 1: Setup (Week 1)**
  - Provision VPC, subnets, IAM, monitoring baseline
  - Set up CI/CD pipeline for Terraform
- **Stage 2: Deploy + Smoke Test (Week 2)**
  - Deploy all clusters (few services, shallow dependency graph)
  - Run integration tests and validate connectivity
  - Confirm cost tracking matches estimates
  - Go/No-Go checkpoint
- **Stage 3: Cutover (Weeks 3-4)**
  - Execute cutover per `preferences.json` strategy
  - 24-48 hour monitoring
  - Keep GCP as hot standby
- **Stage 4: Validation + Cleanup (Weeks 5-6)**
  - Monitor AWS performance for 1 week
  - Compare costs to projections
  - Begin GCP teardown planning

#### Medium (8-12 weeks)

Standard phased plan. Same as the existing `generate-infra.md` default stages. Apply the existing data-migration skip rule: if no databases/storage, compress Cutover to Weeks 8-9 and Validation to Week 10.

#### Large (12-16 weeks)

Extended infrastructure deployment. Extra time for complex dependency graphs, multi-cluster orchestration, and extended parallel validation.

- **Stage 1: Setup (Weeks 1-2)** — same as medium
- **Stage 2: Proof of Concept (Weeks 3-4)** — same as medium
- **Stage 3: Infrastructure Deployment (Weeks 5-8)** — extended by 1 week for additional clusters and cross-cluster networking
- **Stage 4: Data Migration (Weeks 9-11)** — extended for large data volumes and complex replication topologies (skip if no databases/storage)
- **Stage 5: Cutover (Weeks 12-13)** — same structure, adjusted week numbers
- **Stage 6: Validation and Cleanup (Weeks 14-16)** — extended monitoring before GCP teardown

## Risk Scaling by Tier

Risk probabilities should be adjusted based on complexity tier:

| Risk Category                    | Small       | Medium | Large  |
| -------------------------------- | ----------- | ------ | ------ |
| Incorrect service sizing         | low         | medium | high   |
| Missing dependencies             | low         | medium | high   |
| Data migration complexity        | n/a (no DB) | medium | high   |
| Cost overrun                     | low         | medium | high   |
| Performance regression           | low         | medium | medium |
| Timeline overrun                 | low         | medium | high   |
| Unmapped services block progress | low         | medium | medium |

## Success Criteria Scaling by Tier

Tighter thresholds for simpler migrations (fewer unknowns, less variance).

### Billing-Only Path

| Criteria                    | Small                      | Medium                     | Large                      |
| --------------------------- | -------------------------- | -------------------------- | -------------------------- |
| Performance within baseline | Within 15% of GCP          | Within 20% of GCP          | Within 20% of GCP          |
| Monitoring stability        | 24-hour watch period       | 48-hour watch period       | 48-hour watch period       |
| Post-migration stability    | 14-day observation         | 30-day observation         | 45-day observation         |
| Cost variance               | Within 25% of mid estimate | Within 30% of mid estimate | Within 40% of mid estimate |
| Data integrity              | 100%                       | 100%                       | 100%                       |
| Service availability        | 99%                        | 99%                        | 99%                        |

### Infrastructure Path

| Criteria                    | Small                      | Medium                     | Large                      |
| --------------------------- | -------------------------- | -------------------------- | -------------------------- |
| Performance within baseline | Within 10% of GCP          | Within 10% of GCP          | Within 10% of GCP          |
| Monitoring stability        | 24-hour watch period       | 24-hour watch period       | 48-hour watch period       |
| Post-migration stability    | 14-day observation         | 30-day observation         | 30-day observation         |
| Cost variance               | Within 10% of mid estimate | Within 15% of mid estimate | Within 15% of mid estimate |
| Data integrity              | 100%                       | 100%                       | 100%                       |
| Service availability        | 99.9%                      | 99.9%                      | 99.9%                      |

## Output

After classification, the consuming generate file must include a `complexity_tier` field in its output JSON:

```json
{
  "complexity_tier": "small",
  "complexity_inputs": {
    "service_count": 2,
    "monthly_spend": 75.71,
    "has_databases": false,
    "has_stateful_storage": false,
    "has_ai_workloads": false,
    "availability": "single-az",
    "compliance": "none",
    "multi_region": false
  }
}
```

These fields go at the top level of the generation JSON (alongside `phase`, `generation_source`, etc.).
