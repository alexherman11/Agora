"""test_persons_stored (a1590, design a1016 rule 2): stored names become persons when saved.

    python test_persons_stored.py

Builds its own small world in memory (roomworld.py), runs every line through the desk's own dispatch. The story is the
live one, shrunk: the first Juniper owns a card and keeps a queue view, a rule and a lens that say owner=juniper; Pike
keeps 'What I owe' (held-by:pike); Alex's Desktop says person=alex. Then a new Juniper takes up the name and `person
begin` splits them. The done-when of a1590, as goals: (i) the first Juniper's view, rule and lens stop showing or claiming
the current Juniper's cards, and the current Juniper's own view shows hers; (ii) a view bound at save keeps its person:
Pike renamed kestrel, a new Pike made, 'What I owe' still shows kestrel's promise, and a view naming juniper,first shows
none of today's Juniper's; (iii) owner=juniper typed today means today's Juniper; (iv) the migration counts every name
it bound to an earlier person, and names each; undo takes it back.
"""
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import persons     # noqa: E402
import roomworld   # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build(say=False)
W = D.world


def say(me, *lines):
    """One reply as `me` -> the text of the last line run (an error is returned as 'ERR ...')."""
    W.me = me
    per = D._per
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""
    token, out = uuid.uuid4().hex, ""
    for line in lines:
        r = D.dispatch("desk", {"line": line, "whole": True, "reply": token})
        out = r.get("text") or ("ERR " + (r.get("error") or ""))
        if r.get("error"):
            break
    if out.startswith("!! since") or out.startswith("ERR !! since"):     # the delta header is not the answer
        head, _, rest = out.partition("\n")
        while rest.startswith("   "):
            rest = rest.partition("\n")[2]
        out = ("ERR " if out.startswith("ERR") else "") + rest
    return out


def last(verb=None):
    return [e for e in W.events if verb is None or e["verb"] == verb][-1]["id"]


def made(text):
    import re
    m = re.findall(r"created ([af]\d+)", text)
    return m[-1] if m else None


def shows(view):
    return set(D.view_matches(view) or [])


B, J, P = R.BOARD, R.corner["juniper"], R.corner["pike"]

# ---- before: the first Juniper, Pike and Alex, in a world without persons ---------------------------------------------
A = made(say("juniper", f"look {B} :1", f'do create {B} kind=task title="The first one\'s card" owner=juniper status=open'))
QUEUE = made(say("juniper", f"look {B} :1",
                 f'do create {B} kind=view title="Juniper: my queue" query=kind:task,prop:owner=juniper,-prop:status=done'))
RULE = made(say("juniper", f"look {B} :1", f'do create {B} kind=note title="tag mine" tags=rule '
                                          f'text="when kind:task,prop:owner=juniper do tag $item add=firsts"'))
LENS = made(say("juniper", f"look {B} :1", f'do create {B} kind=note title="queue lens" tags=lens '
                                          f'text="root : column, of kind:task,prop:owner=juniper, each c\\nc : text \\"$title\\""'))
say("pike", "promise to=sable look over the board")
OWE = made(say("pike", f"look {P} :1", f'do create {P} kind=view title="What I owe" query=kind:promise,held-by:pike'))
say("alex", f"look {R.DESKTOP} :1", f"do prop {R.DESKTOP} person=alex")

# the new Juniper's first act is the split
Bc = made(say("juniper", f"look {B} :1", f'do create {B} kind=task title="Today\'s card" owner=juniper status=open'))
E_SPLIT = last("create")
t = say("alex", f"person begin again=juniper:{E_SPLIT}")
check("person begin splits the two Junipers", "ok" in t.lower() or "person" in t.lower(), t)
JF, JN = persons.typed(W, "juniper,first")[0], persons.typed(W, "juniper")[0]
check("two Junipers, two persons", JF and JN and JF != JN, (JF, JN))

# ---- the migration runs once, on the next line, and says what it did -----------------------------------------------
say("alex", f"look {B} :1")
mig = [e for e in W.events if e["verb"] == "person" and e["target"] == "persons" and "bound" in (e.get("args") or {})]
check("one migration event, by the house", len(mig) == 1 and mig[0]["by"] == "house", mig)
M = mig[0] if mig else {"args": {}, "note": ""}
note = M.get("note") or ""
check("(iv) its note counts what bound to an earlier person: the first's card, view, rule and lens (4)",
      M["args"].get("earlier") == 4 and "4 bound to an earlier person" in note, note)
check("(iv) and names each of them", all(x in note for x in (A, QUEUE, "tag mine", "queue lens")), note)
check("(iv) today's card binds to today's Juniper, and is not counted as earlier", Bc not in note, note)
SA, SB = W.nodes[A]["subject"], W.nodes[Bc]["subject"]
check("the first's card holds the first Juniper", W.subjects[SA]["props"]["owner"] == JF, W.subjects[SA]["props"])
check("today's card holds today's Juniper", W.subjects[SB]["props"]["owner"] == JN, W.subjects[SB]["props"])
check("the Desktop's person=alex is Alex's person (a1062)",
      W.nodes[R.DESKTOP]["props"]["person"] == persons.typed(W, "alex")[0], W.nodes[R.DESKTOP]["props"])
import rooms   # noqa: E402
check("... and Alex still reads as a person at a keyboard", rooms.kind_of(W, "alex") == "person", rooms.kind_of(W, "alex"))
say("alex", f"look {B} :1")
check("the migration never runs twice", len([e for e in W.events if e["verb"] == "person" and "bound" in (e.get("args") or {})]) == 1)

# ---- printing: a person prop prints as the name, with the mark only where two bore it --------------------------------
ex = say("alex", f"examine {A}")
check("examine prints the first's card as owner=juniper,first", "owner=juniper,first" in ex, ex)
ex = say("alex", f"examine {Bc}")
check("today's card prints owner=juniper, no mark", "owner=juniper " in ex + " " and "juniper,first" not in ex, ex)
tb = say("alex", f"table kind:task cols=owner")
check("a table column prints names, never ids", "juniper,first" in tb and not any(x in tb for x in (JF, JN)), tb)

# ---- (i) the first Juniper's stored lines stop claiming today's Juniper's cards -------------------------------------
check("(i) the first's queue shows her card and not today's", A in shows(QUEUE) and Bc not in shows(QUEUE), shows(QUEUE))
ex = say("alex", f"examine {QUEUE}")
check("examine the queue says whom its query's names are bound to", "query: its names are bound to persons (a1590): "
      f"juniper → juniper, first ({JF})" in ex, ex)
sc = say("alex", "scene \"queue lens\"")
check("(i) the first's lens shows her card, not today's", "The first one" in sc and "Today's card" not in sc, sc)
B2 = made(say("juniper", f"look {B} :1", f'do create {B} kind=task title="Another of today\'s" owner=juniper status=open'))
say("alex", f"look {B} :1")
check("(i) the first's rule doesn't claim today's new card", "firsts" not in W.subjects[W.nodes[B2]["subject"]]["tags"],
      W.subjects[W.nodes[B2]["subject"]]["tags"])
B3 = made(say("alex", f"look {B} :1", f'do create {B} kind=task title="For the first one" owner=juniper,first status=open'))
say("alex", f"look {B} :1")
check("(i) ... and still fires for a card the first Juniper owns", "firsts" in W.subjects[W.nodes[B3]["subject"]]["tags"],
      W.subjects[W.nodes[B3]["subject"]]["tags"])
ex = say("alex", f"examine {RULE}")
check("examine the rule says whom its names are bound to", "juniper → juniper, first" in ex, ex)

r = say("juniper", f"look {J} :1", f'do create {J} kind=view title="Mine" query=kind:task,prop:owner=juniper,-prop:status=done')
MINE = made(r)
check("(i) today's Juniper's own view, saved now, binds to her and says so",
      "bound to persons" in r and f"juniper → juniper ({JN})" in r, r)
check("(i) ... and shows hers, not the first's", Bc in shows(MINE) and B2 in shows(MINE) and A not in shows(MINE), shows(MINE))

# ---- (iii) a typed name is today's bearer -----------------------------------------------------------------------------
r = say("pike", f"look {B} :1", f'do create {B} kind=task title="For today\'s Juniper" owner=juniper status=open')
B4 = made(r)
check("(iii) owner=juniper typed today holds today's Juniper", W.subjects[W.nodes[B4]["subject"]]["props"]["owner"] == JN)
# 9 Oct (a3299, a3806): the door to the first is a standing fact, so the claim's receipt no longer repeats it; examine does
check("(iii) the receipt reads as typed, and does not say the door to the first again", "owner=juniper" in r and "juniper,first" not in r, r)
ex = say("pike", "examine juniper")
check("(iii) ... examine juniper is where the door to the first is said", "juniper,first" in ex, ex)
f = say("pike", "find prop:owner=juniper")
check("(iii) find prop:owner=juniper is today's Juniper's cards", B4 in f and Bc in f and A not in f, f)
f = say("pike", "find prop:owner=juniper,first")
check("(iii) find prop:owner=juniper,first is the first's", A in f and B3 in f and Bc not in f, f)
r = say("pike", f"look {B4} :1", f"do prop {B4} owner={JF}")
check("a person id typed is that person, and prints as the name", W.subjects[W.nodes[B4]["subject"]]["props"]["owner"] == JF
      and "owner=juniper,first" in r, r)
r = say("pike", f"look {B4} :1", f"do prop {B4} owner=nobody-yet")
check("a name no one bears is kept as a word, and the receipt says so",
      W.subjects[W.nodes[B4]["subject"]]["props"]["owner"] == "nobody-yet" and "kept as a word" in r, r)

# ---- (ii) a view bound at save keeps its person through a rename and a new bearer ------------------------------------
PK = persons.typed(W, "pike")[0]
before = shows(OWE)
check("(ii) Pike's 'What I owe' shows Pike's promise", len(before) == 1, before)
say("alex", "person pike name=kestrel")
say("alex", "person new pike")
NP = persons.typed(W, "pike")[0]
check("(ii) a new Pike now bears the name", NP and NP != PK, (NP, PK))
say("pike", "promise to=sable a promise of the new Pike")
check("(ii) 'What I owe' still shows kestrel's promise, and not the new Pike's", shows(OWE) == before, (shows(OWE), before))
check("(ii) typed held-by:pike is the new Pike's", len(set(D._parse_selection("kind:promise,held-by:pike")[0]) - before) == 1)
r = say("alex", f"look {B} :1", f'do create {B} kind=view title="The first one\'s" query=kind:task,prop:owner=juniper,first')
FIRSTS = made(r)
check("(ii) a view naming the first Juniper binds to her at save", f"juniper,first → juniper, first ({JF})" in r, r)
check("(ii) ... and shows none of today's Juniper's", not ({Bc, B2} & shows(FIRSTS)) and A in shows(FIRSTS), shows(FIRSTS))
C = made(say("alex", f"look {B} :1", f'do create {B} kind=task title="Kestrel\'s" owner=kestrel status=open'))
say("alex", f"person {PK} name=wren")
check("a person prop follows a rename: owner prints the person's name now",
      "owner=wren" in say("alex", f"examine {C}"), say("alex", f"examine {C}"))

# ---- undo takes the migration back --------------------------------------------------------------------------------
import copy      # noqa: E402
D2 = copy.deepcopy(D)
W2 = D2.world
W2.undo(M["id"])
check("undo of the migration puts every name back as it was",
      W2.subjects[SA]["props"]["owner"] == "juniper" and W2.nodes[R.DESKTOP]["props"]["person"] == "alex"
      and "qbinds" not in W2.nodes[QUEUE], (W2.subjects[SA]["props"], W2.nodes[R.DESKTOP]["props"]))
check("... and it never runs again", persons.migrate(D2) is None)
say("alex", f"look {A} :1", f"do prop {A} status=doing")
try:
    W.undo(M["id"])
    check("undo of the migration waits while a later act touches what it bound", False, "undo went through")
except Exception as e:
    check("undo of the migration waits while a later act touches what it bound", "not the latest change" in str(e), e)

# ---- the house hears its commissioner by person, and by name where a world has no persons (Claude c2998) -------------
from types import SimpleNamespace   # noqa: E402
os.environ.setdefault("HOUSE_CLAUDE", "claude")       # the house looks for a claude binary; none is started here
import house      # noqa: E402
import workshop   # noqa: E402

HOUSE = SimpleNamespace(_inside=lambda w, n, f: house.House._inside(None, w, n, f),
                        _hold=lambda r, e, t: house.House._hold(None, r, e, t),
                        _knocked=lambda r, e, s, resting: house.House._knocked(None, r, e, s, resting))


def heard(d, me, card, by="worker-x"):
    """A comment on `card` by `by`; -> what house.news gathers for `me` (its own corner as the resident's)."""
    w = d.world
    n0 = len(w.events)
    w.me, d.seen, d.open = by, {}, {w.root}
    token = uuid.uuid4().hex
    for line in (f"read {card}", f'do comment {card} line="a question for whoever asked"'):
        out = d.dispatch("desk", {"line": line, "whole": True, "reply": token})
    assert len(w.events) > n0, out
    r = SimpleNamespace(rid=R.corner.get(me) or R.DESKTOP, state={"cursor": n0}, save=lambda: None)
    house.House.news(HOUSE, w, r, me)
    return "\n".join(r.state.get("inbox") or [])


K = made(say("kestrel", f"look {B} :1", f'do create {B} kind=task title="Kestrel\'s commission" asked_by=kestrel status=open'))
check("(house) asked_by= typed is stored as the person", W.subjects[W.nodes[K]["subject"]]["props"]["asked_by"] == PK)
check("(house) a begun world: the commissioner hears a comment on their commission, by the name they bear now (wren)",
      "on your commission" in heard(D, "wren", K), heard(D, "wren", K))
check("(house) the new bearer of their first name (pike) does not hear it", "on your commission" not in heard(D, "pike", K))
KF = made(say("alex", f"look {B} :1", f'do create {B} kind=task title="The first one\'s commission" asked_by=juniper,first status=open'))
check("(house) today's Juniper does not hear the first Juniper's commission", "on your commission" not in heard(D, "juniper", KF))
W.subjects[W.nodes[K]["subject"]]["props"]["asked_by"] = "kestrel"          # a mix: a name left in a begun world
check("(house) a name left in a begun world is still heard, by name", "on your commission" in heard(D, "kestrel", K))
W.subjects[W.nodes[K]["subject"]]["props"]["asked_by"] = PK
check("(house) workshop prints the commissioner's name, never the id", workshop.Workshop.asked_by(None, W, W.subjects[W.nodes[K]["subject"]]) == "wren")
check("(house) ... with the door mark for an earlier bearer, which typed back means them",
      workshop.Workshop.asked_by(None, W, W.subjects[W.nodes[KF]["subject"]]) == "juniper,first"
      and persons.typed(W, "juniper,first")[0] == JF)

D0, R0 = roomworld.build(say=False)      # a world that never began persons: asked_by stays a name, heard by name
W0 = D0.world
W0.me, D0.seen, D0.open = "pike", {}, {W0.root}
tok0 = uuid.uuid4().hex
D0.dispatch("desk", {"line": f"look {R0.BOARD} :1", "whole": True, "reply": tok0})
r0 = D0.dispatch("desk", {"line": f'do create {R0.BOARD} kind=task title="A commission" asked_by=pike', "whole": True,
                          "reply": tok0})
K0 = made(r0.get("text") or "")
check("(house) a world without persons keeps asked_by=pike as typed", W0.subjects[W0.nodes[K0]["subject"]]["props"]["asked_by"] == "pike",
      r0)
R_saved, R = R, R0
check("(house) ... and its commissioner hears comments on it, by name", "on your commission" in heard(D0, "pike", K0))
check("(house) ... and workshop prints the name as stored", workshop.Workshop.asked_by(None, W0, W0.subjects[W0.nodes[K0]["subject"]]) == "pike")
R = R_saved

print("\n" + ("all passed" if not fails else f"{len(fails)} failed: " + "; ".join(fails)))
sys.exit(1 if fails else 0)
