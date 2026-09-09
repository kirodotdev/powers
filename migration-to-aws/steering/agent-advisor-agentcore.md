# AgentCore Runtime — Service Card

## One-liner

Serverless, agent-purpose-built runtime: managed session routing, true session
isolation, built-in identity, $0 billing during I/O wait.

## Best for

Short agent sessions with high LLM I/O wait, human-in-the-loop, multi-tenant
isolation, minimal ops, cross-session memory, high-volume session launch.

## Hard limits (verify via MCP — volatile)

- Session cap: 8h (extending — verify)
- Compute cap: 2 vCPU / 8 GB (hard)
- FedRAMP: authorization in progress (WIP) — verify current status; NOT a hard block

## Deployment models

- **Harness** — no-code, config-driven; single agent, greenfield, OpenAI Assistants migration.
- **Framework on Runtime** — Strands / LangGraph / CrewAI / custom; multi-agent, complex orchestration.

## Six dimensions

- Identity: built-in (free), OAuth via enhanced Identity
- Observability: auto OTEL traces
- Guardrails: Bedrock Guardrails + Policy (Cedar) for high-risk actions
- Scaling: 5,000 concurrent sessions, 25 TPS launch (adjustable)
- Tool/Gateway: Gateway for external APIs / MCP
- Protocols: HTTP/1.1, WebSocket; MCP, A2A

## Conditional services (relevant but not always)

- Payments: for agents that pay / transact on a user's behalf — surface only for
  transactional / high-risk-action workloads.
- Registry: agent/tool discovery and multi-agent orchestration — surface only for multi-agent setups.

## Tradeoffs

2 vCPU / 8 GB ceiling; no process-level suspend (Session Storage persists files only).

## Serving & security notes

Entry: POST /invocations + GET /ping. IAM: execution role with InvokeModel + Gateway/Registry/SessionStorage permissions as needed. Networking: public service endpoints over TLS; VPC endpoints only if policy demands.
