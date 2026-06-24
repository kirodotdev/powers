# Bedrock Converse API

## Overview

The Converse API is the **recommended** way to invoke any model on Bedrock. It provides a unified interface across all providers — no model-specific payload formats needed.

**Always use Converse API** instead of `invoke_model()`. The only exception is image/video generation models (Nova Canvas, Nova Reel, Stability) which still require `invoke_model()`.

## Client Setup

```python
import boto3

# For model invocation (Converse, InvokeModel)
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

# For management operations (list models, manage resources)
bedrock = boto3.client("bedrock", region_name="us-east-1")
```

**Critical**: Use `bedrock-runtime` for invocation, `bedrock` for management. They are different clients.

## Basic Converse Call

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": [{"text": "Explain quantum computing in one paragraph."}]}
    ],
    system=[{"text": "You are a concise science educator."}],
    inferenceConfig={
        "maxTokens": 1024,
        "temperature": 0.7,
        "topP": 0.9,
        "stopSequences": []
    },
)

# Extract response
output_text = response["output"]["message"]["content"][0]["text"]
stop_reason = response["stopReason"]  # end_turn, max_tokens, stop_sequence, tool_use
usage = response["usage"]  # inputTokens, outputTokens
```

## Streaming

```python
response = bedrock_runtime.converse_stream(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[{"role": "user", "content": [{"text": "Write a poem about clouds."}]}],
    inferenceConfig={"maxTokens": 512},
)

# Process stream events
for event in response["stream"]:
    if "contentBlockDelta" in event:
        delta = event["contentBlockDelta"]["delta"]
        if "text" in delta:
            print(delta["text"], end="", flush=True)
    elif "messageStop" in event:
        stop_reason = event["messageStop"]["stopReason"]
    elif "metadata" in event:
        usage = event["metadata"]["usage"]
```

### Stream Event Order

```
messageStart -> contentBlockStart -> contentBlockDelta (repeats) -> contentBlockStop -> messageStop -> metadata
```

## Multi-Turn Conversations

Bedrock is stateless — include the full conversation history in each call:

```python
messages = []

# Turn 1
messages.append({"role": "user", "content": [{"text": "What is Python?"}]})
response = bedrock_runtime.converse(modelId="us.anthropic.claude-sonnet-4-6", messages=messages)
assistant_message = response["output"]["message"]
messages.append(assistant_message)

# Turn 2
messages.append({"role": "user", "content": [{"text": "Show me a hello world example."}]})
response = bedrock_runtime.converse(modelId="us.anthropic.claude-sonnet-4-6", messages=messages)
```

## Multimodal Inputs

### Images

```python
# From bytes
with open("image.png", "rb") as f:
    image_bytes = f.read()

messages = [{"role": "user", "content": [
    {"image": {"format": "png", "source": {"bytes": image_bytes}}},
    {"text": "Describe this image."}
]}]

# From S3
messages = [{"role": "user", "content": [
    {"image": {"format": "png", "source": {"s3Location": {"uri": "s3://bucket/image.png"}}}},
    {"text": "Describe this image."}
]}]
```

### Documents

```python
with open("report.pdf", "rb") as f:
    doc_bytes = f.read()

messages = [{"role": "user", "content": [
    {"document": {
        "format": "pdf",
        "name": "quarterly-report",  # alphanumeric, whitespace, hyphens, parens, brackets only
        "source": {"bytes": doc_bytes}
    }},
    {"text": "Summarize the key findings."}  # REQUIRED: must include text with documents
]}]
```

Supported formats: pdf, csv, doc, docx, xls, xlsx, html, txt, md, pptx

**Important**: Documents MUST have an accompanying text content block. The document name must only contain alphanumeric characters, whitespace, hyphens, parentheses, and square brackets.

### Video

```python
messages = [{"role": "user", "content": [
    {"video": {"format": "mp4", "source": {"s3Location": {"uri": "s3://bucket/video.mp4"}}}},
    {"text": "What happens in this video?"}
]}]
```

Supported formats: mp4, webm, mov, mkv, flv, avi, wmv, three_gp

## Tool Use (Function Calling)

### Define Tools

```python
tool_config = {
    "tools": [{
        "toolSpec": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    }]
}
```

### Tool Use Loop

```python
messages = [{"role": "user", "content": [{"text": "What's the weather in Paris?"}]}]

response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=messages,
    toolConfig=tool_config,
)

# Check if model wants to use a tool
while response["stopReason"] == "tool_use":
    assistant_message = response["output"]["message"]
    messages.append(assistant_message)

    # Extract tool use request
    tool_use_block = next(
        b for b in assistant_message["content"] if "toolUse" in b
    )
    tool_use_id = tool_use_block["toolUse"]["toolUseId"]
    tool_name = tool_use_block["toolUse"]["name"]
    tool_input = tool_use_block["toolUse"]["input"]

    # Execute tool (your implementation)
    result = execute_tool(tool_name, tool_input)

    # Return result to model
    messages.append({"role": "user", "content": [{
        "toolResult": {
            "toolUseId": tool_use_id,
            "content": [{"text": str(result)}]
        }
    }]})

    response = bedrock_runtime.converse(
        modelId="us.anthropic.claude-sonnet-4-6",
        messages=messages,
        toolConfig=tool_config,
    )
```

## Prompt Caching

Reduces cost and latency for repeated large contexts (system prompts, documents, tool definitions):

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": [
            {"text": "Very long document content here..."},
            {"cachePoint": {"type": "default"}},  # Cache everything before this point
            {"text": "Now answer my question about the document."}
        ]}
    ],
)

# Check cache usage in response
usage = response["usage"]
cache_read = usage.get("cacheReadInputTokensCount", 0)
cache_write = usage.get("cacheWriteInputTokensCount", 0)
```

Cache points can be placed in: system prompts, messages, tool configurations.

## Reasoning / Extended Thinking

For models that support it (Claude 3.7 Sonnet+):

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[{"role": "user", "content": [{"text": "Solve this step by step: ..."}]}],
    additionalModelRequestFields={
        "thinking": {"type": "enabled", "budget_tokens": 4096}
    },
)

# Response includes reasoningContent blocks
for block in response["output"]["message"]["content"]:
    if "reasoningContent" in block:
        print("Thinking:", block["reasoningContent"]["reasoningText"]["text"])
    elif "text" in block:
        print("Answer:", block["text"])
```

**Important**: When continuing a conversation with reasoning, include the reasoning content blocks and their signatures in subsequent requests. Tampering with reasoning content causes errors.

## Guardrails Integration

```python
response = bedrock_runtime.converse(
    modelId="us.anthropic.claude-sonnet-4-6",
    messages=[{"role": "user", "content": [{"text": "User input here"}]}],
    guardrailConfig={
        "guardrailIdentifier": "your-guardrail-id",
        "guardrailVersion": "1",
        "trace": "enabled",  # Optional: see guardrail evaluation details
    },
)
```

## Inference Configuration Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `maxTokens` | int | Maximum tokens in response |
| `temperature` | float (0-1) | Randomness. 0=deterministic, 1=creative |
| `topP` | float (0-1) | Nucleus sampling threshold |
| `stopSequences` | list[str] | Sequences that stop generation |

Model-specific parameters go in `additionalModelRequestFields`:
```python
additionalModelRequestFields={
    "top_k": 50,  # Anthropic-specific
    "thinking": {"type": "enabled", "budget_tokens": 4096},  # Claude reasoning
}
```

## Error Handling

```python
from botocore.exceptions import ClientError

try:
    response = bedrock_runtime.converse(...)
except ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "ThrottlingException":
        # Switch to CRIS or implement backoff
        pass
    elif error_code == "ValidationException":
        # Check message format
        pass
    elif error_code == "AccessDeniedException":
        # Enable model access in console
        pass
    elif error_code == "ModelTimeoutException":
        # Retry or reduce input size
        pass
```

## Common Pitfalls

- **Using `invoke_model()` instead of `converse()`** — Converse is the standard, works across all text models
- **Forgetting to include full history** — Bedrock is stateless, each call needs the complete conversation
- **Not handling `tool_use` stop reason** — If you define tools, you MUST handle the tool use loop
- **Putting system prompt in messages** — Use the `system` parameter, not a user message
- **Wrong client** — `bedrock-runtime` for invocation, `bedrock` for management
- **Not using CRIS** — Always use `us.*` or `global.*` prefixed model IDs for production
