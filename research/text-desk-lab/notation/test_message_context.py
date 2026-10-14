"""Private captures become bounded, self-contained message evidence."""

import base64
import copy
import hashlib
import json
import shlex
import struct
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import message_context as mc
from desk import unescape_value
from world import Refusal, World


@pytest.fixture
def case(monkeypatch):
    world = World()
    sid = world.add_subject("note", "Selection", 'Words "quoted"\nsecond line \\n literal')
    aid = world.place(sid, world.root, 0, 0, 100, 100)
    capture = {
        "id": "cap-1",
        "by": "alex",
        "session": "frontier",
        "at": "now",
        "rect": [0, 0, 100, 100],
        "monitor": {},
        "native": True,
        "windows": [],
        "refs": [
            {
                "world": "frontier",
                "item": aid,
                "subject": sid,
                "kind": "note",
                "role": "",
                "lens": "",
                "key": "",
                "words": world.subjects[sid]["text"],
                "revision": len(world.events),
                "rev": world.nodes[aid]["rev"],
            }
        ],
        "image": None,
        "image_text": "",
        "timing_ms": 1,
    }

    class CaptureError(Exception):
        pass

    service = SimpleNamespace(CaptureError=CaptureError, sent_copy=Mock(return_value=capture))
    monkeypatch.setitem(sys.modules, "captures", service)
    return world, capture, service


def png():
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    raw = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )
    return {
        "media_type": "image/png",
        "data": base64.b64encode(raw).decode(),
        "width": 1,
        "height": 1,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def test_freezes_copy_and_replays_without_private_service(case):
    world, capture, service = case
    saved = mc.resolve("frontier", "alex", "cap-1")
    service.sent_copy.assert_called_once_with("frontier", "alex", "cap-1")
    capture["refs"][0]["words"] = "Changed private capture"
    service.sent_copy.side_effect = service.CaptureError("gone")
    assert mc.resolve("frontier", "alex", saved) == saved
    blocks = mc.model_content(world, saved, session="frontier")
    assert "Changed private capture" not in blocks[0]["text"]
    assert '"status":"unchanged"' in blocks[0]["text"]
    world.nodes[capture["refs"][0]["item"]]["rev"] += 1
    assert '"status":"changed"' in mc.model_content(world, saved, session="frontier")[0]["text"]
    assert '"status":"unavailable"' in mc.model_content(world, saved)[0]["text"]
    assert '"status":"unavailable"' in mc.model_content(world, saved, session="other")[0]["text"]
    del world.nodes[capture["refs"][0]["item"]]
    assert '"status":"unavailable"' in mc.model_content(world, saved, session="frontier")[0]["text"]


def test_missing_and_wrong_owner_refuse(case):
    _, _, service = case
    for reason in ("capture missing", "capture belongs to another actor"):
        service.sent_copy.side_effect = service.CaptureError(reason)
        with pytest.raises(Refusal, match=reason):
            mc.resolve("frontier", "alex", "cap-1")


def test_png_validation_and_model_image_block(case):
    world, capture, _ = case
    capture["image"] = png()
    saved = mc.resolve("frontier", "alex", "cap-1")
    blocks = mc.model_content(world, saved, session="frontier")
    assert blocks[1] == {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": capture["image"]["data"]},
    }
    for change in (
        {"width": 2},
        {"width": True},
        {"data": "broken"},
        {"sha256": "0" * 64},
        {"media_type": "image/svg+xml"},
    ):
        bad = json.loads(saved)
        bad["captures"][0]["image"].update(change)
        with pytest.raises(Refusal):
            mc.resolve("frontier", "alex", json.dumps(bad))


@pytest.mark.parametrize("value", ["cap-1 " * 9, "http://example.com", "cap-xyz", "{}", "[]"])
def test_malformed_inputs(case, value):
    with pytest.raises(Refusal):
        mc.resolve("frontier", "alex", value)


def test_bounded_saved_metadata(case):
    _, capture, _ = case
    for change in ({"refs": "oops"}, {"image_text": "x" * 16001}, {"timing_ms": float("nan")}):
        bad = copy.deepcopy(capture)
        bad.update(change)
        with pytest.raises(Refusal):
            mc.resolve("frontier", "alex", json.dumps({"version": 1, "captures": [bad]}))


def test_durable_command_uses_created_line_and_roundtrips_quotes_newlines(case):
    world, _, service = case
    saved = mc.resolve("frontier", "alex", "cap-1")
    chat = world.add_subject("chat", "Chat")
    world.subjects[chat]["lines"] = []
    words = 'Message "quote"\nnext \\n literal; do nothing'
    world.apply("append", chat, None, {"line": words, "context": saved, "to": "nobody"}, "alex")
    created = world.events[-1]
    world.apply("append", chat, None, {"line": "A separate rule message"}, "house")
    original = (
        f"do append {chat} line=" + json.dumps(words.replace("\\", "\\\\")) + ' captures="cap-1"'
    )
    durable = mc.durable_command(original, world, [created, world.events[-1]])
    decoded = {
        k: unescape_value(v)
        for k, _, v in (word.partition("=") for word in shlex.split(durable)[3:])
    }
    assert decoded["line"] == words
    assert "captures" not in decoded
    assert json.loads(decoded["context"]) == json.loads(saved)
    service.sent_copy.side_effect = service.CaptureError("deleted")
    assert mc.resolve("frontier", "alex", decoded["context"]) == saved
    assert mc.durable_command(durable, world, []) == durable
    arbitrary = f'do append {chat} line="x" context="cap-1"'
    assert mc.durable_command(arbitrary, world, []) == arbitrary
    with pytest.raises(Refusal):
        mc.durable_command(original, world, [])
    from desk import Desk

    world.me = "alex"
    desk = Desk(world)
    desk.seen[chat] = world.subjects[chat]["rev"]
    result = desk.dispatch("desk", {"line": durable, "whole": True})
    assert not result.get("error"), result
    replayed = world.subjects[chat]["lines"][-1]
    assert replayed["text"] == "Alex: " + words
    assert json.loads(replayed["fields"]["context"]) == json.loads(saved)
