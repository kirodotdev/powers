---
name: "stackgen"
displayName: "StackGen Infrastructure as Code"
description: "Design, manage, and deploy cloud infrastructure with StackGen - create appstacks, manage resources, configure environments, and push IaC to Git"
keywords: ["infrastructure", "iac", "cloud", "terraform", "aws", "azure", "gcp", "devops", "deployment"]
author: "StackGen"
---

# StackGen Power

StackGen helps you design and manage cloud infrastructure as code. This power provides tools to create appstacks (infrastructure configurations), manage cloud resources, configure environments, and integrate with Git.

## Available Tools

### Appstack Management
- `get_appstacks` - List all appstacks with filtering options
- `create_appstack` - Create new appstack for AWS, Azure, or GCP
- `copy_topology` - Duplicate existing topology to create new appstack
- `get_appstack_resources` - Get all resources in an appstack
- `get_stackgen_projects` - List all projects in your account

### Resource Operations
- `add_resource_to_appstack` - Add cloud resources (EC2, S3, VPC, etc.)
- `update_resource` - Modify resource configurations and variables
- `delete_resource` - Remove resources from appstack
- `get_resource_configurations` - Get current resource configuration
- `get_resource_type_configurations` - Get available config options for resource types
- `get_supported_resource_types` - List available resource types for an appstack
- `connect_resources` - Create connections/dependencies between resources
- `get_possible_resource_connections` - Get supported connection types

### Environment Profiles
- `get_env_profiles` - List environment profiles for a topology
- `create_env_profile` - Create new environment profile with variables
- `update_env_profile` - Update profile variables and description
- `delete_env_profile` - Delete environment profile

### Module Management
- `get_module_versions` - Get detailed module version information
- `module_usage_in_appstacks` - Find which appstacks use specific modules

### Git Integration
- `list_git_configuration` - List configured Git repositories
- `add_git_configuration` - Add Git repository configuration
- `push_appstack_to_git` - Push IaC to Git repository with commit message

### Policy & Compliance
- `get_policies` - Get available policies and benchmarks
- `get_current_violations` - Check policy violations for a topology

### Snapshots & Secrets
- `get_snapshots` - List available snapshots for appstack or resource
- `restore_snapshot` - Restore from a snapshot
- `list_available_secrets` - List secrets in vault

## Common Workflows

### Creating Infrastructure
1. Create an appstack: `create_appstack`
2. Add resources: `add_resource_to_appstack`
3. Connect resources: `connect_resources`
4. Create environment profiles: `create_env_profile`
5. Push to Git: `push_appstack_to_git`

### Managing Existing Infrastructure
1. List appstacks: `get_appstacks`
2. Get resources: `get_appstack_resources`
3. Update configurations: `update_resource`
4. Check compliance: `get_current_violations`

### Environment Management
1. Create profiles for dev/staging/prod: `create_env_profile`
2. Set environment-specific variables
3. Deploy to different environments using profiles

## Best Practices

- Use descriptive names for appstacks and resources
- Create environment profiles for different deployment stages
- Connect resources to establish proper dependencies
- Check policy violations before deployment
- Use Git integration for version control and collaboration
- Take snapshots before major changes
- Use modules for reusable infrastructure patterns
