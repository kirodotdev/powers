# Phase 3: Integrate

Generate the scraper code into the user's project. The pattern (module / route / tool) was chosen in Phase 1; the API and selectors were chosen in Phase 2. This phase picks the right template, fills it, and writes files — but only after confirming each path with the user.

## Step 1: Pick the template

Use the Phase 1 decision record's `pattern` and `framework` fields. Look up the canonical template:

| Pattern | Framework | Template path |
|---------|-----------|---------------|
| `module` | TypeScript | `templates/module/ts-cheerio.ts` (if user has cheerio) or `templates/module/ts-fetch.ts` (otherwise) |
| `module` | Python | `templates/module/py-bs4.py` (if bs4 acceptable) or `templates/module/py-stdlib.py` (otherwise) |
| `route` | Next.js App Router | `templates/route/next-app-router.ts` |
| `route` | Next.js Pages Router | `templates/route/next-pages-router.ts` |
| `route` | Express | `templates/route/express.ts` |
| `route` | Fastify | `templates/route/fastify.ts` |
| `route` | Hono | `templates/route/hono.ts` |
| `route` | Koa | `templates/route/koa.ts` |
| `route` | FastAPI | `templates/route/fastapi.py` |
| `route` | Flask | `templates/route/flask.py` |
| `route` | Django | `templates/route/django.py` |
| `tool` | LangChain (TS) | `templates/tool/langchain-ts.ts` |
| `tool` | LangChain (Python) | `templates/tool/langchain-py.py` |
| `tool` | Anthropic SDK (TS) | `templates/tool/anthropic-sdk-ts.ts` |
| `tool` | Anthropic SDK (Python) | `templates/tool/anthropic-sdk-py.py` |
| `tool` | OpenAI SDK (TS) | `templates/tool/openai-ts.ts` |
| `tool` | OpenAI SDK (Python) | `templates/tool/openai-py.py` |
| `tool` | Mastra | `templates/tool/mastra.ts` |
| `tool` | Vercel AI SDK | `templates/tool/vercel-ai-sdk.ts` |
| **other language** | any | `templates/fallback/curl.sh` (adapt by hand, tell the user) |

**If a template file does not exist** (because v1 ships a subset), fall back to the closest available template in the same family and tell the user:

> "I don't have a canonical template for `<framework>` yet — I'm using the `<closest>` template as a starting point and adapting it. You may need to adjust imports/syntax."

### Routes and tools also need a module template

The route and tool patterns import the scraper from a sibling module file. So when the pattern is `route` or `tool`, you must also pick a **module** template:

- TypeScript projects: `templates/module/ts-cheerio.ts` if the project already depends on `cheerio`; otherwise `templates/module/ts-fetch.ts` (no parser dep).
- Python projects: `templates/module/py-bs4.py` if `beautifulsoup4` is acceptable to add (or already a dep); otherwise `templates/module/py-stdlib.py` (stdlib only).

In other words: route and tool patterns generate **two** files — the route/tool wrapper and the module it imports.

## Step 2: Fill the template

Replace these placeholders in the template with values from the decision records:

- `{{TARGET_URL}}` → Phase 1 `target_url`
- `{{TARGET_NAME}}` → derived from URL host, snake_case (e.g., `amazon_com`, `competitor_prices`)
- `{{FIELDS}}` → Phase 1 `fields`, formatted per template (TS interface, Python TypedDict, etc.)
- `{{SELECTORS}}` → Phase 2 `selectors` (CSS strings)
- `{{PAGINATION}}` → Phase 2 `pagination` ('url-based' / 'next-link' / 'cursor' / 'infinite-scroll' / 'none')
- `{{APPROACH}}` → Phase 2 `approach`
- `{{DATASET_ID}}` → Phase 2 `dataset_id` (only for pre-built scrapers)
- `{{CONCURRENCY}}` → 20 if `concurrency_required` else 1
- `{{HIDDEN_API_ENDPOINT}}` → Phase 2 `hidden_api_endpoint` if present

Generated files always read **`BRIGHTDATA_API_KEY`** and **`BRIGHTDATA_UNLOCKER_ZONE`** (default `"unblocker"`) from environment.

## Step 3: Pick destination paths

For the **module** pattern:
- TS: `src/scrapers/{{TARGET_NAME}}.ts`
- Python: `src/scrapers/{{TARGET_NAME}}.py` — or use the project's existing source directory if `src/` doesn't exist (check for `app/`, `lib/`, top-level `.py` files)

For the **route** pattern:
- Next.js App Router: `app/api/scrape/route.ts`
- Next.js Pages Router: `pages/api/scrape.ts`
- Express / Fastify / Hono / Koa: `src/routes/scrape.ts` (or wherever the project's existing routes live — inspect)
- FastAPI: `app/api/scrape.py` (with router include line shown to user)
- Flask: `app/scrape.py` (blueprint, with `app.register_blueprint(...)` line shown)
- Django: `<app>/views/scrape.py` (with URL pattern line shown)

The route pattern **also** generates the module file (route imports the module).

For the **tool** pattern:
- TS: `src/tools/scrape.ts`
- Python: `src/tools/scrape.py`

The tool pattern **also** generates the module file (tool calls the module).

## Step 4: Update env and README

Always update:

- `.env.example` — append (skip lines already present):
  ```
  # Get token at https://brightdata.com/cp/setting/users
  BRIGHTDATA_API_KEY=
  # Optional — defaults to the account's "unblocker" zone if unset.
  # Manage zones at https://brightdata.com/cp/zones
  BRIGHTDATA_UNLOCKER_ZONE=
  ```

- `README.md` — append (or create) a `## Web scraping` section with one usage example showing how to call the generated function/route/tool.

## Step 5: Confirmation gate

Before writing **any** file, present the user with a list:

```
I'll write or modify these files:
  • CREATE src/scrapers/competitor_prices.ts
  • CREATE app/api/scrape/route.ts
  • MODIFY .env.example (append BRIGHTDATA_API_KEY, BRIGHTDATA_UNLOCKER_ZONE)
  • MODIFY README.md (append "## Web scraping" section)

OK to write?
```

**WAIT for confirmation. Do not edit a single file before the user says yes.**

## Step 6: Existing-file safety

- **Never overwrite an existing scraper file.** If `src/scrapers/competitor_prices.ts` exists, suggest `competitor_prices_2.ts` or ask the user where to put it.
- **Never overwrite `README.md` or `.env.example` wholesale.** Append only. If `BRIGHTDATA_API_KEY` is already in `.env.example`, skip it. If a `## Web scraping` section already exists, append a sub-section.
- **Never duplicate a route registration line.** If the user's `app.ts` already has `app.use('/api/scrape', ...)`, skip the suggestion.

## Step 7: Output

After writing, summarize for the user:

```
Files written:
  ✓ src/scrapers/competitor_prices.ts
  ✓ app/api/scrape/route.ts
  ✓ .env.example
  ✓ README.md

Next: Phase 4 will wire Bright Data MCP and run a smoke test.
```

Return control to the orchestrator.
