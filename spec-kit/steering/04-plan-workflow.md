---
inclusion: auto
globs: ["**/*.md"]
description: "Plan workflow - converts requirements into technical architecture and design"
keywords: ["plan", "design", "architecture", "technical", "计划", "设计", "架构", "技术方案"]
---

# Plan Workflow

This workflow converts business requirements into technical architecture and implementation plans.

## Purpose

Transform feature specifications into detailed technical plans that:
- Map requirements to technical decisions
- Document technology choices with rationale
- Create data models and API contracts
- Ensure steering compliance

## When to Use

- Feature specification is complete and clarified
- Ready to start technical planning
- Need to document architecture decisions

## Prerequisites

- Feature specification exists (`requirements.md`)
- Clarification complete (no critical `[NEEDS CLARIFICATION]` markers)
- Project steering files exist (optional but recommended)

## Execution Flow

### Step 1: Load Context

Read required documents:
- Feature specification (`requirements.md`)
- Steering files (if exist):
  - `.kiro/steering/product.md` - Product vision and constraints
  - `.kiro/steering/tech.md` - Technology stack and principles
  - `.kiro/steering/structure.md` - Project structure patterns

### Step 2: Create Design File

Create `design.md` in the feature directory using `templates/design-template.md` as reference:
```
.kiro/specs/[###-feature-name]/
├── requirements.md
└── design.md    # Create this
```

### Step 3: Gather Technical Context

If `.kiro/steering/tech.md` exists, use it as reference. Otherwise, determine or ask about:
- **Language/Version**: e.g., Python 3.11, TypeScript 5.0
- **Primary Dependencies**: e.g., FastAPI, React, Express
- **Storage**: e.g., PostgreSQL, MongoDB, files
- **Testing**: e.g., pytest, Jest, Vitest
- **Target Platform**: e.g., Linux server, iOS, Web
- **Project Type**: single/web/mobile
- **Performance Goals**: domain-specific targets
- **Constraints**: specific limitations
- **Scale/Scope**: expected usage levels

Mark any unknowns as `NEEDS CLARIFICATION` for research phase.

### Step 4: Steering Check

If steering files exist, evaluate compliance:

```markdown
## Steering Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Product Alignment (from product.md)
- [ ] Aligns with product vision?
- [ ] Respects business constraints?
- [ ] Meets non-functional requirements?

### Tech Compliance (from tech.md)
- [ ] Uses approved technology stack?
- [ ] Follows development principles?
- [ ] Passes quality gates?

### Structure Compliance (from structure.md)
- [ ] Follows project layout?
- [ ] Uses correct naming conventions?
- [ ] Respects module organization rules?
```

**ERROR if violations not justified.**

### Step 4: Phase 0 - Research

For each unknown in Technical Context:

1. **Extract unknowns**: Each `NEEDS CLARIFICATION` -> research task
2. **Research dependencies**: Best practices for chosen technologies
3. **Evaluate patterns**: Integration approaches

**Output**: `research.md` with format:
```markdown
# Research: [FEATURE]

## Decision 1: [Topic]
- **Decision**: [What was chosen]
- **Rationale**: [Why chosen]
- **Alternatives**: [What else evaluated]

## Decision 2: [Topic]
...
```

### Step 5: Phase 1 - Design

**Prerequisites**: `research.md` complete

#### Generate Data Model

Extract entities from feature spec:
```markdown
# Data Model: [FEATURE]

## Entity: [Name]
- **Purpose**: [What it represents]
- **Fields**:
  - `id`: unique identifier
  - `field1`: [type] - [description]
  - `field2`: [type] - [description]
- **Relationships**: [Links to other entities]
- **Validation**: [Rules from requirements]
- **State Transitions**: [If applicable]

## Entity: [Name]
...
```

#### Generate API Contracts

For each user action -> endpoint:
```markdown
# API Contracts: [FEATURE]

## POST /api/[resource]
- **Purpose**: [From user story]
- **Request**: [Schema]
- **Response**: [Schema]
- **Errors**: [Error cases]
```

Or use OpenAPI/GraphQL schema in `/contracts/` directory.

#### Generate Quickstart

Key validation scenarios:
```markdown
# Quickstart: [FEATURE]

## Scenario 1: [Happy Path]
1. [Step]
2. [Step]
3. [Expected Result]

## Scenario 2: [Edge Case]
...
```

### Step 6: Create Implementation Plan

Generate the plan document:

```markdown
# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

## Summary

[Primary requirement + technical approach]

## Technical Context

**Language/Version**: [e.g., Python 3.11]
**Primary Dependencies**: [e.g., FastAPI, SQLAlchemy]
**Storage**: [e.g., PostgreSQL]
**Testing**: [e.g., pytest]
**Target Platform**: [e.g., Linux server]
**Project Type**: [single/web/mobile]
**Performance Goals**: [specific targets]
**Constraints**: [limitations]
**Scale/Scope**: [expected usage]

## Steering Check

[Gates and compliance status]

## Project Structure

### Documentation (this feature)
```text
.kiro/specs/[###-feature]/
├── design.md            # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Tasks workflow output
```

### Source Code
```text
src/
├── models/
├── services/
├── cli/ or api/
└── lib/
tests/
├── contract/
├── integration/
└── unit/
```

## Complexity Tracking

> Fill ONLY if Steering Check has violations to justify

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [violation] | [reason] | [why simpler won't work] |
```

### Step 7: Re-evaluate Steering

After design phase, re-check steering compliance:
- Have new decisions violated any principles?
- Document justifications if needed

### Step 8: Report Completion

```markdown
## Plan Complete

**Branch**: [branch-name]
**Plan**: [path to design.md]

### Generated Artifacts
- design.md - Implementation plan
- research.md - Technology decisions
- data-model.md - Entity definitions
- contracts/ - API specifications
- quickstart.md - Validation scenarios

### Steering Status
[Pass / Violations justified]

### Ready for Tasks Workflow
```

## Output

After completing this workflow:
- `design.md` - Implementation plan
- `research.md` - Research decisions
- `data-model.md` - Data model
- `contracts/` - API contracts
- `quickstart.md` - Validation scenarios

## Next Steps

Suggest to the user:
```
Plan created at .kiro/specs/[###-feature-name]/design.md

Next, you can:
1. Run **Tasks** to generate executable task list
2. Review plan artifacts before proceeding
3. Run **Checklist** to create quality checklists
```
