"""test_prop_fields (a1322): prop query= changes a view's selection; a field the house keeps elsewhere is never a prop;
an ok never hides a blank kept as typed.

    python test_prop_fields.py

Rough spot a795: an ok for something that will never work. prop query= on a view stored a shadow prop and the view
went on showing its old selection (e1167, e3067); prop title= stored a title nobody reads (Juniper c1393); a wake line
with $new inside other words was kept as typed and the receipt said nothing. Builds its own small world in memory
(roomworld.py) and runs every line through the desk's own dispatch, as explore.py and deskd call it.
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


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
CORNER = R.corner[ME]


def say(*lines):
    """One reply as juniper. -> [(text, error)] for each line run; it stops at the first refusal, as explore does."""
    W.me = ME
    per = D._per
    if ME not in per:
        per[ME] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[ME]
    D._window = ""
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def one(line):
    return say(line)[0]


def props(ident):
    n = W.nodes[ident]
    return (n.get("props") if n["type"] == "surface" else W.subjects[n["subject"]].get("props")) or {}


# a view in my corner, of the board's two cards
say(f"look {CORNER} :1")
txt, err = one(f'do create {CORNER} kind=view title="Cards" query=in:{R.BOARD}')
VIEW = W.last_created
check("a view is made", not err and W.nodes[VIEW]["layout"] == "view", err or txt)
say(f"look {VIEW}")

# (1) prop query= changes the selection, at once
txt, err = one(f"do prop {VIEW} query=?letter")
check("prop query= on a view is an ok", not err, err)
check("the view's own query changed, not a shadow prop", W.nodes[VIEW]["query"] == "?letter" and "query" not in props(VIEW),
      (W.nodes[VIEW].get("query"), props(VIEW)))
check("the receipt shows the new selection and its match count", "of ?letter" in txt and "1 match" in txt, txt)
check("the receipt's head echoes query=", txt.startswith(f"ok prop {VIEW} query=?letter"), txt)
check("the receipt says what it was", f"selection was in:{R.BOARD}; now ?letter" in txt, txt)
txt, err = one(f"look {VIEW}")
check("look shows what the new selection matches", R.NOTE in txt and R.CARDS[0] not in txt, txt)

# a selection filled from a blank, and undo takes it back
txt, err = one(f"do prop {VIEW} query=in:$here")
check("a whole-selection blank fills in query= (a selection, not text)", not err and W.nodes[VIEW]["query"] == f"in:{CORNER}"
      if not err else False, err or W.nodes[VIEW].get("query"))
txt, err = one("undo")
check("undo puts the old selection back", not err and W.nodes[VIEW]["query"] == "?letter", err or W.nodes[VIEW].get("query"))

# a selection that doesn't parse is refused as find refuses it
say(f"look {VIEW}")
_, ferr = one("find bogus:x")
_, err = one(f"do prop {VIEW} query=bogus:x")
check("a bad term is refused with find's own words", err and ferr and err == ferr, (err, ferr))
_, err = one(f"do prop {VIEW} query=letter")
check("words that are no selection are refused, pointing at ?words", "not a selection" in err and "?letter" in err, err)
_, err = one(f"do prop {VIEW} query=")
check("an empty query is refused", "needs query=" in err, err)
check("nothing was stored by the refusals", W.nodes[VIEW]["query"] == "?letter" and not props(VIEW), (W.nodes[VIEW], props(VIEW)))
_, err = one(f"do prop {VIEW} query=?letter")
check("the same selection again is refused as a no-op", "already shows" in err, err)

# (2) of= is how a view reads, not a prop
_, err = one(f"do prop {VIEW} of=kind:note")
check("of= on a view is refused, naming query=", "query=" in err and "of" in err and "of" not in props(VIEW), err)

# (4) a field kept elsewhere is refused, naming its verb
say(f"look {CORNER} :1")
txt, err = one(f'do create {CORNER} kind=note title="Mine" text="a line"')
NOTE = W.last_created
say(f"read {NOTE}")
for k, v, verb in (("title", "Other", "retitle"), ("text", "hi", "rewrite"), ("kind", "task", "no verb"),
                   ("due", "2026-10-02", "do due"), ("tags", "a", "do tag"), ("query", "kind:task", "not a view"),
                   ("of", "x", "not a view")):
    _, err = one(f"do prop {NOTE} {k}={v}")
    check(f"prop {k}= on a note is refused, naming {verb}", err and verb in err and k not in props(NOTE), err)
_, err = one(f"do prop {CORNER} title=X")
check("prop title= on a surface names rename", "rename" in err, err)
_, err = one(f"do prop {NOTE} status=open title=X")
check("one field among props refuses the whole line", err and "status" not in props(NOTE), (err, props(NOTE)))
txt, err = one(f"do prop {NOTE} status=open")
check("an ordinary prop is still an ok", not err and props(NOTE).get("status") == "open", err)

# (3) a blank inside other words: the receipt says it was kept
txt, err = one(f'do prop {CORNER} wake="look $new"')
check("wake=\"look $new\" is an ok, kept as typed", not err and props(CORNER).get("wake") == "look $new", err or props(CORNER))
check("the receipt says $new was kept as typed, in one line",
      "\n  $new kept as typed: a blank fills only when the whole value is one blank (help blanks)" in txt, txt)
txt, err = one(f"do prop {NOTE} next=$today")
check("a whole-value blank fills and gets no note", not err and "kept as typed" not in txt and props(NOTE)["next"] != "$today", txt)
txt, err = one(f'do prop {NOTE} price="costs $5, \\$x"')
check("a price and an escaped dollar are no blanks: no note", not err and "kept as typed" not in txt, txt)
txt, err = one(f'do append {NOTE} line="see $here"')
check("text arguments keep their words with no note", not err and "kept as typed" not in txt, txt)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
