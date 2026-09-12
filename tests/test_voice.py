"""Voice uses the same resident, admission boundary and durable conversation."""

import queue
import threading
import time
from types import SimpleNamespace

import pytest

from agora3.jeff import Jeff
from agora3.server import Application
from agora3.voice_context import Transcript, configuration, spoken_chunks
from agora3.voice_session import VoiceSession
from agora3.world import Refusal


def until(predicate):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Timed out")


class Connection:
    sdp = "answer"

    def __init__(self):
        self.incoming = queue.Queue()
        self.incoming.put({"type": "session.started"})
        self.sent = []
        self.disconnected = self.hung_up = False

    def send(self, event):
        self.sent.append(event)
        if event["type"] == "session.close":
            self.incoming.put({"type": "session.closed", "usage": {"seconds": 2}})

    def receive(self, timeout=0.02):
        try:
            return self.incoming.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError from None

    def hangup(self):
        self.hung_up = True

    def disconnect(self):
        self.disconnected = True


def fragment(text, identifier="f1"):
    return {"type": "session.input_transcript.delta", "event_id": identifier, "delta": text}


def delegation(identifier="d1"):
    return {
        "type": "session.delegation.created",
        "delegation": {"id": identifier, "target": "client"},
    }


def test_config_restricts_browser_and_preserves_history():
    config = configuration("JEFF", [{"role": "user", "text": "Earlier question"}])
    assert config["model"] == "gpt-live-1"
    assert config["audio"]["output"]["voice"] == "stone"
    assert config["store"] is False
    assert config["delegation"] == {"type": "client"}
    assert config["input"][0]["content"][0]["text"] == "Earlier question"
    assert (
        "session.commentary.append" not in config["client"]["data_channel"]["allowed_client_events"]
    )


def test_transcripts_are_durable_bounded_and_not_redelegated():
    saved = []
    transcript = Transcript(lambda role, text: saved.append((role, text)))
    transcript.append(fragment("Open my note"))
    assert "Open my note" in transcript.request()
    assert transcript.request() is None
    transcript.append(fragment("Actually, just read it"))
    assert "through sequence 1 were already sent" in transcript.request()
    assert len(saved) == 2
    for _ in range(3000):
        transcript.append(fragment("a"))
    assert len(transcript.request()) < 30000
    assert len(transcript.rows) <= 1000
    assert all(len(chunk.encode()) <= 450 for chunk in spoken_chunks("🗣️" * 1000))


def test_steering_is_pinned_to_active_turn_and_never_retries(tmp_path):
    jeff = Jeff(tmp_path, lambda *_: {}, lambda: [])
    calls = []
    jeff._client = SimpleNamespace(
        turn_steer=lambda *args: calls.append(args) or SimpleNamespace(turn_id="turn")
    )
    assert jeff.steer("wait") is False
    jeff._thread, jeff._turn, jeff._accept_calls = "resident", "turn", True
    assert jeff.steer("Read only") is True
    assert calls == [("resident", "turn", [{"type": "text", "text": "Read only"}])]
    jeff.cancel()
    with pytest.raises(Refusal, match="stopping"):
        jeff.steer("More")
    assert len(calls) == 1


def test_delegation_deduplication_confirmation_and_transcript_replay(tmp_path):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    session = VoiceSession(app, actor, "browser-client-1", "jeff")
    connection = Connection()
    calls = []
    app.voice_request = lambda request, actor: calls.append(request) or "activity"
    app.backend_snapshot = lambda activity=None: {
        "id": "activity",
        "running": False,
        "reply": "Read confirmed.",
        "error": None,
    }
    session.attach(connection)
    connection.incoming.put(fragment("Read the note"))
    connection.incoming.put(fragment("Read the note"))
    connection.incoming.put(delegation())
    connection.incoming.put(delegation())
    until(lambda: any(e["type"] == "session.commentary.append" for e in connection.sent))
    session.close()
    assert session.done.wait(3)
    assert len(calls) == 1
    assert session.confirmed_closed and connection.disconnected and not connection.hung_up
    assert session.seconds == 2
    assert app.chat_status()["messages"][0]["text"] == "Read the note"
    assert app.chat_status()["messages"][0]["source"] == "voice"
    assert app.gateway.world.verify()["ok"]


def test_revoke_closes_call_and_rejects_late_transcripts(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "browser-client-1", "jeff")
    connection = Connection()
    session.attach(connection)
    app.gateway.revoke()
    assert session.done.wait(3)
    assert session.confirmed_closed
    with pytest.raises(Refusal):
        session.record("user", "late")
    assert not app.chat_status()["messages"]


def test_start_race_owner_and_missing_credentials(tmp_path, monkeypatch):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    monkeypatch.setenv("AGORA_VOICE_API_KEY", "test-only-secret")
    connecting, proceed = threading.Event(), threading.Event()
    connection = Connection()

    def connect(*_):
        connecting.set()
        assert proceed.wait(3)
        return connection

    app.voice.connect = connect
    errors = []

    def start():
        try:
            app.voice.start(actor, "browser-client-1", "v=0\r\n")
        except Refusal as exc:
            errors.append(str(exc))

    thread = threading.Thread(target=start)
    thread.start()
    assert connecting.wait(3)
    with pytest.raises(Refusal, match="already active"):
        app.voice.start(actor, "browser-client-2", "v=0\r\n")
    with pytest.raises(Refusal, match="browser that started"):
        app.voice.end("browser-client-2")
    app.voice.end("browser-client-1")
    proceed.set()
    thread.join(3)
    assert errors and "cancelled" in errors[0]
    assert app.voice.session.done.wait(3)
    assert "secret" not in str(app.voice.status("browser-client-1"))


def test_authored_surface_cannot_start_voice(tmp_path):
    app = Application(tmp_path)
    with pytest.raises(Refusal, match="independent human"):
        app.dispatch("guest", "host.voice.start", {})


def test_transport_failure_preserves_reason_without_payloads(tmp_path, caplog):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "test-diagnostics", "jeff")
    connection = Connection()

    def fail_receive(*args, **kwargs):
        raise OSError("private-key-and-transcript-must-not-be-logged")

    connection.receive = fail_receive
    session.attach(connection)
    assert session.done.wait(3)
    assert session.failure["exception"] == "OSError"
    assert session.failure["phase"] == "receiving voice events"
    assert connection.hung_up and connection.disconnected
    assert "private-key" not in caplog.text
    assert "Voice failure" in caplog.text


def test_result_delivery_failure_retains_its_send_phase(tmp_path):
    app = Application(tmp_path)
    session = VoiceSession(app, app.gateway.principal("human"), "test-diagnostics", "jeff")
    connection = Connection()

    def fail_send(event):
        raise OSError("private content")

    connection.send = fail_send
    session.connection = connection
    with pytest.raises(OSError):
        session.send("session.commentary.append", content="private result")
    assert session.failure["phase"] == "sending session.commentary.append"
    assert "private" not in str(session.status())
