# tooling — parity sync with the upstream plugin

Maintainer scripts. **Not** loaded at runtime; only `POWER.md` and `steering/` are.

The engine content in `steering/` is generated from the upstream plugin:

> https://github.com/awslabs/startups/tree/main/migrate
> → `migrate/plugins/migration-to-aws/{skills,agents,scripts}`

The plugin is a nested Claude/Cursor/Codex plugin. A Kiro power is flat. These scripts perform
the projection deterministically so a sync is a re-run rather than a manual merge.

## Sync

```bash
# 1. get the upstream plugin
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/awslabs/startups.git /tmp/startups
git -C /tmp/startups sparse-checkout set migrate
PLUGIN=/tmp/startups/migrate/plugins/migration-to-aws

# 2. preview the projection (writes nothing; non-zero exit means a name collision)
python3 tooling/flatten_plugin_to_power.py --plugin "$PLUGIN" --check

# 3. regenerate steering/
python3 tooling/flatten_plugin_to_power.py --plugin "$PLUGIN"

# 4. confirm every reference still resolves (must report 0 / 0)
python3 tooling/validate_power.py

# 5. diff against the published power to review the drift being picked up
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/kirodotdev/powers.git /tmp/powers
git -C /tmp/powers sparse-checkout set migration-to-aws
python3 tooling/compare_to_published.py --published /tmp/powers/migration-to-aws
```

Step 3 deletes and rewrites `steering/` wholesale. Never hand-edit a file in `steering/` —
the next sync will overwrite it. Fix the upstream plugin, or fix the projection rules here.

`POWER.md` and `mcp.json` are **hand-maintained**. Step 5 tells you when they need attention:
new engines, renamed orchestrators, or a new MCP server in the plugin's `mcp.json`.

## Scripts

| Script                        | Does                                                                                          | Exit                          |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------- |
| `flatten_plugin_to_power.py`  | Projects plugin paths to flat steering names and rewrites cross-references                     | non-zero on collision or a duplicate table key |
| `validate_power.py`           | Finds unflattened paths, dangling filenames, and plugin layout tokens in `steering/`           | non-zero if any is present    |
| `compare_to_published.py`     | Regressions / unchanged / refreshed / added vs. the published power                            | non-zero on regression        |

## What `validate_power.py` checks, and why it once passed a broken power

It reports four things: unflattened plugin paths, dangling filenames, **plugin layout
tokens**, and broken POWER.md pointers.

The layout-token check exists because the other three all keyed off *extracted references*,
and an unresolvable path does not have to look like a reference. Three gaps let a batch of
genuine breaks through a clean run:

1. **Every slashed token was exempt from the dangling check.** The `continue` sat at the
   `if "/" in clean:` level rather than inside the `PLUGIN_SEGMENT` branch, so anything with
   a directory prefix that was not a recognised plugin segment — `$PLUGIN_ROOT/scripts/x.py`,
   `<somedir>/y.py` — was skipped entirely. A flat power resolves by basename, so the check
   now falls through and verifies the basename.
2. **`PLUGIN_SEGMENT` was missing `shared/` and `scripts/`**, the two most common prefixes in
   the plugin's own prose.
3. **Extraction only saw backticks and markdown links.** References in plain prose and inside
   JSON string values were invisible — that is how a dangling `design-defaults.json` survived
   in a `.json` value. `BARE_REF` now scans for filename-shaped tokens anywhere.

Truncated forms (`` `$GCP_BASE/references/` ``, `` `$SCRIPTS/...` ``) still end in no
extension and cannot be caught by reference extraction at all. `LAYOUT_TOKENS` catches those
as raw substrings instead. Add to it whenever upstream introduces a new base-dir variable —
it is the cheapest guard in the file.

4. **Directory references were matched as backtick-wrapped literals**, which made the check
   depend on the markup around the token. `LAYOUT_TOKENS` held `` `references/` `` with its
   backticks, so it missed both the un-backticked directory rows inside the "Files in This
   Skill" ASCII trees and the deeper backticked form `` `references/phases/workshop/` ``
   (which does not contain `` `references/` `` as a substring). A reviewer found both by
   reading `gcp-orchestrator.md` — the exact failure this validator exists to prevent. Those
   literals are now the `LAYOUT_DIRS` regex, matched regardless of surrounding markup, with a
   trailing boundary so prose like `≥2 phases/rows` does not trip it.

## Layout trees

`gcp-to-aws/SKILL.md` and `heroku-to-aws/SKILL.md` each document themselves with an ASCII
tree of the plugin's **nested** directory layout. Nothing loads through those paths — both
files address every target by bare filename — but the tree is the most prominent structural
statement in the file, so it reads as though the port still resolves
`references/phases/discover/discover.md`.

A prose disclaimer above the fence was the first attempt and was not enough: it does not
travel with the block when the tree is quoted, skimmed, or grepped, and it left heroku's tree
still rooted at `heroku-to-aws/`. `flatten_layout_tree()` now rewrites the tree **body** into
the flat layout — directory rows dropped, every leaf re-anchored under `steering/`, comments
re-aligned, upstream order preserved so the phase grouping is still legible. It runs after
the generic reference pass, so the leaves it reads are already the shipped flat names
(`cached-prices.md`, the `heroku-` prefixes). Rows naming a file the projection does not ship
are dropped, which is what removes heroku's `shared/README.md` row.

Do not re-add a `## Files in This Skill` heading rewrite to `MANUAL_REWRITES`: it runs first
and would stop `flatten_layout_tree()` from finding its marker.

Adding a whitelist entry to `ARTIFACT_HINTS` is the right fix **only** when the name really is
a runtime output or a user-repo file. If it is something the power ships, fix the projection.

## Projection rules

Encoded in `SKILL_RULES` in `flatten_plugin_to_power.py`.

- **gcp-to-aws is unprefixed.** It is the power's primary engine and its names are the ones
  already published in `kirodotdev/powers`, so they must not churn. Every other engine is
  namespaced: `heroku-`, `llm-`, `agent-advisor-`, `tf-`.
- `references/phases/<phase>/<file>.md` → `<file>.md` (prefixed per engine)
- `references/design-refs/<file>.md` → `design-ref-<file>.md`
- `references/decision-refs/<file>.md` → `agent-advisor-<file>.md`
- `references/shared/pricing-cache.md` → `cached-prices.md` (an established published rename)
- `scripts/<name>.py` → `<engine>-<name>.py`, snake_case flattened to hyphens
- `scripts/schemas/<name>.json` → `<engine>-<name>.schema.json`
- `agents/llm2bedrock-<role>.md` → `llm-<role>.md`
- Each engine's `SKILL.md` → `<engine>-orchestrator.md`, so `POWER.md` stays a thin router
- Byte-identical vendored copies of `skills/shared/**` collapse to one canonical name

**Skipped:** `fixtures/`, `tools/`, `docs/`, `pyproject.toml`, `uv.lock`, vendoring
`README.md`s, and all `test_*.py`.

The tests are dropped deliberately. They assert on the *plugin's* directory shape
(`references/phases/<phase>/<phase>.md`, and in one case
`parent.parent.parent.parent / "CONTRIBUTING.md"`), so they cannot pass against a flat power
and cannot be mechanically repaired — rewriting their path joins yields expressions valid in
neither layout. `validate_power.py` is the flat-layout equivalent. Steering prose that points
at them is redirected to the upstream plugin via `MANUAL_REWRITES`, so the pointer stays
truthful.

## Script patching

Scripts reach sibling data through their position in the plugin's nested tree, which
flattening breaks. `SCRIPT_PATCHES` carries the minimal fixes:

| Script                    | Patch                                                                       |
| ------------------------- | --------------------------------------------------------------------------- |
| `agent-advisor-scoring.py` | `RUNTIMES_DIR` → the flat dir; glob narrowed to `agent-advisor-runtime-*.json` |
| `llm-validate-result.py`   | `SCHEMAS_DIR` → the flat dir; schema names → `llm-<name>.schema.json`; PEP 723 deps added |
| `llm-preflight-bedrock.py` | PEP 723 deps added (`boto3`, `botocore`)                                     |
| `llm-bedrock-pricing.py`   | PEP 723 deps added (`boto3`, `botocore`)                                     |

Each patch's `old` text must match **exactly once** or the sync aborts. That is deliberate:
if upstream edits one of those lines, the patch gets re-reviewed instead of silently
skipping.

The glob narrowing matters — pointed at `steering/`, an unqualified `*.json` would sweep up
~24 unrelated files and the profile loader would raise on the first one.

`pyproject.toml` cannot survive flattening (uv needs it named that, inside a project dir), so
each script with a third-party dependency declares it inline via PEP 723 instead, carrying
the same pins the plugin's `pyproject.toml` held.

That also removes the `uv run --project $SCRIPTS python <script>` form the plugin uses — with
no pyproject there is no project to point at. `MANUAL_REWRITES` collapses those to a plain
`uv run <script>`. Ad-hoc invocations that are *not* a shipped script (heredocs, and scripts the
engine generates into the user's repo) still need the pinned SDK, so they get `PINNED_UV` —
the same pins as `--with` flags. Adding a new boto3-dependent helper upstream means adding a
PEP 723 patch for it plus a named-script entry in `MANUAL_REWRITES`; the bare
`uv run --project ... python` fallback would otherwise leave the old snake_case filename
behind, which `validate_power.py` does not catch (a `<placeholder>/name.py` reference is not a
bare dangling name).

## Base-directory tokens

The plugin addresses its own files through a host variable — `${CLAUDE_PLUGIN_ROOT}`,
`<SKILL_BASE>`, `$PLUGIN`, `$SCRIPTS`, `$HELPERS`, `$GCP_BASE`, `<scriptsDir>` — resolving to
a nested `skills/<engine>/{scripts,references}/...` tree. None of that survives flattening,
and `${CLAUDE_PLUGIN_ROOT}` is Claude-Code-only. `MANUAL_REWRITES` collapses every one of
them onto a single token, `STEERING` (`$STEERING`), documented in POWER.md.

It must stay **absolute**. A power installs under the Kiro config dir
(`~/.kiro/powers/installed/<name>/steering/`) while the run directory is created in the
user's workspace, so a relative `steering/...` never resolves. The plugin's own documented
fallback ("fall back to the skill's own directory: `./scripts/...`") is wrong here for the
same reason — it is rewritten, not preserved.

Two traps when adding rewrites here:

- **Silent no-ops.** `MANUAL_REWRITES` skips a key that is not present, so a stale key from
  an upstream edit fails open. After a sync, grep `steering/` for the plugin tokens above;
  they should all be gone.
- **The generic pass runs after.** A replacement containing a bare filename gets rewritten
  again — writing `# scoring.py flattens to ...` produced
  `# agent-advisor-scoring.py flattens to agent-advisor-scoring.py`. Refer to files
  descriptively ("the scoring helper") inside replacement text. Multi-line keys must also
  cover every line a sentence spans, or the leftover line starts mid-clause.

`agent-advisor-scoring.py` is a special case: Clarify `import`s it as a module, and the flat
name's hyphens make that impossible. The rewrite swaps the `PYTHONPATH` + `import scoring`
form for an `importlib.util.spec_from_file_location` load.

## `_exec` dispatch

Upstream dispatches `_exec` phases to a per-tier **registered plugin agent**
(`migration-to-aws:generic-phase-worker-<tier>`) and addresses the phase file relative to a
"Skill root" containing `references/` and `knowledge/`. Neither exists here — Kiro has no
per-tier agent registry, and the layout is flat.

The rewrite retargets dispatch at the generic `general-task-execution` sub-agent and supplies
the worker CONTRACT by pointing it at `generic-phase-worker-rw.md`, which ships as an ordinary
steering file. Context isolation — the reason `_exec` exists — is preserved; the capability
tier becomes advisory, which INTERPRETER.md's platform-asymmetry note already permits.

Two details that matter:

- The **fallback trigger** was "if the host has no Agent/subagent dispatch tool". Kiro has
  one, so the original never fired and the dispatch branch was taken with an unresolvable
  agent name. It now also fires when the tier's worker file is not shipped.
- The tier table must **not** name the `ro` and `git` worker files. Only `rw` ships, so those
  names would be dangling references. The table says "not shipped by this power" instead.

If upstream adds a `ro` or `git` worker, add it to `agents/`, then update that table and the
worker-exists validator item in the same rewrite.

## Determinism

A re-run must be byte-identical. Verify after changing projection rules:

```bash
python3 tooling/flatten_plugin_to_power.py --plugin "$PLUGIN" && cp -R steering /tmp/A
PYTHONHASHSEED=99 python3 tooling/flatten_plugin_to_power.py --plugin "$PLUGIN"
diff -r /tmp/A steering && echo IDENTICAL
```

This caught a real bug. `phases/clarify/clarify-assemble.md` exists in **both**
agent-advisor and heroku-to-aws, so a multi-segment path is not automatically unambiguous.
Those colliding keys were registered globally, and the winner depended on set iteration
order — meaning agent-advisor files sometimes got `heroku-` targets, varying per run.
`build_refmap` now detects a search string with more than one target and demotes it to the
per-engine tier; `compile_rewriter` raises on any residual conflict.

## Reference rewriting

Two tiers, because a bare filename is ambiguous across engines while a multi-segment path is
not:

- **global** — any search string containing `/` is applied across all engines. This is what
  makes cross-engine references work, e.g. `agent-advisor-migration-plan.md` pointing at
  `$GCP_BASE/references/phases/design/design.md`.
- **local** — bare basenames are scoped to the file's own engine, so `clarify.md` becomes
  `heroku-clarify.md` inside a heroku file and stays `clarify.md` inside a gcp file.

Matches are boundary-guarded so a short name cannot eat a longer one (`ai.md` must not fire
inside `clarify-ai.md`). Glob and placeholder forms (`references/design-refs/*.md`,
`references/phases/<phase>/<phase>.md`) cannot be projected generically and are listed
explicitly in `MANUAL_REWRITES`.

If a sync leaves findings in `validate_power.py`, the fix is almost always one of:

1. a new base-dir token upstream → add it to `PATH_PREFIXES`
2. a new glob/placeholder shape → add it to `MANUAL_REWRITES`
3. a genuinely new runtime artifact name → add it to `ARTIFACT_HINTS` in `validate_power.py`
