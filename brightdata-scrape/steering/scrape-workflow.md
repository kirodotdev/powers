# brightdata-scrape Workflow

Orchestrated workflow for adding Bright Data scraping to a project.

## When to use this workflow

Use for any scraping or web-data task — the user said something like "scrape X", "extract data from Y", "monitor competitor prices", "give my agent web search", or any keyword from this power's frontmatter.

## Critical rules

1. **All four phases run in order.** No skipping, no reordering.
2. **One phase steering file at a time.** Read only the next phase's file. Do NOT read ahead.
3. **Wait for user confirmation between phases.** Each phase ends with a confirmation gate.
4. **If you lose track, re-read this orchestrator file.** Identify the last completed phase, dispatch the next one.
5. **Do not improvise the integration code.** Use the templates in `brightdata-scrape/templates/` as canonical references.

## Step 1: Validate prerequisites

Run these checks before proceeding:

1. **`BRIGHTDATA_API_KEY` is set OR hardcoded in `~/.kiro/settings/mcp.json`.**
   - Check env: `echo $BRIGHTDATA_API_KEY` (non-empty)
   - OR check `~/.kiro/settings/mcp.json` for a `brightdata` entry with the token in the URL

2. **The user is in a workspace** (current working directory is set).

If `BRIGHTDATA_API_KEY` is missing, **STOP** and present the onboarding from `POWER.md` Step 1–2. Do not proceed.

## Step 2: Dispatch Phase 1

Read **only** the Phase 1 steering file:

```
Call action "readSteering" with powerName="brightdata-scrape", steeringFile="phase1-detect-and-plan.md"
```

**Do NOT read any other phase file yet.** Phase 1 will summarize a plan and ask the user to confirm. After the user confirms, proceed to Step 3 of this file.

## Step 3: Dispatch subsequent phases

After each phase completes and the user confirms, dispatch the next phase. The phase order is fixed:

1. `phase1-detect-and-plan.md`
2. `phase2-scraping-playbook.md`
3. `phase3-integrate.md`
4. `phase4-mcp-and-verify.md`

After Phase 4 completes, the workflow is done. Tell the user what was added and where.

(See Step 4 below for the exact transition protocol.)

## Step 4: Phase transition pattern

When a phase finishes, it will summarize what it did and stop. The orchestrator then:

1. Tells the user which phase just finished and what's next.
2. Asks: `[Phase name] is complete. Ready to proceed to [next phase name]?`
3. **Waits for the user to confirm.**
4. Once confirmed, reads the next phase steering file with `readSteering` and dispatches it.

## Troubleshooting

- **Smoke test in Phase 4 returns empty data** → re-enter Phase 2 reconnaissance, fix selectors, regenerate the affected files in Phase 3, re-run smoke test. Do not declare success.
- **User asks to change scope mid-flow** → ask if they want to abort and restart Phase 1, or continue with current plan.
- **Multiple manifests in repo (monorepo)** → Phase 1 handles this; ask the user which sub-project.
