# Search Patterns for OpenSearch Serverless

This guide covers query patterns for all three collection types: SEARCH, TIMESERIES, and VECTORSEARCH.

## Full-Text Search Queries

### Simple Match

Search a single field with relevance scoring:

```json
{
  "query": {
    "match": {
      "title": {
        "query": "wireless headphones",
        "operator": "and"
      }
    }
  }
}
```

- `operator: "and"` requires all terms to match. Default is `"or"` (any term matches).

### Multi-Match

Search across multiple fields with field boosting:

```json
{
  "query": {
    "multi_match": {
      "query": "wireless noise canceling",
      "fields": ["title^3", "description^1", "tags^2"],
      "type": "best_fields"
    }
  }
}
```

**Type options:**
- `best_fields` (default) — Uses the score from the best-matching field.
- `most_fields` — Combines scores from all matching fields.
- `cross_fields` — Treats fields as one combined field (good for names split across first/last).
- `phrase` — Matches the query as a phrase in each field.
- `phrase_prefix` — Like phrase but allows prefix matching on the last term (good for autocomplete).

### Phrase Match

Match exact phrases in order:

```json
{
  "query": {
    "match_phrase": {
      "description": {
        "query": "noise canceling headphones",
        "slop": 1
      }
    }
  }
}
```

- `slop` allows terms to be N positions apart. `slop: 0` requires exact adjacent order.

### Prefix / Autocomplete

Match documents where a field starts with a prefix:

```json
{
  "query": {
    "match_phrase_prefix": {
      "title": {
        "query": "wire",
        "max_expansions": 50
      }
    }
  }
}
```

## Boolean Queries

Combine multiple conditions with `must`, `should`, `must_not`, and `filter`:

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "headphones" } }
      ],
      "should": [
        { "match": { "description": "bluetooth" } },
        { "match": { "description": "wireless" } }
      ],
      "must_not": [
        { "term": { "category": "refurbished" } }
      ],
      "filter": [
        { "range": { "price": { "gte": 20, "lte": 100 } } },
        { "term": { "in_stock": true } }
      ],
      "minimum_should_match": 1
    }
  }
}
```

**Clause behavior:**
- `must` — Required. Contributes to relevance score.
- `should` — Optional (unless no `must` clause). Boosts relevance score.
- `must_not` — Excluded. Does not affect score.
- `filter` — Required. Does NOT affect score (faster, cacheable).
- `minimum_should_match` — How many `should` clauses must match.

**Rule of thumb:** Use `filter` instead of `must` for exact-match conditions (terms, ranges) that don't need relevance scoring.

## Vector (kNN) Search

### Approximate kNN Search

For VECTORSEARCH collections. Returns the k most similar documents:

```json
{
  "size": 10,
  "query": {
    "knn": {
      "embedding": {
        "vector": [0.12, -0.34, 0.56, ...],
        "k": 10
      }
    }
  }
}
```

- `embedding` is the name of your `knn_vector` field.
- The vector dimension must match the index mapping's `dimension`.
- `k` is the number of nearest neighbors to return.
- `size` controls how many results are returned (should match or be less than `k`).

### kNN with Filters

Combine vector similarity with metadata filters:

```json
{
  "size": 10,
  "query": {
    "knn": {
      "embedding": {
        "vector": [0.12, -0.34, 0.56, ...],
        "k": 10,
        "filter": {
          "bool": {
            "must": [
              { "term": { "category": "documentation" } },
              { "range": { "created_at": { "gte": "2024-01-01" } } }
            ]
          }
        }
      }
    }
  }
}
```

The filter is applied **before** the kNN search (pre-filtering), which ensures the k results all satisfy the filter.

### Exact kNN (Script Score)

For precise similarity when approximate results aren't sufficient:

```json
{
  "size": 10,
  "query": {
    "script_score": {
      "query": {
        "match_all": {}
      },
      "script": {
        "source": "knn_score",
        "lang": "knn",
        "params": {
          "field": "embedding",
          "query_value": [0.12, -0.34, 0.56, ...],
          "space_type": "cosinesimil"
        }
      }
    }
  }
}
```

This scans all documents and computes exact similarity. Use only when precision matters more than latency (small indices or reranking).

## Hybrid Search

Combine full-text and vector search for better relevance:

### Using Hybrid Query

```json
{
  "size": 10,
  "query": {
    "hybrid": {
      "queries": [
        {
          "match": {
            "text": {
              "query": "machine learning fundamentals"
            }
          }
        },
        {
          "knn": {
            "embedding": {
              "vector": [0.12, -0.34, 0.56, ...],
              "k": 20
            }
          }
        }
      ]
    }
  },
  "search_pipeline": "hybrid-search-pipeline"
}
```

This requires a search pipeline configured with normalization and combination processors. Create a search pipeline first:

```json
PUT /_search/pipeline/hybrid-search-pipeline
{
  "description": "Normalization and combination for hybrid search",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [0.3, 0.7]
          }
        }
      }
    }
  ]
}
```

- `weights` control the balance between text relevance (first value) and vector similarity (second value).
- Adjust weights based on your use case: higher text weight for keyword-heavy queries, higher vector weight for semantic queries.

## Aggregations and Analytics

### Terms Aggregation

Count documents by category:

```json
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {
        "field": "category",
        "size": 20
      }
    }
  }
}
```

### Range Aggregation

Group documents into price ranges:

```json
{
  "size": 0,
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 25, "key": "budget" },
          { "from": 25, "to": 100, "key": "mid-range" },
          { "from": 100, "key": "premium" }
        ]
      }
    }
  }
}
```

### Date Histogram (TIMESERIES)

Aggregate log events by time interval:

```json
{
  "size": 0,
  "query": {
    "range": {
      "@timestamp": {
        "gte": "2024-01-01T00:00:00Z",
        "lte": "2024-01-31T23:59:59Z"
      }
    }
  },
  "aggs": {
    "events_over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "1h"
      },
      "aggs": {
        "avg_response_time": {
          "avg": { "field": "response_time_ms" }
        },
        "error_count": {
          "filter": { "term": { "level": "ERROR" } }
        }
      }
    }
  }
}
```

### Stats Aggregation

Get statistical summary of a numeric field:

```json
{
  "size": 0,
  "aggs": {
    "price_stats": {
      "stats": { "field": "price" }
    },
    "percentile_response": {
      "percentiles": {
        "field": "response_time_ms",
        "percents": [50, 90, 95, 99]
      }
    }
  }
}
```

### Nested Aggregations (Faceted Search)

Combine search with facet counts for UI filtering:

```json
{
  "size": 10,
  "query": {
    "match": { "title": "headphones" }
  },
  "aggs": {
    "brand_facet": {
      "terms": { "field": "brand", "size": 10 }
    },
    "price_facet": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 50 },
          { "from": 50, "to": 100 },
          { "from": 100 }
        ]
      }
    },
    "rating_facet": {
      "terms": { "field": "rating", "size": 5 }
    }
  }
}
```

## Pagination

### From/Size Pagination

Simple offset-based pagination (for small result sets):

```json
{
  "from": 20,
  "size": 10,
  "query": {
    "match": { "title": "headphones" }
  }
}
```

**Limitation:** `from + size` cannot exceed 10,000 in OpenSearch Serverless.

### Search After (Deep Pagination)

For paginating beyond 10,000 results or for cursor-based pagination:

```json
{
  "size": 10,
  "query": {
    "match_all": {}
  },
  "sort": [
    { "price": "asc" },
    { "_id": "asc" }
  ],
  "search_after": [45.00, "product-123"]
}
```

Use the `sort` values from the last document in the previous page as the `search_after` value.

## Sorting

### Single Field Sort

```json
{
  "query": { "match": { "title": "headphones" } },
  "sort": [
    { "price": { "order": "asc" } }
  ]
}
```

### Multi-Field Sort with Relevance

```json
{
  "query": { "match": { "title": "headphones" } },
  "sort": [
    "_score",
    { "price": { "order": "asc" } },
    { "created_at": { "order": "desc" } }
  ]
}
```

`_score` sorts by relevance. Combine with other fields to break ties.

## Source Filtering

Return only specific fields to reduce response size:

```json
{
  "query": { "match": { "title": "headphones" } },
  "_source": ["title", "price", "category"],
  "size": 10
}
```

Exclude fields:

```json
{
  "_source": {
    "excludes": ["description", "embedding"]
  },
  "query": { "match_all": {} }
}
```

## Highlighting

Return matched text fragments with highlighting:

```json
{
  "query": {
    "match": { "description": "noise canceling" }
  },
  "highlight": {
    "fields": {
      "description": {
        "fragment_size": 150,
        "number_of_fragments": 3,
        "pre_tags": ["<mark>"],
        "post_tags": ["</mark>"]
      }
    }
  }
}
```

## Query Tips

- Use `filter` context for exact matches and ranges — it's faster and cacheable.
- Boost important fields with `^N` in multi_match queries (e.g., `title^3`).
- Use `keyword` fields for exact-match filtering (not `text` fields).
- For TIMESERIES collections, always include a time range in queries to limit the search scope.
- Set `size: 0` when you only need aggregation results, not documents.
- Use `_source` filtering to exclude large fields like embeddings from results.
