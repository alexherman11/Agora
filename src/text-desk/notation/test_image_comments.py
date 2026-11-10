"""Selected crops persist and reach only the addressed resident, without screen tools."""

import base64
import copy
import hashlib
import io
import json
import struct
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import image_comments
import roomworld
import store


@pytest.fixture
def case():
    desk, rooms = roomworld.build()
    desk.world.me = "alex"
    aid = rooms.NOTE
    desk.dispatch("desk", {"line": f"read {aid} :3"})
    source = desk.world.subjects[desk.world.nodes[aid]["subject"]]["text"]

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 40, 20, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress((b"\0" + b"\xff\0\0" * 40) * 20))
        + chunk(b"IEND", b"")
    )
    image = dict(
        source=aid,
        source_hash=hashlib.sha256(source.encode()).hexdigest(),
        rect=[0.1, 0.2, 0.4, 0.2],
        width=40,
        height=20,
        data_url=image_comments.PREFIX + base64.b64encode(png).decode(),
    )
    return desk, aid, image


def post(case, image=None, line=None):
    d, aid, original = case
    return d.dispatch(
        "desk",
        {
            "line": line or f'do comment {aid} line="@pike: explain this region"',
            "whole": True,
            "image_context": image or original,
        },
    )


def test_saved_crop_replay_and_undo(case):
    d, aid, image = case
    before = store.flatten(d.world)
    result = post(case)
    assert not result.get("error"), result
    assert "ERR" not in result.get("text", ""), result
    subject = d.world.subjects[d.world.nodes[aid]["subject"]]
    comment = subject["comments"][-1]
    assert comment["image"] == image
    assert image["data_url"] not in json.dumps(d.world.events[-1])
    after = store.flatten(d.world)
    restored = copy.deepcopy(d.world)
    # Replay the complete fact set into a fresh world through the fact API.
    from world import World

    rebuilt = World()
    store.apply(rebuilt, [(a, b, v) for (a, b), v in after.items()])
    assert store.flatten(rebuilt) == after
    result = d.dispatch("desk", {"line": "undo"})
    assert not result.get("error"), result
    assert not d.world.subjects[subject["id"]]["comments"]
    assert (
        image_comments.content(restored, [comment["id"]])[1]["source"]["data"]
        == image["data_url"].split(",")[1]
    )
    assert before != after


@pytest.mark.parametrize(
    "change",
    [
        {"source": "a999999"},
        {"source_hash": "stale"},
        {"rect": [0.9, 0, 0.9, 1]},
        {"data_url": "data:image/png;base64,broken"},
        {"width": 1},
        {"rect": [0, float("nan"), 1, 1]},
    ],
)
def test_bad_attachment_is_atomic(case, change):
    d, _, image = case
    before = store.flatten(d.world)
    result = post(case, {**image, **change})
    assert result.get("error") or "ERR" in result.get("text", ""), result
    assert store.flatten(d.world) == before


def test_attachment_cannot_be_redirected_or_batched(case):
    d, aid, _ = case
    before = store.flatten(d.world)
    result = post(case, line=f'look {aid}; do comment {aid} line="hello"')
    assert result.get("error")
    assert store.flatten(d.world) == before


def test_house_delivers_crop_and_preserves_failed_send(case):
    import house

    d, aid, image = case
    post(case)
    s = d.world.subjects[d.world.nodes[aid]["subject"]]
    c = s["comments"][-1]
    r = house.Resident.__new__(house.Resident)
    r.state = {"session": "existing"}
    r.save = Mock()
    r.log = Mock()
    r.house = SimpleNamespace(load=lambda: d.world)
    r.proc = SimpleNamespace(stdin=io.StringIO())
    house.House._knocked(None, r, d.world.events[-1], s, False)
    assert r.state["image_comments"] == [c["id"]]
    r.send("A comment addressed to you")
    message = json.loads(r.proc.stdin.getvalue())
    assert message["message"]["content"][-1]["type"] == "image"
    pending = r.state.pop("pending")
    r.hold_unanswered(pending, "failed after delivery")
    assert not r.state.get("image_comments")
    r.state.pop("session")
    r.hold_unanswered(pending, "conversation lost")
    assert r.state["image_comments"] == [c["id"]]
    assert image["data_url"] not in json.dumps(r.state)


def test_house_only_routes_crop_to_addressed_resident(case):
    import house

    d, _, _ = case
    cursor = len(d.world.events)
    post(case)
    h = house.House.__new__(house.House)
    for actor in ["pike", "juniper"]:
        rid = next(
            n["id"] for n in d.world.nodes.values() if n.get("props", {}).get("actor") == actor
        )
        r = SimpleNamespace(rid=rid, state={"cursor": cursor}, save=Mock())
        h.news(d.world, r, actor)
        assert bool(r.state.get("image_comments")) == (actor == "pike")
