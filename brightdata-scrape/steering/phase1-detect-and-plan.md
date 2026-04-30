# Phase 1: Detect & Plan

Inspect the user's workspace, classify it, and propose a single integration pattern. Confirm with the user before proceeding to Phase 2.

## Step 1: Manifest detection

Look for these manifest files at the workspace root, in order:

| Manifest | Language |
|----------|----------|
| `package.json` | TypeScript / JavaScript |
| `pyproject.toml`, `requirements.txt`, `Pipfile` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `composer.json` | PHP |

**No manifest found** → **greenfield mode**. Skip to Step 4 and ask the user: "Python or TypeScript?"

**Multiple manifests in subdirectories (monorepo)** → ask the user which sub-project to integrate into. Do **not** pick automatically.

## Step 2: Stack signature

Within the chosen manifest, look for these dependency signatures:

### Web framework dependencies (route pattern)

**TypeScript/JavaScript** — look in `dependencies` and `devDependencies`:
- `next`, `next.js` → Next.js
- `express` → Express
- `fastify` → Fastify
- `hono` → Hono
- `koa`, `koa-router` → Koa
- `@nestjs/core` → NestJS
- `remix`, `@remix-run/react` → Remix

**Python** — look in `pyproject.toml` `[project.dependencies]` or `requirements.txt`:
- `fastapi` → FastAPI
- `flask` → Flask
- `django` → Django
- `aiohttp` → aiohttp
- `starlette` → Starlette

### Agent framework dependencies (agent tool pattern)

**TypeScript/JavaScript:**
- `langchain`, `@langchain/*` → LangChain
- `@anthropic-ai/sdk` → Anthropic SDK
- `openai` → OpenAI SDK
- `mastra`, `@mastra/*` → Mastra
- `@ai-sdk/*`, `ai` → Vercel AI SDK
- `@modelcontextprotocol/sdk` → MCP SDK

**Python:**
- `langchain`, `langchain-*` → LangChain
- `anthropic` → Anthropic SDK
- `openai` → OpenAI SDK
- `llama-index` → LlamaIndex
- `crewai` → CrewAI
- `mcp` → MCP SDK

## Step 3: Pick the single pattern

Apply this decision tree:

| Signals | Pattern | Template family |
|---------|---------|-----------------|
| Web framework deps present | **API route** | `templates/route/` |
| Agent framework deps present, no web framework | **Agent tool** | `templates/tool/` |
| Both web and agent | Ask the user which surface they prefer (route or tool) |
| Library / CLI / unrecognized | **Module** | `templates/module/` |
| Greenfield (no manifest) | **Module**, language asked above | `templates/module/` |

**Inform the user of the choice but don't put it up for vote** — the detection is the choice.

## Step 4: Targeted scraping question

Ask in **one** message:

> What do you want to scrape, and which fields? (Examples: 'product name + price + image from amazon.com search results', 'all job titles + companies from greenhouse.io listings'.) Roughly how many pages or items?

Do NOT ask separately about pagination type, output format, or language preference:
- **Pagination type** → discovered in Phase 2 reconnaissance.
- **Output format** → defaults to typed return value; the caller decides what to do with it.
- **Language** → already determined by manifest (TypeScript for `package.json`, Python for `pyproject.toml`/`requirements.txt`); greenfield is handled in Step 1.

### Canonical framework slugs

When emitting the decision record's `framework` field, use these exact slugs (so Phase 3's template lookup works):

| Framework | Slug |
|-----------|------|
| Next.js (App Router) | `next-app-router` |
| Next.js (Pages Router) | `next-pages-router` |
| Express | `express` |
| Fastify | `fastify` |
| Hono | `hono` |
| Koa | `koa` |
| NestJS | `nestjs` |
| Remix | `remix` |
| FastAPI | `fastapi` |
| Flask | `flask` |
| Django | `django` |
| aiohttp | `aiohttp` |
| Starlette | `starlette` |
| LangChain (TS) | `langchain-ts` |
| LangChain (Python) | `langchain-py` |
| Anthropic SDK (TS) | `anthropic-sdk-ts` |
| Anthropic SDK (Python) | `anthropic-sdk-py` |
| OpenAI SDK (TS) | `openai-ts` |
| OpenAI SDK (Python) | `openai-py` |
| Mastra | `mastra` |
| Vercel AI SDK | `vercel-ai-sdk` |
| LlamaIndex | `llama-index` |
| CrewAI | `crewai` |

If the detected framework isn't in this list, use the bare lowercase package name and tell the user a fallback template will be used.

## Step 5: Present plan and wait for confirmation

Format:

```
## Plan

**Detected:** <stack signature, e.g., "Next.js 14 (App Router) project, TypeScript">
**Pattern:** <module | API route | agent tool>
**Scraping target:** <user's site/data>
**Estimated volume:** <single | small (<50) | bulk (>=50)>

**Phases I'll run:**
  1. ✓ Detect & plan (this phase, just confirmed)
  2. Scraping playbook — pick the right Bright Data API and selectors
  3. Integrate — generate <files I'll write> in your project
  4. MCP & verify — wire Bright Data MCP, run a smoke test

Ready to proceed to Phase 2?
```

**WAIT for the user to confirm before returning control to the orchestrator.**

## Output of this phase

The orchestrator carries forward this decision record:

```
{
  "language": "typescript" | "python" | "other",
  "language_other_name": "<e.g., 'go'>" | null,
  "pattern": "module" | "route" | "tool",
  "framework": "<e.g., 'next-app-router', 'fastapi', 'anthropic-sdk-ts'>",
  "target_url": "<user's site>",
  "fields": ["<field1>", "<field2>", ...],
  "volume": "single" | "small" | "bulk",
  "monorepo_subproject": "<path>" | null
}
```

Subsequent phases reference this record by name. If anything is missing from it, return to Phase 1.
