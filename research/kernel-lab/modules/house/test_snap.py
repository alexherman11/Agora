"""snap.py and the MCP door adapter's pictures.

    C:/Projects/Agora4/.venv/Scripts/python.exe -m pytest research/kernel-lab/modules/house/test_snap.py -q

The adapter tests need nothing running. The shots start a fresh headless test world (test_kdesk.Desk, a temp folder,
a free port) and never touch the live desktop world or its door: a hidden browser for the live-door mode, and for the
source mode a hidden copy of that test world served by a kdesk from this checkout's code. Nothing appears on screen.
"""
import base64
import asyncio
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


@pytest.fixture
def frame_images(tmp_path):
    """Real PNGs: blank interior with busy host chrome, and a feed painted inside it."""
    from PIL import Image, ImageDraw
    picture = Image.new("RGB", (320, 240), "#faf9f5")
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, 0, 319, 39), fill="#225588")
    draw.text((10, 10), "Host title must not count as component paint", fill="white")
    blank = tmp_path / "blank.png"
    picture.save(blank)
    draw.rectangle((10, 50, 80, 220), fill="#d0ddd5")
    draw.text((15, 60), "Channels", fill="#203020")
    for y in (60, 110, 160):
        draw.rectangle((95, y, 300, y + 35), fill="white", outline="#557766")
        draw.text((105, y + 10), "A post in the feed", fill="#203020")
    painted = tmp_path / "painted.png"
    picture.save(painted)
    draw.rectangle((90, 90, 250, 180), fill="#335577")
    changed = tmp_path / "changed.png"
    picture.save(changed)
    return blank.read_bytes(), painted.read_bytes(), changed.read_bytes()


def test_pixel_fixtures_ignore_host_chrome_and_detect_painted_frame(frame_images):
    blank, painted, changed = frame_images
    rect = [0, 40, 320, 240]
    assert snap._frame_pixels(blank, rect) is False
    first = snap._frame_pixels(painted, rect)
    assert first
    assert snap._stable_pixels(first, snap._frame_pixels(painted, rect))
    assert not snap._stable_pixels(first, snap._frame_pixels(changed, rect))
    assert not snap._stable_pixels(first, snap._frame_pixels(painted, [1, 40, 320, 240]))


@pytest.mark.parametrize("background", [(255, 255, 255), (20, 22, 24)])
def test_background_tolerance_and_small_specks_are_not_paint(background):
    import io
    from PIL import Image, ImageDraw
    picture = Image.new("RGB", (200, 200), background)
    draw = ImageDraw.Draw(picture)
    draw.rectangle((0, 0, 199, 99), fill=tuple(c - 2 for c in background))
    draw.point((50, 50), fill="red")
    stream = io.BytesIO()
    picture.save(stream, format="PNG")
    assert snap._frame_pixels(stream.getvalue(), [0, 0, 200, 200]) is False


class FakeFrame:
    """The parent is ready at t=0, but its opaque component frame can paint much later."""
    def __init__(self, frame_images, paint_at=None, component="true", content=None):
        self.now, self.component = 0, component
        self.content = content or (lambda now: frame_images[int(paint_at is not None and now >= paint_at)])
        self.captures = 0

    async def sleep(self, seconds):
        self.now += seconds

    async def call(self, method, **params):
        if method == "Page.captureScreenshot":
            self.captures += 1
            return {"data": base64.b64encode(self.content(self.now)).decode()}
        assert method == "Runtime.evaluate"
        assert "contextId" not in params  # Never try to read the opaque sandbox DOM.
        assert params["expression"] == snap.FRAME_RECT
        return {"result": {"value": {"false": None, "pending": False,
                                    "true": [0, 40, 320, 240]}[self.component]}}

    def wait(self, deadline=90):
        return asyncio.run(snap._wait_for_paint(
            lambda: snap._frame_painted(self.call), deadline,
            clock=lambda: self.now, sleep=self.sleep))


def test_component_waits_past_old_blank_capture_until_frame_paints(frame_images):
    frame = FakeFrame(frame_images, paint_at=13)
    assert frame.wait() == snap.PIXEL_PAINT
    assert frame.now == 14 and frame.captures == 15


def test_component_without_marker_uses_remaining_deadline(frame_images):
    frame = FakeFrame(frame_images)
    frame.now = 17  # resolution and browser startup have already spent part of the overall budget
    assert frame.wait() is False
    assert frame.now == 90


def test_stored_painter_with_stable_content_captures_early_without_marker(frame_images):
    frame = FakeFrame(frame_images, paint_at=0)
    assert frame.wait() == snap.PIXEL_PAINT
    assert frame.now == 1 and frame.captures == 2


@pytest.mark.parametrize("sequence,settled_at", [
    ([1, 2, 1, 1], 3),
    ([1, 0, 1, 1], 3),
])
def test_changing_or_disappearing_content_restarts_stability_interval(frame_images, sequence, settled_at):
    frame = FakeFrame(frame_images, content=lambda now: frame_images[sequence[min(int(now), len(sequence) - 1)]])
    assert frame.wait() == snap.PIXEL_PAINT
    assert frame.now == settled_at


def test_transient_content_does_not_make_an_empty_frame_painted(frame_images):
    frame = FakeFrame(frame_images, content=lambda now: frame_images[int(now < 1)])
    assert frame.wait() is False
    assert frame.now == 90


def test_replaced_component_frame_is_retried(frame_images):
    frame = FakeFrame(frame_images, paint_at=0)
    original = frame.call

    async def call(method, **params):
        if method == "Runtime.evaluate" and frame.now < 2:
            return {"result": {"value": False}}
        return await original(method, **params)

    frame.call = call
    assert frame.wait() == snap.PIXEL_PAINT
    assert frame.now == 3


def test_widget_still_opening_does_not_count_as_painted(frame_images):
    frame = FakeFrame(frame_images, component="pending")
    assert frame.wait() is False
    assert frame.now == 90 and not frame.captures


def test_ordinary_widget_keeps_existing_text_wait(frame_images):
    frame = FakeFrame(frame_images, component="false")
    assert frame.wait() is None
    assert frame.now == 0


@pytest.mark.parametrize("content", ["", "<h1>Feed</h1><p>Channels and posts are painted.</p>"])
def test_real_opaque_iframe_pixels_determine_paint(tmp_path, content):
    """Exercise Chromium's actual sandbox and screenshot, without a world or a live session."""
    import html
    import time
    from urllib.parse import quote
    inside = '<style>body{background:#faf9f5;color:#203020}</style>' + content
    page = ('<style>body{margin:0}iframe{border:0;width:320px;height:200px}</style>'
            '<header style="height:40px;background:#225588;color:white">Host chrome</header>'
            '<main id="widget-surface" data-components="true">'
            f'<iframe sandbox="allow-scripts" srcdoc="{html.escape(inside, quote=True)}"></iframe></main>')
    output = tmp_path / "opaque.png"
    with snap.shoot.browser() as ws:
        started = time.monotonic()
        result = asyncio.run(snap._shoot(ws, "data:text/html," + quote(page),
                                        "http://127.0.0.1:9", "synthetic-test-value",
                                        output, (320, 240), 0, True, None, 8))
        elapsed = time.monotonic() - started
    assert result[2] == (snap.PIXEL_PAINT if content else False)
    if content:
        assert elapsed < 6
    else:
        assert elapsed >= 8
    assert bool(snap._frame_pixels(output.read_bytes(), [0, 40, 320, 240])) == bool(content)


def test_unresponsive_frame_probe_is_bounded():
    async def run():
        async def stuck():
            await asyncio.Future()
        return await snap._wait_for_paint(stuck, asyncio.get_running_loop().time() + 0.01,
                                         clock=asyncio.get_running_loop().time)
    assert asyncio.run(run()) is False


@pytest.mark.parametrize("at_capture", [0, 1, 2])
@pytest.mark.parametrize("settled", [False, True])
def test_shoot_labels_actual_pixels_even_after_deadline_or_paint_disappears(
        tmp_path, monkeypatch, frame_images, at_capture, settled):
    import websockets
    calls = []

    class FakeBrowser:
        async def __aenter__(self):
            self.messages = asyncio.Queue()
            return self

        async def __aexit__(self, *args):
            pass

        def __aiter__(self):
            return self

        async def __anext__(self):
            return await self.messages.get()

        async def send(self, raw):
            request = json.loads(raw)
            method = request["method"]
            calls.append(method)
            result = {}
            if method == "Runtime.evaluate":
                expr = request["params"]["expression"]
                value = [0, 40, 320, 240] if expr == snap.FRAME_RECT else True if "readyState" in expr else ""
                result = {"result": {"value": value}}
            elif method == "Page.captureScreenshot":
                result = {"data": base64.b64encode(frame_images[at_capture]).decode()}
            await self.messages.put(json.dumps({"id": request["id"], "result": result}))

    async def deadline_probe(probe, deadline):
        # Exercise the outer readiness timeout, including a frame appearing only at capture.
        if settled and "Page.captureScreenshot" not in calls:
            return snap.PIXEL_PAINT
        await asyncio.Future()

    monkeypatch.setattr(websockets, "connect", lambda *a, **kw: FakeBrowser())
    monkeypatch.setattr(snap, "_wait_for_paint", deadline_probe)
    output = tmp_path / "deadline.png"
    result = asyncio.run(snap._shoot("fake", "http://127.0.0.1:9/desk/widget.html",
                                   "http://127.0.0.1:9", "synthetic-test-value",
                                   output, (320, 240), 4, True, None, 0.5 if settled else 0.02))
    assert result == ("", 0, snap.PIXEL_PAINT if at_capture else False)
    assert output.read_bytes() == frame_images[at_capture]
    assert calls.count("Page.captureScreenshot") == (4 if settled and not at_capture else 2)


def test_missing_frame_at_capture_is_unverified_not_background_only():
    async def call(method, **params):
        return {"result": {"value": False}}

    assert asyncio.run(snap._frame_painted(call, png())) == "paint not verified"


@pytest.mark.parametrize("painted,label", [
    (False, "not painted after 90 s"),
    (snap.PIXEL_PAINT, snap.PIXEL_PAINT),
])
def test_deadline_picture_and_result_are_labelled(tmp_path, monkeypatch, painted, label):
    from PIL import Image
    output = tmp_path / "unpainted.png"
    monkeypatch.setattr(snap, "resolve", lambda *a: ("/desk/widget.html?widget=fixture", "the lens"))

    def fake_shot(*args, **kwargs):
        output.write_bytes(png(320, 200))
        return "", 0, painted

    monkeypatch.setattr(snap, "_shot", fake_shot)
    got = snap.snap("fixture", "synthetic-test-value", output, size=(320, 200))
    assert got["paint_status"] == label
    assert label in got["detail"]
    with Image.open(output) as picture:
        assert picture.getpixel((0, 0)) == (255, 244, 206)
        assert picture.getpixel((0, 199)) == (30, 120, 90)
        assert len(picture.crop((0, 0, 320, 35)).getcolors(11200)) > 1  # banner contains ink


def test_house_preserves_deadline_label_in_wake_and_last(tmp_path, monkeypatch):
    """Exercise the real method without starting House, a session, a thread or a world."""
    import ast
    import threading
    import time
    from types import SimpleNamespace
    tree = ast.parse((HERE / "house.py").read_text(encoding="utf-8"))
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "snap")
    namespace = {"Path": Path, "threading": threading, "time": time, "URL": "http://127.0.0.1:9"}
    exec(compile(ast.Module(body=[method], type_ignores=[]), "house.py", "exec"), namespace)
    messages = []
    owner = SimpleNamespace(
        snaps={}, snapping=0, snap_lock=threading.Lock(), home=tmp_path, world=None,
        m=SimpleNamespace(see=lambda *a, **kw: {"rows": [{}]}),
        builders=SimpleNamespace(session=lambda p: SimpleNamespace(token="synthetic-test-value")),
        agents={"fixture": SimpleNamespace(wake=messages.append)},
        message=lambda title, **kw: title + ": " + kw["label"])
    monkeypatch.setattr(threading, "Thread", lambda target, **kw: SimpleNamespace(start=target))
    monkeypatch.setattr(snap, "snap", lambda *a, **kw: {"paint_status": "not painted after 90 s"})
    namespace["snap"](owner, {"args": {"target": "lens"}, "caller": {"person": "fixture"}})
    last = namespace["snap"](owner, {"args": {"target": "last"}, "caller": {"person": "fixture"}})
    assert "not painted after 90 s" in messages[0]
    assert "not painted after 90 s" in last["text"] and "[image:" in last["text"]
