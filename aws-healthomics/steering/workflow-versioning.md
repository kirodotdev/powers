# SOP: Workflow Versioning

## Purpose

This SOP defines how you, the agent, handle modifications to existing HealthOmics workflows. You MUST use `CreateAHOWorkflowVersion` to create a new version rather than creating an entirely new workflow. This preserves workflow history, maintains consistent workflow IDs, and follows HealthOmics best practices.

## Trigger Conditions

Use `CreateAHOWorkflowVersion` WHEN:
- Fixing bugs in an existing workflow
- Adding new features or tasks to a workflow
- Updating container images or versions
- Modifying resource allocations (CPU, memory)
- Changing workflow parameters or outputs
- Optimizing workflow performance after analyzing run metrics
- Applying fixes after diagnosing run failures

Use `CreateAHOWorkflow` ONLY WHEN:
- Creating a brand new workflow that doesn't exist yet
- The workflow represents fundamentally different functionality
- The customer explicitly requests a new workflow ID

## Procedure

### Step 1: Identify the Existing Workflow

1. Call `ListAHOWorkflows` to find the workflow.
2. Call `GetAHOWorkflow` to retrieve current workflow details including the workflow ID.

### Step 2: Make Modifications Locally

1. Edit the workflow definition files as needed.
2. Call `LintAHOWorkflowDefinition` or `LintAHOWorkflowBundle` to validate changes.
3. DO NOT proceed if linting errors exist — resolve them first.

### Step 3: Package the Updated Workflow

- Call `PackageAHOWorkflow` to create a zip package of the workflow.

### Step 4: Create a New Version

1. Call `CreateAHOWorkflowVersion` with the existing workflow ID.
2. Apply semantic versioning:
   - MAJOR (e.g., `1.0.0` → `2.0.0`): Breaking changes to inputs/outputs
   - MINOR (e.g., `1.0.0` → `1.1.0`): New features, backward compatible
   - PATCH (e.g., `1.0.0` → `1.0.1`): Bug fixes, performance improvements
3. Include a meaningful description of changes.

### Step 5: Verify the New Version

1. Call `GetAHOWorkflow` to confirm the version was created successfully.
2. Confirm status is `ACTIVE`.

## Common Scenarios

### After Diagnosing a Run Failure
1. `DiagnoseAHORunFailure` identifies the issue.
2. Fix the workflow definition.
3. Call `CreateAHOWorkflowVersion` with the fix.
4. Re-run using the updated workflow version.

### After Performance Optimization
1. `AnalyzeAHORunPerformance` suggests improvements.
2. Apply recommended resource adjustments.
3. Call `CreateAHOWorkflowVersion` with the optimizations.
4. Run the optimized version to validate improvements.

### Updating Container Images
1. Update container references in task definitions.
2. Test locally if possible.
3. Call `CreateAHOWorkflowVersion` with the updated containers.

## Benefits of Versioning

- Audit trail: complete history of workflow changes
- Rollback capability: easy to revert to previous versions
- Consistent integration: downstream systems reference the same workflow ID
- Cost tracking: all runs grouped under a single workflow for billing
- Compliance: maintains lineage for regulatory requirements in genomics workflows
