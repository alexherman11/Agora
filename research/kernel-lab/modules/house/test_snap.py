"""snap.py and the MCP door adapter's pictures.

    C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest research/kernel-lab/modules/house/test_snap.py -q

The adapter tests need nothing running. The shots start a fresh headless test world (test_kdesk.Desk, a temp folder,
a free port) and never touch the live desktop world or its door: a hidden browser for the live-door mode, and for the
source mode a hidden copy of that test world served by a kdesk from this checkout's code. Nothing appears on screen.
"""
import base64
import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ROOT = LAB.parents[1]
DESK = ROOT / "research" / "window-lab" / "kernel-desktop"
sys.path.insert(0, str(LAB / "mcp"))
sys.path.insert(0, str(HERE))
import agora_mcp  # noqa: E402
import snap  # noqa: E402


def png(w=4, h=3, rgb=(30, 120, 90)):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(agora_mcp, "SNAP_ROOT", tmp_path)
    (tmp_path / "residents" / "sable" / "snaps").mkdir(parents=True)
    return tmp_path


def answer(text):
    return {"ok": True, "text": text}


def test_a_named_snap_comes_back_as_an_image_after_the_text(state):
    pic = state / "residents" / "sable" / "snaps" / "board.png"
    pic.write_bytes(png())
    out = agora_mcp.reply(answer(f"board, live\n[image: {pic}]"), False)
    text, image = out["content"]
    assert text["type"] == "text" and json.loads(text["text"])["images"] == ["attached: board.png"]
    assert image == {"type": "image", "mimeType": "image/png", "data": base64.b64encode(png()).decode()}
    assert out["isError"] is False


def test_an_answer_with_no_picture_is_unchanged(state):
    body = answer("nothing to see")
    assert agora_mcp.reply(body, True) == {"content": [{"type": "text", "text": json.dumps(body)}], "isError": True}


@pytest.mark.parametrize("where,why", [
    (lambda s: s / "elsewhere" / "x.png", "outside the snaps folder"),
    (lambda s: s / "residents" / "sable" / "snaps" / ".." / "x.png", "outside the snaps folder"),   # .. resolved
    (lambda s: s.parent / "snaps" / "x.png", "outside the snaps folder"),                         # snaps, not under state
])
def test_a_picture_outside_the_snaps_folder_is_refused(state, where, why):
    pic = where(state)
    pic.parent.mkdir(parents=True, exist_ok=True)
    pic.write_bytes(png())
    out = agora_mcp.reply(answer(f"[image: {pic}]"), False)
    assert len(out["content"]) == 1
    assert json.loads(out["content"][0]["text"])["images"] == [f"not attached: x.png ({why})"]


def test_a_link_out_of_the_snaps_folder_is_refused(state):
    secret = state.parent / "outside.png"
    secret.write_bytes(png())
    link = state / "residents" / "sable" / "snaps" / "link.png"
    try:
        link.symlink_to(secret)
    except OSError:
        pytest.skip("this account may not make symlinks")
    out = agora_mcp.reply(answer(f"[image: {link}]"), False)
    assert len(out["content"]) == 1 and "outside the snaps folder" in out["content"][0]["text"]


def test_missing_too_big_not_png_and_relative_are_noted_not_attached(state, monkeypatch):
    snaps = state / "residents" / "sable" / "snaps"
    (snaps / "big.png").write_bytes(png(200, 200, (1, 2, 3)) + b"\0" * 5000)
    (snaps / "fake.png").write_bytes(b"not a png at all")
    (snaps / "pic.jpg").write_bytes(png())
    monkeypatch.setattr(agora_mcp, "IMAGE_CAP", 4000)
    text = " ".join(f"[image: {p}]" for p in (snaps / "gone.png", snaps / "big.png", snaps / "fake.png",
                                             snaps / "pic.jpg", "snaps/rel.png"))
    out = agora_mcp.reply(answer(text), False)
    assert len(out["content"]) == 1
    notes = json.loads(out["content"][0]["text"])["images"]
    assert notes == ["not attached: gone.png (missing)", "not attached: big.png (too large)",
                     "not attached: fake.png (not a PNG)", "not attached: pic.jpg (not a PNG)",
                     "not attached: rel.png (not a full path)"]


def test_the_server_attaches_pictures_to_one_line_and_to_a_batch(state, monkeypatch):
    pic = state / "residents" / "sable" / "snaps" / "a.png"
    pic.write_bytes(png())
    door = agora_mcp.Door("http://127.0.0.1:9", bearer="test")
    monkeypatch.setattr(door, "post", lambda route, line: {"ok": True, "text": f"shot\n[image: {pic}]"}
                        if "snap" in line else {"ok": True, "text": "fine"})
    server = agora_mcp.Server(door)
    server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                   "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t"}}})
    server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    one = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                         "params": {"name": "do", "arguments": {"line": "house.snap dk1"}}})["result"]
    assert [c["type"] for c in one["content"]] == ["text", "image"]
    many = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "lines", "arguments": {"lines": ["look dk1", "house.snap dk1",
                                                                                "house.snap dk1"]}}})["result"]
    assert [c["type"] for c in many["content"]] == ["text", "image"]          # the same picture once
    assert json.loads(many["content"][0]["text"])["images"] == ["attached: a.png"]


def test_the_real_state_folder_is_the_default_root():
    assert agora_mcp.SNAP_ROOT == DESK / "state"


# ---- real hidden shots --------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def desk():
    sys.path.insert(0, str(DESK))
    from test_kdesk import Desk
    d = Desk()
    try:
        yield d
    finally:
        d.close()


def colours(path):
    from PIL import Image
    with Image.open(path) as im:
        return len(im.convert("RGB").resize((160, 100)).getcolors(16000) or ())


def test_a_hidden_shot_of_a_window_thing_from_the_door(desk, tmp_path):
    assert desk.say("window.open help", "alex")["ok"]
    help_window = desk.wait(lambda: desk.window("help"))
    token = desk.entry.token("alex")
    got = snap.snap(help_window["id"], token, tmp_path / "help.png", door=desk.url, size=(900, 640), wait=1)
    assert got["path"] == str((tmp_path / "help.png").resolve())
    assert got["shown"] == f"{desk.url}/desk/help.html?win={help_window['id']}"
    assert token not in json.dumps(got)
    assert "Words you may use here" in got["detail"] and "live, read-only" in got["detail"]
    assert colours(got["path"]) > 5                     # a painted page, not a blank one


def test_a_hidden_shot_of_a_post_as_a_thing_and_refusals(desk, tmp_path):
    made = desk.say("post Snap can see this post", "alex")
    post = made["made"][0]
    got = snap.snap(post, desk.entry.token("alex"), tmp_path / "post.png", door=desk.url, wait=1)
    assert got["shown"].endswith(f"/desk/thing.html?target={post}") and "Snap can see this post" in got["detail"]
    with pytest.raises(RuntimeError, match="no thing dk999999"):
        snap.snap("dk999999", desk.entry.token("alex"), tmp_path / "x.png", door=desk.url)
    with pytest.raises(RuntimeError, match="loopback"):
        snap.snap(post, desk.entry.token("alex"), tmp_path / "x.png", door="http://example.com")


def test_a_hidden_shot_from_a_source_tree_over_a_copy_of_the_world(desk, tmp_path):
    """source mode: this checkout's code, over a hidden copy of the test world; everything it started ends."""
    import socket
    if not desk.window("help"):
        assert desk.say("window.open help", "alex")["ok"]
    wid = desk.wait(lambda: desk.window("help"))["id"]
    before = set(Path(snap.tempfile.gettempdir()).glob("agora-snap-*"))
    got = snap.snap(wid, desk.entry.token("alex"), tmp_path / "src.png", source=ROOT,
                    world=Path(desk.dir) / "world", size=(900, 640), wait=1)
    assert "a hidden copy of the world" in got["detail"] and "Words you may use here" in got["detail"]
    assert not got["shown"].startswith(desk.url)        # its own door, on another port
    assert colours(got["path"]) > 5
    assert set(Path(snap.tempfile.gettempdir()).glob("agora-snap-*")) <= before     # the copy is gone
    port = int(got["shown"].split(":")[2].split("/")[0])
    with pytest.raises(OSError):                        # and its door with it
        socket.create_connection(("127.0.0.1", port), timeout=1).close()


def test_live_mode_lets_only_readings_leave_the_browser():
    allows, door = snap._read_only_allows, "http://127.0.0.1:8810"
    assert allows("GET", door + "/api/scene?lens=feed", None) and allows("POST", door + "/see", '{"line":"look"}')
    assert allows("POST", door + "/desk/widget/open", "{}") and allows("POST", door + "/desk/widget/poll", "{}")
    assert allows("POST", door + "/desk/widget/call", '{"op":"project"}')
    for path, body in (("/do", '{"line":"failed why=x"}'), ("/api/do", "{}"), ("/upload", ""),
                       ("/desk/widget/call", '{"op":"do","line":"set dk1 x=1"}'), ("/desk/widget/call", '{"op":"upload"}'),
                       ("/desk/widget/stall", "{}"), ("/desk/widget/call", "not json")):
        assert not allows("POST", door + path, body), path
    assert not allows("GET", "https://fonts.googleapis.com/css", None)       # nothing leaves this machine
    assert not allows("DELETE", door + "/see", None)
