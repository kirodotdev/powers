# JavaScript Code Simplification Guide

This guide covers JavaScript-focused simplification
patterns and best practices for modern development.
For TypeScript-specific guidance, load `typescript.md`.

## Table of Contents

1. [Modern JavaScript Features](#modern-javascript-features)
2. [When to Load TypeScript Guidance](#when-to-load-typescript-guidance)
3. [Async/Await Patterns](#asyncawait-patterns)
4. [Array and Object Operations](#array-and-object-operations)
5. [Function Patterns](#function-patterns)
6. [Error Handling](#error-handling)
7. [React Patterns](#react-patterns)

---

## Modern JavaScript Features

### Destructuring

```javascript
// Bad - accessing properties repeatedly
function displayUser(user) {
	console.log(user.name);
	console.log(user.email);
	console.log(user.age);
}

// Good - destructuring
function displayUser({ name, email, age }) {
	console.log(name);
	console.log(email);
	console.log(age);
}

// Array destructuring
const [first, second, ...rest] = array;

// Nested destructuring
const {
	user: { name, email }
} = response;

// Default values
const { name = "Anonymous", age = 0 } = user;
```

### Spread and Rest Operators

```javascript
// Object spreading
const defaults = { theme: "light", language: "en" };
const userPrefs = { language: "fr" };
const config = { ...defaults, ...userPrefs };

// Array spreading
const combined = [...array1, ...array2];

// Rest parameters
function sum(...numbers) {
	return numbers.reduce((total, num) => total + num, 0);
}

// Object rest
const { id, ...userData } = user;
```

### Template Literals

```javascript
// Bad - string concatenation
const message =
	"Hello, " +
	user.name +
	"! You have " +
	count +
	" messages.";

// Good - template literals
const message = `Hello, ${user.name}! You have ${count} messages.`;

// Multi-line strings
const html = `
    <div class="user">
        <h2>${user.name}</h2>
        <p>${user.email}</p>
    </div>
`;
```

### Optional Chaining and Nullish Coalescing

```javascript
// Bad - nested null checks
const city = user && user.address && user.address.city;

// Good - optional chaining
const city = user?.address?.city;

// Nullish coalescing
const displayName = user.name ?? "Anonymous";

// Combined
const city = user?.address?.city ?? "Unknown";
```

---

## When to Load TypeScript Guidance

Load `typescript.md` instead of relying on this file when:

- The file being simplified is `.ts` or `.tsx`
- Type design materially affects the refactor
- React props, state, or hooks depend on TypeScript types
- Utility types, generics, discriminated unions, or strict null handling matter

---

## Async/Await Patterns

### Basic Async/Await

```javascript
// Bad - promise chains
function getUser(id) {
	return fetch(`/api/users/${id}`)
		.then((response) => response.json())
		.then((user) => {
			return fetch(`/api/orders/${user.id}`)
				.then((response) => response.json())
				.then((orders) => {
					user.orders = orders;
					return user;
				});
		});
}

// Good - async/await
async function getUser(id) {
	const response = await fetch(`/api/users/${id}`);
	const user = await response.json();

	const ordersResponse = await fetch(
		`/api/orders/${user.id}`
	);
	const orders = await ordersResponse.json();

	return { ...user, orders };
}
```

### Parallel Async Operations

```javascript
// Bad - sequential awaits
async function getData() {
	const users = await fetchUsers();
	const products = await fetchProducts();
	const orders = await fetchOrders();
	return { users, products, orders };
}

// Good - parallel execution
async function getData() {
	const [users, products, orders] = await Promise.all([
		fetchUsers(),
		fetchProducts(),
		fetchOrders()
	]);
	return { users, products, orders };
}

// Promise.allSettled for handling failures
async function getDataSafely() {
	const results = await Promise.allSettled([
		fetchUsers(),
		fetchProducts(),
		fetchOrders()
	]);

	return results.map((result) =>
		result.status === "fulfilled" ? result.value : null
	);
}
```

### Error Handling with Async/Await

```javascript
// Proper error handling
async function fetchUserData(id) {
	try {
		const response = await fetch(`/api/users/${id}`);

		if (!response.ok) {
			throw new Error(
				`HTTP error! status: ${response.status}`
			);
		}

		const data = await response.json();
		return data;
	} catch (error) {
		console.error("Failed to fetch user:", error);
		throw error; // Re-throw or handle appropriately
	}
}

// Wrapper for cleaner error handling
async function safeAsync(fn) {
	try {
		const data = await fn();
		return [null, data];
	} catch (error) {
		return [error, null];
	}
}

// Usage
const [error, user] = await safeAsync(() => fetchUser(id));
if (error) {
	console.error(error);
} else {
	console.log(user);
}
```

---

## Array and Object Operations

### Array Methods

```javascript
// Filter
const activeUsers = users.filter((user) => user.isActive);

// Map
const userNames = users.map((user) => user.name);

// Reduce
const totalPrice = items.reduce(
	(sum, item) => sum + item.price,
	0
);

// Find
const user = users.find((user) => user.id === targetId);

// Some and Every
const hasAdmin = users.some(
	(user) => user.role === "admin"
);
const allActive = users.every((user) => user.isActive);

// Chaining
const result = users
	.filter((user) => user.isActive)
	.map((user) => ({ id: user.id, name: user.name }))
	.sort((a, b) => a.name.localeCompare(b.name));
```

### Object Operations

```javascript
// Object.entries for iteration
Object.entries(user).forEach(([key, value]) => {
	console.log(`${key}: ${value}`);
});

// Object.fromEntries to create object
const userMap = Object.fromEntries(
	users.map((user) => [user.id, user])
);

// Object.keys and Object.values
const keys = Object.keys(user);
const values = Object.values(user);

// Computed property names
const dynamicKey = "email";
const user = {
	name: "John",
	[dynamicKey]: "john@example.com"
};
```

---

## Function Patterns

### Arrow Functions

```javascript
// Use arrow functions for callbacks
const doubled = numbers.map((n) => n * 2);

// Implicit return for single expressions
const getFullName = (user) =>
	`${user.firstName} ${user.lastName}`;

// Explicit return for multiple statements
const processUser = (user) => {
	const fullName = `${user.firstName} ${user.lastName}`;
	const age = calculateAge(user.birthDate);
	return { fullName, age };
};

// When NOT to use arrow functions
class User {
	constructor(name) {
		this.name = name;
	}

	// Bad - arrow function loses 'this' context
	greet = () => {
		console.log(`Hello, ${this.name}`);
	};

	// Good - regular method
	greet() {
		console.log(`Hello, ${this.name}`);
	}
}
```

### Function Composition

```javascript
// Compose functions for reusability
const pipe =
	(...fns) =>
	(x) =>
		fns.reduce((v, f) => f(v), x);

const addTax = (price) => price * 1.2;
const applyDiscount = (price) => price * 0.9;
const formatPrice = (price) => `$${price.toFixed(2)}`;

const calculateFinalPrice = pipe(
	addTax,
	applyDiscount,
	formatPrice
);

const finalPrice = calculateFinalPrice(100); // "$108.00"
```

### Currying

```javascript
// Currying for partial application
const multiply = (a) => (b) => a * b;
const double = multiply(2);
const triple = multiply(3);

console.log(double(5)); // 10
console.log(triple(5)); // 15

// Practical example
const createLogger = (prefix) => (message) => {
	console.log(`[${prefix}] ${message}`);
};

const errorLogger = createLogger("ERROR");
const infoLogger = createLogger("INFO");

errorLogger("Something went wrong"); // [ERROR] Something went wrong
infoLogger("Process completed"); // [INFO] Process completed
```

---

## Error Handling

### Custom Error Classes

```javascript
// Create custom error classes
class ValidationError extends Error {
	constructor(message, field) {
		super(message);
		this.name = "ValidationError";
		this.field = field;
	}
}

class NotFoundError extends Error {
	constructor(message, resourceType, resourceId) {
		super(message);
		this.name = "NotFoundError";
		this.resourceType = resourceType;
		this.resourceId = resourceId;
	}
}

// Usage
function validateUser(user) {
	if (!user.email) {
		throw new ValidationError(
			"Email is required",
			"email"
		);
	}
}

function findUser(id) {
	const user = users.find((u) => u.id === id);
	if (!user) {
		throw new NotFoundError(
			"User not found",
			"User",
			id
		);
	}
	return user;
}
```

### Error Boundaries (React)

```javascript
// Error boundary component
class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <div>Something went wrong: {this.state.error?.message}</div>;
        }

        return this.props.children;
    }
}
```

---

## React Patterns

### Functional Components with Hooks

```javascript
// Bad - class component
class UserProfile extends React.Component {
    state = { user: null, loading: true };

    componentDidMount() {
        this.fetchUser();
    }

    fetchUser = async () => {
        const user = await api.getUser(this.props.userId);
        this.setState({ user, loading: false });
    };

    render() {
        if (this.state.loading) return <div>Loading...</div>;
        return <div>{this.state.user.name}</div>;
    }
}

// Good - functional component with hooks
function UserProfile({ userId }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchUser() {
            const userData = await api.getUser(userId);
            setUser(userData);
            setLoading(false);
        }
        fetchUser();
    }, [userId]);

    if (loading) return <div>Loading...</div>;
    return <div>{user?.name}</div>;
}
```

### Custom Hooks

```javascript
// Extract reusable logic into custom hooks
function useUser(userId) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchUser() {
            try {
                setLoading(true);
                const userData = await api.getUser(userId);
                setUser(userData);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        }
        fetchUser();
    }, [userId]);

    return { user, loading, error };
}

// Usage
function UserProfile({ userId }) {
    const { user, loading, error } = useUser(userId);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    return <div>{user?.name}</div>;
}
```

### Component Composition

```javascript
// Bad - prop drilling
function App() {
    const [user, setUser] = useState(null);
    return <Dashboard user={user} setUser={setUser} />;
}

function Dashboard({ user, setUser }) {
    return <Sidebar user={user} setUser={setUser} />;
}

function Sidebar({ user, setUser }) {
    return <UserMenu user={user} setUser={setUser} />;
}

// Good - Context API
const UserContext = createContext(null);

function App() {
    const [user, setUser] = useState(null);

    return (
        <UserContext.Provider value={{ user, setUser }}>
            <Dashboard />
        </UserContext.Provider>
    );
}

function UserMenu() {
    const context = useContext(UserContext);
    if (!context) throw new Error('UserMenu must be used within UserContext');

    const { user, setUser } = context;
    return <div>{user?.name}</div>;
}
```

---

## JavaScript Simplification Checklist

- [ ] Using modern ES6+ features (destructuring, spread, etc.)
- [ ] Async/await instead of promise chains
- [ ] Arrow functions for callbacks
- [ ] Array methods (map, filter, reduce) instead of loops
- [ ] Optional chaining and nullish coalescing
- [ ] Custom error classes for specific errors
- [ ] Functional components with hooks (React)
- [ ] Custom hooks for reusable logic (React)
- [ ] Proper error handling with try/catch
- [ ] No nested ternary operators
- [ ] Template literals for string interpolation

---

## Additional Resources

- MDN Web Docs:
  https://developer.mozilla.org/en-US/docs/Web/JavaScript
- React Documentation: https://react.dev/
- JavaScript.info: https://javascript.info/

**Recommended Versions**: Node.js 18+, React 18+
