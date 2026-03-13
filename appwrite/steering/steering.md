# Appwrite Best Practices

This guide provides best practices for building applications with Appwrite.

## Database Design

### Schema Planning

**Always define your schema before creating documents:**

```javascript
// ✅ Good: Define attributes first
await createStringAttribute({ key: "name", size: 255, required: true })
await createEmailAttribute({ key: "email", required: true })
await createBooleanAttribute({ key: "is_active", required: true, default: true })

// Then create documents
await createDocument({ data: { name: "John", email: "john@example.com", is_active: true }})
```

**Use appropriate attribute types:**
- `string` - Short text (names, titles) - specify size
- `email` - Email addresses with validation
- `url` - URLs with validation
- `integer` - Whole numbers
- `float` - Decimal numbers
- `boolean` - True/false values
- `datetime` - ISO 8601 timestamps
- `enum` - Predefined values
- `relationship` - References to other collections

### Indexing Strategy

**Create indexes for frequently queried attributes:**

```javascript
// ✅ Good: Index commonly queried fields
await createIndex({
  key: "email_index",
  type: "unique",
  attributes: ["email"]
})

await createIndex({
  key: "created_at_index",
  type: "key",
  attributes: ["$createdAt"],
  orders: ["DESC"]
})

// For full-text search
await createIndex({
  key: "title_search",
  type: "fulltext",
  attributes: ["title", "content"]
})
```

**Index types:**
- `key` - Standard index for equality and range queries
- `unique` - Ensures unique values (e.g., email, username)
- `fulltext` - Full-text search on text fields
- `array` - Index array values

### Query Optimization

**Use specific queries instead of fetching all documents:**

```javascript
// ❌ Bad: Fetch everything
const all = await listDocuments({ collection_id: "posts" })

// ✅ Good: Use filters and limits
const recent = await listDocuments({
  collection_id: "posts",
  queries: [
    "equal(\"status\", \"published\")",
    "orderDesc(\"$createdAt\")",
    "limit(10)"
  ]
})
```

**Common query methods:**
- `equal(attribute, value)` - Exact match
- `notEqual(attribute, value)` - Not equal
- `lessThan(attribute, value)` - Less than
- `greaterThan(attribute, value)` - Greater than
- `search(attribute, value)` - Full-text search
- `orderAsc(attribute)` - Sort ascending
- `orderDesc(attribute)` - Sort descending
- `limit(count)` - Limit results
- `offset(count)` - Skip results

## Security & Permissions

### Document-Level Security

**Enable document security for user-specific data:**

```javascript
// ✅ Good: Enable document security
await createCollection({
  collection_id: "posts",
  name: "Posts",
  document_security: true,
  permissions: ["read(\"any\")"] // Anyone can list posts
})

// Create document with user-specific permissions
await createDocument({
  collection_id: "posts",
  document_id: "unique()",
  data: { title: "My Post", content: "..." },
  permissions: [
    "read(\"any\")",                    // Anyone can read
    "update(\"user:USER_ID\")",         // Only author can update
    "delete(\"user:USER_ID\")"          // Only author can delete
  ]
})
```

### Permission Patterns

**Common permission patterns:**

```javascript
// Public read, authenticated write
permissions: [
  "read(\"any\")",
  "create(\"users\")",
  "update(\"users\")",
  "delete(\"users\")"
]

// User-specific access
permissions: [
  "read(\"user:USER_ID\")",
  "update(\"user:USER_ID\")",
  "delete(\"user:USER_ID\")"
]

// Team-based access
permissions: [
  "read(\"team:TEAM_ID\")",
  "update(\"team:TEAM_ID/owner\")",
  "delete(\"team:TEAM_ID/owner\")"
]

// Role-based access
permissions: [
  "read(\"any\")",
  "update(\"role:admin\")",
  "delete(\"role:admin\")"
]
```

### API Key Security

**Never expose API keys in client-side code:**

```javascript
// ❌ Bad: API key in frontend
const client = new Client()
  .setEndpoint('https://cloud.appwrite.io/v1')
  .setProject('PROJECT_ID')
  .setKey('API_KEY') // NEVER DO THIS!

// ✅ Good: Use API key only in backend/server
// Frontend should use account sessions
const client = new Client()
  .setEndpoint('https://cloud.appwrite.io/v1')
  .setProject('PROJECT_ID')
```

## User Management

### User Creation

**Create users with proper validation:**

```javascript
// ✅ Good: Validate before creating
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function validatePassword(password) {
  return password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password)
}

if (validateEmail(email) && validatePassword(password)) {
  await createUser({
    user_id: "unique()",
    email: email,
    password: password,
    name: name
  })
}
```

### User Preferences

**Store user settings in preferences:**

```javascript
// ✅ Good: Use preferences for user settings
await updatePrefs({
  user_id: userId,
  prefs: {
    theme: "dark",
    language: "en",
    notifications: {
      email: true,
      push: false
    }
  }
})
```

## Storage Management

### Bucket Configuration

**Configure buckets with appropriate limits:**

```javascript
// ✅ Good: Set reasonable limits
await createBucket({
  bucket_id: "avatars",
  name: "User Avatars",
  permissions: ["read(\"any\")"],
  file_security: true,
  enabled: true,
  maximum_file_size: 5000000, // 5MB
  allowed_file_extensions: ["jpg", "jpeg", "png", "gif", "webp"],
  compression: "gzip",
  encryption: true,
  antivirus: true
})
```

### File Upload Best Practices

**Validate files before upload:**

```javascript
// ✅ Good: Validate file before upload
function validateFile(file) {
  const maxSize = 5 * 1024 * 1024 // 5MB
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  
  if (file.size > maxSize) {
    throw new Error('File too large')
  }
  
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type')
  }
  
  return true
}

if (validateFile(file)) {
  await createFile({
    bucket_id: "avatars",
    file_id: "unique()",
    file: file,
    permissions: ["read(\"any\")"]
  })
}
```

### Image Optimization

**Use preview endpoint for optimized images:**

```javascript
// ✅ Good: Use preview with optimization
const imageUrl = `${endpoint}/storage/buckets/${bucketId}/files/${fileId}/preview?width=400&height=400&quality=80&output=webp`

// For thumbnails
const thumbnail = `${endpoint}/storage/buckets/${bucketId}/files/${fileId}/preview?width=150&height=150&gravity=center&output=webp`
```

## Functions Development

### Function Structure

**Organize function code properly:**

```javascript
// ✅ Good: Clean function structure
export default async ({ req, res, log, error }) => {
  try {
    // Validate input
    const { amount, currency } = JSON.parse(req.body)
    
    if (!amount || !currency) {
      return res.json({ error: 'Missing required fields' }, 400)
    }
    
    // Process logic
    const result = await processPayment(amount, currency)
    
    // Return response
    return res.json({ success: true, result })
    
  } catch (err) {
    error(err.message)
    return res.json({ error: 'Internal server error' }, 500)
  }
}
```

### Environment Variables

**Use environment variables for secrets:**

```javascript
// ✅ Good: Use environment variables
const stripeKey = process.env.STRIPE_API_KEY
const webhookSecret = process.env.WEBHOOK_SECRET

// ❌ Bad: Hardcoded secrets
const stripeKey = 'sk_test_...' // NEVER DO THIS!
```

### Error Handling

**Implement comprehensive error handling:**

```javascript
// ✅ Good: Proper error handling
export default async ({ req, res, log, error }) => {
  try {
    const data = JSON.parse(req.body)
    
    // Validate
    if (!data.email) {
      return res.json({ error: 'Email required' }, 400)
    }
    
    // Process
    const result = await sendEmail(data.email)
    
    log('Email sent successfully')
    return res.json({ success: true })
    
  } catch (err) {
    error(`Failed to send email: ${err.message}`)
    
    // Return appropriate error
    if (err.code === 'INVALID_EMAIL') {
      return res.json({ error: 'Invalid email address' }, 400)
    }
    
    return res.json({ error: 'Internal server error' }, 500)
  }
}
```

## Real-time Subscriptions

### Subscribe to Changes

**Use real-time for live updates:**

```javascript
// ✅ Good: Subscribe to specific channels
client.subscribe('databases.main.collections.posts.documents', response => {
  if (response.events.includes('databases.*.collections.*.documents.*.create')) {
    console.log('New post created:', response.payload)
  }
  
  if (response.events.includes('databases.*.collections.*.documents.*.update')) {
    console.log('Post updated:', response.payload)
  }
})

// Subscribe to specific document
client.subscribe('databases.main.collections.posts.documents.POST_ID', response => {
  console.log('Document changed:', response.payload)
})
```

## Error Handling

### Graceful Error Handling

**Always handle errors gracefully:**

```javascript
// ✅ Good: Comprehensive error handling
async function createPost(title, content) {
  try {
    const document = await createDocument({
      database_id: "main",
      collection_id: "posts",
      document_id: "unique()",
      data: { title, content }
    })
    
    return { success: true, document }
    
  } catch (error) {
    // Handle specific errors
    if (error.code === 404) {
      console.error('Collection not found')
      return { success: false, error: 'Collection not found' }
    }
    
    if (error.code === 401) {
      console.error('Unauthorized')
      return { success: false, error: 'Unauthorized' }
    }
    
    if (error.code === 409) {
      console.error('Document already exists')
      return { success: false, error: 'Duplicate document' }
    }
    
    // Generic error
    console.error('Failed to create post:', error)
    return { success: false, error: 'Failed to create post' }
  }
}
```

## Performance Optimization

### Caching Strategy

**Implement caching for frequently accessed data:**

```javascript
// ✅ Good: Cache frequently accessed data
const cache = new Map()

async function getPost(postId) {
  // Check cache first
  if (cache.has(postId)) {
    return cache.get(postId)
  }
  
  // Fetch from database
  const post = await getDocument({
    database_id: "main",
    collection_id: "posts",
    document_id: postId
  })
  
  // Cache for 5 minutes
  cache.set(postId, post)
  setTimeout(() => cache.delete(postId), 5 * 60 * 1000)
  
  return post
}
```

### Batch Operations

**Use transactions for multiple related operations:**

```javascript
// ✅ Good: Use transactions for atomic operations
const transaction = await createTransaction({ ttl: 300 })

try {
  // Create user
  await createDocument({
    database_id: "main",
    collection_id: "users",
    document_id: "unique()",
    data: { name: "John", email: "john@example.com" },
    transaction_id: transaction.id
  })
  
  // Create user profile
  await createDocument({
    database_id: "main",
    collection_id: "profiles",
    document_id: "unique()",
    data: { user_id: userId, bio: "..." },
    transaction_id: transaction.id
  })
  
  // Commit transaction
  await updateTransaction({
    transaction_id: transaction.id,
    commit: true
  })
  
} catch (error) {
  // Rollback on error
  await updateTransaction({
    transaction_id: transaction.id,
    rollback: true
  })
}
```

## Testing

### Test Environment

**Use separate projects for testing:**

```javascript
// ✅ Good: Separate test and production
const config = {
  test: {
    endpoint: 'https://cloud.appwrite.io/v1',
    project: 'TEST_PROJECT_ID',
    apiKey: 'TEST_API_KEY'
  },
  production: {
    endpoint: 'https://cloud.appwrite.io/v1',
    project: 'PROD_PROJECT_ID',
    apiKey: 'PROD_API_KEY'
  }
}

const env = process.env.NODE_ENV || 'test'
const client = new Client()
  .setEndpoint(config[env].endpoint)
  .setProject(config[env].project)
  .setKey(config[env].apiKey)
```

### Integration Tests

**Write tests for critical operations:**

```javascript
// ✅ Good: Test critical operations
describe('User Management', () => {
  test('should create user', async () => {
    const user = await createUser({
      user_id: "unique()",
      email: "test@example.com",
      password: "SecurePass123!",
      name: "Test User"
    })
    
    expect(user.email).toBe("test@example.com")
    expect(user.name).toBe("Test User")
  })
  
  test('should handle duplicate email', async () => {
    await expect(
      createUser({
        user_id: "unique()",
        email: "test@example.com",
        password: "SecurePass123!",
        name: "Test User"
      })
    ).rejects.toThrow()
  })
})
```

## Monitoring & Logging

### Function Logging

**Use structured logging:**

```javascript
// ✅ Good: Structured logging
export default async ({ req, res, log, error }) => {
  log('Function started', {
    method: req.method,
    path: req.path,
    timestamp: new Date().toISOString()
  })
  
  try {
    const result = await processRequest(req)
    
    log('Function completed successfully', {
      duration: Date.now() - startTime,
      result: result
    })
    
    return res.json({ success: true, result })
    
  } catch (err) {
    error('Function failed', {
      error: err.message,
      stack: err.stack,
      timestamp: new Date().toISOString()
    })
    
    return res.json({ error: 'Internal server error' }, 500)
  }
}
```

### Usage Monitoring

**Monitor API usage and performance:**

```javascript
// ✅ Good: Track API usage
const metrics = {
  requests: 0,
  errors: 0,
  latency: []
}

async function apiCall(operation) {
  const start = Date.now()
  metrics.requests++
  
  try {
    const result = await operation()
    metrics.latency.push(Date.now() - start)
    return result
    
  } catch (error) {
    metrics.errors++
    throw error
  }
}

// Log metrics periodically
setInterval(() => {
  console.log('API Metrics:', {
    requests: metrics.requests,
    errors: metrics.errors,
    avgLatency: metrics.latency.reduce((a, b) => a + b, 0) / metrics.latency.length,
    errorRate: (metrics.errors / metrics.requests * 100).toFixed(2) + '%'
  })
}, 60000) // Every minute
```

## Migration & Backup

### Data Export

**Regularly export important data:**

```javascript
// ✅ Good: Export data for backup
async function exportCollection(databaseId, collectionId) {
  const documents = []
  let offset = 0
  const limit = 100
  
  while (true) {
    const response = await listDocuments({
      database_id: databaseId,
      collection_id: collectionId,
      queries: [`limit(${limit})`, `offset(${offset})`]
    })
    
    documents.push(...response.documents)
    
    if (response.documents.length < limit) {
      break
    }
    
    offset += limit
  }
  
  // Save to file
  fs.writeFileSync(
    `backup-${collectionId}-${Date.now()}.json`,
    JSON.stringify(documents, null, 2)
  )
  
  return documents
}
```

### Schema Migration

**Version your schema changes:**

```javascript
// ✅ Good: Version schema migrations
const migrations = {
  v1: async () => {
    await createStringAttribute({
      database_id: "main",
      collection_id: "users",
      key: "name",
      size: 255,
      required: true
    })
  },
  
  v2: async () => {
    await createEmailAttribute({
      database_id: "main",
      collection_id: "users",
      key: "email",
      required: true
    })
  },
  
  v3: async () => {
    await createBooleanAttribute({
      database_id: "main",
      collection_id: "users",
      key: "is_verified",
      required: true,
      default: false
    })
  }
}

async function runMigrations(currentVersion, targetVersion) {
  for (let v = currentVersion + 1; v <= targetVersion; v++) {
    console.log(`Running migration v${v}`)
    await migrations[`v${v}`]()
  }
}
```

---

Following these best practices will help you build secure, performant, and maintainable applications with Appwrite.
