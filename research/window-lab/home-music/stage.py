"""stage.py: the music panel in the sandbox, against a stand-in media session and a fake Spotify (a6443). 17 Oct 2026.

    python research/window-lab/home-music/stage.py [--empty] [--signed-out] <hud_stage / screen.py arguments ...>

A screen.py copy of the world has no media playing and no Spotify. This gives the copy both, as stand-ins, and lets
the page's buttons run the REAL home base code behind them:
  - a stand-in media session (Stand), what smtc.ps1 would say: two made-up songs with made-up art (drawn here, never
    anyone's), playing from 1:02 of 3:47 when the run starts; its controls change it as an app would;
  - a fake Spotify (fake_spotify.py), signed in through the real connect flow, its Liked Songs empty;
  - a bridge on 127.0.0.1 that the page's stand-in home base (window.pywebview.api.host) calls: each press goes to
    host_verbs.call with media.SESSION = the stand-in and media.LIKES = spotify_like.Library on the fake, and the
    row is written again as hud.py's say_desktop would (witnessed:media of the copy).
  Steps may also say `js stage({position: 200})` (a seek), `js stage({status: 'Paused'})` and so on: the stand-in's
  state, changed as the app would change it, and the row written again.
--empty: no media row at all (the calm empty state). --signed-out: the fake Spotify is not connected (the heart unknown).
It runs hud_stage.main (frost, stand-in windows) in this process, so the copy is sessions/<world>-screen-<this pid>.
Nothing reaches Windows' media session, Spotify, or Alex's library.
"""
import json
import os
import shutil
import sys
import uuid
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
WL = HERE.parent
sys.path.insert(0, str(WL))
import hud_stage      # noqa: E402  (puts the lab on sys.path)
import witnessed      # noqa: E402
import fake_spotify   # noqa: E402
import host_verbs     # noqa: E402
import media          # noqa: E402
import spotify_like   # noqa: E402
import put

SONGS = [{"title": "Night Drive", "artist": "Stand-in Band", "album": "Made Up For Tests", "end": 227.0,
          "colours": ((30, 215, 96), (18, 40, 70), (240, 180, 70))},
         {"title": "Glass Harbour (Extended Version) - Live at the Placeholder Hall, Second Night", "artist":
          "The Placeholders, Stand-in Band and the Made Up Orchestra", "album": "Second Fake Record", "end": 184.0,
          "colours": ((140, 110, 255), (30, 20, 50), (99, 226, 192))}]


def draw_art(i):
    """A made-up album cover: soft shapes on a gradient, 600 px square, in media/now-playing/stage-<i>.png."""
    from PIL import Image, ImageDraw, ImageFilter
    a, b, c = SONGS[i]["colours"]
    im = Image.new("RGB", (600, 600), b)
    d = ImageDraw.Draw(im)
    for y in range(600):
        t = y / 599
        d.line([(0, y), (600, y)], fill=tuple(round(b[k] * (1 - t) + a[k] * t * 0.55) for k in range(3)))
    d.ellipse([150, 120, 470, 440], fill=c)
    d.ellipse([60, 330, 300, 570], fill=a)
    im = im.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, 560, 560], outline=(255, 255, 255), width=3)
    out = media.ART / f"stage-{i}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return str(out)


class Stand:
    """A stand-in for media.Session: the state smtc.ps1 would print, and its controls changing it."""

    def __init__(self):
        self.arts = [draw_art(i) for i in range(len(SONGS))]
        self.i = 0
        self.s = None
        self.load(0, 62.0, "Playing")

    def load(self, i, position, status):
        x = SONGS[i]
        self.i = i
        self.s = {"app": "Spotify.exe", "title": x["title"], "artist": x["artist"], "album": x["album"],
                  "status": status, "position": position, "end": x["end"], "updated": time.time(),
                  "shuffle": False if self.s is None else self.s["shuffle"],
                  "repeat": "None" if self.s is None else self.s["repeat"], "art": self.arts[i],
                  "can": {"play": True, "pause": True, "next": True, "prev": True, "shuffle": True, "repeat": True}}

    def now(self):
        s = self.s
        return s["position"] + (time.time() - s["updated"] if s["status"] == "Playing" else 0)

    def start(self):
        return True

    def state(self, wait=0):
        return {"ok": True, "apps": ["Spotify.exe"], "s": dict(self.s)}

    def send(self, line):
        w = line.split()
        if w[0] == "toggle":
            pos = self.now()
            self.s.update(status="Paused" if self.s["status"] == "Playing" else "Playing", position=pos, updated=time.time())
        elif w[0] in ("next", "prev"):
            self.load((self.i + (1 if w[0] == "next" else -1)) % len(SONGS), 0.0, "Playing")
        elif w[0] == "shuffle":
            self.s["shuffle"] = w[1] == "on"
        elif w[0] == "repeat":
            self.s["repeat"] = {"none": "None", "list": "List", "track": "Track"}[w[1]]
        else:
            return False
        return True

    def stop(self):
        pass


def main():
    a = sys.argv[1:]
    if "--live" in a or "--on-screen" in a:
        raise SystemExit("music stage is sandbox-only")
    empty, signed_out = "--empty" in a, "--signed-out" in a
    a = [x for x in a if x not in ("--empty", "--signed-out")]
    session = f"{a[0]}-screen-{os.getpid()}"             # as hud_stage names the copy
    stand, fake = Stand(), fake_spotify.Fake()
    store = WL / ".tmp-agora" / ("music-stage-" + uuid.uuid4().hex)
    os.makedirs(store, exist_ok=True)  # inherited ACL; tempfile's mode 0700 breaks builder sandboxes
    lib = spotify_like.Library(store=store, api=fake.url + "/v1", accounts=fake.url, fresh=1)
    if not signed_out:
        lib.connect(fake_spotify.browser, "0123456789abcdef0123456789abcdef", port=0, wait=10)
    media.SESSION, media.LIKES = stand, lib

    class Hud:                                           # the home base, as host_verbs sees it
        def say_desktop(self):
            fake.playing = {"type": "track", "uri": f"spotify:track:stage{stand.i}", "name": stand.s["title"],
                            "artists": [{"name": stand.s["artist"]}]}
            if empty:
                witnessed.write(session, "media", [], by="music-stage")
                return
            rows = media.rows(session=stand, library=lib)
            if rows and rows[0]["liked"] == "unknown" and not signed_out:
                time.sleep(0.3)                          # the first ask of a song runs in the background
                rows = media.rows(session=stand, library=lib)
            witnessed.write(session, "media", rows, by="music-stage")
            print("stage: media row", json.dumps({k: rows[0][k] for k in ("title", "playing", "at", "liked", "shuffle", "repeat")} if rows else {}), flush=True)

    hud = Hud()

    class Bridge(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self._send(204, b"")

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            o = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/host":
                # Never let a test page open Alex's real browser/account flow.
                said = ("ERR Connect disabled in the stand-in" if o.get("verb") == "media.connect"
                        else host_verbs.call(hud, o.get("verb", ""), o.get("words", "")))
                print(f"stage: host {o.get('verb')} -> {said}", flush=True)
                time.sleep(0.2)                          # host_verbs' own say_desktop timer runs first
                hud.say_desktop()
            elif self.path == "/stage":
                if "position" in o:
                    stand.s.update(position=float(o["position"]), updated=time.time())
                if "status" in o:
                    stand.s.update(position=stand.now(), status=o["status"], updated=time.time())
                if "liked" in o:                         # liked or unliked in Spotify's own window
                    (fake.liked.add if o["liked"] else fake.liked.discard)(f"spotify:track:stage{stand.i}")
                    lib.known.clear()
                    time.sleep(0.3)
                hud.say_desktop()
                said = "ok staged"
            else:
                said = "ERR no such path"
            self._send(200, said.encode())

        def _send(self, code, body):
            self.send_response(code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *x):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Bridge)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    hud.say_desktop()
    js = ("(() => { const post = (p, o) => fetch(%s + p, {method: 'POST', body: JSON.stringify(o)}).then(r => r.text());"
          " window.pywebview = {api: {host: (verb, words) => post('/host', {verb, words})}};"
          " window.stage = o => post('/stage', o); return 'stand-in home base at ' + %s; })()") % (json.dumps(url), json.dumps(url))
    opts, k = [a[0]], 1                                  # the steps go after the options, as in hud_stage
    while k < len(a) and a[k].startswith("--"):
        n = 1 if a[k] in ("--reduced-motion", "--term", "--live", "--bare", "--busy", "--logged") else 2
        opts += a[k:k + n]
        k += n
    sys.argv = ["hud_stage.py"] + opts + ["js", js] + a[k:]
    original_run = hud_stage.screen.run

    async def prepared(*args, **kwargs):
        # screen.main has made its copy by now. Apply draft lenses to that copy
        # before the browser paints; never depend on live/source having landed.
        ask = put.explore(session, "worker-a6443")
        for line in put.lines(ask):
            target = line.split()[2]
            receipt = ask(f"{'look' if target.startswith('f') else 'read'} {target}\n{line}")
            if "ERR" in receipt or "refused" in receipt:
                raise RuntimeError("draft music setup refused: " + receipt[-600:])
        return await original_run(*args, **kwargs)

    hud_stage.screen.run = prepared
    try:
        hud_stage.main()
    finally:
        hud_stage.screen.run = original_run
        srv.shutdown()
        fake.close()
        witnessed.clear(session, "media")
        shutil.rmtree(store, ignore_errors=True)
        for f in stand.arts:
            Path(f).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
