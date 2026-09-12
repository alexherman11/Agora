"""Active event traffic survives missing pongs; silent or closed links stay bounded."""

import json
import threading
import time
from types import SimpleNamespace

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.frames import OP_PONG
from websockets.sync.client import connect
from websockets.sync.server import ServerConnection, serve

from agora3 import voice_transport
from agora3.world import Refusal


@pytest.mark.parametrize("legacy", [True, False])
def test_live_events_without_pongs(monkeypatch, legacy):
    dropped = threading.Event()

    class NoPong(ServerConnection):
        def __init__(self, sock, protocol, **kwargs):
            original = protocol.send_frame

            def send_frame(frame):
                if frame.opcode == OP_PONG:
                    dropped.set()
                else:
                    original(frame)

            protocol.send_frame = send_frame
            super().__init__(sock, protocol, **kwargs)

    def stream(ws):
        try:
            for _ in range(40):
                ws.send(json.dumps({"type": "session.input_transcript.delta"}))
                time.sleep(0.01)
        except ConnectionClosed:
            pass

    with serve(stream, "127.0.0.1", 0, create_connection=NoPong, ping_interval=None) as server:
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        port = server.socket.getsockname()[1]
        monkeypatch.setattr(
            voice_transport,
            "post",
            lambda *a: {"session": {"id": "test"}, "transport": {"sdp": "answer"}},
        )

        def attach(url, **kwargs):
            kwargs["ping_interval"] = 0.04
            if legacy:
                kwargs["ping_timeout"] = 0.04
            return connect(f"ws://127.0.0.1:{port}", **kwargs)

        monkeypatch.setattr(voice_transport, "connect", attach)
        transport = voice_transport.LiveConnection("test-only", {}, "offer")
        count = 0
        try:
            while True:
                transport.receive()
                count += 1
        except ConnectionClosed as exc:
            if legacy:
                assert exc.sent.reason == "keepalive ping timeout"
                assert count < 40
            else:
                assert count == 40
                assert exc.rcvd.code == 1000
        finally:
            transport.disconnect()
        assert dropped.is_set()
        server.shutdown()
        worker.join(2)


def test_silent_sideband_has_deadline(monkeypatch):
    transport = voice_transport.LiveConnection.__new__(voice_transport.LiveConnection)
    transport._last_received = 0

    def silent(**kwargs):
        raise TimeoutError

    transport.socket = SimpleNamespace(recv=silent)
    monkeypatch.setattr(voice_transport.time, "monotonic", lambda: 119)
    with pytest.raises(TimeoutError):
        transport.receive()
    monkeypatch.setattr(voice_transport.time, "monotonic", lambda: 120)
    with pytest.raises(Refusal, match="120 seconds"):
        transport.receive()
