# SOP: Nextflow Workflow Migration to AWS HealthOmics

## Purpose

This SOP defines how you, the agent, onboard an existing Nextflow workflow to be compatible with AWS HealthOmics. This involves container migration, resource configuration, storage migration, and output path standardization.

## Constraints

AWS HealthOmics requires:
- All containers MUST be in ECR repositories accessible to HealthOmics.
- All input files MUST be in S3.
- All processes MUST have explicit CPU and memory declarations.
- Output directories MUST use `/mnt/workflow/pubdir/` prefix.

## Non-Goals

- DO NOT modify the scientific logic of the workflow.
- DO NOT change the workflow structure or dependencies.
- DO NOT perform performance optimization beyond HealthOmics requirements.

## Procedure

### Phase 1: Container Inventory and Migration

**Objective**: Identify all containers and create ECR migration plan.

**Steps**:
1. Extract all unique container URIs from module files and config files.
2. Generate `container_inventory.csv` with columns: Module/Process name, Original container URI, Container registry, Tool name and version, Target ECR URI.
3. Follow the [ECR Pull Through Cache SOP](./ecr-pull-through-cache.md) to migrate the containers in container_inventory.csv to ECR.
4. Save the container registry map JSON file produced in step 3.

**Done WHEN**:
- `container_inventory.csv` documents all containers.
- All module `main.nf` files use ECR URIs or are covered by the container registry mapping.
- Zero references to external registries remain.
- All Wave containers are cloned to ECR private and URIs are replaced or covered by the container registry map.
- All containers are verified accessible from ECR.

### Phase 2: Resource Declaration Audit

**Objective**: Ensure all processes have CPU and memory declarations.

**HealthOmics Limits**: Min 2 vCPUs / 4 GB memory. Max 96 vCPUs / 768 GB memory.

**Steps**:
1. Scan all module files for resource declarations.
2. Identify processes relying only on labels.
3. Verify all processes in `conf/base.config` have explicit resources.
4. Add HealthOmics-specific resource overrides to Nextflow files or the modules configuration file or the top level `nextflow.config`.

DO NOT create a HealthOmics specific profile. HealthOmics DOES NOT current support profiles.

**Done WHEN**:
- All processes have resources via direct declaration or label.
- All resources meet HealthOmics minimums.

### Phase 3: Reference and Input File Migration

**Objective**: Migrate all reference files and inputs to S3.

You MUST complete the following steps

**Steps**:
1. Identify input files, samplesheets, and hardcoded/configured references:
   - Scan `*.config` files for file references.
   - Extract reference parameters from `nextflow.config`.
   - List files in `assets/` directory.
   - Identify files referenced in sample sheets.
   - Scan for hardcoded paths in helper scripts and process shell scripts.
   - Scan for resources downloaded via http, https, ftp etc.
2. Produce an inventory csv file listing all required file resources   
3. Design S3 bucket structure appropriate for storing these inputs.
4. Create and run a script (`scripts/migrate_references_to_s3.sh`) to retrieve all required files and copy them to the S3 bucket structure.
5. Update sample sheets to point to new S3 URIs then copy those sample sheets to S3.
6. Update any hardcoded paths in the workflow definition or config files with the new S3 URLs.
7. Update the inventory CSV with the S3 URIs of all relocated files

**Done WHEN**:
- Reference inventory CSV lists all files and S3 URIs.
- All reference files accessible from S3.

### Phase 4: Output Path Standardization

**Objective**: Update all output publishing for HealthOmics compatibility, covering both legacy `publishDir` directives and the Nextflow 25.10+ `output { }` block / `publish:` pattern.

**Key Rules**:
- Legacy `publishDir`: ALL task output paths MUST use the absolute path `/mnt/workflow/pubdir/`.
- Nextflow 25.10+ `output { }` block: You MUST use ONLY relative paths in the `path` directive (e.g., `path '.'` or `path 'subdir'`). You MUST NOT use absolute paths in the `output { }` block. HealthOmics manages the output directory.
- Workflow-level content (non-task outputs like provenance reports, DAGs) MUST be written to `/mnt/workflow/output/`.

**Steps**:
1. Identify which output pattern the workflow uses:
   - **Legacy**: `publishDir` directives in processes and config files
   - **Nextflow 25.10+**: Top-level `output { }` block with `publish:` section in the workflow
   - A workflow may use both — audit **ALL** patterns
2. For **legacy `publishDir`** directives:
   - Find all `publishDir` declarations in modules, subworkflows, and configs.
   - Replace `${params.outdir}` with `/mnt/workflow/pubdir/`.
   - IF `params.outdir` is used for both task outputs (`publishDir`) and non-task outputs (workflow-level content), hardcode `publishDir` paths to `/mnt/workflow/pubdir/` so `params.outdir` can be set to `/mnt/workflow/output/` for workflow-level content.
   - Preserve all other `publishDir` options (mode, pattern, saveAs).
3. For **Nextflow 25.10+ `output { }` block**:
   - Remove **ALL** absolute paths from `path` directives — use ONLY relative paths.
   - HealthOmics manages the output directory; the `path` directive specifies a subdirectory within it.
   - If `path` uses a closure, return a relative path (e.g., `path { id, files -> "fastqc/${id}" }`).
   - Preserve other output directives: `index`, `mode`, `enabled`, `overwrite`, `contentType`, `tags`.
   - Verify that `publish:` names in the workflow match `output { }` target names.
4. For **workflow-level content** (provenance reports, pipeline DAGs, etc.):
   - Write to `/mnt/workflow/output/` (e.g., via `params.outdir = "/mnt/workflow/output/"`).
   - HealthOmics exports files from this directory to the `output/` prefix in the run's S3 output location.

**Done WHEN**:
- All legacy `publishDir` paths use `/mnt/workflow/pubdir/` prefix.
- **ALL** Nextflow 25.10+ output block `path` directives use relative paths (no absolute paths).
- Workflow-level content (provenance reports, DAGs) writes to `/mnt/workflow/output/`.
- No references to ${params.outdir} in publishDir directives — all use the literal /mnt/workflow/pubdir/ path or a subdirectory.
- Relative path structure preserved.

### Phase 5: Configuration and Testing

**Objective**: Create HealthOmics-specific configuration and validate.

**Steps**:
1. Create comprehensive `conf/healthomics.config`:
   ```groovy
   params {
       container_registry = '<account>.dkr.ecr.<region>.amazonaws.com/<workflow-name>'
       igenomes_base = 's3://<bucket>/references'
       outdir = '/mnt/workflow/pubdir'
       publish_dir_mode = 'copy'
       max_cpus = 96
       max_memory = 768.GB
       max_time = 168.h
   }

   process {
       conda = null
       container = { "${params.container_registry}/${task.process.tokenize(':')[-1].toLowerCase()}" }
       errorStrategy = { task.exitStatus in [143,137,104,134,139,140] ? 'retry' : 'finish' }
       maxRetries = 3
   }
   ```

2. Create `conf/test/test_healthomics.config` with small test dataset.

3. Update `nextflow.config` with profiles:
   ```groovy
   profiles {
       healthomics { includeConfig 'conf/healthomics.config' }
       test_healthomics { includeConfig 'conf/test/test_healthomics.config' }
   }
   ```

4. Execute test plan:
   - Stage 1: Validate configuration locally.
   - Stage 2: Test on HealthOmics with minimal dataset.
   - Stage 3: Test with full-size dataset.
   - Stage 4: Resource optimization.

**Done WHEN**:
- `conf/healthomics.config` complete with correct syntax.
- Test profile completes successfully on HealthOmics.

## Technical Patterns

### Container Registry (Before/After)
```
Original: quay.io/biocontainers/bwa:0.7.17--h5bf99c6_8
Target:   <account-id>.dkr.ecr.<region>.amazonaws.com/sarek/bwa:0.7.17--h5bf99c6_8
```

### Resource Declaration
```groovy
process EXAMPLE {
    cpus 4
    memory 8.GB
}
```

### PublishDir (Before/After)
```groovy
// Before
publishDir "${params.outdir}/preprocessing/mapped", mode: params.publish_dir_mode
// After
publishDir "/mnt/workflow/pubdir/preprocessing/mapped", mode: params.publish_dir_mode
```

### Nextflow 25.10+ Output Block (New)
```groovy
// Workflow publish section maps names to channels
workflow {
    main:
    output_file = myTask('hello')

    publish:
    results = output_file
}

// Minimal — HealthOmics manages the output directory
output {
    results {
        path '.'
    }
}

// With subdirectories
workflow {
    main:
    fastqc_ch = FASTQC(read_pairs_ch)
    bam_ch = ALIGN(read_pairs_ch)

    publish:
    fastqc_logs = fastqc_ch
    bam_files   = bam_ch
}

output {
    fastqc_logs {
        path 'fastqc'
    }
    bam_files {
        path 'aligned'
    }
}
```

### S3 Reference (Before/After)
```groovy
// Before
params.fasta = "${params.igenomes_base}/Homo_sapiens/GATK/GRCh38/Sequence/WholeGenomeFasta/Homo_sapiens_assembly38.fasta"
// After
params.fasta = "s3://<bucket>/references/Homo_sapiens/GATK/GRCh38/Sequence/WholeGenomeFasta/Homo_sapiens_assembly38.fasta"
```

## Dependencies

- AWS CLI configured with appropriate permissions
- ECR repositories created
- S3 bucket(s) with appropriate permissions
- HealthOmics service access
- Docker/Finch/Podman installed for container operations

## References

- [AWS HealthOmics Documentation](https://docs.aws.amazon.com/omics/)
- [AWS HealthOmics Nextflow Specifics](https://docs.aws.amazon.com/omics/latest/dev/workflow-definition-nextflow.html)
- [nf-core documentation](https://nf-co.re)
- [Nextflow on AWS HealthOmics](https://www.nextflow.io/docs/latest/aws.html#aws-omics)
- [Nextflow Workflow Outputs](https://www.nextflow.io/docs/latest/workflow.html#workflow-outputs)
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)
