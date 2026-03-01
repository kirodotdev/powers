--- 
inclusion: always 
---

# SaaS Architecture Principles

## Multi-Tenancy First
- Every data model MUST include tenant isolation (tenant_id prefix in all keys)
- Prefix all entity keys with tenant: `pk: ${tenantId}#${entityType}#${id}`
- Use separate tables per entity type, not single-table design
- Never allow cross-tenant data access - validate tenant context on every operation
- Tenant ID comes from Lambda authorizer JWT claims, never from request body
- Design for tenant-level feature flags and configuration overrides
- Plan for tenant-specific rate limits and quotas from day one

## Cost-Per-Tenant Economics
- Serverless-first: AWS Lambda, API Gateway, DynamoDB (on-demand), S3
- Zero cost when idle - pay only for active tenant usage
- Design for horizontal scaling: more tenants = same per-tenant cost
- Avoid shared resources that don't scale linearly (RDS, fixed-size caches)
- Use DynamoDB on-demand pricing until predictable traffic patterns emerge
- Monitor cost per tenant to identify pricing model opportunities

## Authentication & Authorization
- Use managed auth: AWS Cognito or Auth0 (never roll your own)
- JWT tokens with tenant claims and user roles embedded
- Lambda authorizer validates tokens and injects tenant context + user roles
- EVERY Lambda function MUST check user roles before performing operations
- Role-based access control (RBAC) within tenants - check permissions at function entry
- Never assume authorization - explicitly verify user has required role/permission
- Support SSO/SAML for enterprise tenants
- API keys for programmatic access with tenant scoping

## Data Isolation & Compliance
- Logical isolation via tenant_id (pool model) for cost efficiency
- Physical isolation (separate tables/databases) only for enterprise tier
- Encrypt at rest (DynamoDB encryption) and in transit (TLS)
- Design for data residency requirements (multi-region support)
- Audit logging per tenant for compliance (CloudTrail, custom audit tables)
- Support tenant data export and deletion (GDPR, right to be forgotten)

## Subscription & Billing Integration
- Design features with usage metering from the start
- Track billable events: API calls, storage, compute time, seats
- Use EventBridge to publish usage events to billing system
- Support multiple pricing tiers with feature gating
- Plan for trial periods, freemium, and usage-based pricing
- Graceful degradation when tenant exceeds quota or payment fails

## Operational Excellence
- Tenant-aware monitoring: CloudWatch metrics tagged by tenant_id
- Isolate noisy neighbors: per-tenant rate limiting and circuit breakers
- Feature flags for gradual rollout and A/B testing
- Zero-downtime deployments with blue/green or canary
- Tenant-specific health checks and status pages
- Support tenant impersonation for debugging (with audit trail)

## Scalability Patterns
- Stateless services: no session affinity required
- Async processing for heavy workloads (SQS, Step Functions)
- Cache tenant config in Lambda memory (refresh on cold start)
- Design for 10x growth: what breaks at 100 tenants? 1000? 10000?
- Use DynamoDB GSIs for tenant-specific queries
- Avoid fan-out queries across all tenants

## Testing Strategy
- Backend: Unit tests for business logic, integration tests for tenant isolation
- Test cross-tenant data leakage scenarios explicitly
- Load test with realistic multi-tenant traffic patterns
- Frontend: Manual testing preferred, focus on tenant-specific UI variations

## Ingress Patterns and Edge Security

**Multi-Tenant Distribution Strategy**:
- Share configuration across tenants for operational efficiency
- Allow tenant-specific customization (domains, certificates, security overrides)
- Use connection groups for DNS routing

**Tiered Service Model for CDN**:
- Basic: Single multi-tenant distribution, platform subdomains, wildcard certificate, pooled origin
- Premium: Same multi-tenant distribution, custom vanity domains, tenant certificates, dedicated origins, Origin Shield, enhanced WAF WebACL protections
- Enterprise: custom vanity domains, tenant certificates, dedicated origins, Origin Shield, custom WAF WebACL

**Certificate Strategy**:
- Use HTTP ACM validation for automatic renewal (Route53 and ACM)
- Wildcard certificates for platform subdomains (cost-effective)
- Tenant-specific certificates for custom domains (optional)

**DNS Ownership Models**:
- Platform-managed: Full control, automated validation, operational overhead
- Tenant-managed: Tenant controls DNS, zero platform cost, manual coordination
- Hybrid: Platform subdomains + optional custom domains

## Security & DDoS Protection

**Defense in Depth**:
- Use AWS WAF with CloudFront to provide for application layer protections
- AWS Shield Standard for network/transport layer DDoS
- Rate limiting at multiple layers (WAF, API Gateway, application)
- Geo-blocking and IP reputation filtering
- API Gateway (request, input validation, access control, usage plans)

**Positive Security Model WAF**:
- Default deny for APIs (explicit allow for known good patterns)
- Default allow for websites (explicit block for known bad patterns)
- Use managed rule groups for OWASP Top 10 protection
- Layer rules: non-terminating (count/challenge) before terminating (block/allow)

**Tenant-Specific Security**:
- Shared Web ACL for Basic tier (cost-effective)
- Enhanced rules for Premium tier (higher rate limits)
- Dedicated Web ACL for Enterprise tier (custom policies)

## Dependency Management
- Minimize third-party libraries - prefer AWS SDKs and built-in language features
- Pin versions to avoid breakages
- Prefer AWS-managed services over self-hosted alternatives
- Evaluate libraries for multi-tenant safety (no global state)
