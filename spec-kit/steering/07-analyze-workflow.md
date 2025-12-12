---
inclusion: auto
globs: ["**/*.md"]
description: "Analyze workflow - cross-artifact consistency validation"
keywords: ["analyze", "analysis", "consistency", "validation", "review", "分析", "一致性", "验证"]
---

# Analyze Workflow

This workflow performs cross-artifact consistency and quality analysis across spec, plan, and tasks.

## Purpose

Identify inconsistencies, duplications, ambiguities, and underspecified items before implementation:
- **Non-destructive**: Read-only analysis
- **Steering-aware**: Flag principle violations
- **Coverage-focused**: Ensure all requirements have tasks

## When to Use

- After Tasks workflow, before Implement
- When artifacts seem inconsistent
- Before major reviews or milestones
- To validate specification quality

## Prerequisites

- **Required**: `requirements.md` - Feature specification
- **Required**: `design.md` - Implementation plan
- **Required**: `tasks.md` - Task list
- **Reference**: Steering files in `.kiro/steering/`:
  - `product.md` - Product vision and constraints
  - `tech.md` - Technology principles
  - `structure.md` - Project structure rules

## Operating Constraints

**STRICTLY READ-ONLY**: Do NOT modify any files. Output analysis report only.

**Steering Authority**: Steering files are authoritative. Steering conflicts are automatically CRITICAL.

## Execution Flow

### Step 1: Load Artifacts

Load from feature directory (`.kiro/specs/[###-feature-name]/`):

**From requirements.md**:
- Overview/Context
- Functional Requirements
- Non-Functional Requirements
- User Stories
- Edge Cases

**From design.md**:
- Architecture/stack choices
- Data Model references
- Phases
- Technical constraints

**From tasks.md**:
- Task IDs and descriptions
- Phase grouping
- Parallel markers [P]
- Referenced file paths

**From steering files** (`.kiro/steering/`):
- `product.md`: Product vision, business constraints
- `tech.md`: Development principles, quality gates
- `structure.md`: Project layout, naming conventions

### Step 2: Build Semantic Models

Create internal representations:

1. **Requirements inventory**: Each requirement with stable key
   - `user-can-upload-file` from "User can upload file"

2. **User story inventory**: Actions with acceptance criteria

3. **Task coverage mapping**: Map tasks to requirements/stories

4. **Steering rule set**: Extracted principles from tech.md, product.md, structure.md

### Step 3: Run Detection Passes

Limit to 50 findings total. Focus on high-signal issues.

#### A. Duplication Detection
- Near-duplicate requirements
- Mark lower-quality phrasing for consolidation

#### B. Ambiguity Detection
- Vague adjectives without metrics: fast, scalable, secure, intuitive, robust
- Unresolved placeholders: TODO, TKTK, ???, `<placeholder>`

#### C. Underspecification
- Requirements with verbs but missing object or outcome
- User stories missing acceptance criteria
- Tasks referencing undefined components

#### D. Steering Alignment
- Requirements conflicting with MUST principles
- Missing mandated sections or quality gates

#### E. Coverage Gaps
- Requirements with zero associated tasks
- Tasks with no mapped requirement
- Non-functional requirements not in tasks

#### F. Inconsistency
- Terminology drift (same concept, different names)
- Data entities in plan but not spec (or vice versa)
- Task ordering contradictions
- Conflicting requirements

### Step 4: Assign Severity

| Severity | Criteria |
|----------|----------|
| CRITICAL | Violates steering MUST, missing core artifact, requirement with zero coverage blocking baseline |
| HIGH | Duplicate/conflicting requirement, ambiguous security/performance, untestable acceptance |
| MEDIUM | Terminology drift, missing non-functional coverage, underspecified edge case |
| LOW | Style/wording improvements, minor redundancy |

### Step 5: Generate Report

Output Markdown report (do NOT write to file):

```markdown
# Specification Analysis Report

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D1 | Duplication | HIGH | requirements.md:L120 | Two similar requirements | Merge, keep clearer version |
| A1 | Ambiguity | MEDIUM | requirements.md:L45 | "fast" undefined | Add specific metric |
| C1 | Steering | CRITICAL | design.md:L30 | 4 projects violates tech.md | Justify or simplify |
| G1 | Coverage | HIGH | requirements.md FR-005 | No task for requirement | Add task to tasks.md |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| user-can-login | Yes | T003, T004 | |
| user-can-upload | No | - | CRITICAL: Missing coverage |
| admin-can-delete | Yes | T012 | |

## Steering Alignment Issues

| Principle | Status | Issue |
|-----------|--------|-------|
| Simplicity (Art VII) | FAIL | 4 projects without justification |
| Test-First (Art III) | PASS | Tests before implementation |

## Unmapped Tasks

| Task ID | Description | Issue |
|---------|-------------|-------|
| T015 | Add caching layer | No requirement source |

## Metrics

- Total Requirements: [N]
- Total Tasks: [N]
- Coverage %: [N]% (requirements with >=1 task)
- Ambiguity Count: [N]
- Duplication Count: [N]
- Critical Issues: [N]
```

### Step 6: Provide Next Actions

```markdown
## Next Actions

### Critical Issues (must resolve)
1. [Issue] - [Recommendation]
2. [Issue] - [Recommendation]

### Recommended Fixes
1. [Issue] - [Recommendation]

### Suggested Commands
- Run `/speckit.specify` with refinement to address spec gaps
- Run `/speckit.plan` to adjust architecture
- Manually edit tasks.md to add coverage for [requirement]

### Proceed to Implement?
[Recommendation based on analysis]
```

### Step 7: Offer Remediation

Ask user:
```
Would you like me to suggest concrete remediation edits for the top [N] issues?

Note: I will NOT apply them automatically. You must approve each change.
```

## Analysis Guidelines

- **NEVER modify files** (read-only)
- **NEVER hallucinate** missing sections
- **Prioritize steering violations** (always CRITICAL)
- **Use examples** over exhaustive rules
- **Report zero issues gracefully** with coverage statistics

## Severity Quick Reference

**CRITICAL** (must fix):
- Steering MUST violation
- Missing core spec/plan/tasks
- Requirement with zero coverage blocking baseline

**HIGH** (should fix):
- Duplicate or conflicting requirement
- Ambiguous security/performance
- Untestable acceptance criterion

**MEDIUM** (nice to fix):
- Terminology drift
- Missing non-functional coverage
- Underspecified edge case

**LOW** (optional):
- Style/wording improvements
- Minor redundancy

## Output

After completing this workflow:
- Analysis report displayed
- No files modified
- Remediation offered (not applied)

## Next Steps

Suggest to the user:
```
Analysis complete.

Next, you can:
1. Address CRITICAL issues before implementation
2. Run **Implement** if no blockers
3. Request remediation suggestions for top issues
4. Re-run analysis after fixes
```
