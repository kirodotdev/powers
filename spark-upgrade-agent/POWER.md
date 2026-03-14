---
name: "spark-upgrade-agent"
displayName: "Upgrade Spark applications on Amazon EMR"
description: "Accelerate Apache Spark version upgrades with conversational AI that automates code transformation, dependency resolution, and validation testing. Supports PySpark and Scala on EMR EC2 and EMR Serverless."
keywords: ["spark", "emr", "upgrade", "migration", "automation", "code-transformation", "pyspark", "scala", "aws"]
author: "AWS"
---

# [Onboarding](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-setup.html)

## Step 1: Validate Prerequisites

Before proceeding, ensure the following are installed:

- **AWS CLI**: Required for AWS authentication
  - Verify with: `aws --version`
  - Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

- **Python 3.10+**: Required for MCP proxy
  - Verify with: `python3 --version`
  - Install: https://www.python.org/downloads/release/python-3100/

- **uv package manager**: Required for MCP Proxy for AWS
  - Verify with: `uv --version`
  - Install: https://docs.astral.sh/uv/getting-started/installation/

- **AWS Credentials**: Must be configured
  - Verify with: `aws sts get-caller-identity`
  - Configure via AWS CLI, environment variables, or IAM roles
  - Identify the AWS Profile that the creds are configured for
    - You can do this with `echo ${AWS_PROFILE}`. No response likely means they are using the `default` profile
    - use this profile later when configuring the `spark-upgrade-profile`

**CRITICAL**: If any prerequisites are missing, DO NOT proceed. Install missing components first.

## Step 2: Deploy CloudFormation Stack

**Note**: If the customer already has a role configured with `sagemaker-unified-studio-mcp` permissions, please ignore this step, get the AWS CLI profile for that role from the customer and configure your (Kiro's) mcp.json file (typically located at `~/.kiro/settings/mcp.json`) with that profile. However, it is recommended to deploy the stack as will contain latest updates for permissions and role policies

1. Log into the AWS Console with the role your AWS CLI is configured with - this role must have permissions to deploy Cloud Formation stacks.
1. Navigate to [upgrade agent setup page](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-setup.html).
1. Deploy Cfn stack / resources to desired region
1. **Configure parameters** on the "Specify stack details" page:
   - **SparkUpgradeIAMRoleName**: Name of the IAM role for Spark upgrade process
   - **EnableEMREC2**: Enable EMR-EC2 upgrade permissions (default: true)
   - **EnableEMRServerless**: Enable EMR-Serverless upgrade permissions (default: true)
   - **StagingBucketPath**: S3 path for staging artifacts (e.g., `s3://my-bucket/spark-upgrade` or leave empty to auto-generate)
   - **UseS3Encryption**: Enable KMS encryption for S3 staging bucket (default: false)
   - **S3KmsKeyArn**: (Optional) ARN of existing KMS key for S3 bucket encryption
   - **CloudWatchKmsKeyArn**: (Optional) ARN of existing KMS key for CloudWatch Logs encryption
   - **EMRServerlessS3LogPath**: (Optional) S3 path where EMR-Serverless application logs are stored
   - **ExecutionRoleToGrantS3Access**: (Optional) IAM Role Name or ARN of existing EMR execution role
1. **Wait for deployment** to complete successfully.

## Step 3: Configure the AWS CLI with the MCP role and Kiro's mcp.json

1. Prompt the user to provide the region and role ARN from the Cfn stack deployment
1. Configure the CLI with the `spark-upgrade-profile`
    ```bash
    # run these as a single command so the use doesn't have to approve multiple times
    aws configure set profile.spark-upgrade-profile.source_profile <profile with Cloud Formation deployment permissions from earlier>
    aws configure set profile.spark-upgrade-profile.role_arn <role arn from Cloud Formation stack, provided by customer>
    aws configure set profile.spark-upgrade-profile.region <region from Cloud Formation stack, provided by customer>
    ```
1. then update your MCP json configuration file (typically located at `~/.kiro/settings/mcp.json`) with the region. Only edit your mcp.json, no other local copies, just the one that configures your mcp settings.

# [Overview](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/spark-upgrades.html)

A fully managed remote MCP server that provides specialized tools and guidance for upgrading Apache Spark applications on Amazon EMR. This server accelerates Spark version upgrades through automated analysis, code transformation, and validation capabilities.

**Important Note**: Not all MCP clients today support remote servers. Please make sure that your client supports remote MCP servers or that you have a suitable proxy setup to use this server.

## [Key Features & Capabilities](https://github.com/awslabs/mcp/blob/main/src/sagemaker-unified-studio-spark-upgrade-mcp-server/README.md#key-features--capabilities)

- **Project Analysis & Planning**: Deep analysis of Spark application structure, dependencies, and API usage to generate comprehensive step-by-step upgrade plans with risk assessment
- **Automated Code Transformation**: Automated PySpark and Scala code updates for version compatibility, handling API changes and deprecations
- **Dependency & Build Management**: Update and manage Maven/SBT/pip dependencies and build environments for target Spark versions with iterative error resolution
- **Comprehensive Testing & Validation**: Execute unit tests, integration tests and EMR validation jobs and validates the upgraded application against target spark version
- **Data Quality Validation**: Ensure data integrity throughout the upgrade process with validation rules
- **EMR Integration & Monitoring**: Submit and monitor EMR jobs for upgrade validation across Amazon EMR on EC2 and Amazon EMR Serverless
- **Observability & Progress Tracking**: Track upgrade progress, analyze results, and provide detailed insights throughout the upgrade process

## [Architecture](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/spark-upgrades.html#emr-spark-upgrade-agent-architecture)

The upgrade agent has three main components: any MCP-compatible AI Assistant in your development environment for interaction, the [MCP Proxy for AWS](https://github.com/aws/mcp-proxy-for-aws) that handles secure communication between your client and the MCP server, and the Amazon SageMaker Unified Studio Managed MCP Server (in preview) that provides specialized Spark upgrade tools for Amazon EMR. This diagram illustrates how you interact with the Amazon SageMaker Unified Studio Managed MCP Server through your AI Assistant.

![img](https://docs.aws.amazon.com/images/emr/latest/ReleaseGuide/images/SparkUpgradeIntroduction.png)


The AI assistant will orchestrate the upgrade using specialized tools provided by the MCP server following these steps:

- **Planning**: The agent analyzes your project structure and generates or revises an upgrade plan that guides the end-to-end Spark upgrade process.

- **Compile & Build**: Agent updates the build environment and dependencies, compiles the project, and iteratively fixes build and test failures.

- **Spark code edit tool**: Applies targeted code updates to resolve Spark version incompatibilities, fixing both build-time and runtime errors.

- **Execution & Validation**: Submits remote validation jobs to EMR (on EC2 or Serverless), monitors execution and logs, and iteratively fixes runtime and data-quality issues.

- **Observability**: Tracks upgrade progress using EMR observability tools and allows users to view upgrade analyses and status at any time.

Please refer to [Using Spark Upgrade Tools](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-tools.html) for a list of major tools for each steps.

### [Supported Upgrade Paths](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/spark-upgrades.html#emr-spark-upgrade-agent-architecture)
- We support Apache Spark upgrades from version 2.4 to 3.5. The corresponding deployment mode mappings are as follows
- **EMR Release Upgrades**:
    - For EMR-EC2
        - Source Version: EMR 5.20.0 and later
        - Target Version: EMR 7.12.0 and earlier, should be newer than EMR 5.20.0

    - For EMR-Serverless
        - Source Version: EMR Serverless 6.6.0 and later
        - Target Version: EMR Serverless 7.12.0 and earlier

## Available MCP Server

### spark-upgrade
**Connection:** MCP Proxy for AWS
**Authentication:** AWS IAM role assumption via spark-upgrade-profile
**Timeout:** 180 seconds

Provides comprehensive Spark upgrade tools including:
- Project Analysis & Planning
- Automated Code Transformation
- Dependency & Build Management
- Comprehensive Testing & Validation
- Data Quality Validation
- EMR Integration & Monitoring
- Observability & Progress Tracking

## [Usage Examples](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-prompt-examples.html)

1. **Run the spark upgrade analysis**:
  - EMR-S
    ```
    Help me upgrade my spark application in <project-path> from EMR-EC2 version 6.0.0 to 7.12.0. you can use EMR-S Application id xxg017hmd2agxxxx and execution role <role name> to run the validation and s3 paths s3://s3-staging-path to store updated application artifacts.
    ```
  - EMR-EC2
    ```
    Upgrade my Spark application <local-project-path> from EMR-S version 6.6.0 to 7.12.0. Use EMR-EC2 Cluster j-PPXXXXTG09XX to run the validation and s3 paths s3://s3-staging-path to store updated application artifacts.
    ```

2. **List the analyses**:
   ```
   Provide me a list of analyses performed by the spark agent
   ```

3. **Describe Analysis**:
   ```
   can you explain the analysis 439715b3-xxxx-42a6-xxxx-3bf7f1fxxxx
   ```
4. **Reuse Plan for other analysis**:
    ```
    Use my upgrade_plan spark_upgrade_plan_xxx.json to upgrade my project in <project-path>
    ```

## [Full Features and Capabilities](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-features.html)

### Supported Technologies

* Languages: Python and Scala applications
* Build Systems: Maven and SBT for Scala projects; requirements.txt, Pipfile, and Setuptools for Python projects
* Target Platforms: Amazon EMR and EMR Serverless
* Supported Versions: We support Apache Spark upgrades from version 2.4 to 3.5. The corresponding deployment mode mappings are as follows
  * For EMR-EC2
    * Source Version: EMR 5.20.0 and later
    * Target Version: EMR 7.12.0 and earlier, should be newer than EMR 5.20.0
  * For EMR Serverless
    * Source Version: EMR Serverless 6.6.0 and later
    * Target Version: EMR Serverless 7.12.0 and earlier

### What We Upgrade

The upgrade agent provide comprehensive Spark application upgrades:

* Build Configuration: Automatically updates dependency management files (pom.xml, requirements.txt, etc.)
* Source Code: Fixes API compatibility issues and deprecated method usage
* Test Code: Ensures unit and integration tests work with the target Spark version
* Dependencies: Upgrades packaged dependencies to versions compatible with target EMR version
* Validation: Compiles and validates applications on target EMR clusters
* Data Quality Analysis: Detects schema differences, value-level statistical drifts (min/max/mean), and aggregate row-count mismatches, with detailed impact reporting.

### Scope of Upgrades and User Requirements

* Cluster Management: Spark Upgrade Agent focuses on application code upgrades. Target EMR clusters for new versions must be created and managed by users.
* Bootstrap Actions: Spark Upgrade Agent does not upgrade custom bootstrap scripts outside of Spark application code. They need to be upgraded by the user.
* Upgrade for Build and Tests: The upgrade agent will perform build and run your unit and integration tests on your development environment locally to validate that applications compile successfully with the target Spark version. If you have restrictions (security policies, resource limitations, network restrictions, or corporate guidelines) for Spark application code for local execution, consider using Amazon SageMaker Unified Studio VSCode IDE Spaces or EC2 to run the upgrade agent. The upgrade agent uses your target EMR-EC2 cluster or EMR-S applications to validate and upgrade end-to-end.
* Error-Driven Approach: The upgrade agent uses an error-driven methodology, making one fix at a time based on compilation or runtime errors rather than multiple fixes at once. This iterative approach ensures each issue is properly addressed before proceeding to the next.
* Private Dependencies: Dependencies installed from private artifact repositories cannot be automatically upgraded as part of this process. They must be upgraded by the user.
* Regional resources: Spark upgrade agent is regional and uses the underlying EMR resources in that region for the upgrade process. Cross-region upgrades are not supported.

## [Data Usage](https://github.com/awslabs/mcp/blob/main/src/sagemaker-unified-studio-spark-upgrade-mcp-server/README.md#data-usage)

This server processes your code and configuration files to provide upgrade recommendations. No sensitive data is stored permanently, and all processing follows AWS data protection standards.

## FAQs ([1](https://github.com/awslabs/mcp/blob/main/src/sagemaker-unified-studio-spark-upgrade-mcp-server/README.md#data-usage), [2](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-troubleshooting.html#spark-upgrade-agent-qa))

### 1. Which Spark versions are supported?
- For EMR-EC2
    - Source Version: EMR 5.20.0 and later
    - Target Version: EMR 7.12.0 and earlier, should be newer than EMR 5.20.0

- For EMR-Serverless
    - Source Version: EMR Serverless 6.6.0 and later
    - Target Version: EMR Serverless 7.12.0 and earlier

### 2. Can I use this for Scala applications?

Yes, the agent supports both PySpark and Scala Spark applications, including Maven and SBT build system

### 3. What about custom libraries and UDFs?

The agent analyzes custom dependencies and provides guidance for updating user-defined functions and third-party libraries.

### 4. How does data quality validation work?

The agent compares output data between old and new Spark versions using validation rules and statistical analysis.

### 5. Can I customize the upgrade process?

Yes, you can modify upgrade plans, exclude specific transformations, and customize validation criteria based on your requirements.

### 6. What if the automated upgrade fails?

The agent provides detailed error analysis, suggested fixes, and fallback strategies. You maintain full control over all changes.

### 7. Should I enable "trust" setting for the tools by default?

Do not turn on "trust" setting by default for all tool calls initially and operate on git-versioned build environment. Review each tool execution to understand what changes are being made, for example review the upgrade plan before providing consent. Never trust the Kiro or your Agent's fs_write tool - this tool modifies your project files and you should always review changes before they are saved/committed. In general, examine all proposed file changes before allowing them to be written. Use git to version changes and create checkpoints throughout the upgrade process. Build confidence gradually - If you are repeatedly using the system for multiple upgrades and have gained confidence in the tools, you can selectively trust certain tools.

## [Troubleshooting Access to the Remote MCP Server](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-upgrade-agent-troubleshooting.html)

The error message from the upgrade process is available in different ways for different MCP clients. In this page, we list some general guidance for common issues you may see using Apache Spark Upgrade Agent for Amazon EMR.

### Topics

### Error: SMUS Managed MCP server failed to load
* Verify your MCP configuration are properly configured.
* Validate JSON syntax:
* Ensure your JSON is valid with no syntax errors
* Check for missing commas, quotes, or brackets
* Verify your local AWS credentials and verify the policy for the MCP IAM role are properly configured.

### Observation : Slow Tool Loading
* Tools may take a few seconds to be loaded on first attempt of launching the server.
* If tools don't appear, try restarting the chat,
* Run /tools command to verify tool availability.
* Run /mcp if the server is launched without error.

### Error: Tool Invocation Failed with Throttling Error
If you hit your service limit, please wait for a few seconds to issue a tool invocation if you see the throttling exception.

### Error: Tool Responds With User Error
* AccessDeniedException - check the error message and fix the permission issue.
* InvalidInputException - check the error message and correct the tool input parameters.
* ResourceNotFoundException - check the error message and fix the input parameter for resource reference.

### Error: Tool Responds With Internal Error
* If you see The service is handling high-volume requests please retry the tool invocation in a few seconds.
* If you see INTERNAL SERVICE EXCEPTION please document the analysis id, tool name, any error message available from the mcp log or tool response and optional sanitized conversation history and reach out to the AWS support.
