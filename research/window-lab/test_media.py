"""test_media.py: the home base's music panel, in a painted copy of a world (a5245; host verbs since a5592; Spotify's
look and Like since a6443). 17 Oct 2026.

    python research/window-lab/test_media.py [world] [--as who]      (default frontier-try, as alex)

1. The row (--logic-only, no screen): static event-reported progress, times, seeks,
   shuffle/repeat, player names and the art's path. Wall time never advances the bar.
2. The panel (home-music/stage.py: a stand-in media session, a fake Spotify; headless): the home-base lens is painted
   with the Music panel, a stand-in home base records what the painter asks, and each control is pressed: pause, next,
   back, shuffle, repeat, the heart; the title asks nothing. Nothing reaches Windows' media session, Spotify or anyone's
   library.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import media  # noqa: E402

fails = []


def check(what, ok, got=""):
    print(("ok   " if ok else "FAIL ") + what + ("" if ok else f"   (got {got!r})"))
    if not ok:
        fails.append(what)


# -- 1. the row
now = time.time()
s = {"app": "Spotify.exe", "title": "A", "artist": "B", "album": "C", "status": "Playing", "position": 60.0,
     "end": 200.0, "updated": now, "shuffle": True, "repeat": "Track", "art": str(media.ART / "0123456789abcdef.jpg"),
     "can": {"play": True, "pause": True, "next": True, "prev": False, "shuffle": True, "repeat": True}}
r = media.session_row(s, ("yes", ""))
want_at = "140 of 200"
check("playing: static reported position and remaining duration", r["at"] == want_at
      and r["position"] == 60 and r["remaining"] == 140 and r["elapsed"] == "1:00", r)
check("the length as m:ss", r["length"] == "3:20", r["length"])
check("shuffle on, repeat this song, player Spotify, liked yes",
      (r["shuffle"], r["repeat"], r["player"], r["liked"], r["playing"]) == ("on", "track", "Spotify", "yes", "yes"), r)
check("the controls the app offers", r["can"] == "play pause next shuffle repeat", r["can"])
check("the art as the desk names it", r["art"] == "media/now-playing/0123456789abcdef.jpg", r["art"])
s2 = {**s, "position": 61.2, "updated": now + 1.0}
check("a new playback position updates the static bar", media.session_row(s2)["position"] == 61.2)
check("wall clock alone does not advance the bar", media.progress(s, now=now + 90) == want_at)
s3 = {**s, "position": 150.0, "updated": now + 1.0}
check("a seek moves it", media.session_row(s3)["at"] != want_at)
p = media.session_row({**s, "status": "Paused", "position": 61.4})
check("paused: the seconds left, standing still", p["at"] == "139 of 200" and p["playing"] == "no", p["at"])
check("no length: no progress words", media.session_row({**s, "end": 0})["at"] == "")
check("Edge's session is named Edge", media.player_of("MSEdge") == "Edge" and media.player_of("Spotify.exe") == "Spotify")
check("repeat off reads off, no shuffle word when the app says none",
      (lambda x: (x["repeat"], x["shuffle"]))(media.session_row({**s, "repeat": "None", "shuffle": None})) == ("off", ""))

# -- 2. the panel, pressed
if "--logic-only" in sys.argv:
    print(f"{len(fails)} failed: static media rows; browser checks not run")
    sys.exit(1 if fails else 0)
world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "alex"
find = ("JSON.stringify([...document.querySelectorAll('[data-key]')].map(e => e.dataset.key)"
        ".filter(k => /lens:home-music-keys\\/keys\\/media$/.test(k) || /lens:home-music\\/music\\/playing\\/media\\/top$/.test(k)))")
stub = ("window.pywebview = {api: {host: (v, w) => { (window.__asked = window.__asked || []).push([v, w]); "
        "return Promise.resolve('ok ' + v); }}}; 1")
attempt = subprocess.run([sys.executable, str(HERE / "home-music" / "stage.py"), world, "--as", who, "--lens", "home-base",
                      "--size", "2560x1440", "wait", "1500", "js", find],
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
out = attempt.stdout
if attempt.returncode:
    print("browser stage failed (not a panel result):", attempt.stderr[-2000:])
keys = next((json.loads(json.loads(l)) for l in out.splitlines() if l.startswith('"[')), [])
row = next((k for k in keys if k.endswith("keys/media")), None)
top = next((k for k in keys if k.endswith("/top")), None)
check("the Music panel is painted with its controls and its song", bool(row and top), out[-800:])
if row and top:
    steps = ["wait", "1500", "js", stub]
    for part in ("pause", "next", "prev", "shuffle", "repeat"):
        steps += ["click", f"{row}/{part}", "wait", "200"]
    steps += ["click", f"{top}/like", "wait", "200", "click", f"{top}/words/title", "wait", "200",
              "js", "JSON.stringify(window.__asked || [])", "facts", top, "1"]
    out = subprocess.run([sys.executable, str(HERE / "home-music" / "stage.py"), world, "--as", who, "--lens", "home-base",
                          "--size", "2560x1440", *steps], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    asked = next((json.loads(json.loads(l)) for l in reversed(out.splitlines()) if l.startswith('"[')), None)
    want = [["media.play", ""], ["media.next", ""], ["media.prev", ""], ["media.shuffle", ""], ["media.repeat", ""],
            ["media.like", ""]]
    check("each control asks its host verb, the title asks nothing", asked == want, asked)
    check("nothing in the panel scrolls", "scrolls" not in out.split("facts", 1)[-1], out[-600:])

print(f"{'all ok' if not fails else str(len(fails)) + ' failed'}: the music panel")
sys.exit(1 if fails else 0)
