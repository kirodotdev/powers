# Core Code Simplification Principles

This guide covers universal code simplification principles
that apply across all programming languages and frameworks.

## Table of Contents

1. [Fundamental Principles](#fundamental-principles)
2. [Complexity Reduction](#complexity-reduction)
3. [Naming Conventions](#naming-conventions)
4. [Code Organization](#code-organization)
5. [Comments and Documentation](#comments-and-documentation)
6. [Common Patterns](#common-patterns)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Fundamental Principles

### Preserve Functionality

**Rule**: Never change what the code does, only how it does
it.

**Guidelines**:

- All inputs should produce the same outputs
- Side effects must remain identical
- Error handling behavior should be preserved
- Performance characteristics should not degrade
  significantly

**Verification**:

- Run existing tests after refactoring
- Manually test edge cases
- Review behavior with original author if uncertain

### Clarity Over Brevity

**Rule**: Explicit code is better than compact code.

**Examples**:

```javascript
// Bad - too compact, hard to understand
const r = d
	.filter((x) => x.a && x.b > 10)
	.map((x) => ({ ...x, c: x.a * 2 }));

// Good - clear and explicit
const activeItems = data.filter(
	(item) => item.isActive && item.value > 10
);
const enrichedItems = activeItems.map((item) => ({
	...item,
	calculatedValue: item.amount * 2
}));
```

### Single Responsibility

**Rule**: Each function/method should do one thing well.

**Guidelines**:

- If a function name contains "and", it might be doing too
  much
- Functions should be easy to name descriptively
- Aim for functions that fit on one screen

**Example**:

```python
# Bad - doing too much
def process_user_data(user):
    # Validate
    if not user.email:
        raise ValueError("Email required")
    # Transform
    user.email = user.email.lower()
    # Save
    db.save(user)
    # Send email
    send_welcome_email(user)
    return user

# Good - separated concerns
def validate_user(user):
    if not user.email:
        raise ValueError("Email required")

def normalize_user_email(user):
    user.email = user.email.lower()
    return user

def save_user(user):
    return db.save(user)

def process_new_user(user):
    validate_user(user)
    normalized_user = normalize_user_email(user)
    saved_user = save_user(normalized_user)
    send_welcome_email(saved_user)
    return saved_user
```

---

## Complexity Reduction

### Reduce Nesting

**Problem**: Deep nesting makes code hard to follow.

**Solution**: Use early returns (guard clauses).

```javascript
// Bad - deep nesting
function processOrder(order) {
	if (order) {
		if (order.items.length > 0) {
			if (order.customer) {
				if (order.customer.isVerified) {
					// process order
					return processPayment(order);
				}
			}
		}
	}
	return null;
}

// Good - early returns
function processOrder(order) {
	if (!order) return null;
	if (order.items.length === 0) return null;
	if (!order.customer) return null;
	if (!order.customer.isVerified) return null;

	return processPayment(order);
}
```

### Eliminate Redundancy

**Problem**: Duplicated code increases maintenance burden.

**Solution**: Extract common logic into reusable functions.

```python
# Bad - duplicated logic
def get_active_users():
    users = db.query(User).all()
    return [u for u in users if u.is_active and not u.is_deleted]

def get_active_admins():
    users = db.query(User).all()
    return [u for u in users if u.is_active and not u.is_deleted and u.is_admin]

# Good - extracted common logic
def get_active_users_base():
    users = db.query(User).all()
    return [u for u in users if u.is_active and not u.is_deleted]

def get_active_users():
    return get_active_users_base()

def get_active_admins():
    return [u for u in get_active_users_base() if u.is_admin]
```

### Avoid Nested Ternaries

**Problem**: Nested ternary operators are extremely hard to
read.

**Solution**: Use explicit conditionals, match expressions,
or switch statements.

```javascript
// Bad - nested ternary
const price = isPremium
	? isAnnual
		? 99
		: isMember
			? 15
			: 20
	: isAnnual
		? 120
		: 25;

// Good - explicit if/else
let price;
if (isPremium) {
	if (isAnnual) {
		price = 99;
	} else if (isMember) {
		price = 15;
	} else {
		price = 20;
	}
} else {
	price = isAnnual ? 120 : 25;
}

// Better - object lookup or switch
const pricingMatrix = {
	"premium-annual": 99,
	"premium-member": 15,
	"premium-regular": 20,
	"standard-annual": 120,
	"standard-regular": 25
};

const tier = isPremium ? "premium" : "standard";
const type =
	isPremium && isAnnual
		? "annual"
		: isPremium && isMember
			? "member"
			: isAnnual
				? "annual"
				: "regular";
const price = pricingMatrix[`${tier}-${type}`];
```

---

## Naming Conventions

### Variables and Functions

**Guidelines**:

- Use descriptive names that reveal intent
- Avoid abbreviations unless universally understood
- Use verbs for functions, nouns for variables
- Boolean variables should read like questions

```python
# Bad
def calc(a, b):
    return a * b * 0.2

usr = get_usr()
flg = True

# Good
def calculate_discount(price, quantity):
    DISCOUNT_RATE = 0.2
    return price * quantity * DISCOUNT_RATE

current_user = get_current_user()
is_email_verified = True
```

### Constants

**Guidelines**:

- Use UPPER_SNAKE_CASE for true constants
- Group related constants together
- Consider using enums for related constant sets

```javascript
// Bad
const x = 86400;
const y = 7;

// Good
const SECONDS_PER_DAY = 86400;
const DAYS_PER_WEEK = 7;
const SECONDS_PER_WEEK = SECONDS_PER_DAY * DAYS_PER_WEEK;
```

### Classes and Types

**Guidelines**:

- Use PascalCase for class names
- Names should be nouns or noun phrases
- Avoid generic names like "Manager", "Helper", "Utility"

```python
# Bad
class data_processor:
    pass

class Helper:
    pass

# Good
class OrderProcessor:
    pass

class EmailValidator:
    pass
```

---

## Code Organization

### Function Length

**Guideline**: Functions should be short and focused.

**Rules of Thumb**:

- Aim for functions under 20-30 lines
- If you need to scroll, consider splitting
- Each function should do one thing at one level of
  abstraction

### File Organization

**Guidelines**:

- Group related functionality together
- Keep files focused on a single concern
- Use clear directory structure

```
# Good structure
src/
  users/
    user-service.js
    user-repository.js
    user-validator.js
  orders/
    order-service.js
    order-repository.js
    order-validator.js
```

### Dependency Management

**Guidelines**:

- Minimize dependencies between modules
- Depend on abstractions, not concretions
- Avoid circular dependencies

---

## Comments and Documentation

### When to Comment

**Do comment**:

- Why something is done (not what or how)
- Complex algorithms or business logic
- Workarounds for bugs or limitations
- Public APIs and interfaces

**Don't comment**:

- Obvious code that explains itself
- What the code does (the code should show this)
- Commented-out code (use version control instead)

```javascript
// Bad - obvious comment
// Increment counter by 1
counter++;

// Get user by ID
const user = getUserById(id);

// Good - explains why
// Use exponential backoff to avoid overwhelming the API
// during high-traffic periods
await retryWithBackoff(apiCall, { maxRetries: 5 });

// Cache results for 5 minutes to reduce database load
// while keeping data reasonably fresh for users
const cachedResult = cache.get(key, { ttl: 300 });
```

### Self-Documenting Code

**Prefer code that explains itself**:

```python
# Bad - needs comments
# Check if user can access resource
if u.r == 'admin' or (u.r == 'user' and r.o == u.id):
    # allow access
    pass

# Good - self-documenting
def user_can_access_resource(user, resource):
    is_admin = user.role == 'admin'
    is_owner = user.role == 'user' and resource.owner_id == user.id
    return is_admin or is_owner

if user_can_access_resource(current_user, requested_resource):
    # grant access
    pass
```

---

## Common Patterns

### Replace Magic Numbers

```javascript
// Bad
if (user.age >= 18 && user.age < 65) {
	applyDiscount(0.15);
}

// Good
const ADULT_AGE = 18;
const SENIOR_AGE = 65;
const STANDARD_DISCOUNT = 0.15;

if (user.age >= ADULT_AGE && user.age < SENIOR_AGE) {
	applyDiscount(STANDARD_DISCOUNT);
}
```

### Extract Complex Conditions

```python
# Bad
if (user.subscription_type == 'premium' and user.payment_status == 'current'
    and user.account_age_days > 30 and not user.has_violations):
    grant_feature_access()

# Good
def user_qualifies_for_premium_features(user):
    has_premium_subscription = user.subscription_type == 'premium'
    payment_is_current = user.payment_status == 'current'
    account_is_established = user.account_age_days > 30
    has_good_standing = not user.has_violations

    return (has_premium_subscription and payment_is_current
            and account_is_established and has_good_standing)

if user_qualifies_for_premium_features(user):
    grant_feature_access()
```

### Use Data Structures

```javascript
// Bad - long if/else chain
function getShippingCost(country) {
	if (country === "US") return 5;
	if (country === "CA") return 7;
	if (country === "UK") return 10;
	if (country === "AU") return 12;
	return 15;
}

// Good - data structure
const SHIPPING_COSTS = {
	US: 5,
	CA: 7,
	UK: 10,
	AU: 12,
	DEFAULT: 15
};

function getShippingCost(country) {
	return (
		SHIPPING_COSTS[country] || SHIPPING_COSTS.DEFAULT
	);
}
```

---

## Anti-Patterns to Avoid

### Premature Optimization

**Problem**: Optimizing before you know where the
bottlenecks are.

**Solution**: Write clear code first, optimize only when
profiling shows a need.

### Over-Engineering

**Problem**: Adding complexity for hypothetical future
needs.

**Solution**: Implement what you need now. YAGNI (You Aren't
Gonna Need It).

### God Objects

**Problem**: Classes or modules that know too much or do too
much.

**Solution**: Split responsibilities into focused, cohesive
units.

### Clever Code

**Problem**: Code that's hard to understand because it's too
"clever".

**Solution**: Prefer straightforward solutions over clever
tricks.

```python
# Bad - too clever
result = [x for x in (y for y in data if y) if x % 2]

# Good - clear and explicit
non_empty_items = [item for item in data if item]
odd_numbers = [num for num in non_empty_items if num % 2 != 0]
```

### Inconsistent Style

**Problem**: Mixing different coding styles in the same
codebase.

**Solution**: Follow a consistent style guide and use
automated formatters.

---

## Simplification Checklist

Before considering your simplification complete, verify:

- [ ] Functionality is preserved (all tests pass)
- [ ] Code is more readable than before
- [ ] Nesting depth is reduced where possible
- [ ] Variable and function names are clear
- [ ] Redundant code is eliminated
- [ ] Complex conditions are extracted
- [ ] Magic numbers are replaced with named constants
- [ ] Comments explain "why", not "what"
- [ ] Code follows consistent style
- [ ] No over-simplification that reduces clarity

---

**Remember**: The goal is maintainable code that's easy to
understand, not the shortest possible code.
