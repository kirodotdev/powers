# Troubleshooting

## Quick Reference

| Issue | Resolution |
|-------|------------|
| `atx` not found | Install: `curl -fsSL https://transform-cli.awsstatic.com/install.sh` piped to `bash` |
| AWS credentials error | Run `aws sts get-caller-identity`. Check `AWS_PROFILE` or access key env vars |
| Permission denied | Need `transform-custom:*` — see Prerequisites → IAM Permissions in POWER.md |
| Network error | Resolve region: `REGION=${AWS_REGION:-${AWS_DEFAULT_REGION:-$(aws configure get region 2>/dev/null)}}; REGION=${REGION:-us-east-1}`. Check access to `transform-custom.${REGION}.api.aws` |
| Build fails during transform | Verify build command works locally first. Try interactive mode for debugging |
| Transform not found | Run `atx custom def list --json` to check available TDs |
| Conversation expired | Conversations expire after 30 days. Start a new one |
| Windows not supported | Tell user to use Windows Subsystem for Linux (WSL) |
| Timeout | Set `export ATX_SHELL_TIMEOUT=1800` (default: 900s) |
| Poor quality results | See Improving Quality section below |

## Local Mode Debugging

| Log | Path |
|-----|------|
| Developer logs | `~/.aws/atx/logs/debug*.log` and `~/.aws/atx/logs/error.log` |
| Conversation log | `~/.aws/atx/custom/<conversation_id>/logs/<timestamp>-conversation.log` |

Network errors may indicate VPN/firewall issues with AWS endpoints.

## Improving Quality

Diagnose in this order:

1. **Build command** (most impactful): Is it deterministic? Does it return meaningful errors? Specific commands (`mvn clean install`) outperform no validation.
2. **Reference materials**: Provide migration guides or API specs via `additionalPlanContext`.
3. **Complexity**: Decompose very complex transforms into smaller steps.
4. **Knowledge items**: Review learnings from previous runs. Enable good ones, disable irrelevant ones.

## Network Requirements

| Endpoint | Purpose |
|----------|---------|
| `transform-cli.awsstatic.com` | CLI installation and updates |
| `transform-custom.${REGION}.api.aws` | Transformation service API |
