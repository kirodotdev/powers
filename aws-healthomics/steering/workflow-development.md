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

### Nextflow Engine Version
- Pin the engine version with `manifest.nextflowVersion` in `nextflow.config` when the workflow depends on version-specific behavior or plugins.
- HealthOmics workflows run in an isolated network and CANNOT fetch plugins or modules at run time. The workflow MUST only depend on plugins pre-installed by HealthOmics for the target engine version. For the per-version plugin matrix and feature support, see [Phase 6: Nextflow Version Compatibility](./migration-guide-for-nextflow.md#phase-6-nextflow-version-compatibility) in the Nextflow migration guide.
- Nextflow v26.04 defaults to the strict (v2) syntax parser. Workflows authored against the legacy (v1) parser must opt in via `engineSettings.syntaxVersion = "v1"` at run time — see [Engine Settings](./running-a-workflow.md#engine-settings) in the Running a Workflow SOP.

### Nextflow Profiles
- HealthOmics supports profiles defined in the workflow's `nextflow.config` `profiles { }` block. Profiles MUST be defined inside the workflow zip — HealthOmics does NOT fetch profile definitions from external sources.
- Profiles are selected at run time via `engineSettings.profile` — see [Engine Settings](./running-a-workflow.md#engine-settings).

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
- You MUST read the verdict from `Return code:` inside `raw_output`. The tool's top-level `"status": "success"` means the linter RAN, not that the workflow is valid — a file that fails to parse is returned as `"status": "success"` with `Return code: 2` in `raw_output`. DO NOT branch on `status` alone.
- DO NOT proceed to deployment if linting errors exist — resolve them first.
- You MAY proceed if only warnings remain, but fixing these is desirable.
- A clean lint means the definition PARSES. It is NOT evidence that HealthOmics will accept it, nor that the workflow is semantically correct — see [Silent Incompatibilities](./migration-guide-for-wdl.md#silent-incompatibilities) for defects that lint clean and run to COMPLETED with the wrong result.

## Procedure: Deploying a Workflow

### Step 1. Packaging
- You MUST use the `PackageAHOWorkflow` tool to create a zip package of the workflow.
- You MUST use file paths or S3 paths to reference input files to the package AND the output path.
- For large workflows with more than ~15 files output to S3 is recommended.
- HealthOmics requires the definition to be a ZIP archive. A bare `.wdl`/`.nf`/`.cwl` file is packaged automatically WHERE `definition_source` is a file path or S3 URI, so a single-file workflow can be passed directly. This does NOT extend to a workflow with imports: only the named file is packaged, and the missing dependencies surface as import resolution errors at creation. Package anything with imports.
- The automatic packaging keeps the original filename and produces a single top-level entry, so `path_to_main` is not required — the file does not have to be named `main.wdl`.
- Inline definition content is left as-is, since that input is expected to be a ZIP already. A file with a `.zip` extension is also left as-is, so a corrupt archive reports as one rather than being wrapped again.

### Step 2. Deploy to HealthOmics
- Call `CreateAHOWorkflow` to create the new workflow.
- IF updating an existing workflow: call `CreateAHOWorkflowVersion` instead — see the [Workflow Versioning SOP](./workflow-versioning.md).
  - Use semantic versioning (e.g., `1.0.0`, `1.0.1`).
- You MUST reference the package created in Step 1 as the workflow `definition_source`.
- You MUST reference the package as a file path or S3 URI.
- Call `GetAHOWorkflow` to verify the workflow was created successfully.
  - Creation is asynchronous: `CreateAHOWorkflow` returns status `CREATING`, so you MUST poll until the status becomes `ACTIVE`. DO NOT treat the create response itself as success — an invalid definition is accepted at submission time and reported as `FAILED` only on a subsequent `GetAHOWorkflow`. See the [Troubleshooting SOP](./troubleshooting.md) for creation failure causes.

### Step 3. Run the Workflow
- Follow the [Running a Workflow SOP](./running-a-workflow.md) to execute the deployed workflow.
