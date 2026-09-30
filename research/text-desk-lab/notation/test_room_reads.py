"""test_room_reads (a951, talk step 3a3): the lines a room's look prints whole are read; its hint names the world's
speaking verb.

    python test_room_reads.py [world]        default frontier-try

Loads the world into memory and never saves it: every desk line runs through the desk's own dispatch, as explore.py
and deskd call it, with a reply token per reply (the harness of test_blanks.py).
"""
import os
import pickle
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

WORLD = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D = pickle.loads((HERE / "sessions" / f"{WORLD}.pickle").read_bytes())
W = D.world
D._session = WORLD + "-inmemory"


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


import rooms   # noqa: E402
import verbs   # noqa: E402

HOME = rooms.home_room(W)
talky = [f for f in rooms.all_rooms(W) if (W.nodes[f].get("props") or {}).get("role") == "room" and (W.nodes[f].get("props") or {}).get("talk")]
LOUNGE = next(f for f in talky if W.nodes[f]["title"] == "Lounge")
TALK = W.nodes[LOUNGE]["props"]["talk"]
ME, OTHER = "pike", "juniper"
speakers = [s for s in verbs.all_verbs(W) if verbs.where(W, s)[0] == "house" and "say" in verbs._names(s["title"])]
print(f"world {WORLD} (in memory): Lounge {LOUNGE} talk {TALK}; house verbs answering to say: "
      + ", ".join(W.appearances_of(s["id"])[0] for s in speakers))
reply(OTHER, f"go {LOUNGE} :1")
LONG = " ".join(["word"] * 50)


def behind(out):
    return [l for l in out.splitlines() if "haven't seen" in l or "haven't read" in l]


# 0. the live Lounge as it is: whatever its look cuts is said as cut, never as unseen
look = reply(ME, f"go {HOME} :1", f"go {LOUNGE}")[-1][1]
shown = look.split("the last lines:")[-1].splitlines()[1:-1]
got = reply(ME, "say having looked at the Lounge as it is")
cuts = sum(l.endswith("…") and not l.strip().startswith("Pike:") for l in shown)
check(f"the Lounge as it is ({cuts} of its shown lines cut): the receipt says no line unseen"
      + (f", and {cuts} shown cut" if cuts else ""),
      "haven't seen" not in got[-1][1] and "haven't read" not in got[-1][1]
      and ((f"{cuts} line" in got[-1][1] and "shown cut" in got[-1][1]) if cuts else "shown cut" not in got[-1][1]), (shown, got))

# 1. look, then say: nothing new since the look, so the receipt names no one else's lines
for k in range(3):
    reply(OTHER, f"say short line {k}")
reply(ME, "look")
look = reply(ME, f"go {HOME} :1", f"go {LOUNGE}")[-1][1]
check("the look ends with a hint naming the world's speaking verb (say <words>)",
      "(say <words>" in look.splitlines()[-1], look)
got = reply(ME, "say first, having only looked")
check("go lounge, then say: the receipt mentions no others", not got[-1][2] and not behind(got[-1][1]), got)

# 1b. narrated from elsewhere (a948 will call narrate so), say would land in your own room: the hint must not offer it
reply(ME, f"go {HOME} :1")
far = rooms.narrate(D, LOUNGE).splitlines()[-1]
check("the Lounge narrated from Home does not offer a $here verb", "(say <words>" not in far and "do append" in far, far)

# 2. another actor speaks between the look and the line
reply(ME, f"go {HOME} :1", f"go {LOUNGE}")
reply(OTHER, "say a line after pike looked")
got = reply(ME, "say second")
check("someone speaks after the look: '1 line from others you haven't seen'",
      not got[-1][2] and "1 line from others you haven't seen" in got[-1][1], got)

# 3. a line the look cuts is not read, for the receipt
reply(OTHER, f"say {LONG}")
look = reply(ME, "look")[-1][1]
check("the long line is cut in the look", "…" in look, look)
got = reply(ME, "say third")
check("a cut line is not read: the receipt counts it, as shown cut",
      not got[-1][2] and "1 line from others you were shown cut" in got[-1][1] and "haven't seen" not in got[-1][1], got)
got = reply(ME, f"read {TALK}")
check("a plain read after the look shows the cut line whole", LONG in got[-1][1], got)
got = reply(ME, "say fourth")
check("and then the receipt is quiet", not got[-1][2] and "from others" not in got[-1][1], got)

# 4. a room whose talk the look prints whole unlocks rewrite; one with a cut line does not
for name, last, want in (("Nook", "Juniper: short too", True), ("Den", "Juniper: " + LONG, False)):
    out = reply(OTHER, f"look {HOME} :1", f'do create {HOME} kind=surface title="{name}"')
    fid = next((f for f, n in W.nodes.items() if n["type"] == "surface" and n["title"] == name), None)
    out += reply(OTHER, f'do create {fid} kind=chat title="{name} talk" text="Juniper: hello\\nJuniper: {last}"')
    cid = next((s["id"] for s in W.subjects.values() if s["title"] == f"{name} talk"), None)
    if not (fid and cid):
        check(f"{name}: the room and its talk were made", False, out)
        continue
    reply(OTHER, f"do prop {fid} role=room talk={cid}")
    look = reply(ME, f"go {fid}")[-1][1]
    got = reply(ME, f'do rewrite {cid} text="Pike: only me"')
    ok = (not got[-1][2]) == want
    check(f"{name}: two lines, the last {'whole' if want else 'cut'}: rewrite {'allowed' if want else 'refused'}",
          ok, (look, got))

# 5. the hint is found in the world: with say off the house, the room falls back to the append form
reply(OTHER, f"go {LOUNGE} :1")
for s in speakers:
    (s.get("props") or {}).pop("on", None)        # carried by its maker now, as with on= removed
look = reply(ME, f"go {HOME} :1", f"go {LOUNGE}")[-1][1]
check("with say's on=house removed, the hint falls back to do append",
      f'(say: do append {TALK} line="..."' in look.splitlines()[-1], look.splitlines()[-1])

# 6. a gap: lines added after your run and before those the look shows are named, not forgotten
for k in range(5):
    reply(OTHER, f'do append {TALK} line="filler {k}"')
look = reply(ME, "look")[-1][1]
check("lines between your last read and the look are counted in the hint",
      "2 earlier lines from others you haven't read" in look.splitlines()[-1], look.splitlines()[-1])

print(f"\n{'all ok' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
