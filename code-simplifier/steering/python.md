# Python Code Simplification Guide

This guide covers Python-specific simplification patterns
and best practices for writing Pythonic code.

## Table of Contents

1. [PEP 8 and Style](#pep-8-and-style)
2. [Pythonic Patterns](#pythonic-patterns)
3. [List Comprehensions](#list-comprehensions)
4. [Context Managers](#context-managers)
5. [Generators and Iterators](#generators-and-iterators)
6. [Type Hints](#type-hints)
7. [Error Handling](#error-handling)
8. [When to Load Django Guidance](#when-to-load-django-guidance)

---

## PEP 8 and Style

### Naming Conventions

```python
# Variables and functions - snake_case
user_name = "John"
def calculate_total(items):
    pass

# Classes - PascalCase
class UserService:
    pass

# Constants - UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private attributes/methods - leading underscore
class User:
    def __init__(self):
        self._password = None  # Private

    def _validate(self):  # Private method
        pass
```

### Import Organization

```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import requests

# Local application imports
from .models import User
from .services import EmailService
```

### Line Length and Formatting

```python
# Bad - too long
result = some_function(argument1, argument2, argument3, argument4, argument5, argument6)

# Good - break into multiple lines
result = some_function(
    argument1,
    argument2,
    argument3,
    argument4,
    argument5,
    argument6
)

# Dictionary formatting
user_data = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'age': 30,
    'is_active': True,
}
```

---

## Pythonic Patterns

### The Zen of Python

```python
import this

# Key principles:
# - Explicit is better than implicit
# - Simple is better than complex
# - Readability counts
# - There should be one obvious way to do it
```

### EAFP vs LBYL

```python
# Bad - LBYL (Look Before You Leap)
if key in dictionary:
    value = dictionary[key]
else:
    value = default_value

# Good - EAFP (Easier to Ask for Forgiveness than Permission)
try:
    value = dictionary[key]
except KeyError:
    value = default_value

# Even better - use dict.get()
value = dictionary.get(key, default_value)
```

### String Formatting

```python
name = "John"
age = 30

# Bad - old style
message = "Hello, %s. You are %d years old." % (name, age)

# Better - str.format()
message = "Hello, {}. You are {} years old.".format(name, age)

# Best - f-strings (Python 3.6+)
message = f"Hello, {name}. You are {age} years old."

# Complex expressions in f-strings
total = f"Total: ${sum(prices):.2f}"
```

### Unpacking

```python
# Tuple unpacking
first, second = (1, 2)
first, *rest = [1, 2, 3, 4, 5]

# Dictionary unpacking
defaults = {'theme': 'light', 'language': 'en'}
user_prefs = {'language': 'fr'}
config = {**defaults, **user_prefs}

# Function arguments
def create_user(name, email, **kwargs):
    user = User(name=name, email=email)
    for key, value in kwargs.items():
        setattr(user, key, value)
    return user
```

### Enumerate and Zip

```python
# Bad - manual indexing
for i in range(len(items)):
    print(f"{i}: {items[i]}")

# Good - enumerate
for index, item in enumerate(items):
    print(f"{index}: {item}")

# Zip for parallel iteration
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]

for name, age in zip(names, ages):
    print(f"{name} is {age} years old")
```

---

## List Comprehensions

### Basic List Comprehensions

```python
# Bad - manual loop
squares = []
for x in range(10):
    squares.append(x ** 2)

# Good - list comprehension
squares = [x ** 2 for x in range(10)]

# With condition
even_squares = [x ** 2 for x in range(10) if x % 2 == 0]

# Nested comprehension
matrix = [[i * j for j in range(5)] for i in range(5)]
```

### Dictionary and Set Comprehensions

```python
# Dictionary comprehension
user_dict = {user.id: user.name for user in users}

# With condition
active_users = {
    user.id: user.name
    for user in users
    if user.is_active
}

# Set comprehension
unique_emails = {user.email.lower() for user in users}
```

### When NOT to Use Comprehensions

```python
# Bad - too complex
result = [
    process_item(item)
    for sublist in nested_list
    for item in sublist
    if item.is_valid() and item.status == 'active'
    if not item.is_deleted
]

# Good - explicit loop for clarity
result = []
for sublist in nested_list:
    for item in sublist:
        if item.is_valid() and item.status == 'active':
            if not item.is_deleted:
                result.append(process_item(item))
```

---

## Context Managers

### Using Context Managers

```python
# Bad - manual file handling
file = open('data.txt', 'r')
try:
    data = file.read()
finally:
    file.close()

# Good - context manager
with open('data.txt', 'r') as file:
    data = file.read()

# Multiple context managers
with open('input.txt', 'r') as infile, open('output.txt', 'w') as outfile:
    outfile.write(infile.read())
```

### Creating Custom Context Managers

```python
from contextlib import contextmanager

# Using decorator
@contextmanager
def database_transaction(connection):
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise

# Usage
with database_transaction(conn) as db:
    db.execute("INSERT INTO users ...")

# Class-based context manager
class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.duration = self.end - self.start
        print(f"Elapsed time: {self.duration:.2f}s")

# Usage
with Timer():
    # Code to time
    process_data()
```

---

## Generators and Iterators

### Generator Functions

```python
# Bad - creates entire list in memory
def get_numbers(n):
    result = []
    for i in range(n):
        result.append(i ** 2)
    return result

# Good - generator (lazy evaluation)
def get_numbers(n):
    for i in range(n):
        yield i ** 2

# Usage
for num in get_numbers(1000000):  # Memory efficient
    print(num)
```

### Generator Expressions

```python
# List comprehension - creates entire list
squares = [x ** 2 for x in range(1000000)]

# Generator expression - lazy evaluation
squares = (x ** 2 for x in range(1000000))

# Use in functions that accept iterables
total = sum(x ** 2 for x in range(1000000))
```

### Itertools

```python
from itertools import chain, groupby, islice

# Chain multiple iterables
combined = chain(list1, list2, list3)

# Group by key
data = [
    {'name': 'Alice', 'dept': 'Sales'},
    {'name': 'Bob', 'dept': 'Sales'},
    {'name': 'Charlie', 'dept': 'IT'},
]

for dept, people in groupby(data, key=lambda x: x['dept']):
    print(f"{dept}: {list(people)}")

# Slice iterator
first_10 = list(islice(infinite_generator(), 10))
```

---

## Type Hints

### Basic Type Hints

```python
from typing import List, Dict, Optional, Union, Tuple

# Function type hints
def calculate_total(items: List[float]) -> float:
    return sum(items)

def get_user(user_id: int) -> Optional[User]:
    return User.objects.filter(id=user_id).first()

# Variable type hints
name: str = "John"
age: int = 30
prices: List[float] = [10.99, 20.50, 5.25]
user_data: Dict[str, Union[str, int]] = {
    'name': 'John',
    'age': 30
}
```

### Advanced Type Hints

```python
from typing import TypeVar, Generic, Protocol, Callable

# Generic types
T = TypeVar('T')

def first_element(items: List[T]) -> Optional[T]:
    return items[0] if items else None

# Protocol (structural subtyping)
class Drawable(Protocol):
    def draw(self) -> None:
        ...

def render(obj: Drawable) -> None:
    obj.draw()

# Callable
def apply_operation(
    items: List[int],
    operation: Callable[[int], int]
) -> List[int]:
    return [operation(item) for item in items]

# TypedDict (Python 3.8+)
from typing import TypedDict

class UserDict(TypedDict):
    id: int
    name: str
    email: str
    age: Optional[int]

def create_user(data: UserDict) -> User:
    return User(**data)
```

### Type Checking

```python
# Use mypy for static type checking
# Install: pip install mypy
# Run: mypy your_script.py

# Example with type errors
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(123)  # mypy will catch this error
```

---

## Error Handling

### Exception Handling

```python
# Bad - bare except
try:
    result = risky_operation()
except:
    print("Error occurred")

# Good - specific exceptions
try:
    result = risky_operation()
except ValueError as e:
    print(f"Invalid value: {e}")
except KeyError as e:
    print(f"Missing key: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    raise  # Re-raise if you can't handle it

# Finally clause
try:
    file = open('data.txt')
    process_file(file)
except IOError as e:
    print(f"File error: {e}")
finally:
    file.close()  # Always executed
```

### Custom Exceptions

```python
# Create custom exception classes
class ValidationError(Exception):
    """Raised when validation fails"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class NotFoundError(Exception):
    """Raised when resource is not found"""
    def __init__(self, resource_type: str, resource_id: int):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            f"{resource_type} with id {resource_id} not found"
        )

# Usage
def validate_user(user_data: dict) -> None:
    if not user_data.get('email'):
        raise ValidationError('email', 'Email is required')

def get_user(user_id: int) -> User:
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise NotFoundError('User', user_id)
    return user
```

---

## When to Load Django Guidance

Load `python-django.md` instead of relying on this file when:

- The code depends on Django models, QuerySets, forms, admin, middleware, or templates
- ORM query shape and N+1 risks are part of the refactor
- Class-based views, serializers, or app structure conventions matter
- The simplification touches request lifecycle, authentication, or transaction boundaries

---

## Python Simplification Checklist

- [ ] Following PEP 8 style guide
- [ ] Using f-strings for string formatting
- [ ] List/dict/set comprehensions where appropriate
- [ ] Context managers for resource management
- [ ] Generators for large datasets
- [ ] Type hints on functions and methods
- [ ] Specific exception handling (not bare except)
- [ ] Custom exception classes for domain errors
- [ ] EAFP over LBYL
- [ ] Enumerate and zip for iteration
- [ ] No nested ternary operators

---

## Additional Resources

- PEP 8 Style Guide: https://pep8.org/
- Python Documentation: https://docs.python.org/3/
- Real Python: https://realpython.com/
- Python Type Checking: https://mypy.readthedocs.io/

**Python Version Recommendation**: Use Python 3.10+ for best
features and performance.
