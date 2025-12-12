# Tasks Template

Use this template when generating task lists.

---

# Tasks: [FEATURE NAME]

**Branch**: `[###-feature-name]`
**Created**: [DATE]
**Design**: [link to design.md]
**Requirements**: [link to requirements.md]

## Overview

Total tasks: [N]
- Setup: [N] tasks
- Foundational: [N] tasks
- User Stories: [N] stories, [N] tasks
- Polish: [N] tasks

Parallel opportunities: [N] tasks marked [P]
MVP Scope: Phase 3 (User Story 1)

---

## Phase 1: Setup

Project initialization tasks.

- [ ] T001 Create project directory structure per implementation plan
- [ ] T002 [P] Initialize package manager with dependencies
- [ ] T003 [P] Create configuration files

---

## Phase 2: Foundational

Blocking prerequisites for all user stories. Must complete before story phases.

- [ ] T004 Create database schema/models base
- [ ] T005 [P] Implement shared utilities
- [ ] T006 [P] Configure testing framework

---

## Phase 3: User Story 1 - [Title] (P1)

**Goal**: [Story goal from spec]

**Independent Test**: [How to test this story alone]

**Tasks**:

- [ ] T007 [US1] Create [Entity] model in src/models/[entity].py
- [ ] T008 [US1] Implement [Entity]Service in src/services/[entity]_service.py
- [ ] T009 [US1] Create API endpoint in src/api/[entity].py
- [ ] T010 [US1] Add integration test in tests/integration/test_[entity].py

**Checkpoint**: After T010, User Story 1 should be independently testable.

---

## Phase 4: User Story 2 - [Title] (P2)

**Goal**: [Story goal from spec]

**Independent Test**: [How to test this story alone]

**Tasks**:

- [ ] T011 [US2] Create [Entity] model in src/models/[entity].py
- [ ] T012 [P] [US2] Implement [Service] in src/services/[service].py
- [ ] T013 [US2] Create API endpoint in src/api/[entity].py

**Checkpoint**: After T013, User Story 2 should be independently testable.

---

## Phase 5: User Story 3 - [Title] (P3)

**Goal**: [Story goal from spec]

**Independent Test**: [How to test this story alone]

**Tasks**:

- [ ] T014 [US3] [Task description with file path]
- [ ] T015 [US3] [Task description with file path]

**Checkpoint**: After T015, User Story 3 should be independently testable.

---

## Phase N: Polish & Cross-Cutting

Final cleanup and cross-cutting concerns.

- [ ] T0XX Add logging throughout application
- [ ] T0XX Update documentation
- [ ] T0XX Performance optimization
- [ ] T0XX Final integration testing

---

## Dependencies

```
Phase 1 (Setup)
    |
    v
Phase 2 (Foundational)
    |
    +--> Phase 3 (US1) --> Phase 4 (US2) --> Phase 5 (US3)
    |                                              |
    +----------------------------------------------+
                        |
                        v
                  Phase N (Polish)
```

### Story Dependencies

| Story | Depends On | Reason |
|-------|------------|--------|
| US2 | US1 | Shares [component] |
| US3 | None | Independent |

---

## Parallel Execution Guide

### Within Phase 3 (US1)
- T007, T008 can run in parallel (different files)
- T009 depends on T007, T008 (uses their outputs)

### Within Phase 4 (US2)
- T011, T012 can run in parallel (different files)
- T013 depends on T011, T012

### Across Phases
- Phase 3 and Phase 4 are generally sequential
- Setup tasks (T001-T003) can run in parallel where marked [P]

---

## Implementation Strategy

### MVP First
Complete Phase 3 (User Story 1) for minimum viable product.

### Incremental Delivery
Each user story phase produces independently testable increment.

### Test Checkpoints
Verify each story works before proceeding to next.

---

## Task Format Reference

Every task MUST follow this format:
```
- [ ] [TaskID] [P?] [Story?] Description with file path
```

**Components**:
1. `- [ ]` - Checkbox (required)
2. `T###` - Task ID (required)
3. `[P]` - Parallel marker (if parallelizable)
4. `[US#]` - Story label (required in story phases)
5. Description with file path (required)

**Mark completed**:
```
- [X] T001 Create project structure
```
