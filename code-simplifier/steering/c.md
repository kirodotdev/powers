# C Code Simplification Guide

This guide covers C-specific simplification patterns and
best practices for writing clean, maintainable C code.

## Table of Contents

1. [C Style and Conventions](#c-style-and-conventions)
2. [Memory Management](#memory-management)
3. [Pointers and Arrays](#pointers-and-arrays)
4. [Error Handling](#error-handling)
5. [Structs and Data Structures](#structs-and-data-structures)
6. [Preprocessor](#preprocessor)
7. [Function Design](#function-design)
8. [Common Patterns](#common-patterns)

---

## C Style and Conventions

### Naming Conventions

```c
// Variables and functions - snake_case
int user_count = 0;
void calculate_total(int items[], int size) {
    // implementation
}

// Constants and macros - UPPER_SNAKE_CASE
#define MAX_BUFFER_SIZE 1024
#define PI 3.14159

// Struct types - snake_case or PascalCase (be consistent)
typedef struct user {
    int id;
    char name[50];
} user_t;

// Enum - UPPER_SNAKE_CASE for values
typedef enum {
    STATUS_PENDING,
    STATUS_PROCESSING,
    STATUS_COMPLETED
} status_t;
```

### File Organization

```c
// header.h
#ifndef HEADER_H
#define HEADER_H

// Include guards prevent multiple inclusion
#include <stdio.h>
#include <stdlib.h>

// Function declarations
void init_system(void);
int process_data(const char *input);

#endif // HEADER_H

// implementation.c
#include "header.h"

// Static functions (file-local)
static int helper_function(int x) {
    return x * 2;
}

// Public functions
void init_system(void) {
    // implementation
}
```

---

## Memory Management

### Always Free Allocated Memory

```c
// Bad - memory leak
void process_data(void) {
    char *buffer = malloc(1024);
    if (buffer == NULL) {
        return;
    }
    // ... use buffer
    // Missing free()!
}

// Good - proper cleanup
void process_data(void) {
    char *buffer = malloc(1024);
    if (buffer == NULL) {
        return;
    }

    // ... use buffer

    free(buffer);
    buffer = NULL; // Prevent use-after-free
}
```

### Check malloc Return Values

```c
// Bad - no null check
int *numbers = malloc(100 * sizeof(int));
numbers[0] = 42; // Crash if malloc failed!

// Good - always check
int *numbers = malloc(100 * sizeof(int));
if (numbers == NULL) {
    fprintf(stderr, "Memory allocation failed\n");
    return -1;
}

numbers[0] = 42;
// ... use numbers

free(numbers);
```

### Use sizeof with Variables, Not Types

```c
// Bad - error-prone if type changes
int *array = malloc(100 * sizeof(int));

// Good - automatically correct if type changes
int *array = malloc(100 * sizeof(*array));

// For structs
user_t *user = malloc(sizeof(*user));
```

### Avoid Memory Leaks in Error Paths

```c
// Bad - leaks on error
int process_file(const char *filename) {
    char *buffer = malloc(1024);
    FILE *file = fopen(filename, "r");

    if (file == NULL) {
        return -1; // Leaked buffer!
    }

    // ... process

    free(buffer);
    fclose(file);
    return 0;
}

// Good - cleanup on all paths
int process_file(const char *filename) {
    char *buffer = malloc(1024);
    if (buffer == NULL) {
        return -1;
    }

    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        free(buffer);
        return -1;
    }

    // ... process

    fclose(file);
    free(buffer);
    return 0;
}

// Better - use goto for cleanup (common C pattern)
int process_file(const char *filename) {
    char *buffer = NULL;
    FILE *file = NULL;
    int result = -1;

    buffer = malloc(1024);
    if (buffer == NULL) {
        goto cleanup;
    }

    file = fopen(filename, "r");
    if (file == NULL) {
        goto cleanup;
    }

    // ... process
    result = 0;

cleanup:
    if (file != NULL) {
        fclose(file);
    }
    free(buffer); // free(NULL) is safe
    return result;
}
```

---

## Pointers and Arrays

### Const Correctness

```c
// Bad - no const
void print_string(char *str) {
    printf("%s\n", str);
}

// Good - const for read-only parameters
void print_string(const char *str) {
    printf("%s\n", str);
}

// Const pointer vs pointer to const
const char *ptr1;      // Pointer to const char (can't modify data)
char *const ptr2;      // Const pointer (can't change pointer)
const char *const ptr3; // Both const
```

### Array Parameters

```c
// Bad - unclear size
void process_array(int arr[]) {
    // How big is arr?
}

// Good - pass size explicitly
void process_array(int arr[], size_t size) {
    for (size_t i = 0; i < size; i++) {
        arr[i] *= 2;
    }
}

// Better - use const for read-only
void print_array(const int arr[], size_t size) {
    for (size_t i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}
```

### Pointer Arithmetic

```c
// Bad - manual indexing with pointers
int sum = 0;
int *p = array;
for (int i = 0; i < size; i++) {
    sum += *(p + i);
}

// Good - use array indexing when clearer
int sum = 0;
for (int i = 0; i < size; i++) {
    sum += array[i];
}

// Pointer arithmetic when appropriate
void copy_string(char *dest, const char *src) {
    while ((*dest++ = *src++) != '\0') {
        // Copy until null terminator
    }
}
```

---

## Error Handling

### Return Error Codes

```c
// Bad - no error indication
void parse_number(const char *str, int *result) {
    *result = atoi(str); // No way to detect errors
}

// Good - return error code
int parse_number(const char *str, int *result) {
    char *endptr;
    long val = strtol(str, &endptr, 10);

    if (endptr == str || *endptr != '\0') {
        return -1; // Parse error
    }

    if (val > INT_MAX || val < INT_MIN) {
        return -1; // Overflow
    }

    *result = (int)val;
    return 0; // Success
}

// Usage
int number;
if (parse_number("123", &number) != 0) {
    fprintf(stderr, "Failed to parse number\n");
    return -1;
}
```

### Use errno for System Calls

```c
#include <errno.h>
#include <string.h>

// Check errno after system calls
FILE *file = fopen("data.txt", "r");
if (file == NULL) {
    fprintf(stderr, "Failed to open file: %s\n", strerror(errno));
    return -1;
}
```

### Error Handling Macros

```c
// Define error handling macros
#define CHECK_NULL(ptr, msg) \
    do { \
        if ((ptr) == NULL) { \
            fprintf(stderr, "Error: %s\n", (msg)); \
            goto cleanup; \
        } \
    } while (0)

#define CHECK_ERROR(expr, msg) \
    do { \
        if ((expr) != 0) { \
            fprintf(stderr, "Error: %s\n", (msg)); \
            goto cleanup; \
        } \
    } while (0)

// Usage
int process_data(void) {
    char *buffer = NULL;
    int result = -1;

    buffer = malloc(1024);
    CHECK_NULL(buffer, "Memory allocation failed");

    CHECK_ERROR(read_data(buffer, 1024), "Failed to read data");

    result = 0;

cleanup:
    free(buffer);
    return result;
}
```

---

## Structs and Data Structures

### Struct Initialization

```c
typedef struct {
    int id;
    char name[50];
    double balance;
} account_t;

// Bad - uninitialized fields
account_t acc;
acc.id = 1;
// name and balance are uninitialized!

// Good - designated initializers (C99)
account_t acc = {
    .id = 1,
    .name = "John Doe",
    .balance = 1000.0
};

// Zero initialization
account_t acc = {0}; // All fields set to 0
```

### Opaque Pointers (Information Hiding)

```c
// header.h
typedef struct user user_t; // Forward declaration

user_t *user_create(const char *name);
void user_destroy(user_t *user);
const char *user_get_name(const user_t *user);

// implementation.c
struct user {
    char name[50];
    int id;
    // Internal fields hidden from users
};

user_t *user_create(const char *name) {
    user_t *user = malloc(sizeof(*user));
    if (user == NULL) {
        return NULL;
    }

    strncpy(user->name, name, sizeof(user->name) - 1);
    user->name[sizeof(user->name) - 1] = '\0';
    user->id = generate_id();

    return user;
}

void user_destroy(user_t *user) {
    free(user);
}
```

### Flexible Array Members

```c
// Bad - fixed size
typedef struct {
    size_t count;
    int data[100]; // Wastes space or limits size
} buffer_t;

// Good - flexible array member (C99)
typedef struct {
    size_t count;
    int data[]; // Flexible array
} buffer_t;

// Allocation
buffer_t *create_buffer(size_t count) {
    buffer_t *buf = malloc(sizeof(*buf) + count * sizeof(int));
    if (buf == NULL) {
        return NULL;
    }

    buf->count = count;
    return buf;
}
```

---

## Preprocessor

### Include Guards

```c
// header.h
#ifndef HEADER_H
#define HEADER_H

// Header content

#endif // HEADER_H

// Modern alternative (not standard but widely supported)
#pragma once
```

### Macro Best Practices

```c
// Bad - unsafe macro
#define SQUARE(x) x * x
int result = SQUARE(2 + 3); // Expands to 2 + 3 * 2 + 3 = 11, not 25!

// Good - parentheses around parameters and expression
#define SQUARE(x) ((x) * (x))
int result = SQUARE(2 + 3); // Correctly expands to 25

// Multi-statement macros - use do-while(0)
#define SWAP(a, b, type) \
    do { \
        type temp = (a); \
        (a) = (b); \
        (b) = temp; \
    } while (0)

// Usage
if (x > y)
    SWAP(x, y, int); // Works correctly with do-while
```

### Conditional Compilation

```c
// Debug logging
#ifdef DEBUG
    #define LOG(msg) printf("DEBUG: %s\n", (msg))
#else
    #define LOG(msg) ((void)0)
#endif

// Platform-specific code
#ifdef _WIN32
    #include <windows.h>
    #define PATH_SEPARATOR '\\'
#else
    #include <unistd.h>
    #define PATH_SEPARATOR '/'
#endif
```

---

## Function Design

### Single Responsibility

```c
// Bad - function does too much
void process_user(const char *name, const char *email) {
    // Validate input
    if (name == NULL || email == NULL) return;

    // Create user
    user_t *user = malloc(sizeof(*user));

    // Save to database
    save_to_db(user);

    // Send email
    send_welcome_email(email);

    // Log activity
    log_user_creation(name);
}

// Good - separate concerns
int validate_user_input(const char *name, const char *email) {
    return (name != NULL && email != NULL) ? 0 : -1;
}

user_t *create_user(const char *name, const char *email) {
    user_t *user = malloc(sizeof(*user));
    if (user == NULL) {
        return NULL;
    }

    strncpy(user->name, name, sizeof(user->name) - 1);
    strncpy(user->email, email, sizeof(user->email) - 1);

    return user;
}

int process_user(const char *name, const char *email) {
    if (validate_user_input(name, email) != 0) {
        return -1;
    }

    user_t *user = create_user(name, email);
    if (user == NULL) {
        return -1;
    }

    if (save_to_db(user) != 0) {
        free(user);
        return -1;
    }

    send_welcome_email(email);
    log_user_creation(name);

    free(user);
    return 0;
}
```

### Limit Function Parameters

```c
// Bad - too many parameters
void create_window(int x, int y, int width, int height,
                   const char *title, int style, int flags,
                   void *parent, void *menu);

// Good - use struct for related parameters
typedef struct {
    int x, y;
    int width, height;
    const char *title;
    int style;
    int flags;
    void *parent;
    void *menu;
} window_config_t;

void create_window(const window_config_t *config);

// Usage with designated initializers
window_config_t config = {
    .x = 100,
    .y = 100,
    .width = 800,
    .height = 600,
    .title = "My Window",
    .style = WINDOW_STYLE_DEFAULT,
    .flags = 0,
    .parent = NULL,
    .menu = NULL
};

create_window(&config);
```

---

## Common Patterns

### String Handling

```c
// Always use safe string functions
#include <string.h>

// Bad - buffer overflow risk
char dest[10];
strcpy(dest, source); // Dangerous!

// Good - bounded copy
char dest[10];
strncpy(dest, source, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0'; // Ensure null termination

// Better - use snprintf for formatting
char buffer[100];
snprintf(buffer, sizeof(buffer), "User: %s, ID: %d", name, id);
```

### Dynamic Arrays

```c
typedef struct {
    int *data;
    size_t size;
    size_t capacity;
} dynamic_array_t;

dynamic_array_t *array_create(size_t initial_capacity) {
    dynamic_array_t *arr = malloc(sizeof(*arr));
    if (arr == NULL) {
        return NULL;
    }

    arr->data = malloc(initial_capacity * sizeof(int));
    if (arr->data == NULL) {
        free(arr);
        return NULL;
    }

    arr->size = 0;
    arr->capacity = initial_capacity;
    return arr;
}

int array_push(dynamic_array_t *arr, int value) {
    if (arr->size >= arr->capacity) {
        size_t new_capacity = arr->capacity * 2;
        int *new_data = realloc(arr->data, new_capacity * sizeof(int));
        if (new_data == NULL) {
            return -1;
        }

        arr->data = new_data;
        arr->capacity = new_capacity;
    }

    arr->data[arr->size++] = value;
    return 0;
}

void array_destroy(dynamic_array_t *arr) {
    if (arr != NULL) {
        free(arr->data);
        free(arr);
    }
}
```

### Callback Functions

```c
// Function pointer typedef
typedef int (*compare_fn)(const void *a, const void *b);

// Generic sort function
void sort_array(void *array, size_t count, size_t size, compare_fn compare) {
    // Sorting implementation using compare callback
}

// Comparison function
int compare_ints(const void *a, const void *b) {
    int arg1 = *(const int *)a;
    int arg2 = *(const int *)b;
    return (arg1 > arg2) - (arg1 < arg2);
}

// Usage
int numbers[] = {5, 2, 8, 1, 9};
sort_array(numbers, 5, sizeof(int), compare_ints);
```

---

## C Simplification Checklist

- [ ] Following C naming conventions
- [ ] Always check malloc/calloc return values
- [ ] Free all allocated memory
- [ ] Use const for read-only parameters
- [ ] Pass array sizes explicitly
- [ ] Return error codes from functions
- [ ] Use designated initializers for structs
- [ ] Include guards in all headers
- [ ] Safe string handling (strncpy, snprintf)
- [ ] Parentheses in macro definitions
- [ ] goto for cleanup in error paths (when appropriate)
- [ ] No nested ternary operators

---

## Additional Resources

- C Programming Language (K&R): The definitive C reference
- C Standard Library: https://en.cppreference.com/w/c
- CERT C Coding Standard:
  https://wiki.sei.cmu.edu/confluence/display/c
- Modern C (Jens Gustedt): Free book on modern C practices

**C Standard Recommendation**: Use C11 or C17 for modern
features while maintaining portability.
