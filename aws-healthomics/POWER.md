---
name: "aws-healthomics"
displayName: "AWS HealthOmics"
description: "Create, migrate, run, debug and optimize genomics workflows in AWS HealthOmics"
keywords: ["healthomics", "WDL", "CWL", "Nextflow", "workflow", "genomics", "bioinformatics", "pipeline"]
author: "AWS"
---

# When to use this power

When you want to create, migrate, run, debug and identify optimization opportunities for genomics workflows in AWS HealthOmics

# When to Load Steering Files

Whenever you are asked to perform a task related to any of the following scenarios - ensure you load and read the appropriate markdown file mentioned

- Creating a workflow from a remote Git repository URL (GitHub, GitLab, Bitbucket) -> use `./steering_files/git-integration.md` (takes precedence over workflow-development.md)
- Creating a new WDL, Nextflow or CWL workflow from local files -> use `./steering_files/workflow-development.md`
- Running a deployed HealthOmics workflow -> use `./steering_files/running-a-workflow.md`
- Submitting, monitoring, or managing batch runs (multiple samples/runs at once) -> use `./steering_files/batch-runs.md`
- Onboarding an existing WDL workflow ensuring compatibility with HealthOmics -> use `.\steering_files/migration-guide-for-wdl.md`
- Onboarding an existing Nextflow workflow ensuring compatibility with HealthOmics -> use `./steering_files/migration-guide-for-nextflow.md`
- Modifying, updating, or fixing an existing HealthOmics workflow -> use `./steering_files/workflow-versioning.md`
- Diagnosing workflow creation issues -> use `./steering_files/troubleshooting.md`
- Diagnosing run failures -> use `./steering_files/troubleshooting.md`
- Using public containers with HealthOmics via ECR Pullthrough Caches -> use `./steering_files/ecr-pull-through-cache.md`


# Onboarding

1. **Ensure the user has valid AWS Credentials** These are used by the HealthOmics MCP server to interact with AWS Services.
2. **Obtain the current account number**  Using `aws sts get-caller-identity`
3. **Create a `config.toml`** Create a `.healthomics/config.toml` file to specify run parameters. This helps you, the agent, create workflows and start runs with the correct settings:

    **config.toml:**
    ```toml
    // This is a service role used to start runs, it must have a trust policy for the omics principal
    omics_iam_role = "arn:aws:iam::<ACCOUNT_ID>:role/<HEALTHOMICS_ROLE_NAME>"
    // Outputs of runs are written here, the service role must have write permissions to this location
    run_output_uri = "s3://<YOUR_BUCKET>/healthomics-outputs/"
    run_storage_type = "DYNAMIC"  # Recommended for faster runs and automatic scaling
    ```

    - Ask the customer for the `omics_iam_role` and `run_output_uri` values. You may also offer to create them. Record the values by updating the toml
    - ALWAYS use settings from `.healthomics/config.toml` when they are set
4. **Dependencies** The MCP server configured by this power requires [`uvx`](https://docs.astral.sh/uv/getting-started/installation/)
```

# Integrations

This power integrates with [AWS Healthomics MCP Server](https://github.com/awslabs/mcp/tree/main/src/aws-healthomics-mcp-server)  (Apache-2.0 license).


# License

```
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```
