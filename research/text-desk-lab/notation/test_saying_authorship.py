"""A multiline message has one author/key; JEFF never signs new comments as Alex."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import persons
import roomworld
import scene
import store
from world import Refusal, World


@pytest.fixture
def case():
    desk, ids = roomworld.build(say=False)
    w = desk.world
    chat = w.add_subject("chat", "Authorship check")
    w.subjects[chat]["lines"] = []
    w.subjects[chat]["props"]["members"] = "alex,jeff"
    w.place(chat, w.root, 0, 0, 100, 100)
    note = w.nodes[ids.NOTE]["subject"]
    return desk, chat, note


@pytest.mark.parametrize("view", ["", "for:jeff", "involving:alex"])
def test_multiline_message_keeps_author_full_text_and_unique_key(case, view):
    desk, chat, _ = case
    w = desk.world
    body = "First paragraph\n\nJeff: this is quoted text, still written by Alex\nLast paragraph"
    w.apply("append", chat, None, {"line": body, "to": "jeff"}, "alex")
    message = w.subjects[chat]["lines"][-1]
    before = store.flatten(w)
    rows = scene.rows(desk, f"sayings {view} in:{chat}")
    assert len(rows) == 1
    assert rows[0]["name"] == "alex"
    assert rows[0]["by"] == "Alex"
    assert rows[0]["said"] == body
    assert rows[0]["line"] == message["id"]
    assert rows[0]["eid"] == message["ev"]
    assert store.flatten(w) == before


@pytest.mark.parametrize("actor", ["alex", "jeff", "juniper"])
def test_new_comment_reply_and_resolution_keep_actual_actor(case, actor):
    desk, _, note = case
    w = desk.world
    w.apply("comment", note, None, {"line": "Opening", "to": "pike"}, actor)
    comment = w.subjects[note]["comments"][-1]
    assert comment["by"] == actor
    assert persons.comment_by(w, comment) == actor
    w.apply("comment", note, None, {"id": comment["id"], "line": "Follow-up"}, actor)
    w.apply("resolve", note, None, {"id": comment["id"], "line": "Closing"}, actor)
    assert [r["by"] for r in comment["replies"]] == [actor, actor]
    assert [persons.reply_by(w, comment, i) for i in range(2)] == [actor, actor]
    assert [e["by"] for e in w.events[-3:]] == [actor, actor, actor]
    facts = store.flatten(w)
    rebuilt = World()
    store.apply(rebuilt, [(a, b, v) for (a, b), v in facts.items()])
    assert store.flatten(rebuilt) == facts


def test_old_signature_is_preserved_and_invalid_reply_is_atomic(case):
    desk, _, note = case
    w = desk.world
    cid = w.add_comment(note, "alex", "Legacy owner signature", actor="jeff")
    old = copy.deepcopy(w.find_comment(cid)[1])
    before = store.flatten(w)
    with pytest.raises(Refusal):
        w.apply("comment", note, None, {"id": "c999999", "line": "Cannot land"}, "jeff")
    assert store.flatten(w) == before
    w.apply("comment", note, None, {"line": "New JEFF comment"}, "jeff")
    assert w.find_comment(cid)[1] == old
    assert persons.comment_by(w, old) == "alex"
    assert w.subjects[note]["comments"][-1]["by"] == "jeff"


def test_edited_message_stays_whole_and_visibly_marked(case):
    desk, chat, _ = case
    w = desk.world
    w.apply("append", chat, None, {"line": "First\n\nSecond", "to": "jeff"}, "alex")
    w.apply("rewrite", chat, None, {"text": "Alex: First\n\nChanged"}, "alex")
    message = w.subjects[chat]["lines"][-1]
    assert message.get("edited")
    rows = scene.rows(desk, f"sayings in:{chat}")
    assert len(rows) == 1 and rows[0]["edited"] == "edited"
    assert rows[0]["said"] == f"First\n\nChanged  (edited, {message['id']})"


def test_jeff_comment_person_and_rename_stay_distinct_from_alex(case):
    desk, _, note = case
    w = desk.world
    persons.begin(w, actor="alex")
    w.apply("comment", note, None, {"line": "JEFF's words", "to": "alex"}, "jeff")
    comment = w.subjects[note]["comments"][-1]
    event = persons.comment_events(w)[comment["id"]]
    assert event["who"] == persons.today(w, "jeff")
    assert event["who"] != persons.today(w, "alex")
    persons.rename(w, event["who"], "jeffrey", actor="alex")
    assert persons.comment_by(w, comment) == "jeffrey"
