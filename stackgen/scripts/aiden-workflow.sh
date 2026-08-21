#!/usr/bin/env bash
# =============================================================================
# aiden-workflow.sh — Create a ServiceNow change_request via the Aiden 2.0
#                     GUILD workflow (post-stackgen-servicenow-change-request).
#
# Called by the StackGen power AFTER a successful Apply. Never for a failed run.
# All inputs are supplied as environment variables so that multi-line values
# (plan_stdout, backout_plan, …) are passed without quoting/escaping problems.
#
# Required inputs (env vars):
#   appStack        — appStack name           (e.g. chat-app-infra-1753990800)
#   environment     — dev | staging | prod
#   provider        — aws | azure | gcp
#   region          — cloud region            (e.g. us-east-1)
#   run_type        — Plan | Apply
#   created changed replaced removed          — resource counts from the run
#   plan_stdout     — full Terraform/OpenTofu plan or apply output
#   cli_run_url     — URL to the StackGen action run
#   correlation_id  — idempotency key = the StackGen action run ID
#   justification   — reason for this change
#
# Optional inputs:
#   executed_via    — saas-runner | local-cli  (how the Apply actually ran)
#   backout_plan test_plan impact risk start_date end_date
#
# Required credentials (env vars):
#   AIDEN_TOKEN     — StackGen PAT with GUILD access (stackgen_…)
#   AIDEN_ORG_ID    — Aiden workspace/org UUID
#   AIDEN_BASE_URL  — base URL of the Aiden API, e.g. https://ai.stackgen.com
#   AIDEN_WORKFLOW  — GUILD workflow to invoke, e.g.
#                     post-stackgen-servicenow-change-request
#
#                     Neither has a default. Together they name WHERE a
#                     completed Apply gets reported, and a guess there fails
#                     right after a successful Apply. Unset is reported as
#                     NOT_CONFIGURED, which is a safe skip.
#
# Optional overrides:
#   AIDEN_MAX_POLLS — default 30 (× 5 s = 150 s)
#
# Exit codes / stdout contract (single line, machine-readable):
#   0   COMPLETED trace_id=<id> chg=<CHG…> correlation_id=<id>
#   1   SN_ERROR <detail>            — network, auth, or Aiden failure
#   2   NOT_CONFIGURED               — AIDEN_TOKEN / AIDEN_ORG_ID missing
#   64  BAD_ARGS                     — a required input is missing
#
# No Python, no temp files, no jq — POSIX shell + curl + awk only.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Guard: credentials  (exit 2 is "not configured", NOT an error to retry)
# ---------------------------------------------------------------------------
AIDEN_TOKEN="${AIDEN_TOKEN:-}"
AIDEN_ORG_ID="${AIDEN_ORG_ID:-}"
AIDEN_BASE_URL="${AIDEN_BASE_URL:-}"
AIDEN_WORKFLOW="${AIDEN_WORKFLOW:-}"

if [[ -z "$AIDEN_TOKEN" || -z "$AIDEN_ORG_ID" || -z "$AIDEN_BASE_URL" || -z "$AIDEN_WORKFLOW" ]]; then
  missing=""
  [[ -z "$AIDEN_TOKEN"    ]] && missing="${missing}AIDEN_TOKEN "
  [[ -z "$AIDEN_ORG_ID"   ]] && missing="${missing}AIDEN_ORG_ID "
  [[ -z "$AIDEN_BASE_URL" ]] && missing="${missing}AIDEN_BASE_URL "
  [[ -z "$AIDEN_WORKFLOW" ]] && missing="${missing}AIDEN_WORKFLOW"
  cat >&2 <<EOF
Missing: ${missing}
Change records need Aiden 2.0 credentials, an explicit Aiden endpoint, and an
explicit workflow name:

  export AIDEN_TOKEN="stackgen_..."
  export AIDEN_ORG_ID="<your-workspace-uuid>"
  export AIDEN_BASE_URL="https://<your-aiden-host>"   # e.g. https://ai.stackgen.com
  export AIDEN_WORKFLOW="post-stackgen-servicenow-change-request"

Use the Aiden instance where AIDEN_WORKFLOW is published. Neither value has a
default: both name where a completed Apply gets reported, and a guess there
fails right after a successful Apply.
EOF
  echo "NOT_CONFIGURED"
  exit 2
fi

# ---------------------------------------------------------------------------
# Required inputs
# ---------------------------------------------------------------------------
_missing=()
for _var in appStack environment provider region run_type \
            created changed replaced removed \
            plan_stdout cli_run_url correlation_id justification; do
  [[ -z "${!_var:-}" ]] && _missing+=("$_var")
done

if (( ${#_missing[@]} > 0 )); then
  echo "Missing required inputs: ${_missing[*]}" >&2
  echo "BAD_ARGS"
  exit 64
fi

# ---------------------------------------------------------------------------
# Optional inputs with defaults
# ---------------------------------------------------------------------------
executed_via="${executed_via:-}"
backout_plan="${backout_plan:-Revert to the previous Terraform state and re-run Apply from the prior appStack version.}"
test_plan="${test_plan:-Post-apply policy scan reviewed. Service health checks validated after deploy.}"
impact="${impact:-3}"
risk="${risk:-Low}"
start_date="${start_date:-}"
end_date="${end_date:-}"

AIDEN_BASE_URL="${AIDEN_BASE_URL%/}"   # tolerate a trailing slash
AIDEN_MAX_POLLS="${AIDEN_MAX_POLLS:-30}"

# ---------------------------------------------------------------------------
# Cross-check the declared counts against the plan text itself.
#
# The counts are supplied by the caller, and a caller that reconstructs them
# after the fact gets them wrong — an observed failure was changed=1 replaced=1
# removed=1 against a plan that plainly said "0 changed, 0 destroyed". A record
# carrying invented numbers is worse than no record: it looks like verified
# audit data.
#
# Only `changed` is enforced. Terraform folds a replacement into both the add
# and the destroy totals, so `created` and `removed` can legitimately differ
# from the summary line depending on how the caller counts replacements —
# failing on those would reject correct input. "N to change" has no such
# ambiguity.
# ---------------------------------------------------------------------------
PLAN_CHANGED=$(printf '%s' "$plan_stdout" \
  | grep -oE '(Plan: [0-9]+ to add, [0-9]+ to change|Resources: [0-9]+ added, [0-9]+ changed)' \
  | head -1 | grep -oE '[0-9]+ (to change|changed)' | grep -oE '^[0-9]+' || true)

if [[ -n "$PLAN_CHANGED" && "$PLAN_CHANGED" != "$changed" ]]; then
  cat >&2 <<EOF
Counts do not match the plan text.
  changed was given as : ${changed}
  the plan text says   : ${PLAN_CHANGED}
Take the counts from the captured run output instead of restating them.
EOF
  echo "BAD_ARGS"
  exit 64
fi

# ---------------------------------------------------------------------------
# Build the structured payload. One field per line so the workflow parser does
# not depend on any particular JSON/YAML shape inside the LLM input.
# ---------------------------------------------------------------------------
EXECUTED_VIA_LINE=""
[[ -n "$executed_via" ]] && EXECUTED_VIA_LINE="
executed_via: ${executed_via}"

OPTIONAL_DATES=""
[[ -n "$start_date" ]] && OPTIONAL_DATES="${OPTIONAL_DATES}start_date: ${start_date}
"
[[ -n "$end_date"   ]] && OPTIONAL_DATES="${OPTIONAL_DATES}end_date: ${end_date}
"

PAYLOAD_TEXT="Create a ServiceNow change request for this StackGen infrastructure run.

appStack: ${appStack}
environment: ${environment}
provider: ${provider}
region: ${region}
run_type: ${run_type}${EXECUTED_VIA_LINE}
created: ${created}
changed: ${changed}
replaced: ${replaced}
removed: ${removed}
correlation_id: ${correlation_id}
cli_run_url: ${cli_run_url}
justification: ${justification}
impact: ${impact}
risk: ${risk}
backout_plan: ${backout_plan}
test_plan: ${test_plan}
${OPTIONAL_DATES}
plan_stdout:
${plan_stdout}"

# ---------------------------------------------------------------------------
# JSON-encode the payload as a JSON string body (no surrounding quotes).
# Pure awk: strips ANSI colour codes and any remaining control characters that
# would make the JSON invalid, then escapes \, ", tab, CR and newline.
# ---------------------------------------------------------------------------
json_escape() {
  awk '
    BEGIN { ORS = ""; first = 1 }
    {
      line = $0
      gsub(/\033\[[0-9;]*[A-Za-z]/, "", line)   # strip ANSI escape sequences
      gsub(/\r/, "", line)                      # strip CR (CRLF input)
      gsub(/\\/, "\\\\", line)                  # escape backslash first
      gsub(/"/,  "\\\"", line)                  # escape double quote
      gsub(/\t/, "\\t",  line)                  # escape tab
      gsub(/[\001-\010\013\014\016-\037\177]/, "", line)  # drop other controls
      if (first) { first = 0 } else { print "\\n" }
      print line
    }
  '
}

JSON_INPUT=$(printf '%s' "$PAYLOAD_TEXT" | json_escape)

# ---------------------------------------------------------------------------
# Extract the change record number from an execution body.
#
# The body carries the whole agent trace, which can include EXAMPLE numbers from
# the workflow's own prompt. Scanning it blindly and taking the first match can
# return a placeholder, which is worse than returning nothing: a fake number
# looks like a verifiable audit reference. So: prefer structured fields, and
# fall back to a bare scan only when the body contains exactly one distinct
# candidate. Prints nothing and returns 1 when there is no safe answer.
# ---------------------------------------------------------------------------
extract_chg() {
  local body="$1" v cands n
  # Ordered by how the real Aiden trace carries the number. Verified against
  # live executions: the final answer appears as "answer":"CHG…", the agent
  # part as "content":"CHG…", and the tool result as a sentence.
  for pat in '"answer"[[:space:]]*:[[:space:]]*"CHG[0-9]+' \
             '"output"[[:space:]]*:[[:space:]]*"CHG[0-9]+' \
             '"content"[[:space:]]*:[[:space:]]*"CHG[0-9]+' \
             'Created Change Request successfully: CHG[0-9]+' \
             'number[\\"]*[[:space:]]*:[[:space:]]*[\\"]*CHG[0-9]+'; do
    v=$(printf '%s' "$body" | grep -oE "$pat" | grep -oE 'CHG[0-9]+' | head -1 || true)
    [[ -n "$v" ]] && { printf '%s' "$v"; return 0; }
  done
  # Fallback: every remaining candidate, minus the ones sitting inside a tool
  # schema. The workflow's own JSON schema documents the field as
  #   "change_number":{"description":"Change request number (e.g., \"CHG0012345\")"}
  # so a naive scan can return that placeholder — a fake number that looks like
  # a real audit reference. Drop anything whose context says description/e.g.
  cands=$(printf '%s' "$body" | grep -oE '.{0,60}CHG[0-9]+' \
          | grep -vi 'description' | grep -v 'e\.g\.' \
          | grep -oE 'CHG[0-9]+' | sort -u || true)
  n=$(printf '%s' "$cands" | grep -c 'CHG' || true)
  if [[ "$n" == "1" ]]; then printf '%s' "$cands"; return 0; fi
  return 1
}

# ---------------------------------------------------------------------------
# Step 1 — Invoke the workflow
# ---------------------------------------------------------------------------
INVOKE_URL="${AIDEN_BASE_URL}/guild/api/v1/workflows/${AIDEN_WORKFLOW}/run?orgId=${AIDEN_ORG_ID}"

INVOKE_RESPONSE=$(curl -sS -w $'\n__HTTP_STATUS__%{http_code}' \
  -X POST "${INVOKE_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AIDEN_TOKEN}" \
  --data-binary "{\"input\": \"${JSON_INPUT}\"}") || {
    echo "SN_ERROR Aiden invoke request failed (network)"; exit 1; }

HTTP_STATUS=$(printf '%s' "$INVOKE_RESPONSE" | sed -n 's/.*__HTTP_STATUS__\([0-9]*\).*/\1/p')
INVOKE_BODY=$(printf  '%s' "$INVOKE_RESPONSE" | sed 's/__HTTP_STATUS__[0-9]*//')

if [[ "$HTTP_STATUS" != "202" && "$HTTP_STATUS" != "200" ]]; then
  echo "SN_ERROR Aiden invoke failed (HTTP ${HTTP_STATUS})" >&2
  echo "SN_ERROR Aiden invoke failed (HTTP ${HTTP_STATUS})"
  exit 1
fi

TRACE_ID=$(printf '%s' "$INVOKE_BODY" | grep -o '"trace_id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [[ -z "$TRACE_ID" ]]; then
  echo "SN_ERROR no trace_id in Aiden response"
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 2 — Poll until terminal (default max 150 s, every 5 s)
# ---------------------------------------------------------------------------
POLL_URL="${AIDEN_BASE_URL}/guild/api/v1/executions/${TRACE_ID}?orgId=${AIDEN_ORG_ID}"
POLL_COUNT=0
SETTLE_COUNT=0
SETTLE_MAX="${AIDEN_SETTLE_POLLS:-12}"  # ~60s of grace after the turn completes
STATUS=""

while (( POLL_COUNT < AIDEN_MAX_POLLS )); do
  sleep 5

  POLL_RESPONSE=$(curl -sS -w $'\n__HTTP_STATUS__%{http_code}' \
    "${POLL_URL}" -H "Authorization: Bearer ${AIDEN_TOKEN}") || {
      echo "SN_ERROR poll request failed (network) trace_id=${TRACE_ID}"; exit 1; }

  POLL_HTTP=$(printf '%s' "$POLL_RESPONSE" | sed -n 's/.*__HTTP_STATUS__\([0-9]*\).*/\1/p')
  POLL_BODY=$(printf '%s' "$POLL_RESPONSE" | sed 's/__HTTP_STATUS__[0-9]*//')

  if [[ "$POLL_HTTP" != "200" ]]; then
    echo "SN_ERROR poll failed (HTTP ${POLL_HTTP}) trace_id=${TRACE_ID}"
    exit 1
  fi

  # NOTE: do NOT trust `grep '"status"' | head -1` as the execution status. In a
  # large trace the first match belongs to an early ACTIVITY, not to the run —
  # so a still-running execution reads as "completed". That is why big payloads
  # reported chg=unknown while small ones worked: more activities, more chance
  # an early completed one appears first. Success is defined by having the
  # number, not by a status string.

  CHG_NUMBER=$(extract_chg "$POLL_BODY" || true)
  if [[ -n "$CHG_NUMBER" ]]; then
    echo "COMPLETED trace_id=${TRACE_ID} chg=${CHG_NUMBER} correlation_id=${correlation_id}"
    exit 0
  fi

  # Only a terminal failure is read from status, and only when it is the sole
  # value present — an activity that failed inside a run that recovers is not
  # a workflow failure.
  if printf '%s' "$POLL_BODY" | grep -oE '"status"[[:space:]]*:[[:space:]]*"(error|failed)"' >/dev/null 2>&1 \
     && ! printf '%s' "$POLL_BODY" | grep -oE '"status"[[:space:]]*:[[:space:]]*"(running|pending|accepted)"' >/dev/null 2>&1; then
    SUMMARY_MSG=$(printf '%s' "$POLL_BODY" | grep -o '"summary":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
    echo "SN_ERROR Aiden workflow failed trace_id=${TRACE_ID} summary=${SUMMARY_MSG}"
    exit 1
  fi

  # Looks finished but the number has not landed yet — keep waiting, bounded.
  if printf '%s' "$POLL_BODY" | grep -q '"chat_turn_completed"'; then
    SETTLE_COUNT=$((SETTLE_COUNT + 1))
    if (( SETTLE_COUNT >= SETTLE_MAX )); then
      echo "COMPLETED trace_id=${TRACE_ID} chg=unknown correlation_id=${correlation_id}"
      exit 0
    fi
  fi

  POLL_COUNT=$((POLL_COUNT + 1))
done

echo "SN_ERROR timed out after $((AIDEN_MAX_POLLS * 5))s trace_id=${TRACE_ID} last_status=${STATUS}"
exit 1