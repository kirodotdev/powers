# Aurora & RDS PostgreSQL Workshop Content Review Checklist

Use this checklist to systematically review any new lab content before it is merged into the aurora-pg-lab or rdspg repository. For each item, mark PASS, FAIL, or N/A and note specific issues found.

---

## A. File & Directory Structure

- [ ] Content files are organized as `content/<Category>/<LabName>/[sub-pages]/index.en.md` (or `index.md`)
- [ ] Static images are under `static/<category>/<lab-folder>/` mirroring the content structure
- [ ] No stale files with "OLD", "USELESS", or duplicate suffixes exist in the deliverable
- [ ] No OS artifacts present (`.DS_Store`, `__MACOSX/`, `Thumbs.db`, `.bak`, `.tmp`, `.new`)
- [ ] No files with spaces in names that are referenced from markdown (use hyphens/underscores)
- [ ] Category folders use numbered prefixes for ordering (e.g., `1-Prerequisites`, `2-Foundation`)
- [ ] Task sub-folders use sequential naming (e.g., `task1/`, `task2/`, `task3/`)
- [ ] A `.gitkeep` is acceptable in otherwise-empty directories but should not appear alongside real content

## B. Front Matter

- [ ] Every `index.en.md` / `index.md` has YAML front matter with `title` and `weight`
- [ ] `title` is a human-readable string (may include emoji for category pages)
- [ ] `weight` follows the established numbering convention for the target workshop
- [ ] Category/lab index pages include `chapter: true` where appropriate
- [ ] `pre` field uses valid HTML/icon syntax if present (e.g., `<b>1. </b>` or `<i class="fas fa-landmark"></i>`)
- [ ] No unknown or unsupported front matter keys are used (valid: `title`, `weight`, `date`, `chapter`, `pre`)

## C. Code Blocks & Commands

- [ ] Participant-facing commands use either `:::code{showCopyAction=true showLineNumbers=false language=<lang>}` or standard fenced blocks with language specified
- [ ] Every code block specifies a `language` attribute (`sql`, `bash`, `sh`, `sh-session`, `json`, `python`, etc.)
- [ ] `showCopyAction=true` is present on `:::code` blocks participants need to copy
- [ ] Standard markdown fenced blocks (` ``` `) are used consistently for non-copyable output, expandable sections, or CLI commands
- [ ] No code block is missing its closing `:::` or ` ``` `
- [ ] Commands that require user-specific values use environment variables (`$PGHOST`, `$DBENDP`, `$DBPASS`, `$DBUSER`, `$AWSREGION`) or clearly mark placeholders with `[brackets]`
- [ ] Multi-line CLI commands use backslash continuation (`\`) for readability
- [ ] Code block style is consistent within each lab (don't mix `:::code` and fenced blocks arbitrarily)

## D. Alerts & Callouts

- [ ] Inline alerts use `::alert[text]{type="..."}` (two colons, single line)
- [ ] Block alerts use `:::alert{header="..." type="..."}` with `:::` closing (three colons, multi-line)
- [ ] No mixed syntax (e.g., `::alert` with block content or `:::alert` for single-line)
- [ ] Alert types are valid: `warning` or `info`
- [ ] Security-sensitive steps have appropriate warning callouts
- [ ] Lab index pages include a prerequisite alert/warning at the top
- [ ] Cost warnings are present for labs that create billable resources

## E. Expandable Sections

- [ ] Expandable sections use `::::expand{header="..."}` with `::::` closing (four colons)
- [ ] Header text is descriptive (e.g., "Code", "CLI Alternative", "Detailed Output")
- [ ] Content within expand sections is properly formatted (code blocks, etc.)
- [ ] Expand sections are used appropriately for optional/supplementary content

## F. Children Directive

- [ ] Category index pages use `::children` to auto-list sub-pages
- [ ] Lab index pages with multiple tasks use `::children` after a "This lab contains following tasks:" heading
- [ ] The `::children` directive is not used on leaf/task pages

## G. Image References

- [ ] All image paths use `/static/<path>/filename.png` format matching content structure
- [ ] Every referenced image file actually exists in the static folder
- [ ] Alt text is descriptive of the actual image content (not generic like "APN Logo" or "screenshot")
- [ ] No unreferenced images remain in the static folder (clean up unused assets)
- [ ] Image filenames use hyphens or underscores, not spaces
- [ ] Screenshots appear after the command/step that produces them, not before

## H. Internal Links

- [ ] All internal links use absolute paths from content root (e.g., `/1-prerequisites/`, `/2-foundation/lab1-create/`)
- [ ] No `localhost` URLs appear in the content
- [ ] No broken internal links (verify target pages exist)
- [ ] Links to prerequisite pages match the standard format for the target workshop
- [ ] External AWS console links use region-agnostic URLs where possible
- [ ] Links to other workshops use `catalog.workshops.aws` domain

## I. Prerequisites Section

### For rdspg:
- [ ] Lab index page includes an inline alert referencing Prerequisites and the first foundation lab
- [ ] Additional prerequisite labs are listed if the lab depends on them
- [ ] Alert uses `type="warning"` for prerequisite notices

### For aurora-pg-lab:
- [ ] The lab index page includes a Prerequisites section with bulleted list
- [ ] Prerequisites reference the standard three items: All Lab Prerequisites, Creating a New Aurora Cluster, Configure VSCode
- [ ] Mandatory/Optional/Skip guidance is included for each prerequisite
- [ ] Links in prerequisites are correct and match existing paths

## J. Security

- [ ] No real PII in sample data (names, emails, phone numbers, addresses must be placeholders)
- [ ] If passwords are hardcoded for lab simplicity, a warning callout is present recommending Secrets Manager for production
- [ ] Passwords use only simple ASCII characters (no `£`, `{`, `|`, or other encoding-problematic characters)
- [ ] Environment variables are used for connection details where the workshop infrastructure provides them
- [ ] No AWS account IDs, access keys, or secret keys appear in the content
- [ ] Connection strings do not embed real credentials when environment variables are available
- [ ] IAM roles and policies follow least-privilege principles in examples
- [ ] Region references use `$AWSREGION` variable rather than hardcoded region names where applicable

## K. Content Quality & Flow

- [ ] Correct grammar and spelling throughout (check for common typos: "preformed" vs "performed", "dipictions" vs "depictions", "secton" vs "section")
- [ ] Consistent step numbering within each page (either 1.1/1.2 or ### Step 1/### Step 2, not mixed)
- [ ] Every command block is preceded by a brief explanation of what it does and why
- [ ] Every screenshot is accompanied by context explaining what the participant should observe
- [ ] Output images appear after the command that produces them, not before
- [ ] No contradictory instructions (e.g., "replace the password" when the password is already in the command)
- [ ] Technical terms are used consistently (e.g., always "RDS PostgreSQL" or "Amazon RDS for PostgreSQL", not mixing without definition)
- [ ] The lab flows logically from setup through execution to validation
- [ ] Console navigation instructions include the specific path (e.g., "from the services dropdown or search bar")
- [ ] Cross-references to related workshops or deep-dive content are included where appropriate

## L. Cleanup / Teardown

- [ ] The lab includes a cleanup section or references the main cleanup page
- [ ] Cleanup instructions cover all resources created during the lab (databases, users, extensions, parameter group changes, CloudFormation stacks, Lambda functions)
- [ ] Cleanup commands are provided as copyable code blocks
- [ ] The order of cleanup steps is correct (e.g., drop dependent objects before parent objects)
- [ ] For rdspg: cleanup is referenced in the centralized `/7-Lab-cleanup/` page
- [ ] For aurora-pg-lab: cleanup is included as the final sub-page of the lab

## M. Workshop Studio Compatibility

- [ ] Content renders correctly with Hugo/Workshop Studio directives (`:::code`, `::alert`, `::::expand`, `::children`)
- [ ] No raw HTML that might not render in Workshop Studio (except `pre` field icons)
- [ ] The `::children` directive is used on category index pages that should auto-list sub-pages
- [ ] Weight values produce the correct page ordering when rendered
- [ ] `contentspec.yaml` is valid if modified (version 2.0, correct structure)
- [ ] CloudFormation parameters use Workshop Studio magic variables where appropriate (`{{.ParticipantRoleArn}}`, `{{.AssetsBucketName}}`, `{{.AssetsBucketPrefix}}`)

## N. Workshop-Specific Patterns

### rdspg-specific:
- [ ] Lab index pages use emoji in titles (🗃️, 🏛️, 📊, 📼, 🧹, ⚗️)
- [ ] `pre` field is used for navigation numbering or icons
- [ ] `chapter: true` is set on both category and lab index pages
- [ ] Independent lab notice is included on category pages: "there are no inter-dependencies between labs"
- [ ] Logo image (`/static/Amazon-RDS_light-bg@4x.png`) is used on category pages

### aurora-pg-lab-specific:
- [ ] `:::code` directive is the primary code block format
- [ ] Prerequisites use the full bulleted list format with Mandatory/Optional guidance
- [ ] Per-lab cleanup sections are included

## O. AWS Well-Architected Framework Alignment

### Security
- [ ] Database creation steps mention or enable storage encryption (KMS)
- [ ] Connection examples include SSL/TLS (`sslmode=require` or equivalent) or explain why not
- [ ] Databases are created in private subnets; not publicly accessible unless explicitly teaching that concept with a warning
- [ ] Secrets Manager or IAM authentication is recommended over static passwords
- [ ] IAM policies avoid `*` resource wildcards unless justified
- [ ] Monitoring/auditing labs mention CloudTrail, event subscriptions, or audit logging

### Performance Efficiency
- [ ] Instance class choice is explained (e.g., "using db.t3.medium for lab cost efficiency")
- [ ] A note exists that production workloads should be sized based on actual requirements
- [ ] Read replica labs explain appropriate use cases (read-heavy, reporting, geo-distribution)
- [ ] Connection pooling (RDS Proxy, PgBouncer) is mentioned for labs involving application connections
- [ ] SQL examples avoid obviously inefficient patterns without explanation
- [ ] Storage type selection is mentioned or explained when creating instances

### Reliability / High Availability
- [ ] Multi-AZ is explained; if Single-AZ is used, a callout recommends Multi-AZ for production
- [ ] Backup labs mention automated backups, retention period, and PITR
- [ ] HA labs include failover testing steps with expected behavior documented
- [ ] Read replica promotion is explained as a DR strategy where applicable
- [ ] RTO/RPO concepts are mentioned when teaching backup/restore
- [ ] Retry logic or connection failover handling is demonstrated or recommended

### Cost Optimization
- [ ] Labs use the smallest instance class that meets lab needs
- [ ] Cost warnings appear at both start and end of labs creating billable resources
- [ ] Features with additional cost (Enhanced Monitoring, RDS Proxy, Multi-AZ) include cost notes
- [ ] Storage allocations are minimal (e.g., 20 GB)
- [ ] Cross-region labs mention data transfer costs
- [ ] Cleanup instructions are thorough and prominent

### Operational Excellence
- [ ] Monitoring is recommended (Enhanced Monitoring, Performance Insights, or Database Insights)
- [ ] Log exports to CloudWatch are enabled and referenced
- [ ] CLI/IaC alternatives are provided (even in expandable sections) for console steps
- [ ] Resources include tags (at minimum a `Name` tag)
- [ ] RDS Event Subscriptions are mentioned for operational awareness
- [ ] Custom parameter groups are used rather than defaults

### Sustainability
- [ ] Right-sizing is reinforced (no over-provisioned instances without explanation)
- [ ] Graviton instance types are mentioned as an energy-efficient option where applicable
- [ ] Efficient SQL patterns are promoted
- [ ] Cleanup of unused resources is emphasized

---

## Review Report Template

When completing a review, generate a **`Review.md`** file as the output artifact. Place it in the root of the reviewed content directory (or the working directory). Use this format:

```markdown
# Workshop Content Review

## Review Summary

| Field | Value |
|-------|-------|
| **Lab** | [Lab name] |
| **Target Workshop** | [aurora-pg-lab / rdspg] |
| **Reviewer** | [Name] |
| **Date** | [Date] |
| **Overall Status** | PASS / PASS WITH ISSUES / FAIL |

## Checklist Results

| Category | Status | Notes |
|----------|--------|-------|
| A. File & Directory Structure | PASS / FAIL / N/A | |
| B. Front Matter | PASS / FAIL / N/A | |
| C. Code Blocks & Commands | PASS / FAIL / N/A | |
| D. Alerts & Callouts | PASS / FAIL / N/A | |
| E. Expandable Sections | PASS / FAIL / N/A | |
| F. Children Directive | PASS / FAIL / N/A | |
| G. Image References | PASS / FAIL / N/A | |
| H. Internal Links | PASS / FAIL / N/A | |
| I. Prerequisites Section | PASS / FAIL / N/A | |
| J. Security | PASS / FAIL / N/A | |
| K. Content Quality & Flow | PASS / FAIL / N/A | |
| L. Cleanup / Teardown | PASS / FAIL / N/A | |
| M. Workshop Studio Compatibility | PASS / FAIL / N/A | |
| N. Workshop-Specific Patterns | PASS / FAIL / N/A | |
| O. Well-Architected: Security | PASS / FAIL / N/A | |
| O. Well-Architected: Performance | PASS / FAIL / N/A | |
| O. Well-Architected: Reliability | PASS / FAIL / N/A | |
| O. Well-Architected: Cost | PASS / FAIL / N/A | |
| O. Well-Architected: Operational Excellence | PASS / FAIL / N/A | |
| O. Well-Architected: Sustainability | PASS / FAIL / N/A | |

## Critical Issues (must fix before merge)

1. [Category] — [File path] — [Description of issue] — [Suggested fix]

## Warnings (should fix)

1. [Category] — [File path] — [Description of issue] — [Suggested fix]

## Recommendations (nice to have)

1. [Category] — [Description] — [Suggestion]

## Files to Remove

- [List of stale/unused files that should be deleted]

## Consistency Notes

- [Any patterns that differ from the established workshop conventions]
```
