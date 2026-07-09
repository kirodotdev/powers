# Storage Services Design Rubric

**Applies to:** Cloud Storage (GCS), Filestore

**Quick lookup (no rubric):** Check `fast-path.md` first (Cloud Storage → S3, deterministic)

## Deterministic Mapping

**Cloud Storage (`google_storage_bucket`) → S3 (`aws_s3_bucket`)**

Confidence: `deterministic` (always 1:1, no decision tree)

**Behavior preservation:**

- Bucket versioning → S3 versioning
- Lifecycle rules → S3 Lifecycle policies
- Access control (UNIFORM vs FINE-GRAINED) → S3 ACLs + Bucket Policies
- Regional location → S3 region selection
- Encryption (default or CSEK) → S3 encryption (default AES-256 or KMS)

## GCS → S3 Attribute Mapping

| GCS Attribute                 | S3 Equivalent                               | Notes                                        |
| ----------------------------- | ------------------------------------------- | -------------------------------------------- |
| `location` (region)           | `region`                                    | Direct mapping; respect user's region choice |
| `versioning_enabled`          | `versioning_enabled`                        | 1:1 copy                                     |
| `lifecycle_rules`             | `lifecycle_rule`                            | Adapt rule conditions                        |
| `uniform_bucket_level_access` | `block_public_acl` + policies               | Convert UNIFORM to S3 ACL block              |
| `encryption` (CSEK)           | `sse_algorithm = "aws:kms"`                 | Use AWS KMS (customer-managed key)           |
| `cors`                        | `cors_rule`                                 | 1:1 copy                                     |
| `retention_policy`            | `object_lock_configuration` (if applicable) | Object Lock stricter than GCS retention      |

## Output Schema

```json
{
  "gcp_type": "google_storage_bucket",
  "gcp_address": "my-app-assets",
  "gcp_config": {
    "location": "us-central1",
    "versioning_enabled": true,
    "lifecycle_rule": [
      {
        "action": "Delete",
        "condition": { "age_days": 90 }
      }
    ]
  },
  "aws_service": "S3",
  "aws_config": {
    "bucket": "my-app-assets-us-east-1",
    "versioning_enabled": true,
    "lifecycle_rule": [
      {
        "id": "delete-old-versions",
        "status": "Enabled",
        "noncurrent_version_expiration": { "days": 90 }
      }
    ],
    "region": "us-east-1"
  },
  "confidence": "deterministic",
  "rationale": "GCS → S3 is 1:1 deterministic; preserve versioning, lifecycle, encryption"
}
```

## Filestore → EFS

**Filestore (`google_filestore_instance`) → EFS (`aws_efs_file_system`)**

Confidence: `deterministic` (both managed NFS, 1:1 mapping)

**Behavior preservation:**

- Managed NFS file system → Managed NFS file system
- Performance tier selection → EFS throughput mode
- Network-attached storage → VPC mount targets
- Shared file access across instances → Shared file access across instances

### Filestore → EFS Attribute Mapping

| Filestore Attribute       | EFS Equivalent                            | Notes                                                    |
| ------------------------- | ----------------------------------------- | -------------------------------------------------------- |
| `tier` (STANDARD)         | `throughput_mode = "bursting"`            | Standard performance maps to bursting throughput          |
| `tier` (PREMIUM)          | `throughput_mode = "provisioned"`         | Premium performance maps to provisioned throughput        |
| `tier` (ENTERPRISE)       | `throughput_mode = "provisioned"`         | Enterprise maps to provisioned with higher IOPS          |
| `capacity_gb`             | (no direct equivalent — EFS auto-scales)  | EFS grows/shrinks automatically; no pre-provisioned size |
| `networks[].network`      | `aws_efs_mount_target.subnet_id`          | Mount target placed in mapped VPC subnet                 |
| `file_shares[].name`      | Mount target path                         | Share name becomes mount path convention                 |
| `file_shares[].capacity`  | (no direct equivalent)                    | EFS has no capacity limits per share                     |

### Filestore → EFS Output Schema

```json
{
  "gcp_type": "google_filestore_instance",
  "gcp_address": "my-app-nfs",
  "gcp_config": {
    "tier": "STANDARD",
    "file_shares": [
      {
        "name": "vol1",
        "capacity_gb": 1024
      }
    ],
    "networks": [
      {
        "network": "projects/my-project/global/networks/my-vpc",
        "modes": ["MODE_IPV4"]
      }
    ]
  },
  "aws_service": "EFS",
  "aws_config": {
    "creation_token": "my-app-nfs",
    "throughput_mode": "bursting",
    "performance_mode": "generalPurpose",
    "encrypted": true,
    "mount_targets": [
      {
        "subnet_id": "subnet-xxx",
        "security_groups": ["sg-xxx"]
      }
    ]
  },
  "confidence": "deterministic",
  "rationale": "Filestore → EFS is 1:1 deterministic; both are managed NFS. EFS auto-scales (no capacity_gb equivalent)."
}
```

## Notes

Cloud Storage and Filestore have direct AWS equivalents with no decision tree required. All mappings are deterministic.

For non-storage use cases (static site hosting, data lakes, etc.), the hosting compute service (Fargate, Amplify) determines architecture, not the bucket itself.
