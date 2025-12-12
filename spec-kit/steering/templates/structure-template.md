# Structure Steering Template

Use this template for `.kiro/steering/structure.md`.

---

# Structure Steering

## Project Layout

```text
[Define your project structure here]

# Example for web application:
src/
├── components/     # UI components
├── services/       # Business logic
├── models/         # Data models
├── api/            # API routes
├── hooks/          # Custom hooks
├── utils/          # Utility functions
└── types/          # Type definitions

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/            # End-to-end tests

docs/               # Documentation
```

## Naming Conventions

### Files
- [Convention, e.g., kebab-case: `user-service.ts`]

### Components
- [Convention, e.g., PascalCase: `UserProfile.tsx`]

### Functions
- [Convention, e.g., camelCase: `getUserById`]

### Constants
- [Convention, e.g., SCREAMING_SNAKE_CASE: `MAX_RETRY_COUNT`]

### Database Tables
- [Convention, e.g., snake_case plural: `user_accounts`]

## Module Organization

### Rules
- Each module is self-contained
- Clear public API via index exports
- No circular dependencies
- Maximum module depth: [N] levels

### Module Structure
```text
feature/
├── index.ts        # Public API exports
├── types.ts        # Type definitions
├── service.ts      # Business logic
├── repository.ts   # Data access
└── __tests__/      # Tests
```

## API Patterns

### REST Endpoints
- `GET /api/[resource]` - List resources
- `GET /api/[resource]/:id` - Get single resource
- `POST /api/[resource]` - Create resource
- `PUT /api/[resource]/:id` - Update resource
- `DELETE /api/[resource]/:id` - Delete resource

### Response Format
```json
{
  "data": {},
  "error": null,
  "meta": {}
}
```

## Database Conventions

### Tables
- [Naming convention]
- [Primary key convention]

### Migrations
- [Migration file naming]
- [Migration process]

## Documentation

### Locations
- API docs: [location]
- Architecture docs: [location]
- User guides: [location]

### Requirements
- [What must be documented]
- [Documentation format]
