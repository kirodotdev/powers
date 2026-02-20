# AWS OpenSearch Serverless Kiro Power

A Kiro Power that enables AI-assisted provisioning and management of Amazon OpenSearch Serverless collections. Describe high-level goals like "I need to build a search application on my data" and the agent will automatically provision collections, set up security policies, create indices, ingest data, and generate application code.

## What's Included

```
aws-opensearch-serverless/
├── POWER.md                    # Core documentation, tool usage, workflows
├── mcp.json                    # AWS MCP server configuration
└── steering/
    ├── getting-started.md      # End-to-end provisioning workflow
    ├── search-patterns.md      # Full-text, vector, and hybrid search queries
    ├── data-ingestion.md       # Bulk ingestion, pipelines, data formats
    ├── index-design.md         # Mappings, analyzers, collection types
    └── security-setup.md       # IAM, encryption, network, access policies
```

## Prerequisites

- **AWS CLI v2** configured with valid credentials (`aws sts get-caller-identity`)
- **UV** (Python package manager) for the aws-mcp proxy (`uvx --version`)
- **IAM permissions** for `aoss:*` actions (see POWER.md for the full policy)

## Installation

### Method 1: Kiro IDE UI (Recommended)

1. Open Kiro IDE.
2. Open the Powers panel: `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Linux/Windows), then search for **"Powers: Manage Powers"**.
3. Click **"Add power from Local Path"**.
4. Select the `aws-opensearch-serverless/` subdirectory (the directory containing `POWER.md`, not this root directory).
5. The power will appear in your Powers list and activate when you mention relevant keywords like "opensearch", "search", "vector search", etc.

### Method 2: Manual File Copy

1. Copy the `aws-opensearch-serverless/` directory to:
   ```
   ~/.kiro/powers/installed/aws-opensearch-serverless/
   ```
2. Kiro will detect the power on next startup.

## Usage

After installation, the power activates automatically when you mention relevant keywords in conversation. Try prompts like:

- "Create an OpenSearch Serverless collection for my product catalog"
- "Set up vector search for semantic search on my knowledge base"
- "Build a log analytics pipeline with OpenSearch Serverless"
- "Help me design an index mapping for e-commerce product search"

The agent will use the `aws-mcp` tools to make AWS API calls on your behalf, handling Sig V4 signing, security policy creation, collection provisioning, and data operations.

## Supported Collection Types

| Type | Use Case |
|------|----------|
| **SEARCH** | Full-text search (products, documents, site search) |
| **TIMESERIES** | Log analytics, metrics, event data |
| **VECTORSEARCH** | Semantic/kNN search, RAG, recommendations |

## Troubleshooting

**Power not activating?**
- Verify the power is listed in the Powers panel.
- Check that you're using relevant keywords (opensearch, search, vector, indexing, etc.).

**AWS API calls failing?**
- Run `aws sts get-caller-identity` to verify credentials.
- Check IAM permissions for `aoss:*` actions.
- Ensure `uvx` is installed and on your PATH.

**Collection creation failing?**
- Encryption policy must be created before the collection.
- Collection names must be 3-32 lowercase characters with hyphens only.
- Policy names must be unique per type per region per account.
