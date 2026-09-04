# Amazon ECS (Fargate) — Service Card

## One-liner

Container runtime, no cluster management, cost-optimized at steady scale.

## Best for

Container experience, steady continuous traffic, custom compute, sessions up to/over 8h.

## Hard limits

None that eliminate it for agents (GPU and >8h are where it wins vs AgentCore).

## Six dimensions

- Identity: IAM / bring-your-own
- Observability: CloudWatch + ADOT (you configure)
- Guardrails: bring-your-own + Bedrock Guardrails
- Scaling: Savings Plans, bin-packing
- Tool/Gateway: AgentCore services available as add-ons
- Protocols: anything you expose

## Tradeoffs

Always-on baseline cost during idle; you build session isolation/memory yourself.
Hands off to migration-to-aws for compute-layer config.

## Serving & security notes

Entry: container behind ALB or Service exposing your HTTP/gRPC endpoint. IAM: task execution role + task role with `bedrock:InvokeModel` (model-bearing units only — a model-less service/light_io unit omits it) + service-specific permissions. Networking: ALB/Service endpoints over TLS; VPC endpoints only if policy demands.
