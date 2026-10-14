"""test_room_look (a948, rooms step 2c): look tells the truth: a room by name, the date, who's really here, and a
create's receipt that teaches $new.

    python test_room_look.py

Builds its own small world in memory (roomworld.py, a1190) and never saves it: every desk line runs through the
desk's own dispatch, as explore.py and deskd call it, with a reply token per reply (the harness of test_blanks.py). The
house's observations are faked in a temporary house-state directory; the real one is never touched.
"""
import json
import os
import re
import sys
import tempfile
import time
import uuid
from datetime import date, datetime, timedelta
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


def said(me, line):
    """One line in its own reply -> (line, text, error), the text without the '!! since your last look' catch-up."""
    line, text, err = reply(me, line)[-1]
    lines = text.splitlines()
    while lines and (lines[0].startswith("!!") or lines[0].startswith("   ")):
        lines.pop(0)
    return line, "\n".join(lines), err


def here_line(text):
    return next((l for l in text.splitlines() if l.startswith(("Here", "No one"))), "")


def here_names(text):
    """The 'Here: a, b.' line as a set: its order follows the corners' ids, which is not what these checks are about."""
    line = here_line(text)
    return set(line.split(":", 1)[1].strip().rstrip(".").split(", ")) if ":" in line else set()


import rooms   # noqa: E402
import scene   # noqa: E402

HOME, LOUNGE, BOARD = R.HOME, R.LOUNGE, R.BOARD
check("(setup) Home is the outermost room", rooms.home_room(W) == HOME)
TALK = R.TALK[LOUNGE]
corner = dict(R.corner)
print(f"built world (in memory): Home {HOME}, Lounge {LOUNGE} (talk {TALK}), Board {BOARD}, corners {corner}")

# 0. every wake still works: each resident's wake line, as the house sends it, runs whole
for a, c in corner.items():
    wake = str(W.nodes[c]["props"].get("wake") or "")
    got = reply(a, *[x.strip() for x in wake.split(";") if x.strip()])
    check(f"{a}'s wake ({wake!r}) runs whole and ends in a narration", got and not got[-1][2]
          and got[-1][1].startswith("You are in "), got[-1] if got else wake)
import house   # noqa: E402
import inspect   # noqa: E402
check("a corner with no wake= wakes to look (a1027: arrive retired with scripts)",
      '.get("wake") or "look"' in inspect.getsource(house.House.wake))
got = reply("claude", "run arrive")
check("run arrive refuses, naming the door (a1027: scripts are verbs now)",
      "run arrive is just arrive" in got[-1][2], got[-1])

# 1. look <room> by a word of its title, from elsewhere: narrated, and it says where you look from
reply("juniper", f"go {corner['juniper']} :1")
out = said("juniper", "look lounge")
check("look lounge from Juniper's corner narrates the Lounge, seen from her corner",
      not out[2] and out[1].startswith(f"Lounge ({LOUNGE}), seen from Juniper's corner ({corner['juniper']}).")
      and "Talk here" in out[1] and "Here with you" not in out[1], out)
check("from elsewhere, look does not move you", rooms.room_of(W, "juniper") == corner["juniper"])
out = said("juniper", f"look {LOUNGE}")
check("look <room id> narrates too", out[1].startswith(f"Lounge ({LOUNGE}), seen from"), out)
out = said("juniper", "look Juniper's corner")
check("look <a title of several words> narrates that room", out[1].startswith(f"You are in Juniper's corner"), out)
out = said("juniper", "look corner")
check("look corner is your own corner", out[1].startswith(f"You are in Juniper's corner"), out)
out = said("claude", "look corner")
check("look corner with no corner of your own names the corners", "names" in out[2] and "rooms" in out[2], out)

# 2. the tree is still there: with a depth, and for anything that is not a room
out = said("juniper", "look Board :2")
check("look Board :2 prints the tree as before", out[1].startswith(f"{BOARD} surface \"Board\"") and f"\n  {R.describe[BOARD]}" in out[1], out)
note = next(k["id"] for k in W.children(LOUNGE) if W.nodes[k["id"]]["type"] == "appearance")
out = said("juniper", f"look {note}")
check("look <a note> is unchanged", out[1].startswith(f"{note} "), out)
out = said("juniper", "look nowhere-at-all")
check("look <a word that names nothing> refuses as before", "no such id" in out[2], out)
out = said("alex", f"look {LOUNGE}")
check("Alex, who is not placed, keeps the tree for look <room>", out[1].startswith(f"{LOUNGE} surface"), out)

# 3. the date line: the desk's clock, the one $today and age< read (roomworld sets clock follow, as the live world is)
out = said("juniper", "look")
now = datetime.now()
today = D.today
line = out[1].splitlines()[1]
filled = said("juniper", f"do prop {corner['juniper']} a948today=$today")
check("with the clock on the wall date, the look says 'It is <day>, <HH:MM>' and the day is $today's",
      today == now.date().isoformat() and re.fullmatch(rf"It is {now.day} {now:%b}, \d\d:\d\d\.", line)
      and W.nodes[corner["juniper"]]["props"].get("a948today") == today, (line, today, filled))
back = (now.date() - timedelta(days=2)).isoformat()
said("juniper", f"clock {back}")
line = said("juniper", "look")[1].splitlines()[1]
d = date.fromisoformat(back)
check("a clock set two days back is said, both days named",
      line.startswith(f"The desk's clock says {d.day} {d:%b}, 2 days behind the house's time, {now.day} {now:%b}, "), line)
said("juniper", "clock follow")
check("clock follow joins them again", said("juniper", "look")[1].splitlines()[1].startswith("It is "))

# 4. presence: asleep (want=rest), resting (between turns), plain (in a turn now), from the house's observations
tmp = Path(tempfile.mkdtemp())
old = scene.HOUSE_STATE
scene.HOUSE_STATE = tmp
try:
    for a in ("pike", "sable", "juniper"):
        reply(a, f"go {LOUNGE} :1")
    (tmp / D._session).mkdir()
    (tmp / D._session / "house.json").write_text(json.dumps({"pid": 0, "beat": time.time(), "world": D._session, "residents": {
        corner["pike"]: {"actor": "pike", "doing": "resting"},
        corner["sable"]: {"actor": "sable", "doing": "working"},
        corner["juniper"]: {"actor": "juniper", "doing": "resting"}}}), encoding="utf-8")
    reply("alex", f"look {corner['juniper']} :1", f"do prop {corner['juniper']} want=rest")
    out = said("claude", "look lounge")[1]
    check("from elsewhere: 'Here: Sable, Pike (resting).' and 'Juniper is asleep here.'",
          here_line(out).startswith("Here: ") and here_names(out) == {"Sable", "Pike (resting)"}
          and "Juniper is asleep here." in out, out)
    out = said("pike", "look")[1]
    check("in the room: 'Here with you: Sable.' (Sable mid-turn is plain), Juniper asleep",
          "Here with you: Sable." in out and "Juniper is asleep here." in out, out)
    until = time.time() + 1800
    st = json.loads((tmp / D._session / "house.json").read_text(encoding="utf-8"))
    st["residents"][corner["pike"]]["rest_until"] = until
    (tmp / D._session / "house.json").write_text(json.dumps(st), encoding="utf-8")
    out = said("sable", "look")[1]
    check("a timed rest says until when", f"Pike (resting until {time.strftime('%H:%M', time.localtime(until))})" in out, out)
    out = said("claude", "go")[1]
    check("go alone uses the same words", "Pike (resting until" in out and "Juniper (asleep)" in out, out)
    st["beat"] = time.time() - 600
    (tmp / D._session / "house.json").write_text(json.dumps(st), encoding="utf-8")
    out = said("claude", "look lounge")[1]
    check("with the house stopped, no one it runs is called awake", "Pike (resting)" in out and "Sable (resting)" in out, out)
finally:
    scene.HOUSE_STATE = old
out = said("claude", "look lounge")[1]
check("with no house state (a copy, a test world), residents are named plain, as before",
      here_line(out).startswith("Here: ") and here_names(out) == {"Sable", "Pike"} and "Juniper is asleep here." in out, out)
reply("alex", f"look {corner['juniper']} :1", f"do prop {corner['juniper']} want=awake")

# 5. a948 (7): a look <room> from elsewhere counts the talk lines it prints whole as read, through a951's rule
reply("pike", f"go {HOME} :1", f"read {TALK} tail=20")      # an earlier look showed Pike a cut line: read it whole first
reply("sable", f'do append {TALK} line="a short line from sable"')
said("pike", "look lounge")
got = said("pike", f'do append {TALK} line="pike, having looked from Home"')
check("look lounge from Home, then speak there: the receipt names no unread lines",
      not got[2] and "haven't" not in got[1] and "from others" not in got[1], got)
reply("sable", f"read {TALK}")       # a5068: Pike spoke since Sable last read; unread, her line would wait
reply("sable", f'do append {TALK} line="{" ".join(["long"] * 50)}"')
said("pike", "look lounge")
got = said("pike", f'do append {TALK} line="again"')
check("a line the far look cut is not read", "shown cut" in got[1], got)

# 6. a948 (6): a create's receipt teaches $new, once per reply
got = reply("juniper", f"look {corner['juniper']} :1", f"do create {corner['juniper']} kind=note title=\"a948 one\"",
            f"do create {corner['juniper']} kind=note title=\"a948 two\"")
check("the first create in a reply teaches $new; the second does not",
      "(next lines in this reply can call it $new)" in got[1][1] and "$new" not in got[2][1], got)
got = reply("juniper", f"do create {corner['juniper']} kind=note title=\"a948 three\"")
check("a new reply teaches it again", "(next lines in this reply can call it $new)" in got[-1][1], got)
got = reply("juniper", f"do create {corner['juniper']} kind=note title=\"a948 four\"", "do tag $new add=a948",
            f"do create {corner['juniper']} kind=note title=\"a948 five\"")
check("once the word is used, no lesson follows it", "(next lines" not in got[2][1] and not got[1][2], got)
got = reply("juniper", f"do rename {corner['juniper']} title=\"Juniper's corner\"")
check("a line that makes nothing teaches nothing", "$new" not in got[-1][1] and "$new" not in got[-1][2], got)

print(f"\n{'all ok' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
