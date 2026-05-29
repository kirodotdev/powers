# Terraform Clustering: Classification Rules

Hardcoded lists for classifying GCP resources as PRIMARY or SECONDARY.

Each PRIMARY resource is assigned a `tier` indicating its infrastructure layer.

## Priority 1: PRIMARY Resources (Workload-Bearing)

These resource types are always PRIMARY:

### Compute (`tier: "compute"`)

- `google_cloud_run_service` — Serverless container workload
- `google_cloud_run_v2_service` — Serverless container workload (v2 API)
- `google_container_cluster` — Kubernetes cluster
- `google_container_node_pool` — Kubernetes node pool
- `google_compute_instance` — Virtual machine
- `google_cloudfunctions_function` — Serverless function (Gen 1)
- `google_cloudfunctions2_function` — Serverless function (Gen 2)
- `google_app_engine_application` — App Engine application

### Database (`tier: "database"`)

- `google_sql_database_instance` — Relational database
- `google_spanner_instance` — Globally-distributed relational database
- `google_firestore_database` — Document database
- `google_bigtable_instance` — Wide-column NoSQL database
- `google_redis_instance` — In-memory cache

### Storage (`tier: "storage"`)

- `google_storage_bucket` — Object storage
- `google_filestore_instance` — Managed NFS file storage
- `google_bigquery_dataset` — Data warehouse

### Messaging (`tier: "messaging"`)

- `google_pubsub_topic` — Message queue
- `google_cloud_tasks_queue` — Task queue

### Networking (`tier: "networking"`)

- `google_compute_network` — Virtual network (VPC — primary because it defines topology)
- `google_compute_security_policy` — Web application firewall (Cloud Armor)
- `google_dns_managed_zone` — DNS zone

### Monitoring (`tier: "monitoring"`)

- `google_monitoring_alert_policy` — Alert policy

### Other

- `module.*` — Terraform module that wraps primary resources (tier inferred from wrapped resource)

**Action**: Mark as `PRIMARY` with assigned `tier`. Classification done. No secondary_role.

## Priority 2: SECONDARY Resources by Role

Match resource type against secondary classification table. Each match assigns a `secondary_role`:

### Identity (`identity`)

- `google_service_account` — Workload identity
- `data.google_service_account` — Data source reference to existing service account

### Access Control (`access_control`)

- `google_*_iam_member` — IAM binding (all variants: project, cloud_run_service, storage_bucket, etc.)
- `google_*_iam_policy` — IAM policy (all variants)

### Network Path (`network_path`)

- `google_vpc_access_connector` — VPC connector for serverless
- `google_compute_subnetwork` — Subnet
- `google_compute_firewall` — Firewall rule
- `google_compute_router` — Cloud router
- `google_compute_router_nat` — NAT rule
- `google_compute_global_address` — Global IP address (for VPC peering, load balancing)
- `google_service_networking_connection` — VPC peering

### Configuration (`configuration`)

- `google_sql_database` — SQL schema
- `google_sql_user` — SQL user
- `google_spanner_database` — Spanner database schema
- `google_secret_manager_secret` — Secret vault
- `google_secret_manager_secret_version` — Secret value
- `google_dns_record_set` — DNS record
- `google_monitoring_notification_channel` — Alert notification target

### Encryption (`encryption`)

- `google_kms_crypto_key` — KMS encryption key
- `google_kms_key_ring` — KMS key ring

### Orchestration (`orchestration`)

- `null_resource` — Terraform orchestration marker
- `time_sleep` — Orchestration delay
- `google_project_service` — API service enablement (prerequisite, not a deployable unit)

**Action**: Mark as `SECONDARY` with assigned role.

## Priority 3: LLM Inference Fallback

If resource type not in Priority 1 or 2, apply these **deterministic fallback heuristics** BEFORE free-form LLM reasoning:

| Pattern                                              | Classification    | secondary_role | confidence |
| ---------------------------------------------------- | ----------------- | -------------- | ---------- |
| Name contains `scheduler`, `task`, `job`, `workflow` | SECONDARY         | orchestration  | 0.65       |
| Name contains `log`, `metric`, `alert`, `dashboard`  | SECONDARY         | configuration  | 0.60       |
| Resource has zero references to/from other resources | SECONDARY         | configuration  | 0.50       |
| Resource only referenced by a `module` block         | SECONDARY         | configuration  | 0.55       |
| Type contains `policy` or `binding`                  | SECONDARY         | access_control | 0.65       |
| Type contains `network` or `subnet`                  | SECONDARY         | network_path   | 0.60       |
| None of the above match                              | Use LLM reasoning | —              | 0.50-0.75  |

If still uncertain after heuristics, use LLM reasoning. Mark with:

- `classification_source: "llm_inference"`
- `confidence: 0.5-0.75`

**Default**: If all heuristics and LLM fail: `SECONDARY` / `configuration` with confidence 0.5. It is safer to under-classify (secondary) than over-classify (primary), because secondaries are grouped into existing clusters while primaries create new clusters.

## Serves[] Population

For SECONDARY resources, populate `serves[]` array (list of PRIMARY resources it supports):

1. Extract all outgoing references from this SECONDARY's config
2. Include direct references: `field = resource_type.name.id` patterns
3. Include transitive chains: if referenced resource is also SECONDARY, trace to PRIMARY

**Example**: `google_compute_firewall` → references `google_compute_network` (SECONDARY) → serves `google_compute_instance.web` (PRIMARY)

**Serves array**: Points back to PRIMARY workloads affected by this firewall rule. Trace through SECONDARY resources until a PRIMARY is reached.
