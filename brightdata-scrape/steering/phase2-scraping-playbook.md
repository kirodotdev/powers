# Phase 2: Scraping Playbook (Condensed)

Pick the right Bright Data API and selectors for the user's target. Output a decision record the next phase consumes.

> This is a **condensed** version of the long-form `scraper-builder` skill. For deeper analysis (anti-bot escalation, multi-site parallelism, retry semantics, browser-session reuse), the brightdata-plugin `scraper-builder` skill is the reference. This phase is a working subset.

## Step 1: Decision tree (the four-line core)

1. **Pre-built scraper exists for this domain?** → use **Web Scraper API** (zero parsing, structured JSON).
2. **Static HTML, no interaction needed?** → use **Web Unlocker** (cheapest, simplest).
3. **JS-rendered, or needs clicks/scrolls/form fills?** → use **Browser API** (full automation).
4. **Search engine results page (Google/Bing/Yandex)?** → use **SERP API**.

## Step 2: Pre-built scraper check

One curl to discover all available pre-built scrapers:

```bash
curl -H "Authorization: Bearer $BRIGHTDATA_API_KEY" \
     https://api.brightdata.com/datasets/list
```

Search the response for the target domain. If you find a match, record the `dataset_id` and **skip to Step 5** — no reconnaissance needed.

Common matches: `amazon`, `linkedin`, `instagram`, `tiktok`, `youtube`, `facebook`, `twitter` (X), `reddit`, `walmart`, `ebay`, `crunchbase`, `zillow`, `booking`, `yahoo-finance`, `google-play`, `apple-app-store`.

## Step 3: Reconnaissance (no pre-built scraper)

### Step 3a: Fetch raw HTML

```bash
curl -X POST https://api.brightdata.com/request \
  -H "Authorization: Bearer $BRIGHTDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"zone": "'"${BRIGHTDATA_UNLOCKER_ZONE:-unblocker}"'", "url": "<TARGET_URL>", "format": "raw"}'
```

### Step 3b: Inspect

- **Is the data in the HTML?** If yes → Web Unlocker is sufficient.
- **Is the HTML mostly an empty shell** (`<div id="root"></div>`, `<div id="__next"></div>`, `ng-app`)? → content is client-rendered → **escalate to Browser API**.
- **Does the page reference internal JSON endpoints** (look for `fetch('/api/...')`, `XMLHttpRequest`, hardcoded JSON in `<script>` tags)? → hitting the API endpoint directly via Web Unlocker is cleaner than HTML parsing.

### Step 3c: Pick selectors (priority order)

Prefer data attributes (`data-*`) over structural selectors — they survive redesigns.

1. **`data-*` attributes** (e.g., `[data-testid="product-price"]`) — survive redesigns.
2. **Semantic class names** (e.g., `.product-card .price`).
3. **`id` attributes** — unique, but may change.
4. **Structural selectors** (e.g., `div > span:nth-child(2)`) — fragile, **avoid**.

## Step 4: Pagination patterns

| Pattern | Detection | Implementation |
|---------|-----------|----------------|
| **URL-based** | URLs like `?page=N`, `?offset=20` | Loop `?page=N` until response has no items |
| **Next-link** | HTML has `<a rel="next">` or `.pagination .next a` | Follow the next-link until absent |
| **Cursor** | API responses include `next_cursor`, `next_token` | Loop with `?cursor=<token>` from previous response |
| **Infinite scroll** | Content loads on scroll, no URL change | Browser API only — scroll until item count stops growing |

## Step 5: Concurrency

If the user said "bulk" volume in Phase 1 (50+ URLs), the generated code **must** use semaphore-bounded async with `CONCURRENCY=20` as the default. Sequential `time.sleep(1)` loops at this volume are unacceptable.

## Step 6: Output the decision record

Hand back to the orchestrator:

```
{
  "approach": "web-unlocker" | "browser-api" | "pre-built" | "serp",
  "dataset_id": "<if pre-built>" | null,
  "selectors": { "<field>": "<css selector>", ... },
  "pagination": "url-based" | "next-link" | "cursor" | "infinite-scroll" | "none",
  "concurrency_required": true | false,
  "hidden_api_endpoint": "<URL or null>"
}
```

Confirm the choice with the user in one short message before returning to the orchestrator:

> I'll use **Web Unlocker** with these selectors: `<list>`. Pagination is **URL-based**. Sound right?

WAIT for confirmation. Then return.
