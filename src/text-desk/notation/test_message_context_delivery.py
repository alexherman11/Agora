"""House delivery with saved state and mocked model pipes; no model is launched."""

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import house
import message_context
import roomworld
from test_message_context import png


@pytest.fixture
def delivery(tmp_path, monkeypatch):
    desk, ids = roomworld.build()
    w = desk.world
    owner = w.nodes[ids.NOTE]["subject"]
    capture = {
        "id": "cap-1",
        "by": "alex",
        "session": "frontier",
        "at": "2026-10-14T10:00:00",
        "refs": [
            {
                "world": "frontier",
                "item": ids.NOTE,
                "subject": owner,
                "kind": "note",
                "role": "document",
                "words": "Selected source words",
                "rev": w.nodes[ids.NOTE]["rev"],
            }
        ],
        "image": png(),
    }
    saved = message_context.resolve(
        "frontier", "alex", json.dumps({"version": 1, "captures": [capture]})
    )
    h = house.House.__new__(house.House)
    h.world, h.dir, h.claude, h.fake = "frontier", tmp_path, "mock-model-process", False
    h.load = lambda: w
    h.welcome_for = lambda _: "Welcome"
    # Charter startup now reports a receipt. This fixture owns only in-memory
    # delivery, so it must never route that report to the real Frontier world.
    h.act = Mock(return_value="fixture charter receipt")
    monkeypatch.setattr(house.desk_mcp, "run_desk", Mock(
        side_effect=AssertionError("delivery fixture attempted a real Desk call")))

    def popen(*args, **kwargs):
        # Close the real temporary stderr handle; this is only a fake process.
        kwargs["stderr"].close()
        return SimpleNamespace(stdin=io.StringIO(), pid=123, poll=lambda: None)

    monkeypatch.setattr(house.subprocess, "Popen", Mock(side_effect=popen))
    monkeypatch.setattr(house.threading, "Thread", Mock())
    monkeypatch.setattr(house, "clean_env", lambda _: {})

    def resident(actor, cursor=None):
        r = house.Resident(h, ids.corner[actor])
        r.state.setdefault("session", "existing-conversation")
        if cursor is not None:
            r.state["cursor"] = cursor
        r.proc = SimpleNamespace(stdin=io.StringIO())
        return r

    def append(parent=None):
        chat = w.add_subject("chat", "Capture conversation")
        w.subjects[chat]["lines"] = []
        w.place(chat, parent or w.root, 0, 0, 100, 100)
        cursor = len(w.events)
        w.apply(
            "append",
            chat,
            None,
            {"line": "Please inspect this", "to": "pike", "context": saved},
            "alex",
        )
        return chat, w.subjects[chat]["lines"][-1]["id"], cursor

    return h, w, ids, saved, resident, append


@pytest.mark.parametrize("in_other_corner", [False, True])
def test_only_addressed_resident_queues_once(delivery, in_other_corner):
    h, w, ids, _, resident, append = delivery
    _, mid, cursor = append(ids.corner["juniper"] if in_other_corner else None)
    for actor in ("pike", "juniper", "sable"):
        r = resident(actor, cursor)
        h.news(w, r, actor, resting=False)
        h.news(w, r, actor, resting=False)
        assert r.state.get("message_contexts", []) == ([mid] if actor == "pike" else [])
        r.save()
        assert house.Resident(h, r.rid).state.get("message_contexts", []) == r.state.get(
            "message_contexts", []
        )


def test_send_builds_real_image_blocks_and_pending_contains_only_ids(delivery):
    h, w, _, saved, resident, append = delivery
    _, mid, cursor = append()
    r = resident("pike", cursor)
    h.news(w, r, "pike")
    r.send("A message addressed to you")
    blocks = json.loads(r.proc.stdin.getvalue())["message"]["content"]
    assert len([b for b in blocks if b["type"] == "image"]) == 1
    assert blocks[-1]["source"]["data"] == png()["data"]
    assert "Selected source words" in " ".join(b.get("text", "") for b in blocks)
    assert r.state["pending"]["message_contexts"] == [mid]
    assert r.state["pending"]["delivered"] is True
    assert saved not in r.state_path.read_text(encoding="utf-8")
    assert png()["data"] not in r.state_path.read_text(encoding="utf-8")


def test_failed_pipe_survives_real_state_reload_and_start(delivery):
    h, w, _, _, resident, append = delivery
    _, mid, cursor = append()
    r = resident("pike", cursor)
    h.news(w, r, "pike")
    r.proc.stdin = Mock(write=Mock(side_effect=BrokenPipeError("closed")))
    r.send("Please inspect this")
    assert not r.state["pending"].get("delivered")
    restarted = house.Resident(h, r.rid)
    restarted.start("mock-model")
    assert restarted.state["message_contexts"] == [mid]
    assert restarted.state["undelivered"] == "Please inspect this"
    restarted.send(restarted.state.pop("undelivered"))
    assert restarted.state["pending"]["delivered"] is True
    assert (
        len(
            [
                b
                for b in json.loads(restarted.proc.stdin.getvalue())["message"]["content"]
                if b["type"] == "image"
            ]
        )
        == 1
    )


@pytest.mark.parametrize("keep_conversation", [True, False])
def test_delivered_restart_requeues_only_if_conversation_lost(delivery, keep_conversation):
    h, w, _, _, resident, append = delivery
    _, mid, cursor = append()
    r = resident("pike", cursor)
    h.news(w, r, "pike")
    r.send("A delivered message")
    if not keep_conversation:
        r.state.pop("session")
        r.save()
    restarted = house.Resident(h, r.rid)
    restarted.start("mock-model")
    assert restarted.state.get("message_contexts", []) == ([] if keep_conversation else [mid])
    assert restarted.state.get("unanswered", 0) == (1 if keep_conversation else 0)


def test_invalid_legacy_context_is_clear_and_does_not_break_send(delivery):
    h, w, _, _, resident, append = delivery
    chat, _, cursor = append()
    w.subjects[chat]["lines"][-1]["fields"]["context"] = "legacy arbitrary text"
    r = resident("pike", cursor)
    h.news(w, r, "pike")
    r.send("Look at this")
    blocks = json.loads(r.proc.stdin.getvalue())["message"]["content"]
    assert "unavailable" in blocks[-1]["text"]
    assert all(b["type"] == "text" for b in blocks)


def test_summary_labels_captured_words_without_base64_and_is_bounded(delivery):
    _, _, _, saved, _, _ = delivery
    text = message_context.summary(saved)
    assert "cap-1" in text and "2026-10-14" in text
    assert "note / document" in text and "frontier/a" in text
    assert "Captured words: Selected source words" in text
    assert "Captured image: PNG 1×1" in text
    assert png()["data"] not in text
    assert "unchanged" not in text and "changed" not in text
    large = json.loads(saved)
    large["captures"][0]["refs"] *= 64
    assert len(message_context.summary(json.dumps(large))) <= 6000
    assert message_context.summary("old arbitrary value").startswith("Context unavailable:")
