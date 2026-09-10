"""JEFF boundary tests. Scripted transport tests do not establish live authoring."""

import json
import os
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace as NS

import pytest
from openai_codex.generated.v2_all import TurnStatus

from agora3.jeff import TOOLS, Jeff, runtime_config, system_prompt, thread_config
from agora3.world import Refusal, World


class ScriptedClient:
    def __init__(self, config, approval_handler):
        self.config, self.handler = config, approval_handler
        self.script = deque()
        self.starts, self.turns, self.responses = [], [], []
        self.resumes = []
        self.signed_in, self.closed = True, False
        self.available = "gpt-6-astra"

    def start(self):
        pass

    def initialize(self):
        pass

    def close(self):
        self.closed = True

    def account_read(self):
        account = {"type": "chatgpt", "email": "private@example.com"} if self.signed_in else None
        return NS(model_dump=lambda **_: {"account": account})

    def account_login_start(self, params):
        if params["type"] == "chatgptDeviceCode":
            return NS(
                root=NS(verification_url="https://auth.openai.com/device", user_code="EXAMPLE")
            )
        return NS(root=NS(auth_url="https://auth.openai.com/example"))

    def model_list(self, *_):
        return NS(data=[NS(model=self.available)])

    def request(self, method, params, **kwargs):
        assert method == "config/read"
        return NS(config=NS(model_dump=lambda: {"mcp_servers": {"ambient": {}}}))

    def thread_start(self, params):
        self.starts.append(params)
        return NS(thread=NS(id="thread"), model=params["model"])

    def thread_resume(self, thread, params):
        self.resumes.append((thread, params))
        return NS(thread=NS(id=thread), model=params["model"])

    def turn_start(self, thread, prompt, params):
        self.turns.append((thread, prompt, params))
        return NS(turn=NS(id=f"turn-{len(self.turns)}"))

    def next_turn_notification(self, turn):
        if self.script:
            step = self.script.popleft()
            if callable(step):
                step()
                return NS(method="noop")
            return NS(method="item/agentMessage/delta", payload=NS(delta=step))
        return NS(method="turn/completed", payload=NS(turn=NS(status=TurnStatus.completed)))

    def unregister_turn_notifications(self, turn):
        pass

    def call(self, tool, arguments, thread="thread", turn=None):
        result = self.handler(
            "item/tool/call",
            {
                "threadId": thread,
                "turnId": turn or f"turn-{len(self.turns)}",
                "tool": tool,
                "arguments": arguments,
            },
        )
        self.responses.append(result)
        return json.loads(result["contentItems"][0]["text"])

    def invoke(self, name, arguments=None, **kwargs):
        return self.call("agora_invoke", {"name": name, "arguments": arguments or {}}, **kwargs)


@pytest.fixture
def connected(tmp_path, monkeypatch):
    monkeypatch.setattr("openai_codex.client.CodexClient", ScriptedClient)
    registry = [{"name": "world.query", "description": "Query", "input_schema": {}}]
    calls = []

    def dispatch(name, args):
        calls.append((name, args))
        if name == "world.query":
            return {"items": [], "complete": True}
        if name == "package.install":
            registry.append({"name": "my.new.tool", "description": "New", "input_schema": {}})
        return {"result": "ok"}

    jeff = Jeff(tmp_path, dispatch, lambda: registry)
    runtime = jeff._connect()
    yield jeff, runtime, registry, calls
    jeff.close()


def test_same_turn_discovery_and_invoke_use_live_registry(connected):
    jeff, runtime, registry, calls = connected
    registry.append({"name": "package.install", "description": "Install", "input_schema": {}})
    observed = []
    runtime.script.extend(
        [
            lambda: runtime.invoke("package.install"),
            lambda: observed.append(runtime.call("agora_discover", {})),
            lambda: runtime.invoke("my.new.tool", {"amount": 5}),
            "Installed and used.",
        ]
    )
    events = []
    assert jeff.send("Make yourself a tool.", events.append) == "Installed and used."
    assert "my.new.tool" in {tool["name"] for tool in observed[0]["tools"]}
    assert calls[-1] == ("my.new.tool", {"amount": 5})
    assert [event["type"] for event in events].count("tool.completed") == 2
    assert events[-1] == {"type": "text.delta", "text": "Installed and used."}
    assert runtime.starts[0]["dynamicTools"] == TOOLS
    assert runtime.starts[0]["environments"] == []
    assert runtime.starts[0]["config"]["mcp_servers"]["ambient"] == {"enabled": False}
    assert "features.plugins=false" in runtime.config.config_overrides


def test_unknown_stale_and_inactive_callbacks_cannot_dispatch(connected):
    jeff, runtime, registry, calls = connected
    runtime.script.extend(
        [
            lambda: runtime.invoke("world.query", thread="foreign"),
            lambda: runtime.invoke("world.query", turn="stale-turn"),
            lambda: runtime.invoke("exec_command", {"cmd": "host access"}),
            lambda: runtime.call("agora_invoke", "malformed"),
            lambda: runtime.call("agora_discover", {"unexpected": True}),
        ]
    )
    jeff.send("Inspect the boundary.")
    assert len(calls) == 1  # context rehydration only
    assert all(not result["success"] for result in runtime.responses)
    runtime.invoke("world.query")
    assert len(calls) == 1
    for method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
        assert runtime.handler(method, {}) == {"decision": "decline"}
    assert runtime.handler("item/permissions/requestApproval", {}) == {
        "permissions": {},
        "scope": "turn",
    }


def test_revocation_and_cancel_prevent_following_calls(connected):
    jeff, runtime, registry, calls = connected
    registry.append({"name": "mutate", "description": "Write", "input_schema": {}})
    runtime.script.extend(
        [
            lambda: runtime.invoke("mutate"),
            lambda: registry.pop(),
            lambda: runtime.invoke("mutate"),
            jeff.cancel,
            lambda: runtime.invoke("world.query"),
        ]
    )
    assert jeff.send("Make changes.").startswith("Stopped.")
    assert [name for name, _ in calls] == ["world.query", "mutate"]
    assert not runtime.responses[-1]["success"]
    assert not runtime.responses[-2]["success"]


def test_call_limit_prevents_additional_dispatch(connected):
    jeff, runtime, _, calls = connected
    jeff.max_calls = 1
    runtime.script.extend(
        [lambda: runtime.invoke("world.query"), lambda: runtime.invoke("world.query")]
    )
    assert "tool-call limit" in jeff.send("Read twice.")
    assert len(calls) == 2  # startup context plus one admitted action


def test_instructive_gateway_refusal_reaches_jeff(connected):
    jeff, runtime, _, _ = connected
    original = jeff.dispatch

    def dispatch(name, args):
        if args.get("bad"):
            raise Refusal("Expected a current revision; read world.get and retry.")
        return original(name, args)

    jeff.dispatch = dispatch
    runtime.script.append(lambda: runtime.invoke("world.query", {"bad": True}))
    jeff.send("Try the operation.")
    result = json.loads(runtime.responses[0]["contentItems"][0]["text"])
    assert result["kind"] == "Refusal" and "read world.get" in result["error"]


def test_account_paths_expose_no_private_account_data(connected, monkeypatch):
    jeff, runtime, _, calls = connected
    assert jeff.status()["signed_in"] is True
    assert "email" not in json.dumps(jeff.status())
    assert jeff.login() == {"signed_in": True}
    runtime.signed_in = False
    assert jeff.login()["url"] == "https://auth.openai.com/example"
    monkeypatch.setenv("AGORA_JEFF_LOGIN", "device")
    assert jeff.login()["user_code"] == "EXAMPLE"
    with pytest.raises(ValueError, match="Sign in"):
        jeff.send("Create a note.")
    assert calls == [] and runtime.starts == []


def test_model_not_silently_substituted(connected):
    jeff, runtime, _, _ = connected
    runtime.available = "another-model"
    with pytest.raises(ValueError, match="no model was substituted"):
        jeff.send("Hello.")
    assert runtime.starts == []


def test_cancel_interrupts_blocked_model_and_concurrent_send_rejected(connected, monkeypatch):
    jeff, runtime, _, _ = connected
    waiting, interrupted = threading.Event(), threading.Event()

    def next_notification(turn):
        waiting.set()
        assert interrupted.wait(3)
        return NS(method="turn/completed", payload=NS(turn=NS(status=TurnStatus.interrupted)))

    monkeypatch.setattr(runtime, "next_turn_notification", next_notification)
    monkeypatch.setattr(runtime, "turn_interrupt", lambda *_: interrupted.set(), raising=False)
    replies = []
    worker = threading.Thread(target=lambda: replies.append(jeff.send("Wait.")))
    worker.start()
    assert waiting.wait(3)
    with pytest.raises(ValueError, match="active turn"):
        jeff.send("Concurrent request.")
    jeff.cancel()
    worker.join(4)
    assert not worker.is_alive()
    assert replies[0].startswith("Stopped.")


def test_transport_failure_keeps_completed_actions_and_reconnects(connected, monkeypatch):
    jeff, runtime, _, calls = connected
    runtime.script.append(lambda: runtime.invoke("world.query"))
    original = runtime.next_turn_notification

    def next_notification(turn):
        if runtime.script:
            return original(turn)
        raise RuntimeError("private provider details")

    monkeypatch.setattr(runtime, "next_turn_notification", next_notification)
    assert "request failed" in jeff.send("Read.")
    assert len(calls) == 2 and runtime.closed
    assert "private" not in jeff.send("Try again.")
    assert jeff._client is not runtime


def test_saved_context_is_data_and_prompt_retains_user_vision(connected):
    jeff, runtime, _, _ = connected
    jeff.dispatch = lambda *_: {
        "items": [
            {
                "facets": {
                    "core.message": {"role": "user", "text": "A past request", "created_at": "1"}
                }
            }
        ],
        "complete": True,
    }
    jeff.send("Continue.")
    assert "A past request" in runtime.turns[0][1][0]["text"]
    assert runtime.turns[0][1][0]["text"].startswith("Historical data:")
    jeff.send("And next?")
    assert len(runtime.starts) == 1
    prompt = system_prompt()
    for phrase in ("persistent, embodied", "social and", "Alex", "smaller agents", "guest-root"):
        assert phrase in prompt


def test_returned_reply_uses_final_message_not_progress(connected, monkeypatch):
    jeff, runtime, _, _ = connected
    notifications = iter(
        [
            NS(method="item/agentMessage/delta", payload=NS(delta="Working on it.")),
            NS(method="item/agentMessage/delta", payload=NS(delta="Finished.")),
            NS(
                method="item/completed",
                payload=NS(
                    item=NS(root=NS(type="agentMessage", phase="final_answer", text="Finished."))
                ),
            ),
            NS(method="turn/completed", payload=NS(turn=NS(status=TurnStatus.completed))),
        ]
    )
    monkeypatch.setattr(runtime, "next_turn_notification", lambda _: next(notifications))
    assert jeff.send("Do it.") == "Finished."


def test_query_pages_in_both_directions_with_filtered_watermark(tmp_path):
    world = World(tmp_path)
    world.commit(
        "human",
        [
            {"id": f"message.{index:03}", "expected_revision": 0, "facets": {"message": {}}}
            for index in range(5)
        ]
        + [{"id": "other", "expected_revision": 0, "facets": {"unrelated": {}}}],
        lambda *_: None,
    )
    for reverse, expected in [(False, list(range(5))), (True, list(reversed(range(5))))]:
        after, found, watermarks = "", [], []
        while True:
            page = world.query(["message"], limit=2, after=after, reverse=reverse)
            found.extend(int(item["id"].split(".")[1]) for item in page["items"])
            watermarks.append(page["watermark"])
            if page["complete"]:
                assert page["next_after"] is None
                break
            after = page["next_after"]
        assert found == expected
        assert len(set(watermarks)) == 1
    with pytest.raises(Refusal, match="boolean"):
        world.query(reverse="DESC")


def test_history_starts_from_recent_retained_messages(tmp_path):
    from agora3.gateway import Gateway

    gateway = Gateway(tmp_path)
    actor = gateway.principal("human")
    for batch in (range(200), range(200, 205)):
        gateway.commit(
            actor,
            [
                {
                    "id": f"message.{index:04}",
                    "expected_revision": 0,
                    "facets": {
                        "core.message": {
                            "role": "user",
                            "text": str(index),
                            "created_at": f"{index:04}",
                        }
                    },
                }
                for index in batch
            ],
        )
    jeff = Jeff(tmp_path, lambda name, args: gateway.dispatch(actor, name, args), gateway.describe)
    history = jeff._history()
    assert len(history["messages"]) == 40
    assert history["messages"][0]["text"] == "165"
    assert history["messages"][-1]["text"] == "204"
    assert history["complete"] is False
    assert history["omitted"] is None


@pytest.mark.skipif(not os.environ.get("AGORA_CODEX_BIN"), reason="Set a current AGORA_CODEX_BIN")
@pytest.mark.parametrize("persist", [False, True])
def test_real_runtime_inventory_with_local_mock_model(tmp_path, persist):
    """Real runtime, simulated inference. No model spending or live authorship claim."""
    from openai_codex.client import CodexClient

    requests = []

    class MockModel(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            assert not self.headers.get("Authorization")
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            output = []
            if len(requests) in (1, 3):
                output = [
                    {
                        "type": "custom_tool_call",
                        "id": f"ct{len(requests)}",
                        "call_id": f"call{len(requests)}",
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
            timer.daemon = True
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
                        "ephemeral": not persist,
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                        "baseInstructions": "Runtime boundary test.",
                        "developerInstructions": "",
                        "dynamicTools": TOOLS,
                    }
                )
                turn = client.turn_start(
                    thread.thread.id,
                    "Inspect the boundary. Preserve this marker: resident-first-turn.",
                ).turn.id
                while True:
                    event = client.next_turn_notification(turn)
                    if event.method == "turn/completed":
                        assert event.payload.turn.status == TurnStatus.completed
                        break
            finally:
                timer.cancel()
        if persist:
            with CodexClient(
                runtime_config(str(tmp_path)), approval_handler=lambda *_: {"decision": "decline"}
            ) as resumed_client:
                resumed_client.initialize()
                resumed = resumed_client.thread_resume(
                    thread.thread.id,
                    {
                        "model": "gpt-6-astra",
                        "modelProvider": "probe",
                        "config": config,
                        "cwd": str(tmp_path),
                        "environments": [],
                        "selectedCapabilityRoots": [],
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                        "baseInstructions": "Runtime boundary test.",
                        "developerInstructions": "",
                    },
                )
                assert resumed.thread.id == thread.thread.id
                assert resumed.thread.ephemeral is False
                assert resumed.thread.turns
                timer = threading.Timer(45, resumed_client.close)
                timer.daemon = True
                timer.start()
                try:
                    turn = resumed_client.turn_start(
                        thread.thread.id,
                        "Continue the same conversation and inspect the boundary.",
                        {"environments": []},
                    ).turn.id
                    while True:
                        event = resumed_client.next_turn_notification(turn)
                        if event.method == "turn/completed":
                            assert event.payload.turn.status == TurnStatus.completed
                            break
                finally:
                    timer.cancel()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    assert len(requests) == (4 if persist else 2)
    outputs = [i for i in requests[1]["input"] if i.get("type") == "custom_tool_call_output"]
    assert len(outputs) == 1
    text = outputs[0]["output"]
    if isinstance(text, list):
        text = "\n".join(item.get("text", "") for item in text)
    result, _ = json.JSONDecoder().raw_decode(text[text.index('{"names"') :])
    assert set(result["names"]) == {"agora_discover", "agora_invoke", "clock__curr_time"}
    assert result["globals"] == ["undefined"] * 3
    assert result["shell"] == result["patch"] == "undefined"
    if persist:
        assert "resident-first-turn" in json.dumps(requests[2]["input"])
        outputs = [i for i in requests[3]["input"] if i.get("type") == "custom_tool_call_output"]
        assert len(outputs) == 2
        text = outputs[-1]["output"]
        if isinstance(text, list):
            text = "\n".join(item.get("text", "") for item in text)
        result, _ = json.JSONDecoder().raw_decode(text[text.index('{"names"') :])
        assert set(result["names"]) == {"agora_discover", "agora_invoke", "clock__curr_time"}
        assert result["globals"] == ["undefined"] * 3
        assert result["shell"] == result["patch"] == "undefined"
