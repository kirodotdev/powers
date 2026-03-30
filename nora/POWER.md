---
name: "nora"
displayName: "Nora — AI Work Intelligence"
description: "Your AI gets smarter every session. Nora captures sessions, learns patterns, injects context, and evolves steering — all locally."
keywords: ["nora", "kernora", "patterns", "context", "memory", "intelligence", "learning", "steering", "session", "decisions", "bugs", "anti-patterns", "knowledge", "recall", "history"]
author: "Kernora AI"
---

# Nora — AI Work Intelligence

Nora is your silent coding partner. She captures every session, extracts patterns, decisions, and anti-patterns, then feeds them back as context and steering. Your AI gets smarter every session.

100% local. Zero bytes leave your machine. BYOK (Bring Your Own Key).

## Onboarding

### Step 1: Check Prerequisites

Verify the following are installed:

- **Python 3.9+** — Run `python3 --version` to confirm
- **git** — Run `git --version` to confirm

If either is missing, halt setup and inform the user.

### Step 2: Install Nora Engine

Check if Nora is already installed by looking for `~/.kernora/app/daemon.py`.

If Nora is NOT installed, run:

```bash
git clone https://github.com/kernora-ai/nora.git /tmp/nora-install && bash /tmp/nora-install/install.sh && rm -rf /tmp/nora-install
```

This installs the engine to `~/.kernora/`, creates a virtual environment, initializes the database, starts the daemon and dashboard, and configures auto-start on login.

If Nora IS already installed, skip to Step 3.

### Step 3: Configure API Key (Optional)

Nora works out of the box without any API key. Session capture, pattern extraction (Phase 1), hooks, MCP tools, and steering files all run locally with zero LLM calls.

For deeper semantic analysis (Phase 2), Nora can optionally use an LLM. If the user wants to enable this, check if any of these environment variables are set:

- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `AWS_PROFILE` (for Bedrock)

If none are set, Nora still works — Phase 1 deterministic analysis extracts patterns, file changes, tool usage, and error signatures without any LLM. Phase 2 is a bonus, not a gate.

To use local Ollama instead of a cloud API: edit `~/.kernora/config.toml` and set `provider = "ollama"`.

Skip this step if you just want to get started.

### Step 4: Install Kiro Hooks

Copy `hooks.json` to `.kiro/hooks/` in the workspace. This registers all four hooks:

```json
{
  "hooks": {
    "agentSpawn": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.kiro/hooks/kiro_agent_spawn.py",
            "timeout": 5
          }
        ]
      }
    ],
    "stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.kiro/hooks/kiro_stop.py",
            "async": true
          }
        ]
      }
    ],
    "preToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.kiro/hooks/kiro_spec_shield.py",
            "timeout": 3
          }
        ]
      }
    ],
    "postToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.kiro/hooks/kiro_post_tool.py",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

The four hooks:

- **agentSpawn** — checks daemon health, verifies steering freshness, auto-starts daemon if down
- **stop** — captures session transcript, sends to Nora daemon for analysis (async)
- **preToolUse** — validates tool invocations against danger patterns and learned anti-patterns
- **postToolUse** — checks tool output against known error signatures from past sessions

### Step 5: Copy Hook Scripts

Download hook scripts to `~/.kiro/hooks/`:

```bash
mkdir -p ~/.kiro/hooks
for f in kiro_agent_spawn.py kiro_stop.py kiro_spec_shield.py kiro_post_tool.py steering_writer.py; do
  [ ! -f "$HOME/.kiro/hooks/$f" ] && curl -sfL "https://raw.githubusercontent.com/kernora-ai/kiro-claw/main/hooks/$f" -o "$HOME/.kiro/hooks/$f"
done
chmod +x ~/.kiro/hooks/*.py
```

### Step 6: Generate Initial Steering

Run the steering writer to generate initial steering files:

```bash
python3 ~/.kiro/hooks/steering_writer.py
```

This creates `~/.kiro/steering/nora-patterns.md`, `nora-decisions.md`, and `nora-antipatterns.md`. These are read by Kiro automatically on every prompt.

### Step 7: Verify Installation

Confirm Nora is running:

1. Check daemon: `ls ~/.kernora/daemon.sock` (should exist)
2. Check dashboard: `curl -sf http://localhost:2742` (should return HTML)
3. Check steering: `ls ~/.kiro/steering/nora-*.md` (should list 3 files)

If all three pass, Nora is ready. Tell the user: "Nora is installed. Your sessions will be captured and analyzed automatically. Steering files update after each session."

## Available MCP Server

### nora

**Connection:** Local stdio process at `~/.kernora/app/nora_mcp.py`

Nora's MCP server provides access to your session intelligence database. All data stays local in `~/.kernora/echo.db`.

**Tools (11):**

- **nora_search** — Full-text search across patterns, decisions, bugs, and insights from past sessions. Required: `query` (string).
- **nora_patterns** — List effective coding patterns, optionally filtered by project. Optional: `project` (string), `min_effectiveness` (number, 0-1).
- **nora_decisions** — List architectural decisions recorded across sessions. Optional: `project` (string).
- **nora_bugs** — List known bugs with severity, file path, and fix code. Optional: `status` (open/resolved/all), `severity` (critical/high/medium/low).
- **nora_stats** — Dashboard stats: session count, insights, patterns, decisions, open bugs, total tokens.
- **nora_session** — Get full details for a specific session by ID. Required: `session_id` (string).
- **nora_scope_validation** — Validate that planned execution scope is focused and safe before multi-file edits. Required: `intent` (string). Optional: `files_to_touch` (string array).
- **nora_skills** — Fetch distilled methodology from your team's highest-quality sessions.
- **nora_dashboard** — Full intelligence dashboard inline: KPIs, top patterns, recent decisions, open bugs, recent sessions, knowledge domains. Say "show dashboard" or "Nora status".
- **nora_analyze_pending** — Get next unanalyzed session with Phase 1 metadata + condensed transcript + analysis prompt. No arguments needed.
- **nora_store_analysis** — Store your analysis of a session (called after nora_analyze_pending). Required: `session_id` (string), `analysis` (object).

## When to Load Steering Files

Nora generates three global steering files that Kiro reads automatically. They don't need explicit loading — they're always active. However, these are the contexts where each is most valuable:

- Starting a new coding task → `nora-patterns.md` provides reusable patterns and playbooks
- Making architectural choices → `nora-decisions.md` provides past decisions and rationale
- About to modify code → `nora-antipatterns.md` warns about known mistakes and bugs

## How Nora Works

1. **You code normally.** Nora is silent during your session.
2. **Session ends.** The stop hook captures the transcript and spools it locally.
3. **Next session starts.** The agentSpawn hook detects pending sessions and nudges the agent.
4. **Agent analyzes (zero API key).** Kiro's built-in model reads Phase 1 metadata + condensed transcript via `nora_analyze_pending`, generates semantic analysis, and stores it via `nora_store_analysis`. No external API key needed.
5. **Knowledge accumulates.** Patterns, decisions, and bugs are stored in `~/.kernora/echo.db`.
6. **Steering evolves.** After each analysis, steering files regenerate with the latest intelligence.
7. **Every session is smarter.** Kiro reads the steering files. The MCP tools answer questions about past work.

**Optional:** If you have an API key (Anthropic, Gemini, etc.), the daemon can also analyze sessions in the background for deeper extraction. But the agent-as-analyzer path works with zero keys.

## Privacy

Nora runs 100% locally:

- Session transcripts stored in `~/.kernora/echo.db` on your machine
- Agent-as-analyzer uses Kiro's built-in model — no external API calls
- Optional deep analysis uses YOUR API key if configured
- Steering files live in `~/.kiro/steering/` on your machine
- Zero telemetry, zero cloud storage, zero data sharing

## Dashboard

Open http://localhost:2742 to see:

- Session history with analysis summaries
- Pattern library with effectiveness scores
- Architectural decision log
- Bug tracker with severity and fix code
- Knowledge Intelligence Quotient (KIQ) — your accumulated engineering judgment

## Configuration

Edit `~/.kernora/config.toml`:

```toml
[mode]
type = "byok"              # your key, your machine

[model]
provider = "anthropic"      # or "bedrock", "gemini", "ollama"

[analysis]
run_every_minutes = 60      # how often to analyze new sessions

[dashboard]
port = 2742                 # dashboard port
```

## Troubleshooting

### Daemon not running
```bash
~/.kernora/venv/bin/python3 ~/.kernora/app/daemon.py &
```

### No steering files generated
Run manually: `python3 ~/.kiro/hooks/steering_writer.py`
If echo.db is empty, complete a few coding sessions first.

### MCP server not connecting
Verify the server starts: `~/.kernora/venv/bin/python3 ~/.kernora/app/nora_mcp.py`
Check for missing dependencies: `~/.kernora/venv/bin/pip install mcp`

## Resources

- [GitHub: kernora-ai/nora](https://github.com/kernora-ai/nora) — Engine source
- [GitHub: kernora-ai/kiro-claw](https://github.com/kernora-ai/kiro-claw) — Kiro hooks source
- [GitHub: kernora-ai/claude-claw](https://github.com/kernora-ai/claude-claw) — Claude Code hooks
- [Dashboard](http://localhost:2742) — Local web UI
- [kernora.ai](https://kernora.ai) — Documentation and guides
