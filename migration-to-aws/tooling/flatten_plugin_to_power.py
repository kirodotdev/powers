#!/usr/bin/env python3
"""Flatten the awslabs/startups `migrate` plugin into this Kiro power's flat steering/ layout.

Source of truth
---------------
    https://github.com/awslabs/startups/tree/main/migrate
      -> migrate/plugins/migration-to-aws/{skills,agents,scripts}

Why this exists
---------------
The plugin is a Claude/Cursor/Codex *plugin*: nested skill directories, each with
`references/`, `scripts/`, `knowledge/`, and vendored copies of shared assets.
A Kiro power is flat: `POWER.md` + `mcp.json` + `steering/`. This script performs the
deterministic path -> flat-name projection plus the cross-reference rewriting that the
flattening implies, so a parity sync is reproducible instead of hand-maintained.

Conventions
-----------
* gcp-to-aws is the power's primary engine and stays **unprefixed** (this matches the
  names already published in kirodotdev/powers/migration-to-aws/steering).
* Every other engine is namespaced: `heroku-`, `llm-`, `agent-advisor-`, `tf-`.
* The plugin vendors `skills/shared/**` into individual skills. Those copies are
  byte-identical, so they collapse onto one canonical unprefixed name.
* Steering files reference each other by **bare flat filename**; POWER.md uses
  `steering/<name>`.
* Plugin CI assets (test_*.py, fixtures/, tools/, docs/) are not agent knowledge and are
  skipped.

Usage
-----
    python3 tooling/flatten_plugin_to_power.py --plugin /path/to/migrate/plugins/migration-to-aws
    python3 tooling/flatten_plugin_to_power.py --plugin ... --check
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# --------------------------------------------------------------------------------------
# Canonical shared assets: the plugin vendors these into several skills. Byte-identical,
# so they collapse to one flat name and every engine points at it.
# --------------------------------------------------------------------------------------
CANONICAL_SHARED = {
    "dsl/INTERPRETER.md": "INTERPRETER.md",
    "estimate/complexity-tiers.json": "complexity-tiers.json",
    "estimate/estimation-infra.schema.json": "estimation-infra.schema.json",
    "estimate/pricing-mode.md": "pricing-mode.md",
    "pricing/aws-infra-pricing.json": "aws-infra-pricing.json",
    "state/phase-status.schema.json": "phase-status.schema.json",
    "workshop/workshop-invariants.md": "workshop-invariants.md",
}

SKIP_PATTERNS = (
    re.compile(r"(^|/)\.gitignore$"),
    re.compile(r"(^|/)uv\.lock$"),
    re.compile(r"(^|/)pyproject\.toml$"),
    re.compile(r"(^|/)README\.md$"),  # vendoring notes, not steering content
)

# Every test_*.py is dropped. These assert on the *plugin's* directory layout
# (`references/phases/<phase>/<phase>.md`, `parent.parent.parent.parent / CONTRIBUTING.md`),
# so they cannot pass against a flat power and cannot be meaningfully repaired — rewriting
# their path joins produces expressions that are valid in neither layout. `validate_power.py`
# is the flat-layout equivalent. Prose that points at them is redirected upstream via
# MANUAL_REWRITES.
def _is_dropped_test(skill: str, rel: str) -> bool:
    return bool(re.search(r"(^|/)test_[^/]+\.py$", rel))


UPSTREAM_PLUGIN = "awslabs/startups:migrate/plugins/migration-to-aws"
UPSTREAM = f"{UPSTREAM_PLUGIN}/skills"

# Replacement for `uv run --project <scripts-dir> python`. The plugin's pinned toolchain came
# from skills/llm-to-bedrock/scripts/pyproject.toml, which cannot be carried into a flat
# layout. These are that file's pins, declared inline so ad-hoc invocations keep the same
# resolved SDK — Bedrock behaviour is sensitive to the boto3 version.
PINNED_UV = (
    "uv run --python '>=3.10' --with 'boto3>=1.35,<2' --with 'botocore>=1.35,<2' python"
)

# The single token for "where this power's files live on disk". A power is installed OUTSIDE
# the user's workspace (`~/.kiro/powers/installed/<name>/steering/`), and the run directory
# (`.migration/`, `.agent-advisor/`) is INSIDE it — so a shipped script can never be reached
# by a workspace-relative path. Every plugin base-dir token (`${CLAUDE_PLUGIN_ROOT}`,
# `<SKILL_BASE>`, `$PLUGIN`, `$SCRIPTS`, `$HELPERS`, `$GCP_BASE`) collapses onto this one.
# Defined for the agent in POWER.md; it resolves it from the path it loaded steering from.
STEERING = "$STEERING"

# Scripts address sibling data through their position in the plugin's nested tree. Flattening
# breaks those constants, so each is patched here.
#
# `old` must appear **exactly once** or the sync aborts. That is deliberate: if upstream
# edits one of these lines, the patch must be re-reviewed rather than silently skipped.
SCRIPT_PATCHES: dict[str, list[tuple[str, str]]] = {
    # was skills/agent-advisor/scripts/scoring.py, reading ../references/runtimes/*.json
    "agent-advisor-scoring.py": [
        (
            'knowledge lives in JSON profiles under references/runtimes/.',
            'knowledge lives in the agent-advisor-runtime-*.json profiles beside this file.',
        ),
        (
            'RUNTIMES_DIR = pathlib.Path(__file__).parent.parent / "references" / "runtimes"',
            "RUNTIMES_DIR = pathlib.Path(__file__).parent",
        ),
        # the flat steering dir holds ~25 unrelated .json files, so narrow the glob
        (
            'for path in sorted(pathlib.Path(runtimes_dir).glob("*.json")):',
            'for path in sorted(pathlib.Path(runtimes_dir).glob("agent-advisor-runtime-*.json")):',
        ),
        # points at a drift test this power does not ship
        (
            "# (the drift test in test_scoring.py locks this against the source lifecycle file).",
            f"# (the drift test in {UPSTREAM}/agent-advisor/scripts/test_scoring.py locks this\n"
            "# against the source lifecycle file).",
        ),
    ],
    # was skills/llm-to-bedrock/scripts/validate_result.py, reading ./schemas/<name>.json
    "llm-validate-result.py": [
        # The plugin declares deps in skills/*/scripts/pyproject.toml, which cannot survive a
        # flat layout (uv needs it named pyproject.toml in a project dir). PEP 723 inline
        # metadata gives the same result for a standalone script: `uv run <script>` resolves
        # jsonschema on its own. This is the only shipped script needing a third-party dep.
        (
            '"""Deterministic gate for phase-result files and run-context comparison.',
            '# /// script\n'
            '# requires-python = ">=3.10"\n'
            '# dependencies = ["jsonschema>=4,<5"]\n'
            '# ///\n'
            '"""Deterministic gate for phase-result files and run-context comparison.',
        ),
        (
            'SCHEMAS_DIR = pathlib.Path(__file__).parent / "schemas"',
            "SCHEMAS_DIR = pathlib.Path(__file__).parent",
        ),
        (
            'load_json(str(SCHEMAS_DIR / f"{schema_name}.json"))',
            'load_json(str(SCHEMAS_DIR / f"llm-{schema_name}.schema.json"))',
        ),
    ],
    # The other two boto3-dependent scripts got their SDK from
    # skills/llm-to-bedrock/scripts/pyproject.toml via `uv run --project $SCRIPTS`. That
    # pyproject cannot survive flattening, so the pins move into PEP 723 inline metadata
    # (same versions) and the scripts become standalone: `uv run <script>` resolves boto3
    # itself. Keeps the "pinned toolchain" guarantee the prose promises — Bedrock calls are
    # sensitive to the SDK version.
    "llm-preflight-bedrock.py": [
        (
            '"""Bedrock fail-fast preflight: authorization, region/model availability, quota.',
            "# /// script\n"
            '# requires-python = ">=3.10"\n'
            '# dependencies = ["boto3>=1.35,<2", "botocore>=1.35,<2"]\n'
            "# ///\n"
            '"""Bedrock fail-fast preflight: authorization, region/model availability, quota.',
        ),
    ],
    "llm-bedrock-pricing.py": [
        (
            '"""Look up Amazon Bedrock on-demand token prices.',
            "# /// script\n"
            '# requires-python = ">=3.10"\n'
            '# dependencies = ["boto3>=1.35,<2", "botocore>=1.35,<2"]\n'
            "# ///\n"
            '"""Look up Amazon Bedrock on-demand token prices.',
        ),
    ],
    # A script's own --help text must name the script by the name it actually ships under,
    # otherwise the usage line it prints cannot be copy-pasted.
    "heroku-validate-migration-report.py": [
        (
            "  python3 validate-heroku-migration-report.py /path/to/migration-report.html",
            "  python3 heroku-validate-migration-report.py /path/to/migration-report.html",
        ),
    ],
}


def _assert_no_shadowed_patches() -> None:
    """A duplicate key in either table is silent data loss.

    Python keeps only the last value for a repeated dict-literal key, so appending a second
    `"agent-advisor-scoring.py": [...]` entry drops the original patches without a word — a
    mistake made and caught during development. Re-derive the key lists from source and fail
    loudly instead.
    """
    src = Path(__file__).read_text()
    for table in ("SCRIPT_PATCHES", "MANUAL_REWRITES"):
        marker = f"{table}: dict"
        if marker not in src:
            continue
        after = src.split(marker, 1)[1]
        # bound to this dict literal only — a closing brace in column 0. Without this the
        # scan runs on into the next table and reports its keys as duplicates.
        end = after.find("\n}\n")
        body = after[: end if end != -1 else len(after)]
        keys = re.findall(r'^    "((?:[^"\\]|\\.)*)":', body, re.M)
        dupes = {k for k in keys if keys.count(k) > 1}
        if dupes:
            raise SystemExit(
                f"duplicate key(s) in {table}: {sorted(dupes)}\n"
                "  A repeated dict key silently discards the earlier entry. Merge them."
            )


def apply_script_patches(flat: str, text: str) -> str:
    for old, new in SCRIPT_PATCHES.get(flat, []):
        found = text.count(old)
        if found != 1:
            raise SystemExit(
                f"script patch for {flat} matched {found} times, expected 1.\n"
                f"  looking for: {old!r}\n"
                "  Upstream changed this line. Re-review the patch in SCRIPT_PATCHES."
            )
        text = text.replace(old, new)
    return text


def _skip(rel: str) -> bool:
    return any(p.search(rel) for p in SKIP_PATTERNS)


# --------------------------------------------------------------------------------------
# "Files in This Skill" layout trees
# --------------------------------------------------------------------------------------
# Both gcp-to-aws/SKILL.md and heroku-to-aws/SKILL.md document themselves with an ASCII
# tree of the plugin's NESTED directory layout. Nothing loads through those paths — every
# load directive in both files addresses its targets by bare filename — but the tree is the
# most prominent structural statement in the file, and it describes a layout this power
# does not have. A reviewer reading it (or grepping the fenced block) reasonably concludes
# the port still references `references/phases/discover/discover.md`.
#
# A prose disclaimer above the fence was the first attempt and was not enough: the
# disclaimer does not travel with the block when it is quoted, skimmed, or grepped. So
# rewrite the tree itself into the flat layout it actually ships, which also makes the
# fenced block agree with the reference scanners.
#
# Directory lines are dropped, every leaf is re-anchored directly under `steering/`, and the
# trailing `#` comments are kept and re-aligned. Leaves are emitted in upstream tree order,
# so the phase grouping is still legible in the sequence even without the directory nodes.
TREE_LEAF = re.compile(r"^[│ ]*[├└]── (?P<name>[A-Za-z0-9_.<>-]+\.[a-z]+)(?P<rest>\s*#.*)?$")
TREE_DIR = re.compile(r"^[│ ]*[├└]── [A-Za-z0-9_./-]+/\s*(#.*)?$")
TREE_FILLER = re.compile(r"^[│ ]*$")


def flatten_layout_tree(text: str, entry_flat: str, shipped: set[str]) -> str:
    """Rewrite a `## Files in This Skill` ASCII tree into this power's flat layout.

    Runs AFTER the generic reference pass, which has already rewritten the leaf names in
    place (`pricing-cache.md` -> `cached-prices.md`, every `heroku-` prefix). So the leaves
    read here are already the shipped flat names and need no further mapping — only the
    directory scaffolding has to go.
    """
    marker = "## Files in This Skill"
    if marker not in text:
        return text
    head, tail = text.split(marker, 1)
    open_fence = tail.find("```\n")
    if open_fence == -1:
        return text
    close_rel = tail.find("\n```", open_fence + 4)
    if close_rel == -1:
        return text
    body = tail[open_fence + 4: close_rel]
    rest = tail[close_rel + 4:]

    leaves: list[tuple[str, str]] = []
    for line in body.splitlines():
        if TREE_DIR.match(line) or TREE_FILLER.match(line) or not line.strip():
            continue
        m = TREE_LEAF.match(line)
        if not m:
            # the root line (`gcp-to-aws/`) and the "You are here" entry-point row
            continue
        flat = m.group("name")
        comment = (m.group("rest") or "").strip()
        if flat == entry_flat:
            continue  # the entry point is emitted first, by hand
        # A leaf the projection does not ship. heroku's tree lists its `shared/README.md`,
        # one of the four layout READMEs deliberately dropped (they document a nested
        # structure a flat power cannot have). Keeping the row would advertise a file that
        # is not there.
        if flat not in shipped:
            continue
        leaves.append((flat, comment))

    if not leaves:
        return text

    # de-dupe: the plugin vendors some shared assets into more than one directory, which
    # collapse onto a single flat name.
    seen: set[str] = set()
    uniq: list[tuple[str, str]] = []
    for flat, comment in leaves:
        if flat in seen:
            continue
        seen.add(flat)
        uniq.append((flat, comment))

    width = max(len(f) for f, _ in uniq + [(entry_flat, "")]) + 2
    lines = [
        "steering/",
        f"├── {entry_flat}".ljust(4 + width) + "# You are here (orchestrator + state machine)",
    ]
    for i, (flat, comment) in enumerate(uniq):
        connector = "└──" if i == len(uniq) - 1 else "├──"
        row = f"{connector} {flat}"
        lines.append(row.ljust(4 + width) + comment if comment else row)

    note = (
        "## Files in This Power\n\n"
        "Every file below is a flat file in `steering/`. This power has no subdirectories;\n"
        "steering files reference each other by bare filename.\n"
    )
    return head + note + "\n```\n" + "\n".join(lines) + "\n```" + rest


# --------------------------------------------------------------------------------------
# Per-skill projection rules: (regex over skill-relative path) -> flat name template.
# First match wins, so order matters. `\g<name>` groups are substituted.
# --------------------------------------------------------------------------------------
Rule = tuple[str, str]

SKILL_RULES: dict[str, list[Rule]] = {
    # ---------------- gcp-to-aws : primary engine, unprefixed ----------------
    "gcp-to-aws": [
        # every engine gets a symmetric orchestrator; POWER.md is a thin router above them
        (r"^SKILL\.md$", "gcp-orchestrator.md"),
        (r"^data/(?P<b>[^/]+)$", r"\g<b>"),
        # design-refs get a design-ref- prefix unless already carrying it
        (r"^references/design-refs/design-ref-(?P<b>.+)$", r"design-ref-\g<b>"),
        (r"^references/design-refs/(?P<b>.+)$", r"design-ref-\g<b>"),
        # clustering: only classification-rules.md needs disambiguating
        (r"^references/clustering/terraform/classification-rules\.md$",
         "clustering-classification-rules.md"),
        (r"^references/clustering/terraform/(?P<b>[^/]+)$", r"\g<b>"),
        # established rename in the published power
        (r"^references/shared/pricing-cache\.md$", "cached-prices.md"),
        (r"^references/shared/(?P<b>[^/]+)$", r"\g<b>"),
        (r"^references/phases/[^/]+/(?P<b>[^/]+)$", r"\g<b>"),
        (r"^references/vendored/(?P<rest>.+)$", "__CANONICAL__"),
    ],
    # ---------------- heroku-to-aws ----------------
    "heroku-to-aws": [
        (r"^SKILL\.md$", "heroku-orchestrator.md"),
        (r"^knowledge/[^/]+/(?P<b>[^/]+)$", r"heroku-\g<b>"),
        (r"^references/shared/heroku-(?P<b>[^/]+)$", r"heroku-\g<b>"),
        (r"^references/shared/(?P<b>[^/]+)$", r"heroku-\g<b>"),
        (r"^references/phases/[^/]+/(?P<b>[^/]+)$", r"heroku-\g<b>"),
        (r"^references/vendored/(?P<rest>.+)$", "__CANONICAL__"),
    ],
    # ---------------- llm-to-bedrock ----------------
    "llm-to-bedrock": [
        (r"^SKILL\.md$", "llm-orchestrator.md"),
        # helper skills: references/helpers/<name>/<name>.md -> llm-<name>.md
        (r"^references/helpers/(?P<n>[^/]+)/(?P=n)\.md$", r"llm-\g<n>.md"),
        (r"^references/helpers/[^/]+/references/(?P<b>[^/]+)$", r"llm-\g<b>"),
        (r"^references/helpers/[^/]+/(?P<b>[^/]+)$", r"llm-\g<b>"),
        (r"^scripts/schemas/(?P<b>[^/]+)\.json$", r"llm-\g<b>.schema.json"),
        (r"^scripts/(?P<b>[^/]+)\.py$", r"llm-\g<b>.py"),
    ],
    # ---------------- agent-advisor ----------------
    "agent-advisor": [
        (r"^SKILL\.md$", "agent-advisor-orchestrator.md"),
        (r"^references/runtimes/(?P<b>[^/]+)\.json$", r"agent-advisor-runtime-\g<b>.json"),
        (r"^references/decision-refs/(?P<b>[^/]+)$", r"agent-advisor-\g<b>"),
        (r"^references/phases/[^/]+/(?P<b>[^/]+)$", r"agent-advisor-\g<b>"),
        (r"^references/(?:diagram|handoff|output-templates)/(?P<b>[^/]+)$",
         r"agent-advisor-\g<b>"),
        (r"^references/vendored/(?P<rest>.+)$", "__CANONICAL__"),
        (r"^references/(?P<b>[^/]+)$", r"agent-advisor-\g<b>"),
        (r"^scripts/schemas/(?P<b>[^/]+)\.json$", r"agent-advisor-\g<b>.schema.json"),
        (r"^scripts/(?P<b>[^/]+)\.py$", r"agent-advisor-\g<b>.py"),
    ],
    # ---------------- tf-best-practices ----------------
    "tf-best-practices": [
        (r"^SKILL\.md$", "tf-best-practices.md"),
        (r"^references/(?P<b>[^/]+)$", r"\g<b>"),
        (r"^scripts/(?P<b>[^/]+)\.py$", r"tf-\g<b>.py"),
    ],
}

# Plugin-root assets outside skills/, each tagged with the engine whose namespace it
# speaks. The subagent definitions in agents/ reference their engine's helpers and scripts
# by bare filename, so they must inherit that engine's local rewrite map.
ROOT_FILES: dict[str, tuple[str, str]] = {
    "agents/generic-phase-worker-rw.md": ("generic-phase-worker-rw.md", ""),
    "agents/llm2bedrock-code-analyzer.md": ("llm-code-analyzer.md", "llm-to-bedrock"),
    "agents/llm2bedrock-code-rewriter.md": ("llm-code-rewriter.md", "llm-to-bedrock"),
    "agents/llm2bedrock-log-ingestor.md": ("llm-log-ingestor.md", "llm-to-bedrock"),
    "agents/llm2bedrock-prompt-evaluator.md": ("llm-prompt-evaluator.md", "llm-to-bedrock"),
    "agents/llm2bedrock-report-generator.md": ("llm-report-generator.md", "llm-to-bedrock"),
    "scripts/validate-migration-report.py": ("validate-migration-report.py", "gcp-to-aws"),
    "scripts/validate-heroku-migration-report.py": (
        "heroku-validate-migration-report.py", "heroku-to-aws"),
    "scripts/validate-startup-program-artifacts.py": (
        "validate-startup-program-artifacts.py", "gcp-to-aws"),
}

# Globs and DSL placeholders. The generic rewriter only understands concrete paths, so
# these pattern-shaped references are projected explicitly. Applied as plain string
# replacement, longest first, before the generic pass.
MANUAL_REWRITES: dict[str, str] = {
    "${CLAUDE_PLUGIN_ROOT}/skills/agent-advisor/references/decision-refs/<verdict>.md":
        "agent-advisor-<verdict>.md",
    "migration-to-aws/skills/gcp-to-aws/references/phases/clarify/clarify-ai.md":
        "clarify-ai.md",
    "<plugin>/skills/agent-advisor/SKILL.md": "agent-advisor-orchestrator.md",
    # the invariant tests are not shipped; keep the pointer truthful by sending readers
    # to the upstream plugin, which is where they live and can actually run
    "skills/agent-advisor/scripts/test_scoring.py":
        f"{UPSTREAM}/agent-advisor/scripts/test_scoring.py",
    "scripts/test_poc_shapes.py": f"{UPSTREAM}/agent-advisor/scripts/test_poc_shapes.py",
    "scripts/test_temporal_decision_refs.py":
        f"{UPSTREAM}/agent-advisor/scripts/test_temporal_decision_refs.py",
    "scripts/test_workload_classes.py":
        f"{UPSTREAM}/agent-advisor/scripts/test_workload_classes.py",
    "scripts/test_cost_levers.py": f"{UPSTREAM}/agent-advisor/scripts/test_cost_levers.py",
    "scripts/test_unit_grouping.py":
        f"{UPSTREAM}/agent-advisor/scripts/test_unit_grouping.py",
    # ---- llm-to-bedrock script invocation -------------------------------------------
    # Upstream runs its helpers as `uv run --project $SCRIPTS python $SCRIPTS/<snake>.py`,
    # where $SCRIPTS is <SKILL_BASE>/scripts and carries a pyproject.toml. Flattened, none
    # of that holds: there is no skill base, no scripts/ dir, and no pyproject (see
    # SCRIPT_PATCHES). The scripts are now standalone PEP 723 files in the flat dir, so
    # `--project ... python` collapses to a plain `uv run <script>`.
    #
    # These must stay longer than the bare `uv run --project ... python` fallbacks below;
    # MANUAL_REWRITES is applied longest-first, so the named-script forms win.
    "uv run --project <scriptsDir> python <scriptsDir>/validate_result.py":
        "uv run <scriptsDir>/llm-validate-result.py",
    "uv run --project $SCRIPTS python $SCRIPTS/validate_result.py":
        "uv run $SCRIPTS/llm-validate-result.py",
    "uv run --project <scriptsDir> python <scriptsDir>/bedrock_pricing.py":
        "uv run <scriptsDir>/llm-bedrock-pricing.py",
    "uv run --project <scriptsDir> python <scriptsDir>/iam_policy.py":
        "uv run <scriptsDir>/llm-iam-policy.py",
    "uv run --project $SCRIPTS python $SCRIPTS/preflight_bedrock.py":
        "uv run $SCRIPTS/llm-preflight-bedrock.py",
    "uv run --project $SCRIPTS python $SCRIPTS/render_report.py":
        "uv run $SCRIPTS/llm-render-report.py",
    # Ad-hoc heredocs and scripts generated into the user's repo still need the pinned SDK,
    # which `--project` used to supply. Carry the same pins inline instead of dropping them.
    "uv run --project <scriptsDir> python": PINNED_UV,
    "uv run --project $SCRIPTS python": PINNED_UV,
    # $SCRIPTS/$HELPERS both collapse onto the flat steering dir; <SKILL_BASE> has no
    # meaning here (Kiro emits no "Base directory for this skill" line).
    'The skill base directory is given in the "Base directory for this skill: X" line the harness\n'
    "emits at load time. Call it `<SKILL_BASE>`. Derived paths:\n\n"
    "- `$SCRIPTS` = `<SKILL_BASE>/scripts`\n"
    "- `$HELPERS` = `<SKILL_BASE>/references/helpers` (the former helper skills, now references)\n":
        "This power is flat: every reference file and executable helper lives directly in its\n"
        f"`steering/` directory. Call that directory's absolute path `{STEERING}` (see POWER.md\n"
        "— it is NOT inside the user's workspace, so a relative path will not reach it).\n"
        "Derived paths:\n\n"
        f"- `$SCRIPTS` = `{STEERING}` (the directory holding the `llm-*.py` helpers)\n"
        f"- `$HELPERS` = `{STEERING}` (the former helper skills, now `llm-*.md` reference files)\n",
    # the context line the orchestrator emits to each dispatched agent, which is where
    # `<scriptsDir>` comes from — it must carry a resolved ABSOLUTE path, because the agent
    # runs with the user's workspace as cwd
    "Scripts directory (pinned uv toolchain): <$SCRIPTS>":
        f"Scripts directory (pinned uv toolchain): <{STEERING}, resolved to an absolute path>",
    "`bedrock_pricing.py`": "`llm-bedrock-pricing.py`",
    # ---- "invoke the skill" / the Skill tool ------------------------------------------
    # Cross-engine handoff upstream is a Claude Code `Skill` tool call against a sibling
    # skill in the same plugin. A power has no such tool and no sibling skills — every engine
    # is already in the one flat namespace, so a handoff is just loading the other engine's
    # orchestrator. llm-to-bedrock's Assess phase marks this **CRITICAL / You MUST**, so left
    # alone it is a hard stop rather than a degradation.
    "**CRITICAL: You MUST use the Skill tool to invoke `migration-to-aws:gcp-to-aws` (a sibling skill\n"
    "in this same plugin). Do NOT perform the Assess phase yourself. Do NOT read source code, detect\n"
    "AI SDKs, or ask Clarify questions manually. The entire Assess phase is handled by the gcp-to-aws\n"
    "skill — you only invoke it and wait for completion.**\n\n"
    "### A1 — Invoke the Assess skill\n\n"
    "Call the **Skill** tool with skill name `migration-to-aws:gcp-to-aws`.\n":
        "**CRITICAL: You MUST delegate Assess to the gcp-to-aws engine. Do NOT perform the Assess\n"
        "phase yourself. Do NOT read source code, detect AI SDKs, or ask Clarify questions manually.\n"
        "The entire Assess phase is handled by that engine — you hand off and wait for completion.**\n\n"
        "### A1 — Hand off to the Assess engine\n\n"
        f"Load `{STEERING}/gcp-orchestrator.md` and follow it. There is no separate skill to call:\n"
        "every engine in this power shares one flat namespace, so the handoff is a file load.\n",
    "After invoking the Skill tool, the `gcp-to-aws` skill instructions will load into context.":
        "Once loaded, the gcp-to-aws instructions are in context.",
    "> confused by the skill's `gcp-to-aws` name — it also covers pure AI/LLM migrations with no":
        "> confused by the `gcp-to-aws` name — it also covers pure AI/LLM migrations with no",
    "Before invoking, tell the user:": "Before handing off, tell the user:",
    "> \"I'm now invoking the migration-to-aws Assess skill to discover your AI workloads and design":
        "> \"I'm now running the migration-to-aws Assess phase to discover your AI workloads and design",
    "- Anything else (including `no-status-file`) → the skill needs to run again. Re-invoke\n"
    "  `migration-to-aws:gcp-to-aws` via the Skill tool — it picks up where it left off.\n"
    "\n**Cap: at most 6 re-invocations.**":
        "- Anything else (including `no-status-file`) → Assess needs to run again. Re-load\n"
        f"  `{STEERING}/gcp-orchestrator.md` — it picks up where it left off.\n"
        "\n**Cap: at most 6 re-runs.**",
    # This one is already a negation ("no Skill tool call") and so was never wrong, but
    # rewording it clears the token from steering/ entirely, which lets LAYOUT_TOKENS guard
    # the phrase permanently instead of carrying an exception.
    "the sibling `gcp-to-aws` skill's phase instruction files — no Skill tool call, no turn\n"
    "boundary.":
        "the gcp-to-aws engine's phase instruction files, which are flat steering files in this\n"
        "same namespace — no separate invocation, no turn boundary.",
    # agent-advisor's handoff table
    "invoke the **`gcp-to-aws`": "hand off to the **gcp-to-aws",
    "invoke the **`llm-to-bedrock` skill**": "hand off to the **llm-to-bedrock engine**",
    # gcp Generate treats tf-best-practices as an invocable skill; here it is a steering file
    "**Before generating any `.tf`, invoke the `tf-best-practices` skill for its authoring posture**":
        "**Before generating any `.tf`, load `tf-best-practices.md` for its authoring posture**",
    "> Invoke the **`tf-best-practices`** skill, telling it you are **about to author `terraform/`**":
        "> Load **`tf-best-practices.md`**, applying it as though you are **about to author `terraform/`**",
    "**Invoke the `tf-best-practices` skill for the post-writing validation context**":
        "**Load `tf-best-practices.md` for the post-writing validation context**",
    # ---- $PLUGIN_ROOT: the report/policy validators -----------------------------------
    # A second, distinct base-dir token (not ${CLAUDE_PLUGIN_ROOT}) that the earlier sweep
    # missed. Three of these also carry pre-flattening script filenames.
    "$PLUGIN_ROOT/scripts/validate-heroku-migration-report.py":
        f"{STEERING}/heroku-validate-migration-report.py",
    # a bare `scripts/`-relative invocation of the same validator two lines below the
    # $PLUGIN_ROOT one; the generic pass flattens the filename but would drop the directory
    "python3 scripts/validate-heroku-migration-report.py":
        f"python3 {STEERING}/heroku-validate-migration-report.py",
    "$PLUGIN_ROOT/skills/tf-best-practices/scripts/validate-terraform-policy.py":
        f"{STEERING}/tf-validate-terraform-policy.py",
    "<tf-best-practices>/scripts/validate-terraform-policy.py":
        f"{STEERING}/tf-validate-terraform-policy.py",
    "$PLUGIN_ROOT/scripts/validate-migration-report.py":
        f"{STEERING}/validate-migration-report.py",
    "Resolve script from plugin root:": f"Resolve script from `{STEERING}`:",
    "the plugin root (`$PLUGIN_ROOT/skills/tf-best-practices/scripts/...`), the same convention the":
        f"`{STEERING}` (`{STEERING}/tf-validate-terraform-policy.py`), the same convention the",
    # ---- remaining unprojected prefixes ----------------------------------------------
    "`.../shared/ai-model-lifecycle.md`": "`ai-model-lifecycle.md`",
    # DELIBERATE CORRECTION of an upstream error, not a projection of it. The gemini/openai
    # delta references point at "`SKILL.md` § Option set: parameter_removed", but that option
    # set lives in behavior-delta-detection.md — there is no such section in any SKILL.md.
    # Projecting it faithfully resolves `SKILL.md` to llm-orchestrator.md, where the section
    # definitively does not exist, so the pointer would dangle in a way the reference scanners
    # cannot see (the target file exists; only the section is missing).
    "see `SKILL.md` § Option set: parameter_removed":
        "see `llm-behavior-delta-detection.md` § Option set: parameter_removed",
    # Prose naming the `design-refs/` directory. Harmless-looking, but it tells the agent a
    # subdirectory exists — and it survives the reference scanners because a bare directory
    # name has no file extension to match on.
    "Sub-design files may reference rubrics in `design-refs/`:":
        "Sub-design files may reference rubrics, which are the flat design-ref files:",
    "files (`design-refs/`, sub-files) ONLY when their trigger condition is met":
        "files (the flat design-ref rubrics, sub-files) ONLY when their trigger condition is met",
    "(located in this skill's `references/` directory)": "(it sits beside this file)",
    "`source_provider` sub-reference under its `references/` dir)":
        "`source_provider` sub-reference, also a flat steering file)",
    "shared/artifact-validation.md": "validate-artifacts.md",
    # the last un-redirected invariant test (its siblings were already handled above)
    "scripts/test_collapse_invariant.py":
        f"{UPSTREAM}/agent-advisor/scripts/test_collapse_invariant.py",
    # a provenance note about a file that no longer exists even upstream — drop the dead
    # path rather than pointing at it
    "Migrated from the former design-refs/eks-mapping-table.md":
        "Migrated from the former upstream EKS mapping table",
    # `<plugin>` in llm-orchestrator: the plugin manifest has no analogue here, and agent
    # definitions are flat steering files
    "<version from <plugin>/.claude-plugin/plugin.json>":
        "<this power's version from POWER.md frontmatter>",
    # NOTE: the two "Files in This Skill" layout trees (gcp + heroku) used to be patched
    # here, by rewriting the heading and the tree's root line and leaving the nested body
    # alone. That was not enough — see flatten_layout_tree(), which now rewrites the tree
    # body itself into the flat layout. Do not re-add a heading rewrite here; it would run
    # first and stop flatten_layout_tree() from finding its marker.
    # imperative "load a skill by name" contradicting these files' own guidance
    "**You MUST use the `resolve-bedrock-model-id` skill.**":
        "**You MUST follow `llm-resolve-bedrock-model-id.md`.**",
    "Load the `resolve-bedrock-model-id`\nskill, pass it the plan's ID and the region":
        "Load `llm-resolve-bedrock-model-id.md`\nand apply it to the plan's ID and the region",
    "<!-- SKILL:dependency-conflict-resolution -->":
        "<!-- see llm-dependency-conflict-resolution.md -->",
    # The C1-C6 dispatch table names the same non-existent registered agents. Point each row
    # at the contract file instead; the agentType column is what the inline path reads too.
    "| C1   | `migration-to-aws:llm2bedrock-code-analyzer`    |":
        "| C1   | `llm-code-analyzer.md`                        |",
    "| C2   | `migration-to-aws:llm2bedrock-log-ingestor`     |":
        "| C2   | `llm-log-ingestor.md`                         |",
    "| C3   | `migration-to-aws:llm2bedrock-prompt-evaluator` |":
        "| C3   | `llm-prompt-evaluator.md`                     |",
    "| C5   | `migration-to-aws:llm2bedrock-code-rewriter`    |":
        "| C5   | `llm-code-rewriter.md`                        |",
    "| C6   | `migration-to-aws:llm2bedrock-report-generator` |":
        "| C6   | `llm-report-generator.md`                     |",
    # A directory-only reference in live prose (heroku clarify-assemble), not in a tree. The
    # generic pass rewrites every workshop reference that carries a filename
    # (`references/phases/workshop/workshop.md` -> `heroku-workshop.md`), but a bare
    # directory has no filename to match on, so this one survived as a dead path an agent
    # could act on. Name the file instead of the directory.
    "(`references/phases/workshop/`) creates/patches":
        "(`heroku-workshop.md`) creates/patches",
    # slash-command invocations in user-facing copy would print a command that does not exist
    "`/migration-to-aws:llm-to-bedrock`": "the llm-to-bedrock engine",
    "/migration-to-aws:llm-to-bedrock": "the llm-to-bedrock engine",
    '  "plugin_version": "<$PLUGIN_VERSION>",':
        '  "plugin_version": null,',
    # ---- llm-to-bedrock Phase C agent dispatch ---------------------------------------
    # Same class as INTERPRETER's `_exec`, in a second place. Upstream names five REGISTERED
    # plugin agents (`migration-to-aws:llm2bedrock-*`); none exist here. Worse, the inline
    # escape hatch is gated on "no Agent/subagent dispatch tool", so a host that HAS generic
    # dispatch but not those names falls between both branches. Retarget to the generic
    # sub-agent with the agent file supplied as the contract, matching the `_exec` convention.
    "Phase C dispatches the five plugin agents sequentially via the **Agent tool** (subagent types\n"
    "`migration-to-aws:llm2bedrock-code-analyzer`, `migration-to-aws:llm2bedrock-log-ingestor`, `migration-to-aws:llm2bedrock-prompt-evaluator`,\n"
    "`migration-to-aws:llm2bedrock-code-rewriter`, `migration-to-aws:llm2bedrock-report-generator`). Each agent writes its result to\n":
        "Phase C dispatches the five phase agents sequentially. There is no per-agent registry here:\n"
        "dispatch the generic sub-agent and supply the phase's agent file as its contract —\n"
        f"`{STEERING}/llm-code-analyzer.md`, `{STEERING}/llm-log-ingestor.md`,\n"
        f"`{STEERING}/llm-prompt-evaluator.md`, `{STEERING}/llm-code-rewriter.md`,\n"
        f"`{STEERING}/llm-report-generator.md`. Each agent writes its result to\n",
    # the inline fallback names the agent file by the agentType column, which yields
    # `llm-llm2bedrock-code-analyzer.md`; the real files drop that segment
    "1. `Read` exactly ONE agent definition (`<plugin>/agents/<name>.md`) — never load more than":
        "1. `Read` exactly ONE agent definition — `$STEERING/llm-code-analyzer.md`,\n"
        "   `-log-ingestor`, `-prompt-evaluator`, `-code-rewriter`, or `-report-generator`\n"
        "   (drop the `llm2bedrock-` segment from the agentType column) — never load more than",
    # POWER.md frontmatter carries no version key, and this is a fingerprinted C0 field
    # Keep the FIELD name (it is referenced by the C0 invalidation table) and fix only its
    # unresolvable source: a power has no plugin manifest and POWER.md declares no version.
    '  "plugin_version": "<version from <plugin>/.claude-plugin/plugin.json>"':
        '  "plugin_version": null'
        '  // this power declares no version; always null, so it never invalidates a run',
    "User can re-run `/migration-to-aws:llm-to-bedrock`.":
        "User can re-invoke this power and ask to migrate to Bedrock again.",
    # Claude Code tool name; a power just asks the user directly
    "Otherwise use **AskUserQuestion**": "Otherwise ask the user directly",
    # upstream references a design-defaults.json that exists nowhere in the plugin; keep the
    # fallback rule the mapping fragment already defines instead of a dead pointer
    "use design-defaults.json":
        "the shared defaults file this once pointed at does not exist anywhere upstream, so "
        "fall back to the mapping fragment's same-major-version rule for",
    "verify `$PLUGIN_ROOT` is correct": f"verify `{STEERING}` is correct",
    # the last <SKILL_BASE>/${CLAUDE_PLUGIN_ROOT} mention: the note telling the orchestrator to
    # hand dispatched agents an absolute $HELPERS, since the token is empty in a subagent
    "Expand `$HELPERS` to its absolute path (you have `<SKILL_BASE>`) so the subagent — where\n"
    "`${CLAUDE_PLUGIN_ROOT}` is empty — receives a resolvable absolute path.":
        f"Expand `$HELPERS` to its absolute path (it is `{STEERING}`) so the dispatched agent — which\n"
        "does not inherit the token — receives a resolvable absolute path.",
    # ---- agent-advisor base-dir tokens ----------------------------------------------
    # `${CLAUDE_PLUGIN_ROOT}` is Claude-Code-only, and the documented fallback ("the skill's
    # own directory ... ./scripts/, ./references/runtimes/, ./references/decision-refs/")
    # describes a nested tree that does not exist here — so both branches were dead. Collapse
    # the whole definition onto $STEERING.
    "- **`$PLUGIN`** = `${CLAUDE_PLUGIN_ROOT}` (the installed plugin root). On Claude Code this token\n"
    "  substitutes inline. **If `${CLAUDE_PLUGIN_ROOT}` does not resolve** (some Cursor/Codex builds,\n"
    "  or a literal `${CLAUDE_PLUGIN_ROOT}` string showing up in a path error), fall back to the\n"
    "  skill's own directory: this SKILL.md lives at `<plugin>/skills/agent-advisor/SKILL.md`, so the\n"
    "  engine and its data are all inside this skill — scripts at `./scripts/...`, runtime profiles at\n"
    "  `./references/runtimes/...`, and decision refs at `./references/decision-refs/...` relative to\n"
    "  it. Prefer `${CLAUDE_PLUGIN_ROOT}/skills/agent-advisor/...`; use the relative fallback only when\n"
    "  it fails to resolve.\n":
        f"- **`{STEERING}`** = the absolute path of this power's `steering/` directory — the directory\n"
        "  these reference files were loaded from. The engine is flat: helper scripts are\n"
        f"  `{STEERING}/agent-advisor-*.py`, runtime profiles are `{STEERING}/agent-advisor-runtime-*.json`,\n"
        f"  and decision refs are `{STEERING}/agent-advisor-<topic>.md`. Resolve it once, before any\n"
        "  other step. It is **not** inside the user's workspace (a power installs under the Kiro\n"
        "  config dir, while the run directory is in the workspace), so a bare relative path such as\n"
        "  `steering/...` or `./scripts/...` will not reach these files — always use the absolute form.\n",
    # The whole gcp path-resolution table is dead in a flat power: every row maps a nested
    # prefix onto `$GCP_BASE/references/...`, which does not exist. Rewriting only the
    # `$GCP_BASE` token (as an earlier pass did) fixes the prefix and leaves the suffix
    # broken. Replace the table with the one rule that is actually true here.
    "$GCP_BASE = ${CLAUDE_PLUGIN_ROOT}/skills/gcp-to-aws\n```\n\n"
    "**IMPORTANT — relative path resolution table:** gcp-to-aws\n"
    "instruction files use several relative path prefixes. Resolve each as follows (the only path\n"
    "that does NOT go under `$GCP_BASE`is`$MIGRATION_DIR`, which stays under the target repo per Step 1):\n\n"
    "| Path prefix in instruction     | Resolves to                                      |\n"
    "| ------------------------------ | ------------------------------------------------ |\n"
    "| `references/shared/...`        | `$GCP_BASE/references/shared/...`                |\n"
    "| `references/design-refs/...`   | `$GCP_BASE/references/design-refs/...`           |\n"
    "| `references/clustering/...`    | `$GCP_BASE/references/clustering/...`            |\n"
    "| `references/phases/...`        | `$GCP_BASE/references/phases/...`                |\n"
    "| `shared/...` (short form)      | `$GCP_BASE/references/shared/...`                |\n"
    "| `design-refs/...` (short form) | `$GCP_BASE/references/design-refs/...`           |\n"
    "| `data/...`                     | `$GCP_BASE/data/...` (**not** under references/) |\n"
    "| `phases/...` (short form)      | `$GCP_BASE/references/phases/...`                |\n":
        f"$GCP_BASE = {STEERING}\n```\n\n"
        "**IMPORTANT — path resolution:** the gcp-to-aws engine is FLAT. Every one of its\n"
        f"instruction files lives directly in `{STEERING}` under its own flattened name, so there\n"
        "are no references, design-refs, clustering, phases, shared, or data\n"
        "subdirectories to resolve. Where a gcp instruction names a bare file, read\n"
        f"`{STEERING}/<that filename>`. Design references are prefixed `design-ref-`; the lookup\n"
        f"table from a GCP resource type to its reference is `{STEERING}/design-ref-index.md`.\n"
        f"`$MIGRATION_DIR` is the exception — it stays under the target repo per Step 1, not under\n"
        f"`{STEERING}`.\n",
    # NOTE: keys here match UPSTREAM text — MANUAL_REWRITES runs before the generic pass, so
    # `migration-plan.md`, not its flattened `agent-advisor-migration-plan.md` name.
    "All paths above are relative to `$GCP_BASE/references/` (defined in migration-plan.md).":
        f"All files above live directly in `$GCP_BASE` (= `{STEERING}`, defined in "
        "migration-plan.md); there are no subdirectories.",
    # build_diagram.py and scoring.py are both stdlib-only, so `--project` (which supplied
    # jsonschema from the dropped pyproject.toml) has nothing left to supply.
    "uv run --project ${CLAUDE_PLUGIN_ROOT}/skills/agent-advisor/scripts python "
    "${CLAUDE_PLUGIN_ROOT}/skills/agent-advisor/scripts/build_diagram.py":
        f"uv run {STEERING}/agent-advisor-build-diagram.py",
    # scoring.py is `import scoring`-ed as a MODULE. Flattening renames it to
    # agent-advisor-scoring.py, which is not an importable module name (hyphens), so no
    # PYTHONPATH can rescue it — load it by path instead.
    # Both comment lines go together: the sentence runs across them, so replacing only the
    # first would leave line 2 starting mid-clause. Ends on "each unit" to hand off cleanly
    # to the untouched line 3. Says "the scoring helper" rather than naming the file, because
    # the generic pass runs after this and would rewrite a bare `scoring.py` token here.
    "# scoring.py is imported as a module, so put its dir on PYTHONPATH (it is not on sys.path from\n"
    "# the run directory). Everything the loop needs is in answers.json (ALWAYS present): each unit\n":
        "# The scoring helper is loaded by file path, not imported by name — flattened, its filename\n"
        "# contains hyphens and so is not a valid module name. All the loop needs is answers.json\n"
        "# (ALWAYS present): each unit\n",
    'SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/agent-advisor/scripts"\n'
    'PYTHONPATH="$SCRIPTS" uv run python -c "\n'
    "import json, scoring\n":
        'uv run python -c "\n'
        "import json, importlib.util\n"
        f"_spec = importlib.util.spec_from_file_location('scoring', '{STEERING}/agent-advisor-scoring.py')\n"
        "scoring = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(scoring)\n",
    # ---- _exec sub-agent dispatch (INTERPRETER.md + the worker shell) ----------------
    # Upstream dispatches to a per-tier REGISTERED plugin agent
    # (`migration-to-aws:generic-phase-worker-rw`) and addresses the phase file relative to
    # a "Skill root" holding references/ and knowledge/. Kiro has neither: no per-tier agent
    # registry, and a flat steering dir. The worker shells ship here as ordinary steering
    # files, so dispatch goes to the generic sub-agent and the tier's file supplies the
    # CONTRACT. That keeps the context isolation `_exec` exists for; the tier becomes
    # advisory, which the platform-asymmetry note already allows ("intent, not a boundary").
    # Only `rw` ships, so the table must not name the ro/git files — they would be dangling.
    "in at dispatch time, so a single shell serves every phase at that tier. The plugin\n"
    "ships these workers under `agents/`; the tier maps to the worker name:\n\n"
    "| `_agent` | Worker to dispatch                          | Allow-list (the tier)         |\n"
    "| -------- | ------------------------------------------- | ----------------------------- |\n"
    "| `ro`     | `migration-to-aws:generic-phase-worker-ro`  | Read, Grep, Glob              |\n"
    "| `rw`     | `migration-to-aws:generic-phase-worker-rw`  | Read, Grep, Glob, Write, Edit |\n"
    "| `git`    | `migration-to-aws:generic-phase-worker-git` | rw + git                      |\n\n"
    "(Only the workers a skill actually needs are shipped. A phase may only name a tier\n"
    "whose worker file is present on disk — CI rejects an `_exec._agent` that names a tier\n"
    "with no `agents/generic-phase-worker-<tier>.md`, since dispatching to an absent worker\n"
    "would fail at runtime. `rw` deliberately excludes shell/Bash so it cannot reach `git`\n"
    "— that keeps the `rw`/`git` distinction real.)\n\n":
        "in at dispatch time, so a single shell serves every phase at that tier. This power\n"
        "ships the worker shells as steering files; the tier maps to a worker contract file:\n\n"
        "| `_agent` | Worker contract file           | Intended allow-list (the tier) |\n"
        "| -------- | ------------------------------ | ------------------------------ |\n"
        "| `ro`     | not shipped by this power      | Read, Grep, Glob               |\n"
        "| `rw`     | `generic-phase-worker-rw.md`   | Read, Grep, Glob, Write, Edit  |\n"
        "| `git`    | not shipped by this power      | rw + git                       |\n\n"
        "(Only the workers a skill actually needs are shipped, and this power ships `rw` only —\n"
        "so `rw` is the only tier a phase may name. A phase naming an unshipped tier falls back\n"
        "to inline execution rather than failing.)\n\n"
        "**There is no per-tier agent registry on Kiro.** Dispatch to the generic\n"
        "`general-task-execution` sub-agent and supply the worker CONTRACT by pointing it at the\n"
        "tier's file above. The tier is therefore advisory here, not enforced — which is exactly\n"
        "how the platform-asymmetry note below already tells you to treat it.\n\n",
    # INTERPRETER's copy of the dispatch context block
    "To dispatch, invoke the tier's worker via the host's Agent/subagent tool with a\n"
    "context block that tells the generic worker WHICH phase to run and where. Build these\n"
    "exact labeled lines (the worker parses them; omit an optional line when empty):\n\n"
    "```\n"
    "Skill: <the skill name, e.g. heroku-to-aws>\n"
    "Skill root: <absolute path to the skill directory (where references/ and knowledge/ live)>\n"
    "Phase: <the _phase id, e.g. discover>\n"
    "Phase file: <path, relative to Skill root, of the phase orchestrator (references/phases/<phase>/<phase>.md)>\n":
        "To dispatch, invoke the generic `general-task-execution` sub-agent with a context block\n"
        "that tells it which worker contract to adopt and WHICH phase to run. Build these\n"
        "exact labeled lines (the worker parses them; omit an optional line when empty):\n\n"
        "```\n"
        f"Worker contract (Read this FIRST and follow it): <{STEERING}>/generic-phase-worker-rw.md\n"
        "Skill: <the engine name, e.g. heroku-to-aws>\n"
        f"Skill root: <{STEERING}, absolute — every reference file is flat in this one directory>\n"
        "Phase: <the _phase id, e.g. discover>\n"
        "Phase file: <the phase orchestrator's flat steering filename, e.g. heroku-discover.md>\n",
    # the worker shell's own copy of the same block
    "Skill root: <absolute path to the skill directory — where references/ and knowledge/ live>\n":
        f"Skill root: <{STEERING}, absolute — every reference file is flat in this one directory>\n",
    "Phase file: <path, relative to Skill root, of the phase orchestrator to load and run>\n":
        "Phase file: <the phase orchestrator's flat steering filename, resolved under Skill root>\n",
    # the fallback must also fire when the tier has no worker file, not only when the host
    # lacks a dispatch tool — Kiro HAS one, so the original trigger never fired here
    "**Fallback — no subagent tool (inline hosts).** If the host has no Agent/subagent\n"
    "dispatch tool (e.g. inline-only platforms), do NOT fail: run the phase's fragments +\n":
        "**Fallback — no dispatch mechanism, or no worker file for the tier.** If the host has no\n"
        "sub-agent dispatch tool (inline-only platforms), or the tier's worker contract file is\n"
        "not shipped, do NOT fail: run the phase's fragments +\n",
    "5. **Worker-exists:** the tier's `agents/generic-phase-worker-<tier>.md` must be\n"
    "   shipped on disk. A phase cannot dispatch to a tier whose worker the plugin does\n"
    "   not ship (it would fail at runtime). (Skipped when the plugin `agents/` dir\n"
    "   cannot be located — tolerant of a non-standard layout.)\n":
        "5. **Worker-exists:** the tier's `generic-phase-worker-<tier>.md` must be shipped in\n"
        "   `steering/`. A phase cannot dispatch to a tier whose worker this power does not\n"
        "   ship — it falls back to inline execution instead. This power ships `rw` only.\n",
    # The report reference fixture lives at the PLUGIN root (fixtures/), not under a skill,
    # and is not shipped. Upstream refers to it in two inconsistent forms — one bare, one
    # half-qualified — and neither resolves here, so both normalise to the upstream pointer.
    # Longest-first ordering means the qualified form is consumed before the bare one.
    "migrate/plugins/migration-to-aws/fixtures/migration-report-reference.html":
        f"{UPSTREAM_PLUGIN}/fixtures/migration-report-reference.html",
    "fixtures/migration-report-reference.html":
        f"{UPSTREAM_PLUGIN}/fixtures/migration-report-reference.html",
    # ---- tf-best-practices fixtures + verification -----------------------------------
    # The fixture corpus and its pytest suite are test data, deliberately not shipped (see
    # _skip / _is_dropped_test). Left as-is, both sections pointed at local paths that do not
    # exist and told the reader to `cd skills/tf-best-practices/`. The shapes themselves
    # document the checker's contract, so they stay — the paths move upstream, and Verification
    # becomes something runnable here: the checker against a real directory.
    "## Fixtures (also the checker's regression suite)\n\n"
    "`fixtures/terraform-policy/` holds **intentionally-shaped** Terraform used by\n"
    "`scripts/test_validate_terraform_policy.py`:\n":
        "## Reference shapes (the checker's regression suite)\n\n"
        "The checker is verified upstream against intentionally-shaped Terraform under\n"
        f"`{UPSTREAM}/tf-best-practices/fixtures/terraform-policy/`.\n"
        "That corpus is test data and is **not shipped here**, but the shapes document the\n"
        "checker's contract:\n",
    'These are deliberately non-compliant test data (never deployed). They are excluded from the\n'
    'repo-wide `checkov` scan via `.checkov.yaml` `skip-path`; do **not** "harden" them — doing so\n'
    "breaks the tests that assert the failure paths.\n\n"
    "## Verification\n\n"
    "```bash\n"
    "# from skills/tf-best-practices/\n"
    "uv run --python 3.12 --with pytest python -m pytest scripts/test_validate_terraform_policy.py -q\n"
    "```\n":
        "Those are deliberately non-compliant inputs, never deployed. If you are editing them\n"
        "upstream, do **not** \"harden\" them — that breaks the tests asserting the failure paths.\n\n"
        "## Verification\n\n"
        "Run the checker against the Terraform you generated. It takes a directory, is\n"
        "zero-dependency, and needs no `terraform init`:\n\n"
        "```bash\n"
        f"uv run {STEERING}/tf-validate-terraform-policy.py <directory containing .tf files>\n"
        "```\n\n"
        "It prints a leading `POLICY_OK | checks=...` or `POLICY_FAIL | checks=...` summary naming\n"
        "every rule it ran, then one `POLICY_FAIL | file=<f> | line=<n> | rule=<r> | reason=<why>`\n"
        "line per violation. The upstream pytest suite that asserts against the reference shapes\n"
        "above is not shipped with this power.\n",
    "references/phases/<sidebar>/<sidebar>.md": "<sidebar>.md",
    "references/phases/<phase>/<phase>.md": "<phase>.md",
    "references/decision-refs/*.md": "agent-advisor-*.md",
    "references/runtimes/*.json": "agent-advisor-runtime-*.json",
    "references/design-refs/*.md": "design-ref-*.md",
    "design-refs/*.md": "design-ref-*.md",
    "knowledge/**.json": "*.json",
}


def project(skill: str, rel: str) -> str | None:
    """Map a skill-relative path to its flat steering name (or None to skip)."""
    for pattern, template in SKILL_RULES[skill]:
        m = re.match(pattern, rel)
        if not m:
            continue
        if template == "__CANONICAL__":
            rest = m.group("rest")
            if rest in CANONICAL_SHARED:
                return CANONICAL_SHARED[rest]
            return None  # vendored README etc.
        flat = m.expand(template)
        # Plugin scripts use snake_case; the flat steering namespace is hyphenated.
        if flat.endswith(".py"):
            flat = flat[:-3].replace("_", "-") + ".py"
        return flat
    return None


# --------------------------------------------------------------------------------------
# Reference rewriting
# --------------------------------------------------------------------------------------
TEXT_SUFFIXES = {".md", ".json", ".py", ".template", ".txt", ".yml", ".yaml"}

# Path scaffolding that disappears in the flat layout. The plugin addresses files through
# a number of base-dir tokens; each collapses to a bare flat name.
#
# Prefixes are scoped to the engine that actually uses the token. Applying every prefix to
# every engine manufactures ambiguity: `$GCP_BASE/...` only ever means the gcp-to-aws tree,
# so letting heroku claim it too would create two rewrites for one search string.
GENERIC_PREFIXES = (
    "${CLAUDE_PLUGIN_ROOT}/skills/{skill}/",
    "$PLUGIN/skills/{skill}/",
    "skills/{skill}/",
    # relative climbs out of a phases/<phase>/ directory back to the skill root
    "../../../",
    "../../",
    "../",
    "./",
    "",
)

ENGINE_PREFIXES: dict[str, tuple[str, ...]] = {
    # the gcp engine's own root, as agent-advisor's migration-plan stage addresses it
    "gcp-to-aws": ("$GCP_BASE/",),
    "llm-to-bedrock": (
        "<SKILL_BASE>/",
        "$HELPERS/",   # <SKILL_BASE>/references/helpers
        "$SCRIPTS/",   # <SKILL_BASE>/scripts
        "<BDD_DIR>/",  # $HELPERS/behavior-delta-detection
    ),
}


def _prefixes_for(skill: str) -> tuple[str, ...]:
    return GENERIC_PREFIXES + ENGINE_PREFIXES.get(skill, ())


def _suffix_forms(rel: str) -> list[str]:
    """Longest-to-shortest path suffixes of a skill-relative path."""
    parts = rel.split("/")
    return ["/".join(parts[i:]) for i in range(len(parts))]


def build_refmap(
    emitted: dict[str, dict[str, str]]
) -> tuple[list[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    """Build two tiers of (search, replacement) rewrites, longest search first.

    Returns ``(global_pairs, local_pairs_by_skill)``.

    * **global** — search strings that still contain a ``/``. A multi-segment path is
      unambiguous, so it is safe to apply across every engine. This is what makes
      cross-engine references work: ``agent-advisor-migration-plan.md`` points at
      ``$GCP_BASE/references/phases/design/design.md``, which only the gcp-to-aws map
      knows how to resolve.
    * **local** — bare basenames, scoped to the file's own engine. ``clarify.md`` means
      ``heroku-clarify.md`` inside a heroku file and ``clarify.md`` inside a gcp file, so
      these must never leak across engines.
    """
    # search -> {(skill, flat)}, so a key claimed by two engines can be spotted
    candidates: dict[str, set[tuple[str, str]]] = {}

    for skill, mapping in emitted.items():
        for rel, flat in mapping.items():
            # A JSON Schema under scripts/schemas/ shares its basename with the run-time
            # artifact it describes (scripts/schemas/scoring-result.json describes
            # $RUN_DIR/scoring-result.json). Registering the bare name would rewrite every
            # mention of the *artifact* into the schema filename, so these are matched only
            # via a multi-segment path.
            path_only = rel.startswith("scripts/schemas/")
            for suffix in _suffix_forms(rel):
                for prefix in _prefixes_for(skill):
                    # plain replace, not .format(): the prefixes contain ${CLAUDE_PLUGIN_ROOT}
                    search = prefix.replace("{skill}", skill) + suffix
                    if not search or search == flat:
                        continue
                    if path_only and "/" not in search:
                        continue
                    candidates.setdefault(search, set()).add((skill, flat))

    global_pairs: set[tuple[str, str]] = set()
    local_pairs: dict[str, set[tuple[str, str]]] = {s: set() for s in emitted}

    for search, owners in candidates.items():
        targets = {flat for _skill, flat in owners}
        if len(targets) == 1 and "/" in search:
            # one meaning everywhere, and specific enough to apply cross-engine
            global_pairs.add((search, next(iter(targets))))
        else:
            # Ambiguous across engines (`phases/clarify/clarify-assemble.md` exists in both
            # agent-advisor and heroku-to-aws) or a bare basename. Resolve per engine, so a
            # file is only ever rewritten with its own engine's meaning. Registering these
            # globally would make the winner depend on set iteration order — the source of a
            # non-determinism bug where agent-advisor files picked up heroku- targets.
            for skill, flat in owners:
                local_pairs[skill].add((search, flat))

    def order(pairs) -> list[tuple[str, str]]:
        return sorted(pairs, key=lambda p: (-len(p[0]), p[0]))

    return order(global_pairs), {s: order(p) for s, p in local_pairs.items()}


def compile_rewriter(pairs: list[tuple[str, str]]):
    """Compile one alternation regex for the whole rewrite table.

    There are ~9k search strings; applying them as individual `re.subn` passes over every
    file is quadratic and takes minutes. A single alternation is one pass per file.

    Matches are bounded so a short name never eats a longer one (`ai.md` must not fire
    inside `clarify-ai.md`, `design.md` must not fire inside `heroku-design.md`), and the
    alternation is ordered longest-first so the most specific path wins at a given
    position.
    """
    table: dict[str, str] = {}
    for search, replacement in pairs:
        # first writer wins: `pairs` arrives ordered by specificity. A genuine conflict
        # (same search, two targets, within one engine's table) would make output depend on
        # ordering, so fail loudly instead of picking silently.
        if search in table and table[search] != replacement:
            raise SystemExit(
                f"ambiguous rewrite for {search!r}: "
                f"{table[search]!r} vs {replacement!r}. Resolve in build_refmap."
            )
        table[search] = replacement

    if not table:
        return None, {}

    alternation = "|".join(
        re.escape(s) for s in sorted(table, key=lambda s: (-len(s), s))
    )
    pattern = re.compile(
        r"(?<![A-Za-z0-9_./\-])(" + alternation + r")(?![A-Za-z0-9_\-])"
    )
    return pattern, table


def rewrite(text: str, pattern, table: dict[str, str]) -> tuple[str, int]:
    count = 0

    # Pattern-shaped references first: they are the most specific forms, and letting the
    # generic pass touch them would leave half-rewritten globs behind.
    #
    # Each replacement is parked behind a sentinel rather than written inline, because an
    # earlier replacement's OUTPUT can contain a later key. That really happened: the
    # qualified `migrate/plugins/.../fixtures/x.html` key produced a string still containing
    # the bare `fixtures/x.html` key, which then fired again and doubled the prefix. Sentinels
    # make each key see only original upstream text, and also protect these results from the
    # generic pass below.
    parked: list[str] = []
    for search, replacement in sorted(MANUAL_REWRITES.items(), key=lambda kv: -len(kv[0])):
        if search in text:
            count += text.count(search)
            token = f"\x00MR{len(parked)}\x00"
            parked.append(replacement)
            text = text.replace(search, token)

    def unpark(s: str) -> str:
        for i, replacement in enumerate(parked):
            s = s.replace(f"\x00MR{i}\x00", replacement)
        return s

    if pattern is None:
        return unpark(text), count

    def sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return table[m.group(1)]

    return unpark(pattern.sub(sub, text)), count


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def collect(plugin: Path) -> dict[str, dict[str, str]]:
    """skill -> {skill-relative path: flat steering name}"""
    emitted: dict[str, dict[str, str]] = {}
    for skill in SKILL_RULES:
        root = plugin / "skills" / skill
        if not root.is_dir():
            print(f"  ! missing skill dir: {root}", file=sys.stderr)
            continue
        mapping: dict[str, str] = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
            if _skip(rel) or "fixtures/" in rel or _is_dropped_test(skill, rel):
                continue
            flat = project(skill, rel)
            if flat:
                mapping[rel] = flat
        emitted[skill] = mapping

    # canonical shared assets, emitted once from skills/shared
    shared: dict[str, str] = {}
    for rel, flat in CANONICAL_SHARED.items():
        if (plugin / "skills" / "shared" / rel).is_file():
            shared[rel] = flat
    emitted["shared"] = shared
    emitted["__root__"] = {
        rel: flat for rel, (flat, _engine) in ROOT_FILES.items()
        if (plugin / rel).is_file()
    }
    return emitted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True, type=Path,
                    help="path to migrate/plugins/migration-to-aws")
    ap.add_argument("--power", type=Path, default=Path(__file__).resolve().parent.parent,
                    help="power root (defaults to this script's parent)")
    ap.add_argument("--check", action="store_true",
                    help="report the projection without writing files")
    args = ap.parse_args()

    _assert_no_shadowed_patches()

    plugin: Path = args.plugin.resolve()
    power: Path = args.power.resolve()
    steering = power / "steering"

    if not (plugin / "skills").is_dir():
        print(f"error: {plugin} has no skills/ dir", file=sys.stderr)
        return 2

    emitted = collect(plugin)
    global_pairs, local_pairs = build_refmap(emitted)

    # collision detection across the flat namespace
    owners: dict[str, list[str]] = {}
    for skill, mapping in emitted.items():
        for rel, flat in mapping.items():
            owners.setdefault(flat, []).append(f"{skill}:{rel}")
    collisions = {
        flat: srcs for flat, srcs in owners.items()
        if len(srcs) > 1 and flat not in CANONICAL_SHARED.values()
    }

    total = sum(len(m) for m in emitted.values())
    print(f"projected {total} files across {len(emitted)} groups")
    for skill, mapping in emitted.items():
        print(f"  {skill:20s} {len(mapping):4d}")
    if collisions:
        print("\nCOLLISIONS (same flat name, different sources):")
        for flat, srcs in sorted(collisions.items()):
            print(f"  {flat}\n    " + "\n    ".join(srcs))

    if args.check:
        return 1 if collisions else 0
    if collisions:
        print("\nrefusing to write while collisions exist", file=sys.stderr)
        return 2

    if steering.exists():
        shutil.rmtree(steering)
    steering.mkdir(parents=True)

    # every flat name this run will emit — flatten_layout_tree() drops tree rows naming a
    # file the projection does not ship. Computed before the loop so it covers all engines.
    shipped = {flat for m in emitted.values() for flat in m.values()}

    rewrites = 0
    written = 0
    for skill, mapping in emitted.items():
        if skill == "shared":
            base = plugin / "skills" / "shared"
        elif skill == "__root__":
            base = plugin
        else:
            base = plugin / "skills" / skill
        # global (multi-segment) rewrites first, then this engine's bare names, then the
        # canonical shared bare names.
        def rewriter_for(engine: str):
            return compile_rewriter(
                global_pairs
                + local_pairs.get(engine, [])
                + local_pairs.get("shared", [])
            )

        pattern, table = rewriter_for(skill)
        for rel, flat in sorted(mapping.items()):
            src = base / rel
            dst = steering / flat
            if skill == "__root__":
                # inherit the engine namespace this root asset speaks
                pattern, table = rewriter_for(ROOT_FILES[rel][1])
            if src.suffix in TEXT_SUFFIXES:
                text = src.read_text(encoding="utf-8")
                text, n = rewrite(text, pattern, table)
                text = apply_script_patches(flat, text)
                # after the reference pass, so the tree's leaves are already flat names
                text = flatten_layout_tree(text, flat, shipped)
                rewrites += n
                dst.write_text(text, encoding="utf-8")
            else:
                shutil.copy2(src, dst)
            written += 1

    print(f"\nwrote {written} files to {steering} ({rewrites} reference rewrites)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
