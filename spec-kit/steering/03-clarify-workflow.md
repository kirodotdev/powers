---
inclusion: auto
globs: ["**/*.md"]
description: "Clarify workflow - eliminates ambiguity through targeted questioning"
keywords: ["clarify", "clarification", "ambiguity", "question", "澄清", "歧义", "问题"]
---

# Clarify Workflow

This workflow identifies and resolves ambiguities in feature specifications through targeted questioning.

## Purpose

Detect and reduce ambiguity or missing decision points in the specification before planning, reducing downstream rework risk.

## When to Use

- Specification has `[NEEDS CLARIFICATION]` markers
- Specification seems incomplete or vague
- Before starting the Plan workflow
- After stakeholder review reveals gaps

## Prerequisites

- Feature specification exists (`requirements.md`)
- Should run BEFORE the Plan workflow

## Execution Flow

### Step 1: Load and Analyze Specification

Read the specification and perform a structured ambiguity scan using this taxonomy:

**Functional Scope & Behavior**:
- Core user goals & success criteria
- Explicit out-of-scope declarations
- User roles / personas differentiation

**Domain & Data Model**:
- Entities, attributes, relationships
- Identity & uniqueness rules
- Lifecycle/state transitions
- Data volume / scale assumptions

**Interaction & UX Flow**:
- Critical user journeys / sequences
- Error/empty/loading states
- Accessibility or localization notes

**Non-Functional Quality Attributes**:
- Performance (latency, throughput targets)
- Scalability (horizontal/vertical, limits)
- Reliability & availability (uptime, recovery)
- Observability (logging, metrics, tracing)
- Security & privacy (authN/Z, data protection)
- Compliance / regulatory constraints

**Integration & External Dependencies**:
- External services/APIs and failure modes
- Data import/export formats
- Protocol/versioning assumptions

**Edge Cases & Failure Handling**:
- Negative scenarios
- Rate limiting / throttling
- Conflict resolution (concurrent edits)

**Terminology & Consistency**:
- Canonical glossary terms
- Avoided synonyms / deprecated terms

### Step 2: Generate Prioritized Questions

Create a prioritized queue of clarification questions (maximum 5):

**Question Constraints**:
- Must be answerable with:
  - Multiple-choice (2-5 distinct options), OR
  - Short phrase (<=5 words)
- Must materially impact architecture, data modeling, task decomposition, test design, UX behavior, or compliance
- Category coverage balance: highest impact first
- Exclude already-answered or trivial questions

### Step 3: Sequential Questioning

Present EXACTLY ONE question at a time.

**For multiple-choice questions**:

```markdown
**推荐:** 选项 [X] - [推荐理由]

**可选答案:**

► **A** - [选项 A 描述]

► **B** - [选项 B 描述]

► **C** - [选项 C 描述]

► **其他** - 提供您自己的答案（≤5 个词）

---
回复选项字母（如 "A"），或输入 "yes" 接受推荐，或直接输入您的答案。
```

**Example (示例)**:

```markdown
**问题:** 系统应如何限制团队并发执行数量？

**推荐:** 选项 C - 动态调整更灵活，能适应不同负载场景

**可选答案:**

► **A** - 不限制，允许所有团队同时执行

► **B** - 限制最多 5 个团队同时执行

► **C** - 根据系统资源动态调整并发数

► **其他** - 提供您自己的答案（≤5 个词）

---
回复选项字母，或输入 "yes" 接受推荐，或直接输入您的答案。
```

**For short-answer questions**:

```markdown
**建议答案:** [您的建议] - [简要理由]

请输入简短答案（≤5 个词）。
输入 "yes" 接受建议，或直接输入您的答案。
```

### Step 4: Record Answers (MANDATORY - DO NOT SKIP)

**CRITICAL**: You MUST create and maintain a clarification log file. This is NON-NEGOTIABLE.

#### 4.1 Create Clarification Log File (REQUIRED)

Use `templates/clarifications-template.md` as reference.

**IMMEDIATELY after the FIRST question is answered**, create the clarification log file:

```
.kiro/specs/[###-feature-name]/clarifications.md
```

**File Format (MUST follow exactly)**:

```markdown
# Clarification Log: [FEATURE NAME]

**Feature**: [###-feature-name]
**Session Date**: YYYY-MM-DD
**Total Questions**: [N]

---

## Q1: [Question Title]

**Category**: [Functional Scope / Domain & Data / Interaction & UX / Non-Functional / Integration / Edge Cases / Terminology]

**Question**: [Complete question text]

**Options Presented**:
- **A**: [Option A description]
- **B**: [Option B description]
- **C**: [Option C description]
- **Other**: Custom answer allowed

**Recommended**: [Option X] - [Reason for recommendation]

**User's Choice**: [Option letter or custom answer]

**Resolution**: [How this was applied to the spec]

---

## Q2: [Question Title]

[Same format as above]

---

## Summary

| # | Question | Category | Choice | Applied To |
|---|----------|----------|--------|------------|
| 1 | [Brief question] | [Category] | [Choice] | [Section in spec] |
| 2 | [Brief question] | [Category] | [Choice] | [Section in spec] |

---

## Impact on Specification

- **Sections Modified**: [List of modified sections]
- **New Requirements Added**: [List if any]
- **Requirements Changed**: [List if any]
```

#### 4.2 Update Clarification Log After EACH Answer

**After EACH question is answered, you MUST**:

1. **Append the Q&A record** to `clarifications.md` immediately
2. **Update the Summary table** with the new entry
3. **Save the file** before asking the next question

#### 4.3 Apply Clarification to Specification

After recording in `clarifications.md`:

1. Apply clarification to appropriate section in `requirements.md`:
   - Functional ambiguity -> Functional Requirements
   - User interaction -> User Stories
   - Data shape -> Key Entities / Data Model
   - Non-functional -> Quality Attributes section
   - Edge case -> Edge Cases section

2. If clarification invalidates earlier statement, replace it (no contradictions)

3. Add reference in `requirements.md` Clarifications section:
   ```markdown
   ## Clarifications

   See [clarifications.md](./clarifications.md) for full clarification log.

   ### Session YYYY-MM-DD
   - Q1: [brief question] -> A: [answer]
   - Q2: [brief question] -> A: [answer]
   ```

4. Save both files after each integration

### Step 5: Stop Conditions

Stop asking questions when:
- All critical ambiguities resolved
- User signals completion ("done", "good", "no more")
- Reached 5 asked questions

### Step 6: Validation

After each write:
- Clarifications section has one bullet per answer
- Total questions <= 5
- No lingering vague placeholders
- No contradictory statements
- Markdown structure valid
- Terminology consistent

### Step 7: Report Completion (MUST include file paths)

**BEFORE reporting completion**, verify:
1. `clarifications.md` has been created and saved
2. `requirements.md` has been updated
3. All questions and answers are recorded

Output completion report:

```markdown
## Clarification Complete

### Files Generated/Updated

| File | Path | Status |
|------|------|--------|
| Clarification Log | `.kiro/specs/[###-feature-name]/clarifications.md` | CREATED |
| Requirements | `.kiro/specs/[###-feature-name]/requirements.md` | UPDATED |

### Session Summary

**Questions asked**: [N]
**Session date**: YYYY-MM-DD

### Questions & Answers

| # | Question | User's Choice |
|---|----------|---------------|
| 1 | [Brief question] | [Choice] |
| 2 | [Brief question] | [Choice] |

### Coverage Summary

| Category | Status |
|----------|--------|
| Functional Scope | Resolved / Clear / Deferred |
| Domain & Data | Resolved / Clear / Deferred |
| Interaction & UX | Resolved / Clear / Deferred |
| Non-Functional | Resolved / Clear / Deferred |
| Integration | Resolved / Clear / Deferred |
| Edge Cases | Resolved / Clear / Deferred |
| Terminology | Resolved / Clear / Deferred |

**Status Legend**:
- Resolved: Was ambiguous, now clarified
- Clear: Already sufficient
- Deferred: Exceeds question quota or better for planning phase

### Recommendation

[Recommend proceeding to Plan or running Clarify again]
```

**IMPORTANT**: If `clarifications.md` was not created, DO NOT report completion. Go back and create the file first.

## Behavior Rules

- If no meaningful ambiguities found: "No critical ambiguities detected. Suggest proceeding to Plan."
- If spec file missing: "Please run Specify first."
- Never exceed 5 total questions
- Avoid speculative tech stack questions unless blocking functional clarity
- Respect user early termination signals

## Output (MANDATORY FILES)

After completing this workflow, you MUST have created/updated:

1. **`clarifications.md`** (REQUIRED - New File)
   - Location: `.kiro/specs/[###-feature-name]/clarifications.md`
   - Contains: Complete Q&A log with all options, recommendations, and user choices
   - Format: As specified in Step 4.1

2. **`requirements.md`** (REQUIRED - Updated)
   - Clarifications applied to relevant sections
   - Reference to `clarifications.md` in Clarifications section
   - No contradictory statements

**VALIDATION CHECKLIST** (verify before reporting completion):
- [ ] `clarifications.md` file exists
- [ ] All questions recorded with complete details
- [ ] All user choices documented
- [ ] Summary table is complete
- [ ] `requirements.md` updated with applied clarifications
- [ ] `requirements.md` references `clarifications.md`

## Next Steps

Suggest to the user:
```
Clarification complete.

Next, you can:
1. Run **Plan** to create technical implementation plan
2. Run **Clarify** again if deferred items need resolution
3. Review updated spec before proceeding
```
