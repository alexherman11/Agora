# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_kinds (5 Oct): kinds in the world. A kind is a note tagged kind; create accepts it; it inherits the verbs of
what it is built on; rekind moves a thing between kinds of one shape and undo puts it back; a lens is a kind.

    python test_kinds.py

Builds its own small world in memory (roomworld.py) and runs every line through the desk's own dispatch.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import kinds       # noqa: E402
import roomworld   # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
CORNER = R.corner[ME]


def say(*lines):
    W.me = ME
    per = D._per
    if ME not in per:
        per[ME] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[ME]
    D._window = ""
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((r.get("text") or "", r.get("error") or "", r))
        if r.get("error"):
            break
    return out


def one(line):
    return say(line)[0]


def made(r):
    return None if r[1] else W.last_created


# ---- 1. no kind without a note
t, e, _ = say(f"look {CORNER} :1", f"do create {CORNER} kind=recipe title=Dal servings=4")[-1]
check("an unknown kind is refused, naming the built-in ones and how to make one",
      "kind= must be note, task, chat" in e and "note tagged kind" in e, e)

# ---- 2. a kind note, then a thing of that kind
r = say(f"look {CORNER} :1", f'do create {CORNER} kind=note title=recipe tags=kind is=note expects=servings,time text="A dish and how to make it."')
check("a kind note is an ordinary note", not r[-1][1], r[-1][1])
check("the world knows it", "recipe" in kinds.known(W) and kinds.chain(W, "recipe") == ["recipe", "note", "text", "appearance", "thing"]
      and kinds.shape(W, "recipe") == "text", (kinds.known(W), kinds.chain(W, "recipe")))
r = say(f"look {CORNER} :1", f"do create {CORNER} kind=recipe title=Dal servings=4")
dal = made(r[-1])
check("create kind=recipe works once the note exists", dal is not None and not r[-1][1], r[-1][1])
t, e, _ = one("find kind:recipe")
check("kind:recipe finds it, kind:note does not", "Dal" in t and "Dal" not in one("find kind:note")[0], (t, one("find kind:note")[0]))
t, e, _ = one(f"examine {dal}")
check("examine says what it is and lists a note's verbs", "a recipe" in t and "rewrite" in t and "retitle" in t, t)

# ---- 3. the refusal now lists the kind made here
t, e, _ = say(f"look {CORNER} :1", f"do create {CORNER} kind=spaceship title=x")[-1]
check("the refusal names kinds made here", "a kind made here: recipe" in e, e)

# ---- 4. rekind within a shape, refused across shapes, undone
r = say(f"look {CORNER} :1", f"do create {CORNER} kind=note title=Plan text=words")
plan = made(r[-1])
t, e, rr = one(f"do rekind {plan} kind=task")
ev = rr.get("events", [None])[0] if rr.get("events") else None
check("rekind note -> task", not e and W.subjects[W.nodes[plan]["subject"]]["kind"] == "task", e or t)
t, e, _ = one(f"do rekind {plan} kind=chat")
check("rekind across shapes is refused", "keeps its shape" in e, e)
t, e, _ = one(f"do rekind {plan} kind=task")
check("rekind to the same kind is refused", "already" in e, e)
t, e, _ = one(f"do rekind {plan} kind=nosuch")
check("rekind to no kind is refused with the list", "kind= must be" in e and "recipe" in e, e)
evs = [x for x in W.events if x["verb"] == "rekind" and not x.get("undone")]
check("the event keeps the old word", evs and evs[-1]["args"] == {"kind": "task", "was": "note"}, evs[-1]["args"] if evs else "no event")
t, e, _ = one(f"undo {evs[-1]['id']}")
check("undo puts the kind back", not e and W.subjects[W.nodes[plan]["subject"]]["kind"] == "note", e or t)

# ---- 5. a lens is a kind
r = say(f"look {CORNER} :1", f'do create {CORNER} kind=note title=lens tags=kind is=note text="A lens: a note whose text says how a part of the world is shown."',
        f'do create {CORNER} kind=lens title=mine text="root : column\n  of kind:recipe\n  each c\nc : text \\"$title\\""')
lens = made(r[-1])
check("create kind=lens, no tag needed", lens is not None and not r[-1][1], r[-1][1])
t, e, _ = one("scene mine")
check("scene finds a lens by its kind", not e and "Dal" in t, e or t)
t, e, _ = one("find kind:note")
check("kind:note no longer lists the lens definition", "mine" not in t, t)
s = scene.find_lens(D, "mine")
check("is_lens by kind, and by the older tag", kinds.is_lens(s) and kinds.is_lens({"kind": "note", "tags": ["lens"]}) and not kinds.is_lens({"kind": "note", "tags": []}))
# the older way still works beside it, and rekind moves one over
r = say(f"look {CORNER} :1", f'do create {CORNER} kind=note title=old tags=lens text="root : column"')
old = made(r[-1])
t, e, _ = one("scene old")
check("a note tagged lens still prints", not e and "root" in t, e or t)
t, e, _ = one(f"do rekind {old} kind=lens")
check("rekind a tagged lens to kind=lens", not e and W.subjects[W.nodes[old]["subject"]]["kind"] == "lens", e)
t, e, _ = one("scene old")
check("it still prints", not e and "root" in t, e or t)
t, e, _ = one(f"do rekind {lens} kind=image")
check("a lens cannot become bytes", "keeps its shape" in e, e)

# ---- 6. a kind built on a world kind, and a loop
r = say(f"look {CORNER} :1", f'do create {CORNER} kind=note title=dessert tags=kind is=recipe text="A recipe eaten last."',
        f'do create {CORNER} kind=note title=loop tags=kind is=loop text="built on itself"')
check("a kind on a kind", kinds.chain(W, "dessert")[:3] == ["dessert", "recipe", "note"], kinds.chain(W, "dessert"))
check("a loop ends", kinds.chain(W, "loop")[-1] == "thing" and len(kinds.chain(W, "loop")) < 12, kinds.chain(W, "loop"))
check("a kind describes itself", kinds.describe(W, "dessert") == "A recipe eaten last." and kinds.describe(W, "chat").startswith("lines"), kinds.describe(W, "dessert"))

print(("all passed" if not fails else f"{len(fails)} failed: {', '.join(fails)}") + f" ({len(W.events)} events)")
sys.exit(1 if fails else 0)
