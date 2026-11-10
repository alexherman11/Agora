"""Native linked-chat reply contract; isolated worlds, no model or live Desk."""

import io
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text-desk/notation"))
import deskd
import explore
import lens_ir
import rooms
import roomworld
import scene
import store

SOURCE = Path(__file__).with_name("home-chat-reply.lens").read_text(encoding="utf-8")


@pytest.fixture
def case(tmp_path, monkeypatch):
    d, ids = roomworld.build(say=False)
    w = d.world
    w.me = "alex"
    sid = w.add_subject("chat", "Talk with Alex, Pike", "")
    w.subjects[sid]["props"]["members"] = "alex"
    chat = w.place(sid, ids.corner["pike"], 0, 0, 500, 300)
    vid = w.add_subject("note", "Viewer state", "")
    w.subjects[vid]["props"].update(role="home-view", actor="alex", viewing=chat)
    w.place(vid, w.root, 0, 0, 100, 100)
    roles = "feed said said.mine saidhead who meta bubble bubble.mine words dock input".split()
    style_text = "token ink = #111111\n" + "\n".join("role " + x + " : ink" for x in roles)
    style = w.add_subject("note", "Chat fixture", style_text, tags=["style"])
    w.place(style, w.root, 0, 0, 100, 100)
    lid = w.add_subject("note", "home-chat", SOURCE, tags=["lens"])
    w.subjects[lid]["props"]["style"] = "Chat fixture"
    w.place(lid, w.root, 0, 0, 100, 100)
    monkeypatch.setattr(deskd, "SESSIONS", tmp_path)
    monkeypatch.setattr(deskd, "_trace", lambda *args: None)
    monkeypatch.setattr(deskd, "_DESKS", {})
    monkeypatch.setattr(deskd, "HOLD", [False])
    monkeypatch.delenv("DESK_LOG", raising=False)
    path = tmp_path / "private-chat-repair.pickle"
    store.genesis(d, path, why="isolated linked-chat test")
    explore.save_desk(path, d)
    return d, chat, vid, path


def send(path, who, line, **fields):
    body = json.dumps(dict(session=path.stem, **{"as": who}, line=line, **fields)).encode()
    h = deskd.Handler.__new__(deskd.Handler)
    h.path, h.headers = "/api/do", {"Content-Length": str(len(body))}
    h.rfile, h._json = io.BytesIO(body), Mock()
    h._post()
    return h._json.call_args.args[0]


def test_linked_chat_sends_once_routes_owner_and_paints_reply(case):
    d, chat, _, path = case
    sc, _ = lens_ir.scene_for(d, "home-chat")
    composer = next(n for n in scene._walk(sc) if n.get("part") == "say")
    assert composer["paint"]["commit"] == "explicit"
    assert composer["acts"] == [{"on": "edit", "line": f'do append {chat} line="$value"'}]
    line = f'do append {chat} line="Please reply here"'
    first = send(path, "alex", line, gesture="one-human-send", observed=composer["fence"])
    assert not first.get("error"), first
    second = send(path, "alex", line, gesture="one-human-send", observed=composer["fence"])
    assert second.get("already") and not second.get("events"), second
    with deskd.Session(path.stem, "alex") as saved:
        s = saved.world.subjects[saved.world.nodes[chat]["subject"]]
        assert len(s["lines"]) == 1
        event = next(
            e
            for e in saved.world.events
            if e.get("gesture") == "one-human-send" and "append" in e.get("args", {})
        )
        assert rooms.reached(saved.world, event) == {"pike": "call"}
    reply = send(
        path, "pike", f'read {chat}; do append {chat} line="@alex: Reply in this same chat"'
    )
    assert not reply.get("error"), reply
    with deskd.Session(path.stem, "alex") as saved:
        sc, _ = lens_ir.scene_for(saved, "home-chat")
        assert any("Reply in this same chat" in str(n.get("text", "")) for n in scene._walk(sc)), [
            n.get("text") for n in scene._walk(sc)
        ]


def test_opening_another_chat_gets_a_distinct_composer_key(case):
    d, chat, vid, _ = case
    sc, _ = lens_ir.scene_for(d, "home-chat")
    first = next(n for n in scene._walk(sc) if n.get("part") == "say")
    w = d.world
    sid = w.add_subject("chat", "Another chat", "")
    other = w.place(sid, w.root, 0, 0, 300, 300)
    w.subjects[vid]["props"]["viewing"] = other
    w.subjects[vid]["rev"] += 1
    sc, _ = lens_ir.scene_for(d, "home-chat")
    second = next(n for n in scene._walk(sc) if n.get("part") == "say")
    assert first["key"] != second["key"]
    assert first["acts"][0]["line"] == f'do append {chat} line="$value"'
    assert second["acts"][0]["line"] == f'do append {other} line="$value"'
