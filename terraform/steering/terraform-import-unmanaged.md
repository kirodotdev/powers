# Import Unmanaged Resources

Import existing AWS resources into Terraform management using the modern `terraform query` and import block approach.

## Workflow: Discover → Generate → Filter → Import

## Step-by-Step Process

### 1. Check Resource List Support
Use MCP tools to verify resource type supports list operations:

```javascript
// Check AWSCC provider capabilities
get_provider_capabilities({
  "name": "awscc",
  "namespace": "hashicorp"
})

// Search for specific resource documentation
search_providers({
  "provider_name": "awscc",
  "provider_namespace": "hashicorp", 
  "service_slug": "s3_bucket",
  "provider_document_type": "list-resources"
})
```

### 2. Create Query File
Create `resource_query.tfquery.hcl` with appropriate list blocks based on provider capabilities.

### 3. Generate Configuration
Run `terraform query -generate-config-out=discovered_resources.tf` to discover resources and generate import blocks.

### 4. Filter Resources
Extract target resources by ID/name/ARN and create separate import file.

### 5. Execute Import
Run `terraform plan` and `terraform apply` for config-driven import.

## Provider Selection

**Prefer AWS Provider First:**
- Familiar syntax and patterns
- Better compatibility with existing configurations

**Use AWSCC When:**
- AWS provider doesn't support list operations
- Need comprehensive resource discovery

## Configuration

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
    awscc = {
      source  = "hashicorp/awscc"
    }
  }
}

provider "aws" {
  # Set based on user preference, defaults to us-east-1, or use AWS_DEFAULT_REGION
  region = "us-east-1"
}

provider "awscc" {
  # Set based on user preference, defaults to us-east-1, or use AWS_DEFAULT_REGION
  region = "us-east-1"
}
```

## Examples

```hcl
# Query file
list "awscc_s3_bucket" "discovered_buckets" {
  provider = awscc
}

# Generated import block
import {
  to = awscc_s3_bucket.example_bucket
  identity = {
    account_id  = "123456789012"
    bucket_name = "my-example-bucket"
    region      = "us-east-1"
  }
}
```

## Best Practices

- Always run `terraform plan` before apply
- Filter carefully - only import what you'll manage
- Verify resource configurations after import
- Verify the current state file includes the resources which were requested to be imported

## Prerequisites

- Terraform 1.14.0+
- AWS CLI configured
- Appropriate IAM permissions

> **Note:** Check the Terraform version with `terraform version`. The import feature requires Terraform 1.14.0 or above. You must upgrade manually if needed before proceeding.
