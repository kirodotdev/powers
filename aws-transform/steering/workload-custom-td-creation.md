# Interactive Transformation Definition Creation (In-Chat)

When the user wants a new custom transformation definition and nothing in the
catalog matches, drive the creation **inside this chat**. Do NOT send the user
to a separate terminal for `atx -t` unless the in-chat helper fails — that is
the fallback only.

The in-chat path uses the AWS Transform CLI's `atx json` NDJSON protocol,
wrapped in a small local Python helper. The Power calls the helper once per
user turn and the helper blocks until ATX is ready for the next answer. No
polling, no raw protocol output in chat.

## When to Use

- The user explicitly asks to create a new transformation definition, OR
- `atx custom def list --json` turned up no transformation definition that
  covers the user's goal

Before starting, confirm with the user in one short question (unless they
already explicitly asked to create one):

> "I didn't find a transformation definition that covers [goal]. Want me to
> build one with you?"

Only proceed on confirmation.

## Prerequisites

The helper requires `python3` and calls `atx json`, which in turn calls the
`transform-custom:ConverseStream` API. A read-only identity hits an
`AccessDeniedException` — the helper returns exit code 3 with the message on
stdout. If the caller's identity is read-only or Python 3 is missing, fall
back to `atx -t`.

Check both once per session before starting:

```bash
python3 --version && atx json --help > /dev/null 2>&1 && echo HELPER_READY || echo HELPER_UNAVAILABLE
```

If this prints `HELPER_UNAVAILABLE`, skip the in-chat path and use the
`atx -t` fallback (see the bottom of this file).

## Setup: Materialize the Helper (Once Per Session)

The helper script is embedded in this file as the fenced Python block below.
The target location is outside the workspace at
`~/.aws/atx/custom/atx-agent-session/atx-json-session.py`, but your native
file-write tool is typically workspace-scoped — writing directly there will
fail. Do NOT try the outside-workspace path first and then fall back; go
straight to the workspace-first install below.

Installation steps:

1. Read the fenced Python block in the "Helper Script" section below.
2. Write its exact contents to `./.atx-json-session.py` at the workspace
   root using your native file-write tool. Byte-for-byte — no reformatting,
   no line-length changes, no substitutions. (Shells mangle large Python
   blobs through heredocs — do not use `cat <<EOF`.)
3. Move it into place and mark executable:

   ```bash
   mkdir -p ~/.aws/atx/custom/atx-agent-session
   cp ./.atx-json-session.py ~/.aws/atx/custom/atx-agent-session/atx-json-session.py
   chmod +x ~/.aws/atx/custom/atx-agent-session/atx-json-session.py
   rm ./.atx-json-session.py
   ```

4. Sanity-check: `python3 -m py_compile ~/.aws/atx/custom/atx-agent-session/atx-json-session.py`.
   If this exits non-zero, the file was corrupted — re-read the block and
   re-write it.

The install is idempotent: check if the target file already exists and
passes `py_compile` first, only re-install if missing or broken.

## Helper Script

```python
#!/usr/bin/env python3
"""Blocking wrapper around `atx json` NDJSON stdio.

Subcommands:
  start "<message>"  Start session; block until ATX waits for input; print text; exit 0.
  send  "<message>"  Send reply; block until ATX waits for input; print text; exit 0.
  stop               Cancel session and clean up. Print nothing.

Exit codes: 0 input_required, 2 complete, 3 error, 4 timeout.
Stdout is clean assistant text only. On error, stdout carries the error message.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / ".aws/atx/custom/atx-agent-session"
BASE.mkdir(parents=True, exist_ok=True)
STATE = BASE / "atx-json.state"
OUT = BASE / "atx-json.out"
ERR = BASE / "atx-json.err"
PID = BASE / "atx-json.pid"
IN_FIFO = BASE / "atx-json.in"
TIMEOUT = 300
SPINNER_SUBSTRINGS = ("Thinking",)


def _spawn():
    if IN_FIFO.exists():
        IN_FIFO.unlink()
    os.mkfifo(str(IN_FIFO))
    fd = os.open(str(IN_FIFO), os.O_RDWR)
    OUT.write_text("")
    ERR.write_text("")
    out_fh = open(OUT, "wb")
    err_fh = open(ERR, "wb")
    proc = subprocess.Popen(
        ["atx", "json"],
        stdin=fd,
        stdout=out_fh,
        stderr=err_fh,
        start_new_session=True,
    )
    PID.write_text(str(proc.pid))
    STATE.write_text("0")
    return fd


def _send(obj):
    fd = os.open(str(IN_FIFO), os.O_WRONLY | os.O_NONBLOCK)
    try:
        os.write(fd, (json.dumps(obj) + "\n").encode())
    finally:
        os.close(fd)


def _err_tail():
    try:
        return ERR.read_text(errors="replace").strip()
    except Exception:
        return ""


def _extract_err(text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "Error occurred:" in line or "Exception" in line:
            return line.split("Error occurred:", 1)[-1].strip() or line
    return text.splitlines()[0] if text else "unknown error"


def _read_until_input():
    offset = int(STATE.read_text() or "0")
    chunks = []
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        if not OUT.exists():
            time.sleep(0.05)
            continue
        with open(OUT, "rb") as f:
            f.seek(offset)
            data = f.read()
        if not data:
            time.sleep(0.1)
            continue
        # Only advance through complete lines. Partial trailing fragments are
        # left in the file for the next read — avoids losing a chunk when the
        # producer's write is split mid-line.
        if not data.endswith(b"\n"):
            last_nl = data.rfind(b"\n")
            if last_nl == -1:
                time.sleep(0.1)
                continue
            data = data[:last_nl + 1]
            offset += last_nl + 1
        else:
            offset += len(data)
        STATE.write_text(str(offset))
        for raw in data.decode(errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            t = msg.get("type")
            if t == "text_delta":
                content = msg.get("content", "")
                if any(s in content for s in SPINNER_SUBSTRINGS):
                    continue
                chunks.append(content)
            elif t == "input_required":
                text = "".join(chunks).strip()
                if not text:
                    err = _err_tail()
                    if err:
                        return "error", _extract_err(err)
                return "input", text
            elif t == "complete":
                return "complete", "".join(chunks).strip()
            elif t == "error":
                return "error", msg.get("message", "unknown error")
        time.sleep(0.1)
    return "timeout", "".join(chunks).strip()


def _cleanup():
    try:
        pid = int(PID.read_text())
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except Exception:
        pass
    for p in (IN_FIFO, PID, OUT, ERR, STATE):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


RC = {"input": 0, "complete": 2, "error": 3, "timeout": 4}


def main():
    if len(sys.argv) < 2:
        print("usage: atx-json-session.py {start|send|stop} [message]", file=sys.stderr)
        sys.exit(3)
    verb = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    try:
        if verb == "start":
            _spawn()
            _send({"type": "start_session", "message": message})
            status, text = _read_until_input()
            print(text)
            sys.exit(RC[status])
        if verb == "send":
            _send({"type": "send_message", "message": message})
            status, text = _read_until_input()
            print(text)
            sys.exit(RC[status])
        if verb == "stop":
            try:
                _send({"type": "cancel"})
            except Exception:
                pass
            _cleanup()
            sys.exit(0)
        print("unknown verb: " + verb, file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(str(e), file=sys.stderr)
        _cleanup()
        sys.exit(3)


if __name__ == "__main__":
    main()
```

## Interaction Loop

Every call is a single shell invocation that blocks until ATX is ready for the
next user message. Do **not** poll. Do **not** wrap in loops. One call per
user turn.

### Turn 1 — Start the session

```bash
python3 ~/.aws/atx/custom/atx-agent-session/atx-json-session.py start "Create a TD to migrate AcmeCorp DataBridge v1 integrations to AcmeCorp DataBridge v3"
```

Build the initial message from what the user told you — their migration goal
in one or two sentences. The helper prints ATX's clean text reply and exits 0
when ATX is waiting for input.

Relay that text to the user in your own first-person voice. Don't say "ATX
asks…" or "the agent wants to know…" — ask the question yourself.

### Turns 2…N — Send the user's reply

```bash
python3 ~/.aws/atx/custom/atx-agent-session/atx-json-session.py send "Java backend, Maven build, package rename from com.acme.v1 to com.acme.v3"
```

Wait for the helper to exit, relay stdout to the user as your own voice, wait
for the user's next answer, repeat.

### Final turn — Close out

When the user signals they're done (TD published, saved as draft, or "stop"):

```bash
python3 ~/.aws/atx/custom/atx-agent-session/atx-json-session.py stop
```

Then re-run `atx custom def list --json` so the newly published TD is picked
up in the catalog, and return to the normal workflow.

## Exit Codes

| Code | Meaning | What to do |
|------|---------|-----------|
| `0` | ATX is waiting for user input | Relay stdout, ask user what's next |
| `2` | Session completed | Relay stdout, run `stop`, refresh TD list |
| `3` | Helper or backend error | Surface stdout (contains the error message — often `AccessDeniedException`), run `stop`, offer `atx -t` fallback |
| `4` | Timeout (no ATX output for 5 min) | Run `stop`, offer to retry or fall back |

## Non-Negotiable UX Rules

- **Single helper call per user turn.** The helper is already blocking; never
  "poll" it. One `start`, one `send` per user reply, one `stop` at the end.
- **Clean text only — never surface protocol output.** If the helper's stdout
  somehow contains JSON braces, raw tool names, `text_delta`, `input_required`,
  `start_session`, `send_message`, or `cancel`, strip or paraphrase before
  showing the user. Those strings must never appear in chat.
- **First-person framing.** Ask ATX's clarifying questions in your own voice.
  Don't say "the agent is asking" or "ATX wants to know."
- **No narration of mechanics.** Don't say "I'll start the interactive session"
  or "calling the helper now." Just ask the user the next question.
- **Stay in the chat.** Don't tell the user to open a separate terminal, run
  `atx -t` themselves, or switch windows. The whole point is in-chat.
- **Re-discover after publish.** The moment `stop` returns, re-run
  `atx custom def list --json` so the newly published TD is reflected.

## Fallback: `atx -t`

Fall back only when:

- The helper returned exit code `3` (error — surface the error text to the user first)
- The helper returned exit code `4` (timeout)
- `python3` is not available on the user's machine
- `atx json` is missing (older CLI versions)

In any of those cases:

> "I couldn't drive this from the chat. Open a terminal and run `atx -t` —
> describe the transformation you want and ATX will walk you through it. Come
> back here once it's published and I'll pick it up automatically."

Never use `atx -t` as the first choice.

## MANDATORY: Cleanup

The helper's `stop` subcommand already removes the FIFO and runtime state
files (`atx-json.in`, `atx-json.out`, `atx-json.err`, `atx-json.pid`,
`atx-json.state`) on a normal session end. Belt-and-suspenders cleanup in
case the helper was killed mid-session, an error bailed out before `stop`,
or the shell was interrupted — run **before starting** and **after completing**
each TD creation session:

```bash
[ -d ~/.aws/atx/custom/atx-agent-session ] && find ~/.aws/atx/custom/atx-agent-session -maxdepth 1 \( -name "atx-json.in" -o -name "atx-json.out" -o -name "atx-json.err" -o -name "atx-json.pid" -o -name "atx-json.state" \) -delete 2>/dev/null || true
```

Keep `atx-json-session.py` in place — the helper script itself is reused
across sessions. Only the per-session state files are removed.
