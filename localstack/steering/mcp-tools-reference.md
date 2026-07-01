# MCP Tools Reference

Complete reference for all LocalStack MCP tools available through this Power.

## MCP-First Principle

When helping in Kiro, **prefer MCP tools** over unstructured shell commands so behavior stays consistent with the [LocalStack MCP Server](https://github.com/localstack/localstack-mcp-server):

| Goal | Prefer | Instead of |
|------|--------|------------|
| Start/stop/restart or health | `localstack-management` | Raw `docker` commands |
| Deploy CDK/Terraform/SAM | `localstack-deployer` | Manual `tflocal`/`cdklocal` without project detection |
| Read or summarize logs | `localstack-logs-analysis` | Pasting huge `localstack logs` output |
| Run AWS API calls against LocalStack | `localstack-aws-client` | Unsanitized `aws` against real AWS endpoints |
| IAM violations / least-privilege drafts | `localstack-iam-policy-analyzer` | Hand-written IAM from guesses |
| Cloud Pods snapshots | `localstack-cloud-pods` | Only CLI `localstack pod` when MCP fits |
| Chaos / faults | `localstack-chaos-injector` | Ad hoc failure injection scripts |
| Docs and coverage questions | `localstack-docs` | Generic web search only |

Tools that depend on your subscription tier still require a valid auth token and the right plan for that capability.

---

## Container Management

**`localstack-management`** — Start, stop, restart, and check the status of your LocalStack container. Injects environment variables and monitors health.

```javascript
usePower('localstack', 'localstack', 'localstack-management', {
  action: 'start',
  envVars: { DEBUG: '1', PERSISTENCE: '1' },
});
```

---

## Infrastructure Deployment

**`localstack-deployer`** — Deploy CDK, Terraform, and SAM infrastructure to LocalStack automatically using the `cdklocal`, `tflocal`, and `samlocal` wrapper tools.

```javascript
usePower('localstack', 'localstack', 'localstack-deployer', {
  action: 'deploy',
  projectType: 'terraform',
  directory: './infra',
});
```

---

## AWS CLI Execution

**`localstack-aws-client`** — Execute `awslocal` CLI commands inside the running LocalStack container. Commands are sanitized to prevent shell injection.

```javascript
usePower('localstack', 'localstack', 'localstack-aws-client', {
  command: 's3 ls',
});
```

---

## Log Analysis

**`localstack-logs-analysis`** — Analyze LocalStack logs for errors, API request patterns, service call metrics, and failure summaries. Supports filtering by service and operation.

```javascript
usePower('localstack', 'localstack', 'localstack-logs-analysis', {
  analysisType: 'errors',
  service: 'lambda',
});
```

---

## IAM Policy Analyzer

**`localstack-iam-policy-analyzer`** — Set IAM enforcement levels, detect permission violations, and auto-generate least-privilege IAM policies based on actual access patterns. **Plan tier:** may require a higher tier than Hobby.

```javascript
usePower('localstack', 'localstack', 'localstack-iam-policy-analyzer', {
  action: 'set-mode',
  mode: 'SOFT_MODE',
});
```

```javascript
usePower('localstack', 'localstack', 'localstack-iam-policy-analyzer', {
  action: 'analyze-policies',
});
```

### IAM Workflows

- **Start with soft enforcement**: Use `ENFORCE_IAM=soft` to discover required permissions without breaking your application.
- **Generate policies from usage**: Let LocalStack observe actual API calls in soft mode, then use the analyzer to generate a least-privilege policy.
- **Mirror production IAM**: Configure LocalStack IAM to match production roles and policies to catch permission issues before deploying.

---

## Chaos Engineering

**`localstack-chaos-injector`** — Inject network latency, service errors, and fault rules to simulate real-world failure conditions. **Plan tier:** may require a higher tier than Hobby.

```javascript
usePower('localstack', 'localstack', 'localstack-chaos-injector', {
  action: 'inject-latency',
  latency_ms: 500,
});
```

```javascript
usePower('localstack', 'localstack', 'localstack-chaos-injector', {
  action: 'inject-faults',
  rules: [
    {
      service: 'dynamodb',
      region: 'us-east-1',
      operation: 'PutItem',
      probability: 0.2,
      error: { statusCode: 503, code: 'ServiceUnavailable' },
    },
  ],
});
```

### Chaos Best Practices

- **Always clean up faults**: Use `action: 'clear-all-faults'` (and `clear-latency`) before running functional tests.
- **Test one failure mode at a time**: Isolate how your application responds to a single service or operation failure.
- **Combine with Cloud Pods**: Save a known-good state before injecting chaos so you can quickly restore after testing.

---

## Cloud Pods (State Snapshots)

**`localstack-cloud-pods`** — Save and load state snapshots to reproduce environments, share state across team members, and preload CI/CD pipelines. **Plan tier:** Cloud Pods often require a paid or team tier.

```javascript
usePower('localstack', 'localstack', 'localstack-cloud-pods', {
  action: 'save',
  pod_name: 'my-feature-branch-state',
});
```

---

## Extensions

**`localstack-extensions`** — Install, list, and uninstall LocalStack Extensions from the marketplace (e.g., MailHog for SES email capture). **Plan tier:** may require a higher tier than Hobby.

```javascript
usePower('localstack', 'localstack', 'localstack-extensions', {
  action: 'install',
  name: 'localstack-extension-mailhog',
});
```

---

## Ephemeral Instances

**`localstack-ephemeral-instances`** — Launch and manage temporary cloud-hosted LocalStack instances for CI/CD pipelines, demos, and isolated testing. **Plan tier:** may require a higher tier than Hobby.

```javascript
usePower('localstack', 'localstack', 'localstack-ephemeral-instances', {
  action: 'create',
  name: 'ci-preview-1',
  lifetime: 60,
});
```

---

## Documentation Search

**`localstack-docs`** — Search the official LocalStack documentation. No running LocalStack instance required. Also useful as a lightweight connectivity check after auth setup.

```javascript
usePower('localstack', 'localstack', 'localstack-docs', {
  query: 'how to configure SQS with LocalStack',
});
```
