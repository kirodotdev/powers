---
name: "checkout-api-reference"
displayName: "Checkout.com Global Payments"
description: "Access Checkout.com's comprehensive API documentation with intelligent search and detailed operation information for payments, customers, disputes, and more."
version: "2.3.0"
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
  - "support"
  - "troubleshooting"
  - "mcp"
  - "reference"
---

# Checkout.com Global Payments

This power provides access to Checkout.com's comprehensive API documentation. It enables AI assistants to search, explore, and understand Checkout.com's payment processing APIs covering payments, customers, disputes, issuing, platforms, workflows, and identity verification, plus developer documentation and support content.

## What This Power Does

This power acts as an intelligent documentation assistant that can:

- **Search API Operations**: Find relevant endpoints using Lucene full-text search with fuzzy matching and typo tolerance
- **Search Documentation**: Find relevant guides, tutorials, and conceptual content (returns document pointers)
- **Read Documentation Pages**: Fetch the full text of a documentation page, one chunk at a time
- **Search Support Content**: Find troubleshooting guides, FAQs, and account management topics from the support site
- **Explore API Structure**: Browse operations by tags and categories
- **Get Operation Details**: Retrieve simplified, token-efficient information about specific endpoints
- **Access Schema Definitions**: Get detailed schema information for request/response objects

All tools are read-only: this power searches and reads Checkout.com's documentation and API reference. It never creates, modifies, or deletes anything, and it does not process live payments.

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
- The main API call creates a Payment Session - use `api_search` for "payment session" then `get_operation` and `get_schema` to explore it

### API-to-API (Direct Integration)
If the user needs full control over the payment experience, they should use the payment API endpoints directly. This is for:
- Server-to-server payment processing
- Custom payment UIs
- Complex payment flows (split payments, marketplace payouts, recurring billing)
- Backend-only integrations with no frontend

**Start with:** `api_search` for "payment" or `list_operations` with tag "Payments" to explore available endpoints.

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
- Separate indexes for the API reference, developer documentation, and the support site

### Token-Efficient Responses
- `get_operation` returns simplified responses: parameters show only essential info (name, location, required, type)
- Request bodies show schema names with hints to use `get_schema` for details
- Responses grouped into success/error categories
- `docs_search` returns compact document pointers; full page text is fetched on demand with `docs_fetch`

## When to Use This Power

This power is ideal for:

- **API Integration Planning**: Understanding available endpoints and their capabilities
- **Development Support**: Getting detailed parameter and response information during coding
- **API Exploration**: Discovering new functionality and understanding API structure
- **Troubleshooting**: Finding relevant endpoints, documentation, and support articles for specific use cases

## Available Tools

The server exposes eight tools. Tool names are shown exactly as they appear over the wire (snake_case).

### `guide`
Get integration guidance for Checkout.com's payment APIs. Call this first to understand the two integration paths: Flow (prebuilt payment UI with minimal code) or API-to-API (direct REST integration with full control). Returns structured recommendations, getting-started steps, and links to relevant documentation for each path.

**Use Cases:**
- Determine which integration approach fits the user's needs
- Get step-by-step onboarding for Flow or direct API integration
- Discover the key operations and npm packages for each path

**When to use:** At the start of any conversation about integrating with Checkout.com, before exploring specific endpoints.

### `api_search`
Search the Checkout.com OpenAPI specification using Lucene full-text search with fuzzy matching, typo tolerance, and relevance ranking. Searches across operationId, path, summary, description, and tags, and also returns matching schemas.

**Use Cases:**
- Find payment-related endpoints: "payment", "charge", "transaction"
- Discover customer management APIs: "customer", "profile", "account"
- Locate dispute handling operations: "dispute", "chargeback", "refund"
- Search for schema definitions: "PaymentRequest", "Customer"

**When to use:** You need to find specific API endpoints, operation IDs, HTTP methods, paths, or schema definitions.

### `list_operations`
List all API operations from the Checkout.com OpenAPI specification, with optional filtering by tag or text.

**Use Cases:**
- Browse all operations in a specific domain (e.g., "Payments", "Customers")
- Find operations containing specific terms
- Get an overview of available functionality

### `get_operation`
Get detailed information about a specific API operation by operationId. Returns a simplified, token-efficient response with parameters, request body schema names, grouped response codes, and required scopes.

**Use Cases:**
- Understand parameters required for an endpoint
- See which schemas are used in request bodies (use `get_schema` for full details)
- Check success/error response codes
- Learn about authentication requirements

### `get_schema`
Get a schema definition by name from the Checkout.com OpenAPI specification (components/schemas).

**Use Cases:**
- Understand data structures for API requests
- Validate request/response formats
- Generate client code with proper type definitions

### `docs_search`
Search Checkout.com's developer documentation (guides, tutorials, webhooks, authentication, 3D Secure, and more) using Lucene full-text search with fuzzy matching and relevance ranking. Returns a ranked list of **document pointers**, not page content: each result has a `urlPath`, `whyMatched` (a short preview snippet, not the full answer), `summary`, `totalChunks`, and `matchedChunk`.

**Use Cases:**
- Find implementation guides: "Flow integration", "3D Secure setup"
- Locate best practices: "payment security", "error handling"
- Discover integration patterns: "webhook configuration", "authentication"

**When to use:** You need to find the right documentation page. This is the first half of a two-step contract — pick the best result, then call `docs_fetch` to read the page. Do not answer from the `whyMatched` snippet alone.

### `docs_fetch`
Read the actual content of a documentation page. This is the only docs tool that returns full page text. Pass the `urlPath` from a `docs_search` result (start with its `matchedChunk`), and page through additional chunks (1..`totalChunks`, following `hasMore`) when you need more context. Returns `{ urlPath, chunk, totalChunks, hasMore, content }`; most pages are a single chunk.

**Use Cases:**
- Read the page behind a `docs_search` result before quoting or answering
- Page through longer guides one chunk at a time

**When to use:** Immediately after `docs_search`, whenever you need to read or quote documentation content.

### `support_search`
Search Checkout.com's support site using Lucene full-text search with fuzzy matching. Find troubleshooting guides, FAQs, account management topics, and common error resolutions.

**Use Cases:**
- Resolve common errors and integration issues
- Answer account management and operational questions
- Find troubleshooting steps that live on the support site rather than in the developer docs

**When to use:** The question is operational or troubleshooting-oriented, or the answer is more likely on the support site than in the API reference or developer docs.

## Example Workflows

### Starting a New Integration
1. Call `guide` to understand the two integration paths (Flow vs API-to-API)
2. Based on the user's needs, follow the recommended path

### Finding Payment Processing Endpoints
1. Use `api_search` with query "payment process" to find relevant API operations
2. Use `get_operation` to get information about specific endpoints
3. Use `get_schema` to understand request/response structures

### Understanding Customer Management
1. Use `list_operations` with tag "Customers" to see all customer-related endpoints
2. Explore specific operations like customer creation, updates, and retrieval
3. Get schema definitions for customer objects and related data structures

### Reading a Documentation Guide
1. Use `docs_search` with query "Flow integration" to find the right page (returns pointers)
2. Call `docs_fetch` with the best result's `urlPath` and `matchedChunk` to read the page
3. Page through further chunks while `hasMore` is true if you need more of the guide

### Troubleshooting an Issue
1. Use `support_search` with a description of the error or account question
2. Fall back to `docs_search` + `docs_fetch` for deeper implementation detail if needed

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
