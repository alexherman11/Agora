"""test_house_verbs (9 Oct 2026, step 6 of the grammar unification): the retired built-ins are verb notes of the house.

    python test_house_verbs.py

tidy, gather, dedupe, reveal, done and reply are notes tagged verb with on=house (houseverbs.py seeds them), found and
run by verbs.py like any verb a person makes; moo.py no longer holds them, the desk has no specialized tier to refuse
them with, and a room's own tidy stands over the house's by saying overrides=. Builds its own small world (roomworld.py,
house=True).
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


D, R = roomworld.build(house=True)
W = D.world
HOUSE = R.HOUSE


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


def props(nid):
    return W.subjects[W.nodes[nid]["subject"]].get("props") or {}


import knife   # noqa: E402
import moo     # noqa: E402

# 1. the code: no specialized tier, no compositions
gone = ("tidy", "split", "gather", "reveal", "dedupe", "done", "stack")
check("moo.REGISTRY holds none of the retired compositions", not any(v in moo.REGISTRY for v in gone), sorted(moo.REGISTRY))
check("every registered verb is general", knife.GENERAL == list(moo.REGISTRY) and not hasattr(knife, "SPECIALIZED"))
check("the house's verbs were made as notes (six that were Python, and wish: 9 Oct, a3806)",
      sorted(HOUSE) == ["dedupe", "done", "gather", "reply", "reveal", "tidy", "wish"], HOUSE)

# 2. help and examine know them as world verbs
t = reply("juniper", "help tidy")[-1][1]
check("help tidy describes the house's note, not a refusal with an alternative", HOUSE["tidy"] in t and "on the house" in t and "use tile" not in t, t)
t = reply("juniper", "help nosuchword")[-1][1]
check("help with an unknown word names the house's verbs among the world verbs at hand", "tidy" in t and "(the house)" in t, t)

# 3. each one does what its lines say, with the verb's provenance on the receipt
LOUNGE, SHELF, NOTE, BOARD = R.LOUNGE, R.SHELF, R.NOTE, R.BOARD
reply("juniper", f"look {LOUNGE} :1", f"do group {LOUNGE} title=Pile as=free")
pile = W.last_created
reply("juniper", f"look {pile} :1", f'do create {pile} kind=note title="Under" text="under"', f'do create {pile} kind=note title="Over" text="over"')
under = [k["id"] for k in W.children(pile)][0]
n0 = len(W.events)
got = reply("juniper", f"look {under} :1", f"do reveal {under}")
check("reveal raises a thing on a free surface", not got[-1][2] and any(e["verb"] == "raise" for e in W.events[n0:]) and f"(reveal {HOUSE['reveal']}" in got[-1][1], got[-1])

got = reply("juniper", f"look {LOUNGE} :1", f"do tidy {LOUNGE}")
check("tidy tiles the surface as a column, as the house's tidy", not got[-1][2] and W.nodes[LOUNGE]["layout"] == "column"
      and f"(tidy {HOUSE['tidy']}" in got[-1][1], got[-1])
check("the receipt lists the primitive event, tile", "tile" in got[-1][1], got[-1][1])

sid = W.nodes[NOTE]["subject"]
got = reply("juniper", f"read {NOTE} :1", f"look {SHELF} :1", f"do place {sid} into={SHELF}", f"look {SHELF} :1", f"look {NOTE} :1", f"do dedupe {NOTE}")
check("dedupe keeps this appearance and removes the other", not got[-1][2] and W.appearances_of(sid) == [NOTE], (got[-1], W.appearances_of(sid)))

got = reply("pike", f"look {BOARD} :1", f'do create {BOARD} kind=task title="A card" status=open priority=1')
card = W.last_created
got = reply("pike", f"look {card} :1", f"do done {card}")
check("done puts the card in the done lane (status=done, a rank)", not got[-1][2] and props(card).get("status") == "done" and props(card).get("rank"), (got[-1], props(card)))

got = reply("juniper", f"look {LOUNGE} :1", f"look {SHELF} :1", f"do gather {SHELF} letter")
check("gather moves what the word finds into the surface", not got[-1][2] and W.nodes[NOTE]["parent"] == SHELF, (got[-1], W.nodes[NOTE]["parent"]))

talk = R.TALK[LOUNGE]
got = reply("sable", f"look {talk} :1", f'do reply {talk} "hello there"')
check("reply appends to the chat (append by another name; the words are its second word, since a note passes no k=v through)",
      not got[-1][2] and "hello there" in W.subjects[W.nodes[talk]["subject"]]["text"], got[-1])

# 4. a word with no note is a miss like any other, and the house's note is nothing special
got = reply("juniper", f"look {SHELF} :1", f"do stack {SHELF}")
check("stack, which has no note, is refused as a word nothing answers (no Python alternative)",
      got[-1][2] and "use tile" not in got[-1][2] and "stack" in got[-1][2], got[-1])
got = reply("juniper", f"look {LOUNGE} :1", f'do create {LOUNGE} kind=note title=tidy tags=verb on={LOUNGE} text="do prop $1 tidied=lounge"')
check("a room's tidy is refused while the house's answers the word, naming it", got[-1][2] and HOUSE["tidy"] in got[-1][2], got[-1])
got = reply("juniper", f"look {LOUNGE} :1", f'do create {LOUNGE} kind=note title=tidy tags=verb on={LOUNGE} overrides={HOUSE["tidy"]} text="do prop $1 tidied=lounge"')
room_tidy = W.last_created
check("... and stands over it with overrides=", not got[-1][2], got[-1])
reply("juniper", f"go {LOUNGE}")
got = reply("juniper", f"look {NOTE} :1", f"do tidy {NOTE}")
check("in the Lounge, tidy is the room's, over the house's", not got[-1][2] and props(NOTE).get("tidied") == "lounge" and f"over tidy {HOUSE['tidy']}" in got[-1][1], got[-1])

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
