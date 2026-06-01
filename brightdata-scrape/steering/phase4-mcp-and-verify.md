# Phase 4: MCP Wiring & Smoke Test

Wire the Bright Data MCP server into the project, run a one-page smoke test, and write the README wrap-up.

## Step 1: Project-level MCP config

Read or create `.kiro/settings/mcp.json`. Apply the following merge logic:

- **File doesn't exist** → create with this content:
  ```json
  {
    "mcpServers": {
      "brightdata": {
        "url": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}",
        "disabled": false
      }
    }
  }
  ```

- **File exists, no `brightdata` key** → merge the entry above into `mcpServers`.

- **File exists, `brightdata` key with the same URL** → no-op.

- **File exists, `brightdata` key with a different URL** → show the diff to the user and ask:
  > "There's an existing `brightdata` MCP server pointing at `<existing-url>`. Want me to: (a) replace it with the standard URL, (b) leave it alone, or (c) append `&pro=1` to enable Pro tools?"

**Always show the diff before writing.** Do not write silently.

## Step 2: User-level alternative

Tell the user:

> "If you'd rather have Bright Data MCP available across **every** Kiro project (not just this one), copy the same `brightdata` block to `~/.kiro/settings/mcp.json` instead. The project-level `.kiro/settings/mcp.json` overrides user-level if both exist."

## Step 3: Token onboarding inline check

Verify the token is actually available at runtime:

1. **Env var path:** `echo $BRIGHTDATA_API_KEY` should be non-empty.
2. **Hardcoded path:** the URL in `.kiro/settings/mcp.json` (or `~/.kiro/settings/mcp.json`) does not contain the literal `${BRIGHTDATA_API_KEY}` (it has been replaced with a real token).

If neither is true, **STOP** and ask the user to set the env var or hardcode the token before continuing. Do not skip to Step 4.

In **greenfield mode** (no project shell context), offer to set the env var inline for the smoke test only:

```bash
BRIGHTDATA_API_KEY=<token> python scrape.py
```

Tell the user this is for the smoke test only — they should add it to their shell profile or `.env` afterward.

## Step 4: Smoke test

Run the generated scraper on the user's target URL with a 1-page sample (or 1–3 items, whichever is faster).

**For a module:** call the function directly from a one-line REPL invocation or a temporary script.

**For a route:** start the dev server (or call the handler function directly if possible) and hit the endpoint with one curl.

**For an agent tool:** invoke the tool's `run`/`call`/`execute` function directly with a sample input.

Show the result to the user.

### Outcomes

- **Empty result, all-null fields, or error** → **return to Phase 2 reconnaissance**, fix selectors, regenerate the affected module file in Phase 3, re-run the smoke test. **Do not declare success.**
- **Partial result** (some fields populated, some null) → ask the user if it's good enough or to iterate.
- **Clean result** → proceed to Step 5.

## Step 5: README wrap-up

Append to `README.md`:

```markdown
## Bright Data MCP

This project has the Bright Data MCP server configured (`.kiro/settings/mcp.json`).
Any AI agent (Claude Code, Cursor, Cline, Kiro) running against this project
gains live web tools — `search_engine`, `scrape_as_markdown`, and structured-data
extractors for 40+ platforms.

To enable the full 60+ Pro tools (e.g., `web_data_amazon_product`,
`web_data_linkedin_person_profile`), append `&pro=1` to the MCP URL in
`.kiro/settings/mcp.json`. To enable specific groups only, use
`&groups=social,ecommerce` (groups: `social`, `ecommerce`, `business`,
`finance`, `research`, `app_stores`, `travel`, `browser`, `advanced_scraping`).
```

If the section already exists, **skip** — do not duplicate.

## Step 6: Final summary

Tell the user:

```
Done. Here's what was added:

  Code:
    ✓ <files written by Phase 3>

  MCP:
    ✓ .kiro/settings/mcp.json — Bright Data server registered
    ℹ︎ Append `&pro=1` to the MCP URL to enable 60+ Pro tools

  Smoke test:
    ✓ Scraped 1 page — extracted <N> items, all fields populated

Try it out:
    <one-line invocation appropriate to the pattern>
```

Workflow complete. Return to the orchestrator with no further action.
