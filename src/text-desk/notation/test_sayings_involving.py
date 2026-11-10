"""A person's outgoing and addressed incoming sayings, with native reply targets."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import persons
import roomworld
import scene


@pytest.fixture
def case():
    desk, ids = roomworld.build()
    w = desk.world
    chats = []
    for title in ("One conversation", "Other conversation"):
        sid = w.add_subject("chat", title)
        w.subjects[sid]["lines"] = []
        w.place(sid, w.root, 0, 0, 100, 100)
        chats.append(sid)
    return desk, ids, chats


def append(w, chat, actor, words, to, **fields):
    w.apply("append", chat, None, {"line": words, "to": to, **fields}, actor)
    return w.subjects[chat]["lines"][-1]["id"]


def comment(w, sid, actor, words, to, thread=None):
    args = {"line": words, "to": to}
    if thread:
        args["id"] = thread
    w.apply("comment", sid, None, args, actor)
    c = w.subjects[sid]["comments"][-1]
    return f"{thread}/reply/{len(c['replies'])}" if thread else c["id"]


def selected(desk, **kwargs):
    source = "sayings involving:alex" + "".join(f" {k}:{v}" for k, v in kwargs.items())
    return {r["saying"]: r for r in scene.rows(desk, source)}


def test_both_directions_other_chats_and_comment_threads(case):
    desk, ids, (one, other) = case
    w = desk.world
    sid = w.nodes[ids.NOTE]["subject"]
    outgoing = append(w, one, "alex", "A question", "pike")
    incoming = append(w, one, "pike", "An answer", "alex")
    second = append(w, other, "juniper", "Another reply", "alex")
    question = comment(w, sid, "alex", "Check this", "pike")
    answer = comment(w, sid, "pike", "Checked", "alex", question)
    followup = comment(w, sid, "alex", "One detail", "pike", question)
    other_comment = comment(w, sid, "juniper", "A separate question", "alex")
    irrelevant = append(w, one, "pike", "Agent work", "juniper")
    aside = comment(w, sid, "juniper", "Aside to another agent", "pike", question)
    unrelated = comment(w, sid, "pike", "Separate agent thread", "juniper")
    rows = selected(desk)
    assert {outgoing, incoming, second, question, answer, followup, other_comment} <= rows.keys()
    assert not {irrelevant, aside, unrelated} & rows.keys()
    assert rows[outgoing]["source"] == one
    assert rows[outgoing]["line"] == outgoing
    assert rows[answer]["thread"] == question
    assert rows[question]["thread"] == question
    assert rows[answer]["item"] == ids.NOTE
    assert all(r["answered"] == r["before"] == r["open"] == "" for r in rows.values())
    assert second not in selected(desk, **{"in": one})


def test_membership_broadcasts_and_unaddressed_lines(case):
    desk, _, (one, other) = case
    w = desk.world
    w.subjects[one]["props"]["members"] = "alex,pike,juniper"
    directed_elsewhere = append(w, one, "pike", "A member speaking to Juniper", "juniper")
    broadcast = append(w, one, "pike", "Everyone", "everyone")
    unaddressed = append(w, one, "pike", "No recipient", "nobody")
    own_broadcast = append(w, one, "alex", "Hello everyone", "everyone")
    own_plain = append(w, one, "alex", "Own note", "nobody")
    w.subjects[other]["props"]["members"] = "pike,juniper"
    private = append(w, other, "pike", "Excluded recipient", "alex")
    own_private = append(w, other, "alex", "Earlier outgoing", "pike")
    rows = selected(desk)
    assert not {directed_elsewhere, broadcast, unaddressed, private} & rows.keys()
    assert {own_broadcast, own_plain, own_private} <= rows.keys()
    # Preserve the broader For-you rule for direct-chat members.
    assert directed_elsewhere in {r["saying"] for r in scene.rows(desk, "sayings for:alex")}
    assert own_plain not in {r["saying"] for r in scene.rows(desk, "sayings for:alex")}


def test_multiline_stable_order_and_fields_cannot_shadow_native_metadata(case):
    desk, _, (one, _) = case
    w = desk.world
    first = append(w, one, "alex", "First line\nsecond line", "pike", mark="ask", context="a123")
    item = w.find_line(first)[1]
    item["fields"].update(source="forged", saying="forged", name="forged", thread="forged")
    second = append(w, one, "pike", "Answer", "alex", reply_to=first)
    # Equal wall-clock timestamps must still follow native event order.
    events = [w.event_by_id(w.find_line(mid)[1]["ev"]) for mid in (first, second)]
    for e in events:
        e["at"] = "2026-10-14T12:00:00"
    rows = scene.rows(desk, f"sayings involving:alex in:{one}")
    assert [r["saying"] for r in rows] == [first, second]
    assert rows[0]["said"] == "First line\nsecond line"
    assert rows[0]["name"] == "alex" and rows[0]["source"] == one
    assert rows[0]["thread"] == "" and rows[0]["context"] == "a123"
    assert rows[1]["reply_to"] == first
    assert scene.rows(desk, f"sayings involving:alex in:{one} mark=ask") == [rows[0]]
    append(w, one, "juniper", "Unrelated", "pike")
    assert [r["saying"] for r in scene.rows(desk, f"sayings involving:alex in:{one}")] == [
        first,
        second,
    ]


def test_renamed_and_reused_person_names_keep_their_own_history(case):
    desk, ids, (one, _) = case
    w = desk.world
    sid = w.nodes[ids.NOTE]["subject"]
    old_out = append(w, one, "alex", "Old outgoing", "pike")
    old_in = append(w, one, "pike", "Old incoming", "alex")
    old_comment = comment(w, sid, "alex", "An older question", "pike")
    old_reply = comment(w, sid, "pike", "An older answer", "alex", old_comment)
    persons.begin(w, actor="alex")
    old_person = persons.today(w, "alex")
    persons.rename(w, old_person, "alexandra", actor="alex")
    persons.new(w, "alex", kind="human", actor="alexandra")
    new_out = append(w, one, "alex", "New outgoing", "pike")
    new_in = append(w, one, "pike", "New incoming", "alex")
    old = {r["saying"] for r in scene.rows(desk, "sayings involving:alexandra")}
    old_by_id = {r["saying"] for r in scene.rows(desk, f"sayings involving:{old_person}")}
    new = selected(desk)
    assert {old_out, old_in, old_comment, old_reply} <= old
    assert old == old_by_id
    assert not {new_out, new_in} & old
    assert {new_out, new_in} <= new.keys()
    assert not {old_out, old_in, old_comment, old_reply} & new.keys()


def test_involving_and_for_are_distinct_modes(case):
    desk, _, _ = case
    with pytest.raises(scene.LensRefusal, match="either"):
        scene.rows(desk, "sayings for:alex involving:alex")
