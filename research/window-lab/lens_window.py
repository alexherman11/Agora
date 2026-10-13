"""Open one lens of a world as its own window on the Windows desktop (13 Oct 2026, the first Agora window).

    python lens_window.py <lens> [--as alex] [--world frontier] [--size 1500,1000] [--at 200,120] [--term]

The window is Edge in app mode: the browser engine that ships with Windows, with no tabs or address bar, showing the
painter (lens.html) through the door on 8794. It runs on its own Edge profile under state/edge-profile, because a
window asked of the Edge that is already running in the background never appeared (ran 13 Oct: two tries, no window;
with its own profile, a window titled "Lens" and the desk reporting alex's painter within seconds).

Close the window to stop it. Nothing else is left running.
"""
import argparse
import subprocess
from pathlib import Path
from urllib.parse import urlencode

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = Path(__file__).resolve().parent / "state" / "edge-profile"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lens")
    ap.add_argument("--as", dest="who", default="alex")
    ap.add_argument("--world", default="frontier")
    ap.add_argument("--size", default="1500,1000")
    ap.add_argument("--at", default="200,120")
    ap.add_argument("--term", action="store_true", help="keep the desk terminal beside the lens")
    a = ap.parse_args()
    q = {"session": a.world, "as": a.who, "lens": a.lens}
    if not a.term:
        q["inspect"] = "0"
    PROFILE.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen([EDGE, f"--user-data-dir={PROFILE}", "--no-first-run", "--no-default-browser-check",
                          f"--app=http://localhost:8794/lens.html?{urlencode(q)}",
                          f"--window-size={a.size}", f"--window-position={a.at}"])
    print("window process", p.pid)


if __name__ == "__main__":
    main()
