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

**Objective**: Identify all containers and make them available to HealthOmics from private ECR.

**Steps**:
1. Extract all unique container URIs from runtime sections:
   - Scan all WDL files for `docker:` and `container:` runtime attributes.
   - Check imported WDL files and sub-workflows.
   - Identify containers in struct/object definitions.
2. Generate `container_inventory.csv` with columns: Task name, Original container URI, Container registry, Tool names and versions, Target ECR URI, Approach (`registry-map` or `uri-replacement`).
3. For each container, CHOOSE one approach — see **Registry Map or URI Replacement** under Technical Patterns:
   - **Registry map (PREFERRED)**: the WDL keeps its original public URIs and HealthOmics redirects them to your pull-through caches. Use this WHERE the image itself is unchanged — same repository, same tag, served from your private ECR instead of the public registry.
   - **URI replacement**: edit the WDL. Use this WHERE the migration changes which repository a task pulls from, because the command block's correctness then depends on which image is used.
4. Stage the containers using the MCP tools — PREFER these over hand-written `docker pull`/`docker push` scripts. Follow the [ECR Pull Through Cache SOP](./ecr-pull-through-cache.md):
   - Call `ListPullThroughCacheRules` first. IF a valid cache already exists for an upstream registry, reuse it — DO NOT create another.
   - Call `CreatePullThroughCacheForHealthOmics` for each remaining upstream registry (`docker-hub`, `quay`, `ecr-public`). This also sets the registry permissions policy and repository creation template that HealthOmics needs.
   - Call `CheckContainerAvailability` with `initiate_pull_through: true` to populate and confirm each image.
   - Call `CloneContainerToECR` for registries NOT supported by pull-through cache.
   - IF using a registry map: call `CreateContainerRegistryMap`, then pass it to `CreateAHOWorkflow` via `container_registry_map` (or `container_registry_map_uri`).
   - IF replacing URIs: update the `docker`/`container` values in the WDL task runtime sections, and PREFER parameterizing the registry base path.

   > **The registry map is a workflow attribute, not a run parameter.** It is supplied at workflow creation, and registration does not appear to validate the definition against it: a workflow whose tasks name public registries registers as `ACTIVE` and is unrunnable. The run then fails partway through with `has an invalid structure. Provide a valid ECR image URI`, naming the task it reached rather than the missing attribute, after earlier tasks have already consumed billed compute. ENSURE the map is attached at creation — a successful `CreateAHOWorkflow` does NOT confirm it.
5. Verify container CONTENTS, not just availability. For each task:
   - List the binaries its `command` block invokes. Take the first bare word of each pipeline stage and of each line, including inside `if`/`for` bodies, and discard shell builtins (`set`, `cd`, `echo`, `if`, `then`, `fi`, `for`, `do`, `done`, `mkdir`, `mv`, `cp`) and `~{}` interpolations.
   - Confirm each one is present in that task's image. `command -v` only checks a single name per invocation, so loop over the tools rather than passing them all at once — otherwise a missing tool after the first silently passes:
     ```bash
     docker run --rm <image> sh -lc '
       for c in bwa samtools bcftools; do
         command -v "$c" >/dev/null || { echo "missing: $c" >&2; exit 1; }
       done'
     ```
   - IF any binary is absent, the task WILL fail at run time — resolve it via step 6 before proceeding.

   > No static check substitutes for this. `CheckContainerAvailability`, `aws ecr describe-images`, `miniwdl check`, and `CreateWorkflow` all pass for an image that exists but lacks a tool the command block pipes to; the task then dies with `command not found`. Single-tool biocontainer images are a frequent source: an image named for one tool often does NOT carry the others in the same pipeline.
6. IF a task needs several tools in one command, use a multi-tool image (for example a `mulled-v2-*` biocontainer). This changes the repository, so treat it as URI replacement per step 3, and record every tool's version in `container_inventory.csv` — they MAY differ from the single-tool images they replace.
7. Create `healthomics.inputs.json` with an ECR registry base path parameter IF container references are parameterized.

**Done WHEN**:
- `container_inventory.csv` documents all containers and records the approach chosen for each.
- All containers are pullable by HealthOmics from private ECR.
- IF using URI replacement: all WDL task runtime sections use ECR URIs, and zero references to external registries remain.
- IF using a registry map: every external registry still referenced in the WDL has a mapping entry, and the map is passed to `CreateAHOWorkflow`.
- For every task, each command invoked in its `command` block is confirmed present in that task's image using the check in step 5.

### Phase 2: Runtime Attribute Audit

**Objective**: Ensure all tasks have CPU and memory runtime declarations.

**HealthOmics Limits**: Min 2 vCPUs / 4 GiB memory. Max 96 vCPUs / 768 GiB memory.

**Steps**:
1. Scan all WDL files for runtime sections.
2. Identify tasks missing `cpu` or `memory` attributes. Note any `disks` attributes as well, but DO NOT treat a missing `disks` as a defect — see [Silent Incompatibilities](#silent-incompatibilities) for what HealthOmics does with it.
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
- All resources meet HealthOmics minimums (≥2 vCPU, ≥4 GiB).

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
4. Choose the engine. `CreateAHOWorkflow` accepts `WDL` or `WDL_LENIENT`:
   - `WDL_LENIENT` "allows for some WDL directives that don't strictly meet the WDL spec and can be useful when migrating legacy workflows designed to run on Cromwell." PREFER it for Cromwell-origin definitions that have not been brought fully to spec; use `WDL` once the definition is spec-compliant.
   - Neither engine is a substitute for the version upgrade in step 2. A definition with no `version` declaration registers `ACTIVE` under BOTH engines, with `MissingVersion, document should declare WDL version; draft-2 assumed` in `statusMessage` — creation does not reject it, so ENSURE the version is declared rather than relying on the engine to object.
   - DO NOT treat the lenient engine as a correctness net. Its leniency applies to registration-time syntax, NOT to runtime type coercion: a lossy conversion such as a `String` `"3.7"` supplied to an `Int` registers as `ACTIVE` under BOTH engines and fails identically once the task runs. Choosing `WDL_LENIENT` does not buy looser typing at run time.
5. Lint:
   - Call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to verify syntax.
   - For large workflows, use `miniwdl check` if available locally.
   - Read the `Return code:` in the tool's `raw_output` to judge the result. A parse failure can still be reported with `"status": "success"` at the top level, so a check that reads only `status` passes broken files.
   - Resolve all issues.

**Done WHEN**:
- All WDL files declare version 1.0 or higher.
- No draft-2 syntax remains.
- Syntax validation passes for all WDL files, confirmed via `Return code:` and not the top-level `status` alone.
- All imports resolve correctly.
- The engine (`WDL` or `WDL_LENIENT`) is chosen deliberately and noted in the workflow's `README.md` (or `.healthomics/config.toml`), so later versions register with the same one.

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
4. Create `healthomics.inputs.json` with S3 URIs for all File inputs. Keys MUST be bare parameter names, NOT namespaced with the workflow name — see [Workflow Development SOP](./workflow-development.md). Cromwell inputs files namespace every key (`WorkflowName.input`), so ENSURE the namespace is stripped when porting one.
   - DO NOT rely on `StartRun` to reject a namespaced key. IF the workflow declares a default for that parameter, the key MAY be accepted silently and **the default runs instead of the value you supplied** — the run reports COMPLETED with results that do not reflect the submitted inputs. A namespaced key fails loudly only where the bare parameter is required.
5. Update any hardcoded paths in command sections to use input variables.

**Done WHEN**:
- Reference inventory CSV lists all files and sizes.
- All reference files accessible from S3.
- `healthomics.inputs.json` uses S3 URIs exclusively.
- No key in `healthomics.inputs.json` is namespaced with the workflow name.
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

### Registry Map or URI Replacement

Decide per container by asking whether the migration changes the image's TRANSPORT or its IDENTITY.

| The change is | Same repository and tag, served from private ECR | A different repository (different tool set or versions) |
|---|---|---|
| Approach | Registry map | Edit the WDL |
| WDL | Unmodified — keeps the public URI | `docker`/`container` value replaced |
| Why | The image is identical, so the redirect hides nothing | The command block's correctness now depends on which image is used |

DO NOT hide an identity change inside a registry map. A task whose runtime says `bwa` while the map redirects it to a different repository executes something other than what the WDL says, and the next reader has no way to see it from the workflow definition.

PREFER pinning by digest (`repository@sha256:...`) over a mutable tag on either path. A tag can be reassigned upstream, in which case the same WDL resolves to a different image on a later run.

### Container Runtime (Before/After)

Both paths add the required `cpu` and `memory` attributes. They differ only in whether the image reference changes.

```wdl
# Before
runtime {
    docker: "quay.io/biocontainers/bwa:0.7.17--h5bf99c6_8"
}

# After — registry map path: the image reference is UNCHANGED.
# The map is passed to CreateAHOWorkflow, which redirects quay.io to your pull-through cache.
runtime {
    docker: "quay.io/biocontainers/bwa:0.7.17--h5bf99c6_8"
    cpu: 4
    memory: "8 GB"
}

# After — URI replacement path, for when the repository itself changes.
runtime {
    docker: "<account-id>.dkr.ecr.<region>.amazonaws.com/workflow-name/bwa:0.7.17--h5bf99c6_8"
    cpu: 4
    memory: "8 GiB"
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

The path MUST become an S3 URI, and the workflow namespace MUST be removed from the key.

```json
// Before (Cromwell)
{ "WorkflowName.reference_fasta": "/path/to/reference.fasta" }

// After (HealthOmics)
{ "reference_fasta": "s3://bucket/references/Homo_sapiens/GATK/GRCh38/Sequence/reference.fasta" }
```

## Silent Incompatibilities

These are Cromwell habits that survive every gate in this SOP — none is caught by lint or by registration. Most produce no error at all: the run reaches COMPLETED and the result means something other than what the definition intended, either because a directive was silently ignored or because it means something different here than it did under Cromwell. AUDIT for each explicitly.

### Outputs written outside the task working directory

```wdl
# Before — the task exits 0 and the data is gone
samtools sort -o /data/out.bam in.bam
# After — write into the working directory and collect it in the output block
samtools sort -o out.bam in.bam
```

Output collection is relative to the task working directory, so a file written to an absolute path elsewhere is not collected while the task still exits 0 — data loss, not a failure. This is distinct from Phase 5, which covers outputs that were never declared; here the output IS declared and the task wrote it somewhere that is not collected.

DETECT by scanning command blocks for absolute paths given to output flags (`-o`, `-O`, `--output`, `>`) and to redirections. Scratch writes under `/tmp` are fine — the concern is anything the `output {}` block expects to find.

### `String` used to pass a directory of files

HealthOmics localizes values declared as file types — `File`, `Directory`, `Array[File]`, and `File` fields inside structs. A `String` is opaque text, so nothing is staged: the service has no way to know it names data.

```wdl
String ref_dir            # nothing is localized
# command: ~{ref_dir}/genome.fasta.bwt
```

This is a common Cromwell-ism, where a shared filesystem made it work. The error surfaces on a file the author never mentioned (a `.bwt` index, for example), several lines away from the declaration that caused it. DETECT by finding every `String` input concatenated with `/` in a command block, and declare each required file as a `File` input — including index companions.

### `preemptible` carried over from Cromwell

In HealthOmics `preemptible` has nothing to do with spot or preemptible capacity. It opts out of automatic retries for service errors:

> HealthOmics supports up to two retries for a task that failed because of service errors (5XX HTTP status codes). You can configure the maximum number of retries (1 or 2) and you can opt out of retries for service errors. By default, HealthOmics attempts a maximum of two retries. The following example sets `preemptible` to opt out of retries for service errors: `{ preemptible: 0 }`

There is no spot or discounted-capacity concept attached to this directive in HealthOmics. `0` opts out of 5XX retries; `1` and `2` set the retry limit, and `2` is already the default — so a Cromwell `preemptible: 2`, which asked for two attempts on preemptible VMs, becomes a no-op that still reads as a cost control. The documented values are `0`, `1`, and `2`; behavior for anything higher is not documented.

REMOVE the directive unless the intent really is to control 5XX retry behavior, and do NOT read an inherited non-zero value as a request for cheaper compute.

### Thread counts not tied to the CPU request

```wdl
# Before — these drift apart
Int threads = 16
runtime { cpu: 4 }
# After — one value, referenced twice
Int threads = cpu_count
runtime { cpu: cpu_count }
```

A literal in a flag (`-t 16`) is visible on review, but legacy code more often declares `Int threads = 16` and writes `-t ~{threads}`, putting the number nowhere near the flag. Oversubscribing degrades throughput and undersubscribing wastes the reservation; neither is an error.

### Unbounded `scatter`

Cromwell deployments were bounded by a cluster queue. HealthOmics has no equivalent, so a scatter over an input list expands as wide as the list. Create a run group to bound it:

```bash
aws omics create-run-group --name my-guard \
    --max-cpus 96 \
    --max-runs 4 \
    --max-duration 2880   # minutes, not hours — 2880 = 48h
```

Size `--max-duration` to the workflow, not to the example. A run that exceeds it fails automatically.

### `disks` read as a size, not as a disk layout

A Cromwell `disks: "local-disk 700 SSD"` describes a volume. HealthOmics reads only the number:

> HealthOmics accepts all standard WDL 1.1 `disks` forms. The mount path and disk type specifier (`SSD`, `HDD`) are ignored — only the numeric size is extracted. If multiple entries are declared, the sizes are summed into a single `/tmp` allocation.

So a design that split scratch across several named volumes does not survive the migration, and no error says so. Whether the size is used at all depends on the run:

- Default (`scratchStorageMode` omitted, which resolves to `SHARED`): `disks` is ignored for CPU tasks, no local storage volume is provisioned, and `/tmp` is backed by the shared filesystem. GPU tasks are unaffected — they always use local NVMe.
- `scratchStorageMode=LOCAL`: `disks` is honored as a hint for per-task ephemeral `/tmp`, rounded up to the next 16 GiB. It does NOT influence instance type, which is selected from `cpu`, `memory`, and `acceleratorType`.

DO NOT read a `disks` value in a migrated definition as evidence that per-task scratch is configured. Confirm the run's `scratchStorageMode` first.

### `maxRetries` without findutils in the image

`maxRetries` retries a task that ran out of memory, doubling memory each attempt:

> HealthOmics supports retries for a task that failed because it ran out of memory (container exit code 137, 4XX HTTP status code). HealthOmics doubles the amount of memory for each retry attempt. By default, HealthOmics doesn't retry for this type of failure.

It has a container dependency that is easy to miss:

> Task retry for out of memory requires GNU findutils 4.2.3+. The default HealthOmics image container includes this package. If you specify a custom image in your WDL definition, make sure that the image includes GNU findutils 4.2.3+.

So a task declaring `maxRetries` on a custom image may not retry at all, and that outcome is indistinguishable from "retried and failed again". CONFIRM the package before relying on the directive:

```bash
docker run --rm <image> find --version
```

### `GB` where the task was tuned in `GiB`

`memory: "8 GB"` and `memory: "8 GiB"` both parse and both run. They differ by 7.4% — about 600 MB at 8, about 4.7 GB at 64 — and for a task tuned to its working-set limit that is the difference between completing and an OOM kill (exit 137).

PREFER `GiB` when porting a task that was tuned on-premises: the tool's own memory reporting almost certainly meant `GiB`. ENSURE a single unit is used across every task in the workflow — a mixed set of examples teaches the next reader to mix them.

A bare `memory: 8` is a separate problem — Cromwell read it as GB, the WDL spec expects a string with a unit — and it belongs to the Phase 2 audit, not here.

### Absolute and remote imports

HealthOmics resolves WDL imports from the workflow zip package. An `import "/home/shared/wdl/tasks/align.wdl"` resolves on the origin cluster but that path is not in the package, and an `http(s)://` import is not fetched. Rewrite both as relative paths within the bundle.

This one does fail rather than pass silently, but it fails at a distance from its cause: registration reports `FAILED` on a missing dependency, and the import validation in Phase 3 step 3 checks versions, aliasing, and cycles — not whether each import path exists in the package. On-prem definitions almost always carry at least one absolute import.

## WDL-Specific Considerations

- **Scatter-Gather**: Ensure scattered tasks have appropriate resources. Verify `Array[File]` outputs are properly collected.
- **Sub-Workflows**: Ensure all imported WDL files are migrated. Verify sub-workflow outputs are properly passed.
- **Optional Inputs**: Handle `File?` inputs gracefully. Use `select_first()` or `defined()` appropriately.
- **Command Section**: Use `~{}` for variable interpolation (WDL 1.0+). Avoid hardcoded paths. Use `sep()` for array joining.
- **Defects that pass every gate**: see [Silent Incompatibilities](#silent-incompatibilities) above for cases that lint clean, register `ACTIVE`, and reach COMPLETED with a result that differs from what the definition intended.

## Dependencies

- AWS CLI configured with appropriate permissions
- ECR repositories created
- S3 bucket(s) created with appropriate permissions
- HealthOmics service access
- HealthOmics MCP server
- Docker/Finch/Podman installed for container operations, including verifying image contents (Phase 1)

## References

- [AWS HealthOmics Documentation](https://docs.aws.amazon.com/omics/)
- [WDL 1.0 Specification](https://github.com/openwdl/wdl/blob/main/versions/1.0/SPEC.md)
- [WDL 1.1 Specification](https://github.com/openwdl/wdl/blob/main/versions/1.1/SPEC.md)
- [WDL on AWS HealthOmics](https://docs.aws.amazon.com/omics/latest/dev/workflows.html)
- [WDL support in HealthOmics](https://docs.aws.amazon.com/omics/latest/dev/workflow-languages-wdl.html) — per-attribute behavior for `preemptible`, `maxRetries`, `disks` forms, `returnCodes`, `omicsTimeout`
- [Ephemeral storage for HealthOmics runs](https://docs.aws.amazon.com/omics/latest/dev/workflows-ephemeral-storage.html) — `scratchStorageMode` and when `disks` is honored
- [Compute and memory requirements for HealthOmics tasks](https://docs.aws.amazon.com/omics/latest/dev/task-resources.html) — states that per-task storage specifications are ignored, which holds for the default `SHARED` mode; see the ephemeral storage page for `LOCAL`
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)
