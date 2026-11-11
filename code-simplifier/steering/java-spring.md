# Spring Boot Code Simplification Guide

This guide covers Spring Boot-specific patterns, conventions,
and best practices for writing clean, maintainable code.

## Table of Contents

1. [Spring Boot Conventions](#spring-boot-conventions)
2. [Dependency Injection](#dependency-injection)
3. [REST Controllers](#rest-controllers)
4. [Service Layer Patterns](#service-layer-patterns)
5. [JPA/Hibernate Best Practices](#jpahibernate-best-practices)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Common Spring Annotations](#common-spring-annotations)

---

## Spring Boot Conventions

### Directory Structure

Keep packages aligned with features and layers:

```
src/main/java/com/example/app
├── Application.java
├── config/
├── controller/
├── service/
├── repository/
├── domain/
├── dto/
└── mapper/
```

### Naming Conventions

```java
// Controllers - resource focused, Controller suffix
OrderController, UserController

// Services - behavior focused, Service suffix
OrderService, BillingService

// Repositories - data access, Repository suffix
OrderRepository, UserRepository

// Entities - singular
Order, User, OrderItem

// DTOs - explicit type role
CreateOrderRequest, OrderResponse, UserSummary
```

---

## Dependency Injection

### Prefer Constructor Injection

```java
// Bad - field injection hides dependencies, hard to test
@Service
public class OrderService {
    @Autowired
    private OrderRepository orderRepository;
}

// Good - constructor injection is explicit and test-friendly
@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

### Use Interfaces for Swappable Implementations

```java
// Good - interface for easy testing/mocking
public interface PaymentGateway {
    PaymentResult charge(PaymentRequest request);
}

@Service
public class StripePaymentGateway implements PaymentGateway {
    @Override
    public PaymentResult charge(PaymentRequest request) {
        return PaymentResult.success();
    }
}
```

---

## REST Controllers

### Thin Controllers

```java
// Bad - fat controller with validation, logic, and persistence
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderRepository orderRepository;

    public OrderController(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    @PostMapping
    public ResponseEntity<Order> create(@RequestBody CreateOrderRequest request) {
        if (request.items() == null || request.items().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }

        Order order = new Order();
        order.setStatus("PENDING");
        order.setTotal(request.items().stream()
            .mapToDouble(i -> i.price() * i.quantity())
            .sum());

        return ResponseEntity.status(HttpStatus.CREATED).body(orderRepository.save(order));
    }
}

// Good - controller delegates to service, validation in DTO
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<OrderResponse> create(
        @Valid @RequestBody CreateOrderRequest request
    ) {
        OrderResponse response = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

### DTOs Over Entities

```java
// Bad - exposing entity directly
@GetMapping("/{id}")
public Order getOrder(@PathVariable Long id) {
    return orderService.getOrderEntity(id);
}

// Good - map to response DTO
@GetMapping("/{id}")
public OrderResponse getOrder(@PathVariable Long id) {
    return orderService.getOrderResponse(id);
}
```

---

## Service Layer Patterns

### Service Composition

```java
// Good - orchestration in service layer
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final PricingService pricingService;
    private final NotificationService notificationService;

    public OrderService(
        OrderRepository orderRepository,
        PricingService pricingService,
        NotificationService notificationService
    ) {
        this.orderRepository = orderRepository;
        this.pricingService = pricingService;
        this.notificationService = notificationService;
    }

    public OrderResponse createOrder(CreateOrderRequest request) {
        Money total = pricingService.calculateTotal(request.items());
        Order order = Order.createPending(total);
        Order saved = orderRepository.save(order);
        notificationService.sendOrderConfirmation(saved);
        return OrderResponse.from(saved);
    }
}
```

### Transactions

```java
// Bad - missing transactional boundary for multi-step updates
public void fulfillOrder(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.markPaid();
    inventoryService.reserve(order.getItems());
    orderRepository.save(order);
}

// Good - transactional boundary around workflow
@Transactional
public void fulfillOrder(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.markPaid();
    inventoryService.reserve(order.getItems());
    orderRepository.save(order);
}
```

---

## JPA/Hibernate Best Practices

### Entity Design

```java
// Good - use immutable identifiers and encapsulate changes
@Entity
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    protected Order() {
    }

    public static Order createPending(Money total) {
        Order order = new Order();
        order.status = OrderStatus.PENDING;
        order.total = total;
        return order;
    }

    public void markPaid() {
        this.status = OrderStatus.PAID;
    }
}
```

### Fetching Strategy

```java
// Bad - N+1 queries due to lazy loading in loops
List<Order> orders = orderRepository.findAll();
for (Order order : orders) {
    order.getItems().size();
}

// Good - fetch required relationships with join fetch
@Query("select o from Order o join fetch o.items where o.id = :id")
Optional<Order> findWithItems(@Param("id") Long id);
```

### Avoid Bidirectional Overuse

```java
// Bad - heavy bidirectional mapping everywhere
@OneToMany(mappedBy = "order")
private List<OrderItem> items = new ArrayList<>();

// Good - use unidirectional where simpler
@OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
@JoinColumn(name = "order_id")
private List<OrderItem> items = new ArrayList<>();
```

### Pagination and Sorting

```java
// Bad - loading all rows into memory
List<Order> orders = orderRepository.findAll();

// Good - use pagination
Page<Order> orders = orderRepository.findAll(PageRequest.of(0, 20, Sort.by("createdAt").descending()));
```

---

## Configuration

### Use Configuration Properties

```java
// Bad - scattered @Value usage
@Value("${billing.currency}")
private String currency;

// Good - strongly typed config
@ConfigurationProperties(prefix = "billing")
public class BillingProperties {
    private String currency;
    private int retryCount;

    public String getCurrency() {
        return currency;
    }

    public void setCurrency(String currency) {
        this.currency = currency;
    }

    public int getRetryCount() {
        return retryCount;
    }

    public void setRetryCount(int retryCount) {
        this.retryCount = retryCount;
    }
}
```

### Profiles

```java
// application.yml
spring:
  profiles:
    active: dev

// application-dev.yml
logging:
  level:
    root: DEBUG
```

---

## Testing

### Slice Tests for Controllers

```java
// Bad - full context for simple controller test
@SpringBootTest
@AutoConfigureMockMvc
class OrderControllerTest {
}

// Good - controller slice test
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;
}
```

### Repository Tests

```java
@DataJpaTest
class OrderRepositoryTest {
    @Autowired
    private OrderRepository orderRepository;
}
```

### Service Tests

```java
// Prefer unit tests with mocks for services
class OrderServiceTest {
    private final OrderRepository orderRepository = mock(OrderRepository.class);
    private final PricingService pricingService = mock(PricingService.class);
    private final NotificationService notificationService = mock(NotificationService.class);
    private final OrderService orderService = new OrderService(
        orderRepository,
        pricingService,
        notificationService
    );
}
```

---

## Common Spring Annotations

```java
@SpringBootApplication // Bootstraps the app
@RestController // REST controller
@RequestMapping // Base path for controller
@GetMapping, @PostMapping, @PutMapping, @DeleteMapping // HTTP methods
@Service // Service layer
@Repository // Data access layer
@Component // Generic component
@Configuration // Configuration class
@Bean // Bean factory method
@Autowired // Dependency injection (prefer constructor)
@Transactional // Transaction boundary
@Valid // Bean validation
@ConfigurationProperties // Typed config
```

---

## Spring Boot Simplification Checklist

- [ ] Controllers are thin and delegate to services
- [ ] Constructor injection used everywhere
- [ ] DTOs used for API requests and responses
- [ ] Transactions wrap multi-step updates
- [ ] JPA queries avoid N+1 problems
- [ ] Pagination for large datasets
- [ ] Configuration properties are typed
- [ ] Tests use slices where appropriate
- [ ] Entities encapsulate state changes
- [ ] Avoid overusing bidirectional mappings

---

## Additional Resources

- Spring Boot Documentation: https://spring.io/projects/spring-boot
- Spring Data JPA Reference: https://spring.io/projects/spring-data-jpa
- Spring Guides: https://spring.io/guides

**Spring Boot Version Recommendation**: Use Spring Boot 3.x
with Java 17+ for modern features and support.
