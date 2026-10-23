# Workshop Content Review Checklist

Use this checklist to review new or changed workshop lab content before it is merged into any AWS Workshop Studio workshop. For each item, mark PASS, FAIL, or N/A and note the file and the issue.

Run **Step 0: Discover House Conventions** (in `POWER.md`) first. Items marked *(house)* are judged against those conventions; all other items are universal.

---

## Severity Guide

| Severity | Meaning | Examples |
|----------|---------|----------|
| **Critical** | Blocks merge. Breaks the lab, leaks data, or creates a security/cost risk. | Exposed credential or account ID, broken directive that stops rendering, command that fails as written, missing cleanup for billable resources, missing IAM permission |
| **Warning** | Should fix before merge. Hurts participant experience or consistency. | Missing language attribute, screenshot without context, inconsistent house convention, missing prerequisite notice |
| **Recommendation** | Nice to have. | Extra CLI alternative, cross-reference to a deeper workshop, wording polish |

---

## A. File & Directory Structure

- [ ] Content is organized as `content/<Category>/<LabName>/[sub-pages]/index.en.md` (or `index.md`) *(house: file name)*
- [ ] Static assets are under `static/` mirroring the content structure
- [ ] No stale or duplicate files ("OLD", "BACKUP", "USELESS", "copy", numbered duplicates)
- [ ] No OS/editor artifacts (`.DS_Store`, `__MACOSX/`, `Thumbs.db`, `.bak`, `.tmp`, `.new`, `.swp`, `*.code-workspace`)
- [ ] No spaces in file or folder names
- [ ] Folder naming follows the workshop's pattern (numbered prefixes, `taskN/` sub-folders) *(house)*
- [ ] `.gitkeep` only in otherwise-empty directories

## B. Front Matter

- [ ] Every page has YAML front matter with `title` and `weight`
- [ ] `title` is human-readable and consistent with sibling pages (emoji only if the workshop uses them) *(house)*
- [ ] Sibling pages have unique `weight` values
- [ ] Weights follow the workshop's numbering scheme and place the lab in the intended position *(house)*
- [ ] Category/lab index pages use `chapter: true` where the workshop does *(house)*
- [ ] `pre` uses valid HTML/icon syntax if present
- [ ] No unsupported front matter keys (valid: `title`, `weight`, `date`, `chapter`, `pre`, plus any the workshop already uses)

## C. Code Blocks & Commands

- [ ] Participant commands use `:::code{showCopyAction=true showLineNumbers=false language=<lang>}` or fenced blocks, per the workshop's style *(house)*
- [ ] Every code block specifies a language
- [ ] `showCopyAction=true` on every block participants copy
- [ ] Every block is closed (`:::` or ` ``` `)
- [ ] Per-participant values use environment variables or clearly marked placeholders (`<your-value>`) with replace instructions
- [ ] No hardcoded region or account ID
- [ ] Multi-line CLI commands use `\` continuation
- [ ] Commands run as written in the documented environment (shell, OS, tool versions)
- [ ] Commands are safe to re-run, or the text says what happens on re-run
- [ ] Destructive commands are in their own block with a warning
- [ ] Code block style is consistent within the lab

## D. Alerts & Callouts

- [ ] Inline alerts use `::alert[text]{type="..."}`
- [ ] Block alerts use `:::alert{header="..." type="..."}` with a matching `:::` close
- [ ] No mixed colon counts
- [ ] Alert types are one of `info`, `success`, `warning`, `error`
- [ ] Security shortcuts have a warning callout
- [ ] Lab index page has a prerequisite notice
- [ ] Labs creating billable resources have a cost warning for self-paced participants

## E. Expandable Sections

- [ ] Uses `::::expand{header="..."}` with a matching `::::` close
- [ ] Header describes the content ("CLI alternative", "Full source code", "Troubleshooting")
- [ ] Nested code blocks render correctly
- [ ] Used for optional/supplementary content, not required steps

## F. Children Directive

- [ ] Category index pages use `::children` where sub-pages should be auto-listed
- [ ] Multi-task lab index pages use `::children` after a "This lab contains the following tasks:" heading
- [ ] Not used on leaf pages

## G. Images

- [ ] Paths use `/static/...` and match the content structure
- [ ] Every referenced image exists
- [ ] Every image in the lab's static folder is referenced
- [ ] Alt text describes the image content
- [ ] File names are descriptive, lowercase, hyphenated, no spaces
- [ ] No account IDs, real ARNs, emails, internal hostnames, or secrets visible in screenshots
- [ ] Screenshots reflect the current console UI
- [ ] Screenshots follow the step that produces them, with context on what to observe

## H. Links

- [ ] Internal links use absolute paths and resolve to existing pages
- [ ] No `localhost`, internal-only, or personal URLs
- [ ] External links point to official sources and resolve
- [ ] Console links are region-agnostic where possible
- [ ] Links to other workshops use the `catalog.workshops.aws` domain
- [ ] Prerequisite links match the workshop's standard paths *(house)*

## I. Prerequisites

- [ ] Lab index page states prerequisites using the workshop's format (inline alert or bulleted list) *(house)*
- [ ] Each prerequisite says Mandatory / Optional / Skip, and under which condition
- [ ] Event vs own-account paths are clearly separated where they differ
- [ ] Dependencies on other labs are listed; independent labs say so
- [ ] Required tools, versions, model access, quotas, or region availability are stated
- [ ] Learning objectives and estimated duration are stated

## I2. Delivery Modes (AWS-Provided vs Own Account)

See `POWER.md` section 15.

- [ ] Prerequisites start with a chooser page linking to both paths, with a "Not sure which to choose?" tie-breaker
- [ ] AWS-provided account path covers Workshop Studio sign-in, console access, and where to find pre-deployed resources/outputs
- [ ] Own-account path exists and covers required permissions, no root user, supported regions, template deployment, deployment time, and stack verification
- [ ] Own-account path lists anything the event account pre-enables (model access, quotas, service-linked roles, opt-in regions)
- [ ] Own-account path has a cost warning and links to cleanup
- [ ] Optional setup variants (full vs minimal) state which later labs they require or let you skip
- [ ] Both paths end in the same state: resources, names, environment variables, and stack outputs match between `contentspec.yaml` and the own-account template *(mismatch = Critical)*
- [ ] Lab steps that differ by path are clearly branched
- [ ] Labs don't rely on event-only conveniences or own-account freedoms without saying so
- [ ] Labs that work in only one mode say so at the top
- [ ] Cleanup says what event participants can skip

## J. Security

- [ ] No passwords, tokens, API keys, or access/secret keys in content, code, templates, or screenshots
- [ ] Static lab passwords carry a callout recommending a secrets service for production
- [ ] Lab passwords use shell-safe ASCII
- [ ] No real PII; placeholders and `example.com` used
- [ ] No real AWS account IDs (use `123456789012` or a variable)
- [ ] IAM policies are least-privilege; wildcards are justified
- [ ] Credentials come from roles, environment variables, or secrets services, not inline strings
- [ ] No public exposure (open security groups, public buckets/endpoints) unless taught with a warning

## K. Content Quality & Flow

- [ ] Correct grammar and spelling
- [ ] One step-numbering style per page
- [ ] Every command/console step is preceded by what it does and why
- [ ] Every screenshot has context
- [ ] Each task ends with a validation (expected output, check command, or `success` alert)
- [ ] Official service name on first mention, consistent terminology afterward
- [ ] No contradictory instructions
- [ ] Console navigation is specific; UI elements are **bold** and match the console
- [ ] Lab flows setup → execution → validation → cleanup
- [ ] Inclusive, accessible language; no "simply/just/easy"
- [ ] Cross-references to deeper content where useful

## L. Cleanup / Teardown

- [ ] Cleanup follows the workshop's model (per-lab page, centralized page, or both) *(house)*
- [ ] Every created resource is covered, including manual and in-resource objects
- [ ] Steps are ordered by dependency
- [ ] Commands are copyable, with console alternatives where useful
- [ ] Opens with a cost warning for self-paced participants
- [ ] States what event participants can skip
- [ ] If centralized, the central page is updated and the lab links to it

## M. Workshop Studio Compatibility

- [ ] Directives render correctly (`:::code`, `::alert`, `::::expand`, `::children`)
- [ ] No raw HTML that Workshop Studio won't render (except `pre` icons)
- [ ] Weights produce the intended page order
- [ ] `contentspec.yaml` is valid if modified
- [ ] Participant IAM policy covers every action the lab performs
- [ ] Templates use magic variables (`{{.ParticipantRoleArn}}`, `{{.AssetsBucketName}}`, `{{.AssetsBucketPrefix}}`) where appropriate
- [ ] All services used are available in the configured regions
- [ ] Service quotas support the expected event size
- [ ] Templates deploy in a fresh account and delete cleanly

## N. House Consistency

- [ ] Conventions detected in Step 0 are recorded in the report
- [ ] New content matches them, or deviations are justified
- [ ] Shared pages (navigation, central cleanup, prerequisites, revision history) are updated where the new lab requires it

## O. Well-Architected Alignment

### Security
- [ ] Encryption at rest is enabled or the omission is explained
- [ ] Encryption in transit (TLS) is used
- [ ] Resources are private or authenticated unless teaching otherwise
- [ ] IAM roles / secrets service preferred over static credentials
- [ ] Audit/detection mentioned in monitoring or security labs

### Reliability
- [ ] HA option (Multi-AZ or equivalent) explained; single-AZ shortcuts have a production callout
- [ ] Backup/versioning strategy mentioned where data is stored; RPO/RTO in DR labs
- [ ] HA/DR labs include a failover test with expected behavior
- [ ] Retries with backoff and idempotency recommended in application code

### Performance Efficiency
- [ ] Resource sizing is explained, with a production sizing note
- [ ] Relevant scaling options are mentioned
- [ ] Sample code/queries avoid obvious inefficiencies

### Cost Optimization
- [ ] Smallest viable resource sizes are used
- [ ] Extra-cost features carry a cost note
- [ ] Cost warnings at start and in cleanup
- [ ] Data transfer / cross-region / idle costs noted where relevant

### Operational Excellence
- [ ] Monitoring and logging enabled or recommended
- [ ] CLI/IaC alternatives provided for console steps
- [ ] Resources are tagged
- [ ] Event notifications mentioned where relevant
- [ ] Custom configuration preferred over modifying defaults

### Sustainability
- [ ] Right-sizing reinforced; idle resources removed
- [ ] Efficient options (e.g., AWS Graviton) mentioned where applicable
- [ ] Efficient code/queries promoted

## P. Domain Modules

Apply each module that matches what the lab teaches. Mark others N/A.

### Databases (relational, NoSQL, caching)
- [ ] Connection details come from environment variables or a secrets service
- [ ] TLS is used for client connections (e.g., `sslmode=require`)
- [ ] Connection pooling or a proxy is mentioned for application workloads
- [ ] Custom parameter/configuration groups are used rather than defaults
- [ ] Backups, snapshots, and point-in-time recovery are covered where relevant
- [ ] Read scaling (replicas) explains use cases and promotion for DR
- [ ] Cleanup drops in-database objects (users, extensions, tables) in dependency order
- [ ] Sample data is synthetic

### Serverless (Lambda, API Gateway, Step Functions, EventBridge)
- [ ] Function execution roles are least-privilege
- [ ] Timeout, memory, and concurrency settings are explained
- [ ] APIs have authentication/authorization or a warning if open
- [ ] Error handling, retries, and dead-letter queues are covered
- [ ] Log groups are cleaned up or have retention set

### Containers (ECS, EKS, App Runner)
- [ ] Images come from trusted or private registries with pinned tags (not `latest`)
- [ ] Containers don't run as root unless explained
- [ ] Task/pod roles are least-privilege; no node-level credentials in containers
- [ ] Resource requests/limits are set
- [ ] Load balancers, target groups, and ECR images are cleaned up
- [ ] `kubectl`/`eksctl`/CLI versions are stated

### Compute & Networking (EC2, VPC, ELB)
- [ ] Access uses SSM Session Manager or a browser IDE rather than open SSH
- [ ] Security groups allow only required ports and sources
- [ ] AMIs are current and referenced by SSM parameter where possible
- [ ] NAT gateways, Elastic IPs, and endpoints are in cleanup (common hidden costs)

### Analytics & Data (S3, Glue, Athena, EMR, Kinesis, Redshift)
- [ ] Buckets block public access and use encryption
- [ ] Sample datasets are licensed for use and contain no real PII
- [ ] Query costs (data scanned) are noted; partitioning or columnar formats mentioned
- [ ] Buckets are emptied before deletion in cleanup

### AI/ML & Generative AI (Bedrock, SageMaker)
- [ ] Required model access, regions, and quotas are listed in prerequisites
- [ ] Model IDs/versions are pinned and currently available
- [ ] Expected outputs note that model responses vary
- [ ] Guardrails, prompt-injection, and data-handling considerations are mentioned
- [ ] Endpoints, notebooks, and GPU instances are in cleanup with a cost warning
- [ ] Token/inference costs are noted

### Security & Identity (IAM, KMS, Cognito, GuardDuty)
- [ ] Any intentionally insecure configuration is clearly labeled and reverted in cleanup
- [ ] KMS keys scheduled for deletion are explained (waiting period)
- [ ] Test users and credentials are removed in cleanup

### Developer Tooling & AI Assistants (IDEs, CI/CD, coding agents)
- [ ] Tool and extension versions are stated
- [ ] Generated code or AI output is reviewed in the lab, not trusted blindly
- [ ] No personal tokens or credentials committed to repos or shown in screenshots
- [ ] Pipelines and repositories are cleaned up

---

## Review Report Template

Write a **`Review.md`** file in the root of the reviewed content directory (or the working directory). Use this format:

```markdown
# Workshop Content Review

## Review Summary

| Field | Value |
|-------|-------|
| **Lab** | [Lab name] |
| **Workshop** | [Workshop name / repository] |
| **Domain(s)** | [e.g., Databases, Serverless, AI/ML] |
| **Delivery Mode(s)** | [AWS event / Own account / Both] |
| **Files Reviewed** | [Count and/or list] |
| **Reviewer** | [Name] |
| **Date** | [Date] |
| **Overall Status** | PASS / PASS WITH ISSUES / FAIL |

## House Conventions (Step 0)

| Convention | Detected Pattern |
|------------|------------------|
| Page file name | |
| Folder naming | |
| Weight scheme | |
| Front matter extras | |
| Code block style | |
| Prerequisites format | |
| Cleanup model | |
| Environment variables | |

## Checklist Results

| Category | Status | Notes |
|----------|--------|-------|
| A. File & Directory Structure | PASS / FAIL / N/A | |
| B. Front Matter | PASS / FAIL / N/A | |
| C. Code Blocks & Commands | PASS / FAIL / N/A | |
| D. Alerts & Callouts | PASS / FAIL / N/A | |
| E. Expandable Sections | PASS / FAIL / N/A | |
| F. Children Directive | PASS / FAIL / N/A | |
| G. Images | PASS / FAIL / N/A | |
| H. Links | PASS / FAIL / N/A | |
| I. Prerequisites | PASS / FAIL / N/A | |
| I2. Delivery Modes | PASS / FAIL / N/A | |
| J. Security | PASS / FAIL / N/A | |
| K. Content Quality & Flow | PASS / FAIL / N/A | |
| L. Cleanup / Teardown | PASS / FAIL / N/A | |
| M. Workshop Studio Compatibility | PASS / FAIL / N/A | |
| N. House Consistency | PASS / FAIL / N/A | |
| O. Well-Architected: Security | PASS / FAIL / N/A | |
| O. Well-Architected: Reliability | PASS / FAIL / N/A | |
| O. Well-Architected: Performance | PASS / FAIL / N/A | |
| O. Well-Architected: Cost | PASS / FAIL / N/A | |
| O. Well-Architected: Operational Excellence | PASS / FAIL / N/A | |
| O. Well-Architected: Sustainability | PASS / FAIL / N/A | |
| P. Domain Module(s): [name] | PASS / FAIL / N/A | |

## Critical Issues (must fix before merge)

1. [Category] — [File path:line or heading] — [Issue] — [Suggested fix]

## Warnings (should fix)

1. [Category] — [File path:line or heading] — [Issue] — [Suggested fix]

## Recommendations (nice to have)

1. [Category] — [Description] — [Suggestion]

## Files to Remove

- [Stale/unused files]

## Consistency Notes

- [Deviations from the house conventions above]
```

Overall status rules:
- **FAIL** — one or more Critical issues.
- **PASS WITH ISSUES** — no Critical issues, one or more Warnings.
- **PASS** — Recommendations only, or nothing.
