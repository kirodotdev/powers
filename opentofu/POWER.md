---
name: "opentofu"
displayName: "Deploy infrastructure with OpenTofu"
description: "Build and manage Infrastructure as Code with OpenTofu - access registry providers and modules, manage state, and execute tofu workflows using the open-source Terraform-compatible toolchain"
keywords: ["opentofu", "tofu", "terraform", "infrastructure", "IaC", "providers", "modules", "registry", "open-source"]
author: "Steven J Miklovic"
---

# OpenTofu Power

## Overview

Access the OpenTofu Registry via the official OpenTofu MCP server for IaC development. Search provider docs, discover modules, and manage infrastructure with the open-source `tofu` CLI.

OpenTofu is an open-source fork of Terraform (MPL-2.0 licensed) that is fully compatible with Terraform provider and module registries. Use this power instead of the Terraform Power when working with OpenTofu.

**Key capabilities:**
- **Provider Documentation**: Search and retrieve docs for resources, data sources, functions
- **Module Discovery**: Find verified and community modules from the Registry
- **OpenTofu CLI**: Full `tofu` workflow (init, validate, plan, apply)
- **Registry Compatibility**: Works with `registry.opentofu.org`

> **Why not the Terraform Power?** The Terraform Power includes HCP Terraform workspace management tools that are specific to HashiCorp's commercial platform and are not applicable to OpenTofu. This power is focused on the open-source OpenTofu toolchain and excludes HCP Terraform features.

## Available Steering Files

- **getting-started** - Interactive setup guide for new OpenTofu projects
- **opentofu-best-practices** - Coding conventions and patterns (auto-loads for .tf files)

## Available MCP Servers

### opentofu
**URL:** `https://mcp.opentofu.org/sse` | **Connection:** SSE (no installation required)

| Tool | Purpose | Key Inputs |
|------|---------|------------|
| `search-opentofu-registry` | Search for providers, modules, resources, and data sources | `query` (string), `type` (`provider`\|`module`\|`resource`\|`data-source`\|`all`) |
| `get-provider-details` | Get detailed information about a specific provider | `namespace`, `name` |
| `get-module-details` | Get detailed information about a specific module | `namespace`, `name`, `target` |
| `get-resource-docs` | Get documentation for a specific resource type | `namespace`, `name`, `resource`, `version` (optional) |
| `get-datasource-docs` | Get documentation for a specific data source type | `namespace`, `name`, `dataSource`, `version` (optional) |

> **Tip:** Do **not** include prefixes like `terraform-provider-` in provider names or `terraform-aws-` in module names. Use simple terms: `aws`, `vpc`, `s3_bucket`.

## Examples

```javascript
// 1. Search for the AWS provider
search-opentofu-registry({ "query": "aws", "type": "provider" })

// 2. Get full provider details
get-provider-details({ "namespace": "hashicorp", "name": "aws" })

// 3. Get S3 bucket resource documentation
get-resource-docs({ "namespace": "hashicorp", "name": "aws", "resource": "s3_bucket" })

// 4. Get AMI data source documentation
get-datasource-docs({ "namespace": "hashicorp", "name": "aws", "dataSource": "ami" })

// 5. Find a VPC module
search-opentofu-registry({ "query": "vpc", "type": "module" })

// 6. Get VPC module details
get-module-details({ "namespace": "terraform-aws-modules", "name": "vpc", "target": "aws" })
```

## Workflow: Research → Write Config

```javascript
// Step 1: Search for the resource you need
search-opentofu-registry({ "query": "lambda", "type": "resource" })

// Step 2: Get full resource documentation
get-resource-docs({ "namespace": "hashicorp", "name": "aws", "resource": "lambda_function" })

// Step 3: Get provider details for version constraint
get-provider-details({ "namespace": "hashicorp", "name": "aws" })

// Now write accurate OpenTofu config using tofu CLI
```

## Configuration

**Prerequisites:** OpenTofu CLI (`tofu`) installed. No Docker or API token required for registry access — the MCP server connects automatically via SSE.

### OpenTofu CLI Workflow

```bash
tofu init      # Initialize working directory
tofu validate  # Validate configuration
tofu plan      # Preview changes
tofu apply     # Apply changes
tofu destroy   # Destroy infrastructure
tofu fmt       # Format configuration files
```

### OpenTofu vs Terraform CLI

OpenTofu uses the `tofu` command instead of `terraform`. The flags and subcommands are largely identical:

| Terraform | OpenTofu | Notes |
|-----------|----------|-------|
| `terraform init` | `tofu init` | Identical behavior |
| `terraform plan` | `tofu plan` | Identical behavior |
| `terraform apply` | `tofu apply` | Identical behavior |
| `terraform destroy` | `tofu destroy` | Identical behavior |
| `terraform fmt` | `tofu fmt` | Identical behavior |
| `terraform validate` | `tofu validate` | Identical behavior |
| `terraform state` | `tofu state` | Identical behavior |
| `terraform providers` | `tofu providers` | Identical behavior |

### OpenTofu-Specific Features

OpenTofu has additional features not present in Terraform:

- **Provider-defined functions** - Call functions defined by providers
- **`tofu test`** - Built-in testing framework (compatible with Terraform test syntax)
- **`removed` block** - Remove resources from state without destroying them
- **Registry**: OpenTofu has its own registry at `registry.opentofu.org` (also compatible with `registry.terraform.io`)

### Version Block

Both `terraform` and `opentofu` blocks are supported:

```hcl
# Standard (recommended for maximum compatibility)
terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## Best Practices

**Do:** Always `search-opentofu-registry` before `get-*-details`, pin versions, use modules, review plans

**Don't:** Hardcode credentials, skip plan review, use `auto_approve` blindly, use HCP Terraform tools (they are not applicable for OpenTofu)

## Troubleshooting

| Error | Solution |
|-------|----------|
| Provider/Module not found | Use `search-opentofu-registry` first to find valid namespace/name values |
| `tofu: command not found` | Install OpenTofu: https://opentofu.org/docs/intro/install/ |
| Provider version mismatch | Run `tofu init -upgrade` to update providers |
| State lock error | Ensure no other `tofu` process is running; use `tofu force-unlock <lock-id>` if stale |
| MCP server unreachable | Check network connectivity to `mcp.opentofu.org` |

## Resources

[OpenTofu Docs](https://opentofu.org/docs/) · [OpenTofu Registry](https://registry.opentofu.org) · [OpenTofu MCP Server](https://mcp.opentofu.org) · [OpenTofu GitHub](https://github.com/opentofu/opentofu)

---

**OpenTofu MCP:** `https://mcp.opentofu.org/sse` | **OpenTofu License:** MPL-2.0
