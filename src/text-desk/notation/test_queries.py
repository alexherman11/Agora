# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_queries (8 Oct 2026, step 3 of the grammar unification): one term table for every selection.

    python test_queries.py

Any aspect or prop compares (k=v k!=v k<v k>v k<=v k>=v), typed as the lens types values; prop:k=v still reads, as
k=v; the fence's record of what a member was read by comes from the same table (knife.aspects_of); a row source may
be followed by terms over its fields, and find, count() and a lens's `of` read it so. Builds its own small world
(roomworld.py) and runs every line through the desk's own dispatch.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1200]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
CORNER, BOARD = R.corner[ME], R.BOARD


def reply(*lines, me=ME):
    W.me = me
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((line, r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def ids(sel):
    r = D._parse_selection(sel)
    return set(r[0]) if r else set()


def made(line):
    got = reply(f"look {CORNER} :1", line)
    return W.last_created, got


reply("clock 2026-10-09")
A, _ = made(f'do create {CORNER} kind=task title="Hall A" seats=20 owner=juniper due=2026-10-20 status=open')
B, _ = made(f'do create {CORNER} kind=task title="Hall B" seats=3 owner=pike due=2026-10-01 status=done')
C, _ = made(f'do create {CORNER} kind=task title="Hall C" seats=lots status=done')
N, _ = made(f'do create {CORNER} kind=note title="Plain note"')
MINE = {A, B, C, N}

# 1. comparisons, typed
check("seats>3 compares as numbers: 20 yes, 3 no, 'lots' never", ids(f"seats>3,in:{CORNER}") == {A}, ids(f"seats>3,in:{CORNER}"))
check("seats>=3 takes 3 too", ids(f"seats>=3,in:{CORNER}") == {A, B})
check("seats=20 is prop:seats=20", ids(f"seats=20,in:{CORNER}") == ids(f"prop:seats=20,in:{CORNER}") == {A})
check("status!=done needs the prop and another value", ids(f"status!=done,in:{CORNER}") == {A})
check("status=done through the one comparison, prop: optional", ids(f"status=done,in:{CORNER}") == ids(f"prop:status=done,in:{CORNER}") == {B, C})
check("due<2026-10-10 compares dates", ids(f"due<2026-10-10,in:{CORNER}") == {B})
check("due<=today uses the clock", ids(f"due<=today,in:{CORNER}") == {B})
check("due=2026-10-20 is a comparison of the field", ids(f"due=2026-10-20,in:{CORNER}") == {A})
check("owner!=pike is the person, not the spelling", ids(f"owner!=pike,in:{CORNER}") == {A})
check("a negated comparison leaves out what it would select", ids(f"-seats>3,kind:task,in:{CORNER}") == {B, C})
check("title=\"Hall A\" is exact; title:hall contains", ids(f"title=Hall,in:{CORNER}") == set() and ids(f"title:hall,in:{CORNER}") == {A, B, C})
got = reply(f"find kind=task")
check("kind is not compared: say kind:task", got[-1][2] and "kind:<kind>" in got[-1][2], got[-1])
got = reply(f"find seats>")
check("a comparison with no value refuses", got[-1][2] and "has no value" in got[-1][2], got[-1])
got = reply(f"do tag seats>3,in:{CORNER} add=big")
check("a verb takes a compared term as its target", not got[-1][2] and ids("tag:big") == {A}, got[-1])
got = reply(f"find in:{CORNER},status=done")
check("find reads a compared term after another", B in got[-1][1] and C in got[-1][1] and A not in got[-1][1], got[-1])

# 2. the fence reads the same table
import knife   # noqa: E402
check("the aspects a compared term reads: prop:seats; due< reads due; title= reads title",
      knife.aspects_of("seats>3") == ({"prop:seats"}, {"place"}) and knife.aspects_of("due<2026-10-10") == ({"due"}, {"place"})
      and knife.aspects_of("title=x,tag:y") == ({"title", "tags"}, {"place"}), knife.aspects_of("seats>3"))
import lens_ir   # noqa: E402
check("lens_ir.term_aspects is knife.aspects_of", lens_ir.term_aspects("prop:status=done,in:f01") == knife.aspects_of("prop:status=done,in:f01"))

# 3. a row source with terms over its fields
TALK = R.TALK[BOARD]
reply(f"go {BOARD} :1", f'do append {TALK} line="one from juniper"')
reply(f'do append {TALK} line="one from pike"', me="pike")
reply(f'do append {TALK} line="two from juniper"', me=ME)
import scene   # noqa: E402
rs = scene.rows(D, f"messages:{TALK} who=Juniper")
check("rows <source> k=v keeps the rows whose field compares", rs is not None and len(rs) == 2 and all("juniper" in r["said"] for r in rs), rs)
rs2 = scene.rows(D, f"messages:{TALK} index>3")
check("a numeric field compares as a number", rs2 is not None and [r["index"] for r in rs2] == [4], rs2)
got = reply(f"find messages:{TALK} who=Pike")
check("find <source> <terms> prints the rows", "find messages:" in got[-1][1] and ": 2 " in got[-1][1] and "juniper" not in got[-1][1], got[-1])
got = reply(f"rows messages:{TALK} tag:x")
check("a term that is not a comparison is refused on a source", got[-1][2] and "fields" in got[-1][2], got[-1])
got = reply(f"look {CORNER} :1", f"do prop {CORNER} nj=$(count(messages:{TALK} who=Juniper)) nt=$(count(kind:task,seats>3,in:{CORNER}))")
props = W.nodes[CORNER].get("props") or {}
check("count() in a command counts a source's rows and a compared selection", props.get("nj") == "2" and props.get("nt") == "1", (got, props))

# 4. in a lens
LENS = "\n".join([f"root : column, let big = count(kind:task,seats>3,in:{CORNER}), of messages:{TALK} who=Juniper as m, each line",
                  '  head : text "$(big) big halls"',
                  'line : text "$m.said"'])
esc = LENS.replace('"', '\\"').replace("$", "\\$")
got = reply(f"look {CORNER} :1", f'do create {CORNER} kind=note tags=lens title=qlens text="{esc}"')
sc, text = lens_ir.scene_for(D, "qlens")
kids = [k for k in sc["kids"] if k.get("text")]
check("a lens repeats over a source with terms and counts a compared selection",
      not got[-1][2] and any(k["text"] == "1 big halls" for k in kids) and sum(1 for k in kids if "juniper" in (k["text"] or "")) == 2,
      (got[-1][2], [k.get("text") for k in kids]))

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
