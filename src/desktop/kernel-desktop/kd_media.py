"""EDITING THE DESKTOP HOST (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
This file is a seam between the world and Windows: it turns world facts into screen effects and screen events into world
facts, through small words. It holds no preferences and no content. Which apps, what a button opens, sizes, names, ids and
who may do what live in settings things it reads (shell-settings, wm-settings). It does not seed the world at start
(people, chats, pins). New behaviour is a rule over the words offered here. Before writing a Windows or browser helper,
use the shared one (gaming_gate for full-screen and desktop tests, widget_browser for hidden pages) instead of a copy.

kd_media: the media words on the new kernel, a module (SHAPE 11) over desktop/media.py, unchanged.

Claude (PROOF a13428), 24 Oct 2026. The home base's media.* host words (host_verbs.py, a6443) press through Windows'
media session first (media.py); this module offers the same words to the kernel, so a lens, a button or an agent can
say them here:

    media.play    play or pause                  (do; it changes the outside world, so undo cannot take it back)
    media.next    the next song
    media.prev    the song before, or this one from its start
    media.now     what is playing: player, title, artist, playing yes|no   (see)

It also writes what is playing to <world>/modules/media/live.json every two seconds (key `media`), which the desk's
live layer (live.py) paints onto a widget that `shows=media`. Nothing is recorded: the song is not a fact of the world.
With --headless it starts no media session and answers from nothing playing (hidden tests).
Off switch: off media (the kernel ends the process; the session reader, a child, ends with its stdin).
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))                 # desktop: media.py
from modproto import Module, log                    # noqa: E402

HEADLESS = "--headless" in sys.argv


class Media:
    def __init__(self):
        self.home = None
        self.m = Module(offer=self.offer(), on_call=self.call, on_hello=self.hello, on_off=self.off)

    def offer(self):
        return [
            {"word": "media.play", "kind": "do", "takes": "[start=yes]", "may": "anyone",
             "help": "media.play [start=yes]: play or pause (a toggle) what Windows' media session names (Spotify, a "
                     "browser ...). With nothing named it presses nothing, unless start=yes."},
            {"word": "media.pause", "kind": "do", "takes": "", "may": "anyone", "undo": "external",
             "help": "media.pause: pause what is playing. Nothing playing: nothing is pressed, and it says so."},
            {"word": "media.resume", "kind": "do", "takes": "", "may": "anyone", "undo": "external",
             "help": "media.resume: play what is paused. Playing already, or nothing named: nothing is pressed."},
            {"word": "media.next", "kind": "do", "takes": "", "may": "anyone", "help": "media.next: the next song."},
            {"word": "media.prev", "kind": "do", "takes": "", "may": "anyone",
             "help": "media.prev: the song before, or this one from its start."},
            {"word": "media.shuffle", "kind": "do", "takes": "", "may": "anyone", "undo": "external",
             "help": "media.shuffle: toggle shuffle, only when the Windows session supports it."},
            {"word": "media.repeat", "kind": "do", "takes": "", "may": "anyone", "undo": "external",
             "help": "media.repeat: cycle off, list, track, only when the Windows session supports it."},
            {"word": "media.now", "kind": "see", "takes": "", "may": "anyone",
             "help": "media.now: what is playing now: the player, the song, the artist, and whether it plays."},
        ]

    def hello(self, msg):
        if msg.get("home"):
            self.home = Path(msg["home"])

    def now(self):
        if HEADLESS:
            return None
        import media
        st = media.SESSION.state() if media.SESSION.start() else None
        s = (st or {}).get("s") if (st or {}).get("ok") else None
        if not s or not (s.get("title") or "").strip():
            return None
        art = ''
        path = Path(s.get('art') or '')
        if path.is_file() and media.ART.resolve() in path.resolve().parents:
            import base64
            import io
            from PIL import Image
            try:
                with Image.open(path) as image:
                    image.thumbnail((480,480))
                    output = io.BytesIO()
                    image.convert('RGB').save(output, 'JPEG', quality=85)
                    art = 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii')
            except (OSError, ValueError):
                pass
        return {"player": media.player_of(s.get("app")) or "", "title": s.get("title") or "",
                "artist": s.get("artist") or "", "album": s.get("album") or "",
                "playing": s.get("status") == "Playing", 'art': art,
                "can": s.get("can") or {}, "shuffle": s.get("shuffle"),
                "repeat": s.get("repeat"),
                'position': s.get('position', 0), 'duration': s.get('end', 0), 'updated': s.get('updated', 0)}

    def call(self, msg):
        word = msg["word"]
        if word == "media.now":
            n = self.now()
            if not n:
                return {"text": "nothing is playing that Windows' media session names", "rows": []}
            return {"text": f"{n['title']} · {n['artist']} ({n['player']}, {'playing' if n['playing'] else 'paused'})",
                    "rows": [dict(n, kind="media")]}
        action = word.split(".", 1)[1]
        # honest no-ops (P3, Alex 27 Oct): press only when it does what was asked; otherwise say nothing was pressed
        n = self.now()
        kv = (msg.get("args") or {}).get("kv") or {}
        if action in ("shuffle", "repeat") and not (n and n.get("can", {}).get(action)):
            return {"refused": f"the media session does not support {action}; nothing pressed"}
        if action in ("pause", "resume"):
            if not n:
                return {"refused": "nothing is playing that Windows' media session names; nothing pressed"}
            if (action == "pause") != bool(n["playing"]):
                return {"refused": f"{n['title'] or n['player']} is {'paused' if action == 'pause' else 'playing'} "
                                   f"already; nothing pressed"}
            action = "play"
        elif action == "play" and not n and kv.get("start") != "yes":
            return {"refused": "nothing is playing that Windows' media session names, so play would press the play "
                               "key blind; nothing pressed (media.play start=yes presses it anyway)"}
        if HEADLESS:
            return {"external": True, "text": f"media.{action} (headless: nothing pressed)"}
        import media
        did = media.press(action)
        if not did:
            return {"refused": "neither the media session, Spotify nor the media key took it"}
        threading.Timer(0.6, self.write).start()
        return {"external": True, "text": f"media.{action} to {did}"}

    def write(self):
        if not self.home:
            return
        n = self.now()
        live = {"at": time.time(), "media": {
            "value": (f"{n['title']} · {n['artist']}" if n and n["artist"] else n["title"]) if n else "",
            "detail": ("playing" if n["playing"] else "paused") if n else "nothing playing",
            "glyph": ("⏸" if n["playing"] else "▶") if n else "▶"}}
        tmp = self.home / "live.json.tmp"
        try:
            tmp.write_text(json.dumps(live, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.home / "live.json")
        except OSError as exc:
            log(f"live.json: {exc!r}")

    def loop(self):
        while not self.m.closed.is_set():
            try:
                self.write()
            except Exception as exc:                # noqa: BLE001  a reading never stops the module
                log(f"media reading failed: {exc!r}")
            self.m.closed.wait(2)

    def off(self):
        try:
            if not HEADLESS:
                import media
                media.SESSION.stop()
        finally:
            os._exit(0)

    def run(self):
        self.m.run_reader()
        self.m.ready.wait(30)
        self.loop()


if __name__ == "__main__":
    Media().run()
