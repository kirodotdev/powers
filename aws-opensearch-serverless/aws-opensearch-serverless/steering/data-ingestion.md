# Data Ingestion for OpenSearch Serverless

**IMPORTANT: All data ingestion must be performed directly via `call_aws`. NEVER write Python scripts, shell scripts, or any other code files to the user's workspace. Read user data files directly, transform data in your context, and execute `call_aws` to ingest.**

## How to Ingest User Data

Follow this process every time a user wants to load data:

### 1. Identify the Data Source

Ask the user where their data is, or look for data files in their workspace. Common locations:
- `data/`, `datasets/`, `sample-data/` directories
- Root directory CSV or JSON files
- Specific file the user mentions

### 2. Read the Data File

Read the file from the workspace. Supported formats:

**JSON Array:**
```json
[
  {"title": "Widget A", "price": 9.99},
  {"title": "Widget B", "price": 19.99}
]
```
Each array element is a document.

**NDJSON (one JSON object per line):**
```
{"title": "Widget A", "price": 9.99}
{"title": "Widget B", "price": 19.99}
```
Each line is a document.

**CSV:**
```
title,price,category
Widget A,9.99,gadgets
Widget B,19.99,gadgets
```
Use the header row as field names. Convert each data row to a JSON object. Cast numeric values to numbers where the index mapping expects float/integer types.

### 3. Build Bulk Payloads

Transform the data into NDJSON bulk format. For each document, create two lines:
1. Action line: `{"index": {"_index": "<index-name>", "_id": "<id>"}}`
2. Document line: the document as JSON

**Generate `_id` values** from:
- An existing ID field in the data (e.g., `id`, `product_id`, `sku`)
- Row number / sequential counter if no natural ID exists
- Omit `_id` to let OpenSearch auto-generate

### 4. Batch and Execute

Split documents into batches and execute `call_aws` for each batch:

- **Batch size:** 500-1000 documents per request (adjust down for large documents)
- **Max request size:** 10 MB per bulk request
- **Execute sequentially:** one `call_aws` per batch, wait for response before next batch

For each batch, execute:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/_bulk",
    "body": "{ \"index\": { \"_index\": \"<index-name>\", \"_id\": \"1\" } }\n{ \"title\": \"Widget A\", \"price\": 9.99, \"category\": \"gadgets\" }\n{ \"index\": { \"_index\": \"<index-name>\", \"_id\": \"2\" } }\n{ \"title\": \"Widget B\", \"price\": 19.99, \"category\": \"gadgets\" }\n"
  },
  "region": "<region>"
})
```

### 5. Check Responses and Report

After each bulk call, check the response:

```json
{
  "took": 30,
  "errors": false,
  "items": [
    { "index": { "_id": "1", "status": 201, "result": "created" } },
    { "index": { "_id": "2", "status": 201, "result": "created" } }
  ]
}
```

- If `errors: false` — all documents succeeded. Report count to user.
- If `errors: true` — find items with status >= 400, report the error details, and retry failed items in a new bulk call.

**Keep a running total** and tell the user: "Ingested N of M documents. Batch K of T complete."

## Single Document Indexing

For indexing individual documents:

### With Explicit ID

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_doc/<doc-id>",
    "body": {
      "title": "Wireless Headphones",
      "description": "Premium noise-canceling headphones",
      "price": 79.99,
      "category": "electronics"
    }
  },
  "region": "<region>"
})
```

### With Auto-Generated ID

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_doc",
    "body": {
      "title": "Wireless Headphones",
      "price": 79.99
    }
  },
  "region": "<region>"
})
```

### Update an Existing Document

Partial update (merge fields without replacing the entire document):

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_update/<doc-id>",
    "body": {
      "doc": {
        "price": 69.99,
        "on_sale": true
      }
    }
  },
  "region": "<region>"
})
```

## Bulk NDJSON Format Reference

Each bulk request is a sequence of action-document pairs in NDJSON format:

```
{"index": {"_index": "products", "_id": "1"}}
{"title": "Wireless Headphones", "price": 79.99, "category": "electronics"}
{"index": {"_index": "products", "_id": "2"}}
{"title": "USB-C Cable", "price": 12.99, "category": "accessories"}
```

**Formatting rules:**
- Each line is valid JSON.
- Lines separated by `\n`.
- **Body must end with `\n`.**
- No blank lines between entries.
- Maximum request size: 10 MB.

**Available actions:**

| Action | Behavior |
|--------|----------|
| `index` | Creates or replaces a document. |
| `create` | Creates only if `_id` doesn't exist. Fails otherwise. |
| `update` | Partial update. Body must contain `"doc": { ... }`. |
| `delete` | Deletes a document. No document line follows. |

## Data Type Conversion

When reading user data files, convert values to match the index mapping:

| Mapping Type | Conversion Rule |
|-------------|----------------|
| `text` | Keep as string |
| `keyword` | Keep as string |
| `integer` | Parse string to integer (e.g., `"42"` → `42`) |
| `float` | Parse string to float (e.g., `"9.99"` → `9.99`) |
| `boolean` | Convert `"true"`/`"false"`, `"yes"`/`"no"`, `"1"`/`"0"` to `true`/`false` |
| `date` | Keep as ISO 8601 string (e.g., `"2024-01-15T10:30:00Z"`) |
| `keyword` (array) | Split comma-separated strings into arrays if appropriate |
| `knn_vector` | Parse array of floats; verify dimension matches mapping |

**For CSV data specifically:**
- All CSV values are strings. Cast numeric columns to numbers.
- Empty CSV cells: omit the field or use `null`.
- Comma-containing values should be properly quoted in the CSV.

## Handling Nested / Hierarchical Data

**Objects:** If the data has nested objects, index them directly. OpenSearch maps them as `object` type by default:

```json
{
  "product_name": "Laptop",
  "specs": {
    "ram": "16GB",
    "storage": "512GB SSD"
  }
}
```

Query with dot notation: `specs.ram: "16GB"`.

**Arrays of objects:** If array elements need to be queried independently, the index mapping must use `nested` type. See `steering/index-design.md` for mapping guidance.

## Vector Data Ingestion

For VECTORSEARCH collections with pre-computed embeddings:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_doc/1",
    "body": {
      "text": "OpenSearch Serverless provides automatic scaling",
      "embedding": [0.123, -0.456, 0.789],
      "source": "documentation",
      "created_at": "2024-01-15T10:30:00Z"
    }
  },
  "region": "<region>"
})
```

The vector dimension must exactly match the `dimension` in the index mapping.

For bulk vector ingestion, follow the same bulk pattern above — include the `embedding` array in each document line.

## Ingest Pipelines

Ingest pipelines transform documents server-side before indexing. Create them via the data plane API.

### Create a Pipeline

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/_ingest/pipeline/<pipeline-name>",
    "body": {
      "description": "Pipeline description",
      "processors": [
        {
          "lowercase": {
            "field": "category"
          }
        },
        {
          "set": {
            "field": "indexed_at",
            "value": "{{_ingest.timestamp}}"
          }
        }
      ]
    }
  },
  "region": "<region>"
})
```

### Index with Pipeline

Add `?pipeline=<name>` to the path:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_doc/1?pipeline=<pipeline-name>",
    "body": {
      "title": "Widget",
      "category": "ELECTRONICS"
    }
  },
  "region": "<region>"
})
```

### Common Processors

| Processor | Use Case |
|-----------|----------|
| `set` | Add or overwrite a field with a static or dynamic value |
| `remove` | Remove fields from the document |
| `rename` | Rename a field |
| `convert` | Convert field types (string to integer, etc.) |
| `lowercase` | Lowercase a string field |
| `trim` | Remove leading/trailing whitespace |
| `date` | Parse date strings into date fields |
| `grok` | Parse unstructured text using patterns |
| `script` | Custom transformation using Painless script |
| `text_embedding` | Generate vector embeddings from text |
| `text_chunking` | Split long text into smaller chunks |

## Re-indexing

If you need to change index mappings (field types, analyzers), create a new index and re-index:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/_reindex",
    "body": {
      "source": { "index": "<old-index>" },
      "dest": { "index": "<new-index>" }
    }
  },
  "region": "<region>"
})
```

## Monitoring Ingestion

### Check Document Count

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_count",
    "body": {}
  },
  "region": "<region>"
})
```

### Verify a Specific Document

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "GET",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_doc/<doc-id>"
  },
  "region": "<region>"
})
```

## Common Ingestion Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `mapper_parsing_exception` | Document field doesn't match mapping type | Check field types; convert strings to numbers where needed |
| `illegal_argument_exception` for vectors | Vector dimension mismatch | Ensure all vectors match the `dimension` in index mapping |
| `version_conflict_engine_exception` | Concurrent updates to same document | Retry or use `_id` sequencing |
| 429 Too Many Requests | Write throughput limit exceeded | Reduce batch size and add delays between batches |
| Request body too large | Exceeds 10 MB bulk limit | Reduce batch size |
| Missing newline at end of bulk body | Bulk format requires trailing `\n` | Ensure bulk NDJSON body ends with newline |
