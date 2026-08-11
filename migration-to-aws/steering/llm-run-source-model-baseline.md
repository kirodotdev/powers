# Run Source-Model Baseline

The Track 2 evaluator scores Bedrock outputs against a baseline. When that
baseline is just an agent-synthesized `assistant_response` from the golden
dataset, "Bedrock matches baseline" only proves Bedrock matches the agent's
own writing — PM rejected the previous "100% pass rate" report on exactly
this gap. This skill produces a fresh side-by-side baseline by re-running
each golden prompt against the customer's live source model.

The skill uses Python stdlib `urllib.request` only — no SDK install needed;
it runs fine under the pinned `uv` toolchain.

`<REPO>` is the repository path supplied in your context (the evaluator that
loads this skill receives it). `<scriptsDir>` is the pinned-toolchain scripts
directory supplied in your context. Substitute both before running.

## Input

- `source_provider`: `openai` | `anthropic` | `google`
- `source_model_id`: the model ID to call (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`, `gemini-1.5-pro`)
- `golden_dataset_path`: usually `<REPO>/.saws-migrate/golden-dataset/prompts.jsonl`
- `output_path`: usually `<REPO>/.saws-migrate/eval-results/source_baselines.jsonl`

## Preconditions

- `<REPO>/.saws-migrate/.source-provider-env` exists (written by the
  orchestration skill's Phase B3 when the user provided a source-provider
  API key). The file contains a single `KEY=VALUE` line, one of:
  `OPENAI_API_KEY=...` / `ANTHROPIC_API_KEY=...` / `GEMINI_API_KEY=...`.
- The golden dataset JSONL exists at `golden_dataset_path` and each entry
  has at least `id`, `user_prompt`, optionally `system_prompt`.

If the env file is absent, do NOT run this skill — the caller should set
`live_source_baseline: false` and skip to static baselines.

## Procedure

### Step 1: Verify the env file

```bash
test -f <REPO>/.saws-migrate/.source-provider-env && echo present || echo absent
grep -qE '^(OPENAI|ANTHROPIC|GEMINI)_API_KEY=.+' <REPO>/.saws-migrate/.source-provider-env 2>/dev/null && echo format_ok || echo format_bad
```

- `absent` → return immediately with `status: "skipped"`.
- `present` + `format_bad` → the file exists but has no parseable `KEY=VALUE` line (e.g. a bare
  key was pasted without the env-var prefix). Do NOT proceed — the resolver would silently hit
  the `no_key` path. Return `status: "skipped"` with a note telling the caller the env file is
  malformed and needs re-collection in `KEY=VALUE` form. Never print the file's contents.
- `present` + `format_ok` → continue.

### Step 1.5: Resolve the source model ID against the live provider catalog

The `source_model_id` you were handed is the user's STATED source model
(extracted by llm2bedrock-code-analyzer / log-ingestor from the customer's source
code or plan). It might be a slight misspelling, a stale alias, or a
date-suffixed variant compared to what the provider actually exposes
right now. Before running the baseline, check that the ID exists in the
provider's live catalog and resolve to the closest valid variant **of
the SAME model line** if needed.

🚫 **Hard rule — model line is sacred.** You may auto-resolve `gpt-5.4`
to `gpt-5.4-2024-08-06` (a date-pinned variant of the same model). You
MUST NOT resolve it to `gpt-5`, `gpt-5.5`, `gpt-4o`, `gpt-5.4-mini`,
`gpt-5.4-pro`, `gpt-5.4-latest`, or any other model line / alias. The
migration report's pass rate is meaningful only when the live baseline
is the SAME deterministic model the customer said they were running. A
cross-line swap or a moving alias is worse than no baseline.

Write a small resolver script and run it. The resolver:

1. Calls the provider's list-models endpoint with the env key:
   - OpenAI: `GET https://api.openai.com/v1/models`
   - Anthropic: `GET https://api.anthropic.com/v1/models`
   - Gemini: `GET https://generativelanguage.googleapis.com/v1beta/models?key=...`
2. Looks for, in order:
   - **Exact match** for `source_model_id` → use unchanged.
   - **Safe prefix match**: a catalog ID that starts with
     `<source_model_id>-` AND whose suffix is a date (`YYYY-MM-DD`) or
     pure version number (e.g. `2`, `3.1`). These are the same model
     pinned to a date or version — same-line. Examples:
     `gpt-5.4` matches `gpt-5.4-2026-03-05`; `claude-3-5-sonnet`
     matches `claude-3-5-sonnet-20241022`. Does NOT match `gpt-5`,
     `gpt-5.5`, `gpt-54` (different lines), nor `gpt-5.4-mini`,
     `gpt-5.4-pro`, `gpt-5.4-latest` (alphabetic suffixes — those are
     either different model lines or non-deterministic aliases).
     If multiple safe variants, pick the shortest ID (most general).
   - **Ambiguous prefix** (catalog has prefix hits but ALL of them have
     alphabetic / alias suffixes — `mini`, `nano`, `pro`, `turbo`,
     `latest`, `codex`, etc.): do NOT auto-pick. Surface the prefix
     hits as `not_found` candidates so the user picks the right
     model line themselves.
   - **No match** → emit a JSON record with the top 5 catalog IDs
     whose names share the longest common prefix with
     `source_model_id`, for the caller to show the user.

Example resolver script (OpenAI shown; adapt headers/path for
Anthropic / Gemini). Use the `Write` tool to save it to a local temp file
(e.g. `<REPO>/.saws-migrate/eval-results/resolve_source_model.py`):

```python
import json, os, sys, urllib.request

with open("<REPO>/.saws-migrate/.source-provider-env") as f:
    for line in f:
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

PLAN_ID = os.environ["PLAN_MODEL_ID"]

def list_openai():
    req = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return [m["id"] for m in json.loads(r.read())["data"]]

def list_anthropic():
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return [m["id"] for m in json.loads(r.read())["data"]]

def list_gemini():
    url = (f"https://generativelanguage.googleapis.com/v1beta/models"
           f"?key={os.environ['GEMINI_API_KEY']}")
    with urllib.request.urlopen(url, timeout=30) as r:
        # Gemini returns names like "models/gemini-1.5-pro"; strip prefix
        return [m["name"].split("/", 1)[-1] for m in json.loads(r.read()).get("models", [])]

if "OPENAI_API_KEY" in os.environ:
    catalog = list_openai()
elif "ANTHROPIC_API_KEY" in os.environ:
    catalog = list_anthropic()
elif "GEMINI_API_KEY" in os.environ:
    catalog = list_gemini()
else:
    print(json.dumps({"status": "no_key"})); sys.exit(2)

if PLAN_ID in catalog:
    print(json.dumps({"status": "exact", "resolved_id": PLAN_ID}))
    sys.exit(0)

prefix_hits = [m for m in catalog
               if m == PLAN_ID
               or m.startswith(PLAN_ID + "-")]

# A bare prefix match is NOT enough to auto-resolve. "gpt-4o-mini",
# "gpt-5-pro", "claude-3-5-sonnet-latest" all start with a plausible
# plan ID's prefix but are different model lines / non-deterministic
# aliases. Only auto-pick when the suffix after PLAN_ID is a date
# (YYYY-MM-DD) or pure version number — these are the same model line,
# just a date- or version-pinned variant. Any alphabetic suffix
# (mini, nano, pro, turbo, codex, latest, ...) escalates to the user.
import re
SAFE_SUFFIX = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d[\d.]*$")

def safe_variant(catalog_id):
    if catalog_id == PLAN_ID:
        return True
    suffix = catalog_id[len(PLAN_ID) + 1:]  # strip "PLAN_ID-"
    return bool(SAFE_SUFFIX.match(suffix))

safe_hits = [m for m in prefix_hits if safe_variant(m)]
if safe_hits:
    safe_hits.sort(key=len)
    print(json.dumps({"status": "prefix",
                      "resolved_id": safe_hits[0],
                      "all_hits": safe_hits}))
    sys.exit(0)

# Prefix matched but ONLY via unsafe suffixes — fall through to
# user-pick path with the prefix hits surfaced as candidates so the
# user can pick the right model line themselves.
if prefix_hits:
    print(json.dumps({"status": "not_found",
                      "candidates": prefix_hits[:5],
                      "ambiguous_prefix": True}))
    sys.exit(0)

# No prefix match — return top 5 nearest (longest common prefix len)
def lcp(a, b):
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i

ranked = sorted(catalog, key=lambda m: -lcp(m, PLAN_ID))[:5]
print(json.dumps({"status": "not_found", "candidates": ranked}))
```

Run it through the pinned toolchain, passing the plan model id via env:

```bash
PLAN_MODEL_ID=<source_model_id> \
  uv run --python '>=3.10' --with 'boto3>=1.35,<2' --with 'botocore>=1.35,<2' python <REPO>/.saws-migrate/eval-results/resolve_source_model.py
```

Interpret the JSON output:

| `status`    | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exact`     | `resolved_id == source_model_id`. Continue to Step 2 with `SOURCE_MODEL_ID = source_model_id`. No notes entry needed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `prefix`    | Use `resolved_id` as `SOURCE_MODEL_ID` for Step 2. Caller appends to the evaluator's returned notes field: `live baseline used <resolved_id> (resolved from plan id <source_model_id>)`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `not_found` | Do NOT auto-pick a catalog entry and do NOT prompt — the evaluator that loads this skill is non-interactive. Skip the live baseline: return `live_source_baseline: false` and record the situation in the evaluator's `notes` so the orchestration skill can surface the model choice to the user. Include up to 5 candidates from the JSON in the note, **using the raw catalog ID exactly as returned by the provider — do NOT add invented qualifiers like "(closest match)", "(latest stable)", "(recommended)", or any other editorializing tag. The skill has no basis to rank these; the user does.** Phrasing depends on the `ambiguous_prefix` flag in the JSON: if `true`, the candidates DO start with the plan ID but only via alphabetic / alias suffixes (e.g. `gpt-5.4-mini`, `gpt-5.4-pro`); note `plan source model <source_model_id> has prefix matches in the <provider> catalog but only as different model lines or non-deterministic aliases — orchestration skill should ask the user to pick the right model line or skip the live baseline; candidates: <list>`. Otherwise (no prefix hits at all): `plan source model <source_model_id> not in <provider> catalog — orchestration skill should ask the user to pick the closest match or skip the live baseline; candidates: <list>`. |
| `no_key`    | env file malformed; return `live_source_baseline: false`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |

If the orchestration skill later re-invokes the baseline with a user-chosen
candidate, the caller appends to notes: `live baseline used <chosen_id> (selected from candidates after plan id <source_model_id> not found, confirmed by user)`.

NEVER silently substitute a different model line. The `prefix` rule
above is the only automatic substitution allowed.

### Step 2: Write the runner script

Use the `Write` tool to save it to a local temp file
(e.g. `<REPO>/.saws-migrate/eval-results/source_baseline.py`):

```python
import json, os, sys, urllib.request, urllib.error

with open("<REPO>/.saws-migrate/.source-provider-env") as f:
    for line in f:
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k] = v

SOURCE_MODEL_ID = os.environ.get("SOURCE_MODEL_ID", "<source_model_id>")

def call_openai(system, user_text):
    # Note: requests intentionally use provider defaults for temperature/top_p —
    # the golden dataset doesn't record per-request sampling params, and the same
    # defaults-only shape is used for all three providers so the comparison is
    # apples-to-apples. maxTokens 4096 matches the Bedrock eval side.
    req_body = {
        "model": SOURCE_MODEL_ID,
        "messages": ([{"role": "system", "content": system}] if system else []) +
                    [{"role": "user", "content": user_text}],
        # gpt-5.x rejects max_tokens (HTTP 400 unsupported_parameter) and
        # requires max_completion_tokens. The newer name is accepted by all
        # current models (gpt-3.5-turbo / gpt-4-turbo / gpt-4.1 / gpt-4o too),
        # so we send it unconditionally — no per-model fallback needed.
        "max_completion_tokens": 4096,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]

def call_anthropic(system, user_text):
    req_body = {
        "model": SOURCE_MODEL_ID,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": user_text}],
    }
    if system:
        req_body["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(req_body).encode("utf-8"),
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]

def call_gemini(system, user_text):
    req_body = {
        "contents": [{"parts": [{"text": user_text}]}],
        # parity with the other providers' 4096-token cap
        "generationConfig": {"maxOutputTokens": 4096},
    }
    if system:
        # systemInstruction mirrors how the customer's app passes system prompts —
        # concatenating into the user turn would change model behavior vs production.
        req_body["systemInstruction"] = {"parts": [{"text": system}]}
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{SOURCE_MODEL_ID}:generateContent?key={os.environ['GEMINI_API_KEY']}")
    req = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]

if "OPENAI_API_KEY" in os.environ:
    call = call_openai
elif "ANTHROPIC_API_KEY" in os.environ:
    call = call_anthropic
elif "GEMINI_API_KEY" in os.environ:
    call = call_gemini
else:
    print("FAIL: no recognized provider key in <REPO>/.saws-migrate/.source-provider-env",
          file=sys.stderr)
    sys.exit(2)

with open(os.environ.get("GOLDEN_DATASET_PATH", "<REPO>/.saws-migrate/golden-dataset/prompts.jsonl")) as f:
    prompts = [json.loads(line) for line in f]

# Partial-resume guard: prompts whose id already has a LIVE row in the output
# are skipped — re-calling the source provider for them would double-spend the
# user's budget. Failed rows (non-"live" status) are retried.
output_path = os.environ.get("OUTPUT_PATH", "<REPO>/.saws-migrate/eval-results/source_baselines.jsonl")
results = []
done_live = set()
if os.path.exists(output_path):
    with open(output_path) as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if row.get("status") == "live":
                    results.append(row)
                    done_live.add(row["id"])
prompts = [p for p in prompts if p["id"] not in done_live]
if done_live:
    print(f"RESUME: {len(done_live)} live baselines kept, {len(prompts)} to fetch")

for p in prompts:
    try:
        out = call(p.get("system_prompt") or "", p["user_prompt"])
        results.append({"id": p["id"], "source_response": out, "status": "live"})
    except urllib.error.HTTPError as e:
        results.append({"id": p["id"], "source_response": "",
                        "status": f"http_{e.code}: {e.reason}"})
    except Exception as e:
        results.append({"id": p["id"], "source_response": "",
                        "status": f"error: {type(e).__name__}: {e}"})

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")

ok = sum(1 for r in results if r["status"] == "live")
print(f"live source baselines: {ok}/{len(results)}")
```

### Step 3: Execute

Pass `SOURCE_MODEL_ID`, `GOLDEN_DATASET_PATH`, `OUTPUT_PATH` via env so the
script does not need substitution:

```bash
SOURCE_MODEL_ID=<source_model_id> \
  GOLDEN_DATASET_PATH=<golden_dataset_path> \
  OUTPUT_PATH=<output_path> \
  uv run --python '>=3.10' --with 'boto3>=1.35,<2' --with 'botocore>=1.35,<2' python <REPO>/.saws-migrate/eval-results/source_baseline.py
```

### Step 4: Classify the result

Parse the printed `live K/N` line and inspect the JSONL.

| Outcome                                                          | Caller should set                                                                                                                                                                              |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live N/N` (all succeed)                                         | `live_source_baseline: true`, all prompts have live `source_response`                                                                                                                          |
| `live K/N`, `0 < K < N`                                          | `live_source_baseline: true`, prompts with `status != "live"` fall back to static baseline                                                                                                     |
| `live 0/N`, all `http_401` / `http_403`                          | invalid key — the evaluator returns `blocked` with `reason: source_key_auth` (per the evaluator prompt) so the orchestration skill asks the user for a new key or to skip; do NOT echo the key |
| `live 0/N`, all network errors (DNS / connect refused / timeout) | `live_source_baseline: false`, host cannot reach provider; banner notes the gap                                                                                                                |
| Script exit code 2 (no recognized key in env file)               | `live_source_baseline: false`, file is malformed                                                                                                                                               |

## Security

- Never echo, log, or include the API key value in any returned notes or
  output (including any `blocked` detail). The key only lives in
  `<REPO>/.saws-migrate/.source-provider-env` on the local host.
- The script reads the key from the env file into `os.environ` only —
  never writes it to stdout or to the output JSONL.

## Output contract

`source_baselines.jsonl`, one record per line:

```json
{
  "id": "<prompt_id>",
  "source_response": "<text or empty>",
  "status": "live | http_<code>: <reason> | error: <type>: <message>"
}
```

Only records with `status: "live"` carry a usable `source_response`. The
caller (llm2bedrock-prompt-evaluator Step 4) merges these into `raw_results.jsonl`
and falls back to the dataset's stored `assistant_response` for any
prompt without a live response.
