# Flask Code Simplification Guide

This guide covers Flask-specific patterns, conventions,
and best practices for writing clean, maintainable code.

## Table of Contents

1. [Flask Conventions](#flask-conventions)
2. [Blueprints](#blueprints)
3. [Application Factory Pattern](#application-factory-pattern)
4. [Request and Response Handling](#request-and-response-handling)
5. [SQLAlchemy Patterns](#sqlalchemy-patterns)
6. [Configuration](#configuration)
7. [Error Handling](#error-handling)
8. [Testing](#testing)

---

## Flask Conventions

### Directory Structure

Follow a modular structure with clear separation of concerns:

```
app/
├── __init__.py
├── extensions.py
├── config.py
├── blueprints/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── services.py
│   └── orders/
│       ├── __init__.py
│       ├── routes.py
│       ├── schemas.py
│       └── services.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── order.py
├── errors/
│   ├── __init__.py
│   └── handlers.py
└── tests/
    ├── conftest.py
    └── test_users.py
```

### Naming Conventions

```python
# Blueprints - plural, feature-based
users_bp = Blueprint("users", __name__)
orders_bp = Blueprint("orders", __name__)

# Routes - clear resource naming
@users_bp.get("/users/<int:user_id>")
def get_user(user_id): ...

# Models - singular, PascalCase
class User(db.Model): ...

# Services - singular, PascalCase
class UserService: ...
```

---

## Blueprints

### Keep Blueprints Focused

```python
# Bad - single blueprint with unrelated routes
api = Blueprint("api", __name__)

@api.get("/users/<int:user_id>")
def get_user(user_id): ...

@api.get("/orders/<int:order_id>")
def get_order(order_id): ...

# Good - separate blueprints by feature
users_bp = Blueprint("users", __name__)
orders_bp = Blueprint("orders", __name__)

@users_bp.get("/users/<int:user_id>")
def get_user(user_id): ...

@orders_bp.get("/orders/<int:order_id>")
def get_order(order_id): ...
```

### Blueprint Registration

```python
# app/__init__.py
def register_blueprints(app):
    from app.blueprints.users import users_bp
    from app.blueprints.orders import orders_bp

    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(orders_bp, url_prefix="/api")
```

---

## Application Factory Pattern

### Use a Factory for Configurable Apps

```python
# Bad - global app instance at import time
app = Flask(__name__)
app.config.from_object("app.config.Config")

@app.get("/health")
def health():
    return {"status": "ok"}

# Good - factory pattern with extensions
def create_app(config_object="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    from app.errors import register_error_handlers
    register_error_handlers(app)

    from app import register_blueprints
    register_blueprints(app)

    return app
```

### Extension Initialization

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
```

---

## Request and Response Handling

### Validate and Normalize Inputs

```python
# Bad - manual parsing, no validation
@users_bp.post("/users")
def create_user():
    data = request.json
    user = User(name=data["name"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

# Good - schema validation and explicit response
@users_bp.post("/users")
def create_user():
    payload = request.get_json() or {}
    data = UserCreateSchema().load(payload)

    user = UserService().create_user(data)
    return UserSchema().dump(user), 201
```

### Keep Routes Thin

```python
# Bad - business logic in route
@orders_bp.post("/orders")
def create_order():
    data = request.get_json() or {}
    total = sum(item["price"] * item["qty"] for item in data["items"])
    order = Order(user_id=data["user_id"], total=total)
    db.session.add(order)
    db.session.commit()
    return {"id": order.id}, 201

# Good - delegate to service layer
@orders_bp.post("/orders")
def create_order():
    data = OrderCreateSchema().load(request.get_json() or {})
    order = OrderService().create_order(data)
    return OrderSchema().dump(order), 201
```

---

## SQLAlchemy Patterns

### Model Organization

```python
class Order(db.Model):
    __tablename__ = "orders"

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)

    user = db.relationship("User", back_populates="orders")

    @classmethod
    def completed(cls):
        return cls.query.filter_by(status=cls.STATUS_COMPLETED)

    def mark_completed(self):
        self.status = self.STATUS_COMPLETED
```

### Avoid Query-in-Loop

```python
# Bad - N+1 queries
orders = Order.query.all()
for order in orders:
    print(order.user.email)

# Good - eager loading
orders = Order.query.options(db.joinedload(Order.user)).all()
for order in orders:
    print(order.user.email)
```

### Transactions for Multi-Step Operations

```python
# Bad - partial writes on failure
order = Order(user_id=user.id, total=total)
db.session.add(order)
db.session.commit()

for item in items:
    db.session.add(OrderItem(order_id=order.id, **item))
db.session.commit()

# Good - atomic transaction
with db.session.begin():
    order = Order(user_id=user.id, total=total)
    db.session.add(order)
    for item in items:
        db.session.add(OrderItem(order=order, **item))
```

---

## Configuration

### Environment-Based Settings

```python
# app/config.py
import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
```

### Config Selection

```python
# wsgi.py
from app import create_app

app = create_app("app.config.ProductionConfig")
```

---

## Error Handling

### Centralized Error Handlers

```python
# app/errors/handlers.py
from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "error": error.name,
            "message": error.description,
        }), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception("Unhandled exception")
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
        }), 500
```

### Custom Domain Errors

```python
class ValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}

# Register a handler for domain errors
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return {
        "error": "ValidationError",
        "message": str(error),
        "details": error.details,
    }, 400
```

---

## Testing

### Use a Test App Factory

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db

@pytest.fixture()
def app():
    app = create_app("app.config.TestingConfig")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
```

### Keep Tests Focused

```python
# Bad - too much setup in each test
def test_create_user(client):
    client.post("/users", json={"name": "A", "email": "a@example.com"})
    client.post("/users", json={"name": "B", "email": "b@example.com"})
    response = client.get("/users")
    assert response.status_code == 200

# Good - fixtures + clear intent
@pytest.fixture()
def user(client):
    response = client.post("/users", json={"name": "A", "email": "a@example.com"})
    return response.get_json()

def test_list_users(client, user):
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.get_json()) == 1
```

---

## Flask Simplification Checklist

- [ ] Application factory used for app creation
- [ ] Blueprints split by feature
- [ ] Routes are thin; services handle business logic
- [ ] Input validation via schemas (Marshmallow or similar)
- [ ] SQLAlchemy models include helper methods/scopes
- [ ] Eager loading prevents N+1 queries
- [ ] Transactions wrap multi-step writes
- [ ] Environment-specific configuration classes
- [ ] Centralized error handling with consistent JSON responses
- [ ] Tests use fixtures and app factory
- [ ] Testing database is isolated and clean

---

## Additional Resources

- Flask Documentation: https://flask.palletsprojects.com
- Flask Application Factories:
  https://flask.palletsprojects.com/en/latest/patterns/appfactories/
- Flask Blueprints:
  https://flask.palletsprojects.com/en/latest/blueprints/
- Flask SQLAlchemy:
  https://flask-sqlalchemy.palletsprojects.com
- Pytest:
  https://docs.pytest.org

**Flask Version Recommendation**: Use Flask 2.3+ with
Python 3.11+ for best features and support.
