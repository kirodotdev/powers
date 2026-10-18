# C# Code Simplification Guide

This guide covers C#-specific simplification patterns and
best practices for writing clean, maintainable C# code.

## Table of Contents

1. [C# Style and Conventions](#csharp-style-and-conventions)
2. [LINQ and Collections](#linq-and-collections)
3. [Async/Await](#asyncawait)
4. [Null Safety](#null-safety)
5. [Properties and Expression Bodies](#properties-and-expression-bodies)
6. [Pattern Matching](#pattern-matching)
7. [Error Handling](#error-handling)
8. [Dependency Injection and SOLID](#dependency-injection-and-solid)

---

## C# Style and Conventions

### Naming Conventions

```csharp
// Classes, interfaces, methods - PascalCase
public class UserService
{
    // Interface prefix with 'I'
    private readonly IUserRepository _repository;

    // Private fields - _camelCase with underscore
    private readonly ILogger _logger;

    // Public properties - PascalCase
    public string UserName { get; set; }

    // Local variables and parameters - camelCase
    public void ProcessUser(int userId)
    {
        var userName = GetUserName(userId);
        // ...
    }

    // Constants - PascalCase
    private const int MaxRetries = 3;

    // Async methods - suffix with 'Async'
    public async Task<User> GetUserAsync(int id)
    {
        // ...
    }
}
```

### File Organization

```csharp
// One class per file (generally)
// File name matches class name: UserService.cs

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

// Third-party using statements
using Microsoft.Extensions.Logging;

// Local using statements
using MyApp.Models;
using MyApp.Repositories;

namespace MyApp.Services
{
    public class UserService
    {
        // Fields
        private readonly IUserRepository _repository;

        // Constructor
        public UserService(IUserRepository repository)
        {
            _repository = repository;
        }

        // Methods
        public async Task<User> GetUserAsync(int id)
        {
            // implementation
        }
    }
}
```

---

## LINQ and Collections

### Use LINQ for Collection Operations

```csharp
var numbers = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };

// Bad - manual loop
var evenNumbers = new List<int>();
foreach (var num in numbers)
{
    if (num % 2 == 0)
    {
        evenNumbers.Add(num);
    }
}

// Good - LINQ
var evenNumbers = numbers.Where(n => n % 2 == 0).ToList();

// Method chaining
var result = numbers
    .Where(n => n % 2 == 0)
    .Select(n => n * n)
    .OrderByDescending(n => n)
    .Take(3)
    .ToList();
```

### Query Syntax vs Method Syntax

```csharp
var users = GetUsers();

// Query syntax - good for complex queries with multiple from clauses
var query1 = from user in users
             where user.IsActive
             orderby user.Name
             select user.Email;

// Method syntax - more common and flexible
var query2 = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .Select(u => u.Email);

// Use method syntax for most cases
// Use query syntax when it improves readability (joins, multiple from)
```

### Avoid Multiple Enumeration

```csharp
// Bad - enumerates twice
var activeUsers = users.Where(u => u.IsActive);
var count = activeUsers.Count();
var firstUser = activeUsers.First(); // Enumerates again!

// Good - materialize once
var activeUsers = users.Where(u => u.IsActive).ToList();
var count = activeUsers.Count;
var firstUser = activeUsers.First();

// Or use Any() instead of Count() when checking existence
if (users.Any(u => u.IsActive))
{
    // Better than users.Count(u => u.IsActive) > 0
}
```

### Collection Initializers

```csharp
// Bad - verbose
var list = new List<string>();
list.Add("apple");
list.Add("banana");
list.Add("cherry");

// Good - collection initializer
var list = new List<string> { "apple", "banana", "cherry" };

// Dictionary initializer
var dict = new Dictionary<string, int>
{
    ["apple"] = 1,
    ["banana"] = 2,
    ["cherry"] = 3
};

// Or with Add syntax
var dict = new Dictionary<string, int>
{
    { "apple", 1 },
    { "banana", 2 },
    { "cherry", 3 }
};
```

---

## Async/Await

### Always Use Async/Await for I/O Operations

```csharp
// Bad - blocking call
public User GetUser(int id)
{
    var response = httpClient.GetAsync($"/users/{id}").Result; // Blocks!
    return response.Content.ReadAsAsync<User>().Result;
}

// Good - async all the way
public async Task<User> GetUserAsync(int id)
{
    var response = await httpClient.GetAsync($"/users/{id}");
    return await response.Content.ReadAsAsync<User>();
}
```

### ConfigureAwait for Library Code

```csharp
// In library code (not UI or ASP.NET Core)
public async Task<string> ReadFileAsync(string path)
{
    using var reader = new StreamReader(path);
    return await reader.ReadToEndAsync().ConfigureAwait(false);
}

// In ASP.NET Core and UI code, ConfigureAwait(false) is not needed
public async Task<IActionResult> GetUser(int id)
{
    var user = await _userService.GetUserAsync(id);
    return Ok(user);
}
```

### Parallel Async Operations

```csharp
// Bad - sequential execution
var user = await GetUserAsync(userId);
var orders = await GetOrdersAsync(userId);
var preferences = await GetPreferencesAsync(userId);

// Good - parallel execution
var userTask = GetUserAsync(userId);
var ordersTask = GetOrdersAsync(userId);
var preferencesTask = GetPreferencesAsync(userId);

await Task.WhenAll(userTask, ordersTask, preferencesTask);

var user = userTask.Result;
var orders = ordersTask.Result;
var preferences = preferencesTask.Result;

// Or with tuple deconstruction
var (user, orders, preferences) = await (
    GetUserAsync(userId),
    GetOrdersAsync(userId),
    GetPreferencesAsync(userId)
);
```

### Avoid Async Void

```csharp
// Bad - async void (only for event handlers)
public async void ProcessData()
{
    await DoSomethingAsync();
}

// Good - async Task
public async Task ProcessDataAsync()
{
    await DoSomethingAsync();
}

// Exception: Event handlers must be async void
private async void Button_Click(object sender, EventArgs e)
{
    try
    {
        await ProcessDataAsync();
    }
    catch (Exception ex)
    {
        // Handle exception
    }
}
```

---

## Null Safety

### Nullable Reference Types (C# 8.0+)

```csharp
// Enable in .csproj
// <Nullable>enable</Nullable>

// Non-nullable by default
public class User
{
    public string Name { get; set; } // Warning if not initialized
    public string? MiddleName { get; set; } // Nullable

    public User(string name)
    {
        Name = name; // Must be set
    }
}
```

### Null-Coalescing Operators

```csharp
// Null-coalescing operator (??)
string name = user.Name ?? "Unknown";

// Null-coalescing assignment (??=)
if (cache == null)
{
    cache = new Cache();
}
// Better
cache ??= new Cache();

// Null-conditional operator (?.)
var length = user?.Name?.Length;

// Null-conditional with null-coalescing
var length = user?.Name?.Length ?? 0;
```

### Pattern Matching for Null Checks

```csharp
// Bad - traditional null check
if (user != null && user.IsActive)
{
    ProcessUser(user);
}

// Good - pattern matching (C# 9.0+)
if (user is { IsActive: true })
{
    ProcessUser(user);
}

// Not null pattern
if (user is not null)
{
    ProcessUser(user);
}
```

---

## Properties and Expression Bodies

### Auto-Properties

```csharp
// Bad - unnecessary backing field
private string _name;
public string Name
{
    get { return _name; }
    set { _name = value; }
}

// Good - auto-property
public string Name { get; set; }

// Read-only auto-property
public string Name { get; }

// Init-only property (C# 9.0+)
public string Name { get; init; }

// Property with default value
public int Age { get; set; } = 0;
```

### Expression-Bodied Members

```csharp
// Properties
public string FullName => $"{FirstName} {LastName}";

// Methods
public int Add(int a, int b) => a + b;

// Constructors
public User(string name) => Name = name;

// Finalizers
~User() => Cleanup();

// Indexers
public string this[int index] => _items[index];
```

### Computed Properties

```csharp
public class Order
{
    public List<OrderItem> Items { get; set; }

    // Bad - method for simple calculation
    public decimal GetTotal()
    {
        return Items.Sum(i => i.Price * i.Quantity);
    }

    // Good - computed property
    public decimal Total => Items.Sum(i => i.Price * i.Quantity);

    // With caching if expensive
    private decimal? _cachedTotal;
    public decimal Total
    {
        get
        {
            if (_cachedTotal == null)
            {
                _cachedTotal = Items.Sum(i => i.Price * i.Quantity);
            }
            return _cachedTotal.Value;
        }
    }
}
```

---

## Pattern Matching

### Switch Expressions (C# 8.0+)

```csharp
// Bad - traditional switch
string GetStatusMessage(OrderStatus status)
{
    switch (status)
    {
        case OrderStatus.Pending:
            return "Order is pending";
        case OrderStatus.Processing:
            return "Order is being processed";
        case OrderStatus.Completed:
            return "Order completed";
        case OrderStatus.Cancelled:
            return "Order cancelled";
        default:
            return "Unknown status";
    }
}

// Good - switch expression
string GetStatusMessage(OrderStatus status) => status switch
{
    OrderStatus.Pending => "Order is pending",
    OrderStatus.Processing => "Order is being processed",
    OrderStatus.Completed => "Order completed",
    OrderStatus.Cancelled => "Order cancelled",
    _ => "Unknown status"
};
```

### Type Patterns

```csharp
// Bad - type checking and casting
if (obj is string)
{
    string str = (string)obj;
    Console.WriteLine(str.Length);
}

// Good - pattern matching with declaration
if (obj is string str)
{
    Console.WriteLine(str.Length);
}

// Switch with type patterns
string Describe(object obj) => obj switch
{
    int i => $"Integer: {i}",
    string s => $"String of length {s.Length}",
    User u => $"User: {u.Name}",
    null => "null",
    _ => "Unknown type"
};
```

### Property Patterns

```csharp
// Check properties in patterns
string GetDiscount(User user) => user switch
{
    { IsPremium: true, OrderCount: > 10 } => "20% off",
    { IsPremium: true } => "10% off",
    { OrderCount: > 5 } => "5% off",
    _ => "No discount"
};

// Nested property patterns
string GetShippingCost(Order order) => order switch
{
    { ShippingAddress: { Country: "US" }, Total: > 100 } => "Free",
    { ShippingAddress: { Country: "US" } } => "$10",
    { ShippingAddress: { Country: "CA" } } => "$15",
    _ => "$25"
};
```

### Relational Patterns (C# 9.0+)

```csharp
string GetTemperatureDescription(int temp) => temp switch
{
    < 0 => "Freezing",
    >= 0 and < 10 => "Cold",
    >= 10 and < 20 => "Cool",
    >= 20 and < 30 => "Warm",
    >= 30 => "Hot"
};
```

---

## Error Handling

### Use Specific Exceptions

```csharp
// Bad - generic exception
if (user == null)
{
    throw new Exception("User not found");
}

// Good - specific exception
if (user == null)
{
    throw new ArgumentNullException(nameof(user));
}

// Custom exceptions
public class UserNotFoundException : Exception
{
    public int UserId { get; }

    public UserNotFoundException(int userId)
        : base($"User with ID {userId} not found")
    {
        UserId = userId;
    }
}
```

### Exception Filters

```csharp
// Use when clauses to filter exceptions
try
{
    await ProcessDataAsync();
}
catch (HttpRequestException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
{
    // Handle 404 specifically
}
catch (HttpRequestException ex) when (ex.StatusCode == HttpStatusCode.Unauthorized)
{
    // Handle 401 specifically
}
catch (HttpRequestException ex)
{
    // Handle other HTTP errors
}
```

### Using Statements

```csharp
// Bad - manual disposal
FileStream file = new FileStream("data.txt", FileMode.Open);
try
{
    // Use file
}
finally
{
    file.Dispose();
}

// Good - using statement
using (var file = new FileStream("data.txt", FileMode.Open))
{
    // Use file
} // Automatically disposed

// Better - using declaration (C# 8.0+)
using var file = new FileStream("data.txt", FileMode.Open);
// Use file
// Automatically disposed at end of scope
```

---

## Dependency Injection and SOLID

### Constructor Injection

```csharp
// Bad - tight coupling
public class UserService
{
    private readonly UserRepository _repository = new UserRepository();

    public User GetUser(int id)
    {
        return _repository.GetById(id);
    }
}

// Good - dependency injection
public class UserService
{
    private readonly IUserRepository _repository;

    public UserService(IUserRepository repository)
    {
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
    }

    public User GetUser(int id)
    {
        return _repository.GetById(id);
    }
}
```

### Interface Segregation

```csharp
// Bad - fat interface
public interface IUserService
{
    User GetUser(int id);
    void CreateUser(User user);
    void UpdateUser(User user);
    void DeleteUser(int id);
    List<User> SearchUsers(string query);
    void SendEmail(int userId, string message);
    void GenerateReport(int userId);
}

// Good - segregated interfaces
public interface IUserReader
{
    User GetUser(int id);
    List<User> SearchUsers(string query);
}

public interface IUserWriter
{
    void CreateUser(User user);
    void UpdateUser(User user);
    void DeleteUser(int id);
}

public interface IUserNotifier
{
    void SendEmail(int userId, string message);
}
```

### Single Responsibility

```csharp
// Bad - multiple responsibilities
public class UserService
{
    public void RegisterUser(User user)
    {
        // Validate user
        if (string.IsNullOrEmpty(user.Email))
            throw new ValidationException("Email required");

        // Save to database
        _context.Users.Add(user);
        _context.SaveChanges();

        // Send email
        var smtp = new SmtpClient();
        smtp.Send(new MailMessage("from@example.com", user.Email, "Welcome", "Welcome!"));

        // Log activity
        File.AppendAllText("log.txt", $"User registered: {user.Email}");
    }
}

// Good - separated concerns
public class UserService
{
    private readonly IUserRepository _repository;
    private readonly IUserValidator _validator;
    private readonly IEmailService _emailService;
    private readonly ILogger<UserService> _logger;

    public UserService(
        IUserRepository repository,
        IUserValidator validator,
        IEmailService emailService,
        ILogger<UserService> logger)
    {
        _repository = repository;
        _validator = validator;
        _emailService = emailService;
        _logger = logger;
    }

    public async Task RegisterUserAsync(User user)
    {
        _validator.Validate(user);

        await _repository.AddAsync(user);

        await _emailService.SendWelcomeEmailAsync(user.Email);

        _logger.LogInformation("User registered: {Email}", user.Email);
    }
}
```

---

## C# Simplification Checklist

- [ ] Following C# naming conventions (PascalCase,
      camelCase)
- [ ] Using LINQ for collection operations
- [ ] Async/await for I/O operations
- [ ] Nullable reference types enabled
- [ ] Null-coalescing and null-conditional operators
- [ ] Auto-properties instead of backing fields
- [ ] Expression-bodied members where appropriate
- [ ] Switch expressions over traditional switch
- [ ] Pattern matching for type checks
- [ ] Specific exception types
- [ ] Using statements for IDisposable
- [ ] Constructor injection for dependencies
- [ ] Interface segregation
- [ ] Single responsibility principle
- [ ] No nested ternary operators (use switch expressions)

---

## Additional Resources

- C# Documentation:
  https://docs.microsoft.com/en-us/dotnet/csharp/
- .NET API Browser:
  https://docs.microsoft.com/en-us/dotnet/api/
- C# Coding Conventions:
  https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions
- Dependency Injection in .NET:
  https://docs.microsoft.com/en-us/dotnet/core/extensions/dependency-injection

**C# Version Recommendation**: Use C# 10+ with .NET 6+ for
latest features and performance improvements.
