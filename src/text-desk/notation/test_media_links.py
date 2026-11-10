"""a5941: a path in a line of talk becomes a film or picture, from the folders the desk may show and nowhere else.

Imagined uses: JEFF writes the demo film's path the way agents do (absolute with C:/, relative, with backslashes,
inside a sentence ending in a full stop or a bracket); a line quotes a path to Alex's .env or to a film elsewhere on the
PC; a page asks deskd for a file by climbing out of the folder, by percent-encoding the climb, or by naming a kind the
desk does not show. Each must come out as words, or as a refusal, never as the file.
"""
import http.client
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import lens_ir
import media_links
import roomworld
import scene


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A checkout with a demo film, a picture in media/, and files outside the folders the desk may show."""
    r = tmp_path / "Agora4"
    demos = r / "src" / "desktop" / "demos" / "a5820"
    demos.mkdir(parents=True)
    (demos / "writing-demo.mp4").write_bytes(bytes(range(256)) * 40)          # 10240 bytes
    (r / "media").mkdir()
    (r / "media" / "board.png").write_bytes(b"\x89PNG....")
    (r / "media" / "drawing.svg").write_text("<svg onload='alert(1)'/>")
    (r / ".env").write_text("KEY=secret")
    (r / "elsewhere").mkdir()
    (r / "elsewhere" / "private.mp4").write_bytes(b"not for the desk")
    monkeypatch.setattr(media_links, "REPO", r)
    return r


def test_paths_as_agents_write_them(repo):
    film = repo / "src/desktop/demos/a5820/writing-demo.mp4"
    abs_fwd = str(film).replace("\\", "/")
    line = (f"@alex: the writing area is ready. Demo film (55 s): {abs_fwd}. Also src\\desktop\\demos\\a5820\\writing-demo.mp4, "
            f"(media/board.png) and src/desktop/demos/a5820/writing-demo.mp4 again.")
    got = media_links.find(line)
    shown = [m for m in got if m.get("src")]
    assert [m["src"] for m in shown] == ["/media/demos/a5820/writing-demo.mp4", "/media/media/board.png"]
    assert [m["kind"] for m in shown] == ["video", "image"]
    assert shown[0]["path"] == abs_fwd                      # the full stop after it is not part of the path
    assert len(got) == 2                                     # one film, however many ways it was spelled


def test_paths_outside_are_words(repo):
    outside = str(repo / "elsewhere" / "private.mp4").replace("\\", "/")
    got = media_links.find(f"look at {outside} and media/../elsewhere/private.mp4 and media/drawing.svg and {repo}/.env")
    assert all("src" not in m for m in got), got
    by = {m["path"]: m["refused"] for m in got}
    assert "outside the folders" in by[outside]
    assert "'..'" in by["media/../elsewhere/private.mp4"]
    assert not any(p.endswith((".svg", ".env")) for p in by)         # never even taken for a path
    assert "no such file" in media_links.find("media/missing.mp4")[0]["refused"]
    # names Windows treats oddly (a device, a share, a drive that is not there, too long) are words, never a fault
    odd = media_links.find("C:/con.mp4 media/aux.png \\\\server\\share\\x.mp4 Z:/nope/x.webm media/" + "a" * 300 + ".mp4")
    assert odd and all("src" not in m for m in odd), odd


def test_urls_are_checked_again(repo):
    assert media_links.file_for("/media/demos/a5820/writing-demo.mp4") == (repo / "src/desktop/demos/a5820/writing-demo.mp4").resolve()
    for bad in ["/media/demos/../../../.env", "/media/demos/%2e%2e/%2e%2e/%2e%2e/%2e%2e/elsewhere/private.mp4",
                "/media/media/drawing.svg", "/media/elsewhere/private.mp4", "/media/media/..\\elsewhere\\private.mp4",
                "/media/media/C:/Windows/win.ini", "/media/demos/", "/media/media//board.png"]:
        assert isinstance(media_links.file_for(bad), str), bad


def test_served_with_ranges_and_refusals(repo):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            media_links.serve(self, self.path)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    def get(path, rng=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", path, headers={"Range": rng} if rng else {})
        r = c.getresponse()
        return r.status, dict(r.getheaders()), r.read()

    try:
        st, h, body = get("/media/demos/a5820/writing-demo.mp4")
        assert (st, h["Content-Type"], len(body), h["Accept-Ranges"]) == (200, "video/mp4", 10240, "bytes")
        st, h, body = get("/media/demos/a5820/writing-demo.mp4", "bytes=100-199")
        assert (st, h["Content-Range"], body) == (206, "bytes 100-199/10240", (bytes(range(256)) * 40)[100:200])
        st, h, body = get("/media/demos/a5820/writing-demo.mp4", "bytes=10000-")
        assert (st, h["Content-Range"], len(body)) == (206, "bytes 10000-10239/10240", 240)
        st, h, body = get("/media/demos/a5820/writing-demo.mp4", "bytes=-16")
        assert (st, h["Content-Range"]) == (206, "bytes 10224-10239/10240")
        assert get("/media/demos/a5820/writing-demo.mp4", "bytes=20000-")[0] == 416
        assert get("/media/demos/../../../.env")[0] == 403
        st, _h, body = get("/media/elsewhere/private.mp4")
        assert st == 403 and b"not for the desk" not in body
        assert get("/media/media/nothing.png")[0] == 404
    finally:
        srv.shutdown()


LENS = '''chat : column
  of kind:note,?film as s
  each line
line : column
  body : text "$text"
    media
    on pop do prop $s seen=yes
    on pop host window media-player
big : text "$text"
  media player'''


def test_a_lens_draws_what_is_shown_and_prints_the_rest(repo, monkeypatch):
    desk, _ = roomworld.build()
    w = desk.world
    w.me = "alex"
    monkeypatch.setattr(scene, "reported_views", lambda *a: ({}, None))
    st = w.add_subject("note", "Media Style", "token accent = #123456", tags=["style"])
    w.place(st, w.root, 0, 0, 10, 10)
    lens = w.add_subject("note", "Media Lens", LENS, tags=["lens"])
    w.subjects[lens]["props"]["style"] = "Media Style"
    w.place(lens, w.root, 0, 0, 10, 10)
    outside = str(repo / "elsewhere" / "private.mp4").replace("\\", "/")
    s = w.add_subject("note", "a film line", f"the film: src/desktop/demos/a5820/writing-demo.mp4 and {outside}")
    w.place(s, w.root, 0, 0, 10, 10)
    sc, printed = lens_ir.scene_for(desk, "Media Lens")
    body = next(n for n in scene._walk(sc) if n.get("part") == "body" and (n.get("text") or "").startswith("the film:"))
    pv = scene.painter_view(body)
    assert pv["paint"]["media"] == {"mode": "embed", "items": [
        {"path": "src/desktop/demos/a5820/writing-demo.mp4", "src": "/media/demos/a5820/writing-demo.mp4",
         "kind": "video", "name": "writing-demo.mp4"}]}
    assert [(a["on"], a["line"]) for a in pv["acts"]] == [("pop", f"do prop {body['item']} seen=yes"), ("pop", "host window media-player")]
    assert "media 1 video (not shown: " in printed and "outside the folders" in printed
    assert outside in pv["paint"]["text"]                  # the words are kept whole; nothing is taken out of the line


@pytest.mark.parametrize("src, why", [
    ('t : text ""\n  media\n  on edit do rewrite $item text="$value"', "is edited"),
    ('t : text "x"\n  media\n  picture', "also a picture"),
    ('t : text "x"\n  on pop do prop $item a=b', "has no `media`"),
    ('t : text "x"\n  media small', "`media player`"),
])
def test_refusals(src, why):
    with pytest.raises(scene.LensRefusal, match=why.replace("(", r"\(")):
        scene.parse(src)
