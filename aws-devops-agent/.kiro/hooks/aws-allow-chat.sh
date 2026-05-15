#!/usr/bin/env bash
# Auto-approve aws___run_script when the code is a SendMessage via call_boto3
# and contains no destructive operation.
# Requires Kiro hook engine with stdin tool-input passthrough (not yet available).
#
# When Kiro adds stdin passthrough, install by adding to your hook config:
#   toolTypes: ["aws___run_script"]
#   command: ".kiro/hooks/aws-allow-chat.sh"
set -euo pipefail
input=$(cat)
code=$(echo "$input" | jq -r '.tool_input.code // ""')
if echo "$code" | grep -qP "operation_name\s*=\s*['\"]SendMessage['\"]" && \
   ! echo "$code" | grep -qP "operation_name\s*=\s*['\"](Delete|Terminate|Remove|Put|Create|Update)[A-Z]"; then
  echo '{"decision": "allow"}'
else
  echo '{}'
fi
