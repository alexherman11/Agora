"""test_media.py: the home base's music buttons, in a painted copy of a world (a5245; host verbs since a5592). 15 Oct 2026.

    python test_media.py [world] [--as who] [--live]      (--live: the live world, read as `who`; use your own name)

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
PANEL = "lens:home-music/music/top"                  # wherever the frame puts the panel (home-base's column, a5496's tiling)
WANT = [["media.play", ""], ["media.next", ""], ["media.prev", ""]]


def screen(world, who, *steps):
    live = ["--live"] if "--live" in sys.argv else []        # the real world through the door: presses ask a stand-in
    return subprocess.run([sys.executable, str(SCREEN), world, "--as", who, "--lens", "home-base", "--size", "1920x1080",
                           *live, *steps], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def answers(out):
    """What the js steps printed, as values (a JSON string that holds JSON is read twice)."""
    got = []
    for line in out.splitlines():
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, str) and v.startswith("["):
            v = json.loads(v)
        got.append(v)
    return got


def main():
    world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "alex"
    find = ("[...document.querySelectorAll('[data-key]')].map(e => e.dataset.key)"
            f".filter(k => k.endsWith('{PANEL}'))")
    tops = [v for v in answers(screen(world, who, "js", find)) if isinstance(v, list)]
    top = tops[0][0] if tops and tops[0] else None
    print("music panel:", top or "NOT painted")
    if not top:
        print("media buttons: NOT ok (no part keyed ...%s in home-base)" % PANEL)
        sys.exit(1)
    stub = ("window.pywebview = {api: {host: (v, w) => { (window.__asked = window.__asked || []).push([v, w]); "
            "return 'ok ' + v; }}}; 1")
    out = screen(world, who, "js", stub,
                 "click", f"{top}/play", "click", f"{top}/next", "click", f"{top}/prev", "click", f"{top}/head",
                 "js", "JSON.stringify(window.__asked || [])")
    print(out)
    asked = ([v for v in answers(out) if isinstance(v, list)] or [None])[-1]
    ok = asked == WANT
    print("asked:", asked)
    print("media buttons:", "ok" if ok else f"NOT ok (wanted {WANT})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
