# PHP Code Simplification Guide

This guide covers PHP-specific simplification patterns and
best practices following PSR standards.

## Table of Contents

1. [PHP Standards](#php-standards)
2. [Type Declarations](#type-declarations)
3. [Modern PHP Features](#modern-php-features)
4. [Error Handling](#error-handling)
5. [Array Operations](#array-operations)
6. [String Operations](#string-operations)
7. [Object-Oriented Patterns](#object-oriented-patterns)

---

## PHP Standards

### PSR-12 Compliance

Follow PSR-12 coding style standard:

```php
<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\User;
use App\Exceptions\ValidationException;

class UserService
{
    public function __construct(
        private UserRepository $repository,
        private EmailService $emailService
    ) {
    }

    public function createUser(array $data): User
    {
        // Method body
    }
}
```

### Namespace and Imports

**Guidelines**:

- Always use `declare(strict_types=1)` at the top
- Organize imports alphabetically
- Group imports by type (classes, functions, constants)
- Remove unused imports

```php
// Bad
use App\Models\User;
use Illuminate\Support\Facades\DB;
use App\Services\EmailService;
use function App\Helpers\format_date;

// Good
use App\Models\User;
use App\Services\EmailService;
use Illuminate\Support\Facades\DB;

use function App\Helpers\format_date;
```

---

## Type Declarations

### Return Types

**Always declare return types explicitly**:

```php
// Bad
public function getUser($id)
{
    return User::find($id);
}

// Good
public function getUser(int $id): ?User
{
    return User::find($id);
}
```

### Parameter Types

**Use type hints for all parameters**:

```php
// Bad
public function sendEmail($user, $subject, $body)
{
    // ...
}

// Good
public function sendEmail(User $user, string $subject, string $body): void
{
    // ...
}
```

### Union Types (PHP 8.0+)

```php
// Use union types when appropriate
public function process(int|float $value): string
{
    return number_format($value, 2);
}

public function find(int|string $identifier): ?User
{
    return is_int($identifier)
        ? User::find($identifier)
        : User::where('email', $identifier)->first();
}
```

---

## Modern PHP Features

### Constructor Property Promotion (PHP 8.0+)

```php
// Bad - verbose
class UserService
{
    private UserRepository $repository;
    private EmailService $emailService;

    public function __construct(UserRepository $repository, EmailService $emailService)
    {
        $this->repository = $repository;
        $this->emailService = $emailService;
    }
}

// Good - promoted properties
class UserService
{
    public function __construct(
        private UserRepository $repository,
        private EmailService $emailService
    ) {
    }
}
```

### Match Expression (PHP 8.0+)

```php
// Bad - switch statement
switch ($status) {
    case 'pending':
        $message = 'Order is pending';
        break;
    case 'processing':
        $message = 'Order is being processed';
        break;
    case 'completed':
        $message = 'Order is completed';
        break;
    default:
        $message = 'Unknown status';
}

// Good - match expression
$message = match ($status) {
    'pending' => 'Order is pending',
    'processing' => 'Order is being processed',
    'completed' => 'Order is completed',
    default => 'Unknown status',
};
```

### Nullsafe Operator (PHP 8.0+)

```php
// Bad - nested null checks
$country = null;
if ($user !== null) {
    if ($user->getAddress() !== null) {
        $country = $user->getAddress()->getCountry();
    }
}

// Good - nullsafe operator
$country = $user?->getAddress()?->getCountry();
```

### Named Arguments (PHP 8.0+)

```php
// Use named arguments for clarity with many parameters
public function createUser(
    string $name,
    string $email,
    bool $isActive = true,
    bool $isVerified = false,
    ?string $phone = null
): User {
    // ...
}

// Bad - unclear what parameters mean
$user = $this->createUser('John', 'john@example.com', true, false, null);

// Good - named arguments make intent clear
$user = $this->createUser(
    name: 'John',
    email: 'john@example.com',
    isActive: true,
    isVerified: false
);
```

---

## Error Handling

### Use Exceptions, Not Error Codes

```php
// Bad - error codes
public function processPayment($amount)
{
    if ($amount <= 0) {
        return ['error' => true, 'code' => 'INVALID_AMOUNT'];
    }

    if (!$this->hasBalance($amount)) {
        return ['error' => true, 'code' => 'INSUFFICIENT_FUNDS'];
    }

    return ['error' => false, 'data' => $this->charge($amount)];
}

// Good - exceptions
public function processPayment(float $amount): Payment
{
    if ($amount <= 0) {
        throw new InvalidAmountException('Amount must be positive');
    }

    if (!$this->hasBalance($amount)) {
        throw new InsufficientFundsException('Insufficient balance');
    }

    return $this->charge($amount);
}
```

### Custom Exception Classes

```php
// Create specific exception classes
namespace App\Exceptions;

class InvalidAmountException extends \InvalidArgumentException
{
}

class InsufficientFundsException extends \RuntimeException
{
}

class PaymentProcessingException extends \RuntimeException
{
}
```

### Try-Catch Blocks

```php
// Bad - catching generic Exception
try {
    $payment = $this->processPayment($amount);
} catch (\Exception $e) {
    return 'Error occurred';
}

// Good - catch specific exceptions
try {
    $payment = $this->processPayment($amount);
} catch (InvalidAmountException $e) {
    return 'Invalid payment amount';
} catch (InsufficientFundsException $e) {
    return 'Insufficient funds';
} catch (PaymentProcessingException $e) {
    Log::error('Payment processing failed', ['exception' => $e]);
    return 'Payment processing failed';
}
```

---

## Array Operations

### Array Functions

```php
// Use array functions instead of loops when appropriate

// Bad - manual loop
$activeUsers = [];
foreach ($users as $user) {
    if ($user->isActive()) {
        $activeUsers[] = $user;
    }
}

// Good - array_filter
$activeUsers = array_filter($users, fn($user) => $user->isActive());

// Bad - manual loop for transformation
$userNames = [];
foreach ($users as $user) {
    $userNames[] = $user->getName();
}

// Good - array_map
$userNames = array_map(fn($user) => $user->getName(), $users);
```

### Array Destructuring

```php
// Use array destructuring for clarity
[$firstName, $lastName] = explode(' ', $fullName, 2);

// With associative arrays
['name' => $name, 'email' => $email] = $userData;
```

### Spread Operator

```php
// Use spread operator for array merging
$defaults = ['color' => 'blue', 'size' => 'medium'];
$custom = ['size' => 'large'];

// Bad
$config = array_merge($defaults, $custom);

// Good
$config = [...$defaults, ...$custom];
```

---

## String Operations

### String Interpolation

```php
// Bad - concatenation
$message = 'Hello, ' . $user->getName() . '! Your balance is ' . $user->getBalance();

// Good - interpolation
$message = "Hello, {$user->getName()}! Your balance is {$user->getBalance()}";

// For simple variables
$message = "Hello, $name!";
```

### Heredoc and Nowdoc

```php
// Use heredoc for multi-line strings with interpolation
$email = <<<HTML
<html>
    <body>
        <h1>Hello, {$user->getName()}</h1>
        <p>Your order #{$order->getId()} has been confirmed.</p>
    </body>
</html>
HTML;

// Use nowdoc (single quotes) when no interpolation needed
$sql = <<<'SQL'
SELECT * FROM users
WHERE status = 'active'
AND created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
SQL;
```

---

## Object-Oriented Patterns

### Readonly Properties (PHP 8.1+)

```php
// Use readonly for immutable properties
class User
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        private string $password
    ) {
    }
}
```

### Enums (PHP 8.1+)

```php
// Bad - class constants
class OrderStatus
{
    public const PENDING = 'pending';
    public const PROCESSING = 'processing';
    public const COMPLETED = 'completed';
    public const CANCELLED = 'cancelled';
}

// Good - enum
enum OrderStatus: string
{
    case PENDING = 'pending';
    case PROCESSING = 'processing';
    case COMPLETED = 'completed';
    case CANCELLED = 'cancelled';

    public function label(): string
    {
        return match($this) {
            self::PENDING => 'Pending',
            self::PROCESSING => 'Processing',
            self::COMPLETED => 'Completed',
            self::CANCELLED => 'Cancelled',
        };
    }
}
```

### Interface Segregation

```php
// Bad - fat interface
interface UserServiceInterface
{
    public function create(array $data): User;
    public function update(int $id, array $data): User;
    public function delete(int $id): void;
    public function sendWelcomeEmail(User $user): void;
    public function sendPasswordReset(User $user): void;
    public function generateReport(): array;
}

// Good - segregated interfaces
interface UserRepositoryInterface
{
    public function create(array $data): User;
    public function update(int $id, array $data): User;
    public function delete(int $id): void;
}

interface UserNotificationInterface
{
    public function sendWelcomeEmail(User $user): void;
    public function sendPasswordReset(User $user): void;
}

interface UserReportInterface
{
    public function generateReport(): array;
}
```

### Dependency Injection

```php
// Bad - hard-coded dependencies
class OrderService
{
    public function createOrder(array $data): Order
    {
        $repository = new OrderRepository();
        $emailService = new EmailService();

        $order = $repository->create($data);
        $emailService->sendConfirmation($order);

        return $order;
    }
}

// Good - injected dependencies
class OrderService
{
    public function __construct(
        private OrderRepository $repository,
        private EmailService $emailService
    ) {
    }

    public function createOrder(array $data): Order
    {
        $order = $this->repository->create($data);
        $this->emailService->sendConfirmation($order);

        return $order;
    }
}
```

---

## PHP Simplification Checklist

- [ ] `declare(strict_types=1)` at the top of files
- [ ] All functions have explicit return types
- [ ] All parameters have type hints
- [ ] Using constructor property promotion where applicable
- [ ] Using match expressions instead of switch when
      appropriate
- [ ] Using nullsafe operator for chained null checks
- [ ] Using exceptions instead of error codes
- [ ] Using array functions (map, filter, reduce)
      appropriately
- [ ] Using modern PHP features (8.0+) when available
- [ ] Following PSR-12 coding standards
- [ ] Proper namespace organization
- [ ] No unused imports

---

**PHP Version Recommendation**: Use PHP 8.1+ for best modern
features and performance.
