# Bedrock Prompt Management and Flows

## Prompt Management

### Overview

Create, version, and manage reusable prompts with variables. Prompts can be used directly as the `modelId` in Converse API calls.

### Client

```python
import boto3

bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")
```

### Create a Prompt

```python
prompt = bedrock_agent.create_prompt(
    name="customer-email-response",
    defaultVariant="main",
    variants=[
        {
            "name": "main",
            "modelId": "us.anthropic.claude-sonnet-4-6",
            "templateType": "CHAT",
            "templateConfiguration": {
                "chat": {
                    "system": [{"text": "You are a customer service agent. Respond professionally and helpfully."}],
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": "Customer email: {{customer_email}}\n\nDraft a response addressing their concern."}],
                        }
                    ],
                    "inputVariables": [{"name": "customer_email"}],
                }
            },
            "inferenceConfiguration": {
                "text": {
                    "maxTokens": 1024,
                    "temperature": 0.5,
                }
            },
        }
    ],
)
prompt_id = prompt["id"]
```

### Create a Version

```python
version = bedrock_agent.create_prompt_version(
    promptIdentifier=prompt_id,
    description="Production v1",
)
version_number = version["version"]
```

### Invoke a Managed Prompt

Use the prompt ARN with version as the `modelId`:

```python
prompt_arn = f"arn:aws:bedrock:us-east-1:ACCOUNT:prompt/{prompt_id}:{version_number}"

response = bedrock_runtime.converse(
    modelId=prompt_arn,
    messages=[{"role": "user", "content": [{"text": "placeholder"}]}],  # Required but overridden by prompt
    promptVariables={
        "customer_email": {"text": "I received a damaged product and want a replacement."},
    },
)
```

**Important restrictions** when using managed prompts as `modelId`:
- Cannot include `additionalModelRequestFields`
- Cannot include `inferenceConfig` (defined in the prompt)
- Cannot include `system` (defined in the prompt)
- Cannot include `toolConfig` (defined in the prompt)

### Variables

Use `{{variable_name}}` in templates:

```python
# In template
"text": "Translate the following from {{source_language}} to {{target_language}}: {{text}}"

# At invocation
promptVariables={
    "source_language": {"text": "English"},
    "target_language": {"text": "French"},
    "text": {"text": "Hello, how are you?"},
}
```

### Template Types

| Type | Use When |
|------|----------|
| `TEXT` | Single-turn completions |
| `CHAT` | Multi-turn conversations with system prompt |

## Flows

### Overview

Flows orchestrate multi-step AI workflows linking models, prompts, knowledge bases, Lambda functions, and guardrails into end-to-end pipelines.

### Clients

```python
# Build-time
bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")

# Runtime
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
```

### Create a Flow

```python
flow = bedrock_agent.create_flow(
    name="document-summarizer",
    executionRoleArn="arn:aws:iam::ACCOUNT:role/BedrockFlowRole",
    definition={
        "nodes": [
            {
                "type": "Input",
                "name": "FlowInput",
                "outputs": [{"name": "document", "type": "String"}],
            },
            {
                "type": "Prompt",
                "name": "Summarize",
                "configuration": {
                    "prompt": {
                        "sourceConfiguration": {
                            "inline": {
                                "modelId": "us.anthropic.claude-sonnet-4-6",
                                "templateType": "TEXT",
                                "templateConfiguration": {
                                    "text": {
                                        "text": "Summarize the following document in 3 bullet points:\n\n{{document}}",
                                        "inputVariables": [{"name": "document"}],
                                    }
                                },
                                "inferenceConfiguration": {
                                    "text": {"maxTokens": 512, "temperature": 0.3}
                                },
                            }
                        }
                    }
                },
                "inputs": [{"name": "document", "type": "String", "expression": "$.data"}],
                "outputs": [{"name": "modelCompletion", "type": "String"}],
            },
            {
                "type": "Output",
                "name": "FlowOutput",
                "inputs": [{"name": "document", "type": "String", "expression": "$.data"}],
            },
        ],
        "connections": [
            {
                "name": "input-to-summarize",
                "source": "FlowInput",
                "target": "Summarize",
                "type": "Data",
                "configuration": {
                    "data": {"sourceOutput": "document", "targetInput": "document"}
                },
            },
            {
                "name": "summarize-to-output",
                "source": "Summarize",
                "target": "FlowOutput",
                "type": "Data",
                "configuration": {
                    "data": {"sourceOutput": "modelCompletion", "targetInput": "document"}
                },
            },
        ],
    },
)
flow_id = flow["id"]
```

### Node Types

| Node Type | Purpose | Configuration |
|-----------|---------|---------------|
| `Input` | Entry point, receives input data | Outputs only |
| `Output` | Exit point, returns final result | Inputs only |
| `Prompt` | Invoke a model with a prompt template | Inline or managed prompt |
| `KnowledgeBase` | Query a Knowledge Base | KB ID, model for generation |
| `LambdaFunction` | Execute custom code | Lambda function ARN |
| `Guardrail` | Apply content safeguards | Guardrail ID and version |

### Prepare and Version

```python
# Prepare for testing
bedrock_agent.prepare_flow(flowIdentifier=flow_id)

# Create immutable version
version = bedrock_agent.create_flow_version(flowIdentifier=flow_id)
flow_version = version["version"]

# Create alias for production
alias = bedrock_agent.create_flow_alias(
    flowIdentifier=flow_id,
    name="production",
    routingConfiguration=[{
        "flowVersion": flow_version,
    }],
)
flow_alias_id = alias["id"]
```

### Invoke a Flow

```python
response = bedrock_agent_runtime.invoke_flow(
    flowIdentifier=flow_id,
    flowAliasIdentifier=flow_alias_id,
    inputs=[{
        "content": {"document": "Your document text here..."},
        "nodeName": "FlowInput",
        "nodeOutputName": "document",
    }],
)

# Process streaming response
result = ""
for event in response["responseStream"]:
    if "flowOutputEvent" in event:
        result = event["flowOutputEvent"]["content"]["document"]
    elif "flowCompletionEvent" in event:
        if event["flowCompletionEvent"]["completionReason"] == "SUCCESS":
            print(f"Result: {result}")
```

### Versioning Model

```
Working Draft (iterate) -> Version (immutable snapshot) -> Alias (points to version)
```

- **Working Draft**: Edit freely, test with `prepare_flow()`
- **Version**: Immutable snapshot, safe for production
- **Alias**: Points to a version, swap without code changes (blue/green deployments)

## Best Practices

### Prompt Management
- **Use variables** for dynamic content — avoid hardcoding values in templates
- **Version prompts before production** — DRAFT can change unexpectedly
- **Use CHAT template type** for conversations — TEXT for single completions
- **Test variants** — create multiple variants with different models/configs for A/B testing

### Flows
- **Test on working draft** before creating versions
- **Use aliases for rollback** — point to a previous version without code changes
- **Keep nodes modular** — each node should do one thing well
- **Use Guardrail nodes** for user-facing flows
- **Lambda functions for custom logic** — data transformation, API calls, business rules

## Troubleshooting

### Prompt invocation fails with "Invalid modelId"
- Ensure you're using the full prompt ARN with version: `arn:aws:bedrock:region:account:prompt/ID:VERSION`
- Verify the prompt version exists (not just DRAFT)

### Flow fails at a node
- Check CloudWatch logs for the flow execution
- Verify all node inputs/outputs are correctly connected
- Ensure IAM role has permissions for all resources used in nodes

### Variables not populated
- Check variable names match exactly (case-sensitive)
- Ensure `inputVariables` in template lists all used variables
- Variables must be passed as `{"text": "value"}` in `promptVariables`
