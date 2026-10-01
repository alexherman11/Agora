"""test_lines (a1581, lines as things phase 1): each chat line is a thing with its own id, and who it addresses is
the writer's stored word.

    python test_lines.py

Builds its own small world in memory (roomworld.py) and never saves it; every desk line runs through the desk's own
dispatch, as explore.py and deskd call it. Checks: a line's id, chat, to and its by and at read from its event; @name
outside quotes is stored as to=, a quoted @ addresses nobody, to= overrides, and the receipt says which; For you
(inbox:) reads to=, not the words; one press never makes two lines; a changed line says 'edited' and keeps its
words; a chat from before lines becomes lines in one event, an unknown line says 'by unknown, at unknown', and
undoing that event puts the chat back as it was.
"""
import copy
import os
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ["DESKD"] = "off"

import roomworld   # noqa: E402
import scene       # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n     {str(detail)[:1500]}"))
    if not ok:
        fails.append(name)


D, R = roomworld.build()
W = D.world


def be(me):
    per = D._per = getattr(D, "_per", None) or {}
    W.me = me
    if me not in per:
        per[me] = ({}, {W.root}, len(W.events))
    D.seen, D.open, D.last_event_seen = per[me]
    D._window = ""


def say(me, line, whole=True):
    be(me)
    r = D.dispatch("desk", {"line": line, "whole": whole, "reply": uuid.uuid4().hex})
    return (r.get("text") or "") + (("\nERROR " + r["error"]) if r.get("error") else "")


def made(text):
    m = re.search(r"line (m\d+) · to: ([^\n]*)", text)
    return (m.group(1), m.group(2)) if m else (None, None)


TALK = R.TALK[R.LOUNGE]
SID = W.nodes[TALK]["subject"]
S = W.subjects[SID]

# ---- a chat made now has lines from the start ------------------------------------------------------------------
lines = S.get("lines")
check("a chat made by create holds its lines as things, one per append", lines is not None and len(lines) == 3, lines)
check("each line is the chat's text, joined: the text reads as before", "\n".join(l["text"] for l in lines) == S["text"].strip("\n"),
      (S["text"], lines))
check("a line stores no by and no at; its event does", all(set(l) <= {"id", "text", "to", "ev"} and l["ev"] for l in lines), lines)
first = lines[0]
by, at = W.line_by_at(first)
check("by and at are read from the event that made the line", by == "sable" and at[:4].isdigit(), (by, at))

# ---- addresses: the writer's word, stored when written ---------------------------------------------------------
t = say("sable", f'do append {TALK} line="@pike could you look at this? and @Juniper too"')
mid, to = made(t)
check("append reads @name outside quotes as to=, and the receipt says so", mid and to == "pike, juniper", t)
t = say("juniper", f"do append {TALK} line=\"as Pike wrote, '@sable (e3305)' and `@pike` are quoted\"")
qid, qto = made(t)
check("a quoted @ addresses nobody, and the receipt says 'to: nobody'", qid and qto == "nobody", t)
t = say("pike", f'do append {TALK} line="@sable this is really for Juniper" to=juniper')
oid, oto = made(t)
check("to= overrides what the words say", oto == "juniper", t)
t = say("pike", f'do append {TALK} line="thinking out loud, @sable" to=nobody')
check("to=nobody says outright that a line addresses no one", made(t)[1] == "nobody", t)
t = say("pike", f'do append {TALK} line="mail me at pike@example.org"')
check("an @ inside a word (an address) names no one", made(t)[1] == "nobody", t)

# ---- examine <line id> ---------------------------------------------------------------------------------------------
t = say("alex", f"examine {mid}")
check("examine <line id> names its chat, by, at and to",
      f"a chat line in \"{S['title']}\"" in t and "by sable · at 20" in t and "to: pike, juniper" in t and "@pike could you" in t, t)
check("read and look of a line id print the same", say("alex", f"read {mid}") == t == say("alex", f"look {mid}"), say("alex", f"read {mid}"))
t = say("alex", f"history {mid}")
check("history <line id> lists the event that made it", W.find_line(mid)[1]["ev"] in t, t)

# ---- For you reads to= -------------------------------------------------------------------------------------------
rows = scene.rows(D, "inbox:sable")
said = [r["said"] for r in rows]
check("a quoted '@sable (e3305)' does not reach Sable's For you", not any("quoted" in s for s in said), said)
check("an @sable that to= took elsewhere does not reach her either", not any("really for Juniper" in s for s in said), said)
check("to=nobody keeps a line out of For you even with @sable in it", not any("thinking out loud" in s for s in said), said)
rows = scene.rows(D, "inbox:juniper")
check("a line to=juniper reaches Juniper's For you, with its line id",
      any(r["line"] == oid and "really for Juniper" in r["said"] for r in rows), rows)
t = say("pike", f'do append {TALK} line="@sable the parser is in"')
pid, _ = made(t)
check("@sable written outside quotes reaches Sable's For you",
      any(r["line"] == pid for r in scene.rows(D, "inbox:sable")), scene.rows(D, "inbox:sable"))
msgs = scene.rows(D, f"messages:{TALK}")
check("messages rows carry each line's id and who it addresses",
      any(r["line"] == mid and r["to"] == "pike, juniper" for r in msgs), msgs[-6:])

# ---- the house's say verb reads @ the same way ------------------------------------------------------------------
say("juniper", f"go {R.LOUNGE} :1")
t = say("juniper", "say @pike the couches are new")
check("say reads @name as to=, through the append it makes", "to: pike" in t, t)

# ---- one press, one line (a1008) ------------------------------------------------------------------------------------
n0 = len(S["lines"])
W.intent, W._intent_k = "juniper-press-1", 0
t1 = say("juniper", f'do append {TALK} line="sent once"; do append {TALK} line="and a second line in the same press"', whole=False)
W.intent, W._intent_k = "juniper-press-1", 0       # the same press, sent again (a lost answer, a door swapped)
t2 = say("juniper", f'do append {TALK} line="sent once"; do append {TALK} line="and a second line in the same press"', whole=False)
W.intent = None
check("two lines in one press are two lines", len(S["lines"]) == n0 + 2, (t1, S["lines"][-3:]))
check("the same press sent again makes no line, and says which it made", "already said, as m" in t2 and len(S["lines"]) == n0 + 2, t2)
check("a line keeps the press it came from", [l.get("intent") for l in S["lines"][-2:]] == ["juniper-press-1", "juniper-press-1#2"],
      S["lines"][-2:])

# ---- a line is testimony -----------------------------------------------------------------------------------------
say("alex", f"read {TALK} :3")
t = say("alex", f'do replace {TALK} old="the parser is in" new="the parser is in, tested"')
line = W.find_line(pid)[1]
check("changing a line's words marks it edited and keeps its words before",
      line.get("edited") and line["was"][0]["text"].endswith("the parser is in") and line["text"].endswith("tested"), (t, line))
check("the receipt names the edited line", f"edited line(s) {pid}" in t, t)
t = say("alex", f"read {TALK} :3")
check("read of the chat shows the line as edited", f"the parser is in, tested  (edited, {pid})" in t, t[-400:])
t = say("alex", f"examine {pid}")
check("examine shows who edited it and the words before", "· edited" in t and "edited by alex" in t and "the parser is in\n" in t + "\n", t)
check("messages rows say edited", any(r["line"] == pid and r["edited"] == "edited" for r in scene.rows(D, f"messages:{TALK}")), "")
t = say("alex", f'do rewrite {TALK} text="Alex: nothing was said"')
check("a rewrite that drops lines is refused, pointing at replace or undo", "ERR" in t and "replace old=" in t, t)

# ---- undo of an append takes its line ----------------------------------------------------------------------------
t = say("pike", f'do append {TALK} line="a line to take back"')
gone, _ = made(t)
ev = W.find_line(gone)[1]["ev"]
say("pike", f"undo {ev}")
check("undo of an append takes its line away", W.find_line(gone)[1] is None, S["lines"][-2:])
t = say("pike", f"examine {gone}")
check("an undone line's id still answers, by the event that made it", "no longer here" in t and ev in t, t)

# ---- migration: a chat from before lines --------------------------------------------------------------------------
BT = R.TALK[R.BOARD]
bsid = W.nodes[BT]["subject"]
B = W.subjects[bsid]
B.pop("lines")                     # as every chat was before a1581
B["text"] += "\nSomeone: a line no event made"
was = copy.deepcopy(B)
n_ev = len(W.events)
t = say("alex", "look")
mig = [e for e in W.events[n_ev:] if e["verb"] == "lines"]
check("a chat from before lines becomes lines in one event, by the house, said in history",
      len(mig) == 1 and mig[0]["by"] == "house" and "became things" in mig[0]["note"] and "lines in" in t, (mig, t[:300]))
check("its text is untouched", B["text"] == was["text"], "")
bl = B.get("lines") or []
check("the appended line got its event; the other says by unknown", len(bl) == 2 and bl[0]["ev"] and bl[1]["ev"] is None, bl)
t = say("alex", f"examine {bl[1]['id']}")
check("examine of a line no event made says 'by unknown, at unknown'", "by unknown, at unknown" in t, t)
check("the migration event counts the lines it addressed", mig[0]["args"] == {"lines": 2, "addressed": 0, "unknown": 1}, mig[0]["args"])
say("alex", f"undo {mig[0]['id']}")
B = W.subjects[bsid]                # undo puts back the subject as it was: a new record
now = copy.deepcopy(B)
check("undo of the migration puts the chat back as it was", {k: v for k, v in now.items() if k != "rev"} == {k: v for k, v in was.items() if k != "rev"},
      (now.keys(), was.keys()))
n_ev = len(W.events)
say("alex", "look")
check("an undone migration is not done again", "lines" not in W.subjects[bsid] and not any(e["verb"] == "lines" for e in W.events[n_ev:]), "")
t = say("pike", f'do append {BT} line="@sable still appends, as before"')
check("a chat without lines still takes a line as it always did", "line m" not in t and W.subjects[bsid]["text"].endswith("as before"), t)

print(f"\n{'all ok' if not fails else str(len(fails)) + ' failed: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
