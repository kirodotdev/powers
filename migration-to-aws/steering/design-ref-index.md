# GCP Service → Design Reference Mapping

> **Column note:** **Typical AWS target** is the usual rubric outcome for that Terraform type. It is **not** the same as **`deterministic` confidence** in `aws-design.json`. Only resource types listed in **`design-ref-fast-path.md` → Direct Mappings** get `deterministic`; everything else in this table is mapped via rubric → `inferred` (unless `billing_inferred` on the billing-only path).

## Compute Services

| GCP Service         | Resource Type                    | Reference File | Typical AWS target |
| ------------------- | -------------------------------- | -------------- | ------------------ |
| Cloud Run           | `google_cloud_run_service`       | `design-ref-compute.md`   | Fargate            |
| Cloud Functions     | `google_cloudfunctions_function` | `design-ref-compute.md`   | Lambda             |
| Compute Engine (VM) | `google_compute_instance`        | `design-ref-compute.md`   | EC2 or Fargate     |
| GKE                 | `google_container_cluster`       | `design-ref-compute.md`   | EKS                |
| App Engine          | `google_app_engine_application`  | `design-ref-compute.md`   | Fargate or Amplify |

## Database Services

| GCP Service            | Resource Type                  | Reference File | Typical AWS target                                                                |
| ---------------------- | ------------------------------ | -------------- | --------------------------------------------------------------------------------- |
| Cloud SQL (PostgreSQL) | `google_sql_database_instance` | `design-ref-database.md`  | RDS PostgreSQL or Aurora PostgreSQL (Q6 selects family)                           |
| Cloud SQL (MySQL)      | `google_sql_database_instance` | `design-ref-database.md`  | RDS MySQL or Aurora MySQL (Q6 selects family)                                     |
| Cloud SQL (SQL Server) | `google_sql_database_instance` | `design-ref-database.md`  | RDS SQL Server                                                                    |
| Firestore (instance)   | `google_firestore_database`    | `design-ref-database.md`  | DynamoDB                                                                          |
| Firestore (document)   | `google_firestore_document`    | `design-ref-database.md`  | DynamoDB                                                                          |
| BigQuery               | `google_bigquery_*`            | `design-ref-database.md`  | **`Deferred — specialist engagement`** only (see `design-infra.md` BigQuery gate) |
| Memorystore (Redis)    | `google_redis_instance`        | `design-ref-database.md`  | ElastiCache Redis                                                                 |
| Cloud Spanner          | `google_spanner_instance`      | `design-ref-database.md`  | Aurora DSQL                                                                       |

## Storage Services

| GCP Service         | Resource Type               | Reference File | Typical AWS target |
| ------------------- | --------------------------- | -------------- | ------------------ |
| Cloud Storage (GCS) | `google_storage_bucket`     | `design-ref-storage.md`   | S3                 |
| Filestore           | `google_filestore_instance` | `design-ref-storage.md`   | EFS                |

## Networking Services

| GCP Service          | Resource Type                     | Reference File  | Typical AWS target |
| -------------------- | --------------------------------- | --------------- | ------------------ |
| VPC Network          | `google_compute_network`          | `design-ref-networking.md` | VPC                |
| Firewall Rules       | `google_compute_firewall`         | `design-ref-networking.md` | Security Groups    |
| Cloud Load Balancing | `google_compute_forwarding_rule`  | `design-ref-networking.md` | ALB/NLB            |
| Cloud CDN            | (part of compute_backend_service) | `design-ref-networking.md` | CloudFront         |
| Cloud DNS            | `google_dns_managed_zone`         | `design-ref-networking.md` | Route 53           |
| Cloud Interconnect   | (custom config)                   | `design-ref-networking.md` | AWS Direct Connect |
| Cloud Armor          | `google_compute_security_policy`  | `design-ref-networking.md` | AWS WAF            |

## Messaging Services

| GCP Service | Resource Type              | Reference File | Typical AWS target |
| ----------- | -------------------------- | -------------- | ------------------ |
| Pub/Sub     | `google_pubsub_topic`      | `design-ref-messaging.md` | SNS or SQS         |
| Cloud Tasks | `google_cloud_tasks_queue` | `design-ref-messaging.md` | SQS or EventBridge |

## AI/ML Services

| GCP Service                | Resource Type       | Reference File            | Typical AWS target      |
| -------------------------- | ------------------- | ------------------------- | ----------------------- |
| Vertex AI (LLM/Gemini)     | (generative models) | `design-ref-ai-gemini-to-bedrock.md` | Bedrock                 |
| OpenAI (in GCP env)        | (openai SDK)        | `design-ref-ai-openai-to-bedrock.md` | Bedrock                 |
| Vertex AI (traditional ML) | (custom endpoints)  | `design-ref-ai.md`                   | SageMaker               |
| Vertex AI (pipelines)      | (custom config)     | `design-ref-ai.md`                   | SageMaker Pipelines     |
| Cloud Vision API           | (managed API)       | `design-ref-ai.md`                   | Textract or Rekognition |

## Secondary/Infrastructure Services

| GCP Service              | Resource Type                          | Reference File    | Typical AWS target |
| ------------------------ | -------------------------------------- | ----------------- | ------------------ |
| Service Accounts         | `google_service_account`               | `design-ref-networking.md`   | IAM Roles          |
| Secret Manager (secret)  | `google_secret_manager_secret`         | `design-ref-security.md`     | Secrets Manager    |
| Secret Manager (version) | `google_secret_manager_secret_version` | `design-ref-security.md`     | Secrets Manager    |
| Cloud Monitoring         | (managed)                              | Not in v1.0 scope | CloudWatch         |

---

**Usage:**

1. Extract GCP resource type from Terraform
2. Find in table above
3. If resource found in `design-ref-fast-path.md` Direct Mappings table: use that mapping (confidence = deterministic)
4. Otherwise: load Reference File listed above and apply 6-criteria rubric (confidence = inferred)

**User-facing labels** for chat and reports: see `design-ref-fast-path.md` → **User-facing vocabulary** (e.g. **Standard pairing** / **Tailored to your setup** / **Estimated from billing only**).
