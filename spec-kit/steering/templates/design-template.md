# Implementation Plan Template

Use this template when creating implementation plans.

---

# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  Replace with technical details for this project.
  Mark unknowns as NEEDS CLARIFICATION for research phase.
-->

**Language/Version**: [e.g., Python 3.11, TypeScript 5.0, or NEEDS CLARIFICATION]
**Primary Dependencies**: [e.g., FastAPI, React, Express, or NEEDS CLARIFICATION]
**Storage**: [e.g., PostgreSQL, MongoDB, files, or N/A]
**Testing**: [e.g., pytest, Jest, Vitest, or NEEDS CLARIFICATION]
**Target Platform**: [e.g., Linux server, iOS 15+, Web, or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 60 fps, or NEEDS CLARIFICATION]
**Constraints**: [domain-specific, e.g., <200ms p95, offline-capable, or NEEDS CLARIFICATION]
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, or NEEDS CLARIFICATION]

## Steering Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

<!--
  Fill in based on steering files (.kiro/steering/product.md, tech.md, structure.md).
  Common gates:
-->

### Simplicity Gate
- [ ] Using <=3 projects?
- [ ] No future-proofing?
- [ ] Minimal necessary complexity?

### Anti-Abstraction Gate
- [ ] Using framework directly?
- [ ] Single model representation?
- [ ] No unnecessary wrappers?

### Integration-First Gate
- [ ] Contracts defined?
- [ ] Contract tests planned?
- [ ] Real environments for testing?

### Product Alignment (from .kiro/steering/product.md)
- [ ] Aligns with product vision?
- [ ] Respects business constraints?

### Tech Compliance (from .kiro/steering/tech.md)
- [ ] Uses approved technology stack?
- [ ] Follows development principles?

### Structure Compliance (from .kiro/steering/structure.md)
- [ ] Follows project layout?
- [ ] Uses correct naming conventions?

## Project Structure

### Documentation (this feature)

```text
.kiro/specs/[###-feature]/
├── requirements.md      # Feature specification
├── design.md            # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
├── checklists/          # Checklist workflow output
└── tasks.md             # Tasks workflow output
```

### Source Code (repository root)

<!--
  Replace with concrete layout for this feature.
  Delete unused options.
-->

**Option 1: Single project (DEFAULT)**

```text
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

**Option 2: Web application**

```text
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Option 3: Mobile + API**

```text
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [Document selected structure and rationale]

## Complexity Tracking

> **Fill ONLY if Steering Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Phase 0: Research

<!--
  For each NEEDS CLARIFICATION in Technical Context:
  - Research task
  - Document decision with rationale
-->

*Output: research.md*

## Phase 1: Design

<!--
  Prerequisites: research.md complete
-->

### Data Model
*Extract entities from feature spec -> data-model.md*

### API Contracts
*Generate from functional requirements -> contracts/*

### Validation Scenarios
*Key test scenarios -> quickstart.md*

*Output: data-model.md, contracts/, quickstart.md*
