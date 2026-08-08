# SAM Project Initialization

## Creating New Projects

Use `sam init` to bootstrap new serverless applications:

```bash
sam init --runtime python3.13 --name hello-serverless --app-template hello-world --dependency-manager pip --no-interactive

```

### Recommended Runtimes
- **Python**: python3.13, python3.12
- **Node.js**: nodejs22.x, nodejs20.x
- **Java**: java21, java17
- **.NET**: dotnet8

### Common Templates
- `hello-world` - Basic Lambda function with API Gateway
- `quick-start-web` - Web backend with API Gateway
- `step-functions-sample-app` - Step Functions workflow
- `eventbridge-schema-app` - EventBridge integration

## Project Structure

Standard SAM project layout:
```
my-app/
├── template.yaml          # SAM template
├── samconfig.toml        # SAM CLI configuration
├── src/                  # Function code
│   └── handler.py
├── events/               # Test events
│   └── event.json
└── tests/                # Unit tests
```

## Template.yaml Best Practices

### Use SAM Transform
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: My serverless application
```

### Define Globals for Common Settings
```yaml
Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.13
    Tracing: Active
    Environment:
      Variables:
        LOG_LEVEL: INFO
```

### Use Parameters for Configuration
```yaml
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
```

## Naming Conventions
- Use descriptive, kebab-case names for resources
- Prefix resources with application name
- Include environment in resource names for multi-stage deployments
