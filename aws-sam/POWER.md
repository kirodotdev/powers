---
name: "aws-sam"
displayName: "AWS SAM"
description: "An opinionated Kiro Power to aid development with AWS Serverless Application Model (SAM). Includes MCP tooling and common usage patterns."
keywords: ["aws", "sam", "serverless", "lambda", "cloudformation", "deployment"]
author: "AWS"
---

# AWS Serverless Application Model (SAM) Power

## Overview

## Onboarding

1. Install SAM CLI https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
2. Verify installation: `sam --version`
3. Optionally install docker or finch.

## Available Steering Files

This power includes the following steering files:

- **cloudformation** - General rules to follow when using AWS CloudFormation

## Available MCP Tools

- sam_init - Creates a new SAM App. **ALWAYS** follow the steps outlined below under "Create a new SAM Application"
- sam_build - Build SAM app
- sam_deploy - Deploy SAM app
- sam_logs - Fetch deployed SAM app logs
- sam_local_invoke - Locally invoke a Lambda function on the user machine

## Common Workflows

### Create a new SAM Application

1. **Initialize**:

- Ask the user what backend language should be used
- Use `sam_init` to create the base project structure. Example args below:

```
{
  "application_template": "hello-world",
  "architecture": "x86_64",
  "dependency_manager": "pip",
  "package_type": "Zip",
  "project_directory": "/Users/abc/git/myApp", # the current working directory
  "project_name": "my-serverless-app",
  "runtime": "python3.13"
}
```

2. **Restructure**: Immediately reorganize files to follow the recommended structure:

**If sam_init created a subdirectory (project_name != current directory):**

- Move all files from the generated subdirectory to the repository root:
  ```
  mv {project_name}/* .
  mv {project_name}/.gitignore . 2>/dev/null || true
  rmdir {project_name}
  ```

**Always perform these restructuring steps:**

- Create the proper infrastructure directory:
  ```
  mkdir -p infrastructure/lambda
  ```
- Move the generated function folder to the infrastructure directory:
  ```
  mv {generated_function_folder} infrastructure/lambda/{function_name}
  ```
- Update `CodeUri` paths in template.yaml to point to new locations:
  - Change from: `CodeUri: {generated_function_folder}/`
  - Change to: `CodeUri: infrastructure/lambda/{function_name}/`
- Rebuild the application to verify structure with the `sam_build` tool
- Add `.aws-sam` to `.gitignore`

**DO NOT**:

- Add additional resources to achieve a comprehensive solution, unless explicitly asked to.
- Make assumptions about what the user wants beyond basic SAM initialization

#### Adding an API

When adding APIs to SAM applications:

- **ALWAYS** create a new AWS::Serverless::Function for each API or logical grouping of endpoints
- **NEVER** modify existing Lambda functions when asked to add a new API
- **ALWAYS** create separate Lambda functions in `infrastructure/lambda/[function-name]/` directories

### Set up a static website with API backend

- Add an S3 bucket for hosting the static site

```
  WebUIBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
```

- Add an API Gateway API (HTTP or REST), example:

```
  ApiGatewayApi:
    Type: AWS::Serverless::Api
    Properties:
      AccessLogSetting:
        DestinationArn: !GetAtt ApiGWLogGroup.Arn
        Format: "$context.identity.sourceIp $context.requestTime $context.httpMethod $context.resourcePath $context.protocol $context.status $context.responseLength $context.requestId"
      StageName: !Ref Stage
      EndpointConfiguration: REGIONAL
      Auth:
        ApiKeyRequired: "true"
```

- Add an `AWS::CloudFront::OriginAccessControl` resource
- Add a CloudFront Distribution with origins for the static site and API:

```
  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
          - Id: S3
            DomainName: !GetAtt UIBucket.RegionalDomainName
            OriginAccessControlId: !Ref CloudFrontOriginAccessControl
            S3OriginConfig: {}
          - Id: api
            DomainName: !Sub "${ApiGatewayApi}.execute-api.${AWS::Region}.amazonaws.com"
            OriginPath: !Sub "/${Stage}"
            CustomOriginConfig:
              HTTPSPort: 443
              OriginProtocolPolicy: https-only
              OriginSSLProtocols:
                - TLSv1.2
        DefaultRootObject: index.html
        PriceClass: PriceClass_100
        Enabled: true
        DefaultCacheBehavior:
          AllowedMethods:
            - GET
            - HEAD
            - OPTIONS
          CachedMethods:
            - GET
            - HEAD
          Compress: true
          ForwardedValues:
            Cookies:
              Forward: none
            QueryString: true
          TargetOriginId: S3
          ViewerProtocolPolicy: redirect-to-https
          ResponseHeadersPolicyId: !Ref ResponseHeadersPolicy
        CacheBehaviors:
          - AllowedMethods:
              - GET
              - HEAD
              - OPTIONS
              - PUT
              - POST
              - PATCH
              - DELETE
            CachedMethods:
              - HEAD
              - GET
              - OPTIONS
            Compress: false
            PathPattern: '/api/*'
            TargetOriginId: api
            CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad # Managed: CachingDisabled
            OriginRequestPolicyId: b689b0a8-53d0-40ab-baf2-68738e2966ac # Managed: AllViewerExceptHostHeader
            ViewerProtocolPolicy: redirect-to-https
            ResponseHeadersPolicyId: !Ref ResponseHeadersPolicy
        HttpVersion: http2
        IPV6Enabled: true
```

- Add an S3 bucket policy for CloudFront usage:

```
  WebUIBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref WebUIBucket
      PolicyDocument:
        Statement:
          - Sid: HttpsOnly
            Action: "*"
            Effect: Deny
            Resource:
              - !Sub arn:${AWS::Partition}:s3:::${WebUIBucket}
              - !Sub arn:${AWS::Partition}:s3:::${WebUIBucket}/*
            Principal: "*"
            Condition:
              Bool:
                "aws:SecureTransport": "false"
          - Sid: CloudFrontOriginOnly
            Action: s3:GetObject
            Effect: Allow
            Resource: !Sub arn:${AWS::Partition}:s3:::${WebUIBucket}/*
            Principal:
              Service: "cloudfront.amazonaws.com"
            Condition:
              ArnEquals:
                aws:SourceArn: !Sub arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontDistribution}
```

- Add a AWS::Serverless::Function as an API Handler

```
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: app.lambda_handler
      CodeUri: infrastructure/lambda/api
      Description: API function
      Timeout: 5
      Architectures:
        - x86_64
      Environment:
        Variables:
          POWERTOOLS_SERVICE_NAME: MyService
          POWERTOOLS_METRICS_NAMESPACE: MyService
      Events:
        AnyPath:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
            RestApiId: !Ref ApiGatewayApi
```

- Create the Lambda function code using the Powertools for AWS Lambda library and the REST API handler

### Enable CORS on an API

- Add a parameter so a user deploying can set the CORS policy:

```
Parameters:
  AccessControlAllowOriginOverride:
    Type: String
    Default: ""
    Description: Optional override for the CORS policy. Leave blank to scope CORS to the CloudFront distribution
```

- Add a condition based on the parameter:

```
Conditions:
  DefaultAccessControlOrigin:
    !Equals [!Ref AccessControlAllowOriginOverride, ""]
```

- Add CORS configuration to AWS::Serverless::Api resource:

```
  ApiGatewayApi:
    Type: AWS::Serverless::Api
    Properties:
      Cors:
        AllowMethods: "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
        AllowHeaders: "'Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers'"
        AllowOrigin: !If
          - DefaultAccessControlOrigin
          - !Sub "'https://${CloudFrontDistribution.DomainName}'"
          - !Sub "'${AccessControlAllowOriginOverride}'"
      GatewayResponses:
        DEFAULT_4XX:
          ResponseTemplates:
            "application/json": '{ "Message": $context.error.messageString }'
          ResponseParameters:
            Headers:
              Access-Control-Allow-Methods: "'*'"
              Access-Control-Allow-Headers: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
              Access-Control-Allow-Origin: !If
                - DefaultAccessControlOrigin
                - !Sub "'https://${CloudFrontDistribution.DomainName}'"
                - !Sub "'${AccessControlAllowOriginOverride}'"
        DEFAULT_5XX:
          ResponseTemplates:
            "application/json": '{ "Message": $context.error.messageString }'
          ResponseParameters:
            Headers:
              Access-Control-Allow-Methods: "'*'"
              Access-Control-Allow-Headers: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
              Access-Control-Allow-Origin: !If
                - DefaultAccessControlOrigin
                - !Sub "'https://${CloudFrontDistribution.DomainName}'"
                - !Sub "'${AccessControlAllowOriginOverride}'"
```

- Configure the Lambda function with CORS:

```
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig

cors_config = CORSConfig(max_age=300)
app = APIGatewayRestResolver(cors=cors_config)
```

**NEVER** add additional CORS configuration unless explicitly asked to

### Use amplify and Cognito for web app authentication

- Add a parameter for a default admin user:

```
Parameters:
  DefaultUserEmail:
    Type: String
    Default: ""
    Description: Optional email for the default admin user. Leave blank to skip creation
```

- Create a condition based on the admin user parameter:

```
Conditions:
  CreateUser: !Not [!Equals [!Ref DefaultUserEmail, ""]]
```

- Create cognito resources

```
Resources:
  UserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      AdminCreateUserConfig:
        InviteMessageTemplate:
          EmailMessage: "Your username is {username} and the temporary password is {####}"
          EmailSubject: "Your temporary password"
      AutoVerifiedAttributes:
        - email
      UserPoolAddOns:
        AdvancedSecurityMode: !Ref CognitoAdvancedSecurity
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: true
          RequireUppercase: true

  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref UserPool
      SupportedIdentityProviders:
        - COGNITO

  CognitoUserPoolAdmin:
    Condition: CreateUser
    Type: AWS::Cognito::UserPoolUser
    Properties:
      Username: admin
      DesiredDeliveryMediums:
        - EMAIL
      UserPoolId: !Ref UserPool
      UserAttributes:
        - Name: email
          Value: !Ref DefaultUserEmail
        - Name: email_verified
          Value: "True"

  IdentityPool:
    Type: "AWS::Cognito::IdentityPool"
    Properties:
      IdentityPoolName: !Sub vca-${Stage}
      AllowUnauthenticatedIdentities: false
      CognitoIdentityProviders:
        - ClientId: !Ref UserPoolClient
          ProviderName: !GetAtt UserPool.ProviderName

  CognitoAuthorizedRole:
    Type: "AWS::IAM::Role"
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: "Allow"
            Principal:
              Federated: "cognito-identity.amazonaws.com"
            Action:
              - "sts:AssumeRoleWithWebIdentity"
            Condition:
              StringEquals:
                "cognito-identity.amazonaws.com:aud": !Ref IdentityPool
              ForAnyValue:StringLike:
                "cognito-identity.amazonaws.com:amr": authenticated

  IdentityPoolRoleMapping:
    Type: "AWS::Cognito::IdentityPoolRoleAttachment"
    Properties:
      IdentityPoolId: !Ref IdentityPool
      Roles:
        authenticated: !GetAtt CognitoAuthorizedRole.Arn
```

- Update the API with Cognito configuration:

```
Resources:
  ApiGatewayApi:
    Type: AWS::Serverless::Api
    Properties:
      Auth:
        AddDefaultAuthorizerToCorsPreflight: false
        DefaultAuthorizer: Cognito
        Authorizers:
          Cognito:
            UserPoolArn: !GetAtt UserPool.Arn
```

- Add appropriate outputs:

```
Outputs:
  CognitoUserPoolID:
    Description: The UserPool ID
    Value: !Ref UserPool
  CognitoWebClientID:
    Description: The web client ID
    Value: !Ref UserPoolClient
  CognitoIdentityPoolID:
    Description: The IdentityPool ID
    Value: !Ref IdentityPool
```

## Best Practices

### Recommended Project Structure

The following structure should be used, with a main `template.yaml` at the repository root, and any other stacks and code defined within `infrastructure`.

```
├── infrastructure
│   ├── cloudformation
│   │   └── monitoring.yaml
│   └── lambda
│       └── api
│           ├── app.py
│           └── requirements.txt  # or pyproject.toml for uv
└── template.yaml
```

### Template Structure

- **ALWAYS** use AWS SAM (Serverless Application Model) for serverless applications
- Use the transform `Transform: AWS::Serverless-2016-10-31` in all templates which leverage SAM

### Using SAM Resource Types

**ALWAYS** use AWS SAM (Serverless Application Model) resource types for the following resources:

- Lambda Function --> AWS::Serverless::Function
- Lambda Layer --> AWS::Serverless::LayerVersion
- API Gateway REST API --> AWS::Serverless::Api
- API Gateway HTTP API --> AWS::Serverless::HttpApi
- AppSync GraphQL API --> AWS::Serverless::GraphQLApi
- Step Functions State Machine --> AWS::Serverless::StateMachine

### Lambda Powertools

**ALWAYS** use the Powertools for AWS Lambda library when creating functions in Python, Java, TypeScript or .NET.

**CRITICAL**: Use Lambda Layers for Powertools, **NEVER** add Powertools to your dependency file. Query the relevant documentation to get the latest version for a language.

Documentation:

- Python: https://docs.aws.amazon.com/powertools/python/latest/
- TypeScript: https://docs.aws.amazon.com/powertools/typescript/latest/
- Java: https://docs.aws.amazon.com/powertools/java/latest/
- .NET: https://docs.aws.amazon.com/powertools/dotnet/

### Dependency Management Guidelines

**ALWAYS** use version locking when adding dependencies. For example, in Python:

```
# requirements.txt (pip)
# GOOD - Version locked
requests==2.31.0

# Bad - No version locking
requests
```

```
# pyproject.toml (uv)
# GOOD - Version locked
[project]
dependencies = [
    "requests==2.31.0",
]

# BAD - Version locked
[project]
dependencies = [
    "requests",
]
```

**DO NOT** add these to your dependency file (use layers instead):

- `aws-lambda-powertools` (use layer)
- `boto3` (included in Lambda runtime)
- `botocore` (included in Lambda runtime)

### Security

When defining a Lambda Function or Step Functions State Machine, prefer [AWS SAM policy templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-policy-templates.html) for defining IAM permissions.
However, revert to plain IAM statements where required to ensure only minimal permissions are granted.

#### Globals

- Define `Globals` section for common Lambda and API Gateway configurations, e.g.

```
Globals:
  Function:
    MemorySize: 512
    Runtime: python3.13
    Tracing: Active
    Layers:
      - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:18
  Api:
    TracingEnabled: true
```

## Troubleshooting

### MCP Server Connection Issues

**Problem**: MCP server won't start or connect

**Symptoms**:

- Error: "Connection refused"
- Server not responding
- Tools not available

**Solutions**:

1. Verify uv is installed: `uv --version`
2. Check Python version: `python --version` (must be 3.10+)
3. Verify AWS credentials: `aws sts get-caller-identity`
4. Check mcp.json configuration for correct AWS_PROFILE and AWS_REGION
5. Review Kiro logs for specific error messages
6. Restart Kiro and reconnect the MCP server

### SAM CLI Errors

**Error**: "Template validation failed"
**Cause**: Invalid SAM template syntax
**Solution**:

1. Validate template: `sam validate --lint --template template.yaml`
2. Check YAML syntax and indentation
3. Ensure required properties are present
4. Review sam and cloudformation steering files for best practices

**Error**: "Unable to upload artifact"
**Cause**: S3 bucket doesn't exist or no permissions
**Solution**:

1. Use `resolve_s3: true` in sam_deploy to auto-create bucket
2. Or manually create S3 bucket: `aws s3 mb s3://my-deployment-bucket`
3. Verify IAM permissions for S3 access

### Deployment Failures

**Error**: "Stack creation failed"
**Cause**: CloudFormation stack creation error
**Solution**:

1. Check CloudFormation console for detailed error
2. Review stack events: `aws cloudformation describe-stack-events --stack-name my-app`
3. Common causes:
   - IAM permission issues (add CAPABILITY_IAM)
   - Resource name conflicts (use unique names)
   - Invalid parameter values
   - Service limits exceeded

**Error**: "Insufficient permissions"
**Cause**: IAM user/role lacks required permissions
**Solution**:

1. Ensure IAM user has CloudFormation, Lambda, S3, and IAM permissions
2. Add `capabilities: ["CAPABILITY_IAM"]` to sam_deploy
3. Review AWS IAM policies and attach necessary permissions

### Local Invoke Issues

**Error**: "Function not found"
**Cause**: Resource name doesn't match template
**Solution**:

1. Check logical ID in template.yaml
2. Ensure you've run sam_build before sam_local_invoke
3. Verify resource_name matches exactly (case-sensitive)

**Error**: "Event parsing failed"
**Cause**: Invalid event JSON format
**Solution**:

1. Validate JSON syntax
2. Use get_lambda_event_schemas to get correct event structure
3. Test with simple event first: `{"key": "value"}`

## Validation & Compliance

Your SAM applications should follow the security and operational standards defined in the CloudFormation Guidelines document.

### Pre-Deployment Validation Workflow

1. **Static Validation**: Run `sam validate` to check template syntax
2. **Security Validation**: Ensure compliance with CloudFormation Guidelines security standards
3. **Pre-Deployment Check**: Create a change set to validate against your AWS account
4. **Deploy**: Only after all validations pass

See the CloudFormation Guidelines document for detailed security, monitoring, and operational requirements.

---

This power integrates with [`awslabs.aws-serverless-mcp-server@latest`](https://github.com/awslabs/mcp/tree/main/src/aws-serverless-mcp-server) | Apache-2.0 license.

