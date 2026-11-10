"""Captured selections survive edits/removal without silently becoming live text."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import context
from world import Refusal, World


@pytest.fixture
def native():
    w = World()
    sid = w.add_subject("task", "Test the design", "First draft.\nA selected passage.")
    aid = w.place(sid, w.root, 0, 0, 100, 100)
    w.subjects[sid]["props"]["status"] = "open"
    return w, sid, aid


def test_capture_is_detached_and_current_is_separate(native):
    w, sid, aid = native
    saved = context.capture(w, [{"ref": aid, "quote": "A selected passage."}])
    original = copy.deepcopy(saved)
    w.apply("edit", sid, w.subjects[sid]["rev"], {"text": "Second draft."}, "alex")
    w.subjects[sid]["props"]["status"] = "done"
    rendered = context.describe(w, saved)
    assert saved == original
    assert "A selected passage." in rendered
    assert '"status":"changed"' in rendered
    assert "Second draft." not in rendered
    assert saved["items"][0]["fields"]["status"] == "open"
    del w.nodes[aid]
    assert '"status":"unavailable"' in context.describe(w, saved)
    assert saved == original


def test_appearance_identity_not_only_equal_words(native):
    w, sid, aid = native
    saved = context.capture(w, [aid])
    other = w.add_subject("task", "Test the design", w.subjects[sid]["text"])
    w.nodes[aid]["subject"] = other
    assert "different subject" in context.describe(w, saved)


def test_comment_and_line_sources(native):
    w, sid, _ = native
    cid = w.add_comment(sid, "alex", "Please check this.")
    chat = w.add_subject("chat", "Conversation")
    w.subjects[chat]["lines"] = []
    w.apply(
        "append",
        chat,
        w.subjects[chat]["rev"],
        {"line": "A clear reply.", "quote": "example"},
        "rowan",
    )
    line = w.subjects[chat]["lines"][-1]
    saved = context.capture(w, [cid, line["id"]])
    assert [i["kind"] for i in saved["items"]] == ["comment", "line"]
    assert saved["items"][1]["fields"]["by"] == "rowan"
    assert saved["items"][1]["fields"]["quote"] == "example"
    w.find_comment(cid)[1]["replies"].append({"by": "rowan", "text": "Checked."})
    assert '"status":"changed"' in context.describe(w, saved)
    assert "Checked." not in context.describe(w, saved)


def test_bounds_and_full_source_change_detection(native):
    w, sid, _ = native
    w.subjects[sid]["text"] = "x" * 20000 + "selected tail"
    saved = context.capture(w, [{"ref": sid, "quote": "selected tail"}])
    assert saved["items"][0]["truncated"] is True
    assert len(saved["items"][0]["text"]) == context.MAX_TEXT
    assert saved["items"][0]["quote"] == "selected tail"
    assert '"status":"unchanged"' in context.describe(w, saved)
    w.subjects[sid]["text"] += " changed beyond the retained prefix"
    assert '"status":"changed"' in context.describe(w, saved)


@pytest.mark.parametrize(
    "selection", ["a999999", "https://example.com", "../../secret", {"ref": "s01", "other": "x"}]
)
def test_invalid_reference_and_selection_are_read_only(native, selection):
    w, _, _ = native
    before = copy.deepcopy(vars(w))
    with pytest.raises(Refusal):
        context.capture(w, [selection])
    assert vars(w) == before


@pytest.mark.parametrize("quote", ["not in the source", "", "x" * 2001, 7])
def test_quote_must_come_from_source(native, quote):
    w, sid, _ = native
    with pytest.raises(Refusal):
        context.snapshot(w, sid, quote=quote)


def test_envelope_validation_and_json_roundtrip(native):
    w, sid, _ = native
    saved = context.capture(w, [sid])
    restored = context.validate(json.loads(json.dumps(saved)))
    restored["items"][0]["fields"]["status"] = "edited externally"
    assert saved["items"][0]["fields"]["status"] == "open"
    for key, bad in [
        ("revision", True),
        ("text", "x" * 8001),
        ("digest", "bogus"),
        ("fields", {"x": []}),
        ("truncated", 1),
        ("event", "anything"),
    ]:
        changed = copy.deepcopy(saved)
        changed["items"][0][key] = bad
        with pytest.raises(Refusal):
            context.validate(changed)
    with pytest.raises(Refusal):
        context.capture(w, [sid] * 9)
    with pytest.raises(Refusal):
        context.capture(w, [])


def test_native_context_note_does_not_recursively_follow_references(native):
    w, sid, _ = native
    note = w.add_subject("note", "Captured context", json.dumps({"refs": [sid]}))
    w.subjects[note]["props"].update(role="context", optionalimage="a99999")
    saved = context.capture(w, [note])
    assert saved["items"][0]["fields"]["optionalimage"] == "a99999"
    assert "A selected passage." not in context.describe(w, saved)
