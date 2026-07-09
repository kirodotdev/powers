# SOP: Git Integration for HealthOmics Workflows

## Purpose

This SOP defines how you, the agent, handle workflow creation when a user provides a Git repository URL. You MUST use the `definitionRepository` parameter instead of manually cloning, packaging, and uploading.

## Trigger Conditions

Follow this SOP WHEN:
- User provides a GitHub, GitLab, or Bitbucket repository URL
- User wants to create a workflow from a specific branch, tag, or commit
- User references a public workflow repository (e.g., nf-core pipelines)
- User wants to keep their workflow definition in source control

DO NOT follow this SOP WHEN:
- User has local workflow files not in a Git repository — use traditional packaging instead
- User provides an S3 URI for the workflow definition
- User explicitly requests local packaging

## Supported Git Providers

| Provider | URL Format |
|----------|------------|
| GitHub | `https://github.com/owner/repo` |
| GitLab | `https://gitlab.com/owner/repo` |
| Bitbucket | `https://bitbucket.org/owner/repo` |
| GitLab Self-Managed | `https://gitlab.example.com/owner/repo` |
| GitHub Enterprise | `https://github.example.com/owner/repo` |

## Procedure

### Step 1: Check for Existing Code Connections

1. Call `ListCodeConnections(provider_type_filter="GitHub")` (or GitLab, Bitbucket as appropriate).
2. IF a connection with status `AVAILABLE` exists, use its `connection_arn`. Proceed to Step 3.
3. IF no suitable connection exists, proceed to Step 2.

### Step 2: Create Code Connection (If Needed)

1. Call `CreateCodeConnection` with:
   - `connection_name`: a descriptive name (e.g., `"my-github-connection"`)
   - `provider_type`: one of `GitHub`, `GitLab`, `Bitbucket`, `GitHubEnterpriseServer`, `GitLabSelfManaged`
2. INFORM the user they must complete OAuth authorization in the AWS Console.
   - The tool returns a `console_url` — provide this to the user.
   - Connection status will be `PENDING` until OAuth is completed.
3. Call `GetCodeConnection(connection_arn="...")` to verify status.
4. DO NOT proceed until status is `AVAILABLE`.

### Step 3: Parse Repository Information

Extract from the user-provided URL:
- `fullRepositoryId`: `owner/repo` format (e.g., `nf-core/rnaseq`)
- `sourceReference`:
  - `type`: `BRANCH`, `TAG`, or `COMMIT`
  - `value`: the branch name, tag name, or commit SHA

### Step 4: Check for Container Registry Map

1. Check if the repository contains a container registry map file at common locations: `container-registry-map.json`, `registry-map.json`, `.healthomics/container-registry-map.json`.
2. IF a container registry map exists:
   - Pass `container_registry_map_uri` pointing to the S3 location if uploaded, OR use `container_registry_map` parameter with the map contents.
3. IF no container registry map exists:
   - Analyze the workflow definition for container references.
   - IF containers reference public registries (Docker Hub, Quay.io, ECR Public):
     - Follow the [ECR Pull Through Cache SOP](./ecr-pull-through-cache.md).
     - Call `CreateContainerRegistryMap` to generate a registry map.
     - Call `ValidateHealthOmicsECRConfig` to verify ECR configuration.
   - IF containers reference private ECR repositories:
     - Proceed without a container registry map.

### Step 5: Create the Workflow

Call `CreateAHOWorkflow` with the `definition_repository` parameter:

```
CreateAHOWorkflow(
    name="my-workflow",
    definition_repository={
        "connectionArn": "<connection_arn>",
        "fullRepositoryId": "owner/repo",
        "sourceReference": {
            "type": "BRANCH",
            "value": "main"
        },
        "excludeFilePatterns": ["test/*", "docs/*"]  # optional
    },
    description="Workflow created from Git repository",
    parameter_template_path="parameters.json",  # optional
    readme_path="README.md",  # optional
    container_registry_map={...}  # if needed
)
```

### Step 6: Verify Workflow Creation

1. Call `GetAHOWorkflow(workflow_id="...")`.
2. Confirm status is `ACTIVE`.
3. Confirm workflow type matches expected engine (WDL, NEXTFLOW, CWL).

## Parameter Reference

### definitionRepository Object

| Field | Required | Description |
|-------|----------|-------------|
| `connectionArn` | Yes | ARN of the CodeConnection |
| `fullRepositoryId` | Yes | `owner/repo` format |
| `sourceReference.type` | Yes | `BRANCH`, `TAG`, or `COMMIT` |
| `sourceReference.value` | Yes | Branch name, tag name, or commit SHA |
| `excludeFilePatterns` | No | Glob patterns for files to exclude |

### Additional Parameters

| Parameter | Description |
|-----------|-------------|
| `parameter_template_path` | Path to parameter template JSON within the repo |
| `readme_path` | Path to README markdown file within the repo |

## Common Scenarios

### nf-core Pipeline
```
1. ListCodeConnections(provider_type_filter="GitHub")
2. IF no connection: CreateCodeConnection(connection_name="github", provider_type="GitHub")
3. CreateAHOWorkflow(
       name="nf-core-rnaseq",
       definition_repository={
           "connectionArn": "...",
           "fullRepositoryId": "nf-core/rnaseq",
           "sourceReference": {"type": "TAG", "value": "3.14.0"}
       },
       container_registry_map={...}
   )
```

### Specific Branch
```
CreateAHOWorkflow(
    name="my-workflow-dev",
    definition_repository={
        "connectionArn": "...",
        "fullRepositoryId": "my-org/my-workflow",
        "sourceReference": {"type": "BRANCH", "value": "develop"}
    }
)
```

### Specific Commit
```
CreateAHOWorkflow(
    name="my-workflow",
    definition_repository={
        "connectionArn": "...",
        "fullRepositoryId": "owner/repo",
        "sourceReference": {"type": "COMMIT", "value": "abc123def456"}
    }
)
```

## Error Handling

### Connection Not Available
- IF `GetCodeConnection` returns status `PENDING`:
  - Remind user to complete OAuth authorization in AWS Console.
  - Provide the console URL from the connection creation response.
  - WAIT for user confirmation before retrying.

### Repository Access Denied
- Verify the connection has appropriate repository permissions.
- For private repositories, ensure OAuth scope includes repo access.
- Check that `fullRepositoryId` is correct.

### Workflow Definition Not Found
- Verify the repository contains a valid workflow file (`main.wdl`, `main.nf`, `main.cwl`).
- Check `excludeFilePatterns` isn't excluding the main workflow file.
- Use `path_to_main` parameter if the main file isn't at the repository root.

## Required IAM Permissions

Users need these permissions for Git integration:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "codeconnections:CreateConnection",
                "codeconnections:GetConnection",
                "codeconnections:ListConnections",
                "codeconnections:UseConnection"
            ],
            "Resource": "*"
        }
    ]
}
```

## References

- [AWS HealthOmics Git Integration Documentation](https://docs.aws.amazon.com/omics/latest/dev/workflows-git-integration.html)
- [CreateWorkflow API Reference](https://docs.aws.amazon.com/omics/latest/api/API_CreateWorkflow.html)
- [ECR Pull Through Cache SOP](./ecr-pull-through-cache.md)
