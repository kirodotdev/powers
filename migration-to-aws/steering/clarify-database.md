# Category D — Database Model (If Database Resources Present)

_Fire when:_ Database resources present (Cloud SQL, Spanner, Memorystore).

Traffic pattern and I/O intensity determine the Aurora configuration — standard vs I/O-Optimized, read replicas, Serverless v2, or DSQL.

---

## Database Engine Detection

Before asking questions, detect the database engine from IaC (`database_version` in `google_sql_database_instance`). State what was found:

> "I see Cloud SQL for PostgreSQL (or MySQL) in your Terraform."

Handle non-Aurora-compatible engines:

| Detected Engine          | Migration Target                                                  | Notes                                |
| ------------------------ | ----------------------------------------------------------------- | ------------------------------------ |
| Cloud SQL for PostgreSQL | Aurora PostgreSQL                                                 | Direct migration path                |
| Cloud SQL for MySQL      | Aurora MySQL                                                      | Direct migration path                |
| Cloud SQL for SQL Server | **RDS for SQL Server**                                            | Aurora doesn't support SQL Server    |
| Spanner                  | Aurora DSQL (global distributed) or DynamoDB (key-value patterns) | Migration path differs significantly |
| Firestore                | DynamoDB                                                          | NoSQL migration                      |
| AlloyDB                  | Aurora PostgreSQL                                                 | Closest equivalent                   |

If the engine is not PostgreSQL or MySQL, note that Aurora doesn't support it and flag the appropriate RDS or DynamoDB target. Ask the user to confirm if detection is ambiguous.

---

## Q12 — What does your database traffic pattern look like?

_Fire when:_ Cloud SQL present in inventory. Skip when: no Cloud SQL.

**Rationale:** Database traffic pattern determines whether standard Aurora is sufficient or whether more specialized options (read replicas, DSQL, Serverless v2) are needed. Asking about the pattern rather than whether they have a problem avoids leading the answer.

**Context for user:** When asking, give concrete examples so the user can pattern-match to their situation:

- **Steady, predictable load** — consistent query volume day-to-day, no major spikes (e.g., internal CRUD app, content CMS)
- **Read-heavy with occasional write spikes** — mostly reads with bursts of writes at certain times (e.g., reporting dashboards, catalog browsing with periodic bulk imports)
- **Write-heavy or globally distributed writes** — high write throughput or writes coming from multiple regions (e.g., IoT ingestion, multi-region user-generated content, event logging)
- **Rapidly growing** — traffic is noticeably increasing month over month, doubling every few months (e.g., post-launch growth, viral product)

> Understanding your database traffic pattern helps me recommend the right Aurora configuration — standard vs I/O-Optimized, read replicas, or Serverless v2.
>
> A) Steady, predictable load — consistent volume, no major spikes
> B) Read-heavy with occasional write spikes — mostly reads, periodic write bursts
> C) Write-heavy or globally distributed writes — high write throughput or multi-region writes
> D) Rapidly growing — doubling every few months
> E) N/A — We don't use Cloud SQL
> F) I don't know

| Answer                              | Recommendation Impact                                                                                            |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Steady, predictable                 | Standard Aurora Multi-AZ; straightforward sizing from current Cloud SQL config                                   |
| Read-heavy with write spikes        | Aurora with read replicas; auto-scaling read capacity                                                            |
| Write-heavy or globally distributed | **Aurora DSQL considered** for global active-active; architecture review flagged                                 |
| Rapidly growing                     | Aurora with headroom planning; **Aurora Serverless v2** for elastic scaling; revisit sizing at 6-month intervals |

Interpret:

```
A -> database_traffic: "steady" — Standard Aurora Multi-AZ
B -> database_traffic: "read-heavy" — Aurora with read replicas; auto-scaling read capacity
C -> database_traffic: "write-heavy-global" — Aurora DSQL considered; architecture review flagged
D -> database_traffic: "rapidly-growing" — Aurora Serverless v2 for elastic scaling
E -> (no constraint written)
F -> same as default (A) — assume steady traffic
```

Default: A — `database_traffic: "steady"`.

---

## Q13 — What's your typical database I/O workload?

_Fire when:_ Cloud SQL present in inventory. Skip when: no Cloud SQL.

**Rationale:** Aurora has two pricing modes — standard and I/O-Optimized. The right choice depends on actual I/O intensity. Choosing wrong can mean paying 40% more than necessary.

> Aurora has two pricing modes — standard and I/O-Optimized. Choosing wrong can mean paying 40% more than necessary.
>
> A) Low (< 1,000 IOPS) — Mostly reads, infrequent writes
> B) Medium (1,000–10,000 IOPS) — Balanced workload
> C) High (> 10,000 IOPS) — Write-heavy, high transactions
> D) N/A — We don't use Cloud SQL
> E) I don't know

| Answer                     | Recommendation Impact                                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------- |
| Low (< 1,000 IOPS)         | Aurora standard pricing recommended                                                       |
| Medium (1,000–10,000 IOPS) | Aurora standard pricing; flag I/O-Optimized as option if workload grows                   |
| High (> 10,000 IOPS)       | **Aurora I/O-Optimized recommended** — can save up to 40% vs standard at high I/O volumes |

Interpret:

```
A -> db_io_workload: "low" — Aurora standard pricing
B -> db_io_workload: "medium" — Aurora standard; flag I/O-Optimized as option if workload grows
C -> db_io_workload: "high" — Aurora I/O-Optimized recommended (up to 40% savings at high I/O)
D -> (no constraint written)
E -> same as default (B) — assume medium I/O
```

Default: B — `db_io_workload: "medium"`.
