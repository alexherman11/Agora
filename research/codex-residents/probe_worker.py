"""Inspect the compiled worker runtime using loopback mock inference."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from codex_resident import ThreadEnvelope, deny, receive
from codex_worker import build_config, pinned_catalog, thread_parameters
from openai_codex.client import CodexClient
from probe_support import empty_profile, fixture_mcp, options, probe_directory
from worker_job import child_job


def main():
    args = options("worker")
    requests = []
    directory = None

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            # Capture the offered tools even when a later execution check fails.
            # A nonzero exit still makes the checker refuse this candidate.
            if len(requests) == 1:
                args.output.write_text(json.dumps(requests[0], indent=2), encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            item = (
                {
                    "type": "tool_search_call",
                    "id": "search_desk",
                    "call_id": "search_desk",
                    "execution": "client",
                    "status": "completed",
                    "arguments": {"query": "desk shared world", "limit": 1},
                }
                if len(requests) == 1
                else {
                    "type": "function_call",
                    "id": "call_probe",
                    "call_id": "call_probe",
                    "name": "exec_command",
                    "namespace": "functions",
                    "arguments": json.dumps(
                        {
                            "cmd": "Set-Content -LiteralPath worker-probe.txt -Value passed",
                            "workdir": directory,
                                "login": False,
                            "max_output_tokens": 200,
                        }
                    ),
                }
                if len(requests) == 2
                else {
                    "type": "function_call",
                    "id": "call_desk",
                    "call_id": "call_desk",
                    "name": "desk",
                    "namespace": "mcp__desk",
                    "arguments": json.dumps({"line": "help", "as": "codex"}),
                }
                if len(requests) == 3
                else {
                    "type": "message",
                    "id": "probe",
                    "role": "assistant",
                    "phase": "final_answer",
                    "content": [{"type": "output_text", "text": "WORKER_PROBE_OK"}],
                }
            )
            events = [
                {"type": "response.output_item.added", "output_index": 0, "item": item},
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {
                    "type": "response.completed",
                    "response": {
                        "id": "worker_probe",
                        "status": "completed",
                        "output": [item],
                        "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                    },
                },
            ]
            for event in events:
                self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                self.wfile.flush()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Model)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with probe_directory() as directory:
            profile = empty_profile(directory)
            mcp = fixture_mcp(directory)
            catalog, _ = pinned_catalog(args.model)
            with (
                CodexClient(
                    build_config(directory, str(args.binary), profile, catalog),
                    approval_handler=deny,
                ) as client,
                child_job(client._proc),
            ):
                timer = threading.Timer(60, client.close)
                timer.daemon = True
                timer.start()
                try:
                    client.initialize()
                    params = thread_parameters(
                        directory,
                        args.model,
                        "WORKER_PROTOCOL_MARKER",
                        mcp,
                        {
                            "model_providers.worker_probe": {
                                "name": "Worker probe",
                                "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                                "wire_api": "responses",
                                "requires_openai_auth": False,
                                "supports_websockets": False,
                            },
                            "features.enable_request_compression": False,
                        },
                    )
                    params.update(modelProvider="worker_probe", ephemeral=True)
                    started = client.request("thread/start", params, response_model=ThreadEnvelope)
                    turn = client.turn_start(started.thread.id, "Return WORKER_PROBE_OK").turn.id
                    output = []
                    assert receive(client, turn, output.append)
                    command_events = [
                        e
                        for e in output
                        if e.get("method") == "item/completed"
                        and e.get("data", {}).get("item", {}).get("type") == "commandExecution"
                    ]
                    assert command_events and command_events[0]["data"]["item"]["exitCode"] == 0, (
                        command_events
                    )
                    desk_events = [
                        e["data"]["item"]
                        for e in output
                        if e.get("method") == "item/completed"
                        and e.get("data", {}).get("item", {}).get("type") == "mcpToolCall"
                    ]
                    assert desk_events and desk_events[0]["status"] == "completed", (
                        desk_events,
                        requests[-1].get("input", [])[-2:],
                    )
                    assert "PIN_FIXTURE_DESK_OK" in json.dumps(requests[-1])
                    assert (Path(directory) / "worker-probe.txt").read_text().strip() == "passed"
                finally:
                    timer.cancel()
        assert len(requests) == 4
        discovered = [i for i in requests[1]["input"] if i.get("type") == "tool_search_output"]
        assert discovered and "mcp__desk" in json.dumps(discovered), discovered
        request = requests[0]
        path = args.output
        path.write_text(json.dumps(request, indent=2), encoding="utf-8")
        tools = request.get("tools") or []
        for item in request.get("input", []):
            tools.extend(item.get("tools") or [])
        print(
            json.dumps(
                {
                    "model": request.get("model"),
                    "tools": [
                        {
                            "name": t.get("name"),
                            "tools": [x.get("name") for x in t.get("tools", [])],
                        }
                        for t in tools
                    ],
                    "input_kinds": [
                        (i.get("type"), i.get("role")) for i in request.get("input", [])
                    ],
                },
                indent=2,
            )
        )
        assert request.get("model") == args.model
        assert "WORKER_PROTOCOL_MARKER" in json.dumps(request)
        assert tools, "Worker has no tools"
        assert "- desk:" in json.dumps(tools), "Desk MCP server missing from tool discovery"
        print("PASS: actual worker runtime and protocol; mock inference, no live model")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
