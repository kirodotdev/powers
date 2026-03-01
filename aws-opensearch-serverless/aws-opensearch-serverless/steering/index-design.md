# Index Design for OpenSearch Serverless

This guide covers index mapping design, field type selection, analyzers, and schema patterns for each collection type.

## Collection Type Selection

Choose the collection type based on your primary access pattern:

| If your data is... | And you need... | Use |
|---|---|---|
| Documents, products, articles | Full-text search, filtering, facets | **SEARCH** |
| Logs, metrics, events | Time-range queries, aggregations | **TIMESERIES** |
| Embeddings, feature vectors | Similarity search, kNN queries | **VECTORSEARCH** |

**Key differences:**
- SEARCH collections are optimized for random-access read patterns.
- TIMESERIES collections optimize storage and queries for time-ordered data. They have lower storage costs but do not support random-access updates well.
- VECTORSEARCH collections enable the kNN plugin and vector similarity features.

## Field Types

### Text Fields

| Type | Use For | Queryable With |
|------|---------|---------------|
| `text` | Full-text content (analyzed, tokenized) | `match`, `multi_match`, `match_phrase` |
| `keyword` | Exact values (not analyzed) | `term`, `terms`, `prefix`, aggregations |

**When to use which:**
- Use `text` for fields users will search with natural language: titles, descriptions, body text.
- Use `keyword` for fields used in exact filters and aggregations: categories, status, tags, IDs, email addresses.
- Use both (multi-field) when you need full-text search AND exact filtering:

```json
{
  "title": {
    "type": "text",
    "analyzer": "standard",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    }
  }
}
```

Query `title` for full-text search, `title.keyword` for exact match and aggregations.

### Numeric Fields

| Type | Range | Use For |
|------|-------|---------|
| `integer` | -2^31 to 2^31-1 | Counts, quantities, status codes |
| `long` | -2^63 to 2^63-1 | Large IDs, timestamps as epoch ms |
| `float` | 32-bit IEEE 754 | Prices, ratings, percentages |
| `double` | 64-bit IEEE 754 | High-precision measurements |
| `scaled_float` | Backed by long, with scaling factor | Financial amounts (use `scaling_factor: 100` for cents) |

### Date Fields

```json
{
  "@timestamp": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

Common formats:
- `strict_date_optional_time` — ISO 8601 (e.g., `2024-01-15T10:30:00Z`)
- `epoch_millis` — Unix timestamp in milliseconds
- `yyyy-MM-dd` — Date only
- Custom: `yyyy-MM-dd HH:mm:ss`

### Boolean Fields

```json
{
  "in_stock": { "type": "boolean" }
}
```

Accepts `true`, `false`, `"true"`, `"false"`.

### Vector Fields

For VECTORSEARCH collections:

```json
{
  "embedding": {
    "type": "knn_vector",
    "dimension": 1536,
    "method": {
      "name": "hnsw",
      "space_type": "cosinesimil",
      "engine": "nmslib"
    }
  }
}
```

**Parameters:**
- `dimension` — Must match your embedding model's output size exactly. Common values: 384 (MiniLM), 768 (BERT), 1536 (OpenAI ada-002), 3072 (OpenAI text-embedding-3-large).
- `space_type` — Similarity metric:
  - `cosinesimil` — Cosine similarity (most common for text embeddings)
  - `l2` — Euclidean distance
  - `innerproduct` — Dot product (use with normalized vectors)
- `engine` — ANN algorithm implementation:
  - `nmslib` — Fastest for search. Supports HNSW.
  - `faiss` — More tunable. Supports HNSW and IVF.
- `name` — Algorithm name: `hnsw` (recommended for most use cases).

**HNSW Parameters (optional tuning):**

```json
{
  "method": {
    "name": "hnsw",
    "space_type": "cosinesimil",
    "engine": "nmslib",
    "parameters": {
      "ef_construction": 256,
      "m": 16
    }
  }
}
```

- `ef_construction` — Controls index build quality. Higher = better recall, slower indexing. Default: 512.
- `m` — Number of bidirectional links per node. Higher = better recall, more memory. Default: 16.

### Object and Nested Fields

**Object type** (default for JSON objects):

```json
{
  "address": {
    "properties": {
      "street": { "type": "text" },
      "city": { "type": "keyword" },
      "zip": { "type": "keyword" }
    }
  }
}
```

Queried with dot notation: `address.city: "Seattle"`. Object arrays are flattened internally (cross-object matches possible).

**Nested type** (independent inner objects):

```json
{
  "reviews": {
    "type": "nested",
    "properties": {
      "author": { "type": "keyword" },
      "rating": { "type": "integer" },
      "text": { "type": "text" }
    }
  }
}
```

Use `nested` when you need to query array elements independently (e.g., "reviews where author is Alice AND rating is 5" without cross-matching). Requires `nested` query type.

## Analyzers

Analyzers control how `text` fields are tokenized and normalized for search.

### Built-in Analyzers

| Analyzer | Behavior | Best For |
|----------|----------|----------|
| `standard` (default) | Unicode tokenization, lowercase | General-purpose text search |
| `simple` | Splits on non-letter characters, lowercase | Simple text, names |
| `whitespace` | Splits on whitespace only, no lowercasing | Preserving exact tokens |
| `keyword` | No tokenization (entire value as one token) | When text type must act as keyword |
| `english` | Standard + English stemming + stop words | English natural language |
| `pattern` | Splits by regex pattern | Structured text with known delimiters |

### Custom Analyzers

Create custom analyzers for specialized search behavior:

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "product_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stemmer", "english_stop"]
        }
      },
      "filter": {
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "product_analyzer"
      }
    }
  }
}
```

### Autocomplete Analyzer

Use `edge_ngram` for type-ahead / autocomplete:

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "type": "custom",
          "tokenizer": "autocomplete_tokenizer",
          "filter": ["lowercase"]
        },
        "autocomplete_search": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      },
      "tokenizer": {
        "autocomplete_tokenizer": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20,
          "token_chars": ["letter", "digit"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "autocomplete",
        "search_analyzer": "autocomplete_search"
      }
    }
  }
}
```

Use a different `search_analyzer` so search queries are not n-grammed.

## Index Mapping Patterns

### E-Commerce Product Catalog

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "product_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stemmer"]
        }
      },
      "filter": {
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "product_analyzer",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "description": { "type": "text", "analyzer": "product_analyzer" },
      "category": { "type": "keyword" },
      "subcategory": { "type": "keyword" },
      "brand": { "type": "keyword" },
      "price": { "type": "scaled_float", "scaling_factor": 100 },
      "sale_price": { "type": "scaled_float", "scaling_factor": 100 },
      "currency": { "type": "keyword" },
      "in_stock": { "type": "boolean" },
      "stock_quantity": { "type": "integer" },
      "sku": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "rating": { "type": "float" },
      "review_count": { "type": "integer" },
      "images": { "type": "keyword" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

### Application Logs

```json
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "level": { "type": "keyword" },
      "logger": { "type": "keyword" },
      "service": { "type": "keyword" },
      "environment": { "type": "keyword" },
      "host": { "type": "keyword" },
      "message": { "type": "text" },
      "trace_id": { "type": "keyword" },
      "span_id": { "type": "keyword" },
      "request_id": { "type": "keyword" },
      "http_method": { "type": "keyword" },
      "http_path": { "type": "keyword" },
      "http_status": { "type": "integer" },
      "response_time_ms": { "type": "integer" },
      "error_type": { "type": "keyword" },
      "error_message": { "type": "text" },
      "user_id": { "type": "keyword" }
    }
  }
}
```

### Knowledge Base / RAG

```json
{
  "settings": {
    "index": { "knn": true }
  },
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "content": { "type": "text" },
      "content_embedding": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib"
        }
      },
      "source_url": { "type": "keyword" },
      "source_type": { "type": "keyword" },
      "chunk_index": { "type": "integer" },
      "parent_doc_id": { "type": "keyword" },
      "metadata": {
        "properties": {
          "author": { "type": "keyword" },
          "published_date": { "type": "date" },
          "tags": { "type": "keyword" }
        }
      },
      "created_at": { "type": "date" }
    }
  }
}
```

### Geospatial Data

```json
{
  "mappings": {
    "properties": {
      "name": { "type": "text" },
      "location": { "type": "geo_point" },
      "category": { "type": "keyword" },
      "address": { "type": "text" },
      "city": { "type": "keyword" },
      "rating": { "type": "float" }
    }
  }
}
```

`geo_point` accepts multiple formats: `{ "lat": 47.6, "lon": -122.3 }`, `"47.6,-122.3"`, or `[-122.3, 47.6]` (GeoJSON order).

## Schema Evolution

OpenSearch Serverless does not support changing the type of existing fields. To modify mappings:

### Adding New Fields

New fields can be added to an existing index without re-indexing:

```
PUT <endpoint>/<index-name>/_mapping
{
  "properties": {
    "new_field": { "type": "keyword" }
  }
}
```

### Changing Field Types (Requires Re-index)

1. Create a new index with the updated mapping.
2. Use the `_reindex` API to copy data.
3. Update application references to point to the new index.
4. Delete the old index.

See `data-ingestion.md` for re-indexing details.

### Dynamic Mapping

By default, OpenSearch creates mappings automatically for new fields. Control this behavior:

```json
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "title": { "type": "text" },
      "price": { "type": "float" }
    }
  }
}
```

**Dynamic options:**
- `true` (default) — Automatically create mappings for new fields.
- `false` — Accept new fields but don't index them (not searchable).
- `strict` — Reject documents with unmapped fields.

**Recommendation:** Use `strict` for production indices to prevent accidental field proliferation and mapping conflicts.

## Index Settings

### Refresh Interval

Controls how quickly indexed documents become searchable:

```json
{
  "settings": {
    "index": {
      "refresh_interval": "5s"
    }
  }
}
```

- Default: `1s` (documents are searchable within 1 second).
- Set to `"30s"` or `"-1"` (disable) during bulk ingestion for better throughput, then reset.
- OpenSearch Serverless manages many settings automatically — not all settings are configurable.

### Number of Replicas

OpenSearch Serverless manages replication automatically. You cannot configure shard count or replica count — these are handled by the service.
