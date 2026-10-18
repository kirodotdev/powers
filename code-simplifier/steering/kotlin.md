# Kotlin Code Simplification Guide

This guide covers Kotlin-specific simplification patterns and
best practices for writing idiomatic Kotlin code.

## Table of Contents

1. [Kotlin Style and Conventions](#kotlin-style-and-conventions)
2. [Null Safety](#null-safety)
3. [Data Classes](#data-classes)
4. [Extension Functions](#extension-functions)
5. [Coroutines](#coroutines)
6. [Scope Functions](#scope-functions)
7. [Collections](#collections)
8. [Sealed Classes](#sealed-classes)
9. [Interop with Java](#interop-with-java)

---

## Kotlin Style and Conventions

### Naming Conventions

```kotlin
// Variables and functions - camelCase
val userName = "Sam"
fun calculateTotal(items: List<Item>): Double {
    // implementation
    return 0.0
}

// Types and interfaces - PascalCase
data class UserProfile(val id: String, val email: String)
interface Drawable {
    fun draw()
}

// Constants - UPPER_SNAKE_CASE (use const val or top-level val)
const val MAX_RETRIES = 3
val DEFAULT_TIMEOUT_SECONDS = 30

// Packages - lowercase, no underscores
package com.example.billing
```

### Prefer Expression Style

```kotlin
// Bad - verbose block and temporary variable
fun isAdult(age: Int): Boolean {
    val result = if (age >= 18) true else false
    return result
}

// Good - expression body
fun isAdult(age: Int): Boolean = age >= 18
```

---

## Null Safety

### Avoid Nullable Types When Not Needed

```kotlin
// Bad - nullable without reason
data class User(val id: String, val email: String?)

fun sendReceipt(user: User) {
    if (user.email != null) {
        sendEmail(user.email)
    }
}

// Good - make nullability explicit and constrained
data class User(val id: String, val email: String)

fun sendReceipt(user: User) = sendEmail(user.email)
```

### Prefer Safe Calls and Elvis

```kotlin
// Bad - non-null assertion can crash
val length = user.nickname!!.length

// Good - safe call with default
val length = user.nickname?.length ?: 0
```

### Use let for Scoped Nullable Handling

```kotlin
// Bad - nested ifs
if (user != null) {
    if (user.address != null) {
        println(user.address.city)
    }
}

// Good - safe calls and let
user?.address?.let { address ->
    println(address.city)
}
```

---

## Data Classes

### Prefer Data Classes for Value Objects

```kotlin
// Bad - manual boilerplate
class Money(val amount: Long, val currency: String) {
    override fun equals(other: Any?): Boolean {
        if (other !is Money) return false
        return amount == other.amount && currency == other.currency
    }

    override fun hashCode(): Int = 31 * amount.hashCode() + currency.hashCode()

    override fun toString(): String = "Money(amount=$amount, currency=$currency)"
}

// Good - data class
data class Money(val amount: Long, val currency: String)
```

### Use copy for Immutable Updates

```kotlin
data class User(val id: String, val name: String, val active: Boolean)

// Bad - mutable updates
val user = User("u1", "Sam", true)
val updated = User(user.id, "Samantha", user.active)

// Good - copy
val updated = user.copy(name = "Samantha")
```

---

## Extension Functions

### Encapsulate Reusable Logic

```kotlin
// Bad - utility object and noisy call site
object StringUtils {
    fun String.toSlug(): String = lowercase().replace(" ", "-")
}

val slug = StringUtils.run { "Hello World".toSlug() }

// Good - extension function at top-level
fun String.toSlug(): String = lowercase().replace(" ", "-")

val slug = "Hello World".toSlug()
```

### Avoid Overusing Extensions

```kotlin
// Bad - hides dependencies and side effects
fun HttpClient.postJson(url: String, body: String): HttpResponse {
    return this.post(url, body)
}

// Good - keep behavior explicit when dependencies are involved
class ApiClient(private val http: HttpClient) {
    fun postJson(url: String, body: String): HttpResponse {
        return http.post(url, body)
    }
}
```

---

## Coroutines

### Prefer Structured Concurrency

```kotlin
// Bad - GlobalScope leaks lifecycle
fun loadUserData() {
    GlobalScope.launch {
        val user = api.fetchUser()
        saveUser(user)
    }
}

// Good - tie to a scope
class UserRepository(private val scope: CoroutineScope) {
    fun loadUserData() = scope.launch {
        val user = api.fetchUser()
        saveUser(user)
    }
}
```

### Use suspend and withContext

```kotlin
// Bad - blocking call on main thread
suspend fun readFile(path: String): String {
    return File(path).readText()
}

// Good - shift to IO dispatcher
suspend fun readFile(path: String): String = withContext(Dispatchers.IO) {
    File(path).readText()
}
```

### Use async for Parallel Work

```kotlin
// Bad - sequential calls
suspend fun loadDashboard(): Dashboard {
    val user = api.fetchUser()
    val stats = api.fetchStats()
    return Dashboard(user, stats)
}

// Good - parallel with async
suspend fun loadDashboard(): Dashboard = coroutineScope {
    val user = async { api.fetchUser() }
    val stats = async { api.fetchStats() }
    Dashboard(user.await(), stats.await())
}
```

---

## Scope Functions

### Choose the Right Scope Function

```kotlin
data class Config(var host: String, var port: Int)

// Bad - confusing nested scope usage
val config = Config("localhost", 8080).also {
    it.host = "api.local"
    it.port = 9090
}.run {
    "http://$host:$port"
}

// Good - use apply for configuration and let for transformation
val config = Config("localhost", 8080).apply {
    host = "api.local"
    port = 9090
}
val baseUrl = config.let { "http://${it.host}:${it.port}" }
```

### Avoid Overusing It

```kotlin
// Bad - ambiguous it chain
user?.let { it.profile }?.let { it.preferences }?.let { it.theme }

// Good - name values for clarity
val theme = user?.profile?.preferences?.theme
```

---

## Collections

### Prefer Immutable Collections

```kotlin
// Bad - mutable lists by default
val users = mutableListOf("a", "b", "c")
users.add("d")

// Good - immutable list and create new list when needed
val users = listOf("a", "b", "c")
val updated = users + "d"
```

### Use Standard Library Functions

```kotlin
val numbers = listOf(1, 2, 3, 4, 5)

// Bad - manual loop
val evenSquares = mutableListOf<Int>()
for (n in numbers) {
    if (n % 2 == 0) {
        evenSquares.add(n * n)
    }
}

// Good - filter/map
val evenSquares = numbers.filter { it % 2 == 0 }.map { it * it }
```

### Avoid Temporary Collections

```kotlin
// Bad - intermediate list
val total = numbers.map { it * 2 }.filter { it > 5 }.sum()

// Good - use sequence for large data
val total = numbers.asSequence()
    .map { it * 2 }
    .filter { it > 5 }
    .sum()
```

---

## Sealed Classes

### Model Exhaustive State

```kotlin
// Bad - enum with extra data via nullable fields
data class Result(val status: String, val error: String?, val data: String?)

// Good - sealed hierarchy
sealed class Result {
    data class Success(val data: String) : Result()
    data class Error(val message: String) : Result()
    object Loading : Result()
}

fun render(result: Result): String = when (result) {
    is Result.Success -> "Data: ${result.data}"
    is Result.Error -> "Error: ${result.message}"
    Result.Loading -> "Loading"
}
```

### Use when Without else

```kotlin
// Bad - else hides missing cases
fun label(result: Result): String = when (result) {
    is Result.Success -> "OK"
    else -> "Other"
}

// Good - exhaustive when
fun label(result: Result): String = when (result) {
    is Result.Success -> "OK"
    is Result.Error -> "Error"
    Result.Loading -> "Loading"
}
```

---

## Interop with Java

### Use @JvmStatic and @JvmOverloads

```kotlin
// Bad - Java callers get awkward usage
class Dates {
    companion object {
        fun nowUtc(): Instant = Instant.now()
    }

    fun format(date: Instant, pattern: String = "yyyy-MM-dd"): String {
        return DateTimeFormatter.ofPattern(pattern)
            .withZone(ZoneOffset.UTC)
            .format(date)
    }
}

// Good - Java-friendly APIs
class Dates {
    companion object {
        @JvmStatic fun nowUtc(): Instant = Instant.now()
    }

    @JvmOverloads
    fun format(date: Instant, pattern: String = "yyyy-MM-dd"): String {
        return DateTimeFormatter.ofPattern(pattern)
            .withZone(ZoneOffset.UTC)
            .format(date)
    }
}
```

### Avoid Platform Types with Explicit Nullability

```kotlin
// Bad - platform types from Java are nullable at runtime
val name = javaUser.name
val length = name.length

// Good - use safe call or requireNotNull
val name = javaUser.name
val length = name?.length ?: 0

val strictName = requireNotNull(javaUser.name) { "name is required" }
```

### Prefer Kotlin Types and Builders

```kotlin
// Bad - Java collections in public API
fun loadUsers(): java.util.List<User> = java.util.ArrayList()

// Good - Kotlin collections
fun loadUsers(): List<User> = emptyList()
```

---

## Kotlin Simplification Checklist

- [ ] Following Kotlin naming conventions (camelCase,
      PascalCase)
- [ ] Nullability is explicit and minimized
- [ ] Using data classes for value objects
- [ ] Extension functions are small and focused
- [ ] Structured concurrency for coroutines
- [ ] Scope functions chosen intentionally
- [ ] Prefer immutable collections
- [ ] Sealed classes with exhaustive when
- [ ] Java interop annotations as needed
- [ ] No unsafe !! in core flows

---

## Additional Resources

- Kotlin Coding Conventions: https://kotlinlang.org/docs/coding-conventions.html
- Kotlin Coroutines Guide: https://kotlinlang.org/docs/coroutines-guide.html
- Effective Kotlin: https://kt.academy/book/effectivekotlin
- Kotlin Standard Library: https://kotlinlang.org/api/latest/jvm/stdlib/
- Interop with Java: https://kotlinlang.org/docs/java-interop.html

**Kotlin Version Recommendation**: Use the latest stable
version for best features and tooling.
