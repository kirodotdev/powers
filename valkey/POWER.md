---
name: "valkey"
displayName: "Valkey Integration in Kiro"
description: "Execute commands, manage data structures, and administer Valkey/Redis instances directly from Kiro."
keywords: ["valkey", "redis", "cache", "caching", "key-value", "database", "nosql", "in-memory", "data-structures", "cluster", "elasticache", "memorydb", "message-broker", "pubsub", "session"]
author: "Valkey Maintainers"
---

# Valkey

## Overview

The Valkey Power provides direct access to Valkey/Redis instances from within the Kiro IDE. Execute commands without leaving your development environment.

Valkey is a fast, open-source key-value store that you can use as a cache, message broker, or database. It maintains full compatibility with the Redis protocol while being developed openly under the Linux Foundation. Valkey focuses on high performance and reliability, supporting advanced features like vector search and indexing through community-maintained modules.

**Key capabilities:**
- **Direct Command Execution**: Run Valkey/Redis commands directly from Kiro
- **Data Structure Management**: Work with strings, lists, sets, hashes, and more
- **Server Administration**: Check memory usage, manage keys, and configure settings
- **SSL/TLS Support**: Secure connections with certificate-based authentication
- **Cluster Mode**: Support for Valkey Cluster deployments

**Authentication**: Supports username/password authentication and SSL/TLS encryption.

## Available MCP Servers

### valkey-mcp-server
**Package:** `awslabs.valkey-mcp-server@latest`

**Connection:** uvx-based MCP server

**Authentication:** Username/password with optional SSL/TLS

## Configuration

For more details about configuration, please check the [AWS MCP Servers Website.](https://awslabs.github.io/mcp/servers/valkey-mcp-server)

The server can be configured using environment variables. You can set these directly in the power's `mcp.json` file (can be accessed by the `Open powers config` button) or as system environment variables in your shell:

| Name | Description | Default Value |
|------|-------------|---------------|
| `VALKEY_HOST` | ElastiCache Primary Endpoint or MemoryDB Cluster Endpoint or Valkey IP or hostname | `"127.0.0.1"` |
| `VALKEY_PORT` | Valkey port | `6379` |
| `VALKEY_USERNAME` | Default database username | `None` |
| `VALKEY_PWD` | Default database password | `""` |
| `VALKEY_USE_SSL` | Enables or disables SSL/TLS | `false` |
| `VALKEY_CA_PATH` | CA certificate for verifying server | `None` |
| `VALKEY_SSL_KEYFILE` | Client's private key file | `None` |
| `VALKEY_SSL_CERTFILE` | Client's certificate file | `None` |
| `VALKEY_CERT_REQS` | Server certificate verification | `"required"` |
| `VALKEY_SSL_CA_CERTS` | Path to trusted CA certificates | `None` |
| `VALKEY_CLUSTER_MODE` | Enable Valkey Cluster mode | `false` |

**Setup Steps:**
1. Install this power in Kiro
2. Configure environment variables for your Valkey instance
3. Test connection with basic commands like `SET`
4. Start executing Valkey commands directly from Kiro

## Onboarding

### Quick Start

Ensure you have a running instance of a Valkey server before continuing.

#### Using JSON Configuration

You can configure environment variables directly in your `mcp.json` file. Here are examples for different scenarios:

**Local Instance (Default)**
```json
{
  "mcpServers": {
    "awslabs.valkey-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": {
        "VALKEY_HOST": "127.0.0.1",
        "VALKEY_PORT": "6379",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

**Remote Instance with Authentication**
```json
{
  "mcpServers": {
    "awslabs.valkey-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": {
        "VALKEY_HOST": "your-valkey-server.com",
        "VALKEY_PORT": "6379",
        "VALKEY_USERNAME": "your-username",
        "VALKEY_PWD": "your-password",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

**SSL/TLS Connection**
```json
{
  "mcpServers": {
    "awslabs.valkey-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": {
        "VALKEY_HOST": "secure-valkey-server.com",
        "VALKEY_PORT": "6380",
        "VALKEY_USE_SSL": "true",
        "VALKEY_SSL_CA_CERTS": "/path/to/ca.crt",
        "VALKEY_SSL_CERTFILE": "/path/to/client.crt",
        "VALKEY_SSL_KEYFILE": "/path/to/client.key",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

**Cluster Mode**
```json
{
  "mcpServers": {
    "awslabs.valkey-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": {
        "VALKEY_HOST": "cluster-endpoint.com",
        "VALKEY_PORT": "7000",
        "VALKEY_CLUSTER_MODE": "true",
        "VALKEY_USERNAME": "your-username",
        "VALKEY_PWD": "your-password",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

#### Using System Environment Variables

You can also reference system environment variables in your JSON configuration:

```json
{
  "mcpServers": {
    "awslabs.valkey-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.valkey-mcp-server@latest"],
      "env": {
        "VALKEY_HOST": "${VALKEY_HOST}",
        "VALKEY_PORT": "${VALKEY_PORT}",
        "VALKEY_PWD": "${VALKEY_PASSWORD}",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

Then set the environment variables in your shell:

1. **Connect to Local Instance**
   ```bash
   # Default connection (localhost:6379)
   # No additional configuration needed for local development
   ```

2. **Connect to Remote Instance**
   ```bash
   # Set environment variables
   export VALKEY_HOST="your-valkey-server.com"
   export VALKEY_PORT="6379" # Replace as needed
   export VALKEY_USERNAME="your-username"
   export VALKEY_PWD="your-password"
   ```

3. **Connect with SSL/TLS**
   ```bash
   # Enable SSL and provide certificates
   export VALKEY_USE_SSL="true"
   export VALKEY_SSL_CA_CERTS="/path/to/ca.crt"
   export VALKEY_SSL_CERTFILE="/path/to/client.crt"
   export VALKEY_SSL_KEYFILE="/path/to/client.key"
   ```

4. **Connect to Cluster**
   ```bash
   # Enable cluster mode
   export VALKEY_HOST="cluster-endpoint.com"
   export VALKEY_PORT="7000" # Replace as needed
   export VALKEY_CLUSTER_MODE="true"
   ```

## Example Prompts

Here are some example prompts to get you started with the Valkey Power:

**Note:** Before using these prompts, activate the power by saying "activate my Valkey power" so Kiro can access the Valkey tools.

### Basic Operations
- "Check if my Valkey server is responding with PING"
- "Set a key called 'user:123' with value 'John Doe'"
- "Get the value for key 'user:123'"
- "Delete the key 'temp:data'"
- "Show me all keys that start with 'user:'"

### Data Structures
- "Create a list called 'tasks' and add three items to it"
- "Add a new member to the set 'active_users'"
- "Set multiple fields in the hash 'user:profile:123'"
- "Get all members from the set 'categories'"
- "Pop an item from the list 'queue'"

### Server Management
- "Show me server information and statistics"
- "Check memory usage and key count"
- "List all connected clients"
- "Get configuration for maxmemory setting"
- "Monitor real-time commands being executed"

### Advanced Operations
- "Set a key with expiration time of 1 hour"
- "Check the TTL (time to live) for key 'session:abc123'"
- "Perform a transaction with MULTI/EXEC"
- "Use a Lua script to atomically increment multiple counters"
- "Search for keys matching pattern 'cache:*'"

### Troubleshooting
- "Check if key 'user:456' exists"
- "Show me the type of data stored in key 'analytics:data'"
- "Get the size of the list 'notifications'"
- "Check server memory usage and fragmentation"
- "Show me slow queries from the slow log"

## Troubleshooting

**Error: "Connection refused"**
- Check if Valkey server is running
- Verify `VALKEY_HOST` and `VALKEY_PORT` settings
- Ensure firewall allows connections on the specified port

**Error: "Authentication failed"**
- Verify `VALKEY_USERNAME` and `VALKEY_PWD` are correct
- Check if the user has necessary permissions
- Ensure authentication is enabled on the server

**Error: "SSL connection failed"**
- Verify SSL certificates are valid and accessible
- Check `VALKEY_SSL_CA_CERTS`, `VALKEY_SSL_CERTFILE`, and `VALKEY_SSL_KEYFILE`
- Ensure server supports SSL/TLS connections

---

**Package:** awslabs.valkey-mcp-server
**Source:** AWS Labs
**License:** Apache-2.0