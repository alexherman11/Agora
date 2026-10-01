"""test_rule_bound (a1388, from Claude e3229 and Pike a1356): hitting the 3-round bound is said to the rules' authors.

    python test_rule_bound.py [world]        default frontier-try

Loads the world into memory and never saves it (the harness of test_rules.py). Rules trip rules in rounds: a round runs
each rule once, in the order they were made, so a chain written last-step-first takes one round per step. A 4-step
chain, by three authors, is tripped by juniper: the fourth step is not run, and the receipt, the sills and the counts
say so. A 3-step chain fits the bound and says nothing.
"""
import os
import pickle
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

WORLD = sys.argv[1] if len(sys.argv) > 1 else "frontier-try"
fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:2000]}"))
    if not ok:
        fails.append(name)


D = pickle.loads((HERE / "sessions" / f"{WORLD}.pickle").read_bytes())
W = D.world
D._session = WORLD + "-inmemory"


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


def last(me, *lines):
    _, text, err = reply(me, *lines)[-1]
    return text, err


import rooms   # noqa: E402

# rules already in the world would fire beside the ones written here: set them aside, in memory only (never saved)
for _s in W.subjects.values():
    if "rule" in (_s.get("tags") or []):
        _s["tags"] = [t for t in _s["tags"] if t != "rule"]
D._rulestate = None

BOARD = next(f for f in rooms.all_rooms(W) if W.nodes[f]["title"] == "Board")
TITLE = "your rules were stopped after 3 rounds"


def sill(who):
    fid = rooms.corner_of(W, who)
    return [k["id"] for k in W.children(fid) if k.get("subject") and W.subjects[k["subject"]]["title"] == TITLE]


def tags(nid):
    return W.subjects[W.nodes[nid]["subject"]].get("tags") or []


t, e = last("juniper", f"look {BOARD} :1", f"do create {BOARD} kind=surface title=\"Chain rules\" layout=column")
check("a surface for the rules", not e, e)
RULES = W.last_created


def rule(me, title, text):
    t, e = last(me, f"look {RULES} :1", f'do create {RULES} kind=note tags=rule title="{title}" text="{text}"')
    check(f"{me} saves {title}", not e and "saved:" in t, e or t)
    return W.last_created


def thing(title):
    t, e = last("juniper", f"look {RULES} :1", f'do create {RULES} kind=note title="{title}" text=x')
    return W.last_created


# ---- a 4-step chain, written last step first, by three authors ---------------------------------------------------------
D4 = rule("pike", "step 4", "when tag:b4 do tag add=b5")
C4 = rule("juniper", "step 3", "when tag:b3 do tag add=b4")
B4 = rule("juniper", "step 2", "when tag:b2 do tag add=b3")
A4 = rule("sable", "step 1", "when tag:b1 do tag add=b2")
# ---- a 3-step chain, the same way, by pike --------------------------------------------------------------------------
Z3 = rule("pike", "three 3", "when tag:c3 do tag add=c4")
Y3 = rule("pike", "three 2", "when tag:c2 do tag add=c3")
X3 = rule("pike", "three 1", "when tag:c1 do tag add=c2")
pike0, sable0, juniper0 = len(sill("pike")), len(sill("sable")), len(sill("juniper"))

# ---- the 3-step chain fits: nothing said ----------------------------------------------------------------------------
T3 = thing("three-step thing")
t, e = last("juniper", f"look {T3} :1", f"do tag {T3} add=c1")
check("3 steps: the chain runs to its end", not e and "c4" in tags(T3), e or t)
check("3 steps: no ~ line about the bound", "still firing" not in t, t)
check("3 steps: no sill notes", (len(sill("pike")), len(sill("sable"))) == (pike0, sable0))
t, e = last("pike", "rules")
check("3 steps: rules counts no stop", "stopped" not in t, t)

# ---- the 4-step chain is cut after round 3 ---------------------------------------------------------------------------
T4 = thing("four-step thing")
t, e = last("juniper", f"look {T4} :1", f"do tag {T4} add=b1")
print("     juniper's receipt:\n" + "\n".join("       " + l for l in t.splitlines() if l.startswith(("~", "  told"))))
check("4 steps: three run, the fourth does not", not e and "b4" in tags(T4) and "b5" not in tags(T4), (e or t, tags(T4)))
check("4 steps: the ~ line names the rule, its thing and its author, and says not run",
      f"~ rules still firing after 3 rounds: {D4} on {T4}, by pike; not run" in t, t)
check("4 steps: it names the sills told, not juniper's own (the tripper reads the ~ line)",
      "told on their sills: pike (" in t and "sable (" in t and "juniper (" not in t, t)
ps, ss = sill("pike"), sill("sable")
check("pike (the stopped rule's author) and sable (step 1's) each get one note", len(ps) == pike0 + 1 and len(ss) == sable0 + 1,
      (ps, ss))
check("juniper, who tripped it, gets none", len(sill("juniper")) == juniper0)
ptext = W.subjects[W.nodes[ps[-1]]["subject"]]["text"] if ps else ""
check("pike's note names their rule, stopped, and the whole chain",
      f'{D4} "step 4" was stopped: it would still fire on {T4}' in ptext and f"round 1: {A4} on {T4} (as sable)" in ptext
      and f"round 3: {C4} on {T4} (as juniper)" in ptext and f"stopped: {D4} on {T4} (as pike)" in ptext, ptext)
stext = W.subjects[W.nodes[ss[-1]]["subject"]]["text"] if ss else ""
check("sable's note names their rule as fired in it", f'{A4} "step 1" fired in it' in stext, stext)
t, e = last("pike", "rules")
check("rules counts the stop beside fired, failed, skipped",
      f"fired 0x · stopped by the 3-round bound 1x (last: on {T4}, set off by juniper" in t, t)
t, e = last("pike", f"examine {D4}")
check("examine <rule> says the same", "stopped by the 3-round bound 1x" in t, e or t)

# ---- the next change runs what was stopped -------------------------------------------------------------------------
t, e = last("juniper", f"look {RULES} :1", f'do create {RULES} kind=note title="any change" text=x')
check("what was stopped fires on the next change", "b5" in tags(T4) and f"~ {D4} fired on {T4}" in t, (t, tags(T4)))

# ---- tripped again: the ~ line and the count again, the authors not told twice ----------------------------------------
T5 = thing("another four-step thing")
t, e = last("juniper", f"look {T5} :1", f"do tag {T5} add=b1")
check("again: the ~ line again", f"~ rules still firing after 3 rounds: {D4} on {T5}, by pike" in t, t)
check("again: no second note (once per rule until its text changes)", len(sill("pike")) == pike0 + 1
      and len(sill("sable")) == sable0 + 1 and "told on their sills" not in t, t)
t, e = last("pike", "rules")
check("again: rules counts 2", "stopped by the 3-round bound 2x" in t, t)

# ---- a re-saved rule is told afresh ---------------------------------------------------------------------------------
t, e = last("pike", f"read {D4}", f'do replace {D4} old="add=b5" new="add=b6"')
check("pike re-saves step 4", not e and "saved" in t, e or t)
T6 = thing("a third four-step thing")
t, e = last("juniper", f"look {T6} :1", f"do tag {T6} add=b1")
check("after a re-save, its author is told again (and only they)", len(sill("pike")) == pike0 + 2
      and len(sill("sable")) == sable0 + 1 and "told on their sills: pike (" in t, t)

t, e = last("pike", "help rules")
check("help rules says it", "each act runs at" in t and "stopped by the bound" in t, t)

print(f"\n{'all passed' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
