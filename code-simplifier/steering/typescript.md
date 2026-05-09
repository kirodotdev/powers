# TypeScript Code Simplification Guide

This guide covers TypeScript-specific simplification
patterns and best practices for writing type-safe,
maintainable code.

## Table of Contents

1. [TypeScript Style and Conventions](#typescript-style-and-conventions)
2. [Type System](#type-system)
3. [Interfaces vs Types](#interfaces-vs-types)
4. [Generics](#generics)
5. [Utility Types](#utility-types)
6. [Async/Await and Promises](#asyncawait-and-promises)
7. [Modern JavaScript Features](#modern-javascript-features)
8. [React with TypeScript](#react-with-typescript)

---

## TypeScript Style and Conventions

### Naming Conventions

```typescript
// Interfaces and Types - PascalCase
interface User {
	id: number;
	name: string;
}

type UserRole = "admin" | "user" | "guest";

// Classes - PascalCase
class UserService {
	// Private fields - camelCase with # or private keyword
	#repository: UserRepository;

	// Public properties - camelCase
	userName: string;

	// Methods - camelCase
	async getUser(id: number): Promise<User> {
		// implementation
	}
}

// Functions and variables - camelCase
const calculateTotal = (items: Item[]): number => {
	return items.reduce((sum, item) => sum + item.price, 0);
};

// Constants - UPPER_SNAKE_CASE or camelCase
const MAX_RETRIES = 3;
const apiBaseUrl = "https://api.example.com";

// Enums - PascalCase for enum, UPPER_SNAKE_CASE for values
enum OrderStatus {
	PENDING = "PENDING",
	PROCESSING = "PROCESSING",
	COMPLETED = "COMPLETED"
}
```

### File Organization

```typescript
// user.types.ts - Type definitions
export interface User {
	id: number;
	name: string;
	email: string;
}

export type UserRole = "admin" | "user" | "guest";

// user.service.ts - Implementation
import { User, UserRole } from "./user.types";

export class UserService {
	async getUser(id: number): Promise<User> {
		// implementation
	}
}

// index.ts - Barrel export
export * from "./user.types";
export * from "./user.service";
```

---

## Type System

### Type Inference

```typescript
// Bad - unnecessary type annotations
const name: string = "John";
const age: number = 30;
const isActive: boolean = true;

// Good - let TypeScript infer
const name = "John";
const age = 30;
const isActive = true;

// Annotate when needed
const users: User[] = []; // Empty array needs type
const result: Promise<User> = fetchUser(); // Clarify return type
```

### Avoid `any`

```typescript
// Bad - loses type safety
function processData(data: any): any {
	return data.value;
}

// Good - use specific types
function processData(data: { value: string }): string {
	return data.value;
}

// Better - use generics for flexibility
function processData<T extends { value: string }>(
	data: T
): string {
	return data.value;
}

// Use unknown for truly unknown types
function processData(data: unknown): string {
	if (
		typeof data === "object" &&
		data !== null &&
		"value" in data
	) {
		return String((data as { value: unknown }).value);
	}
	throw new Error("Invalid data");
}
```

### Union and Intersection Types

```typescript
// Union types - value can be one of several types
type Status = "pending" | "success" | "error";
type Result = User | Error;

function handleResult(result: Result): void {
	if (result instanceof Error) {
		console.error(result.message);
	} else {
		console.log(result.name);
	}
}

// Intersection types - combine multiple types
type Timestamped = {
	createdAt: Date;
	updatedAt: Date;
};

type User = {
	id: number;
	name: string;
};

type TimestampedUser = User & Timestamped;

const user: TimestampedUser = {
	id: 1,
	name: "John",
	createdAt: new Date(),
	updatedAt: new Date()
};
```

### Type Guards

```typescript
// Type predicate
function isUser(obj: unknown): obj is User {
	return (
		typeof obj === "object" &&
		obj !== null &&
		"id" in obj &&
		"name" in obj
	);
}

// Usage
function processData(data: unknown): void {
	if (isUser(data)) {
		console.log(data.name); // TypeScript knows it's User
	}
}

// Discriminated unions
type Success = { status: "success"; data: User };
type Error = { status: "error"; message: string };
type Result = Success | Error;

function handleResult(result: Result): void {
	if (result.status === "success") {
		console.log(result.data); // TypeScript knows it's Success
	} else {
		console.log(result.message); // TypeScript knows it's Error
	}
}
```

---

## Interfaces vs Types

### When to Use Each

```typescript
// Use interface for object shapes (can be extended)
interface User {
	id: number;
	name: string;
}

// Extend interface
interface AdminUser extends User {
	permissions: string[];
}

// Use type for unions, intersections, primitives
type Status = "pending" | "success" | "error";
type ID = string | number;
type Point = { x: number; y: number };

// Type can do everything interface can (with &)
type User = {
	id: number;
	name: string;
};

type AdminUser = User & {
	permissions: string[];
};
```

### Declaration Merging (Interface Only)

```typescript
// Interfaces can be merged
interface User {
	id: number;
	name: string;
}

interface User {
	email: string;
}

// Merged result
const user: User = {
	id: 1,
	name: "John",
	email: "john@example.com"
};

// Types cannot be merged
type User = { id: number }; // Error if declared again
```

### Recommendation

```typescript
// Use interface for public APIs and object shapes
export interface User {
	id: number;
	name: string;
}

// Use type for complex types, unions, and internal types
type UserRole = "admin" | "user" | "guest";
type Result<T> =
	| { success: true; data: T }
	| { success: false; error: string };
```

---

## Generics

### Generic Functions

```typescript
// Bad - duplicated code
function getFirstString(arr: string[]): string | undefined {
	return arr[0];
}

function getFirstNumber(arr: number[]): number | undefined {
	return arr[0];
}

// Good - generic function
function getFirst<T>(arr: T[]): T | undefined {
	return arr[0];
}

// Usage
const firstString = getFirst(["a", "b", "c"]); // string | undefined
const firstNumber = getFirst([1, 2, 3]); // number | undefined
```

### Generic Constraints

```typescript
// Constrain generic to have certain properties
function getProperty<T, K extends keyof T>(
	obj: T,
	key: K
): T[K] {
	return obj[key];
}

const user = {
	id: 1,
	name: "John",
	email: "john@example.com"
};
const name = getProperty(user, "name"); // string
const id = getProperty(user, "id"); // number

// Constrain to have specific shape
interface HasId {
	id: number;
}

function findById<T extends HasId>(
	items: T[],
	id: number
): T | undefined {
	return items.find((item) => item.id === id);
}
```

### Generic Classes

```typescript
class DataStore<T> {
	private data: T[] = [];

	add(item: T): void {
		this.data.push(item);
	}

	get(index: number): T | undefined {
		return this.data[index];
	}

	filter(predicate: (item: T) => boolean): T[] {
		return this.data.filter(predicate);
	}
}

// Usage
const userStore = new DataStore<User>();
userStore.add({ id: 1, name: "John" });
const user = userStore.get(0); // User | undefined
```

---

## Utility Types

### Built-in Utility Types

```typescript
interface User {
	id: number;
	name: string;
	email: string;
	age: number;
}

// Partial - all properties optional
type PartialUser = Partial<User>;
const update: PartialUser = { name: "John" };

// Required - all properties required
type RequiredUser = Required<Partial<User>>;

// Readonly - all properties readonly
type ReadonlyUser = Readonly<User>;

// Pick - select specific properties
type UserPreview = Pick<User, "id" | "name">;
const preview: UserPreview = { id: 1, name: "John" };

// Omit - exclude specific properties
type UserWithoutEmail = Omit<User, "email">;

// Record - create object type with specific keys
type UserRoles = Record<string, "admin" | "user" | "guest">;
const roles: UserRoles = {
	john: "admin",
	jane: "user"
};

// ReturnType - extract return type of function
function getUser(): User {
	return {
		id: 1,
		name: "John",
		email: "john@example.com",
		age: 30
	};
}
type UserType = ReturnType<typeof getUser>; // User

// Parameters - extract parameter types
function createUser(name: string, age: number): User {
	return { id: 1, name, email: "", age };
}
type CreateUserParams = Parameters<typeof createUser>; // [string, number]
```

### Custom Utility Types

```typescript
// Make specific properties optional
type PartialBy<T, K extends keyof T> = Omit<T, K> &
	Partial<Pick<T, K>>;

type UserWithOptionalEmail = PartialBy<User, "email">;

// Make specific properties required
type RequiredBy<T, K extends keyof T> = Omit<T, K> &
	Required<Pick<T, K>>;

// Deep partial
type DeepPartial<T> = {
	[P in keyof T]?: T[P] extends object
		? DeepPartial<T[P]>
		: T[P];
};

// Non-nullable
type NonNullableFields<T> = {
	[P in keyof T]: NonNullable<T[P]>;
};
```

---

## Async/Await and Promises

### Async Functions

```typescript
// Bad - callback hell
function getUser(
	id: number,
	callback: (user: User) => void
): void {
	fetchUser(id, (user) => {
		fetchOrders(user.id, (orders) => {
			callback({ ...user, orders });
		});
	});
}

// Good - async/await
async function getUser(id: number): Promise<User> {
	const user = await fetchUser(id);
	const orders = await fetchOrders(user.id);
	return { ...user, orders };
}
```

### Error Handling

```typescript
// Bad - unhandled promise rejection
async function getUser(id: number): Promise<User> {
	const response = await fetch(`/api/users/${id}`);
	return response.json();
}

// Good - proper error handling
async function getUser(id: number): Promise<User> {
	try {
		const response = await fetch(`/api/users/${id}`);

		if (!response.ok) {
			throw new Error(
				`HTTP error! status: ${response.status}`
			);
		}

		return await response.json();
	} catch (error) {
		console.error("Failed to fetch user:", error);
		throw error;
	}
}

// Better - typed errors
class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = "ApiError";
	}
}

async function getUser(id: number): Promise<User> {
	const response = await fetch(`/api/users/${id}`);

	if (!response.ok) {
		throw new ApiError(
			response.status,
			`Failed to fetch user ${id}`
		);
	}

	return response.json();
}
```

### Parallel Execution

```typescript
// Bad - sequential
async function loadData(
	userId: number
): Promise<Dashboard> {
	const user = await fetchUser(userId);
	const orders = await fetchOrders(userId);
	const preferences = await fetchPreferences(userId);

	return { user, orders, preferences };
}

// Good - parallel
async function loadData(
	userId: number
): Promise<Dashboard> {
	const [user, orders, preferences] = await Promise.all([
		fetchUser(userId),
		fetchOrders(userId),
		fetchPreferences(userId)
	]);

	return { user, orders, preferences };
}

// With error handling for individual promises
async function loadData(
	userId: number
): Promise<Dashboard> {
	const results = await Promise.allSettled([
		fetchUser(userId),
		fetchOrders(userId),
		fetchPreferences(userId)
	]);

	const [userResult, ordersResult, preferencesResult] =
		results;

	return {
		user:
			userResult.status === "fulfilled"
				? userResult.value
				: null,
		orders:
			ordersResult.status === "fulfilled"
				? ordersResult.value
				: [],
		preferences:
			preferencesResult.status === "fulfilled"
				? preferencesResult.value
				: {}
	};
}
```

---

## Modern JavaScript Features

### Destructuring

```typescript
// Object destructuring
const user = {
	id: 1,
	name: "John",
	email: "john@example.com"
};

// Bad
const id = user.id;
const name = user.name;

// Good
const { id, name } = user;

// With renaming
const { id: userId, name: userName } = user;

// With defaults
const { id, name, age = 0 } = user;

// Array destructuring
const numbers = [1, 2, 3, 4, 5];
const [first, second, ...rest] = numbers;

// Function parameters
function printUser({ id, name }: User): void {
	console.log(`${id}: ${name}`);
}
```

### Spread and Rest

```typescript
// Spread operator
const user = { id: 1, name: "John" };
const updatedUser = { ...user, email: "john@example.com" };

const numbers = [1, 2, 3];
const moreNumbers = [...numbers, 4, 5, 6];

// Rest parameters
function sum(...numbers: number[]): number {
	return numbers.reduce((total, n) => total + n, 0);
}

sum(1, 2, 3, 4, 5); // 15
```

### Optional Chaining and Nullish Coalescing

```typescript
// Optional chaining (?.)
const userName = user?.profile?.name;
const firstOrder = user?.orders?.[0];
const result = user?.getOrders?.();

// Nullish coalescing (??)
const name = user.name ?? "Unknown";
const port = config.port ?? 3000;

// Different from ||
const count = 0;
const value1 = count || 10; // 10 (0 is falsy)
const value2 = count ?? 10; // 0 (0 is not null/undefined)
```

### Template Literals

```typescript
// Bad - string concatenation
const message =
	"Hello, " +
	user.name +
	"! You have " +
	user.orderCount +
	" orders.";

// Good - template literal
const message = `Hello, ${user.name}! You have ${user.orderCount} orders.`;

// Multi-line strings
const html = `
    <div class="user">
        <h1>${user.name}</h1>
        <p>${user.email}</p>
    </div>
`;

// Tagged templates
function sql(
	strings: TemplateStringsArray,
	...values: unknown[]
): string {
	// Custom processing
	return strings.reduce((query, str, i) => {
		return (
			query +
			str +
			(values[i] !== undefined
				? `'${values[i]}'`
				: "")
		);
	}, "");
}

const query = sql`SELECT * FROM users WHERE id = ${userId}`;
```

---

## React with TypeScript

### Component Props

```typescript
// Bad - no types
function Button(props) {
    return <button onClick={props.onClick}>{props.label}</button>;
}

// Good - typed props
interface ButtonProps {
    label: string;
    onClick: () => void;
    disabled?: boolean;
}

function Button({ label, onClick, disabled = false }: ButtonProps) {
    return (
        <button onClick={onClick} disabled={disabled}>
            {label}
        </button>
    );
}

// With children
interface CardProps {
    title: string;
    children: React.ReactNode;
}

function Card({ title, children }: CardProps) {
    return (
        <div className="card">
            <h2>{title}</h2>
            {children}
        </div>
    );
}
```

### Hooks with TypeScript

```typescript
// useState with type inference
const [count, setCount] = useState(0); // number
const [name, setName] = useState(""); // string

// useState with explicit type
const [user, setUser] = useState<User | null>(null);

// useRef
const inputRef = useRef<HTMLInputElement>(null);

// useEffect
useEffect(() => {
	// Effect logic

	return () => {
		// Cleanup
	};
}, [dependency]);

// Custom hook
function useUser(userId: number) {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<Error | null>(null);

	useEffect(() => {
		let cancelled = false;

		async function fetchUser() {
			try {
				const data = await getUser(userId);
				if (!cancelled) {
					setUser(data);
				}
			} catch (err) {
				if (!cancelled) {
					setError(err as Error);
				}
			} finally {
				if (!cancelled) {
					setLoading(false);
				}
			}
		}

		fetchUser();

		return () => {
			cancelled = true;
		};
	}, [userId]);

	return { user, loading, error };
}
```

### Event Handlers

```typescript
// Form events
function LoginForm() {
    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        // Handle form submission
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        console.log(event.target.value);
    };

    return (
        <form onSubmit={handleSubmit}>
            <input type="text" onChange={handleChange} />
            <button type="submit">Submit</button>
        </form>
    );
}

// Mouse events
function Button() {
    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        console.log('Clicked at', event.clientX, event.clientY);
    };

    return <button onClick={handleClick}>Click me</button>;
}
```

---

## TypeScript Simplification Checklist

- [ ] Following TypeScript naming conventions
- [ ] Let TypeScript infer types when obvious
- [ ] Avoid `any`, use `unknown` for truly unknown types
- [ ] Use union and intersection types appropriately
- [ ] Type guards for runtime type checking
- [ ] Prefer interface for object shapes, type for unions
- [ ] Generic functions and classes for reusability
- [ ] Built-in utility types (Partial, Pick, Omit, etc.)
- [ ] Async/await for asynchronous operations
- [ ] Proper error handling in async functions
- [ ] Destructuring for cleaner code
- [ ] Optional chaining and nullish coalescing
- [ ] Template literals for string interpolation
- [ ] Typed React components and hooks
- [ ] No nested ternary operators (use switch or if-else)

---

## Additional Resources

- TypeScript Handbook:
  https://www.typescriptlang.org/docs/handbook/
- TypeScript Deep Dive:
  https://basarat.gitbook.io/typescript/
- React TypeScript Cheatsheet:
  https://react-typescript-cheatsheet.netlify.app/
- Type Challenges:
  https://github.com/type-challenges/type-challenges

**TypeScript Version Recommendation**: Use TypeScript 5.0+
for latest features and performance improvements.
