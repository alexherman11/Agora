"""Reading is per person and bounded by what was displayed, independently of replies."""

from copy import deepcopy

import lens_ir
import pytest
import rooms
import roomworld
import scene
from world import Refusal


def thread():
    desk, ids = roomworld.build()
    w = desk.world
    w.me = "alex"
    sid = w.nodes[ids.NOTE]["subject"]
    w.apply("append", sid, None, {"line": "Test passage"}, "alex")
    w.apply("comment", sid, None, {"line": "Please review this", "to": "alex"}, "pike")
    c = w.subjects[sid]["comments"][-1]
    return desk, ids.NOTE, sid, c


def test_read_checkpoint_does_not_answer_or_consume_a_concurrent_reply():
    desk, aid, sid, c = thread()
    w = desk.world
    shown = w.events[-1]["id"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "Another detail", "to": "alex"}, "pike")
    later = w.events[-1]["id"]
    before = deepcopy(w.subjects[sid])
    w.apply("markread", sid, None, {"id": c["id"], "through": shown}, "alex")
    assert w.subjects[sid] == before  # Reading cannot invalidate an edit to the passage.
    assert rooms.thread_read_state(w, c, "alex") == ({1}, later)
    assert rooms.thread_read_state(w, c, "juniper") == ({0, 1}, later)
    assert rooms.thread_waiting(w, c, "alex") == {0, 1}
    row = scene.rows(desk, "comments:" + aid)[0]
    assert (row["unread"], row["unread_count"], row["reply_count"], row["latest"]) == (
        "no",
        1,
        1,
        later,
    )
    assert scene.rows(desk, "replies:" + aid)[0]["unread"] == "yes"
    w.apply("markread", sid, None, {"id": c["id"], "through": later}, "alex")
    checkpoint = w.events[-1]["id"]
    assert rooms.thread_read_state(w, c, "alex")[0] == set()
    w.undo(checkpoint)
    assert rooms.thread_read_state(w, c, "alex")[0] == {1}
    # Derived indexes rebuild from native state without a browser cache.
    restored = deepcopy(w)
    assert rooms.thread_read_state(restored, restored.find_comment(c["id"])[1], "alex")[0] == {1}


def test_invalid_read_is_atomic_and_native_lenses_can_author_open_behavior():
    desk, aid, sid, c = thread()
    w = desk.world
    before = deepcopy(w.events)
    with pytest.raises(Refusal):
        w.apply("markread", sid, None, {"id": c["id"], "through": "e999999"}, "alex")
    assert w.events == before
    source = f"""root : column, of comments:{aid}, each card
card : column
  fold "$by"
  on open do markread $item id=$cid through=$latest
  preview : text "$text", peek 3
  state : text "$reply_count replies · $unread_count unread", peek"""
    view = lens_ir.evaluate(desk, source)
    nodes = list(scene._walk(view))
    assert any(a["on"] == "open" and "markread" in a["line"] for n in nodes for a in n["acts"])
    assert any(n.get("peek") == 3 for n in nodes)
    scene.emit(view)
    assert any(n.get("paint", {}).get("peek") == 3 for n in scene._walk(scene.painter_view(view)))
    assert "markread" in w.verbs_for(aid)
