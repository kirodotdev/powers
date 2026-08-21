#!/usr/bin/env bash
# =============================================================================
# check-change-record-setup.sh — Is the ServiceNow change record step usable?
#
# The change record is OPTIONAL. Exit 1 here does NOT block a deploy — it only
# means no CHG record will be created for this run.
#
# Exit 0 → READY        (AIDEN_TOKEN + AIDEN_ORG_ID present)
# Exit 1 → NOT_CONFIGURED
# =============================================================================

echo "StackGen power — ServiceNow change record configuration"
echo ""

ok=1

check() {
  local var="$1" hint="$2"
  if [[ -n "${!var:-}" ]]; then
    printf "  [ok]      %s\n" "$var"
  else
    printf "  [missing] %-16s  %s\n" "$var" "$hint"
    ok=0
  fi
}

check AIDEN_TOKEN    "StackGen PAT with GUILD access (stackgen_...)"
check AIDEN_ORG_ID   "Aiden workspace UUID"
check AIDEN_BASE_URL "base URL of the Aiden API — no default"
check AIDEN_WORKFLOW "GUILD workflow name — no default"


echo ""
echo "Optional overrides:"
for _var in AIDEN_MAX_POLLS; do
  if [[ -n "${!_var:-}" ]]; then
    printf "  [set]     %-16s  %s\n" "$_var" "${!_var}"
  else
    printf "  [default] %s\n" "$_var"
  fi
done

echo ""
if (( ok )); then
  echo "READY — successful Apply runs will produce a ServiceNow CHG record."
  exit 0
else
  cat <<'EOF'
NOT_CONFIGURED — deploys still work, but no CHG record will be created.

  export AIDEN_TOKEN="stackgen_..."
  export AIDEN_ORG_ID="<your-workspace-uuid>"
  export AIDEN_BASE_URL="https://<your-aiden-host>"   # e.g. https://ai.stackgen.com
  export AIDEN_WORKFLOW="post-stackgen-servicenow-change-request"
EOF
  exit 1
fi