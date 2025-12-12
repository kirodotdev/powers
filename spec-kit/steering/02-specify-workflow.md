---
inclusion: auto
globs: ["**/*.md"]
description: "Specify workflow - transforms feature descriptions into structured specifications"
keywords: ["specify", "specification", "spec", "requirements", "feature", "PRD", "需求", "规格", "功能规格"]
---

# Specify Workflow

This workflow transforms a feature description into a structured, executable specification.

## Purpose

Create specifications that are:
- **Complete**: All necessary requirements captured
- **Unambiguous**: Only one interpretation possible
- **Testable**: Every requirement has acceptance criteria
- **Technology-agnostic**: Focus on WHAT, not HOW

## When to Use

- Starting a new feature
- Documenting an existing feature idea
- Converting informal requirements to formal specs

## Quick Guidelines

- Focus on **WHAT** users need and **WHY**
- Avoid **HOW** to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers
- Mark unclear items with `[NEEDS CLARIFICATION: specific question]`
- Maximum 3 clarification markers

## Execution Flow

### Step 1: Gather Feature Description

Ask the user for their feature description. Example prompt:
```
Please describe the feature you want to specify.

Include:
- What problem it solves
- Who the users are
- Key capabilities needed
```

### Step 2: Generate Feature Branch Name

Create a concise short name (2-4 words) for the feature:
- Use action-noun format: "user-auth", "payment-flow"
- Preserve technical terms: OAuth2, API, JWT
- Keep concise but descriptive

Determine the next feature number by checking existing specs directories.

### Step 3: Create Feature Structure

Create the feature directory and spec file:
```
.kiro/specs/[###-feature-name]/
└── requirements.md
```

### Step 4: Create Specification Content

Generate the spec using `templates/requirements-template.md` as reference.

Key template structure:

```markdown
# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft

## User Scenarios & Testing

### User Story 1 - [Title] (Priority: P1)

[Description in plain language]

**Why this priority**: [Value explanation]

**Independent Test**: [How to test this story alone]

**Acceptance Scenarios**:
1. **Given** [state], **When** [action], **Then** [outcome]
2. **Given** [state], **When** [action], **Then** [outcome]

---

### User Story 2 - [Title] (Priority: P2)
...

### Edge Cases

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements

### Functional Requirements

- **FR-001**: System MUST [capability]
- **FR-002**: System MUST [capability]
- **FR-003**: Users MUST be able to [interaction]

### Key Entities (if data involved)

- **[Entity 1]**: [What it represents, key attributes]
- **[Entity 2]**: [Relationships to other entities]

## Success Criteria

### Measurable Outcomes

- **SC-001**: [Measurable metric]
- **SC-002**: [Measurable metric]
```

### Step 4: Handle Ambiguities

When information is unclear:

1. **Make informed guesses** based on context and industry standards
2. **Document assumptions** in an Assumptions section
3. **Limit clarifications** to maximum 3 `[NEEDS CLARIFICATION]` markers
4. **Prioritize**: scope > security/privacy > user experience > technical details

**Examples of reasonable defaults** (don't ask about these):
- Data retention: Industry-standard practices
- Performance targets: Standard web/mobile expectations
- Error handling: User-friendly messages with fallbacks
- Authentication: Standard session-based or OAuth2

### Step 5: Validate Specification

Run quality validation:

**Content Quality**:
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

**Requirement Completeness**:
- [ ] No [NEEDS CLARIFICATION] markers remain (or max 3)
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic
- [ ] All acceptance scenarios are defined
- [ ] Edge cases are identified

**Feature Readiness**:
- [ ] All functional requirements have acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] Scope is clearly bounded

### Step 6: Handle Clarification Markers

If clarification markers remain, present questions to user:

```markdown
## 问题 1: [主题]

**背景**: [引用相关规格内容]

**需要明确**: [具体问题]

**可选答案:**

► **A** - [第一个答案]
  _影响: [选择这个意味着什么]_

► **B** - [第二个答案]
  _影响: [选择这个意味着什么]_

► **C** - [第三个答案]
  _影响: [选择这个意味着什么]_

► **其他** - 提供您自己的答案

---
**您的选择**: _[等待回复]_
```

**Example (示例)**:

```markdown
## 问题 1: 用户认证方式

**背景**: 规格中提到"用户需要登录系统"

**需要明确**: 应该使用哪种认证方式？

**可选答案:**

► **A** - 邮箱 + 密码
  _影响: 实现简单，但需要处理密码重置流程_

► **B** - OAuth2 (Google/GitHub)
  _影响: 用户体验更好，但依赖第三方服务_

► **C** - 两者都支持
  _影响: 覆盖更多用户，但实现复杂度增加_

► **其他** - 提供您自己的答案

---
**您的选择**: _[等待回复]_
```

### Step 7: Finalize

Write the specification to the feature directory:
```
.kiro/specs/[###-feature-name]/requirements.md
```

## Success Criteria Guidelines

Success criteria must be:
1. **Measurable**: Include specific metrics (time, percentage, count)
2. **Technology-agnostic**: No frameworks, languages, databases
3. **User-focused**: Describe outcomes from user perspective
4. **Verifiable**: Can be tested without knowing implementation

**Good examples**:
- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"

**Bad examples** (implementation-focused):
- "API response time under 200ms" (too technical)
- "Database handles 1000 TPS" (implementation detail)
- "React components render efficiently" (framework-specific)

## Output

After completing this workflow:
- Specification at `.kiro/specs/[###-feature-name]/requirements.md`
- Quality checklist at `.kiro/specs/[###-feature-name]/checklists/requirements.md`
- Feature branch created

## Next Steps

Suggest to the user:
```
Specification created at .kiro/specs/[###-feature-name]/requirements.md

Next, you can:
1. Run **Clarify** if [N] clarification markers remain
2. Run **Plan** to create technical implementation plan
3. Run **Checklist** to create additional quality checklists
```
