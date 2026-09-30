"""test_blanks (a806, rooms step 2a): the one filler, $here and $new, presence, and rest going home.

    python test_blanks.py [world]        default frontier-try

Part 1 loads the world into memory and never saves it: every desk line runs through the desk's own dispatch, as
explore.py and deskd call it, with a reply token per reply. Part 2 drives the house's own rest path (House.rest, as
after a resident says > rest) with DESKD off, so it CHANGES the world it is given: give it a -try copy.
"""
import os
import pickle
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"
os.environ.setdefault("HOUSE_CLAUDE", "claude")     # the house looks for a claude binary; none is started here

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
    """Switch reader, as explore.py does per invocation."""
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def reply(me, *lines, whole=True):
    """One reply: its lines share a token, as the house and explore.py send them. -> [(line, text, error)]"""
    be(me)
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": whole, "reply": token})
        out.append((line, r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def text_of(ident):
    n = W.nodes.get(ident)
    return W.subjects[n["subject"] if n else ident]["text"]


def props(ident):
    n = W.nodes[ident]
    return (n.get("props") if n["type"] == "surface" else W.subjects[n["subject"]].get("props")) or {}


import rooms   # noqa: E402

t0 = time.time()
BEFORE = {sid: (s["title"], s["text"]) for sid, s in W.subjects.items()}
ROOMS = rooms.all_rooms(W)
talky = [f for f in ROOMS if (W.nodes[f].get("props") or {}).get("talk") and (W.nodes[f].get("props") or {}).get("role") == "room"]
quiet = [f for f in ROOMS if not (W.nodes[f].get("props") or {}).get("talk")]
assert len(talky) >= 2 and quiet, f"this test wants two rooms with talk= and one without: {ROOMS}"
LOUNGE, BOARD, NOTALK = talky[0], talky[1], quiet[0]
TALK = {f: W.nodes[f]["props"]["talk"] for f in talky}
HOME = rooms.home_room(W)
CORNER = sorted(f for f in ROOMS if (W.nodes[f].get("props") or {}).get("role") == "resident")[0]
ME = W.nodes[CORNER]["props"]["actor"]
print(f"world {WORLD} (in memory): rooms {LOUNGE} {BOARD} with talk, {NOTALK} without; home {HOME}; acting as {ME}")

VERBS = {s["title"] for s in W.subjects.values() if "verb" in s["tags"]}


def own(word):
    """A verb name of the test's own that no verb in the world already answers to (a965: the world grew a say, a939,
    and a second house-wide say made every say line ambiguous). A test must not break because the world grew."""
    n, name = 0, word
    while name in VERBS:
        n += 1
        name = f"{word}{n}"
    VERBS.add(name)
    return name


SAY, PLAN, TWO = own("say"), own("plan-here"), own("two-notes")

# 1. say, written once as a world verb, lands in the talk of the room you are in, signed
got = reply("claude", f"look {HOME} :1",
            f'do create {HOME} kind=note title={SAY} tags=verb on=house '
            f'text="# say something in the room you are in\\ndo append $here.talk line=\\"$*\\""')
say = next(s for s in W.subjects.values() if s["title"] == SAY and "verb" in s["tags"])
check("the say verb is stored as written ($here.talk and $* not filled in typed text)",
      "$here.talk" in say["text"] and '"$*"' in say["text"], got)


def last_line(fid):
    return (text_of(TALK[fid]).splitlines() or [""])[-1]


for room in (LOUNGE, BOARD):
    got = reply(ME, f"go {room} :1", f"{SAY} hello from here")
    check(f"{SAY} in {W.nodes[room]['title']} lands in its talk ({TALK[room]}), signed",
          last_line(room) == f"{W.display_name(ME)}: hello from here", (got, last_line(room)))
got = reply(ME, f"go {BOARD} :1", f'{SAY} a; b "hi" and $here and \\$new')
check(f'{SAY} a; b "hi" lands verbatim, semicolon and quotes intact, $here in the words untouched',
      last_line(BOARD) == f'{W.display_name(ME)}: a; b "hi" and $here and $new', (got, last_line(BOARD)))
got = reply(ME, f"go {BOARD} :1", f"{SAY} it's fine")
check(f"{SAY} it's fine (an apostrophe) is words, not an open quote",
      last_line(BOARD) == f"{W.display_name(ME)}: it's fine", (got, last_line(BOARD)))
before = {f: text_of(TALK[f]) for f in talky}
got = reply(ME, f"go {NOTALK} :1", f"{SAY} anyone here?")
check(f"{SAY} in a room with no talk= refuses, saying so, and nothing lands",
      got[-1][2] and "has no talk=" in got[-1][2] and before == {f: text_of(TALK[f]) for f in talky}, got)

# 2. create then prop describe=$new, in one reply; the receipt shows the value
got = reply(ME, f"look {CORNER} :1", f"do create {CORNER} kind=note title=Plan", f"do prop {CORNER} testdesc=$new")
made = next((a for a in W.nodes if a.startswith("a") and W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Plan"
             and W.nodes[a]["parent"] == CORNER), None)
check("create, then prop testdesc=$new in the same reply sets the id", made and props(CORNER).get("testdesc") == made, got)
check("the receipt says testdesc=<id>, never the blank", f"testdesc={made}" in got[-1][1] and "=$new" not in got[-1][1], got[-1])

# 3. the same lines pasted into a verb body do the same thing
reply("claude", f"look {HOME} :1",
      f'do create {HOME} kind=note title={PLAN} tags=verb on=house '
      f'text="# a plan note in the room you are in, described\\ndo create $here kind=note title=Plan2\\ndo prop $here testdesc2=$new"')
got = reply(ME, f"go {CORNER} :1", f"look {CORNER} :1", PLAN)
made2 = next((a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Plan2"), None)
check("the same lines as a verb body: $new in step 2 is what step 1 made", made2 and props(CORNER).get("testdesc2") == made2, got)
got = reply(ME, f"look {CORNER} :1", PLAN, f"do prop {CORNER} testdesc3=$new")
made3 = [a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Plan2"][-1]
check("what a verb made is the caller's $new on the next line of the reply", props(CORNER).get("testdesc3") == made3, got)
reply("claude", f"look {HOME} :1",
      f'do create {HOME} kind=note title={TWO} tags=verb on=house text="do create $here kind=note title=First\\ndo create $here kind=note title=Second"')
got = reply(ME, f"look {CORNER} :1", TWO, f"do prop {CORNER} last=$new")
second = [a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Second"][-1]
check("a verb that made two things: the caller's $new is the last", props(CORNER).get("last") == second, got)

# 4. a missing blank refuses; nothing stores a literal $name
for line, why in ((f"do prop {CORNER} x=$new", "nothing earlier"), (f"do prop {CORNER} x=$nothing", "no blank"),
                  (f"do prop {CORNER} x=$here.nothere", "has no nothere="), (f"do prop {CORNER} x=$item", "Did you mean $new")):
    got = reply(ME, f"look {CORNER} :1", line)
    check(f"{line.split()[-1]} refuses ({why})", why in got[-1][2] and "x" not in props(CORNER), got[-1])
got = reply(ME, f"look {CORNER} :1", f"do prop {CORNER} x=1", f"do prop {CORNER} y=$new")
check("$new in a reply where nothing was made refuses", "nothing earlier" in got[-1][2] and "y" not in props(CORNER), got[-1])
got = reply(ME, f"look {CORNER} :1", f"do create {CORNER} kind=note title=Old", f"do prop {CORNER} y=1",
            f"do prop {CORNER} y2=$new", f"do tag $new add=blanktest")
old = got[1][1].split("created ")[1].split()[0] if len(got) > 1 else None
check("$new is the most recent thing made in this reply, across lines that made nothing (a806 (10))",
      props(CORNER).get("y2") == old and "blanktest" in W.subjects[W.nodes[old]["subject"]]["tags"], got)
check("the receipt names what $new was", got[-1][1].rstrip().endswith(f"($new = {old})"), got[-1])
got = reply(ME, f"look {CORNER} :1", f"do prop {CORNER} z=$new")
check("$new never reaches into an earlier reply", "nothing earlier" in got[-1][2] and "z" not in props(CORNER), got[-1])
check("no prop anywhere stores a blank's own name", not any(str(v).startswith(("$new", "$here", "$item", "$nothing"))
                                                              for n in W.nodes.values() for v in (n.get("props") or {}).values()))

# 5. words a person types are stored as typed; the literal \$ reads as $
chat = TALK[LOUNGE]
got = reply(ME, f"go {LOUNGE} :1", f"read {chat}", f'do append {chat} line="about $here and $here.talk, $new and $today, \\$5"')
check("a typed chat line with $here, $new and the today-blank is stored exactly as typed",
      text_of(chat).splitlines()[-1] == f"{W.display_name(ME)}: about $here and $here.talk, $new and $today, $5", got)
got = reply(ME, f"look {CORNER} :1", f"do prop {CORNER} price=$5", f"do prop {CORNER} spot=$here", f"do prop {CORNER} lit=\\$here")
check("in a value: $5 is a price, $here is filled, \\$here is literal",
      props(CORNER).get("price") == "$5" and props(CORNER).get("spot") == rooms.room_of(W, ME) and props(CORNER).get("lit") == "$here", got)

# 5b. text is words by default (a965): the verb's own argument list says what is prose. A resident writes about the
# blanks and then corrects it, in a reply where $new has a value, so nothing stays literal merely because it couldn't
# be filled
got = reply(ME, f"look {CORNER} :1", f'do create {CORNER} kind=note title="Blank notes" text="use $new after a create"',
            'do replace $new old="use $new after a create" new="use $new after a create; $today is the date, $here.talk the chat"',
            f"do prop {CORNER} describe=$new")
bn = next((a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Blank notes"), None)
check("replace old= and new= with blanks in them are stored as typed (the verb declares them <str>)",
      bn and text_of(bn) == "use $new after a create; $today is the date, $here.talk the chat", got)
check("prop describe=$new, the whole value one blank, still fills", bn and props(CORNER).get("describe") == bn, got)
got = reply(ME, f"look {CORNER} :1", f'do prop {CORNER} next="write $today into the log, then tell $here"',
            f"do prop {CORNER} when=$today")
check("a prop next= holding a sentence with blanks inside stays exactly as typed",
      props(CORNER).get("next") == "write $today into the log, then tell $here", got)
check("a prop whose whole value is one blank (when=$today) fills", props(CORNER).get("when") == D.today, (got, D.today))
got = reply(ME, f"go {LOUNGE} :1", f"read {chat}", f"do append {chat} line=$here")
check("a prose argument that is one whole blank (line=$here) is still words",
      text_of(chat).splitlines()[-1] == f"{W.display_name(ME)}: $here", got)
got = reply(ME, f"look {CORNER} :1", f'do create {CORNER} kind=view title="Here now" query=kind:note,in:$here')
view = next((f for f in W.nodes if W.nodes[f].get("layout") == "view" and W.nodes[f].get("title") == "Here now"), None)
check("a declared selection (create query=<selection>) with a blank inside is filled",
      view and W.nodes[view].get("query") == f"kind:note,in:{rooms.room_of(W, ME)}", (got, view and W.nodes[view].get("query")))

# 6. rules: $item is the thing it fired on; $here and $new refuse, saying why
got = reply(ME, f"rule on create by={ME} do prop tagged=$item.title")
reply(ME, f"look {CORNER} :1", f"do create {CORNER} kind=note title=Ruled")
ruled = [a for a in W.nodes if W.nodes[a].get("subject") and W.subjects[W.nodes[a]["subject"]]["title"] == "Ruled"][-1]
check("a rule's $item.title is the title of the thing it fired on", props(ruled).get("tagged") == "Ruled", props(ruled))
reply(ME, f"rule drop {D.rules[-1]['id']}")
reply(ME, f"rule on create by={ME} do prop where=$here")
got = reply(ME, f"look {CORNER} :1", f"do create {CORNER} kind=note title=Ruled2")
reply(ME, f"rule drop {D.rules[-1]['id']}")
check("$here in a rule refuses: rules have no room until step 2b", "a rule has no room" in got[-1][1], got[-1])

# 7. presence: Jeff is at Home without ever going there; a sleeping resident is not 'here with you'
be("worker-test")
look = D.dispatch("desk", {"line": f"go {HOME}"})["text"]
check("Jeff shows as here in Home", "Jeff" in look.split("Here with you:")[-1].split("\n")[0] if "Here with you:" in look else False, look)
other = sorted(f for f in ROOMS if (W.nodes[f].get("props") or {}).get("role") == "resident")[1]
pal = W.nodes[other]["props"]["actor"]
reply(pal, f"go {BOARD} :1")
W.nodes[other]["props"]["status"] = "asleep"
look = reply("worker-test", f"go {BOARD}")[-1][1]
head = look.split("Here with you:")[-1].split("\n")[0] if "Here with you:" in look else ""
check(f"{pal} asleep on the Board is not 'here with you' and is said to be asleep here",
      W.display_name(pal) not in head and f"{W.display_name(pal)} is asleep here." in look, look)

# 8. rest, typed: home to your corner, marked via=rest
got = reply(ME, f"go {BOARD} :1", "rest")
ev = W.events[-1]
check("rest takes you to your corner, and history can tell it from walking",
      rooms.room_of(W, ME) == CORNER and ev["verb"] == "go" and ev.get("via") == "rest", (got, ev))
hist = D.dispatch("desk", {"line": f"history"})["text"].splitlines()[-1]
check("history shows the rest move via rest", "via rest" in hist, hist)

# 9. nothing already written is re-filled: every note and chat reads the same (the talk the test added aside),
# and an export writes each $ as \$, so a replay stores what was stored
said = {W.nodes[TALK[f]]["subject"] if TALK[f] in W.nodes else TALK[f] for f in talky}
changed = [sid for sid, tt in BEFORE.items() if sid not in said and (W.subjects[sid]["title"], W.subjects[sid]["text"]) != tt]
dollars = [sid for sid, tt in BEFORE.items() if "$" in tt[1]]
check(f"every note and chat already in the world reads the same ({len(dollars)} of them hold a $)", not changed, changed[:5])
be(ME)
exp = D.cmd_export()
import re as _re  # noqa: E402
check("export writes no bare blank", not _re.search(r"(?<!\\)\$(here|new|item|today)\b", exp),
      _re.findall(r".{30}(?<!\\)\$(?:here|new|item|today)\b.{10}", exp)[:3])
print(f"part 1: {time.time() - t0:.0f} s (in memory; nothing saved)")

# part 2: the house's own rest, through the desk process, on the -try world
if not WORLD.endswith("-try"):
    print("skip part 2: it changes the world, and this is not a -try copy")
else:
    import house   # noqa: E402
    H = house.House(WORLD)
    w = H.load()
    H.act(ME, f"go {BOARD} :1")
    check("(setup) the resident is on the Board", rooms.room_of(H.load(), ME) == BOARD)
    r = house.Resident(H, CORNER)
    H.rest(r, 0, "you said > rest")
    w = H.load()
    last = [e for e in w.events if e["verb"] == "go" and e["by"] == ME][-1]
    check("the house's rest (as after > rest) takes the resident home to its corner, via=rest",
          rooms.room_of(w, ME) == CORNER and last.get("via") == "rest" and last["args"]["to"] == CORNER, last)

print(f"{len(fails)} failed" if fails else "all passed", f"({time.time() - t0:.0f} s, world {WORLD})")
sys.exit(1 if fails else 0)
