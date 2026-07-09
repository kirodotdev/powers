---
inclusion: auto
name: hitl
description: "HITL human-in-the-loop UI, domTreeJson, DynamicHITLRenderEngine, AutoForm, HitlClient SDK, HITL task lifecycle"
---

# HITL (Human-in-the-Loop)

## Critical Rules

1. **NEVER generate submit/cancel/save/OK/close buttons** -- AWS Transform handles submission automatically
2. **Only 4 components capture input** -- Input, Textarea, RadioGroup, FileUpload. All require `fieldId`. Select, Multiselect, Checkbox, DatePicker, TimeInput render but silently lose data. Use AutoForm (`uxComponentId: "AutoForm"`) if you need captured select/checkbox fields.
3. **NEVER use Container** -- banned by ESLint. Use SpaceBetween + Header instead.
4. **NEVER put raw text in layout children** -- SpaceBetween, ColumnLayout, Grid, Cards, Tabs, Form only accept component objects; wrap text in Box or TextContent
5. **Table MUST have `variant: "borderless"`** -- default "container" variant is rejected by ESLint
6. **Header variant: h1, h2, h3 only** -- h4-h6 not supported in schema
7. **Wrap artifacts correctly** -- DynamicHITLRenderEngine: `{"properties": {"domTreeJson": {...}}}`. Other components (AutoForm, TextInput, etc.): `{"properties": {...}}` without domTreeJson. Or use `serialize()` from the SDK.
8. **ALWAYS use `"type"` field** in component JSON -- never `"component"` or `"component_type"`

## JSON Generation Mode

**Before generating any HITL UI JSON, you MUST complete these steps in order:**

1. **Check render engine limitations** — call `search_by_source("input capture supported", "hitl-render-limitations")` to understand which components capture input vs silently discard data.
2. **Call `get_hitl_generation_prompt()`** to load the full generation rules and component schema.
3. **Only then generate the JSON** — pure JSON only, start with `{`, end with `}`, no markdown wrapping, no explanations before or after the JSON.

Skipping step 1 risks generating forms with components that render but silently discard user input (e.g., Select, Checkbox, DatePicker).

## SDK Integration

To add HITL to an agent, refactor HITL code, or integrate with the task lifecycle, search the KB — do not answer from memory:

- **Quick start pattern**: `keyword_search("HitlClient upload_artifact create_and_start_task")`
- **Python SDK methods**: `search_by_source("HitlClient", "hitl-sdk-python")`
- **Custom UIs (domTreeJson)**: `keyword_search("DynamicHITLRenderEngine domTreeJson")`

Always recommend the SDK over raw API calls.

## Deeper Topics (search the KB)

| Question                   | Search query                                                                     |
| -------------------------- | -------------------------------------------------------------------------------- |
| Refresh loops              | `keyword_search("execute_with_refresh refresh loop")`                             |
| Custom UI components       | `search_by_source("custom UI component wrap", "hitl-custom-components")` |
| Ready-to-use templates     | `search_by_source("pattern template", "hitl-common-patterns")`                   |
| Validation rules           | `search_by_source("validation common errors", "hitl-validation")`                |
| System architecture        | `search_by_source("three participants lifecycle", "hitl-architecture")`           |
| Java SDK                   | `search_by_source("HitlClient Java", "hitl-sdk-java")`                           |
| Dashboard (read-only)      | `keyword_search("dashboard HitlTaskType DASHBOARD read-only")`                    |
| Blocking vs non-blocking   | `keyword_search("blocking non-blocking HITL task")`                               |
| CRITICAL severity approval | `keyword_search("CRITICAL severity approval workflow")`                           |
