# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_nearest (9 Oct 2026, step 7 of the grammar unification): lenses, styles and kinds resolve by place, nearest first,
as verbs do (verbs.ladder is the one lookup).

    python test_nearest.py

Two rooms each hold a lens titled cal, a style titled mood and a kind note titled event. From inside a room its own is
taken; a lens placing `lens cal` takes the one nearest its own room, whoever looks; a style is found from its lens's
room; a kind note describes the things in its room; from a corner, where neither is nearer, the lookup refuses naming
both doors instead of silently taking the first. Builds its own small world (roomworld.py).
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


D, R = roomworld.build()
W = D.world
LOUNGE, BOARD, CORNER = R.LOUNGE, R.BOARD, R.corner["juniper"]


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def reply(me, *lines):
    be(me)
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((line, r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def make(me, where, how):
    got = reply(me, f"look {where} :1", f"do create {where} {how}")
    assert not got[-1][2], f"setup refused: {got[-1]}"
    return W.last_created


import scene   # noqa: E402
import verbs   # noqa: E402

# 1. two lenses with one title, one per room
lc = make("juniper", LOUNGE, 'kind=note tags=lens title=cal text="root : text \\"lounge cal\\""')
bc = make("pike", BOARD, 'kind=note tags=lens title=cal text="root : text \\"board cal\\""')
reply("juniper", f"go {LOUNGE}")
t = reply("juniper", "scene cal")[-1]
check("scene cal in the Lounge is the Lounge's", not t[2] and "lounge cal" in t[1], t)
reply("juniper", f"go {BOARD}")
t = reply("juniper", "scene cal")[-1]
check("scene cal in the Board is the Board's", not t[2] and "board cal" in t[1], t)
reply("juniper", f"go {CORNER}")
t = reply("juniper", "scene cal")[-1]
check("from a corner, where neither is nearer, the lookup refuses naming both doors",
      t[2] and lc in t[2] and bc in t[2] and "Lounge" in t[2] and "Board" in t[2] and "neither is nearer" in t[2], t)
check("find_lens with the room given takes that room's", scene.find_lens(D, "cal", LOUNGE)["id"] == W.nodes[lc]["subject"]
      and scene.find_lens(D, "cal", BOARD)["id"] == W.nodes[bc]["subject"])

# 2. a lens placing `lens cal` takes the one nearest its own room, whoever looks from wherever
outer = make("juniper", LOUNGE, 'kind=note tags=lens title=outer text="root : column\\n  inner : lens cal"')
reply("pike", f"go {BOARD}")
t = reply("pike", "scene outer")[-1]
check("a Lounge lens placing cal shows the Lounge's cal, looked at from the Board", not t[2] and "lounge cal" in t[1] and "board cal" not in t[1], t)

# 3. a style is found from its lens's room
ls = make("juniper", LOUNGE, 'kind=note tags=style title=mood text="token ink = #111\\nrole a : ink"')
bs = make("pike", BOARD, 'kind=note tags=style title=mood text="token ink = #222\\nrole b : ink"')
la = make("juniper", LOUNGE, 'kind=note tags=lens title=styled style=mood text="root : text x, role a"')
ba = make("pike", BOARD, 'kind=note tags=lens title=styledb style=mood text="root : text x, role a"')
reply("pike", f"go {BOARD}")
t = reply("pike", "scene styled ok")[-1]
check("the Lounge's lens compiles under the Lounge's mood (role a), looked at from the Board", not t[2] and "compiles" in t[1], t)
t = reply("pike", "scene styledb ok")[-1]
check("the Board's lens under the Board's mood has no role a", "does not compile" in t[1] and "role" in t[1], t)
check("style_source from each room", scene.style_source(D, "mood", LOUNGE)["origin"] == W.nodes[ls]["subject"]
      and scene.style_source(D, "mood", BOARD)["origin"] == W.nodes[bs]["subject"])

# 4. a kind note describes the things in its room
import table   # noqa: E402
lk = make("juniper", LOUNGE, 'kind=note tags=kind title=event is=note text="A gathering.\\nseats : number"')
bk = make("pike", BOARD, 'kind=note tags=kind title=event is=note text="A board event.\\nseats : word"')
got = reply("juniper", f"look {LOUNGE} :1", f'do create {LOUNGE} kind=event title="Picnic" seats=lots')
check("in the Lounge, event's seats is usually a number: the receipt remarks", not got[-1][2] and "seats=lots kept" in got[-1][1], got[-1])
got = reply("pike", f"look {BOARD} :1", f'do create {BOARD} kind=event title="Meeting" seats=lots')
check("in the Board, event's seats is a word: no remark", not got[-1][2] and "kept" not in got[-1][1], got[-1])
check("declared reads by room", [s.type for s in table.declared(W, "event", LOUNGE)] == ["number"] and [s.type for s in table.declared(W, "event", BOARD)] == ["word"])
import kinds   # noqa: E402
note, others = kinds.note_for(W, "event", CORNER)
check("from a corner the first by id is read and the others are named", note["id"] == W.nodes[lk]["subject"] and [o["id"] for o in others] == [W.nodes[bk]["subject"]], (note, others))
got = reply("juniper", f"look {CORNER} :1", f'do create {CORNER} kind=event title="Here" seats=lots')
check("a thing made where neither note is nearer: the receipt says which was read and names both",
      not got[-1][2] and "2 kind notes are titled event" in got[-1][1] and "none is nearer" in got[-1][1], got[-1])

# 5. one name in one place is found from anywhere, as before (nothing single moved)
single = make("juniper", LOUNGE, 'kind=note tags=lens title=solo text="root : text solo"')
reply("pike", f"go {BOARD}")
t = reply("pike", "scene solo")[-1]
check("a lens with one holder is found from another room", not t[2] and "solo" in t[1], t)
reply("pike", f"go {CORNER}")
check("the ladder itself: a verb's levels and a note's are one function", verbs.ladder is not None and verbs.place_of_note(W, W.subjects[W.nodes[single]["subject"]]) == ("room", LOUNGE))

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
