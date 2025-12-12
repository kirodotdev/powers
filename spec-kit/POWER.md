---
name: "spec-kit"
displayName: "Spec-Driven Development"
description: "Complete SDD methodology power with 8 workflows: Steering, Specify, Clarify, Plan, Tasks, Implement, Analyze, and Checklist - transforming specifications into executable code"
keywords: ["specification", "SDD", "requirements", "planning", "implementation", "TDD", "code generation", "PRD", "user stories", "acceptance criteria", "steering", "specify", "clarify", "plan", "tasks", "implement", "analyze", "checklist", "spec-kit", "speckit", "功能规格", "需求文档", "技术设计"]
author: "Kiro User"
---

# Spec-Driven Development Power

A comprehensive methodology power that guides you through the complete Spec-Driven Development (SDD) lifecycle - from project steering to implementation.

## Overview

**Spec-Driven Development inverts the traditional development paradigm**: Specifications don't serve code - code serves specifications.

This power embodies the SDD philosophy where:
- Specifications are the primary artifact
- Code is the generated output that serves the specification
- Natural language intent drives development
- Multi-step refinement over one-shot generation

## Core Principles

### The Power Inversion
Traditional development treats specifications as scaffolding - built and discarded once coding begins. SDD eliminates the gap between specification and implementation by making specifications executable.

### Executable Specifications
Specifications must be precise, complete, and unambiguous enough to generate working systems. The specification becomes the source of truth, with code as its expression.

### Steering Governance
Every project operates under steering files - guiding principles split into product, technology, and structure concerns, ensuring consistency, simplicity, and quality.

### Template-Driven Quality
Templates constrain AI behavior toward higher-quality specifications through:
- Preventing premature implementation details
- Forcing explicit uncertainty markers
- Structured thinking through checklists
- Steering compliance through gates

## Workflow Options

### Complete Workflow (8 Commands)

1. **Steering** - Establish project principles (product.md, tech.md, structure.md)
2. **Specify** - Transform feature descriptions into structured specifications
3. **Clarify** - Eliminate ambiguity through targeted questioning
4. **Plan** - Convert specifications to technical architecture
5. **Tasks** - Break plans into executable task lists
6. **Implement** - Execute tasks following TDD approach
7. **Analyze** - Cross-artifact consistency validation
8. **Checklist** - Generate domain-specific quality checklists

### Simplified Workflow (3 Steps)
For quick iterations:
1. **Specify** - Capture requirements
2. **Plan** - Technical approach
3. **Implement** - Execute

## Activation Response

See `00-interaction-protocol.md` for the activation flow. The power first asks for language selection (English/中文), then presents workflow options.

## Methodology Overview

### Phase 1: Foundation (Steering)
Establish guiding principles split into three files:
- **product.md** - Product vision, business constraints
- **tech.md** - Technology stack, development principles
- **structure.md** - Project layout, naming conventions

### Phase 2: Specification (Specify + Clarify)
Transform ideas into executable specifications:
- User stories with priorities
- Acceptance scenarios (Given-When-Then)
- Functional requirements
- Success criteria (measurable, technology-agnostic)

### Phase 3: Planning (Plan + Tasks)
Convert business requirements to technical architecture:
- Technology stack selection
- Data models and API contracts
- Task breakdown with dependencies
- Parallel execution markers

### Phase 4: Execution (Implement)
Execute tasks following the plan:
- Phase-by-phase execution
- TDD approach
- Progress tracking
- Validation checkpoints

### Phase 5: Quality (Analyze + Checklist)
Ensure consistency and completeness:
- Cross-artifact validation
- Coverage analysis
- Domain-specific quality checklists

## Interaction Rules

- **WAIT for user instructions** - Never automatically start workflows
- **CONFIRM scope first** - Understand project context before proceeding
- **One question at a time** - When clarifying, ask single focused questions
- **Ask before proceeding** - Never proceed to next phase without user agreement
- **Mark uncertainties** - Use [NEEDS CLARIFICATION] markers for ambiguous items

## Steering Files

Detailed methodologies for each workflow are available in the steering files:
- `00-interaction-protocol.md` - Interaction guidelines (always loaded)
- `01-steering-workflow.md` - Project principles establishment
- `02-specify-workflow.md` - Feature specification creation
- `03-clarify-workflow.md` - Ambiguity elimination process
- `04-plan-workflow.md` - Technical planning workflow
- `05-tasks-workflow.md` - Task generation process
- `06-implement-workflow.md` - Implementation execution
- `07-analyze-workflow.md` - Consistency analysis
- `08-checklist-workflow.md` - Quality checklist generation

Template files:
- `templates/requirements-template.md` - Feature requirements template
- `templates/clarifications-template.md` - Clarification log template
- `templates/design-template.md` - Technical design template
- `templates/tasks-template.md` - Task list template
- `templates/product-template.md` - Product steering template
- `templates/tech-template.md` - Technology steering template
- `templates/structure-template.md` - Structure steering template

## File Structure

All specification files are stored in `.kiro/specs/`:

```
.kiro/specs/
└── [###-feature-name]/
    ├── requirements.md      # Feature specification (Specify workflow)
    ├── clarifications.md    # Clarification Q&A log (Clarify workflow)
    ├── design.md            # Technical design (Plan workflow)
    ├── research.md          # Technology decisions
    ├── data-model.md        # Entity definitions
    ├── contracts/           # API specifications
    ├── quickstart.md        # Validation scenarios
    ├── tasks.md             # Task list (Tasks workflow)
    └── checklists/          # Quality checklists
```
