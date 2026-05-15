#!/usr/bin/env bash
# Auto-approve aws___call_aws when the CLI command is a read-only DevOps Agent op.
# Requires Kiro hook engine with stdin tool-input passthrough (not yet available).
#
# When Kiro adds stdin passthrough, install by adding to your hook config:
#   toolTypes: ["aws___call_aws"]
#   command: ".kiro/hooks/aws-allow-reads.sh"
set -euo pipefail
input=$(cat)
cli_command=$(echo "$input" | jq -r '.tool_input.cli_command // ""')
operation=$(echo "$cli_command" | grep -oP 'devops-agent\s+\K[a-z]+-[a-z-]+' || true)
case "$operation" in
  list-*|describe-*|get-*) echo '{"decision": "allow"}' ;;
  *)                       echo '{}' ;;
esac
