# Getting Started: Provision an OpenSearch Serverless Collection

**IMPORTANT: Execute every step directly using `call_aws`. Do NOT write any code files, scripts, or templates. All operations are performed by you through the MCP tool.**

This guide walks through the complete provisioning workflow from security policies to indexed and searchable data.

## Before You Begin

### Step 0: Verify Environment and Get IAM Identity

First, verify credentials work and get the caller identity (needed for data access policies):

```
call_aws({
  "service_name": "STS",
  "operation_name": "GetCallerIdentity",
  "parameters": {},
  "region": "us-east-1"
})
```

Save the `Arn` from the response. You need it in Step 5.

If this fails, the user needs to configure AWS credentials first (`aws configure` or `aws configure sso`).

## Step 1: Create an Encryption Security Policy

**Execute this before creating the collection.** Collections cannot be created without a matching encryption policy.

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "<collection-name>-encryption",
    "type": "encryption",
    "description": "Encryption policy for <collection-name>",
    "policy": "{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/<collection-name>\"]}],\"AWSOwnedKey\":true}"
  },
  "region": "<region>"
})
```

**Policy format notes:**
- The `policy` field is a JSON string (not a JSON object).
- `AWSOwnedKey: true` uses AWS-managed encryption keys (no additional cost).
- The `Resource` pattern `collection/<name>` matches by collection name.

**If the call returns "Resource already exists":** The policy name is taken. Either use a different name or call `GetSecurityPolicy` to check the existing one, then `UpdateSecurityPolicy` if needed.

## Step 2: Create a Network Security Policy

**Execute this to configure network access:**

### Public Access (use for development/testing)

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateSecurityPolicy",
  "parameters": {
    "name": "<collection-name>-network",
    "type": "network",
    "description": "Network policy for <collection-name>",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"collection\",\"Resource\":[\"collection/<collection-name>\"]},{\"ResourceType\":\"dashboard\",\"Resource\":[\"collection/<collection-name>\"]}],\"AllowFromPublic\":true}]"
  },
  "region": "<region>"
})
```

Default to public access unless the user specifically requests VPC endpoint access. For VPC access, see `steering/security-setup.md`.

**Policy format notes:**
- Network policies are JSON arrays (wrapped in `[]`), unlike encryption policies which are objects.
- Include both `collection` and `dashboard` resource types.

## Step 3: Create the Collection

**Execute this to create the collection:**

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateCollection",
  "parameters": {
    "name": "<collection-name>",
    "type": "SEARCH",
    "description": "Description of your collection"
  },
  "region": "<region>"
})
```

**Collection type options:**
- `SEARCH` — Full-text search workloads
- `TIMESERIES` — Log and event analytics
- `VECTORSEARCH` — k-NN vector similarity search

Choose based on the user's stated goal. Default to `SEARCH` if unclear.

The response includes `id`, `name`, `status` (initially `CREATING`), and `arn`.

## Step 4: Wait for Collection to Become ACTIVE

**Poll this every 30 seconds until status is ACTIVE.** Collections typically take 1-3 minutes.

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "BatchGetCollection",
  "parameters": {
    "names": ["<collection-name>"]
  },
  "region": "<region>"
})
```

Check `collectionDetails[0].status`:
- `CREATING` — Still provisioning. Wait 30 seconds and call again.
- `ACTIVE` — Ready. **Save the `collectionEndpoint` URL** — you need it for all data operations.
- `FAILED` — Report the `failureMessage` to the user.

The endpoint follows the format: `https://<collection-id>.<region>.aoss.amazonaws.com`

**Tell the user** when the collection is active and show them the endpoint.

## Step 5: Create a Data Access Policy

**Execute this using the IAM ARN from Step 0:**

```
call_aws({
  "service_name": "OpenSearchServerless",
  "operation_name": "CreateAccessPolicy",
  "parameters": {
    "name": "<collection-name>-access",
    "type": "data",
    "description": "Data access policy for <collection-name>",
    "policy": "[{\"Rules\":[{\"ResourceType\":\"index\",\"Resource\":[\"index/<collection-name>/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"]},{\"ResourceType\":\"collection\",\"Resource\":[\"collection/<collection-name>\"],\"Permission\":[\"aoss:CreateCollectionItems\"]}],\"Principal\":[\"<iam-arn-from-step-0>\"]}]"
  },
  "region": "<region>"
})
```

**Policy format notes:**
- Data access policies are JSON arrays.
- `index/<collection-name>/*` grants access to all indices in the collection.
- `Principal` must be the full IAM ARN.
- For assumed roles, use the role ARN (not the assumed-role session ARN). If `GetCallerIdentity` returned an assumed-role ARN like `arn:aws:sts::123456789012:assumed-role/RoleName/session`, convert it to `arn:aws:iam::123456789012:role/RoleName`.

## Step 6: Create an Index

**Execute this using the collection endpoint from Step 4.** Design the mapping based on the user's data.

### For SEARCH Collections

Examine the user's data (ask them about their data or read their data files) and create appropriate mappings:

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>",
    "body": {
      "mappings": {
        "properties": {
          "title": { "type": "text", "analyzer": "standard" },
          "description": { "type": "text" },
          "category": { "type": "keyword" },
          "price": { "type": "float" },
          "in_stock": { "type": "boolean" },
          "tags": { "type": "keyword" }
        }
      }
    }
  },
  "region": "<region>"
})
```

### For VECTORSEARCH Collections

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>",
    "body": {
      "settings": {
        "index": { "knn": true }
      },
      "mappings": {
        "properties": {
          "embedding": {
            "type": "knn_vector",
            "dimension": 1536,
            "method": {
              "name": "hnsw",
              "space_type": "cosinesimil",
              "engine": "nmslib"
            }
          },
          "text": { "type": "text" },
          "source": { "type": "keyword" }
        }
      }
    }
  },
  "region": "<region>"
})
```

### For TIMESERIES Collections

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "PUT",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>",
    "body": {
      "mappings": {
        "properties": {
          "@timestamp": { "type": "date" },
          "level": { "type": "keyword" },
          "service": { "type": "keyword" },
          "message": { "type": "text" },
          "trace_id": { "type": "keyword" },
          "response_time_ms": { "type": "integer" }
        }
      }
    }
  },
  "region": "<region>"
})
```

For detailed mapping guidance, see `steering/index-design.md`.

## Step 7: Ingest Data

**Read the user's data files directly from the workspace.** Do NOT write any code files or scripts.

### How to Ingest User Data

1. **Read the data file** from the workspace (JSON, CSV, NDJSON, etc.).
2. **Parse the data** in your context:
   - For JSON arrays: extract each object as a document.
   - For CSV: use the headers as field names, convert each row to a JSON object. Cast numeric strings to numbers where the mapping expects float/integer.
   - For NDJSON: each line is a document.
3. **Build bulk API payloads** in NDJSON format: alternating action lines and document lines.
4. **Batch into groups** of 500-1000 documents (stay under 10 MB per request).
5. **Execute `call_aws`** for each batch.
6. **Check responses** for `errors: true` and report any failures.

### Single Document Ingestion

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
      "description": "Premium noise-canceling Bluetooth headphones",
      "category": "electronics",
      "price": 79.99,
      "in_stock": true,
      "tags": ["bluetooth", "noise-canceling", "wireless"]
    }
  },
  "region": "<region>"
})
```

### Bulk Ingestion

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/_bulk",
    "body": "{ \"index\": { \"_index\": \"<index-name>\", \"_id\": \"1\" } }\n{ \"title\": \"Wireless Headphones\", \"price\": 79.99, \"category\": \"electronics\" }\n{ \"index\": { \"_index\": \"<index-name>\", \"_id\": \"2\" } }\n{ \"title\": \"USB-C Cable\", \"price\": 12.99, \"category\": \"accessories\" }\n"
  },
  "region": "<region>"
})
```

**NDJSON format rules:**
- Each line is valid JSON.
- Lines separated by `\n`.
- Body must end with `\n`.
- Max 10 MB per request.

After each bulk call, check the response:
- If `errors: false` — all documents indexed successfully.
- If `errors: true` — iterate `items` to find failures (status >= 400), report them to the user, and retry failed items.

## Step 8: Verify Data

**Execute a count query to verify ingestion:**

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

**Then run a sample search to verify data quality:**

```
call_aws({
  "service_name": "OpenSearchServerless",
  "api_name": "OpenSearchDataPlane",
  "operation_name": "POST",
  "parameters": {
    "endpoint": "<collection-endpoint>",
    "path": "/<index-name>/_search",
    "body": {
      "query": { "match_all": {} },
      "size": 5
    }
  },
  "region": "<region>"
})
```

**Report to the user:** total document count, sample results, and whether the data looks correct. If there are issues with field types or missing data, suggest re-indexing with corrected mappings.

## Complete Provisioning Checklist

After completing all steps, confirm with the user:

- Encryption policy created
- Network policy created (public access for development)
- Collection created and ACTIVE
- Collection endpoint: `https://<id>.<region>.aoss.amazonaws.com`
- Data access policy created with correct IAM principal
- Index created with mappings matching their data
- Data ingested (N documents)
- Verification search returned expected results
