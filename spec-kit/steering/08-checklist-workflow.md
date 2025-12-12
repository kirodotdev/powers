---
inclusion: auto
globs: ["**/*.md"]
description: "Checklist workflow - generates quality validation checklists"
keywords: ["checklist", "quality", "validation", "gate", "检查清单", "质量", "门禁"]
---

# Checklist Workflow

This workflow generates domain-specific quality checklists for requirement validation.

## Purpose

Create checklists that are **"Unit Tests for Requirements"** - validating the quality of requirements themselves, NOT testing implementation.

## Core Concept

**CRITICAL**: Checklists validate REQUIREMENTS QUALITY, not implementation behavior.

**NOT for verification**:
- "Verify the button clicks correctly"
- "Test error handling works"
- "Confirm the API returns 200"

**FOR requirements quality**:
- "Are visual hierarchy requirements defined for all card types?"
- "Is 'prominent display' quantified with specific sizing?"
- "Are accessibility requirements specified for keyboard navigation?"

## When to Use

- After Specify, to validate spec quality
- Before Plan, to ensure spec is ready
- Before Implementation, as quality gates
- For specific domain validation (UX, security, API)

## Prerequisites

- Feature specification exists (`requirements.md`)
- Optional: `design.md`, `tasks.md` for additional context

## Execution Flow

### Step 1: Clarify Intent

Ask up to THREE contextual questions to understand:

**Generation Algorithm**:
1. Extract signals from user request: domain keywords (auth, UX, API), risk indicators, stakeholder hints
2. Cluster signals into candidate focus areas (max 4)
3. Identify audience & timing (author, reviewer, QA)
4. Detect missing dimensions: scope, depth, risk emphasis
5. Formulate questions from these archetypes:
   - Scope refinement
   - Risk prioritization
   - Depth calibration
   - Audience framing
   - Boundary exclusion

**Question Formatting**:
```markdown
Q1: [Question]

| Option | Candidate | Why It Matters |
|--------|-----------|----------------|
| A | [Option A] | [Impact] |
| B | [Option B] | [Impact] |
| C | [Option C] | [Impact] |
```

**Defaults** (if interaction impossible):
- Depth: Standard
- Audience: Reviewer (PR) if code-related
- Focus: Top 2 relevance clusters

### Step 2: Load Feature Context

Read from feature directory:
- `requirements.md`: Requirements and scope
- `design.md` (if exists): Technical details
- `tasks.md` (if exists): Implementation tasks

**Context Loading Strategy**:
- Load only portions relevant to focus areas
- Summarize long sections
- Progressive disclosure: add retrieval only if gaps detected

### Step 3: Generate Checklist

#### File Naming
- Create `checklists/` directory if needed
- Use descriptive names: `ux.md`, `api.md`, `security.md`
- Each run creates NEW file (never overwrites)

#### Checklist Structure

```markdown
# [Domain] Requirements Quality Checklist: [FEATURE NAME]

**Purpose**: Validate [domain] requirement completeness and quality
**Created**: [DATE]
**Feature**: [Link to requirements.md]

## Requirement Completeness
[Items checking if all necessary requirements exist]

- [ ] CHK001 - Are [requirement type] defined for [scenario]? [Completeness]
- [ ] CHK002 - Are [edge cases] addressed in requirements? [Coverage, Gap]

## Requirement Clarity
[Items checking if requirements are unambiguous]

- [ ] CHK003 - Is '[vague term]' quantified with specific criteria? [Clarity, Spec §X.Y]
- [ ] CHK004 - Can '[requirement]' be objectively measured? [Measurability]

## Requirement Consistency
[Items checking alignment across requirements]

- [ ] CHK005 - Do [area A] requirements align with [area B]? [Consistency]
- [ ] CHK006 - Is terminology consistent for '[concept]'? [Consistency]

## Scenario Coverage
[Items checking if all flows are addressed]

- [ ] CHK007 - Are primary flow requirements complete? [Coverage, Spec §X.Y]
- [ ] CHK008 - Are error/exception requirements defined? [Coverage, Gap]

## Notes

[Any additional context or guidance]
```

### Step 4: Write Checklist Items

**EVERY item MUST test REQUIREMENTS QUALITY**:

| Quality Dimension | Pattern | Example |
|-------------------|---------|---------|
| Completeness | "Are [X] requirements defined?" | "Are error handling requirements defined for all API failures?" |
| Clarity | "Is [X] quantified/specified?" | "Is 'fast loading' quantified with timing thresholds?" |
| Consistency | "Do [X] and [Y] align?" | "Do navigation requirements align across all pages?" |
| Measurability | "Can [X] be objectively verified?" | "Can 'visual hierarchy' be objectively measured?" |
| Coverage | "Are [scenarios] addressed?" | "Are zero-state scenarios defined?" |
| Edge Cases | "Is [boundary] defined?" | "Is fallback behavior specified for image load failure?" |

**Item Structure**:
```
- [ ] CHK### - [Question about requirement quality] [Dimension, Reference]
```

**References**:
- `[Spec §X.Y]` - Checking existing requirement
- `[Gap]` - Checking for missing requirement
- `[Ambiguity]` - Flagging unclear wording
- `[Conflict]` - Flagging contradictions
- `[Assumption]` - Flagging undocumented assumptions

### Step 5: Traceability Requirements

**MINIMUM**: >=80% of items must include traceability reference

Each item should reference:
- Spec section: `[Spec §FR-001]`
- Gap marker: `[Gap]`
- Quality marker: `[Ambiguity]`, `[Conflict]`, `[Assumption]`

### Step 6: Content Consolidation

- Soft cap: If >40 candidate items, prioritize by risk/impact
- Merge near-duplicates
- If >5 low-impact edge cases, consolidate: "Are edge cases X, Y, Z addressed?"

## Prohibited Patterns

**ABSOLUTELY PROHIBITED** (makes it implementation test):
- Any item starting with "Verify", "Test", "Confirm" + implementation behavior
- References to code execution, user actions, system behavior
- "Displays correctly", "works properly", "functions as expected"
- "Click", "navigate", "render", "load", "execute"
- Test cases, test plans, QA procedures
- Implementation details (frameworks, APIs)

**REQUIRED PATTERNS**:
- "Are [requirement type] defined/specified for [scenario]?"
- "Is [vague term] quantified with specific criteria?"
- "Are requirements consistent between [A] and [B]?"
- "Can [requirement] be objectively measured?"
- "Does the spec define [missing aspect]?"

## Example Checklists

### UX Requirements Quality (`ux.md`)
```markdown
- [ ] CHK001 - Are visual hierarchy requirements defined with measurable criteria? [Clarity, Spec §FR-1]
- [ ] CHK002 - Is the number and positioning of UI elements explicitly specified? [Completeness, Spec §FR-1]
- [ ] CHK003 - Are interaction state requirements (hover, focus, active) consistently defined? [Consistency]
- [ ] CHK004 - Are accessibility requirements specified for all interactive elements? [Coverage, Gap]
- [ ] CHK005 - Is fallback behavior defined when images fail to load? [Edge Case, Gap]
```

### API Requirements Quality (`api.md`)
```markdown
- [ ] CHK001 - Are error response formats specified for all failure scenarios? [Completeness]
- [ ] CHK002 - Are rate limiting requirements quantified with specific thresholds? [Clarity]
- [ ] CHK003 - Are authentication requirements consistent across all endpoints? [Consistency]
- [ ] CHK004 - Are retry/timeout requirements defined for external dependencies? [Coverage, Gap]
```

### Security Requirements Quality (`security.md`)
```markdown
- [ ] CHK001 - Are authentication requirements specified for all protected resources? [Coverage]
- [ ] CHK002 - Are data protection requirements defined for sensitive information? [Completeness]
- [ ] CHK003 - Is the threat model documented and requirements aligned to it? [Traceability]
- [ ] CHK004 - Are security failure response requirements defined? [Gap, Exception Flow]
```

## Output

After completing this workflow:
- Checklist file created at `checklists/[domain].md`
- Items numbered CHK001, CHK002, etc.
- Ready for review before implementation

## Report

```markdown
## Checklist Generated

**Path**: [full path to checklist]
**Items**: [N] checklist items

### Focus Areas
[Selected focus areas]

### Depth Level
[Standard/Comprehensive/Light]

### Audience
[Author/Reviewer/QA]

### Traceability
[N]% of items have spec references
```

## Next Steps

Suggest to the user:
```
Checklist created at checklists/[domain].md

Next, you can:
1. Review and complete the checklist
2. Run **Implement** (will check checklist status)
3. Create additional checklists for other domains
4. Run **Analyze** for full consistency check
```
