"""test_witnessed: rows a program keeps beside the house reach a lens as a row source, and only while it runs (a5052).

    python test_witnessed.py

A small world in memory (roomworld.py); the witnessed files go to a temporary folder. The `windows` source is what the
window manager prototype (research/window-lab/wm.py) writes: one row per window it keeps on the screen, in its order.
  1. no host has said anything: `rows windows` is empty, and a lens over it compiles with no instances
  2. a host's rows: a lens repeats over them, each instance keyed by the row's name, fields read bare, in its order
  3. terms filter them as any source's (`windows collapsed=no`), and a `role ... when` reads a field
  4. the rows are not in the world: no event, the world unchanged
  5. a host that has stopped (its process gone) has no rows; its file is not believed
  6. the stamp deskd keys scenes by changes when the rows are rewritten, and when they are removed
  7. the door's stream says `world` with no id when the rows change, so a painter repaints (door._stream, read)
"""
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
import roomworld   # noqa: E402
import scene       # noqa: E402
import witnessed   # noqa: E402

witnessed.ROOT = Path(tempfile.mkdtemp(prefix="witnessed-"))
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
WORLD = "wmtest"
D._session = WORLD


def say(*lines, me="pike"):
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    out = ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": uuid.uuid4().hex})
        out = r.get("text") or ("ERR " + (r.get("error") or ""))
    return out


def esc(t):
    """Words going inside a quoted command: backslashes, quotes and dollars kept, newlines written as backslash n."""
    return t.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"').replace("$", chr(92) + "$").replace(chr(10), chr(92) + "n")


STRIP = "\n".join([
    "strip : row",
    "  big : row",
    "    share 3",
    "    of windows collapsed=no",
    "    each win",
    "  shelf : column",
    "    share 1",
    "    of windows collapsed=yes",
    "    each win",
    "win : column",
    "  share 1",
    "  role pane",
    "  role pinned when $pinned = yes",
    '  t : text "$title ($lens) #$order"',
])
STYLE = "\n".join(["role pane", "  pad 4", "role pinned", "  pad 8"])
say(f"look {R.BOARD} :1", f'do create {R.BOARD} kind=note tags=style title=wm-test-style text="{esc(STYLE)}"')
out = say(f'do create {R.BOARD} kind=note tags=lens title=wm-test style=wm-test-style text="{esc(STRIP)}"')
check("0. the layout lens is made", "ERR" not in out and "created" in out, out)


def keys(node, out=None):
    out = [] if out is None else out
    out.append(node.get("key"))
    for k in node.get("kids") or []:
        keys(k, out)
    return out


def build():
    sc, _ = scene.scene_for(D, "wm-test")
    return sc


# 1
sc = build()
check("1. no host: no rows, and the lens compiles with no instances", scene.rows(D, "windows") == []
      and not sc.get("refused") and not [k for k in keys(sc) if k and "/win" in k and k.count("/") > 2], sc.get("refused"))

# 2
ROWS = [{"name": "w1", "title": "design-review", "lens": "design-review", "kind": "agora", "pinned": "yes", "collapsed": "no", "focused": "no"},
        {"name": "w2", "title": "command-center", "lens": "command-center", "kind": "agora", "pinned": "no", "collapsed": "yes", "focused": "no"},
        {"name": "x1", "title": "Notepad", "lens": "", "kind": "adopted", "pinned": "no", "collapsed": "no", "focused": "yes", "hwnd": 1234}]
events = len(W.events)
witnessed.write(WORLD, "windows", ROWS, by="wm")
rows = scene.rows(D, "windows")
check("2. the host's rows, in its order, with order, age and by; a field the source does not name is not passed",
      [r["name"] for r in rows] == ["w1", "w2", "x1"] and [r["order"] for r in rows] == [1, 2, 3]
      and rows[0]["by"] == "wm" and rows[0]["age"] == 0 and "hwnd" not in rows[2], rows)
sc = build()
ks = keys(sc)
check("2. a lens repeats over them, each instance keyed by the row's name",
      "strip/big/w1" in ks and "strip/big/x1" in ks and "strip/shelf/w2" in ks, ks)

# 3
text = say("scene wm-test")
check("3. terms filter (collapsed ones on the shelf only), fields read bare, a role when a field says so",
      "design-review (design-review) #1" in text and "command-center (command-center) #2" in text
      and "Notepad () #3" in text and "win [pinned, since" in text and "shelf column share 1 · 1 of windows" in text, text[:3000])

# 4
check("4. the rows are not in the world: no event", len(W.events) == events, W.events[events:])

# 5
p = subprocess.Popen([sys.executable, "-c", "import sys, witnessed; witnessed.ROOT = __import__('pathlib').Path(sys.argv[1]);"
                      "witnessed.write('wmtest', 'windows', [{'name': 'ghost'}], by='gone')", str(witnessed.ROOT)], cwd=HERE)
p.wait()
check("5. a host that has stopped has no rows", witnessed.path(WORLD, "windows").exists() and scene.rows(D, "windows") == [],
      scene.rows(D, "windows"))

# 6
s0 = witnessed.stamp(WORLD)
time.sleep(0.02)
witnessed.write(WORLD, "windows", ROWS[:1], by="wm")
s1 = witnessed.stamp(WORLD)
witnessed.clear(WORLD, "windows")
s2 = witnessed.stamp(WORLD)
check("6. the stamp changes when the rows are rewritten and when they are removed", s0 != s1 and s1 != s2 and s2 == (), (s0, s1, s2))

# 7
src = (HERE / "door.py").read_text(encoding="utf-8")
check("7. the door's stream says world, with no id, when witnessed rows change",
      'put("world", {"witnessed"' in src and "witnessed.stamp(session)" in src)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
