"""test_room_verbs (a990, rooms step 2b): rooms show their verbs and are namespaces for new ones (show, don't lock).

    python test_room_verbs.py [world]        default frontier-try

Loads the world into memory and never saves it (the harness of test_room_look.py). The Desktop is marked the way the
live world will be (do prop <Desktop> verbs=layout); two rooms each grow a world verb named tidy, and nothing else in
the house changes to allow it. Each check is a line of the commission's 'done when'.
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


def said(me, line):
    """One line in its own reply -> (text, error), without the '!! since your last look' catch-up."""
    _, text, err = reply(me, line)[-1]
    strip = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith(("!!", "   ")))
    return strip(text), strip(err)


import rooms   # noqa: E402
import verbs   # noqa: E402

room = lambda title: next(f for f in rooms.all_rooms(W) if W.nodes[f]["title"] == title)
LOUNGE, BOARD, DESKTOP, ARCHIVE = room("Lounge"), room("Board"), room("Desktop"), room("Archive")
CORNER = rooms.corner_of(W, "juniper")
NOTE = "a333"                      # a note in the Lounge
print(f"world {WORLD} (in memory): Lounge {LOUNGE}, Board {BOARD}, Desktop {DESKTOP}, Juniper's corner {CORNER}")


def goto(me, fid):
    reply(me, f"go {fid} :1")


def make(me, fid, title, extra=""):
    got = reply(me, f"look {fid} :1", f'do create {fid} kind=note title="{title}" text=x {extra}'.strip())
    assert not got[-1][2], got[-1]
    return W.last_created


def prop(nid, key):
    n = W.nodes[nid]
    return ((W.subjects[n["subject"]] if n.get("subject") else n).get("props") or {}).get(key)


# ---- (1) show, don't lock --------------------------------------------------------------------------------------
goto("juniper", LOUNGE)
before_mark, _ = said("juniper", f"examine {NOTE}")
reply("juniper", f"look {DESKTOP} :1", f"do prop {DESKTOP} verbs=layout")
check("the Desktop is marked by a prop, verbs=layout", "layout" in str(W.nodes[DESKTOP]["props"].get("verbs")))
lounge_ex, _ = said("juniper", f"examine {NOTE}")
vline = next((l for l in lounge_ex.splitlines() if l.strip().startswith("verbs:")), "")
check("examine a note in the Lounge leaves out resize, raise, lower, fold and match",
      not any(f" {v} " in f" {vline} " for v in ("resize", "raise", "lower", "fold", "match")) and " move " in f" {vline} ", vline)
check("... and says the one pointer line: 'layout verbs are at hand on the Desktop'",
      "  layout verbs are at hand on the Desktop" in lounge_ex.splitlines(), lounge_ex)
vbefore = next(l for l in before_mark.splitlines() if l.strip().startswith("verbs:"))
print(f"     examine: {len(before_mark.split())} words before, {len(lounge_ex.split())} after, the pointer line included; "
      f"its verbs line {len(vbefore.split())} -> {len(vline.split())} words")
print("     before: " + vbefore.strip())
print("     after:  " + vline.strip() + " / " + lounge_ex.splitlines()[-1].strip())
check("examine's verbs line in the Lounge is shorter", len(vline.split()) < len(vbefore.split()), (vbefore, vline))

reply("juniper", f"look {DESKTOP} :1", f"do prop {DESKTOP} remove=verbs")
vb0, _ = said("juniper", f"verbs {NOTE}")
reply("juniper", f"look {DESKTOP} :1", f"do prop {DESKTOP} verbs=layout")
vb, _ = said("juniper", f"verbs {NOTE}")
print(f"     verbs {NOTE}: {len(vb0.splitlines())} lines, {len(vb0.split())} words before; {len(vb.splitlines())} lines, "
      f"{len(vb.split())} words after")
check("verbs <note> in the Lounge is shorter", len(vb.split()) < len(vb0.split()), (vb0, vb))
check("verbs <note> in the Lounge: move keeps into/before/after, no to=/by=, no resize; the pointer line",
      "move into=<surface> | before=<id> | after=<id>" in vb and "to=<x>" not in vb and "resize" not in vb
      and "layout verbs are at hand on the Desktop" in vb, vb)
sx, _ = said("juniper", "examine f177")
check("examine a surface in the Lounge leaves out tile and untile", " tile " not in sx and "untile" not in sx, sx)

goto("juniper", DESKTOP)
desk_ex, _ = said("juniper", f"examine {NOTE}")
check("on the Desktop they are listed, and no pointer", all(v in desk_ex for v in ("resize", "raise", "lower", "fold", "match"))
      and "layout verbs are at hand" not in desk_ex, desk_ex)
check("verbs <note> on the Desktop lists move to= and by=", "to=<x>,<y>" in said("juniper", f"verbs {NOTE}")[0])
alex_ex, _ = said("alex", f"examine {NOTE}")
check("Alex, placed nowhere (his hands are on the Desktop), sees them all", "resize" in alex_ex and "layout verbs are" not in alex_ex, alex_ex)

goto("juniper", LOUNGE)
got = reply("juniper", f"look {NOTE} :1", f"do resize {NOTE} to=40x40", f"do fold {NOTE}", f"do unfold {NOTE}")
check("a layout verb typed in the Lounge still works (shown, not locked)", not got[-1][2] and len(got) == 4, got)

# ---- (2) a room is a namespace -------------------------------------------------------------------------------
LT = make("juniper", LOUNGE, "tidy", f"tags=verb on={LOUNGE}")
reply("juniper", f"look {LT} :1", f'do rewrite {LT} text="# tidy, the Lounge\'s\\ndo prop $1 tidied=lounge"')
check("the Lounge grows a world verb named tidy (on=<room>)", verbs.where(W, W.subjects[W.nodes[LT]["subject"]]) == ("room", LOUNGE))
t, e = said("juniper", f"examine {NOTE}")
check("examine in the Lounge shows it at hand", f"at hand in Lounge, made in the world: tidy ({LT})" in t, t)
n0 = len(W.events)
got = reply("sable", f"look {LOUNGE} :1", f"do create {LOUNGE} kind=note title=tidy tags=verb on={LOUNGE} text=\"do prop $1 tidied=twice\"")
check("a second tidy in the SAME room is refused when made, naming the first", got[-1][2] and "second tidy" in got[-1][2]
      and LT in got[-1][2], got[-1])
check("... and nothing was changed (no event, no note)", len(W.events) == n0 and not any(
    W.subjects[s]["title"] == "tidy" and "twice" in W.subjects[s]["text"] for s in W.subjects), W.events[n0:])

bnote = make("pike", BOARD, "Board scrap")
goto("juniper", CORNER)
got = reply("juniper", f"look {NOTE} :1", f"tidy {NOTE}")
check("bare tidy typed from a corner runs the Lounge's while it is the only one", not got[-1][2] and prop(NOTE, "tidied") == "lounge", got[-1])

BT = make("pike", BOARD, "tidy", f"tags=verb on={BOARD}")
reply("pike", f"look {BT} :1", f'do rewrite {BT} text="do prop $1 tidied=board"')
got = reply("juniper", f"look {NOTE} :1", f"tidy {NOTE}")
err = got[-1][2]
check("with two, bare tidy from a corner refuses naming both doors",
      f"Lounge ({LOUNGE}, use {LT})" in err and f"Board ({BOARD}, use {BT})" in err and "go there, or use <id>" in err, got[-1])
print("     " + err.splitlines()[-1])

goto("juniper", LOUNGE)
reply("juniper", f"look {NOTE} :1", f"do prop {NOTE} tidied=no")
got = reply("juniper", f"look {NOTE} :1", f"tidy {NOTE}")
check("bare tidy in the Lounge runs the Lounge's", not got[-1][2] and prop(NOTE, "tidied") == "lounge", got[-1])
goto("pike", BOARD)
got = reply("pike", f"look {bnote} :1", f"tidy {bnote}")
check("bare tidy in the Board runs the Board's", not got[-1][2] and prop(bnote, "tidied") == "board", got[-1])
got = reply("pike", f"look {bnote} :1", f"do prop {bnote} tidied=no", f"look {bnote} :1", f"do tidy {bnote}")
check("do tidy (a retired built-in's word) is answered by the room's verb too", not got[-1][2] and prop(bnote, "tidied") == "board", got[-1])

goto("juniper", CORNER)
got = reply("juniper", f"look {NOTE} :1", f"use {BT} {NOTE}")
check("use <id> runs the Board's from a corner", not got[-1][2] and prop(NOTE, "tidied") == "board", got[-1])
got = reply("juniper", f"look {NOTE} :1", f"use {LT} {NOTE}")
check("use <id> runs the Lounge's from a corner", not got[-1][2] and prop(NOTE, "tidied") == "lounge", got[-1])

# ---- stored lines name their door when saved ----------------------------------------------------------------
t, e = said("juniper", "script t1 = tidy $1")
check("saving a script away from a room with tidy is refused at save, naming the doors",
      "not saved" in e and f"use {LT}" in e and "not where this line lives" in e, e)
print("     " + e.splitlines()[-1])
t, e = said("juniper", "rule when tag:messy do tidy")
check("saving a rule away from a room with tidy is refused at save, naming the doors", f"use {LT}" in e and f"Board ({BOARD}" in e, e)
t, e = said("juniper", f"rule when tag:messy2 do use {LT}")
check("... and a rule that names its door (use <id>) saves anywhere", not e and "ok r" in t, e or t)
t, e = said("juniper", f'do prop {CORNER} wake="read a583 :3; look; tidy {NOTE}"')
check("a wake line calling bare tidy, set on a corner, is refused naming the doors", "wake line is stored text" in e and f"use {LT}" in e, e)
HV = make("juniper", CORNER, "neaten")
n0 = len(W.events)
got = reply("juniper", f"look {HV} :1", f'do rewrite {HV} text="tidy $1"', )
got2 = reply("juniper", f"look {HV} :1", f"do tag {HV} add=verb", f"do prop {HV} on=house")
check("a house verb whose lines say bare tidy is refused when it becomes a verb, naming the doors",
      got2[-1][2] and "stored text" in got2[-1][2] and f"use {LT}" in got2[-1][2], got2)

# ---- (3) templates stand in their own home ------------------------------------------------------------------
goto("juniper", LOUNGE)
t, e = said("juniper", "script t2 = tidy $1")
check("a script saved in the Lounge calling bare tidy saves, and says where it lives", not e and f"lives in Lounge ({LOUNGE})" in t, e or t)
got = reply("pike", f"look {bnote} :1", f"run t2 {bnote}")
check("run from the Board by someone else, it runs the Lounge's tidy", not got[-1][2] and prop(bnote, "tidied") == "lounge", got[-1])

t, e = said("juniper", "rule when tag:messy do tidy")
check("a rule saved in the Lounge calling bare tidy saves", not e and "ok r" in t, e or t)
rid = D.rules[-1]["id"]
for where, label in ((LOUNGE, "in the Lounge"), (BOARD, "in the Board")):
    goto("juniper", where)
    x = make("pike", BOARD, f"mess {label}")
    got = reply("pike", f"look {x} :1", f"do tag {x} add=messy")
    check(f"the Lounge rule runs the Lounge's tidy while its author is {label}", prop(x, "tidied") == "lounge", got[-1])
reply("juniper", "rest")
W.nodes[CORNER]["props"]["want"] = "rest"            # asleep, as the house marks it
x = make("pike", BOARD, "mess while asleep")
got = reply("pike", f"look {x} :1", f"do tag {x} add=messy")
check("... and while its author is asleep in her corner", rooms.asleep(W, "juniper") and prop(x, "tidied") == "lounge", got[-1])
W.nodes[CORNER]["props"]["want"] = "awake"

# (5), Juniper c996: where a rule lives is seen and changed on purpose (rules are no placed notes yet: the room it was
# saved in is the fallback, and so every rule's home today)
t, e = said("juniper", f"examine {rid}")
check("examine rN shows where the rule lives", not e and f"lives in Lounge ({LOUNGE})" in t, e or t)
t, e = said("juniper", f"rule home {rid} corner")
check("rule home to a room where tidy is not at hand is refused, naming the doors", f"use {LT}" in e, e or t)
t, e = said("juniper", f"rule home {rid} board")
check("rule home to the Board is accepted", not e and f"lives in Board ({BOARD})" in t, e or t)
x = make("pike", BOARD, "mess after the move")
reply("pike", f"look {x} :1", f"do tag {x} add=messy")
check("... and the rule now runs the Board's tidy", prop(x, "tidied") == "board", prop(x, "tidied"))
reply("juniper", f"rule home {rid} lounge")
t, e = said("juniper", "script home t2 corner")
check("script home to a room where tidy is not at hand is refused", "not moved" in e and f"use {LT}" in e, e or t)
t, e = said("juniper", "script home t2 board")
check("script home to the Board is accepted, and scripts says so", not e and f"(lives in Board {BOARD})" in said("juniper", "scripts")[0], e or t)

# a rule living elsewhere whose word lost its room: Pike's corner had a tidy when he saved it, then it went
PC = rooms.corner_of(W, "pike")
goto("pike", PC)
PT = make("pike", PC, "tidy", f"tags=verb on={PC}")
reply("pike", f"look {PT} :1", f'do rewrite {PT} text="do prop $1 tidied=pike"')
t, e = said("pike", "rule when tag:pikemess do tidy")
check("Pike saves a rule in his corner while tidy is at hand there", not e, e)
reply("pike", f"look {PT} :1", f"do remove {PT}")
x = make("sable", BOARD, "orphan")
got = reply("sable", f"look {x} :1", f"do tag {x} add=pikemess")
note = next((l for l in got[-1][1].splitlines() if "could not" in l), "")
check("a rule living elsewhere calling bare tidy refuses at run time, naming the doors (it never guesses)",
      prop(x, "tidied") is None and f"use {LT}" in note and f"Board ({BOARD}" in note, got[-1])
print("     " + note.strip())

goto("juniper", LOUNGE)
SP = make("juniper", LOUNGE, "spruce", f"tags=verb on={LOUNGE}")
got = reply("juniper", f"look {SP} :1", f'do rewrite {SP} text="tidy $1"')
check("a Lounge verb whose lines say bare tidy saves (tidy is at hand where it lives)", not got[-1][2], got[-1])
goto("pike", BOARD)
reply("pike", f"look {bnote} :1", f"do prop {bnote} tidied=no")
got = reply("pike", f"look {bnote} :1", f"use {SP} {bnote}")
check("used from the Board, its bare tidy means the Lounge's, not the caller's", not got[-1][2] and prop(bnote, "tidied") == "lounge", got[-1])

got = reply("juniper", f"look {LOUNGE} :1", f"rule when tag:herey do move into=$here")
check("a rule's $here is its home", not got[-1][2], got[-1])
goto("juniper", CORNER)
x = make("pike", BOARD, "herey")
reply("pike", f"look {x} :1", f"do tag {x} add=herey")
check("... it moved the thing into the Lounge while its author was in her corner", W.nodes[x]["parent"] == LOUNGE, W.nodes[x]["parent"])

# a lens gesture stands in its lens's room (deskd sets _act_home from the painted lens)
be("alex")
reply("alex", f"look {bnote} :1", f"do prop {bnote} tidied=no")
D._act_home = (LOUNGE,)
try:
    r = D.dispatch("desk", {"line": f"tidy {bnote}", "whole": True})
finally:
    D._act_home = None
check("a lens act in the Lounge's lens runs the Lounge's tidy", not r.get("error") and prop(bnote, "tidied") == "lounge", r)
D._act_home = (ARCHIVE,)
try:
    r = D.dispatch("desk", {"line": f"tidy {bnote}", "whole": True})
finally:
    D._act_home = None
check("a lens act living elsewhere refuses naming the doors", "use " + LT in (r.get("error") or ""), r)
D._act_home = (verbs.room_holding(W, "s588"),)     # the command center's lens lives on the Desktop
try:
    r = D.dispatch("desk", {"line": f"look {bnote} :1; do resize {bnote} to=200x100; do fold {bnote}", "whole": False})
finally:
    D._act_home = None
check("a painter gesture with a built-in verb is unchanged", not r.get("error") and "ERR" not in (r.get("text") or ""), r)

# ---- (4) a verb's word is not a name --------------------------------------------------------------------------
t, e = said("juniper", "read tidy")
check("read tidy is never ambiguous between two rooms' verbs: it says it is a verb's word", "is a verb's word" in e
      and "names" not in e, e)
t, e = said("juniper", f"read {LT}")
check("a verb note is read by its id", not e and "tidied=lounge" in t, e)
t, e = said("juniper", "help tidy")
check("help tidy explains both, each with its door", f"use {LT}" in t and f"use {BT}" in t, t)

print()
print("all ok" if not fails else f"{len(fails)} FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
