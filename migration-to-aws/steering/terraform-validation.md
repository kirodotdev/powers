# Terraform Validation Protocol (Shared Reference)

> Canonical definition of the `fmt → init → validate → fix-and-retry → offline-fallback` protocol used by any phase that emits Terraform. Referenced by `steering/generate-artifacts-infra.md` Step 6 and reusable by future artifact generators.

## When to Use

Any step that writes a `terraform/` directory and wants to block phase completion on HCL-level defects while still degrading gracefully when the provider registry is unreachable.

## Protocol

Working directory: the `terraform/` directory under test. All commands run non-interactively (`-input=false -no-color` where supported).

### Stage A — Format

1. `terraform fmt -recursive` (auto-apply).
2. `terraform fmt -recursive -check`. If non-zero, enter the Fix-and-Retry loop targeting fmt failures. On success, advance to Stage B.

### Stage B — Initialize (no backend)

1. `terraform init -backend=false -input=false -no-color`, capturing stderr.
2. On non-zero exit, run the **Offline Detection** algorithm below on the captured stderr.
   - If classified network-unavailable: set `validation_status = "passed_degraded_offline"`, emit warning, SKIP Stage C, proceed to Stage E. Do NOT enter the retry loop.
   - Otherwise: enter the Fix-and-Retry loop targeting init failures.
3. On success, advance to Stage C.

### Stage C — Validate

1. `terraform validate -json`, capturing stdout.
2. On non-zero exit, parse `.diagnostics[]` and enter the Fix-and-Retry loop targeting validate failures.
3. On success, set `validation_status = "passed"` and advance to Stage E.

### Stage D — Fix-and-Retry Loop

Attempt budget: **3 attempts per batch**. Hardcoded. Not configurable via `preferences.json`.

Per attempt:

1. Read the failing command's error output:
   - fmt: the diff shown by `fmt -recursive -check` (list of files that would change).
   - init: the stderr captured from `terraform init`.
   - validate: the JSON diagnostics array from `terraform validate -json`.
2. **Group errors by file path.** For each file, open it once, apply all targeted edits for that file, close. Never rewrite a file wholesale; only edit the lines/blocks reported.
3. Re-run only the failing command (fmt -check, init, or validate).
4. If it passes, exit the loop and return to the calling stage's success path.
5. If the same `(file, line, summary)` reappears on consecutive attempts, emit a "same error recurring" signal in the attempt log — this is a warning only; continue to the next attempt.

On the 3rd consecutive failure in a batch, prompt the user:

```
Terraform validation failed after 3 automated fix attempts.
Last error: <one-line summary>
[retry] attempt 3 more fixes
[skip]  proceed with warning (validation_status = skipped_user_continue)
[abort] stop, do NOT write .phase-status.json
Choose [retry/skip/abort]:
```

User choices:

- **retry** — reset the per-batch attempt counter to 0, grant 3 more attempts, continue. The cumulative `attempts` field in `validation-report.json` is NOT reset (it keeps incrementing).
- **skip** — set `validation_status = "skipped_user_continue"`, emit warning, proceed to Stage E. Phase Completion is allowed.
- **abort** — set `validation_status = "skipped_user_abort"`, write `validation-report.json` with that status, STOP. **Do NOT write to `.phase-status.json`.** The caller (generate.md) relies on seeing no completion signal.

### Stage E — Emit validation-report.json

Write `$MIGRATION_DIR/validation-report.json` following the schema in the **Report Schema** section below.

## Offline Detection

```
FUNCTION isNetworkUnavailable(init_stderr)
  INPUT: init_stderr (string, captured stderr of `terraform init`)
  OUTPUT: boolean

  patterns ← ["lookup", "dial tcp", "connection refused", "timeout", "no such host"]

  IF init_stderr IS NULL OR trim(init_stderr) = "" THEN
    RETURN false   // empty stderr → treat as non-network failure (let retry loop handle)
  END IF

  haystack ← toLowerCase(init_stderr)

  FOR EACH p IN patterns DO              // first-match-wins; order does not matter for correctness
    IF contains(haystack, toLowerCase(p)) THEN
      RETURN true
    END IF
  END FOR

  RETURN false
END FUNCTION
```

**Rules**:

- **Source stream**: stderr of `terraform init` only. Do not read stdout for classification (terraform writes progress to stdout, errors to stderr).
- **Case sensitivity**: case-insensitive. Lowercase both the haystack and the patterns before comparing.
- **Match semantics**: first-match-wins. Any pattern hit short-circuits to `true`. Full-stderr scan, not per-line.
- **Empty stderr**: treat as non-network failure. The retry loop runs. This prevents silent offline-fallback when terraform fails for an unrelated reason (e.g., a panic) and produces no stderr.

## Fix-and-Retry Algorithm (pseudocode)

```
FUNCTION fixAndRetry(stage, initial_error_output)
  INPUT:
    stage ∈ {"fmt", "init", "validate"}
    initial_error_output — captured output from the failing command
  OUTPUT:
    terminal_status ∈ {"passed", "skipped_user_continue", "skipped_user_abort"}
    cumulative_attempts (int)

  cumulative_attempts ← 0
  last_error_output ← initial_error_output
  recurring_errors ← ∅

  LOOP                                // outer loop: retry user choice may re-enter
    batch_attempt ← 0
    last_batch_errors ← ∅

    WHILE batch_attempt < 3 DO
      batch_attempt ← batch_attempt + 1
      cumulative_attempts ← cumulative_attempts + 1

      errors ← parseErrors(stage, last_error_output)
      errors_by_file ← groupBy(errors, e → e.file)

      FOR EACH (file, file_errors) IN errors_by_file DO
        applyTargetedEdits(file, file_errors)    // LLM edits only reported sites
      END FOR

      (exit_code, new_output) ← run(stage)       // rerun only the failing command

      IF exit_code = 0 THEN
        // advance the caller to the next stage; this function returns "passed"
        // once the caller reaches Stage C success. For fmt/init this means
        // success at the current stage; the caller chains into the next.
        RETURN ("passed", cumulative_attempts)
      END IF

      // Detect recurring errors for logging (warning signal, not a control-flow change)
      new_errors_set ← set of (file, line, summary) from parseErrors(stage, new_output)
      recurring ← last_batch_errors ∩ new_errors_set
      IF recurring ≠ ∅ THEN
        emitWarning("same error recurring: " + recurring)
        recurring_errors ← recurring_errors ∪ recurring
      END IF
      last_batch_errors ← new_errors_set
      last_error_output ← new_output
    END WHILE

    choice ← promptUser("retry/skip/abort")

    IF choice = "retry" THEN
      // reset per-batch counter; outer loop continues for 3 more attempts
      CONTINUE
    ELSE IF choice = "skip" THEN
      RETURN ("skipped_user_continue", cumulative_attempts)
    ELSE IF choice = "abort" THEN
      writeValidationReport(status="skipped_user_abort", attempts=cumulative_attempts, ...)
      STOP_WITHOUT_PHASE_STATUS_WRITE()   // MUST NOT update .phase-status.json
    END IF
  END LOOP
END FUNCTION
```

**Key contract points**:

- The cumulative `attempts` counter in `validation-report.json` counts every rerun across all batches, including after a user `retry`. It never resets.
- The per-batch counter (triggering the user prompt) resets to 0 on `retry`.
- On `abort`, the function terminates the whole run without touching `.phase-status.json`. The calling phase (`generate.md`) must see the absence of a completion write and NOT advance the state machine.
- "Progress" vs "same error recurring": progress is when `exit_code == 0` OR when `last_batch_errors \ new_errors_set ≠ ∅` (at least one error disappeared). A fully-overlapping error set across consecutive attempts triggers the warning but does not change control flow.

## Report Schema

```json
{
  "$schema": "validation-report/v1",
  "status": "passed | passed_degraded_offline | skipped_user_continue | skipped_user_abort",
  "attempts": 0,
  "errors_found": [
    {
      "file": "string (relative to terraform/)",
      "line": "integer (1-based, 0 if unknown)",
      "severity": "error | warning",
      "summary": "string (≤200 chars, first line of diagnostic)"
    }
  ],
  "errors_fixed": [
    {
      "file": "string",
      "line": "integer",
      "severity": "error | warning",
      "summary": "string",
      "attempt": "integer (1-indexed; which retry attempt repaired it)"
    }
  ],
  "offline_fallback_used": false,
  "timestamp": "ISO 8601 UTC (e.g., 2026-02-26T15:35:22Z)",
  "terraform_version": "string (output of `terraform version -json | .terraform_version`; empty string if unavailable)"
}
```

**Field rules**:

- `status`: MUST match one of the four enum values. MUST equal the terminal `validation_status`.
- `attempts`: integer ≥ 0. Counts total fix-and-retry attempts across all batches (a `retry` user choice that grants 3 more attempts continues to increment this counter; it does NOT reset). Value 0 means fmt/init/validate all passed on first try.
- `errors_found`: every distinct diagnostic emitted across all attempts, deduplicated by `(file, line, summary)`.
- `errors_fixed`: subset of `errors_found` that did not reappear after the indicated `attempt`.
- `offline_fallback_used`: `true` iff `status == "passed_degraded_offline"`.
- `terraform_version`: populated by parsing `terraform version -json`; if that command fails, fall back to empty string (never crash on this).

**Example** (passed after 2 retry attempts repaired a missing brace and an unresolved reference):

```json
{
  "$schema": "validation-report/v1",
  "status": "passed",
  "attempts": 2,
  "errors_found": [
    {
      "file": "vpc.tf",
      "line": 47,
      "severity": "error",
      "summary": "Missing close brace on resource \"aws_subnet\" \"private_a\""
    },
    {
      "file": "compute.tf",
      "line": 12,
      "severity": "error",
      "summary": "Reference to undeclared resource aws_security_group.app"
    }
  ],
  "errors_fixed": [
    {
      "file": "vpc.tf",
      "line": 47,
      "severity": "error",
      "summary": "Missing close brace on resource \"aws_subnet\" \"private_a\"",
      "attempt": 1
    },
    {
      "file": "compute.tf",
      "line": 12,
      "severity": "error",
      "summary": "Reference to undeclared resource aws_security_group.app",
      "attempt": 2
    }
  ],
  "offline_fallback_used": false,
  "timestamp": "2026-02-26T15:37:04Z",
  "terraform_version": "1.9.5"
}
```
