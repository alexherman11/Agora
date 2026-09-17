"""Closure causes survive cleanup without retaining speech or provider messages."""

from websockets.exceptions import ConnectionClosedError
from websockets.frames import Close

from agora3.server import Application
from agora3.voice_session import VoiceSession
from agora3.voice_transport import LiveConnection


def session_at(path):
    app = Application(path)
    return VoiceSession(app, app.gateway.principal("human"), "diagnostic-test-client", "jeff")


def test_provider_close_reason_and_usage(tmp_path):
    session = session_at(tmp_path)
    session.handle({"type": "session.closed", "reason": "expired", "usage": {"seconds": 52}})
    session.close()
    assert session.confirmed_closed and session.seconds == 52
    assert session.status()["close_reason"] == "expired"


def test_provider_error_excludes_reflected_private_content(tmp_path):
    session = session_at(tmp_path)
    session.handle({"type": "error", "error": {
        "code": "unknown_parameter", "type": "invalid_request_error",
        "param": "session.voice", "message": "private transcript and key",
    }})
    assert session.close_reason == "provider_error"
    assert session.provider_error["code"] == "unknown_parameter"
    assert "private" not in str(session.status())


def test_ping_failure_survives_later_cleanup_failure(tmp_path):
    session = session_at(tmp_path)
    session.failed(ConnectionClosedError(None, Close(1011, "keepalive ping timeout")), "receive")
    session.failed(OSError("private cleanup error"), "cleanup")
    assert session.failure["phase"] == "receive"
    assert session.failure["sent_close_reason"] == "keepalive ping timeout"


def test_heartbeat_timeout_is_distinct_from_transport_failure(tmp_path):
    session = session_at(tmp_path)
    session.last_seen -= 31
    session.tick()
    assert session.close_reason == "browser_heartbeat_timeout"
    session.connection = type("Connection", (), {"policy": LiveConnection.policy})()
    assert session.status()["transport"]["ping_timeout"] is None
