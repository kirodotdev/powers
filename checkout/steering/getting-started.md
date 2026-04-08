# Getting Started with Checkout.com Developer Experience MCP

This guide will help you quickly start using the Checkout.com Developer Experience MCP to explore and understand Checkout.com's payment processing APIs.

## Official Documentation

For comprehensive information about Checkout.com's APIs, refer to the official documentation:
- [Checkout.com API Documentation](https://www.checkout.com/docs/)
- [API Reference](https://api-reference.checkout.com/)
- [Get Started Guide](https://www.checkout.com/docs/get-started)
- [SDKs](https://www.checkout.com/docs/integrate/sdks)

## Quick Start

### First: Determine the Integration Path

The most important question to ask is: **what kind of payment integration does the user need?**

#### Flow (Prebuilt Payment UI)
If the user wants to accept payments on their website with minimal effort, guide them to **Flow** - Checkout.com's prebuilt payment interface.

Flow manages the entire payment experience: tokenization, payment method display, customer data capture, 3D Secure authentication, and redirects. The user creates a Payment Session server-side, then mounts Flow client-side using the `@checkout.com/checkout-web-components` npm package.

**Key steps for Flow:**
1. Create a Payment Session (`CreatePaymentSession` endpoint)
2. Install `@checkout.com/checkout-web-components`
3. Initialize `CheckoutWebComponents` with the payment session and public key
4. Mount Flow onto the page with `checkout.create('flow').mount('#container')`
5. Handle payment response via webhooks or `onPaymentCompleted` callback

**Resources:**
- [Get started with Flow](https://www.checkout.com/docs/get-started)
- [Customize Flow](https://www.checkout.com/docs/payments/accept-payments/accept-a-payment-on-your-website/customize-your-flow-integration)
- [Add localization](https://www.checkout.com/docs/payments/accept-payments/accept-a-payment-on-your-website/add-localization-to-your-flow-integration)

Use `ApiSearch` with "payment session" to find the relevant operationId, then `GetOperation` and `GetSchema` for `PaymentSessionRequest` to explore the server-side setup.

#### API-to-API (Direct Integration)
If the user needs full control, custom UI, or server-to-server processing, they should use the payment API endpoints directly. Start exploring with `ApiSearch` for "payment" or `ListOperations` with tag "Payments".

---

Once the integration path is clear, you have access to six tools for exploring the API:

### 1. Get Integration Guidance (`Guide`)

Start here. The `Guide` tool returns structured guidance on the two integration paths (Flow vs API-to-API), including getting-started steps, relevant documentation links, and suggested next tools to call.

```
Call Guide to understand integration options
```

### 2. Search for API Operations (`ApiSearch`)

The fastest way to find relevant API endpoints is through keyword search:

```
Search for payment processing endpoints
```

This will use the `ApiSearch` tool to find operations related to payments. Supports fuzzy matching so typos like "paymnt" still find results. You can search for:
- **Business functions**: "payment", "refund", "customer", "dispute"
- **Technical terms**: "webhook", "authentication", "token"
- **Specific operations**: "create", "update", "delete", "list"

### 3. Browse Operations by Category (`ListOperations`)

To explore operations in a specific domain:

```
List all customer-related operations
```

This helps you understand the full scope of functionality available in each API domain.

### 4. Get Operation Information (`GetOperation`)

Once you find an interesting operation, get its details:

```
Get details for the createPayment operation
```

This provides a simplified, token-efficient response including:
- HTTP method and path
- Parameter names, locations, and types
- Request body schema names (with hints to use `GetSchema` for full details)
- Success and error response codes
- Required authentication scopes

### 5. Understand Data Structures (`GetSchema`)

To understand the data structures used in requests and responses:

```
Get the schema definition for PaymentRequest
```

This is essential for:
- Understanding required fields
- Validating data formats
- Generating client code
- Creating proper API requests

### 6. Search Documentation (`DocsSearch`)

For additional context and implementation guidance:

```
Search for webhook implementation examples
```

## Common Use Cases

### Planning a Payment Integration

1. **Discover Payment Operations**
   ```
   Search for payment processing operations
   ```

2. **Understand Payment Flow**
   ```
   Get details for createPayment operation
   Get schema for PaymentRequest
   ```

3. **Explore Related Operations**
   ```
   List operations containing "payment"
   Get details for capturePayment operation
   Get details for refundPayment operation
   ```

### Setting Up Customer Management

1. **Find Customer Operations**
   ```
   List operations with tag "Customers"
   ```

2. **Understand Customer Creation**
   ```
   Get details for createCustomer operation
   Get schema for CustomerRequest
   ```

3. **Explore Customer Lifecycle**
   ```
   Get details for updateCustomer operation
   Get details for deleteCustomer operation
   ```

### Handling Disputes and Chargebacks

1. **Discover Dispute Operations**
   ```
   Search for dispute and chargeback operations
   ```

2. **Understand Dispute Process**
   ```
   Get details for getDispute operation
   Get schema for DisputeResponse
   ```

### Implementing Webhooks

1. **Find Webhook Information**
   ```
   Search documentation for webhook setup
   Search for webhook-related operations
   ```

2. **Understand Event Types**
   ```
   Get schema for WebhookEvent
   Search documentation for event types
   ```

## Tips for Effective Usage

### Search Strategy
- Start with broad terms like "payment" or "customer"
- Fuzzy matching handles 1-character typos automatically
- Use specific operation names when you know them

### Understanding Relationships
- Operations often work together in workflows
- Use `GetSchema` to understand data flow between operations
- Look for common parameters that link operations

### Schema Exploration
- `GetOperation` shows schema names in request bodies - use `GetSchema` to get full details
- Pay attention to required vs optional fields
- Look for nested objects and their schemas

## Getting Help

If you need assistance:
- Use broad search terms to discover relevant operations
- Check schema definitions for data structure questions
- Search documentation for implementation guidance
- Explore related operations to understand complete workflows

For additional resources and detailed implementation guides, visit:
- [Checkout.com Developer Portal](https://www.checkout.com/docs/)
- [API Reference](https://api-reference.checkout.com/)
- [Webhook Management](https://www.checkout.com/docs/developer-resources/webhooks/manage-webhooks/)
- [Authentication Guide](https://www.checkout.com/docs/resources/api-authentication/)
