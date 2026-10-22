"""Durable resident input handoffs with disposable state and fake pipes only."""
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import house  # noqa: E402
import image_comments  # noqa: E402


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    world = SimpleNamespace(
        nodes={"r1": {"props": {"provider": "codex", "actor": "pike"}}},
        find_line=lambda mid: (None, None),
    )
    h = house.House.__new__(house.House)
    h.dir, h.world, h.fake = tmp_path, "delivery-fixture", False
    h.load = lambda: world
    h.welcome_for = lambda r: ""
    h.act = Mock(side_effect=AssertionError("no native world writes in delivery fixture"))
    monkeypatch.setattr(house, "clean_env", lambda _: {})
    monkeypatch.setattr(house.charter, "collect", lambda *args: "fixture charter")
    monkeypatch.setattr(house.threading, "Thread", Mock())
    monkeypatch.setattr(image_comments, "content", lambda world, refs: [
        {"type": "text", "text": "image evidence: " + ",".join(refs)}])

    def popen(*args, **kwargs):
        kwargs["stderr"].close()
        return SimpleNamespace(stdin=io.StringIO(), pid=123, poll=lambda: None)

    monkeypatch.setattr(house.subprocess, "Popen", Mock(side_effect=popen))
    r = house.Resident(h, "r1")
    r.state = {"session": "preserved-conversation", "session_provider": "codex",
               "charter_text": "fixture charter"}
    r.proc = SimpleNamespace(stdin=io.StringIO())
    return h, r


def restore(h):
    r = house.Resident(h, "r1")
    r.start("fixture-model")
    return r


def test_restart_after_take_preserves_order_and_attachment_references(delivery):
    h, r = delivery
    r.state.update(calls=[{"by": "alex", "text": "Alex called"}],
                   for_you=[{"by": "alex", "text": "Please finish keyboard support"}],
                   inbox=["Also check focus", "Use the light theme"],
                   image_comments=["c1"], message_contexts=["m1"])
    r.save()
    taken = h.take(r)
    disk = json.loads(r.state_path.read_text())
    assert not disk.get("inbox") and not disk.get("calls") and not disk.get("for_you")
    assert disk["handoff"]["carry"] == "\n".join(taken)
    assert disk["handoff"]["image_comments"] == ["c1"]
    assert disk["handoff"]["message_contexts"] == ["m1"]
    restarted = restore(h)
    assert restarted.state["undelivered"] == "\n".join(taken)
    assert restarted.state["image_comments"] == ["c1"]
    assert restarted.state["message_contexts"] == ["m1"]
    assert "handoff" not in restarted.state
    again = restore(h)
    assert again.state["undelivered"] == restarted.state["undelivered"]
    assert again.state["message_contexts"] == ["m1"]


def test_first_is_durable_even_if_wake_fails_before_take(delivery):
    h, r = delivery
    r.state.update(calls=[{"by": "alex", "text": "Please resume"}],
                   for_you=[{"by": "pike", "text": "The blocker is resolved"}])
    r.save()
    first = h.first(r)
    restarted = restore(h)
    assert restarted.state["undelivered"] == "\n".join(first)
    assert "blocker is resolved" in restarted.state["undelivered"]


def test_wake_stages_recovered_text_before_any_news_side_effect(delivery):
    h, r = delivery
    r.state["undelivered"] = "Earlier request never reached the pipe"
    r.state["message_contexts"] = ["m1"]
    r.save()

    def crash_after_news_save(*args, **kwargs):
        r.save()
        raise RuntimeError("crash before send")

    h.news = crash_after_news_save
    with pytest.raises(RuntimeError, match="crash before send"):
        h.wake(r, {"props": {}}, "pike", "")
    restarted = restore(h)
    assert restarted.state["undelivered"] == "Earlier request never reached the pipe"
    assert restarted.state["message_contexts"] == ["m1"]


def test_success_replaces_handoff_without_replaying_delivered_batch(delivery):
    h, r = delivery
    r.state.update(inbox=["First request", "Second request"], message_contexts=["m1"])
    batch = h.take(r)
    r.send("\n".join(batch))
    assert "handoff" not in r.state
    assert r.state["pending"]["delivered"]
    assert r.state["pending"]["message_contexts"] == ["m1"]
    restarted = restore(h)
    assert restarted.state["unanswered"] == 1
    assert not restarted.state.get("undelivered")
    assert not restarted.state.get("message_contexts")
    assert restarted.state["session"] == "preserved-conversation"


def test_pipe_failure_recovers_text_and_attachments(delivery):
    h, r = delivery
    r.state.update(inbox=["Please inspect this capture"], image_comments=["c1"],
                   message_contexts=["m1"])
    batch = h.take(r)
    r.proc.stdin.close()
    r.send("\n".join(batch))
    assert not r.state["pending"].get("delivered")
    assert "handoff" not in r.state
    restarted = restore(h)
    assert restarted.state["undelivered"] == "Please inspect this capture"
    assert restarted.state["image_comments"] == ["c1"]
    assert restarted.state["message_contexts"] == ["m1"]


def test_new_batch_cannot_overwrite_previous_unsent_batch(delivery):
    h, r = delivery
    r.state.update(inbox=["First request"], message_contexts=["m1"])
    first = h.take(r)
    r.proc.stdin.close()
    r.send("\n".join(first))
    r.state.update(inbox=["Second request"], message_contexts=["m2"])
    second = h.take(r)
    r.proc.stdin = io.StringIO()
    r.send("\n".join(second))
    pending = r.state["pending"]
    assert pending["carry"] == "First request\nSecond request"
    assert pending["message_contexts"] == ["m1", "m2"]
    sent = json.loads(r.proc.stdin.getvalue())["message"]["content"][0]["text"]
    assert sent.index("First request") < sent.index("Second request")
    assert pending["delivered"]


def test_lost_conversation_replays_delivered_input_with_attachments_in_fresh_session(delivery):
    h, r = delivery
    r.state.update(inbox=["Inspect the screenshot and selection"], image_comments=["c1"],
                   message_contexts=["m1"])
    r.send("\n".join(h.take(r)))
    assert r.state["pending"]["delivered"]
    r.alive = lambda: False
    r.lost_conversation = lambda: True
    h.failed(r, {"props": {}}, {"detail": "saved conversation no longer exists"})
    assert "session" not in r.state
    assert r.state["lost"]
    restarted = restore(h)
    assert restarted.state["undelivered"] == "Inspect the screenshot and selection"
    assert restarted.state["image_comments"] == ["c1"]
    assert restarted.state["message_contexts"] == ["m1"]
    text = restarted.state.pop("undelivered")
    restarted.send(text)
    payload = json.loads(restarted.proc.stdin.getvalue())["message"]["content"]
    assert any("image evidence: c1" in block.get("text", "") for block in payload)
    assert any("m1: saved context" in block.get("text", "") for block in payload)
    assert restarted.state["pending"]["message_contexts"] == ["m1"]
