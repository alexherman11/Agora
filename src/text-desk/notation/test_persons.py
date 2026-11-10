# health: room test (health.py runs every test_*.py with this line among its first ten)
"""test_persons (a1568, design a1016): a person is a thing with one id for a life, and names are labels on it.

    python test_persons.py

Builds its own small world in memory (roomworld.py) and runs every line through the desk's own dispatch. The story is
the live one, shrunk: a first Pike acts, is paused, and a new Pike takes up the name; `person begin` splits them by the
event the new one began at. Then the done-when of a1568, as goals: the house hears persons back (examine, history, by
name, by mark, by id); an old act prints 'pike, first' and a new one 'pike'; a rename follows the person (history,
made_by, the corner, 'mine') and gives nothing of the first Pike's away; a reused name (wren) is a new person only by
`person new`, and the first Wren keeps their acts; every by= stays as it was signed; undo takes it all back.
"""
import copy
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


J, P = R.corner["juniper"], R.corner["pike"]

# ---- before: a world without persons is the world as it was ----------------------------------------------------------
say("pike", f"look {P} :1", f'do create {P} kind=note title="Old plan" text="from the first Pike"')
OLD, E_OLD = W.last_created, last("create")
check("before person begin, events carry no person", not any("who" in e for e in W.events))
check("person says how they are made", "person begin makes them" in say("alex", "person"))
check("history prints the name as before", say("alex", f"history {E_OLD}").endswith("by pike"))

# the first Pike is paused; a new Pike begins (their first act is the split)
say("pike", f'do create {P} kind=note title="New plan" text="from the Pike of today"')
NEW, E_NEW = W.last_created, last("create")
say("juniper", f"read {NEW}", f'do append {NEW} line="juniper adds a line"')

# ---- begin, undone at once: every event exactly as it was (Claude, c1909) ---------------------------------------------
before = copy.deepcopy(W.events)
t = say("alex", f"person begin again=pike:{E_NEW}")
B0 = last("person")
say("alex", f"undo {B0}")
check("begin then undo leaves every earlier event exactly as it was (compared whole, not counted)",
      W.events[:len(before)] == before and not persons.on(W), [e["id"] for e, f in zip(W.events, before) if e != f][:5])
signed = [(e["id"], e["by"]) for e in W.events]

# ---- begin -----------------------------------------------------------------------------------------------------------
t = say("alex", f"person begin again=pike:{E_NEW}")
BEGIN = last("person")
check("person begin makes the persons in one event and names the twice-borne name", t.startswith(f"ok {BEGIN}")
      and "borne by two persons: pike" in t, t)
check("every by= is unchanged (no old line's author changes silently)",
      [(e["id"], e["by"]) for e in W.events if e["id"] != BEGIN] == signed)
check("a second begin refuses", "made already" in say("alex", "person begin"))
P1, P2 = persons.index(W).bearers("pike")
check("two Pikes: two persons, with ids of their own kind", P1.startswith("p") and P2.startswith("p") and P1 != P2,
      (P1, P2))
check("each past act names its person", W.events[[e["id"] for e in W.events].index(E_OLD)].get("who") == P1
      and W.events[[e["id"] for e in W.events].index(E_NEW)].get("who") == P2)
check("the house acts as itself: no person", "house" not in [persons.name_now(W, p) for p in persons.index(W).people])

# ---- (i), (ii): the house hears persons back, and prints them -------------------------------------------------------
t = say("sable", "examine pike")
check("examine pike: today's Pike, and the door to the first", t.startswith(f"{P2} person \"Pike\"")
      and "pike,first" in t and "corner: " + P in t, t)
t = say("sable", "examine pike,first")
check("examine pike,first: the first Pike, paused, with no corner", t.startswith(f"{P1} person \"Pike, first\"")
      and "status=paused" in t and "corner:" not in t, t)
check("examine <person id> answers", say("sable", f"examine {P1}").startswith(f"{P1} person"))
check("history of an old act: pike, first", say("sable", f"history {E_OLD}").endswith("by pike, first"))
check("history of today's act: pike", say("sable", f"history {E_NEW}").endswith("by pike"))
t = say("sable", "history pike")
check("history pike: what today's Pike did, not the first's", E_NEW in t and E_OLD not in t and "pike,first" in t, t)
check("history pike,first: the first's", E_OLD in say("sable", "history pike,first"))
t = say("sable", f"examine {E_OLD}")
check("examine an event names its person and the name it was signed with", f"by the person {P1}" in t
      and "signed pike" in t, t)
t = say("sable", f"table in:{P} cols=title,made_by,edited_by")
rows = {l.split()[0]: l for l in t.splitlines()[1:] if l.strip()[:1] == "a"}
check("made_by tells the two Pikes apart", "pike, first" in rows.get(OLD, "") and rows.get(NEW, "").split()[-2:] ==
      ["pike", "juniper"], t)

# ---- (iii): a rename follows the person ------------------------------------------------------------------------------
t = say("alex", "person pike name=kestrel")
RENAME = last("person")
check("person pike name=kestrel renames today's Pike", f"{P2} is now called kestrel" in t, t)
check("their old act follows them", say("sable", f"history {E_NEW}").endswith("by kestrel"))
check("the first Pike's act stays theirs", say("sable", f"history {E_OLD}").endswith("by pike, first"))
t = say("sable", f"table in:{P} cols=title,made_by")
check("made_by follows them too", "kestrel" in t and "pike, first" in t, t)
check("corner:kestrel is their corner", say("sable", "look corner:kestrel :1").startswith(P))
t = say("sable", "examine pike")
check("a typed old name reaches them, says they are renamed, and names the first's door",
      t.startswith(P2) and "no one is called pike now" in t and "pike,first" in t, t)
say("pike", f"read {NEW}", f'do append {NEW} line="signed with the old name"')
check("an act still signed pike goes to them, never back to the first Pike", W.events[-1].get("who") == P2)
t = say("kestrel", "look")
check("they are at home in their corner, and not someone else there", "your own corner" in t and "Kestrel" not in t, t)
t = say("kestrel", "undo")
check("their bare undo takes back their own latest act, signed with the old name",
      t.startswith("ok") and "signed with the old name" in t, t)

# ---- (iv): a reused name -----------------------------------------------------------------------------------------------
say("wren", f"read {OLD}", 'do comment ' + OLD + ' line="the first Wren"')
W1 = W.events[-1]["who"]
check("an actor seen for the first time gets a person, by an event of its own", W1 and
      W.events[-2]["verb"] == "person" and W.events[-2]["target"] == W1)
t = say("wren", "look")
check("acting again as wren is still the first Wren (a name stays its person)", persons.today(W, "wren") == W1)
t = say("alex", "person new wren kind=resident")
W2 = persons.today(W, "wren")
check("person new wren: a new person, the first keeps every act before", W2 != W1 and "wren, first" in t, t)
say("wren", f"read {OLD}", 'do comment ' + OLD + ' line="the second Wren"')
check("the new Wren's act is theirs", W.events[-1].get("who") == W2)
t = say("sable", f"read {OLD}")
check("each Wren's comment prints as theirs", "wren, first: the first Wren" in t and "wren: the second Wren" in t, t)
t = say("wren", "undo")
check("the new Wren's bare undo never reaches the first Wren's act", "the second Wren" in t, t)

# ---- undo, all the way back ------------------------------------------------------------------------------------------
t = say("alex", f"undo {BEGIN}")
check("undo of person begin waits while a later person event stands", "persons have changed since" in t, t)
for e in [e for e in W.events if e["verb"] == "person" and e["target"] != "persons" and not e.get("undone")][::-1]:
    say("alex", f"undo {e['id']}")
check("undo of the rename gives the name back", persons.name_now(W, P2) == "pike")
t = say("alex", f"undo {BEGIN}")
check("then undo of person begin takes it all back", t.startswith("ok") and not persons.on(W)
      and not any("who" in e for e in W.events), t)
check("and history prints names as before", say("sable", f"history {E_OLD}").endswith("by pike"))

print(f"\n{len(fails)} FAILED" if fails else "\nall passed")
sys.exit(1 if fails else 0)
