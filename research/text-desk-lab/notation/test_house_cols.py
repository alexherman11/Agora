# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_house_cols (a1431): a view or a table can show who made a thing and who last changed it, read from the house's
own events (made_by made_at edited_by edited_at), never from props; a column that names nothing is said.

    python test_house_cols.py

Rough spot a1429: a view read only props, so authorship showed only if people typed their names into titles, a name
standing in for the house's own record. Builds its own small world in memory (roomworld.py) and runs every line through
the desk's own dispatch, as explore.py and deskd call it, as two people.
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


def say(me, *lines):
    """One reply as `me`. -> [(text, error)] for each line run; it stops at the first refusal, as explore does."""
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


def row(txt, ident):
    return next((l.split() for l in txt.splitlines() if l.strip().startswith(ident + " ")), [])


J, P = R.corner["juniper"], R.corner["pike"]
say("juniper", f"look {J} :1")
(_, err), = say("juniper", f'do create {J} kind=note title="partA" tags=part text="one line"')
A = W.last_created
say("juniper", f'do create {J} kind=note title="partB" tags=part text="two"')
B = W.last_created
check("two parts are made by juniper", not err, err)

# pike edits one of them; a comment and a move are not edits
say("pike", f"read {A}", f'do append {A} line="pike was here"')
say("juniper", f"read {B}", f'do comment {B} line="a thought"')

txt, err = say("pike", f"look {P} :1", f"do create {P} kind=view title=Parts query=tag:part cols=title,made_by,edited_by")[-1]
V = W.last_created
check("a view with house columns is made, with no note about its columns", not err and "nothing by" not in txt, err or txt)
txt, err = say("pike", f"look {V}")[0]
check("made_by reads the create's actor, nobody typing it", row(txt, A)[:4] == [A, "partA", "juniper", "pike"], txt)
check("a thing never edited after it was made has no edited_by", row(txt, B)[:3] == [B, "partB", "juniper"]
      and len(row(txt, B)) == 3, txt)

txt, err = say("pike", "table tag:part cols=made_at,edited_at")[0]
check("made_at and edited_at are times", not err and len(row(txt, A)) == 6 and row(txt, A)[2].count("-") == 2, txt)

# a column that names nothing is said on the create's receipt, and on table
txt, err = say("pike", f"do create {P} kind=view title=Probe query=tag:part cols=title,author,by")[-1]
check("the receipt names both columns as nothing",
      "author, by: nothing by those names on any of 2 things; house columns are made_by, made_at, edited_by, edited_at" in txt,
      err or txt)
txt, err = say("pike", "table tag:part cols=author")[0]
check("table says it too", "author: nothing by that name on any of 2 things" in txt, txt)
txt, err = say("pike", f"do prop {A} author=juniper", "table tag:part cols=author")[-1]
check("a prop one thing has is a column, nothing said", not err and "nothing by" not in txt, err or txt)

# a prop named like a house column is shadowed, and the receipt says so
txt, err = say("pike", f"do prop {B} made_by=nobody", "table tag:part cols=made_by")[-1]
check("the house's record wins over a prop of that name", row(txt, B)[:3] == [B, "partB", "juniper"], txt)
check("and the receipt says the prop is shadowed", "made_by: the house's record, not the prop made_by= that 1 of 2 things has" in txt,
      txt)
check("a view look itself says nothing about columns", "nothing by" not in say("pike", f"look {V}")[0][0])

# an undone edit counts for nothing
say("juniper", f"read {B}", f'do append {B} line="later"')
txt = say("pike", "table tag:part cols=edited_by")[0][0]
check("juniper's edit is the latest", row(txt, B)[2:3] == ["juniper"], txt)
say("juniper", "undo")
txt = say("pike", "table tag:part cols=edited_by")[0][0]
check("undone, the edit before it is the latest again", row(txt, B)[2:3] == ["pike"], txt)

# a1595: help views is a note in the world's Help binder now; health holds it to naming the four (helpnotes.check)
import helpnotes   # noqa: E402
say("pike", f"look {P} :1", f"do create {P} kind=surface title=Help", "do prop $new role=help")
HB = helpnotes.binder(W)
say("pike", f"look {HB} :1", f'do create {HB} kind=note title=views text="views: house columns made_by made_at edited_by"')
probs = [p for p in helpnotes.check(D) if '"views"' in p]
check("a views note that leaves out edited_at is told so by the check, naming the code's columns",
      len(probs) == 1 and "does not name the column edited_at (desk_knife.py HOUSE_COLS" in probs[0], probs)
txt = say("pike", "help views")[0][0]
check("help views prints the note", txt.rstrip().endswith("views: house columns made_by made_at edited_by"), txt)

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
