# Bedrock Agents

## Overview

Bedrock Agents are autonomous AI agents that orchestrate foundation models, knowledge bases, APIs, and code execution. The agent automatically handles prompt engineering, memory management, and multi-step reasoning.

Use Bedrock Agents when you need:
- Multi-step task execution with tool/API calling
- Retrieval-augmented generation with Knowledge Bases
- Code interpretation and execution
- Autonomous decision-making with guardrails

## Clients

```python
import boto3

# Build-time: create and configure agents
bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")

# Runtime: invoke agents
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
```

## Create an Agent

```python
agent = bedrock_agent.create_agent(
    agentName="my-assistant",
    foundationModel="us.anthropic.claude-sonnet-4-6",
    agentResourceRoleArn="arn:aws:iam::ACCOUNT:role/BedrockAgentRole",
    instruction="You are a helpful assistant that can look up customer information and process orders.",
    idleSessionTTLInSeconds=1800,  # 30 min session timeout (default)
)
agent_id = agent["agent"]["agentId"]
```

## Action Groups

Action groups define the tools an agent can use. Three approaches:

### 1. Function Definitions (Simplest)

Up to 11 functions, 5 parameters each:

```python
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="customer-tools",
    actionGroupExecutor={"lambda": "arn:aws:lambda:us-east-1:ACCOUNT:function:customer-handler"},
    functionSchema={
        "functions": [
            {
                "name": "get_customer",
                "description": "Look up a customer by ID",
                "parameters": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID",
                        "required": True,
                    }
                },
            },
            {
                "name": "create_order",
                "description": "Create a new order for a customer",
                "parameters": {
                    "customer_id": {"type": "string", "required": True},
                    "product_id": {"type": "string", "required": True},
                    "quantity": {"type": "integer", "required": True},
                },
            },
        ]
    },
)
```

### 2. OpenAPI Schema (For existing APIs)

```python
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="api-tools",
    actionGroupExecutor={"lambda": "arn:aws:lambda:us-east-1:ACCOUNT:function:api-handler"},
    apiSchema={
        "s3": {
            "s3BucketName": "my-schemas",
            "s3ObjectKey": "openapi-spec.json",
        }
    },
)
```

### 3. Return Control (No Lambda — handle in your code)

```python
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="client-tools",
    actionGroupExecutor={"customControl": "RETURN_CONTROL"},
    functionSchema={
        "functions": [{
            "name": "show_ui_dialog",
            "description": "Show a confirmation dialog to the user",
            "parameters": {
                "message": {"type": "string", "required": True},
            },
        }]
    },
)
```

With return control, the agent returns tool use requests to your code — you execute them and return results.

## Lambda Handler for Action Groups

```python
def lambda_handler(event, context):
    action_group = event["actionGroup"]
    function_name = event.get("function", "")
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}

    if function_name == "get_customer":
        result = lookup_customer(parameters["customer_id"])
    elif function_name == "create_order":
        result = create_order(parameters)
    else:
        result = {"error": f"Unknown function: {function_name}"}

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function_name,
            "functionResponse": {
                "responseBody": {
                    "TEXT": {"body": json.dumps(result)}
                }
            },
        },
    }
```

## Code Interpreter

Enable the built-in code interpreter action group:

```python
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="CodeInterpreterAction",
    parentActionGroupSignature="AMAZON.CodeInterpreter",
)
```

The agent can then write and execute Python code to answer questions, perform calculations, and create visualizations.

## Associate Knowledge Bases

```python
bedrock_agent.associate_agent_knowledge_base(
    agentId=agent_id,
    agentVersion="DRAFT",
    knowledgeBaseId="KB_ID",
    description="Company documentation and policies",
    knowledgeBaseState="ENABLED",
)
```

## Prepare and Create Alias

```python
# Prepare agent for testing
bedrock_agent.prepare_agent(agentId=agent_id)

# Create alias for deployment
alias = bedrock_agent.create_agent_alias(
    agentId=agent_id,
    agentAliasName="production",
)
agent_alias_id = alias["agentAlias"]["agentAliasId"]
```

## Invoke Agent

```python
response = bedrock_agent_runtime.invoke_agent(
    agentId=agent_id,
    agentAliasId=agent_alias_id,
    sessionId="unique-session-id",
    inputText="Look up customer C-1234 and create an order for product P-5678, quantity 2.",
    enableTrace=True,  # Enable during development
)

# Process streaming response
for event in response["completion"]:
    if "chunk" in event:
        text = event["chunk"]["bytes"].decode("utf-8")
        print(text, end="")
    if "trace" in event:
        # Detailed execution trace for debugging
        trace = event["trace"]["trace"]
        print(f"\n[Trace] {trace}")
```

## Invoke Agent with Return Control

```python
response = bedrock_agent_runtime.invoke_agent(
    agentId=agent_id,
    agentAliasId=agent_alias_id,
    sessionId=session_id,
    inputText="Show a confirmation dialog for the order.",
)

for event in response["completion"]:
    if "returnControl" in event:
        invocation_id = event["returnControl"]["invocationId"]
        invocation_inputs = event["returnControl"]["invocationInputs"]

        # Execute the function in your code
        for inp in invocation_inputs:
            func = inp["functionInvocationInput"]
            result = handle_function(func["actionGroup"], func["function"], func["parameters"])

        # Return result to agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            sessionState={
                "returnControlInvocationResults": [{
                    "functionResult": {
                        "actionGroup": func["actionGroup"],
                        "function": func["function"],
                        "responseBody": {"TEXT": {"body": json.dumps(result)}},
                    }
                }],
                "invocationId": invocation_id,
            },
        )
```

## User Confirmation

For sensitive operations, enable user confirmation:

```python
bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion="DRAFT",
    actionGroupName="sensitive-ops",
    actionGroupExecutor={"lambda": "arn:aws:lambda:..."},
    functionSchema={...},
    # Agent will ask for confirmation before executing
    actionGroupState="ENABLED",
)
```

Handle in the invocation response similarly to return control.

## IAM Role for Agents

The agent's execution role needs:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:*::foundation-model/*"
        },
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:*:ACCOUNT:function:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": "arn:aws:bedrock:*:ACCOUNT:knowledge-base/*"
        }
    ]
}
```

Trust policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock.amazonaws.com"},
        "Action": "sts:AssumeRole",
        "Condition": {
            "StringEquals": {"aws:SourceAccount": "ACCOUNT_ID"}
        }
    }]
}
```

## Best Practices

- **Enable tracing during development** — `enableTrace=True` shows the agent's reasoning steps
- **Use user confirmation for sensitive actions** — prevents prompt injection attacks
- **Tool naming convention** — agent generates `httpVerb__actionGroupName__apiName` internally; avoid double underscores in your names
- **Session management** — default session timeout is 30 minutes; use unique session IDs per conversation
- **Keep instructions focused** — clear, specific instructions produce better agent behavior
- **Test with DRAFT version** — use `agentVersion="DRAFT"` during development before creating aliases

## Troubleshooting

### Agent not calling tools
- Verify action group is associated with DRAFT version
- Run `prepare_agent()` after any changes
- Check that function descriptions clearly explain when to use each tool

### Lambda timeout
- Default Lambda timeout may be too short for complex operations
- Increase timeout in Lambda configuration
- Ensure Lambda has network access to required services

### AccessDeniedException during invocation
- Verify agent execution role has `bedrock:InvokeModel` permission
- Check Lambda resource policy allows `bedrock.amazonaws.com` invocation
- Ensure model access is enabled in Bedrock console
