"""Names, not ids (a6109): how many raw ids a person can read on each of the home base's main screens, on a copy.

    python research/window-lab/names/audit.py <world> [--tag before|after] [--out <dir>]

Each screen is one screen.py run on a fresh copy of <world> as alex, at Alex's size (2560x1440): the home screen; the
Conversation's Everything feed; the board panel's lens (home-board, a5548) opened in the viewer; a waiting item
opened; the Writing room (its dock icon). The ids named are frontier's of 16 Oct (the viewer note a5482, f155).
ids_audit.js counts every id-shaped word that is drawn, unhidden, inside the window and not cut by a scrolling box,
and names the part it is in. Shots go to <out>/screen-<tag>-<screen>.png (screen-*.png is ignored by git)."""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LAB = HERE.parents[1] / "text-desk-lab" / "notation"
SCREENS = [("home", None), ("everything", "tabs/all"), ("board", ["desk", "look a5482", "desk", "do prop a5482 viewing=a5548 back=f155"]),
           ("waiting", r"rx:lens:waiting-on-me/waiting/mine/a\d+/now/a\d+/head$"), ("writing", "text:Writing room")]


def run(world, tag, out):
    rows = {}
    for name, press in SCREENS:
        steps = ["js", "document.body.style.background='#1b1f27'", "wait", "1200"]
        if isinstance(press, list):                   # desk lines on the copy, as alex (the board panel's lens, opened)
            steps += press + ["wait", "2500"]
        elif press:
            steps +=["js", f"window.PRESS={json.dumps(press)}", "js", f"@{HERE / 'press.js'}", "wait", "2500"]
        steps += ["js", f"@{HERE / 'ids_audit.js'}", "shot", str(out / f"screen-{tag}-{name}.png")]
        said = subprocess.run([sys.executable, str(LAB / "screen.py"), world, "--as", "alex", "--lens", "home-base", "--size", "2560x1440", *steps],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600).stdout
        got = []
        for x in said.splitlines():
            if x.startswith('{"visible"'):
                try:
                    got.append(json.loads(x))
                except ValueError:
                    got.append({"error": "the audit's answer was cut: " + x[:200]})
        pressed = [x for x in said.splitlines() if x.startswith('"') and "home/" in x or x.startswith('"none')]
        rows[name] = got[0] if got else {"error": said[-600:]}
        r = rows[name]
        print(f"{tag} {name}: {r.get('visible', '?')} raw id(s) visible" + (f"  (pressed {pressed[0][:90]})" if pressed else ""))
        for i, where in (r.get("ids") or {}).items():
            print(f"    {i}: {where[:160]}")
    return rows


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d       # noqa: E731
    out = pathlib.Path(opt("--out", ".")).resolve()
    rows = run(argv[0], opt("--tag", "now"), out)
    print("total:", sum(r.get("visible", 0) for r in rows.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
