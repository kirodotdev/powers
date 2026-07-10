# API Gateway Patterns

## REST API with SAM

```yaml
ServerlessRestApi:
  Type: AWS::Serverless::Api
  Properties:
    StageName: Prod
    Cors:
      AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
      AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"
      AllowOrigin: "'*'"
    Auth:
      DefaultAuthorizer: MyCognitoAuthorizer
      Authorizers:
        MyCognitoAuthorizer:
          UserPoolArn: !GetAtt UserPool.Arn

GetItemFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      GetItem:
        Type: Api
        Properties:
          RestApiId: !Ref ServerlessRestApi
          Path: /items/{id}
          Method: get
```

## HTTP API (Recommended for Lower Cost)

```yaml
HttpApi:
  Type: AWS::Serverless::HttpApi
  Properties:
    CorsConfiguration:
      AllowOrigins:
        - "*"
      AllowMethods:
        - GET
        - POST
      AllowHeaders:
        - Content-Type

MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      HttpApiEvent:
        Type: HttpApi
        Properties:
          ApiId: !Ref HttpApi
          Path: /items
          Method: get
```

## Request/Response Patterns

### Lambda Proxy Integration (Default)
Function receives full request and returns formatted response:

```python
def lambda_handler(event, context):
    # event contains: httpMethod, path, queryStringParameters, headers, body
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Success'})
    }
```

### Path Parameters
```yaml
Events:
  GetItem:
    Type: Api
    Properties:
      Path: /items/{id}
      Method: get
```

Access in handler:
```python
item_id = event['pathParameters']['id']
```

### Query Parameters
```python
query_params = event.get('queryStringParameters', {})
limit = query_params.get('limit', '10')
```

## Authentication

### Cognito Authorizer
```yaml
Auth:
  DefaultAuthorizer: MyCognitoAuth
  Authorizers:
    MyCognitoAuth:
      UserPoolArn: !GetAtt UserPool.Arn
```

### Lambda Authorizer
```yaml
Auth:
  DefaultAuthorizer: MyLambdaAuth
  Authorizers:
    MyLambdaAuth:
      FunctionArn: !GetAtt AuthFunction.Arn
      Identity:
        Headers:
          - Authorization
```

## API Gateway Best Practices

### Enable Throttling
```yaml
MethodSettings:
  - ResourcePath: "/*"
    HttpMethod: "*"
    ThrottlingBurstLimit: 100
    ThrottlingRateLimit: 50
```

### Enable Caching (REST API only)
```yaml
MethodSettings:
  - ResourcePath: "/*"
    HttpMethod: "GET"
    CachingEnabled: true
    CacheTtlInSeconds: 300
```

### Request Validation
```yaml
RequestValidator:
  Type: AWS::ApiGateway::RequestValidator
  Properties:
    RestApiId: !Ref ServerlessRestApi
    ValidateRequestBody: true
    ValidateRequestParameters: true
```

### API Keys and Usage Plans
```yaml
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
    Throttle:
      RateLimit: 100
      BurstLimit: 200
```

## Error Handling

Return proper HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error
