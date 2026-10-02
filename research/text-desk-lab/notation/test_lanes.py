"""test_lanes (a1081, for Alex's a1069 and Pike's design a1078): lanes sorted `by priority, rank`, the verb
`put <card> above=<card>`, and a drop on a card answered by the card. (`put` was named `place` until Pike's c1202:
one word, one meaning; `place` still makes a new appearance, and `put` with a move's arguments still moves.)

    python test_lanes.py

Builds its own small world (roomworld.py), in memory, never saved, and its own board of eight cards in two lanes.

a3029: the last check read the live Desktop's lens (command-center), gave it the lines a1081 proposed, and held it
under 1500 nodes. The lines have long been in the live lens, the budget is scene.BUDGET (5000 since 30 Sep), and the
Desktop's size is the world's, not this code's: it failed at 1529. What a1081 owned is the cost of its own lines, so
the check is now that: on a Desktop-shaped lens of this test's own, sorting the lanes and making the cards drop
targets add no scene node at all, however many cards there are.
"""
import os
import random
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


import roomworld  # noqa: E402

D, R = roomworld.build()
W = D.world

import lens_ir  # noqa: E402
import moo      # noqa: E402
import scene    # noqa: E402


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def said(me, *lines):
    """Lines in one reply -> the last (text, error)."""
    be(me)
    token, text, err = uuid.uuid4().hex, "", ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        text, err = r.get("text") or "", r.get("error") or ""
        if err:
            break
    return text, err


def prop(nid, key):
    return ((W.subjects[W.nodes[nid]["subject"]]).get("props") or {}).get(key)


# ---- (1) the word -----------------------------------------------------------------------------------------------
_, parts = scene.parse("root : column, of kind:task, by priority, rank, each c\nc : text $title")
check("`by priority, rank` reads as one word with two props", parts["root"]["by"] == ["priority", "rank"], parts["root"]["by"])
try:
    scene.parse("root : column, by priority\n  a : text x")
    check("`by` without `of` is refused", False)
except scene.LensRefusal as e:
    check("`by` without `of` is refused", "no `of`" in str(e), e)
check("order: numbers ascending, words after them, a missing value last",
      sorted(["3", None, "10", "b", "1", ""], key=moo.order_value) == ["1", "3", "10", "b", None, ""])

# ---- a board of our own, on its own surface: four cards in each of two lanes ----------------------------------
be("alex")
said("alex", "look")
home = R.DESKTOP
said("alex", f"look {home} :1", f'do group {home} title="Lanes test" as=column')
F = W.last_created
made = {}
for lane in ("open", "doing"):
    for t in ("plain", "blue", "yellow", "red"):
        said("alex", f"look {F} :1", f'do create {F} kind=task title="{lane} {t}" status={lane}-t')
        made[f"{lane} {t}"] = W.last_created
LENS = f"""root : column
  ol : column, of kind:task,prop:status=open-t,in:{F}, by priority, rank, each card
  dl : column, of kind:task,prop:status=doing-t,in:{F}, by priority, rank, each card
card : column, carry, on drop card do put $carried above=$item
  t : text "$title"
"""
said("alex", f"look {F} :1", f'do create {F} kind=note title="lanes-test-lens" tags=lens text=x')
LID = W.last_created
W.subjects[W.nodes[LID]["subject"]]["text"] = LENS


def lane(part):
    sc, _ = scene.scene_for(D, "lanes-test-lens")
    node = next(k for k in sc["kids"] if k["part"] == part)
    return [W.subjects[W.nodes[k["item"]]["subject"]]["title"].split(" ", 1)[1] for k in node["kids"] if k.get("item")], sc


# the right-click menu's four lines are `prop $item priority=N` and `prop $item remove=priority`
for lane_ in ("open", "doing"):
    for t, p in (("red", "1"), ("yellow", "2"), ("blue", "3")):
        said("alex", f"look {made[lane_ + ' ' + t]}", f"do prop {made[lane_ + ' ' + t]} priority={p}")
for part in ("ol", "dl"):
    order, sc = lane(part)
    check(f"{part}: four cards given priorities sort red, yellow, blue, plain", order == ["red", "yellow", "blue", "plain"], order)
text, _ = said("alex", "scene lanes-test-lens")
printed = re.findall(r'"(open|doing) (\w+)"', text)
check("the text print says the order ('by priority, rank') and prints the cards in it",
      "by priority, rank" in text and [t for l, t in printed if l == "open"] == ["red", "yellow", "blue", "plain"], text[:900])

# ---- (2) place above ------------------------------------------------------------------------------------------
red, blue = made["doing red"], made["doing blue"]
n0 = len(W.events)
out, err = said("alex", f"look {red}", f"look {blue}", f"do put {red} above={blue}")
print("     receipt: " + " | ".join(l.strip() for l in out.splitlines()[:3]))
check("a red card placed above a blue one turns blue", not err and prop(red, "priority") == "3", err or out)
check("... one event", len(W.events) - n0 == 1, W.events[n0:])
order, _ = lane("dl")
check("... and sits just above the blue card", order == ["yellow", "red", "blue", "plain"], order)
check("the receipt names what changed", "priority 1 -> 3" in out and "rank" in out, out)
ev = W.events[-1]
check("the event is `put` and touches status, priority and rank (the fence's aspects)",
      ev["verb"] == "put" and lens_ir.event_aspects(ev) == {"prop:status", "prop:priority", "prop:rank"}, (ev["verb"], ev.get("args")))

# across lanes: a Backlog card onto a Now card starts, takes its priority, sits above it
yb = made["open yellow"]
out, err = said("alex", f"look {yb}", f"look {blue}", f"do put {yb} above={blue}")
order, _ = lane("dl")
check("a Backlog card placed above a Now card starts, takes its priority, sits above it",
      not err and prop(yb, "status") == "doing-t" and prop(yb, "priority") == "3" and order == ["yellow", "red", "yellow", "blue", "plain"], (err, order))

# onto a card with no priority: the priority is removed
out, err = said("alex", f"look {yb}", f"look {made['doing plain']}", f"do put {yb} above={made['doing plain']}")
check("placed above a card with no priority, it has none", not err and prop(yb, "priority") is None, err or out)

# undo takes back the whole place, renumbered ranks included
before = {i: dict(W.subjects[W.nodes[i]["subject"]].get("props") or {}) for i in made.values()}
out, err = said("alex", f"look {red}", f"look {made['doing yellow']}", f"do put {red} above={made['doing yellow']}")
eid = W.events[-1]["id"]
out2, err2 = said("alex", f"undo {eid}")
after = {i: dict(W.subjects[W.nodes[i]["subject"]].get("props") or {}) for i in made.values()}
check("undo takes the place back whole, every rank it renumbered included", not err and not err2 and before == after, (err, err2, out2))

# a gap that runs out renumbers the group quietly, keeping its order
grp = [made["doing blue"], made["doing red"]]
for i in grp:
    W.subjects[W.nodes[i]["subject"]].setdefault("props", {})["priority"] = "3"
W.subjects[W.nodes[made["doing red"]]["subject"]]["props"]["rank"] = "5"
W.subjects[W.nodes[made["doing blue"]]["subject"]]["props"]["rank"] = "6"
yd = made["doing yellow"]
out, err = said("alex", f"look {yd}", f"look {made['doing blue']}", f"do put {yd} above={made['doing blue']}")
order, _ = lane("dl")
ranks = [prop(i, "rank") for i in (made["doing red"], yd, made["doing blue"])]
check("a gap that ran out is renumbered quietly: red, then the new one, then blue",
      not err and "renumbered" in out and order[:3] == ["red", "yellow", "blue"] and len(set(ranks)) == 3, (err, out, order, ranks))

# a drop on a lane's empty space: its status, its priority kept, the bottom of its group
ob = made["open blue"]
out, err = said("alex", f"look {ob}", f"do put {ob} status=doing-t")
order, _ = lane("dl")
check("place status= (a drop on a lane's empty space) puts it at the bottom of its priority group",
      not err and prop(ob, "priority") == "3" and order.index("blue") < order.index("blue", order.index("blue") + 1)
      and [o for o in order if o == "blue"] == ["blue", "blue"], (err, out, order))
n0 = len(W.events)
out, err = said("alex", f"look {ob}", f"do put {ob} status=doing-t")
check("placing it where it already is succeeds, says 'already there, nothing moved', and makes no event",
      not err and "already there, nothing moved" in out and len(W.events) == n0, (err, out))

# ---- twenty moves in a row never move a card they didn't touch -------------------------------------------------
rng = random.Random(1069)
cards = list(made.values())
bad = []
for k in range(20):
    x, y = rng.sample(cards, 2)
    seq_before = [W.nodes[i]["subject"] for i in [k2["item"] for k2 in next(n for n in scene.scene_for(D, "lanes-test-lens")[0]["kids"] if n["part"] == ("dl" if prop(y, "status") == "doing-t" else "ol"))["kids"] if k2.get("item")]]
    before_all = {p: [k2["item"] for k2 in n["kids"] if k2.get("item")] for n in scene.scene_for(D, "lanes-test-lens")[0]["kids"] for p in [n["part"]]}
    out, err = said("alex", f"look {x}", f"look {y}", f"do put {x} above={y}")
    after_all = {p: [k2["item"] for k2 in n["kids"] if k2.get("item")] for n in scene.scene_for(D, "lanes-test-lens")[0]["kids"] for p in [n["part"]]}
    for p in before_all:
        if [i for i in before_all[p] if i != x] != [i for i in after_all[p] if i != x]:
            bad.append((k, x, y, p, before_all[p], after_all[p], err))
    if not err:
        lane_after = after_all["dl" if prop(y, "status") == "doing-t" else "ol"]
        if lane_after.index(x) + 1 != lane_after.index(y):
            bad.append((k, x, y, "not just above", lane_after))
check("twenty places in a row: each lands just above its card, and no other card changes place", not bad, bad[:3])

# ---- one word, one meaning: put orders a card; with a move's arguments it still moves; place still places -------
said("alex", f"look {F} :1", f'do group {F} title="elsewhere" as=column')
G = W.last_created
c = made["open plain"]
props0 = dict(W.subjects[W.nodes[c]["subject"]].get("props") or {})
out, err = said("alex", f"look {c}", f"look {G} :1", f"do put {c} into={G}")
check("put <card> into=<surface> is still move: the card moves, its props untouched",
      not err and W.nodes[c]["parent"] == G and dict(W.subjects[W.nodes[c]["subject"]].get("props") or {}) == props0
      and W.events[-1]["verb"] == "move", (err, out))
said("alex", f"look {F} :1", f'do create {F} kind=note title="a note to put" text=x')
nt = W.last_created
out, err = said("alex", f"look {nt}", f"do put {nt} into={G}")
check("put on a note is move, as before (the synonym)", not err and W.nodes[nt]["parent"] == G, (err, out))
napps = len(W.appearances_of(W.nodes[c]["subject"]))
out, err = said("alex", f"look {c}", f"do place {c} into={F}")
check("place <card> into=<surface> still makes a new appearance", not err and len(W.appearances_of(W.nodes[c]["subject"])) == napps + 1, (err, out))
out, err = said("alex", f"look {nt}", f"look {red}", f"do put {nt} above={red}")
check("put above= on a note is refused, naming why", bool(err) and "note" in err, (err, out))

# ---- the lines a1081 added to the Desktop cost no scene node --------------------------------------------------------
# a3029: a lens shaped as the Desktop's Board (lanes that scroll, a card that carries, folds and has menus), over this
# test's own cards, without and with a1081's lines. The budget itself is scene.BUDGET's, and scene_for refuses past it
DESK = f"""cols : row, gap
  open : column, on drop card do put $carried status=open-t
    ol : column, of kind:task,prop:status=open-t,in:{F}, SORT scroll scroll, each card
  doing : column, on drop card do put $carried status=doing-t
    dl : column, of kind:task,prop:status=doing-t,in:{F}, SORT scroll scroll, each card
card : column, role card, carry, DROP on menu "start" do prop $item status=doing-t, on menu "priority 1" do prop $item priority=1
  more : column, fold "$title"
    tx : text "$text", role body
  acts : row, gap
    p1 : text "P1", role mark, only when prop:priority=1
    go : text "start", role tool, on click do prop $item status=doing-t, only when prop:status=open-t
"""
said("alex", f"look {F} :1", f'do create {F} kind=note title="desk-shaped-plain" tags=lens text=x')
W.subjects[W.nodes[W.last_created]["subject"]]["text"] = DESK.replace("SORT ", "").replace("DROP ", "")
said("alex", f"look {F} :1", f'do create {F} kind=note title="desk-shaped-a1081" tags=lens text=x')
W.subjects[W.nodes[W.last_created]["subject"]]["text"] = A1081 = DESK.replace("SORT ", "by priority, rank, ").replace(
    "DROP ", "on drop card do put $carried above=$item, ")
assert A1081.count("by priority, rank") == 2 and "above=$item" in A1081, A1081


def count(n):
    return 1 + sum(count(k) for k in n.get("kids", []))


def both():
    return count(scene.scene_for(D, "desk-shaped-plain")[0]), count(scene.scene_for(D, "desk-shaped-a1081")[0])


plain, sorted_ = both()
print(f"     a Desktop-shaped board over {len(W.children(F))} things: {plain} scene nodes plain, {sorted_} with a1081's lines")
check("sorting the lanes and making every card a drop target add no scene node", plain == sorted_ and plain > 1, (plain, sorted_))
for k in range(60):
    said("alex", f"look {F} :1", f'do create {F} kind=task title="more {k}" status={("open", "doing")[k % 2]}-t priority={k % 3 + 1}')
plain2, sorted2 = both()
print(f"     ... and with 60 more cards: {plain2} plain, {sorted2} with them (scene.BUDGET is {scene.BUDGET})")
check("... with 60 cards more, still none: the lines cost nothing per card", plain2 == sorted2 and plain2 > plain, (plain2, sorted2))
print(("FAILED: " + ", ".join(fails)) if fails else "all passed")
sys.exit(1 if fails else 0)
