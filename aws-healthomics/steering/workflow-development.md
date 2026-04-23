# SOP: Workflow Development

## Purpose

This SOP defines how you, the agent, create and deploy genomics workflows for AWS HealthOmics from local files. For running deployed workflows, see the [Running a Workflow SOP](./running-a-workflow.md).

## Procedure: Creating a Workflow

### Language Selection
- Use WDL 1.1, Nextflow DSL2, or CWL 1.2.
- PREFER WDL 1.1 unless the user instructs otherwise.

### Structure
- Define a top-level entry point: `main.wdl`, `main.nf`, or `main.cwl`.
- IF writing a Nexflow workflow, THEN follow the nf-core project structure.
- IF writing WDL or CWL, THEN place tasks in a `./tasks/` folder structs in `./structs/` etc and reference these via imports

### Code Documentation
- Use comments to document the purpose of each task and workflow.
- For WDL: generate `meta` and `parameter_meta` blocks.
- For Nextflow: generate `nf-schema.json`.
- You MUST create a detailed `README.md` describing the purpose of the workflow, it's inputs, steps, and outputs.

### Scripting Rules
- Use BASH best practices for task/process command/script definitions.
- You MUST use `set -eu` to prevent silent failures.
- In WDL:
    - You MUST use `~{var_name}` interpolation syntax when interpolating variables in Strings.
    - You MUST use `<<< >>>` syntax to delimit the command block. DO NOT use curly braces.

### Parallelization
- WHERE possible, use `scatter` patterns (WDL) and `Channels` (Nextflow) to parallelize tasks.
- WHERE possible, scatter over arrays of samples.
- IF the software in a task is capable of using intervals THEN you MUST use intervals to parallelize (scatter) tasks.
- You MAY compute intervals in reference genomes so they have approximately even sizes.
- NOTE: HealthOmics supports large scatters but may require quota limit increases (Maximum concurrent tasks per run).

### Task Parameters
- ALL tasks/processes MUST declare CPU, memory, and container requirements.
- You MUST use at least 1 GB memory and 1 CPU for all tasks.
- You MAY set appropriate timeouts and retries using language-appropriate directives.
- You MUST declare a `container` for each task. The container value MAY be a variable.

### Outputs
- Final workflow outputs MUST be declared. Intermediate task outputs will NOT be retained by HealthOmics.
- WHEN using Nextflow `publishDir`, the path MUST be a subdirectory of `/mnt/workflow/pubdir`.
- WHEN using Nextflow 25.10+ `output { }` block, you MUST use ONLY relative paths in the `path` directive (HealthOmics manages the output directory).
- Workflow-level content (provenance reports, DAGs) MUST be written to `/mnt/workflow/output/`.

### Containers
- All workflow tasks run in containers. Containers MUST contain all software used in the script/command.
- If the container is in a public registry (e.g. docker, ecr-public, quay.io) you MUST use ECR Pull Through caches. Consult the [ECR Pull Through Cache SOP](./ecr-pull-through-cache.md).
- ALL other container images MUST be in the user's AWS ECR private registry in repositories readable by HealthOmics.
  - Use the `ListECRRepositories`, `CheckContainerAvailability` tools to find existing containers
  - Use the `CloneContainerToECR` tool to add containers to ECR 
- IF suitable containers cannot be found you SHOULD create appropriate Dockerfiles, build the images and push them to ECR
  - You MUST use x86_64 architecture containers `--platform linux/amd64`

### parameters.json
- You MUST define an example `parameters.json` for the workflow.
- You MAY use the `SearchGenomicsFiles` tool to help identify suitable inputs.
- Workflow parameters MUST NOT be namespaced:

  Correct:
  ```json
  {
    "input_file": "s3://bucket/path/to/input.vcf"
  }
  ```

  Wrong:
  ```json
  {
    "MyWorkflow.input_file": "s3://bucket/path/to/input.vcf"
  }
  ```

### Linting
- IF the workflow is WDL or CWL, you MUST call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to validate the workflow.
- When calling the `Lint*` tools you MUST supply a file path(s) or S3 URI(s) to reference the workflow content
- DO NOT proceed to deployment if linting errors exist — resolve them first.
- You MAY proceed if only warnings remain, but fixing these is desirable.

## Procedure: Deploying a Workflow

### Step 1. Packaging
- You MUST use the `PackageAHOWorkflow` tool to create a zip package of the workflow.
- You MUST use file paths or S3 paths to reference input files to the package AND the output path.
- For large workflows with more than ~15 files output to S3 is recommended.

### Step 2. Deploy to HealthOmics
- Call `CreateAHOWorkflow` to create the new workflow.
- IF updating an existing workflow: call `CreateAHOWorkflowVersion` instead — see the [Workflow Versioning SOP](./workflow-versioning.md).
  - Use semantic versioning (e.g., `1.0.0`, `1.0.1`).
- You MUST reference the package created in Step 1 as the workflow `definition_source`.
- You MUST reference the package as a file path or S3 URI.
- Call `GetAHOWorkflow` to verify the workflow was created successfully.

### Step 3. Run the Workflow
- Follow the [Running a Workflow SOP](./running-a-workflow.md) to execute the deployed workflow.
