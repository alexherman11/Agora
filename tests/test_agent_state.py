"""Resident continuity survives a service restart without silently forking identity."""

import pytest

from agora3.agent_state import OBJECT, AgentState
from agora3.gateway import Gateway
from agora3.jeff import Jeff
from agora3.world import Refusal
from tests.test_jeff import ScriptedClient


def resident(directory):
    gateway = Gateway(directory)
    state = AgentState(gateway, directory)
    actor = gateway.principal("jeff", agent_id=state.public()["id"])
    return (
        gateway,
        state,
        Jeff(
            directory,
            lambda name, args: gateway.dispatch(actor, name, args),
            gateway.describe,
            continuity=state,
            bind_session=lambda thread, model: state.bind(actor, thread, model),
        ),
    )


def test_restart_resumes_same_thread_and_preserves_native_identity(tmp_path, monkeypatch):
    monkeypatch.setattr("openai_codex.client.CodexClient", ScriptedClient)
    gateway = Gateway(tmp_path)
    AgentState(gateway, tmp_path).configure(
        gateway.principal("human"),
        agent_id="jeff0",
        name="JEFF0",
        continuity="First-party application experiment; history preserved.",
    )
    gateway, state, first = resident(tmp_path)
    first.send("Remember the architecture discussion.")
    assert first._client.starts[0]["ephemeral"] is False
    binding = state.read()[1]
    assert binding["id"] == "jeff0"
    assert gateway.world.get(OBJECT)["written_by"] == "jeff:jeff0"
    first.close()
    gateway, state, second = resident(tmp_path)
    second.send("Continue.")
    assert second._client.starts == []
    assert second._client.resumes[0][0] == binding["session"]["thread_id"]
    assert second._client.turns[0][1] == [{"type": "text", "text": "Continue."}]
    assert state.read()[1] == binding
    assert gateway.world.verify()["ok"]
    second.close()


def test_failed_resume_keeps_binding_without_replacement(tmp_path, monkeypatch):
    monkeypatch.setattr("openai_codex.client.CodexClient", ScriptedClient)
    gateway, state, agent = resident(tmp_path)
    agent.send("First turn.")
    before = state.read()[1]
    agent.close()
    _, _, agent = resident(tmp_path)
    runtime = agent._connect()

    def fail(*_):
        raise RuntimeError("Missing runtime session")

    monkeypatch.setattr(runtime, "thread_resume", fail)
    with pytest.raises(ValueError, match="could not be resumed"):
        agent.send("Continue.")
    assert runtime.starts == runtime.turns == []
    assert state.read()[1] == before
    agent.close()


def test_copied_world_must_transfer_resident_before_chat(tmp_path):
    original, copied = tmp_path / "original", tmp_path / "copy"
    gateway = Gateway(original)
    state = AgentState(gateway, original)
    state.configure(
        gateway.principal("human"), agent_id="jeff0", name="JEFF0", continuity="Preserved resident."
    )
    state.bind(gateway.principal("jeff"), "retained-thread", "gpt-6-astra")
    copied.mkdir()
    with gateway.world.connection() as source:
        import sqlite3

        with sqlite3.connect(copied / "world.db") as target:
            source.backup(target)
    moved_gateway = Gateway(copied)
    moved = AgentState(moved_gateway, copied)
    with pytest.raises(Refusal, match="copy"):
        moved.owned()
    moved.configure(
        moved_gateway.principal("human"),
        agent_id="jeff0",
        name="JEFF0",
        continuity="Explicitly transferred after the source became idle.",
    )
    assert moved.owned()["session"]["thread_id"] == "retained-thread"
    with pytest.raises(Refusal, match="resume"):
        moved.bind(moved_gateway.principal("jeff"), "replacement", "gpt-6-astra")
    with pytest.raises(Refusal, match="protected"):
        moved_gateway.dispatch(
            moved_gateway.principal("human"),
            "world.transact",
            {
                "changes": [
                    {
                        "id": OBJECT,
                        "expected_revision": moved.read()[0]["revision"],
                        "facets": {"core.title": {"text": "spoofed"}},
                    }
                ]
            },
        )
    assert moved_gateway.world.verify()["ok"]
