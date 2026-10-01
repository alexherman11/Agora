"""test_room_reads (a951, talk step 3a3): the lines a room's look prints whole are read; its hint names the world's
speaking verb.

    python test_room_reads.py

Builds its own small world in memory (roomworld.py, a1190) and never saves it: every desk line runs through the
desk's own dispatch, as explore.py and deskd call it, with a reply token per reply (the harness of test_blanks.py).
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
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build()
W = D.world


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

HOME, LOUNGE = R.HOME, R.LOUNGE
TALK = R.TALK[LOUNGE]
ME, OTHER = "pike", "juniper"
speakers = [s for s in verbs.all_verbs(W) if verbs.where(W, s)[0] == "house" and "say" in verbs._names(s["title"])]
print(f"built world (in memory): Lounge {LOUNGE} talk {TALK}; house verbs answering to say: "
      + ", ".join(W.appearances_of(s["id"])[0] for s in speakers))
check("(setup) one house verb answers to say", len(speakers) == 1, speakers)
reply(OTHER, f"go {LOUNGE} :1")
LONG = " ".join(["word"] * 50)
# the Lounge as residents leave it: lines Pike never read, the last one too long for a look to print whole
for k in range(4):
    reply("sable", f'do append {TALK} line="Sable: an older line {k}"')
reply("sable", f'do append {TALK} line="Sable: {LONG}"')


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
reply(ME, f"read {TALK}")       # caught up: the counts below are of lines made after this (a1190)

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
check("and the hint says a plain read shows them (no tail= guess)",
      look.splitlines()[-1].endswith(f"read {TALK})"), look.splitlines()[-1])


# 7. a986 (3a4), as lived 29 Sep 20:12: read; others add 8; the look shows the last 3; the 5 between are holes, not
# skipped: the receipt counts those 5 as unseen, a plain read shows all 8 oldest first, and the next receipt is quiet
def gap_lines(out):
    return [l for l in out.splitlines() if "gap line " in l]


def lived(how, tag):
    reply(ME, f"read {TALK}")
    for k in range(8):
        reply(OTHER, f'do append {TALK} line="Juniper: gap line {tag}{k}"')
    first = reply(ME, how)[-1][1]
    shown = gap_lines(first)
    check(f"{tag}: {how} shows only the last 3 of the 8", len(shown) == 3 and shown[-1].endswith(f"{tag}7"), first)
    got = reply(ME, f'do append {TALK} line="Pike: before reading, after the {tag} {how}"')
    check(f"{tag}: the receipt after it counts the 5 it skipped past as unseen (the 3 it showed whole were read)",
          "5 lines from others you haven't seen" in got[-1][1] and "shown cut" not in got[-1][1], got[-1][1])
    got = reply(ME, f"read {TALK}")[-1][1]
    check(f"{tag}: a plain read then shows all 8, oldest first",
          [l.split("gap line ")[-1] for l in gap_lines(got)] == [f"{tag}{k}" for k in range(8)], got)
    got = reply(ME, f'do append {TALK} line="Pike: read them, {tag}"')
    check(f"{tag}: and the next receipt is quiet", not got[-1][2] and "from others" not in got[-1][1], got[-1][1])


lived("look", "L")
lived(f"read {TALK} tail=3", "T")      # tail= is the same promise: a tail that doesn't reach your run skips nothing

# 7b. both kinds of hole at once: 4 skipped past, and the last of the 3 shown cut
reply(ME, f"read {TALK}")
for k in range(6):
    reply(OTHER, f'do append {TALK} line="Juniper: gap line M{k}"')
reply(OTHER, f'do append {TALK} line="Juniper: gap line M6 {LONG}"')
reply(ME, "look")
got = reply(ME, f'do append {TALK} line="Pike: mixed"')[-1][1]
check("skipped and cut together: '4 lines ... haven't seen; 1 line ... shown cut'",
      "4 lines from others you haven't seen; 1 line from others you were shown cut" in got, got)
got = reply(ME, f"read {TALK}")[-1][1]
check("and a plain read shows all 7, the cut one whole",
      [l.split("gap line ")[-1][:2] for l in gap_lines(got)] == [f"M{k}" for k in range(7)] and LONG in got, got)

print(f"\n{'all ok' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
