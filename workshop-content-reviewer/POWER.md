---
name: "workshop-content-reviewer"
displayName: "Workshop Content Reviewer"
description: "Reviews AWS Workshop Studio lab content for any service or topic against structure, formatting, security, content quality, cleanup, and Well-Architected best practices, then produces a Review.md report."
keywords: ["workshop", "workshop-studio", "lab-content", "content-review", "hugo", "markdown", "aws", "well-architected", "technical-writing", "documentation-review"]
author: "Workshop Content Team"
---

# Workshop Content Reviewer

## Overview

This power provides a checklist and ruleset for reviewing new or updated AWS workshop lab content before it is merged. It applies to any Workshop Studio (Hugo-based) workshop, whatever the subject: databases, serverless, containers, compute, networking, security, analytics, AI/ML, or developer tooling.

The rules come from lessons learned reviewing real workshops. The most important one: **workshops legitimately differ in their house conventions** (weights, prerequisite format, cleanup model, code block style). A good review enforces the universal rules strictly and checks the house rules for internal consistency, rather than imposing one workshop's style on another.

## Onboarding

### What This Power Reviews

- **File and directory structure** — layout under `content/` and `static/`, naming, stale files
- **Front matter** — required YAML fields, weight ordering, chapter metadata
- **Workshop Studio directives** — `:::code`, `::alert`, `::::expand`, `::children`, `::image`
- **Code blocks** — language attributes, copy actions, placeholders, environment variables
- **Images** — paths, existence, alt text, naming, unused assets
- **Links** — internal paths, external links, no `localhost`
- **Prerequisites** — clear statement of what must be done first
- **Delivery modes** — separate, complete setup paths for AWS-provided accounts (Workshop Studio events) and participants' own accounts
- **Security** — credentials, PII, account identifiers, least privilege
- **Content quality** — grammar, step numbering, explanations, flow, accessibility
- **Cleanup / teardown** — every created resource can be removed
- **Workshop Studio configuration** — `contentspec.yaml`, CloudFormation/CDK templates, IAM policies
- **Well-Architected alignment** — the six pillars, applied to whatever service the lab teaches
- **Domain-specific checks** — targeted checks for the technology area the lab covers

### When to Activate

Activate this power when a user asks you to:
- Review or audit new or changed workshop/lab content before merging
- Validate a lab against workshop standards
- Check a PR, branch, folder, or zip of workshop content
- Make a new lab consistent with the rest of its workshop
- Compare conventions between two workshops

### How to Use

1. Activate this power.
2. Read the `review-checklist` steering file.
3. **Run Step 0 (Discover House Conventions)** below against the target workshop before judging the new content.
4. Walk through checklist sections A–P against every new or changed file.
5. Pick the relevant domain module(s) in section P based on what the lab teaches.
6. Write a `Review.md` report using the template in the steering file.

### Output

The review produces a **`Review.md`** file in the root of the reviewed content directory (or the working directory when reviewing a PR/zip). It must follow the Review Report Template in the `review-checklist` steering file and include:
- Review metadata (lab, workshop, domain, delivery mode, reviewer, date, overall status)
- The house conventions detected in Step 0
- Critical issues (must fix before merge)
- Warnings (should fix)
- Recommendations (nice to have)
- Files to remove
- Consistency notes
- A summary table of checklist categories with PASS / FAIL / N/A

Every finding should cite the file path (and line or heading where possible) and propose a concrete fix.

## Available Steering Files

- **review-checklist** — Full checklist with pass/fail criteria (sections A–P), domain modules, severity guidance, and the `Review.md` report template.

---

## Step 0: Discover House Conventions

Before reviewing new content, sample 3–5 existing, published labs in the same workshop and record:

| Convention | What to look for |
|------------|------------------|
| Page file name | `index.en.md` vs `index.md` |
| Folder naming | Numbered prefixes (`1-Prerequisites`), descriptive names (`Lab1-Create`), task folders (`task1/`) |
| Weight scheme | Tens (10, 20, 30) vs hundreds (100, 200) vs category + offset (310, 315) |
| Front matter extras | Use of `chapter`, `pre`, emoji in titles |
| Code block style | `:::code` directive vs fenced blocks, or a deliberate mix |
| Prerequisites format | Inline alert vs bulleted list with Mandatory/Optional/Skip guidance |
| Cleanup model | Per-lab cleanup page vs centralized cleanup page vs both |
| Environment variables | Names the environment exports (e.g., `$AWS_REGION`, stack outputs, service endpoints) |
| Delivery modes | Workshop Studio event, self-paced in own account, or both; where the chooser page and each path's setup pages live (see section 15) |

Record these in the `Review.md` "House Conventions" section. New content that deviates from them is a **consistency warning**, not a universal failure, unless it also breaks a universal rule.

If there is no existing content (a brand-new workshop), apply the defaults in this document and recommend the author write down their conventions.

---

## Universal Patterns (Reference)

### 1. File & Directory Structure

- Content lives under `content/<Category>/<LabName>/` with sub-folders per page (e.g., `task1/`, `task2/`).
- Static assets live under `static/` mirroring the content structure (e.g., `static/<Category>/<LabName>/task1/`).
- Every page is an `index.en.md` or `index.md` inside its own folder, consistent within the workshop.
- No stale, duplicate, or "OLD"/"BACKUP"/"USELESS" files.
- No OS or editor artifacts (`.DS_Store`, `__MACOSX/`, `Thumbs.db`, `.bak`, `.tmp`, `.new`, `.swp`, `*.code-workspace`).
- No spaces in file or folder names; use hyphens or underscores.
- Ordering is controlled by `weight`, optionally reinforced by numbered folder prefixes.

### 2. Front Matter

Every page needs YAML front matter with at least:

```yaml
---
title: "Human-Readable Title"
weight: 10
---
```

Category and lab index pages may add:

```yaml
---
chapter: true
pre: <b>1. </b>
title: "🧪 Lab Title"
weight: 10
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Human-readable page title; emoji allowed if the workshop uses them |
| `weight` | Yes | Numeric ordering; unique among siblings |
| `chapter` | No | `true` for category/section index pages |
| `pre` | No | Navigation prefix (icon or bold number) |
| `date` | No | ISO date |

Weight rules that hold across all workshops:
- Sibling pages have unique weights; duplicates render in unpredictable order.
- Leave gaps (10, 20, 30) so pages can be inserted later.
- The new lab's weight places it where the author intends relative to existing labs.

### 3. Code Blocks

**Workshop Studio `:::code` directive** (preferred for commands participants run):

```
:::code{showCopyAction=true showLineNumbers=false language=bash}
aws sts get-caller-identity
:::
```

- `showCopyAction=true` on anything participants copy.
- `language=` always set (`bash`, `sql`, `python`, `json`, `yaml`, `typescript`, `java`, etc.).
- `showLineNumbers=true` only when the text refers to line numbers.

**Standard fenced blocks** (` ```lang `) are acceptable for sample output, content inside `::::expand`, and workshops that use them by convention. Always include a language.

Best practices:
- Values that vary per participant use environment variables the lab environment provides, or clearly marked placeholders like `<your-bucket-name>`, with an instruction to replace them.
- Do not hardcode region or account ID; use `$AWS_REGION` / `$AWS_ACCOUNT_ID` or the workshop's equivalents.
- Multi-line CLI commands use `\` continuation.
- Each block does one logical step. Don't bury a destructive command in the middle of a long block.
- Commands must be idempotent or say what happens on re-run, since participants often re-run steps.
- Commands run as-is in the documented environment (shell, OS, tool versions). Pin or state tool versions when it matters.

### 4. Alerts & Callouts

**Inline (single line):**
```
::alert[Alert text here.]{type="info"}
```

**Block (multi-line):**
```
:::alert{header="Important" type="warning"}
Multi-line alert content here.
:::
```

- Supported types: `info`, `success`, `warning`, `error`. Flag anything else.
- Colon counts must match: `::` for inline, `:::` open and close for block. Mixing them breaks rendering.
- Use `warning` for cost, security, data-loss, and prerequisite notices; `info` for context and cross-references; `success` for checkpoints.

Common uses:
- Prerequisite notice at the top of each lab index page
- Cost warning for self-paced participants running in their own account
- Security note wherever a lab takes a shortcut that is not production-safe
- Cross-reference to a deeper workshop or documentation

### 5. Expandable Sections

```
::::expand{header="CLI alternative"}
Content, including code blocks.
::::
```

Use for optional CLI/IaC alternatives, long code listings, troubleshooting, and advanced detail. Headers should describe the content, not just say "Click here".

### 6. Children Directive

```markdown
## This lab contains the following tasks:

::children
```

Use on category and lab index pages that should auto-list sub-pages. Do not use it on leaf pages.

### 7. Images

- Paths start at `/static/` and mirror the content structure.
- Every referenced image exists and every image in the lab's static folder is referenced.
- Alt text describes what the image shows (not "screenshot" or "image1").
- File names are descriptive and lowercase with hyphens (e.g., `create-function-console.png`).
- Screenshots show no account IDs, ARNs with real account numbers, emails, or internal hostnames. Blur or crop them.
- Screenshots match the current console UI; outdated UIs confuse participants.
- Screenshots come after the step that produces them, with text that says what to look for.

### 8. Links

- Internal links use absolute paths from the content root and match real folder names.
- No `localhost`, internal-only, or personal URLs.
- External documentation links point to official sources and resolve.
- Console links are region-agnostic where possible (e.g., `https://console.aws.amazon.com/<service>/home`).
- Links to other workshops use the `catalog.workshops.aws` (or `catalog.us-east-1.prod.workshops.aws`) domain.

### 9. Prerequisites

Each lab index page must say what must be done first. Two patterns are accepted; use whichever the workshop already uses.

**Inline alert:**
```markdown
::alert[This lab assumes you have completed the [Prerequisites](/1-prerequisites/) and the [Getting Started](/2-getting-started/) lab.]{type="warning"}
```

**Bulleted list with guidance:**
```markdown
## Prerequisites

This lab requires the following to be completed first:

* [Workshop Prerequisites](/1-prerequisites/)
* [Set up the environment](/1-prerequisites/setup/) (Mandatory if you are running in your own account. Skip if you are at an AWS event.)
```

Lessons learned:
- Say whether each prerequisite is Mandatory, Optional, or Skip, and under which condition.
- Branch clearly for the two delivery modes: AWS-provided event account vs own account (see section 15).
- Call out labs that are independent of each other so participants can jump around.

### 10. Security

- No passwords, tokens, API keys, access keys, or secret keys in content, code, templates, or screenshots.
- If a lab uses a static password for simplicity, a warning callout recommends AWS Secrets Manager (or the service's native secret mechanism) for production.
- Lab passwords use plain ASCII; avoid characters that break shells or encodings (`£`, `{`, `|`, `$`, `` ` ``, quotes).
- No real PII in sample data; use placeholder names, `example.com` emails, and reserved phone ranges.
- No real AWS account IDs; use `123456789012` or a variable.
- IAM policies follow least privilege; wildcards (`*`) are justified in text.
- Credentials flow through environment variables, IAM roles, or secrets services, never inline in connection strings.
- Resources are not public (open security groups, public buckets, public endpoints) unless the lab teaches that, with a warning.

### 11. Content Quality

- Correct grammar and spelling. Watch for common slips like "preformed/performed", "secton/section", "seperate/separate".
- One step-numbering style per page.
- Each command or console step is preceded by what it does and why.
- Each screenshot has context explaining what to observe.
- Each task ends with a way to validate success (expected output, a check command, or a `success` alert).
- Terminology is consistent; use the official service name on first mention (e.g., "Amazon Simple Storage Service (Amazon S3)", then "Amazon S3").
- No contradictory instructions (e.g., "replace the value" when it is already filled in).
- Console navigation is specific ("In the search bar, type **Lambda** and choose **Lambda**").
- UI element names are **bold** and match the console exactly.
- The lab flows setup → execution → validation → cleanup, and states learning objectives and estimated time up front.
- Inclusive, accessible language; no idioms that don't translate, no "simply/just/easy".

### 12. Cleanup / Teardown

Every lab that creates resources must say how to remove them. Two models are accepted:
- **Per-lab cleanup**: a final sub-page in the lab.
- **Centralized cleanup**: a workshop-level cleanup page listing per-lab steps, with each lab linking to its section.

Requirements for both:
- Cover every resource: stacks, instances, functions, buckets, containers, endpoints, users, roles, policies, parameters, log groups, and in-resource objects (tables, indexes, extensions).
- Order steps by dependency (children before parents; empty buckets before deleting them).
- Provide copyable commands, with a console alternative where useful.
- Open with a cost warning for self-paced participants.
- Make clear what event participants can skip because the account is reclaimed.

Example:
```markdown
::alert[To avoid ongoing charges, delete the resources created in this lab.]{type="warning"}

1. If you completed the [Optional Lab](/3-advanced/optional-lab/), delete the `optional-lab-stack` CloudFormation stack.
2. Delete the CloudFormation stack created in [Prerequisites](/1-prerequisites/setup/).
3. Manually created resources per lab:
   - [Lab 2 cleanup](/2-foundation/lab2/cleanup/)
```

### 13. Workshop Studio Configuration (`contentspec.yaml`)

`contentspec.yaml` defines workshop metadata, account sources, IAM policies, regions, infrastructure templates, and navigation links.

Review points:
- Valid structure for the declared `version`.
- Participant IAM policies follow least privilege and cover everything the labs actually do (a missing permission breaks the lab at the event).
- Templates use Workshop Studio magic variables where appropriate (`{{.ParticipantRoleArn}}`, `{{.AssetsBucketName}}`, `{{.AssetsBucketPrefix}}`).
- Region configuration matches where every service used is available.
- Stack outputs shown to participants are limited to what they need.
- Service quotas (instance counts, GPU capacity, concurrency) are enough for the expected event size.

### 14. Static Assets & Templates

- CloudFormation/CDK/Terraform templates live under `static/` (commonly `static/templates/`) or `assets/`.
- Templates deploy cleanly in a fresh account, tag resources, and delete without manual steps (no retained resources unless documented).
- Scripts and sample code in `assets/` or `resources/` follow the same security rules as page content.
- Large binaries (zips, datasets, spreadsheets) are justified, versioned, and referenced from content.

### 15. Delivery Modes: AWS-Provided Accounts vs Own Account

Most workshops run in two ways, and each needs its own setup path:

| | AWS-provided account (Workshop Studio event) | Participant's own account (self-paced) |
|---|---|---|
| Account access | Event access code or link; temporary credentials | Participant's IAM user/role |
| Infrastructure | Pre-deployed from `contentspec.yaml` | Participant deploys a template from the workshop |
| Permissions | Limited by the Workshop Studio participant role | Whatever the participant has; may be broader or narrower |
| Cost | Paid by AWS; account is reclaimed after the event | Paid by the participant until cleanup |
| Duration | Fixed event window | Unlimited |
| Region | Set by the event | Participant chooses |

**Required structure.** The workshop's prerequisites must include:

1. **A chooser page** at the top of prerequisites that describes both paths and links to each, with a "Not sure which to choose?" tie-breaker (e.g., "If you received an event access code or workshop URL from an instructor, use the AWS-provided path. Otherwise, use your own account.").
2. **An AWS-provided account path** (e.g., `in-a-workshop-using-workshop-studio/`) covering sign-in through Workshop Studio, opening the console, and locating pre-deployed resources and stack outputs.
3. **An own-account path** (e.g., `deploy-in-your-own-account/`) covering:
   - Required permissions (ideally a sample IAM policy) and a warning against using the root user
   - Supported regions and a region selection step
   - A downloadable or one-click template (CloudFormation/CDK/Terraform) that deploys the same environment the event provides
   - Expected deployment time and how to confirm the stack succeeded
   - A cost estimate or cost warning, and a link to the cleanup page
   - Any service prerequisites the event account pre-enables (model access, quota increases, service-linked roles, opt-in regions)
   - Optional variants if offered (e.g., "full environment" vs "minimal environment, create the main resource manually in a later lab"), with the downstream labs that each variant requires or lets you skip

**Parity.** Both paths must end in the same state: the same resources, names, environment variables, and stack outputs. Labs after prerequisites should then work identically regardless of path. If a lab can't (e.g., it needs a quota only events have), it must say so at the top.

**Lab-level checks.** Inside individual labs:
- Steps that differ by path are clearly branched (headings, tabs, or `::alert` callouts like "If you are using your own account...").
- Cost warnings target own-account participants; cleanup says what event participants can skip because the account is reclaimed.
- Don't assume event-only conveniences (pre-created resources, pre-enabled model access, specific regions) without saying so.
- Don't assume own-account freedoms (creating IAM users, changing account settings, using unlisted regions) that the Workshop Studio participant role blocks.
- References to stack names, outputs, and environment variables match between the event template in `contentspec.yaml` and the own-account template. A mismatch is a Critical issue.

**Lessons learned:**
- Missing one path is the most common gap. Workshops built for events often have no own-account path, or an outdated one.
- Own-account templates drift from the event template. Compare their resources, parameters, and outputs.
- Self-paced participants are the ones who pay, so cleanup and cost warnings matter most on their path.
- Name the paths by the participant's situation ("I am at an AWS event" / "I am using my own AWS account"), not by internal tool names alone.

---

## Well-Architected Alignment (Service-Agnostic)

Labs don't need to cover every pillar, but they must not teach anti-patterns, and should mention the best practice when a shortcut is taken for simplicity.

### Security
- Encryption at rest (KMS) is enabled, or the lab explains why not and recommends it for production.
- Encryption in transit (TLS) is used for connections and endpoints.
- Resources sit in private subnets or behind authentication unless the lab teaches public exposure.
- Credentials use IAM roles, IAM auth, or a secrets service instead of static values.
- IAM is least-privilege; wildcards are explained.
- Audit and detection (CloudTrail, service logs, GuardDuty/Security Hub where relevant) are mentioned in monitoring or security labs.

### Reliability
- Multi-AZ (or the service's HA equivalent) is explained; single-AZ shortcuts carry a production callout.
- Backup, versioning, or snapshot strategy is mentioned where data is stored, with RPO/RTO in backup/DR labs.
- HA/DR labs include a failover test and describe expected behavior.
- Application code demonstrates or recommends retries with backoff and idempotency.

### Performance Efficiency
- Resource sizing (instance class, memory, concurrency, shard count) is explained, with a note that production should size from real requirements.
- Scaling options (auto scaling, read scaling, caching, pooling) are mentioned where relevant.
- Sample code and queries avoid obvious inefficiencies unless teaching optimization.

### Cost Optimization
- The smallest resource that meets lab needs is used.
- Features with extra cost carry a short cost note.
- Cost warnings appear at the start and the cleanup of labs that create billable resources.
- Data transfer, cross-region, and idle-resource costs are noted where relevant.
- Production cost levers (Savings Plans, Reserved capacity, Spot, lifecycle policies) are mentioned when discussing production.

### Operational Excellence
- Monitoring and logging (CloudWatch metrics, logs, alarms, service-specific insights) are enabled or recommended.
- Console steps have a CLI/IaC alternative, even inside `::::expand`.
- Resources are tagged (at minimum `Name`, ideally a workshop/lab tag).
- Event notifications (EventBridge, SNS, service events) are mentioned for operational awareness.
- Custom configuration (parameter groups, config files) is preferred over modifying defaults.

### Sustainability
- Right-size and remove idle resources.
- Mention AWS Graviton or other efficient options where applicable.
- Promote efficient code and queries that reduce compute.

---

## Common Issues Found in Reviews

Seen repeatedly across workshops:

1. **Mixed code block styles** without a reason.
2. **Missing language attribute** on code blocks.
3. **Broken internal links** — case mismatch, renamed folders, missing trailing slash.
4. **Screenshots without context**, or before the step that produces them.
5. **Hardcoded region or account ID** instead of variables.
6. **Missing prerequisite notice** on lab index pages.
7. **Stale and OS files** — `.DS_Store`, `.bak`, `.tmp`, `.new`, "OLD" copies.
8. **Inconsistent naming** — spaces mixed with hyphens.
9. **Missing or incomplete cleanup**, especially for manually created resources.
10. **Incorrect alert syntax** — colon mismatches or unsupported types.
11. **Duplicate sibling weights** causing unpredictable page order.
12. **Secrets or account IDs in screenshots**, not just in text.
13. **Participant IAM policy missing a permission** the lab needs, discovered only at the event.
14. **Assuming one delivery mode** — steps that only work at an event, or only in an own account.
15. **Missing or stale own-account path** — no self-paced setup, or an own-account template that no longer matches the event template.
