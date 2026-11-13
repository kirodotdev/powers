---
inclusion: auto
name: connectors
description: "S3 connector for AWS Transform agents: read or write files in a customer's S3 bucket through the platform S3 connector (create_platform_connector_hitl_task, the SDK Connector class, temporary credentials, the 'not authorized to access this type of connector' error)"
---

# Connectors (S3)

A **connector** gives a job scoped, temporary access to a resource in the user's AWS account. To
read files from a customer's S3 bucket, ask the user for the platform S3 connector with the MCP tool
`create_platform_connector_hitl_task`, then get temporary credentials for it with the SDK class
`Connector`. This file covers S3 only.

## When to load

- An agent must read files from a customer's S3 bucket, or write its output to that bucket.
- A credential call fails with `not authorized to access this type of connector`.

## Flow

```
1  model       create_platform_connector_hitl_task(step_id, connector="s3")
   |             -> HITL task (GeneralConnector, NON_BLOCKING); the result holds hitl_task_id
   v
2  user        creates or selects the connector in the task             status PENDING
   v
3  admin       an administrator of the target AWS account approves it   status ACTIVE
   v
4  user        submits the task
   v
5  model       retrieve_hitl_output_as_string(hitl_task_id)
   |             -> payload: {"connectorId": "..."}
   v
6  agent code  Connector.get_connector(connector_id)                    -> status, s3BucketArn
               Connector.get_temporary_credentials_for_connector(connector_id)
                                                                        -> credentials for 1 hour
               boto3.client("s3", ...) with these credentials           -> S3 calls on the bucket
```

The connector type is `platform|s3|1`. It works for every agent, also one whose agent card declares
`"connectors": []`. No allowlisting.

## The tool

`create_platform_connector_hitl_task` is a tool of the agentic MCP server. An agent that is built
with the MCP client has it with no code change: the SDK passes every MCP tool to the model, except
a deny-list.

| Name | Value |
|------|-------|
| Argument `step_id` | The id of a step of the current job plan. Any step works. `list_job_plan_steps` returns the ids. An orchestrator whose plan has no step creates one first with `put_job_plan`, then reads the id with `list_job_plan_steps`. |
| Argument `connector` | `"s3"` |
| Result key `hitl_task_id` | The id of the HITL task (component `GeneralConnector`, `NON_BLOCKING`). The tool starts the task and does not wait for the user. |
| Connector settings | `s3BucketArn` (required), `s3BucketKmsKeyArn` (optional) |
| Task output | After the user submits the task, `retrieve_hitl_output_as_string` (argument `hitl_task_id`) returns it: the result key `payload` holds the JSON text `{"connectorId": "..."}` |

- **Subagents:** a subagent cannot create plan steps (`put_job_plan` is not among its tools by
  default), so it gets the step id from its orchestrator.
- **System prompt:** give the model the order: call the tool, ask the user to say when the task is
  submitted, then read `connectorId` and pass it to your custom tool.
- **Other tool:** do not use `create_s3_connector_hitl_task` here. It asks for a workload-owned
  connector type (see the error below).
- **Your own task:** a `GeneralConnector` task that you build without the tool needs the wrapper
  `{"properties": {"connector": {...}}}` in its input artifact.
  `Connector.build_general_connector_artifact` adds it.

## Get credentials in agent code

Call this function in a custom tool, with the connector id that the model passes. It returns an S3
client and the bucket name. If the connector is not `ACTIVE`, it raises an error before the
credential call.

```python
from typing import Any

import boto3
from agent_builder_sdk.agentic_framework.client_factory import create_agentic_api_client
from agent_builder_sdk.agentic_framework.connector import Connector
from agent_builder_sdk.env_var import get_agent_context_from_env


def s3_for_connector(connector_id: str) -> tuple[Any, str]:
    ctx = get_agent_context_from_env()
    connector = Connector(workspace_id=ctx.workspace_id, job_id=ctx.job_id,
                          agent_instance_id=ctx.agent_instance_id,
                          client=create_agentic_api_client())
    info = connector.get_connector(connector_id)
    status = info["accountConnection"]["awsAccountConnection"]["status"]
    if status != "ACTIVE":
        raise RuntimeError(f"Connector {connector_id} is {status}, not ACTIVE. Tell the user, "
                           "and try again after they confirm.")
    bucket = info["configuration"]["s3BucketArn"].split(":::")[-1]
    creds = connector.get_temporary_credentials_for_connector(connector_id)
    s3 = boto3.client("s3", aws_access_key_id=creds["accessKey"],
                      aws_secret_access_key=creds["secretKey"],
                      aws_session_token=creds["accessToken"])
    return s3, bucket
```

## Rules

| Topic | Rule |
|-------|------|
| Approval | `get_connector` returns the status at `accountConnection.awsAccountConnection.status`: `PENDING`, `ACTIVE` or `REJECTED`. An administrator of the target AWS account approves a `PENDING` connector; then it is `ACTIVE`. Ask for credentials only when it is `ACTIVE`. If it is not, tell the user, and try again after they confirm. |
| Expiry | The credentials last 1 hour (`expirationTime`). After that, call `get_temporary_credentials_for_connector` again and build a new S3 client. |
| Read | The credentials can read the bucket. |
| Write | Only under `transform-output/<jobId>/`: `s3.put_object(Bucket=bucket, Key=f"transform-output/{job_id}/{file_name}", Body=data)`, where `job_id` is `get_agent_context_from_env().job_id`. S3 denies a write under another job's prefix with `AccessDenied`. |
| Secrets | Never log or print the credentials. Never return them from a tool to the model. |
| Key names | `accessKey`, `secretKey`, `accessToken` (the session token). They differ from the AWS STS names: copy the mapping from the sample. |

## Error: not authorized to access this type of connector

```
ValidationException: ... Partner '<name>' is not authorized to access this type of connector.
```

- **Where:** the credential call (`GetTemporaryCredentialsForConnector`). The connector can still be
  created and become `ACTIVE` before that; only the credential call fails.
- **Cause:** the connector has a workload-owned type, `mainframe_modernization|s3|1` or
  `dotnet_modernization|s3|1`. These types are allowlisted per agent publisher, and this agent is
  not on the list.
- **Fix:** ask the user for the platform connector with `create_platform_connector_hitl_task`, then
  use the new connector id.

## Minimum versions

| Package | Provides | Minimum version |
|---------|----------|-----------------|
| `agent-builder-agentic-mcp-aws-transform` | The tool `create_platform_connector_hitl_task` | TBD (set at release) |
| `agent-builder-sdk-aws-transform` | The class `Connector` | TBD (set at release) |
