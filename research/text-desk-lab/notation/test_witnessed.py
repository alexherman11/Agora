# health: room test (health.py runs every test_*.py with this line among its first ten)
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

# 8 (15 Oct, the home base): any program's rows under a name of its own, `witnessed:<name>`, every field it wrote
DESK = "\n".join([
    "screen : row",
    "  of witnessed:desktop program=notepad as w",
    "  each tile",
    "tile : column",
    "  role pane",
    "  role pinned when $w.front = yes",
    '  t : text "$w.title, $w.program, $w.order"',
])
say(f"look {R.BOARD} :1", f'do create {R.BOARD} kind=note tags=lens title=desk-test style=wm-test-style text="{esc(DESK)}"')
witnessed.write(WORLD, "desktop", [{"name": "131072", "title": "Notes", "program": "notepad", "front": "yes"},
                                   {"name": "65800", "title": "Inbox", "program": "outlook", "front": "no", "extra": {"a": 1}},
                                   {"name": "917504", "title": "Draft", "program": "notepad", "front": "no"}], by="hud")
rows = scene.rows(D, "witnessed:desktop")
check("8. witnessed:<name> passes every field the program wrote, with order, age and by",
      [r["name"] for r in rows] == ["131072", "65800", "917504"] and rows[1]["program"] == "outlook"
      and rows[1]["extra"] == '{"a": 1}' and rows[2]["order"] == 3 and rows[0]["by"] == "hud", rows)
sc, _ = scene.scene_for(D, "desk-test")
ks = keys(sc)
text = say("scene desk-test")
check("8. a lens repeats over it through a frame, keyed by name, terms filter, a role reads a field",
      "screen/131072" in ks and "screen/917504" in ks and "screen/65800" not in ks
      and "Notes, notepad, 1" in text and "Draft, notepad, 3" in text and "[pinned, since" in text, (ks, text[:2000]))
check("8. witnessed alone names no source; a stopped program's rows are none",
      scene.rows(D, "witnessed") is None and scene.rows(D, "witnessed:nobody") == [], scene.rows(D, "witnessed"))
witnessed.clear(WORLD, "desktop")

# 9 (15 Oct): a style's `align` says where a part stands across its parent's flow
import style as style_mod   # noqa: E402
lk = style_mod.looks("token ink = #111111\ntoken gap = 8\nrole a : align end, ink\nrole b : align left")["roles"]
check("9. align end is a look; align with another word is unread with the reason",
      lk["a"]["look"].get("align") == "end" and lk["b"]["unread"] and "start, center, end" in lk["b"]["unread"][0][1], lk)
js = (HERE / "desk-shell" / "style" / "style.js").read_text(encoding="utf-8")
check("9. the browser painter draws align as align-self", 'align: v => ({ "align-self"' in js)

print(f"{len(fails)} FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
