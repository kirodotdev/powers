# Technology Steering Template

Use this template for `.kiro/steering/tech.md`.

---

# Technology Steering

## Stack

- **Language**: [e.g., TypeScript 5.0, Python 3.11]
- **Framework**: [e.g., Next.js 14, FastAPI]
- **Database**: [e.g., PostgreSQL, MongoDB]
- **Cache**: [e.g., Redis, N/A]
- **Testing**: [e.g., Vitest, pytest]
- **CI/CD**: [e.g., GitHub Actions]

## Development Principles

### Test-First (NON-NEGOTIABLE)

All implementation MUST follow strict TDD:
1. Tests are written first
2. Tests are validated and approved
3. Tests are confirmed to FAIL (Red phase)
4. Implementation makes tests pass (Green phase)
5. Refactor while keeping tests green

### Simplicity Gate

- Maximum 3 projects for initial implementation
- Additional projects require documented justification
- No future-proofing allowed
- Start simple, add complexity only when proven necessary

### Anti-Abstraction Gate

- Use framework features directly rather than wrapping them
- Single model representation (no DTOs unless mandated)
- No wrapper classes unless adding behavior
- Trust the framework

### Library-First Principle

- Every feature begins as a standalone module
- Modules MUST be self-contained
- Modules MUST be independently testable
- Clear purpose required - no organizational-only modules

## Coding Standards

### Naming
- [Naming convention rules]

### Error Handling
- [Error handling approach]

### Logging
- [Logging requirements]

## Quality Gates

- [ ] All tests pass
- [ ] Code coverage >= [X]%
- [ ] No lint errors
- [ ] Type-safe (no `any` or equivalent)
- [ ] No security vulnerabilities
- [ ] Documentation updated

## Dependency Rules

- [Rules for adding new dependencies]
- [Version pinning policy]
- [Security scanning requirements]
