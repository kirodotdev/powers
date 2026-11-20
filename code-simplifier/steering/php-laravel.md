# Laravel Code Simplification Guide

This guide covers Laravel-specific patterns, conventions,
and best practices for writing elegant, maintainable code.

## Table of Contents

1. [Laravel Conventions](#laravel-conventions)
2. [Eloquent Best Practices](#eloquent-best-practices)
3. [Controller Patterns](#controller-patterns)
4. [Service Layer](#service-layer)
5. [Validation](#validation)
6. [Query Optimization](#query-optimization)
7. [Collections](#collections)
8. [Routing](#routing)

---

## Laravel Conventions

### Directory Structure

Follow Laravel's standard directory structure:

```
app/
├── Http/
│   ├── Controllers/
│   ├── Middleware/
│   ├── Requests/
│   └── Resources/
├── Models/
├── Services/
├── Repositories/
├── Exceptions/
└── Providers/
```

### Naming Conventions

```php
// Controllers - singular, Controller suffix
UserController, OrderController

// Models - singular
User, Order, Product

// Migrations - descriptive
create_users_table, add_status_to_orders_table

// Routes - plural for resources
Route::resource('users', UserController::class);
Route::resource('orders', OrderController::class);

// Database tables - plural, snake_case
users, orders, order_items

// Pivot tables - alphabetical, singular
order_product, role_user
```

---

## Eloquent Best Practices

### Model Organization

```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Order extends Model
{
    use HasFactory;

    // 1. Constants
    public const STATUS_PENDING = 'pending';
    public const STATUS_COMPLETED = 'completed';

    // 2. Properties
    protected $fillable = [
        'user_id',
        'total',
        'status',
    ];

    protected $casts = [
        'total' => 'decimal:2',
        'completed_at' => 'datetime',
    ];

    // 3. Relationships
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }

    // 4. Scopes
    public function scopeCompleted($query)
    {
        return $query->where('status', self::STATUS_COMPLETED);
    }

    public function scopeRecent($query)
    {
        return $query->where('created_at', '>=', now()->subDays(30));
    }

    // 5. Accessors & Mutators
    public function getTotalFormattedAttribute(): string
    {
        return '$' . number_format($this->total, 2);
    }

    // 6. Business Logic Methods
    public function markAsCompleted(): void
    {
        $this->update([
            'status' => self::STATUS_COMPLETED,
            'completed_at' => now(),
        ]);
    }

    public function isCompleted(): bool
    {
        return $this->status === self::STATUS_COMPLETED;
    }
}
```

### Relationship Type Hints

```php
// Always type hint relationships
public function posts(): HasMany
{
    return $this->hasMany(Post::class);
}

public function author(): BelongsTo
{
    return $this->belongsTo(User::class, 'author_id');
}

public function tags(): BelongsToMany
{
    return $this->belongsToMany(Tag::class)
        ->withTimestamps()
        ->withPivot('order');
}
```

### Query Scopes

```php
// Bad - repeating query logic
$activeUsers = User::where('is_active', true)->get();
$activeAdmins = User::where('is_active', true)->where('role', 'admin')->get();

// Good - reusable scopes
class User extends Model
{
    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    public function scopeAdmins($query)
    {
        return $query->where('role', 'admin');
    }
}

$activeUsers = User::active()->get();
$activeAdmins = User::active()->admins()->get();
```

---

## Controller Patterns

### Thin Controllers

```php
// Bad - fat controller
class OrderController extends Controller
{
    public function store(Request $request)
    {
        // Validation
        $validated = $request->validate([
            'items' => 'required|array',
            'items.*.product_id' => 'required|exists:products,id',
            'items.*.quantity' => 'required|integer|min:1',
        ]);

        // Business logic
        $total = 0;
        foreach ($validated['items'] as $item) {
            $product = Product::find($item['product_id']);
            $total += $product->price * $item['quantity'];
        }

        // Create order
        $order = Order::create([
            'user_id' => auth()->id(),
            'total' => $total,
            'status' => 'pending',
        ]);

        // Create order items
        foreach ($validated['items'] as $item) {
            $order->items()->create($item);
        }

        // Send email
        Mail::to($request->user())->send(new OrderConfirmation($order));

        return response()->json($order, 201);
    }
}

// Good - thin controller with Form Request and Service
class OrderController extends Controller
{
    public function __construct(
        private OrderService $orderService
    ) {
    }

    public function store(StoreOrderRequest $request)
    {
        $order = $this->orderService->createOrder(
            user: $request->user(),
            items: $request->validated('items')
        );

        return new OrderResource($order);
    }
}
```

### Form Requests

```php
// Extract validation to Form Request classes
class StoreOrderRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'items' => ['required', 'array', 'min:1'],
            'items.*.product_id' => ['required', 'exists:products,id'],
            'items.*.quantity' => ['required', 'integer', 'min:1', 'max:100'],
        ];
    }

    public function messages(): array
    {
        return [
            'items.*.product_id.exists' => 'One or more products do not exist.',
            'items.*.quantity.max' => 'Maximum quantity per item is 100.',
        ];
    }
}
```

### Resource Classes

```php
// Use API Resources for consistent response formatting
class OrderResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'total' => $this->total_formatted,
            'status' => $this->status,
            'items' => OrderItemResource::collection($this->whenLoaded('items')),
            'user' => new UserResource($this->whenLoaded('user')),
            'created_at' => $this->created_at->toISOString(),
        ];
    }
}
```

---

## Service Layer

### Service Classes

```php
// Create service classes for complex business logic
class OrderService
{
    public function __construct(
        private OrderRepository $orderRepository,
        private ProductRepository $productRepository,
        private NotificationService $notificationService
    ) {
    }

    public function createOrder(User $user, array $items): Order
    {
        $total = $this->calculateTotal($items);

        $order = $this->orderRepository->create([
            'user_id' => $user->id,
            'total' => $total,
            'status' => Order::STATUS_PENDING,
        ]);

        $this->createOrderItems($order, $items);
        $this->notificationService->sendOrderConfirmation($order);

        return $order->load('items');
    }

    private function calculateTotal(array $items): float
    {
        return collect($items)->sum(function ($item) {
            $product = $this->productRepository->find($item['product_id']);
            return $product->price * $item['quantity'];
        });
    }

    private function createOrderItems(Order $order, array $items): void
    {
        foreach ($items as $item) {
            $order->items()->create($item);
        }
    }
}
```

### Repository Pattern (Optional)

```php
// Use repositories for complex queries or when you need to swap implementations
class OrderRepository
{
    public function findWithItems(int $id): ?Order
    {
        return Order::with('items.product')->find($id);
    }

    public function getRecentOrders(User $user, int $days = 30): Collection
    {
        return Order::where('user_id', $user->id)
            ->where('created_at', '>=', now()->subDays($days))
            ->with('items')
            ->latest()
            ->get();
    }

    public function create(array $data): Order
    {
        return Order::create($data);
    }
}
```

---

## Validation

### Custom Validation Rules

```php
// Create custom rule classes for complex validation
class ValidCouponCode implements Rule
{
    public function passes($attribute, $value): bool
    {
        return Coupon::where('code', $value)
            ->where('expires_at', '>', now())
            ->where('is_active', true)
            ->exists();
    }

    public function message(): string
    {
        return 'The coupon code is invalid or expired.';
    }
}

// Usage in Form Request
public function rules(): array
{
    return [
        'coupon_code' => ['nullable', 'string', new ValidCouponCode],
    ];
}
```

### Conditional Validation

```php
// Use conditional validation rules
public function rules(): array
{
    return [
        'payment_method' => ['required', 'in:card,paypal,bank'],
        'card_number' => [
            'required_if:payment_method,card',
            'string',
            'size:16',
        ],
        'paypal_email' => [
            'required_if:payment_method,paypal',
            'email',
        ],
    ];
}
```

---

## Query Optimization

### Eager Loading

```php
// Bad - N+1 query problem
$orders = Order::all();
foreach ($orders as $order) {
    echo $order->user->name; // Queries user for each order
}

// Good - eager loading
$orders = Order::with('user')->get();
foreach ($orders as $order) {
    echo $order->user->name; // No additional queries
}

// Nested eager loading
$orders = Order::with(['user', 'items.product'])->get();

// Conditional eager loading
$orders = Order::with(['user' => function ($query) {
    $query->select('id', 'name', 'email');
}])->get();
```

### Query Optimization

```php
// Bad - loading unnecessary data
$users = User::all();

// Good - select only needed columns
$users = User::select('id', 'name', 'email')->get();

// Use chunk for large datasets
User::chunk(100, function ($users) {
    foreach ($users as $user) {
        // Process user
    }
});

// Use cursor for memory efficiency
foreach (User::cursor() as $user) {
    // Process user with minimal memory usage
}
```

### Avoid Query in Loops

```php
// Bad - query in loop
foreach ($orderIds as $orderId) {
    $order = Order::find($orderId);
    // process order
}

// Good - single query
$orders = Order::whereIn('id', $orderIds)->get();
foreach ($orders as $order) {
    // process order
}
```

---

## Collections

### Collection Methods

```php
// Use Laravel collections for data manipulation

// Bad - manual loops
$activeUsers = [];
foreach ($users as $user) {
    if ($user->is_active) {
        $activeUsers[] = $user;
    }
}

// Good - collection methods
$activeUsers = $users->filter(fn($user) => $user->is_active);

// Chaining collection methods
$result = $orders
    ->filter(fn($order) => $order->isCompleted())
    ->map(fn($order) => [
        'id' => $order->id,
        'total' => $order->total,
    ])
    ->sortByDesc('total')
    ->take(10);

// Grouping
$ordersByStatus = $orders->groupBy('status');

// Plucking
$userIds = $orders->pluck('user_id')->unique();

// Sum and average
$totalRevenue = $orders->sum('total');
$averageOrderValue = $orders->avg('total');
```

### Higher Order Messages

```php
// Use higher order messages for cleaner code
$names = $users->map->name;
$activeUsers = $users->filter->isActive();
$totalSpent = $users->sum->total_spent;
```

---

## Routing

### Route Model Binding

```php
// Bad - manual model lookup
Route::get('/users/{id}', function ($id) {
    $user = User::findOrFail($id);
    return view('users.show', compact('user'));
});

// Good - route model binding
Route::get('/users/{user}', function (User $user) {
    return view('users.show', compact('user'));
});

// Custom key for route model binding
public function getRouteKeyName(): string
{
    return 'slug';
}

// Route: /posts/{post:slug}
Route::get('/posts/{post:slug}', function (Post $post) {
    return view('posts.show', compact('post'));
});
```

### Resource Controllers

```php
// Use resource controllers for RESTful routes
Route::resource('orders', OrderController::class);

// API resource routes (no create/edit)
Route::apiResource('orders', OrderController::class);

// Limit resource routes
Route::resource('orders', OrderController::class)->only(['index', 'show']);
Route::resource('orders', OrderController::class)->except(['destroy']);
```

### Route Groups

```php
// Group related routes
Route::prefix('admin')
    ->middleware(['auth', 'admin'])
    ->name('admin.')
    ->group(function () {
        Route::get('/dashboard', [AdminController::class, 'dashboard'])->name('dashboard');
        Route::resource('users', AdminUserController::class);
    });
```

---

## Laravel Simplification Checklist

- [ ] Controllers are thin (business logic in services)
- [ ] Using Form Requests for validation
- [ ] Using API Resources for response formatting
- [ ] Relationships have return type hints
- [ ] Using query scopes for reusable queries
- [ ] Eager loading to avoid N+1 queries
- [ ] Using collections instead of manual loops
- [ ] Route model binding where applicable
- [ ] Service classes for complex business logic
- [ ] Following Laravel naming conventions
- [ ] Using enums for status/type constants (PHP 8.1+)
- [ ] Proper use of middleware
- [ ] Database transactions for multi-step operations

---

## Additional Resources

- Laravel Documentation: https://laravel.com/docs
- Laravel Best Practices:
  https://github.com/alexeymezenin/laravel-best-practices
- Laracasts: https://laracasts.com

**Laravel Version Recommendation**: Use Laravel 10+ with PHP
8.1+ for best features and support.
