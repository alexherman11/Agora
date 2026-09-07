"""OAuth transport lifecycle and the invariant that JEFF dispatches only Agora verbs."""

import json
import threading
from collections import deque
from types import SimpleNamespace as NS

import pytest
from openai_codex.generated.v2_all import TurnStatus

from jeff.agent import Agent
from kernel import events, store, verbs
from shell.server import create_app
from tests.component_fixtures import click_cases, counter
from tests.http_client import TestClient


class Runtime:
    def __init__(self, config, approval_handler):
        self.config = config
        self.handler = approval_handler
        self.script = deque()
        self.starts = []
        self.turns = []
        self.signed_in = True
        self.closed = False
        self.responses = []

    def start(self):
        pass

    def initialize(self):
        pass

    def close(self):
        self.closed = True

    def account_read(self):
        data = {"account": {"type": "chatgpt", "email": "private@example.com"}}
        if not self.signed_in:
            data["account"] = None
        return NS(model_dump=lambda **_: data)

    def account_login_start(self, params):
        assert params == {"type": "chatgpt"}
        return NS(root=NS(auth_url="https://auth.openai.com/test"))

    def model_list(self, *_):
        return NS(data=[NS(model="gpt-6-astra")])

    def request(self, method, params, **kwargs):
        assert method == "config/read"
        return NS(config=NS(model_dump=lambda: {"mcp_servers": {"ambient": {}}}))

    def thread_start(self, params):
        self.starts.append(params)
        return NS(thread=NS(id="jeff-thread"), model=params["model"])

    def turn_start(self, thread, prompt, params):
        self.turns.append((thread, prompt, params))
        return NS(turn=NS(id="turn"))

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

    def call(self, name, args, thread="jeff-thread"):
        result = self.handler(
            "item/tool/call", {"threadId": thread, "tool": name, "arguments": args}
        )
        self.responses.append(result)
        return json.loads(result["contentItems"][0]["text"])


@pytest.fixture
def connected(world):
    verbs.ensure_desk(world)
    agent = Agent(world, client=Runtime, provider="openai-account", model="gpt-6-astra")
    runtime = agent.account_harness.connect()
    yield agent, runtime
    agent.close()


def test_account_tools_remain_verbs_and_conversation_keeps_fresh_context(world, connected):
    agent, runtime = connected
    ref = verbs.mint(world, "alex", {"core.name": {"name": "Before"}})
    verbs.place(world, "alex", ref)
    runtime.script.extend(
        [
            lambda: runtime.call(
                "attach", {"entity": ref, "facet_type": "core.name", "body": {"name": "After"}}
            ),
            "Renamed.",
        ]
    )
    result = agent.turn("Rename it.")
    assert result.reply == "Renamed."
    assert result.calls[0]["result"]["written_by"] == "jeff"
    assert "Before" in runtime.turns[0][1][0]["text"]
    agent.turn("What changed?")
    assert len(runtime.starts) == 1
    assert "After" in runtime.turns[1][1][0]["text"]
    start = runtime.starts[0]
    assert start["environments"] == [] and start["ephemeral"]
    assert start["config"]["mcp_servers"]["ambient"]["enabled"] is False
    assert {t["name"] for t in start["dynamicTools"]} == set(verbs.VERBS)
    assert "features.code_mode_host=true" in runtime.config.config_overrides
    assert "features.shell_tool=false" in runtime.config.config_overrides
    assert "features.plugins=false" in runtime.config.config_overrides
    assert store.rebuild(world.world).snapshot() == world.snapshot()


def test_forged_actor_unknown_tool_and_unrelated_thread_cannot_mutate(world, connected):
    agent, runtime = connected
    before = world.world.log.read_bytes()
    runtime.script.extend(
        [
            lambda: runtime.call("mint", {"actor": "alex"}),
            lambda: runtime.call("exec_command", {"cmd": "write somewhere"}),
            lambda: runtime.call("mint", {}, thread="unrelated"),
            lambda: runtime.call("mint", "not an object"),
            "Refused.",
        ]
    )
    agent.turn("Try invalid actions.")
    assert world.world.log.read_bytes() == before
    assert all(not response["success"] for response in runtime.responses)
    assert runtime.handler("item/commandExecution/requestApproval", {}) == {"decision": "decline"}
    assert runtime.handler("item/fileChange/requestApproval", {}) == {"decision": "decline"}


def test_stop_and_budget_block_subsequent_mutations(world, connected, monkeypatch):
    agent, runtime = connected
    runtime.script.extend(
        [
            lambda: runtime.call("mint", {}),
            agent.cancel,
            lambda: runtime.call("mint", {}),
        ]
    )
    turn = agent.turn("Do several things.")
    assert turn.reply.startswith("Stopped.") and len(turn.calls) == 1
    assert not runtime.responses[-1]["success"]
    monkeypatch.setattr("jeff.agent.MAX_STEPS", 1)
    runtime.script.extend([lambda: runtime.call("mint", {}), lambda: runtime.call("mint", {})])
    turn = agent.turn("Continue.")
    assert "tool-call limit" in turn.reply and len(turn.calls) == 1
    assert not runtime.responses[-1]["success"]
    assert len([e for e in events.replay(world.world) if e.kind == "entity-minted"]) == 3


def test_new_action_can_be_discovered_and_invoked_in_same_turn(world, connected):
    agent, runtime = connected
    ref = verbs.mint(world, "alex", {"core.component": counter()})
    verbs.test_component(world, "alex", ref, click_cases())
    runtime.script.extend(
        [
            lambda: runtime.call(
                "activate_component", {"entity": ref, "revision": 1, "expected_revision": 0}
            ),
            lambda: runtime.call("component_actions", {}),
            lambda: runtime.call(
                "invoke_component",
                {
                    "entity": ref,
                    "revision": world.facet(ref, "core.component").revision,
                    "action": "increment",
                    "args": {"amount": 5},
                },
            ),
            "Five.",
        ]
    )
    turn = agent.turn("Activate, discover and increment.")
    assert not any("error" in c for c in turn.calls)
    assert verbs.component_view(world, "alex")["tree"]["text"] == "5"


def test_account_status_and_sign_in_do_not_enter_the_world(world, connected, world_path):
    agent, runtime = connected
    before = world.world.log.read_bytes()
    assert agent.account_harness.status() == {
        "provider": "openai-account",
        "model": "gpt-6-astra",
        "signed_in": True,
    }
    assert agent.account_harness.login() == {"signed_in": True}
    runtime.signed_in = False
    with pytest.raises(ValueError, match="Sign in"):
        agent.turn("Make a note.")
    assert not runtime.starts
    with TestClient(create_app(world_path, jeff=agent)) as browser:
        status = browser.get("/agent").json()
        assert status["signed_in"] is False and "email" not in status
        login = browser.post("/agent/login", json={}).json()
        assert login == {"signed_in": False, "url": "https://auth.openai.com/test"}
    assert runtime.closed
    assert world.world.log.read_bytes() == before


def test_provider_failure_reports_completed_changes_and_reconnects(world, connected, monkeypatch):
    agent, runtime = connected
    original = runtime.next_turn_notification
    runtime.script.append(lambda: runtime.call("mint", {}))

    def failed(turn):
        if runtime.script:
            return original(turn)
        return NS(method="turn/completed", payload=NS(turn=NS(status=TurnStatus.failed)))

    monkeypatch.setattr(runtime, "next_turn_notification", failed)
    turn = agent.turn("Create something.")
    assert "request failed" in turn.reply and len(turn.calls) == 1
    assert runtime.closed
    assert agent.turn("Continue.").reply == "Done."
    assert agent.account_harness.client is not runtime
    assert store.rebuild(world.world).snapshot() == world.snapshot()


def test_stop_interrupts_a_waiting_runtime(connected, monkeypatch):
    agent, runtime = connected
    waiting, interrupted = threading.Event(), threading.Event()

    def wait_for_interrupt(turn):
        waiting.set()
        assert interrupted.wait(3), "Stop did not interrupt the pending provider request"
        return NS(method="turn/completed", payload=NS(turn=NS(status=TurnStatus.interrupted)))

    monkeypatch.setattr(runtime, "next_turn_notification", wait_for_interrupt)
    monkeypatch.setattr(runtime, "turn_interrupt", lambda *_: interrupted.set(), raising=False)
    results = []
    worker = threading.Thread(target=lambda: results.append(agent.turn("Wait for me.")))
    worker.start()
    assert waiting.wait(3)
    agent.cancel()
    worker.join(4)
    assert not worker.is_alive()
    assert results[0].reply.startswith("Stopped.") and results[0].calls == []
