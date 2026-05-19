# Security and IAM Best Practices

## SAM Policy Templates

Use built-in policy templates for common permissions:

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      # DynamoDB
      - DynamoDBCrudPolicy:
          TableName: !Ref MyTable
      - DynamoDBReadPolicy:
          TableName: !Ref MyTable
      
      # S3
      - S3ReadPolicy:
          BucketName: !Ref MyBucket
      - S3CrudPolicy:
          BucketName: !Ref MyBucket
      
      # SQS
      - SQSSendMessagePolicy:
          QueueName: !GetAtt MyQueue.QueueName
      - SQSPollerPolicy:
          QueueName: !GetAtt MyQueue.QueueName
      
      # SNS
      - SNSPublishMessagePolicy:
          TopicName: !GetAtt MyTopic.TopicName
      
      # Secrets Manager
      - AWSSecretsManagerGetSecretValuePolicy:
          SecretArn: !Ref MySecret
      
      # CloudWatch Logs
      - CloudWatchPutMetricPolicy: {}
```

## Custom IAM Policies

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      - Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - dynamodb:GetItem
              - dynamodb:PutItem
            Resource: !GetAtt MyTable.Arn
          - Effect: Allow
            Action:
              - s3:GetObject
            Resource: !Sub '${MyBucket.Arn}/*'
```

## Least Privilege Principle

### Scope Permissions to Specific Resources
```yaml
Policies:
  - Statement:
      - Effect: Allow
        Action: dynamodb:GetItem
        Resource: !Sub 'arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/MyTable'
```

### Use Conditions
```yaml
Policies:
  - Statement:
      - Effect: Allow
        Action: s3:GetObject
        Resource: !Sub '${MyBucket.Arn}/*'
        Condition:
          StringLike:
            s3:prefix: 'public/*'
```

## Secrets Management

### AWS Secrets Manager
```yaml
MySecret:
  Type: AWS::SecretsManager::Secret
  Properties:
    SecretString: !Sub |
      {
        "api_key": "${ApiKey}",
        "db_password": "${DBPassword}"
      }

MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Environment:
      Variables:
        SECRET_ARN: !Ref MySecret
    Policies:
      - AWSSecretsManagerGetSecretValuePolicy:
          SecretArn: !Ref MySecret
```

Retrieve in code:
```python
import boto3
import json

secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId=os.environ['SECRET_ARN'])
secret = json.loads(response['SecretString'])
api_key = secret['api_key']
```

### Parameter Store
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Environment:
      Variables:
        PARAM_NAME: /myapp/config/api-key
    Policies:
      - SSMParameterReadPolicy:
          ParameterName: myapp/config/*
```

## API Gateway Security

### API Keys
```yaml
ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    Auth:
      ApiKeyRequired: true

ApiKey:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Enabled: true

UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    ApiStages:
      - ApiId: !Ref ServerlessRestApi
        Stage: Prod
```

### Cognito Authorizer
```yaml
UserPool:
  Type: AWS::Cognito::UserPool

ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    Auth:
      DefaultAuthorizer: CognitoAuth
      Authorizers:
        CognitoAuth:
          UserPoolArn: !GetAtt UserPool.Arn
```

### Lambda Authorizer
```yaml
AuthFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: authorizer/
    Handler: app.handler

ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    Auth:
      DefaultAuthorizer: LambdaAuth
      Authorizers:
        LambdaAuth:
          FunctionArn: !GetAtt AuthFunction.Arn
```

## Resource Policies

### S3 Bucket Policy
```yaml
MyBucket:
  Type: AWS::S3::Bucket

BucketPolicy:
  Type: AWS::S3::BucketPolicy
  Properties:
    Bucket: !Ref MyBucket
    PolicyDocument:
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: s3:GetObject
          Resource: !Sub '${MyBucket.Arn}/*'
```

## Encryption

### Enable Encryption at Rest
```yaml
MyTable:
  Type: AWS::DynamoDB::Table
  Properties:
    SSESpecification:
      SSEEnabled: true
      SSEType: KMS
      KMSMasterKeyId: !Ref MyKMSKey

MyBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256
```

## VPC Configuration

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    VpcConfig:
      SecurityGroupIds:
        - !Ref LambdaSecurityGroup
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
```

## Security Checklist

- [ ] Use SAM policy templates for common permissions
- [ ] Apply least privilege to all IAM policies
- [ ] Store secrets in Secrets Manager or Parameter Store
- [ ] Enable encryption at rest for all data stores
- [ ] Use API Gateway authorizers for authentication
- [ ] Enable AWS X-Ray for security monitoring
- [ ] Implement input validation in Lambda functions
- [ ] Use VPC for functions accessing private resources
- [ ] Enable CloudTrail for audit logging
- [ ] Regularly rotate credentials and secrets
