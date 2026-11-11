# Rust Code Simplification Guide

This guide covers Rust-specific simplification patterns and
best practices for writing idiomatic Rust code.

## Table of Contents

1. [Rust Style and Conventions](#rust-style-and-conventions)
2. [Ownership and Borrowing](#ownership-and-borrowing)
3. [Error Handling](#error-handling)
4. [Pattern Matching](#pattern-matching)
5. [Iterators and Functional Patterns](#iterators-and-functional-patterns)
6. [Type System](#type-system)
7. [Traits and Generics](#traits-and-generics)
8. [Concurrency](#concurrency)

---

## Rust Style and Conventions

### Naming Conventions

```rust
// Variables and functions - snake_case
let user_name = "John";
fn calculate_total(items: &[Item]) -> f64 {
    // implementation
}

// Types and traits - PascalCase
struct UserService;
trait Drawable {
    fn draw(&self);
}

// Constants - UPPER_SNAKE_CASE
const MAX_RETRIES: u32 = 3;
const DEFAULT_TIMEOUT: u64 = 30;

// Lifetimes - lowercase single letter
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### Module Organization

```rust
// lib.rs or main.rs
mod models;
mod services;
mod utils;

// Re-export commonly used items
pub use models::{User, Order};
pub use services::UserService;

// Conditional compilation
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_something() {
        // test code
    }
}
```

---

## Ownership and Borrowing

### Prefer Borrowing Over Cloning

```rust
// Bad - unnecessary clone
fn process_data(data: Vec<String>) -> usize {
    data.len()
}

let items = vec!["a".to_string(), "b".to_string()];
let count = process_data(items.clone()); // Expensive clone

// Good - borrow instead
fn process_data(data: &[String]) -> usize {
    data.len()
}

let items = vec!["a".to_string(), "b".to_string()];
let count = process_data(&items); // No clone needed
```

### Use References Appropriately

```rust
// Bad - taking ownership when not needed
fn print_user(user: User) {
    println!("{}", user.name);
} // user is dropped here

// Good - borrow for read-only access
fn print_user(user: &User) {
    println!("{}", user.name);
}

// Mutable borrow when modification is needed
fn update_user(user: &mut User, new_name: String) {
    user.name = new_name;
}
```

### Avoid Unnecessary String Conversions

```rust
// Bad - unnecessary allocations
fn greet(name: String) -> String {
    format!("Hello, {}", name)
}

let greeting = greet("Alice".to_string());

// Good - use string slices
fn greet(name: &str) -> String {
    format!("Hello, {}", name)
}

let greeting = greet("Alice");
```

---

## Error Handling

### Use Result and Option

```rust
// Bad - panic on error
fn parse_number(s: &str) -> i32 {
    s.parse().unwrap() // Panics on invalid input
}

// Good - return Result
fn parse_number(s: &str) -> Result<i32, std::num::ParseIntError> {
    s.parse()
}

// Usage with error propagation
fn process_input(input: &str) -> Result<i32, Box<dyn std::error::Error>> {
    let num = parse_number(input)?; // ? operator propagates error
    Ok(num * 2)
}
```

### Custom Error Types

```rust
use std::fmt;

// Define custom error type
#[derive(Debug)]
enum AppError {
    NotFound(String),
    ValidationError { field: String, message: String },
    DatabaseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::NotFound(resource) =>
                write!(f, "Resource not found: {}", resource),
            AppError::ValidationError { field, message } =>
                write!(f, "Validation error on {}: {}", field, message),
            AppError::DatabaseError(msg) =>
                write!(f, "Database error: {}", msg),
        }
    }
}

impl std::error::Error for AppError {}

// Usage
fn get_user(id: u64) -> Result<User, AppError> {
    if id == 0 {
        return Err(AppError::ValidationError {
            field: "id".to_string(),
            message: "ID cannot be zero".to_string(),
        });
    }
    // ... fetch user
    Ok(user)
}
```

### The ? Operator

```rust
// Bad - nested match statements
fn read_and_parse(path: &str) -> Result<i32, Box<dyn std::error::Error>> {
    match std::fs::read_to_string(path) {
        Ok(contents) => {
            match contents.trim().parse() {
                Ok(num) => Ok(num),
                Err(e) => Err(Box::new(e)),
            }
        }
        Err(e) => Err(Box::new(e)),
    }
}

// Good - use ? operator
fn read_and_parse(path: &str) -> Result<i32, Box<dyn std::error::Error>> {
    let contents = std::fs::read_to_string(path)?;
    let num = contents.trim().parse()?;
    Ok(num)
}
```

---

## Pattern Matching

### Exhaustive Matching

```rust
enum Status {
    Pending,
    Processing,
    Completed,
    Failed(String),
}

// Bad - using if-else chains
fn handle_status(status: Status) {
    if matches!(status, Status::Pending) {
        println!("Pending");
    } else if matches!(status, Status::Processing) {
        println!("Processing");
    }
    // Missing cases!
}

// Good - exhaustive match
fn handle_status(status: Status) {
    match status {
        Status::Pending => println!("Pending"),
        Status::Processing => println!("Processing"),
        Status::Completed => println!("Completed"),
        Status::Failed(reason) => println!("Failed: {}", reason),
    }
}
```

### Match Guards and Patterns

```rust
// Use match guards for complex conditions
fn categorize_number(n: i32) -> &'static str {
    match n {
        n if n < 0 => "negative",
        0 => "zero",
        n if n % 2 == 0 => "positive even",
        _ => "positive odd",
    }
}

// Destructuring in patterns
struct Point { x: i32, y: i32 }

fn describe_point(point: Point) -> String {
    match point {
        Point { x: 0, y: 0 } => "origin".to_string(),
        Point { x: 0, y } => format!("on y-axis at {}", y),
        Point { x, y: 0 } => format!("on x-axis at {}", x),
        Point { x, y } => format!("at ({}, {})", x, y),
    }
}
```

### if let and while let

```rust
// Bad - match with single arm
match some_option {
    Some(value) => println!("Got: {}", value),
    None => {}
}

// Good - if let for single pattern
if let Some(value) = some_option {
    println!("Got: {}", value);
}

// while let for iterating until None
let mut stack = vec![1, 2, 3];
while let Some(top) = stack.pop() {
    println!("{}", top);
}
```

---

## Iterators and Functional Patterns

### Prefer Iterators Over Loops

```rust
// Bad - manual loop
let mut sum = 0;
for i in 0..10 {
    sum += i * i;
}

// Good - iterator chain
let sum: i32 = (0..10).map(|i| i * i).sum();

// Filter and map
let even_squares: Vec<i32> = (0..10)
    .filter(|&x| x % 2 == 0)
    .map(|x| x * x)
    .collect();
```

### Iterator Adapters

```rust
let numbers = vec![1, 2, 3, 4, 5];

// take, skip, enumerate
let first_three: Vec<_> = numbers.iter().take(3).collect();
let skip_two: Vec<_> = numbers.iter().skip(2).collect();

for (index, value) in numbers.iter().enumerate() {
    println!("{}: {}", index, value);
}

// find, any, all
let has_even = numbers.iter().any(|&x| x % 2 == 0);
let all_positive = numbers.iter().all(|&x| x > 0);
let first_even = numbers.iter().find(|&&x| x % 2 == 0);

// fold for custom accumulation
let product = numbers.iter().fold(1, |acc, &x| acc * x);
```

### Avoid Collecting Unnecessarily

```rust
// Bad - unnecessary collect
let sum: i32 = numbers.iter()
    .map(|&x| x * 2)
    .collect::<Vec<_>>()
    .iter()
    .sum();

// Good - chain iterators
let sum: i32 = numbers.iter()
    .map(|&x| x * 2)
    .sum();
```

---

## Type System

### Type Inference

```rust
// Bad - unnecessary type annotations
let x: i32 = 5;
let y: f64 = 3.14;
let name: String = String::from("Alice");

// Good - let compiler infer
let x = 5;
let y = 3.14;
let name = String::from("Alice");

// Annotate when needed for clarity or disambiguation
let numbers: Vec<i32> = vec![]; // Empty vec needs type
let result: Result<_, AppError> = parse_data(); // Specify error type
```

### Newtype Pattern

```rust
// Bad - primitive obsession
fn transfer_money(from: u64, to: u64, amount: f64) {
    // Easy to mix up parameters
}

// Good - newtype pattern
struct UserId(u64);
struct Amount(f64);

fn transfer_money(from: UserId, to: UserId, amount: Amount) {
    // Type safety prevents mistakes
}
```

### Type Aliases

```rust
// Simplify complex types
type Result<T> = std::result::Result<T, AppError>;
type UserId = u64;
type UserMap = std::collections::HashMap<UserId, User>;

// Usage
fn get_user(id: UserId) -> Result<User> {
    // implementation
}
```

---

## Traits and Generics

### Implement Standard Traits

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct User {
    id: u64,
    name: String,
    email: String,
}

// Implement Display for user-friendly output
impl std::fmt::Display for User {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{} ({})", self.name, self.email)
    }
}

// Implement From for conversions
impl From<(u64, String, String)> for User {
    fn from((id, name, email): (u64, String, String)) -> Self {
        User { id, name, email }
    }
}
```

### Generic Functions and Trait Bounds

```rust
// Bad - concrete types
fn print_vec_i32(v: &Vec<i32>) {
    for item in v {
        println!("{}", item);
    }
}

// Good - generic with trait bounds
fn print_vec<T: std::fmt::Display>(v: &[T]) {
    for item in v {
        println!("{}", item);
    }
}

// Multiple trait bounds
fn process<T>(item: T) -> String
where
    T: std::fmt::Display + std::fmt::Debug + Clone,
{
    format!("{} - {:?}", item, item.clone())
}
```

### Trait Objects vs Generics

```rust
// Static dispatch (generics) - faster, larger binary
fn process_static<T: Processor>(processor: T, data: &str) {
    processor.process(data);
}

// Dynamic dispatch (trait objects) - smaller binary, runtime cost
fn process_dynamic(processor: &dyn Processor, data: &str) {
    processor.process(data);
}

// Use generics when performance matters
// Use trait objects when you need heterogeneous collections
let processors: Vec<Box<dyn Processor>> = vec![
    Box::new(JsonProcessor),
    Box::new(XmlProcessor),
];
```

---

## Concurrency

### Use Channels for Communication

```rust
use std::sync::mpsc;
use std::thread;

// Create channel
let (tx, rx) = mpsc::channel();

// Spawn thread
thread::spawn(move || {
    let result = expensive_computation();
    tx.send(result).unwrap();
});

// Receive result
let result = rx.recv().unwrap();
```

### Shared State with Arc and Mutex

```rust
use std::sync::{Arc, Mutex};
use std::thread;

// Bad - trying to share mutable state
let counter = 0;
let handle = thread::spawn(|| {
    counter += 1; // Error: can't capture mutable reference
});

// Good - Arc<Mutex<T>> for shared mutable state
let counter = Arc::new(Mutex::new(0));
let counter_clone = Arc::clone(&counter);

let handle = thread::spawn(move || {
    let mut num = counter_clone.lock().unwrap();
    *num += 1;
});

handle.join().unwrap();
println!("Result: {}", *counter.lock().unwrap());
```

### Async/Await

```rust
use tokio;

// Async function
async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    Ok(body)
}

// Concurrent execution
#[tokio::main]
async fn main() {
    let urls = vec![
        "https://api.example.com/1",
        "https://api.example.com/2",
        "https://api.example.com/3",
    ];

    // Execute concurrently
    let futures: Vec<_> = urls.iter()
        .map(|url| fetch_data(url))
        .collect();

    let results = futures::future::join_all(futures).await;
}
```

---

## Rust Simplification Checklist

- [ ] Following Rust naming conventions (snake_case,
      PascalCase)
- [ ] Prefer borrowing over cloning
- [ ] Use Result and Option instead of panicking
- [ ] Exhaustive pattern matching
- [ ] Iterator chains over manual loops
- [ ] Derive standard traits (Debug, Clone, etc.)
- [ ] Use ? operator for error propagation
- [ ] Appropriate use of lifetimes
- [ ] Generic functions with trait bounds
- [ ] Arc<Mutex<T>> for shared mutable state
- [ ] Async/await for concurrent operations
- [ ] No nested ternary operators (use match instead)

---

## Additional Resources

- The Rust Book: https://doc.rust-lang.org/book/
- Rust by Example:
  https://doc.rust-lang.org/rust-by-example/
- Rust API Guidelines:
  https://rust-lang.github.io/api-guidelines/
- Clippy Lints: https://rust-lang.github.io/rust-clippy/
- Tokio Documentation: https://tokio.rs/

**Rust Version Recommendation**: Use the latest stable
version for best features and tooling.
