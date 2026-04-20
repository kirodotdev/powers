# SAM Build and Deploy Workflow

## Building Applications

### Basic Build
```bash
sam build
```

### Build with Container (Recommended for Dependencies)
```bash
sam build --use-container
```

### Build Specific Function
```bash
sam build MyFunction
```

## Deployment

### Guided Deployment (First Time)
```bash
sam deploy --guided
```

This creates `samconfig.toml` with deployment settings.

### Subsequent Deployments
```bash
sam deploy
```

### Deploy to Specific Environment
```bash
sam deploy --config-env prod
```

## samconfig.toml Structure

```toml
version = 0.1

[default.deploy.parameters]
stack_name = "my-app"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket"
s3_prefix = "my-app"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Environment=dev"

[prod.deploy.parameters]
stack_name = "my-app-prod"
region = "us-east-1"
capabilities = "CAPABILITY_IAM"
parameter_overrides = "Environment=prod"
```

## Deployment Best Practices

### Use Stack Outputs
```yaml
Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/"
  FunctionArn:
    Description: Lambda Function ARN
    Value: !GetAtt MyFunction.Arn
```

### Enable Rollback Configuration
```yaml
DeploymentPreference:
  Type: Canary10Percent5Minutes
  Alarms:
    - !Ref CanaryErrorsAlarm
```

### Tag Resources
```yaml
Tags:
  Environment: !Ref Environment
  Application: my-app
  ManagedBy: SAM
```

## Validation Before Deploy

Always validate template:
```bash
sam validate
```

## Cleanup

Delete stack when no longer needed:
```bash
sam delete
```
