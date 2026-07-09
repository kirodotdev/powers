# Infrastructure as Code Deployment with LocalStack

Guidelines for deploying Terraform, CDK, CloudFormation, and Pulumi against LocalStack.

## MCP: `localstack-deployer`

In Kiro, use the **`localstack-deployer`** tool when the user wants to deploy from a project directory and the repo already uses `cdklocal`, `tflocal`, or `samlocal`. It runs the same wrappers the [LocalStack MCP server](https://github.com/localstack/localstack-mcp-server) documents, with automatic configuration detection where possible.

```javascript
usePower('localstack', 'localstack', 'localstack-deployer', {
  action: 'deploy',
  projectType: 'terraform',
  directory: './infra',
});
```

Use terminal `tflocal` / `cdklocal` / `samlocal` when the user is iterating in their own shell, when paths or env are highly custom, or when `localstack-deployer` is not available. Combine with **`localstack-logs-analysis`** if deploys fail and you need structured errors.

## Core Principle: Always Use Wrapper Tools

LocalStack provides drop-in wrapper tools that automatically configure all AWS provider endpoints to point to `http://localhost:4566`. **ALWAYS** use these wrappers — they require zero changes to your existing IaC code.

| Tool | Wrapper | Install |
|------|---------|---------|
| Terraform | `tflocal` | `pip install terraform-local` |
| AWS CDK | `cdklocal` | `npm install -g aws-cdk-local aws-cdk` |
| AWS SAM | `samlocal` | `pip install aws-sam-cli-local` |
| Pulumi | `pulumilocal` | `pip install pulumi-local` |
| AWS CLI | `awslocal` | `pip install awscli-local` |

Only fall back to manual provider configuration if a wrapper tool cannot be installed (e.g., package manager unavailable in environment).

---

## Terraform

### Using tflocal (PREFERRED)

```bash
# Install once
pip install terraform-local

# Use exactly like terraform — no provider changes needed
tflocal init
tflocal plan
tflocal apply -auto-approve
tflocal destroy -auto-approve
```

### Manual Provider Configuration (FALLBACK ONLY)

Only modify provider config if `tflocal` is unavailable. When using manual config, list endpoints for **every** AWS service used:

```hcl
provider "aws" {
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3       = "http://localhost:4566"
    dynamodb = "http://localhost:4566"
    lambda   = "http://localhost:4566"
    iam      = "http://localhost:4566"
    sqs      = "http://localhost:4566"
    sns      = "http://localhost:4566"
    # Add all other services used in your configuration
  }
}
```

### Terraform Best Practices for LocalStack

- **ALWAYS** use `tflocal` to avoid manual provider changes
- Run `tflocal plan` before `tflocal apply` to review changes
- Use `PERSISTENCE=1` with LocalStack to retain state across restarts
- Use Cloud Pods to save Terraform-deployed state for team sharing
- Test `tflocal destroy` to ensure cleanup works correctly

---

## AWS CDK

### Setup and Deployment

```bash
# Install cdklocal (installs aws-cdk too)
npm install -g aws-cdk-local aws-cdk

# Bootstrap LocalStack (first time per environment)
cdklocal bootstrap

# Deploy all stacks (no approval needed locally)
cdklocal deploy --all --require-approval never

# Deploy a specific stack
cdklocal deploy MyStack --require-approval never

# Preview changes (equivalent to diff)
cdklocal diff

# Synthesize to CloudFormation without deploying
cdklocal synth

# Destroy all stacks
cdklocal destroy --all --force
```

### CDK Best Practices for LocalStack

- **ALWAYS** run `cdklocal bootstrap` before the first deploy in a new environment
- Use `cdklocal synth` to validate CDK code generates valid CloudFormation before deploying
- Use `--require-approval never` for local development to skip manual confirmation prompts
- Use `cdklocal diff` to review what changes will be applied before deploying

---

## CloudFormation

### Deploy with awslocal

```bash
# Create a new stack
awslocal cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

# Wait for stack creation to complete
awslocal cloudformation wait stack-create-complete \
  --stack-name my-stack

# Update an existing stack
awslocal cloudformation update-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM

# Describe a stack and its outputs
awslocal cloudformation describe-stacks --stack-name my-stack | jq '.Stacks[0].Outputs'

# List all stack resources
awslocal cloudformation list-stack-resources --stack-name my-stack

# Delete a stack
awslocal cloudformation delete-stack --stack-name my-stack
```

### CloudFormation Best Practices for LocalStack

- Use `--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM` when templates create IAM resources
- Always `describe-stacks` after deployment to confirm stack status and retrieve outputs
- Use `wait` commands to ensure operations complete before proceeding

---

## Pulumi

### Using pulumilocal (PREFERRED)

```bash
# Install once
pip install pulumi-local

# Use exactly like pulumi — no config changes needed
pulumilocal preview
pulumilocal up --yes
pulumilocal destroy --yes
```

### Manual Configuration (FALLBACK ONLY)

```bash
# Configure Pulumi to target LocalStack
pulumi config set aws:accessKey test
pulumi config set aws:secretKey test
pulumi config set aws:region us-east-1
pulumi config set aws:skipCredentialsValidation true
pulumi config set aws:skipRequestingAccountId true
pulumi config set aws:s3UsePathStyle true
pulumi config set aws:endpoints '[{"s3":"http://localhost:4566","dynamodb":"http://localhost:4566","lambda":"http://localhost:4566"}]'
```

---

## General IaC Workflow with LocalStack

### Recommended Development Loop

1. **Start LocalStack with persistence**:
   ```bash
   PERSISTENCE=1 localstack start -d
   ```

2. **Deploy your infrastructure**:
   ```bash
   tflocal apply -auto-approve
   # or
   cdklocal deploy --all --require-approval never
   ```

3. **Verify resources were created**:
   ```bash
   awslocal s3 ls
   awslocal dynamodb list-tables
   awslocal lambda list-functions
   ```

4. **Run your application or tests** against LocalStack.

5. **Save state as a Cloud Pod** if you want to share it:
   ```bash
   localstack pod save my-feature-state
   ```

6. **Iterate**: Make changes and re-deploy.

7. **Clean up when done**:
   ```bash
   tflocal destroy -auto-approve
   # or
   cdklocal destroy --all --force
   ```

### Troubleshooting Deployments

- **Deployment fails immediately**: Check `localstack status` — LocalStack may not be running
- **Resources not created**: Review `localstack logs | grep -i error` for service-level errors
- **IAM errors with `ENFORCE_IAM=1`**: Switch to `ENFORCE_IAM=soft` to discover required permissions
- **CDK bootstrap errors**: Run `cdklocal bootstrap` before deploying for the first time
- **Terraform state issues**: The `tflocal` wrapper stores state locally; ensure it isn't referencing stale remote state
