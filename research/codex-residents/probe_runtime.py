"""Exercise the real Codex runtime with local mock inference (no live model)."""

import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from codex_resident import MODEL, ThreadEnvelope, deny, receive, runtime_config, thread_parameters
from openai_codex.client import CodexClient


def main():
    requests, events = [], []

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            # Loopback-only diagnostic endpoint; never record request headers.
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            item = {
                "type": "message",
                "id": f"msg{len(requests)}",
                "role": "assistant",
                "phase": "final_answer",
                "content": [{"type": "output_text", "text": "> look\n> rest"}],
            }
            for event in [
                {
                    "type": "response.output_item.added",
                    "output_index": 0,
                    "item": {**item, "content": []},
                },
                {
                    "type": "response.output_text.delta",
                    "output_index": 0,
                    "content_index": 0,
                    "delta": "> look\n> rest",
                },
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {
                    "type": "response.completed",
                    "response": {
                        "id": f"resp{len(requests)}",
                        "status": "completed",
                        "output": [item],
                        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                    },
                },
            ]:
                self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                self.wfile.flush()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="agora-resident-probe-") as temp:
            with CodexClient(runtime_config(temp), approval_handler=deny) as client:
                timer = threading.Timer(45, client.close)
                timer.daemon = True
                timer.start()
                try:
                    client.initialize()
                    params = thread_parameters(
                        client,
                        temp,
                        MODEL,
                        ephemeral=True,
                        config={
                            "model_providers.resident_probe": {
                                "name": "Resident probe",
                                "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                                "wire_api": "responses",
                                "requires_openai_auth": False,
                                "supports_websockets": False,
                            },
                            "features.enable_request_compression": False,
                        },
                    )
                    params["modelProvider"] = "resident_probe"
                    started = client.request("thread/start", params, response_model=ThreadEnvelope)
                    turn = client.turn_start(
                        started.thread.id, "The door probe.", {"effort": "medium"}
                    ).turn.id
                    assert receive(client, turn, events.append)
                finally:
                    timer.cancel()
        assert len(requests) == 1, len(requests)
        req = requests[0]
        summary = {
            "model": req.get("model"),
            "tools": req.get("tools"),
            "instructions": req.get("instructions"),
            "messages": req.get("input"),
            "reply": [e for e in events if e.get("type") in ("assistant", "result")],
            "kind": "actual compiled runtime, local mock inference; no live model",
        }
        output = Path(__file__).parent / "runtime-inventory.json"
        output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    **summary,
                    "messages": [
                        {
                            "type": i.get("type"),
                            "role": i.get("role"),
                            "text": str(i.get("content", ""))[:250],
                            "tools": [t.get("name") for t in i.get("tools", [])],
                        }
                        for i in req.get("input", [])
                    ],
                },
                indent=2,
            )
        )
        assert not req.get("tools") and not any(i.get("tools") for i in req.get("input", [])), (
            "Resident runtime exposed tools"
        )
        assert not req.get("instructions"), "Resident runtime injected system instructions"
        assert [
            i
            for i in req.get("input", [])
            if i.get("type") == "message" and i.get("role") in ("system", "developer")
        ] == [], "Injected instructions"
        assert [
            i
            for i in req.get("input", [])
            if i.get("type") == "message" and i.get("role") == "user"
        ] == [req["input"][-1]], "Injected user instructions"
        assert any(
            e.get("type") == "result" and e.get("result") == "> look\n> rest" for e in events
        )
        print(
            "PASS: no tools, no system/developer prompt, completed text reaches the house protocol"
        )
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
