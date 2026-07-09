# IaC Discovery Schemas

Schemas for `gcp-resource-inventory.json` and `gcp-resource-clusters.json`, produced by `discover-iac.md`.

**Convention**: Values shown as `X|Y` in examples indicate allowed alternatives — use exactly one value per field, not the literal pipe character.

---

## gcp-resource-inventory.json (Phase 1 output)

Complete inventory of discovered GCP resources with classification, dependencies, and AI detection.

```json
{
  "metadata": {
    "report_date": "2026-02-26",
    "project_directory": "/path/to/terraform",
    "terraform_version": ">= 1.0.0"
  },
  "summary": {
    "total_resources": 50,
    "primary_resources": 12,
    "secondary_resources": 38,
    "total_clusters": 6,
    "classification_coverage": "100%"
  },
  "resources": [
    {
      "address": "google_cloud_run_service.orders_api",
      "type": "google_cloud_run_service",
      "name": "orders_api",
      "classification": "PRIMARY",
      "tier": "compute",
      "confidence": 0.99,
      "config": {
        "timeout": 60,
        "memory_mb": 512,
        "concurrency": 100
      },
      "depth": 3,
      "cluster_id": "compute_cloudrun_us-central1_001"
    },
    {
      "address": "google_service_account.app",
      "type": "google_service_account",
      "name": "app",
      "classification": "SECONDARY",
      "tier": "identity",
      "confidence": 0.99,
      "secondary_role": "identity",
      "serves": ["google_cloud_run_service.orders_api", "google_cloud_run_service.products_api"],
      "config": {
        "account_id": "app-sa"
      },
      "depth": 2,
      "cluster_id": "compute_cloudrun_us-central1_001"
    },
    {
      "address": "google_compute_network.main",
      "type": "google_compute_network",
      "name": "main",
      "classification": "PRIMARY",
      "tier": "networking",
      "confidence": 0.99,
      "config": {
        "auto_create_subnetworks": false
      },
      "depth": 0,
      "cluster_id": "networking_vpc_us-central1_001"
    }
  ],
  "ai_detection": {
    "has_ai_workload": false,
    "confidence": 0,
    "confidence_level": "none",
    "signals_found": [],
    "ai_services": []
  }
}
```

**CRITICAL Field Names** (use EXACTLY these keys):

- `address` — Terraform resource address (NOT `id`, `resource_address`)
- `type` — Resource type (NOT `resource_type`)
- `name` — Resource name component (NOT `resource_name`)
- `classification` — `"PRIMARY"` or `"SECONDARY"` (NOT `class`, `category`)
- `tier` — Infrastructure layer: compute, database, storage, networking, identity, messaging, monitoring (NOT `layer`)
- `confidence` — Classification confidence 0.0-1.0 (NOT `certainty`)
- `secondary_role` — For secondaries only: identity, access_control, network_path, configuration, encryption, orchestration
- `serves` — For secondaries only: array of primary resource addresses served
- `depth` — Dependency depth (0 = foundational, N = depends on depth N-1)
- `cluster_id` — Which cluster this resource belongs to

**Key Sections:**

- `metadata` — Report metadata (report_date, project_directory, terraform_version)
- `summary` — Aggregate statistics (total_resources, primary/secondary counts, cluster count, classification_coverage)
- `resources[]` — All discovered resources with fields above
- `ai_detection` — AI workload detection results:
  - `has_ai_workload` — boolean
  - `confidence` — 0.0-1.0
  - `confidence_level` — "very_high" (90%+), "high" (70-89%), "medium" (50-69%), "low" (< 50%), "none" (0%)
  - `signals_found[]` — array of detection signals with method, pattern, confidence, evidence
  - `ai_services[]` — list of AI services detected (vertex_ai, bigquery_ml, etc.)

---

## gcp-resource-clusters.json (Phase 1 output)

Resources grouped into logical clusters for migration with full dependency graph and creation order.

```json
{
  "clusters": [
    {
      "cluster_id": "networking_vpc_us-central1_001",
      "gcp_region": "us-central1",
      "primary_resources": [
        "google_compute_network.main"
      ],
      "secondary_resources": [
        "google_compute_subnetwork.app",
        "google_compute_firewall.app"
      ],
      "network": null,
      "creation_order_depth": 0,
      "must_migrate_together": true,
      "dependencies": [],
      "edges": []
    },
    {
      "cluster_id": "database_sql_us-central1_001",
      "gcp_region": "us-central1",
      "primary_resources": [
        "google_sql_database_instance.db"
      ],
      "secondary_resources": [
        "google_sql_database.main"
      ],
      "network": "networking_vpc_us-central1_001",
      "creation_order_depth": 1,
      "must_migrate_together": true,
      "dependencies": ["networking_vpc_us-central1_001"],
      "edges": [
        {
          "from": "google_sql_database_instance.db",
          "to": "google_compute_network.main",
          "relationship_type": "network_membership",
          "evidence": {
            "field_path": "settings.ip_configuration.private_network",
            "reference": "VPC membership"
          }
        }
      ]
    },
    {
      "cluster_id": "compute_cloudrun_us-central1_001",
      "gcp_region": "us-central1",
      "primary_resources": [
        "google_cloud_run_service.orders_api",
        "google_cloud_run_service.products_api"
      ],
      "secondary_resources": [
        "google_service_account.app"
      ],
      "network": "networking_vpc_us-central1_001",
      "creation_order_depth": 2,
      "must_migrate_together": true,
      "dependencies": ["database_sql_us-central1_001"],
      "edges": [
        {
          "from": "google_cloud_run_service.orders_api",
          "to": "google_sql_database_instance.db",
          "relationship_type": "data_dependency",
          "evidence": {
            "field_path": "template.spec.containers[0].env[].value",
            "reference": "DATABASE_URL"
          }
        }
      ]
    }
  ],
  "creation_order": [
    { "depth": 0, "clusters": ["networking_vpc_us-central1_001"] },
    { "depth": 1, "clusters": ["database_sql_us-central1_001"] },
    { "depth": 2, "clusters": ["compute_cloudrun_us-central1_001"] }
  ]
}
```

**Key Fields:**

- `cluster_id` — Unique cluster identifier (deterministic format: `{service_category}_{service_type}_{gcp_region}_{sequence}`)
- `gcp_region` — GCP region for this cluster
- `primary_resources` — GCP resources that map independently
- `secondary_resources` — GCP resources that support primary resources
- `network` — Which VPC cluster this cluster belongs to (cluster ID reference, or null if networking cluster itself)
- `creation_order_depth` — Depth level in topological sort (0 = foundational)
- `must_migrate_together` — Boolean indicating if cluster is an atomic deployment unit
- `dependencies` — Other cluster IDs this cluster depends on (derived from cross-cluster Primary->Primary edges)
- `edges` — Typed relationships between resources with structured evidence
- `creation_order` — Global ordering of clusters by depth level (for migration sequencing)
