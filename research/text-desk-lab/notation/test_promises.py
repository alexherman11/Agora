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
# ---- (ii): carried, seen from both sides; a carry is an offer until accepted (a2798) --------------------------------
t = say("pike", f"carry {aid_c} to=juniper")
check("carry is an offer: it stays Pike's, 'offered to juniper'", "you promised sable · offered to juniper" in t, t)
check("held-by: still selects Pike while it is offered", promises.state(W, W.nodes[aid_c]["subject"])["holder"]["name"] == "pike")
t = say("juniper", "promises")
check("the one offered reads 'offered to you by pike'", "offered to you (accept or decline)" in t and "offered to you by pike" in t, t)
check("only the one offered may answer it", "only they can accept" in say("sable", f"look {aid_c} :1", f"accept {aid_c}"))
t = say("juniper", f"look {aid_c} :1", f"decline {aid_c}")
check("a declined offer leaves it Pike's", "pike promised sable · you declined" in t, t)
t = say("pike", "promises")
check("and Pike reads 'juniper declined'", "you promised sable · juniper declined" in t, t)
t = say("pike", f"carry {aid_c} to=juniper")
check("a second offer, after a decline", "offered to juniper" in t, t)
check("one offer at a time", "already" in say("pike", f"carry {aid_c} to=sable"))
t = say("pike", f"withdraw {aid_c}")
check("the carrier withdraws the offer; it stays theirs", "ok" in t and "offered" not in t.split("\n")[0], t)
check("a withdrawn offer cannot be accepted", say("juniper", f"accept {aid_c}").startswith("ERR"))
say("pike", f"carry {aid_c} to=juniper")
t = say("juniper", f"accept {aid_c}")
check("accepted, it is theirs: 'carried to you from pike'", "carried to you from pike" in t, t)
t = say("pike", f"look {aid_c} :1")
check("the old holder reads 'you carried it to juniper'", "you carried it to juniper" in t, t)
t = say("juniper", "promises")
check("the new holder's list reads 'carried to you from pike'", "carried to you from pike" in t, t)
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
q_decline = re.search(r"ok (e\d+)", t).group(1)
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

# ---- a3198: lived= is its holder's word alone; anyone else's is testimony (lived_by=), which ends nothing -------------
V = made(say("sable", f"look {B} :1", f'do create {B} kind=task title="Visits" owner=sable asked_by=sable status=open'))
t = say("sable", f"look {V} :1", f"do prop {V} commission=asked")
pv = re.search(r"asker's promise: (a\d+)", t).group(1)
n_ev = len(W.events)
t = say("pike", f"look {V} :1", f'do prop {V} lived="{V}@4bf2a2a: the door let me in and out"')
check("a visitor's lived= on someone else's commission is refused, naming whose word it is and the line for testimony",
      t.startswith("ERR") and "is sable's word, not yours" in t and f'do prop {V} lived_by="{V}@4bf2a2a: <what you saw>"' in t
      and "Nothing was changed" in t, t)
check("and nothing was changed: no event, no lived= on the card, the promise open with one act",
      len(W.events) == n_ev and "lived" not in (W.subjects[W.nodes[V]["subject"]].get("props") or {})
      and promises.state(W, W.nodes[pv]["subject"])["state"] == "open", W.events[n_ev:])
t = say("pike", f"look {V} :1", f'do prop {V} lived_by="{V}@4bf2a2a: the door let me in and out"')
check("lived_by= is testimony: kept on the card, said to end nothing, and the promise stays sable's and open",
      f"lived_by= is your testimony on {V}: it ends nothing" in t and f"{pv} stays open: sable's own promise" in t
      and "Only sable's own lived= reports it" in t and promises.state(W, W.nodes[pv]["subject"])["state"] == "open", t)
t = say("sable", "promises")
check("sable's list shows it on her open promise: 'also lived by pike at <commit>'",
      f"{pv} " in t and "your own promise · also lived by pike at 4bf2a2a" in t, t)
say("juniper", f"look {V} :1", f'do prop {V} lived_by="read the receipts only, no visit"')
t = say("sable", f"examine {pv}")
check("a second testimony does not hide the first, and one naming no commit says no commit",
      "also lived by pike at 4bf2a2a; by juniper ·" in t and "testimony by pike" in t and "testimony by juniper" in t
      and "which ends nothing: read the receipts only" in t, t)
check("the promise is still held-by:sable, and no testimony made pike or juniper its holder",
      pv in say("sable", "table kind:promise,held-by:sable cols=title") and pv not in say("pike", "table kind:promise,held-by:pike cols=title"))
check("the door's question (whose commission is this?) answers by who asks",
      (setattr(W, "me", "sable") or promises.commission_of(W, V)) == {"promise": pv, "holder": "sable", "owed": "sable", "yours": True}
      and (setattr(W, "me", "pike") or promises.commission_of(W, V)["yours"]) is False, promises.commission_of(W, V))
t = say("sable", f"look {V} :1", f'do prop {V} lived="{V}@4bf2a2a: lived it myself"')
check("the holder's own lived= naming a commit is her report as of it (a3165), and the testimony shows beside it",
      f"lived= reports {pv} as of 4bf2a2a, not landed yet" in t
      and "your own promise · lived at 4bf2a2a, not landed yet · also lived by pike at 4bf2a2a; by juniper" in say("sable", "promises"), t)
t = say("sable", f"look {V} :1", f'do prop {V} lived="lived it myself, as pike did"')
check("the holder's own lived= then ends it, on her own word", f"lived= reports {pv}: kept (your own word)" in t, t)
check("and the card keeps the testimony beside her report", (W.subjects[W.nodes[V]["subject"]]["props"]).get("lived_by")
      and W.subjects[W.nodes[V]["subject"]]["props"]["lived"].endswith("as pike did"))
check("a card whose commission promise has ended takes no promise's word: anyone's lived= is a prop again",
      not say("pike", f"look {V} :1", f'do prop {V} lived="pike, after"').startswith("ERR"))
# owed to someone else: their lived= is the confirmation it always was; a third person's is still refused
V2 = made(say("juniper", f"look {B} :1", f'do create {B} kind=task title="Visits 2" owner=sable status=open'))
t = say("sable", f"look {V2} :1", f"do prop {V2} commission=asked")
check("(sable asks on juniper's card: sable promised juniper)", "sable promised juniper" in t or "you promised juniper" in t, t)
t = say("pike", f"look {V2} :1", f'do prop {V2} lived="x"')
check("a third person's lived= is refused there too", t.startswith("ERR") and "is sable's word, not yours" in t, t)
t = say("juniper", f"look {V2} :1", f'do prop {V2} lived="saw it land"')
check("the owed one's lived= confirms, as before", "lived= by the one it's owed to confirms" in t, t)

# ---- a2798: a commission's promise is its asker's own act; set for them by another hand, it is no one's ---------------
Z = made(say("sable", f"look {B} :1", f'do create {B} kind=task title="Worlds" owner=sable asked_by=juniper status=open'))
t = say("sable", f"look {Z} :1", f"do prop {Z} commission=asked")
check("set by someone other than asked_by: no one's promise, and the receipt says so",
      "no one's promise yet" in t and "asked for juniper; held by no one" in t, t)
pz = re.search(r"so (a\d+) is no one's", t).group(1)
check("held-by:sable does not select it", pz not in say("sable", "table kind:promise,held-by:sable cols=title"))
t = say("juniper", "promises")
check("juniper's list: 'asked for you, held by no one'", "asked for you, held by no one" in t and pz in t, t)
check("no one can report what no one holds", "held by no one" in say("sable", f"look {pz} :1", f"report {pz}"))
t = say("juniper", f"look {pz} :1", f"accept {pz}")
check("asked_by accepting it makes it hers", "your own promise" in t, t)
Z2 = made(say("sable", f"look {B} :1", f'do create {B} kind=task title="Doors 2" owner=sable asked_by=juniper status=open'))
t = say("sable", f"look {Z2} :1", f"do prop {Z2} commission=asked")
pz2 = re.search(r"so (a\d+) is no one's", t).group(1)
t = say("pike", f"look {pz2} :1", f"accept {pz2}")
check("anyone may hold it by accepting it: Pike's promise, owed to juniper", "you promised juniper" in t, t)
Z3 = made(say("juniper", f"look {B} :1", f'do create {B} kind=task title="Doors 3" owner=juniper asked_by=juniper status=open'))
say("juniper", f"look {Z3} :1", f"do prop {Z3} commission=working")
t = say("sable", f"look {Z3} :1", f"do prop {Z3} commission=asked")
check("no one's, even when asked_by made the card", "no one's promise yet" in t, t)
t = say("pike", f"look {Z3} :1", f'do prop {Z3} lived="x"')
check("a3198: held by no one, a passer-by's lived= is refused, naming the one it was asked for",
      t.startswith("ERR") and "is juniper's word, not yours" in t and "held by no one" in t, t)

# ---- a2798: a request on a card that leaves the living asks its asker, once: withdraw or keep ----------------------
X2 = made(say("sable", f"look {B} :1", f'do create {B} kind=task title="Ask it" status=doing'))
t = say("sable", f'ask to=pike "Pike looks at it" about={X2}')
rq = re.search(r"(a\d+) ask", t).group(1)
t = say("sable", f"look {X2} :1", f"do prop {X2} status=done")
check("closing a card with an open request asks its asker once", "sable is asked once, on their sill" in t
      and "withdraw or keep?" in t, t)
qn = [s for s in W.subjects.values() if (s.get("props") or {}).get("promise") == rq]
check("the question sits on Sable's sill", len(qn) == 1 and W.nodes[W.appearances_of(qn[0]["id"])[0]]["parent"] == R.corner["sable"], qn)
say("sable", f"look {X2} :1", f"do prop {X2} status=doing")
check("and only once", "asked once" not in say("sable", f"look {X2} :1", f"do prop {X2} status=done"))
say("pike", f"look {rq} :1", f"decline {rq}")
check("an answer to the request closes the question", qn[0]["props"].get("status") == "done", qn)

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
t = say("juniper", f"undo {q_decline}")
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

# ---- a2986: a re-ask makes its asker's promise; an old ask, or a different promise about the card, never stops it -----
D3, R3 = roomworld.build(say=False)        # a1590's life, shrunk: asked before promises, the ask taken back for an owe
W3 = D3.world
D, W = D3, W3
K3 = create("pike", R3.BOARD, 'kind=task title="Persons 2" owner=pike asked_by=pike status=open')
say("pike", f"look {K3} :1", f"do prop {K3} commission=asked")
old_ask = W3.events[-1]["id"]
say("pike", f"look {K3} :1", f'do prop {K3} owe="ask it when phase 1 lands" remove=commission')
W3._promises_version = 0
say("sable", "look :1")
check("(the migration ran, and made the owe a promise, not a commission's)", promises.on(W3)
      and len(promises.open_about(W3, W3.nodes[K3]["subject"])) == 1)
p_owe = promises.open_about(W3, W3.nodes[K3]["subject"])[0]["aid"]
say("pike", f"look {p_owe} :1", f"release {p_owe}")
t = say("pike", f"look {K3} :1", f"do prop {K3} commission=asked")
ask = [e for e in W3.events if e["verb"] == "prop" and (e.get("args") or {}).get("commission") == "asked"][-1]["id"]
st3 = [st for st in (promises.state(W3, x) for x in promises.all_sids(W3))
       if (promises.events(W3).get(st["made"]) or {}).get("cause") == ask and st["state"] == "open"]
check("re-asking a card whose old ask came before promises makes the asker's promise, made by this ask (not the old one)",
      "a commission is its asker's promise" in t and old_ask not in t and len(st3) == 1
      and st3[0]["holder"]["name"] == "pike", (t, st3))
K4 = create("pike", R3.BOARD, 'kind=task title="Persons 3" owner=pike asked_by=pike status=open')
t = say("pike", f'promise to=pike "set {K4} commission=asked once phase 1 lands" about={K4}')
check("(pike holds a different promise about the card)", "promise" in t and len(promises.open_about(W3, W3.nodes[K4]["subject"])) == 1, t)
t = say("pike", f"look {K4} :1", f"do prop {K4} commission=asked")
op = promises.open_about(W3, W3.nodes[K4]["subject"])
check("asking a card about which the asker holds a different open promise still makes the commission's promise",
      "a commission is its asker's promise" in t and len(op) == 2, (t, op))
t = say("pike", f"look {K4} :1", f"do prop {K4} commission=working", f"do prop {K4} commission=asked")
check("but a commission promise for this card already open is not made twice, and the receipt names it",
      "a commission is its asker's promise" not in t and len(promises.open_about(W3, W3.nodes[K4]["subject"])) == 2
      and re.search(r"no new promise: a\d+ already holds this commission", t), t)

print(f"\n{len(fails)} failed" if fails else "\nall ok")
sys.exit(1 if fails else 0)
