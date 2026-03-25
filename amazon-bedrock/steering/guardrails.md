# Bedrock Guardrails

## Overview

Guardrails provide configurable safeguards for AI applications: content filtering, topic denial, PII protection, word blocking, contextual grounding checks, and automated reasoning. Apply them to any Bedrock model invocation or use standalone for input/output validation.

## Client

```python
import boto3

bedrock = boto3.client("bedrock", region_name="us-east-1")
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
```

## Create a Guardrail

```python
guardrail = bedrock.create_guardrail(
    name="app-guardrail",
    blockedInputMessaging="I can't process that request.",
    blockedOutputsMessaging="I can't provide that response.",

    # Content filters
    contentPolicyConfig={
        "filtersConfig": [
            {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "HIGH"},
            {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
        ]
    },

    # Topic denial
    topicPolicyConfig={
        "topicsConfig": [
            {
                "name": "competitor-advice",
                "definition": "Questions asking for recommendations or advice about competitor products or services",
                "examples": [
                    "Should I use competitor X instead?",
                    "Compare your product with competitor Y",
                ],
                "type": "DENY",
            }
        ]
    },

    # PII protection
    sensitiveInformationPolicyConfig={
        "piiEntitiesConfig": [
            {"type": "EMAIL", "action": "ANONYMIZE"},
            {"type": "PHONE", "action": "ANONYMIZE"},
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
        ],
        "regexesConfig": [
            {
                "name": "internal-id",
                "description": "Internal employee IDs",
                "pattern": "EMP-\\d{6}",
                "action": "ANONYMIZE",
            }
        ],
    },

    # Word filters
    wordPolicyConfig={
        "wordsConfig": [
            {"text": "confidential"},
            {"text": "internal-only"},
        ],
        "managedWordListsConfig": [
            {"type": "PROFANITY"},
        ],
    },

    # Contextual grounding (for RAG)
    contextualGroundingPolicyConfig={
        "filtersConfig": [
            {"type": "GROUNDING", "threshold": 0.7},
            {"type": "RELEVANCE", "threshold": 0.7},
        ]
    },
)

guardrail_id = guardrail["guardrailId"]
```

## Create a Version

After configuring, create an immutable version for production:

```python
version = bedrock.create_guardrail_version(
    guardrailIdentifier=guardrail_id,
    description="Production v1",
)
guardrail_version = version["version"]
```

## Use with Converse API

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[{"role": "user", "content": [{"text": "User input here"}]}],
    guardrailConfig={
        "guardrailIdentifier": guardrail_id,
        "guardrailVersion": guardrail_version,  # or "DRAFT" for testing
        "trace": "enabled",
    },
)

# Check if guardrail intervened
if response["stopReason"] == "guardrail_intervened":
    print("Blocked by guardrail")
    # response contains the blocked messaging

# Trace details (if trace enabled)
if "trace" in response:
    guardrail_trace = response["trace"].get("guardrail", {})
```

## Standalone Guardrail Evaluation

Evaluate content without invoking a model:

```python
response = bedrock_runtime.apply_guardrail(
    guardrailIdentifier=guardrail_id,
    guardrailVersion=guardrail_version,
    source="INPUT",  # or "OUTPUT"
    content=[{"text": {"text": "Content to evaluate"}}],
)

action = response["action"]  # "NONE" or "GUARDRAIL_INTERVENED"
if action == "GUARDRAIL_INTERVENED":
    for assessment in response["assessments"]:
        # Check which policies triggered
        if "topicPolicy" in assessment:
            for topic in assessment["topicPolicy"]["topics"]:
                print(f"Topic denied: {topic['name']}")
        if "contentPolicy" in assessment:
            for filter in assessment["contentPolicy"]["filters"]:
                print(f"Content filtered: {filter['type']} ({filter['action']})")
        if "sensitiveInformationPolicy" in assessment:
            for pii in assessment["sensitiveInformationPolicy"]["piiEntities"]:
                print(f"PII detected: {pii['type']} ({pii['action']})")
```

## Filter Types Reference

### Content Filters

| Type | Description |
|------|-------------|
| `HATE` | Discriminatory or hateful content |
| `INSULTS` | Demeaning or offensive language |
| `SEXUAL` | Sexually explicit content |
| `VIOLENCE` | Violent or graphic content |
| `MISCONDUCT` | Criminal activity, dangerous behavior |
| `PROMPT_ATTACK` | Jailbreak attempts, prompt injection |

Strength levels: `NONE`, `LOW`, `MEDIUM`, `HIGH`

### PII Entity Types

Common types: `EMAIL`, `PHONE`, `US_SOCIAL_SECURITY_NUMBER`, `CREDIT_DEBIT_CARD_NUMBER`, `NAME`, `ADDRESS`, `AGE`, `DATE_TIME`, `IP_ADDRESS`, `URL`, `DRIVER_ID`, `LICENSE_PLATE`, `PASSPORT_NUMBER`, `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`

Actions: `BLOCK` (reject entire message), `ANONYMIZE` (replace with placeholder)

### Contextual Grounding

| Type | Description | Threshold |
|------|-------------|-----------|
| `GROUNDING` | Is the response supported by the provided context? | 0.0-1.0 (higher = stricter) |
| `RELEVANCE` | Is the response relevant to the user's query? | 0.0-1.0 (higher = stricter) |

Use with RAG applications — pass retrieved context as `guardContent` blocks in the conversation.

## Guardrails in RAG Applications

When using guardrails with Knowledge Bases, tag context blocks for selective evaluation:

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": [
            {"text": "What is the refund policy?"},
            # Tag retrieved context for grounding check
            {"guardContent": {
                "text": {"text": "Retrieved context from KB: Refunds are available within 30 days..."},
                "qualifiers": ["grounding_source"],
            }},
        ]},
    ],
    guardrailConfig={
        "guardrailIdentifier": guardrail_id,
        "guardrailVersion": guardrail_version,
    },
)
```

## Best Practices

- **Always use guardrails in user-facing apps** — at minimum enable content filters and prompt attack detection
- **Start with HIGH strength** for content filters — relax only if false positives are an issue
- **Use ANONYMIZE over BLOCK for PII** — better user experience, still protects sensitive data
- **Set contextual grounding thresholds to 0.7** — good balance of precision and recall for RAG
- **Create versions for production** — don't use DRAFT in production
- **Test iteratively** — use `apply_guardrail()` standalone to test policies before deploying
- **Reasoning content blocks are NOT filtered** — guardrails skip `reasoningContent` blocks

## Troubleshooting

### False positives blocking legitimate content
- Lower the filter strength from HIGH to MEDIUM
- Review topic denial definitions — make them more specific
- Check word filter list for overly broad terms

### Guardrail not catching unwanted content
- Increase filter strength
- Add specific topic denial policies for your use case
- Add custom regex patterns for domain-specific sensitive data

### Performance impact
- Guardrails add latency (~100-300ms per evaluation)
- Use streaming (`converse_stream`) to reduce perceived latency
- Evaluate only input OR output if full round-trip checking isn't needed
