# AWS EnterpriseBrain VPC & Bedrock AgentCore Gateway Reference

Teams running strict data-residency or PCI/regulated workloads on AWS can point this Kiro Power at a self-hosted **Knot EnterpriseBrain** deployment inside their own VPC instead of the multi-tenant cloud endpoint.

## 1. Self-Hosted AWS VPC Architecture (`charts/knot-enterprisebrain`)

Knot EnterpriseBrain v1.1.0 ships an official AWS EKS Helm preset (`charts/knot-enterprisebrain/presets/aws-eks.yaml`) built around single-codebase isolation (`KNOT_TENANCY_MODEL=subject_domain`):

| AWS Layer | Knot EnterpriseBrain Integration |
| :--- | :--- |
| **Compute & Ingress** | Amazon EKS (`knot-api` + `knot-ingest-worker` pods) behind internal ALB/Envoy with NetworkPolicies |
| **Identity** | EKS IRSA (`eks.amazonaws.com/role-arn`), mTLS (`X-Forwarded-Client-Cert`), or OAuth2 JWKS |
| **Encryption & Key Hierarchy** | **AWS KMS SigV4** root key unwrapping (`alias/knot-enterprisebrain-root`) feeding 3-level HKDF (`K_org_root -> K_domain -> K_subject`) + orthogonal `pgvector` rotation |
| **Database** | **Amazon Aurora PostgreSQL** or **RDS PostgreSQL** with `pgvector` (zero outbound telemetry or egress) |
| **Event Ingestion** | **Amazon EventBridge** / **Amazon SQS** / MSK ingest worker (`ingestWorker.source: aws_sqs`) with scrubbed dead-letter queue |
| **Write-Door Guardrails** | Declarative `knot-policy.yaml` domain authority ACLs + HTTP `422 PCI_CDE_PAYLOAD_REJECTED` firewall rejecting raw PAN/CVV payloads before storage |
| **LLM Inference** | **Amazon Bedrock** (`llm.provider: aws-bedrock`) or airgapped deterministic mode (`KNOT_ALLOW_REMOTE_MODELS=false`, `KNOT_LLM_PROVIDER=none`) |

## 2. Pointing the Kiro Power at Your VPC `/mcp` Endpoint

Your self-hosted EnterpriseBrain container exposes a native Streamable HTTP `/mcp` route (`get_relevant_context`, `propose_context`, `commit_context`, `get_lineage`) with domain-scoped authentication.

To override the hosted cloud URL locally inside a workspace, update `.kiro/settings/mcp.json` (never commit secrets or tokens):

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "knot": {
      "type": "streamable-http",
      "url": "https://knot-internal.your-vpc.internal/mcp"
    }
  }
}
```

## 3. Complementary Positioning with AWS Native AI Services

Knot does not replace intra-AWS agent memory services; it governs cross-tool agreement and upstream continuity across independent AI ecosystems:

- **Kiro IDE & Kiro CLI (`/memories`, `.kiro/steering/`)**: Kiro remembers repository-local conventions and past Kiro sessions. Knot supplies upstream requirements, design decisions, and `v1 -> v2` overrides created outside Kiro (in ChatGPT, Claude, Gemini, or Cursor) and syncs Kiro outcomes back to those tools.
- **Amazon Bedrock AgentCore Memory & Strands SDK (`Mem0`)**: AgentCore Memory handles session STM/LTM inside Bedrock agents. Knot sits alongside it (and ships a drop-in `Mem0CompatClient` in `@knot-ai/sdk`) when multiple independent products or business domains need write-door conflict arbitration, `knot-policy.yaml` domain authority ranking, and cryptographic `as_of` audit replay.
- **Amazon Quick (Shared Spaces) & Amazon Connect (Contact Flows)**: Both Quick and Connect consume remote MCP endpoints directly or through **Amazon Bedrock AgentCore Gateway**. Registering the same Knot `/mcp` endpoint in AgentCore Gateway lets Quick assistants and Connect customer-service flows share governed, up-to-date context without duplicating policy state.

## References

- EnterpriseBrain Public Technical Brief: https://connectknot.com/enterprise-brain
- EnterpriseBrain Reference Manual: https://connectknot.com/enterprise-brain/reference
- Knot Developer Quickstart: https://connectknot.com/developers/quickstart
- Security & Trust Overview: https://connectknot.com/security
