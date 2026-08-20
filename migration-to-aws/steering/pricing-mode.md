# Estimate — Pricing Mode Selection (canonical Step 0)

> Canonical pricing-mode procedure for estimate cost engines, vendored into
> each skill (`pricing-mode.md`) and kept
> byte-identical by `shared:sync`. The `cached_stale` enum bug happened because
> two copies of this logic evolved separately — do not fork this text again.
> Skill cost engines execute this file AS their Step 0, then own everything
> after it (baseline rungs, service formulas, tiers).

## Step 0a: Load the pricing cache

Read `aws-infra-pricing.json`. Check
`_meta.last_updated` against `_meta.staleness_days` (default 30):

- Within the window: **cached prices are the primary source.** No MCP calls
  needed for services in the file. Set `pricing_source: "cached"`.
- Past the window: infrastructure prices remain reliable. Attempt MCP (Step
  0b) for services not in the file; use cached rates as fallback with
  `pricing_source: "cached_stale"`.

Each service object carries its rates and (where relevant) a
`multi_az_handling` key. Look rates up from the file — never hardcode them.

## Step 0b: MCP availability check (only if cache stale or service not listed)

Attempt the awspricing MCP with **up to 2 retries** (3 total attempts,
10-second timeout per attempt):

1. Attempt 1: `get_pricing_service_codes()`
2. Timeout/error → wait 1s, attempt 2
3. Timeout/error → wait 2s, attempt 3
4. All 3 fail → cached prices, `pricing_source: "cached_fallback"`

## Step 0c: Display the pricing mode

Before any calculation, surface the status:

- Cache fresh + all services covered: "Pricing source: cached (updated
  [date], ±5-10% accuracy). Live pricing API not required."
- Cache stale + MCP available: "Pricing source: live API (awspricing MCP).
  Cache is stale ([date]) — using real-time pricing."
- Cache stale + MCP unavailable: "Pricing source: stale cache only (updated
  [date]). The awspricing MCP server is unreachable. Proceeding with cached
  pricing; accuracy ±5-10% for infrastructure."
- Service not in cache + MCP unavailable: "Some services not in pricing cache
  and MCP unreachable. Those services will show `pricing_source: unavailable`
  in the estimate."

## Pricing hierarchy (per-service lookup order)

| Priority | Source                                               | Condition                                                                                      | `pricing_source` value |
| -------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------- |
| 1        | `aws-infra-pricing.json` | Service found in the pricing file                                                              | `"cached"`             |
| 2        | MCP API (`get_pricing`)                              | Service NOT in the file, MCP available                                                         | `"live"`               |
| 3        | Pricing file after MCP failure                       | MCP attempted but failed, service IS in file                                                   | `"cached_fallback"`    |
| 4        | Formula constants / well-known published rate        | NOT in file, MCP failed, but the cost engine's own formulas carry the rate (state it verbatim) | `"estimated"`          |
| 5        | Unavailable                                          | NOT in file, MCP failed, no formula constant either                                            | `"unavailable"`        |

Row 4 is the documented home of the `services_by_source.estimated` bucket the
shared schema and assemblers carry: a service priced from a rate the cost
engine itself states (never a guessed or remembered number) is `"estimated"`,
always accompanied by a warning naming the rate and its source. Only a service
with no cache entry, no MCP, AND no stated formula rate is `"unavailable"` and
excluded from totals.
