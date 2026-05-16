# Bedrock Knowledge Bases (RAG)

## Overview

Bedrock Knowledge Bases implement Retrieval-Augmented Generation (RAG) — index your data, retrieve relevant context, and generate grounded responses with citations.

Use Knowledge Bases when you need:
- Question answering over enterprise documents
- Grounded responses with source citations
- Semantic search across large document collections
- RAG pipelines without managing vector infrastructure

## Clients

```python
import boto3

# Build-time: create and manage KB
bedrock_agent = boto3.client("bedrock-agent", region_name="us-east-1")

# Runtime: query KB
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
```

## Create a Knowledge Base

### Step 1: Create the Knowledge Base

```python
kb = bedrock_agent.create_knowledge_base(
    name="company-docs",
    roleArn="arn:aws:iam::ACCOUNT:role/BedrockKBRole",
    knowledgeBaseConfiguration={
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
            "embeddingModelConfiguration": {
                "bedrockEmbeddingModelConfiguration": {
                    "dimensions": 1024,
                    "embeddingDataType": "FLOAT32",
                }
            },
        },
    },
    storageConfiguration={
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": "arn:aws:aoss:us-east-1:ACCOUNT:collection/COLLECTION_ID",
            "vectorIndexName": "bedrock-knowledge-base-index",
            "fieldMapping": {
                "vectorField": "embedding",
                "textField": "text",
                "metadataField": "metadata",
            },
        },
    },
)
kb_id = kb["knowledgeBase"]["knowledgeBaseId"]
```

### Step 2: Add a Data Source

```python
ds = bedrock_agent.create_data_source(
    knowledgeBaseId=kb_id,
    name="s3-documents",
    dataSourceConfiguration={
        "type": "S3",
        "s3Configuration": {
            "bucketArn": "arn:aws:s3:::my-documents-bucket",
            "inclusionPrefixes": ["docs/"],
        },
    },
    vectorIngestionConfiguration={
        "chunkingConfiguration": {
            "chunkingStrategy": "SEMANTIC",
            "semanticChunkingConfiguration": {
                "maxTokens": 300,
                "bufferSize": 0,
                "breakpointPercentileThreshold": 95,
            },
        }
    },
)
ds_id = ds["dataSource"]["dataSourceId"]
```

### Step 3: Sync Data

```python
bedrock_agent.start_ingestion_job(
    knowledgeBaseId=kb_id,
    dataSourceId=ds_id,
)
```

**Important**: You must manually sync after creating a data source or updating documents. Syncing is NOT automatic.

## Vector Store Options

| Store | Best For | Notes |
|-------|----------|-------|
| OpenSearch Serverless | Most use cases, Confluence/SharePoint/Salesforce connectors | 2 OCUs minimum (~$345/month) |
| Aurora PostgreSQL Serverless | Already using Aurora, want SQL access | pgvector extension |
| Neptune Analytics | Graph + vector hybrid queries | Knowledge graph use cases |
| Amazon S3 Vectors | Simple, low-cost, no server management | New — zero infrastructure |

## Data Source Types

| Source | Configuration Key | Notes |
|--------|-------------------|-------|
| S3 | `s3Configuration` | Most common; supports all document formats |
| Web Crawler | `webConfiguration` | Crawl websites with configurable scope |
| Confluence | `confluenceConfiguration` | Requires OpenSearch Serverless |
| SharePoint | `sharePointConfiguration` | Requires OpenSearch Serverless |
| Salesforce | `salesforceConfiguration` | Requires OpenSearch Serverless |
| Custom | `customConfiguration` | Bring your own data pipeline |

## Supported Document Formats

| Format | Max Size | Extensions |
|--------|----------|------------|
| Text | 50 MB | .txt, .md, .html, .csv |
| Documents | 50 MB | .doc, .docx, .pdf, .pptx |
| Spreadsheets | 50 MB | .xls, .xlsx |
| Images (multimodal) | 3.75 MB | .jpeg, .png |

## Chunking Strategies

| Strategy | Use When |
|----------|----------|
| `FIXED_SIZE` | Simple documents, predictable chunks |
| `SEMANTIC` | Best quality — splits on meaning boundaries |
| `HIERARCHICAL` | Complex docs with sections/subsections |
| `NONE` | Documents already pre-chunked |

## Embedding Model Selection

| Model | Dimensions | Modality | Recommendation |
|-------|-----------|----------|----------------|
| Titan Text Embeddings V2 | 256/512/1024 | Text | Default for text-only |
| Cohere Embed v4 | 256-1024 | Text+Image | Best quality, CRIS support |
| Titan Multimodal Embeddings | 256/384/1024 | Text+Image | Multimodal documents |
| Nova Multimodal Embeddings | 256/512/1024 | Text+Image+Audio+Video | Full multimodal |

## Query Knowledge Base

### Retrieve Only (Get relevant chunks)

```python
response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId=kb_id,
    retrievalQuery={"text": "What is our refund policy?"},
    retrievalConfiguration={
        "vectorSearchConfiguration": {
            "numberOfResults": 5,
        }
    },
)

for result in response["retrievalResults"]:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']['text']}")
    print(f"Source: {result['location']}")
    print()
```

### Retrieve and Generate (RAG with answer)

```python
response = bedrock_agent_runtime.retrieve_and_generate(
    input={"text": "What is our refund policy?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": kb_id,
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-sonnet-4-6",
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                }
            },
        },
    },
)

print(response["output"]["text"])

# Citations
for citation in response.get("citations", []):
    for ref in citation.get("retrievedReferences", []):
        print(f"Source: {ref['location']}")
```

### Query via MCP Server

If using the power's MCP tools:

```
ListKnowledgeBases()
QueryKnowledgeBases(query="refund policy", knowledge_base_id="KB_ID", number_of_results=5)
```

## IAM Role for Knowledge Bases

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
        },
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::my-documents-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::my-documents-bucket"
        },
        {
            "Effect": "Allow",
            "Action": "aoss:APIAccessAll",
            "Resource": "arn:aws:aoss:us-east-1:ACCOUNT:collection/COLLECTION_ID"
        }
    ]
}
```

Trust policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock.amazonaws.com"},
        "Action": "sts:AssumeRole",
        "Condition": {
            "StringEquals": {"aws:SourceAccount": "ACCOUNT_ID"}
        }
    }]
}
```

## Best Practices

- **Use semantic chunking** for best retrieval quality
- **Sync data sources after every update** — ingestion is not automatic
- **Use metadata filters** to narrow search scope (reduce noise, improve relevance)
- **Start with Titan Text Embeddings V2** at 1024 dimensions — good balance of quality and cost
- **Test retrieval before building RAG** — use `retrieve()` first, then `retrieve_and_generate()`
- **Monitor OpenSearch Serverless OCU usage** — minimum 2 OCUs (~$345/month) even when idle
- **Tag knowledge bases with `mcp-multirag-kb=true`** if using the KB retrieval MCP server

## Troubleshooting

### No results returned
- Verify data source sync completed: check ingestion job status
- Ensure query is semantically relevant to indexed content
- Increase `numberOfResults` to check if results exist at all
- Check that the embedding model matches what was used during indexing

### Sync job fails
- Check IAM role has S3 GetObject/ListBucket permissions
- Verify S3 bucket and prefix exist
- Check document formats are supported (unsupported files silently skipped)
- Check CloudWatch logs for detailed errors

### High latency on queries
- Reduce `numberOfResults`
- Use metadata filters to narrow scope
- Consider enabling reranking for better precision (fewer results needed)

### OpenSearch Serverless costs
- Minimum 2 OCUs always running (~$345/month)
- Consider S3 Vectors for lower-cost use cases
- Delete unused collections when not needed
