---
name: "polar"
displayName: "Polar"
description: "Monetization platform for developers - manage products, subscriptions, payments, and customer billing"
keywords: ["polar","monetization","payments","subscriptions","products","customers","orders","billing","saas","revenue","checkout"]
author: "Polar"
---

# Polar Power

## Overview

Build monetization features with Polar's developer-first payment platform. Accept payments, manage subscriptions, handle customer billing, and track revenue. This power provides access to Polar's APIs through an MCP server, enabling you to build production-ready monetization systems.

Use Polar Checkout for hosted payment pages, Products API for catalog management, or Subscriptions API for recurring billing. The platform handles payment processing via Stripe, provides customer portal, and supports multiple currencies.

**Key capabilities:**

- **Products**: Create digital products with flexible pricing models (one-time, recurring, usage-based)
- **Checkouts**: Hosted payment pages for seamless purchase flows
- **Subscriptions**: Recurring billing with automatic renewals and proration
- **Customers**: Manage customer data and payment methods
- **Orders**: Track purchases and fulfillment
- **Payments**: Monitor payment transactions
- **Metrics**: Revenue analytics and business insights
- **Benefits**: Grant features/perks when products are purchased

**Authentication**: Requires Organization Access Token (OAT) for server-side operations. Never expose in client code. Customer Access Tokens are for customer-facing operations only.

## Available MCP Servers

### polar

**Connection:** MCP server via npx
**Authorization:** Requires `POLAR_ACCESS_TOKEN` environment variable

## Best Practices

### Integration Approach

**Always prefer Checkout Sessions** for standard payment flows:

- One-time product purchases
- Subscription sign-ups
- Hosted checkout pages (Polar handles UI)

**Use Products API** to:

- Create and manage your product catalog
- Define pricing models (recurring, one-time, usage-based)
- Configure benefits and features
- Set up multiple price points per product

**Use Subscriptions API** for:

- Listing active subscriptions
- Updating subscription plans (upgrades/downgrades)
- Canceling subscriptions
- Checking subscription status for access control

### Authentication

**Organization Access Tokens (OAT)** for server-side:

- Full API access to manage products, orders, subscriptions
- Create in Polar Dashboard → Settings → API
- Store securely in environment variables
- Never expose in browser/client code

**Customer Access Tokens** for customer-facing:

- Generate via `/v1/customer-sessions/` endpoint
- Scoped to individual customer data only
- Use with Customer Portal API
- Safe for client-side use (limited scope)

### Environments

**Sandbox** (`https://sandbox-api.polar.sh/v1`):

- Safe testing environment
- Use during development
- Test all workflows before production

**Production** (`https://api.polar.sh/v1`):

- Real customers and live payments
- Switch after thorough testing
- Monitor carefully in Dashboard

### Pricing Strategy

**Use cents for all amounts**:

- `price_amount: 2900` = $29.00
- Avoids floating-point issues
- Consistent with Stripe conventions

**Offer multiple pricing options**:

- Monthly and annual plans (with discount)
- Good-Better-Best tiers
- Usage-based for APIs/metered services

**Consider psychological pricing**:

- $29 converts better than $30
- Annual discounts (15-20%) encourage commitment
- Free trials to convert users

### Subscription Management

**Handle subscription lifecycle**:

- Listen for webhook events (created, updated, canceled)
- Check subscription status before granting access
- Implement grace periods for failed payments
- Allow cancel at period end (customer keeps access)

**Proration is automatic**:

- Polar handles mid-cycle plan changes
- Credits/charges calculated automatically
- No manual proration logic needed

### Customer Experience

**Use hosted checkout**:

- Fastest integration path
- Polar handles payment UI
- Mobile-optimized by default
- PCI compliance handled

**Implement webhooks**:

- Real-time subscription updates
- Payment success/failure notifications
- Order fulfillment triggers
- Critical for production apps

**Provide customer portal**:

- Let customers manage subscriptions
- Update payment methods
- View invoices and receipts
- Reduces support burden

### Error Handling

**Handle rate limits**:

- 100 requests/minute (authenticated)
- 10 requests/minute (unauthenticated)
- Check `Retry-After` header on 429 responses
- Implement exponential backoff

**Validate before API calls**:

- Check product/price IDs exist
- Verify customer data format
- Ensure required fields present
- Log all API errors for debugging

## Common Workflows

### Workflow 1: Create Product and Accept Payment

```typescript
// Step 1: Create product with pricing
const product = polar_products_create({
  name: "Pro Plan",
  description: "Full access to all features",
  is_recurring: true,
  prices: [{
    type: "recurring",
    recurring_interval: "month",
    price_amount: 2900,  // $29.00
    price_currency: "usd"
  }]
});

// Step 2: Create checkout session
const checkout = polar_checkouts_create({
  product_id: product.id,
  success_url: "https://yourapp.com/success",
  customer_email: "customer@example.com"
});

// Step 3: Redirect customer to checkout.url
// Step 4: Handle webhook for subscription.created
```

### Workflow 2: Check Subscription Status for Access Control

```typescript
// Step 1: List customer's subscriptions
const subscriptions = polar_subscriptions_list({
  customer_id: "cus_xxx",
  active: true
});

// Step 2: Check if they have required subscription
const hasAccess = subscriptions.items.some(
  sub => sub.status === 'active' && sub.product_id === 'prod_required'
);

// Step 3: Grant or deny access based on status
if (hasAccess) {
  // Allow access to premium features
} else {
  // Show upgrade prompt
}
```

### Workflow 3: Upgrade/Downgrade Subscription

```typescript
// Step 1: Update subscription with new product
const updated = polar_subscriptions_update({
  subscription_id: "sub_xxx",
  product_id: "prod_new_plan"
});

// Polar automatically handles proration
// Customer charged/credited for difference
// Handle webhook for subscription.updated
```

### Workflow 4: Track Revenue Metrics

```typescript
// Get monthly recurring revenue
const metrics = polar_metrics_get({
  start_date: "2024-01-01",
  end_date: "2024-01-31",
  interval: "month"
});

// Returns MRR, active subscriptions, churn rate, etc.
```

## Best Practices Summary

### ✅ Do:

- **Use Checkout Sessions** for standard payment flows
- **Store OAT securely** in environment variables
- **Test in Sandbox** before going live
- **Implement webhooks** for all async events
- **Use cents for pricing** (2900 = $29.00)
- **Handle rate limits** with exponential backoff
- **Check subscription status** before granting access
- **Provide customer portal** for self-service
- **Log all API interactions** for debugging
- **Validate webhook signatures** for security

### ❌ Don't:

- **Expose OAT in client code** - use Customer Access Tokens instead
- **Skip webhook handling** - critical for subscription updates
- **Hardcode product IDs** - fetch from API or use environment variables
- **Ignore rate limits** - implement proper retry logic
- **Skip Sandbox testing** - test all scenarios first
- **Forget error handling** - show clear messages to customers
- **Use floating-point for prices** - always use cents (integers)
- **Immediately revoke access** on payment failure - implement grace periods
- **Skip pagination** - handle large result sets properly
- **Ignore webhook events** - they contain critical state changes

## Configuration

**Authentication Required**: Polar Organization Access Token

**Setup Steps:**

1. Create Polar account at https://polar.sh
2. Navigate to Dashboard → Settings → API
3. Click "Create Access Token"
4. Copy your token (starts with `polar_oat_`)
5. For testing, use Sandbox environment
6. For production, switch to Production environment
7. Configure token in Kiro Powers UI when installing this power

**Permissions**: OAT has full API access - keep secure and never expose client-side.

**MCP Configuration:**

```json
{
  "mcpServers": {
    "polar": {
      "command": "npx",
      "args": ["-y", "@polar-sh/mcp-server-polar"],
      "env": {
        "POLAR_ACCESS_TOKEN": "${POLAR_ACCESS_TOKEN}",
        "POLAR_ENVIRONMENT": "${POLAR_ENVIRONMENT:-sandbox}"
      }
    }
  }
}
```

## Troubleshooting

### Error: "Invalid API token"

**Cause:** Incorrect or missing API token
**Solution:**

1. Verify token starts with `polar_oat_`
2. Check token hasn't been deleted in Dashboard
3. Ensure using Organization Access Token, not Customer token
4. Regenerate token if compromised

### Error: "Product not found"

**Cause:** Invalid product ID or product deleted
**Solution:**

1. Verify product ID format (starts with `prod_`)
2. Check product exists in Dashboard
3. Ensure using correct environment (sandbox vs production)
4. List products to verify ID

### Error: "Subscription not found"

**Cause:** Invalid subscription ID or subscription deleted
**Solution:**

1. Verify subscription ID format (starts with `sub_`)
2. Check subscription exists in Dashboard
3. Ensure using correct environment
4. List subscriptions to verify ID

### Checkout creation failed

**Cause:** Missing required parameters or invalid product
**Solution:**

1. Verify product ID exists and is active
2. Check success_url is valid HTTPS URL
3. Ensure product has at least one price
4. Review error message for specific issue

### Webhook not received

**Cause:** Webhook endpoint not configured or failing
**Solution:**

1. Configure webhook endpoint in Dashboard → Settings → Webhooks
2. Verify endpoint is publicly accessible
3. Check endpoint returns 200 status
4. Review webhook logs in Dashboard
5. Validate webhook signature in your handler

### Rate limit exceeded

**Cause:** Too many requests in short time
**Solution:**

1. Check `Retry-After` header in 429 response
2. Implement exponential backoff
3. Cache frequently accessed data
4. Batch operations where possible
5. Review rate limits (100/min authenticated)

## Tips

1. **Start with Sandbox** - Test all scenarios before going live
2. **Use hosted checkout** - Fastest way to accept payments
3. **Implement webhooks early** - Critical for subscription updates
4. **Cache subscription status** - Reduce API calls with short TTL (5-10 min)
5. **Offer annual discounts** - Encourage longer commitments
6. **Monitor Dashboard** - Review payments, subscriptions, and metrics
7. **Handle errors gracefully** - Show clear messages to customers
8. **Use pagination** - Handle large result sets properly
9. **Keep tokens secure** - Never commit to version control
10. **Test edge cases** - Failed payments, cancellations, upgrades

## Resources

- [Polar Documentation](https://polar.sh/docs)
- [API Reference](https://polar.sh/docs/api-reference)
- [Sandbox Environment](https://sandbox.polar.sh)
- [Webhook Events](https://polar.sh/docs/webhooks)
- [Customer Portal](https://polar.sh/docs/customer-portal)
- [Checkout Guide](https://polar.sh/docs/features/checkouts)

---

**License:** Proprietary
