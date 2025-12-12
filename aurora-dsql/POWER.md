---
name: "aurora-dsql"
displayName: "Build a database with Aurora DSQL"
description: "Build and deploy a PostgreSQL-compatible serverless distributed SQL database with Aurora DSQL - manage schemas, execute queries, and handle migrations with DSQL-specific requirements."
keywords: ["aurora", "dsql", "postgresql", "serverless", "database", "sql", "aws", "distributed"]
author: "AWS"
---

# Amazon Aurora DSQL Power

## Overview

The Amazon Aurora DSQL Power provides access to Aurora DSQL, a serverless, PostgreSQL-compatible distributed SQL database with specific constraints and capabilities. Execute queries, manage schemas, handle migrations, and work with multi-tenant data while respecting DSQL's unique limitations.

Aurora DSQL is a true serverless database with scale-to-zero capability, zero operations overhead, and consumption-based pricing. It uses the PostgreSQL wire protocol but has specific limitations around foreign keys, array types, JSON columns, and transaction sizes.

**Key capabilities:**
- **Direct Query Execution**: Run SQL queries directly against your DSQL cluster
- **Schema Management**: Create tables, indexes, and manage DDL operations
- **Migration Support**: Execute schema migrations with DSQL constraints
- **Multi-Tenant Patterns**: Built-in tenant isolation and data scoping
- **Authentication**: Uses AWS IAM credentials with automatic token generation.

## Available Steering Files

This power includes the following steering files in [steering](./steering)
- **development-guide** - DSQL Guidelines and Operational Rules (always loaded)
- **dsql-examples** - Code examples and implementation patterns (load when implementing)
- **language** - Language-based implementation examples and references (load when implementing)
- **troubleshooting** - Common pitfalls and errors and how to solve (load when debugging an error)
- **onboarding** - Interactive "Get Started with DSQL" guide for onboarding users step-by-step

## Available MCP Servers

### aurora-dsql
**Package:** `awslabs.aurora-dsql-mcp-server@latest`
**Connection:** uvx-based MCP server
**Authentication:** AWS IAM credentials with automatic token generation

**Configuration Required:**
- `CLUSTER` - Your DSQL cluster identifier
- `REGION` - AWS region (e.g., us-east-1)
- `AWS_PROFILE` - AWS CLI profile name (optional, uses default if not set)

**Tools:**

1. **query** - Execute SQL queries against Aurora DSQL
   - Required: `sql` (string) - SQL query to execute
   - Optional: `parameters` (array) - Parameterized query values
   - Returns: Query results with rows and metadata
   - Use for: SELECT queries, data exploration, ad-hoc analysis

2. **execute** - Execute SQL statements (DDL/DML)
   - Required: `sql` (string) - SQL statement to execute
   - Optional: `parameters` (array) - Parameterized values
   - Returns: Execution result with affected rows
   - Use for: INSERT, UPDATE, DELETE, CREATE TABLE, ALTER TABLE

3. **list_tables** - List all tables in the database
   - Optional: `schema` (string) - Schema name (default: public)
   - Returns: Array of table names
   - Use for: Schema exploration, validation

4. **describe_table** - Get table schema details
   - Required: `table_name` (string) - Name of table to describe
   - Optional: `schema` (string) - Schema name (default: public)
   - Returns: Column definitions, types, constraints, indexes
   - Use for: Understanding table structure, planning migrations

### aws-core (Optional)
**Package:** `awslabs.core-mcp-server@latest`
**Connection:** uvx-based MCP server
**Authentication:** AWS IAM credentials

Provides additional AWS context and documentation access for DSQL operations.


## Tool Usage Examples

### Querying Data

**Simple SELECT query:**
```javascript
usePower("dsql", "aurora-dsql", "query", {
  "sql": "SELECT * FROM entities WHERE tenant_id = $1 LIMIT 10",
  "parameters": ["tenant-123"]
})
// Returns: { rows: [...], rowCount: 10 }
```

**Aggregate query:**
```javascript
usePower("dsql", "aurora-dsql", "query", {
  "sql": "SELECT tenant_id, COUNT(*) as count FROM objectives GROUP BY tenant_id"
})
```

**Join query:**
```javascript
usePower("dsql", "aurora-dsql", "query", {
  "sql": `
    SELECT e.entity_id, e.name, o.title
    FROM entities e
    INNER JOIN objectives o ON e.entity_id = o.entity_id
    WHERE e.tenant_id = $1
  `,
  "parameters": ["tenant-123"]
})
```

### Schema Operations

**Create table with proper DSQL types:**
```javascript
usePower("dsql", "aurora-dsql", "execute", {
  "sql": `
    CREATE TABLE IF NOT EXISTS entities (
      entity_id VARCHAR(255) PRIMARY KEY,
      tenant_id VARCHAR(255) NOT NULL,
      name VARCHAR(255) NOT NULL,
      tags TEXT,
      metadata TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `
})
```

**Create async index (REQUIRED):**
```javascript
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "CREATE INDEX ASYNC idx_entities_tenant ON entities(tenant_id)"
})
```

**Add column (one at a time):**
```javascript
// Step 1: Add column
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "ALTER TABLE entities ADD COLUMN status VARCHAR(50)"
})

// Step 2: Set default values
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "UPDATE entities SET status = 'active' WHERE status IS NULL"
})
```

### Data Manipulation

**Insert with tenant isolation:**
```javascript
usePower("dsql", "aurora-dsql", "execute", {
  "sql": `
    INSERT INTO entities (entity_id, tenant_id, name, tags)
    VALUES ($1, $2, $3, $4)
  `,
  "parameters": ["entity-456", "tenant-123", "My Entity", "tag1,tag2,tag3"]
})
```

**Batch update:**
```javascript
usePower("dsql", "aurora-dsql", "execute", {
  "sql": `
    UPDATE entities
    SET status = 'archived', updated_at = CURRENT_TIMESTAMP
    WHERE tenant_id = $1 AND created_at < $2
  `,
  "parameters": ["tenant-123", "2024-01-01"]
})
```

**Delete with validation:**
```javascript
// First check for dependents
const dependents = await usePower("dsql", "aurora-dsql", "query", {
  "sql": "SELECT COUNT(*) FROM objectives WHERE entity_id = $1 AND tenant_id = $2",
  "parameters": ["entity-456", "tenant-123"]
})

// Then delete if safe
if (dependents.rows[0].count === 0) {
  usePower("dsql", "aurora-dsql", "execute", {
    "sql": "DELETE FROM entities WHERE entity_id = $1 AND tenant_id = $2",
    "parameters": ["entity-456", "tenant-123"]
  })
}
```

### Schema Exploration

**List all tables:**
```javascript
usePower("dsql", "aurora-dsql", "list_tables", {})
// Returns: ["entities", "objectives", "key_results", ...]
```

**Describe table structure:**
```javascript
usePower("dsql", "aurora-dsql", "describe_table", {
  "table_name": "entities"
})
// Returns: { columns: [...], indexes: [...], constraints: [...] }
```

## Combining Tools (Workflows)

### Workflow 1: Create Multi-Tenant Schema

```javascript
// Step 1: Create main table
usePower("dsql", "aurora-dsql", "execute", {
  "sql": `
    CREATE TABLE IF NOT EXISTS entities (
      entity_id VARCHAR(255) PRIMARY KEY,
      tenant_id VARCHAR(255) NOT NULL,
      name VARCHAR(255) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `
})

// Step 2: Create tenant index (ASYNC required)
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "CREATE INDEX ASYNC idx_entities_tenant ON entities(tenant_id)"
})

// Step 3: Create composite index for common queries
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "CREATE INDEX ASYNC idx_entities_tenant_created ON entities(tenant_id, created_at DESC)"
})

// Step 4: Verify schema
usePower("dsql", "aurora-dsql", "describe_table", {
  "table_name": "entities"
})
```

### Workflow 2: Safe Data Migration

```javascript
// Step 1: Add new column
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "ALTER TABLE entities ADD COLUMN status VARCHAR(50)"
})

// Step 2: Populate with default (in batches if needed)
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "UPDATE entities SET status = 'active' WHERE status IS NULL AND tenant_id = $1",
  "parameters": ["tenant-123"]
})

// Step 3: Verify migration
const result = await usePower("dsql", "aurora-dsql", "query", {
  "sql": "SELECT COUNT(*) as total, COUNT(status) as with_status FROM entities WHERE tenant_id = $1",
  "parameters": ["tenant-123"]
})

// Step 4: Create index for new column
usePower("dsql", "aurora-dsql", "execute", {
  "sql": "CREATE INDEX ASYNC idx_entities_status ON entities(tenant_id, status)"
})
```

### Workflow 3: Application-Layer Foreign Key Validation

```javascript
// Step 1: Validate parent exists
const parent = await usePower("dsql", "aurora-dsql", "query", {
  "sql": "SELECT entity_id FROM entities WHERE entity_id = $1 AND tenant_id = $2",
  "parameters": ["parent-123", "tenant-123"]
})

if (parent.rows.length === 0) {
  throw new Error("Invalid parent reference")
}

// Step 2: Insert child record
usePower("dsql", "aurora-dsql", "execute", {
  "sql": `
    INSERT INTO objectives (objective_id, entity_id, tenant_id, title)
    VALUES ($1, $2, $3, $4)
  `,
  "parameters": ["obj-456", "parent-123", "tenant-123", "My Objective"]
})
```

## Configuration

**Authentication Required**: AWS IAM credentials

**Environment Variables:**
- `CLUSTER` - Your DSQL cluster identifier (e.g., "abc123def456")
- `REGION` - AWS region (e.g., "us-east-1")
- `AWS_PROFILE` - AWS CLI profile (optional, uses default if not set)

**Setup Steps:**
1. Create Aurora DSQL cluster in AWS Console
2. Note your cluster identifier from the console
3. Ensure AWS credentials are configured (`aws configure`)
4. Install this power and configure environment variables
5. Test connection with `list_tables` tool

**Permissions Required:**
- `dsql:DbConnect` - Connect to DSQL cluster
- `dsql:DbConnectAdmin` - Admin access for DDL operations

**Database Name**: Always use `postgres` (only database available in DSQL)

## Best Practices

- **SHOULD read guidelines first** - Check [development_guide.md](steering/development-guide.md) before making schema changes
- **SHOULD Execute queries directly** - PREFER MCP tools for ad-hoc queries 
- **REQUIRED: Follow DDL Guidelines** - Refer to [DDL Rules](steering/development-guide.md#schema-ddl-rules)
- **SHALL repeatedly generate fresh tokens** - Refer to [Connection Limits](steering/development-guide.md#connection-rules)
- **ALWAYS use ASYNC indexes** - `CREATE INDEX ASYNC` is mandatory
- **MUST Serialize arrays/JSON as TEXT** - Store arrays/JSON as TEXT (comma separated, JSON.stringify)
- **ALWAYS Batch under 3,000 rows** - maintain transaction limits
- **REQUIRED: Use parameterized queries** - Prevent SQL injection with $1, $2 placeholders
- **MUST follow correct Application Layer Patterns** - when multi-tenant isolation or application referential itegrity are required; refer to [Application Layer Patterns](steering/development-guide.md#application-layer-patterns)
- **REQUIRED use DELETE for truncation** - DELETE is the only supported operation for truncation
- **SHOULD test any migrations** - Verify DDL on dev clusters before production
- **SHOULD use partial indexes** - For sparse data with WHERE clauses
- **Plan for Scale** - DSQL is designed to optimize for massive scales without latency drops
- **SHOULD use connection pooling in production applications** - Refer to [Connection Pooling](steering/development-guide.md#connection-pooling-recommended)
- **SHOULD debug with the troubleshooting guide:** - Always refer to the resources and guidelines in [troubleshooting.md](steering/troubleshooting.md)

## Additional Resources

- [Aurora DSQL Documentation](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/)
- [Aurora DSQL Starter Kit](https://github.com/awslabs/aurora-dsql-starter-kit/tree/main)
- [Code Samples Repository](https://github.com/aws-samples/aurora-dsql-samples)
- [IAM Authentication Guide](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/using-database-and-iam-roles.html)
- [Getting Started Guide](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/getting-started.html)
- [What Comaptibility DSQL Supports with PostgreSQL](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-postgresql-compatibility.html)
- [Incompatible Postgres Features](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-postgresql-compatibility-unsupported-features.html)
- [CloudFormation Resource](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-dsql-cluster.html)

