"""test_promises (a1587, design a1576 with Revisions 2 and 3): promises and requests are things with honest ends.

    python test_promises.py

Builds its own small world in memory (roomworld.py) and runs every line through the desk's own dispatch. The story is
the live one, shrunk: before promises, cards carry owe= and awaiting= as props (one owe that is really a request, one
'none', one on a card already done, a commission with its due note). Then the migration runs once, at the next line,
and the done-when of a1587, as goals: each owe becomes a promise by whoever wrote it, an owe with its writer's
awaiting= a request of that person, flagged to them; a done card's open promise asks its holder once; views read
promises; a request is 'asked of you' until accepted; a promise carried is seen from both sides; closing a card asks
once and the answer ends it; a commission is its asker's promise and lived= its report; owe= is refused after; a
rename of a person moves nothing (the maker is read from events); undo takes back an act and the migration whole.
"""
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import promises    # noqa: E402
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


def made(text):
    m = re.findall(r"created (a\d+)", text)
    return m[-1] if m else None


B = R.BOARD


def create(me, where, how):
    say(me, f"look {where} :1")
    t = say(me, f"do create {where} {how}")
    m = re.search(r"created ([af]\d+)", t)
    assert m, t
    return m.group(1)


# ---- before promises: the props, written by who wrote them on the live board ---------------------------------------
check("the build migrated nothing: no owe= anywhere, so no Promises surface and no event", not promises.on(W)
      and not [e for e in W.events if e["verb"] == "promises"])
A = create("sable", B, 'kind=task title="Trash surface" owner=sable asked_by=claude status=doing')
say("sable", f"look {A} :1", f'do prop {A} owe="bring the Trash to the meeting"')
C = create("sable", B, 'kind=task title="Pulse" owner=sable status=doing')
say("sable", f"look {C} :1", f'do prop {C} owe="Pike\'s review before landing" awaiting=pike')
E = create("juniper", B, 'kind=task title="Old research" owner=juniper status=done owe="bring the report"')
N = create("sable", B, 'kind=task title="Nothing owed" owner=sable owe=none')
K = create("pike", B, 'kind=task title="Persons" owner=pike asked_by=pike status=open')
say("pike", f"look {K} :1", f"do prop {K} commission=asked")
DUE = create("house", R.corner["pike"], f'kind=note title="Your live check is due: Persons" due_for={K}')
V1 = create("sable", B, 'kind=view title="What I owe" query=kind:task,prop:owner=sable,-prop:status=done cols=title,owe')
V2 = create("pike", B, 'kind=view title="Waiting on me" query=prop:awaiting=pike cols=title,owe')
check("before: the views read the props", "Pulse" in say("pike", f"look {V2}") and "Trash surface" in say("sable", f"look {V1}"))

# ---- the migration, once, at the next line ---------------------------------------------------------------------------
W._promises_version = 0          # the world as it stood before a1587 landed
n0 = len(W.events)
t = say("sable", f"look {V1}")
mig = [e for e in W.events[n0:] if e["verb"] == "promises"]
check("one event by the house says the migration in history; the due notes' retirement is its consequence",
      len(mig) == 2 and all(e["by"] == "house" for e in mig) and mig[1].get("cause") == mig[0]["id"], W.events[n0:])
check("a card the migration changed is not 'changed status' by it (it says which aspects it touched)",
      "prop:status" not in __import__("desk").event_aspects(mig[0]))
note = mig[0].get("note", "") if mig else ""
check("the props go", not any(k in (W.subjects[W.nodes[x]["subject"]].get("props") or {}) for x in (A, C, E, N) for k in ("owe", "awaiting")))
sts = {promises.state(W, s)["about"]: promises.state(W, s) for s in promises.all_sids(W)}
st_a = sts.get(A)
check("an owe is a promise by whoever wrote it, owed to asked_by",
      st_a and st_a["state"] == "open" and st_a["maker"]["name"] == "sable" and st_a["owed"]["name"] == "claude", st_a)
st_c = sts.get(C)
check("an owe with its writer's awaiting=pike is a request of pike, held by its writer (a1193's shape)",
      st_c and st_c["state"] == "requested" and st_c["asker"]["name"] == "sable" and st_c["asked"]["name"] == "pike", st_c)
check("owe=none makes nothing", N not in sts, sts.keys())
st_k = sts.get(K)
check("a commission in flight is its asker's promise; its due note retires into it",
      st_k and st_k["maker"]["name"] == "pike" and W.subjects[W.nodes[DUE]["subject"]]["props"].get("status") == "done", st_k)
check("the view What I owe reads promises held", "held-by:sable" in W.nodes[V1]["query"] and "Trash surface" not in t
      and "bring the Trash to the meeting" in t, t)
asked = [s for s in W.subjects.values() if (s.get("props") or {}).get("promise") == (sts.get(E) or {}).get("aid")]
check("a done card's open promise asks its holder once, on their sill", len(asked) == 1 and
      W.nodes[W.appearances_of(asked[0]["id"])[0]]["parent"] == R.corner["juniper"], asked)
told = [s for s in W.subjects.values() if s["title"].startswith("What the promises migration made of yours")]
check("each writer is told what was made of theirs, on their sill", len(told) >= 2, [s["title"] for s in told])

# ---- (iii): a request is 'asked of you' until accepted --------------------------------------------------------------
t = say("pike", f"look {V2}")
check("Pike's Waiting on me says 'asked of you'", "asked of you by sable" in t, t)
aid_c = st_c["aid"]
t = say("juniper", f"look {aid_c} :1", f"accept {aid_c}")
check("only the one asked may accept", t.startswith("ERR") and "only pike" in t, t)
t = say("pike", f"accept {aid_c}")
check("accept makes it Pike's promise, owed to Sable", "you promised sable" in t, t)
check("and it leaves Waiting on me", "0 matches" in say("pike", f"look {V2}"))
# ---- (ii): carried, seen from both sides ----------------------------------------------------------------------------
t = say("pike", f"carry {aid_c} to=juniper")
check("carry: the old holder reads 'you carried it to juniper'", "you carried it to juniper" in t, t)
t = say("juniper", "promises")
check("the new holder reads 'carried to you from pike'", "carried to you from pike" in t, t)
t = say("sable", f"look {aid_c} :1")
check("the one owed sees who holds it now", "juniper holds it, owed to you" in t, t)
# ---- report and confirm; release; decline; withdraw --------------------------------------------------------------
t = say("juniper", f'report {aid_c} how="reviewed, two notes"')
check("report: 'reported, not confirmed', never a debt", "not confirmed" in t, t)
t = say("sable", "promises")
check("the one owed sees 'reported by juniper, not confirmed'", "reported by juniper, not confirmed" in t, t)
t = say("sable", f"confirm {aid_c}")
check("confirm: kept", "kept, confirmed by you" in t, t)
t = say("sable", f'ask to=juniper "read the census" about={A}')
q = made(t) or re.search(r"(a\d+) ask", t).group(1)
t = say("juniper", f"look {q} :1", f"decline {q}")
check("decline needs no reason", "declined by you" in t, t)
t = say("sable", f'ask to=pike "and the table" about={A}')
q2 = re.search(r"(a\d+) ask", t).group(1)
t = say("sable", f"withdraw {q2}")
check("the asker withdraws", "withdrawn by you" in t, t)
check("an ended promise refuses another end", say("sable", f"withdraw {q2}").startswith("ERR"))

# ---- (i): close a card with a promise open, without ending it: asked once, the answer ends it -----------------------
X = made(say("sable", f"look {B} :1", f'do create {B} kind=task title="Try it" status=doing'))
t = say("sable", f'promise to=alex "Alex sees it" about={X}')
p = re.search(r"(a\d+) promise", t).group(1)
t = say("sable", f"look {X} :1", f"do prop {X} status=done")
check("closing the card asks its holder once", "is asked once, on their sill" in t, t)
say("sable", f"look {X} :1", f"do prop {X} status=doing")
t = say("sable", f"look {X} :1", f"do prop {X} status=done")
check("and only once", "asked once" not in t, t)
t = say("sable", f"release {p}")
check("release ends it, no reason needed", "released by you" in t, t)
qs = [s for s in W.subjects.values() if (s.get("props") or {}).get("promise") == p]
check("and the sill question is answered with it", qs and qs[0]["props"].get("status") == "done", qs)

# ---- (7): a commission is its asker's promise; lived= is the report ---------------------------------------------------
Y = made(say("pike", f"look {B} :1", f'do create {B} kind=task title="Doors" owner=pike asked_by=pike status=open'))
t = say("pike", f"look {Y} :1", f"do prop {Y} commission=asked")
check("commission=asked makes its asker's promise", "a commission is its asker's promise" in t, t)
t = say("pike", f"look {Y} :1", f'do prop {Y} lived="lived it"')
check("lived= reports it; owed to yourself, kept on your own word", "kept (your own word)" in t, t)

# ---- the props stay gone; persons; undo ------------------------------------------------------------------------------
check("owe= is refused, naming promise", "promise to=" in say("sable", f"look {X} :1", f'do prop {X} owe="x"'))
t = say("sable", f"table kind:promise,held-by:sable cols=title,promise,holder")
check("held-by: selects and the promise column reads", "your own promise" in t or "you promised" in t, t)
check("help names each verb", all(not say("sable", f"help {v}").startswith("no command") for v in promises.VERBS))
say("jeff", "person begin")
say("jeff", "person pike name=kestrel")
t = say("sable", f"examine {aid_c}")
check("a rename moves nothing: who accepted and carried is read from events, and prints by the person's name now",
      "accept by kestrel" in t and "carry by kestrel" in t and "pike" not in t.split("verbs:")[0].replace("Pike's", ""), t)
t = say("juniper", f"undo")
check("undo of an act puts it back (a decline undone is a request again)", "reverted" in t, t)
D2, R2 = roomworld.build(say=False)        # a world where nothing came after the migration, so undo may reach it
W2 = D2.world
D, W = D2, W2
C2 = create("sable", R2.BOARD, 'kind=task title="Pulse" owner=sable status=doing')
say("sable", f"look {C2} :1", f'do prop {C2} owe="Pike\'s review before landing" awaiting=pike')
K2 = create("pike", R2.BOARD, 'kind=task title="Persons" owner=pike asked_by=pike status=open')
say("pike", f"look {K2} :1", f"do prop {K2} commission=asked")
DUE2 = create("house", R2.corner["pike"], f'kind=note title="Your live check is due: Persons" due_for={K2}')
W2._promises_version = 0
say("sable", "look :1")
m2 = [e for e in W2.events if e["verb"] == "promises"]
t = say("jeff", f"undo {m2[0]['id']}")
check("undo of the migration takes back what it made and what it caused, and puts the props back",
      "reverted" in t and not promises.all_sids(W2) and (W2.subjects[W2.nodes[C2]["subject"]].get("props") or {}).get("awaiting") == "pike"
      and W2.subjects[W2.nodes[DUE2]["subject"]]["props"].get("status") != "done", t)
say("sable", "look :1")
check("and it never runs again", len([e for e in W2.events if e["verb"] == "promises"]) == 2)

print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
