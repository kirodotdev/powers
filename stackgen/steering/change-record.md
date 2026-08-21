# Change Record — ServiceNow CHG via Aiden 2.0

Optional post-Apply step. A successful Apply produces an auditable ServiceNow
change request carrying the full plan diff, so a reviewer can see exactly what
happened and against which run.

**This step never blocks a deploy.** If credentials are missing, say so in one
line and finish normally. The deploy succeeded; only the record is missing.

## When to run it

| Situation | Action |
|---|---|
| Apply completed, health check passed | Run it |
| Plan completed, no Apply yet | Skip — no infrastructure changed |
| Apply failed, or health check failed | Skip — never record a failed run |
| Any of the four required variables unset | Skip — report "no CHG record created" |
| User says "no change record" / "skip ServiceNow" | Skip |

## Locating the script

The relative path depends on which folder is open in Kiro — the repo root and an
app subfolder are both valid workspaces. Resolve it first, never assume:

```bash
SG_SCRIPT=""
for p in powers/stackgen/scripts/aiden-workflow.sh \
         ../powers/stackgen/scripts/aiden-workflow.sh \
         ../../powers/stackgen/scripts/aiden-workflow.sh \
         ../../../powers/stackgen/scripts/aiden-workflow.sh; do
  [ -f "$p" ] && { SG_SCRIPT="$p"; break; }
done
[ -z "$SG_SCRIPT" ] && SG_SCRIPT=$(find "$HOME/.kiro/powers" -maxdepth 4 -name aiden-workflow.sh 2>/dev/null | head -1)
```

No bare globs: on zsh an unmatched glob aborts the whole command.

If nothing is found, skip the change record and say so in one line. NEVER
recreate the script inline and NEVER call the Aiden API directly instead.

## Credentials

| Variable | Required | Notes |
|---|---|---|
| `AIDEN_TOKEN` | yes | StackGen PAT with GUILD access (`stackgen_…`) |
| `AIDEN_ORG_ID` | yes | Aiden workspace UUID |
| `AIDEN_BASE_URL` | **yes** | Base URL of the Aiden API, e.g. `https://ai.stackgen.com`. Must be the Aiden instance where `AIDEN_WORKFLOW` is published. **No default on purpose** — a guessed endpoint fails right after a successful Apply. Unset is treated as `NOT_CONFIGURED`, which skips safely |
| `AIDEN_WORKFLOW` | **yes** | The GUILD workflow to invoke, e.g. `post-stackgen-servicenow-change-request`. **No default on purpose** — a workflow is published into a specific Aiden workspace, so a name that is correct in one is a 404 in another |
| `AIDEN_MAX_POLLS` | no | Default `30` (× 5 s = 150 s) |

Check silently before running:

```bash
bash "$(dirname "$SG_SCRIPT")/check-change-record-setup.sh"
```

Exit 1 → skip the step. Do not ask the user for tokens mid-deploy.

## Gathering the inputs

Everything comes from the Apply run — never invent a value.

| Input | Source |
|---|---|
| `appStack` | The appStack name from `create_appstack` |
| `environment` | The env profile name used for the run |
| `provider` | `aws` (or `azure` / `gcp`) |
| `region` | Region from the env profile |
| `run_type` | `Apply` |
| `created` `changed` `replaced` `removed` | Parsed from the captured run output — see the per-path table below |
| `correlation_id` | The run ID — differs per path, see below. The idempotency key |
| `cli_run_url` | The run URL — differs per path, see below |
| `plan_stdout` | **The plan text captured at deploy-flow step 11.** Not fetched now: by this point the diff no longer exists anywhere |
| `executed_via` | `saas-runner` or `local-cli` — how the Apply actually ran |
| `justification` | The user's stated reason, or the deploy intent in one sentence |

### Three inputs differ by execution path

`POWER.md` offers the SaaS runner and the local CLI, and falls back from the
first to the second after two failures — so both paths occur in practice.

| Input | SaaS runner | Local CLI (`stackgen provision`) |
|---|---|---|
| `correlation_id` | the Apply `action_run_id` | the CLI Run ID (`sg-clirun-<uuid>`) |
| `cli_run_url` | run URL from `get_action_run` | the CLI run URL |
| counts source | `get_action_run_logs` (`apply_stdout`) | the captured stdout of the provision run |
| `executed_via` | `saas-runner` | `local-cli` |

`executed_via` is not bookkeeping. An Apply run by StackGen's governed runner
and one run from a laptop with personal AWS credentials are different events to
whoever reviews the record, so the record has to say which happened.

The plan text itself is NOT in this table on purpose: capturing it is the same
action on both paths, and a branch there is one more thing to get wrong.

Optional: `backout_plan`, `test_plan`, `impact` (default `3`), `risk` (default
`Low`), `start_date`, `end_date`.

## Running it

Single `execute_bash` call, env vars only — never positional args, because
`plan_stdout` is multi-line. Requires bash: macOS and Linux natively, Windows
via WSL or Git Bash.

```bash
appStack="<name>" environment="<env>" provider=aws region="<region>" \
run_type=Apply \
created=<N> changed=<N> replaced=<N> removed=<N> \
correlation_id="<APPLY_RUN_ID>" \
cli_run_url="<APPLY_RUN_URL>" \
justification="<one sentence>" \
plan_stdout="<PLAN_OUTPUT>" \
bash "$SG_SCRIPT"
```

The script polls to completion itself (150 s default). Do not wrap it in your
own retry loop.

## Reading the output

One line on stdout:

| Output | Meaning | What to do |
|---|---|---|
| `COMPLETED trace_id=… chg=CHG0030002 correlation_id=…` | Record created | Show the **CHG number** to the user — this is the one ID that is always surfaced |
| `COMPLETED … chg=unknown` | Workflow finished, number not parseable | Tell the user the record was created but the number could not be read; give them the Aiden execution link |
| `NOT_CONFIGURED` | Aiden credentials missing | One line: "No CHG record created — Aiden credentials not configured." Stop. Do not retry |
| `BAD_ARGS` | An input was empty | Fix the missing input from the run data and retry **once** |
| `SN_ERROR …` | Aiden/ServiceNow rejected or timed out | Report it in one line with the trace ID. Do not retry blindly |

Re-checking an execution later (e.g. the user asks for the CHG number of an
earlier run):

```bash
curl -sS "${AIDEN_BASE_URL}/guild/api/v1/executions/<trace_id>?orgId=${AIDEN_ORG_ID}" \
  -H "Authorization: Bearer ${AIDEN_TOKEN}"
```

`status` → `completed` (extract `CHG[0-9]*`) · `running`/`pending`/`accepted`
(wait 5 s, max 3 retries) · `error`/`failed` (report `summary`, stop).

Human-readable view: `${AIDEN_BASE_URL}/guild/executions/<trace_id>`.

## Reporting to the user

Append one line to the final deploy result — no extra message, no narration
while the script runs:

```
Change record: CHG0030002
```

or, when skipped:

```
Change record: not created (Aiden credentials not configured)
```

## Never

- Never create a change record for a failed Plan or a failed Apply.
- Never invent `correlation_id`, `cli_run_url`, a CHG number, or resource counts.
- Never rebuild the plan text with `terraform show`, `tofu show`, or the `.tfplan`
  file. Those give current state, not the diff. If the plan output was not
  captured at step 11, skip the record and say so.
- Never call the ServiceNow API directly, and never use ServiceNow basic-auth
  credentials (`SN_USER` / `SN_PASSWORD`) — Aiden is the only supported path.
- Never modify or close an existing change record.
- Never echo `AIDEN_TOKEN` or write it into a file in this repository.
- Never let a change-record failure change the reported deploy outcome.