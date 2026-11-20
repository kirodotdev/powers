"""Deterministic, registry-driven runtime-scoring engine for agent-advisor.

Pure: answers dict -> recommendation dict. No network, no AWS. Runtime
knowledge lives in the agent-advisor-runtime-*.json profiles beside this file.
"""
import json
import pathlib

RUNTIMES_DIR = pathlib.Path(__file__).parent

_REQUIRED_PROFILE_KEYS = ("id", "status", "affinities", "hard_constraints")

NEUTRAL_SCORE = 2

DIMENSIONS = [
    "session_duration", "traffic_pattern", "platform_fit", "session_state",
    "ops_preference", "isolation", "memory_needs", "multi_agent", "framework",
    "existing_cluster", "multi_cloud", "idle_resume", "compute_tier",
    "launch_concurrency",
]

# Legal answer values per scoring dimension (the closed set the engine reasons about).
LEGAL_VALUES = {
    "session_duration": ["under_15min", "15min_to_8hr", "over_8hr", "unknown"],
    "traffic_pattern": ["bursty", "steady", "idle", "unknown"],
    "platform_fit": ["ecs", "eks", "lambda", "none", "unknown"],
    "session_state": ["stateless", "stateful", "hitl", "unknown"],
    "ops_preference": ["minimal", "moderate", "full_control", "unknown"],
    "isolation": ["required", "nice_to_have", "not_needed", "unknown"],
    "memory_needs": ["cross_session", "session_only", "none", "unknown"],
    "multi_agent": ["yes", "no", "unknown"],
    "framework": ["strands", "langgraph", "crewai", "custom", "none", "unknown"],
    "existing_cluster": ["eks", "ecs", "none", "unknown"],
    "multi_cloud": ["yes", "no", "unknown"],
    "idle_resume": ["process_level", "filesystem", "none", "unknown"],
    "compute_tier": ["light", "heavy_non_gpu", "gpu", "unknown"],
    "launch_concurrency": ["high", "moderate", "low", "unknown"],
}

DEFAULTS = {
    **{dim: "unknown" for dim in DIMENSIONS},
    "compliance": ["none"],
    "model_priority": "unknown",
    "model_features": "unknown",
    "current_model": "unknown",
    "region": "unknown",
}


def load_profiles(runtimes_dir=RUNTIMES_DIR, statuses=frozenset({"ga"})):
    """Load runtime profiles whose status is in `statuses`, sorted by id."""
    profiles = []
    for path in sorted(pathlib.Path(runtimes_dir).glob("agent-advisor-runtime-*.json")):
        try:
            profile = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON ({exc})") from exc
        missing = [k for k in _REQUIRED_PROFILE_KEYS if k not in profile]
        if missing:
            raise ValueError(f"{path}: missing required keys {missing}")
        if profile["status"] in statuses:
            profiles.append(profile)
    return sorted(profiles, key=lambda p: p["id"])


def _apply_hard_constraints(answers, profiles):
    eliminated = {}
    compliance = answers.get("compliance", ["none"])
    for profile in profiles:
        for constraint in profile.get("hard_constraints", []):
            field, trigger = constraint["field"], constraint["value"]
            if field == "compliance":
                matched = trigger in compliance
            else:
                matched = answers.get(field) == trigger
            if matched:
                eliminated[profile["id"]] = constraint["reason"]
                break
    return eliminated


def _compute_scores(answers, profiles, eliminated):
    scores = {}
    for profile in profiles:
        if profile["id"] in eliminated:
            continue
        affinities = profile.get("affinities", {})
        total = 0
        for dim in DIMENSIONS:
            value = answers.get(dim, "unknown")
            total += affinities.get(dim, {}).get(value, NEUTRAL_SCORE)
        scores[profile["id"]] = total
    return scores


TIE_THRESHOLD = 2


def _determine_verdict(scores, eliminated):
    active = {r: s for r, s in scores.items() if r not in eliminated}
    if not active:
        return "no_viable_runtime", []
    max_score = max(active.values())
    top = sorted(r for r, s in active.items() if s >= max_score - TIE_THRESHOLD)
    if len(top) > 1:
        return "co_recommend", top
    return top[0], []


def _select_deployment_model(answers, verdict, profiles):
    profile = next((p for p in profiles if p["id"] == verdict), None)
    if profile is None:
        return None
    models = profile.get("deployment_models", [])
    if "harness" not in models or "framework_on_runtime" not in models:
        return None
    # Explicit user preference (Pass 2) overrides the inference below.
    pref = answers.get("deployment_preference", "unknown")
    if pref == "harness":
        return "harness"
    if pref == "framework":
        return "framework_on_runtime"
    # Inference (pref is "either" / "unknown"): multi-agent or a code framework → framework.
    if answers.get("multi_agent") == "yes":
        return "framework_on_runtime"
    if answers.get("framework") in ("langgraph", "crewai", "custom"):
        return "framework_on_runtime"
    return "harness"


AGENTCORE_ALWAYS_SERVICES = ["identity", "observability", "evaluations", "optimization"]


def _select_agentcore_services(answers):
    services = list(AGENTCORE_ALWAYS_SERVICES)

    def add(name):
        if name not in services:
            services.append(name)

    if answers.get("session_state") in ("hitl", "stateful"):
        add("memory")
    if answers.get("memory_needs") == "cross_session":
        add("memory")
    if answers.get("isolation") == "required":
        add("policy")
    if answers.get("multi_agent") == "yes":
        add("gateway")
    return services


# Q16 priority baseline. Model choice is independent of runtime scoring.
_MODEL_PRIORITY = {
    "quality": ("claude_sonnet_4_6", "Best quality for agentic workloads"),
    "balanced": ("claude_sonnet_4_6", "Balanced quality, speed, and cost"),
    "speed": ("claude_haiku_4_5", "Fastest response time"),
    "cost": ("claude_haiku_4_5", "Lowest cost per token"),
    "unknown": ("claude_sonnet_4_6", "Default for agentic workloads"),
}

# Q17 specialized-feature HARD override (beats priority). Coarse family mapping
# only — no pricing. Active models only, per migration-to-aws ai-model-lifecycle.md
# (the drift test in awslabs/startups:migrate/plugins/migration-to-aws/skills/agent-advisor/scripts/test_scoring.py locks this
# against the source lifecycle file).
# Each value: (model, reasoning, alternates).
_FEATURE_OVERRIDE = {
    "tool_use": ("claude_sonnet_4_6", "Best-in-class tool use on Bedrock", []),
    "long_context": (
        "llama_4_scout",
        "Ultra-long context (10M native window); Claude Sonnet 4.6 for shorter long-context",
        ["claude_sonnet_4_6"]),
    "extended_thinking": (
        "claude_sonnet_4_6_thinking", "Extended thinking for deep reasoning", []),
    "rag": (
        "claude_sonnet_4_6",
        "Strong retrieval + reasoning; pair with Bedrock Knowledge Bases + Titan Embeddings",
        ["titan_embed_v2"]),
    "multimodal": (
        "claude_sonnet_4_6",
        "Vision understanding; add a Stability AI model if you also generate images",
        ["stability_image_core"]),
    "image_generation": (
        "stability_image_core",
        "Image generation (Stable Image Core for cost, Ultra for quality) — a separate "
        "capability, not a text-model swap; see the llm-to-bedrock skill for integration",
        ["stability_image_ultra"]),
    "speech": (
        "nova_2_sonic",
        "Speech-to-speech (Transcribe/Polly for one-directional STT/TTS) — a separate "
        "capability, not a text-model swap; see the llm-to-bedrock skill for integration",
        []),
    "embedding": (
        "titan_embed_v2",
        "Text embeddings (Titan Embeddings v2)", []),
}

# Coarse source->family mapping for migrate (baseline only; feature override wins).
_MIGRATE_FAMILY = {
    "gpt4": "claude_sonnet_4_6", "gpt4o": "claude_sonnet_4_6",
    "gemini_flash": "nova_lite", "gemini_pro": "claude_sonnet_4_6",
    "claude": "claude_sonnet_4_6", "other": "claude_sonnet_4_6",
}

_PRICING_NOTE = ("Coarse family mapping only — see migration-to-aws for detailed "
                 "model pricing and TCO comparison.")


def _select_model(answers):
    priority = answers.get("model_priority", "unknown")
    feature = answers.get("model_features", "unknown")

    # Priority baseline.
    model, reasoning = _MODEL_PRIORITY.get(priority, _MODEL_PRIORITY["unknown"])
    rec = {"model": model, "reasoning": reasoning, "alternates": []}

    # Q17 feature HARD override (beats priority and, later, migrate family).
    override = _FEATURE_OVERRIDE.get(feature) if feature not in ("none", "unknown") else None
    if override:
        rec["model"], rec["reasoning"], alternates = override
        rec["alternates"] = list(alternates)
        # Cost/speed conflict advisory: the specialized model may not be cheapest/fastest.
        if priority in ("cost", "speed"):
            rec["reasoning"] += (
                f" (Feature override applied over your '{priority}' priority — this "
                "specialized model may not be the lowest-cost/fastest option; see pricing "
                "downstream.)")

    # Migrate: record source, and only fall to family mapping when no feature override.
    if answers.get("_entry_point") == "migrate":
        current = answers.get("current_model", "unknown")
        if current in _MIGRATE_FAMILY:
            rec["migration_from"] = current
            if not override:
                rec["model"] = _MIGRATE_FAMILY[current]
            rec["pricing_note"] = _PRICING_NOTE

    if not rec["alternates"]:
        del rec["alternates"]
    return rec


def _collect_assumptions(raw_answers):
    out = []
    for dim in DIMENSIONS:
        if raw_answers.get(dim, "unknown") == "unknown":
            out.append(f"{dim} defaulted to unknown")
    return out


def _collect_warnings(answers, verdict, co_recommend=None):
    warnings = []
    microvms_is_winner = (
        verdict == "lambda_microvms"
        or (verdict == "co_recommend" and "lambda_microvms" in (co_recommend or []))
    )
    if microvms_is_winner and answers.get("launch_concurrency") == "high":
        warnings.append(
            "Lambda MicroVMs RunMicrovm is capped at 5 TPS and is not "
            "adjustable; high-concurrency launch storms will queue. If launch "
            "rate matters at scale, reconsider AgentCore Runtime (25 TPS, "
            "adjustable).")
    return warnings


def score(input_data, profiles=None):
    if profiles is None:
        profiles = load_profiles()
    entry_point = input_data.get("entry_point", "build_scratch")
    raw_answers = input_data.get("answers", {})

    answers = dict(DEFAULTS)
    answers.update({k: v for k, v in raw_answers.items() if v is not None})
    answers["_entry_point"] = entry_point

    eliminated = _apply_hard_constraints(answers, profiles)
    scores = _compute_scores(answers, profiles, eliminated)
    verdict, co_recommend = _determine_verdict(scores, eliminated)

    deployment_model = None
    if verdict not in ("no_viable_runtime", "co_recommend"):
        deployment_model = _select_deployment_model(answers, verdict, profiles)
    elif verdict == "co_recommend":
        for rid in co_recommend:
            dm = _select_deployment_model(answers, rid, profiles)
            if dm is not None:
                deployment_model = dm
                break

    result = {
        "verdict": verdict,
        "scores": scores,
        "eliminated": eliminated,
        "deployment_model": deployment_model,
        "agentcore_services": _select_agentcore_services(answers),
        "model_recommendation": _select_model(answers),
        "assumptions_used": _collect_assumptions(raw_answers),
        "warnings": _collect_warnings(answers, verdict, co_recommend),
    }
    if verdict == "co_recommend":
        result["co_recommend"] = co_recommend
    if verdict == "no_viable_runtime":
        result["blocking_constraints"] = [
            f"{r}: {reason}" for r, reason in sorted(eliminated.items())]
    return result


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="agent-advisor runtime scoring")
    parser.add_argument("answers", type=pathlib.Path, help="path to answers.json")
    args = parser.parse_args(argv)
    input_data = json.loads(args.answers.read_text())
    result = score(input_data)
    out_path = args.answers.parent / "scoring-result.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"RESULT=ok VERDICT={result['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
