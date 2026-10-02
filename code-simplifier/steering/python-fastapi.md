# FastAPI Code Simplification Guide

This guide covers FastAPI-specific patterns, conventions,
and best practices for writing clean, maintainable code.

## Table of Contents

1. [FastAPI Conventions](#fastapi-conventions)
2. [Dependency Injection](#dependency-injection)
3. [Path Operations](#path-operations)
4. [Pydantic Models](#pydantic-models)
5. [Async Patterns](#async-patterns)
6. [Database Integration](#database-integration)
7. [Middleware](#middleware)
8. [Testing](#testing)
9. [OpenAPI Documentation](#openapi-documentation)

---

## FastAPI Conventions

### Directory Structure

Keep modules aligned with features and layers:

```
app/
├── main.py
├── api/
│   ├── deps.py
│   ├── routes/
│   └── schemas/
├── core/
│   ├── config.py
│   └── logging.py
├── db/
│   ├── session.py
│   └── models/
├── services/
└── tests/
```

### Naming Conventions

```python
# Routers - resource focused
orders.py, users.py

# Services - behavior focused
order_service.py, billing_service.py

# Schemas - explicit type role
CreateOrderRequest, OrderResponse, UserSummary

# Database models - singular
Order, User, OrderItem
```

---

## Dependency Injection

### Prefer Explicit Dependencies

```python
# Bad - hidden global dependency
db = SessionLocal()

@app.post("/orders")
def create_order(payload: CreateOrderRequest):
    return OrderService(db).create(payload)

# Good - explicit dependency injection
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/orders")
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
) -> OrderResponse:
    return OrderService(db).create(payload)
```

### Use Dependency Factories for Swappable Implementations

```python
# Good - interface-like protocol for easy testing
class PaymentGateway(Protocol):
    def charge(self, request: PaymentRequest) -> PaymentResult:
        ...

class StripePaymentGateway:
    def charge(self, request: PaymentRequest) -> PaymentResult:
        return PaymentResult.success()

def get_payment_gateway() -> PaymentGateway:
    return StripePaymentGateway()
```

---

## Path Operations

### Thin Handlers

```python
# Bad - validation, logic, and persistence in handler
@router.post("/orders")
def create_order(payload: dict, db: Session = Depends(get_db)):
    if "items" not in payload or not payload["items"]:
        raise HTTPException(status_code=400, detail="No items")
    total = sum(i["price"] * i["quantity"] for i in payload["items"])
    order = Order(status="PENDING", total=total)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

# Good - handler delegates to service, validation in schema
@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(
    payload: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return service.create(payload)
```

### Response Models Over ORM Objects

```python
# Bad - returning ORM objects directly
@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    return db.get(Order, order_id)

# Good - map to response schema
@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, service: OrderService = Depends(get_order_service)):
    return service.get(order_id)
```

---

## Pydantic Models

### Separate Request and Response Types

```python
# Bad - one schema for everything
class OrderSchema(BaseModel):
    id: int | None = None
    status: str
    total: float

# Good - explicit request/response schemas
class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest]

class OrderResponse(BaseModel):
    id: int
    status: str
    total: Decimal
```

### Validation at the Edge

```python
# Good - validate types and ranges in schema
class OrderItemRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=Decimal("0.00"))
```

---

## Async Patterns

### Do Not Block the Event Loop

```python
# Bad - blocking call in async handler
@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    data = generate_report_blocking(report_id)
    return {"data": data}

# Good - use threadpool for blocking work
@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    data = await run_in_threadpool(generate_report_blocking, report_id)
    return {"data": data}
```

### Use Async I/O End-to-End

```python
# Bad - async handler with sync DB session
@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(get_db)):
    return db.get(Order, order_id)

# Good - async handler with async DB session
@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: AsyncSession = Depends(get_async_db)):
    return await db.get(Order, order_id)
```

---

## Database Integration

### Keep Session Lifecycle Scoped

```python
# Bad - session created at import time
db = SessionLocal()

def get_order(order_id: int):
    return db.get(Order, order_id)

# Good - session per request
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Prefer Explicit Transactions

```python
# Bad - multiple commits for one workflow
def fulfill_order(order_id: int, db: Session):
    order = db.get(Order, order_id)
    order.status = "PAID"
    db.commit()
    reserve_inventory(order, db)
    db.commit()

# Good - one transaction boundary
def fulfill_order(order_id: int, db: Session):
    with db.begin():
        order = db.get(Order, order_id)
        order.status = "PAID"
        reserve_inventory(order, db)
```

---

## Middleware

### Keep Middleware Focused

```python
# Bad - middleware doing auth, logging, and parsing
@app.middleware("http")
async def all_in_one(request: Request, call_next):
    user = await auth(request)
    request.state.user = user
    request.state.body = await request.json()
    response = await call_next(request)
    response.headers["X-Request-Id"] = str(uuid4())
    return response

# Good - small, single-purpose middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response
```

---

## Testing

### Use TestClient and Dependency Overrides

```python
# Bad - hitting real database in unit tests
def test_create_order():
    response = client.post("/orders", json={"items": [{"sku": "x", "quantity": 1, "price": 10}]})
    assert response.status_code == 201

# Good - override dependencies for isolation
def test_create_order(client: TestClient, db_session: Session):
    app.dependency_overrides[get_db] = lambda: db_session
    response = client.post("/orders", json={"items": [{"sku": "x", "quantity": 1, "price": 10}]})
    assert response.status_code == 201
```

### Async Tests with AnyIO

```python
@pytest.mark.anyio
async def test_get_order(async_client: AsyncClient):
    response = await async_client.get("/orders/1")
    assert response.status_code == 200
```

---

## OpenAPI Documentation

### Use Response Models and Metadata

```python
# Bad - minimal metadata, no response model
@router.get("/orders/{order_id}")
def get_order(order_id: int):
    ...

# Good - clear docs, tags, summaries, response models
@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order by id",
    tags=["orders"],
)
def get_order(order_id: int, service: OrderService = Depends(get_order_service)):
    return service.get(order_id)
```

### Group Routers

```python
# Good - group endpoints by router and include tags
orders_router = APIRouter(prefix="/orders", tags=["orders"])
users_router = APIRouter(prefix="/users", tags=["users"])
```

---

## FastAPI Simplification Checklist

- [ ] Routers are thin and delegate to services
- [ ] Dependencies are explicit via Depends
- [ ] Request/response schemas are separate
- [ ] Async endpoints avoid blocking calls
- [ ] DB sessions are scoped per request
- [ ] Transactions wrap multi-step updates
- [ ] Middleware is single-purpose
- [ ] Tests use dependency overrides
- [ ] OpenAPI metadata is filled in

---

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com
- Pydantic Documentation: https://docs.pydantic.dev
- SQLAlchemy Documentation: https://docs.sqlalchemy.org
- Testing FastAPI: https://fastapi.tiangolo.com/tutorial/testing

**FastAPI Version Recommendation**: Use FastAPI 0.110+
with Pydantic v2 and Python 3.11+.
