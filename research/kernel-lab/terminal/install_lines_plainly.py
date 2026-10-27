"""install_lines_plainly: put the language Alex approved on 27 Oct 2026 into a running world, in order.

    python install_lines_plainly.py [--port 8810] [--world <desktop world dir>]

1. install_renames.py         one dotted spelling per family; old names stay aliases; help texts follow
2. install_topics.py          topic pages: missing ones made, ones only the installer has touched refreshed
3. help-fixes.lines           help texts that say the new words
4. the Appearance lens        its "use" button meant the place's theme; theme.use is yours by default now, so it
                              says for=place (only if the lens still has the old line)
Every step is ordinary undoable lines through the door, as Alex's agent; each prints what it did.
"""
import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
DESKTOP_WORLD = HERE.parents[1] / "window-lab" / "kernel-desktop" / "state" / "world"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8810)
    ap.add_argument("--world", default=str(DESKTOP_WORLD))
    a = ap.parse_args()
    common = ["--port", str(a.port), "--world", a.world]
    for step in ([str(HERE / "install_renames.py")],
                 [str(HERE / "install_topics.py"), "--refresh"],
                 [str(HERE / "install_topics.py"), "--file", str(HERE / "help-fixes.lines"), "--always"]):
        print(f"--- {Path(step[0]).name} {' '.join(step[1:])}", flush=True)
        subprocess.run([PY, *step, *common], check=True)
    print("--- the Appearance lens", flush=True)
    sessions = json.loads((Path(a.world) / "keep" / "sessions.json").read_text(encoding="utf-8"))
    token = next(t for t, v in sessions.items() if v.get("signer") == "claude")

    def say(route, line):
        req = urllib.request.Request(f"http://127.0.0.1:{a.port}/{route}", json.dumps({"line": line}).encode(),
                                     {"Content-Type": "application/json", "Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    old, new = "on use do theme.use $theme\n", "on use do theme.use $theme for=place\n"
    for row in say("see", "rows lens").get("rows", []):
        text = str(row.get("text") or "")
        if old in text:
            say("see", f"look {row['id']}")
            value = text.replace(old, new).replace("\\", "\\\\").replace('"', '\\"')     # real newlines stay
            out = say("do", f'set {row["id"]} text="{value}"')
            print(("ok     " if out.get("ok") else "REFUSED ") + f"{row.get('name') or row['id']}: "
                  + out.get("text", "").splitlines()[0][:120])
    print("done")


if __name__ == "__main__":
    main()
