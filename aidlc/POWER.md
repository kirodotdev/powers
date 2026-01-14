---
name: "aidlc"
displayName: "AI-DLC Workflow"
description: "AI-Driven Development Life Cycle - an intelligent software development workflow that adapts to your needs, maintains quality standards, and keeps you in control. Guides you through inception, construction, and operations phases with structured requirements, design, and code generation."
keywords: ["aidlc", "ai-dlc", "software-development", "workflow", "requirements", "design", "code-generation", "sdlc"]
author: "AWS Labs"
---

# AI-DLC (AI-Driven Development Life Cycle)

## Overview

AI-DLC is an intelligent software development workflow that adapts to your needs, maintains quality standards, and keeps you in control of the process. It provides a structured yet flexible approach to software development that:

- **Analyzes your requirements** and asks clarifying questions when needed
- **Plans the optimal approach** based on complexity and risk
- **Skips unnecessary steps** for simple changes while providing comprehensive coverage for complex projects
- **Documents everything** so you have a complete record of decisions and rationale
- **Guides you through each phase** with clear checkpoints and approval gates

## Available Steering Files

This power includes comprehensive workflow guides organized by phase:

### Core Workflow
- **core-workflow** - Main workflow orchestration and phase coordination

### Inception Phase (Planning & Architecture)
- **inception/workspace-detection** - Analyze workspace state and project type
- **inception/reverse-engineering** - Analyze existing codebase (brownfield projects)
- **inception/requirements-analysis** - Gather and validate requirements
- **inception/user-stories** - Create user stories and personas
- **inception/workflow-planning** - Create execution plan
- **inception/application-design** - High-level component and service design
- **inception/units-generation** - Decompose into units of work

### Construction Phase (Design, Implementation & Test)
- **construction/functional-design** - Detailed business logic design
- **construction/nfr-requirements** - Non-functional requirements and tech stack
- **construction/nfr-design** - NFR patterns and logical components
- **construction/infrastructure-design** - Infrastructure service mapping
- **construction/code-generation** - Code generation with planning and execution
- **construction/build-and-test** - Build and comprehensive testing

### Common Guidelines
- **common/process-overview** - Complete workflow overview with diagrams
- **common/welcome-message** - User-facing welcome and introduction
- **common/question-format-guide** - Question formatting rules
- **common/depth-levels** - Adaptive depth explanation
- **common/content-validation** - Content validation requirements
- **common/session-continuity** - Session resumption guidance
- **common/terminology** - AI-DLC terminology definitions
- **common/error-handling** - Error handling guidelines
- **common/ascii-diagram-standards** - ASCII diagram standards
- **common/workflow-changes** - Workflow modification guidelines
- **common/overconfidence-prevention** - Overconfidence prevention rules

## The Three-Phase Lifecycle

```
                         User Request
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║     INCEPTION PHASE                   ║
        ║     Planning & Application Design     ║
        ╠═══════════════════════════════════════╣
        ║ • Workspace Detection (ALWAYS)        ║
        ║ • Reverse Engineering (CONDITIONAL)   ║
        ║ • Requirements Analysis (ALWAYS)      ║
        ║ • User Stories (CONDITIONAL)          ║
        ║ • Workflow Planning (ALWAYS)          ║
        ║ • Application Design (CONDITIONAL)    ║
        ║ • Units Generation (CONDITIONAL)      ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║     CONSTRUCTION PHASE                ║
        ║     Design, Implementation & Test     ║
        ╠═══════════════════════════════════════╣
        ║ • Per-Unit Loop (for each unit):      ║
        ║   - Functional Design (CONDITIONAL)   ║
        ║   - NFR Requirements (CONDITIONAL)    ║
        ║   - NFR Design (CONDITIONAL)          ║
        ║   - Infrastructure Design (COND)      ║
        ║   - Code Generation (ALWAYS)          ║
        ║ • Build and Test (ALWAYS)             ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
        ╔═══════════════════════════════════════╗
        ║     OPERATIONS PHASE                  ║
        ║     Placeholder for Future            ║
        ╠═══════════════════════════════════════╣
        ║ • Operations (PLACEHOLDER)            ║
        ╚═══════════════════════════════════════╝
                              │
                              ▼
                          Complete
```

## Quick Start

To start using AI-DLC, simply state your intent starting with:

```
Using AI-DLC, [describe what you want to build or change]
```

AI-DLC will automatically:
1. Analyze your workspace to understand if this is a new or existing project
2. Gather requirements and ask clarifying questions if needed
3. Create an execution plan showing which stages will run and why
4. Guide you through each phase with checkpoints for your approval
5. Generate working code with complete documentation and tests

## Key Principles

- **Adaptive Execution**: Only execute stages that add value
- **Transparent Planning**: Always show execution plan before starting
- **User Control**: You can request stage inclusion/exclusion
- **Progress Tracking**: State tracked in `aidlc-docs/aidlc-state.md`
- **Complete Audit Trail**: All decisions logged in `aidlc-docs/audit.md`
- **Quality Focus**: Complex changes get full treatment, simple changes stay efficient

## Directory Structure

```
<WORKSPACE-ROOT>/                   # Application code here
├── [project-specific structure]    # Varies by project
│
├── aidlc-docs/                     # Documentation only
│   ├── inception/                  # INCEPTION PHASE
│   │   ├── plans/
│   │   ├── reverse-engineering/    # Brownfield only
│   │   ├── requirements/
│   │   ├── user-stories/
│   │   └── application-design/
│   ├── construction/               # CONSTRUCTION PHASE
│   │   ├── plans/
│   │   ├── {unit-name}/
│   │   │   ├── functional-design/
│   │   │   ├── nfr-requirements/
│   │   │   ├── nfr-design/
│   │   │   ├── infrastructure-design/
│   │   │   └── code/               # Markdown summaries only
│   │   └── build-and-test/
│   ├── operations/                 # OPERATIONS PHASE (placeholder)
│   ├── aidlc-state.md
│   └── audit.md
```

## Best Practices

1. **Start with clear intent** - The clearer your initial request, the more efficient the workflow
2. **Review each phase** - Take time to review and approve each stage before proceeding
3. **Provide feedback** - If something doesn't look right, request changes before approval
4. **Use the audit trail** - Reference `audit.md` to understand decisions made
5. **Leverage adaptivity** - Trust the workflow to skip unnecessary stages for simple changes

## Troubleshooting

### Workflow Not Starting
- Ensure you start your request with "Using AI-DLC, ..."
- Check that steering files are properly loaded

### Missing Stages
- AI-DLC adapts to your needs - some stages are conditional
- You can request specific stages be included in Workflow Planning

### Session Continuity
- AI-DLC tracks state in `aidlc-docs/aidlc-state.md`
- Resume interrupted sessions by referencing this file

## Additional Resources

- [AI-DLC GitHub Repository](https://github.com/awslabs/aidlc-workflows)
- [AI-DLC Methodology Blog](https://aws.amazon.com/blogs/)

## Attribution

This power is based on the [AI-DLC (AI-Driven Development Life Cycle) workflows](https://github.com/awslabs/aidlc-workflows) by AWS Labs, which is licensed under the MIT No Attribution License (MIT-0).

---

**Workflow:** AI-DLC (AI-Driven Development Life Cycle)
**Source:** AWS Labs
**License:** MIT-0 (MIT No Attribution)
