---
inclusion: auto
globs: ["**/*.md"]
description: "Implement workflow - executes tasks with TDD approach"
keywords: ["implement", "implementation", "execute", "coding", "TDD", "实现", "编码", "开发"]
---

# Implement Workflow

This workflow executes the implementation plan by processing tasks from `tasks.md`.

## Purpose

Execute tasks systematically to build the feature:
- Phase-by-phase execution
- TDD approach when tests are included
- Progress tracking with checkmarks
- Validation at each checkpoint

## When to Use

- Tasks have been generated
- Ready to start coding
- Want AI-assisted implementation

## Prerequisites

- **Required**: `tasks.md` - Complete task list
- **Required**: `design.md` - Tech stack and architecture
- **Optional**: `data-model.md` - Entity definitions
- **Optional**: `contracts/` - API specifications
- **Optional**: `research.md` - Technical decisions
- **Optional**: `quickstart.md` - Validation scenarios
- **Optional**: `checklists/` - Quality checklists

## Execution Flow

### Step 1: Check Checklists (if exist)

If `checklists/` directory exists, scan all checklist files:

```markdown
| Checklist | Total | Completed | Incomplete | Status |
|-----------|-------|-----------|------------|--------|
| ux.md     | 12    | 12        | 0          | PASS   |
| test.md   | 8     | 5         | 3          | FAIL   |
| security.md | 6   | 6         | 0          | PASS   |
```

**If any checklist incomplete**:
- Display the table
- Ask: "Some checklists are incomplete. Proceed anyway? (yes/no)"
- Wait for user response

**If all complete**: Proceed automatically

### Step 2: Load Implementation Context

Read required documents:
- `tasks.md` - Task list and execution plan
- `design.md` - Tech stack, architecture, file structure

Read if available:
- `data-model.md` - Entities and relationships
- `contracts/` - API specifications
- `research.md` - Technical decisions
- `quickstart.md` - Integration scenarios

### Step 3: Project Setup Verification

Create/verify ignore files based on detected technologies:

**Detection Logic**:
- Git repo? -> `.gitignore`
- Dockerfile exists? -> `.dockerignore`
- ESLint config? -> `.eslintignore` or config ignores
- Prettier config? -> `.prettierignore`
- Terraform files? -> `.terraformignore`

**Common Patterns by Technology**:

| Technology | Patterns |
|------------|----------|
| Node.js | `node_modules/`, `dist/`, `build/`, `*.log`, `.env*` |
| Python | `__pycache__/`, `*.pyc`, `.venv/`, `dist/` |
| Java | `target/`, `*.class`, `*.jar`, `.gradle/`, `build/` |
| Go | `*.exe`, `*.test`, `vendor/`, `*.out` |
| Rust | `target/`, `debug/`, `release/`, `*.rs.bk` |

**Universal**: `.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/`

### Step 4: Parse Task Structure

Extract from `tasks.md`:
- **Task phases**: Setup, Foundational, User Stories, Polish
- **Task dependencies**: Sequential vs parallel
- **Task details**: ID, description, file paths, [P] markers
- **Execution flow**: Order and dependencies

### Step 5: Execute Tasks

#### Execution Rules

1. **Phase-by-phase**: Complete each phase before moving to next
2. **Respect dependencies**: Run sequential tasks in order
3. **Parallel execution**: Tasks with [P] can run together if different files
4. **TDD approach**: If tests exist, run test tasks before implementation
5. **File coordination**: Tasks affecting same files run sequentially
6. **Validation checkpoints**: Verify phase completion before proceeding

#### Execution Order

1. **Setup first**: Project structure, dependencies, configuration
2. **Tests before code** (if TDD): Write tests for contracts/entities
3. **Core development**: Models, services, CLI/endpoints
4. **Integration**: Database, middleware, external services
5. **Polish**: Unit tests, optimization, documentation

### Step 6: Progress Tracking

After completing each task:
1. Mark task as complete in `tasks.md`: `- [X] T001 ...`
2. Report progress to user
3. If task fails: halt and report error
4. For parallel tasks: continue with successful ones, report failures

### Step 7: Error Handling

**Non-parallel task fails**:
- Halt execution
- Report clear error with context
- Suggest debugging steps
- Ask how to proceed

**Parallel task fails**:
- Continue with other parallel tasks
- Report failure
- Allow user to decide: fix and retry, skip, or stop

### Step 8: Validation Checkpoints

At each phase completion:
- Verify all phase tasks completed
- Run any phase-specific tests
- Check against quickstart scenarios
- Report status before proceeding

### Step 9: Completion Validation

After all tasks:
- [ ] All required tasks completed
- [ ] Implemented features match specification
- [ ] Tests pass (if applicable)
- [ ] Implementation follows technical plan
- [ ] All tasks marked [X] in tasks.md

### Step 10: Report Completion

```markdown
## Implementation Complete

### Summary
- Total tasks: [N]
- Completed: [N]
- Failed: [N]
- Skipped: [N]

### Phase Status
| Phase | Tasks | Status |
|-------|-------|--------|
| Setup | N/N | Complete |
| Foundational | N/N | Complete |
| US1 | N/N | Complete |
| US2 | N/N | Complete |
| Polish | N/N | Complete |

### Validation
- Tests passing: Yes/No
- Quickstart scenarios: Verified/Not verified

### Files Created/Modified
[List of files]

### Next Steps
[Recommendations]
```

## TDD Approach Details

When tests are included:

1. **Red Phase**: Write failing tests
   - Contract tests first
   - Then integration tests
   - Then unit tests

2. **Green Phase**: Write minimal code to pass
   - Implement just enough to pass tests
   - No extra features

3. **Refactor Phase**: Clean up while green
   - Improve code quality
   - Keep tests passing

## Output

After completing this workflow:
- All tasks executed and marked complete in `tasks.md`
- Source code created per implementation plan
- Tests passing (if applicable)

## Next Steps

Suggest to the user:
```
Implementation complete.

Next, you can:
1. Run **Analyze** to verify consistency
2. Run tests manually to confirm
3. Review generated code
4. Create PR for review
```
