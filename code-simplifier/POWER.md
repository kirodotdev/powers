---
name: "code-simplifier"
displayName: "Code Simplifier"
description: "Simplify and refine code across languages and frameworks for clarity, consistency, and maintainability while preserving behavior."
keywords: ["refactoring", "simplification", "clean-code", "maintainability", "readability", "code-review"]
author: "Raishin"
---

# Code Simplifier

## Overview

Code Simplifier helps you make behavior-preserving refactors that improve readability, consistency, and maintainability. It combines general simplification rules with language-specific and framework-specific steering so you can clean up code without drifting away from the repository's conventions.

Use this power when you want to reduce nesting, remove duplication, improve naming, simplify control flow, or align code with established framework patterns while keeping behavior the same.

## Onboarding

### Local Installation

1. Open the Kiro Powers UI.
2. Add a custom power from a local directory.
3. Select the `code-simplifier` power directory.
4. Confirm the power appears in the installed list.

### MCP Setup

This is a Guided MCP Power because it depends on Context7 lookups in Kiro.

1. Ensure `CONTEXT7_API_KEY` is available in the environment used by Kiro.
2. Verify the power includes `mcp.json` with a `context7` server definition.
3. Install or update the power in Kiro so the MCP configuration is reloaded.

### Verification

After installation, verify:

- the power appears in Kiro's installed powers list
- the `context7` MCP server connects successfully
- the power activates for refactoring or code simplification requests
- the steering files are available when the agent needs stack-specific guidance

## Available Steering Files

This power includes focused steering files for general rules, languages, and frameworks:

- **core** - Universal simplification rules and safety boundaries
- **c** - C simplification patterns and memory-aware cleanup
- **csharp** - C# readability, async flow, and .NET conventions
- **java** - Modern Java simplification and maintainable OO patterns
- **java-spring** - Spring Boot layering, DI, and controller/service cleanup
- **js** - JavaScript readability and control-flow simplification
- **kotlin** - Kotlin idioms, null-safety, and coroutine-aware cleanup
- **php** - General PHP readability and maintainability guidance
- **php-laravel** - Laravel conventions for controllers, services, and Eloquent code
- **php-symfony** - Symfony service and controller simplification patterns
- **python** - Pythonic cleanup and readability improvements
- **python-django** - Django views, models, and QuerySet simplification
- **python-fastapi** - FastAPI route, schema, and dependency cleanup
- **python-fastmcp** - FastMCP server and tool simplification guidance
- **python-flask** - Flask blueprint and application structure cleanup
- **rust** - Rust ownership-aware simplification and error handling
- **typescript** - TypeScript and TSX simplification patterns

All conceptual guidance is in this `POWER.md`. The steering files provide stack-specific guidance you can load as needed.

To load a specific guide:

```text
Call action "readSteering" with powerName="code-simplifier", steeringFile="core.md"
```

## When to Use This Power

- Simplifying recently modified code without changing behavior
- Refactoring controllers, services, components, functions, or small modules
- Reducing nesting and clarifying conditionals
- Removing duplication when the shared abstraction stays readable
- Aligning code with current language or framework conventions
- Reviewing a change for maintainability and readability issues

## Available MCP Servers

### context7

**Purpose:** Query current library and framework documentation when best-practice guidance depends on version or ecosystem conventions.

**Available tools:**
- `resolve-library-id` - Find the correct documentation target
- `query-docs` - Fetch current documentation and examples for a library or framework

## Tool Usage Examples

### Resolve a Documentation Target

```text
Use tool "resolve-library-id" with:
- libraryName: "laravel"
- query: "I want current Laravel controller and Eloquent simplification guidance"
```

### Query Current Best Practices

```text
Use tool "query-docs" with:
- libraryId: "/laravel/docs"
- query: "controller validation best practices"
```

## Recommended Workflow

1. Read `core.md` first to establish the safety boundaries for behavior-preserving cleanup.
2. Load the language steering file that matches the code you are touching.
3. Load the framework steering file only when the file clearly depends on that framework.
4. Use Context7 when current best practices or version-specific behavior matters.
5. Keep the change local unless broader cleanup is explicitly requested.

## Example Workflow

### Simplify a Laravel Controller

1. Activate the power for a request such as: "simplify this Laravel controller without changing behavior".
2. Read `core.md` to apply the behavior-preserving rules first.
3. Read `php.md` for general PHP cleanup guidance.
4. Read `php-laravel.md` because controller and Eloquent patterns depend on Laravel conventions.
5. Call `resolve-library-id` with:
   - `libraryName`: `laravel`
   - `query`: `controller validation and relationship loading best practices`
6. Call `query-docs` with:
   - `libraryId`: the resolved Laravel docs id
   - `query`: `controller validation best practices`
7. Apply the smallest refactor that improves clarity without changing interfaces, side effects, or request lifecycle behavior.
8. Re-check that the result is more readable, still local in scope, and still follows repository conventions.

## Best Practices

- Preserve behavior, public interfaces, and side effects unless change is explicitly requested.
- Prefer clarity over brevity.
- Use guard clauses, extraction, and clearer control flow to reduce nesting.
- Keep abstractions only when they improve readability.
- Avoid dense or clever rewrites that make the code harder to reason about.
- Follow the repository's existing style unless there is a clear reason not to.

## Configuration

This power expects Context7 to be configured through `code-simplifier/mcp.json`.

- Set `CONTEXT7_API_KEY` in the environment used by Kiro before enabling the power.
- If Context7 is unavailable, you can still use the steering files, but version-sensitive best-practice checks will be weaker.
- Keep `autoApprove` limited to the read-only Context7 tools already defined in `mcp.json`.

## Troubleshooting

### The refactor changes behavior

- Narrow the scope and start from the smallest safe cleanup.
- Re-check interfaces, side effects, and lifecycle ordering.
- Use the stack-specific steering file before broadening the change.

### The right simplification is unclear

- Load `core.md`, then the relevant language guide.
- Add the framework guide only if it materially affects the code shape.
- Use Context7 to verify current conventions when versions or APIs matter.

### The code is already dense for good reason

- Organize the code rather than forcing it to be shorter.
- Prefer explicit helpers and comments over aggressive collapsing.

### Context7 lookups fail

- Verify that `CONTEXT7_API_KEY` is set in the environment used by Kiro.
- Confirm the `context7` server in `code-simplifier/mcp.json` still points to `@upstash/context7-mcp`.
- Fall back to the relevant steering file if the external docs lookup is temporarily unavailable.
