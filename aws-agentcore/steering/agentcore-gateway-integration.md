# AgentCore Gateway Integration Guide

## Overview

AgentCore Gateway is a managed MCP endpoint that puts several tool sources behind one URL: external MCP servers, Lambda functions, runtimes in the project, OpenAPI and Smithy APIs, and curated connectors such as web search. With the AgentCore CLI, a gateway is a project resource: `agentcore add gateway` declares it, `agentcore add gateway-target` adds tool sources, and `agentcore deploy` creates everything and passes the gateway URL to the project's runtimes.

## Step 1: Add the Gateway

```bash
agentcore add gateway --name tools --protocol-type MCP --authorizer-type AWS_IAM
```

Use these two flags unless the user wants something else:

- `--authorizer-type AWS_IAM` requires SigV4-signed requests. On deploy, the project's runtimes get permission to invoke the gateway. The other values are `CUSTOM_JWT` (callers send a JWT; also pass `--authorizer-configuration`) and `NONE`. **Without the flag, the gateway is created with `NONE`, so anyone with the URL can call its tools.**
- `--protocol-type MCP` makes the gateway URL a complete MCP endpoint. Without it, the gateway URL is a bare origin, and MCP clients must append `/mcp`.

Other options: `--enable-semantic-search`, `--description`, `--policy-engine-name`, `--tags` (see `agentcore add gateway --help`).

## Step 2: Add Targets

### External MCP server

```bash
agentcore add gateway-target --gateway tools --name docs \
  --endpoint https://knowledge-mcp.global.api.aws
```

For a server that needs OAuth (client credentials), first add the credential, then reference it. Secrets are read from a file or stdin; inline values are rejected:

```bash
agentcore add credentials oauth --name partnerOauth \
  --client-id <client-id> \
  --discovery-url https://auth.example.com/.well-known/openid-configuration \
  --client-secret file://client-secret.txt
agentcore add gateway-target --gateway tools --name partner \
  --endpoint https://mcp.example.com/mcp \
  --outbound-auth oauth --credential-name partnerOauth --scope tools.read
```

For a vendor such as GitHub, pass `--vendor` and `--provider-configuration` instead (see `agentcore add credentials oauth --help`). MCP server targets support `--outbound-auth none` or `oauth`, not `api-key`.

### Runtime in the same project

```bash
agentcore add gateway-target --gateway tools --name orderAgent --runtime orders
```

### Lambda function

Write the tool schema as a JSON array of tool definitions, for example `tools/orders.json` in the project:

```json
[
  {
    "name": "get_order",
    "description": "Look up an order by ID",
    "inputSchema": {
      "type": "object",
      "properties": {
        "orderId": { "type": "string", "description": "Order ID" }
      },
      "required": ["orderId"]
    }
  }
]
```

Then add the target with the complete target configuration:

```bash
agentcore add gateway-target --gateway tools --target-configuration '{
  "name": "orders",
  "targetType": "lambdaFunctionArn",
  "lambdaFunctionArn": {
    "lambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:orders",
    "toolSchemaFile": "tools/orders.json"
  }
}'
```

The deploy grants the gateway's role `lambda:InvokeFunction` on the function.

The gateway passes the tool arguments as the Lambda `event`, and the tool name in the client context as `<target>___<tool>` (three underscores):

```python
def lambda_handler(event, context):
    full_name = context.client_context.custom["bedrockAgentCoreToolName"]
    tool_name = full_name.split("___", 1)[1]

    if tool_name == "get_order":
        order_id = event["orderId"]
        return {"orderId": order_id, "status": "shipped"}

    return {"error": f"Unknown tool: {tool_name}"}
```

The function must return JSON.

### Connectors

```bash
agentcore add gateway-connector --gateway tools --name search --connector web-search
agentcore add gateway-connector --gateway tools --name kb --connector bedrock-knowledge-bases --knowledge-base <kb-id>
```

Connectors are not available in the China regions.

### Other target types

`--target-configuration` also accepts `openApiSchema`, `smithyModel`, `apiGateway`, and `passthrough` targets, in the `agentCoreGateways[].targets[]` shape of `agentcore.json`. Use the `get_gateway_guide` MCP tool or the [Gateway documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html) for their fields.

## Step 3: Call the Gateway from a Strands Agent

On deploy, every runtime in the project receives:

- `AGENTCORE_GATEWAY_<NAME>_URL`: the gateway URL
- `AGENTCORE_GATEWAY_<NAME>_ARN`
- `AGENTCORE_GATEWAY_<NAME>_AUTH_TYPE`: `AWS_IAM`, `CUSTOM_JWT`, or `NONE`

`<NAME>` is the gateway name in upper case, with every character other than letters and digits replaced by `_`. The gateway `tools` arrives as `AGENTCORE_GATEWAY_TOOLS_URL`.

Add the dependencies to the runtime's `pyproject.toml`:

```toml
dependencies = [
    "aws-opentelemetry-distro ~= 0.21.0",
    "bedrock-agentcore[strands-agents] >= 1.18.1, < 2.0.0",
    "strands-agents >= 1.62.0, < 2.0.0",
    "mcp",
    "httpx",
    "botocore",
]
```

Create `gateway_client.py` next to `main.py`. It signs requests with the runtime's AWS credentials for `AWS_IAM` gateways:

```python
import os

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient


class GatewaySigV4Auth(httpx.Auth):
    """Signs gateway requests with the runtime's AWS credentials (AWS_IAM gateways)."""

    requires_request_body = True

    def __init__(self, region: str):
        self._signer = SigV4Auth(get_session().get_credentials(), "bedrock-agentcore", region)

    def auth_flow(self, request):
        headers = {k: v for k, v in request.headers.items() if k.lower() != "connection"}
        signed = AWSRequest(method=request.method, url=str(request.url), data=request.content, headers=headers)
        self._signer.add_auth(signed)
        request.headers.update(dict(signed.headers))
        yield request


def get_gateway_mcp_client(name: str) -> MCPClient | None:
    """Return an MCP client for the project gateway NAME, or None if it is not deployed yet."""
    url = os.environ.get(f"AGENTCORE_GATEWAY_{name}_URL")
    if not url:
        return None
    auth_type = os.environ.get(f"AGENTCORE_GATEWAY_{name}_AUTH_TYPE")
    auth = GatewaySigV4Auth(os.environ["AWS_REGION"]) if auth_type == "AWS_IAM" else None
    return MCPClient(lambda: streamablehttp_client(url, auth=auth))
```

This assumes the gateway was added with `--protocol-type MCP`. For a gateway without it, append `/mcp` to the URL. A `CUSTOM_JWT` gateway needs a bearer token instead of SigV4.

Pass the client to the agent as a tool provider. Strands starts the MCP session and lists the gateway's tools:

```python
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from gateway_client import get_gateway_mcp_client

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context):
    tools = []
    gateway = get_gateway_mcp_client("TOOLS")
    if gateway:
        tools.append(gateway)
    agent = Agent(system_prompt="You are a helpful assistant.", tools=tools)
    result = agent(payload.get("prompt", ""))
    return {"response": str(result)}


if __name__ == "__main__":
    app.run()
```

Gateway tools are named `<target>___<tool>`, for example `orders___get_order`.

## Step 4: Deploy and Test

Confirm with the user before deploying.

```bash
agentcore deploy
agentcore invoke --runtime agent --payload '{"prompt": "What is the status of order 42?"}'
agentcore logs runtime --name agent --since 15m
```

## Testing the Gateway Locally

`agentcore dev` does not inject the gateway variables. After the first deploy, get the gateway URL and add the variables to `agentcore/.env.local`:

```bash
agentcore gateway list
agentcore gateway get --id <gateway-id>
```

```bash
AGENTCORE_GATEWAY_TOOLS_URL=<gateway-url>
AGENTCORE_GATEWAY_TOOLS_AUTH_TYPE=AWS_IAM
```

For an `AWS_IAM` gateway, the developer's credentials need `bedrock-agentcore:InvokeGateway` on the gateway.

## Inspect and Remove

```bash
agentcore gateway list
agentcore gateway get --id <gateway-id>
agentcore gateway target list --gateway-id <gateway-id>

agentcore remove gateway-target --gateway tools --name docs
agentcore remove gateway --name tools
agentcore deploy
```

Removing a resource takes effect on the next deploy. Confirm with the user before removing.

## Troubleshooting

**The agent sees no gateway tools:** check that the project was deployed after the gateway and its targets were added, and that the code reads the right `AGENTCORE_GATEWAY_<NAME>_URL`. Locally, check `agentcore/.env.local`.

**The gateway rejects requests as unauthorized:** for `AWS_IAM`, requests must be SigV4-signed for the service `bedrock-agentcore` in the gateway's region, by a principal allowed to call `bedrock-agentcore:InvokeGateway`.

**MCP calls fail on a gateway created without `--protocol-type MCP`:** its URL is a bare origin; append `/mcp`.

**`mcpServer targets do not support API_KEY outbound auth`:** MCP server targets take `none` or `oauth`.

**Lambda tool fails:** check the Lambda's CloudWatch logs, that the handler strips the `<target>___` prefix from the tool name, and that the tool schema matches the arguments the handler reads.

## Resources

- [AgentCore Gateway documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [Lambda function targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html)
- [Strands MCP tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/)
