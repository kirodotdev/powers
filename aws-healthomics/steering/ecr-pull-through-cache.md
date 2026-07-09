# SOP: ECR Pull-Through Cache and Container Registry Maps

## Purpose

This SOP defines how you, the agent, configure ECR Pull-Through Caches and Container Registry Maps so that HealthOmics workflows can access containers from public registries. HealthOmics requires containers from PRIVATE ECR repositories with correct permissions.

## Key Concepts

- **ECR Pull-Through Cache**: Automatically pulls and caches containers from upstream registries. Workflows reference containers using ECR private URIs.
- **Container Registry Map**: Optional mapping that allows workflows to use original public registry URIs while HealthOmics automatically redirects to your ECR pull-through caches.

## When to Use Each Approach

- **New workflows**: Use ECR pull-through caches with private ECR URIs (registry maps not needed).
- **Migrating existing workflows**: Use container registry maps to avoid changing container URIs in workflow definitions.

## Prerequisites

- AWS credentials configured with appropriate IAM permissions for ECR and HealthOmics.
- For Docker Hub: a Docker Hub access token (obtain from https://docs.docker.com/security/access-tokens/).

## MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `ValidateHealthOmicsECRConfig` | Validate ECR configuration for HealthOmics |
| `ListPullThroughCacheRules` | List existing PTC rules with HealthOmics usability status |
| `CreatePullThroughCacheForHealthOmics` | Create PTC rules pre-configured for HealthOmics |
| `ListECRRepositories` | List ECR private repositories with HealthOmics accessibility status |
| `CheckContainerAvailability` | Check if a container is available and accessible by HealthOmics |
| `CloneContainerToECR` | Clone containers to ECR with HealthOmics access permissions |
| `GrantHealthOmicsRepositoryAccess` | Grant HealthOmics access to an ECR repository |
| `CreateContainerRegistryMap` | Generate container registry maps for workflows |

## Procedure

### Step 1: Validate Current ECR Configuration

1. Call `ValidateHealthOmicsECRConfig` to check:
   - Existing pull-through cache rules.
   - Registry permissions policy for HealthOmics.
   - Repository creation templates.
   - Required permissions for each prefix.
2. Review the returned list of issues with specific remediation steps.

### Step 2: Create Secrets for Authenticated Registries

IF the upstream registry requires authentication, create secrets in AWS Secrets Manager BEFORE creating pull-through cache rules.

Docker Hub Secret (required for Docker Hub):
```bash
aws secretsmanager create-secret \
    --name "ecr-pullthroughcache/docker-hub" \
    --description "Docker Hub credentials for ECR pull through cache" \
    --secret-string '{"username": "your-docker-username", "accessToken": "your-docker-access-token"}' \
    --region us-east-1
```

Quay.io Secret (ONLY for private Quay repositories):
```bash
aws secretsmanager create-secret \
    --name "ecr-pullthroughcache/quay" \
    --description "Quay.io credentials for ECR pull through cache" \
    --secret-string '{"username": "your-quay-username", "accessToken": "your-quay-access-token"}' \
    --region us-east-1
```

### Step 3: Create Pull-Through Cache Rules

1. Call `ListPullThroughCacheRules` to check for existing rules. IF a valid cache already exists for the upstream registry, reuse it — DO NOT create another.
2. Call `CreatePullThroughCacheForHealthOmics` with:
   - `upstream_registry`: `docker-hub`, `quay`, or `ecr-public`
   - `ecr_repository_prefix`: OPTIONAL custom prefix (defaults to registry type name)
   - `credential_arn`: OPTIONAL Secrets Manager ARN (REQUIRED for `docker-hub`)

This tool automatically:
- Creates the pull-through cache rule.
- Updates the registry permissions policy for HealthOmics.
- Creates a repository creation template granting HealthOmics image pull permissions.

| Registry | upstream_registry | credential_arn | Notes |
|----------|------------------|----------------|-------|
| Docker Hub | `docker-hub` | Required | Use secret ARN from Step 2 |
| Quay.io | `quay` | Optional | Only needed for private repos |
| ECR Public | `ecr-public` | Not needed | Public access |

### Step 4: Verify Pull-Through Cache Configuration

1. Call `ListPullThroughCacheRules` to verify rules are properly configured.
2. A rule is usable by HealthOmics WHEN:
   - Registry permissions policy grants HealthOmics required permissions.
   - Repository creation template exists for the prefix.
   - Template grants HealthOmics image pull permissions.

### Step 5: Check Container Availability

1. Call `CheckContainerAvailability` with:
   - `repository_name`: ECR repository name (e.g., `docker-hub/library/ubuntu`)
   - `image_tag`: image tag (default: `latest`)
   - `initiate_pull_through`: set to `true` to trigger pull-through for missing images (recommended)

Example repository names for pull-through caches:
- Docker Hub official: `docker-hub/library/ubuntu`
- Docker Hub user: `docker-hub/broadinstitute/gatk`
- Quay.io: `quay/biocontainers/samtools`
- ECR Public: `ecr-public/lts/ubuntu`

### Step 6: Clone Containers (Alternative Approach)

IF you need containers from registries NOT supported by pull-through cache (e.g., Seqera Wave), OR you want to copy without pull-through:

1. Call `CloneContainerToECR` — it will:
   - Parse source image references (handles Docker Hub shorthand).
   - Use existing pull-through cache rules when available.
   - Grant HealthOmics access permissions automatically.
   - Return the ECR URI and digest.

Supported image reference formats:
- `ubuntu:latest` → Docker Hub official
- `myorg/myimage:v1` → Docker Hub user
- `quay.io/biocontainers/samtools:1.17` → Quay.io
- `public.ecr.aws/lts/ubuntu:22.04` → ECR Public
- Image URIs with hashes (`sha256:...`) are also supported.

### Step 7: Grant HealthOmics Access to Existing Repositories

1. Call `ListECRRepositories` to list repositories and check HealthOmics accessibility status.
2. For repositories NOT created through pull-through cache, call `GrantHealthOmicsRepositoryAccess` to add required permissions:
   - `ecr:BatchGetImage`
   - `ecr:GetDownloadUrlForLayer`
3. The tool preserves existing repository policies while adding HealthOmics permissions.

### Step 8: Create Container Registry Maps (Optional)

IF migrating existing workflows that reference public container URIs you MUST create a container registry map (preferred) ALTERNATIVELY you MAY replace the existing container URIs with the new ECR Private URIs:

IF you have cloned containers not supported by ECR PTC you MUST provide image mappings for those containers:

1. Call `CreateContainerRegistryMap` with:
   - `include_pull_through_caches`: auto-discover and include PTC rules (default: `true`)
   - `additional_registry_mappings`: custom registry mappings
   - `image_mappings`: specific image overrides (take precedence over registry mappings)

2. Use the generated map:
   - Pass directly to `CreateAHOWorkflow` via `container_registry_map` parameter.
   - OR upload to S3 and reference via `container_registry_map_uri` parameter.

Example registry map:
```json
{
    "registryMappings": [
        { "upstreamRegistryUrl": "registry-1.docker.io", "ecrRepositoryPrefix": "docker-hub" },
        { "upstreamRegistryUrl": "quay.io", "ecrRepositoryPrefix": "quay" },
        { "upstreamRegistryUrl": "public.ecr.aws", "ecrRepositoryPrefix": "ecr-public" }
    ]
}
```

Example image overrides:
```json
{
    "imageMappings": [
        {
            "sourceImage": "ubuntu",
            "destinationImage": "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-hub/library/ubuntu:20.04"
        }
    ]
}
```

Registry mappings and image mappings can be combined. Image mappings override any matching registry mapping.

### Step 9: Configure HealthOmics Service Role

ENSURE the HealthOmics service role has ECR permissions:
```json
{
    "Effect": "Allow",
    "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchCheckLayerAvailability"
    ],
    "Resource": [
        "arn:aws:ecr:us-east-1:123456789012:repository/docker-hub/*",
        "arn:aws:ecr:us-east-1:123456789012:repository/quay/*",
        "arn:aws:ecr:us-east-1:123456789012:repository/ecr-public/*"
    ]
}
```

Adjust repository ARN patterns to match your pull-through cache prefixes.

## Regions

Configure your ECR registry and HealthOmics workflows in the SAME region. IF using multiple regions, repeat these steps in each region.

## Quick Reference: Common Workflows

### New Workflow with Pull-Through Cache
1. `CreatePullThroughCacheForHealthOmics` — create PTC rule.
2. `ValidateHealthOmicsECRConfig` — verify configuration.
3. Use ECR URIs in workflow OR use container registry mapping.

### Migrate Existing Workflow
1. `CreatePullThroughCacheForHealthOmics` — create required PTC rules.
2. `CreateContainerRegistryMap` — generate registry map.
3. `CloneContainerToECR` — clone containers from unsupported registries.
4. `CreateAHOWorkflow` with `container_registry_map` parameter.

### Verify Container Access
1. `CheckContainerAvailability` with `initiate_pull_through: true`.
2. `ListECRRepositories` with `filter_healthomics_accessible: true`.

### Troubleshoot Access Issues
1. `ValidateHealthOmicsECRConfig` — check for configuration issues.
2. `ListPullThroughCacheRules` — verify PTC rule status.
3. `GrantHealthOmicsRepositoryAccess` — fix repository permissions.
