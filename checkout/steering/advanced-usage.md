# Advanced Usage Guide - Checkout.com Developer Experience MCP

This guide covers advanced techniques and patterns for maximizing the value of the Checkout.com Developer Experience MCP in complex integration scenarios.

Tool names are shown exactly as they appear over the wire (snake_case). The server exposes eight read-only tools: `guide`, `api_search`, `list_operations`, `get_operation`, `get_schema`, `docs_search`, `docs_fetch`, and `support_search`.

## Official Resources

Before diving into advanced usage, familiarize yourself with Checkout.com's official resources:
- [Payment Authentication](https://www.checkout.com/docs/payments/authenticate-payments)
- [Marketplace Solutions](https://www.checkout.com/solutions/marketplaces)
- [Dispute Management](https://www.checkout.com/docs/disputes)
- [Workflow Automation](https://www.checkout.com/docs/workflows)
- [Security and Compliance](https://www.checkout.com/docs/payments/ensure-regulatory-compliance)

## Advanced Search Techniques

### Multi-Step Discovery Workflows

For complex integrations, use a systematic approach to discover and understand related operations:

1. **Domain Exploration**
   ```
   list_operations with tag "Payments"
   list_operations with tag "Workflows"
   api_search for "webhook"
   ```

2. **Relationship Mapping**
   ```
   get_operation for createPayment
   get_schema for PaymentRequest
   get_schema for PaymentResponse
   api_search for "payment capture"
   ```

3. **Error Scenario Planning**
   ```
   api_search for "void"
   api_search for "refund"
   get_operation for disputePayment
   ```

### Schema Deep Diving

Understanding complex data structures requires systematic schema exploration:

1. **Identify Core Schemas**
   ```
   get_schema for PaymentRequest
   get_schema for CustomerRequest
   get_schema for WebhookEvent
   ```

2. **Explore Nested Objects**
   - `get_operation` shows schema names referenced in request bodies
   - Use `get_schema` to follow those references and understand full structures
   - Map required vs optional fields across related schemas

3. **Validate Data Flow**
   - Trace how data flows from request to response
   - Understand which response fields become input for subsequent operations
   - Identify shared data structures across operations

## Complex Integration Patterns

### Multi-Step Payment Flows

For sophisticated payment processing:

1. **Authorization and Capture Pattern**
   ```
   get_operation for authorizePayment
   get_operation for capturePayment
   get_schema for AuthorizationRequest
   get_schema for CaptureRequest
   ```

2. **Payment Instrument Management**
   ```
   api_search for "instrument"
   get_operation for createPaymentInstrument
   get_operation for updatePaymentInstrument
   ```

3. **Recurring Payment Setup**
   ```
   api_search for "recurring"
   api_search for "subscription"
   get_schema for RecurringPaymentRequest
   ```

### Platform and Marketplace Integrations

For multi-entity scenarios:

1. **Sub-Entity Management**
   ```
   list_operations with tag "Platforms"
   get_operation for createSubEntity
   get_schema for SubEntityRequest
   ```

2. **Split Payment Scenarios**
   ```
   api_search for "split"
   api_search for "marketplace"
   get_schema for SplitPaymentRequest
   ```

3. **Onboarding Workflows**
   ```
   api_search for "onboard"
   get_operation for uploadDocument
   get_schema for OnboardingRequest
   ```

### Advanced Dispute Management

For comprehensive dispute handling:

1. **Dispute Lifecycle Management**
   ```
   get_operation for getDispute
   get_operation for acceptDispute
   get_operation for provideDisputeEvidence
   get_schema for DisputeEvidence
   ```

2. **Chargeback Prevention**
   ```
   api_search for "alert"
   api_search for "prevention"
   get_operation for getDisputeAlert
   ```

## Working With Documentation and Support Content

### The docs_search / docs_fetch Two-Step Contract

`docs_search` returns document pointers (`urlPath`, `whyMatched`, `summary`, `totalChunks`, `matchedChunk`), never full page text. Always follow up with `docs_fetch` to read the page.

1. **Find the Page**
   ```
   docs_search for "3D Secure setup"
   ```

2. **Read the Page**
   ```
   docs_fetch with the best result's urlPath, starting at its matchedChunk
   ```

3. **Page Through Longer Guides**
   - Read `totalChunks` and `hasMore` from the response
   - Fetch chunks 1..totalChunks while `hasMore` is true
   - Most pages are a single chunk, so one fetch is usually the whole page

### Choosing the Right Search Tool

- `api_search` - the OpenAPI reference (operations and schemas)
- `docs_search` + `docs_fetch` - developer documentation (guides, tutorials, concepts)
- `support_search` - the support site (troubleshooting, FAQs, account and operational topics)

## Workflow Automation Patterns

### Event-Driven Architecture

Understanding webhook and event patterns:

1. **Event Type Discovery**
   ```
   docs_search for "webhook events", then docs_fetch the best page
   get_schema for WebhookEvent
   api_search for "event"
   ```

2. **Workflow Configuration**
   ```
   list_operations with tag "Workflows"
   get_operation for createWorkflow
   get_schema for WorkflowRequest
   ```

### Identity Verification Workflows

For KYC and compliance:

1. **Verification Process Discovery**
   ```
   list_operations with tag "Identity Verification"
   get_operation for createIdentityVerification
   get_schema for IdentityVerificationRequest
   ```

2. **Document Management**
   ```
   api_search for "document"
   get_operation for uploadDocument
   get_schema for DocumentRequest
   ```

## Performance and Optimization

### Efficient Tool Usage

1. **Start with Search** - Use `api_search` or `docs_search` to find relevant operations or pages first
2. **Get Simplified Details** - `get_operation` returns token-efficient responses
3. **Drill into Schemas** - Only call `get_schema` when you need full data structure details
4. **Use Tag Filtering** - `list_operations` with a tag is more efficient than broad searches
5. **Fetch Docs on Demand** - `docs_search` returns compact pointers; only `docs_fetch` the pages you actually need

### Token-Efficient Workflows

The `get_operation` tool returns simplified responses by default:
- Parameters show only name, location, required status, and type
- Request bodies show schema names with hints to use `get_schema`
- Responses are grouped into success/error code arrays
- Security shows only required scopes

Similarly, `docs_search` keeps result payloads small by returning pointers plus short preview snippets, deferring full page text to `docs_fetch`.

## Security and Compliance

### Authentication Deep Dive

1. **Auth Method Discovery**
   ```
   docs_search for "authentication", then docs_fetch the page
   docs_search for "authorization", then docs_fetch the page
   ```

2. **Token Management**
   ```
   api_search for "token"
   get_operation for createToken
   get_schema for TokenRequest
   ```

### PCI and Compliance

1. **Secure Data Handling**
   ```
   docs_search for "PCI compliance", then docs_fetch the page
   docs_search for "sensitive data", then docs_fetch the page
   ```

2. **Audit and Logging**
   ```
   api_search for "audit"
   api_search for "log"
   ```

## Best Practices for Power Usage

### Systematic Exploration
- Always start with broad searches and narrow down
- Use schema exploration to understand data relationships
- Map complete workflows before implementation

### Continuous Learning
- Regularly explore new API areas as your integration grows
- Stay updated with new operations and schema changes
- Use the power to understand deprecation notices and migration paths

## Additional Resources

For comprehensive implementation guidance, consult these official resources:
- [Checkout.com Developer Portal](https://www.checkout.com/docs/)
- [API Status and Updates](https://status.checkout.com/)
- [Testing and Test Cards](https://www.checkout.com/docs/testing/test-cards)
- [API Authentication](https://www.checkout.com/docs/resources/api-authentication/)
