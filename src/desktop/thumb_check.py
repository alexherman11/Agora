"""thumb_check.py: where hud.py would draw the live window pictures, on a staged home base, and whether any of them
would paint over something it must not (a5736). Headless: nothing appears on the screen.

    python src/desktop/thumb_check.py [--size 2560x1440] [--scale 1.5]

A DWM picture paints over the whole page, so a tile cut at its panel's foot drew its window over the dock (Alex, 15
Oct). This runs hud.py's own SLOTS in hud_stage.py's copy (six stand-in windows), fits each as hud.fit does for a
1920x1080 window, and checks every picture lies inside the boxes that clip its tile and clear of the dock.
Prints one line per tile and 'ok' or what is wrong; exits 1 when something is wrong.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hud  # noqa: E402


def main():
    a = sys.argv[1:]
    size = a[a.index("--size") + 1] if "--size" in a else "2560x1440"
    scale = a[a.index("--scale") + 1] if "--scale" in a else "1.5"
    # screen.py prints at most 2000 characters of an answer: only the tiles, by the last step of their keys
    js = ("(() => { const s = (" + hud.SLOTS + ").filter(x => x.slot).map(x => ({...x, key: x.key.split('/').pop()}));"
          " const r0 = window.devicePixelRatio || 1;"
          " const d = [...document.querySelectorAll('[data-key]')].find(e => /(^|\\/)dock$/.test(e.dataset.key));"
          " const b = d && d.getBoundingClientRect();"
          " return {slots: s, dock: b ? [b.left * r0, b.top * r0, b.right * r0, b.bottom * r0] : null}; })()")
    f = Path(tempfile.mkdtemp()) / "slots.js"
    f.write_text(js, encoding="utf-8")
    out = subprocess.run([sys.executable, str(HERE / "hud_stage.py"), "frontier-try", "--as", "alex", "--lens", "home-base",
                          "--size", size, "--scale", scale, "wait", "2000", "js", "@" + str(f)],
                         capture_output=True, text=True, encoding="utf-8").stdout
    line = next((x for x in out.splitlines() if x.startswith("{")), None)
    if not line:
        print(out)
        sys.exit("thumb_check: the page did not answer")
    got = json.loads(line)
    dock, bad = got["dock"], []
    tiles = [s for s in got["slots"] if s["slot"]]
    print(f"{len(tiles)} tiles at {size} scale {scale}; dock {dock and [int(v) for v in dock]}")
    for s in tiles:
        r = hud.fit(s, 1920, 1080)
        name = s["key"].split("/")[-1]
        if not r:
            print(f"  {name}: not drawn (under 40% shows)")
            continue
        (x, y, x2, y2), _ = r
        print(f"  {name}: drawn {x},{y} {x2 - x}x{y2 - y}")
        cl, ct, cr, cb = s["clip"]
        if x < cl - 1 or y < ct - 1 or x2 > cr + 1 or y2 > cb + 1:
            bad.append(f"{name} outside the box that clips it")
        if dock and x < dock[2] and x2 > dock[0] and y < dock[3] and y2 > dock[1]:
            bad.append(f"{name} over the dock")
    print("ok" if not bad else "WRONG: " + "; ".join(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
