"""fake_model: a scripted stand-in for the Messages API, to test the house's loop without calling a model.

    python fake_model.py [port] [script.json]

Point `claude -p` at it with ANTHROPIC_BASE_URL=http://127.0.0.1:<port>. Every POST to /v1/messages answers with
the next scripted reply for the resident whose door it came through, streamed in the API's event format. A reply is
chosen by the first rule whose `when` text appears in the latest user message (rules without `when` match anything);
`reply` may contain {n} for a per-process turn count. A rule with `status` (say 400) answers with that API error
instead, its `reply` as the message; `times: N` lets a rule match only N times. Requests are recorded, bodies only,
in fake-model-log.jsonl.

This proves plumbing. It never shows what a model would do.
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8898
SCRIPT = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else [
    {"when": "What is your name", "reply": "A door, then. Let me think.\ni am testa"},
    {"when": "Welcome", "reply": "I should see my corner first.\nlook Board"},
    {"reply": "Quiet for now. Turn {n}."},
]
LOG = HERE / "fake-model-log.jsonl"
COUNT = {"n": 0}
LOCK = threading.Lock()


def last_user_text(body):
    for m in reversed(body.get("messages") or []):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                return c
            return "\n".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""


def choose(text):
    """-> the first matching rule. A rule with `times` matches at most that many times."""
    for rule in SCRIPT:
        if (not rule.get("when") or rule["when"] in text) and rule.get("times", 1) > 0:
            if "times" in rule:
                rule["times"] -= 1
            return rule
    return {"reply": "ok"}


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)) or b"{}")
        if "count_tokens" in self.path:
            return self._json({"input_tokens": 100})
        with LOCK:
            COUNT["n"] += 1
            n = COUNT["n"]
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"n": n, "path": self.path, "body": body}) + "\n")
        with LOCK:
            rule = choose(last_user_text(body))
        if rule.get("status"):                 # an API error, to test how a failure is handled
            return self._json({"type": "error", "error": {"type": rule.get("error", "invalid_request_error"),
                               "message": rule.get("reply", "scripted failure")}}, rule["status"])
        text = rule.get("reply", "ok").replace("{n}", str(n))
        model = body.get("model", "claude-opus-5-5")
        if not body.get("stream"):
            return self._json({"id": f"msg_{n}", "type": "message", "role": "assistant", "model": model,
                               "content": [{"type": "text", "text": text}], "stop_reason": "end_turn",
                               "stop_sequence": None, "usage": {"input_tokens": 100, "output_tokens": 10}})
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        events = [
            ("message_start", {"type": "message_start", "message": {"id": f"msg_{n}", "type": "message", "role": "assistant",
             "model": model, "content": [], "stop_reason": None, "stop_sequence": None,
             "usage": {"input_tokens": 100, "output_tokens": 1}}}),
            ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
            ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}}),
            ("content_block_stop", {"type": "content_block_stop", "index": 0}),
            ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
             "usage": {"output_tokens": 10}}),
            ("message_stop", {"type": "message_stop"}),
        ]
        for name, data in events:
            self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode("utf-8"))
            self.wfile.flush()

    def do_GET(self):
        self._json({"ok": True})

    def _json(self, obj, status=200):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"fake model on 127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
