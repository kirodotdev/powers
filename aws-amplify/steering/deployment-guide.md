# Deployment Guide

Context and routing for the `amplify-deployment-guide` Agent SOP.

## When to Use This Workflow

Use this workflow when:
- Setting up sandbox development environment
- Deploying to production
- Configuring CI/CD pipelines
- Managing environment variables and secrets
- Setting up custom domains

## Retrieve the SOP

```
Tool: retrieve_agent_sop
Parameters: { "sop_name": "amplify-deployment-guide" }
```

## Deployment Options

### Sandbox Environment (Development)

Personal cloud environment for rapid iteration:

```bash
npx ampx sandbox
```

**Features:**
- Isolated per-developer
- Real-time backend hot-reload
- Auto-generates types on changes
- No impact on production

**Requirements:**
- AWS credentials configured
- Node.js 18+
- `AdministratorAccess-Amplify` policy

### Amplify Hosting (Production)

Git-based deployment with automatic builds:

1. Connect repository in [Amplify Console](https://console.aws.amazon.com/amplify)
2. Configure build settings
3. Deploy on push to branch

**Branch Strategy:**

| Branch | Environment | Purpose |
|--------|-------------|---------|
| `main` | Production | Live users |
| `develop` | Staging | QA testing |
| `feature/*` | Preview | PR reviews |

### Custom CI/CD

For custom pipelines:

```bash
npx ampx pipeline-deploy --branch main --app-id <app-id>
```

## Environment Configuration

### Secrets

```typescript
// amplify/backend.ts
import { secret } from '@aws-amplify/backend';

// Reference secret (set in Amplify Console)
const apiKey = secret('THIRD_PARTY_API_KEY');
```

### Environment Variables

Set in Amplify Console -> App settings -> Environment variables

## CI/CD Examples

### GitHub Actions

```yaml
name: Deploy Amplify
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-region: us-east-1
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
      - run: npx ampx pipeline-deploy --branch main --app-id ${{ vars.AMPLIFY_APP_ID }}
```

### AWS CodePipeline

Amplify Hosting includes built-in CI/CD:
- Automatic builds on push
- Preview deployments for PRs
- Environment variable management
- Build notifications

## Monitoring

- **CloudWatch:** Lambda logs, API metrics
- **Amplify Console:** Build logs, deployment status
- **X-Ray:** Distributed tracing (if enabled)

## Next Steps

After deployment:
- Monitor in Amplify Console
- Set up custom domain
- Configure CloudWatch alarms
