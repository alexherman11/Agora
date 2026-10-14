"""test_design_talk (13 Oct): a conversation about a design, where a message may point at a passage.

    python test_design_talk.py

Alex, 13 Oct, for the design-review documents: one conversation per design between him and its author, where @anyone
may be called in; a message may point at a passage of the design (about=, quote=) and say what it is (mark=ask: it
wants an answer; mark=folded: the point was taken in); the passages talked about are lit in the document. Builds its
own small world (roomworld.py).
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import expr        # noqa: E402
import lens_ir     # noqa: E402
import roomworld   # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world


def say(me, *lines):
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


A, B, C = "juniper", "pike", "sable"
CORNER = R.corner[A]
txt, err = say(A, f"look {CORNER} :1", f'do create {CORNER} kind=note title="p" text="A change is a room. The builder is in it."')[-1]
PARA = W.last_created
txt, err = say(A, f"look {CORNER} :1", f'do create {CORNER} kind=chat title="talk" with={A},{B}')[-1]
TALK = W.last_created
check("a paragraph and a conversation", PARA and TALK and not err, txt + err)
chat = W.subjects[W.nodes[TALK]["subject"]]


def last_line():
    return chat["lines"][-1]


txt, err = say(A, f"read {TALK}", f'do append {TALK} line="is this restrictive?" about={PARA} quote="A change is a room."')[-1]
check("a line points at a passage", not err and last_line().get("about") == PARA and last_line().get("quote") == "A change is a room.", (txt, err))
check("with= sends a plain line to the other of the two", last_line()["to"] == [B], last_line())

txt, err = say(B, f"read {TALK}", f'do append {TALK} line="reworded it" about={PARA} mark=folded')[-1]
check("a folded line, to the asker", not err and last_line().get("mark") == "folded" and last_line()["to"] == [A], (txt, err, last_line()))

txt, err = say(A, f"read {TALK}", f'do append {TALK} line="@{C}: what do you think?"')[-1]
check("a line that opens with @names is for them only, not the author too (Pike, 14 Oct)", not err and last_line()["to"] == [C], (txt, err, last_line()))

for line, word in ((f'do append {TALK} line="x" about=a999999', "no thing here"),
                   (f'do append {TALK} line="x" about={PARA} mark=maybe', "mark= is ask"),
                   (f'do append {TALK} line="x" quote="room"', "say about=")):
    txt, err = say(A, f"read {TALK}", line)[-1]
    check(f"refused in words: {word}", word in (txt + err), txt + err)

rows = scene.rows(D, f"lines:{TALK} about={PARA}")
check("the lines rows carry about, quote and mark, and filter by about", len(rows) == 2 and rows[0]["quote"] == "A change is a room." and rows[1]["mark"] == "folded", rows)

v = expr.run(f"join($quote of lines:{TALK} about={PARA})",
             {"get": lambda n: None, "select": lambda q: [f"\x00row{k}" for k in range(len(scene.rows(D, q)))],
              "field": lambda i, f: rows[int(i[4:])].get(f)})[0]
check("join gathers a field, one a line, leaving out the empty", v.kind == "text" and v.v == "A change is a room.", (v.kind, v.v))

LENS = chr(10).join(["w : column", f"  doc : column", f"    of in:{CORNER}", "    each para",
                     "para : column", f'  let spots = join($quote of lines:{TALK} about=$item)',
                     '  words : text "$text"', '    light "$(spots)"'])
sc = lens_ir.evaluate(D, LENS)
scene.emit(sc)
pv = scene.painter_view(sc)
lit = [k["kids"][0]["paint"].get("light") for k in pv["kids"][0]["kids"] if k["kids"] and k["kids"][0]["paint"].get("text", "").startswith("A change")]
check("the passage talked about is lit in the paragraph's paint", lit == [["A change is a room."]], lit)
check("light is printed as a count", "light 1" in scene.to_text(sc, "w", A, 0), scene.to_text(sc, "w", A, 0)[:600])

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
