"""Voice generations change without interrupting work or discarding closed-call context."""

import threading
from types import SimpleNamespace

import pytest

from agora3 import voice_reload
from agora3.server import Application
from agora3.voice_session import VoiceSession
from agora3.world import Refusal


def test_reload_during_running_jeff_preserves_turn_and_history(tmp_path):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    started, finish = threading.Event(), threading.Event()

    def send(message, observe):
        started.set()
        assert finish.wait(5)
        return "Finished the original task"

    agent = SimpleNamespace(send=send)
    app._agent = lambda: agent
    app.jeff = agent
    app.jeff_identity = app.gateway.principal("jeff")
    activity = app.send("Original task", actor)["activity_id"]
    assert started.wait(2)
    session = VoiceSession(app, actor, "closed-voice-client", "jeff")
    session.transcript.typed("Retain this context")
    session.done.set()
    app.voice.session = session
    old_factory = app.voice.session_factory
    try:
        result = app.dispatch("operator", "host.voice.reload", {}, actor)
        assert result["reloaded"] and app.running
        assert app.jeff is agent and app.activity.id == activity
        assert app.voice.session is session
        assert app.voice.session_factory is not old_factory
        assert "Retain this context" in app.voice.text_context()
    finally:
        finish.set()
        for thread in threading.enumerate():
            if thread.name == "agora-jeff":
                thread.join(3)
    assert app.backend_snapshot(activity)["reply"] == "Finished the original task"
    assert app.gateway.world.verify()["ok"]


def test_active_voice_and_running_delegation_refuse_reload(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "voice-client-test", "jeff")
    app.voice.session = session
    with pytest.raises(Refusal, match="finish closing"):
        app.voice.reload()
    session.done.set()
    session.threads = (SimpleNamespace(is_alive=lambda: True),)
    with pytest.raises(Refusal, match="finish closing"):
        app.voice.reload()


def test_bad_generation_preserves_current_factories(tmp_path, monkeypatch):
    app = Application(tmp_path / "world")
    sources = tmp_path / "source"
    sources.mkdir()
    for name in voice_reload.NAMES:
        (sources / (name + ".py")).write_text("invalid python !")
    monkeypatch.setattr(voice_reload, "ROOT", sources)
    original = app.voice.connect, app.voice.session_factory, app.voice.version
    with pytest.raises(Refusal, match="current version is retained"):
        app.voice.reload()
    assert (app.voice.connect, app.voice.session_factory, app.voice.version) == original


def test_reload_is_protected_and_has_no_caller_source_path(tmp_path):
    app = Application(tmp_path)
    with pytest.raises(Refusal, match="independent human"):
        app.dispatch("guest", "host.voice.reload", {})
    with pytest.raises(Refusal, match="no arguments"):
        app.dispatch("operator", "host.voice.reload", {"path": "foreign.py"})
