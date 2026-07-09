# Pricing Fallback

> Loaded by `ai-migration-guardrails.md` as the tertiary pricing source when both
> `cached-prices.md` (primary) and the `awspricing` MCP server (secondary) are unavailable.

## When This File Is Used

Use this fallback **only** when:

1. `cached-prices.md` is stale (>30 days since `Last updated`) **and**
2. The `awspricing` MCP `get_pricing` call fails or times out

## Fallback Behavior

When this fallback is active:

1. Set `pricing_source: "unavailable"` on all AI model cost estimates in `estimation-ai.json`
2. Surface a visible warning to the user:

   > ⚠️ **Pricing data unavailable.** The pricing cache is stale and the live pricing API could not be reached. AI cost estimates in this report are omitted. Re-run the Estimate phase when connectivity is restored, or check [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing) manually.

3. Do **not** fabricate or guess token prices — emit `null` for all per-token cost fields
4. Infrastructure pricing (Fargate, RDS, S3, etc.) from `cached-prices.md` may still be used — infrastructure prices change rarely and the cache remains reliable beyond 30 days

## MCP Retry Path

Before falling back to this file, attempt the MCP call with one retry:

```
get_pricing(service="bedrock", model_id="", region="")
```

If the retry also fails, proceed with `pricing_source: "unavailable"` as above.

## Do Not Guess

Never emit fabricated prices. A missing cost estimate is better than a wrong one.
