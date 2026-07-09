# SOP: WDL Workflow Migration to AWS HealthOmics

## Purpose

This SOP defines how you, the agent, migrate on-prem or Cromwell-variant WDL workflows to run in AWS HealthOmics. This involves container migration, runtime configuration, storage migration, and output path standardization.

## Constraints

AWS HealthOmics requires:
- All containers MUST be in ECR repositories accessible to HealthOmics.
- All input files MUST be in S3.
- All tasks MUST have explicit CPU and memory runtime attributes.
- Output files are automatically collected from task outputs.
- WDL 1.0+ syntax is required (draft-2 is NOT supported).
- WDL 1.1 syntax is preferred

## Non-Goals

- DO NOT modify the scientific logic of the workflow.
- DO NOT change the workflow structure or task dependencies.
- DO NOT perform performance optimization beyond HealthOmics requirements.

## Procedure

### Phase 1: Container Inventory and Migration

**Objective**: Identify all containers and create ECR migration plan.

**Steps**:
1. Extract all unique container URIs from runtime sections:
   - Scan all WDL files for `docker:` and `container:` runtime attributes.
   - Check imported WDL files and sub-workflows.
   - Identify containers in struct/object definitions.
2. Generate `container_inventory.csv` with columns: Task name, Original container URI, Container registry, Tool name and version, Target ECR URI.
3. Create `scripts/migrate_containers_to_ecr.sh` to:
   - Find or create ECR repositories for each tool with access policies allowing the omics principal to read.
   - Pull each container from source registry ensuring x86 containers are pulled.
   - Tag for ECR: `<account>.dkr.ecr.<region>.amazonaws.com/<workflow-name>/<tool>:<version>`
   - Push to ECR repositories.
4. Create `scripts/update_container_refs.sh` to:
   - Replace all container URIs in WDL task runtime sections.
   - Update to use ECR registry.
   - Parameterize container references.
5. Create `healthomics.inputs.json` with ECR registry base path parameter.

**Done WHEN**:
- `container_inventory.csv` documents all containers.
- Migration script pushes all containers to ECR.
- All WDL task runtime sections use ECR URIs.
- Zero references to external registries remain.
- At least 5 key containers verified accessible from ECR.

### Phase 2: Runtime Attribute Audit

**Objective**: Ensure all tasks have CPU and memory runtime declarations.

**HealthOmics Limits**: Min 2 vCPUs / 4 GiB memory. Max 96 vCPUs / 768 GiB memory.

**Steps**:
1. Scan all WDL files for runtime sections.
2. Identify tasks missing `cpu`, `memory`, or `disks` attributes.
3. Check for dynamic resource calculations.
4. Add or update runtime attributes in all tasks:
   ```wdl
   runtime {
       docker: "..."
       cpu: 4
       memory: "8 GiB"
   }
   ```
5. Document resource requirements per task in `docs/healthomics_resources.md`.
6. Create validation script to confirm no task lacks runtime attributes.

**Done WHEN**:
- All tasks have `docker` (or `container` for WDL 1.1), `cpu`, and `memory` runtime attributes.
- All resources meet HealthOmics minimums (≥2 vCPU, ≥4 GB).

### Phase 3: WDL Version Compatibility

**Objective**: Ensure WDL 1.0+ compatibility.

**Steps**:
1. Scan all WDL files for version statements. Identify draft-2 syntax usage.
2. Upgrade syntax as needed:
   - Update version declaration to `version 1.0` or `version 1.1`.
   - Replace `${}` with `~{}` for command interpolation.
   - Update type declarations.
   - Replace deprecated functions.
   - Update struct definitions if using WDL 1.1.
   - Replace `command { ... }` with `command <<< ... >>>` for WDL 1.1+.
3. Validate imports:
   - Ensure all imported WDL files are the same version as the main workflow.
   - Update import statements to use proper aliasing.
   - Check for circular dependencies.
4. Lint:
   - Call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to verify syntax.
   - For large workflows, use `miniwdl check` if available locally.
   - Resolve all issues.

**Done WHEN**:
- All WDL files declare version 1.0 or higher.
- No draft-2 syntax remains.
- Syntax validation passes for all WDL files.
- All imports resolve correctly.

### Phase 4: Reference and Input File Migration

**Objective**: Migrate all reference files and inputs to S3.

**Steps**:
1. Identify input files and reference data:
   - Extract all `File` and `File?` input parameters.
   - Scan for hardcoded file paths in command sections.
   - List reference files in workflow inputs.
   - Identify files in `Array[File]` inputs.
   - Generate reference inventory with sizes.
2. Design S3 bucket structure appropriate for the workflow. Example:
   ```
   s3://<bucket>/
   ├── references/
   │   ├── Homo_sapiens/
   │   │   ├── GATK/GRCh38/
   │   │   └── NCBI/GRCh38/
   │   └── Mus_musculus/
   ├── annotation/
   └── inputs/
       └── samples/
   ```
3. Create `scripts/migrate_references_to_s3.sh` to:
   - Copy from existing S3 locations if available.
   - Upload local files if needed.
   - Obtain and upload `http(s)://` and `ftp://` resources to S3.
   - Set appropriate S3 storage class (Intelligent-Tiering).
   - Validate checksums after upload.
4. Create `healthomics.inputs.json` with S3 URIs for all File inputs.
5. Update any hardcoded paths in command sections to use input variables.

**Done WHEN**:
- Reference inventory CSV lists all files and sizes.
- All reference files accessible from S3.
- `healthomics.inputs.json` uses S3 URIs exclusively.
- No hardcoded file paths in command sections.

### Phase 5: Output Collection Strategy

**Objective**: Ensure all workflow outputs are properly declared.

**Key Rule**: Intermediate files are automatically cleaned up unless declared as workflow outputs.

**Steps**:
1. Audit workflow outputs:
   - Identify all task outputs that should be retained.
   - Check workflow output section completeness.
   - Verify output types (`File`, `Array[File]`, etc.).
2. Update workflow output section:
   ```wdl
   output {
       File final_vcf = CallVariants.vcf
       File final_vcf_index = CallVariants.vcf_index
       Array[File] bam_files = AlignReads.bam
       File metrics_report = CollectMetrics.report
   }
   ```
3. Document output structure in `docs/healthomics_outputs.md`.
4. Verify all task output declarations and glob patterns.

**Done WHEN**:
- Workflow output section includes all desired outputs.
- All task outputs properly declared.
- Output types correctly specified.

### Phase 6: Configuration and Testing

**Objective**: Create HealthOmics-specific configuration and validate.

**Steps**:
1. Create comprehensive `healthomics.inputs.json` with all required inputs using S3 URIs.
2. Create `test_healthomics.inputs.json`:
   - Use small test dataset (e.g., chr22 only).
   - Minimal sample set (1-2 samples).
   - Use DYNAMIC storage for test runs.
3. Execute test plan:
   - Stage 1: Validate WDL syntax and lint.
   - Stage 2: Test on HealthOmics with minimal dataset.
   - Stage 3: Test with full-size dataset.
   - Stage 4: Resource optimization.
4. IF a test run fails, call `DiagnoseAHORunFailure` to identify issues and remediate.

**Done WHEN**:
- `healthomics.inputs.json` complete with all required inputs.
- WDL validation passes.
- Test workflow completes successfully on HealthOmics.

## Technical Patterns

### Container Runtime (Before/After)
```wdl
# Before
runtime {
    docker: "quay.io/biocontainers/bwa:0.7.17--h5bf99c6_8"
}

# After
runtime {
    docker: "<account-id>.dkr.ecr.<region>.amazonaws.com/workflow-name/bwa:0.7.17--h5bf99c6_8"
    cpu: 4
    memory: "8 GB"
}
```

### WDL Version Upgrade (Before/After)
```wdl
# Before (draft-2)
workflow MyWorkflow {
    call MyTask { input: file = input_file }
}

# After (1.0+)
version 1.0

workflow MyWorkflow {
    input {
        File input_file
    }
    call MyTask { input: file = input_file }
    output {
        File result = MyTask.output_file
    }
}
```

### S3 Input (Before/After)
```json
// Before
{ "WorkflowName.reference_fasta": "/path/to/reference.fasta" }

// After
{ "WorkflowName.reference_fasta": "s3://bucket/references/Homo_sapiens/GATK/GRCh38/Sequence/reference.fasta" }
```

## WDL-Specific Considerations

- **Scatter-Gather**: Ensure scattered tasks have appropriate resources. Verify `Array[File]` outputs are properly collected.
- **Sub-Workflows**: Ensure all imported WDL files are migrated. Verify sub-workflow outputs are properly passed.
- **Optional Inputs**: Handle `File?` inputs gracefully. Use `select_first()` or `defined()` appropriately.
- **Command Section**: Use `~{}` for variable interpolation (WDL 1.0+). Avoid hardcoded paths. Use `sep()` for array joining.

## Dependencies

- AWS CLI configured with appropriate permissions
- ECR repositories created
- S3 bucket(s) created with appropriate permissions
- HealthOmics service access
- HealthOmics MCP server
- Docker/Finch/Podman installed for container operations

## References

- [AWS HealthOmics Documentation](https://docs.aws.amazon.com/omics/)
- [WDL 1.0 Specification](https://github.com/openwdl/wdl/blob/main/versions/1.0/SPEC.md)
- [WDL 1.1 Specification](https://github.com/openwdl/wdl/blob/main/versions/1.1/SPEC.md)
- [WDL on AWS HealthOmics](https://docs.aws.amazon.com/omics/latest/dev/workflows.html)
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)
