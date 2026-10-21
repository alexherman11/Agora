# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_house_words (a1308): the house answers its own words. Every id kind it prints (a, s, f, e, c, l) can be typed
back; help explains every command a person can type, the nouns it names itself by, and, for a word it doesn't know,
names every door: the commands, the built-in verbs, the world verbs at hand where you are (Pike's a1299), the topics.

    python test_house_words.py

Builds its own small world in memory (roomworld.py, a1190) and never saves it: every desk line runs through the
desk's own dispatch, as explore.py and deskd call it, with a reply token per reply (the harness of test_room_reads.py).
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
    """-> (text, error) of one line, the !! header taken off."""
    _, text, err = reply(me, line)[-1]
    strip = lambda t: re.sub(r"^!! .*\n", "", t)
    return strip(text), strip(err)


import verbs   # noqa: E402
import house   # noqa: E402

ME = "pike"
FALLBACK = "no command, verb or topic"

# ---- the world: a comment, a link, an event caused by a rule, a removed thing, room and house verbs ------------------
NOTE, CARD = R.NOTE, R.CARDS[0]
reply(ME, f"look {NOTE} :1", f'do comment {NOTE} line="is this the letter?"')
CID = next(c["id"] for c in W.subjects[W.nodes[NOTE]["subject"]]["comments"])
reply(ME, f"look {NOTE} :1", f"look {CARD} :1", f"do link {CARD} {NOTE} as=refers")
LID = W.links[-1]["id"]
EV = W.events[-1]["id"]                      # the link's event
reply("jeff", f"look {R.HOME} :1", 'do create $here kind=note title=card|cards tags=verb on=house '
      'text="# card <title>: a task where you are\\ndo create $here kind=task title=\\"$*\\""')
corner = R.corner["pike"]
reply("pike", f"look {corner} :1", 'do create $here kind=note title=wish tags=verb '     # a1587: release is the house's word now
      'text="# wish: say a wish\\ndo append $here.talk line=\\"wished\\""')
REL = W.nodes[W.last_created]["subject"] if W.last_created in W.nodes else None
reply("pike", f"look {corner} :1", f"look {W.appearances_of(REL)[0]} :1", f"do prop {W.appearances_of(REL)[0]} on={corner}")
GONE = reply(ME, f"look {R.SHELF} :1", 'do create $here kind=note title="Soon gone"')
GONE = W.last_created
reply(ME, f"look {GONE} :1", f"do remove {GONE}")
print(f"built world (in memory): note {NOTE}, comment {CID}, link {LID} ({EV}), removed {GONE}, wish {REL}")

# ---- 1. every id kind, typed back -----------------------------------------------------------------------------------
for cmd in ("examine", "look", "read", "x", "help"):
    t, e = one(ME, f"{cmd} {EV}")
    check(f"{cmd} {EV} (an event) answers with the line history prints for it, and how to undo it",
          not e and t.startswith(f"{EV} link ") and "Card one" in t and f"undo {EV}" in t, (t, e))
t, e = one(ME, f"history {EV}")
check(f"history {EV} lists that event", not e and t.splitlines()[0].startswith(f"{EV} link"), (t, e))
t, e = one(ME, f"examine {CID}")
check(f"examine {CID} (a comment) shows its text, its thing, and how to close it",
      not e and "is this the letter?" in t and "open" in t and f"do resolve {CID}" in t, (t, e))
t, e = one(ME, f"examine {LID}")
check(f"examine {LID} (a link) shows both ends and how to remove it",
      not e and "refers →" in t and "Card one" in t and "A letter" in t and f"id={LID}" in t, (t, e))
t, e = one(ME, f"history {CID}")
check(f"history {CID} lists the comment's making", not e and "comment" in t, (t, e))
reply(ME, f"look {CARD} :1", f"do unlink {CARD} id={LID}")
t, e = one(ME, f"examine {LID}")
check(f"examine {LID} after unlink: a link no longer here, and what happened to it",
      not e and "no longer here" in t and "unlink" in t, (t, e))
t, e = one(ME, f"history {LID}")
check(f"history {LID} lists its making and its unlinking", not e and " link " in t and " unlink " in t, (t, e))
for cmd, k in (("examine", "a"), ("examine", "s"), ("examine", "f"), ("read", "s")):
    rid = {"a": NOTE, "s": W.nodes[NOTE]["subject"], "f": R.LOUNGE}[k]
    t, e = one(ME, f"{cmd} {rid}")
    check(f"{cmd} {rid} (kind {k}) still answers as before", not e and rid in t, (t, e))

# refusals that name the door
t, e = one(ME, f"where {EV}")
check(f"where {EV}: refused, saying it is an event and which commands show it",
      e and "is an event" in e and f"examine {EV}" in e, (t, e))
t, e = one(ME, "examine q77")
check("an unknown id's refusal lists all six kinds (f a s e c l)",
      e and all(x in e for x in ("f02", "a05", "s03", "e12", "c40", "l41")), (t, e))
t, e = one(ME, "examine e999999")
check("examine e999999: no event by that id, and the latest one named", e and "no event e999999" in e
      and W.events[-1]["id"] in e, (t, e))
t, e = one(ME, "examine 9661f78")
check("examine <a commit hash>: says it looks like a commit", e and "looks like a commit" in e, (t, e))
check("examine <a hash no card landed>: says no card landed it, and how one is found (a3295)",
      e and "no card here landed it" in e and "find prop:landed=" in e, (t, e))
reply("house", f"look {CARD} :1", f"do prop {CARD} commission=landed landed=9661f78")
for h in ("9661f78", "9661f78a0b1c2d3e4f"):
    t, e = one(ME, f"examine {h}")
    check(f"examine {h} (a hash a card landed): names the card and the door to it (a3295)",
          e and "looks like a commit" in e and f"landed by {CARD}" in e and f"read {CARD}" in e and "no card" not in e, (t, e))
t, e = one(ME, "examine 9661f79")
check("a hash one digit off a landed one is no card's", e and "no card here landed it" in e, (t, e))

# a3295: a link's receipt names the link it made and its kind, and $new holds it
got = reply(ME, f"look {NOTE} :1", f"look {CARD} :1", f"do link {CARD} {NOTE} as=blocks", "examine $new",
            f"do unlink {CARD} id=$new")
L2 = W.events[-2]["undo"].get("drop_link") if len(got) == 5 else None
check("do link A B: the receipt says 'created l…' and 'l…: A blocks → B'",
      L2 and f"→ created {L2}" in got[2][1] and f"{L2}: {CARD} blocks → {NOTE}" in got[2][1], got[2:])
check("$new after a link is the link: examine $new shows it, unlink id=$new removes it",
      L2 and got[3][1].lstrip().startswith(f"{L2} link") and f"{L2} removed" in got[4][1]
      and not any(l["id"] == L2 for l in W.links), got[3:])
t, e = one(ME, f"examine {GONE}")
check(f"examine {GONE} (removed): not 'no such id', but its last event", e and "not in the world now" in e
      and "remove" in e, (t, e))
t, e = one(ME, f"history {GONE}")
check(f"history {GONE} (removed) still lists what happened to it", not e and "remove" in t, (t, e))

# ---- 2. help knows every command ------------------------------------------------------------------------------------
words = sorted(verbs.DESK_WORDS | house.COMMANDS | {"rest"})
missing = []
for word in words:
    t, e = one(ME, f"help {word}")
    if e or FALLBACK in t or t.startswith("no verb"):
        missing.append((word, (e or t)[:100]))
check(f"help <command> explains each of the {len(words)} command words", not missing, missing)
# a1595: help's words are notes in a Help binder; this world has none, so a command answers from the floor (its
# arguments, from the code) and says its note is missing. The live world's notes are health's to check (helpnotes.py)
t, e = one(ME, "help history")
check("help history answers (the Board's 'history lists every event'): here, the floor, saying the note is missing",
      not e and t.startswith("history [<id>]") and "no note says this yet" in t, (t, e))
# the nouns are notes too: a Help binder with a note for each, as the live world has; a noun yields to a world verb
reply(ME, f"look {R.HOME} :1", "do create $here kind=surface title=Help layout=column", "do prop $new role=help")
HELPB = W.last_created if W.nodes.get(W.last_created, {}).get("type") == "surface" else \
    next(n["id"] for n in W.nodes.values() if (n.get("props") or {}).get("role") == "help")
for title in ("ids|id", "events|event", "comments", "chat|chats", "task|tasks", "note|notes",
              "resident|residents|corner|corners", "card"):
    reply(ME, f"look {HELPB} :1", f'do create {HELPB} kind=note title="{title}" text="about {title.split("|")[0]}"')
for noun in ("ids", "event", "comments", "chat", "task", "note", "corner"):
    t, e = one(ME, f"help {noun}")
    check(f"help {noun} answers, from its note", not e and FALLBACK not in t and t.startswith("about "), (t, e))
t, e = one(ME, "help card")
check("help card: the house verb card answers, not the noun's note (a noun yields to a verb made in the world)",
      not e and "card" in t and "about card" not in t, (t, e))

# ---- 3. a word help doesn't know names every door (a1299) -----------------------------------------------------------
builtin_line = "  verbs: " + " ".join(D._help_verbs())


def fallback_in(room):
    reply(ME, f"go {room} :1")
    t, e = one(ME, "help zzzq")
    return t, e, next((l for l in t.splitlines() if l.startswith("  world verbs")), "")


t, e, wv = fallback_in(R.LOUNGE)
check("help <unknown> in the Lounge: says it doesn't know, lists commands, the built-in verbs unchanged, topics",
      not e and t.startswith(FALLBACK) and "  commands: " in t and "history" in t.split("  commands: ")[1].splitlines()[0]
      and builtin_line in t.splitlines() and "  topics: " in t, t)
check("... and lists say and card among the world verbs at hand, the house's", "card, say (the house)" in wv, wv)
check("... and not wish, which lives in Pike's corner", "wish" not in wv, wv)
t, e, wv = fallback_in(corner)
check("help <unknown> in Pike's corner also lists wish, as its room's", "wish (Pike's corner" in wv
      and "card, say (the house)" in wv, wv)
t, e, wv = fallback_in(R.ARCHIVE)
check("help <unknown> in a room with no verbs of its own lists only the house's",
      wv.split(": ", 1)[-1].startswith("card, say (the house)") and wv.count("(") == 2, wv)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
