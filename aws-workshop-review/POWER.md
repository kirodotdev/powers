---
name: "workshop-content-reviewer"
displayName: "Workshop Content Reviewer"
description: "Reviews new Aurora PostgreSQL and RDS PostgreSQL workshop lab content against established patterns, formatting standards, and security practices from the existing aurora-pg-lab and rdspg workshops."
keywords: ["aurora", "rds", "workshop", "postgresql", "lab-content", "content-review", "hugo", "workshop-studio", "aurora-pg-lab", "rdspg"]
author: "Workshop Content Team"
---

# Workshop Content Reviewer

## Overview

This power provides a comprehensive checklist and ruleset for reviewing new Aurora PostgreSQL and RDS PostgreSQL workshop lab content before it is merged. It codifies the patterns, conventions, and security practices established across both the `aurora-pg-lab` and `rdspg` workshop repositories so that every new lab is consistent, high-quality, and ready for participants.

Use this power whenever you are asked to review, audit, or validate new workshop content destined for either the Aurora PostgreSQL or RDS PostgreSQL labs.

## Onboarding

### What This Power Reviews

This power is designed for reviewing Hugo/Workshop Studio-based lab content for PostgreSQL workshops on AWS. It covers:

- **File and directory structure** — correct layout under `content/` and `static/`
- **Front matter** — required YAML fields, weight conventions, and chapter metadata
- **Code blocks** — Workshop Studio `:::code` directive usage and standard fenced blocks
- **Alerts and callouts** — correct `::alert` / `:::alert` syntax
- **Expandable sections** — `::::expand` directive usage
- **Children directive** — `::children` for auto-listing sub-pages
- **Image references** — paths, alt text, and file naming
- **Internal links** — absolute paths, no broken links
- **Prerequisites section** — standard block format for each workshop
- **Security** — no hardcoded credentials, no real PII, environment variable usage
- **Content quality** — grammar, step numbering, flow, explanations before commands
- **Cleanup / teardown** — resource cleanup instructions
- **Workshop Studio compatibility** — contentspec.yaml, CloudFormation templates, IAM policies

### When to Activate

Activate this power when a user asks you to:
- Review or audit new lab content before merging
- Validate a lab against workshop standards
- Check a PR or zip of new workshop content
- Ensure a new lab follows established patterns from either workshop
- Compare content patterns between the aurora-pg-lab and rdspg workshops

### How to Use

1. Activate this power.
2. Read the `review-checklist` steering file for the full structured checklist.
3. Walk through each category against the new content files.
4. Generate a `Review.md` file as the output artifact containing the full review report.

### Output

The review must produce a **`Review.md`** file in the root of the reviewed content directory (or the working directory if reviewing a PR/zip). This file is the single deliverable of every review and must follow the Review Report Template defined in the `review-checklist` steering file.

The `Review.md` file should include:
- Review metadata (lab name, target workshop, reviewer, date, overall status)
- Critical issues that must be fixed before merge
- Warnings that should be fixed
- Recommendations (nice to have)
- List of files to remove (stale/unused)
- Consistency notes
- A summary table of checklist categories with PASS/FAIL/N/A status

## Available Steering Files

- **review-checklist** — Full review checklist with pass/fail criteria organized by category (structure, front matter, formatting, images, security, content quality, cleanup), plus a review report template.

---

## Established Workshop Patterns (Reference)

The following patterns are extracted from both the `aurora-pg-lab` and `rdspg` workshop content and represent the standards every new lab must follow.

### 1. File & Directory Structure

- Content lives under `content/<Category>/<LabName>/` with sub-folders for each page (e.g., `task1/`, `task2/`, `Prerequisites/`).
- Static assets (images) live under `static/<category-folder>/<lab-folder>/` mirroring the content structure (e.g., `static/2-Foundation/Lab6-Monitoring/task1/`).
- Every page is an `index.en.md` (preferred) or `index.md` file inside its folder.
- No stale, duplicate, or "OLD"/"USELESS" files should be present in the deliverable.
- No OS artifacts (`.DS_Store`, `__MACOSX/`, `Thumbs.db`) should be committed.
- Category folders use numbered prefixes for ordering (e.g., `1-Prerequisites`, `2-Foundation`, `3-Intermediate`, `4-Advanced`).
- Lab folders within categories use descriptive names (e.g., `Lab1-Create`, `Lab4-Backup`, `RDS-Proxy`, `Secrets-Mgr`).
- Task sub-folders use sequential naming (e.g., `task1/`, `task2/`, `task3/`).

### 2. Front Matter

Every `index.en.md` must have YAML front matter with at minimum:

```yaml
---
title: "Human-Readable Title"
weight: <number>
---
```

#### Category/Chapter Index Pages

Category and lab index pages use additional fields:

```yaml
---
chapter: true
pre: '<i class="fas fa-landmark"></i>  - '
title: 🏛️ Foundation
weight: 20
---
```

Or with numbered prefix:

```yaml
---
chapter: true
pre: <b>1. </b>
title: 🗃️ Create RDS PostgreSQL Database Instance
weight: 10
---
```

#### Valid Front Matter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Human-readable page title, may include emoji for category pages |
| `weight` | Yes | Numeric ordering value |
| `chapter` | No | Set to `true` for category/section index pages |
| `pre` | No | Prefix content (icons, bold numbers) for navigation display |
| `date` | No | Creation/modification date in ISO format |

#### Weight Conventions (rdspg)

| Level | Pattern | Examples |
|-------|---------|---------|
| Top-level category | Tens/Hundreds | 1, 20, 30, 40, 100 |
| Lab index page | Within category range | 10, 20, 30, 40, 59, 61, 75 |
| Sub-pages within a lab | Small increments | 10, 20, 30, 51, 52 |

#### Weight Conventions (aurora-pg-lab)

| Level | Pattern | Examples |
|-------|---------|---------|
| Top-level category | Hundreds | 100, 200, 400, 510, 705, 805 |
| Lab index page | Category weight + offset | 315, 410, 510 |
| Sub-pages within a lab | Small increments | 51, 52, 151, 171 |

### 3. Code Blocks

The workshops use two code block styles depending on context:

#### Workshop Studio `:::code` Directive (preferred for participant-facing commands)

```
:::code{showCopyAction=true showLineNumbers=false language=sql}
SELECT version();
:::
```

Key attributes:
- `showCopyAction=true` — always present so participants can copy.
- `showLineNumbers=false` — default for most blocks.
- `language=sql` / `language=bash` / `language=json` — always specify the language.

#### Standard Markdown Fenced Blocks

The rdspg workshop also uses standard markdown fenced blocks (` ```lang `) for CLI commands, especially within expandable sections:

```
```sh
aws rds modify-db-instance \
    --db-instance-identifier rds-pg-labs \
    --multi-az \
    --apply-immediately
```
```

Standard fenced blocks are acceptable for:
- Non-copyable output examples
- Commands within `::::expand` sections
- Inline code references
- CLI commands where the Workshop Studio directive is not used

#### Best Practice

- Every code block should specify a language (`sql`, `bash`, `sh`, `sh-session`, `json`, `python`, etc.)
- Commands that require user-specific values should use environment variables (`$PGHOST`, `$DBENDP`, `$DBPASS`, `$DBUSER`, `$AWSREGION`) or clearly mark placeholders with `[brackets]`
- Multi-line CLI commands should use backslash continuation (`\`) for readability

### 4. Alerts & Callouts

The workshop uses two syntaxes:

**Inline alert (single line):**
```
::alert[Alert text here.]{type="warning"}
```

**Block alert (multi-line):**
```
:::alert{header="Important" type="warning"}
Multi-line alert content here.
:::
```

Valid types: `warning`, `info`.

Both syntaxes must use the correct number of colons — `::` for inline, `:::` for block. Mixing them (e.g., using `::alert` with `:::` closing) will break rendering.

Common usage patterns observed:
- **Prerequisites warnings** at the top of lab index pages: `::alert[This chapter assumes you have completed the Prerequisites...]{type="warning"}`
- **Cost warnings** for self-paced labs: `:::alert{type="warning"} CAREFUL... :::`
- **Informational notes** about AWS services: `::alert[Amazon RDS provides...]{type="info"}`
- **Cross-reference notes** to related workshops: `::alert[Please check [Workshop Name](URL) for a deep dive...]{type="info"}`

### 5. Expandable Sections

Used for optional content, CLI alternatives, or verbose code:

```
::::expand{header="Code"}
Content here, including code blocks.
::::
```

Common uses:
- Optional CLI alternatives to console steps
- Detailed code snippets that would clutter the main flow
- Additional context for advanced users

### 6. Children Directive

Used on category and lab index pages to auto-list sub-pages:

```
::children
```

Or within a section:

```markdown
## This lab contains following tasks:

::children
```

### 7. Image References

- All images use the `/static/<path>/` prefix matching the content structure.
- Path pattern: `/static/<category>/<lab-folder>/<optional-task>/filename.png`
- Examples:
  - `/static/2-Foundation/Lab6-Monitoring/task1/cwlogs.png`
  - `/static/3-Intermediate/SecretManager/sm-main-page.png`
  - `/static/4-Advanced/PgVector/pgpgvector.png`
- Alt text should be descriptive of the actual image content.
- Image filenames should be descriptive (e.g., `cwlogs.png`, `createalarm.png`, `sm-rotate-secret.png`).
- No spaces in filenames that are referenced from markdown (use hyphens or underscores).
- Logo images may be at the top level of `/static/` (e.g., `/static/Amazon-RDS_light-bg@4x.png`).

### 8. Internal Links

- Use absolute paths from the content root: `/1-prerequisites/`, `/2-foundation/lab1-create/`.
- Links are case-insensitive in Hugo but should match the folder naming convention.
- External links to AWS documentation and console are acceptable and encouraged.
- Console links should use region-agnostic URLs where possible (e.g., `https://console.aws.amazon.com/rds/home#databases:`).
- Links to other workshops use the `catalog.workshops.aws` domain.

### 9. Prerequisites Section

#### rdspg Pattern

Labs reference the Prerequisites section and the first foundation lab:

```markdown
::alert[This chapter assumes you have completed the [Prerequisites](/1-prerequisites/) and have already created an RDS PostgreSQL instance in the [first lab](/2-foundation/lab1-create/).]{type="warning"}
```

Some labs add additional prerequisites:

```markdown
::alert[This chapter assumes you have completed the [Prerequisites](/1-prerequisites/), have already created an RDS PostgreSQL instance in the [first lab](/2-foundation/lab1-create/) and have already created a Secret in [Create Secret lab](/2-foundation/lab1-create/task3/).]{type="warning"}
```

#### aurora-pg-lab Pattern

```markdown
## Prerequisites

This lab requires the following lab modules to be completed first.

* [All Lab Prerequisites](/1-prereq)
* [Creating a New Aurora Cluster](/1-prereq/create-aurora-cluster) (Mandatory if you followed [bare minimal lab environment without the Aurora PostgreSQL Cluster](/1-prereq/i-need-to-deploy-lab-environment-manually/setup-without-aurora-pg) in the **All Lab Prerequisites** section. Optional otherwise.)
* [Configure VSCode and Initialize Database](/1-prereq/VSCode-client)  (Mandatory if you followed [bare minimal lab environment without the Aurora PostgreSQL Cluster](/1-prereq/i-need-to-deploy-lab-environment-manually/setup-without-aurora-pg) in the **All Lab Prerequisites** section. Skip otherwise.)
```

### 10. Security Standards

- **No hardcoded passwords** in production-like code. If passwords are required for a lab, they must be accompanied by a warning callout recommending AWS Secrets Manager or equivalent.
- **No real PII** in sample data. Use placeholder names, emails, and identifiers.
- Passwords should use simple ASCII characters to avoid terminal encoding issues (avoid `£`, `{`, `|` and similar).
- Environment variables (`$PGHOST`, `$DBENDP`, `$DBPASS`, `$DBUSER`, `$AWSREGION`) should be used where the workshop infrastructure provides them.
- Connection strings should not embed credentials when environment variables are available.
- **No AWS account IDs, access keys, or secret keys** should appear in content.
- IAM roles and policies in examples should follow least-privilege principles.
- When demonstrating credential rotation or secrets management, emphasize it as a best practice.

### 11. Content Quality

- Correct grammar and spelling throughout.
- Consistent step numbering (1.1, 1.2 or ### Step 1, ### Step 2).
- Every SQL/CLI command block should be preceded by a brief explanation of what it does.
- Every screenshot should be preceded or followed by context explaining what the participant should see.
- Output images should appear after the command that produces them, not before.
- Labs should include a cleanup/teardown section or reference the main cleanup page.
- Technical terms should be used consistently (e.g., always "RDS PostgreSQL" or "Amazon RDS for PostgreSQL", not mixing abbreviations without definition).
- The lab should flow logically from setup through execution to validation.
- No contradictory instructions (e.g., "replace the password" when the password is already in the command).
- Console navigation instructions should include the specific path (e.g., "from the services dropdown or search bar in Navigation").

### 12. Cleanup / Teardown

Every lab that creates AWS resources, databases, users, or extensions should either:
- Include its own cleanup section as the final sub-page, OR
- Reference the main cleanup page with specific instructions for what this lab created.

The rdspg workshop uses a centralized cleanup page (`/7-Lab-cleanup/`) that lists per-lab cleanup steps:

```markdown
::alert[In order to avoid unnecessary charges we recommend to decommission the resources that were created for this lab.]{type="warning"}

1. If you completed the Graviton Lab...delete the `rds-pg-x86` and `rds-pg-graviton` RDS databases...
2. If you completed the [Service Catalog](/4-advanced/6-servicecatalog) lab, delete the `SvcCatalogSetup` cloudformation stack.
3. Delete CloudFormation Stack `rds-pg-labs` created in [Prerequisites section](/1-prerequisites/task2/)
4. Manually created resources per Lab:
  - Cleanup for Lab [Backup and Restore](/2-foundation/lab4-backup/task6#cleanup-restored-database-copies)
```

### 13. Workshop Studio Configuration (contentspec.yaml)

The `contentspec.yaml` file at the repository root defines:
- Workshop metadata (author, description, locale)
- Account configuration (account sources, IAM policies, managed policies)
- Region configuration (required, recommended, optional regions)
- Infrastructure (CloudFormation templates with parameters)
- Additional navigation links

Key review points:
- IAM policies should follow least-privilege
- CloudFormation parameters should use Workshop Studio magic variables where appropriate (e.g., `{{.ParticipantRoleArn}}`, `{{.AssetsBucketName}}`)
- Region configuration should include commonly used regions
- Participant-visible stack outputs should be limited to what's needed

### 14. Static Assets & Templates

- CloudFormation templates live under `static/templates/`
- IAM policy documents live under `static/templates/` as JSON files
- The `assets/` directory may contain supplementary scripts and zip files
- The `resources/` directory may contain code samples, policies, and generated content

---

## Workshop Comparison: aurora-pg-lab vs rdspg

| Aspect | aurora-pg-lab | rdspg |
|--------|--------------|-------|
| Database engine | Aurora PostgreSQL | RDS PostgreSQL |
| Code blocks | Primarily `:::code` directive | Mix of `:::code` and standard fenced blocks |
| Prerequisites format | Bulleted list with Mandatory/Optional guidance | Inline alert with links |
| Category weights | Hundreds (100, 200, 400) | Tens (1, 20, 30, 40) |
| File naming | `index.en.md` | Mix of `index.en.md` and `index.md` |
| Cleanup | Per-lab cleanup sections | Centralized cleanup page + per-lab references |
| Front matter `pre` | Less common | Frequently used for icons and numbering |
| Front matter `chapter` | Used on category pages | Used on category and lab index pages |
| Emoji in titles | Less common | Frequently used (🗃️, 🏛️, 📊, 📼, 🧹, ⚗️) |
| External workshop links | Inline | `::alert` callouts with links to dedicated workshops |

---

## AWS Well-Architected Framework Review

Every lab should align with the AWS Well-Architected Framework pillars where applicable. Not every pillar applies to every lab, but reviewers should verify that labs don't teach anti-patterns and that they promote best practices when the opportunity arises naturally.

### Security Pillar

- **Encryption at rest**: Labs that create databases should mention or enable storage encryption (KMS). If encryption is not enabled, a callout should explain why (e.g., lab simplicity) and recommend it for production.
- **Encryption in transit**: Labs involving database connections should recommend or enforce SSL/TLS. Connection strings should include `sslmode=require` or equivalent where appropriate.
- **Network isolation**: Database instances should be created in private subnets. Labs should not make databases publicly accessible unless explicitly teaching that concept with a warning.
- **Credential management**: Prefer AWS Secrets Manager or IAM authentication over static passwords. If static passwords are used for simplicity, include a callout recommending Secrets Manager for production.
- **Least-privilege IAM**: IAM policies in examples should grant only the permissions needed. Avoid `*` resource wildcards unless explaining why.
- **Detective controls**: Labs that teach monitoring or auditing should mention CloudTrail, RDS event subscriptions, or audit logging as best practices.

### Performance Efficiency Pillar

- **Right-sizing**: Labs should explain why a particular instance class is chosen (e.g., `db.t3.medium` for lab cost efficiency). Include a note that production workloads should be sized based on actual requirements.
- **Read scaling**: Labs covering read replicas should explain when to use them (read-heavy workloads, reporting, geographic distribution).
- **Connection pooling**: Labs involving application connections should mention RDS Proxy or PgBouncer for connection management at scale.
- **Storage optimization**: Labs should mention the differences between gp2/gp3/io1 storage types when creating instances, or at minimum note that storage type affects performance.
- **Query performance**: Labs with SQL examples should avoid obviously inefficient patterns (e.g., `SELECT *` on large tables without LIMIT) unless teaching optimization.
- **Caching**: Where applicable, mention ElastiCache or application-level caching as a complement to database scaling.

### Reliability / High Availability Pillar

- **Multi-AZ**: Labs that create database instances should explain the Multi-AZ option. If Single-AZ is used for cost savings in the lab, include a callout recommending Multi-AZ for production.
- **Backup strategy**: Labs should mention automated backups and their retention period. Point-in-time recovery (PITR) should be referenced when teaching backup concepts.
- **Failover testing**: Labs covering HA should include steps to test failover and explain expected behavior (DNS propagation, connection interruption duration).
- **Read replica promotion**: Labs with read replicas should explain that replicas can be promoted in a disaster recovery scenario.
- **Recovery objectives**: When teaching backup/restore, labs should mention RTO and RPO concepts and how different strategies affect them.
- **Connection handling**: Labs should demonstrate or recommend retry logic and connection failover handling in application code.

### Cost Optimization Pillar

- **Instance sizing awareness**: Labs should use the smallest instance class that meets the lab's needs (e.g., `db.t3.medium` or `db.t3.micro` rather than `db.r5.xlarge`).
- **Cleanup emphasis**: Every lab must emphasize resource cleanup to avoid ongoing charges. Cost warnings should appear at both the start and end of labs that create billable resources.
- **Cost callouts**: When introducing a feature that has additional cost (Enhanced Monitoring, Performance Insights, RDS Proxy, Multi-AZ), include a brief note about the cost implications.
- **Reserved capacity**: When discussing production deployments, mention Reserved Instances or Savings Plans as cost optimization strategies.
- **Storage costs**: Note that allocated storage incurs cost even when unused. Labs should use minimal storage allocations (e.g., 20 GB).
- **Data transfer**: Labs involving cross-region replication or data export should mention data transfer costs.

### Operational Excellence Pillar

- **Monitoring**: Labs should recommend enabling Enhanced Monitoring, Performance Insights, or CloudWatch Database Insights where relevant.
- **Logging**: Labs should enable and reference appropriate log exports (PostgreSQL log, upgrade log) to CloudWatch.
- **Automation**: Labs that perform manual console steps should include CLI/IaC alternatives (even if in expandable sections) to promote automation.
- **Tagging**: Resources created in labs should include tags (at minimum a `Name` tag) to demonstrate the tagging best practice.
- **Event notifications**: Labs creating databases should mention RDS Event Subscriptions for operational awareness.
- **Parameter groups**: Labs should use custom parameter groups rather than the default, explaining that defaults cannot be modified.

### Sustainability Pillar

- **Right-sizing**: Reinforce that over-provisioned instances waste energy and cost. Use appropriate instance sizes.
- **Graviton**: When applicable, mention Graviton-based instance types as a more energy-efficient option.
- **Efficient queries**: Promote efficient SQL patterns that reduce compute cycles.
- **Cleanup**: Emphasize deleting unused resources to avoid idle infrastructure.

---

## Common Issues Found in Reviews

Based on patterns observed across both workshops, these are the most frequently encountered issues:

1. **Mixed code block styles** — Using `:::code` in some places and fenced blocks in others without clear rationale.
2. **Missing language attribute** — Code blocks without a specified language.
3. **Broken internal links** — Links that don't match the actual folder structure (case sensitivity, missing trailing slashes).
4. **Screenshots without context** — Images placed without preceding or following explanation.
5. **Hardcoded region** — Using `us-east-1` directly instead of `$AWSREGION` environment variable.
6. **Missing prerequisite alert** — Lab index pages that don't warn about required prior labs.
7. **Stale files** — `.DS_Store`, `.bak`, `.tmp`, `.new` files committed to the repository.
8. **Inconsistent naming** — Mixing spaces and hyphens in folder/file names.
9. **Missing cleanup instructions** — Labs that create resources but don't document how to remove them.
10. **Incorrect alert syntax** — Mixing `::` and `:::` colon counts, or using invalid alert types.
