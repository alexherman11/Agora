"""Opt-in real Codex runtime test: local mock inference, no account/model spending."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from openai_codex.client import CodexClient
from openai_codex.generated.v2_all import TurnStatus

from jeff.codex_config import runtime_config, thread_config
from jeff.tools import derive_tools


@pytest.mark.skipif(not os.environ.get("AGORA_CODEX_BIN"), reason="set a current AGORA_CODEX_BIN")
def test_runtime_exposes_only_agora_actions_and_no_computer_globals(tmp_path):
    requests = []

    class MockModel(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            # The mock provider must not receive the user's OAuth credentials.
            assert not self.headers.get("Authorization")
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(data)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            output = []
            if len(requests) == 1:
                output = [
                    {
                        "type": "custom_tool_call",
                        "id": "ct1",
                        "call_id": "call1",
                        "name": "exec",
                        "namespace": "functions",
                        "input": "text({names:ALL_TOOLS.map(t=>t.name),"
                        "globals:[typeof process,typeof fetch,typeof require],"
                        "shell:typeof tools.exec_command,patch:typeof tools.apply_patch});",
                    }
                ]
            for item in output:
                self.emit({"type": "response.output_item.done", "output_index": 0, "item": item})
            self.emit(
                {
                    "type": "response.completed",
                    "response": {
                        "id": f"r{len(requests)}",
                        "status": "completed",
                        "output": output,
                        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                    },
                }
            )

        def emit(self, event):
            self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
            self.wfile.flush()

    server = ThreadingHTTPServer(("127.0.0.1", 0), MockModel)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with CodexClient(
            runtime_config(str(tmp_path)), approval_handler=lambda *_: {"decision": "decline"}
        ) as client:
            timer = threading.Timer(45, client.close)
            timer.start()
            try:
                client.initialize()
                config = thread_config(client)
                config.update(
                    {
                        "model_providers.probe": {
                            "name": "Probe",
                            "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                            "wire_api": "responses",
                            "requires_openai_auth": False,
                            "supports_websockets": False,
                        },
                        "features.enable_request_compression": False,
                    }
                )
                thread = client.thread_start(
                    {
                        "model": "gpt-6-astra",
                        "modelProvider": "probe",
                        "config": config,
                        "cwd": str(tmp_path),
                        "environments": [],
                        "selectedCapabilityRoots": [],
                        "ephemeral": True,
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                        "baseInstructions": "Runtime test.",
                        "developerInstructions": "",
                        "dynamicTools": [
                            {
                                "type": "function",
                                "name": t["name"],
                                "description": t["description"],
                                "inputSchema": t["input_schema"],
                            }
                            for t in derive_tools()
                        ],
                    }
                )
                turn = client.turn_start(thread.thread.id, "Inspect the tool boundary.").turn.id
                while True:
                    event = client.next_turn_notification(turn)
                    if event.method == "turn/completed":
                        assert event.payload.turn.status == TurnStatus.completed
                        break
            finally:
                timer.cancel()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    assert len(requests) == 2
    outputs = [i for i in requests[1]["input"] if i.get("type") == "custom_tool_call_output"]
    assert len(outputs) == 1
    raw = json.dumps(outputs[0])
    for t in derive_tools():
        assert t["name"] in raw
    assert "undefined" in raw
    # Parse the returned JSON text, which the runtime wraps in an output envelope.
    texts = outputs[0]["output"]
    if isinstance(texts, list):
        texts = "\n".join(x.get("text", "") for x in texts)
    begin = texts.index('{"names"')
    result, _ = json.JSONDecoder().raw_decode(texts[begin:])
    # Astra's model catalog adds a UTC clock independently of feature flags.
    # It cannot read files or world state; allow this one documented helper.
    assert set(result["names"]) == {t["name"] for t in derive_tools()} | {"clock__curr_time"}
    assert result["globals"] == ["undefined"] * 3
    assert result["shell"] == result["patch"] == "undefined"
