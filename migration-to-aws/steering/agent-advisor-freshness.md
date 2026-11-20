# Volatile Facts & Freshness

## Fields to verify at runtime via the awsknowledge MCP

- AgentCore session cap (currently "8h, extending")
- AgentCore compute cap (2 vCPU / 8 GB)
- AgentCore / Lambda MicroVMs region availability
- Lambda MicroVMs launch TPS (5, not adjustable)
- FedRAMP certification status for AgentCore and Lambda MicroVMs
- Any Bedrock model price (defer to migration-to-aws pricing cache; never hardcode here)

## Temporal (agent-advisor-design.md — Freshness, temporal units only)

Volatile facts to re-verify when the Temporal branch generates a plan. The awsknowledge
MCP does not cover Temporal-side facts; each fact below names its actual verification
channel. Whatever cannot be verified this run stays cached and the footer must say so.

**Temporal Knowledge Base MCP (preferred channel for Temporal-side facts):**
Temporal's hosted knowledge-base MCP server (`temporal-docs` →
`https://temporal.mcp.kapa.ai`, real-time answers compiled from Temporal docs, forum,
and Slack) **ships in this plugin's `.mcp.json`** — it is already registered for every
install. It is the preferred source for the **Feature statuses** fact below. It needs a
one-time OAuth login to actually connect. **Auth-gate procedure (run BEFORE any Temporal
feature-status lookup):**

1. Check whether the `temporal-docs` MCP is connected AND authenticated this session.
2. **If authenticated** → query it first for feature statuses.
3. **If registered but NOT authenticated** → STOP and ask with AskUserQuestion (do not
   silently fall through): "The Temporal docs MCP (`temporal-docs`) gives the freshest
   feature-status answers but needs a one-time Google/GitHub login. Authenticate now?"
   with options:
   - **"Yes — I'll authenticate"** → tell the user to run `/mcp` → `temporal-docs` →
     Authenticate, and **wait** for them to confirm it's done; then re-check and query
     the MCP. (Step 4 is a read-only freshness check — pausing here is safe and resumes
     cleanly.)
   - **"No — use public web instead"** → fall back to the WebFetch channel named on the
     fact for this run.
4. Only ask once per run; if the user declined this run, do not re-prompt.

- The anti-fabrication rule applies to the MCP identically: a fact counts as verified
  only if the MCP (or the WebFetch) actually returned it this run.
- Scope note: the MCP covers Temporal **platform** knowledge only. The Marketplace
  listing / commercial-terms fact below is AWS buyer-side and stays WebFetch-only — do
  not route it through the Temporal KB MCP.

**Verifiable this run (attempt these):**

- **Marketplace listing + commercial terms** — fetch
  `https://aws.amazon.com/marketplace/pp/prodview-xx2x66m6fp2lo` (public page, no auth).
  Confirm: listing resolves (not 404/redirect to search), product name still
  "Temporal Cloud (Pay-as-you-Go)", the $0.01/action pricing dimension, free trial.
  (The Marketplace Catalog API cannot do this — it is seller-scoped; the public page is
  the only buyer-side channel. The Temporal KB MCP does NOT cover this — it is
  Temporal-platform-scoped, not AWS Marketplace.)
- **Feature statuses** (Serverless Workers, Workflow Streams, External Payload Storage,
  Worker Versioning) — **preferred:** query the Temporal KB MCP (above). **Fallback:**
  fetch the relevant docs.temporal.io page. CAUTION for Serverless Workers regardless of
  channel: the docs label has shown "Available" while the feature was pre-release
  (user-verified 2026-07); a docs label — or an MCP answer echoing it — alone does NOT
  upgrade it to GA — keep the pre-release label until the user shows GA evidence (e.g. a
  GA announcement post).

**Not verifiable (always cached):**

- $1,000 credits / SCMP / Vendor Insights details beyond what the listing page shows.
- "No official cross-cluster history migration tool" — absence is unprovable by lookup;
  restate as of the last-verified date.

The anti-fabrication rule below applies unchanged: only facts actually fetched and
observed this run may be listed as verified.

## Procedure

1. Identify the volatile facts to check: for the main skill, the `volatile_facts` entries
   (`verify_via_mcp: true`) from the winning runtime's profile JSON; for **add-capabilities**
   (which has no winning runtime profile), the "Hard limits" facts in the relevant service card
   (agent-advisor-agentcore.md) instead.
2. Attempt an awsknowledge MCP lookup for each.
3. On success (the MCP call returned a value THIS run), use the fresh value and list the field as
   verified.
4. On failure OR if you did not call the MCP at all (unavailable, skipped), use the cached
   `value` and list the field as fallen-back.

**Anti-fabrication rule (do not skip):** a field may appear in the "verified via MCP" list ONLY
if you actually made an MCP call this run and observed its result. If you did not call the MCP
for a field — for any reason — it goes in the cached/fell-back list. Never claim verification you
did not perform. If the MCP was not called at all, the verified list is empty and every field is
cached.

## Freshness footer template (append to every recommendation doc)

Choose the wording that matches what actually happened:

- If some fields were MCP-verified this run:
  > _Generated `<DATE>`. Facts verified via AWS Knowledge MCP: `<list verified>`. Cached values used
  > for: `<list cached>`. Limits and pricing change — verify against AWS docs before committing._
- If the MCP was not called / unavailable:
  > _Generated `<DATE>`. AWS Knowledge MCP not called this run; all facts are cached values —
  > verify against AWS docs before committing._
