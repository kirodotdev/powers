# Get Started with OpenTofu

## Overview

Interactive guide for setting up OpenTofu in a new project.

## Trigger

When user says "Get started with OpenTofu" or similar.

---

## Step 1: Check Existing Setup

Look for `*.tf` files, `.terraform/`, `*.tfstate`, `.opentofu/`.

**If found:** Ask to continue or start fresh.
**If not:** Proceed to Step 2.

## Step 2: Install OpenTofu (if needed)

Check if `tofu` is installed:
```bash
tofu version
```

If not installed, guide the user to install OpenTofu:

**macOS (Homebrew):**
```bash
brew install opentofu
```

**Linux (apt):**
```bash
curl -fsSL https://get.opentofu.org/install-opentofu.sh | bash -s -- --install-method deb
```

**Linux (rpm):**
```bash
curl -fsSL https://get.opentofu.org/install-opentofu.sh | bash -s -- --install-method rpm
```

**Windows (Chocolatey):**
```powershell
choco install opentofu
```

**Other / Manual:** https://opentofu.org/docs/intro/install/

## Step 3: Determine Provider

Ask: "Which cloud provider? (AWS, Azure, GCP, other)"

Use the OpenTofu MCP to get provider info:
```javascript
// Search for the provider
search-opentofu-registry({ "query": "aws", "type": "provider" })

// Get provider details including available versions
get-provider-details({ "namespace": "hashicorp", "name": "aws" })
```

## Step 4: Create Base Files

**versions.tf:**
```hcl
terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Use version from MCP
    }
  }
}
```

**provider.tf:**
```hcl
provider "aws" {
  region = var.aws_region
}
```

**variables.tf:**
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}
```

## Step 5: First Resource

Ask what to create, then:
1. Search the registry for the resource or module:
   ```javascript
   search-opentofu-registry({ "query": "s3_bucket", "type": "resource" })
   ```
2. Retrieve full resource documentation:
   ```javascript
   get-resource-docs({ "namespace": "hashicorp", "name": "aws", "resource": "s3_bucket" })
   ```
3. Or find a community module:
   ```javascript
   search-opentofu-registry({ "query": "vpc", "type": "module" })
   get-module-details({ "namespace": "terraform-aws-modules", "name": "vpc", "target": "aws" })
   ```

## Step 6: Initialize

Guide through:
1. `tofu init`
2. `tofu validate`
3. `tofu plan`

## Step 7: What's Next

Offer help with:
- Adding resources/modules
- Multiple environments
- Remote state setup (S3, GCS, Azure Blob, etc.)
- CI/CD pipelines

---

## Quick Reference

```bash
tofu init      # Initialize
tofu fmt       # Format
tofu validate  # Validate
tofu plan      # Preview
tofu apply     # Apply
tofu destroy   # Destroy
```

## File Structure

```
project/
├── versions.tf      # OpenTofu/provider versions
├── provider.tf      # Provider config
├── variables.tf     # Input variables
├── main.tf          # Resources
├── outputs.tf       # Outputs
└── terraform.tfvars # Values (don't commit secrets; OpenTofu also supports tofu.tfvars)
```

## Remote State Example (S3)

```hcl
terraform {
  backend "s3" {
    bucket = "my-tofu-state"
    key    = "project/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Initialize with:
```bash
tofu init -backend-config="bucket=my-tofu-state"
```
