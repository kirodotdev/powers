# Category A — Global/Strategic (Always Fires)

These foundational constraints gate everything downstream — region selection, service catalog, data residency, credits eligibility, compute platform, availability topology, and migration strategy.

Present questions with a conversational tone and brief context explaining why each matters.

---

## Q1 — Where are your users located?

**Rationale:** Geography drives AWS region selection and CDN strategy. It does NOT by itself justify multi-region architecture or Aurora Global Database — those decisions require understanding write patterns and RTO/RPO requirements from Q6 (uptime) and Q7 (maintenance window). Recommending multi-region based on geography alone would over-engineer most architectures and significantly increase cost.

> I need to understand your user base to recommend the right AWS region and CDN strategy.
>
> A) Single region (e.g., US-only, EU-only)
> B) Multi-region (2–3 regions, e.g., US + EU)
> C) Global (users worldwide, latency critical)
> D) I don't know

| Answer        | Recommendation Impact                                                                                                                                                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Single region | Deploy in closest AWS region to users; standard Route 53 routing                                                                                                                                                                          |
| Multi-region  | Primary region closest to majority; CloudFront for static assets and API caching; Route 53 latency-based routing — multi-region infrastructure deferred to Q6                                                                             |
| Global        | Primary region by largest user concentration; CloudFront globally distributed; Route 53 geolocation routing — Aurora Global Database and multi-region compute only if Q6 = Catastrophic AND write latency is a confirmed hard requirement |

Interpret:

```
A -> target_region: "<closest AWS region to GCP region in inventory>"
B -> target_region: "<closest AWS region>", replication: "cross-region"
C -> target_region: "<closest AWS region>", replication: "cross-region", cdn: "required"
D -> same as default (A)
```

Default: A — single region, closest AWS region to GCP region in inventory.

---

## Q2 — Do you have any compliance or regulatory requirements?

**Rationale:** Compliance requirements gate entire service categories and regions. A HIPAA customer cannot use the same architecture as an unconstrained startup.

> Compliance requirements determine which AWS services, regions, and configurations are available to you. This gates the entire architecture.
>
> A) None — No specific compliance requirements
> B) SOC 2 / ISO 27001 — Security and availability standards
> C) PCI DSS — Payment card data handling
> D) HIPAA — Healthcare data
> E) FedRAMP / Government — Federal compliance
> F) GDPR / Data residency — EU data sovereignty requirements
> G) I don't know
>
> _(Multiple selections allowed)_

| Answer            | Recommendation Impact                                                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| None              | Full service catalog available, any region                                                                                                 |
| SOC 2 / ISO 27001 | CloudTrail, Config, Security Hub enabled by default; encryption at rest required                                                           |
| PCI DSS           | Dedicated VPC with strict segmentation, WAF required, no shared tenancy for cardholder data, specific RDS encryption config                |
| HIPAA             | BAA-eligible services only, encryption in transit and at rest mandatory, specific logging requirements, us-east-1/us-west-2 preferred      |
| FedRAMP           | GovCloud regions required (us-gov-east-1, us-gov-west-1), GovCloud-specific service endpoints, limited service catalog                     |
| GDPR              | EU regions required (eu-west-1, eu-central-1), data residency constraints, no cross-region replication outside EU without explicit consent |

Interpret:

```
A -> (no constraint written — full service catalog available, any region)
B -> compliance: ["soc2"] — CloudTrail, Config, Security Hub enabled; encryption at rest required
C -> compliance: ["pci"] — Dedicated VPC, WAF required, strict segmentation
D -> compliance: ["hipaa"] — BAA-eligible services only, encryption mandatory, us-east-1/us-west-2 preferred
E -> compliance: ["fedramp"] — GovCloud regions required (us-gov-east-1, us-gov-west-1)
F -> compliance: ["gdpr"] — EU regions required (eu-west-1, eu-central-1), data residency constraints
G -> same as default (A) — no constraint assumed; verify with compliance team before production
```

Default: A — no constraint.

---

## Q3 — Approximately how much are you spending on GCP per month in total?

**Rationale:** Total GCP spend is the primary input for ARR estimation, which determines credits eligibility tier. Also provides a sanity check for cost estimates when billing data is not uploaded.

> Total GCP spend helps me estimate AWS credits eligibility and provides a cost baseline for the migration plan.
>
> A) < $1,000/month
> B) $1,000–$5,000/month
> C) $5,000–$20,000/month
> D) $20,000–$100,000/month
> E) > $100,000/month
> F) I don't know

**Billing enrichment:** If `billing-profile.json` exists, show:

> Your billing data shows ~$[total_monthly_spend]/month. Does this match your expectation?

| Answer                 | Recommendation Impact                                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| < $1,000/month         | AWS Activate credits eligibility (~$5K–$25K); cost estimates use conservative ranges                                         |
| $1,000–$5,000/month    | IW Migrate credits at 25% of ARR (~$3K–$15K/yr); mid-range estimates                                                         |
| $5,000–$20,000/month   | IW Migrate credits at 25% of ARR (~$15K–$60K/yr); Reserved Instance recommendations included                                 |
| $20,000–$100,000/month | IW Migrate credits at 25% of ARR (~$60K–$300K/yr); Savings Plans analysis; AWS Specialist consultation eligible (>=$60K ARR) |
| > $100,000/month       | MAP eligibility (>$500K ARR); Enterprise support tier; dedicated migration team engagement                                   |

Interpret (write constraint only — do NOT surface the downstream notes to the user):

```
A -> gcp_monthly_spend: "<$1K"
B -> gcp_monthly_spend: "$1K-$5K"
C -> gcp_monthly_spend: "$5K-$20K"
D -> gcp_monthly_spend: "$20K-$100K"
E -> gcp_monthly_spend: ">$100K"
F -> same as default (billing-informed bucket if billing data exists, otherwise B)
```

Default: If `billing-profile.json` exists, use the billing-informed bucket from Step 2 extraction. Otherwise B — `gcp_monthly_spend: "$1K-$5K"`.

---

## Q4 — _(Skipped)_

Credits program eligibility is inferred from Q3 (GCP spend) alone. No question asked.

Default: `funding_stage`: not set.

---

## Q5 — Do you need to run workloads across multiple cloud providers?

**Rationale:** Multi-cloud portability is an early exit condition that immediately determines the compute recommendation without needing further questions. If multi-cloud is required, Kubernetes (EKS) is the only portable abstraction layer.

> Multi-cloud portability is an immediate decision point — if required, Kubernetes (EKS) is the only portable abstraction, and we can skip several compute questions.
>
> A) Yes, multi-cloud required
> B) No, AWS-only is acceptable
> C) I don't know

| Answer                    | Recommendation Impact                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Yes, multi-cloud required | **Immediate EKS recommendation** — Kubernetes is the only portable abstraction layer. Skip Q8. ECS Fargate excluded. |
| No, AWS-only acceptable   | Full compute decision tree continues — EKS vs ECS Fargate evaluated based on K8s sentiment (Q8)                      |

Interpret:

```
A -> compute: "eks" — Immediate EKS recommendation. EARLY EXIT: skip Q8.
B -> (no constraint written — full compute decision tree continues)
C -> same as default (B) — assume AWS-only
```

Default: B — no constraint, evaluate full compute options.

---

## Q6 — If your application went down unexpectedly right now, what would happen?

**Rationale:** Availability requirements drive database engine selection, deployment topology, and whether multi-AZ is mandatory. Aurora Global Database and multi-region compute are only recommended when Catastrophic is selected AND Q1 confirms global users — both signals are required.

**Context for user:** When asking, include these descriptions so the user can self-select accurately:

- **Inconvenient** — users can wait, no revenue impact (e.g., internal tool, dev/staging environment, hobby project)
- **Significant Issue** — users notice and complain, some revenue impact, but workarounds exist (e.g., B2B SaaS with email support SLA)
- **Mission-Critical** — direct revenue loss per minute of downtime, SLA obligations to customers, needs fast recovery (e.g., e-commerce checkout, paid API)
- **Catastrophic** — regulatory, safety, or major financial consequences; every minute of downtime is measurable loss (e.g., financial transactions, healthcare systems, real-time trading)

> Availability requirements drive database engine selection, deployment topology, and whether multi-AZ is mandatory.
>
> A) INCONVENIENT — Users can wait, brief outages tolerable (5–30 min)
> B) SIGNIFICANT ISSUE — Customers frustrated, revenue loss
> C) MISSION-CRITICAL — Cannot tolerate outages, SLA violations
> D) CATASTROPHIC — Regulatory, safety, or major financial consequences per minute of downtime
> E) I don't know

| Answer            | Recommendation Impact                                                                                                                                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Inconvenient      | Single-AZ RDS acceptable, standard ECS/EKS deployment, no special HA requirements                                                                                                                                                                      |
| Significant Issue | Multi-AZ RDS required, ALB with health checks, auto-scaling groups                                                                                                                                                                                     |
| Mission-Critical  | Aurora Multi-AZ (higher availability than RDS), multi-AZ mandatory, Route 53 health checks; single-region with fast failover is sufficient for most mission-critical workloads                                                                         |
| Catastrophic      | If Q1 = Global: Aurora Global Database + active-active multi-region + Route 53 failover routing; If Q1 = Single/Multi-region: Aurora Multi-AZ with aggressive RTO/RPO targets is sufficient — global infrastructure not warranted without global users |

Interpret:

```
A -> availability: "single-az" — Single-AZ RDS acceptable, standard deployment
B -> availability: "multi-az" — Multi-AZ RDS required, ALB with health checks, auto-scaling
C -> availability: "multi-az-ha" — Aurora Multi-AZ, multi-AZ mandatory, Route 53 health checks
D -> IF Q1 = C (Global): availability: "multi-region" — Aurora Global Database + active-active multi-region + Route 53 failover
     IF Q1 = A or B: availability: "multi-az-ha" — Aurora Multi-AZ with aggressive RTO/RPO (global infra not warranted without global users)
E -> same as default (B) — assume multi-AZ for safety
```

Default: B — `availability: "multi-az"`.

---

## Q7 — Do you have a scheduled maintenance window where downtime is acceptable?

**Rationale:** Determines cutover strategy and which database migration tooling is recommended. Zero-downtime migrations require significantly more complex infrastructure (blue/green, traffic shifting). With a maintenance window, databases can be taken offline briefly and migrated with native tools — without one, live replication via DMS is required.

**Database migration tooling notes:**

- For PostgreSQL databases <10GB: **pg_dump/pg_restore** is sufficient.
- For larger PostgreSQL databases (>10GB): **pgcopydb** offers parallel table copying and index rebuilding, significantly reducing migration time within the same maintenance window.
- pgcopydb's CDC mode requires `wal_level=logical` on Cloud SQL, which must be enabled explicitly.

> The maintenance window determines your migration cutover strategy and which database migration tooling we recommend. Zero-downtime migrations require significantly more complex infrastructure.
>
> A) Yes — weekly maintenance window (e.g., Sunday 2–4am)
> B) Yes — monthly maintenance window only
> C) No — zero downtime required, must use blue/green or rolling deployment
> D) Flexible — we can schedule one if needed
> E) I don't know

| Answer         | Recommendation Impact                                                                                                                                                                                                              |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Weekly window  | Standard cutover with DNS switchover during window; **pg_dump/pg_restore** for PostgreSQL <10GB; **pgcopydb** for larger databases — parallel copying cuts migration time significantly; no DMS licensing, no replication lag risk |
| Monthly window | Cutover timed to monthly window; pg_dump/pg_restore or **pgcopydb** depending on DB size; blue/green for application layer                                                                                                         |
| Zero downtime  | **AWS DMS required** for live database replication; blue/green deployment for application layer; Aurora blue/green deployments; Route 53 weighted routing for traffic shifting                                                     |
| Flexible       | Recommend scheduling a weekly window to enable pg_dump/pgcopydb approach; falls back to DMS if window cannot be arranged                                                                                                           |

Interpret:

```
A -> cutover_strategy: "maintenance-window-weekly" — pg_dump/pg_restore or pgcopydb recommended; standard cutover with DNS switchover
B -> cutover_strategy: "maintenance-window-monthly" — pg_dump/pg_restore or pgcopydb recommended; blue/green for app layer
C -> cutover_strategy: "zero-downtime" — AWS DMS required for live DB replication; blue/green deployment; Route 53 weighted routing
D -> cutover_strategy: "flexible" — Recommend scheduling weekly window for pg_dump approach; DMS fallback
E -> same as default (D) — assume flexible
```

Default: D — `cutover_strategy: "flexible"`.
