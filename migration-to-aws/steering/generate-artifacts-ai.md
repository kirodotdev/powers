# Generate Phase: AI Artifact Generation

> Loaded by generate.md when generation-ai.json and aws-design-ai.json exist.

**Execute ALL steps in order. Do not skip or optimize.**

## Overview

Generate migration artifacts from the AI migration plan and design. Artifacts vary by gateway type detected in discovery.

**Outputs (all users):**

- `ai-migration/setup_bedrock.sh` — Bedrock model access and IAM setup
- `ai-migration/test_comparison.py` — A/B test harness (always Python)

**Outputs (direct SDK users — `ai_framework` = `"direct"`):**

- `ai-migration/provider_adapter.{py,js,go}` — Provider abstraction with feature flag

**Outputs (gateway users — `ai_framework` != `"direct"`):**

- `ai-migration/gateway_config.{yaml,py,json}` — Gateway-specific configuration snippet

**Outputs (if user opted into model evaluation in generate-ai.md Part 0):**

- `ai-migration/eval-prompts.jsonl` — Evaluation prompt dataset
- `ai-migration/run-evaluation.sh` — Bedrock evaluation job script

## Prerequisites

Read from `$MIGRATION_DIR/`:

- `aws-design-ai.json` (REQUIRED) — AI architecture with model mappings and code migration plan
- `generation-ai.json` (REQUIRED) — AI migration plan with timeline and rollback strategy
- `ai-workload-profile.json` (REQUIRED) — AI workload profile with models, languages, and capabilities

If any required file is missing: **STOP**. Output: "Missing required artifact: [filename]. Complete the prior phase that produces it."

---

## Step 0: Determine Artifact Path

Check `preferences.json` → `ai_constraints.ai_framework.value`:

- `"direct"` or absent → Generate provider adapter (Step 1) + setup (Step 3) + test harness (Step 2)
- `"llm_router"`, `"api_gateway"`, `"voice_platform"`, or `"framework"` → Skip Step 1, generate gateway config (Step 3B) instead

**Determine language** (direct SDK users only): Read `ai-workload-profile.json` → `integration.languages` array. Use the first entry: `"python"` → `.py`, `"javascript"`/`"typescript"` → `.js`, `"go"` → `.go`, other/unknown → `.py`.

---

## Step 1: Generate Provider Adapter (Direct SDK Only)

Generate `ai-migration/provider_adapter.{py,js,go}` — an abstraction layer that lets the user switch between the source AI provider and Bedrock via an environment variable.

**Requirements:**

- Read `AI_PROVIDER` env var to select provider: `vertex_ai` (current), `bedrock` (target), `shadow` (both — return source response, log Bedrock response)
- Expose only the methods matching capabilities in `ai-workload-profile.json` → `integration.capabilities_summary`:
  - `text_generation: true` → `generate(prompt) → str`
  - `streaming: true` → `generate_stream(prompt) → Iterator[str]`
  - `embeddings: true` → `embed(text) → list[float]`
- **Source provider class**: Use SDK imports from `ai-workload-profile.json` → `integration.sdk_imports`. Use model IDs from `ai-workload-profile.json` → `models[].model_id`.
- **Bedrock provider class**: Use `boto3` Converse API (`converse` for generate, `converse_stream` for streaming, `invoke_model` for embeddings with Titan). Use model IDs from `aws-design-ai.json` → `ai_architecture.bedrock_models[].aws_model_id`. Use region from `preferences.json` → `design_constraints.target_region`.
- **Shadow mode**: Send requests to both providers, return source response, log Bedrock response for comparison.
- Include error handling and logging for API calls.

For JS: use `@aws-sdk/client-bedrock-runtime` + `@google-cloud/vertexai`. For Go: use `github.com/aws/aws-sdk-go-v2/service/bedrockruntime` + `cloud.google.com/go/aiplatform`.

---

## Step 2: Generate Test Comparison Harness

Generate `ai-migration/test_comparison.py` — always Python regardless of adapter language.

**Requirements:**

- Accept prompts from a JSON file (`--prompts`) or use built-in defaults (`--quick`)
- Run each prompt against both the source provider and Bedrock
- Measure per-prompt: latency (ms), success/failure, response text (truncated to 500 chars)
- Compute summary statistics: p50/p95/mean latency per provider, quality score (trait matching against expected traits), pass/fail criteria
- Pass criteria: Bedrock latency ≤ 2x source latency, mean quality score ≥ 0.9
- Output structured JSON to `--output` (default: `comparison_results.json`)
- Built-in test prompts: include 3-5 prompts based on `ai-workload-profile.json` → `models[].usage_context` covering the primary use case
- Import the provider adapter via `from provider_adapter import get_provider`

---

## Step 3: Generate Bedrock Setup Script

Generate `ai-migration/setup_bedrock.sh`.

**Requirements:**

- Dry-run by default (`--execute` flag to run for real)
- Step 1 — Request model access: List each model from `aws-design-ai.json` → `bedrock_models[].aws_model_id` and the embedding model
- Step 2 — Create IAM role: Trust policy for the compute platform (Lambda, ECS, or EC2 based on `aws-design.json` if present). Bedrock policy: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` scoped to `arn:aws:bedrock:*::foundation-model/*`
- Step 3 — Print required environment variables: `AWS_REGION`, `AI_PROVIDER=bedrock`, model IDs
- Step 4 — Verification: Test Bedrock access with a simple `converse` call using the primary model
- If `$MIGRATION_DIR/terraform/` exists, print coordination note: "Ensure the IAM role is referenced in compute.tf task definitions"
- Use region from `preferences.json` → `design_constraints.target_region`

---

## Step 3B: Generate Gateway Configuration (Gateway Users Only)

Skip if `ai_framework` = `"direct"` or absent. Read `preferences.json` → `ai_constraints.ai_framework.value` to determine format.

**`"llm_router"`** → Generate `gateway_config.yaml` (LiteLLM format):

- Map each model from `aws-design-ai.json` to a `bedrock/MODEL_ID` entry with `aws_region_name`
- Include embedding model entry if embeddings are used
- Note required env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

**`"framework"`** → Generate `gateway_config.py`:

- Show before/after import swap for the detected framework (`ai-workload-profile.json` → `integration.sdk_imports`)
- LangChain: `langchain_google_vertexai` → `langchain_aws.ChatBedrock` (or `langchain_openai` → `langchain_aws.ChatBedrock`)
- LlamaIndex: `llama_index.llms.vertex` → `llama_index.llms.bedrock_converse`
- Include pip install note for the AWS package

**`"voice_platform"`** → Generate `gateway_config.json`:

- Dashboard configuration steps: add Bedrock as provider, set model ID, set region, test before switching production
- Include the Bedrock model ID and region from design artifacts

**`"api_gateway"`** → Generate `gateway_config.yaml`:

- Upstream URL: `https://bedrock-runtime.{region}.amazonaws.com`
- Auth: AWS SigV4 signing for the `bedrock` service
- Note: Converse API endpoint is `POST /model/{modelId}/converse`
- Include gateway-specific notes (Kong plugin, Apigee policy)

---

## Step 3C: Generate Evaluation Artifacts (If User Opted In)

Skip if the user did not opt into model evaluation in `generate-ai.md` Part 0.

**`eval-prompts.jsonl`**: Generate 10-20 domain-specific prompts in JSONL format (`{"prompt": "...", "referenceResponse": "", "category": "..."}`). Base prompts on `ai-workload-profile.json` → `models[].usage_context`. Include function-calling prompts if `capabilities_summary.function_calling` is true, retrieval prompts if RAG patterns were detected. Include 2-3 edge case prompts.

**`run-evaluation.sh`**: Dry-run by default. Creates S3 bucket, uploads prompts, calls `aws bedrock create-evaluation-job` with model IDs from `aws-design-ai.json`, downloads results. Use the same model IDs and region as `setup_bedrock.sh`.

---

## Step 4: Self-Check

Verify all generated artifacts:

- [ ] Provider adapter (or gateway config) uses actual model IDs from `aws-design-ai.json` — no placeholders
- [ ] Only capabilities present in `capabilities_summary` have methods/tests generated
- [ ] Feature flag (`AI_PROVIDER` env var) controls provider selection in adapter
- [ ] Test harness includes domain-specific prompts from `usage_context`
- [ ] Test harness produces structured JSON output with latency and quality metrics
- [ ] Setup script has correct region from `preferences.json`
- [ ] Setup script IAM role follows least privilege
- [ ] All scripts default to dry-run mode
- [ ] Evaluation artifacts (if generated) have correct model IDs and region
- [ ] No hardcoded credentials in any file

## Phase Completion

Report generated files to the parent orchestrator. **Do NOT update `.phase-status.json`** — the parent `generate.md` handles phase completion.

Output:

```
Generated AI migration artifacts:
- ai-migration/setup_bedrock.sh
- ai-migration/test_comparison.py
- ai-migration/provider_adapter.{py|js|go}    # Direct SDK users only
- ai-migration/gateway_config.{yaml|py|json}  # Gateway users only
- ai-migration/eval-prompts.jsonl              # If evaluation opted in
- ai-migration/run-evaluation.sh               # If evaluation opted in

Gateway type: [ai_framework value]
Language: [detected language]
Models to migrate: [count] models
Capabilities covered: [list from capabilities_summary]
```
