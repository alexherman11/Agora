"""Thread recipients, wake-up and receipts agree, without historical broadcast."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import house
import lens_ir
import rooms
import roomworld
import scene


def test_unaddressed_reply_wakes_original_partner_once_and_return_reaches_person():
    desk, ids = roomworld.build()
    w = desk.world
    sid = w.nodes[ids.NOTE]["subject"]
    w.apply("comment", sid, None, {"line": "@pike Question"}, "alex")
    cid = w.subjects[sid]["comments"][-1]["id"]
    w.apply("comment", sid, None, {"id": cid, "line": "@alex Passing observation"}, "juniper")
    cursor = len(w.events)
    result = w.apply(
        "comment", sid, None, {"id": cid, "line": "More detail without an address"}, "alex"
    )
    event = w.events[-1]
    assert event["to"] == ["pike"]
    assert "by alex" in result["note"]
    assert rooms.reached(w, event) == {"pike": "call"}
    h = house.House.__new__(house.House)
    for actor in ["pike", "juniper", "alex"]:
        r = SimpleNamespace(
            rid=rooms.corner_of(w, actor) or "missing", state={"cursor": cursor}, save=Mock()
        )
        assert h.news(w, r, actor, resting=True) == (actor == "pike")
        assert not h.news(w, r, actor, resting=True)
    w.apply("comment", sid, None, {"id": cid, "line": "I received that"}, "pike")
    event = w.events[-1]
    assert event["to"] == ["alex"]
    assert rooms.shown(w, w.subjects[sid], event["to"], "alex", comment=True)
    w.apply("comment", sid, None, {"id": cid, "line": "@juniper A specific question"}, "alex")
    assert w.events[-1]["to"] == ["juniper"]


def test_native_recipients_are_independent_of_document_metadata_and_saved_authoritatively():
    desk, ids = roomworld.build()
    w = desk.world
    aid = ids.NOTE
    sid = w.nodes[aid]["subject"]
    parent = w.nodes[aid]["parent"]
    w.nodes[parent]["props"].update(role="doc", by="juniper")
    w.apply("comment", sid, None, {"line": "Question without header", "to": "pike"}, "alex")
    cid = w.subjects[sid]["comments"][-1]["id"]
    w.apply("comment", sid, None, {"id": cid, "line": "Another detail"}, "alex")
    assert w.events[-1]["to"] == ["pike"]
    event = dict(w.events[-1], args={"id": cid, "line": "@juniper Later display text"})
    assert rooms.comment_to(event) == ["pike"]
    assert rooms.reached(w, event) == {"pike": "call"}
    event.pop("to")
    assert rooms.comment_to(event) == ["juniper"]


def test_explicit_native_address_overrides_header_and_can_suppress_delivery():
    desk, ids = roomworld.build()
    w = desk.world
    sid = w.nodes[ids.NOTE]["subject"]
    w.apply("comment", sid, None, {"line": "@juniper quoted context", "to": "pike,alex"}, "alex")
    c = w.subjects[sid]["comments"][-1]
    assert w.events[-1]["to"] == ["pike"]
    root = scene.rows(desk, "comments:" + ids.NOTE)[0]
    assert root["to"] == "pike"
    assert root["eid"] == w.events[-1]["id"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "@pike no call", "to": "nobody"}, "alex")
    assert w.events[-1]["to"] == []
    w.apply(
        "comment", sid, None, {"id": c["id"], "line": "One directed aside", "to": "juniper"}, "alex"
    )
    assert w.events[-1]["to"] == ["juniper"]
    aside = scene.rows(desk, "replies:" + ids.NOTE)[-1]
    assert aside["to"] == "juniper" and aside["eid"] == w.events[-1]["id"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "Back to the conversation"}, "alex")
    assert w.events[-1]["to"] == ["pike"]


def test_unaddressed_thread_acquires_only_first_partner_on_an_ordinary_task():
    desk, _ = roomworld.build()
    w = desk.world
    sid = w.add_subject("task", "Check a machine", "")
    w.apply("comment", sid, None, {"line": "A question"}, "alex")
    c = w.subjects[sid]["comments"][-1]
    w.apply("comment", sid, None, {"id": c["id"], "line": "I can help"}, "pike")
    assert w.events[-1]["to"] == ["alex"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "An observation"}, "juniper")
    w.apply("comment", sid, None, {"id": c["id"], "line": "Following up"}, "alex")
    assert w.events[-1]["to"] == ["pike"]


def test_world_authored_verb_and_lens_can_extend_native_replies_without_editor():
    desk, ids = roomworld.build()
    w = desk.world
    w.me = "alex"

    def command(line):
        result = desk.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        assert not result.get("error"), result
        return result

    # A world-authored word chooses its recipient. The platform knows no app or holder.
    command(f"look {w.root} :2")
    words = 'do comment $1 to=pike line="$2"'
    command(
        f"do create {w.root} kind=note title=askpike tags=verb on=house text={json.dumps(words)}"
    )
    command(f"read {ids.NOTE}")
    command(f'do askpike {ids.NOTE} "Can you check this?"')
    sid = w.nodes[ids.NOTE]["subject"]
    c = w.subjects[sid]["comments"][-1]
    assert w.events[-1]["to"] == ["pike"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "Checked"}, "pike")
    reply_event = w.events[-1]["id"]
    command(f"read {ids.NOTE}")
    command(f'do comment {ids.NOTE} id={c["id"]} line="Thank you"')
    assert w.events[-1]["to"] == ["pike"]
    rows = scene.rows(desk, "replies:" + ids.NOTE)
    assert rows[0]["thread"] == c["id"] and rows[0]["eid"] == reply_event
    assert rows[0]["to"] == "alex" and rows[0]["awaiting"] == "no"
    source = f'''root : column, of replies:{ids.NOTE}, each message
message : column
  address : text "$to $eid"
  answer : text "", commit explicit, on edit do comment $item id=$thread line="$value"'''
    view = lens_ir.evaluate(desk, source)
    assert any(n.get("text") == "alex " + reply_event for n in scene._walk(view))
    command(f"read {ids.NOTE}")
    receipt = command(f'do comment {ids.NOTE} id={c["id"]} to=nobody line="@juniper silent"')[
        "text"
    ]
    assert "to: nobody" in receipt and "to: juniper" not in receipt
    assert "to=<names>" in command(f"verbs {ids.NOTE}")["text"]


def test_explicit_recipient_and_thread_reply_do_not_wake_an_unrelated_corner_owner():
    desk, ids = roomworld.build()
    w = desk.world
    sid = w.add_subject("task", "Shared task", "")
    aid = w.place(sid, ids.corner["juniper"], 0, 0, 200, 100)
    w.apply(
        "comment", aid, None, {"line": "Private routing on a visible task", "to": "pike"}, "alex"
    )
    c = w.subjects[sid]["comments"][-1]
    assert rooms.reached(w, w.events[-1]) == {"pike": "call"}
    for args in [
        {"line": "@juniper explicitly silent", "to": "nobody"},
        {"id": c["id"], "line": "Following up with Pike"},
    ]:
        cursor = len(w.events)
        w.apply("comment", aid, None, args, "alex")
        assert "juniper" not in rooms.reached(w, w.events[-1])
        h = house.House.__new__(house.House)
        resident = SimpleNamespace(rid=ids.corner["juniper"], state={"cursor": cursor}, save=Mock())
        assert not h.news(w, resident, "juniper", resting=True)


def test_reply_status_and_for_you_follow_sent_messages_not_opening_a_card():
    desk, ids = roomworld.build()
    w = desk.world
    w.me = "alex"
    sid = w.nodes[ids.NOTE]["subject"]
    w.apply("comment", sid, None, {"line": "@pike Question"}, "alex")
    c = w.subjects[sid]["comments"][-1]
    w.apply("comment", sid, None, {"id": c["id"], "line": "First answer"}, "pike")
    w.apply("comment", sid, None, {"id": c["id"], "line": "Another thought"}, "pike")
    assert rooms.thread_waiting(w, c, "alex") == {1, 2}
    assert scene.rows(desk, "comments:" + ids.NOTE)[0]["awaiting"] == "yes"
    for _ in range(2):
        assert [r["awaiting"] for r in scene.rows(desk, "replies:" + ids.NOTE)] == ["yes", "yes"]
    inbox = scene.saying_rows(desk, "for:alex")
    assert [r["said"] for r in inbox if r["what"] == "reply"] == ["First answer", "Another thought"]
    w.apply("comment", sid, None, {"id": c["id"], "line": "Thanks, understood"}, "alex")
    assert rooms.thread_waiting(w, c, "alex") == set()
    response = w.events[-1]["id"]
    w.undo(response)
    c = w.subjects[sid]["comments"][-1]
    assert rooms.thread_waiting(w, c, "alex") == {1, 2}
    assert len([r for r in scene.saying_rows(desk, "for:alex") if r["what"] == "reply"]) == 2
    w.apply("comment", sid, None, {"id": c["id"], "line": "Thanks, understood"}, "alex")
    assert [r["answered"] for r in scene.saying_rows(desk, "for:alex") if r["what"] == "reply"] == [
        "yes",
        "yes",
    ]
    w.apply("comment", sid, None, {"id": c["id"], "line": "@juniper Side conversation"}, "pike")
    assert rooms.thread_waiting(w, c, "alex") == set()
