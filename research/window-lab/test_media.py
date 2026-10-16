"""test_media.py: the home base's music buttons, in a painted copy of a world (a5245; host verbs since a5592). 15 Oct 2026.

    python test_media.py [world] [--as who]

Paints the home-base lens with screen.py (a copy of the world, headless), puts a stand-in for the home base's js_api
where pywebview would put its own, presses each button of the music panel (lens home-music, a5592) and reads back what
the host was asked: the buttons ask by host verbs (`on click host media.play`, a5300), so the painter sends
host("media.play", "") and nothing else. Pressing the heading beside them must ask nothing. Nothing reaches Spotify:
host_verbs.call() and media.press() are the home base's, run by hand (`python media.py play`).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCREEN = HERE.parents[0] / "text-desk-lab" / "notation" / "screen.py"
TOP = "home/body/right/music/lens:home-music/music/top"
WANT = [["media.play", ""], ["media.next", ""], ["media.prev", ""]]


def main():
    world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "alex"
    stub = ("window.pywebview = {api: {host: (v, w) => { (window.__asked = window.__asked || []).push([v, w]); "
            "return 'ok ' + v; }}}; 1")
    steps = ["js", stub,
             "click", f"{TOP}/play", "click", f"{TOP}/next", "click", f"{TOP}/prev", "click", f"{TOP}/head",
             "js", "JSON.stringify(window.__asked || [])"]
    out = subprocess.run([sys.executable, str(SCREEN), world, "--as", who, "--lens", "home-base", "--size", "1600x900",
                          *steps], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    print(out)
    asked = None
    for line in out.splitlines():                    # the js step prints its answer as JSON: here a JSON string
        try:
            v = json.loads(line)
            asked = json.loads(v) if isinstance(v, str) and v.startswith("[") else asked
        except ValueError:
            pass
    ok = asked == WANT
    print("asked:", asked)
    print("media buttons:", "ok" if ok else f"NOT ok (wanted {WANT})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
