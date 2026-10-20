"""a6638 (Alex, 20 Oct: 'this chat is the universal chat ... comments get routed to the right person, but I talk here'):
a line says what it is about, and the one it is handed to hears it.

  - a line in a Talk is about the Talk's document unless it says otherwise; a reply is about what it answers;
  - a line with its own about= keeps it;
  - the house hands a called agent the line's words AND what it points at: the thing by name and id, the quote."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import house
import roomworld
import scene


@pytest.fixture
def case():
    desk, ids = roomworld.build()
    w = desk.world
    doc = w.add_subject("note", "Proposal reader")
    w.subjects[doc]["text"] = "## What it is\nA reader for proposals."
    doc_at = w.place(doc, w.root, 0, 0, 100, 100)
    talk = w.add_subject("chat", "Talk: Proposal reader")
    w.subjects[talk]["lines"] = []
    w.subjects[talk]["props"] = {"talk_of": doc_at, "with": "alex,pike"}
    w.place(talk, w.root, 0, 200, 100, 100)
    conv = w.add_subject("chat", "Conversation")
    w.subjects[conv]["lines"] = []
    w.place(conv, w.root, 0, 400, 100, 100)
    return desk, doc_at, talk, conv


def append(w, chat, actor, words, to, **fields):
    w.apply("append", chat, None, {"line": words, "to": to, **fields}, actor)
    return w.subjects[chat]["lines"][-1]


def rows(desk):
    return {r["saying"]: r for r in scene.rows(desk, "sayings involving:alex")}


def test_talk_lines_are_about_their_document(case):
    desk, doc_at, talk, conv = case
    w = desk.world
    comment = append(w, talk, "alex", "Shorter, please", "pike", quote="A reader for proposals.", heading="What it is")
    answer = append(w, talk, "pike", "Done: one sentence now", "alex")
    plain = append(w, conv, "alex", "How are we doing?", "jeff")
    got = rows(desk)
    assert got[comment["id"]]["about"] == doc_at
    assert got[comment["id"]]["quote"] == "A reader for proposals."
    assert got[answer["id"]]["about"] == doc_at, "an agent's reply in the Talk arrives tagged with the document"
    assert got[plain["id"]]["about"] == "", "a line about nothing stays about nothing"


def test_a_reply_is_about_what_it_answers_and_its_own_word_wins(case):
    desk, doc_at, talk, conv = case
    w = desk.world
    asked = append(w, conv, "alex", "Is this ready?", "jeff", about=doc_at)
    answered = append(w, conv, "jeff", "Nearly", "alex", reply_to=asked["id"])
    other = w.place(w.add_subject("note", "Another note"), w.root, 300, 0, 100, 100)
    elsewhere = append(w, conv, "jeff", "And this one", "alex", reply_to=asked["id"], about=other)
    got = rows(desk)
    assert got[asked["id"]]["about"] == doc_at
    assert got[answered["id"]]["about"] == doc_at
    assert got[elsewhere["id"]]["about"] == other


def test_the_called_agent_hears_what_the_line_points_at(case):
    desk, doc_at, talk, conv = case
    w = desk.world
    line = append(w, talk, "alex", "Shorter, please", "pike", quote="A reader for proposals.", heading="What it is")
    ev = w.events[-1]
    said = house.points_at(w, ev, w.subjects[talk])
    assert said == '  [on the words "A reader for proposals." under § What it is]', said
    line = append(w, conv, "alex", "Is this ready?", "jeff", about=doc_at)
    said = house.points_at(w, w.events[-1], w.subjects[conv])
    assert said == f'  [about "Proposal reader" ({doc_at})]', said
    plain = append(w, conv, "alex", "Hello", "jeff")
    assert house.points_at(w, w.events[-1], w.subjects[conv]) == ""
    assert line["id"] != plain["id"]
