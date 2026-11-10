import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import listener_bridge
import pytest
import visual_event_listener as listener
from visual_event_listener import Changes, ingest, process


def test_quiet_and_self_events_do_not_wake(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"since": 10, "pending": {}, "handled": {}}))
    calls = []
    result = {
        "total": 12,
        "events": [
            {"id": "e90", "by": "codex/tool", "args": {"text": "@codex test"}},
            {"id": "e91", "by": "someone", "args": {"text": "@codex2 test"}},
        ],
    }
    process({}, path, lambda _: result, lambda *a: calls.append(a))
    assert calls == []
    assert json.loads(path.read_text())["since"] == 12


def test_failure_keeps_pending_and_retry_delivers_once(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"since": 10, "pending": {}, "handled": {}}))
    event = {"id": "e400", "by": "designer", "args": {"text": "@codex try this"}}

    def fail(*args):
        raise OSError("bridge unavailable")

    with pytest.raises(OSError):
        process({"thread": "test"}, path, lambda _: {"total": 11, "events": [event]}, fail)
    state = json.loads(path.read_text())
    assert state["since"] == 11
    assert "e400" in state["pending"]
    assert not state.get("notified")
    calls = []
    for _ in range(2):
        process(
            {"thread": "test"},
            path,
            lambda _: {"total": 11, "events": []},
            lambda *a: calls.append(a),
        )
    assert len(calls) == 1
    assert "e400" in json.loads(path.read_text())["pending"]


def test_backward_count_preserves_state():
    state = {"since": 10, "pending": {}}
    with pytest.raises(RuntimeError):
        ingest(state, {"total": 9, "events": []})
    assert state == {"since": 10, "pending": {}}


def test_saved_reply_address_reaches_codex_without_mention():
    state = {"since": 0, "pending": {}}
    events = [
        {
            "id": "e1",
            "verb": "comment",
            "by": "alex",
            "to": ["codex"],
            "args": {"line": "Please fix this"},
        },
        {
            "id": "e2",
            "verb": "comment",
            "by": "alex",
            "to": ["rowan"],
            "args": {"line": "Not for Codex"},
        },
        {"id": "e3", "verb": "comment", "by": "alex", "to": ["codex"], "undone": True},
    ]
    ingest(state, {"total": 3, "events": events})
    assert list(state["pending"]) == ["e1"]


def test_house_knock_record_makes_its_line_pending_once():
    """a5267: the house's knock record saying codex was knocked pends the line it names (its cause), once; a record
    that says codex was not knocked (not a member) pends nothing."""
    state = {"since": 0, "pending": {}, "handled": {"e7": "done"}}
    events = [
        {"id": "e5", "verb": "append", "by": "alex", "args": {"append": "a line with to=codex stored", "to": "codex"}},
        {"id": "e6", "verb": "knock", "by": "house", "cause": "e5", "args": {"codex": "knocked: their listener ..."}},
        {"id": "e8", "verb": "knock", "by": "house", "cause": "e7", "args": {"codex": "knocked: their listener ..."}},
        {"id": "e9", "verb": "knock", "by": "house", "cause": "e4", "args": {"codex": "not a member, not knocked"}},
    ]
    ingest(state, {"total": 4, "events": events})
    assert list(state["pending"]) == ["e5"]
    ingest(state, {"total": 5, "events": [dict(events[1], id="e10")]})
    assert list(state["pending"]) == ["e5"]


def test_publish_writes_the_row_only_when_it_changes(tmp_path, monkeypatch):
    """a5267: the witnessed row listener-codex says what was handed to the chat; unchanged, it is not rewritten."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
    import witnessed

    monkeypatch.setattr(witnessed, "ROOT", witnessed.ROOT)          # put back after: publish points it at WORLD's
    monkeypatch.setattr(listener, "WORLD", tmp_path / "sessions" / "t.pickle")
    monkeypatch.setattr(listener, "_published", [None])
    listener.publish({"notified": ["e10", "e9"]})
    assert witnessed.ROOT == tmp_path / "house-state"
    doc = witnessed.read("t", "listener-codex")
    assert doc["rows"][0]["delivered"] == "e9 e10" and doc["rows"][0]["carries"] == "its Codex app chat"
    stamp = witnessed.stamp("t")
    time.sleep(0.02)
    listener.publish({"notified": ["e10", "e9"]})
    assert witnessed.stamp("t") == stamp
    listener.unpublish()
    assert witnessed.read("t", "listener-codex") is None


@pytest.mark.skipif(os.name != "nt", reason="Windows notification API")
def test_real_change_notification_and_rearm(tmp_path):
    changes = Changes([tmp_path])
    try:
        assert changes.wait(20) is None
        for i in range(2):
            writer = threading.Thread(
                target=lambda n=i: (tmp_path / f"change{n}").write_text("signal")
            )
            writer.start()
            assert changes.wait(2000) == 0
            writer.join()
        assert len(changes.handles) == 1
    finally:
        changes.close()


def test_app_reconnect_ignores_stale_and_untrusted_pipes(monkeypatch):
    monkeypatch.delenv(listener_bridge.PIPE_ENV, raising=False)
    calls = []
    config = {
        "thread": "same-chat",
        "pipe": listener_bridge.PIPE_ROOT + "gone",
        "bridge_executable_pattern": "C:/trusted/Codex.exe",
    }

    def owner(pipe):
        return "C:/other/Codex.exe" if pipe.endswith("a") else "C:/trusted/Codex.exe"

    candidate, pipe = listener_bridge.resolve(
        config,
        owner=owner,
        names=["unrelated", "codex-browser-use-a", "codex-browser-use-b"],
        call=lambda c, name, args: calls.append((c, name, args)),
    )
    assert pipe.endswith("-b")
    assert candidate["bridge_env"][listener_bridge.PIPE_ENV] == pipe
    assert len(calls) == 1 and calls[0][1] == "read_thread"
    assert calls[0][2]["threadId"] == "same-chat"


@pytest.mark.skipif(os.name != "nt", reason="Windows state/process lock")
def test_failed_delivery_retries_without_another_world_change(tmp_path, monkeypatch):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"since": 0, "pending": {}, "handled": {}}))
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"thread": "same-chat"}))
    world = tmp_path / "world.pickle"
    world.write_bytes(b"Only its stat is used")
    control = tmp_path / "control"
    for name, path in {
        "LOCAL": tmp_path,
        "STATE": state,
        "CONFIG": config,
        "STATUS": tmp_path / "status.json",
        "WORLD": world,
        "CONTROL": control,
    }.items():
        monkeypatch.setattr(listener, name, path)
    clock = [100.0]
    waits = []

    class Notifications:
        def __init__(self, directories):
            pass

        def wait(self, timeout):
            waits.append(timeout)
            if timeout == 0xFFFFFFFF:
                (control / "stop").write_text("finished")
            else:
                clock[0] += timeout / 1000

        def close(self):
            pass

    calls = []
    original = listener.process

    def send(*args):
        calls.append(args)
        if len(calls) == 1:
            raise OSError("app restarting")

    def process(config):
        return original(
            config,
            state,
            lambda since: {
                "total": 1,
                "events": []
                if since
                else [{"id": "e1", "by": "alex", "verb": "comment", "to": ["codex"]}],
            },
            send,
        )

    monkeypatch.setattr(listener, "Changes", Notifications)
    monkeypatch.setattr(listener.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(listener, "process", process)
    monkeypatch.setattr("sys.argv", ["listener", "run"])
    listener.main()
    saved = json.loads(state.read_text())
    assert waits == [2000, 0xFFFFFFFF]
    assert len(calls) == 2
    assert saved["since"] == 1 and saved["notified"] == ["e1"]
    assert "e1" in saved["pending"]


@pytest.mark.skipif(os.name != "nt", reason="Real Windows directory notifications")
def test_live_process_recovers_when_http_service_restarts(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"since": 0, "pending": {}, "handled": {}}))
    (tmp_path / "config.json").write_text(json.dumps({"thread": "fixture"}))
    (tmp_path / "world.pickle").write_bytes(b"stat only")
    (tmp_path / "control").mkdir()
    generation = [1]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            since = int(self.path.rsplit("=", 1)[1])
            payload = json.dumps(
                {
                    "total": generation[0],
                    "events": [
                        {"id": f"e{i}", "by": "alex", "verb": "comment", "to": ["codex"]}
                        for i in range(since + 1, generation[0] + 1)
                    ],
                }
            ).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_port
    server.server_close()  # Start with a real refused connection.
    source = f"""
import sys,json
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).parent)!r})
import visual_event_listener as l
p=Path({str(tmp_path)!r})
l.LOCAL=p;l.STATE=p/'state.json';l.CONFIG=p/'config.json'
l.STATUS=p/'status.json';l.CONTROL=p/'control';l.WORLD=p/'world.pickle'
l.URL='http://127.0.0.1:{port}/events?since='
original=l.process
def send(*args):
    with (p/'delivered').open('a') as f: f.write('sent\\n')
l.process=lambda c: original(c, state_path=l.STATE, send=send)
sys.argv=['listener','run']
l.main()
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", source], creationflags=subprocess.CREATE_NO_WINDOW
    )

    def wait_for(test):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            assert proc.poll() is None, "fixture listener exited"
            try:
                if test():
                    return
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            time.sleep(0.05)
        raise AssertionError("listener did not recover")

    def status_is(value):
        return json.loads((tmp_path / "status.json").read_text())["state"] == value

    active = None
    try:
        for count in (1, 2):
            wait_for(lambda: status_is("reconnecting"))
            generation[0] = count
            active = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            threading.Thread(target=active.serve_forever, daemon=True).start()
            wait_for(
                lambda expected=count: (
                    json.loads(state.read_text()).get("notified")
                    == [f"e{i}" for i in range(1, expected + 1)]
                )
            )
            wait_for(lambda: status_is("waiting_for_change"))
            if count == 1:
                active.shutdown()
                active.server_close()
                active = None
                (tmp_path / "world.pickle").write_bytes(b"new event during service restart")
        assert (tmp_path / "delivered").read_text().splitlines() == ["sent", "sent"]
        assert json.loads(state.read_text())["since"] == 2
    finally:
        (tmp_path / "control" / "stop").write_text("test complete")
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        if active:
            active.shutdown()
            active.server_close()
