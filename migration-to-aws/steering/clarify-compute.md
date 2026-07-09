# Category B — Configuration Gaps + Category C — Compute Model

This file covers two related categories:

- **Category B** — Configuration gaps for billing-source inventories (factual questions to fill inferred data)
- **Category C** — Compute model questions (platform and traffic pattern decisions)

---

## Category B — Configuration Gaps (Billing-Source Inventories Only)

_Fire when:_ `gcp-resource-inventory.json` exists with `metadata.source == "billing"` AND at least one resource has `config_confidence == "assumed"`.
_Skip when:_ `metadata.source == "terraform"`.

These fill factual gaps in the inferred inventory. Answers update the inventory understanding — they do not produce design constraints directly.

- **Cloud SQL HA**: Single-zone or high-availability? _(ask if SKU says Zonal)_
  > Default: assume Zonal is intentional.
- **Cloud Run service count**: How many distinct services? _(ask if Cloud Run billing is present)_
  > Default: assume 1 service.
- **Memorystore memory size**: How much memory (GB)? _(ask if cannot be derived from usage units)_
  > Default: estimate from usage amount.
- **Cloud Functions generation**: Gen 1 or Gen 2? _(ask if SKU does not specify)_
  > Default: assume Gen 1.

Record Category B answers in `metadata.inventory_clarifications`.

---

## Category C — Compute Model (If Compute Resources Present)

_Fire when:_ Compute resources present (Cloud Run, Cloud Functions, GKE, GCE).

---

## Q8 — How does your team feel about managing Kubernetes?

_Fire when:_ GKE cluster present AND Q5 != A (multi-cloud). Skip when: Q5 = A (already resolved to EKS) or no GKE in inventory.

**Rationale:** When multi-cloud is not required (Q5=No) and GKE is detected, team sentiment is the deciding factor between EKS and ECS Fargate. This is subjective and cannot be inferred from IaC.

**Context for user:** When asking, frame it practically so the user gives an honest answer rather than aspirational:

- **Love it / K8s expert** — your team writes Helm charts, debugs CrashLoopBackOff in their sleep, and actively chose K8s
- **Neutral / Competent** — K8s works, your team can operate it, but it's not a passion project
- **Frustrated / Steep curve** — K8s feels like overhead; your team spends more time fighting YAML than shipping features

> Your team's Kubernetes experience determines whether we recommend EKS (Kubernetes on AWS) or ECS Fargate (simpler managed containers).
>
> A) Love it / Team is K8s expert
> B) Neutral / Competent with K8s
> C) Frustrated / Learning curve steep
> D) N/A — We don't use Kubernetes
> E) I don't know

| Answer                   | Recommendation Impact                                                                                        |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Love it / K8s expert     | EKS recommended — preserves existing Kubernetes investment and expertise                                     |
| Neutral / Competent      | EKS recommended with managed node groups to reduce operational burden                                        |
| Frustrated / Steep curve | **Strong ECS Fargate recommendation** — eliminates Kubernetes management entirely; simpler operational model |

_Note: If Q5=Yes (multi-cloud), this question is skipped and EKS is already decided._

Interpret:

```
A -> kubernetes: "eks-managed" — EKS recommended, preserves K8s investment
B -> kubernetes: "eks-or-ecs" — EKS with managed node groups to reduce operational burden
C -> kubernetes: "ecs-fargate" — Strong ECS Fargate recommendation, eliminates K8s management
D -> (no constraint written — no K8s workloads)
E -> same as default (B) — assume neutral, evaluate both EKS and ECS
```

Default: B — `kubernetes: "eks-or-ecs"`.

---

## Q9 — Do any of your services need WebSocket support or long-lived connections?

_Fire when:_ Compute resources present AND WebSocket usage cannot be determined from inventory.

**Rationale:** WebSocket support affects load balancer configuration. App Runner is now on KTLO (keep the lights on) and is no longer recommended for any workload — this question confirms whether ALB WebSocket configuration is needed in templates.

> WebSocket support affects load balancer configuration. This confirms whether ALB WebSocket configuration is needed in the migration templates.
>
> A) Yes — Real-time features, WebSockets, persistent connections
> B) No — Standard HTTP/HTTPS only
> C) I don't know

| Answer                  | Recommendation Impact                                                         |
| ----------------------- | ----------------------------------------------------------------------------- |
| Yes — WebSockets needed | ECS Fargate or EKS required; ALB with WebSocket support included in templates |
| No — HTTP only          | ECS Fargate recommended for simple stateless services                         |

Interpret:

```
A -> websocket: "required" — ALB with WebSocket support, ECS Fargate or EKS required
B -> (no constraint written)
C -> same as default (B) — assume no WebSocket; can be reconfigured later
```

Default: B — no constraint.

---

## Q10 — What's your typical traffic pattern for your Cloud Run services?

_Fire when:_ Cloud Run present in inventory. Skip when: no Cloud Run.

**Rationale:** Cloud Run's scale-to-zero is its primary cost advantage. If traffic is constant, that advantage disappears and AWS becomes cost-competitive or cheaper. This drives whether we recommend migrating Cloud Run at all.

> Cloud Run's scale-to-zero is its primary cost advantage. Understanding your traffic pattern helps me determine whether migrating Cloud Run to AWS makes financial sense.
>
> A) Business hours only (9am–5pm weekdays, ~40 hrs/week)
> B) Active most of the day (16–20 hours, ~120 hrs/week)
> C) Constant 24/7 traffic (~168 hrs/week)
> D) N/A — We don't use Cloud Run
> E) I don't know

| Answer              | Recommendation Impact                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| Business hours only | AWS likely 40–50% MORE expensive — recommend staying on Cloud Run or flagging cost increase prominently |
| Active most of day  | Moderate cost difference — present both options with cost comparison                                    |
| Constant 24/7       | AWS costs similar or cheaper — ECS Fargate recommended as straightforward migration                     |

Interpret:

```
A -> cloud_run_traffic_pattern: "business-hours" — AWS likely 40-50% MORE expensive; flag cost increase
B -> cloud_run_traffic_pattern: "most-of-day" — Moderate cost difference; present both options
C -> cloud_run_traffic_pattern: "constant-24-7" — AWS costs similar or cheaper; ECS Fargate recommended
D -> (no constraint written — Cloud Run not used)
E -> same as default (C) — assume constant traffic for conservative estimate
```

Default: C — `cloud_run_traffic_pattern: "constant-24-7"`.

---

## Q11 — Approximately how much are you spending on Cloud Run per month?

_Fire when:_ Cloud Run present in inventory. Skip when: no Cloud Run.

**Rationale:** Absolute spend determines whether the migration math makes financial sense regardless of traffic pattern. Low-spend Cloud Run workloads are rarely worth the migration complexity.

> Absolute Cloud Run spend determines whether the migration math makes financial sense regardless of traffic pattern.
>
> A) < $100/month
> B) $100–$500/month
> C) $500–$1,500/month
> D) > $1,500/month
> E) N/A — We don't use Cloud Run
> F) I don't know

| Answer            | Recommendation Impact                                                            |
| ----------------- | -------------------------------------------------------------------------------- |
| < $100/month      | Recommend staying on Cloud Run — migration cost and complexity exceeds savings   |
| $100–$500/month   | Present cost comparison; migration may make sense if consolidating to AWS        |
| $500–$1,500/month | Fixed-cost AWS options (ECS Fargate reserved capacity) become attractive         |
| > $1,500/month    | Strong case for migration to ECS Fargate with Savings Plans or reserved capacity |

Interpret:

```
A -> cloud_run_monthly_spend: "<$100" — Recommend staying on Cloud Run; migration cost exceeds savings
B -> cloud_run_monthly_spend: "$100-$500" — Present cost comparison; migration may make sense if consolidating
C -> cloud_run_monthly_spend: "$500-$1500" — Fixed-cost AWS options attractive (ECS Fargate reserved)
D -> cloud_run_monthly_spend: ">$1500" — Strong case for ECS Fargate with Savings Plans
E -> (no constraint written)
F -> same as default (B)
```

Default: B — `cloud_run_monthly_spend: "$100-$500"`.
