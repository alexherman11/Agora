"""Voice and text share one continuing turn and retain unspoken completed results."""

import threading

from agora3.server import Application
from agora3.voice_session import VoiceSession


def test_spoken_followups_steer_same_activity_and_completed_result_survives(tmp_path):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    started, finish = threading.Event(), threading.Event()
    inputs, steering = [], []

    class Agent:
        def send(self, message, observe):
            inputs.append(message)
            started.set()
            assert finish.wait(3)
            return "Read confirmed"

        def steer(self, message):
            steering.append(message)
            return True

    agent = Agent()
    app._agent = lambda: agent
    app.jeff = agent
    app.jeff_identity = app.gateway.principal("jeff")
    activity = app.voice_request("Read the note", actor)
    assert started.wait(3)
    assert app.voice_request("Use the second note", actor) == activity
    assert steering == ["Use the second note"]
    finish.set()
    # Completion can be observed without polling or disturbing the worker.
    for thread in threading.enumerate():
        if thread.name == "agora-jeff":
            thread.join(3)
    assert inputs == ["Read the note"]
    assert app.backend_snapshot(activity)["reply"] == "Read confirmed"
    later = app.send("A later typed message", actor)["activity_id"]
    assert later != activity
    assert app.backend_snapshot(activity) == {
        "id": activity,
        "running": False,
        "reply": "Read confirmed",
        "error": None,
    }
    for thread in threading.enumerate():
        if thread.name == "agora-jeff":
            thread.join(3)


def test_closed_voice_context_reaches_next_typed_turn_once(tmp_path):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    session = VoiceSession(app, actor, "browser-client-1", "jeff")
    app.voice.session = session
    session.transcript.append(
        {"type": "session.input_transcript.delta", "delta": "Call this Orchid"}
    )
    session.transcript.flush()
    session.done.set()
    assert "Call this Orchid" in app.voice.text_context()
    assert app.voice.text_context() == ""
    app.gateway.revoke()
    assert app.voice.text_context() == ""
