"""test_media.py: the home base's music buttons, in a painted copy of a world (a5245). 15 Oct 2026.

    python test_media.py [world] [--as who]

Paints the home-base lens with screen.py (a copy of the world, headless), puts a stand-in for the host's js_api where
pywebview would put its own, runs media.CLICKS in the page as hud.py does, presses each button, and reads back what
the host was asked. Pressing the heading beside them must ask nothing. Nothing reaches Spotify: media.press() is the
host's, run by hand (`python media.py play`).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import media  # noqa: E402

SCREEN = HERE.parents[0] / "text-desk-lab" / "notation" / "screen.py"
TOP = "home/body/right/music/top"


def main():
    world = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "frontier-try"
    who = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else "worker-a5245"
    stub = "window.pywebview = {api: {media: a => { (window.__asked = window.__asked || []).push(a); return true; }}}; 1"
    steps = ["js", stub, "js", media.CLICKS,
             "click", f"{TOP}/play", "click", f"{TOP}/next", "click", f"{TOP}/prev", "click", f"{TOP}/head",
             "js", "window.__asked || []"]
    out = subprocess.run([sys.executable, str(SCREEN), world, "--as", who, "--lens", "home-base", "--size", "1600x900",
                          *steps], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    print(out)
    ok = '["play", "next", "prev"]' in out or '["play","next","prev"]' in out
    print("media buttons:", "ok" if ok else "NOT ok")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
