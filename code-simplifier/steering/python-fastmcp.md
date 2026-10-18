# FastMCP Python Code Simplification Guide

This guide focuses on writing clean, maintainable MCP servers using FastMCP.
It highlights common simplification patterns, error handling, testing, and best
practices, with side-by-side examples of bad vs good approaches. The patterns
align with typical FastMCP documentation conventions such as `@mcp.tool`,
`@mcp.resource`, `@mcp.prompt`, and server lifespan hooks.

## Table of Contents

1. [Server Patterns](#server-patterns)
2. [Tool Definitions](#tool-definitions)
3. [Resource Management](#resource-management)
4. [Context Handling](#context-handling)
5. [Error Handling](#error-handling)
6. [Testing MCP Servers](#testing-mcp-servers)
7. [Best Practices](#best-practices)
8. [Checklist](#checklist)
9. [Resources](#resources)

---

## Server Patterns

### Minimal, Clear Server Construction

```python
# Bad - global state, hidden configuration, hard to test
from fastmcp import FastMCP

mcp = FastMCP("server")
API_KEY = "dev-key"

@mcp.tool()
def search(query: str) -> str:
    return f"Searching {query} with {API_KEY}"
```

```python
# Good - explicit config, pure logic separated from transport
from dataclasses import dataclass
from fastmcp import FastMCP

@dataclass(frozen=True)
class Config:
    api_key: str

def build_server(config: Config) -> FastMCP:
    mcp = FastMCP("search-server")

    @mcp.tool()
    def search(query: str) -> str:
        return f"Searching {query} with {config.api_key}"

    return mcp
```

### Lifespan and Startup/Shutdown Hooks

```python
# Bad - setup scattered inside tools
from fastmcp import FastMCP

mcp = FastMCP("server")

@mcp.tool()
def fetch_user(user_id: str) -> dict:
    db = connect_db()
    return db.get_user(user_id)
```

```python
# Good - use lifespan hooks for shared resources
from fastmcp import FastMCP

mcp = FastMCP("server")

@mcp.lifespan()
async def lifespan():
    db = await connect_db_async()
    try:
        yield {"db": db}
    finally:
        await db.close()

@mcp.tool()
def fetch_user(user_id: str, ctx) -> dict:
    return ctx.state["db"].get_user(user_id)
```

---

## Tool Definitions

### Keep Tool Functions Narrow and Typed

```python
# Bad - multiple responsibilities, weak types
from fastmcp import FastMCP

mcp = FastMCP("server")

@mcp.tool()
def manage_user(action: str, payload: dict) -> dict:
    if action == "create":
        return create_user(payload)
    if action == "update":
        return update_user(payload)
    raise ValueError("Unknown action")
```

```python
# Good - single purpose, typed inputs/outputs
from dataclasses import dataclass
from fastmcp import FastMCP

mcp = FastMCP("server")

@dataclass
class UserInput:
    name: str
    email: str

@mcp.tool()
def create_user_tool(user: UserInput) -> dict:
    return create_user(user)

@mcp.tool()
def update_user_tool(user_id: str, user: UserInput) -> dict:
    return update_user(user_id, user)
```

### Document Tools With Descriptions

```python
# Bad - missing descriptions, unclear intent
@mcp.tool()
def summarize(text: str) -> str:
    return do_summary(text)
```

```python
# Good - explicit docstring and clear parameter names
@mcp.tool()
def summarize(text: str) -> str:
    """Summarize a block of text into a short paragraph."""
    return do_summary(text)
```

---

## Resource Management

FastMCP resources (via `@mcp.resource`) provide structured access to data.

### Avoid Dynamic, Unbounded Resource Paths

```python
# Bad - single resource with too many responsibilities
from fastmcp import FastMCP

mcp = FastMCP("server")

@mcp.resource("data/{path}")
def data_resource(path: str) -> str:
    return read_anything(path)
```

```python
# Good - explicit, focused resource endpoints
from fastmcp import FastMCP

mcp = FastMCP("server")

@mcp.resource("data/users/{user_id}")
def user_resource(user_id: str) -> dict:
    return load_user(user_id)

@mcp.resource("data/orders/{order_id}")
def order_resource(order_id: str) -> dict:
    return load_order(order_id)
```

### Cache or Reuse Expensive Resources

```python
# Bad - reload config on every call
@mcp.resource("config")
def config_resource() -> dict:
    return load_config_from_disk()
```

```python
# Good - read once, reuse from context
@mcp.lifespan()
async def lifespan():
    config = load_config_from_disk()
    yield {"config": config}

@mcp.resource("config")
def config_resource(ctx) -> dict:
    return ctx.state["config"]
```

---

## Context Handling

Use context (`ctx`) to access shared state, logging, and request metadata.

### Keep Context Usage Explicit

```python
# Bad - implicit global context
CURRENT_REQUEST = None

@mcp.tool()
def get_request_id() -> str:
    return CURRENT_REQUEST.id
```

```python
# Good - explicit context passing
@mcp.tool()
def get_request_id(ctx) -> str:
    return ctx.request_id
```

### Avoid Passing Context Deep into Pure Functions

```python
# Bad - context leaks into pure business logic
def calculate_quote(ctx, user_id: str) -> dict:
    logger = ctx.logger
    logger.info("Calculating quote")
    return pricing_engine(user_id)
```

```python
# Good - extract data once, keep logic pure
def calculate_quote(user_id: str) -> dict:
    return pricing_engine(user_id)

@mcp.tool()
def calculate_quote_tool(user_id: str, ctx) -> dict:
    ctx.logger.info("Calculating quote")
    return calculate_quote(user_id)
```

---

## Error Handling

Prefer clear, user-safe error messages while preserving internal detail for logs.

### Avoid Leaking Internal Exceptions

```python
# Bad - raw exception details exposed
@mcp.tool()
def parse_report(payload: dict) -> dict:
    return parse(payload)  # May raise with stack trace
```

```python
# Good - catch and wrap, log internally
@mcp.tool()
def parse_report(payload: dict, ctx) -> dict:
    try:
        return parse(payload)
    except ValueError as exc:
        ctx.logger.exception("Parse failure")
        raise ValueError("Invalid report payload") from exc
```

### Validate Inputs Early

```python
# Bad - validation buried later
@mcp.tool()
def create_invoice(amount: float) -> dict:
    return invoice_service.create(amount)
```

```python
# Good - guardrails at boundaries
@mcp.tool()
def create_invoice(amount: float) -> dict:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    return invoice_service.create(amount)
```

---

## Testing MCP Servers

Keep tools pure and testable with minimal FastMCP plumbing.

### Test Pure Logic Directly

```python
# Bad - tests depend on server infrastructure
def test_search_tool(mcp_client):
    result = mcp_client.call_tool("search", {"query": "cats"})
    assert "cats" in result
```

```python
# Good - separate pure logic and test directly
def search_logic(query: str, api_key: str) -> str:
    return f"Searching {query} with {api_key}"

def test_search_logic():
    result = search_logic("cats", "test-key")
    assert "cats" in result
```

### Use FastMCP Test Clients When Needed

```python
# Good - integration test around tool wiring
def test_search_tool_integration(mcp_client):
    result = mcp_client.call_tool("search", {"query": "cats"})
    assert "cats" in result
```

### Fake External Dependencies

```python
# Bad - hitting live services
def test_weather_tool(mcp_client):
    result = mcp_client.call_tool("weather", {"city": "Paris"})
    assert "Paris" in result
```

```python
# Good - stub service with predictable output
class FakeWeatherService:
    def get(self, city: str) -> dict:
        return {"city": city, "temp_c": 18}

def test_weather_logic():
    service = FakeWeatherService()
    assert service.get("Paris")["temp_c"] == 18
```

---

## Best Practices

### Keep Tools Small and Composable

```python
# Bad - tool does fetch, transform, and persist
@mcp.tool()
def sync_users() -> dict:
    data = api.fetch_users()
    transformed = transform_users(data)
    return db.save_users(transformed)
```

```python
# Good - delegate to small, testable functions
def fetch_users():
    return api.fetch_users()

def transform_users(data):
    return [normalize_user(u) for u in data]

def save_users(users):
    return db.save_users(users)

@mcp.tool()
def sync_users() -> dict:
    users = transform_users(fetch_users())
    return save_users(users)
```

### Avoid Hidden Side Effects

```python
# Bad - tool mutates global config
@mcp.tool()
def set_timezone(tz: str) -> str:
    global SETTINGS
    SETTINGS["timezone"] = tz
    return "ok"
```

```python
# Good - update explicit state or config store
@mcp.tool()
def set_timezone(tz: str, ctx) -> str:
    ctx.state["settings"].set_timezone(tz)
    return "ok"
```

### Prefer Data Classes or Typed Models

```python
# Bad - loose dicts
@mcp.tool()
def create_project(payload: dict) -> dict:
    return projects.create(payload)
```

```python
# Good - explicit schema
from dataclasses import dataclass

@dataclass
class ProjectInput:
    name: str
    owner_id: str

@mcp.tool()
def create_project(project: ProjectInput) -> dict:
    return projects.create(project)
```

---

## Checklist

- Define a clear `build_server(config)` entry for testability.
- Keep `@mcp.tool` functions single-purpose and typed.
- Use `@mcp.resource` for structured data access, avoid catch-all paths.
- Use lifespan hooks to manage shared resources like DBs or caches.
- Keep context access explicit, avoid passing `ctx` deep into pure logic.
- Validate inputs at tool boundaries; wrap and log errors safely.
- Separate pure logic from IO for fast unit tests.
- Use FastMCP test clients for integration-level coverage.

---

## Resources

- FastMCP README and examples (decorators: `@mcp.tool`, `@mcp.resource`, `@mcp.prompt`)
- MCP specification and protocol reference
- Python typing and `dataclasses` documentation
- Testing patterns for async servers (pytest, asyncio)
