"""Runtime callbacks and history stay reachable during a follow-up."""

import threading
from types import SimpleNamespace

import pytest

from agora3.server import Application


@pytest.mark.parametrize("route", ["text", "voice", "worker"])
def test_steering_allows_runtime_callback_and_history(tmp_path, route):
    app = Application(tmp_path)
    actor = app.gateway.principal("human")
    app.running = True
    app.work = True
    activity_id = app.activity.id
    callback_done = threading.Event()

    def steer(message):
        def callback():
            # The SDK reader must be able to deliver this before steering returns.
            app.backend_snapshot()
            callback_done.set()

        thread = threading.Thread(target=callback, daemon=True)
        thread.start()
        assert callback_done.wait(2), "Steering held the callback/history lock"
        thread.join(2)
        return True

    app.jeff = SimpleNamespace(steer=steer)
    if route == "text":
        assert app.send("Follow-up", actor)["activity_id"] == activity_id
    elif route == "voice":
        assert app.voice_request("Follow-up", actor) == activity_id
    else:
        assert app.worker_update("Follow-up")
    assert callback_done.is_set()
