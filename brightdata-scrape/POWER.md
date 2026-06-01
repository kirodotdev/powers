---
name: "brightdata-scrape"
displayName: "Add web scraping to any app with Bright Data"
description: "Detect your project's stack and add production-ready web scraping — generates the right integration pattern (module, API route, or agent tool), wires Bright Data MCP into your project, handles pagination and bot detection."
keywords: ["scrape", "scraping", "scraper", "crawl", "crawler", "web-data", "extract", "extract-data", "competitor", "pricing-monitor", "lead-generation", "amazon", "linkedin", "instagram", "tiktok", "youtube", "serp", "google-search", "search-engine", "brightdata", "bright-data", "web-unlocker", "browser-api", "captcha", "bot-detection", "pagination", "agent-tools", "mcp"]
author: "Bright Data"
---

# Add web scraping to any app with Bright Data

This power detects what kind of project you're working on and adds production-ready scraping in the right shape — a reusable module, an API route, or an agent tool — backed by Bright Data's Web Unlocker, Web Scraper API, Browser API, and SERP API. It also wires the Bright Data MCP server into your project so any AI agent that runs against the project (Claude Code, Cursor, Cline, Kiro itself) gains live web tools.

**It works on any language**, but Python and TypeScript/JavaScript get first-class code generation. Other languages get a generic `curl`/HTTP template that you adapt.

## What you can do

- "Scrape competitor prices from example.com daily into my Next.js dashboard"
- "Add a `/api/scrape` route to my Express app"
- "Give my Claude SDK agent a tool that searches Google and reads results"
- "Extract all product listings from this Shopify store"
- "Monitor LinkedIn profiles of my pipeline contacts"

## Onboarding

Before using this power, complete the following.

### Step 1: Get a Bright Data API token

Sign up (or log in) at [Sign up at brightdata.com](https://brightdata.com). Generate an API token at [API token settings](https://brightdata.com/cp/setting/users). The free tier includes **5,000 requests per month** including Pro tools.

### Step 2: Configure the token (pick one)

**Option A — Env var (recommended for CI / production):**

```bash
export BRIGHTDATA_API_KEY=<your-token>
```

Add to your shell profile (`.zshrc`, `.bashrc`) or a project `.env` file. The generated `mcp.json` references `${BRIGHTDATA_API_KEY}`, so this works automatically.

**Option B — Hardcoded in user-level Kiro config:**

Edit `~/.kiro/settings/mcp.json` and add:

```json
{
  "mcpServers": {
    "brightdata": {
      "url": "https://mcp.brightdata.com/mcp?token=YOUR_TOKEN_HERE",
      "disabled": false
    }
  }
}
```

This makes Bright Data MCP available in every Kiro project on your machine.

### Step 3 (optional): Set up an Unlocker zone

The default Web Unlocker zone is named `unblocker` on new accounts. If you've renamed it or hit "no zone" errors, set:

```bash
export BRIGHTDATA_UNLOCKER_ZONE=<your-zone-name>
```

Or create / rename a zone at [zone management page](https://brightdata.com/cp/zones).

---

## How to use this power

For any scraping task, **always** read the orchestrator steering file first:

```
Call action "readSteering" with powerName="brightdata-scrape", steeringFile="scrape-workflow.md"
```

The orchestrator runs four phases in sequence with confirmation gates between each:

1. **Detect & plan** — inspect the project, pick the right integration pattern, ask what to scrape.
2. **Scraping playbook** — pick the right Bright Data API and selectors based on the target site.
3. **Integrate** — generate the scraper module, API route, or agent tool into the user's project.
4. **MCP & verify** — wire the Bright Data MCP server, run a smoke test, write a README snippet.

**Do NOT improvise. Do NOT skip phases.** The steering files contain the exact instructions for each.
