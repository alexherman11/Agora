# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_help_notes (a1595): help lives in the world, as notes in the Help binder; the code keeps a floor; helpnotes.check
keeps the notes true to the code.

    python test_help_notes.py

Builds its own small world in memory (roomworld.py) and never saves it. In order:
  1. no Help binder: help <command>, help <verb> and help alone answer from the floor and say the note is missing;
     a word help doesn't know still lists every door. Help never goes blank.
  2. a Help binder (a surface with prop role=help) with notes: help <word> prints the note's text exactly, by any
     word of its title; help alone prints the note titled manual; a note tagged topic is listed among the topics
  3. a resident changes a note with replace: the next help shows it, and the receipt says help reads it
  4. an empty note, or one moved out of the binder: the floor again, saying so
  5. the check: a command or verb with no note; a note that no longer names an argument; and an argument taken out of
     the code while its note still names it fails, naming the note, its maker and the code's place. An edit that
     names an argument the code doesn't take is told to its editor, in the receipt.
"""
import os
import re
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
import helpnotes   # noqa: E402
import moo   # noqa: E402


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


def one(me, line):
    _, text, err = reply(me, line)[-1]
    # the !! line, and a ~ line telling the note's maker someone changed it (that is how a maker hears), come first
    return re.sub(r"^(?:(?:!!|~) .*\n)+", "", text), err


ME = "pike"

# ---- 1. no Help binder: the floor ------------------------------------------------------------------------------------
t, e = one(ME, "help history")
check("no binder: help history is the floor: its arguments from the code, and that the note is missing",
      not e and t.splitlines()[0] == "history [<id>]" and "no note says this yet" in t, (t, e))
t, e = one(ME, "help create")
check("no binder: help create is the registry's own entry (doc, args, example), and that the note is missing",
      not e and t.startswith("create  (on: surface; level 1)") and "args: kind=" in t and "no note says this yet" in t, t)
t, e = one(ME, "help")
check("no binder: help alone lists every command with its arguments, and says the manual note is missing",
      not e and t.startswith("commands:") and "  table <selection> [cols=" in t and "help manual" in t, t)
t, e = one(ME, "help x")
check("no binder: help x (an alias) is examine's floor", not e and t.startswith("examine <id>"), t)
t, e = one(ME, "help zzzq")
check("no binder: a word help doesn't know still lists commands, verbs, and says there are no topics here",
      not e and t.startswith("no command, verb or topic") and "  verbs: move" in t and "topics: none here" in t, t)
probs = helpnotes.check(D)
check("no binder: the check says so, in one line", probs and probs[0].startswith("no Help binder"), probs)

# ---- 2. a Help binder with notes -------------------------------------------------------------------------------------
HIST = ("history [id]: the latest events, newest last, each with its event id (e12): who did what to which id, via\n"
        "  which verb or rule. history <id> only those about one thing.")
CREATE = ("create  (on: surface; level 1)\n  Make a new thing inside this surface.\n  args: kind=note|task title=<str> "
          "[text=<str>] [due=YYYY-MM-DD] [tags=a,b] [layout=column|row|free] [query=<selection>] [any other key: a prop]"
          "\n  e.g. do create f03 kind=task title=\"Send parser\" due=2026-09-19")


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


out = reply(ME, f"look {R.HOME} :1", f"do create {R.HOME} kind=surface title=Help layout=column", "do prop $new role=help")
HB = helpnotes.binder(W)
check("a surface with prop role=help is the Help binder", HB and W.nodes[HB]["title"] == "Help", out)
out = reply(ME, f"look {HB} :1", f"do create {HB} kind=surface title=Commands layout=column")
SUB = W.last_created
made = reply(ME, f"look {SUB} :1",
             f"do create {SUB} kind=note title=history text={q(HIST)}",
             f"do create {HB} kind=note title=create text={q(CREATE)}",
             f"do create {HB} kind=note title=\"examine|x|ex\" text=\"examine <id>: one thing in depth.\"",
             f"do create {HB} kind=note title=manual text=\"the manual, from its note\"",
             f"do create {HB} kind=note title=rooms tags=topic text=\"rooms: you are always in one room.\"")
check("the notes are made", all(not e for _, _, e in made), made)
receipt = made[1][1]
check("making a help note: its receipt says which help reads it now", "~ help note: help history reads this now" in receipt,
      receipt)
t, e = one(ME, "help history")
check("help history prints its note's text, word for word (a note in a binder inside the Help binder)", t == HIST, t)
t, e = one(ME, "help create")
check("help create prints its note's text, word for word", t == CREATE, t)
t, e = one(ME, "help ex")
check("help ex: any word of a note's title answers", t == "examine <id>: one thing in depth.", t)
t, e = one(ME, "help")
check("help alone prints the note titled manual", t == "the manual, from its note", t)
t, e = one(ME, "help zzzq")
check("a note tagged topic is listed among the topics", "  topics: rooms" in t, t)
t, e = one(ME, "help table")
check("a command whose note is missing still answers from the floor", t.startswith("table <selection>")
      and "no note says this yet" in t, t)

# ---- 3. a resident changes a note with replace; the next help shows it -----------------------------------------------
HID = next(aid for words, s, aid in helpnotes.entries(W) if words == ["history"])
out = reply("sable", f"read {HID} :3", f'do replace {HID} old="the latest events" new="the most recent events"')
check("sable replaces a word in the history note: ok, and the receipt says help history reads it",
      not out[-1][2] and "~ help note: help history reads this now" in out[-1][1], out)
t, e = one(ME, "help history")
check("the next help history shows sable's words (no commit, no restart: the note is the help)",
      t == HIST.replace("the latest events", "the most recent events"), t)

# ---- 4. an empty note, or a note moved out: the floor ----------------------------------------------------------------
EXID = next(aid for words, s, aid in helpnotes.entries(W) if "x" in words)
reply(ME, f"look {EXID} :1", f'do rewrite {EXID} text=" "')
t, e = one(ME, "help examine")
check("an empty note: help examine answers from the floor, saying so", t.startswith("examine <id>\n")
      and "no note says this yet" in t, t)
reply(ME, f"look {HID} :1", f"look {R.SHELF} :1", f"do move {HID} into={R.SHELF}")
t, e = one(ME, "help history")
check("a note moved out of the binder is no longer help: the floor answers", t.startswith("history [<id>]")
      and "no note says this yet" in t, t)
reply(ME, f"look {HID} :1", f"look {SUB} :1", f"do move {HID} into={SUB}")

# ---- 5. the check ----------------------------------------------------------------------------------------------------
probs = helpnotes.check(D)
check("the check names each command and verb that has no note (table among them)",
      any(p.startswith("no help note for table: ") and "USAGE['table']" in p for p in probs)
      and any(p.startswith("no help note for move: ") and "moo.py:" in p for p in probs), probs[:5])
check("the check names the empty note", any("says nothing" in p and "examine|x|ex" in p for p in probs), probs)
mine = [p for p in probs if '"create"' in p]
check("the create note names every argument create takes: nothing said of it", not mine, mine)
CID = next(aid for words, s, aid in helpnotes.entries(W) if words == ["create"])
v = moo.REGISTRY["create"]
args0 = v.args
try:
    v.args = args0.replace(" [due=YYYY-MM-DD]", "")          # due= taken out of the code; the note still names it
    probs = [p for p in helpnotes.check(D) if '"create"' in p]
    hit = [p for p in probs if "args: line names due=" in p]
    check("due= taken out of create's code, its note unchanged: the check fails, naming the note, its maker and the "
          "code's place", hit and f"help note {CID} \"create\" (made by {ME})" in hit[0] and "moo.py:" in hit[0], probs)
finally:
    v.args = args0
probs = [p for p in helpnotes.check(D) if '"create"' in p]
check("put back: nothing said of create", not probs, probs)
try:
    v.args = args0 + " [color=<name>]"                     # an argument the code takes that the note doesn't name
    probs = [p for p in helpnotes.check(D) if '"create"' in p]
    check("an argument added to create's code, its note unchanged: the check says the note does not name it",
          any("does not name color=, which create takes" in p for p in probs), probs)
finally:
    v.args = args0
usage0 = D.USAGE["history"]
try:
    D.USAGE["history"] = "history [<id>] [since=<event>]"
    reply(ME, f"look {HID} :1")
    probs = [p for p in helpnotes.check(D) if '"history"' in p]
    check("a key added to a command's USAGE: its note is told it does not name it",
          any("does not name since=, which history takes (desk_knife.py USAGE['history'])" in p for p in probs), probs)
finally:
    D.USAGE["history"] = usage0
out = reply("sable", f"read {CID} :3", f'do replace {CID} old="[tags=a,b]" new="[tags=a,b] [color=<name>]"')
check("sable's edit names color=, which create doesn't take: her receipt says so, naming the note and the code",
      not out[-1][2] and "! help note" in out[-1][1] and "names color=, which create does not take (moo.py:" in out[-1][1],
      out[-1])
t, e = one(ME, "help create")
check("... and help create still prints the note as written: the reader of help is never told", "color=" in t
      and "!" not in t, t)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
