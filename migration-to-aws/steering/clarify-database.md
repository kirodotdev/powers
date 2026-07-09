# Category D — Database Model (If Database Resources Present)

_Fire when:_ Database resources present (Cloud SQL, Spanner, Memorystore).

**Q6 (`availability`) selects RDS vs Aurora** for Cloud SQL PostgreSQL/MySQL — see `clarify-global.md` Q6. Q12–Q13 tune sizing and storage **within** the family Q6 chose. **Q12–Q13 never override Q6.**

---

## Database Engine Detection

Before asking questions, detect the database engine from IaC (`database_version` in `google_sql_database_instance`). State what was found:

> "I see Cloud SQL for PostgreSQL (or MySQL) in your Terraform."

| Detected Engine          | Migration Target family                                           | Notes                                |
| ------------------------ | ----------------------------------------------------------------- | ------------------------------------ |
| Cloud SQL for PostgreSQL | **RDS PostgreSQL** or **Aurora PostgreSQL** (per Q6)              | Q6 selects family; engine from IaC   |
| Cloud SQL for MySQL      | **RDS MySQL** or **Aurora MySQL** (per Q6)                        | Q6 selects family; engine from IaC   |
| Cloud SQL for SQL Server | **RDS for SQL Server**                                            | Aurora doesn't support SQL Server    |
| Spanner                  | Aurora DSQL (global distributed) or DynamoDB (key-value patterns) | Migration path differs significantly |
| Firestore                | DynamoDB                                                          | NoSQL migration                      |
| AlloyDB                  | Aurora PostgreSQL                                                 | Closest equivalent                   |

If the engine is not PostgreSQL or MySQL, note the appropriate RDS or DynamoDB target. Ask the user to confirm if detection is ambiguous.

**Skip Q12/Q13/Q13b** when Cloud SQL (PostgreSQL or MySQL) is not present in inventory — auto-detect from IaC; no separate screening question required.

---

## Q12 — What does your database traffic pattern look like?

_Fire when:_ Cloud SQL (PostgreSQL or MySQL) present in inventory. Skip when: no Cloud SQL.

**Auto-extract signal (dev-tier):** When **all** Cloud SQL instances match dev pattern (`db-f1-micro`, `db-g1-small`, or `tier` contains `micro`/`small` with `availability_type: ZONAL`), extract `database_traffic: "steady"` with `chosen_by: "extracted"` and **skip Q12**. When instances mix dev and prod tiers, ask Q12.

**Rationale:** Traffic pattern informs capacity planning on the target **already chosen by Q6**.

**Context for user:** Give concrete examples so the user can pattern-match:

- **Steady, predictable load** — consistent query volume day-to-day, no major spikes (e.g., internal CRUD app, content CMS)
- **Read-heavy with occasional write spikes** — mostly reads with bursts of writes at certain times (e.g., reporting dashboards, catalog browsing with periodic bulk imports)
- **Write-heavy or globally distributed writes** — high write throughput or writes coming from multiple regions (e.g., IoT ingestion, multi-region user-generated content, event logging)
- **Rapidly growing** — traffic is noticeably increasing month over month, doubling every few months (e.g., post-launch growth, viral product)

> Understanding your database traffic pattern helps me recommend the right sizing on AWS — within the RDS or Aurora family Q6 already selected.
>
> A) Steady, predictable load — consistent volume, no major spikes
> B) Read-heavy with occasional write spikes — mostly reads, periodic write bursts
> C) Write-heavy or globally distributed writes — high write throughput or multi-region writes
> D) Rapidly growing — doubling every few months
> E) N/A — We don't use Cloud SQL
> F) I don't know

| Answer                              | When Q6 = Inconvenient or Significant Issue (**RDS** path)                    | When Q6 = Mission-Critical or Catastrophic (**Aurora** path)                     |
| ----------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Steady, predictable                 | Size **RDS** from Cloud SQL config; single-AZ or Multi-AZ per Q6              | **Aurora** standard Multi-AZ; size from Cloud SQL config                         |
| Read-heavy with write spikes        | **RDS** with read replicas where justified; size writer for spikes            | **Aurora** with read replicas; auto-scaling read capacity where supported        |
| Write-heavy or globally distributed | Size **RDS** writer; flag architecture review if multi-region writes required | **Aurora DSQL** considered for global active-active; architecture review flagged |
| Rapidly growing                     | **RDS** with headroom on instance class; plan capacity reviews                | **Aurora** with headroom; **Aurora Serverless v2** for elastic scaling           |

Interpret:

```
A -> database_traffic: "steady"
B -> database_traffic: "read-heavy"
C -> database_traffic: "write-heavy-global"
D -> database_traffic: "rapidly-growing"
E -> (no constraint written)
F -> same as default (A)
```

Default: A — `database_traffic: "steady"`.

---

## Q13 — What's your typical database I/O workload?

_Fire when:_ Cloud SQL (PostgreSQL or MySQL) present in inventory. Skip when: no Cloud SQL.

**Auto-extract signal (dev-tier):** Same dev-tier pattern as Q12 — extract `db_io_workload: "low"` with `chosen_by: "extracted"` and **skip Q13** only when **all** instances are dev-tier. When instances mix dev and prod tiers, ask Q13.

**Rationale:** On AWS, storage and I/O billing differ between RDS and Aurora. This captures how disk-heavy the workload is. **Q6 still governs RDS vs Aurora** — this question only selects storage/I/O options within that family.

> A) Low (< 1,000 IOPS) — Mostly reads, infrequent writes
> B) Medium (1,000–10,000 IOPS) — Balanced workload
> C) High (> 10,000 IOPS) — Write-heavy, high transactions
> D) N/A — We don't use Cloud SQL
> E) I don't know

| Answer                     | When Q6 = Inconvenient or Significant Issue (**RDS** path) | When Q6 = Mission-Critical or Catastrophic (**Aurora** path) |
| -------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| Low (< 1,000 IOPS)         | **gp3** (default RDS storage)                              | **Aurora Standard** storage/I/O billing                      |
| Medium (1,000–10,000 IOPS) | **gp3**; note optional Provisioned IOPS if I/O grows       | **Aurora Standard**; note optional switch to I/O-Optimized   |
| High (> 10,000 IOPS)       | **io2** or Provisioned IOPS on RDS                         | **Aurora I/O-Optimized**                                     |

Interpret:

```
A -> db_io_workload: "low"
B -> db_io_workload: "medium"
C -> db_io_workload: "high"
D -> (no constraint written)
E -> same as default (B)
```

Default: B — `db_io_workload: "medium"`.

---

## Q13b — Approximately how large is your primary database?

_Fire when:_ Cloud SQL (PostgreSQL or MySQL) present in inventory. Skip when: no Cloud SQL, or engine is SQL Server (DMS is always recommended for SQL Server regardless of size).

**Rationale:** Database size is the primary driver of migration tooling selection. pg_dump/pg_restore is sufficient for small databases but becomes impractically slow above ~10GB within a typical maintenance window. pgcopydb's parallel copy cuts migration time by 3–5x for medium databases. Very large databases (>500GB) require DMS for continuous replication regardless of whether a maintenance window exists.

**Auto-detect signal:** Read disk size from `google_sql_database_instance`: `config.disk_size`, `config.disk_size_gb`, or `gcp_config.disk_size_gb`. Map to Q13b band and **skip Q13b** when unambiguous:

| Disk size (GB) | `db_size` value | Skip Q13b?                     |
| -------------- | --------------- | ------------------------------ |
| < 10           | `"<10GB"`       | Yes — `chosen_by: "extracted"` |
| 10 – 99        | `"10-100GB"`    | Yes — `chosen_by: "extracted"` |
| 100 – 499      | `"100-500GB"`   | Yes — `chosen_by: "extracted"` |
| ≥ 500          | `">500GB"`      | Yes — `chosen_by: "extracted"` |

If multiple instances disagree, ask Q13b. Record raw GB in `metadata.inventory_clarifications.db_size_gb` when extracted.

> Database size determines which migration tool we recommend — this directly affects your migration window length and risk.
>
> A) < 10 GB — small, pg_dump/pg_restore completes in minutes
> B) 10 GB – 100 GB — medium, pgcopydb recommended for parallel copy
> C) 100 GB – 500 GB — large, pgcopydb required; plan for multi-hour window
> D) > 500 GB — very large, AWS DMS strongly recommended regardless of window
> E) I don't know

| Answer          | Tooling Recommendation                                                                                                                                                        |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| < 10 GB         | **pg_dump/pg_restore** — fast, simple, no extra tooling required                                                                                                              |
| 10 GB – 100 GB  | **pgcopydb** — parallel table copy + index rebuild; 3–5x faster than pg_dump; requires `wal_level=logical` on Cloud SQL if CDC mode used                                      |
| 100 GB – 500 GB | **pgcopydb** required — pg_dump at this size risks exceeding maintenance window; plan for 4–12 hour window depending on table count and index complexity                      |
| > 500 GB        | **AWS DMS strongly recommended** — single-pass export/import at this scale is high-risk; DMS provides continuous replication with minimal cutover window (minutes, not hours) |
| I don't know    | Default to pgcopydb (safer than pg_dump at unknown scale); flag for user to verify before migration                                                                           |

Interpret:

```
A -> design_constraints.db_size: { value: "<10GB", chosen_by: "user" } — pg_dump/pg_restore recommended
B -> design_constraints.db_size: { value: "10-100GB", chosen_by: "user" } — pgcopydb recommended
C -> design_constraints.db_size: { value: "100-500GB", chosen_by: "user" } — pgcopydb required; flag extended window
D -> design_constraints.db_size: { value: ">500GB", chosen_by: "user" } — AWS DMS strongly recommended; flag in migration plan
E -> design_constraints.db_size: { value: "unknown", chosen_by: "default" } — default to pgcopydb; flag for verification
```

Default: E — `design_constraints.db_size: { value: "unknown", chosen_by: "default" }` (default to pgcopydb; safer than pg_dump at unknown scale).
