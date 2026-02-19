---
inclusion: always
---

# Atlassian Admin Best Practices

## Jira

- Always search for existing issues before creating new ones to avoid duplicates.
- Use JQL (Jira Query Language) for precise issue searches; prefer structured queries over free-text.
- When creating issues, always set a meaningful summary, issue type, and project key.
- Assign issues to the appropriate team member when known.
- Use epics to group related stories and tasks; link issues to their parent epic.
- Prefer updating issue status via transitions rather than direct field edits.
- Include acceptance criteria in issue descriptions for stories and tasks.
- Use labels and components consistently to support filtering and reporting.
- When adding comments, be concise and actionable; mention assignees with `@user` when action is needed.
- Always verify the project key exists before creating or querying issues.

## Confluence

- Search for existing pages before creating new ones to prevent duplication.
- Use the correct space key when creating or retrieving pages.
- Structure pages with clear headings and a consistent layout matching the space's conventions.
- Prefer updating existing pages over creating duplicates when content overlaps.
- Use page labels to improve discoverability within a space.
- When creating technical documentation, include code blocks with appropriate language tags.
- Attach related files or images to pages rather than embedding external links where possible.
- Always set a descriptive page title that reflects the content.

## General

- Authenticate using OAuth 2.0 (3LO) via the Atlassian Remote MCP server; never hardcode credentials.
- Respect user permissions—only perform actions the authenticated user is authorized to do.
- Use pagination when listing large sets of issues or pages to avoid timeouts.
- Prefer bulk operations when creating or updating multiple items.
