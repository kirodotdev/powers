---
name: "checkout-api-reference"
displayName: "Checkout.com Global Payments"
description: "Access Checkout.com's comprehensive API documentation with intelligent search and detailed operation information for payments, customers, disputes, and more."
version: "1.0.0"
author: "Checkout.com"
keywords:
  - "checkout"
  - "payments"
  - "api"
  - "documentation"
  - "openapi"
  - "fintech"
  - "payment processing"
  - "customers"
  - "disputes"
  - "issuing"
  - "workflows"
  - "identity verification"
  - "mcp"
  - "reference"
---

# Checkout.com Developer Experience MCP

This power provides access to Checkout.com's comprehensive API documentation through a Model Context Protocol (MCP) server. It enables AI assistants to search, explore, and understand Checkout.com's payment processing APIs with over 189 operations covering payments, customers, disputes, issuing, platforms, workflows, and identity verification.

## What This Power Does

The Checkout.com Developer Experience MCP acts as an intelligent documentation assistant that can:

- **Search API Operations**: Find relevant endpoints by keywords, functionality, or business domain
- **Explore API Structure**: Browse operations by tags and categories
- **Get Detailed Documentation**: Retrieve comprehensive information about specific endpoints including parameters, responses, and examples
- **Access Schema Definitions**: Get detailed schema information for request/response objects
- **Understand API Relationships**: Discover how different endpoints work together

## Key Features

### Comprehensive API Coverage
Access to all Checkout.com API operations including:
- **Payments**: Process payments, refunds, captures, and voids
- **Customers**: Manage customer profiles and payment instruments  
- **Disputes**: Handle chargebacks and dispute management
- **Issuing**: Card issuing and management capabilities
- **Platforms**: Multi-entity and marketplace functionality
- **Workflows**: Automated business logic and event handling
- **Identity Verification**: KYC and identity checking services

### Intelligent Search
- Keyword-based search across operation IDs, paths, summaries, and descriptions
- Tag-based filtering for specific API domains
- Fuzzy matching to find relevant operations even with partial information

### Detailed Documentation Access
- Complete operation details including HTTP methods, paths, and parameters
- Request/response schema definitions with examples
- Error codes and handling information
- Authentication and authorization requirements

## When to Use This Power

This power is ideal for:

- **API Integration Planning**: Understanding available endpoints and their capabilities
- **Development Support**: Getting detailed parameter and response information during coding
- **API Exploration**: Discovering new functionality and understanding API structure
- **Troubleshooting**: Finding relevant endpoints for specific use cases
- **Documentation Generation**: Creating comprehensive API documentation and guides

## Available Tools

### docssearch
Search through Checkout.com's API documentation for operations matching specific keywords.

**Use Cases:**
- Find payment-related endpoints: "payment", "charge", "transaction"
- Discover customer management APIs: "customer", "profile", "account"
- Locate dispute handling operations: "dispute", "chargeback", "refund"

### openapilistOperations  
List and filter API operations with advanced filtering capabilities.

**Use Cases:**
- Browse all operations in a specific domain (e.g., "Payments", "Customers")
- Find operations containing specific terms
- Get an overview of available functionality

### openapigetOperation
Get comprehensive details about a specific API operation.

**Use Cases:**
- Understand exact parameters required for an endpoint
- Get response schema and example data
- Learn about authentication requirements
- Find related operations and workflows

### openapigetSchema
Retrieve detailed schema definitions for request/response objects.

**Use Cases:**
- Understand data structures for API requests
- Validate request/response formats
- Generate client code with proper type definitions
- Create comprehensive API documentation

### markdownsearch
Search through additional markdown documentation for contextual information.

**Use Cases:**
- Find implementation guides and best practices
- Locate troubleshooting information
- Discover integration patterns and examples

## Example Workflows

### Finding Payment Processing Endpoints
1. Use `docssearch` with query "payment process" to find relevant operations
2. Use `openapigetOperation` to get detailed information about specific endpoints
3. Use `openapigetSchema` to understand request/response structures

### Understanding Customer Management
1. Use `openapilistOperations` with tag "Customers" to see all customer-related endpoints
2. Explore specific operations like customer creation, updates, and retrieval
3. Get schema definitions for customer objects and related data structures

### Exploring Dispute Handling
1. Search for dispute-related operations using `docssearch`
2. Get detailed operation information to understand the dispute lifecycle
3. Access schema definitions for dispute objects and status updates

## Integration Benefits

- **Faster Development**: Quickly find and understand the right APIs for your use case
- **Reduced Documentation Overhead**: Get answers without manually browsing extensive documentation
- **Better API Understanding**: Discover relationships between different endpoints and workflows
- **Improved Code Quality**: Access to complete schema definitions ensures proper implementation
- **Enhanced Troubleshooting**: Quickly find relevant endpoints and understand their behavior

## Technical Architecture

This power runs as an MCP server that:
- Loads and parses Checkout.com's OpenAPI specification
- Provides intelligent search and filtering capabilities
- Serves detailed documentation through standardized MCP tools
- Maintains up-to-date API information through bundled documentation

The power is built with .NET 9.0 and follows clean architecture principles with comprehensive test coverage.

---

## Privacy & Support

### Privacy Policy
For information about how Checkout.com collects, stores, and processes user data, please review our [Privacy Policy](https://www.checkout.com/legal/privacy-policy).

### Service Information
This power connects to Checkout.com's Developer Experience MCP service, which provides access to our API documentation and developer resources. The service is hosted and maintained by Checkout.com.

### Support
For technical support, questions, or to report issues with this power, please contact our support team:
- [Checkout.com Support Center](https://support.checkout.com/hc/en-us)

For API-related questions and developer resources, visit our [Developer Documentation](https://www.checkout.com/docs/).