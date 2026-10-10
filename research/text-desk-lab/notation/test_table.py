"""test_table (8 Oct 2026, step 4 of the grammar unification): the row table.

    python test_table.py

Every word a host reads is a row with typed slots, read from the hosts' own tables into the sources words, slots and
kinds; a kind's row is what its things carry and what its note declares (`seats : number`); a value that is not the
declared kind is kept and the receipt remarks on it. Builds its own small world (roomworld.py).
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


D, R = roomworld.build(say=False)
W = D.world
ME = "juniper"
CORNER, HOME = R.corner[ME], R.HOME


def reply(*lines, me=ME):
    W.me = me
    token, out = uuid.uuid4().hex, []
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out.append((line, r.get("text") or "", r.get("error") or ""))
        if r.get("error"):
            break
    return out


import scene   # noqa: E402
import table   # noqa: E402

# 1. the hosts' tables as one
words = scene.rows(D, "words")
by = {(r["host"], r["word"]): r for r in words}
check("every built-in verb, command, lens word and term is a row", all(k in by for k in (("verb", "move"), ("verb", "create"), ("command", "find"), ("lens", "fold"), ("lens", "of"), ("term", "kind:"), ("term", "k op v"))), sorted(by)[:12])
check("a kind is a row in the same table", ("kind", "task") in by and ("kind", "note") in by, [k for k in by if k[0] == "kind"])
slots = scene.rows(D, "slots host=verb word=move")
check("rows slots host=verb word=move: into before after to by, each a typed slot, none needed on its own",
      [r["slot"] for r in slots] == ["target", "into", "before", "after", "to", "by"] and {r["type"] for r in slots[1:4]} == {"thing"} and slots[1]["needed"] == "", slots)
sl = {r["slot"]: r for r in scene.rows(D, "slots host=verb word=link")}
check("link: to is a thing, as a choice of blocks|refers|answers|part-of", sl["to"]["type"] == "thing" and sl["as"]["type"] == "choice" and "refers" in sl["as"]["doc"], sl)
sl = {r["slot"]: r for r in scene.rows(D, "slots host=lens word=fold")}
check("a lens word's shape is slots too: fold's label is prose, open and float are flags, handle is a name",
      sl.get("handle label", sl.get("label", {})).get("type") == "prose" and sl["open"]["type"] == "flag" and sl["float"]["type"] == "flag" and sl["handle"]["type"] == "name", sl)
sl = {r["slot"]: r for r in scene.rows(D, "slots host=lens word=let")}
check("let: a name, an expression, a `when` expression", sl["name"]["type"] == "name" and sl["expr"]["type"] == "expr", sl)
check("the words source takes a filter like any source", all(r["host"] == "lens" for r in scene.rows(D, "words host=lens")) and len(scene.rows(D, "words host=lens")) == len(scene.WORDS))

# 2. kinds: what things carry, and what a note declares
reply(f"look {CORNER} :1",
      f'do create {CORNER} kind=task title="T1" status=open seats=20',
      f'do create {CORNER} kind=task title="T2" status=done seats=3',
      f'do create {CORNER} kind=task title="T3" status=done')
kr = {r["kind"]: r for r in scene.rows(D, "kinds")}
check("rows kinds: a task's row says what its things carry, most common first, with the usual type",
      "task" in kr and kr["task"]["props"].startswith("status ") and "number" in kr["task"]["props"] and kr["task"]["shape"] == "text", kr.get("task"))
got = reply(f"look {HOME} :1", f'do create {HOME} kind=note tags=kind title=event is=task text="A gathering with seats.\\nseats : number\\nhost : person\\nwhen : date, needed\\nmood : calm|loud"')
check("a kind note is made with slot lines in the lens's line form", not got[-1][2], got[-1])
decl = table.declared(W, "event")
check("the declared slots are read: seats number, host person, when date needed, mood a choice",
      [(s.name, s.type, s.needed) for s in decl] == [("seats", "number", False), ("host", "person", False), ("when", "date", True), ("mood", "choice", False)]
      and decl[3].doc == "calm|loud", [(s.name, s.type, s.needed, s.doc) for s in decl])
kr = {r["kind"]: r for r in scene.rows(D, "kinds")}
check("rows kinds shows the declaration", "seats:number?" in kr["event"]["declared"] and "when:date" in kr["event"]["declared"], kr["event"])
sl = [r for r in scene.rows(D, "slots host=kind word=event")]
check("rows slots host=kind word=event lists the declared slots with how many things have each",
      [r["slot"] for r in sl] == ["seats", "host", "when", "mood"] and all("(0/0 have it)" in r["doc"] for r in sl), sl)

# 3. a kind describes, it never enforces: the value is kept, the receipt remarks
got = reply(f"look {CORNER} :1", f'do create {CORNER} kind=event title="Picnic" seats=lots mood=wild when=2026-10-20')
pic = W.last_created
props = W.subjects[W.nodes[pic]["subject"]]["props"]
check("the thing is made and keeps its values", props.get("seats") == "lots" and props.get("mood") == "wild", props)
check("the receipt remarks on seats (usually a number) and mood (a choice), and says the kind does not refuse",
      "seats=lots kept; a event's seats is usually a number" in got[-1][1] and "mood=wild kept" in got[-1][1] and "calm|loud" in got[-1][1]
      and "does not refuse" in got[-1][1], got[-1][1])
got = reply(f"look {CORNER} :1", f'do create {CORNER} kind=event title="Supper" seats=12')
check("a missing needed slot is remarked on at create, once", "usually has when" in got[-1][1] and "seats" not in got[-1][1].split("~")[-1], got[-1][1])
got = reply(f"read {pic} :1", f"do prop {pic} seats=40")
check("a prop set to the usual kind gets no remark", "~ seats" not in got[-1][1] and "kept;" not in got[-1][1], got[-1][1])
got = reply(f"read {pic} :1", f"do prop {pic} seats=many")
check("a prop set to an unusual kind is kept and remarked on", "seats=many kept" in got[-1][1] and W.subjects[W.nodes[pic]["subject"]]["props"]["seats"] == "many", got[-1][1])
sl = [r for r in scene.rows(D, "slots host=kind word=event")]
check("the slots now say how many events have each", any("(2/2 have it)" in r["doc"] for r in sl if r["slot"] == "seats"), sl)

# 4. a source's field is no longer a name taken from every lens
got = reply(f"look {CORNER} :1", f'do create {CORNER} kind=note tags=lens title=shapelens text="root : column, let shape = 1\\n  t : text \\"\\$(shape)\\""')
import lens_ir   # noqa: E402
sc, text = lens_ir.scene_for(D, "shapelens")
check("`let shape` compiles though a source has a field called shape (nearer binding wins)", not got[-1][2] and sc["kids"][0]["text"] == "1", (got[-1], text[:200]))

print(f"{len(fails)} failed" if fails else "all passed")
sys.exit(1 if fails else 0)
