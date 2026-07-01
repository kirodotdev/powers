# LocalStack Troubleshooting

Debugging guide for common LocalStack issues.

## LocalStack Won't Start

```bash
# Check if port 4566 is already in use
lsof -i :4566

# Check Docker is running
docker info

# View startup logs
localstack start 2>&1 | head -50

# Force stop and restart
localstack stop
localstack start -d
```

## MCP Server Not Connecting

1. Confirm the token in the Power's `mcp.json` is a real value (not `${LOCALSTACK_AUTH_TOKEN}` unless your IDE resolves it at launch).
2. Ensure Node.js v22+ is installed: `node --version`
3. Test MCP connectivity by calling `localstack-docs` with any query — this does NOT require LocalStack to be running.
4. If `localstack-docs` fails, the MCP server itself is not starting. Check Kiro's MCP server logs.
5. As a last resort, smoke-test the MCP package outside Kiro by running it with the token inline for one process: `LOCALSTACK_AUTH_TOKEN=your-token npx -y @localstack/localstack-mcp-server`. Prefer verifying from inside Kiro via `localstack-docs` whenever possible.

**DO NOT** use the shell to verify MCP auth, including `$([ -n "$LOCALSTACK_AUTH_TOKEN" ] && echo YES || echo NO)`, `echo`, `printenv`, or `grep` on `LOCALSTACK`. The MCP token is injected from IDE/MCP configuration, which is unrelated to interactive shell profiles. Prefer a **`localstack-docs`** MCP call as the smoke test.

## Services Not Available

```bash
# Check service health
curl http://localhost:4566/_localstack/health | jq '.services'

# Restart with debug mode
localstack stop && DEBUG=1 localstack start -d
```

## awslocal Command Not Found

```bash
pip install awscli-local
# Verify installation (use 'which', not '--version')
which awslocal
```

`awslocal --version` will fail even when correctly installed — always use `which awslocal`.

## Feature or MCP Tool Not Available

1. Verify your auth token is valid at https://app.localstack.cloud/
2. For Kiro: confirm the MCP `env.LOCALSTACK_AUTH_TOKEN` value in `mcp.json` is correct — use an MCP tool call to confirm, not `echo` in bash.
3. For CLI: run `localstack auth show-token` and confirm `Valid: True`.
4. Confirm your **plan tier** includes the feature or MCP capability you're using (some tools need a higher tier than Hobby).

## Common Workflow Issues

### Deployment Fails

- Check `localstack status` — LocalStack may not be running
- Review logs: use `localstack-logs-analysis` MCP tool or `localstack logs | grep -i error`
- IAM errors with `ENFORCE_IAM=1`: switch to `ENFORCE_IAM=soft` to discover required permissions
- CDK bootstrap errors: run `cdklocal bootstrap` before first deploy

### Lambda Not Executing

```bash
# Check function exists
awslocal lambda list-functions

# Check logs for the function
awslocal logs describe-log-groups
awslocal logs get-log-events --log-group-name /aws/lambda/my-function --log-stream-name $(awslocal logs describe-log-streams --log-group-name /aws/lambda/my-function --query 'logStreams[0].logStreamName' --output text)
```

### SQS Not Triggering Lambda

```bash
# Verify event source mapping exists
awslocal lambda list-event-source-mappings

# Check queue has messages
awslocal sqs get-queue-attributes --queue-url http://localhost:4566/000000000000/my-queue --attribute-names All
```

## Debugging Tips

- **Enable debug logging**: Start with `DEBUG=1` when troubleshooting. Use `LS_LOG=trace` for maximum verbosity.
- **Use the logs analysis tool**: Instead of grepping raw logs, use `localstack-logs-analysis` for structured error summaries.
- **Check health endpoints**: `curl http://localhost:4566/_localstack/health | jq` shows which services are available.
- **Container name**: Default is `localstack-main`. Use `docker logs localstack-main` for raw Docker logs.
