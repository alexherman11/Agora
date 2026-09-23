"""The transport exposes complete progress during work without persisting it as a reply."""
import threading

from agora3.server import Application


def test_progress_survives_poll_gaps_then_final_is_recorded_once(tmp_path, monkeypatch):
    app = Application(tmp_path)
    ready, finish = threading.Event(), threading.Event()

    class Agent:
        def send(self, message, observe):
            for _ in range(350):
                observe({"type": "text.delta", "id": "p", "text": "a"})
            observe({"type": "text.completed", "id": "p", "phase": "commentary", "text": "Working."})
            observe({"type": "text.delta", "id": "f", "text": "Done."})
            observe({"type": "text.completed", "id": "f", "phase": "final_answer", "text": "Done."})
            ready.set()
            assert finish.wait(5)
            return "Done."

    app.jeff_identity = app.gateway.principal("jeff")
    monkeypatch.setattr(app, "_agent", lambda: Agent())
    app.send("Work", app.gateway.principal("human"))
    try:
        assert ready.wait(5)
        status = app.chat_status()
        assert status["running"]
        assert [m["text"] for m in status["activity"]["messages"]] == ["Working.", "Done."]
        assert [m["role"] for m in status["messages"]] == ["user"]
    finally:
        finish.set()
        for thread in threading.enumerate():
            if thread.name == "agora-jeff":
                thread.join(5)
    status = app.chat_status()
    assert not status["running"]
    assert [m["text"] for m in status["messages"]] == ["Work", "Done."]
