"""The house's transports: one long-lived model process per agent, speaking newline JSON on stdin and stdout.

Ported from the old desk's house (research/text-desk-lab/notation/house.py, Resident.start/send/turns_ended) with only
the provider-agnostic parts: the Claude `-p` stream-json process, compaction at the house's compact_at (400k), the
Codex transport (research/codex-residents/codex_resident.py), and the charter as the system prompt with a compact hook
that reads it again. What is new: the agent acts through MCP (kernel-lab/mcp/agora_mcp.py, see/do/lines) with its own
bearer session, never through `>` lines in its text.

Every child's stream is reduced to these events, put on the agent's queue:
    {"e": "init", "session": id}        {"e": "text", "text": ...}        {"e": "tool", "name": ..., "input": {...}}
    {"e": "compacted"}                  {"e": "result", "ok": bool, "detail": ...}     {"e": "exit", "code": n}
    {"e": "toolresult", "refused": n}   (a tool's answer: how many of its lines were refused)
Thinking blocks are never reduced to anything: they stay in the transcript.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
REPO = LAB.parents[1]
MCP = LAB / "mcp" / "agora_mcp.py"
CODEX = LAB.parent / "codex-residents" / "codex_resident.py"
PY = REPO / ".venv" / "Scripts" / "python.exe"
NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
TOOLS = ("see", "do", "lines")


def find_claude():
    """-> the newest claude here: $HOUSE_CLAUDE, the one on PATH, or one the desktop app keeps (house.py's rule: PATH
    can hold an old install that newer models refuse)."""
    if os.environ.get("HOUSE_CLAUDE"):
        return os.environ["HOUSE_CLAUDE"]
    found = []
    kept = os.path.expandvars(r"%APPDATA%\Claude\claude-code")
    for path in [shutil.which("claude")] + sorted(glob.glob(kept + r"\*\claude.exe") + glob.glob(kept + r"\*\*\claude.exe")):
        if not path:
            continue
        try:
            out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=30,
                                 creationflags=NO_WINDOW).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        m = re.match(r"\s*(\d+)\.(\d+)\.(\d+)", out)
        if m:
            found.append((tuple(int(x) for x in m.groups()), path))
    return max(found)[1] if found else shutil.which("claude")


def clean_env(compact_at="400k", fake=None):
    """The child inherits nothing of a launcher's Claude session (house.py clean_env), and compacts at compact_at."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("CLAUDE")}
    # 28 Oct: a review's hidden desktop tests started a kernel with the live keeper's AGORA_KEEPER, joined the live
    # keeper and knocked Alex's kernel off it. Nothing the House starts may reach the live keeper.
    env.pop("AGORA_KEEPER", None)
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    if str(compact_at).lower() != "off":
        env["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = str(compact_at)
    if fake:
        env["ANTHROPIC_BASE_URL"] = fake
        env["ANTHROPIC_API_KEY"] = "fake-key-for-a-scripted-model"
    return env


def mcp_config(url, token_file, out):
    """The agent's tools: the door adapter with its own session, written to `out` beside the house's state (never on
    a command line, where other programs could read the token). -> the file's path."""
    token = Path(token_file).read_text(encoding="utf-8").strip()
    cfg = {"mcpServers": {"agora": {"command": str(PY), "args": [str(MCP)],
                                    "env": {"AGORA_URL": url, "AGORA_BEARER_TOKEN": token}}}}
    Path(out).write_text(json.dumps(cfg), encoding="utf-8")
    return str(out)


class Child:
    """One model process. `events` gets the reduced events above; `send(text)` starts a turn."""

    def __init__(self, cmd, cwd, env, events, log, stderr=None):
        self.events, self.log = events, log
        self.codex_streamed = False
        self.proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=open(stderr or Path(cwd) / "stderr.log", "a", encoding="utf-8"),
                                     text=True, encoding="utf-8", errors="replace", bufsize=1,
                                     creationflags=NO_WINDOW)
        threading.Thread(target=self._read, daemon=True, name="agent-child").start()

    def alive(self):
        return self.proc.poll() is None

    def send(self, text):
        msg = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}
        try:
            self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
            return True
        except (OSError, ValueError, AttributeError) as e:
            self.log("unsent", f"{type(e).__name__}: {e}")
            return False

    def _read(self):
        for raw in self.proc.stdout:
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self.log("event", ev)
            if ev.get("type") == "codex_event" and ev.get("method") == "item/completed" and (ev.get("data") or {}).get("item", {}).get("type") == "agentMessage":
                self.codex_streamed = True
            if ev.get("type") == "assistant" and self.codex_streamed:
                continue  # the adapter's final aggregate duplicates already delivered public text
            if ev.get("type") == "result":
                self.codex_streamed = False
            for out in reduce(ev):
                self.events.put(out)
        self.events.put({"e": "exit", "code": self.proc.wait()})

    def stop(self):
        if self.alive():
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=10)
            except Exception:                    # noqa: BLE001
                self.proc.kill()


def reduce(ev):
    """A stream-json event (Claude's, or codex_resident's, which speaks the same shape) -> house events."""
    t = ev.get("type")
    if t == "system" and ev.get("subtype") == "turn_started":
        return [{"e": "turn_started", "turn": ev.get("turn_id")}]
    if t == "codex_event":
        item = (ev.get("data") or {}).get("item") or {}
        if ev.get("method") == "item/completed" and item.get("type") == "agentMessage":
            return [{"e": "text", "text": item.get("text", "")}]
        if ev.get("method") == "item/started" and item.get("type") in (
                "commandExecution", "mcpToolCall", "dynamicToolCall", "fileChange", "webSearch"):
            return [{"e": "tool", "name": str(item.get("tool") or item.get("type")), "input": {}}]
        return []  # reasoning and raw tool arguments/results never become public activity
    if t == "system" and ev.get("subtype") == "init" and ev.get("session_id"):
        return [{"e": "init", "session": ev["session_id"]}]
    if t == "system" and ev.get("subtype") == "compact_boundary":
        return [{"e": "compacted"}]
    if t == "assistant":
        out = []
        for c in ev.get("message", {}).get("content", []) or []:
            if c.get("type") == "text" and c.get("text", "").strip():
                out.append({"e": "text", "text": c["text"]})
            elif c.get("type") == "tool_use":
                out.append({"e": "tool", "name": c.get("name", ""), "input": c.get("input") or {}})
        return out
    if t == "user":
        out = []
        for c in ev.get("message", {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "tool_result":
                body = c.get("content")
                text = body if isinstance(body, str) else "".join(x.get("text", "") for x in body or [] if isinstance(x, dict))
                try:
                    r = json.loads(text)
                    refused = int(r.get("refused", 0 if r.get("ok") else 1)) if isinstance(r, dict) else 0
                except (ValueError, TypeError):
                    refused = 1 if c.get("is_error") else 0
                out.append({"e": "toolresult", "refused": refused})
        return out
    if t == "result":
        return [{"e": "result", "ok": not ev.get("is_error"), "detail": str(ev.get("result") or ev.get("subtype") or "")[:500]}]
    return []


def claude_cmd(claude, model, effort, system_prompt, mcp, hook, session=None):
    cmd = [claude, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
           "--system-prompt", system_prompt, "--model", model,
           "--tools", "", "--mcp-config", mcp, "--strict-mcp-config",
           "--allowedTools", ",".join(f"mcp__agora__{t}" for t in TOOLS),
           "--setting-sources", "", "--settings", json.dumps(hook)]
    if effort:
        cmd += ["--effort", effort]
    if session:
        cmd += ["--resume", session]
    return cmd


def codex_cmd(model, effort, charter_file, mcp, session=None, context=None):
    """codex_resident.py with the door adapter as its one MCP server (--mcp-config <file>). Unproven with a live model."""
    cmd = [str(PY), str(CODEX), "--model", model, "--reasoning", effort or "medium",
           "--charter-file", str(charter_file), "--mcp-config", mcp]
    if session:
        cmd += ["--resume", session]
    if context:
        cmd += ["--kernel-context", json.dumps(context)]
    return cmd


def compact_hook(url, token_file, charter, agent=None):
    """Claude's SessionStart hook after a compaction: read the charter again through the door (charter_hook.py)."""
    command = f'"{PY}" "{HERE / "charter_hook.py"}" --url {url} --token-file "{token_file}" --charter {charter}'
    if agent:
        command += f" --agent {agent}"
    return {"hooks": {"SessionStart": [{"matcher": "compact", "hooks": [{"type": "command", "command": command}]}]}}
