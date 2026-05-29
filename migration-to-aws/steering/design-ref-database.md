# Database Mappings

## google_sql_database_instance

**Purpose:** Managed relational database (MySQL, PostgreSQL)

**Default:** aws_db_instance (RDS) or aws_rds_cluster (Aurora)

**Rationale for default:** AWS RDS is the closest equivalent to Cloud SQL — fully managed, multi-AZ support, automated backups. Aurora is preferred for higher scale requirements.

**Candidates:**
- aws_db_instance (RDS MySQL or RDS PostgreSQL)
- aws_rds_cluster (Aurora MySQL or Aurora PostgreSQL)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| database_version | >= MySQL 8.0 or PostgreSQL 13+ | aws_rds_cluster | moderate | Aurora supports latest versions better |
| backup_configuration.enabled | true | aws_db_instance or aws_rds_cluster | weak | Both support backups equally |
| backup_configuration.point_in_time_recovery_enabled | true | aws_rds_cluster | moderate | Aurora has superior PITR capabilities |
| settings.backup_config.transaction_log_retention_days | > 7 | aws_rds_cluster | moderate | Aurora supports longer retention |
| settings.ip_configuration.require_ssl | true | aws_db_instance or aws_rds_cluster | weak | Both enforce SSL |
| tier | Scaling for high IOPS | aws_rds_cluster | moderate | Aurora better for scaling to high I/O |
| scale (inferred from current load) | Large (> 100 GB, > 10K QPS) | aws_rds_cluster | strong | Aurora handles scale better |
| scale (inferred from current load) | Standard (< 100 GB, < 5K QPS) | aws_db_instance | moderate | RDS sufficient for smaller workloads |

**Eliminators:**
- Custom engine features not in AWS → flag for user, may need workaround

**Peek at secondaries:** Yes — check for google_sql_database resources and backup configurations

**1:Many Expansion (RDS):**
- aws_db_instance — primary
- aws_db_parameter_group — if custom parameters needed
- aws_db_option_group — if DB options needed
- aws_db_subnet_group — for multi-AZ placement
- aws_security_group — for database access control

**1:Many Expansion (Aurora):**
- aws_rds_cluster — cluster definition
- aws_rds_cluster_instance — one or more instances (2+ for HA)
- aws_rds_cluster_parameter_group — custom cluster parameters
- aws_db_subnet_group — for multi-AZ placement
- aws_security_group — for database access control
- aws_rds_cluster_backup — if backing up to specific window needed

**Source Config to Carry Forward:**
- database_version — determines engine/engine_version
- tier — determines instance_class or cluster instance type
- region — determines AWS region
- availability_type — determines multi_az (HA requirement)
- backup_configuration — determines backup retention and window
- settings.ip_configuration — determines db_subnet_group and security groups
- name — determines database name
- user credentials — determines master username/password (migrate to Secrets Manager)

---

## google_firestore_database

**Purpose:** NoSQL document database with real-time capabilities

**Default:** aws_dynamodb_table (DynamoDB)

**Rationale for default:** DynamoDB is the closest AWS equivalent to Firestore — serverless NoSQL, auto-scaling, document-oriented data model. Similar pricing model (read/write units).

**Candidates:**
- aws_dynamodb_table (DynamoDB)
- aws_rds_cluster (Aurora PostgreSQL — if relational features critical)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| Data model | Document/JSON-like | aws_dynamodb_table | strong | Firestore's natural equivalent |
| Data model | Highly relational (lots of joins) | aws_rds_cluster | strong | Aurora handles complex relationships better |
| Query patterns | Mostly key-value reads | aws_dynamodb_table | strong | DynamoDB's strength |
| Query patterns | Range queries, filters | aws_dynamodb_table | moderate | DynamoDB GSI handles this, but more complex |
| Query patterns | Complex queries, aggregations | aws_rds_cluster | strong | Aurora PostgreSQL better for analytics |
| Real-time listeners | Required | aws_dynamodb_table + aws_kinesis | strong | DynamoDB Streams + Lambda for real-time |
| Real-time listeners | Not required | aws_dynamodb_table | moderate | Standard DynamoDB sufficient |
| Indexes | Multiple custom indexes | aws_dynamodb_table | moderate | DynamoDB supports up to 10 GSI |
| Indexes | Complex multi-column indexes | aws_rds_cluster | moderate | Aurora handles complex indexes better |

**Eliminators:**
- ACID transactions across unrelated documents → DynamoDB transactions are limited (up to 25 items), consider Aurora instead

**Peek at secondaries:** No

**1:Many Expansion (DynamoDB):**
- aws_dynamodb_table — primary
- aws_dynamodb_global_table — if multi-region replication needed
- aws_kinesis_stream — if real-time processing needed (for Streams)
- aws_lambda_function — for Streams processing (real-time listeners)

**1:Many Expansion (Aurora PostgreSQL):**
- aws_rds_cluster — primary
- aws_rds_cluster_instance — 2+ instances for HA
- aws_db_subnet_group — for placement
- aws_security_group — for access control

**Source Config to Carry Forward:**
- Collection structure — informs table design and GSI strategy
- Document structure — informs item schema
- Indexes — informs DynamoDB GSI configuration
- Real-time listeners — informs whether Streams and Lambda are needed

---

## google_bigquery_dataset

**Purpose:** Data warehouse and analytics

**Default:** aws_athena_workgroup (Athena) or aws_redshift_cluster (Redshift)

**Rationale for default:** Athena is the closest BigQuery equivalent for ad-hoc queries on data in S3 (similar pay-per-query model). Redshift is preferred for frequent/complex interactive queries requiring consistent performance.

**Candidates:**
- aws_athena_workgroup (Athena — query data in S3)
- aws_redshift_cluster (Redshift — data warehouse cluster)

**Signals:**

| Config Field | Value | Favors | Weight | Reason |
|---|---|---|---|---|
| Query pattern | Infrequent, ad-hoc analytics | aws_athena_workgroup | strong | Athena's strength; similar to BigQuery pay-per-query |
| Query pattern | Frequent interactive queries (dashboards) | aws_redshift_cluster | strong | Redshift's consistency and performance |
| Data volume | Large (> 100 GB) | aws_athena_workgroup or aws_redshift_cluster | weak | Both handle large data; choice depends on query pattern |
| Data volume | Massive (> 1 TB, > 10K queries/month) | aws_redshift_cluster | moderate | Redshift more cost-effective at scale |
| Query complexity | Simple aggregations | aws_athena_workgroup | moderate | Athena sufficient |
| Query complexity | Complex, multi-table joins, UDFs | aws_redshift_cluster | moderate | Redshift better for complex queries |
| SLA requirements | Consistent sub-second performance | aws_redshift_cluster | strong | Redshift cluster SLA > Athena variable performance |
| Cost sensitivity | Budget-conscious, sporadic usage | aws_athena_workgroup | strong | Pay only for data scanned |
| Cost sensitivity | Predictable workload | aws_redshift_cluster | moderate | Cluster cost predictable once sized |

**Eliminators:**
- Real-time data ingestion patterns (streaming) → Neither Athena nor Redshift ideal; consider Kinesis + DynamoDB instead

**Peek at secondaries:** Yes — check for linked datasets, scheduled queries, or Pub/Sub triggers

**1:Many Expansion (Athena):**
- aws_athena_workgroup — query execution workgroup
- aws_s3_bucket — data storage (linked from data_source)
- aws_glue_catalog_database — metadata catalog
- aws_glue_catalog_table — table definitions
- aws_athena_named_query — saved queries

**1:Many Expansion (Redshift):**
- aws_redshift_cluster — primary data warehouse
- aws_redshift_subnet_group — cluster placement
- aws_security_group — access control
- aws_redshift_parameter_group — cluster parameters
- aws_s3_bucket — for external table data (Redshift Spectrum)

**Source Config to Carry Forward:**
- Dataset name and description — determines Athena workgroup name or Redshift database name
- Table schemas — informs Glue catalog design (Athena) or Redshift table definitions
- Scheduled queries — informs Lambda/EventBridge triggers (Athena) or Redshift scheduled queries
- Linked sources — informs S3 bucket configuration (Athena) or external table setup (Redshift)

---

## Secondary: google_sql_database

**Behavior:** SQL databases are configuration secondaries that define which databases are created within a Cloud SQL instance. They are absorbed into the primary database resource configuration.

**Mapping Behavior:**

When google_sql_database_instance maps to:
- aws_db_instance (RDS) → Each google_sql_database is absorbed as `db_name` during RDS initialization
- aws_rds_cluster (Aurora) → Each google_sql_database is absorbed as `database_name` during Aurora initialization

**Implementation:**
1. Database names and character sets are carried forward to AWS resource configuration
2. Database creation SQL (`CREATE DATABASE ...`) runs during RDS/Aurora initialization
3. No separate aws_db resource is created
4. Multiple databases on same instance each become their own initialization

**Skip Condition:**
If the primary google_sql_database_instance is skipped or not mapped to AWS, skip these secondaries.

---

## Secondary: google_sql_user

**Behavior:** SQL users are configuration secondaries that define database authentication credentials. They map to AWS Secrets Manager for secure credential storage.

**Mapping Behavior:**

When google_sql_database_instance maps to:
- aws_db_instance (RDS) → Service account credentials become `master_username` / `master_password` stored in aws_secretsmanager_secret
- aws_rds_cluster (Aurora) → Service account credentials become `master_username` / `master_password` stored in aws_secretsmanager_secret

**Implementation:**
1. GCP service account email/password becomes AWS master user credentials
2. Credentials must be stored in AWS Secrets Manager (not in code/config)
3. Connection strings must be updated with new AWS credentials
4. Application code must retrieve credentials from Secrets Manager

**Security Note:**
Never commit database passwords. Use Secrets Manager for credential management and rotation.

**Skip Condition:**
If the primary google_sql_database_instance is skipped, skip these secondaries.

---

## google_redis_instance (Memorystore)

**Purpose:** In-memory cache and data store

**Default:** aws_elasticache_replication_group (ElastiCache Redis)

**Rationale for default:** ElastiCache Redis is the direct 1:1 equivalent to Memorystore Redis. Same Redis engine, managed service with multi-AZ failover.

**Candidates:**
- aws_elasticache_replication_group (ElastiCache Redis) — always the target

**This is a fast-path (deterministic) mapping.** No rubric evaluation needed.

**Signals:**

| Signal | Favors | Weight | Reason |
|---|---|---|---|
| Cluster mode enabled | ElastiCache Redis with cluster mode | strong | Preserve sharding topology |
| High availability required | ElastiCache Redis Multi-AZ with auto-failover | strong | Match HA configuration |
| Single node, dev/test | ElastiCache Redis (single node) | moderate | Cost optimization for dev |

**1:Many Expansion:**
- aws_elasticache_replication_group
- aws_elasticache_subnet_group
- aws_elasticache_parameter_group (if custom parameters)

**Source Config to Carry Forward:**
- tier → determines node type (e.g., BASIC → cache.t4g.micro, STANDARD_HA → cache.r7g.large)
- memory_size_gb → determines node size
- redis_version → determines engine version
- auth_enabled → determines transit encryption and AUTH token
- replica_count → determines number of replicas per shard
