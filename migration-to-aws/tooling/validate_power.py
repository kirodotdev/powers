#!/usr/bin/env python3
"""Validate the flat steering/ namespace of this power.

Two failure modes matter after flattening the upstream plugin:

1. **Unflattened paths** — a reference still shaped like a plugin path
   (`references/phases/design/design.md`, `$PLUGIN/skills/...`). In a flat power there
   are no subdirectories, so any surviving `/` in a steering reference is a bug.
2. **Dangling names** — a bare `foo.md` that no longer exists in steering/.

Runtime artifacts (files the power *writes* during a run, e.g. `aws-design.json`) are not
steering files and are excluded via ARTIFACT_HINTS.

    python3 tooling/validate_power.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

STEERING = Path(__file__).resolve().parent.parent / "steering"

REF_EXT = (".md", ".json", ".py", ".template", ".schema.json")

# Inline-code spans and markdown link targets are where references live.
BACKTICK = re.compile(r"`([^`\n]+)`")
MDLINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

# Directory names that only exist inside the upstream plugin. If one of these survives in
# a reference, the flattener failed to project it.
# `shared/` and `scripts/` were missing here and hid four real defects (a `shared/…md`
# pointer and three `$PLUGIN_ROOT/scripts/…py` invocations), so keep this list in step with
# the plugin's actual directory names.
PLUGIN_SEGMENT = re.compile(
    r"(^|/)(references|skills|helpers|phases|design-refs|decision-refs|clustering|"
    r"knowledge|vendored|output-templates|runtimes|dsl|data|shared|scripts|agents|"
    r"fixtures|tools|docs)/"
)

# Host/plugin base-directory tokens. A flat power addresses its own files through exactly
# one token ($STEERING); anything else here is an unprojected plugin-ism that will not
# resolve at runtime. Checked as raw substrings, independent of reference extraction —
# these hid in prose and in truncated forms (`$GCP_BASE/references/`) that the
# extension-based extractor never saw.
LAYOUT_TOKENS = (
    "CLAUDE_PLUGIN_ROOT",
    "$PLUGIN_ROOT",
    "<SKILL_BASE>",
    "<plugin>",
    "$PLUGIN/",
    "$GCP_BASE/references",
    "$SCRIPTS/schemas",
    # Claude Code's Skill tool has no Kiro equivalent, and every engine already shares this
    # one flat namespace — a cross-engine handoff is a file load, not an invocation.
    "Skill tool",
    "Skill** tool",
)

# Plugin directory names appearing as a *directory* reference, with no filename after them.
#
# These were originally listed in LAYOUT_TOKENS as backtick-wrapped literals (`` `references/` ``),
# which made the check depend on the exact markup around the token. It missed two real
# classes: the un-backticked directory rows inside the "Files in This Skill" ASCII trees,
# and deeper backticked forms like `` `references/phases/workshop/` `` — which does not
# contain `` `references/` `` as a substring, so the literal never fired. A reviewer found
# both by reading the file, which is what this validator exists to prevent.
#
# Matched anywhere in the text, independent of surrounding markup. The reference extractor
# cannot see these: a bare directory has no file extension to key on.
#
# The trailing lookahead requires the reference to END at a directory boundary, so prose
# that merely contains a slash between two words does not trip it (`≥2 phases/rows` in
# validate-migration-report.md is a table cell, not a path).
LAYOUT_DIRS = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"(?:references|design-refs|decision-refs|phases|vendored|helpers|output-templates|dsl)/"
    r"(?:[a-z0-9-]+/)*"
    r"(?![A-Za-z0-9_.-])"
)

# Files produced or consumed at run time, never steering content.
ARTIFACT_HINTS = (
    # run state + phase artifacts written under $MIGRATION_DIR / $RUN_DIR
    "phase-status.json", "aws-design", "estimation-", "estimation.json",
    "generation-", "gcp-resource-", "migration-preview.json", "preferences",
    "answers.json", "confirm.json", "context-signals.json", "trace.json",
    "diagram.md", "plan.md", "mini-brief.md", "handoff-summary.md",
    "harness.json", "created-resources.json", "migration-plan-injection.json",
    "-inventory.json", "-profile.json", "scenario", "index.json", "manifest.json",
    "-extracted.json", "assets.json", "regions.json", "addons.json", "apps.json",
    "spaces.json", "pipelines.json",
    # llm-to-bedrock run artifacts
    "analysis.json", "rewrite.json", "eval.json", "ingestion.json",
    "delta-decisions.json", "scoring-result.json", "verdict.json",
    "MIGRATION_REPORT", "comparison_results.json",
    # agent-advisor per-phase outputs, and the generate-phase validation report
    "design.json", "estimate.json", "feedback.json", "validation-report.json",
    "inputschema.json",  # a JSON-path expression in retarget-gotchas.md, not a file
    # user-repo files the power reads, and code it generates into the user's repo
    "package.json", "package-lock.json", "requirements.txt", "pyproject.toml",
    "uv.lock", "setup.py", "conftest.py", "composer.json", "vercel.json",
    "app.json", "Procfile", "tsconfig.json", "plugin.json", "mcp.json",
    "credentials.json", "service-account.json",
    "agent.py", "app.py", "handler.py", "job.py", "prompts.py", "smoke_worker.py",
    "bridge_retarget.py", "gateway_config", "strands_agents.py", "cost_compare.py",
    "resolve_source_model.py", "source_baseline.py",
    "test_comparison.py", "test_bedrock_", "serverless_workers.md",
    ".tf", "terraform.tfvars",
    "README.md", "MIGRATION.md", "MIGRATION_GUIDE.md", "RUNBOOK.md", "COSTS.md",
    "STARTUP_PROGRAMS.md", "recommendation.md", "SKILL.md",
    ".gitignore", ".env", "Dockerfile", "docker-compose.yml", "buildspec.yml",
    # more run-time outputs and user-repo paths, surfaced once the slashed-token and
    # bare-token gaps below were closed
    "context-notes.md", "discovery-summary.md", "discovery-log.md",
    "_extract_billing.py", "_extract_live.py", "spec.template",
    "README-DMS.md", "README-BIGQUERY", "scoring.json", "test-results.json",
    "iam-policy.json", "POWER.md",
    # CLI usage placeholders inside the shipped scripts' own --help text
    "args.json", "report.json", "payload.json", "saved.json", "current.json",
    "current-context.json", "schema.json", "out.json", "extracted.json", "tf.json",
    # example application code in schema/discovery docs (the user's repo, not ours)
    "core.py", "client.py", "indexer.py", "researcher.py", "writer.py",
    "reader.py", "search.py", "__init__.py", "data.json", "x.py",
    # upstream design docs that are not shipped
    "design-execute-orchestration",
)

# Deliberate pointers at the upstream plugin. `awslabs/startups:` is the canonical form, but
# the bare-token scan cannot span the `:` so it captures the tail — accept both.
UPSTREAM_POINTER = (
    "awslabs/startups:",
    "migrate/plugins/migration-to-aws/",
)

# gcloud / heroku live-capture dumps: `<resource>.json` and `<resource>-<scope>.json`
LIVE_CAPTURE = re.compile(
    r"^(gce|gke|run|sql|spanner|firestore|redis|pubsub|dns|buckets|networks|subnets|"
    r"firewalls|functions|secrets|sa|bq|vertex|connector|ps|domains|config-keys|"
    r"space|space-peerings|pipeline|app)(-[<A-Za-z0-9_.*-]+>?)?\.json$"
)

# Bare tokens that are not references at all (regex fragments inside test scripts,
# split-off file extensions, glob-only strings).
NOISE = re.compile(r"^(json|py|md|\*|\?|[*?].*|.*\\\..*|-.*)$")


def is_artifact(name: str) -> bool:
    low = name.lower()
    if any(h.lower() in low for h in ARTIFACT_HINTS):
        return True
    if LIVE_CAPTURE.match(name):
        return True
    if NOISE.match(name):
        return True
    # glob / placeholder shaped, not a concrete file (`{id}` is a runtime substitution the
    # same way `<phase>` is)
    return "*" in name or "<" in name or "{" in name


# A filename-shaped token anywhere in the text, backticked or not. Backtick/mdlink
# extraction alone missed references sitting in plain prose and inside JSON string values
# (that is how a dangling `design-defaults.json` survived), so this runs as well.
BARE_REF = re.compile(
    r"(?<![A-Za-z0-9_.\-/])"
    r"((?:[A-Za-z0-9_$<>{}\-]+/)*[A-Za-z0-9_][A-Za-z0-9_.\-]*"
    r"\.(?:md|json|py|template))"
    r"(?![A-Za-z0-9_\-])"
)


def candidates(text: str) -> set[str]:
    out: set[str] = set()
    for m in list(BACKTICK.finditer(text)) + list(MDLINK.finditer(text)):
        tok = m.group(1).strip()
        # a reference is a single token ending in a known extension
        if " " in tok or "\t" in tok:
            continue
        if not tok.endswith(REF_EXT):
            continue
        out.add(tok)
    for m in BARE_REF.finditer(text):
        out.add(m.group(1))
    return out


def check_power_md(present: set[str]) -> list[str]:
    """POWER.md is hand-written, so its `steering/<name>` pointers need checking too."""
    power_md = STEERING.parent / "POWER.md"
    if not power_md.is_file():
        return ["POWER.md is missing"]
    text = power_md.read_text(encoding="utf-8")
    bad = []
    for m in re.finditer(r"steering/([A-Za-z0-9_.\-]+)", text):
        name = m.group(1)
        if name not in present:
            bad.append(name)
    return sorted(set(bad))


def main() -> int:
    present = {p.name for p in STEERING.iterdir() if p.is_file()}

    unflattened: dict[str, set[str]] = defaultdict(set)
    dangling: dict[str, set[str]] = defaultdict(set)
    layout: dict[str, set[str]] = defaultdict(set)

    for path in sorted(STEERING.iterdir()):
        if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".template"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in LAYOUT_TOKENS:
            if token in text:
                layout[token].add(path.name)
        for m in LAYOUT_DIRS.finditer(text):
            layout[m.group(0)].add(path.name)
        for tok in candidates(text):
            clean = tok.lstrip("./")
            if clean.startswith("steering/"):
                clean = clean[len("steering/"):]
            base = clean.rsplit("/", 1)[-1]
            if is_artifact(base):
                continue
            if "/" in clean:
                # Deliberate pointers at the upstream plugin (e.g. the invariant tests this
                # power does not ship) are not flattening failures.
                if clean.startswith(UPSTREAM_POINTER):
                    continue
                # Only a *plugin-internal* path is a bug. Runtime artifact paths
                # ($MIGRATION_DIR/..., scenarios/..., globs) legitimately contain slashes.
                if PLUGIN_SEGMENT.search(clean):
                    unflattened[tok].add(path.name)
                    continue
                # NOT a `continue` for every slashed token — that was the original bug, and
                # it silently exempted every path-prefixed reference from the check below
                # (`$PLUGIN_ROOT/scripts/foo.py`, `<somedir>/bar.py`). A flat power resolves
                # by basename, so fall through and check the basename exists.
            if base not in present:
                dangling[clean].add(path.name)

    def report(title: str, data: dict[str, set[str]]) -> None:
        print(f"\n### {title} ({len(data)}) ###")
        for tok, files in sorted(data.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            shown = ", ".join(sorted(files)[:4])
            more = f" (+{len(files) - 4})" if len(files) > 4 else ""
            print(f"  {tok}\n      in: {shown}{more}")

    report("UNFLATTENED PATH REFERENCES", unflattened)
    report("DANGLING NAMES", dangling)
    report("PLUGIN LAYOUT TOKENS", layout)

    bad_power = check_power_md(present)
    print(f"\n### POWER.md BROKEN POINTERS ({len(bad_power)}) ###")
    for name in bad_power:
        print(f"  steering/{name}")

    print(f"\nsteering files: {len(present)}")
    return 1 if (unflattened or dangling or layout or bad_power) else 0


if __name__ == "__main__":
    raise SystemExit(main())
