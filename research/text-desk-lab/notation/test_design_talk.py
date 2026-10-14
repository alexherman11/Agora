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
check("a line points at a passage", not err and scene.line_fields(last_line()) == {"about": PARA, "quote": "A change is a room."}, (txt, err))
check("with= sends a plain line to the other of the two", last_line()["to"] == [B], last_line())

txt, err = say(B, f"read {TALK}", f'do append {TALK} line="reworded it" about={PARA} mark=folded')[-1]
check("a folded line, to the asker", not err and scene.line_fields(last_line()).get("mark") == "folded" and last_line()["to"] == [A], (txt, err, last_line()))

txt, err = say(A, f"read {TALK}", f'do append {TALK} line="@{C}: what do you think?"')[-1]
check("a line that opens with @names is for them only, not the author too (Pike, 14 Oct)", not err and last_line()["to"] == [C], (txt, err, last_line()))

txt, err = say(A, f"read {TALK}", f'do append {TALK} line="x" about=a999999')[-1]
check("refused in words: about= names no thing here", "no thing here" in (txt + err), txt + err)

# 14 Oct (Alex: 'make those changes more general purpose'): a line takes any field of its own, as a thing takes props;
# what mark= or mood= means is the lens's to say, not the world's
txt, err = say(C, f"read {TALK}", f'do append {TALK} line="noted" mood=calm mark=maybe')[-1]
check("a line keeps any field it is given", not err and last_line().get("fields") == {"mood": "calm", "mark": "maybe"}, (txt, err, last_line()))
any_rows = scene.rows(D, f"lines:{TALK} mood=calm")
check("a line's own field is a row field, filtered like any", len(any_rows) == 1 and any_rows[0]["said"] == "noted", any_rows)
check("a line without that field reads it as empty", all(r["mood"] == "" for r in scene.rows(D, f"lines:{TALK}") if r["said"] != "noted"),
      scene.rows(D, f"lines:{TALK}"))
check("rows prints the lines' own fields in its header", "$mood" in scene.rows_text(D, f"lines:{TALK}").splitlines()[0],
      scene.rows_text(D, f"lines:{TALK}").splitlines()[0])

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
MENU = chr(10).join(["w : column", f"  of in:{CORNER}", "  each para",
                     "para : column", f'  let talkable = "yes" when $talk != ""', '  let talkable = "no" otherwise',
                     '  on menu "Comment" when talkable = "no" do comment $item line="$value"',
                     f'  on menu "Comment" when talkable = "yes" do append {TALK} line="$value" about=$item quote="$quoted"',
                     '  words : text "$text"'])
for src, verb in ((MENU, "comment"), (MENU.replace('when $talk != ""', 'when $text != ""'), "append")):
    msc = lens_ir.evaluate(D, src)
    scene.emit(msc)
    acts = [a for k in scene.painter_view(msc)["kids"] for a in k.get("acts", []) if a["on"] == "menu"]
    check(f"a menu entry with `when` is offered only where its test holds: {verb} (14 Oct: a design's comments go to its conversation)",
          acts and [a["line"].split(" ")[1] for a in acts] == [verb] * len(acts), acts)
check("light is printed as a count","light 1" in scene.to_text(sc, "w", A, 0), scene.to_text(sc, "w", A, 0)[:600])

# 14 Oct, made general: `when` on every gesture. Pike's case (e9108): Enter on a plain line should split without
# storing block=p, and on a list line split keeping the list; two Enter lines, one offered per paragraph.
txt, err = say(A, f"look {CORNER} :1", f'do create {CORNER} kind=note title="p" text="a list line" block=bullet')[-1]
LISTED = W.last_created
KEYS = chr(10).join(["w : column", f"  of in:{CORNER}", "  each para",
                     "para : column", '  let next = "bullet" when $block = "bullet"', '  let next = "p" otherwise',
                     '  words : text "$text"', '    on edit do rewrite $item text="$value"',
                     '    on key Enter when next = "p" do splitplain $item "$head" "$tail"',
                     '    on key Enter when next != "p" do split $item $(next) "$head" "$tail"',
                     '    on click when next = "bullet" do prop $item remove=block'])
ksc = lens_ir.evaluate(D, KEYS)
scene.emit(ksc)
by_item = {k["kids"][0]["paint"].get("text"): [a for a in k["kids"][0]["acts"] if a["on"] in ("key", "click")] for k in scene.painter_view(ksc)["kids"]}
check("two Enter lines with `when`: a plain line is offered the plain split only",
      [a["line"].split(" ")[1] for a in by_item.get("A change is a room. The builder is in it.", [])] == ["splitplain"], by_item)
check("... and a list line the list split, and a click that holds only there",
      sorted(a["line"].split(" ")[1] for a in by_item.get("a list line", [])) == ["prop", "split"], by_item)
try:
    lens_ir.evaluate(D, KEYS.replace('when next = "p"', 'when next = = "p"'))
    check("a `when` that is not an expression is refused when the lens is read", False)
except scene.LensRefusal as e:
    check("a `when` that is not an expression is refused when the lens is read", "when" in str(e), e)

# `on select`: the gesture is offered like any, and the lens says where a highlight is kept (here, a prop on a desk
# note of the viewer's own), so a second template lights it beside the passages talked about
txt, err = say(A, f"look {CORNER} :1", f'do create {CORNER} kind=note title="mine" text="" role=reviewer quoting={PARA} quote="The builder"')[-1]
MINE = W.last_created
SEL = chr(10).join(["w : column", f"  of {MINE} as r", "  each mine", "mine : column", "  doc : column", f"    of in:{CORNER},-prop:role", "    each para",
                    "para : column", f'  let spots = join($quote of lines:{TALK} about=$item)',
                    '  let mine = $r.quote when $r.quoting = $item', '  let mine = "" otherwise',
                    '  on select do prop $r quoting=$item quote="$value"',
                    '  words : text "$text"', '    light "$(spots)" "$(mine)"'])
ssc = lens_ir.evaluate(D, SEL)
scene.emit(ssc)
paras = [k for k in scene.painter_view(ssc)["kids"][0]["kids"][0]["kids"]]
lit = [k["kids"][0]["paint"].get("light") for k in paras if k["kids"] and k["kids"][0]["paint"].get("text", "").startswith("A change")]
check("light takes more than one template: the talked-about passage and this viewer's own highlight",
      lit == [["A change is a room.", "The builder"]], lit)
sel_acts = [a for k in paras for a in k.get("acts", []) if a["on"] == "select"]
check("on select is offered with $value left for the painter and $r filled",
      sel_acts and all(f"prop {MINE} quoting=" in a["line"] and 'quote="$value"' in a["line"] for a in sel_acts), sel_acts)
txt, err = say(A, f"look {CORNER} :1", sel_acts[0]["line"].replace("$value", "is a room"))[-1]
check("the select line, filled as the painter fills it, keeps the highlight as world data",
      not err and (W.subjects[W.nodes[MINE]["subject"]].get("props") or {}).get("quote") == "is a room", (txt, err))

print(f"\n{len(fails)} failed" if fails else "\nall passed")
sys.exit(1 if fails else 0)
