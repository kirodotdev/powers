# Java Code Simplification Guide

This guide covers Java-specific simplification patterns
and best practices for writing clear, modern Java.

## Table of Contents

1. [Java Naming and Style](#java-naming-and-style)
2. [Modern Java Features](#modern-java-features)
3. [Streams, Lambdas, and Optional](#streams-lambdas-and-optional)
4. [Collections](#collections)
5. [Exception Handling](#exception-handling)
6. [Generics](#generics)
7. [Design Patterns](#design-patterns)
8. [Best Practices](#best-practices)

---

## Java Naming and Style

### Naming Conventions

```java
// Classes - PascalCase
public class OrderService {
}

// Interfaces - PascalCase, use adjectives if possible
public interface SerializableReport {
}

// Methods and variables - lowerCamelCase
public int calculateTotal(List<Item> items) {
    return 0;
}

// Constants - UPPER_SNAKE_CASE
public static final int MAX_RETRIES = 3;

// Enums - PascalCase with UPPER_SNAKE_CASE constants
public enum Status {
    PENDING,
    COMPLETED
}
```

### Package and Import Organization

```java
// Packages - lower case, reverse domain
package com.acme.orders.service;

// Standard library imports
import java.time.Instant;
import java.util.List;

// Third-party imports
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

// Local application imports
import com.acme.orders.model.Order;
import com.acme.orders.repository.OrderRepository;
```

### Formatting and Readability

```java
// Bad - long line
Order order = orderService.create(user, items, address, paymentMethod, discountCode, notes);

// Good - break into multiple lines
Order order = orderService.create(
    user,
    items,
    address,
    paymentMethod,
    discountCode,
    notes
);

// Prefer early returns for clarity
public Optional<Order> findActiveOrder(User user) {
    if (user == null) {
        return Optional.empty();
    }
    return orderRepository.findActiveByUserId(user.getId());
}
```

---

## Modern Java Features

### Records (Java 16+)

```java
// Bad - verbose data holder
public final class Address {
    private final String street;
    private final String city;

    public Address(String street, String city) {
        this.street = street;
        this.city = city;
    }

    public String getStreet() { return street; }
    public String getCity() { return city; }
}

// Good - record for simple data
public record Address(String street, String city) {}
```

### Switch Expressions (Java 14+)

```java
// Bad - fall-through switch
int discount;
switch (tier) {
    case GOLD:
        discount = 20;
        break;
    case SILVER:
        discount = 10;
        break;
    default:
        discount = 0;
}

// Good - switch expression
int discount = switch (tier) {
    case GOLD -> 20;
    case SILVER -> 10;
    default -> 0;
};
```

### Text Blocks (Java 15+)

```java
// Bad - hard-to-read string
String json = "{\n" +
    "  \"name\": \"Alice\",\n" +
    "  \"active\": true\n" +
    "}";

// Good - text block
String json = """
    {
      "name": "Alice",
      "active": true
    }
    """;
```

### Sealed Classes (Java 17+)

```java
// Good - sealed hierarchy with explicit variants
public sealed interface Payment permits CardPayment, BankTransfer {}

public record CardPayment(String cardId) implements Payment {}
public record BankTransfer(String iban) implements Payment {}
```

---

## Streams, Lambdas, and Optional

### Streams vs Loops

```java
// Bad - verbose loop
List<String> activeEmails = new ArrayList<>();
for (User user : users) {
    if (user.isActive()) {
        activeEmails.add(user.getEmail().toLowerCase());
    }
}

// Good - stream pipeline
List<String> activeEmails = users.stream()
    .filter(User::isActive)
    .map(User::getEmail)
    .map(String::toLowerCase)
    .toList();
```

### Avoid Overusing Streams

```java
// Bad - stream for simple case
boolean hasAdmin = users.stream()
    .anyMatch(user -> user.getRole() == Role.ADMIN);

// Good - for-each is fine when simple
boolean hasAdmin = false;
for (User user : users) {
    if (user.getRole() == Role.ADMIN) {
        hasAdmin = true;
        break;
    }
}
```

### Optional Usage

```java
// Bad - Optional used as field type
public class UserProfile {
    private Optional<String> nickname;
}

// Good - Optional for return types
public Optional<User> findByEmail(String email) {
    return userRepository.findByEmail(email);
}

// Avoid get() without a fallback
String name = user.findNickname()
    .orElse("Anonymous");

// Map and flatMap
String city = user.findAddress()
    .map(Address::city)
    .orElse("Unknown");
```

### Method References and Lambdas

```java
// Bad - unnecessary lambda
users.forEach(user -> audit.log(user));

// Good - method reference
users.forEach(audit::log);
```

---

## Collections

### Prefer Interfaces

```java
// Bad - concrete type everywhere
ArrayList<Order> orders = new ArrayList<>();

// Good - program to interface
List<Order> orders = new ArrayList<>();
```

### Use Unmodifiable Collections

```java
// Bad - returns mutable list
public List<String> getTags() {
    return tags;
}

// Good - return unmodifiable view or copy
public List<String> getTags() {
    return List.copyOf(tags);
}
```

### Choose the Right Collection

```java
// Bad - using List for lookup
boolean exists = false;
for (String code : codes) {
    if (code.equals(target)) {
        exists = true;
        break;
    }
}

// Good - use Set for lookup
Set<String> codeSet = new HashSet<>(codes);
boolean exists = codeSet.contains(target);
```

### Map Operations

```java
// Bad - manual null checks
Integer count = counts.get(key);
if (count == null) {
    counts.put(key, 1);
} else {
    counts.put(key, count + 1);
}

// Good - use Map helpers
counts.merge(key, 1, Integer::sum);
```

---

## Exception Handling

### Specific Exceptions

```java
// Bad - catching Exception
try {
    process(order);
} catch (Exception e) {
    log.error("Failed", e);
}

// Good - specific exceptions
try {
    process(order);
} catch (ValidationException e) {
    log.warn("Invalid order: {}", e.getMessage());
} catch (IOException e) {
    log.error("I/O error", e);
}
```

### Try-with-Resources

```java
// Bad - manual close
BufferedReader reader = new BufferedReader(new FileReader(path));
try {
    return reader.readLine();
} finally {
    reader.close();
}

// Good - try-with-resources
try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
    return reader.readLine();
}
```

### Custom Exceptions

```java
// Good - domain-specific exception
public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(String orderId) {
        super("Order not found: " + orderId);
    }
}

public Order getOrder(String orderId) {
    return orderRepository.findById(orderId)
        .orElseThrow(() -> new OrderNotFoundException(orderId));
}
```

---

## Generics

### Avoid Raw Types

```java
// Bad - raw types
List items = new ArrayList();
items.add("name");
items.add(42);

// Good - parameterized types
List<String> names = new ArrayList<>();
names.add("Alice");
```

### Bounded Type Parameters

```java
// Bad - too generic
public static <T> T max(T a, T b, Comparator<T> comparator) {
    return comparator.compare(a, b) >= 0 ? a : b;
}

// Good - bounded to Comparable
public static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}
```

### Wildcards

```java
// Bad - overly strict parameter
public void printUsers(List<User> users) {
    users.forEach(System.out::println);
}

// Good - accept subtypes
public void printUsers(List<? extends User> users) {
    users.forEach(System.out::println);
}
```

---

## Design Patterns

### Builder for Complex Objects

```java
// Bad - many constructor params
User user = new User(
    id,
    name,
    email,
    phone,
    address,
    preferences
);

// Good - builder
User user = User.builder()
    .id(id)
    .name(name)
    .email(email)
    .phone(phone)
    .address(address)
    .preferences(preferences)
    .build();
```

### Strategy for Algorithms

```java
// Bad - conditional logic spread around
public int calculateDiscount(Order order) {
    if (order.isVip()) {
        return 20;
    }
    if (order.isEmployee()) {
        return 30;
    }
    return 0;
}

// Good - strategy map
public interface DiscountStrategy {
    int discountFor(Order order);
}

Map<OrderType, DiscountStrategy> strategies = Map.of(
    OrderType.VIP, order -> 20,
    OrderType.EMPLOYEE, order -> 30,
    OrderType.STANDARD, order -> 0
);
```

### Factory for Object Creation

```java
// Bad - scattered new calls
Payment payment = new CardPayment(cardId);

// Good - factory
public final class PaymentFactory {
    public static Payment create(PaymentType type, String ref) {
        return switch (type) {
            case CARD -> new CardPayment(ref);
            case BANK -> new BankTransfer(ref);
        };
    }
}
```

---

## Best Practices

### Prefer Immutability

```java
// Bad - mutable data carrier
public class Money {
    public BigDecimal amount;
    public String currency;
}

// Good - immutable record
public record Money(BigDecimal amount, String currency) {}
```

### Use Dependency Injection

```java
// Bad - hard-coded dependency
public class ReportService {
    private final EmailClient emailClient = new EmailClient();
}

// Good - constructor injection
public class ReportService {
    private final EmailClient emailClient;

    public ReportService(EmailClient emailClient) {
        this.emailClient = emailClient;
    }
}
```

### Keep Methods Small

```java
// Bad - large method doing too much
public void processOrder(Order order) {
    validate(order);
    save(order);
    notifyUser(order);
    updateAnalytics(order);
}

// Good - delegate to focused methods
public void processOrder(Order order) {
    validate(order);
    persist(order);
    notifyUser(order);
    track(order);
}
```

### Avoid Nulls When Possible

```java
// Bad - returning null
public User findUser(String id) {
    return userRepository.findById(id).orElse(null);
}

// Good - Optional return
public Optional<User> findUser(String id) {
    return userRepository.findById(id);
}
```

---

## Java Simplification Checklist

- [ ] Following Java naming conventions and formatting
- [ ] Using records for simple data carriers
- [ ] Switch expressions instead of verbose switch statements
- [ ] Streams for transformations; loops for simple checks
- [ ] Optional used for return types, not fields
- [ ] Prefer interfaces for collections
- [ ] Use List.copyOf/Set.copyOf/Map.copyOf for immutability
- [ ] Specific exceptions and try-with-resources
- [ ] No raw types; generics are bounded when appropriate
- [ ] Prefer builders for complex construction
- [ ] Avoid null returns; use Optional
- [ ] Methods are small and focused

---

## Additional Resources

- Java 17 Documentation: https://docs.oracle.com/en/java/javase/17/
- Java Language Updates: https://openjdk.org/projects/jdk/
- Effective Java (3rd Edition): https://www.oreilly.com/library/view/effective-java/9780134686097/
- Java Streams Guide: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/stream/package-summary.html
- Java Optional: https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Optional.html

**Java Version Recommendation**: Use Java 17+ for best
language features and performance.
