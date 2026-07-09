# Anthropic SDK → Amazon Bedrock Migration

> Loaded by `design-ai.md` when `ai_source == "anthropic"`.
> The user is already on Claude via the Anthropic SDK. Migration is a client swap only.
> No model change, no prompt rewriting, no retraining required.

---

## Step 1: Map model IDs to Bedrock

| Anthropic SDK model | Bedrock model ID                           | Tier     | Input/Output per 1M |
| ------------------- | ------------------------------------------ | -------- | ------------------- |
| `claude-opus-4-*`   | `anthropic.claude-opus-4-6-v1`             | Premium  | $5 / $25            |
| `claude-sonnet-4-*` | `anthropic.claude-sonnet-4-6`              | Flagship | $3 / $15            |
| `claude-haiku-4-*`  | `anthropic.claude-haiku-4-5-20251001-v1:0` | Fast     | $1 / $5             |

Older Claude models — Claude 3.5 Haiku, Claude 3 Sonnet, Claude 3.5 Sonnet (v1/v2), Claude 3 Haiku, and Claude 3.7 Sonnet — are past EOL or within the 90-day exclusion window. Do **not** recommend them as migration targets. See `steering/ai-model-lifecycle.md` for authoritative status (recomputed each run).

**Recommendation:** Migrate to Claude 4.x directly. Converse API call shape is identical across generations.

---

## Step 2: Rewrite client

Before: `anthropic.Anthropic(api_key=...)`
After: `boto3.client("bedrock-runtime", region_name="us-east-1")`

Remove ANTHROPIC_API_KEY. Use IAM role with bedrock:InvokeModel.

---

## Step 3: Rewrite API calls

Before: `client.messages.create(model=..., max_tokens=1024, messages=[{"role": "user", "content": "Hello"}])`

After: `client.converse(modelId="anthropic.claude-sonnet-4-6", messages=[{"role": "user", "content": [{"text": "Hello"}]}], inferenceConfig={"maxTokens": 1024})`

Key differences:

- content is typed blocks [{"text": "..."}] not a plain string
- max_tokens moves to inferenceConfig.maxTokens
- response text at `response["output"]["message"]["content"][0]["text"]`

---

## Step 4: System prompts

Before: `system="You are helpful"` as a string param
After: `system=[{"text": "You are helpful"}]` as a list of blocks

---

## Step 5: Streaming

Before: `client.messages.stream()` context manager
After: `client.converse_stream()` — iterate `response["stream"]` for `contentBlockDelta` events

---

## Step 6: IAM permissions

Add bedrock:InvokeModel and bedrock:InvokeModelWithResponseStream on arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*

---

## Step 7: Request Bedrock quota

Request TPM increases via Service Quotas. Cross-region inference profiles (us.* prefix) have higher shared limits.

---

## Validation checklist

- [ ] anthropic.Anthropic() replaced with boto3.client("bedrock-runtime")
- [ ] client.messages.create() replaced with client.converse()
- [ ] content blocks use typed format [{"text": "..."}]
- [ ] max_tokens moved to inferenceConfig.maxTokens
- [ ] Streaming uses converse_stream with contentBlockDelta events
- [ ] ANTHROPIC_API_KEY removed from environment/secrets
- [ ] IAM role has bedrock:InvokeModel permission
- [ ] Model IDs updated to Bedrock format (Claude 4.x recommended)
