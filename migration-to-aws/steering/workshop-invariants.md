# What-If Workshop — Cross-Skill Invariants (canonical)

> Canonical contract for the post-Estimate what-if workshop, vendored into each
> skill (`workshop-invariants.md`) and kept
> byte-identical by `shared:sync`. Skill workshop files (`workshop.md`,
> `workshop-sheet.md`, `workshop-refresh.md`, `workshop-compare.md`,
> `workshop-assemble.md`) own the skill-SPECIFIC parts — knobs, artifact names,
> engine refreshes — and defer to THIS file for every invariant below. When a
> skill file and this file disagree on an invariant, this file wins; fix the
> skill file.
>
> Placeholders: `{INVENTORY}` = the skill's frozen discovery artifact
> (`heroku-resource-inventory.json` /
> `gcp-resource-inventory.json`); `{SKILL_LABEL}` = "Heroku" / "GCP".

## 1. Discovery is frozen

- The workshop NEVER writes `{INVENTORY}`, capture directories, or any
  discovery-derived analysis artifact (coupling, preflight, clusters).
- `scenarios/index.json.inventory_fingerprint` = SHA-256 hex of the raw
  `{INVENTORY}` bytes (no JSON re-serialization), recorded at baseline capture.
- Every Apply & reprice MUST recompute the fingerprint first and ABORT with
  "Inventory changed since baseline. Re-run Discover before workshop reprice."
  on any difference.

## 2. Sidebar state semantics

- The workshop is a sidebar: it NEVER becomes `current_phase`. Entry sets
  `phases.workshop: "in_progress"`; `current_phase` stays at `"estimate"`
  until exit/decline.
- Exit to Generate (assembler): `phases.workshop: "completed"`,
  `current_phase: "generate"`. Decline at the Estimate offer: same, without
  requiring `scenarios/`.
- Warm-start rule: `current_phase == "estimate"` AND
  `phases.estimate == "completed"` AND `phases.workshop == "pending"` →
  present the workshop offer; NEVER recompute Estimate.
- If Generate (or later) is already `completed`, apply the Estimate re-entry
  guard (confirm → reset downstream to pending) before any refresh.

## 3. Inner runs are artifact-only

When the refresh re-runs a backbone phase (Design/Recommend/Estimate) to
reprice:

| Allowed                               | Forbidden                                                                                |
| ------------------------------------- | ---------------------------------------------------------------------------------------- |
| Overwrite that phase's artifact(s)    | Set the phase to `in_progress`/`completed` (they stay `completed`)                       |
| Soft-validate before snapshot         | Emit `HANDOFF_OK` from the inner phase                                                   |
| One brief chat note when done         | Touch `current_phase` or advance the backbone                                            |
| Keep `phases.workshop: "in_progress"` | Run the post-Estimate workshop offer (recursion)                                         |
|                                       | Fail on `_check_single_active_phase`-style preconditions because workshop is in progress |

## 4. Scenario store

- Max **5** scenarios. Before evicting, WARN and NAME the victim (id + label);
  never delete `baseline_scenario_id` unless the user explicitly resets.
- Working tree == active scenario: the skill's preference/design/estimate
  artifacts always match `index.active_scenario_id`.
- Each manifest's `estimation_summary` carries at minimum:
  `aws_monthly_premium` / `_balanced` / `_optimized`, `complexity_tier`,
  `pricing_source`, `region_note` (nullable), `calculator_url` (nullable).
  Optional: `recommendation_outcome` (nullable — copy of
  `recommendation.outcome` when the inner estimate wrote v2 decision fields;
  compare views may render an Outcome column and flag flips vs baseline).
- `preferences_subset` records ONLY the knob paths that differ from baseline.

## 5. Region honesty

The sheet always shows: region repricing needs live pricing access (awspricing
MCP) for true regional rates; without it, numbers stay on the us-east-1 cache
basis and every affected estimate carries a `region_note`. Never present
cache-based numbers as regional.

## 6. Shareable calculator link (best-effort, never blocks)

After each scenario snapshot, if the `aws-pricing-calculator` MCP server is
available (probe `get_server_info` once; no retry on failure):

1. Prefer one-shot `build_estimate`: name
   `"{SKILL_LABEL} migration — {scenario label} ({target_region})"`, services
   from the scenario's Balanced-tier estimate breakdown (the PRIMARY outcome's
   set where outcomes exist), each with the scenario's target region — the
   calculator computes REGIONAL prices server-side, which the cache cannot.
   On a structured needs-field-discovery response, resolve via
   `get_service_fields` and retry ONCE; else fall back to
   `create_estimate` → `add_service` → `export_estimate`.
2. Store the URL as the manifest's `estimation_summary.calculator_url`.
3. Any failure or unmappable service → `calculator_url: null`, one chat note,
   continue. Workshop numbers stay authoritative; the link is a complementary
   stakeholder artifact. Unconfigured server → silent null.

Compare tables and stakeholder reports render one link line per non-null
`calculator_url`.
