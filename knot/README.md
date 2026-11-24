# Knot Power for Kiro

**Cross-AI Shared Context and Spec Continuity with Knot.**

Connect **Kiro IDE** and **Kiro CLI** to your governed **Knot** context engine (`https://api.connectknot.com/mcp`) so feature specs, architectural constraints, superseded `v1 -> v2` decisions, and task handoffs from **ChatGPT**, **Claude**, **Gemini**, and **Cursor** flow directly into `.kiro/specs/` on Turn 0.

## Why Use Knot Inside Kiro

Most product specs and architecture reviews start outside the IDE in ChatGPT, Claude, or team research threads. Native IDE memory only sees what happened inside that single editor.

This Kiro Power gives Kiro:

1. **Zero-Copy Spec Hydration (`hydrate-kiro-spec`)**: Pulls active requirements, architectural decisions, `v1 -> v2` supersession lineage, and pending cross-AI handoffs straight into `.kiro/specs/<feature>/` (`requirements.md`, `design.md`, `tasks.md`).
2. **Conflict and Supersession Safety**: Enforces the current `v2` truth when an upstream security or architecture decision overrides an earlier `v1` assumption, and surfaces unresolved `potential_conflicts` instead of silently guessing.
3. **Closed-Loop Upstream Sync (`sync-decisions-and-handoffs`)**: Commits verified implementation state, supersedes stale claims with `supersedes_context_id`, updates work threads, and sends structured follow-up handoffs back to ChatGPT, Claude, or teammates.
4. **Enterprise AWS VPC Ready**: Works out of the box with hosted Knot Cloud (`OAuth 2.1 with PKCE`) or a self-hosted **Knot EnterpriseBrain** endpoint inside your AWS VPC (EKS + Aurora/RDS PostgreSQL + AWS KMS SigV4 + EventBridge/SQS).

## Install in Kiro (1 Click)

1. Open **Kiro IDE** and open the **Powers** panel.
2. Click **Add Custom Power** -> **Import power from a repository URL** (or **Import power from GitHub**).
3. Paste:

```text
https://github.com/ConnectKnot/knot-kiro-power
```

4. Click **Install**.
5. When prompted, complete **OAuth 2.1** browser sign-in with your Knot account (`https://api.connectknot.com`). There are zero API keys to copy or embed in configuration files.

## Included Components (Agent Plugins v1.0.0)

```text
knot-kiro-power/
├── plugin.json                                           # Agent Plugins v1.0.0 manifest
├── mcp.json                                              # Streamable HTTP MCP (https://api.connectknot.com/mcp)
├── skills/
│   ├── hydrate-kiro-spec/
│   │   └── SKILL.md                                      # Recover context + compile .kiro/specs/
│   └── sync-decisions-and-handoffs/
│       ├── SKILL.md                                      # Sync verified decisions + handoffs back
│       └── references/
│           └── aws-enterprise-vpc.md                     # Self-hosted EKS / KMS / AgentCore Gateway guide
├── README.md
└── LICENSE
```

## Example Prompts to Try

- `"Check Knot for pending handoffs and current v2 constraints on OrderStream Webhook Service, then hydrate .kiro/specs/orderstream-webhooks/."`
- `"Inspect the v1 -> v2 supersession history for our retry policy in Knot before editing src/webhookHandler.ts."`
- `"Sync our verified implementation and passing test results back to Knot and mark the Kiro handoff completed."`

## Self-Hosted AWS VPC Override (Knot EnterpriseBrain)

Enterprise teams running **Knot EnterpriseBrain** in their own AWS VPC can point `.kiro/settings/mcp.json` at their internal EKS Ingress `/mcp` endpoint instead of the multi-tenant cloud endpoint. See [AWS EnterpriseBrain VPC & Gateway Reference](skills/sync-decisions-and-handoffs/references/aws-enterprise-vpc.md) for the full EKS, AWS KMS SigV4, EventBridge/SQS, and Bedrock AgentCore Gateway setup.

## Security, Privacy, and Support

- **Authentication**: User-delegated OAuth 2.1 with PKCE and Dynamic Client Registration (`https://api.connectknot.com/.well-known/oauth-protected-resource`). No tokens or secrets are stored in `mcp.json`.
- **Grant Isolation**: Kiro sees only the personal or shared knots authorized by your OAuth grant.
- **Quickstart & Docs**: https://connectknot.com/developers/quickstart
- **Security**: https://connectknot.com/security
- **Privacy Policy**: https://connectknot.com/privacy
- **Terms of Service**: https://connectknot.com/terms
- **Support**: support@connectknot.com (https://connectknot.com/support)

## License

MIT License. See [LICENSE](LICENSE).
