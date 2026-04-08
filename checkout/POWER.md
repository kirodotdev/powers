---
name: "checkout-api-reference"
displayName: "Checkout.com Global Payments"
description: "Access Checkout.com's comprehensive API documentation with intelligent search and detailed operation information for payments, customers, disputes, and more."
version: "2.0.0"
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

# Checkout.com Global Payments

This power provides access to Checkout.com's comprehensive API documentation. It enables AI assistants to search, explore, and understand Checkout.com's payment processing APIs covering payments, customers, disputes, issuing, platforms, workflows, and identity verification.

## What This Power Does

This power acts as an intelligent documentation assistant that can:

- **Search API Operations**: Find relevant endpoints using Lucene full-text search with fuzzy matching and typo tolerance
- **Search Documentation**: Find relevant guides, tutorials, and conceptual content
- **Explore API Structure**: Browse operations by tags and categories
- **Get Operation Details**: Retrieve simplified, token-efficient information about specific endpoints
- **Access Schema Definitions**: Get detailed schema information for request/response objects

## Important: Understand the Integration Path First

Before diving into API operations, determine which integration path the user needs:

### Flow (Prebuilt Payment UI)
If the user wants to accept payments with minimal effort, steer them towards **Flow** - Checkout.com's prebuilt payment interface. Flow handles:
- Tokenizing sensitive payment details (PCI compliant out of the box)
- Displaying available payment methods
- Capturing additional customer data
- 3D Secure authentication and redirects

**Flow is the right choice when:**
- The user wants a drop-in payment form on their website
- They want to get up and running quickly
- They don't need deep customization of the payment UI
- They want Checkout.com to manage the end-to-end payment experience

**Key resources for Flow:**
- [Get started with Flow](https://www.checkout.com/docs/get-started)
- [Customize Flow](https://www.checkout.com/docs/payments/accept-payments/accept-a-payment-on-your-website/customize-your-flow-integration)
- npm package: `@checkout.com/checkout-web-components`
- The main API call creates a Payment Session - use `ApiSearch` for "payment session" then `GetOperation` and `GetSchema` to explore it

### API-to-API (Direct Integration)
If the user needs full control over the payment experience, they should use the payment API endpoints directly. This is for:
- Server-to-server payment processing
- Custom payment UIs
- Complex payment flows (split payments, marketplace payouts, recurring billing)
- Backend-only integrations with no frontend

**Start with:** `ApiSearch` for "payment" or `ListOperations` with tag "Payments" to explore available endpoints.

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
- Lucene full-text search with fuzzy matching and typo tolerance
- Handles 1-character typos (e.g. "paymnt" finds "payment")
- Relevance-ranked results with scoring
- Tag-based filtering for specific API domains

### Token-Efficient Responses
- `GetOperation` returns simplified responses (~300 tokens vs ~1,200 previously)
- Parameters show only essential info: name, location, required, type
- Request bodies show schema names with hints to use `GetSchema()` for details
- Responses grouped into success/error categories

## When to Use This Power

This power is ideal for:

- **API Integration Planning**: Understanding available endpoints and their capabilities
- **Development Support**: Getting detailed parameter and response information during coding
- **API Exploration**: Discovering new functionality and understanding API structure
- **Troubleshooting**: Finding relevant endpoints for specific use cases

## Available Tools

### Guide
Get integration guidance for Checkout.com's payment APIs. Call this first to understand the two integration paths: Flow (prebuilt payment UI with minimal code) or API-to-API (direct REST integration with full control). Returns structured recommendations, getting-started steps, and links to relevant documentation for each path.

**Use Cases:**
- Determine which integration approach fits the user's needs
- Get step-by-step onboarding for Flow or direct API integration
- Discover the key operations and npm packages for each path

**When to use:** At the start of any conversation about integrating with Checkout.com, before exploring specific endpoints.

### ApiSearch
Search the Checkout.com OpenAPI specification using Lucene full-text search with fuzzy matching, typo tolerance, and relevance ranking. Searches across operationId, path, summary, description, and tags.

**Use Cases:**
- Find payment-related endpoints: "payment", "charge", "transaction"
- Discover customer management APIs: "customer", "profile", "account"
- Locate dispute handling operations: "dispute", "chargeback", "refund"
- Search for schema definitions: "PaymentRequest", "Customer"

**When to use:** You need to find specific API endpoints, operation IDs, HTTP methods, paths, or schema definitions.

### DocsSearch
Search through Checkout.com documentation using Lucene full-text search with fuzzy matching, typo tolerance, and relevance ranking. Returns relevant sections with context.

**Use Cases:**
- Find implementation guides: "Flow integration", "3D Secure setup"
- Locate best practices: "payment security", "error handling"
- Discover integration patterns: "webhook configuration", "authentication"

**When to use:** You need to understand how to implement features, follow tutorials, or learn about concepts and best practices.

### ListOperations
List all API operations from the Checkout.com OpenAPI specification, with optional filtering by tag or text.

**Use Cases:**
- Browse all operations in a specific domain (e.g., "Payments", "Customers")
- Find operations containing specific terms
- Get an overview of available functionality

### GetOperation
Get detailed information about a specific API operation by operationId. Returns a simplified, token-efficient response with parameters, request body schema names, grouped response codes, and required scopes.

**Use Cases:**
- Understand parameters required for an endpoint
- See which schemas are used in request bodies (use `GetSchema` for full details)
- Check success/error response codes
- Learn about authentication requirements

### GetSchema
Get a schema definition by name from the Checkout.com OpenAPI specification (components/schemas).

**Use Cases:**
- Understand data structures for API requests
- Validate request/response formats
- Generate client code with proper type definitions

## Example Workflows

### Starting a New Integration
1. Call `Guide` to understand the two integration paths (Flow vs API-to-API)
2. Based on the user's needs, follow the recommended path

### Finding Payment Processing Endpoints
1. Use `ApiSearch` with query "payment process" to find relevant API operations
2. Use `GetOperation` to get information about specific endpoints
3. Use `GetSchema` to understand request/response structures

### Understanding Customer Management
1. Use `ListOperations` with tag "Customers" to see all customer-related endpoints
2. Explore specific operations like customer creation, updates, and retrieval
3. Get schema definitions for customer objects and related data structures

### Learning About Integration Patterns
1. Use `DocsSearch` with query "Flow integration" to find implementation guides
2. Search for "webhook" to understand event notification setup
3. Look for "3D Secure" to learn about authentication flows

---

## Privacy & Support

### Privacy Policy
For information about how Checkout.com collects, stores, and processes user data, please review our [Privacy Policy](https://www.checkout.com/legal/privacy-policy).

### Service Information
This power connects to Checkout.com's MCP service at `https://docs.mcp.checkout.com/rpc`, which provides access to our API documentation and developer resources.

### Support
For technical support, questions, or to report issues with this power, please contact our support team:
- [Checkout.com Support Center](https://support.checkout.com/hc/en-us)

For API-related questions and developer resources, visit our [Developer Documentation](https://www.checkout.com/docs/).
