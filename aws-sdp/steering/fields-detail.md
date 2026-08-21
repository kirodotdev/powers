# Detailed Field Guide — With Examples and Common Mistakes

## Field: Name of the Publicly Available Case Study

**Format**: `[Customer] – [Solution Description] with [Main AWS Services]`

**Good examples**:
- "Comfandi – Network Infrastructure Transformation on AWS with Transit Gateway, Site-to-Site VPN, Network Firewall, CloudFront, and Route 53"
- "Bancolombia – Microservices Platform on Amazon EKS with Multi-AZ High Availability"
- "EPM – Real-Time Analytics with Serverless Architecture on AWS Lambda and Kinesis"

**Common mistakes**:
- "Infrastructure project for financial customer" — too vague
- "AWS implementation for Comfandi" — doesn't mention services or solution
- Just reading the name should identify which SDP it applies to

---

## Field: Customer Challenge

**Ideal length**: 300–500 words

**What AWS wants to see**:
- A real business problem, not just a technical one
- The impact of NOT solving the problem
- Enough context to understand the scope of the engagement
- The customer's language (as if the customer wrote it)

**Common mistakes**:
- Mentioning the partner: "Comfandi contacted ITERA to..."
- Being generic: "they needed to improve their cloud infrastructure"
- Mixing challenge and solution in the same paragraph
- "The Fovis and Fosfec applications lacked centralized web perimeter protection, exposing them to OWASP threats with no network traffic visibility."

**Opening templates by industry**:

*Compensation fund / social sector:*
> "[Customer] is one of the [adjective] family compensation funds in Colombia, with operations in [region] serving more than [N] beneficiaries. Its technology infrastructure supports critical applications for [subsidies/health/education] that require continuous availability."

*Financial sector:*
> "[Customer] operates in [N] countries with a [services] platform processing [N] transactions daily. The growing demand for secure connectivity between cloud environments and legacy systems represented a significant operational risk."

---

## Field: Proposed Solution

**Level of detail expected by AWS**:

| Element | Poor | Good |
|---|---|---|
| Service name | "database" | "Amazon Aurora PostgreSQL-Compatible" |
| Configuration | "multi-zone" | "3 availability zones: us-east-1a, 1b, 1c" |
| Network | "private VPC" | "VPC CIDR 10.249.36.0/22 with private subnets under Control Tower" |
| Security | "with WAF" | "AWS WAF with 1 Web ACL, 9 custom rules, and 1 Managed Rule Group" |

**Introductory paragraph template**:
> "[Partner] designed and implemented a [type: network/container/serverless] architecture on AWS that [what it solves]. The solution integrates the following components..."

**Services table template** (always include):
```
| AWS Service | Role in the Solution |
|---|---|
| AWS Transit Gateway | Central routing hub between N VPCs across [customer]'s accounts |
| AWS Site-to-Site VPN | N encrypted tunnels connecting [A] to [B] |
```

---

## Field: Third-party Applications or Solutions

**When it applies**:
- External CI/CD tools (Jenkins, GitLab, GitHub Actions)
- Third-party monitoring (Datadog, New Relic, Grafana)
- Identity providers (Keycloak, Okta, Active Directory)
- On-premises systems connected to the solution
- External providers connected via VPN/Direct Connect
- IaC tools: Terraform, Pulumi, Ansible (if part of the delivered solution)

**If no third parties**:
> "No third-party solutions were used. The solution was implemented 100% on native AWS services."

---

## Field: How AWS Is Used as Part of the Solution

**Recommended format**: table + integration flow paragraph

**Tip**: Be specific per service. Examples:

| Vague | Specific |
|---|---|
| "Amazon VPC for networking" | "Amazon VPC with CIDR 10.249.36.0/22, private subnets across 3 AZs under Control Tower" |
| "CloudWatch for monitoring" | "CloudWatch for ingesting VPC Flow Logs (20 GB/month) and network traffic auditing" |
| "S3 for storage" | "Amazon S3 as the origin for static assets distributed via CloudFront" |

---

## Date Fields

### Important rules:
- `Start ≤ End ≤ Production` — AWS checks for consistency
- If there are multiple sub-projects, document the full range
- Use the closure report date as the end reference when available
- The project MUST already be in production — if not, it doesn't qualify for SDP

### When there are multiple phases:
```
Start date: [date of the first sub-project]
End date: [date of the last closure]
Production date: [go-live date of the main component]
```

---

## Field: Results/Outcomes

### Value hierarchy for AWS:
1. Business metrics (USD saved, % cost reduction, time-to-market)
2. Measurable technical metrics (latency, uptime %, throughput RPS)
3. perational improvements (reduced tickets, eliminated processes)
4. Security improvements (achieved compliance, mitigated risks)

### Templates by outcome type:

**Connectivity/Networking**:
> "Connectivity across [N] AWS accounts was consolidated via Transit Gateway, replacing bilateral peering management with a hub-and-spoke model with a single control point."

**Security**:
> "The centralized WAF with [N] active rules protects [N] applications against OWASP Top 10 threats, with full traffic visibility through VPC Flow Logs."

**High availability**:
> "The multi-AZ architecture guarantees continuous 7x24x365 availability with automatic failover in case of availability zone failures."

**Content delivery**:
> "CloudFront reduced static content delivery latency for [application] users in [region], with functional tests approved in both QA and production environments."

---

## Field: Architecture Diagrams

**Accepted formats**: PNG, JPG, PDF

**Diagram checklist**:
- [ ] All AWS services in the case appear in the diagram
- [ ] Data/connectivity flow between components is shown
- [ ] Separate AWS accounts are identified (if applicable)
- [ ] Availability zones are shown (if there is HA)
- [ ] Connections to external/on-premises systems are shown

**Recommended tools**:
- draw.io / diagrams.net (free, official AWS icons available)
- Official AWS Architecture Icons: https://aws.amazon.com/architecture/icons/
- Cloudcraft (AWS-specialized)
- Lucidchart

**If the diagram doesn't exist**: flag it explicitly in the document and create a task for the technical team to produce it before submitting to AWS.
