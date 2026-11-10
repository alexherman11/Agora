"""fake_model: a scripted stand-in for the Messages API that can call tools, for testing the house without a model.

    python fake_model.py <port> <log.jsonl>

Point claude -p at it (HOUSE_FAKE_MODEL=http://127.0.0.1:<port>, which the house passes as ANTHROPIC_BASE_URL).
For each request whose latest user turn is words, it answers "On it." and calls the `lines` tool once with the lines
that follow `RUN:` in those words (one per `|`); when the latest turn is that tool's result, it answers
"Done: <the first line of the result>". Requests are logged (the tool names offered, the last user text).

This proves plumbing. It never shows what a model would do.
"""
import json
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()


def last_user(body):
    for m in reversed(body.get("messages") or []):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                return c, None
            texts, result = [], None
            for p in c:
                if p.get("type") == "text":
                    texts.append(p.get("text", ""))
                elif p.get("type") == "tool_result":
                    rc = p.get("content")
                    result = rc if isinstance(rc, str) else "\n".join(x.get("text", "") for x in rc or [])
            return "\n".join(texts), result
    return "", None


def reply(body):
    text, result = last_user(body)
    tools = [t.get("name") for t in body.get("tools") or []]
    if result is not None:
        first = result.strip().splitlines()[0][:200] if result.strip() else "(nothing)"
        return [{"type": "text", "text": "Done: " + first}], "end_turn"
    if "RUN:" in text and any(t.endswith("__lines") for t in tools):
        lines = [x.strip() for x in text.split("RUN:", 1)[1].splitlines()[0].split("|") if x.strip()]
        name = next(t for t in tools if t.endswith("__lines"))
        return [{"type": "text", "text": "On it."},
                {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:12], "name": name, "input": {"lines": lines}}], "tool_use"
    if not tools:
        return [{"type": "text", "text": "A title"}], "end_turn"       # claude's own side requests
    return [{"type": "text", "text": "Heard you."}], "end_turn"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        if "count_tokens" in self.path:
            return self._json({"input_tokens": 100})
        blocks, stop = reply(body)
        with LOCK, open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"tools": [t.get("name") for t in body.get("tools") or []],
                                "user": last_user(body)[0][-2000:], "result": last_user(body)[1],
                                "system": str(body.get("system"))[:3000], "model": body.get("model")}) + "\n")
        mid = "msg_" + uuid.uuid4().hex[:12]
        usage = {"input_tokens": 50, "output_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
        if not body.get("stream"):
            return self._json({"id": mid, "type": "message", "role": "assistant", "model": body.get("model"),
                               "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": usage})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def ev(name, data):
            self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()
        ev("message_start", {"type": "message_start", "message": {"id": mid, "type": "message", "role": "assistant",
            "model": body.get("model"), "content": [], "stop_reason": None, "stop_sequence": None, "usage": usage}})
        for i, b in enumerate(blocks):
            if b["type"] == "text":
                ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}})
                ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": b["text"]}})
            else:
                ev("content_block_start", {"type": "content_block_start", "index": i, "content_block":
                    {"type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}})
                ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta":
                    {"type": "input_json_delta", "partial_json": json.dumps(b["input"])}})
            ev("content_block_stop", {"type": "content_block_stop", "index": i})
        ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                             "usage": {"output_tokens": 10}})
        ev("message_stop", {"type": "message_stop"})

    def _json(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    PORT, LOG = int(sys.argv[1]), sys.argv[2]
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"fake model on {srv.server_address[1]}", flush=True)
    srv.serve_forever()
