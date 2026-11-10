"""Notification decisions do not require live model calls."""

import pytest
from desk_notifier import deliver


def test_quiet_and_repeated_polls_never_notify():
    calls = []
    send = lambda cfg, ids: calls.append(ids)  # noqa: E731
    sent, changed = deliver({}, [], [], send)
    assert not changed and not calls
    sent, changed = deliver({}, [{"id": "e1"}, {"id": "e2"}], sent, send)
    assert changed and calls == [["e1", "e2"]]
    sent, changed = deliver({}, [{"id": "e1"}, {"id": "e2"}], sent, send)
    assert not changed and len(calls) == 1
    sent, changed = deliver({}, [{"id": "e2"}, {"id": "e3"}], sent, send)
    assert changed and calls[-1] == ["e3"]


def test_failed_delivery_remains_unnotified():
    sent = ["e1"]

    def failing(cfg, ids):
        raise RuntimeError("app unavailable")

    with pytest.raises(RuntimeError, match="app unavailable"):
        deliver({}, [{"id": "e2"}], sent, failing)
    assert sent == ["e1"]
