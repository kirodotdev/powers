---
name: "amazon-api-gateway"
displayName: "Amazon API Gateway"
description: "Expert guidance for building, managing, governing, and operating APIs with Amazon API Gateway. Covers REST APIs (v1), HTTP APIs (v2), and WebSocket APIs including architecture patterns, authentication, security, observability, deployment strategies, and SAM/CloudFormation templates."
keywords: ["api-gateway", "api gateway", "serverless", "rest-api", "rest api", "http-api", "http api", "websocket-api", "websocket api", "websocket", "aws-api", "aws api", "rest", "api management", "api governance", "build api", "create api", "migrate api", "develop api", "implement api"]
author: "AWS"
---

# Amazon API Gateway

Expert guidance for building, managing, governing, and operating APIs with Amazon API Gateway. Covers REST APIs (v1), HTTP APIs (v2), and WebSocket APIs.

## Overview

This power provides comprehensive documentation for Amazon API Gateway, including architecture patterns, authentication strategies, security best practices, observability setup, deployment strategies, and complete SAM/CloudFormation templates for direct AWS service integrations.

When answering API Gateway questions:

1. Read the relevant steering file(s) before responding — do not rely solely on this overview
2. For tasks spanning multiple concerns (e.g., "private API with mTLS and custom domain"), read all relevant steering files
3. When the user needs IaC templates, consult `sam-cloudformation.md` or `sam-service-integrations.md` and provide complete, working SAM/CloudFormation YAML
4. Always mention relevant pitfalls and limits that affect the user's design

## Available Steering Files

- **architecture-patterns** — Topology patterns, multi-tenant SaaS, hybrid/on-premises workloads, private API endpoints, VPC Links, multi-region, response streaming, AI agent API design, reducing backend load
- **authentication** — Auth decision tree, IAM (SigV4), Lambda authorizers (REST + HTTP API), JWT authorizers, Cognito user pools, resource policies, mTLS, API keys
- **custom-domains-routing** — Custom domain setup by endpoint type, base path mappings, routing rules, header-based API versioning, multi-tenant white-label domains, host header forwarding
- **deployment** — Deployment basics (REST/HTTP/WebSocket), canary deployments, manual rollback, blue/green zero-downtime deployments, routing rules for A/B testing, deployment pitfalls
- **governance** — Governance framework (preventative, proactive, detective, responsive controls), SCPs, CloudFormation Hooks, AWS Config rules, EventBridge, management access control, API lifecycle, audit
- **observability** — Execution logging, access logging (REST/HTTP/WebSocket formats), enhanced observability variables, CloudWatch metrics and alarms, X-Ray tracing, Logs Insights queries, analytics pipeline, cross-account logging
- **performance-scaling** — Throttling (account/stage/method level), usage plans, caching (REST API), scaling considerations, multi-layer caching strategy, payload compression, handling large payloads
- **pitfalls** — Additional pitfalls beyond the critical ones listed below (header handling, URL encoding, throttling, caching charges, usage plans, logging costs, canary deployments, management API limits)
- **requirements-gathering** — Structured requirements gathering workflow covering API purpose, endpoints, request/response specs, data models, auth, integrations, WebSocket, performance, security, deployment, custom domains, governance
- **sam-cloudformation** — OpenAPI extensions, common SAM patterns, private API with VPC endpoint, gateway responses with CORS, response streaming, routing rules, VTL mapping templates, HTTP API parameter mapping, binary data handling
- **sam-service-integrations** — Complete SAM templates for direct AWS service integrations: EventBridge, SQS, DynamoDB full CRUD, Kinesis Data Streams, Step Functions (REST + WebSocket sync/async)
- **security** — TLS configuration, mTLS setup and automation, CRL checks, CloudFront viewer mTLS, resource policies, WAF (managed rule groups, best practices), CORS configuration, HttpOnly cookie auth, cache encryption
- **service-integrations** — Direct AWS service integrations without Lambda: EventBridge, SQS, SNS, DynamoDB, Kinesis, Step Functions, S3, HTTP proxy, mock integrations, common patterns (IAM roles, validation, binary media types)
- **service-limits** — Complete quota tables for REST API, HTTP API, WebSocket API, account-level throttling, management API rate limits, cache sizes, reserved paths, gateway response types, feature availability matrix
- **troubleshooting** — Detailed resolution steps for HTTP 400/401/403/413/429/500/502/504, SSL/TLS issues, CORS errors, Lambda integration errors, VPC/private API issues, mapping template errors, WebSocket issues, SQS integration errors
- **websocket** — Route selection, @connections management API, session management, client resilience, SAM templates, Lambda message sending, limits, pricing, multi-region WebSocket

## Quick Decision: Which API Type?

Choose the right API type first. This decision affects every downstream choice.

| Factor | REST API (v1) | HTTP API (v2) | WebSocket API |
|---|---|---|---|
| Positioning | Full API management | Low-cost proxy | Real-time bidirectional |
| Cost | Higher | ~70% cheaper | Per-message pricing |
| Latency | Higher | Lower | Persistent connection |
| Max timeout | 50ms-29s (up to 300s Regional/Private) | 30s hard limit | 29s |
| Payload | 10 MB | 10 MB | 128 KB message / 32 KB frame |
| Usage plans/API keys | Yes | No | No |
| Request validation | Yes (JSON Schema draft 4) | No | No |
| Caching | Yes (0.5-237 GB) | No | No |
| WAF | Yes | No (use CloudFront + WAF) | No |
| Resource policies | Yes | No | No |
| Private endpoints | Yes | No | No |
| Lambda authorizer | Yes (TOKEN + REQUEST) | Yes (REQUEST only) | Yes ($connect only) |
| JWT authorizer | No (use Cognito authorizer) | Yes (native) | No |
| Canary deployments | Yes | No | No |
| Response streaming | Yes | No | No |
| X-Ray tracing | Yes | No | No |
| Execution logging | Yes | No | Yes |

Use REST API when you need full API management (usage plans, request validation, caching, WAF, private endpoints, canary deployments).

Use HTTP API when you need a lightweight, low-cost proxy and don't require the enterprise controls above.

Use WebSocket API for persistent bidirectional connections (chat, notifications, live dashboards).

## Critical Pitfalls

1. REST API default timeout is 29 seconds (increasable up to 300s for Regional/Private). Lambda continues running but client gets 504
2. HTTP API hard timeout is 30 seconds. Returns `{"message":"Service Unavailable"}` while Lambda continues
3. `/ping` and `/sping` are reserved paths
4. Execution log events truncated at 1,024 bytes. Use access logs for complete data
5. 413 `REQUEST_TOO_LARGE` is the only gateway response that cannot be customized
6. `maxItems`/`minItems` not validated in REST API request validation
7. Root-level `security` in OpenAPI is ignored. Must set per-operation
8. JWT authorizer public keys cached 2 hours. Account for this in key rotation
9. Management API rate limit: 10 rps / 40 burst
10. Always redeploy REST API after configuration changes
11. Edge-optimized endpoints do NOT cache at the edge — use a Regional API with your own CloudFront distribution for edge caching

## Troubleshooting Quick Reference

| Error | Most Common Cause | Quick Fix |
|---|---|---|
| 400 Bad Request | Protocol mismatch (HTTP/HTTPS) with ALB | Match protocol to listener type |
| 401 Unauthorized | Wrong token type or missing identity sources | Check token type; verify identity sources |
| 403 Missing Auth Token | Stage name in URL when using custom domain | Remove stage name from URL path |
| 403 from VPC | Private DNS on VPC endpoint intercepts ALL API calls | Use custom domain names for public APIs |
| 429 Too Many Requests | Account/stage/method throttle limits exceeded | Jittered exponential backoff; request limit increase |
| 500 Internal Error | Missing Lambda invoke permission (stage variables) | Add resource-based policy to Lambda |
| 502 Bad Gateway | Lambda response not in required proxy format | Return `{statusCode, headers, body}` |
| 504 Timeout | Backend exceeds timeout limit | Optimize backend or switch to async invocation |
| CORS errors | Missing CORS headers on Gateway Responses | Add CORS headers to DEFAULT_4XX and DEFAULT_5XX |

## Service Limits Quick Reference

| Resource | REST API | HTTP API | WebSocket |
|---|---|---|---|
| Payload size | 10 MB | 10 MB | 128 KB |
| Integration timeout | 50ms-29s (up to 300s) | 30s hard | 29s |
| APIs per region | 600 Regional/Private; 120 Edge | 600 | 600 |
| Routes/resources per API | 300 | 300 | 300 |
| Account throttle | 10,000 rps / 5,000 burst | Same | Same (shared) |
