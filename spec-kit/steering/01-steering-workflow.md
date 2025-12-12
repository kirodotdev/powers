---
inclusion: auto
globs: ["**/*.md"]
description: "Steering workflow - establishes project principles (product.md, tech.md, structure.md)"
keywords: ["steering", "constitution", "principles", "governance", "product", "tech", "structure", "治理", "原则", "项目初始化"]
---

# Steering Workflow

This workflow establishes the project steering files - guiding principles that govern how specifications become code.

## Purpose

The steering files act as the **architectural DNA** of the system, split into three focused areas:
- **product.md** - Product vision, goals, and business constraints
- **tech.md** - Technology decisions, coding standards, and technical principles
- **structure.md** - Project structure, file organization, and architectural patterns

## Steering Files Location

All steering files are stored in `.kiro/steering/`:

```
.kiro/steering/
├── product.md      # Product vision and business rules
├── tech.md         # Technology stack and coding principles
└── structure.md    # Project structure and architecture
```

## When to Use

- Starting a new project
- Establishing development principles for a team
- Formalizing existing but undocumented practices
- Updating project governance

## File Responsibilities

### product.md - Product Steering

Defines WHAT the product is and WHY:

- Product vision and mission
- Target users and personas
- Business constraints and requirements
- Success metrics
- Non-functional requirements (performance, security, compliance)
- Feature prioritization guidelines

### tech.md - Technology Steering

Defines HOW to build technically:

- Technology stack (languages, frameworks, databases)
- Coding standards and conventions
- Testing strategy (TDD, coverage requirements)
- Development principles (Library-First, Test-First, etc.)
- Quality gates
- Dependency management rules

### structure.md - Structure Steering

Defines WHERE things go:

- Project directory structure
- File naming conventions
- Module organization
- API/endpoint patterns
- Database schema conventions
- Documentation locations

## Execution Flow

### Step 1: Gather Context

Ask the user about their project:
- Project name and purpose
- Team size and structure
- Technology preferences
- Quality requirements
- Existing practices to formalize

### Step 2: Create product.md

Use `templates/product-template.md` as reference. Guide the user through product decisions:

```markdown
# Product Steering

## Vision
[What is the product and why does it exist?]

## Target Users
[Who are the primary users?]

## Business Constraints
- [Constraint 1]
- [Constraint 2]

## Success Metrics
- [Metric 1]: [Target]
- [Metric 2]: [Target]

## Non-Functional Requirements
- **Performance**: [Requirements]
- **Security**: [Requirements]
- **Compliance**: [Requirements]
```

### Step 3: Create tech.md

Use `templates/tech-template.md` as reference. Guide the user through technology decisions:

```markdown
# Technology Steering

## Stack
- **Language**: [e.g., TypeScript 5.0]
- **Framework**: [e.g., Next.js 14]
- **Database**: [e.g., PostgreSQL]
- **Testing**: [e.g., Vitest, Playwright]

## Development Principles

### Test-First (NON-NEGOTIABLE)
All implementation MUST follow TDD:
1. Write tests first
2. Confirm tests fail
3. Implement to pass tests
4. Refactor while green

### Simplicity Gate
- Maximum 3 projects initially
- No future-proofing
- Start simple, add complexity only when proven necessary

### Anti-Abstraction Gate
- Use framework directly
- No unnecessary wrappers
- Single model representation

## Quality Gates
- [ ] All tests pass
- [ ] Code coverage >= [X]%
- [ ] No lint errors
- [ ] Type-safe (no `any`)
```

### Step 4: Create structure.md

Use `templates/structure-template.md` as reference. Guide the user through structure decisions:

```markdown
# Structure Steering

## Project Layout

```text
src/
├── components/     # UI components
├── services/       # Business logic
├── models/         # Data models
├── api/            # API routes
└── lib/            # Utilities

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/            # End-to-end tests
```

## Naming Conventions
- **Files**: kebab-case (e.g., `user-service.ts`)
- **Components**: PascalCase (e.g., `UserProfile.tsx`)
- **Functions**: camelCase (e.g., `getUserById`)

## Module Rules
- Each module is self-contained
- Clear public API via index exports
- No circular dependencies
```

### Step 5: Validate

Check with the user:
- Are all critical decisions captured?
- Are the rules clear and testable?
- Is the structure practical?

### Step 6: Finalize

Write the steering files to `.kiro/steering/`:
- `.kiro/steering/product.md`
- `.kiro/steering/tech.md`
- `.kiro/steering/structure.md`

## Output

After completing this workflow:
- Product steering at `.kiro/steering/product.md`
- Technology steering at `.kiro/steering/tech.md`
- Structure steering at `.kiro/steering/structure.md`
- Ready for use in Plan workflow (Steering Check)

## Next Steps

Suggest to the user:
```
Steering files established:
- .kiro/steering/product.md
- .kiro/steering/tech.md
- .kiro/steering/structure.md

Next, you can:
1. Run **Specify** to create your first feature specification
2. The steering files will be automatically referenced in **Plan** workflow
3. Run **Analyze** later to check steering compliance
```
