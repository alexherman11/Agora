"""A visible fallback recipient never overrides an explicit message header."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import roomworld
from world import Refusal


@pytest.fixture
def chat():
    desk, ids = roomworld.build()
    w = desk.world
    sid = w.nodes[ids.TALK[ids.LOUNGE]]["subject"]
    return w, sid


def test_default_header_and_two_recipients(chat):
    w, sid = chat
    for words, expected in [("Question", ["pike"]), ("@juniper: Question", ["juniper"]),
                            ("@juniper @sable: Question", ["juniper", "sable"])]:
        w.apply("append", sid, None, {"line": words, "default_to": "pike"}, "alex")
        line = w.subjects[sid]["lines"][-1]
        assert line["to"] == expected
        assert "default_to" not in line.get("fields", {})


@pytest.mark.parametrize("words,audience", [("Question", ""), ("Question", "pikee"),
                                          ("@pikee: Question", "pike"), ("Question", "alex")])
def test_missing_or_unknown_audience_refuses_atomically(chat, words, audience):
    w, sid = chat
    before = copy.deepcopy(w.subjects[sid]), copy.deepcopy(w.events)
    with pytest.raises(Refusal, match="recipient"):
        w.apply("append", sid, None, {"line": words, "default_to": audience}, "alex")
    assert (w.subjects[sid], w.events) == before


def test_explicit_to_retains_its_existing_precedence(chat):
    w, sid = chat
    w.apply(
        "append", sid, None,
        {"line": "@juniper: Hi", "to": "sable", "default_to": "pike"}, "alex",
    )
    assert w.subjects[sid]["lines"][-1]["to"] == ["sable"]
