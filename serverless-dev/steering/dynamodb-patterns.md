# DynamoDB Integration Patterns

## Table Definition in SAM

```yaml
MyTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub ${AWS::StackName}-items
    BillingMode: PAY_PER_REQUEST  # On-demand pricing
    AttributeDefinitions:
      - AttributeName: PK
        AttributeType: S
      - AttributeName: SK
        AttributeType: S
      - AttributeName: GSI1PK
        AttributeType: S
    KeySchema:
      - AttributeName: PK
        KeyType: HASH
      - AttributeName: SK
        KeyType: RANGE
    GlobalSecondaryIndexes:
      - IndexName: GSI1
        KeySchema:
          - AttributeName: GSI1PK
            KeyType: HASH
          - AttributeName: SK
            KeyType: RANGE
        Projection:
          ProjectionType: ALL
    StreamSpecification:
      StreamViewType: NEW_AND_OLD_IMAGES
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true
```

## Granting Permissions

```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref MyTable
```

## Python SDK Usage

```python
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

# Put Item
table.put_item(
    Item={
        'PK': f'USER#{user_id}',
        'SK': f'PROFILE#{user_id}',
        'name': 'John Doe',
        'email': 'john@example.com'
    }
)

# Get Item
response = table.get_item(
    Key={
        'PK': f'USER#{user_id}',
        'SK': f'PROFILE#{user_id}'
    }
)
item = response.get('Item')

# Query
response = table.query(
    KeyConditionExpression=Key('PK').eq(f'USER#{user_id}')
)
items = response['Items']

# Update Item
table.update_item(
    Key={'PK': pk, 'SK': sk},
    UpdateExpression='SET #name = :name',
    ExpressionAttributeNames={'#name': 'name'},
    ExpressionAttributeValues={':name': 'Jane Doe'}
)

# Delete Item
table.delete_item(
    Key={'PK': pk, 'SK': sk}
)
```

## Single-Table Design

Use composite keys for multiple entity types:

```python
# User entity
PK: USER#123
SK: PROFILE#123

# Order entity
PK: USER#123
SK: ORDER#456

# Product entity
PK: PRODUCT#789
SK: METADATA#789
```

## Access Patterns

### Query by Partition Key
```python
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123')
)
```

### Query with Sort Key Condition
```python
response = table.query(
    KeyConditionExpression=Key('PK').eq('USER#123') & Key('SK').begins_with('ORDER#')
)
```

### Query GSI
```python
response = table.query(
    IndexName='GSI1',
    KeyConditionExpression=Key('GSI1PK').eq('STATUS#PENDING')
)
```

### Scan (Avoid in Production)
```python
response = table.scan(
    FilterExpression=Attr('status').eq('active')
)
```

## Best Practices

### Key Design
- Use meaningful prefixes (USER#, ORDER#, PRODUCT#)
- Design keys to support access patterns
- Avoid hot partitions

### Attributes
- Use sparse indexes for optional attributes
- Store related data together (denormalization)
- Use DynamoDB Streams for change data capture

### Performance
- Use BatchGetItem and BatchWriteItem for bulk operations
- Enable DAX for read-heavy workloads
- Use projection expressions to fetch only needed attributes

### Cost Optimization
- Use on-demand billing for unpredictable workloads
- Use provisioned capacity with auto-scaling for predictable workloads
- Archive old data to S3

## Transactions

```python
dynamodb_client = boto3.client('dynamodb')

dynamodb_client.transact_write_items(
    TransactItems=[
        {
            'Put': {
                'TableName': table_name,
                'Item': {'PK': {'S': 'USER#123'}, 'balance': {'N': '100'}}
            }
        },
        {
            'Update': {
                'TableName': table_name,
                'Key': {'PK': {'S': 'ACCOUNT#456'}},
                'UpdateExpression': 'SET balance = balance - :amount',
                'ExpressionAttributeValues': {':amount': {'N': '100'}}
            }
        }
    ]
)
```

## Error Handling

```python
from botocore.exceptions import ClientError

try:
    table.put_item(Item=item)
except ClientError as e:
    if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
        # Handle condition failure
        pass
    elif e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
        # Handle throttling
        pass
```
