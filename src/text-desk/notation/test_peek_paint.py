"""peek in a real browser (a1032, Pike's review): a peek shows only when its nearest folded ancestor is its own parent.
Something hidden between (a non-peek child of a folded part, or a fold inside a fold) keeps it hidden, so a folded
section never leaks pieces of its insides. The CSS decides this (lens.html), so only a painter can test it: this drives
screen.py (headless Chrome or Edge) on a scratch world and reads what was painted. Not part of health, which needs no
browser; run it after touching fold or peek in lens.js or lens.html.

    python test_peek_paint.py
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PROBE = "\n".join([
    "ws : column",
    '  a : column, fold "A"',                  # folded
    '    p1 : text "summary", peek',            # its own child: shown
    "    b : column",                           # a non-peek child: hidden
    '      p2 : text "leak one", peek',         # so this stays hidden
    '    g : column, fold "G"',                 # a fold inside the fold, not a peek: hidden
    '      p3 : text "leak two", peek',         # so this stays hidden
    '    x : text "inside"',                    # hidden
    '  o : column, fold "O" open',              # open
    '    h : column, fold "H"',                 # folded, inside an open part
    '      p4 : text "inner summary", peek',    # its nearest folded ancestor is its parent: shown
    '      y : text "inner inside"',            # hidden
])
SHOWN = {"ws/a/p1", "ws/o/h/p4"}
HIDDEN = {"ws/a/b", "ws/a/b/p2", "ws/a/g", "ws/a/g/p3", "ws/a/x", "ws/o/h/y"}


def main():
    import explore
    import screen
    if not any(os.path.exists(b) for b in screen.BROWSERS):
        print("skip: no Chrome or Edge to paint with")
        return
    d = explore.fresh()
    d.world.me = "alex"
    d.dispatch("desk", {"line": "look"})
    made = d.dispatch("desk", {"line": f"do create {d.world.root} kind=note title=peek-probe tags=lens text=" + '"' + PROBE.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'})
    assert "created" in (made.get("text") or ""), made
    world = "_test_peek_paint"
    path = HERE / "sessions" / f"{world}.pickle"
    explore.save_desk(path, d)
    try:
        out = subprocess.run([sys.executable, str(HERE / "screen.py"), world, "--as", "alex", "--lens", "peek-probe", "facts", "ws", "5"],
                             capture_output=True, text=True, timeout=180).stdout
    finally:
        for p in path.parent.glob(world + "*"):
            p.unlink(missing_ok=True)
    if "-v" in sys.argv:
        print(out)
    painted = {m.group(1) for m in re.finditer(r"^(ws[\w/]*): (?!hidden)", out, re.M)}
    assert "ws/a" in painted and "ws/o/h" in painted, out
    assert SHOWN <= painted, f"a peek of a folded parent was not painted: {SHOWN - painted}\n{out}"
    assert not (HIDDEN & painted), f"a folded part leaked its insides: {HIDDEN & painted}\n{out}"
    print(f"ok peek: {len(SHOWN)} shown, {len(HIDDEN)} kept hidden (nested peeks included)")


if __name__ == "__main__":
    main()
