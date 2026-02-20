# Security Setup for OpenSearch Serverless

OpenSearch Serverless uses three independent security policy types to control access: encryption, network, and data access. All three must be configured for a functional collection.

## Security Policy Overview

| Policy Type | Controls | Required? | When to Create |
|------------|----------|-----------|---------------|
| **Encryption** | Encryption keys for data at rest | Yes | Before collection creation |
| **Network** | How collection endpoints can be reached | Yes | Before collection creation |
| **Data Access** | Who can perform which operations on collections and indices | Yes | After collection creation (but before indexing) |

Policies are matched to collections by resource patterns (collection names or wildcards), not by direct association.

## Encryption Policies

### AWS-Owned Key (Default, Recommended)

No additional cost. AWS manages the encryption key lifecycle.

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "my-app-encryption",
    "type": "encryption",
    "description": "Encryption for my-app collections",
    "policy": "{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"]}],\"AWSOwnedKey\":true}"
  },
  "region": "us-east-1"
})
```

### Customer-Managed Key (CMK)

Use when compliance requires you to control the encryption key:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "my-app-encryption-cmk",
    "type": "encryption",
    "description": "CMK encryption for my-app collections",
    "policy": "{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"]}],\"AWSOwnedKey\":false,\"KmsARN\":\"arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012\"}"
  },
  "region": "us-east-1"
})
```

**Notes:**
- The KMS key must exist in the same region as the collection.
- Your IAM identity needs `kms:CreateGrant`, `kms:DescribeKey`, and `kms:GenerateDataKey` on the KMS key.
- Deleting the KMS key makes the collection data permanently inaccessible.

### Encryption Policy Patterns

Use wildcards to cover multiple collections:

```json
{
  "Rules": [
    {
      "ResourceType": "collection",
      "Resource": ["collection/my-app-*"]
    }
  ],
  "AWSOwnedKey": true
}
```

This matches any collection whose name starts with `my-app-`.

**Important:** A collection must match exactly one encryption policy. If zero or multiple encryption policies match, collection creation fails.

## Network Policies

### Public Access (Development / Testing)

Both the OpenSearch API endpoint and Dashboards are accessible from the internet:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "my-app-network-public",
    "type": "network",
    "description": "Public access for development",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"]},{\"ResourceType\":\"dashboard\",\"Resource\":[\"collection/my-app-*\"]}],\"AllowFromPublic\":true}]"
  },
  "region": "us-east-1"
})
```

### VPC Endpoint Access (Production)

Restrict access to traffic from specific VPC endpoints:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "my-app-network-vpc",
    "type": "network",
    "description": "VPC-only access for production",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"]},{\"ResourceType\":\"dashboard\",\"Resource\":[\"collection/my-app-*\"]}],\"SourceVPCEs\":[\"vpce-0123456789abcdef0\"]}]"
  },
  "region": "us-east-1"
})
```

### Mixed Access (API Public, Dashboard VPC-Only)

Separate rules for API and dashboard access:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-app-*"]
      }
    ],
    "AllowFromPublic": true
  },
  {
    "Rules": [
      {
        "ResourceType": "dashboard",
        "Resource": ["collection/my-app-*"]
      }
    ],
    "SourceVPCEs": ["vpce-0123456789abcdef0"]
  }
]
```

### Creating a VPC Endpoint for AOSS

Before using VPC endpoint access, create an OpenSearch Serverless VPC endpoint:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateVpcEndpoint",
  "parameters": {
    "name": "my-aoss-vpce",
    "vpcId": "vpc-0123456789abcdef0",
    "subnetIds": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"],
    "securityGroupIds": ["sg-0123456789abcdef0"]
  },
  "region": "us-east-1"
})
```

**Notes:**
- Network policies are JSON arrays (not objects like encryption policies).
- Multiple rules can exist in one policy for different resource types.
- A collection can match multiple network policies — rules are merged (union).
- VPC endpoints must be for the `com.amazonaws.<region>.aoss` service.

## Data Access Policies

Data access policies grant IAM principals permission to perform operations on collections and indices. These are applied after collection creation.

### Full Access for a Single IAM Role

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateAccessPolicy",
  "parameters": {
    "name": "my-app-data-access",
    "type": "data",
    "description": "Full data access for application role",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"index\",\"Resource\":[\"index/my-app-*/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:DeleteIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"]},{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:DescribeCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DeleteCollectionItems\"]}],\"Principal\":[\"arn:aws:iam::123456789012:role/my-app-role\"]}]"
  },
  "region": "us-east-1"
})
```

### Read-Only Access

For services that only need to search, not write:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/my-app-*/*"],
        "Permission": [
          "aoss:DescribeIndex",
          "aoss:ReadDocument"
        ]
      },
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-app-*"],
        "Permission": [
          "aoss:DescribeCollectionItems"
        ]
      }
    ],
    "Principal": ["arn:aws:iam::123456789012:role/my-app-reader-role"]
  }
]
```

### Write-Only Access (Ingestion Service)

For services that ingest data but don't need to search:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/my-app-*/*"],
        "Permission": [
          "aoss:WriteDocument",
          "aoss:CreateIndex"
        ]
      },
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-app-*"],
        "Permission": [
          "aoss:CreateCollectionItems"
        ]
      }
    ],
    "Principal": ["arn:aws:iam::123456789012:role/my-app-ingestion-role"]
  }
]
```

### Multiple Principals

Grant different access levels to different roles:

```json
[
  {
    "Description": "Admin access",
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/my-app-*/*"],
        "Permission": [
          "aoss:CreateIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:DeleteIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ]
      },
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-app-*"],
        "Permission": [
          "aoss:CreateCollectionItems",
          "aoss:DescribeCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DeleteCollectionItems"
        ]
      }
    ],
    "Principal": ["arn:aws:iam::123456789012:role/admin-role"]
  },
  {
    "Description": "Application read access",
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/my-app-*/*"],
        "Permission": [
          "aoss:DescribeIndex",
          "aoss:ReadDocument"
        ]
      }
    ],
    "Principal": [
      "arn:aws:iam::123456789012:role/app-role",
      "arn:aws:iam::123456789012:role/analytics-role"
    ]
  }
]
```

### SAML Authentication

For federated access via SAML identity providers:

```json
[
  {
    "Rules": [
      {
        "ResourceType": "collection",
        "Resource": ["collection/my-app-*"],
        "Permission": [
          "aoss:CreateCollectionItems",
          "aoss:DescribeCollectionItems"
        ]
      },
      {
        "ResourceType": "index",
        "Resource": ["index/my-app-*/*"],
        "Permission": [
          "aoss:ReadDocument",
          "aoss:WriteDocument",
          "aoss:CreateIndex",
          "aoss:DescribeIndex"
        ]
      }
    ],
    "Principal": ["saml/123456789012/my-saml-provider/group/Developers"]
  }
]
```

## Available Permissions

### Collection Permissions

| Permission | Description |
|-----------|-------------|
| `aoss:CreateCollectionItems` | Create indices within the collection |
| `aoss:DescribeCollectionItems` | List and describe indices |
| `aoss:UpdateCollectionItems` | Update collection-level settings |
| `aoss:DeleteCollectionItems` | Delete indices from the collection |

### Index Permissions

| Permission | Description |
|-----------|-------------|
| `aoss:CreateIndex` | Create new indices |
| `aoss:UpdateIndex` | Update index mappings and settings |
| `aoss:DescribeIndex` | Get index metadata, mappings, and settings |
| `aoss:DeleteIndex` | Delete indices |
| `aoss:ReadDocument` | Search and get documents |
| `aoss:WriteDocument` | Index, update, and delete documents |

## Policy Management

### List Policies

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "ListSecurityPolicies",
  "parameters": {
    "type": "encryption"
  },
  "region": "us-east-1"
})
```

Replace `type` with `"network"` or use `ListAccessPolicies` for data access policies.

### Update a Policy

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "UpdateSecurityPolicy",
  "parameters": {
    "name": "my-app-network-public",
    "type": "network",
    "policyVersion": "MTY3ODIxMDk1NTEwOV8x",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/my-app-*\"]}],\"AllowFromPublic\":true}]"
  },
  "region": "us-east-1"
})
```

**Note:** `policyVersion` is required for updates. Get it from `GetSecurityPolicy`.

### Delete a Policy

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "DeleteSecurityPolicy",
  "parameters": {
    "name": "my-app-encryption",
    "type": "encryption"
  },
  "region": "us-east-1"
})
```

**Warning:** Deleting an encryption policy that is actively used by a collection will prevent the collection from functioning. Delete the collection first.

## Security Best Practices

1. **Use wildcards in resource patterns** to cover related collections: `collection/my-app-*` instead of `collection/my-app-products`, `collection/my-app-logs` separately.
2. **Create separate data access policies** for different roles — admin, application, analytics — rather than one policy granting everyone full access.
3. **Use VPC endpoints** for production workloads. Public access should only be used for development and testing.
4. **Restrict `Principal` lists** to the specific IAM roles that need access. Avoid using `*` wildcards in principals.
5. **Use index-level resource patterns** (e.g., `index/my-collection/products-*`) to restrict access to specific indices rather than `index/my-collection/*`.
6. **Separate read and write principals** when possible. Ingestion services should not have read access, and search services should not have write access.
7. **Audit policies regularly** with `ListSecurityPolicies` and `ListAccessPolicies` to remove stale entries.
8. **Use AWS-owned encryption keys** unless compliance requires customer-managed keys — they're free and require no management.
