"""Selective handoffs, one conversation, and honest delivery receipts."""

from agora3.server import Application
from agora3.voice_coordination import Coordination
from agora3.voice_session import VoiceSession


def capture(target):
    return lambda kind, **values: target.append({"type": kind, **values})


def test_progress_has_no_tool_payload_and_receipt_does_not_claim_speech():
    state, sent = Coordination(), []
    state.received("d", "voice", "d")
    state.accepted("d", "activity")
    state.observe(
        "activity",
        "d",
        {
            "id": "activity",
            "running": True,
            "tool": {"name": "package.read", "running": True, "arguments": "SECRET"},
            "messages": [
                {
                    "id": "m",
                    "phase": "commentary",
                    "complete": True,
                    "text": "I am checking the package.",
                }
            ],
        },
    )
    state.flush(capture(sent))
    assert "SECRET" not in str(sent)
    assert any(e["type"] == "session.thinking.append" for e in sent)
    assert any("I am checking" in e["content"] for e in sent)
    assert state.snapshot()["requests"][0]["stage"] == "working"
    state.observe("activity", "d", {"id": "activity", "running": False, "reply": "Done. " * 200})
    sent.clear()
    state.flush(capture(sent))
    assert state.snapshot()["requests"][0]["stage"] == "sent"
    for event in sent[:-1]:
        state.acknowledge(
            {"type": "session.commentary.appended", "client_event_id": event["event_id"]}
        )
    assert state.snapshot()["requests"][0]["stage"] == "sent"
    state.acknowledge(
        {"type": "session.commentary.appended", "client_event_id": sent[-1]["event_id"]}
    )
    assert state.snapshot()["requests"][0]["stage"] == "delivered"
    assert state.snapshot()["last_spoke_at"] is None


def test_new_task_does_not_discard_previous_result_and_followup_supersedes_same_task():
    state = Coordination()
    for identifier, activity in [("a", "first"), ("b", "second"), ("c", "second")]:
        state.received(identifier, "voice", identifier)
        state.accepted(identifier, activity)
    assert state.activities() == [("first", "a"), ("second", "c")]
    assert state.snapshot()["requests"][1]["stage"] == "continued"


def test_typed_brainstorm_stays_in_conversation_even_while_harness_is_busy(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "test-conversation", "jeff")
    app.voice.session = session
    app.running = True
    app._agent = lambda: (_ for _ in ()).throw(AssertionError("Must not invoke Astra"))
    result = app.send("Maybe a calendar, but let's explore the idea first", session.actor)
    assert result["route"] == "conversation"
    assert session.jobs.empty() and session.coordination.activities() == []
    assert app.chat_status()["messages"][-1]["text"].startswith("Maybe a calendar")
    sent = []
    session.coordination.flush(capture(sent))
    assert all(e["type"] == "session.thinking.append" for e in sent)
    for event in sent:
        session.coordination.acknowledge(
            {"type": "session.thinking.appended", "client_event_id": event["event_id"]}
        )
    sent.clear()
    session.coordination.flush(capture(sent))
    assert len(sent) == 1 and sent[0]["type"] == "session.commentary.append"
    assert session.jobs.empty()


def test_live_speech_and_persisted_speech_share_chat_without_starting_work(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "test-conversation", "jeff")
    app.voice.session = session
    session.handle({"type": "session.input_transcript.delta", "delta": "Let's think about it."})
    before = app.chat_status()
    assert before["messages"][-1]["text"] == "Let's think about it."
    assert before["messages"][-1]["streaming"]
    assert session.jobs.empty() and not app.running
    session.transcript.flush()
    after = app.chat_status()
    assert len(after["messages"]) == len(before["messages"]) == 1
    assert after["messages"][-1]["text"] == before["messages"][-1]["text"]
    assert app.gateway.world.verify()["ok"]


def test_observer_gets_receipts_without_renewing_owner_heartbeat(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "owner-conversation", "jeff")
    app.voice.session = session
    session.last_seen = 1
    session.coordination.received("d", "voice", "d")
    result = app.voice.status("observer-client-1")
    assert not result["owner"] and result["coordination"]["requests"]
    assert session.last_seen == 1
