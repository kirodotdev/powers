# Polar Integration Best Practices

## Integration Approach

When designing a monetization integration with Polar, always prefer the documentation in [Polar's API Reference](https://polar.sh/docs/api-reference) and [Integration Guides](https://polar.sh/docs).

The [Checkout Guide](https://polar.sh/docs/features/checkouts) provides a comprehensive overview of Polar's payment flows.

You should always use the latest version of the API and SDK unless the user specifies otherwise.

## Payment and Checkout APIs

Polar's primary API for accepting payments is [Checkout Sessions](https://polar.sh/docs/features/checkouts/checkout-sessions). It supports one-time payments and subscriptions with hosted or embedded checkout pages. Prioritize Checkout Sessions for standard payment flows.

For custom implementations, you can use the Products API to manage your catalog and the Subscriptions API for recurring billing. Integrations should primarily use Checkout Sessions combined with Products and Subscriptions APIs.

## Product Management

**Create products with clear pricing models**:

- Use `is_recurring: true` for subscription products
- Use `is_recurring: false` for one-time purchases
- Define multiple prices per product (monthly, annual, etc.)
- Use cents for all price amounts (2900 = $29.00)

**Product types to consider**:

- **Recurring subscriptions**: SaaS plans, memberships
- **One-time products**: Digital downloads, courses, lifetime access
- **Usage-based**: APIs, metered services (combine with Customer Meters)

## Subscription Management

**For recurring revenue models**, use the Subscriptions API:

- List subscriptions to check customer access
- Update subscriptions for plan changes (automatic proration)
- Cancel subscriptions with `cancel_at_period_end` option
- Monitor subscription status for access control

**Subscription lifecycle**:

- `active`: Customer has access, billing is current
- `canceled`: Subscription canceled but may still be active until period ends
- `past_due`: Payment failed, implement grace period
- `incomplete`: Initial payment not completed

## Authentication and Security

**Organization Access Tokens (OAT)**:

- Use for all server-side API operations
- Create in Dashboard → Settings → API
- Store securely in environment variables
- Never expose in client-side code or public repositories

**Customer Access Tokens**:

- Generate via `/v1/customer-sessions/` endpoint
- Use for customer-facing operations (Customer Portal)
- Scoped to individual customer data only
- Safe for client-side use with limited scope

## Environments

**Always test in Sandbox first**:

- Sandbox: `https://sandbox-api.polar.sh/v1`
- Use for development and integration testing
- Test all payment flows and edge cases
- Verify webhook handling

**Production deployment**:

- Production: `https://api.polar.sh/v1`
- Switch after thorough Sandbox testing
- Monitor Dashboard for issues
- Set up proper error logging

## Webhooks

**Implement webhook handlers for critical events**:

- `subscription.created`: New subscription started
- `subscription.updated`: Plan changed or renewed
- `subscription.canceled`: Subscription canceled
- `order.created`: New order placed
- `payment.succeeded`: Payment completed successfully
- `payment.failed`: Payment failed, handle gracefully

**Webhook best practices**:

- Validate webhook signatures for security
- Return 200 status quickly (process async if needed)
- Handle idempotency (same event may be sent multiple times)
- Log all webhook events for debugging
- Configure in Dashboard → Settings → Webhooks

## Access Control

**Check subscription status before granting access**:

```typescript
// List customer's active subscriptions
const subscriptions = await polar_subscriptions_list({
  customer_id: customerId,
  active: true
});

// Verify they have required subscription
const hasAccess = subscriptions.items.some(
  sub => sub.status === 'active' && sub.product_id === requiredProductId
);
```

**Implement caching**:

- Cache subscription status with short TTL (5-10 minutes)
- Reduces API calls and improves performance
- Invalidate cache on webhook events
- Balance freshness vs API usage

## Pricing Strategy

**Use psychological pricing**:

- $29 converts better than $30 (charm pricing)
- Offer annual discounts (15-20%) to encourage commitment
- Create Good-Better-Best tiers (3 options)
- Position middle tier as "most popular"

**Pricing in cents**:

- Always use integers for price amounts
- 2900 = $29.00 (avoids floating-point issues)
- Consistent with Stripe conventions
- Prevents rounding errors

## Error Handling

**Handle rate limits gracefully**:

- 100 requests/minute for authenticated requests
- 10 requests/minute for unauthenticated requests
- Check `Retry-After` header on 429 responses
- Implement exponential backoff for retries

**Validate before API calls**:

- Check product IDs exist before creating checkouts
- Verify customer data format
- Ensure required fields are present
- Log all API errors with context

**Common errors to handle**:

- Invalid API token: Check token format and permissions
- Product not found: Verify product ID and environment
- Subscription not found: Check subscription ID and status
- Rate limit exceeded: Implement backoff and retry logic

## Customer Experience

**Use hosted checkout for fastest integration**:

- Polar handles payment UI and PCI compliance
- Mobile-optimized by default
- Supports multiple payment methods
- Reduces development time significantly

**Provide customer portal**:

- Let customers manage their own subscriptions
- Update payment methods without support
- View invoices and receipts
- Reduces support burden

**Handle failed payments gracefully**:

- Don't immediately revoke access
- Send payment reminder emails
- Implement grace period (3-7 days)
- Polar retries failed payments automatically

## Benefits and Features

**Use Benefits to grant access**:

- Define what customers get with each product
- Types: custom, discord, github_repo, downloadables, license_keys
- Automatically fulfilled by Polar where possible
- Check benefits in subscription object for access control

## Pagination

**Handle large result sets properly**:

- Use `page` and `limit` parameters
- Default limit is 10, max is 100
- Check `total_count` for total items
- Check `max_page` for total pages
- Implement pagination UI for better UX

## Testing

**Test thoroughly in Sandbox**:

- Create test products and prices
- Complete test checkout flows
- Verify webhook delivery
- Test subscription updates and cancellations
- Test failed payment scenarios
- Verify access control logic

**Use test payment methods**:

- Polar uses Stripe for payment processing
- Use Stripe test cards in Sandbox
- Test card: 4242 4242 4242 4242
- Test declined: 4000 0000 0000 0002
- Test 3D Secure: 4000 0027 6000 3184

## Monitoring

**Monitor key metrics in Dashboard**:

- Monthly Recurring Revenue (MRR)
- Active subscriptions count
- Churn rate
- Failed payment rate
- Customer lifetime value (LTV)

**Set up alerts**:

- Failed payment spikes
- Unusual cancellation rates
- API error rates
- Webhook delivery failures

## Migration from Other Platforms

**If migrating from Stripe, Paddle, or others**:

- Export customer and subscription data
- Create matching products in Polar
- Migrate customers with existing subscriptions
- Update payment methods if needed
- Test thoroughly before switching
- Communicate changes to customers

## Performance Optimization

**Reduce API calls**:

- Cache frequently accessed data (products, prices)
- Use webhooks instead of polling
- Batch operations where possible
- Implement request deduplication

**Database design**:

- Store product IDs and subscription IDs locally
- Cache subscription status with TTL
- Index customer_id for fast lookups
- Log all API interactions for debugging

## Compliance and Legal

**Ensure compliance**:

- Display clear pricing and terms
- Provide easy cancellation process
- Send receipts and invoices
- Handle refunds appropriately
- Follow local regulations (GDPR, etc.)

**Tax handling**:

- Polar integrates with Stripe Tax
- Configure tax settings in Dashboard
- Collect customer location for tax calculation
- Display tax-inclusive or exclusive pricing

## Common Patterns

**Freemium model**:

- Create free product with limited features
- Offer paid tiers with more features
- Use free trials to convert users
- Track conversion metrics

**Usage-based billing**:

- Use Customer Meters API
- Track usage events (API calls, storage, etc.)
- Combine with base subscription fee
- Bill based on actual usage

**Seat-based pricing**:

- Store seat count in subscription metadata
- Charge per user/seat
- Allow adding/removing seats
- Prorate charges automatically

## Resources

- [Polar Documentation](https://polar.sh/docs)
- [API Reference](https://polar.sh/docs/api-reference)
- [Checkout Guide](https://polar.sh/docs/features/checkouts)
- [Webhook Events](https://polar.sh/docs/webhooks)
- [Customer Portal](https://polar.sh/docs/customer-portal)
- [Sandbox Dashboard](https://sandbox.polar.sh)
