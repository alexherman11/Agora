"""Optional installed-runtime probe. Loopback fake inference, empty private home,
no tools, no live account. Not part of health; requires an explicit runtime path.

Reports request metadata and compact boundaries, never prompts or environment.
Fake usage counts exercise compaction without building a huge real conversation.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import claude_worker_runtime


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runtime")
    ap.add_argument("--usage", type=int, default=600001)
    ap.add_argument("--response-chars", type=int, default=0,
                    help="Synthetic loopback reply size; no paid model or private content")
    ap.add_argument("--enforce-fake-window", action="store_true",
                    help="Fake provider rejects turn two above 600k; exercises reactive compact transport")
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "desktop"))
    import agora_tmp
    root = Path(agora_tmp.directory("claude-probe-"))
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if "count_tokens" in self.path:
                payload = json.dumps({"input_tokens": 100}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)
                return
            calls.append({"model": body.get("model"), "effort": body.get("output_config", {}).get("effort"),
                          "tools": len(body.get("tools") or [])})
            if args.enforce_fake_window and args.usage > 600000 and len(calls) == 2:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"type": "error", "error": {"type": "invalid_request_error",
                    "message": f"prompt is too long: {args.usage} tokens > 600000 maximum"}}).encode())
                return
            # Only the first reply claims a large context; a compact summary is small.
            usage = args.usage if len(calls) == 1 else 100
            msg = {"id": "fixture", "type": "message", "role": "assistant", "model": body.get("model"),
                   "content": [], "stop_reason": None, "stop_sequence": None,
                   "usage": {"input_tokens": usage, "output_tokens": 1}}
            text = "Fixture response." if len(calls) != 1 else ("x " * (args.response_chars // 2) or "Fixture response.")
            events = [
                ("message_start", {"type": "message_start", "message": msg}),
                ("content_block_start", {"type": "content_block_start", "index": 0,
                                         "content_block": {"type": "text", "text": ""}}),
                ("content_block_delta", {"type": "content_block_delta", "index": 0,
                                         "delta": {"type": "text_delta", "text": text}}),
                ("content_block_stop", {"type": "content_block_stop", "index": 0}),
                ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn",
                                      "stop_sequence": None}, "usage": {"output_tokens": 10}}),
                ("message_stop", {"type": "message_stop"}),
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                for name, data in events:
                    self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = {k: v for k, v in os.environ.items() if k.upper() in
           ("SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "COMSPEC", "PROCESSOR_ARCHITECTURE")}
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "CLAUDE_CONFIG_DIR",
                "TEMP", "TMP", "TMPDIR", "AGORA_TMP"):
        env[key] = str(root)
    env.update(ANTHROPIC_BASE_URL=f"http://127.0.0.1:{server.server_port}",
               ANTHROPIC_API_KEY="fixture-not-a-credential", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               DISABLE_TELEMETRY="1", DISABLE_ERROR_REPORTING="1", CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")
    cmd = [args.runtime, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
           "--model", "claude-opus-5-5", "--tools", "", "--strict-mcp-config",
           "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "",
           "--system-prompt", "Local fixture only.", "--no-session-persistence",
           "--debug-file", str(root / "debug.txt"),
           *claude_worker_runtime.arguments({})]
    out = queue.Queue()
    proc = None
    events = []
    try:
        with open(root / "stderr.txt", "w", encoding="utf-8") as err:
            proc = subprocess.Popen(cmd, cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=err, text=True, encoding="utf-8")
            def read():
                for line in proc.stdout:
                    try:
                        out.put(json.loads(line))
                    except ValueError:
                        pass
                out.put(None)
            threading.Thread(target=read, daemon=True).start()
            def send(text):
                proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
                proc.stdin.flush()
            send("Fixture first turn.")
            results = 0
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline and results < 2:
                try:
                    event = out.get(timeout=1)
                except queue.Empty:
                    continue
                if event is None:
                    break
                events.append(event)
                if event.get("type") == "result":
                    results += 1
                    if results == 1:
                        send("Fixture next turn.")
            compact = [e for e in events if e.get("subtype") == "compact_boundary"]
            states = [e for e in events if e.get("type") in ("autocompact_state", "context_usage")]
            notices = [e for e in events if e.get("type") == "system" and e.get("subtype") == "informational"]
            debug = (root / "debug.txt").read_text(encoding="utf-8", errors="replace")
            print(json.dumps({"fake_usage": args.usage, "results": results, "requests": calls,
                              "fake_provider_window": 600000 if args.enforce_fake_window else None,
                              "compact_boundaries": compact, "runtime_context": states,
                              "runtime_notices": notices,
                              "compact_diagnostics": [line for line in debug.splitlines() if "autocompact:" in line],
                              "event_types": sorted({(e.get("type", ""), e.get("subtype", "")) for e in events}),
                              "exit_code": proc.poll(),
                              "fixture": str(root)}, indent=2))
            boundary_ok = (not args.enforce_fake_window or bool(compact) == (args.usage > 600000))
            return 0 if results == 2 and calls and boundary_ok and all(
                c["model"] == "claude-opus-5-5" and c["effort"] == "medium" and c["tools"] == 0 for c in calls) else 1
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()    # only this probe's own process, no host actions or real models
            proc.wait(timeout=10)
        server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
