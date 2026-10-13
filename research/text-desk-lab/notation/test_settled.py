"""test_settled: settled things fold, and say so (9 Oct 2026, a3806).

On a small world it builds itself (roomworld.build):
  - `settled` selects what is done, cured, answered... and `-settled` what is live; a promise that has ended is settled
  - a room with more than twelve things, some settled, shows the live ones at hand and says how many it left out
  - `look <room> :2` folds the same ones into one line that names the way to them (table in:<room>,settled)
  - a place whose things are all settled shows them (a shelf); so does a place with settled=shown; a small place folds nothing
  - nothing moved: every thing is where it was
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import roomworld

FAILED = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {detail}"))
    if not ok:
        FAILED.append(name)


d, R = roomworld.build()
W = d.world


def say(me, *lines):
    W.me = me
    out = []
    for l in lines:
        r = d.dispatch("desk", {"line": l, "whole": True})
        out.append(r.get("text") or "ERR " + r["error"])
    return "\n".join(out)


def made(t):
    return t.split("created ")[1].split()[0]


B = R.BOARD
say("pike", f"look {B} :2")
live = [made(say("pike", f'do create {B} kind=task title="Live {k}" status=open')) for k in range(8)]
done = [made(say("pike", f'do create {B} kind=task title="Done {k}" status=done')) for k in range(5)]
cured = made(say("pike", f'do create {B} kind=note title="A cured spot" status=cured'))
before = {i: W.nodes[i]["parent"] for i in live + done + [cured]}

t = say("pike", f"find in:{B},settled")
check("settled selects the done and the cured", all(i in t for i in done + [cured]) and not any(i in t for i in live), t)
t = say("pike", f"table in:{B},-settled")
check("-settled is what is live", all(i in t for i in live) and not any(i in t for i in done + [cured]), t)

t = say("sable", f"look {B}")
check("the room shows live things at hand and says how many settled it left out",
      f"(6 settled, not shown: table in:{B},settled lists them)" in t and not any(f"{i} " in t for i in done), t)
t = say("sable", f"look {B} :2")
check("look :2 folds them into one line that names the way to them",
      f"(6 settled, not shown: table in:{B},settled lists them)" in t
      and not any(f"{i} " in t for i in done) and all(f"{i} " in t for i in live), t)
t = say("sable", f"table in:{B},settled")
check("the line it names runs as printed and lists every one", all(i in t for i in done + [cured]) and "6 row(s)" in t, t)
t = say("sable", f"look {B} :3")
check("look :3 (the deep look, with its own cap) folds nothing as settled", "settled, not shown" not in t and f"{done[0]} " in t, t)

SH = made(say("pike", f'do create {B} kind=surface title="Done shelf"'))
say("pike", f"look {SH}")
shelf = [made(say("pike", f'do create {SH} kind=task title="Shelved {k}" status=done')) for k in range(14)]
t = say("sable", f"look {SH} :2")
check("a place whose things are all settled is a shelf: it shows them", all(f"{i} " in t for i in shelf) and "not shown" not in t, t)

say("pike", f"look {B} :1", f"do prop {B} settled=shown")
t = say("sable", f"look {B} :2")
check("settled=shown on a place shows them all", all(f"{i} " in t for i in done) and "settled, not shown" not in t, t)

L = R.LOUNGE
say("pike", f"look {L} :2")
one = made(say("pike", f'do create {L} kind=task title="A small done thing" status=done'))
t = say("sable", f"look {L} :2")
check("a small place folds nothing", f"{one} " in t and "not shown" not in t, t)
check("nothing moved", all(W.nodes[i]["parent"] == p for i, p in before.items()))

print()
print("all passed" if not FAILED else f"{len(FAILED)} failed: " + "; ".join(FAILED))
sys.exit(1 if FAILED else 0)
