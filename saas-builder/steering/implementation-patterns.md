---
inclusion: always
---

# Implementation Patterns

## Frontend Stack
- React with TypeScript (strict mode)
- Tailwind CSS for styling
- Functional components with hooks only

## API Design

### RESTful Conventions
- Use plural nouns for collections: `/api/v1/users`, `/api/v1/users/{id}`
- HTTP methods: GET (retrieve), POST (create), PUT/PATCH (update), DELETE (delete)
- Version APIs: `/v1/`, `/v2/`
- Avoid RPC-style endpoints like `/doEverything`
- Use query parameters for filtering, not custom endpoints

### Request/Response Models
- Define schemas in `schema/` (language-agnostic format preferred)
- Validate at API boundary with appropriate validation library
- API request validation with format and type checking
- Success: Return JSON object or array
- Error: `{ "error": { "code": "...", "message": "..." } }`
- Never expose internal database fields directly
- Document with OpenAPI specification

### Error Handling
- Use proper HTTP status codes:
  - 400: Client input errors
  - 401/403: Auth errors
  - 404: Not found
  - 500: Server errors
- Log errors internally (CloudWatch), return friendly messages to clients
- Implement global exception handlers
- Never leak stack traces or raw exceptions

### Authentication & Authorization
- Require auth on all endpoints (except rare public ones)
- Use JWTs or OAuth tokens (Auth0, AWS Cognito)
- Verify tokens in Lambda authorizer
- Lambda authorizer injects tenant ID and user roles into request context
- Use scopes/roles for sensitive operations
- Enforce tenant context for data segregation
- Never rely on client-side auth checks
- Never accept tenant ID from request body - only from authorizer

### Pagination & Filtering
- Enforce pagination for large lists
- Use `?page=` and `?pageSize=` or cursor-based `?nextToken=`
- Provide filters: `/orders?status=pending&created_after=2024-01-01`
- Refuse to return extremely large payloads
- All queries automatically scoped to tenant (no cross-tenant results)

### Rate Limiting
- Use API Gateway throttling quotas per tenant
- Document limits to users
- Protect expensive operations with application-level limits
- Degrade gracefully under load
- Consider per-tenant rate limits based on subscription tier

### Usage Tracking & Metering
- Track billable events at API boundary
- Publish usage events to EventBridge for billing system
- Include tenant ID, user ID, operation type, timestamp
- Check tenant quota before expensive operations
- Return 429 (Too Many Requests) when quota exceeded

## AWS Patterns

### DynamoDB
- Composite keys: `pk: ${tenantId}#${entityType}#${id}`, `sk: metadata | #{relationType}#${relatedId}`
- GSI for queries: `GSI1PK: ${tenantId}`, `GSI1SK: ${entityType}#${timestamp}`
- Always prefix keys with tenant ID for isolation
- Design access patterns upfront to minimize queries
- Use appropriate SDK for your backend language

### Lambda Functions
- Multi-Tenant Pattern
Every Lambda function should follow this pattern:

1. **Extract tenant context** from authorizer claims (injected by Lambda authorizer)
2. **Extract user roles** from authorizer claims
3. **Validate required parameters** at function entry
4. **Check user roles/permissions** before performing operations (RBAC)
5. **Prefix all database operations** with tenant ID
6. **Return proper HTTP status codes** (403 for unauthorized, etc.)
7. **Log errors with tenant context** for debugging
8. **Never trust tenant ID from request body** - only from authorizer

Example flow:
```
handler(event) {
  tenantId = event.requestContext.authorizer.tenantId
  userRoles = event.requestContext.authorizer.roles
  
  if (!hasRequiredRole(userRoles, 'admin')) {
    return 403 Forbidden
  }
  
  // All DB queries use tenantId prefix
  result = db.get(pk: `${tenantId}#User#${userId}`)
  
  return 200 OK
}
```
### CloudFront and Custom Domains

**Multi-Tenant Distribution Setup**:
- Create one distribution per tier (for example; Basic, Premium, Enterprise)
- Use parameters for tenant-specific values:
  - S3 origin: `${tenantId}.s3.${region}.amazonaws.com`, `/tenants/${tenantId}`
  - API Gateway origin: `${apiId}.execute-api.${region}.amazonaws.com`, `/${stage}/tenants/${tenantId}`
- Attach shared Web ACL ARN to distribution
- Create distribution tenant per tenant with domain names and certificate ARN
- Pass parameter values (tenantId, apiId, stage, region) to distribution tenant

**ACM Certificate Implementation**:
- Wildcard for Basic tier: `*.yourplatform.com` with DNS validation (auto-validates via Route53)
- Tenant-specific for Premium/Enterprise: DNS validation (tenant adds CNAME records)
- Poll certificate status: `PENDING_VALIDATION` → `ISSUED`
- Associate certificate ARN with CloudFront distribution tenant once issued
- All CloudFront certificates must be in us-east-1 region
- Never use email validation (manual renewal, not scalable)

**DNS Configuration**:

Platform subdomain (instant onboarding):
- Create CNAME in platform hosted zone: `${tenantId}.yourplatform.com` → CloudFront endpoint
- TTL: Low value for flexibility during onboarding (e.g., 5 minutes)
- Uses wildcard certificate

Platform-managed tenant domain (automated validation):
- Create Route53 hosted zone for tenant domain
- Request ACM certificate with HTTP(1st choice) or DNS(2nd choice) validation (auto-creates validation CNAME in zone)
- Create CNAME for traffic: `${tenantDomain}` → CloudFront endpoint
- Provide Route53 name servers to tenant for domain delegation

Tenant-managed DNS (manual coordination):
- Request ACM certificate for tenant domain
- Provide DNS validation CNAME records to tenant
- Tenant adds CNAME to their DNS provider
- Poll ACM status until validated
- Provide CloudFront endpoint CNAME to tenant
- Tenant adds traffic CNAME to their DNS

**Tenant Onboarding Workflows**:
- Platform subdomain: Create CNAME → instant access
- Tenant vanity (manual): Request cert → provide validation records → tenant adds → poll status → associate cert → provide endpoint
- Platform-managed: Create zone → request cert → auto-validate → add CNAME → provide name servers → tenant delegates

**Critical Implementation Rules**:
- All CloudFront certificates must be in us-east-1 region
- Use DNS validation (never email - requires manual renewal)
- Keep validation CNAMEs in DNS permanently (enables auto-renewal)
- Use Alias records for apex domains (no query charges)
- Set TTL low during onboarding for flexibility, increase after stable
- Monitor certificate validation status and alert tenant if stuck
- Test DNS propagation (can take minutes to days depending on DNS provider)

### AWS WAF and Security

**Web ACL Configuration**:
Key settings for CloudFront WAF integration:

- **Scope**: `CLOUDFRONT` (required for CloudFront distributions)
- **Associate with CloudFront**: Attach Web ACL ARN to multi-tenant distribution

**Positive Security Model** (if using default deny):
If changing default action to `Block`, add terminating allow rule lower in the rule order:
- Allow `/api/v1/*` with valid JWT token label, count/label match, with a rate limit
- Allow static assets: `\.(css|js|png|jpg|gif|ico|woff2?)$`, with a rate limit
- Allow health check: `/health`, with a rate limit

**API use-case: Positive Security Model Pattern**:
- Reference WAF Rule Priority Order table above for complete configuration
- Default action: Allow (with comprehensive rule-based blocking)
- Alternative: Default Block with explicit allow rules for known good patterns
- Use labels from managed rules to identify and allow authenticated requests

**DDoS Protection**:
- AWS Shield Standard: Automatic with CloudFront (no config needed)
- CloudFront absorbs layer 3/4 attacks at edge locations
- Route53 provides DNS query flood protection
- WAF rate limiting prevents application layer attacks

**AWS WAF Rule Priority Order**:
Configure based on your security requirements. Default action depends on use case:
- **Websites**: Default Allow with rule-based blocking
- **APIs**: Default Block (positive security model) with explicit allow rules

**Rule Priority Guidelines** (adjust priorities in increments of 10 for flexibility):

| Priority Range | Rule Type | Action | Purpose |
|----------------|-----------|--------|---------|
| 0-10 | AntiDDoS (AMR) | Count/Challenge | DDoS protection (exclude API endpoints from challenge using regex) |
| 10-20 | IP Allowlist | Allow | Trusted IPs bypass all rules (if applicable) |
| 30-40 | IP Blocklist | Block | Known malicious IPs, headers, user-agents |
| 50-60 | Geo-Blocking | Block | High-risk countries based on your requirements |
| 60-90 | Rate Limiting | Count | Global, per-method (GET, POST/PUT/DELETE) |
| 90-100 | Body Size Restriction | Count | Tune based on your API requirements (default: 16KB, max: 64KB with additional cost) |
| 100-110 | IP Reputation (AMR) | None/Challenge | Block/challenge known DDoS IPs, count reconnaissance |
| 110-120 | DDoS IP Rate Limit | Count | Rate limit for labeled DDoS IPs |
| 120-130 | Anonymous IP (AMR) | None | Block VPNs, proxies, Tor (if required) |
| 130-140 | Core Rule Set (AMR) | None | OWASP Top 10 protection |
| 140-150 | Known Bad Inputs (AMR) | None | Malicious patterns, directory traversal |
| 150-160 | Language-Specific (AMR) | None | PHP, Linux, etc. (based on your stack) |
| 160-170 | SQL Injection (AMR) | None | SQLi attack prevention |
| 170-180 | Admin Protection (AMR) | None | Protect admin paths |
| 180-190 | Bot Control (AMR) | Count | Common bot detection (optional: upgrade to Targeted for enterprise) |

**Important Configurations**:
- **Body Inspection**: Default 16KB, up to 64KB available (additional cost)
- **Token Domains**: Configure for your application domains for use with WAF tokens
- **CSP Headers**: Set appropriate Content Security Policy headers (if AWS WAF Bot Control required)
- **Regex Handling**: Exclude static assets and API endpoints from challenges where appropriate (use AWS WAF regex)

### Environment Configuration
- Use environment variables for runtime config
- Use AWS Secrets Manager for sensitive values
- Never hard-code credentials or secrets

## Frontend Code Style (React + TypeScript)

### React Components
- Functional components with hooks only
- Keep under 100 lines when possible
- TypeScript interfaces for props (strict mode)
- Prefer local state over global state
- Use Tailwind utility classes
- Mobile-first responsive design

### Naming Conventions
- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useAuth.ts`)
- Files: Match component name

### Multi-Tenant Frontend Patterns
- Store tenant context in React Context or auth state
- Include tenant ID in all API requests (from auth token)
- Handle tenant-specific branding/theming
- Support feature flags for tenant-specific features
- Display tenant-scoped data only
- Handle quota exceeded errors gracefully (show upgrade prompts)

### Frontend Best Practices
- Descriptive variable names (self-documenting)
- Proper error handling with try-catch
- Avoid comments - code should be self-documenting
- Only comment complex logic when necessary

## Backend Code Style (Language-Agnostic)

### General Principles
- Descriptive variable and function names
- Proper error handling
- Structured logging (errors only, with context)
- Consistent terminology across codebase
- Follow language-specific conventions (PEP8 for Python, etc.)

### Libraries & Dependencies
- Minimize third-party libraries
- Prefer AWS SDKs and built-in language features
- Pin versions to avoid breakages
- Use libraries packaged in Lambda runtime when possible
